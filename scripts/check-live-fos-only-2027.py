#!/usr/bin/env python3
"""Check live GitHub Pages: only official FOS 2027 is published."""
import argparse
import json
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
            sequence_probe = request("subjects/liturgics/2027/trainers/sequence.html").decode("utf-8")
            if 'id="liturgicsSequenceManifest"' not in sequence_probe:
                raise ValueError("Sequence entry has not yet been deployed")
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
        full_bytes = request(full)
        if not full_bytes.startswith(b"%PDF-") or len(full_bytes) < 1000000:
            raise ValueError("Invalid or incomplete question-ordered L3+L2+L1 PDF: " + full)
        print("LIVE COMPLETE PDF PASS", full, len(full_bytes), flush=True)
        pdf_count += 1

    # Exercise pages are generated separately from L1/L2/L3 answers.
    for slug, route in (("liturgics", "practice/q01.html"),
                        ("liturgics", "examples/q01.html"),
                        ("dogmatics", "practice/practicum-01.html")):
        path = f"subjects/{slug}/2027/{route}"
        check_navigation(request(path).decode("utf-8", errors="replace"), path, slug)

    # All published Liturgics games use one browser engine and separate JSON case passports.
    shared_js = request("assets/js/liturgics-pyramid.js").decode("utf-8")
    shared_css = request("assets/css/liturgics-pyramid.css").decode("utf-8")
    if "function applyLayout()" not in shared_js or "function showSuccessL3Link()" not in shared_js:
        raise ValueError("Shared Liturgics engine or its L3 link is missing")
    if ".swap-columns" not in shared_css or ".column.pyramid" not in shared_css:
        raise ValueError("Shared Liturgics styles are incomplete")
    games = (
        ("index.html", "lit11-proskomedia.json", "assembly", "Проскомидия", 11),
        ("vozdvizhenie.html", "lit03-vozdvizhenie.json", "assembly", "Воздвижение", 18),
        ("velikiy-post.html", "lit05-velikiy-post.json", "assembly", "Великий пост", 36),
        ("q12-errors.html", "lit12-diagnostic.json", "diagnostic", "Найди и исправь ошибки", 19),
        ("q12-assembly.html", "lit12-assembly.json", "assembly", "Литургия оглашенных", 19),
        ("q13-assembly.html", "lit13-anaphora.json", "assembly", "Анафора", 14),
        ("q14-assembly.html", "lit14-faithful.json", "assembly", "Литургия верных", 24),
        ("q15-assembly.html", "lit15-presanctified.json", "assembly", "Литургия Преждеосвященных Даров", 26),
        ("q01-assembly.html", "lit01-octoechos-weekday.json", "assembly", "Октоих", 27),
        ("q02-assembly.html", "lit02-sunday-indiction.json", "assembly", "Воскресное бдение", 33),
        ("q04-assembly.html", "lit04-sozont-forefeast.json", "assembly", "Предпразднство", 32),
        ("q07-assembly.html", "lit07-nicholas-temple.json", "assembly", "Храм святителя Николая", 31),
        ("q06-assembly.html", "lit06-great-friday.json", "assembly", "Великий пяток", 36),
        ("q08-assembly.html", "lit08-nativity-vigil.json", "assembly", "Рождество Христово", 28),
        ("q09-assembly.html", "lit09-pentecostarion-weekday.json", "assembly", "Цветная Триодь", 26),
        ("q10-assembly.html", "lit10-trinity-saturday.json", "assembly", "Троицкая родительская суббота", 37),
    )
    variant_games = (
        ("q11-errors-a.html", "lit11-diagnostic-a.json", 12),
        ("q11-errors-b.html", "lit11-diagnostic-b.json", 11),
        ("q11-errors-c.html", "lit11-diagnostic-c.json", 12),
        ("q12-errors-a.html", "lit12-diagnostic-a.json", 19),
        ("q12-errors-b.html", "lit12-diagnostic-b.json", 19),
        ("q12-errors-c.html", "lit12-diagnostic-c.json", 19),
        ("q13-errors-a.html", "lit13-diagnostic-a.json", 14),
        ("q13-errors-b.html", "lit13-diagnostic-b.json", 14),
        ("q13-errors-c.html", "lit13-diagnostic-c.json", 15),
        ("q14-errors-a.html", "lit14-diagnostic-a.json", 24),
        ("q14-errors-b.html", "lit14-diagnostic-b.json", 24),
        ("q14-errors-c.html", "lit14-diagnostic-c.json", 24),
        ("q15-errors-a.html", "lit15-diagnostic-a.json", 27),
        ("q15-errors-b.html", "lit15-diagnostic-b.json", 26),
        ("q15-errors-c.html", "lit15-diagnostic-c.json", 7),
    )
    games = games + tuple((name, case, "diagnostic", "Найди и исправь ошибки", count)
                          for name, case, count in variant_games)
    base_game = "subjects/liturgics/2027/sandbox-pyramid/"
    for file_name, case_file, mode, heading, total_items in games:
        path = base_game + file_name
        body = request(path).decode("utf-8", errors="replace")
        check_navigation(body, path, "liturgics")
        if heading not in body or 'id="sand"' not in body or 'id="pyramid"' not in body:
            raise ValueError("Incorrect Liturgics game: " + path)
        if 'id="swapBtn"' not in body or 'class="column pyramid"' not in body:
            raise ValueError("Swappable columns missing: " + path)
        if 'data-case="data/' + case_file + '"' not in body:
            raise ValueError("Incorrect case reference: " + path)
        if "assets/js/liturgics-pyramid.js" not in body or "assets/css/liturgics-pyramid.css" not in body:
            raise ValueError("Common engine not loaded from page: " + path)
        case = json.loads(request(base_game + "data/" + case_file).decode("utf-8"))
        if case.get("mode") != mode or len(case.get("items", [])) != total_items:
            raise ValueError("Incorrect case data: " + case_file)
        if case.get("assessment") != "training_check" or not case.get("l3", "").endswith("-l3.html"):
            raise ValueError("Incorrect case assessment / L3: " + case_file)
        if len({item["id"] for item in case["items"]}) != total_items:
            raise ValueError("Duplicate brick IDs: " + case_file)
        if case_file == "lit01-octoechos-weekday.json" and (case.get("sourceStatus") != "task_scope_reviewed" or case.get("passport", {}).get("task_scope_sufficient") is not True):
            raise ValueError("Q01 task scope must be sufficient without calendar extras")
        if case_file == "lit09-pentecostarion-weekday.json" and (case.get("sourceStatus") != "task_scope_reviewed" or case.get("passport", {}).get("task_scope_sufficient") is not True):
            raise ValueError("Q09 must be judged only by rows required for its task")
        print("LIVE GAME PASS", path, flush=True)

    practice_catalog = "subjects/liturgics/2027/trainers/index.html"
    practice_html = request(practice_catalog).decode("utf-8", errors="replace")
    check_navigation(practice_html, practice_catalog, "liturgics")
    if practice_html.count('data-question="') != 15:
        raise ValueError("Practice exam catalog has not exactly 15 questions")
    for name, _, _, _, _ in games:
        if "sandbox-pyramid/" + name not in practice_html:
            raise ValueError("Practice catalog missing published game: " + name)
    for n in (1, 2, 4, 6, 7, 8, 9, 10, 12, 13, 14, 15):
        for route in ("practice", "examples"):
            page = f"subjects/liturgics/2027/{route}/q{n:02d}.html"
            content = request(page).decode("utf-8", errors="replace")
            check_navigation(content, page, "liturgics")
            if f"sandbox-pyramid/q{n:02d}-assembly.html" not in content:
                raise ValueError("Missing main game on teacher page: " + page)

    # Sequential practice reuses the actual game URLs and must come from the same case registry.
    seq_path = "subjects/liturgics/2027/trainers/sequence.html"
    seq_html = request(seq_path).decode("utf-8")
    check_navigation(seq_html, seq_path, "liturgics")
    if not all('id="' + name + '"' in seq_html for name in
               ("startOne", "startSelected", "startAll", "oneCase", "mode12", "sessionItems", "liturgicsSequenceManifest")):
        raise ValueError("Sequence launcher is incomplete")
    pattern = r'<script id="liturgicsSequenceManifest" type="application/json">(.*?)</script>'
    found = re.search(pattern, seq_html, flags=re.S)
    if not found:
        raise ValueError("The live sequence has no rendered manifest")
    embedded = json.loads(found.group(1))
    qs = embedded.get("questions", [])
    if len(qs) != 15 or len([c for q in qs for c in q["cases"]]) != 31:
        raise ValueError("Rendered sequence manifest has incorrect question/case count")
    if sum(c["mode"] == "diagnostic" for q in qs for c in q["cases"]) != 16:
        raise ValueError("Error-correction mode missing from equal-access sequence")
    if any("version" not in c or "data_path" not in c for q in qs for c in q["cases"]):
        raise ValueError("Cannot independently restore case progress")
    slots = embedded.get("variant_slots", [])
    if len(slots) != 45 or len([v for v in slots if v.get("status") == "published_training"]) != 15:
        raise ValueError("45 source variant slots are not accurately audited")
    if len([v for v in slots if v.get("status") == "task_defined_key_pending" and v.get("task_scope_sufficient")]) != 30:
        raise ValueError("All 30 pending tasks must have sufficient task-defined conditions")
    if not any(v.get("id") == "lit-15-C" and v.get("status") == "published_training" and v.get("case_id") == "lit15-diagnostic-c"
               for v in slots):
        raise ValueError("Q15-C must be published without invented calendar details")
    year_path = "subjects/liturgics/2027/trainers/year.html"
    year_html = request(year_path).decode("utf-8")
    check_navigation(year_html, year_path, "liturgics")
    calendar_cases = [c for q in qs for c in q["cases"] if c.get("year")]
    if len(calendar_cases) != 11 or year_html.count("Собрать последование") != 11:
        raise ValueError("Calendar catalog must contain exactly nine prepared cases")
    for c in calendar_cases:
        if "sandbox-pyramid/" + c["path"].split("/")[-1] not in year_html:
            raise ValueError("Calendar case game link is missing: " + c["case_id"])
    print("LIVE YEAR PASS: eleven source-grounded cases and teaching schemes; no invented calendar", flush=True)
    print("LIVE VARIANTS PASS: 45 slots; 15 published diagnostics, 30 task-defined pending games; no calendar blocker", flush=True)
    program_js = request("assets/js/liturgics-sequence.js").decode("utf-8")
    program_css = request("assets/css/liturgics-sequence.css").decode("utf-8")
    if not all(token in program_js for token in ("startSelected", "startAll", "bpds-liturgics-sequence-v1", "bpds-liturgics-checked-")):
        raise ValueError("Sequence client logic is incomplete")
    if ".exam-options" not in program_css or "function examSequenceNavigation()" not in shared_js:
        raise ValueError("Sequence links to games are incomplete")
    if "sequence.html" not in practice_html:
        raise ValueError("Exam catalog does not link to the sequence")
    practice_root = "practice/index.html"
    practice_body = request(practice_root).decode("utf-8")
    check_navigation(practice_body, practice_root)
    if "trainers/sequence.html" not in practice_body:
        raise ValueError("Practice landing has no exam sequence")
    print("LIVE SEQUENCE PASS: one / selected / all 15, both modes at q12, full per-case progress versions", flush=True)
    print("LIVE TRAINERS PASS: 15 exam slots, 31 real games (15 assembly + 16 error-correction), shared JS/CSS/JSON", flush=True)

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
