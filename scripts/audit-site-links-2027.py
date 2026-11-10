#!/usr/bin/env python3
"""Non-mutating inventory of user-facing site Markdown links, PDF and library URLs.

Output: inventory.json and links.csv under an optional report directory.
This is NOT an HTTP test; it checks repository paths, not deployed Pages.
"""
import argparse
import csv
import json
import re
from collections import Counter, defaultdict
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
SLUGS = ("nt", "ot", "oi", "rpc", "dogmatics", "liturgics")
OLD_RE = re.compile(r"^subjects/(nt|ot|oi|rpc|dogmatics|liturgics)/(?!2027/)")
CURRENT_RE = re.compile(r"^subjects/(nt|ot|oi|rpc|dogmatics|liturgics)/2027/")
EXCLUDE = {".git", ".github", "scripts", "tests", "planning"}
MD_LINK = re.compile(r"(?<!!)\[[^\]]*\]\(([^)]+)\)")
HTML_LINK = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""", re.I)
FULL_URL = re.compile(r"https?://[^\s<>\]\)\"']+")

def inventory(out):
    md_files = sorted(p for p in ROOT.rglob("*.md")
                      if not any(x in EXCLUDE for x in p.relative_to(ROOT).parts))
    all_pages = {p.relative_to(ROOT).as_posix() for p in md_files}
    all_files = {p.relative_to(ROOT).as_posix() for p in ROOT.rglob("*") if p.is_file() and ".git" not in p.parts}
    link_rows = []
    stats = Counter()
    groups = defaultdict(Counter)
    direct_books = set()
    source_targets = set()
    unresolved = []
    legacy_from_current = []
    for file in md_files:
        source = file.relative_to(ROOT).as_posix()
        srcgroup = "current_subject" if CURRENT_RE.match(source) else ("legacy_subject" if OLD_RE.match(source) else ("legacy_session" if source.startswith("sessions/") else "entry"))
        t = file.read_text(encoding="utf-8", errors="replace")
        links = [m.group(1).split(' "')[0].strip() for m in MD_LINK.finditer(t)]
        links += [m.group(1).strip() for m in HTML_LINK.finditer(t)]
        # HTML comments are ignored for link counting only when entirely removed.
        for raw in links:
            stats["links"] += 1
            groups[srcgroup]["links"] += 1
            if not raw or raw.startswith("#"):
                stats["local_fragment_or_empty"] += 1
                continue
            if any(k in raw for k in ("{{", "{%", "}}", "%}")):
                stats["template_dynamic"] += 1
                continue
            parsed = urlsplit(raw)
            if parsed.scheme in ("http", "https"):
                stats["external"] += 1
                if parsed.netloc == "library.logoscosmos.org":
                    stats["library_links"] += 1
                    source_targets.add(raw)
                    if parsed.path.endswith("/index.html") and not parsed.fragment:
                        stats["library_book_index_no_section"] += 1
                        direct_books.add(raw)
                    elif parsed.fragment:
                        stats["library_fragment"] += 1
                    else:
                        stats["library_other_path"] += 1
                    kind = "library"
                else:
                    kind = "external_other"
                link_rows.append([source, raw, kind, "", "not_http_checked"])
                continue
            if raw.startswith(("mailto:", "tel:", "javascript:", "data:")):
                stats["other_scheme"] += 1
                continue
            if parsed.scheme or parsed.netloc:
                stats["unhandled_uri"] += 1
                continue
            rel = unquote(parsed.path)
            if not rel:
                stats["local_fragment_or_empty"] += 1
                continue
            target = (ROOT / rel.lstrip("/")) if rel.startswith("/") else (file.parent / rel)
            # Some links may deliberately point above repository root: report them.
            norm = target.resolve()
            try:
                dest = norm.relative_to(ROOT.resolve()).as_posix()
            except ValueError:
                dest = f"OUTSIDE_REPO:{raw}"
            if dest.endswith(".html"):
                expected = dest[:-5] + ".md"
                candidates = [expected, dest, dest[:-5] + "/index.md"]
            elif dest.endswith("/"):
                candidates = [dest + "index.md", dest + "index.html"]
            else:
                candidates = [dest, dest + ".md", dest + "/index.md"]
            exists = any(p in all_files for p in candidates)
            kind = "legacy_session" if dest.startswith("sessions/") else ("legacy_subject" if OLD_RE.match(dest) else ("current_subject" if CURRENT_RE.match(dest) else "other_internal"))
            if kind.startswith("legacy") and srcgroup in ("current_subject", "entry"):
                stats["legacy_links_from_current_or_entry"] += 1
                if len(legacy_from_current) < 80:
                    legacy_from_current.append({"from": source, "to": dest})
            if exists:
                stats["internal_existing_files"] += 1
            else:
                stats["internal_not_resolved"] += 1
                if len(unresolved) < 200:
                    unresolved.append({"from": source, "link": raw, "resolved": dest})
            link_rows.append([source, raw, kind, dest, "file_present" if exists else "not_resolved"])
    pdfs = sorted(p for p in ROOT.rglob("*.pdf") if "planning" not in p.parts)
    bad_pdf = [p.relative_to(ROOT).as_posix() for p in pdfs if p.open("rb").read(5) != b"%PDF-"]
    stats["markdown_pages"] = len(md_files)
    stats["pdf_files"] = len(pdfs)
    stats["pdf_bad_signature"] = len(bad_pdf)
    current = {}
    for s in SLUGS:
        p = ROOT / "subjects" / s / "2027"
        md = list(p.glob("q??-l?.md"))
        pf = list((p / "pdf").glob("*.pdf"))
        names = {q.name for q in md}
        missing = [f"q{n:02d}-l{k}.md" for n in range(1, 26) for k in (1, 2, 3) if f"q{n:02d}-l{k}.md" not in names]
        current[s] = {"answer_pages": len(md), "missing_answer_files": missing, "pdf": len(pf),
                      "has_index": (p / "index.md").is_file(),
                      "has_numbers": (p / "numbers.md").is_file()}
    summary = {"method": "GitHub repository contents at checked-out commit; no HTTP request",
               "counts": dict(stats), "groups": {k: dict(v) for k, v in groups.items()},
               "current_subjects": current,
               "unique_library_urls": len(source_targets),
               "unique_unsectioned_library_book_urls": len(direct_books),
               "unresolved_links_sample": unresolved,
               "legacy_links_from_current_sample": legacy_from_current,
               "bad_pdf_signatures": bad_pdf}
    out.mkdir(parents=True, exist_ok=True)
    (out / "inventory.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    with (out / "links.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f); w.writerow(["source", "raw_url", "kind", "resolved_repo_path", "repository_check"])
        w.writerows(link_rows)
    print("=== Site link inventory (REPOSITORY FILES; NOT LIVE HTTP) ===")
    print(json.dumps({"counts": summary["counts"], "current_subjects": current,
                      "unique_library_urls": summary["unique_library_urls"],
                      "unique_unsectioned_library_book_urls": summary["unique_unsectioned_library_book_urls"]},
                     ensure_ascii=False, indent=2))
    print("UNRESOLVED SAMPLE:", json.dumps(unresolved[:15], ensure_ascii=False))
    print("LEGACY FROM CURRENT SAMPLE:", json.dumps(legacy_from_current[:15], ensure_ascii=False))
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, default=Path("site-inventory-report"))
    opts = parser.parse_args()
    inventory(opts.out)
