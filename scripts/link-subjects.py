#!/usr/bin/env python3
"""Stage reversible subject-to-lesson navigation without publishing unfinished PDF links.

All 72 canonical articles x L3/L2/L1 retain their original URL, body and lesson controls.
The generated patch is applied to the website only together with verified subject PDFs.

Usage:
  python scripts/link-subjects.py --private-root PRIVATE --public-root PUBLIC --output-root STAGING
  python scripts/link-subjects.py --private-root PRIVATE --public-root PUBLIC --apply
"""
import argparse
import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SUBJECTS = ("nt", "ot", "dogmatics")
LEVELS = ("l3", "l2", "l1")
BEGIN = "<!-- subject-navigation:begin -->"
END = "<!-- subject-navigation:end -->"
URL_RE = re.compile(r'^sessions/\d{2}/q\d{2}(?:-[a-z]+)?-l[123]\.html$')
CSS_BEGIN = "/* subject-navigation:begin */"
CSS_END = "/* subject-navigation:end */"
HOME = "index.md"
MATERIALS = "materials/index.md"


def publisher():
    spec = importlib.util.spec_from_file_location(
        "subject_catalog", ROOT / "scripts" / "build-subjects.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def replace_managed(text, begin, end, content, *, marker=None):
    if (begin in text) != (end in text):
        raise ValueError("Incomplete managed block")
    if begin in text:
        start = text.index(begin)
        finish = text.index(end, start) + len(end)
        if text.count(begin) != 1 or text.count(end) != 1:
            raise ValueError("Duplicate managed navigation block")
        return text[:start] + begin + "\n" + content + "\n" + end + text[finish:]
    if marker is None or marker not in text:
        raise ValueError("Navigation insertion marker missing")
    return text.replace(marker, begin + "\n" + content + "\n" + end + "\n\n" + marker, 1)


def build_models(private, public):
    core = publisher()
    models = {}
    for slug in SUBJECTS:
        model, routes = core.read_model(private, public, slug)
        canonical = []
        seen = set()
        for row in model["topics"]:
            c = row["canonical_question"]
            if c not in seen:
                canonical.append(row)
                seen.add(c)
        if len(canonical) != {"nt": 25, "ot": 24, "dogmatics": 23}[slug]:
            raise ValueError("Unexpected canonical count " + slug)
        models[slug] = (model, routes, canonical)
    return models


def link_from_session(path):
    if not URL_RE.fullmatch(path):
        raise ValueError("Unsafe article route " + path)
    return "../../" + path


def subject_block(model, rows, index, row, level, route_for, aliases):
    slug = model["slug"]
    c = row["canonical_question"]
    group = aliases[c]
    label = "/".join("№%d" % n for n in group)
    topic_title = model["title"]
    anchor = group[0]
    stem = "../../subjects/" + slug + "/"
    parts = [
        '<nav class="exam-subject-nav" aria-label="Навигация по предмету">',
        '<p class="exam-subject-title">По предмету: <strong>' + topic_title +
        "</strong> · вопрос " + label + "</p>",
        '<div class="exam-subject-links">',
        '<a href="' + stem + 'index.html#meaning-q%02d">По учебнику</a>' % anchor,
        '<a href="' + stem + 'index.html#number-q%02d">По номеру билета</a>' % anchor,
        '<a href="' + stem + 'numbers.html#number-q%02d">Все 25 номеров</a>' % anchor,
        '<a href="../../subjects/index.html">Все предметы</a>',
        '</div>',
    ]
    neighbor_links = []
    if index > 0:
        prev = rows[index - 1]
        url = route_for[prev["canonical_question"]][level]
        neighbor_links.append(
            '<a href="' + link_from_session(url) + '">← ' +
            ("№%d" % prev["official_number"]) + "</a>")
    if index + 1 < len(rows):
        nxt = rows[index + 1]
        url = route_for[nxt["canonical_question"]][level]
        neighbor_links.append(
            '<a href="' + link_from_session(url) + '">' +
            ("№%d" % nxt["official_number"]) + ' →</a>')
    if neighbor_links:
        parts.extend(['<div class="exam-subject-neighbors">',
                      '<span>Следовать по учебнику:</span> ' + " · ".join(neighbor_links),
                      "</div>"])
    parts.append("</nav>")
    return "\n".join(parts)


def subject_patch(public, models):
    modified = {}
    count = 0
    for slug, (model, routes, rows) in models.items():
        aliases = {}
        route_for = {}
        for item in model["topics"]:
            c = item["canonical_question"]
            aliases.setdefault(c, []).append(item["official_number"])
        for item in rows:
            route_for[item["canonical_question"]] = routes[item["official_number"]]
        for i, row in enumerate(rows):
            for level in LEVELS:
                route = route_for[row["canonical_question"]][level]
                file = Path(route.replace(".html", ".md"))
                original = (public / file).read_text(encoding="utf-8")
                if '<nav class="exam-levels"' not in original:
                    raise ValueError("Existing lesson level switch missing: " + str(file))
                snippet = subject_block(model, rows, i, row, level, route_for, aliases)
                updated = replace_managed(
                    original, BEGIN, END, snippet, marker='<nav class="exam-levels"')
                if file in modified:
                    raise ValueError("Shared session article between subject catalogs")
                modified[file] = updated
                count += 1
    if count != 216:
        raise ValueError("Expected 216 article backlinks, got %d" % count)
    return modified


HOME_LINKS = ('**[Учебные материалы по предметам](subjects/index.html)** — '
              '[Новый Завет](subjects/nt/index.html) · '
              '[Ветхий Завет](subjects/ot/index.html) · '
              '[Догматика](subjects/dogmatics/index.html).\n\n'
              'Все вопросы можно изучать **по учебнику** или **по номерам 1–25**.')
MATERIALS_LINKS = ('## По предметам\n\n'
                   'Быстрый доступ: **[Все предметы](../subjects/index.html)** · '
                   '[Новый Завет](../subjects/nt/index.html) · '
                   '[Ветхий Завет](../subjects/ot/index.html) · '
                   '[Догматика](../subjects/dogmatics/index.html).\n\n'
                   'Переход по предметам не заменяет прежний список занятий.')


def catalog_patch(public):
    result = {}
    home = (public / HOME).read_text(encoding="utf-8")
    result[Path(HOME)] = replace_managed(
        home, BEGIN, END, HOME_LINKS, marker="## Подготовка к государственным экзаменам — 2027")
    materials = (public / MATERIALS).read_text(encoding="utf-8")
    result[Path(MATERIALS)] = replace_managed(
        materials, BEGIN, END, MATERIALS_LINKS, marker="## Первый круг")
    return result


CSS = """
.exam-subject-nav {margin:1rem 0 1.15rem;padding:.8rem 1rem;border:1px solid #d1dce3;border-radius:6px;background:#f6f9fb}
.exam-subject-title {margin:0 0 .45rem;font-size:.94rem;line-height:1.55}
.exam-subject-links {display:flex;gap:.45rem .9rem;flex-wrap:wrap;line-height:1.7}
.exam-subject-links a {display:inline-block}
.exam-subject-neighbors {margin-top:.5rem;padding-top:.45rem;border-top:1px solid #dbe3e9;font-size:.92rem}
@media(max-width:600px) {
 .exam-subject-nav {padding:.7rem}
 .exam-subject-links a {padding:.25rem .15rem}
}
""".strip()


def css_patch(public):
    file = Path("assets/css/style.scss")
    text = (public / file).read_text(encoding="utf-8")
    return {file: replace_managed(
        text, CSS_BEGIN, CSS_END, CSS,
        marker=".site-footer { display: none !important; }")}


def verify(original_root, patch, models):
    expected = 216 + 2 + 1
    if len(patch) != expected:
        raise ValueError("Expected 219 managed files, got %d" % len(patch))
    unique_urls = set()
    for slug, (model, routes, canon) in models.items():
        for row in canon:
            for level in LEVELS:
                route = routes[row["official_number"]][level]
                unique_urls.add(Path(route.replace(".html", ".md")))
    if len(unique_urls) != 216:
        raise ValueError("Duplicate route in backlink graph")
    for file, content in patch.items():
        original = (original_root / file).read_text(encoding="utf-8")
        begin, end = (CSS_BEGIN, CSS_END) if file.suffix == ".scss" else (BEGIN, END)
        if content.count(begin) != 1 or content.count(end) != 1:
            raise ValueError("Broken managed block in " + str(file))
        # The exact old article body must remain unchanged once the managed block is removed.
        stripped = re.sub(re.escape(begin) + r"\n.*?\n" + re.escape(end) + r"\n\n?",
                          "", content, count=1, flags=re.S)
        if begin not in original and stripped != original:
            raise ValueError("Existing content changed in " + str(file))
        if file in unique_urls:
            if not all(t in content for t in ("subjects/", "meaning-q", "number-q")):
                raise ValueError("Incomplete article backlink: " + str(file))
            if '<nav class="exam-levels"' not in content:
                raise ValueError("Existing L3/L2/L1 navigation damaged")
    return True


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--private-root", required=True, type=Path)
    p.add_argument("--public-root", default=ROOT, type=Path)
    p.add_argument("--output-root", type=Path)
    p.add_argument("--apply", action="store_true")
    args = p.parse_args(argv)
    if bool(args.output_root) == bool(args.apply):
        p.error("Choose exactly one of --output-root or --apply")
    private, public = args.private_root.resolve(), args.public_root.resolve()
    models = build_models(private, public)
    edits = {}
    edits.update(subject_patch(public, models))
    edits.update(catalog_patch(public))
    edits.update(css_patch(public))
    verify(public, edits, models)
    if args.apply:
        out = public
    else:
        out = args.output_root.resolve()
        if out.exists():
            raise ValueError("Refusing to overwrite staged patch directory")
    hashes = {}
    for name, content in sorted(edits.items()):
        target = out / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        hashes[str(name)] = hashlib.sha256(content.encode("utf-8")).hexdigest()
    manifest = {"source": "approved published session articles",
                "article_count": 216, "files_count": len(edits), "files": hashes}
    (out / "subject-navigation-manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("PASS: 216 lesson backlinks, 2 entry pages, 1 stylesheet; ",
          "APPLIED" if args.apply else "STAGED", out)
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (ValueError, OSError, KeyError) as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)
