"use strict";
(function(){
 const MANIFEST_ID="liturgicsSequenceManifest";
 const SESSION_KEY="bpds-liturgics-sequence-v1";
 const PROGRESS_PREFIX="bpds-sandbox-pyramid-";
 const CHECKED_PREFIX="bpds-liturgics-checked-";
 const errorNode=document.getElementById("sequenceError");
 function error(message){errorNode.hidden=false;errorNode.textContent=message;}
 let questions;
 try{
  const raw=JSON.parse(document.getElementById(MANIFEST_ID).textContent);
  if(!raw||!Array.isArray(raw.questions)||raw.questions.length!==15)throw Error("Нет 15 вопросов");
  questions=raw.questions;
  for(const q of questions)if(!q.cases.length||q.cases.some(c=>!c.case_id||!c.version||!/^sandbox-pyramid\/(?:index|vozdvizhenie|velikiy-post|q\d\d-(?:assembly|errors))\.html$/.test(c.path)))throw Error("Неправильный адрес игры №"+q.number);
 }catch(e){error("Не удалось загрузить реестр игр: "+e.message);return;}
 const questionByNumber=new Map(questions.map(q=>[q.number,q]));
 const choices=document.getElementById("questionList");
 const one=document.getElementById("oneCase");
 const mode12=document.getElementById("mode12");
 const btnSelected=document.getElementById("startSelected");
 const selectedCaseIds=new Map();
 const sessionNode=document.getElementById("session");
 function readJSON(key){try{const s=localStorage.getItem(key);return s?JSON.parse(s):null}catch(e){return null}}
 function pickCase(q){
  if(q.number===12){const requested=mode12.value;return q.cases.find(c=>c.case_id===requested)||q.cases[0];}
  return q.cases[0];
 }
 function caseLabel(q,c){
  return "№"+q.number+". "+q.title+(q.cases.length>1?" — "+c.label:"");
 }
 function fill(){
  questions.forEach(q=>{
   for(const c of q.cases){const option=document.createElement("option");option.value=c.case_id;option.textContent=caseLabel(q,c);one.append(option);}
   const row=document.createElement("div");row.className="exam-question";
   const label=document.createElement("label");const box=document.createElement("input");box.type="checkbox";box.value=String(q.number);box.addEventListener("change",()=>{btnSelected.disabled=!choices.querySelector("input:checked")});
   label.append(box,document.createTextNode("№"+q.number+". "+q.title));row.append(label);
   if(q.cases.length>1){
    const select=document.createElement("select");select.className="exam-case-choice";select.setAttribute("aria-label","Режим и вариант вопроса №"+q.number);
    for(const c of q.cases){const option=document.createElement("option");option.value=c.case_id;option.textContent=c.label;select.append(option)}
    select.addEventListener("change",()=>selectedCaseIds.set(q.number,select.value));row.append(select);
   }
   choices.append(row);
  });
  const q12=questionByNumber.get(12);
  for(const c of q12.cases){const option=document.createElement("option");option.value=c.case_id;option.textContent=c.label;mode12.append(option);}
 }
 function entryFor(q,c){return{number:q.number,case_id:c.case_id,version:c.version,path:c.path,mode:c.mode};}
 function validSession(s){
  if(!s||s.v!==1||!Array.isArray(s.entries)||!s.entries.length||s.entries.length>15||!Number.isInteger(s.index)||s.index<0||s.index>=s.entries.length)return false;
  const seen=new Set();
  return s.entries.every(e=>{
   if(seen.has(e.number))return false;seen.add(e.number);
   const q=questionByNumber.get(e.number);
   return !!q&&q.cases.some(c=>c.case_id===e.case_id&&c.version===e.version&&c.path===e.path&&c.mode===e.mode);
  });
 }
 function currentSession(){const s=readJSON(SESSION_KEY);return validSession(s)?s:null;}
 function saveSession(session){try{localStorage.setItem(SESSION_KEY,JSON.stringify(session));return true}catch(e){error("Браузер не разрешает сохранять прохождение. Проверьте настройки хранилища.");return false}}
 function toGame(entry){
  if(!entry||!/^sandbox-pyramid\/(?:index|vozdvizhenie|velikiy-post|q\d\d-(?:assembly|errors))\.html$/.test(entry.path))return;
  window.location.href="../"+entry.path+"?sequence=1";
 }
 function launch(selected,mode){
  if(!selected.length)return;
  const entries=selected.map(({q,c})=>entryFor(q,c));
  const session={v:1,mode,entries,index:0};
  if(saveSession(session))toGame(entries[0]);
 }
 function gameStatus(e){
  const checked=readJSON(CHECKED_PREFIX+e.case_id);
  if(checked&&checked.correct===true&&checked.version===e.version)return{label:"Проверено",cls:"checked"};
  const attempt=readJSON(PROGRESS_PREFIX+e.version);
  if(attempt&&Array.isArray(attempt.pyramid)&&attempt.pyramid.length)return{label:"В работе",cls:""};
  return{label:"Не начато",cls:""};
 }
 function renderSession(){
  const s=currentSession();
  sessionNode.hidden=!s;
  if(!s)return;
  const checks=s.entries.filter(e=>gameStatus(e).cls==="checked").length;
  document.getElementById("sessionSummary").textContent=s.mode+" · Проверено "+checks+" из "+s.entries.length+". Можно продолжать с любого вопроса; прежние сборки сохраняются.";
  const items=document.getElementById("sessionItems");items.replaceChildren();
  s.entries.forEach((e,index)=>{
   const q=questionByNumber.get(e.number),c=q.cases.find(c=>c.case_id===e.case_id),status=gameStatus(e);
   const row=document.createElement("div");row.className="exam-session-item";
   const link=document.createElement("a");link.href="../"+e.path+"?sequence=1";link.textContent=(index===s.index?"● ":"")+caseLabel(q,c);link.addEventListener("click",()=>{s.index=index;saveSession(s)});
   const badge=document.createElement("span");badge.className="exam-status "+status.cls;badge.textContent=status.label;
   row.append(link,badge);items.append(row);
  });
  const continueButton=document.getElementById("continue");
  continueButton.textContent=checks===s.entries.length?"Открыть последний билет":"Продолжить";
  continueButton.onclick=()=>{const t=currentSession();if(t)toGame(t.entries[t.index])};
 }
 fill();
 document.getElementById("startOne").addEventListener("click",()=>{
  const c=questions.flatMap(q=>q.cases.map(c=>({q,c}))).find(x=>x.c.case_id===one.value);
  if(c)launch([c],"Один вопрос");
 });
 document.getElementById("startSelected").addEventListener("click",()=>{
  const nums=[...choices.querySelectorAll("input:checked")].map(x=>Number(x.value)).sort((a,b)=>a-b);
  launch(nums.map(n=>{const q=questionByNumber.get(n);return{q,c:q.cases.find(c=>c.case_id===selectedCaseIds.get(n))||pickCase(q)}}),"Выбранные вопросы");
 });
 document.getElementById("startAll").addEventListener("click",()=>launch(questions.map(q=>({q,c:pickCase(q)})),"Все 15 вопросов"));
 document.getElementById("end").addEventListener("click",()=>{
  if(!confirm("Завершить текущее прохождение? Результаты отдельных игр останутся сохранёнными."))return;
  try{localStorage.removeItem(SESSION_KEY)}catch(e){}renderSession();
 });
 window.addEventListener("pageshow",renderSession);
 renderSession();
})();
