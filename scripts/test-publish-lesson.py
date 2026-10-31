#!/usr/bin/env python3
"""Integration test: build an unpublished lesson in a disposable copy only."""
import csv
import importlib.util
import shutil
import sys
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
    module.validate()  # Existing published lessons remain valid.
    published = {int(r['session']) for r in module.csv_rows(module.LEDGER)}
    session = next((n for n in range(1, 24) if n not in published), None)
    if session is None:
        raise AssertionError('No unpublished lesson available for regression test')
    original_schedule = module.read("schedule.md")
    original_legacy = {p.relative_to(dst): p.read_bytes()
                       for p in (dst / "sessions").rglob("*.md")}
    rows = module.topics(session)
    (private / "planning").mkdir(parents=True)
    progress = private / "planning/lesson-progress.csv"
    with progress.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("meeting", "subject", "question",
                             "sources", "l3", "l2", "l1", "quality"))
        writer.writeheader()
        for row in rows:
            writer.writerow({"meeting": session, "subject": row["subject"], "question": row["question"],
                             "sources": "done", "l3": "done", "l2": "done", "l1": "done",
                             "quality": "approved"})
    start, end = module.schedule_section(original_schedule, session)
    section = original_schedule[start:end]
    for row in rows:
        _, cells = module.schedule_row(section, row)
        question = cells[1]
        pathcode = module.code(row)
        for level in module.LEVELS:
            subject_dir = module.SUBJECTS[row["subject"]][0]
            path = private / "materials" / subject_dir / level / f"q{pathcode}.md"
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(
                f"# {row['subject']} №{row['question']}. Учебный пример\n\n"
                f"> **Официальный экзаменационный вопрос.** {question}\n\n"
                "Полностью искусственный тестовый абзац; тест не публикуется.\n",
                encoding="utf-8")
    planned = module.assemble(session, private)
    assert len(planned) == len(rows) * 3 + 2
    assert not (dst / f"sessions/{session:02d}").exists(), "Dry-run touched public files"
    module.add_navigation(session, planned)
    assert (dst / "schedule.md").read_text(encoding="utf-8") == original_schedule
    assert len(planned) == len(rows) * 3 + 6  # content + schedule, catalog, home, ledger.
    # Exercise the real --apply path, including isolated full-site prevalidation.
    original_argv = sys.argv[:]
    try:
        sys.argv = ["publish-lesson.py", "build", str(session), "--private-root",
                    str(private), "--apply"]
        module.main()
    finally:
        sys.argv = original_argv
    module.validate()
    assert sum(r.startswith(f"{session},") for r in module.read("_data/published_sessions.csv").splitlines()) == 1
    assert f"sessions/{session:02d}/q{module.code(rows[0])}-l3.html" in module.read("schedule.md")
    assert f"sessions/{session:02d}/index.html" in module.read("index.md")
    for path, data in original_legacy.items():
        assert (dst / path).read_bytes() == data, f"Existing URL modified: {path}"
    try:
        module.assemble(session, private)
    except ValueError as exc:
        assert "already published" in str(exc) or "Existing URL cannot be overwritten" in str(exc)
    else:
        raise AssertionError("Second publication overwrote existing URLs")

    # A failed quality gate must reject content before writing.
    with progress.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=("meeting", "subject", "question",
                             "sources", "l3", "l2", "l1", "quality"))
        writer.writeheader()
        for row in rows:
            writer.writerow({"meeting": session, "subject": row["subject"], "question": row["question"],
                             "sources": "done", "l3": "done", "l2": "done", "l1": "done",
                             "quality": "review_pending"})
    try:
        module.quality_gate(private, session, rows)
    except ValueError as exc:
        assert "Quality gate" in str(exc)
    else:
        raise AssertionError("Rejected quality passed publication gate")
print("PASS: dry run, generated pages, redirects preservation, catalogs, and quality gate")
