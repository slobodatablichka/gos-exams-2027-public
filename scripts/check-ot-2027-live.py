#!/usr/bin/env python3
"""HTTP verification of Old Testament 2027 pages, PDFs and preserved routes."""
import json, time, urllib.request
from pathlib import Path
from urllib.error import HTTPError, URLError
BASE="https://slobodatablichka.github.io/gos-exams-2027-public/"
FOLDER=Path("subjects/ot/2027")
manifest=json.loads((FOLDER/"pdf-manifest.json").read_text(encoding="utf-8"))
urls=["subjects/ot/2027/index.html","subjects/ot/2027/numbers.html"]
urls += [f"subjects/ot/2027/q{n:02d}-{lev}.html" for n in range(1,26) for lev in ("l3","l2","l1")]
pdfs=["subjects/ot/2027/"+entry["file"] for entry in manifest["pdfs"]]
assert len(urls)==77 and len(pdfs)==78
legacy=["subjects/ot/index.html","subjects/ot/numbers.html","subjects/nt/2027/index.html","sessions/02/index.html","subjects/index.html"]
def get(path):
    req=urllib.request.Request(BASE+path,headers={"User-Agent":"GosExams-2027-release-audit/1.0","Cache-Control":"no-cache"})
    with urllib.request.urlopen(req,timeout=30) as response:
        assert response.status==200,(path,response.status)
        data=response.read()
        assert len(data)>100,(path,"empty")
        if path.endswith(".pdf"):
            assert data.startswith(b"%PDF-"),(path,"not a PDF")
        else:
            assert b"<html" in data[:6000].lower(),(path,"not rendered HTML")
            if "q24-" in path:
                assert "А-2027-ВЗ-24-01".encode("utf-8") in data,(path,"missing caveat")
        return len(data)
# Wait until Pages serves the new release, then perform the entire audit.
ready=False
for i in range(20):
    try:
        get("subjects/ot/2027/q24-l3.html")
        get("subjects/ot/2027/pdf/l3.pdf")
        ready=True
        break
    except (HTTPError,URLError,AssertionError,TimeoutError) as e:
        print(f"Pages synchronization check {i+1}: {e}",flush=True)
        time.sleep(15)
assert ready,"New release not deployed on GitHub Pages"
failed=[]
for path in urls+pdfs+legacy:
    try:
        size=get(path)
        print("PASS",path,size,flush=True)
    except Exception as e:
        failed.append((path,str(e)))
for path,reason in failed:
    print("FAIL",path,reason,flush=True)
assert not failed,f"HTTPS check failed for {len(failed)} files"
print(f"PASS: {len(urls)} new HTML + {len(pdfs)} PDF + {len(legacy)} legacy checks; all HTTP 200; q24 caveat visible")
print("External BPDS library links were not independently tested by this audit.")
