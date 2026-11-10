#!/usr/bin/env python3
"""Inventory source links in all 450 current answers; test unique library HTML and anchors.
A valid URL/anchor is NOT evidence that chapter text supports the answer."""
from pathlib import Path
from urllib.parse import urlsplit,urlunsplit,unquote
from urllib.request import Request,urlopen
from urllib.error import HTTPError
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor,as_completed
from collections import Counter
import json,re
R=Path(__file__).resolve().parents[1]
SUBS=("nt","ot","oi","rpc","dogmatics","liturgics")
URL=re.compile(r'https?://[^\s)\]>"' + "'" + r'\`]+')
LABEL=re.compile(r'\[([^\]\n]{1,200})\]\((https?://[^)\s]+)\)')
class IDs(HTMLParser):
 def __init__(self):super().__init__();self.ids=set()
 def handle_starttag(self,tag,attrs):
  for k,v in attrs:
   if k in ("id","name") and v:self.ids.add(v)
 handle_startendtag=handle_starttag
def test(url):
 try:
  with urlopen(Request(url,headers={"User-Agent":"GosExams-2027-chapter-link-audit"}),timeout=12) as f:
   status=f.status;typ=f.headers.get("Content-Type","")
   data=f.read(7000001) if "html" in typ.lower() else b""
   truncated=len(data)>7000000
   h=IDs()
   try:h.feed(data[:7000000].decode(f.headers.get_content_charset() or "utf-8",errors="replace"))
   except Exception:pass
   return {"status":status,"checked":True,"ids":h.ids,"truncated":truncated,"error":None}
 except HTTPError as e:return {"status":e.code,"checked":True,"ids":set(),"truncated":False,"error":str(e)}
 except Exception as e:return {"status":None,"checked":False,"ids":set(),"truncated":False,"error":type(e).__name__+":"+str(e)[:100]}
def main():
 data=[];pages=set();count=Counter()
 for s in SUBS:
  for n in range(1,26):
   q={"question_id":f"{s}-2027-{n:02d}","subject_id":s,"number":n,"references":[],"levels":{},"status":"verification_needed"}
   for level in ("l3","l2","l1"):
    f=R/f"subjects/{s}/2027/q{n:02d}-{level}.md"
    if not f.is_file():q["levels"][level]={"present":False};count["missing_files"]+=1;continue
    t=f.read_text(encoding="utf-8");labels=dict((m.group(2).rstrip(".,;"),m.group(1)) for m in LABEL.finditer(t))
    urls=set(x.group(0).rstrip(".,;") for x in URL.finditer(t) if urlsplit(x.group(0)).netloc=="library.logoscosmos.org")
    q["levels"][level]={"present":True,"links":len(urls)};count["answer_pages"]+=1
    if level=="l3" and not urls:count["l3_without_library_link"]+=1
    for url in sorted(urls):
     sp=urlsplit(url);page=urlunsplit((sp.scheme,sp.netloc,sp.path,sp.query,""));pages.add(page)
     form="anchor" if sp.fragment else ("book_index" if sp.path.endswith("/index.html") else ("chapter_page_candidate" if re.search(r'(?:chapter|part|index_split)[_-]\d+',sp.path) else "other_page"))
     q["references"].append({"level":level,"url":url,"label":labels.get(url),"page":page,"fragment":unquote(sp.fragment) or None,"url_type":form})
   data.append(q)
 count["questions"]=len(data);count["distinct_html_pages_to_test"]=len(pages)
 results={}
 with ThreadPoolExecutor(max_workers=8) as pool:
  fs={pool.submit(test,u):u for u in sorted(pages)}
  for f in as_completed(fs):results[fs[f]]=f.result()
 for q in data:
  exact=0
  for r in q["references"]:
   t=results[r["page"]];ok=t["status"]==200
   r["http_status"]=t["status"];r["http_checked"]=t["checked"];r["http_error"]=t["error"]
   r["server_verified"]=ok
   r["chapter_url_verified"]=bool(ok and ((r["fragment"] and r["fragment"] in t["ids"] and not t["truncated"]) or (r["url_type"]=="chapter_page_candidate" and not r["fragment"])))
   r["content_verified"]=False
   count["source_link_occurrences"]+=1
   count["url_type_"+r["url_type"]]+=1
   if ok:count["source_links_http_200"]+=1
   if r["chapter_url_verified"]:count["technically_verified_chapter_links"]+=1;exact+=1
  if exact:q["status"]="partial_chapter_url_verified_content_pending";count["questions_with_some_verified_chapter"]+=1
  if not q["references"]:count["questions_without_library_links"]+=1
 count["unique_library_urls"]=len(set(ref["url"] for q in data for ref in q["references"]))
 count["http_pages_200"]=sum(x["status"]==200 for x in results.values())
 count["http_pages_error_or_unchecked"]=len(results)-count["http_pages_200"]
 count["content_verified"]=0
 summary={"method":"450 L1/L2/L3 markdown source URL extraction + library HTTP/anchor probe; NO chapter-to-claim textual verification","counts":dict(count),"by_subject":{s:{"some_chapter_url_verified":sum(x["status"]!="verification_needed" for x in data if x["subject_id"]==s),"without_library_links":sum(not x["references"] for x in data if x["subject_id"]==s)} for s in SUBS},"http_failures":[{"url":u,"status":v["status"],"error":v["error"]} for u,v in sorted(results.items()) if v["status"]!=200]}
 obj={"audit_date":"2026-11-10","summary":summary,"questions":data,"statuses_disclaimer":"HTTP 200 and an existing anchor are not evidence that its chapter contains any specific factual claim. No content_verified=true is assigned."}
 out=R/"planning/data";out.mkdir(exist_ok=True,parents=True)
 (out/"site-2027-source-links.json").write_text(json.dumps(obj,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
 md=["# Этап 3 — источники и точные ссылки библиотеки","",
 "**Выполнена проверка файлов и HTTP/якорей; содержательная сверка глав с тезисами ответов остаётся отдельной работой.**",
 "","## Машинный итог","","| Показатель | Число |","|---|---:|"]
 md.extend(f"| {k} | {v} |" for k,v in sorted(count.items()))
 md+=["","## Дисциплины","","| Дисциплина | Есть технически проверенная глава | Нет ссылок на библиотеку |","|---|---:|---:|"]
 for s,x in summary["by_subject"].items():md.append(f"| {s} | {x['some_chapter_url_verified']} | {x['without_library_links']} |")
 md+=["","## Незакрытые случаи","","Вопросы без технически подтверждённой главы:"]
 for s in SUBS:
  miss=[x["number"] for x in data if x["subject_id"]==s and x["status"]=="verification_needed"]
  md.append(f"- {s}: "+(", ".join(f"№{n}" for n in miss) or "нет; содержание всё равно не проверено"))
 md+=["","## Недоступные HTML адреса","","Все необработанные/отклонённые адреса содержатся в JSON."]
 md.extend("- "+(str(f["status"]) if f["status"] else "не проверено")+": "+f["url"] for f in summary["http_failures"][:25])
 (out/"site-2027-source-links-summary.md").write_text("\n".join(md)+"\n",encoding="utf-8")
 print("STAGE3_SUMMARY="+json.dumps(summary,ensure_ascii=False))
if __name__=="__main__":main()
