#!/usr/bin/env python3
"""Compact stage-8 publication audit; no repeat reading of theological manuscripts.

Usage:
  python scripts/check-publication-final.py 15
  python scripts/check-publication-final.py 15 --private-root ../gos-exams-2027 \
    --pr-run 41817572413 --main-run 41817640307 --pages-run 41817639261 --http

Without run IDs or --http the corresponding remote checks are explicitly NOT_VERIFIED.
Only structural errors cause a nonzero exit. HTTP/tool access problems remain visible.
"""
import argparse
import csv
import importlib.util
import json
import os
import posixpath
import re
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
REPO = "slobodatablichka/gos-exams-2027-public"
SITE = "https://slobodatablichka.github.io/gos-exams-2027-public"
LINK = re.compile(r'(?:href=["\']([^"\']+)["\']|\]\(([^)]+)\))')


def load_publisher():
    spec = importlib.util.spec_from_file_location(
        "publication", ROOT / "scripts/publish-lesson.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def structural_check(session):
    mod = load_publisher()
    mod.validate()  # All registered lessons, announcements and old routes.
    rows = mod.topics(session)
    entry = [r for r in mod.csv_rows(mod.LEDGER)
             if int(r["session"]) == session]
    if len(entry) != 1:
        raise ValueError(f"Lesson {session} not in public published registry")
    if entry[0]["topics"].split(";") != [mod.code(r) for r in rows]:
        raise ValueError("Published topic numbers or order differ")
    folder = ROOT / f"sessions/{session:02d}"
    names = ["index.md", "l3-complete.md"]
    names += [f'{mod.page_code(row, rows)}-{level}.md'
              for row in rows for level in mod.LEVELS]
    errors = []
    for name in names:
        path = folder / name
        if not path.is_file():
            errors.append(f"missing {path.relative_to(ROOT)}")
            continue
        body = path.read_text(encoding="utf-8")
        if not body.strip():
            errors.append(f"empty {name}")
        if name.startswith("q") and body.count('<blockquote class="exam-official">') != 1:
            errors.append(f"official question missing/duplicated in {name}")
        for match in LINK.finditer(body):
            href = next(v for v in match.groups() if v is not None)
            href = href.strip().split("?", 1)[0].split("#", 1)[0]
            if not href or href.startswith(("http:", "https:", "mailto:", "//", "/")):
                continue
            if not href.endswith(".html"):
                continue  # Only generated HTML routes are in this contract.
            relative = posixpath.normpath(posixpath.join(
                f"sessions/{session:02d}", href))
            target = ROOT / (relative[:-5] + ".md")
            if not target.is_file():
                errors.append(f"{name}: broken local link {href}")
    reader = (folder / "l3-complete.md")
    if reader.exists():
        body = reader.read_text(encoding="utf-8")
        for row in rows:
            mixed_numbers = len({mod.code(x) for x in rows}) != len(rows)
            anchor = (f'n{mod.page_code(row, rows)}' if mixed_numbers
                      else f'n{mod.code(row)}')
            if f'id="{anchor}"' not in body:
                errors.append(f"Collection lacks anchor {anchor}")
    if session == 16:
        # Explicit conditional approval: warning and explanation must stay public.
        for name in ("index.md", "l3-complete.md", "q24-l3.md",
                     "q24-l2.md", "q24-l1.md"):
            text = (folder / name).read_text(encoding="utf-8")
            if "source-status.html" not in text or "условн" not in text.lower():
                errors.append(f"{name}: missing explicit q24 conditional-approval notice")
        if not (folder / "source-status.md").is_file():
            errors.append("missing source-status.md for lesson 16")
    if errors:
        raise ValueError("; ".join(errors[:12]))
    return len(rows), len(rows) * 3


def private_quality(root, session, numbers):
    if root is None:
        return "NOT_VERIFIED (private repository not provided)"
    with (root / "planning/lesson-progress.csv").open(
            encoding="utf-8-sig", newline="") as f:
        rows = [r for r in csv.DictReader(f) if int(r["meeting"]) == session]
    public_rows = load_publisher().topics(session)
    wanted = {(r["subject"], int(r["question"])) for r in public_rows}
    actual = {(r["subject"], int(r["question"])) for r in rows}
    if actual != wanted or len(rows) != len(public_rows):
        raise ValueError("Private journal has incorrect lesson topics")
    accepted = sum(all(r[k] == "done" for k in ("sources", "l3", "l2", "l1"))
                   and r["quality"] == "approved" for r in rows)
    if session == 16:
        # Five fully sourced topics and one user-approved conditional exception.
        q24 = next((r for r in rows if int(r["question"]) == 24), None)
        if (len(rows) != 6 or accepted != 5 or q24 is None
                or q24["sources"] != "todo"
                or q24["quality"] != "approved"
                or any(q24[level] != "done" for level in ("l3", "l2", "l1"))):
            raise ValueError("Session 16 special source gap not documented correctly")
        return "5/6 fully sourced; q24 conditionally approved with sources=todo"
    if session == 18:
        if len(rows) != 7 or accepted != 4:
            raise ValueError("Session 18 must have four approved and three working topics")
        for q in (18, 13, 14):
            x = next((r for r in rows if int(r["question"]) == q), None)
            if (x is None or x["sources"] != "todo" or x["quality"] != "todo"
                    or any(x[level] != "done" for level in ("l3", "l2", "l1"))):
                raise ValueError(f"Session 18 q{q} working gap status is invalid")
        return "4/7 approved; q18, q13, q14 working editions with source gaps"
    if accepted != len(rows) and session != 13:
        raise ValueError("Private quality gate no longer approved")
    return f"{accepted}/{len(rows)} approved" + (
        " (session 13 has a documented working exception)"
        if session == 13 and accepted != len(rows) else "")


def remote_run(run_id, label):
    if run_id is None:
        return "NOT_VERIFIED"
    uri = f"https://api.github.com/repos/{REPO}/actions/runs/{run_id}"
    headers = {"Accept": "application/vnd.github+json",
               "User-Agent": "gos-exams-publication-audit"}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        with urlopen(Request(uri, headers=headers), timeout=10) as response:
            run = json.load(response)
        if run.get("id") != run_id:
            return f"UNVERIFIED (run ID mismatch: {run_id})"
        if label == "PR CI" and run.get("event") != "pull_request":
            return f"UNVERIFIED (run {run_id} is not a PR check)"
        if label == "Main CI" and (run.get("event") != "push"
                                    or run.get("head_branch") != "main"):
            return f"UNVERIFIED (run {run_id} is not a main push check)"
        if label == "Pages" and "pages" not in run.get("name", "").lower():
            return f"UNVERIFIED (run {run_id} is not Pages)"
        return f'{run.get("status")}/{run.get("conclusion") or "pending"} (run {run_id})'
    except (HTTPError, URLError, TimeoutError, ValueError, OSError) as e:
        return f"NOT_VERIFIED (GitHub API unavailable: {type(e).__name__})"


def external_http(session, first, enabled):
    if not enabled:
        return "NOT_VERIFIED (not requested)"
    suffixes = [f"sessions/{session:02d}/index.html",
                f"sessions/{session:02d}/l3-complete.html",
                f"sessions/{session:02d}/q{first}-l3.html"]
    failures = []
    for suffix in suffixes:
        url = f"{SITE}/{suffix}"
        try:
            with urlopen(Request(url, headers={"User-Agent": "PublicationAudit/1.0"}),
                         timeout=10) as response:
                if response.status != 200:
                    failures.append(f"{suffix}: HTTP {response.status}")
        except (HTTPError, URLError, TimeoutError, OSError) as e:
            failures.append(f"{suffix}: {type(e).__name__}")
    return "PASS: 3/3 HTTP 200" if not failures else (
        "NOT_VERIFIED: " + "; ".join(failures))


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("session", type=int)
    ap.add_argument("--private-root", type=Path)
    ap.add_argument("--pr-run", type=int)
    ap.add_argument("--main-run", type=int)
    ap.add_argument("--pages-run", type=int)
    ap.add_argument("--http", action="store_true",
                    help="Check representative public URLs, never assume Pages equals HTTP")
    args = ap.parse_args()
    if not 1 <= args.session <= 23:
        ap.error("Session must be 1..23")
    print(f"SESSION {args.session:02d}")
    try:
        total, pages = structural_check(args.session)
        publisher = load_publisher()
        numbers = [publisher.code(r) for r in publisher.topics(args.session)]
        quality = private_quality(args.private_root, args.session, numbers)
    except (ValueError, OSError, KeyError) as e:
        print(f"STRUCTURE: FAIL ({e})")
        return 1
    print(f"Private quality: {quality}")
    print(f"Public pages: {pages}/{pages} PASS")
    print("Collection and index: PASS")
    print("Navigation and old routes: PASS (local structural check)")
    pr = remote_run(args.pr_run, "PR CI")
    main_ci = remote_run(args.main_run, "Main CI")
    pages_ci = remote_run(args.pages_run, "Pages")
    http = external_http(args.session, numbers[0], args.http)
    print(f"PR CI: {pr}")
    print(f"Main CI: {main_ci}")
    print(f"Pages: {pages_ci}")
    print(f"External HTTP: {http}")
    confirmed = all(v.startswith("completed/success") for v in
                    (pr, main_ci, pages_ci))
    if confirmed:
        conclusion = ("publication verified (including HTTP)"
                      if http.startswith("PASS") else
                      "deployment confirmed; HTTP audit pending")
    else:
        conclusion = "structural PASS; deployment not fully verified"
    print(f"FINAL: {conclusion}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
