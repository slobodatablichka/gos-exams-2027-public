#!/usr/bin/env python3
"""Stage-5 offline release acceptance for 3 subjects. Does NOT publish.

Input: staged-site assembled from old public tree, generated subjects/PDF,
and the 219 managed backlink/header/CSS files.
Strictly verify all 75 official numbers, 72 unique manuscripts, 225 PDFs,
216 reverse links, 9 full PDF books, and historical article paths.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import posixpath
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

SLUGS = ("nt", "ot", "dogmatics")
CANONICAL = {"nt": 25, "ot": 24, "dogmatics": 23}
LEVELS = ("l3", "l2", "l1")
HTML_ROUTE = re.compile(r"^sessions/\d{2}/q\d{2}(?:-[a-z]+)?-l[123]\.html$")
MD_LINKS = re.compile(r"\]\(([^)\s]+)(?:\s+['\"][^)]*['\"])?\)")
NAV_START, NAV_END = "<!-- subject-navigation:begin -->", "<!-- subject-navigation:end -->"


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.hrefs = []
        self.ids = set()

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and "href" in attrs:
            self.hrefs.append(attrs["href"])


def fail(msg):
    raise ValueError(msg)


def md_for_url(root, route):
    if not route.endswith(".html") or not (route == "index.html" or route.startswith(("sessions/", "subjects/", "materials/"))):
        fail("Invalid internal route: " + route)
    md = root / route[:-5] / "index.md" if route.endswith("/index.html") else root / (route[:-5] + ".md")
    if route.endswith("/index.html"):
        md = root / (route[:-5] + ".md")
    if not md.is_file():
        fail("Missing linked site source: " + route)
    return md


def resolve_link(source_file, href, stage):
    part = urlsplit(href)
    if part.scheme or part.netloc or href.startswith(("#", "mailto:", "tel:", "//")):
        return None
    if "%" in part.path:
        route = unquote(part.path)
    else:
        route = part.path
    if not route or route.startswith("/"):
        return None
    source = source_file.relative_to(stage).as_posix()
    resolved = posixpath.normpath(posixpath.join(posixpath.dirname(source), route))
    if resolved.startswith("../") or resolved == "..":
        fail("Link escapes public site: " + source + " -> " + href)
    if route.endswith(".html"):
        actual = md_for_url(stage, resolved)
    elif route.endswith(".pdf"):
        actual = stage / resolved
        if not actual.is_file():
            fail("Broken PDF link: " + source + " -> " + href)
    elif route.endswith(".md"):
        actual = stage / resolved
        if not actual.is_file():
            fail("Missing Markdown link: " + source + " -> " + href)
    else:
        fail("Unknown generated link format: " + source + " -> " + href)
    if part.fragment and actual.suffix == ".md":
        content = actual.read_text(encoding="utf-8")
        # Generated subject anchors are explicit HTML IDs.
        if resolved.startswith("subjects/") and not (part.fragment in content):
            fail("Missing subject fragment: " + resolved + "#" + part.fragment)
    return resolved


def original_unchanged(old_text, new_text, filename):
    if filename == "assets/css/style.scss":
        begin, end = "/* subject-navigation:begin */", "/* subject-navigation:end */"
    else:
        begin, end = NAV_START, NAV_END
    if new_text.count(begin) != 1 or new_text.count(end) != 1:
        fail("Missing managed block: " + filename)
    stripped = re.sub(re.escape(begin) + r"\n.*?\n" + re.escape(end) + r"\n\n?",
                      "", new_text, count=1, flags=re.S)
    if stripped != old_text:
        fail("Original site content modified outside managed block: " + filename)


def check(stage, original, private, output=None):
    counts = Counter()
    routes = set()
    unique_articles = set()
    input_manuscripts = set()
    all_targets = set()
    total_pdf = 0
    report = {"subjects": {}, "pdf_files": 0, "article_backlinks": 0,
              "entry_pages": 2, "legacy_preserved": True}
    for slug in SLUGS:
        model = json.loads((private / "planning" / ("subject-order-" + slug + ".json"))
                           .read_text(encoding="utf-8"))
        topics = model["topics"]
        if len(topics) != 25 or sorted(row["official_number"] for row in topics) != list(range(1, 26)):
            fail("Incomplete official question numbering: " + slug)
        if len({row["canonical_question"] for row in topics}) != CANONICAL[slug]:
            fail("Incorrect number of original manuscripts: " + slug)
        folder = stage / "subjects" / slug
        for page in ("index.md", "numbers.md"):
            file = folder / page
            if not file.is_file():
                fail("Missing subject page " + str(file))
            txt = file.read_text(encoding="utf-8")
            parser = Links()
            parser.feed(txt)
            for n in range(1, 26):
                if page == "index.md":
                    for prefix in ("meaning", "number"):
                        if "%s-q%02d" % (prefix, n) not in parser.ids:
                            fail("Missing question ID: %s/%s #%d" % (slug, prefix, n))
                elif "number-q%02d" % n not in parser.ids:
                    fail("Missing numeric-only anchor: " + slug + " #" + str(n))
            if page == "index.md" and (
                'data-sort-panel="meaning"' not in txt or 'data-sort-panel="number"' not in txt
            ):
                fail("Incomplete sort control " + slug)
            for url in parser.hrefs + MD_LINKS.findall(txt):
                resolved = resolve_link(file, url, stage)
                if resolved:
                    all_targets.add(resolved)
        manifest = json.loads((folder / "pdf-manifest.json").read_text(encoding="utf-8"))
        expected_pdf = (CANONICAL[slug] + 1) * 3
        if manifest["pdf_count"] != expected_pdf or len(manifest["files"]) != expected_pdf:
            fail("Wrong PDF count " + slug)
        full_count = sum(x["kind"] == "subject" for x in manifest["files"])
        if full_count != 3:
            fail("Not exactly 3 full collection PDF " + slug)
        for record in manifest["files"]:
            file = folder / record["file"]
            if not file.is_file():
                fail("Missing declared PDF " + str(file))
            if file.stat().st_size != record["bytes"]:
                fail("Changed PDF length " + str(file))
            if hashlib.sha256(file.read_bytes()).hexdigest() != record["sha256"]:
                fail("Changed PDF checksum " + str(file))
        if set(p.relative_to(folder).as_posix() for p in (folder / "pdf").glob("*.pdf")) != {
            item["file"] for item in manifest["files"]
        }:
            fail("Unlisted PDFs " + slug)
        total_pdf += expected_pdf
        for row in topics:
            canon = row.get("canonical_question", row["official_number"])
            for level in LEVELS:
                manuscript = private / "materials" / slug / level / ("q%02d.md" % canon)
                if not manuscript.is_file() or not manuscript.read_text(encoding="utf-8").strip():
                    fail("Missing manuscript: " + str(manuscript))
                input_manuscripts.add(manuscript)
                url = row["level_urls"][level]
                if not HTML_ROUTE.fullmatch(url):
                    fail("Invalid article link " + str(url))
                if not (stage / url.replace(".html", ".md")).is_file():
                    fail("Article route not found " + url)
                routes.add(url)
                unique_articles.add(url)
            if row["quality"] != "approved":
                if row["site"] != "published_working" or not row.get("working_notice_url"):
                    fail("Unapproved manuscript without warning: " + slug)
                pdf = folder / "pdf" / ("q%02d-l3.pdf" % canon)
                if not pdf.is_file():
                    fail("Working manuscript PDF missing")
                page = (folder / "index.md").read_text(encoding="utf-8")
                if "Рабочая редакция" not in page:
                    fail("Working edition warning hidden on site")
        counts[slug] = len(topics)
        report["subjects"][slug] = {"official": 25, "canonical": CANONICAL[slug],
                                     "pdf": expected_pdf}
    if len(routes) != 216 or len(input_manuscripts) != 216:
        fail("Missing canonical L1/L2/L3 content: %d routes and %d inputs" %
             (len(routes), len(input_manuscripts)))
    if total_pdf != 225:
        fail("PDF inventory should contain 225 files, got " + str(total_pdf))
    report["pdf_files"] = total_pdf

    for url in unique_articles:
        mdpath = url.replace(".html", ".md")
        original_file = original / mdpath
        staged_file = stage / mdpath
        if not original_file.is_file():
            fail("Old public URL not preserved: " + url)
        raw = original_file.read_text(encoding="utf-8")
        updated = staged_file.read_text(encoding="utf-8")
        original_unchanged(raw, updated, mdpath)
        parser = Links()
        region = updated.split(NAV_START)[1].split(NAV_END)[0]
        parser.feed(region)
        if not any("meaning-q" in x for x in parser.hrefs):
            fail("No semantic return: " + url)
        if not any("number-q" in x for x in parser.hrefs):
            fail("No numeric return: " + url)
        for target in parser.hrefs:
            resolved = resolve_link(staged_file, target, stage)
            if resolved:
                all_targets.add(resolved)
        report["article_backlinks"] += 1

    for p in ("index.md", "materials/index.md", "assets/css/style.scss"):
        original_unchanged((original / p).read_text(encoding="utf-8"),
                           (stage / p).read_text(encoding="utf-8"), p)
    for p in ("index.md", "materials/index.md"):
        file = stage / p
        for slug in SLUGS:
            if ("subjects/" + slug + "/index.html") not in file.read_text(encoding="utf-8"):
                fail("Missing entry point: " + p + " " + slug)
        for link in MD_LINKS.findall(file.read_text(encoding="utf-8")):
            if "subjects/" in link:
                resolve_link(file, link, stage)

    if report["article_backlinks"] != 216:
        fail("Article backlink count mismatch")
    report["generated_references_resolved"] = len(all_targets)
    report["status"] = "PASS"
    if output:
        Path(output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("FINAL PASS: 3 subjects, 75 official positions, 72 manuscripts, "
          "225 PDFs, 216 backlinks, 9 PDF books, %d linked targets" % len(all_targets))
    return report


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--stage", required=True, type=Path)
    p.add_argument("--original", required=True, type=Path)
    p.add_argument("--private", required=True, type=Path)
    p.add_argument("--report", type=Path)
    args = p.parse_args()
    check(args.stage, args.original, args.private, args.report)


if __name__ == "__main__":
    try:
        main()
    except (ValueError, OSError, KeyError, json.JSONDecodeError) as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)
