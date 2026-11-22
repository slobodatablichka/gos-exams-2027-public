#!/usr/bin/env python3
"""Integrity check for the digital vespers/matins teaching table."""
import json
import pathlib
import re
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
assets = ROOT / "assets" / "liturgics"
data = json.loads((assets / "vespers-matins-data.json").read_text(encoding="utf-8"))
assert len(data["columns"]) == 17
assert len(data["rows"]) == 23

layout = data["source_layout"]
assert layout["reference"]["width"] == 1419 and layout["reference"]["height"] == 2048
assert layout["reference"]["sha256"] == "f60e36751fea7f29ab3a983f32ea2cd67ea7db1380896d126be702bfd1c52cc4"
assert len(layout["column_edges"]) == 19
assert len(layout["body_row_edges"]) == 30
assert len(layout["body_bands"]) == 29
assert sum(group["colspan"] for group in layout["column_groups"]) == 17
assert [band["row_id"] for band in layout["body_bands"]] == [
    "r01","r02","r03","r04","r05","r05","r06","r07","r07",
    "r08","r08","r09","r10","r10","r11","r12","r13","r14",
    "r15","r16","r17","r18","r19","r20","r20","r21","r21",
    "r22","r23"
]
assert len(layout["merged_regions"]) == 52
coverage = set()
for region in layout["merged_regions"]:
    rs, cs = region["row_start"], region["col_start"]
    assert 0 <= rs < 29 and 0 <= cs < 18
    assert rs + region["rowspan"] <= 29
    assert cs + region["colspan"] <= 18
    assert region["rowspan"] * region["colspan"] > 1
    for rr in range(rs, rs+region["rowspan"]):
        for cc in range(cs, cs+region["colspan"]):
            assert (rr, cc) not in coverage, "Overlapping merged region"
            coverage.add((rr, cc))
assert len(coverage) == 112, len(coverage)

columns = [c["id"] for c in data["columns"]]
assert len(set(columns)) == 17
for row in data["rows"]:
    assert len(row["cells"]) == 17, row["id"]
    assert [cell["column_id"] for cell in row["cells"]] == columns, row["id"]
    assert all(isinstance(cell["text"], str) for cell in row["cells"])
for sign in (assets / "service-signs").glob("*.svg"):
    ET.parse(sign)
for c in data["columns"]:
    assert isinstance(c.get("typikon"), str) and c["typikon"].strip(), c["id"]
    signs = c.get("icons") or ([c["icon"]] if c.get("icon") else [])
    for sign in signs:
        assert (assets / "service-signs" / sign).is_file(), sign
mid = (assets / "service-signs" / "bdennaya-srednego-svyatogo.svg").read_text(encoding="utf-8")
assert 'M12 32 A20 20 0 0 0 52 32' in mid, "Expected exact lower semicircle"
js = (assets / "vespers-matins-digital.js").read_text(encoding="utf-8")
page = (ROOT / "subjects/liturgics/2027/vespers-matins.md").read_text(encoding="utf-8")
assert "res.json()" in js
assert "layout.merged_regions" in js
assert "node.colSpan=merge.colspan" in js
assert "vespers-matins-data.json" in page
assert "vespers-matins-digital.js" in page
assert (ROOT / "subjects/liturgics/2027/vespers-matins-scan.md").is_file()
print("PASS: 17 columns, 23 logical rows, 29 source bands, 52 original merged regions, SVG and links")
