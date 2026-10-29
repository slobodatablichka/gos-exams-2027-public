#!/usr/bin/env python3
"""Check the study plan: 147 unique topics, 150 official numbers and no duplicate answers."""
import csv
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALIASES = {("ВЗ", "5"): "14", ("ДБ", "1"): "7", ("ДБ", "6"): "16"}
IDS = ("05", "03", "07", "08", "22", "06")
LEVELS = ("l1", "l2", "l3")


def read_csv(path):
    with (ROOT / path).open(encoding="utf-8-sig", newline="") as f:
        return list(csv.DictReader(f))


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def check():
    errors = []
    roles = {}
    expected_keys = None
    for n in (5, 6, 7):
        data = read_csv(f"_data/roles_{n}.csv")
        keys = [(r["meeting"], r["subject"], r["question"]) for r in data]
        roles[n] = data
        if len(data) != 147 or len(set(keys)) != 147:
            errors.append(f"size {n}: expected 147 distinct rows")
        if expected_keys is not None and keys != expected_keys:
            errors.append(f"size {n}: row order differs from other groups")
        expected_keys = keys
        for row in data:
            key = (row["subject"], row["question"])
            if row["aliases"] != ALIASES.get(key, ""):
                errors.append(f"size {n}: invalid alias at {key}")
            p, s = int(row["primary"]), int(row["second"])
            if p == s or not (1 <= p <= n and 1 <= s <= n):
                errors.append(f"size {n}: invalid pair at {key}")
    dates = read_csv("_data/meetings.csv")
    if len(dates) != 23:
        errors.append("Expected 23 meeting dates")
    if 147 + len(ALIASES) != 150:
        errors.append("Official number coverage mismatch")

    schedule = read("schedule.md")
    meetings = re.findall(r"(?=^## Занятие (\d+) —)", schedule, flags=re.M)
    if meetings != [str(i) for i in range(1, 24)]:
        errors.append("Schedule meeting headings do not match 1..23")
    sections = re.split(r"(?=^## Занятие \d+ —)", schedule, flags=re.M)[1:]
    total_rows = 0
    for meeting, section in enumerate(sections, start=1):
        lines = [line for line in section.splitlines()
                 if line.startswith("| ") and line.endswith(" |") and "| Студент " in line]
        expected = [r for r in roles[7] if int(r["meeting"]) == meeting]
        if len(lines) != len(expected):
            errors.append(f"Meeting {meeting}: {len(lines)} schedule rows instead of {len(expected)}")
            continue
        for line, role in zip(lines, expected):
            cells = line[2:-2].split(" | ")
            if len(cells) != 5:
                errors.append(f"Meeting {meeting}: not 5 columns")
                continue
            numbers = role["question"] + ("/" + role["aliases"] if role["aliases"] else "")
            if "№ " + numbers not in cells[0]:
                errors.append(f"Meeting {meeting}: wrong official numbers {numbers}")
            if cells[2] != "Студент " + role["primary"] or cells[3] != "Студент " + role["second"]:
                errors.append(f"Meeting {meeting}: mismatch with group 7 roles")
            if role["aliases"] and (
                "под №" + role["aliases"] not in cells[1]
                or "один раз" not in cells[1]
            ):
                errors.append(f"Meeting {meeting}: missing second number explanation")
        total_rows += len(lines)
    if total_rows != 147:
        errors.append(f"Schedule has {total_rows} topics instead of 147")

    assignments = read("assignments.md")
    if "item.aliases" not in assignments or "roleplan-alias" not in assignments:
        errors.append("Assignments page cannot show combined official numbers")

    index = read("sessions/02/index.md")
    reader = read("sessions/02/l3-complete.md")
    if index.count('class="lesson-card"') != 6:
        errors.append("Session 02 has duplicated or missing cards")
    if reader.count('<blockquote class="exam-official">') != 6 or 'id="n14"' in reader:
        errors.append("Session 02 L3 reader duplicates question 14")
    for level in LEVELS:
        for id_ in IDS:
            page = read(f"sessions/02/q{id_}-{level}.md")
            if page.count('<blockquote class="exam-official">') != 1:
                errors.append(f"q{id_}/{level}: official formula not exactly once")
            if re.search(r'href="q14-(l1|l2|l3)\.html"', page):
                errors.append(f"q{id_}/{level}: duplicate page in navigation")
            if 'class="exam-prevnext"' not in page or 'class="exam-questions"' not in page:
                errors.append(f"q{id_}/{level}: navigation missing")
            if id_ == "05" and (
                "№5/14" not in page or "под ВЗ №14" not in page
            ):
                errors.append(f"q05/{level}: other official number not announced")
        duplicate = read(f"sessions/02/q14-{level}.md")
        if f'url=q05-{level}.html' not in duplicate or '<blockquote class="exam-official">' in duplicate:
            errors.append(f"q14/{level}: missing redirect or duplicate full answer")

    js = read("assets/js/schedule-mobile.js")
    if "totalQuestions !== 147" not in js:
        errors.append("Mobile schedule still assumes 150 topic cards")

    for error in errors:
        print("ERROR:", error)
    if errors:
        raise SystemExit(1)
    print("PASS: 23 dates; 147 distinct study topics; 150 official numbers")
    print("PASS: 3 explicit topic aliases; 147 valid pairs in each group 5/6/7")
    print("PASS: 6 session-02 articles/cards; 3 legacy redirects; mobile guard 147")


if __name__ == "__main__":
    check()
