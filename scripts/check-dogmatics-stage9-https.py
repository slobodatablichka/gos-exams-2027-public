#!/usr/bin/env python3
"""Stage 9: verify real GitHub Pages HTTPS, 40 exercises, assets and subject links."""
import re
import time
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT="https://slobodatablichka.github.io/gos-exams-2027-public/"
BASE=ROOT+"subjects/dogmatics/2027/"
REQUESTS={}
for n in range(1,11):
    fos=n+15
    REQUESTS[BASE+f"trainers/official-{n:02}.html"]=f'"case_id":"official-{n:02}"'
    for v in range(1,4):
        REQUESTS[BASE+f"trainers/training-{n:02}-{v}.html"]=f'"case_id":"training-{n:02}-{v}"'
    REQUESTS[BASE+f"q{fos:02}-l3.html"]=None
    REQUESTS[BASE+f"practice/practicum-{n:02}.html"]=None
REQUESTS[BASE+"trainers/index.html"]="Догматическое различение"
REQUESTS[ROOT+"assets/js/dogmatics-trainer.js"]="StageOneCore"
REQUESTS[ROOT+"assets/css/dogmatics-trainer.css"]="trainer-nav"
REQUESTS[ROOT+"practice/index.html"]="40 электронных тренажёров"
def check(item):
    url,needle=item
    req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (Stage9-exams-2027-acceptance)"})
    try:
        with urllib.request.urlopen(req,timeout=14) as res:
            data=res.read(5_000_000)
            if res.status!=200:return url,f"HTTP {res.status}"
            if not data:return url,"Empty response"
            if needle is not None and needle.encode("utf-8") not in data:
                return url,f"Missing expected public evidence: {needle}"
            if b"<html" not in data[:500].lower() and url.endswith(".html"):
                return url,"Not a real HTML document"
            return url,None
    except Exception as e:return url,str(e)
def main():
    assert len(REQUESTS)==64,len(REQUESTS)
    for attempt in range(1,17):
        with ThreadPoolExecutor(max_workers=8) as pool:
            responses=dict(pool.map(check,REQUESTS.items()))
        failures={k:v for k,v in responses.items() if v is not None}
        print(f"HTTPS attempt {attempt}/16: {len(REQUESTS)-len(failures)}/{len(REQUESTS)} reachable and content-verified",flush=True)
        if not failures:
            print("PASS Stage 9: 40/40 HTTPS trainer URLs, 10 L3 pages, 10 practicum pages, catalog, shared JS+CSS, practice index. Exact expected case ids present.",flush=True)
            return
        for k,v in list(failures.items())[:4]:print("  ",k,v,flush=True)
        if attempt<16:time.sleep(15)
    raise SystemExit("FAIL: Pages HTTPS acceptance not complete: "+str(failures))
if __name__=="__main__":main()
