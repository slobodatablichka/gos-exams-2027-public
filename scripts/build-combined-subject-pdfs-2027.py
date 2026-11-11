#!/usr/bin/env python3
"""One complete PDF per FOS-2027 subject: question 1 (L3,L2,L1), ..., 25.

Reuse the already approved per-question PDFs without changing academic content.
Generate a nested PDF bookmark tree: 25 questions x 3 levels.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
from pathlib import Path
from pypdf import PdfReader, PdfWriter

SUBJECTS = ("nt", "ot", "oi", "rpc", "dogmatics", "liturgics")
LEVELS = ("l3", "l2", "l1")
OUTPUT = "pdf/full-l3-l2-l1.pdf"
LINK = (
    "**Полный PDF-сборник L3+L2+L1:** "
    "[скачать все 25 вопросов подряд: №1 (L3, L2, L1) … №25 (L3, L2, L1)]"
    "(" + OUTPUT + ")"
)
SOURCE_SHA = "77a84e19e0fa2c3eb500c99bd85f3cf4e598e29b"


def complete_pdf(folder: Path, check_only: bool) -> dict:
    target = folder / OUTPUT
    expected_pages = 0
    sources = []
    for question in range(1, 26):
        for level in LEVELS:
            path = folder / "pdf" / f"q{question:02d}-{level}.pdf"
            if not path.is_file():
                raise ValueError(f"Missing {path}")
            reader = PdfReader(path, strict=True)
            pages = len(reader.pages)
            if pages < 1:
                raise ValueError(f"Empty {path}")
            expected_pages += pages
            sources.append((question, level, path, pages))

    if not check_only:
        writer = PdfWriter()
        writer.add_metadata({
            "/Title": f"Государственный экзамен 2027. {folder.parent.name}. L3, L2, L1 по номерам",
            "/Subject": "25 официальных вопросов: каждый №1–25, затем L3 → L2 → L1",
            "/Creator": "Госэкзамены — 2027",
        })
        # Merge all pages before adding outline destinations: bookmarks must
        # point to the final page objects, not unresolved forward references.
        for _, _, src, _ in sources:
            writer.append(src, import_outline=False)
        position = 0
        for number in range(1, 26):
            question_bookmark = writer.add_outline_item(
                f"Вопрос №{number}", position, bold=True
            )
            for i, level in enumerate(LEVELS):
                _, actual_level, src, length = sources[(number - 1) * 3 + i]
                assert actual_level == level
                writer.add_outline_item(level.upper(), position, parent=question_bookmark)
                position += length
        assert position == expected_pages
        target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("wb") as f:
            writer.write(f)
        writer.close()

    if not target.is_file() or not target.read_bytes().startswith(b"%PDF-"):
        raise ValueError(f"Combined PDF missing or corrupt: {target}")

    final = PdfReader(target, strict=True)
    if len(final.pages) != expected_pages:
        raise ValueError(f"Wrong combined page count: {target}: {len(final.pages)} != {expected_pages}")
    outline = final.outline
    if len(outline) != 50:
        raise ValueError(f"Expected 25 headings plus 25 nested arrays in {target}, got {len(outline)}")
    offset = 0
    for q in range(1, 26):
        root_item, children = outline[(q - 1) * 2:(q - 1) * 2 + 2]
        if root_item.title != f"Вопрос №{q}" or len(children) != 3:
            raise ValueError(f"Bad question bookmark: {q}, {target}")
        if final.get_destination_page_number(root_item) != offset:
            raise ValueError(f"Question {q} begins at wrong PDF page")
        for i, level in enumerate(LEVELS):
            _, _, individual, length = sources[(q - 1) * 3 + i]
            if children[i].title != level.upper():
                raise ValueError(f"Incorrect L3/L2/L1 order: {target} q{q}")
            if final.get_destination_page_number(children[i]) != offset:
                raise ValueError(f"Wrong bookmark page: {target} q{q} {level}")
            # Confirm original material survives: compare extracted text of each first page.
            original_text = PdfReader(individual).pages[0].extract_text()
            merged_text = final.pages[offset].extract_text()
            if original_text.strip() != merged_text.strip():
                raise ValueError(f"PDF text differs: {target} q{q} {level}")
            offset += length
    assert offset == expected_pages
    b = target.read_bytes()
    return {
        "file": OUTPUT,
        "pages": len(final.pages),
        "bytes": len(b),
        "sha256": hashlib.sha256(b).hexdigest(),
    }


def build(root: Path, *, check_only: bool) -> None:
    for slug in SUBJECTS:
        folder = root / "subjects" / slug / "2027"
        manifest_path = folder / "pdf-manifest.json"
        if not manifest_path.is_file():
            raise ValueError(f"No PDF manifest for {slug}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        if manifest["source_sha"] != SOURCE_SHA:
            raise ValueError(f"Different FOS source revision: {slug}")
        prior = [x for x in manifest["pdfs"] if x["file"] != OUTPUT]
        if len(prior) != 78 or len({e["file"] for e in prior}) != 78:
            raise ValueError(f"Expected 78 existing PDFs: {slug}")
        entry = complete_pdf(folder, check_only)
        index_file = folder / "index.md"
        source = index_file.read_text(encoding="utf-8")
        if not re.search(r"(?m)^\*\*PDF-сборники:\*\*.*$", source):
            raise ValueError(f"No subject PDF links in {slug}")
        # Link is always placed next to the three existing full-level collections.
        updated = re.sub(
            r"(?m)^(\*\*PDF-сборники:\*\*[^\n]*)$",
            lambda m: m.group(1) + "\n\n" + LINK,
            re.sub(r"(?m)^\*\*Полный PDF-сборник L3\+L2\+L1:\*\*[^\n]*\n{0,2}", "", source)
        )
        if updated.count(OUTPUT) != 1:
            raise ValueError(f"Full collection link not unique: {slug}")
        combined = dict(manifest, pdfs=prior + [entry])
        if check_only:
            if source != updated or manifest != combined:
                raise ValueError(f"PDF manifest or catalog not in sync: {slug}")
        else:
            index_file.write_text(updated, encoding="utf-8")
            manifest_path.write_text(
                json.dumps(combined, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
        print(f"PASS {slug}: 25 questions x L3,L2,L1; {entry['pages']} pages; 79 PDF files")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", required=True, type=Path)
    ap.add_argument("--check", action="store_true")
    args = ap.parse_args()
    build(args.root, check_only=args.check)
    print("PASS: 6 full combined PDFs, 25 ordered question groups per subject")

if __name__ == "__main__":
    main()
