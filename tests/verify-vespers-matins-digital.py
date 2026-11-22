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
columns = [c["id"] for c in data["columns"]]
assert len(set(columns)) == 17
for row in data["rows"]:
    assert len(row["cells"]) == 17, row["id"]
    assert [cell["column_id"] for cell in row["cells"]] == columns, row["id"]
    assert all(isinstance(cell["text"], str) for cell in row["cells"])
for sign in (assets / "service-signs").glob("*.svg"):
    ET.parse(sign)
for c in data["columns"]:
    if c.get("icon"):
        assert (assets / "service-signs" / c["icon"]).is_file(), c["icon"]
mid = (assets / "service-signs" / "bdennaya-srednego-svyatogo.svg").read_text(encoding="utf-8")
assert 'M12 32 A20 20 0 0 0 52 32' in mid, "Expected exact lower semicircle"
js = (assets / "vespers-matins-digital.js").read_text(encoding="utf-8")
page = (ROOT / "subjects/liturgics/2027/vespers-matins.md").read_text(encoding="utf-8")
assert "res.json()" in js
assert "vespers-matins-data.json" in page
assert "vespers-matins-digital.js" in page
assert (ROOT / "subjects/liturgics/2027/vespers-matins-scan.md").is_file()
print("PASS: 17 columns, 23 rows, 391 text cells, SVG signs, proper semicircle, links")
