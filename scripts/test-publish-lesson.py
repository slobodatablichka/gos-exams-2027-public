#!/usr/bin/env python3
"""Integration test: build an unpublished lesson in a disposable copy only."""
import csv
import importlib.util
import shutil
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("publication", ROOT / "scripts/publish-lesson.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

with tempfile.TemporaryDirectory(prefix="lesson-links-") as temp:
    dst = Path(temp) / "public"
    private = Path(temp) / "private"
    dst.mkdir()
    for directory in ("_data", "sessions"):
        shutil.copytree(ROOT / directory, dst / directory)
    (dst / "materials").mkdir()
    for path in ("schedule.md", "index.md", "materials/index.md"):
        target = dst / path
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(ROOT / path, target)
    module.ROOT = dst
    module.validate()  # All four pre-existing published lessons.
    original_schedule = module.read("schedule.md")
    original_legacy = {p.relative_to(dst): p.read_bytes()
                       for p in (dst / "sessions").rglob("*.md")}
    rows = module.topics(5)
    (private / "planning").mkdir(parents=True)
    progress = private / "planning/lesson-progress.csv"
    with progress.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("meeting", "subject", "question",
                             "sources", "l3", "l2", "l1", "quality"))
        writer.writeheader()
        for row in rows:
            writer.writerow({"meeting": 5, "subject": row["subject"], "question": row["question"],
                             "sources": "done", "l3": "done", "l2": "done", "l1": "done",
                             "quality": "approved"})
    start, end = module.schedule_section(original_schedule, 5)
    section = original_schedule[start:end]
    for row in rows:
        _, cells = module.schedule_row(section, row)
        question = cells[1]
        pathcode = module.code(row)
        for level in module.LEVELS:
            path = private / "materials" / "dogmatics" / level / f"q{pathcode}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f"# ДБ №{row['question']}. Учебный пример\n\n"
                f"> **Официальный экзаменационный вопрос.** {question}\n\n"
                "Полностью искусственный тестовый абзац; тест не публикуется.\n",
                encoding="utf-8")
    planned = module.assemble(5, private)
    assert len(planned) == len(rows) * 3 + 2
    assert not (dst / "sessions/05").exists(), "Dry-run touched public files"
    module.add_navigation(5, planned)
    assert (dst / "schedule.md").read_text(encoding="utf-8") == original_schedule
    assert len(planned) == len(rows) * 3 + 6  # content + schedule, catalog, home, ledger.
    for path, data in planned.items():
        target = dst / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(data, encoding="utf-8")
    module.validate()
    assert module.read("_data/published_sessions.csv").count("5,") == 1
    assert "sessions/05/q01-l3.html" in module.read("schedule.md")
    assert "sessions/05/index.html" in module.read("index.md")
    for path, data in original_legacy.items():
        assert (dst / path).read_bytes() == data, f"Existing URL modified: {path}"
    try:
        module.assemble(5, private)
    except ValueError as exc:
        assert "Existing URL cannot be overwritten" in str(exc)
    else:
        raise AssertionError("Second publication overwrote existing URLs")

    # A failed quality gate must reject content before writing.
    with progress.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("meeting", "subject", "question",
                             "sources", "l3", "l2", "l1", "quality"))
        writer.writeheader()
        for row in rows:
            writer.writerow({"meeting": 5, "subject": row["subject"], "question": row["question"],
                             "sources": "done", "l3": "done", "l2": "done", "l1": "done",
                             "quality": "review_pending"})
    try:
        module.quality_gate(private, 5, rows)
    except ValueError as exc:
        assert "Quality gate" in str(exc)
    else:
        raise AssertionError("Rejected quality passed publication gate")
print("PASS: dry run, generated pages, redirects preservation, catalogs, and quality gate")
