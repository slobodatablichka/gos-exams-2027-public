#!/usr/bin/env python3
"""Gate for all subject PDF files, canonical aliases, and generated download links."""
import argparse
import hashlib
import json
import re
from pathlib import Path
from pypdf import PdfReader

REQUIRED = {"nt": 25, "ot": 24, "dogmatics": 23, "oi": 25, "rpc": 25, "liturgics": 25}
LEVELS = ("l3", "l2", "l1")
DOWNLOAD = re.compile(r'href="(pdf/[^"]+\.pdf)"')


def verify(root, subjects):
    total = 0
    for slug in subjects:
        folder = root / slug
        manifest_path = folder / "pdf-manifest.json"
        if not manifest_path.is_file():
            raise ValueError("Missing PDF manifest: " + str(manifest_path))
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        expected = 3 * (REQUIRED[slug] + 1)
        if manifest["pdf_count"] != expected or manifest["canonical_count"] != REQUIRED[slug]:
            raise ValueError("Unexpected PDF inventory for " + slug)
        entries = manifest["files"]
        if len(entries) != expected:
            raise ValueError("Incomplete PDF manifest " + slug)
        paths = []
        for record in entries:
            file = folder / record["file"]
            if not file.is_file() or file.stat().st_size != record["bytes"]:
                raise ValueError("Missing or size-mismatched PDF: " + str(file))
            if hashlib.sha256(file.read_bytes()).hexdigest() != record["sha256"]:
                raise ValueError("PDF digest does not match manifest: " + str(file))
            if not file.read_bytes().startswith(b"%PDF-"):
                raise ValueError("Invalid PDF signature " + str(file))
            paths.append(str(file.relative_to(folder)))
        if len(set(paths)) != expected:
            raise ValueError("Same PDF counted twice " + slug)
        pdfs_on_disk = sorted(str(p.relative_to(folder)) for p in (folder / "pdf").glob("*.pdf"))
        if sorted(paths) != pdfs_on_disk:
            raise ValueError("Unlisted/stale PDFs in " + slug)
        # Every generated link must target an existing PDF, including aliases.
        links = []
        for name in ("index.md", "numbers.md"):
            file = folder / name
            if not file.is_file():
                raise ValueError("Subject page missing: " + str(file))
            text = file.read_text(encoding="utf-8")
            links += DOWNLOAD.findall(text)
            for n in range(1, 26):
                if ("№%d" % n) not in text and ("№%02d" % n) not in text:
                    raise ValueError("Ticket number absent on subject page: " + str(n))
        for link in links:
            if not (folder / link).is_file():
                raise ValueError("Broken subject PDF link: " + slug + " / " + link)
        for level in LEVELS:
            full = folder / "pdf" / (level + ".pdf")
            reader = PdfReader(str(full), strict=True)
            if not reader.outline:
                raise ValueError("No clickable chapter outline: " + str(full))
            if len(reader.pages) < 2:
                raise ValueError("No actual full manuscript: " + str(full))
            first = " ".join((p.extract_text() or "") for p in reader.pages[:3])
            if "Указатель официальных номеров" not in first or "Оглавление" not in first:
                raise ValueError("Contents/index missing: " + str(full))
        print("PASS", slug, expected, "PDF files; references", len(links))
        total += expected
    if total != sum(3 * (REQUIRED[k] + 1) for k in subjects):
        raise ValueError("Total mismatch")
    print("FINAL PASS", total, "PDF files")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("root", type=Path)
    parser.add_argument("--subjects", nargs="+", required=True, choices=tuple(REQUIRED))
    args = parser.parse_args()
    try:
        verify(args.root, args.subjects)
    except (OSError, KeyError, ValueError) as e:
        parser.exit(1, "ERROR: " + str(e) + "\n")
