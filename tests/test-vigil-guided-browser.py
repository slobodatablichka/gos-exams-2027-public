#!/usr/bin/env python3
"""Acceptance for the full source-based guided vigil, two supplementary lessons."""
import functools
import http.server
import json
import pathlib
import re
import shutil
import tempfile
import threading
from playwright.sync_api import sync_playwright

ROOT=pathlib.Path(__file__).resolve().parents[1]
DATA=json.loads((ROOT/"assets/liturgics/vigil-guided-data.json").read_text(encoding="utf-8"))
TEXT=(ROOT/"subjects/liturgics/2027/vigil-guided.md").read_text(encoding="utf-8")
JS=(ROOT/"assets/liturgics/vigil-guided.js").read_text(encoding="utf-8")
assert len(DATA["steps"])==72
assert [s["section"] for s in DATA["steps"]].count("Великая вечерня")==29
assert [s["section"] for s in DATA["steps"]].count("Утреня")==34
assert [s["section"] for s in DATA["steps"]].count("Первый час")==9
assert len({s["id"] for s in DATA["steps"]})==72
assert all(s["title"] and s["cue"] and s["definition"] and s["question"] and s["answer"] and s["source"] for s in DATA["steps"])
assert all(s["source"] in {"E","M","H"} for s in DATA["steps"])
assert all(src["name"].startswith("Аверкий (Таушев)") for src in DATA["sources"][:3])
assert len(DATA["lessons"])==2
assert all(sum(pair[1] for pair in lesson["blocks"])==150 for lesson in DATA["lessons"])
assert [s["id"] for s in DATA["steps"]]==[f"s{i:02d}" for i in range(1,73)]
assert all(s.get("nextStepId")==(DATA["steps"][i+1]["id"] if i<71 else None) for i,s in enumerate(DATA["steps"]))
assert all(isinstance(s.get("subelements"),list) and isinstance(s.get("conditions"),list) for s in DATA["steps"])
assert sum(bool(s["conditions"]) for s in DATA["steps"])>=50
assert sum(bool(s["subelements"]) for s in DATA["steps"])>=50
assert DATA["steps"][52]["id"]=="s53" and "Честнейшую" in DATA["steps"][52]["cue"]
assert DATA["steps"][-1]["title"]=="Окончание первого часа и отпуст"
assert "vg-detail-elements" in TEXT and "vg-conditions" in TEXT

assert not re.search(r"<audio|<video",TEXT,re.I)
assert 'vigil-guided-data.json' in TEXT and 'vigil-guided.js' in TEXT
assert "localStorage" in JS and "data.steps" in JS and "Что дальше" in TEXT
assert all("#"+id in JS for id in ["vg-show-answer","vg-show-next","vg-training","vg-course","vg-back","vg-forward"])
assert "vigil-guided.html" in (ROOT/"subjects/liturgics/2027/index.md").read_text(encoding="utf-8")
assert "vigil-guided.html" in (ROOT/"subjects/liturgics/2027/practicum/index.md").read_text(encoding="utf-8")

style=re.search(r"<style>[\s\S]*?</style>",TEXT)
start=TEXT.index('<div class="vg-root"')
end=TEXT.index('<script src=',start)
part=TEXT[start:end]
part=part.replace("{{ '/assets/liturgics/vigil-guided-data.json' | relative_url }}","/assets/liturgics/vigil-guided-data.json")
part=part.replace("{{ '/subjects/liturgics/2027/vespers-matins.html' | relative_url }}","/subjects/liturgics/2027/vespers-matins.html")
HTML='<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'+style.group()+'</head><body>'+part+'<script defer src="/assets/liturgics/vigil-guided.js"></script></body></html>'

with tempfile.TemporaryDirectory() as temp:
    path=pathlib.Path(temp)
    (path/"index.html").write_text(HTML,encoding="utf-8")
    (path/"assets").symlink_to(ROOT/"assets",target_is_directory=True)
    server=http.server.ThreadingHTTPServer(("127.0.0.1",0),functools.partial(http.server.SimpleHTTPRequestHandler,directory=temp))
    worker=threading.Thread(target=server.serve_forever,daemon=True);worker.start()
    url=f"http://127.0.0.1:{server.server_port}/"
    try:
        with sync_playwright() as p:
            chrome=shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
            args={"headless":True,"args":["--no-sandbox"]}
            if chrome:args["executable_path"]=chrome
            browser=p.chromium.launch(**args)
            try:
                for width,height in [(1440,900),(390,844),(320,700)]:
                    page=browser.new_page(viewport={"width":width,"height":height})
                    errors=[];page.on("pageerror",lambda e:errors.append(str(e)))
                    page.goto(url,wait_until="networkidle")
                    page.wait_for_selector("#vg-loaded:not([hidden])",timeout=15000)
                    assert not errors,errors
                    assert page.locator("#vg-counter").inner_text()=="1 / 72"
                    assert "Восстаните" in page.locator("#vg-cue").inner_text()
                    assert page.locator("#vg-explanation").is_hidden()
                    # The added semantic subelements and conditional Typikon notes must be interactive.
                    assert page.locator("#vg-detail-elements").is_visible()
                    page.locator("#vg-detail-elements summary").click()
                    assert page.locator("#vg-detail-list li").count()>=1
                    assert page.locator("#vg-conditions").is_hidden()
                    page.locator("#vg-show-explanation").click()
                    assert page.locator("#vg-explanation").is_visible()
                    assert "Аверкий" in page.locator("#vg-source").inner_text()
                    page.locator("#vg-show-answer").click()
                    assert page.locator("#vg-answer").is_visible()
                    page.locator("#vg-show-next").click()
                    assert page.locator("#vg-next-answer").is_visible()
                    page.locator("#vg-forward").click()
                    assert page.locator("#vg-counter").inner_text()=="2 / 72"
                    assert page.locator("#vg-explanation").is_hidden()
                    page.locator("#vg-training").check()
                    assert page.locator("#vg-title").is_hidden()
                    page.locator("#vg-show-name").click()
                    assert page.locator("#vg-title").is_visible()
                    page.reload(wait_until="networkidle")
                    page.wait_for_selector("#vg-loaded:not([hidden])")
                    assert page.locator("#vg-counter").inner_text()=="2 / 72"
                    assert page.locator("#vg-training").is_checked()
                    assert page.locator("#vg-title").is_hidden()
                    page.goto(url+"#step-7",wait_until="networkidle")
                    assert page.locator("#vg-counter").inner_text()=="7 / 72"
                    assert page.locator("#vg-conditions").is_visible()
                    page.locator("#vg-conditions summary").click()
                    assert "Блажен муж" in page.locator("#vg-conditions-list").inner_text()
                    page.goto(url+"#step-53",wait_until="networkidle")
                    assert "Честнейшую" in page.locator("#vg-cue").inner_text()
                    assert page.locator("#vg-conditions").is_visible()
                    page.locator("#vg-conditions summary").click()
                    assert "припев" in page.locator("#vg-conditions-list").inner_text().lower()
                    page.locator("#vg-section button").nth(2).click()
                    assert page.locator("#vg-counter").inner_text()=="64 / 72"
                    assert page.locator("#vg-cue").inner_text().startswith("«Приидите")
                    page.locator("#vg-map").evaluate("(el)=>el.open=true")
                    page.wait_for_function("document.querySelectorAll(\'#vg-menu button\').length === 72",timeout=10000)
                    assert page.locator("#vg-menu button").count()==72
                    page.locator("#vg-menu button").last.click()
                    assert page.locator("#vg-counter").inner_text()=="72 / 72"
                    assert page.locator("#vg-forward").is_disabled()
                    page.locator("#vg-reset").click()
                    assert page.locator("#vg-counter").inner_text()=="1 / 72"
                    page.locator("#vg-training").uncheck()
                    assert page.locator("#vg-title").is_visible()
                    page.locator("#vg-course").evaluate("(el)=>el.parentElement.open=true")
                    assert page.locator("#vg-course .vg-lesson").count()==2
                    assert not errors,errors
                    print(f"PASS {width}px: 72 steps; explanations, recall, next, persistence, lessons")
                    page.close()
            finally:browser.close()
    finally:server.shutdown()
