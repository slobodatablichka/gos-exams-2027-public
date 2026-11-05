#!/usr/bin/env python3
"""Validate actual Jekyll HTML of the staged subject release, not just Markdown."""
import argparse
import posixpath
import re
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

SUBJECTS = ("nt", "ot", "dogmatics")
LEVELS = ("l3", "l2", "l1")


class Page(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = set()
        self.links = []
        self.buttons = 0

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if "id" in attrs:
            self.ids.add(attrs["id"])
        if tag == "a" and attrs.get("href"):
            self.links.append(attrs["href"])
        if tag == "button" and attrs.get("data-sort-button"):
            self.buttons += 1


def check(root):
    def read(name):
        file = root / name
        if not file.is_file():
            raise ValueError("HTML not rendered: " + name)
        parser = Page()
        parser.feed(file.read_text(encoding="utf-8"))
        return parser

    catalogue = read("subjects/index.html")
    for slug in SUBJECTS:
        if (slug + "/index.html") not in catalogue.links:
            raise ValueError("Missing subject in compiled catalog: " + slug)
    for name in ("index.html", "materials/index.html"):
        page = read(name)
        for slug in SUBJECTS:
            if not any(("subjects/" + slug + "/index.html") in url for url in page.links):
                raise ValueError("Missing subject from " + name + ": " + slug)
    pages = 0
    matched = set()
    for slug in SUBJECTS:
        listing = read("subjects/" + slug + "/index.html")
        numeric = read("subjects/" + slug + "/numbers.html")
        if listing.buttons < 2:
            raise ValueError("Sorting buttons absent in rendered site " + slug)
        for n in range(1, 26):
            if "meaning-q%02d" % n not in listing.ids or "number-q%02d" % n not in listing.ids:
                raise ValueError("Missing dual anchors on " + slug + " #" + str(n))
            if "number-q%02d" % n not in numeric.ids:
                raise ValueError("Missing numerical anchor " + slug + " #" + str(n))
        for listing_name, entry in (("index.html", listing), ("numbers.html", numeric)):
            path = "subjects/" + slug + "/" + listing_name
            for link in entry.links:
                part = urlsplit(link)
                if part.scheme or part.netloc or not part.path:
                    continue
                if part.path.startswith("/"):
                    # Root-absolute Jekyll-managed assets are outside article navigation.
                    continue
                rel = posixpath.normpath(posixpath.join(posixpath.dirname(path), part.path))
                if rel.startswith("../"):
                    raise ValueError("Unsafe relative URL " + path + " -> " + link)
                destination = root / rel
                if rel.endswith((".html", ".pdf")) and not destination.is_file():
                    raise ValueError("Broken compiled link: " + path + " -> " + link)
                if rel.startswith("sessions/") and rel.endswith(".html"):
                    matched.add(rel)
                pages += 1
        for level in LEVELS:
            pdf = root / "subjects" / slug / "pdf" / (level + ".pdf")
            if not pdf.is_file():
                raise ValueError("Full PDF absent after Jekyll build: " + str(pdf))
    if len(matched) != 216:
        raise ValueError("Rendered subject links cover only %d / 216 original articles" % len(matched))
    for file in matched:
        page = read(file)
        if not any("subjects/" in url and "#meaning-q" in url for url in page.links):
            raise ValueError("Rendered article missing semantic backlink " + file)
        if not any("subjects/" in url and "#number-q" in url for url in page.links):
            raise ValueError("Rendered article missing numeric backlink " + file)
    print("PASS JEKYLL: 3 subject pages, 3 numeric lists, all 75 dual anchors, "
          "216 linked legacy articles and their reverse links, %d checked anchors/files" % pages)


if __name__ == "__main__":
    a = argparse.ArgumentParser()
    a.add_argument("root", type=Path)
    args = a.parse_args()
    try:
        check(args.root)
    except (ValueError, OSError) as error:
        print("ERROR:", error, file=sys.stderr)
        sys.exit(1)
