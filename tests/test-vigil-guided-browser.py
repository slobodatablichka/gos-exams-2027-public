#!/usr/bin/env python3
"""Acceptance: two quizzes at each step, unified scrolling, persistence and statistics."""
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
assert [s["id"] for s in STEPS]==[f"s{i:02d}" for i in range(1,73)]
assert [sum(s["section"]==p for s in STEPS) for p in ("Великая вечерня","Утреня","Первый час")]==[29,34,9]
assert all(s["nameQuiz"]["correctStepId"]==s["id"] and
           2<=len(s["nameQuiz"]["choices"])<=5 and
           len({c["stepId"] for c in s["nameQuiz"]["choices"]})==len(s["nameQuiz"]["choices"]) and
           len({c["label"] for c in s["nameQuiz"]["choices"]})==len(s["nameQuiz"]["choices"]) and
           sum(c["stepId"]==s["id"] for c in s["nameQuiz"]["choices"])==1 and
           s["nameQuiz"]["editorial"]["relatedStepIds"] and
           s["nameQuiz"]["editorial"]["source"] for s in STEPS)
assert all(s["quiz"] and len(s["quiz"]["choices"])==3 and
           s["quiz"]["correctStepId"]==STEPS[i+1]["id"] and
           sum(c["stepId"]==s["quiz"]["correctStepId"] for c in s["quiz"]["choices"])==1
           for i,s in enumerate(STEPS[:71]))
assert STEPS[-1]["quiz"] is None
assert len(DATA["lessons"])==2 and all(sum(x[1] for x in l["blocks"])==150 for l in DATA["lessons"])
assert not re.search(r"знакомые с детства|Как устроена игра|Узнать элемент|<audio|<video",TEXT,re.I)
assert 'id="vg-stream"' in TEXT and 'id="vg-jump"' in TEXT and 'id="vg-ribbon"' not in TEXT
assert "Как это называется?" in JS and "Что следует дальше?" in JS
assert "nameAnswers" in JS and "143-arr.length" in JS and "scrollRevision===revision" in JS
assert "positionCard(latestTarget(),behavior)" in JS and "window.innerHeight*0.54" in JS

style=re.search(r"<style>[\s\S]*?</style>",TEXT)
start=TEXT.index('<div class="vg-root"')
end=TEXT.index('<script src=',start)
part=TEXT[start:end]
part=part.replace("{{ '/assets/liturgics/vigil-guided-data.json' | relative_url }}","/assets/liturgics/vigil-guided-data.json")
part=part.replace("{{ '/subjects/liturgics/2027/vespers-matins.html' | relative_url }}","/subjects/liturgics/2027/vespers-matins.html")
HTML='<!doctype html><html lang="ru"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">'+style.group()+'</head><body>'+part+'<script defer src="/assets/liturgics/vigil-guided.js"></script></body></html>'

def answer(page,step,kind,correct):
    assert kind in ("nameQuiz","quiz")
    quiz=STEPS[step-1][kind]
    choices=quiz["choices"]
    idx=next(i for i,c in enumerate(choices) if (c["stepId"]==quiz["correctStepId"])==correct)
    selector=f"#vg-step-{step} "+(".vg-name-quiz" if kind=="nameQuiz" else ".vg-quiz")
    page.locator(selector+" .vg-choice").nth(idx).click()
    assert page.locator(selector+" .vg-choice.is-correct").count()==1
    assert page.locator(selector+" .vg-choice.is-wrong").count()==(0 if correct else 1)

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
            settings={"headless":True,"args":["--no-sandbox"]}
            if chrome:settings["executable_path"]=chrome
            browser=p.chromium.launch(**settings)
            try:
                for width,height in [(1440,900),(390,844),(320,700)]:
                    page=browser.new_page(viewport={"width":width,"height":height})
                    errors=[]
                    page.on("pageerror",lambda e:errors.append(str(e)))
                    page.goto(url,wait_until="networkidle")
                    page.wait_for_selector("#vg-loaded:not([hidden])",timeout=15000)
                    assert page.locator(".vg-step").count()==1
                    assert "Восстаните" in page.locator("#vg-step-1 .vg-cue").inner_text()
                    assert page.locator("#vg-step-1 .vg-name").is_hidden()
                    assert page.locator("#vg-quiz-1").is_hidden()
                    assert page.locator("#vg-step-1 .vg-name-quiz .vg-choice").count()==len(STEPS[0]["nameQuiz"]["choices"])
                    answer(page,1,"nameQuiz",False)
                    assert page.locator("#vg-step-1 .vg-name").is_visible()
                    assert "Правильный ответ" in page.locator("#vg-step-1 .vg-name").inner_text()
                    page.wait_for_selector("#vg-quiz-1:not([hidden])",timeout=5000)
                    answer(page,1,"quiz",False)
                    page.wait_for_selector("#vg-step-2",timeout=5000)
                    assert page.locator("#vg-step-1 .vg-name").is_visible()
                    answer(page,2,"nameQuiz",True)
                    page.wait_for_selector("#vg-quiz-2:not([hidden])",timeout=5000)
                    answer(page,2,"quiz",True)
                    page.wait_for_selector("#vg-step-3",timeout=5000)
                    answer(page,3,"nameQuiz",True)
                    page.wait_for_selector("#vg-quiz-3:not([hidden])",timeout=5000)
                    answer(page,3,"quiz",False)
                    page.evaluate("window.scrollTo({top:0,behavior:'instant'})")
                    page.wait_for_selector("#vg-step-4",timeout=5000)
                    page.wait_for_timeout(300)
                    assert page.evaluate("window.scrollY")<200,"Upward reading was interrupted"
                    assert page.locator("#vg-jump").is_visible()
                    page.locator("#vg-jump").click()
                    page.wait_for_timeout(1000)
                    relative=page.locator("#vg-step-4").evaluate("(e)=>e.getBoundingClientRect().top/window.innerHeight")
                    assert 0.28<=relative<=0.72, f"Jump-to-current overshot the latest card: {relative:.2f} viewport heights"
                    assert page.locator("#vg-step-3").evaluate("(e)=>e.getBoundingClientRect().bottom>0"), "Previous answered card must remain visible above the new one"
                    page.reload(wait_until="networkidle")
                    page.wait_for_selector("#vg-loaded:not([hidden])")
                    assert page.locator(".vg-step").count()==4
                    assert page.locator("#vg-step-1 .vg-name-quiz .is-wrong").count()==1
                    assert page.locator("#vg-step-1 .vg-quiz .is-wrong").count()==1
                    assert page.locator("#vg-step-2 .vg-name-quiz .is-correct").count()==1
                    page.locator("#vg-map").evaluate("(e)=>e.open=true")
                    page.wait_for_function("document.querySelectorAll('#vg-menu button').length===72")
                    page.locator("#vg-menu button").last.click()
                    assert page.locator("#vg-step-72").count()==1
                    assert page.locator("#vg-results").count()==0
                    answer(page,72,"nameQuiz",True)
                    page.wait_for_selector("#vg-results",timeout=5000)
                    stats=page.locator("#vg-results").inner_text()
                    assert "Названия" in stats and "Последовательность" in stats
                    assert page.locator("#vg-results .vg-stat").nth(0).locator("strong").inner_text()=="4"
                    assert page.locator("#vg-results .vg-stat").nth(1).locator("strong").inner_text()=="3"
                    assert page.locator("#vg-results .vg-stat").nth(2).locator("strong").inner_text()=="136"
                    page.reload(wait_until="networkidle")
                    page.wait_for_selector("#vg-results")
                    assert not errors,errors
                    print(f"PASS {width}px: 72 naming and 71 order questions, automatic transitions, scroll and results")
                    page.close()
            finally:browser.close()
    finally:server.shutdown()
