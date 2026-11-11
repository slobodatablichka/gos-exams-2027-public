#!/usr/bin/env python3
"""Validate usable global return navigation on every rendered FOS-2027 page."""
from html.parser import HTMLParser
from pathlib import Path
import argparse

SUBJECTS = ("nt", "ot", "oi", "rpc", "dogmatics", "liturgics")

class NavLinks(HTMLParser):
    def __init__(self):
        super().__init__()
        self.depth = 0
        self.navs = []
        self.current = None
        self.in_nav = False

    def handle_starttag(self, tag, attrs):
        props = dict(attrs)
        if tag == "nav" and "exam-global-nav" in props.get("class", "").split():
            self.in_nav = True
            self.current = []
        elif tag == "a" and self.in_nav:
            self.current.append(props.get("href", ""))

    def handle_endtag(self, tag):
        if tag == "nav" and self.in_nav:
            self.navs.append(self.current)
            self.current = None
            self.in_nav = False

def check(path, slug=None):
    html = path.read_text(encoding="utf-8")
    parser = NavLinks()
    parser.feed(html)
    if len(parser.navs) != 2:
        raise ValueError(f"{path}: two navigation bars required, found {len(parser.navs)}")
    for links in parser.navs:
        if not any(x.endswith("/index.html") and "/subjects/" not in x and "/materials/" not in x for x in links):
            raise ValueError(f"{path}: missing return to main homepage")
        if not any(x.endswith("/subjects/index.html") for x in links):
            raise ValueError(f"{path}: missing all-subjects link")
        if slug is not None and not any(x.endswith(f"/subjects/{slug}/2027/index.html") for x in links):
            raise ValueError(f"{path}: missing current subject/question-list link")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--built-site", required=True, type=Path)
    args = ap.parse_args()
    root = args.built_site
    checked = []
    for p in ("index.html", "subjects/index.html", "materials/index.html"):
        path = root / p
        if not path.is_file():
            raise ValueError(f"missing public entrypoint {p}")
        check(path)
        checked.append(path)
    for slug in SUBJECTS:
        folder = root / "subjects" / slug / "2027"
        pages = sorted(folder.rglob("*.html"))
        assert len(pages) >= 77, f"{slug}: not all question pages or indexes"
        for path in pages:
            check(path, slug=slug)
            checked.append(path)
    print(f"PASS: top and bottom return navigation validated on {len(checked)} rendered pages")
    print("PASS: Main / All Subjects / Current Subject routes present on every subject page")

if __name__ == "__main__":
    main()
