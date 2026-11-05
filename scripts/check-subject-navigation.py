#!/usr/bin/env python3
"""Audit staged subject backlinks without relying on still-unpublished subject pages."""
import argparse
import json
import re
import sys
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

SUBJECTS = ("nt", "ot", "dogmatics")
EXPECTED = {"nt": 25, "ot": 24, "dogmatics": 23}
LEVELS = ("l3", "l2", "l1")
BEGIN = "<!-- subject-navigation:begin -->"
END = "<!-- subject-navigation:end -->"


class Anchors(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend([value for key, value in attrs if key == "href"])


def check(private, public, staged):
    manifest_file = staged / "subject-navigation-manifest.json"
    manifest = json.loads(manifest_file.read_text(encoding="utf-8"))
    paths = set(manifest["files"])
    if manifest["article_count"] != 216 or manifest["files_count"] != 219 or len(paths) != 219:
        raise ValueError("Incorrect staged navigation inventory")
    import hashlib
    for relative, digest in manifest["files"].items():
        p = Path(relative)
        if not (staged / p).is_file():
            raise ValueError("Missing patch file " + str(p))
        if hashlib.sha256((staged / p).read_bytes()).hexdigest() != digest:
            raise ValueError("Patch SHA-256 mismatch: " + str(p))
    page_files = [p for p in paths if re.fullmatch(r"sessions/\d{2}/q\d{2}(?:-[a-z]+)?-l[123]\.md", p)]
    if len(page_files) != 216:
        raise ValueError("Expected 216 L3/L2/L1 articles")
    counts = Counter()
    valid_routes = set()
    official = {}
    for slug in SUBJECTS:
        config = json.loads((private / "planning" / ("subject-order-" + slug + ".json")).read_text(encoding="utf-8"))
        rows = config["topics"]
        if len(rows) != 25 or len(set(r["topic_id"] for r in rows)) != EXPECTED[slug]:
            raise ValueError("Bad canonical model " + slug)
        official[slug] = {r["official_number"] for r in rows}
        for row in rows:
            for url in row["level_urls"].values():
                valid_routes.add(url)
                if row["session"] == 19 and row.get("canonical_question", row["official_number"]) == 23:
                    valid_routes.add("sessions/19/q23-%s-%s.html" % (slug, url[-7:-5]))
    for relative in sorted(page_files):
        counts[relative.rsplit("-", 1)[-1]] += 1
        source = (public / relative).read_text(encoding="utf-8")
        after = (staged / relative).read_text(encoding="utf-8")
        if after.count(BEGIN) != 1 or after.count(END) != 1:
            raise ValueError("Repeated/missing backlinks: " + relative)
        region = after.split(BEGIN, 1)[1].split(END, 1)[0]
        anchors = Anchors()
        anchors.feed(region)
        if not (5 <= len(anchors.links) <= 7):
            raise ValueError("Unexpected backlink count: " + relative)
        if not any("meaning-q" in x for x in anchors.links):
            raise ValueError("Missing semantic link: " + relative)
        if not any("number-q" in x for x in anchors.links):
            raise ValueError("Missing number link: " + relative)
        base = Path(relative).parent
        for url in anchors.links:
            part = urlsplit(url)
            if part.scheme or part.netloc or part.path.startswith("/"):
                raise ValueError("Unexpected absolute link: " + url)
            parts = []
            for value in (base / part.path).parts:
                if value == "..":
                    if not parts:
                        raise ValueError("Escaping site root: " + url)
                    parts.pop()
                elif value not in ("", "."):
                    parts.append(value)
            target = "/".join(parts)
            if target.startswith("subjects/"):
                pieces = target.split("/")
                if target == "subjects/index.html":
                    continue
                if len(pieces) < 3 or pieces[1] not in SUBJECTS or pieces[2] not in ("index.html", "numbers.html"):
                    raise ValueError("Nonexistent subject target: " + url)
                if part.fragment and not re.fullmatch(r"(meaning|number)-q\d{2}", part.fragment):
                    raise ValueError("Invalid subject anchor: " + url)
                if part.fragment:
                    n = int(part.fragment[-2:])
                    if n not in official[pieces[1]]:
                        raise ValueError("Missing official number anchor: " + url)
            elif target.startswith("sessions/"):
                if target.endswith("/index.html"):
                    if not (public / target.replace(".html", ".md")).is_file():
                        raise ValueError("Missing lesson index: " + target)
                elif target not in valid_routes and not (public / target.replace(".html", ".md")).is_file():
                    raise ValueError("Broken previous/next route: " + url)
            else:
                raise ValueError("Unexpected backlink destination: " + url)
        if "<nav class=\"exam-levels\"" not in source or "<nav class=\"exam-levels\"" not in after:
            raise ValueError("Legacy levels lost " + relative)
    if set(counts) != {"l1.md", "l2.md", "l3.md"} or any(v != 72 for v in counts.values()):
        raise ValueError("Incomplete levels: " + str(counts))
    for relative in ("index.md", "materials/index.md"):
        contents = (staged / relative).read_text(encoding="utf-8")
        for slug in SUBJECTS:
            if ("subjects/" + slug + "/index.html") not in contents:
                raise ValueError("Missing front-page link: " + relative + " -> " + slug)
    print("FINAL PASS: 216 backlink blocks, 72/72/72 levels, 2 entry pages, 1 CSS; all new links structurally valid")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--private-root", type=Path, required=True)
    parser.add_argument("--public-root", type=Path, required=True)
    parser.add_argument("--staged-root", type=Path, required=True)
    args = parser.parse_args()
    try:
        check(args.private_root, args.public_root, args.staged_root)
    except (ValueError, KeyError, OSError, json.JSONDecodeError) as ex:
        parser.exit(1, "ERROR: " + str(ex) + "\n")
