#!/usr/bin/env python3
"""Check live GitHub Pages: only official FOS 2027 is published."""
import argparse
import re
import time
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

BASE = "https://slobodatablichka.github.io/gos-exams-2027-public/"
SUBJECTS = ("nt", "ot", "oi", "rpc", "dogmatics", "liturgics")
LEVELS = ("l3", "l2", "l1")

def request(path):
    req = Request(BASE + path, headers={
        "User-Agent": "FOS2027-NewOnly-Audit/1.0",
        "Cache-Control": "no-cache",
        "Accept": "text/html,application/pdf,*/*",
    })
    for attempt in range(4):
        try:
            with urlopen(req, timeout=25) as resp:
                if resp.status != 200:
                    raise ValueError(f"{path}: unexpected HTTP {resp.status}")
                return resp.read()
        except HTTPError as exc:
            if exc.code not in (502, 503, 504) or attempt == 3:
                raise
            time.sleep(2)

def check_navigation(html, path, slug=None):
    """Both return bars must be present in the actual deployed HTML."""
    if html.count('class="exam-global-nav"') < 2:
        raise ValueError(f"{path}: no top-and-bottom return navigation")
    for dest in ("/index.html", "/subjects/index.html"):
        if f'href="{BASE.rstrip("/").removeprefix("https://slobodatablichka.github.io")}{dest}"' not in html:
            raise ValueError(f"{path}: missing link to {dest}")
    if slug and f"/subjects/{slug}/2027/index.html" not in html:
        raise ValueError(f"{path}: missing return to its subject")


def check_gone(path):
    try:
        request(path)
    except HTTPError as exc:
        if exc.code == 404:
            return
        raise ValueError(f"{path}: expected HTTP 404, got {exc.code}") from exc
    raise ValueError(f"OBSOLETE CONTENT STILL LIVE: {path}")

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--attempts", type=int, default=18)
    ap.add_argument("--retry-seconds", type=int, default=10)
    args = ap.parse_args()
    # Wait for the actual GitHub Pages deployment, not merely the Git commit.
    for attempt in range(1, args.attempts + 1):
        try:
            check_gone("sessions/01/index.html")
            check_gone("subjects/nt/index.html")
            mainpage = request("subjects/index.html").decode("utf-8")
            if "Государственного экзамена" in mainpage and "2027" not in mainpage:
                raise ValueError("Unexpected catalog")
            if "2027" not in mainpage or "архив" in mainpage.lower():
                raise ValueError("Current-only catalog is not deployed")
            break
        except (ValueError, HTTPError, URLError, TimeoutError, OSError) as exc:
            print(f"Pages deployment attempt {attempt}/{args.attempts}: {exc}", flush=True)
            if attempt == args.attempts:
                raise
            time.sleep(args.retry_seconds)

    for path in ("index.html", "subjects/index.html", "materials/index.html"):
        body = request(path).decode("utf-8", errors="replace")
        if "2027" not in body:
            raise ValueError("No 2027 menu: " + path)
        check_navigation(body, path)
        if "sessions/" in body or "архив" in body.lower():
            raise ValueError("Archived links or labels on page: " + path)

    html_count = pdf_count = 0
    for slug in SUBJECTS:
        base = f"subjects/{slug}/2027/"
        for page in ("index.html", "numbers.html"):
            body = request(base + page).decode("utf-8", errors="replace")
            if "2027" not in body:
                raise ValueError("Invalid official subject page: " + base + page)
            if page == "index.html" and "pdf/full-l3-l2-l1.pdf" not in body:
                raise ValueError("Missing combined PDF download on " + base + page)
            check_navigation(body, base + page, slug)
            if re.search(r"\[?Прежний вопросник|Старый перечень|sessions/", body, flags=re.I):
                raise ValueError("Old question bank is linked from: " + base + page)
        for n in range(1, 26):
            for level in LEVELS:
                path = base + f"q{n:02d}-{level}.html"
                body = request(path).decode("utf-8", errors="replace")
                if "2027" not in body or "sessions/" in body:
                    raise ValueError("Old content/link on new answer: " + path)
                check_navigation(body, path, slug)
                html_count += 1
                pdf = base + f"pdf/q{n:02d}-{level}.pdf"
                content = request(pdf)
                if not content.startswith(b"%PDF-") or len(content) < 1400:
                    raise ValueError("Invalid current PDF: " + pdf)
                pdf_count += 1
        for level in LEVELS:
            pdf = base + f"pdf/{level}.pdf"
            if not request(pdf).startswith(b"%PDF-"):
                raise ValueError("Invalid full PDF: " + pdf)
            pdf_count += 1
        full = base + "pdf/full-l3-l2-l1.pdf"
        if not request(full).startswith(b"%PDF-"):
            raise ValueError("Invalid question-ordered L3+L2+L1 PDF: " + full)
        pdf_count += 1

    # Exercise pages are generated separately from L1/L2/L3 answers.
    for slug, route in (("liturgics", "practice/q01.html"),
                        ("liturgics", "examples/q01.html"),
                        ("dogmatics", "practice/practicum-01.html")):
        path = f"subjects/{slug}/2027/{route}"
        check_navigation(request(path).decode("utf-8", errors="replace"), path, slug)

    old_routes = ["schedule.html", "assignments.html",
                  "subjects/navigation-manifest.json", "subjects/expansion-navigation-manifest.json",
                  "sessions/01/q12-l3.html", "sessions/19/q23-dogmatics-l3.html"]
    old_routes.extend(f"sessions/{n:02d}/index.html" for n in range(1,24))
    for slug in SUBJECTS:
        old_routes.extend((f"subjects/{slug}/index.html",
                           f"subjects/{slug}/numbers.html",
                           f"subjects/{slug}/pdf/l3.pdf",
                           f"subjects/{slug}/pdf/q01-l3.pdf",
                           f"subjects/{slug}/pdf-manifest.json"))
    for path in old_routes:
        check_gone(path)
    print(f"LIVE PASS: {html_count} official HTML pages, {pdf_count} PDFs")
    print(f"LIVE PASS: {len(old_routes)} obsolete URLs return HTTP 404")
    print("LIVE PASS: homepage and all six subject catalogs show only official FOS 2027")
    print("LIVE PASS: visible return links on 450 answers, 12 catalogs and 3 exercises")

if __name__ == "__main__":
    main()
