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
    s = re.sub(r"(?m)[ \t]+$", "", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s

def numbered_only(folder: Path, check: bool, modified: list, errors: list) -> None:
    """Maintain exactly one canonical list: index.md, question numbers 1–25."""
    catalog = folder / "index.md"
    alias = folder / "numbers.md"
    index = catalog.read_text(encoding="utf-8")
    numbers = alias.read_text(encoding="utf-8")
    pattern = re.compile(r"\*\*\[№(\d+)\.")
    def correct_sequence(body: str) -> bool:
        return [int(x) for x in pattern.findall(body)] == list(range(1, 26))

    if correct_sequence(numbers):
        # The old generators produce a grouped index and a separate numeric copy.
        # Retain the original introductory notes, practice links and source caveats.
        first_group = re.search(r"(?m)^## ", index)
        if first_group is None:
            errors.append(f"{catalog}: missing section start")
            return
        intro = index[:first_group.start()]
        intro = re.sub(r"\[(?:Билеты )?[Пп]о номерам\]\(numbers\.html\)\s*·?\s*", "", intro)
        intro = re.sub(r"\n{3,}", "\n\n", intro).rstrip()
        first_question = re.search(r"\*\*\[№1\.", numbers)
        new_catalog = intro + "\n\n## Вопросы №1–25\n\n" + numbers[first_question.start():].rstrip() + "\n"
        heading = re.search(r"(?m)^# (.+)$", index)
        title = heading.group(1) if heading else "ФОС 2027"
        new_alias = (
            "---\nlayout: default\ntitle: Вопросы №1–25\n---\n\n"
            "# Вопросы №1–25\n\n"
            "**[Открыть единый перечень вопросов](index.html)**\n\n"
            "На странице предмета находятся все 25 вопросов в порядке официальных номеров.\n"
        )
    else:
        new_catalog, new_alias = index, numbers

    for path, original, updated in ((catalog, index, new_catalog), (alias, numbers, new_alias)):
        if original != updated:
            modified.append(path.as_posix())
            if not check:
                path.write_text(updated, encoding="utf-8")

    result = new_catalog
    if not correct_sequence(result):
        errors.append(f"{catalog}: question list is not exactly №1–25")
    if correct_sequence(new_alias):
        errors.append(f"{alias}: duplicate question list must not be exposed")
    if not re.search(r"\]\(index\.html\)", new_alias):
        errors.append(f"{alias}: missing canonical question-list link")
    if re.search(r"смысловой порядок|смысловым разделам|по разделам|смысловом порядке", result + new_alias, re.I):
        errors.append(f"{folder}: redundant thematic-order navigation survived")


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
    for slug in SUBJECTS:
        numbered_only(args.root / "subjects" / slug / "2027", args.check, modified, errors)
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
