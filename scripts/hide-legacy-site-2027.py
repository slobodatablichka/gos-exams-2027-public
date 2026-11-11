#!/usr/bin/env python3
"""Remove hyperlinks to earlier exam solutions from all public FOS-2027 pages.

Historical sources stay in Git; Jekyll _config.yml excludes them from Pages.
"""
from pathlib import Path
import argparse
import re

SUBJECTS = ("nt", "ot", "oi", "rpc", "dogmatics", "liturgics")
LINK = re.compile(r"\[([^\]\n]+)\]\(([^)\n]+)\)")
OLD_SUBJECT_LINK = re.compile(
    r"(?:[ \t]*·[ \t]*)?\[[^\]\n]*\]\(\.\./index\.html\)"
    r"(?:[ \t]+сохранены\.)?", re.I
)
OLD_SESSION_LINK = re.compile(
    r"\[[^\]\n]+\]\([^)\n]*sessions/\d{2}/[^)\n]*\)", re.I
)

def clean(s: str, in_subject_root: bool) -> str:
    if in_subject_root:
        s = OLD_SUBJECT_LINK.sub("", s)
        s = re.sub(r"(?m)[ \t]+сохранены\.(?=[ \t]*$)", "", s)
    s = OLD_SESSION_LINK.sub("", s)
    s = re.sub(r"(?m)[ \t]+·[ \t]*$", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    errors, modified = [], []
    for slug in SUBJECTS:
        folder = args.root / "subjects" / slug / "2027"
        assert folder.is_dir(), "Missing official subject: " + slug
        for path in sorted(folder.rglob("*.md")):
            original = path.read_text(encoding="utf-8")
            new = clean(original, path.parent == folder)
            if new != original:
                modified.append(path.relative_to(args.root).as_posix())
                if not args.check:
                    path.write_text(new, encoding="utf-8")
            output = original if args.check else new
            for _, target in LINK.findall(output):
                if re.search(r"(?:^|/)sessions/\d{2}/", target):
                    errors.append(f"{path}: archived session link: {target}")
                if path.parent == folder and target.split("#")[0] == "../index.html":
                    errors.append(f"{path}: archived subject link")
                if re.search(
                    r"(?:^|/)subjects/(?:nt|ot|oi|rpc|dogmatics|liturgics)"
                    r"/(?:index|numbers)\.html|"
                    r"(?:^|/)subjects/(?:nt|ot|oi|rpc|dogmatics|liturgics)/pdf/",
                    target
                ):
                    errors.append(f"{path}: archived question-bank link: {target}")
    print(f"FOS-2027 cleanup: {len(modified)} changed files")
    if args.check and modified:
        errors += ["Pending cleanup: " + p for p in modified]
    if errors:
        for e in errors[:45]:
            print("ERROR:", e)
        raise SystemExit(1)
    print("PASS: no links to older exam solutions in official FOS-2027 pages")

if __name__ == "__main__":
    main()
