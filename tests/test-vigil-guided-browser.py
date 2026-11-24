#!/usr/bin/env python3
"""Acceptance: one unfolding scroll, 3-choice transitions, stats and no scroll hijack."""
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
STEPS=DATA["steps"]
assert len(STEPS)==72
assert [x["id"] for x in STEPS]==[f"s{i:02d}" for i in range(1,73)]
assert [sum(x["section"]==part for x in STEPS) for part in ["Великая вечерня","Утреня","Первый час"]]==[29,34,9]
assert all(x["title"] and x["cue"] and x["definition"] and x["question"] and x["answer"] for x in STEPS)
assert all(x["nextStepId"]==(STEPS[i+1]["id"] if i<71 else None) for i,x in enumerate(STEPS))
assert all(x["quiz"] and len(x["quiz"]["choices"])==3 and x["quiz"]["correctStepId"]==STEPS[i+1]["id"] and
  sum(c["stepId"]==x["quiz"]["correctStepId"] for c in x["quiz"]["choices"])==1 and
  len({c["stepId"] for c in x["quiz"]["choices"]})==3 and
  len({c["label"] for c in x["quiz"]["choices"]})==3 for i,x in enumerate(STEPS[:71]))
assert STEPS[-1]["quiz"] is None
assert len(DATA["lessons"])==2 and all(sum(y[1] for y in l["blocks"])==150 for l in DATA["lessons"])
assert not re.search(r"знакомые с детства|знакомые нам с детства|с детских лет",TEXT,re.I)
assert not re.search(r"Как устроена игра|Узнать элемент|<audio|<video",TEXT,re.I)
assert all('id="'+x+'"' in TEXT for x in ["vg-stream","vg-jump","vg-reset","vg-map","vg-course"])
assert 'id="vg-ribbon"' not in TEXT
assert "gos-exams-vigil-guided-2027-v1" in JS
assert "Как это называется?" in JS and "Что следует дальше?" in JS
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
    threading.Thread(target=server.serve_forever,daemon=True).start()
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
                    errors=[]
                    page.on("pageerror",lambda e:errors.append(str(e)))
                    page.goto(url,wait_until="networkidle")
                    page.wait_for_selector("#vg-loaded:not([hidden])",timeout=15000)
                    assert not errors,errors
                    assert page.locator(".vg-step").count()==1
                    assert page.locator("#vg-counter").inner_text()=="1 / 72"
                    assert "Восстаните" in page.locator("#vg-step-1 .vg-cue").inner_text()
                    assert page.locator("#vg-step-1 .vg-name").is_hidden()
                    page.locator("#vg-step-1 .vg-reveal").click()
                    assert page.locator("#vg-step-1 .vg-name").is_visible()
                    page.wait_for_selector("#vg-quiz-1:not([hidden])",timeout=5000)
                    assert page.locator("#vg-quiz-1 .vg-choice").count()==3
                    wrong=next(i for i,c in enumerate(STEPS[0]["quiz"]["choices"]) if c["stepId"]!=STEPS[1]["id"])
                    page.locator("#vg-quiz-1 .vg-choice").nth(wrong).click()
                    assert page.locator("#vg-quiz-1 .is-correct").count()==1
                    assert page.locator("#vg-quiz-1 .is-wrong").count()==1
                    assert "Правильный ответ" in page.locator("#vg-quiz-1 .vg-feedback").inner_text()
                    page.wait_for_selector("#vg-step-2",timeout=5000)
                    assert page.locator(".vg-step").count()==2
                    assert page.locator("#vg-step-1 .vg-name").is_visible()
                    page.locator("#vg-step-2 .vg-reveal").click()
                    page.wait_for_selector("#vg-quiz-2:not([hidden])",timeout=5000)
                    correct=next(i for i,c in enumerate(STEPS[1]["quiz"]["choices"]) if c["stepId"]==STEPS[2]["id"])
                    page.locator("#vg-quiz-2 .vg-choice").nth(correct).click()
                    page.wait_for_selector("#vg-step-3",timeout=5000)
                    assert page.locator(".vg-step").count()==3
                    # Scrolling up must not be overridden by the auto-advance timer.
                    page.locator("#vg-step-3 .vg-reveal").click()
                    page.wait_for_selector("#vg-quiz-3:not([hidden])",timeout=5000)
                    page.locator("#vg-quiz-3 .vg-choice").first.click()
                    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
                    page.wait_for_selector("#vg-step-4",timeout=5000)
                    page.wait_for_timeout(300)
                    assert page.evaluate("window.scrollY")<200,"Automatic scroll unexpectedly pulled the reader back"
                    assert page.locator("#vg-jump").is_visible(),"Jump-to-current arrow missing"
                    page.locator("#vg-jump").click()
                    page.wait_for_timeout(700)
                    assert page.locator("#vg-step-4").evaluate("(e)=>e.getBoundingClientRect().top<window.innerHeight")
                    page.reload(wait_until="networkidle")
                    page.wait_for_selector("#vg-loaded:not([hidden])")
                    assert page.locator(".vg-step").count()==4
                    assert page.locator("#vg-step-1 .is-wrong").count()==1
                    assert page.locator("#vg-step-2 .is-correct").count()==1
                    page.locator("#vg-map").evaluate("(el)=>el.open=true")
                    page.wait_for_function("document.querySelectorAll('#vg-menu button').length===72")
                    page.locator("#vg-menu button").nth(6).click()
                    assert page.locator("#vg-step-7").count()==1
                    page.locator("#vg-step-7 details").first.evaluate("(e)=>e.open=true")
                    assert "Уставные варианты" in page.locator("#vg-step-7").inner_text()
                    page.locator("#vg-map").evaluate("(el)=>el.open=true")
                    page.locator("#vg-menu button").last.click()
                    assert page.locator("#vg-step-72").count()==1
                    page.locator("#vg-step-72 .vg-reveal").click()
                    page.wait_for_selector("#vg-results",timeout=5000)
                    stats=page.locator("#vg-results").inner_text()
                    assert "Ошибок" in stats and "Без ответа" in stats and "Точность" in stats and "Время" in stats
                    assert page.locator("#vg-results .vg-stat").nth(0).locator("strong").inner_text()=="1"
                    assert page.locator("#vg-results .vg-stat").nth(1).locator("strong").inner_text()=="2"
                    assert page.locator("#vg-results .vg-stat").nth(2).locator("strong").inner_text()=="68"
                    page.reload(wait_until="networkidle")
                    page.wait_for_selector("#vg-results")
                    assert not errors,errors
                    print(f"PASS {width}px: unfolding 72-step sequence, 3-answer quiz, return arrow, restoration and results")
                    page.close()
            finally:browser.close()
    finally:server.shutdown()
