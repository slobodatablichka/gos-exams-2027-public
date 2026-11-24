#!/usr/bin/env python3
"""Browser acceptance: guided-vigil 72-step quiz, ribbon, restore and statistics."""
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
assert [sum(s["section"]==section for s in STEPS) for section in ["Великая вечерня","Утреня","Первый час"]]==[29,34,9]
assert all(s["title"] and s["cue"] and s["definition"] and s["question"] and s["answer"] for s in STEPS)
assert all(s["nextStepId"]==(STEPS[i+1]["id"] if i<71 else None) for i,s in enumerate(STEPS))
assert all(s["quiz"] and len(s["quiz"]["choices"])==3 and s["quiz"]["correctStepId"]==STEPS[i+1]["id"] and
  sum(c["stepId"]==s["quiz"]["correctStepId"] for c in s["quiz"]["choices"])==1 and
  len(set(c["label"] for c in s["quiz"]["choices"]))==3 and
  len(set(c["stepId"] for c in s["quiz"]["choices"]))==3 for i,s in enumerate(STEPS[:71]))
assert STEPS[-1]["quiz"] is None
assert len(DATA["lessons"])==2
assert all(sum(b[1] for b in l["blocks"])==150 for l in DATA["lessons"])
assert not re.search(r"знакомые с детства|знакомые нам с детства|с детских лет",TEXT,re.I)
assert not re.search(r"<audio|<video",TEXT,re.I)
assert "gos-exams-vigil-guided-2027-v1" in JS
assert all("id=\""+x+"\"" in TEXT for x in ["vg-choices","vg-feedback","vg-ribbon","vg-summary","vg-finish","vg-new-run","vg-map","vg-conditions"])
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
    worker=threading.Thread(target=server.serve_forever,daemon=True)
    worker.start()
    url=f"http://127.0.0.1:{server.server_port}/"
    try:
        with sync_playwright() as p:
            chrome=shutil.which("google-chrome") or shutil.which("chromium") or shutil.which("chromium-browser")
            kw={"headless":True,"args":["--no-sandbox"]}
            if chrome:kw["executable_path"]=chrome
            browser=p.chromium.launch(**kw)
            try:
                for width,height in [(1440,900),(390,844),(320,700)]:
                    page=browser.new_page(viewport={"width":width,"height":height})
                    errors=[]
                    page.on("pageerror",lambda e:errors.append(str(e)))
                    page.goto(url,wait_until="networkidle")
                    page.wait_for_selector("#vg-loaded:not([hidden])",timeout=15000)
                    assert not errors,errors
                    assert page.locator("#vg-counter").inner_text()=="1 / 72"
                    assert "Восстаните" in page.locator("#vg-cue").inner_text()
                    assert page.locator("#vg-title").is_hidden()
                    assert page.locator("#vg-quiz").is_hidden()
                    page.locator("#vg-show-name").click()
                    assert "Приглашение" in page.locator("#vg-title").inner_text()
                    assert page.locator("#vg-choices button").count()==3
                    wrong=next(i for i,c in enumerate(STEPS[0]["quiz"]["choices"]) if c["stepId"]!=STEPS[1]["id"])
                    page.locator("#vg-choices button").nth(wrong).click()
                    assert page.locator("#vg-choices button.is-correct").count()==1
                    assert page.locator("#vg-choices button.is-wrong").count()==1
                    assert "Правильный ответ" in page.locator("#vg-feedback").inner_text()
                    page.locator("#vg-forward").click()
                    assert page.locator("#vg-counter").inner_text()=="2 / 72"
                    assert page.locator("#vg-ribbon .vg-ribbon-item").count()==2
                    page.locator("#vg-show-name").click()
                    correct=next(i for i,c in enumerate(STEPS[1]["quiz"]["choices"]) if c["stepId"]==STEPS[2]["id"])
                    page.locator("#vg-choices button").nth(correct).click()
                    assert page.locator("#vg-choices button.is-correct").count()==1
                    assert "Верно" in page.locator("#vg-feedback").inner_text()
                    page.reload(wait_until="networkidle")
                    page.wait_for_selector("#vg-loaded:not([hidden])")
                    assert page.locator("#vg-counter").inner_text()=="2 / 72"
                    page.locator("#vg-show-name").click()
                    assert page.locator("#vg-choices button.is-correct").count()==1
                    page.locator("#vg-map").evaluate("(el)=>el.open=true")
                    page.wait_for_function("document.querySelectorAll('#vg-menu button').length === 72")
                    page.locator("#vg-menu button").nth(6).click()
                    assert page.locator("#vg-counter").inner_text()=="7 / 72"
                    page.locator("#vg-more").evaluate("(el)=>el.open=true")
                    assert "Уставные варианты" in page.locator("#vg-more").inner_text()
                    page.locator("#vg-conditions").evaluate("(el)=>el.open=true")
                    assert "Блажен муж" in page.locator("#vg-conditions-list").inner_text()
                    page.goto(url+"#step-53",wait_until="networkidle")
                    assert page.locator("#vg-counter").inner_text()=="53 / 72"
                    page.locator("#vg-more").evaluate("(el)=>el.open=true")
                    page.locator("#vg-conditions").evaluate("(el)=>el.open=true")
                    assert "припев" in page.locator("#vg-conditions-list").inner_text().lower()
                    page.locator("#vg-section button").nth(2).click()
                    assert page.locator("#vg-counter").inner_text()=="64 / 72"
                    page.locator("#vg-back").click()
                    assert page.locator("#vg-counter").inner_text()=="63 / 72"
                    page.locator("#vg-map").evaluate("(el)=>el.open=true")
                    page.locator("#vg-menu button").last.click()
                    assert page.locator("#vg-counter").inner_text()=="72 / 72"
                    assert page.locator("#vg-forward").is_disabled()
                    page.locator("#vg-finish").click()
                    stats=page.locator("#vg-summary").inner_text()
                    assert "Ошибок" in stats and "Пропуск" not in stats
                    assert "Без ответа" in stats and "Точность" in stats and "Время" in stats
                    assert page.locator("#vg-summary .vg-stat").nth(0).locator("strong").inner_text()=="1"  # correct
                    assert page.locator("#vg-summary .vg-stat").nth(1).locator("strong").inner_text()=="1"  # wrong
                    assert page.locator("#vg-summary .vg-stat").nth(2).locator("strong").inner_text()=="69" # unanswered
                    page.reload(wait_until="networkidle")
                    page.wait_for_selector("#vg-loaded:not([hidden])")
                    assert page.locator("#vg-summary").is_visible()
                    page.locator("#vg-ribbon .vg-ribbon-item").first.click()
                    assert page.locator("#vg-counter").inner_text()=="1 / 72"
                    page.locator("#vg-course").evaluate("(el)=>el.parentElement.open=true")
                    assert page.locator("#vg-course .vg-lesson").count()==2
                    assert not errors,errors
                    print(f"PASS {width}px: three-choice quiz, wrong/right, ribbon, navigation, restore, statistics")
                    page.close()
            finally:browser.close()
    finally:server.shutdown()
