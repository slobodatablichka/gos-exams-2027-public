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
assert len(layout["merged_regions"]) == 67
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
assert len(coverage) == 144, len(coverage)

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
assert "node.colSpan=m.colspan" in js
assert "rr.source_bands?.length" in js
assert "vm-inner-line" in js
assert "rr.source_label!==undefined" in js
assert 'cell.kind==="span"' in js
assert "vespers-matins-data.json" in page
assert "vespers-matins-digital.js" in page
assert (ROOT / "subjects/liturgics/2027/vespers-matins-scan.md").is_file()
assert data["source_layout"]["reviewed_rows"] == [f"r{i:02d}" for i in range(1,24)]
assert all(c.get("verified_from_source") is True for r in data["rows"][:8] for c in r["cells"])
assert all(c.get("kind") in {"empty","symbol","text"} for r in data["rows"][:8] for c in r["cells"])
assert data["rows"][3]["cells"][8]["text"] == "←"
assert [b["source_band"] for b in data["rows"][6]["source_bands"]] == [7,8]
assert [b["source_band"] for b in data["rows"][7]["source_bands"]] == [9,10]
assert all(len(b["texts"]) == 17 for r in data["rows"][6:8] for b in r["source_bands"])
assert data["rows"][6]["source_bands"][0]["texts"][4] == "Минея аще есть"
assert data["rows"][6]["source_bands"][1]["texts"][4] == "2 прил. или на ряду"
assert data["rows"][7]["source_bands"][1]["texts"][12].startswith("Минея св., аще полиел.")
assert len(data["rows"][7]["source_bands"][1]["cell_parts"]["c13"]) == 2
assert all(c.get("verified_from_source") is True for r in data["rows"][:15] for c in r["cells"])
assert all(c.get("kind") in {"empty","symbol","text","span"} for r in data["rows"][:15] for c in r["cells"])
assert [b["source_band"] for b in data["rows"][9]["source_bands"]] == [12,13]
assert all(len(b["texts"]) == 17 for b in data["rows"][9]["source_bands"])
assert data["rows"][11]["cells"][10]["span_anchor"] == "c10"
assert data["rows"][12]["cells"][8]["span_anchor"] == "c07"
assert data["rows"][13]["cells"][16]["span_anchor"] == "c15"
assert data["rows"][14]["cells"][0]["text"].startswith("Окт.-2, Мин.-1")
assert data["source_layout"]["reviewed_stage_4"]["logical_cells"] == 119
assert len([c for r in data["rows"][8:15] for c in r["cells"]]) == 119
assert all(c.get("verified_from_source") is True for r in data["rows"][15:21] for c in r["cells"])
assert all(c.get("kind") in {"text","empty"} for r in data["rows"][15:21] for c in r["cells"])
assert data["source_layout"]["reviewed_stage_5"]["logical_cells"] == 102
assert data["source_layout"]["reviewed_stage_5"]["source_bands"] == list(range(19,27))
assert [b["source_band"] for b in data["rows"][19]["source_bands"]] == [23,24]
assert [b["source_band"] for b in data["rows"][20]["source_bands"]] == [25,26]
assert all(len(b["texts"]) == 17 for r in data["rows"][19:21] for b in r["source_bands"])
assert data["rows"][19]["source_bands"][1]["texts"][9] == "«Преблагосл. еси»"
assert data["rows"][20]["source_bands"][0]["texts"][9].startswith("Окт. гл.")
assert data["rows"][20]["source_bands"][1]["texts"][9] == ""
assert data["rows"][20]["source_bands"][1]["cell_parts"]["c02"] == ["2 св.","4 прил."]
assert data["rows"][17]["cells"][2]["text"].startswith("Свет. Октоиха")
assert data["rows"][18]["cells"][16]["text"].startswith("Окт.-4")
assert all(c.get("verified_from_source") is True for r in data["rows"][21:23] for c in r["cells"])
assert [b["row_id"] for b in layout["body_bands"][27:29]] == ["r22","r23"]
assert data["source_layout"]["reviewed_stage_6"]["logical_cells"] == 34
assert data["source_layout"]["reviewed_stage_6"]["source_bands"] == [27,28]
assert data["rows"][21]["cells"][0]["text"] == "Свят. 1"
assert data["rows"][21]["cells"][1]["text"] == "Оба тр."
assert data["rows"][21]["cells"][13]["text"].startswith("1, 6 — воскр.")
assert data["rows"][22]["cells"][1]["text"] == "Перемен."
assert data["rows"][22]["cells"][11]["text"] == "← →"
assert data["rows"][22]["cells"][11]["kind"] == "symbol"
assert data["rows"][22]["cells"][12]["text"] == "1, 6 — св.\n3, 9 — воскр."
assert data["rows"][22]["cells"][13]["text"] == "1, 6 — пр.\n3, 9 — воскр."
assert [b["source_band"] for b in data["rows"][4]["source_bands"]] == [4,5]
assert all(len(b["texts"]) == 17 for b in data["rows"][4]["source_bands"])
assert data["rows"][4]["source_bands"][0]["texts"][12] == "Минея"
assert data["rows"][4]["source_bands"][1]["texts"][12] == "1 прил. по гл. сл."
assert data["rows"][4]["cells"][12]["text"] == "\n".join(["Минея","1 прил. по гл. сл."])
assert {tuple(m[k] for k in ("row_start","rowspan","col_start","colspan")) for m in layout["merged_regions"]} >= {(4,2,0,1),(4,2,8,1),(4,2,15,1)}
assert len(data["source_layout"]["body_bands"]) == 29
assert len([x for row in data["rows"] for x in row["cells"]]) == 391
assert all(c.get("verified_from_source") for r in data["rows"] for c in r["cells"])
assert data["rows"][1]["source_label"] == "Слава:\nи ныне:"
assert data["rows"][2]["source_label"] == ""
assert data["rows"][15]["source_label"].startswith("Чтения по:")
assert all(data["rows"][i]["source_label"] == "" for i in [16,17])
assert all(data["rows"][19]["source_bands"][0]["texts"][i] == "Минея на ряду или 2 прил." for i in range(5,9))
assert all(data["rows"][19]["source_bands"][1]["texts"][i] == "" for i in range(5,9))
print("PASS: 17 columns, 23 logical rows, 29 bands, 67 merges, 391 source-reviewed cells, SVG and links")
