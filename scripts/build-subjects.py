#!/usr/bin/env python3
"""Build subject catalogs and PDF from PRIVATE/planning/subject-order-<slug>.json.

check: verify all official positions, aliases, approvals, sources and published routes.
build: stage a complete site/PDF build in a temporary directory (dry-run by default).
build --apply: write new subject files; never overwrite existing published files.

Example:
python scripts/build-subjects.py build --private-root ../gos-exams-2027 --subjects nt dogmatics --apply
Dependencies for PDF: reportlab, a Cyrillic DejaVu Sans TTF family.
"""
import argparse
import html
import os
import json
import json
import re
import shutil
import sys
import tempfile
from collections import Counter
from pathlib import Path

PUBLIC = Path(__file__).resolve().parents[1]
SUBJECTS = {
    "nt": ("НЗ", "Священное Писание Нового Завета"),
    "dogmatics": ("ДБ", "Догматическое богословие"),
    "ot": ("ВЗ", "Священное Писание Ветхого Завета"),
    "oi": ("ОИ", "Общецерковная история"),
    "rpc": ("ИРПЦ", "История Русской Православной Церкви"),
    "liturgics": ("Л", "Литургика"),
}
LEVELS = ("l3", "l2", "l1")
LABELS = {"l3": "Полный ответ", "l2": "Устный ответ", "l1": "Тезисный план"}
ROUTE = re.compile(r"^sessions/\d{2}/q\d{2}(?:-[a-z]+)?-l[123]\.html$")
FRONT = re.compile(r"\A---\s*\n.*?\n---\s*\n", re.S)


def abort(message):
    raise ValueError(message)


def source_path(private, slug, row, level):
    """Resolve optional historical source layout without changing old models."""
    folder = row.get("source_folder", slug)
    filename = row.get("source_file", "q%02d.md" % row["canonical_question"])
    if not isinstance(folder, str) or not re.fullmatch(r"[a-z][a-z0-9-]*", folder):
        abort("Unsafe source folder: " + str(folder))
    if not isinstance(filename, str) or not re.fullmatch(r"(?:q[0-9]{2}|l-[0-9]{2})\.md", filename):
        abort("Unsafe source filename: " + str(filename))
    expected = "%02d" % row["canonical_question"]
    if filename not in ("q" + expected + ".md", "l-" + expected + ".md"):
        abort("Source filename/question mismatch: " + filename)
    return private / "materials" / folder / level / filename


def published_page(public, row, level, slug):
    requested = row["level_urls"][level]
    if not isinstance(requested, str) or not ROUTE.fullmatch(requested):
        abort("Unsafe published route: " + str(requested))
    if (public / requested.replace(".html", ".md")).is_file():
        return requested
    alternate = "sessions/%02d/q%02d-%s-%s.html" % (
        row["session"], row["canonical_question"], slug, level)
    if (public / alternate.replace(".html", ".md")).is_file():
        return alternate
    abort("Published page missing: " + requested + " / " + alternate)


def read_model(private, public, slug):
    file = private / "planning" / ("subject-order-" + slug + ".json")
    if not file.is_file():
        abort("Missing order config: " + str(file))
    model = json.loads(file.read_text(encoding="utf-8"))
    if model.get("schema_version") != 1 or model.get("slug") != slug:
        abort(slug + ": incompatible schema")
    topics = model.get("topics")
    sections = model.get("sections")
    if not isinstance(topics, list) or len(topics) != 25 or not isinstance(sections, list):
        abort(slug + ": expected 25 positions and subject sections")
    if Counter(row.get("official_number") for row in topics) != Counter(range(1, 26)):
        abort(slug + ": incomplete or duplicated official numbers")
    if [x.get("semantic_rank") for x in topics] != list(range(1, 26)):
        abort(slug + ": semantic ranks must be consecutive")
    ids = [x["id"] for x in sections]
    if len(set(ids)) != len(ids):
        abort(slug + ": duplicated section IDs")
    groups = {key: [] for key in ids}
    routes = {}
    canonicals = {}
    for row in topics:
        n = row["official_number"]
        c = row.setdefault("canonical_question", n)
        if not isinstance(c, int) or c not in range(1, 26):
            abort(slug + ": invalid canonical for question " + str(n))
        if row.get("topic_id") != "%s-q%02d" % (slug, c):
            abort(slug + ": wrong topic ID for " + str(n))
        if row.get("section_id") not in groups:
            abort(slug + ": unknown section for " + str(n))
        groups[row["section_id"]].append(n)
        question = row.get("official_question")
        if not isinstance(question, str) or len(question) < 18:
            abort(slug + ": empty official formulation: " + str(n))
        if c in canonicals and canonicals[c] != question:
            abort(slug + ": alias formula differs: " + str(n))
        canonicals[c] = question
        if row.get("site") not in ("published", "published_working"):
            abort(slug + ": unpublished question: " + str(n))
        if row.get("quality") != "approved":
            notice = row.get("working_notice_url")
            if row.get("site") != "published_working" or not notice:
                abort(slug + ": unapproved question without exception: " + str(n))
            if not re.fullmatch(r"sessions/\d{2}/source-status\.html", notice):
                abort(slug + ": invalid notice route: " + str(n))
            if not (public / notice.replace(".html", ".md")).is_file():
                abort(slug + ": missing working notice: " + str(n))
        routes[n] = {}
        for level in LEVELS:
            routes[n][level] = published_page(public, row, level, slug)
            source = source_path(private, slug, row, level)
            if not source.is_file() or not source.read_text(encoding="utf-8").strip():
                abort("Missing or empty manuscript: " + str(source))
    for section in sections:
        if section["official_numbers"] != groups[section["id"]]:
            abort(slug + ": section and topic order disagree: " + section["id"])
    return model, routes


def h(value):
    return html.escape(str(value), quote=True)


def html_entry(row, paths, order="meaning", previous=None, following=None):
    n = row["official_number"]
    alias = ""
    if row["canonical_question"] != n:
        alias = '<p class="subject-alias">Общий ответ с вопросом №%d</p>' % row["canonical_question"]
    notice = ""
    if row.get("quality") != "approved":
        notice = ('<p class="subject-notice"><b>Рабочая редакция.</b> %s '
                  '<a href="../../%s">Ограничения источников</a></p>' %
                  (h(row.get("working_note", "")), h(row["working_notice_url"])))
    links = []
    for level in LEVELS:
        links.append('<a href="../../%s">%s — %s</a>' % (
            h(paths[level]), level.upper(), h(LABELS[level])))
        links.append('<a href="pdf/q%02d-%s.pdf" download>PDF %s</a>' %
                     (row["canonical_question"], level, level.upper()))
    adjacent = []
    if previous is not None:
        adjacent.append('<a href="#%s-q%02d">← №%d</a>' % (order, previous, previous))
    if following is not None:
        adjacent.append('<a href="#%s-q%02d">№%d →</a>' % (order, following, following))
    adjacent.append('<a href="../../sessions/%02d/index.html">Занятие №%d</a>' % (row["session"], row["session"]))
    return ('<li class="subject-question" id="%s-q%02d"><p><b>№%d.</b> %s</p>%s%s'
            '<div class="subject-links">%s</div><nav class="subject-neighbors">%s</nav></li>' %
            (order, n, n, h(row["official_question"]), alias, notice, " · ".join(links), " · ".join(adjacent)))


def jump_links(order):
    return '<nav class="subject-jump" aria-label="Номер билета">' + " ".join(
        '<a href="#%s-q%02d">%d</a>' % (order, n, n) for n in range(1, 26)) + '</nav>'


def order_list(rows, all_rows, routes, order):
    positions = {r["official_number"]: i for i, r in enumerate(all_rows)}
    content = []
    for row in rows:
        i = positions[row["official_number"]]
        prev = all_rows[i-1]["official_number"] if i else None
        nxt = all_rows[i+1]["official_number"] if i+1 < len(all_rows) else None
        content.append(html_entry(row, routes[row["official_number"]], order, prev, nxt))
    return "".join(content)


def page_markdown(model, routes):
    title = model["title"]
    parts = []
    semantic = model["topics"]
    numerical = sorted(semantic, key=lambda row: row["official_number"])
    for section in model["sections"]:
        rows = [r for r in model["topics"] if r["section_id"] == section["id"]]
        parts.append('<section><h2>%s</h2><ol class="subject-list">%s</ol></section>' %
                     (h(section["title"]), order_list(rows, semantic, routes, "meaning")))
    numeric = order_list(numerical, numerical, routes, "number")
    css = """<style>
.subject-choice {display:flex;gap:.65rem;flex-wrap:wrap;margin:1rem 0}
.subject-choice button {padding:.65rem .9rem;border:1px solid #90a4b4;border-radius:6px;background:white;cursor:pointer}
.subject-choice button[aria-pressed="true"] {background:#e7eff5;font-weight:bold}
.subject-list {list-style:none;padding:0}
.subject-question {padding:.7rem;margin:0 0 1rem;border:1px solid #d9e0e5;border-radius:6px;background:#fafbfc}
.subject-question p {margin:.15rem 0 .6rem}
.subject-links {font-size:.88rem;line-height:1.8}
.subject-notice {color:#78371f}
.subject-alias {color:#526573;font-size:.9rem}
.subject-neighbors {border-top:1px solid #d9e0e5;margin-top:.45rem;padding-top:.45rem;font-size:.9rem}
.subject-question {scroll-margin-top:1rem}
.subject-jump {line-height:2.4;margin:.7rem 0;padding:.6rem;border:1px solid #d9e0e5;border-radius:6px}
.subject-jump a {display:inline-block;min-width:1.8rem;text-align:center}
.subject-downloads {display:flex;gap:.7rem;flex-wrap:wrap;margin:1rem 0}
[hidden] {display:none!important}
</style>"""
    js = """<script>
(function() {
 var buttons=document.querySelectorAll("[data-sort-button]");
 var panels=document.querySelectorAll("[data-sort-panel]");
 function set(mode) {
   buttons.forEach(function(b){b.setAttribute("aria-pressed",String(b.dataset.sortButton===mode));});
   panels.forEach(function(p){p.hidden=p.dataset.sortPanel!==mode;});
 }
 buttons.forEach(function(b){b.addEventListener("click",function(){set(b.dataset.sortButton);location.hash=b.dataset.sortButton+"-q01";});});
 window.addEventListener("hashchange",function(){set(location.hash.indexOf("#number-q")===0?"number":"meaning");});
 set(location.hash.indexOf("#number-q")===0?"number":"meaning");
}());
</script>"""
    pdfs = " ".join('<a href="pdf/%s.pdf" download>Весь %s (PDF)</a>' % (x, x.upper()) for x in LEVELS)
    return ('---\nlayout: default\ntitle: "%s — подготовка по предмету"\n---\n\n<!-- subject-generator: managed -->\n' % title
            + '[Главная](../../index.html) › [Материалы](../../materials/index.html) › [Предметы](../index.html) › **%s**\n\n# %s\n\n' % (title, title)
            + 'Все 25 официальных номеров. Смысловой порядок основан на православных учебниках БПДС.\n\n'
            + css + '<p><a href="../index.html">Все предметы</a> · <a href="../../materials/index.html">По занятиям</a> · <a href="numbers.html">По номерам без JavaScript</a></p><div class="subject-downloads">' + pdfs + '</div>'
            + '<div class="subject-choice" role="group" aria-label="Порядок вопросов">'
            + '<button type="button" data-sort-button="meaning" aria-pressed="true">Смысловой порядок</button>'
            + '<button type="button" data-sort-button="number" aria-pressed="false">По номерам</button></div>'
            + '<div data-sort-panel="meaning">' + jump_links("meaning") + "".join(parts) + '</div>'
            + '<div data-sort-panel="number" hidden><h2>Номера 1–25</h2>'
            + jump_links('number') + '<ol class="subject-list">' + numeric + '</ol></div>'
            + '<noscript><p>Без JavaScript доступен смысловой порядок и отдельный числовой список: <a href="numbers.html">№1–25</a>.</p></noscript>'
            + js + '\n')


def numbers_markdown(model, routes):
    rows = sorted(model['topics'], key=lambda row: row['official_number'])
    return ('---\nlayout: default\ntitle: Билеты по номерам\n---\n\n'
            '<!-- subject-generator: managed -->\n'
            '[Все предметы](../index.html) · [К смысловому порядку](index.html)\n\n'
            '# %s — билеты №1–25\n\n' % model['title']
            + jump_links('number')
            + '<ol class="subject-list">' + order_list(rows, rows, routes, 'number') + '</ol>')


def catalog(ready):
    lines = ['---', 'layout: default', 'title: Подготовка по предметам', '---', '', '<!-- subject-generator: managed -->',
             '[Главная](../index.html) › **Предметы**', '', '# Подготовка по предметам', '',
             'Материалы представлены также [по занятиям](../materials/index.html).', '']
    for slug, (_, name) in SUBJECTS.items():
        lines.append('- [%s](%s/index.html) — 25 вопросов, L3/L2/L1, PDF.' %
                     (name, slug) if slug in ready else '- %s — готовится.' % name)
    return "\n".join(lines) + "\n"


def build(private, public, dest, slugs, with_pdf):
    if with_pdf:
        import importlib.util
        spec = importlib.util.spec_from_file_location("subject_pdf", Path(__file__).with_name("subject_pdf.py"))
        pdf_lib = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(pdf_lib)
    else:
        pdf_lib = None
    for slug in slugs:
        model, routes = read_model(private, public, slug)
        base = dest / "subjects" / slug
        base.mkdir(parents=True, exist_ok=True)
        (base / "index.md").write_text(page_markdown(model, routes), encoding="utf-8")
        (base / "numbers.md").write_text(numbers_markdown(model, routes), encoding="utf-8")
        if with_pdf:
            seen = set()
            canonical = []
            for row in model["topics"]:
                if row["canonical_question"] not in seen:
                    canonical.append(row)
                    seen.add(row["canonical_question"])
            source_ref = os.environ.get("SUBJECT_SOURCE_SHA", "")
            pdf_records = []
            for level in LEVELS:
                full = base / "pdf" / (level + ".pdf")
                pdf_lib.build_pdf(full, model, canonical, private, slug, level,
                                  source_ref=source_ref, include_index=True)
                meta = pdf_lib.check_pdf(full, full=True, expected_numbers=range(1, 26),
                                         expected_title=model["title"])
                pdf_records.append({"file": str(full.relative_to(base)), "level": level,
                                    "kind": "subject", **meta})
                for row in canonical:
                    individual = base / "pdf" / ("q%02d-%s.pdf" % (row["canonical_question"], level))
                    pdf_lib.build_pdf(individual, model, [row], private, slug, level,
                                      source_ref=source_ref, include_index=False)
                    info = pdf_lib.check_pdf(individual, expected_title=model["title"])
                    pdf_records.append({"file": str(individual.relative_to(base)),
                                        "level": level, "kind": "question",
                                        "canonical_question": row["canonical_question"], **info})
            expected = (len(canonical) + 1) * len(LEVELS)
            if len(pdf_records) != expected:
                abort("PDF count mismatch for " + slug)
            (base / "pdf-manifest.json").write_text(
                json.dumps({"subject": slug, "canonical_count": len(canonical),
                            "official_numbers": 25, "source_ref": source_ref,
                            "pdf_count": expected, "files": pdf_records},
                           ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    (dest / "subjects" / "index.md").write_text(catalog(slugs), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build"))
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--public-root", type=Path, default=PUBLIC)
    parser.add_argument("--subjects", nargs="+", required=True, choices=tuple(SUBJECTS))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-pdf", action="store_true", help="diagnostic only")
    parser.add_argument("--preview-dir", type=Path, help="save HTML drafts outside the public site")
    args = parser.parse_args()
    private, public = args.private_root.resolve(), args.public_root.resolve()
    slugs = list(dict.fromkeys(args.subjects))
    if args.preview_dir and (args.command != "build" or args.apply):
        parser.error("--preview-dir requires build without --apply")
    if args.apply and (args.command != "build" or args.no_pdf):
        parser.error("--apply requires build with PDF")
    for slug in slugs:
        model, _ = read_model(private, public, slug)
        print("PASS %s: 25 official numbers, %d distinct answers" %
              (slug, len({r["canonical_question"] for r in model["topics"]})))
    if args.command == "check":
        return
    with tempfile.TemporaryDirectory(prefix="subject-build-") as folder:
        staged = Path(folder)
        build(private, public, staged, slugs, not args.no_pdf)
        already_ready = {slug for slug in SUBJECTS if (public / "subjects" / slug / "index.md").is_file()}
        (staged / "subjects" / "index.md").write_text(catalog(already_ready | set(slugs)), encoding="utf-8")
        count = sum(p.is_file() for p in staged.rglob("*"))
        print("PASS: built %d staged files" % count)
        if args.preview_dir:
            preview = args.preview_dir.resolve()
            if preview.exists():
                abort("Refusing to overwrite existing preview: " + str(preview))
            shutil.copytree(staged / "subjects", preview)
            print("PREVIEW: subject pages saved to " + str(preview))
        if args.apply:
            # Protect hand-written content, but permit reproducible updates to managed pages/PDF.
            marker = "subject-generator: managed"
            for slug in slugs:
                existing = public / "subjects" / slug / "index.md"
                if existing.exists() and marker not in existing.read_text(encoding="utf-8"):
                    abort("Refusing to overwrite unmanaged subject: " + str(existing))
            existing_catalog = public / "subjects" / "index.md"
            if existing_catalog.exists() and marker not in existing_catalog.read_text(encoding="utf-8"):
                abort("Refusing to overwrite unmanaged catalog: " + str(existing_catalog))
            for p in staged.rglob("*"):
                if p.is_file():
                    target = public / p.relative_to(staged)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(p, target)
            print("APPLIED managed files; Git commit, CI and Pages not yet verified")
        else:
            print("DRY RUN: no public repository files changed")


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as exc:
        print("ERROR: " + str(exc), file=sys.stderr)
        sys.exit(1)
