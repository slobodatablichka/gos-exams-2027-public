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
    return private / "materials" / slug / level / ("q%02d.md" % row["canonical_question"])


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
                     (n, level, level.upper()))
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


def page_markdown(model, routes):
    title = model["title"]
    parts = []
    for section in model["sections"]:
        rows = [r for r in model["topics"] if r["section_id"] == section["id"]]
        parts.append('<section><h2>%s</h2><ol class="subject-list">%s</ol></section>' %
                     (h(section["title"]), "".join(html_entry(r, routes[r["official_number"]]) for r in rows)))
    numeric = "".join(html_entry(row, routes[row["official_number"]])
                      for row in sorted(model["topics"], key=lambda r: r["official_number"]))
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
 buttons.forEach(function(b){b.addEventListener("click",function(){set(b.dataset.sortButton);});});
 set("meaning");
}());
</script>"""
    pdfs = " ".join('<a href="pdf/%s.pdf" download>Весь %s (PDF)</a>' % (x, x.upper()) for x in LEVELS)
    return ('---\nlayout: default\ntitle: "%s — подготовка по предмету"\n---\n\n<!-- subject-generator: managed -->\n' % title
            + '[Главная](../../index.html) › [Предметы](../index.html) › **%s**\n\n# %s\n\n' % (title, title)
            + 'Все 25 официальных номеров. Смысловой порядок основан на православных учебниках БПДС.\n\n'
            + css + '<div class="subject-downloads">' + pdfs + '</div>'
            + '<div class="subject-choice" role="group" aria-label="Порядок вопросов">'
            + '<button type="button" data-sort-button="meaning" aria-pressed="true">Смысловой порядок</button>'
            + '<button type="button" data-sort-button="number" aria-pressed="false">По номерам</button></div>'
            + '<div data-sort-panel="meaning">' + "".join(parts) + '</div>'
            + '<div data-sort-panel="number" hidden><h2>Номера 1–25</h2><ol class="subject-list">'
            + numeric + '</ol></div>'
            + '<noscript><p>Без JavaScript доступен смысловой перечень со всеми 25 номерами.</p></noscript>'
            + js + '\n')


def catalog(ready):
    lines = ['---', 'layout: default', 'title: Подготовка по предметам', '---', '', '<!-- subject-generator: managed -->',
             '[Главная](../index.html) › **Предметы**', '', '# Подготовка по предметам', '',
             'Материалы представлены также [по занятиям](../materials/index.html).', '']
    for slug, (_, name) in SUBJECTS.items():
        lines.append('- [%s](%s/index.html) — 25 вопросов, L3/L2/L1, PDF.' %
                     (name, slug) if slug in ready else '- %s — готовится.' % name)
    return "\n".join(lines) + "\n"


def pdf_tools():
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import ParagraphStyle
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
    except ImportError:
        abort("PDF dependency missing: pip install reportlab")
    regular = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf")
    bold = Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf")
    if not regular.is_file() or not bold.is_file():
        abort("Cyrillic DejaVuSans fonts missing; cannot create readable PDF")
    if "SubjectFont" not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont("SubjectFont", str(regular)))
        pdfmetrics.registerFont(TTFont("SubjectBold", str(bold)))
        pdfmetrics.registerFontFamily("SubjectFont", normal="SubjectFont", bold="SubjectBold")
    styles = {
        "title": ParagraphStyle("S-Title", fontName="SubjectBold", fontSize=15, leading=21, spaceAfter=15),
        "chapter": ParagraphStyle("S-Chapter", fontName="SubjectBold", fontSize=12, leading=17, spaceBefore=11, spaceAfter=8),
        "heading": ParagraphStyle("S-Heading", fontName="SubjectBold", fontSize=10.7, leading=15, spaceBefore=9, spaceAfter=5),
        "body": ParagraphStyle("S-Body", fontName="SubjectFont", fontSize=10.3, leading=16, spaceAfter=7),
        "quote": ParagraphStyle("S-Quote", fontName="SubjectFont", fontSize=10, leading=15, leftIndent=14, spaceAfter=9),
    }
    return A4, SimpleDocTemplate, Paragraph, Spacer, PageBreak, styles


def inline(value):
    # Safe plain-text Markdown conversion; tags and links from private source are not executed.
    value = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", value)
    value = re.sub(r"<[^>]*>", "", value)
    value = h(value)
    value = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", value)
    value = re.sub(r"(?<!\*)\*([^*]+)\*(?!\*)", r"<i>\1</i>", value)
    return value


def article_story(source, tools):
    A4, Doc, P, Spacer, Break, st = tools
    story = []
    text = []
    def flush():
        if text:
            story.append(P(inline(" ".join(text)), st["body"]))
            text.clear()
    body = FRONT.sub("", source).replace("\r\n", "\n")
    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            flush()
        elif re.match(r"^#{1,6} ", line):
            flush()
            story.append(P(inline(re.sub(r"^#+\s*", "", line)), st["heading"]))
        elif line.startswith(">"):
            flush()
            story.append(P(inline(line.lstrip("> ")), st["quote"]))
        elif re.match(r"^(?:[-*] |\d+\. )", line):
            flush()
            story.append(P("• " + inline(re.sub(r"^(?:[-*] |\d+\. )", "", line)), st["body"]))
        elif line.startswith("|"):
            flush()
            if not re.fullmatch(r"[\s|:-]+", line):
                story.append(P(inline(" · ".join(x.strip() for x in line.strip("|").split("|"))), st["body"]))
        else:
            text.append(line)
    flush()
    return story


def create_pdf(path, model, rows, private, slug, level, tools):
    A4, Doc, P, Spacer, Break, st = tools
    path.parent.mkdir(parents=True, exist_ok=True)
    def footer(canvas, document):
        canvas.saveState()
        canvas.setFont("SubjectFont", 8)
        canvas.drawRightString(A4[0] - 48, 24, str(document.page))
        canvas.restoreState()
    doc = Doc(str(path), pagesize=A4, leftMargin=48, rightMargin=48,
              topMargin=48, bottomMargin=48, title=model["title"] + " — " + level.upper())
    story = [P(h(model["title"]), st["title"]),
             P(level.upper() + " — Госэкзамены 2027", st["body"])]
    if len(rows) > 1:
        story.append(P("Оглавление", st["heading"]))
        for row in rows:
            story.append(P("№%d — %s" % (row["official_number"], h(row["official_question"])), st["body"]))
        story.append(Break())
    for i, row in enumerate(rows):
        if i:
            story.append(Break())
        story.append(P("Вопрос №%d" % row["official_number"], st["chapter"]))
        story.append(P("<b>Официальная формулировка.</b> " + h(row["official_question"]), st["quote"]))
        if row.get("quality") != "approved":
            story.append(P("<b>РАБОЧАЯ РЕДАКЦИЯ.</b> " +
                           h(row.get("working_note", "Есть незакрытые источниковые замечания.")), st["quote"]))
        source = source_path(private, slug, row, level).read_text(encoding="utf-8")
        story.extend(article_story(source, tools))
    doc.build(story, onFirstPage=footer, onLaterPages=footer)
    if path.stat().st_size < 900:
        abort("Invalid PDF: " + str(path))


def build(private, public, dest, slugs, with_pdf):
    pdf_lib = pdf_tools() if with_pdf else None
    for slug in slugs:
        model, routes = read_model(private, public, slug)
        base = dest / "subjects" / slug
        base.mkdir(parents=True, exist_ok=True)
        (base / "index.md").write_text(page_markdown(model, routes), encoding="utf-8")
        if with_pdf:
            seen = set()
            canon = []
            for row in model["topics"]:
                if row["canonical_question"] not in seen:
                    canon.append(row)
                    seen.add(row["canonical_question"])
            for level in LEVELS:
                create_pdf(base / "pdf" / (level + ".pdf"), model, canon, private, slug, level, pdf_lib)
                for row in model["topics"]:
                    create_pdf(base / "pdf" / ("q%02d-%s.pdf" % (row["official_number"], level)),
                               model, [row], private, slug, level, pdf_lib)
    (dest / "subjects" / "index.md").write_text(catalog(slugs), encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("check", "build"))
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--public-root", type=Path, default=PUBLIC)
    parser.add_argument("--subjects", nargs="+", required=True, choices=tuple(SUBJECTS))
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--no-pdf", action="store_true", help="diagnostic only")
    args = parser.parse_args()
    private, public = args.private_root.resolve(), args.public_root.resolve()
    slugs = list(dict.fromkeys(args.subjects))
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
