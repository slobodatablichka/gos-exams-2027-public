#!/usr/bin/env python3
"""Read-only source and staged release control for six FOS-2027 subjects.

This verifies editorial structure, not theological truth or availability of remote books.
"""
import argparse
import json
import re
import sys
from pathlib import Path

SUBJECTS = ("nt", "ot", "oi", "rpc", "dogmatics", "liturgics")
LEVELS = ("l3", "l2", "l1")
FORM = re.compile(
    r"^\s*(?:>\s*)?\*\*(?:Официальный вопрос|Официальная формулировка)"
    r"(?:\.|:)\*\*\s*(?:[:.]\s*)?(.+?)\s*$", re.M
)
PRACTICAL_FORM = re.compile(r"^## Официальное задание\\s*\\n+(?:>\\s*)?(.+?)\\s*$", re.M)
URL = re.compile(r"\[([^]]+)\]\(([^)]+)\)")
PRODUCTION = re.compile(
    r"(?:source-texts/|\bCURRENT-STATE\.md\b|"
    r"\b(?:planning|research)/[^\s)]+\.(?:md|json|csv)|"
    r"\bэтап[а-я]* [1-9]\b|история редакции)",
    re.IGNORECASE
)

def normalized(s):
    return " ".join(s.split()).strip()

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("sources", "candidate"))
    ap.add_argument("--private-root", required=True, type=Path)
    ap.add_argument("--public-root", type=Path)
    ap.add_argument("--report", required=True, type=Path)
    ap.add_argument("--source-sha", default="")
    args = ap.parse_args()
    private = args.private_root
    model = json.loads((private / "planning/data/site-2027-questions.json").read_text(encoding="utf-8"))
    rows = {(x["subject_id"], int(x["number"])): x for x in model["questions"]}
    errors, warnings, details = [], [], []
    if len(rows) != 150:
        errors.append("Model has not exactly 150 unique questions")

    if args.mode == "sources":
        for slug in SUBJECTS:
            for n in range(1, 26):
                model_row = rows.get((slug, n))
                if model_row is None:
                    errors.append(f"{slug} q{n:02}: absent from 150-question model")
                    continue
                bodies = {}
                for lev in LEVELS:
                    name = f"materials/{slug}/2027/{lev}/q{n:02}.md"
                    path = private / name
                    if not path.is_file():
                        errors.append("Missing source: " + name)
                        continue
                    s = path.read_text(encoding="utf-8-sig")
                    if len(s.strip()) < 100:
                        errors.append("Empty/short source: " + name)
                    match = FORM.search(s)
                    if not match:
                        errors.append("Missing official question: " + name)
                    else:
                        text = normalized(match.group(1))
                        if not is_practical and text != normalized(model_row["official_question"]):
                            errors.append("Model/FOS text mismatch: " + name)
                    bodies[lev] = s
                    occurrences = PRODUCTION.findall(s)
                    if occurrences:
                        warnings.append({"path": name, "kind": "production_metadata_candidates",
                                         "examples": occurrences[:6], "count": len(occurrences)})
                    for label, dest in URL.findall(s):
                        if dest.startswith(("http://", "https://", "#", "mailto:", "/")):
                            continue
                        if "?" in dest:
                            dest = dest.split("?", 1)[0]
                        dest = dest.split("#", 1)[0]
                        if not dest.endswith(".md"):
                            continue
                        resolved = (path.parent / dest).resolve()
                        if not resolved.is_file():
                            warnings.append({"path": name, "kind": "missing_relative_markdown",
                                             "target": dest, "label": label})
                if len(bodies) == 3:
                    forms = [normalized(FORM.search(b).group(1)) for b in bodies.values()
                             if FORM.search(b)]
                    if len(forms) == 3 and len(set(forms)) != 1:
                        errors.append(f"{slug} q{n:02}: official variants differ")
                    if slug == "liturgics" and re.search(r"^\d+\. \*\*", bodies["l2"], re.M):
                        errors.append(f"Liturgics q{n:02} L2 remains a numbered plan")
                details.append({"subject": slug, "number": n, "levels_present": len(bodies)})
        if len(details) != 150:
            errors.append("Not all 150 questions audited")
    else:
        if args.public_root is None:
            ap.error("--public-root required for candidate")
        root = args.public_root
        try:
            from pypdf import PdfReader
        except ImportError:
            PdfReader = None
            warnings.append({"kind": "pypdf_unavailable", "message": "PDF pages not parsed"})
        for slug in SUBJECTS:
            base = root / f"subjects/{slug}/2027"
            manifest_path = base / "pdf-manifest.json"
            if not manifest_path.is_file():
                errors.append(f"{slug}: missing PDF manifest")
                continue
            manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
            if args.source_sha and manifest.get("source_sha") != args.source_sha:
                errors.append(f"{slug}: source SHA mismatch")
            pdfs = manifest.get("pdfs", [])
            if len(pdfs) != 78:
                errors.append(f"{slug}: expected 78 PDF manifest items, got {len(pdfs)}")
            for n in range(1, 26):
                for lev in LEVELS:
                    file = base / f"q{n:02}-{lev}.md"
                    if not file.is_file():
                        errors.append(f"Missing generated page: {file.relative_to(root)}")
            actual_pdf = sorted((base / "pdf").glob("*.pdf"))
            if len(actual_pdf) != 78:
                errors.append(f"{slug}: expected 78 actual PDF, got {len(actual_pdf)}")
            for item in pdfs:
                fp = base / item["file"]
                if not fp.is_file():
                    errors.append(f"Missing PDF {slug}: {item['file']}")
                    continue
                if fp.read_bytes()[:5] != b"%PDF-":
                    errors.append(f"Invalid PDF header {slug}: {item['file']}")
                if "bytes" in item and fp.stat().st_size != item["bytes"]:
                    errors.append(f"PDF length does not match manifest: {slug} {item['file']}")
            if PdfReader:
                for lev in LEVELS:
                    full = base / "pdf" / f"{lev}.pdf"
                    if full.is_file():
                        try:
                            reader = PdfReader(str(full))
                            if len(reader.pages) < 25:
                                errors.append(f"Too few collection PDF pages: {slug}/{lev}.pdf")
                        except Exception as exc:
                            errors.append(f"Unreadable collection PDF {slug}/{lev}.pdf: {exc}")
            details.append({"subject": slug, "questions": 25, "markdown": 75, "pdfs": len(actual_pdf),
                            "manifest_source_sha": manifest.get("source_sha")})

    report = {"mode": args.mode, "source_sha": args.source_sha,
              "checked_questions": len(details) if args.mode == "sources" else 150,
              "errors": errors, "warnings": warnings, "details": details,
              "result": "FAIL" if errors else "PASS_WITH_WARNINGS" if warnings else "PASS",
              "boundary": "Structural and editorial checks only; no primary-source theological verification"}
    args.report.parent.mkdir(parents=True, exist_ok=True)
    args.report.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{report['result']}: {args.mode}; {len(errors)} errors; {len(warnings)} warnings")
    for error in errors[:25]:
        print("ERROR:", error)
    for warning in warnings[:10]:
        print("NOTICE:", warning)
    return 1 if errors else 0

if __name__ == "__main__":
    sys.exit(main())
