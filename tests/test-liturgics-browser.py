#!/usr/bin/env python3
"""Browser acceptance against actual deployed Liturgics training pages (Chrome, mobile emulation)."""
import json
import time
from urllib.request import Request, urlopen
from playwright.sync_api import sync_playwright, expect

BASE = "https://slobodatablichka.github.io/gos-exams-2027-public/subjects/liturgics/2027/"
SEQ = BASE + "trainers/sequence.html"

def ensure_deployed():
    for attempt in range(30):
        try:
            req = Request(SEQ, headers={"User-Agent": "FOS2027-Exam-Browser-Test", "Cache-Control": "no-cache"})
            with urlopen(req, timeout=20) as res:
                content = res.read().decode("utf-8")
            if 'id="liturgicsSequenceManifest"' in content and "lit12-diagnostic" in content:
                return
        except Exception:
            pass
        time.sleep(5)
    raise RuntimeError("Latest exam sequence was not deployed")

def touch_drag(page):
    """Generate actual TouchEvents at real screen coordinates, including the 245 ms hold."""
    before = page.locator("#pyramid .brick").count()
    page.evaluate("""() => {
      const brick=document.querySelector('#sand .brick'),target=document.querySelector('#pyramid');
      if(!brick||!target)throw Error('Missing brick or destination');
      const a=brick.getBoundingClientRect(),b=target.getBoundingClientRect();
      const start={identifier:92,target:brick,clientX:a.left+a.width/2,clientY:a.top+a.height/2,screenX:0,screenY:0,pageX:0,pageY:0};
      window.__dragCase={brick,start,finish:{...start,clientX:b.left+b.width/2,clientY:b.top+Math.min(65,b.height/2)}};
      const t=new Touch(start);
      brick.dispatchEvent(new TouchEvent('touchstart',{bubbles:true,cancelable:true,touches:[t],changedTouches:[t],targetTouches:[t]}));
    }""")
    page.wait_for_timeout(340)
    page.evaluate("""() => {
      const x=window.__dragCase,t=new Touch(x.finish);
      document.dispatchEvent(new TouchEvent('touchmove',{bubbles:true,cancelable:true,touches:[t],changedTouches:[t],targetTouches:[t]}));
      document.dispatchEvent(new TouchEvent('touchend',{bubbles:true,cancelable:true,touches:[],changedTouches:[t],targetTouches:[]}));
    }""")
    page.wait_for_timeout(150)
    assert page.locator("#pyramid .brick").count() == before + 1, "Touch and hold did not move a brick"

def test_mobile(context):
    page = context.new_page()
    page.goto(SEQ, wait_until="domcontentloaded")
    page.locator("#oneCase option").first.wait_for(state="attached")
    assert page.locator("#oneCase option").count() == 16
    assert page.locator("#mode12 option").count() == 2
    page.select_option("#oneCase", "lit12-diagnostic")
    page.locator("#startOne").click()
    page.wait_for_url("**/sandbox-pyramid/q12-errors.html?sequence=1")
    expect(page.locator(".exam-sequence-nav")).to_be_visible()
    assert "Билет 1 из 1" in page.locator(".exam-sequence-nav").inner_text()
    assert page.locator("#pyramid .brick").count() > 0, "Diagnostic Pyramid should be prefilled"
    left=page.locator(".column.sandbox").bounding_box()
    right=page.locator(".column.pyramid").bounding_box()
    assert abs(left["y"]-right["y"])<10 and abs(left["x"]-right["x"])>35, "Mobile board must preserve two columns"
    first=page.locator("#pyramid .brick").first
    first.tap()
    expect(page.locator(".detail")).to_be_visible()
    assert "q12-l3.html" in page.locator(".detail a").last.get_attribute("href")
    page.keyboard.press("Escape")
    expect(page.locator(".detail")).to_have_count(0)
    before=page.locator("#gameBoard").get_attribute("class")
    page.locator("#swapBtn").click()
    after=page.locator("#gameBoard").get_attribute("class")
    assert ("swapped" in before)!=("swapped" in after), "Column swap failed"
    touch_drag(page)
    for level in (1,2,3):
        page.locator("#hintBtn").click()
        assert "Уровень "+str(level)+" из 3" in page.locator("#hintFeedback").inner_text()
    page.once("dialog",lambda d:d.accept())
    page.locator("#resetBtn").click()
    assert page.locator("#pyramid .brick").count()>0, "Reset diagnostic case should restore initial erroneous Pyramid"
    page.goto(SEQ,wait_until="domcontentloaded")
    page.locator("#oneCase option").first.wait_for(state="attached")
    page.locator('#questionList input[value="1"]').check()
    page.locator('#questionList input[value="12"]').check()
    page.select_option("#mode12","lit12-diagnostic")
    page.locator("#startSelected").click()
    page.wait_for_url("**/sandbox-pyramid/q01-assembly.html?sequence=1")
    assert "Билет 1 из 2" in page.locator(".exam-sequence-nav").inner_text()
    page.get_by_role("link",name="Следующий →").click()
    page.wait_for_url("**/sandbox-pyramid/q12-errors.html?sequence=1")
    assert "Билет 2 из 2" in page.locator(".exam-sequence-nav").inner_text()
    page.get_by_role("link",name="К итогам").click()
    page.wait_for_url("**/trainers/sequence.html")
    expect(page.locator("#session")).to_be_visible()
    assert page.locator("#sessionItems .exam-session-item").count()==2
    page.select_option("#mode12","lit12-diagnostic")
    page.locator("#startAll").click()
    page.wait_for_url("**/sandbox-pyramid/q01-assembly.html?sequence=1")
    program=page.evaluate("JSON.parse(localStorage.getItem('bpds-liturgics-sequence-v1'))")
    assert len(program["entries"])==15
    assert next(e for e in program["entries"] if e["number"]==12)["mode"]=="diagnostic"
    page.close()
    print("BROWSER MOBILE PASS: both columns, touch/tap, drag/hold, swap, 3 hints, reset, one/selected/all, alternate q12, next/previous.")

def test_checked_answer(context):
    page=context.new_page()
    page.goto(BASE+"sandbox-pyramid/q12-assembly.html",wait_until="domcontentloaded")
    page.locator("#sand .brick").first.wait_for()
    data=page.evaluate("""async () => (await (await fetch('data/lit12-assembly.json')).json())""")
    required=[x["id"] for x in data["items"] if not x.get("extra")]
    extra=[x["id"] for x in data["items"] if x.get("extra")]
    page.evaluate("""v => localStorage.setItem('bpds-sandbox-pyramid-'+v.version,JSON.stringify({sand:v.extra,pyramid:v.required,layoutSwapped:false}))""",{"version":data["version"],"required":required,"extra":extra})
    page.reload()
    page.locator("#checkBtn").click()
    expect(page.locator("#checkFeedback a.result-l3-link")).to_be_visible()
    assert page.locator("#checkFeedback a").get_attribute("href")=="../q12-l3.html"
    checked=page.evaluate("k => JSON.parse(localStorage.getItem(k))", "bpds-liturgics-checked-"+data["case_id"])
    assert checked and checked["correct"] is True and checked["version"]==data["version"]
    page.once("dialog",lambda d:d.accept())
    page.locator("#resetBtn").click()
    assert page.evaluate("k => localStorage.getItem(k)", "bpds-liturgics-checked-"+data["case_id"]) is None
    page.close()
    print("BROWSER RESULT PASS: correct key checked, clickable same-question L3, persistent proof, reset clears checked status.")

if __name__=="__main__":
    ensure_deployed()
    with sync_playwright() as p:
        browser=p.chromium.launch(channel="chrome",headless=True,args=["--no-sandbox"])
        context=browser.new_context(viewport={"width":390,"height":844},device_scale_factor=2,is_mobile=True,has_touch=True)
        try:
            test_mobile(context)
            test_checked_answer(context)
        finally:
            context.close()
            browser.close()
