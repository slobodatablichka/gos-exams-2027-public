"use strict";
(()=>{
const root=document.querySelector("#vigil-guide");if(!root)return;
const el=(tag,content,cls)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(content!==undefined&&content!==null)n.textContent=String(content);return n};
const by=id=>root.querySelector("#"+id);
const nodes={
 status:by("vg-status"),loaded:by("vg-loaded"),menu:by("vg-menu"),map:by("vg-map"),
 section:by("vg-section"),counter:by("vg-counter"),progress:by("vg-progress"),
 title:by("vg-title"),role:by("vg-role"),cue:by("vg-cue"),definition:by("vg-definition"),
 showname:by("vg-show-name"),quiz:by("vg-quiz"),choices:by("vg-choices"),feedback:by("vg-feedback"),
 next:by("vg-forward"),previous:by("vg-back"),training:by("vg-training"),reset:by("vg-reset"),
 ribbon:by("vg-ribbon"),ribbonCount:by("vg-ribbon-count"),
 more:by("vg-more"),question:by("vg-question"),answer:by("vg-answer"),
 parts:by("vg-detail-elements"),partsList:by("vg-detail-list"),
 conditions:by("vg-conditions"),conditionsList:by("vg-conditions-list"),
 link:by("vg-table-link"),source:by("vg-source"),course:by("vg-course"),
 completion:by("vg-complete"),summary:by("vg-summary"),finish:by("vg-finish"),newRun:by("vg-new-run")
};
const storageKey="gos-exams-vigil-guided-2027-v1";
const sectionKeys=["Великая вечерня","Утреня","Первый час"];
let data,index=0,training=true,seen=new Set([0]),answers={},elapsedMs=0,completed=false,visibleName=false;
let tickerStart=null,lastIndex=null;
function safeLoad(){try{return JSON.parse(localStorage.getItem(storageKey)||"null")}catch(_){return null}}
function persist(){try{localStorage.setItem(storageKey,JSON.stringify({index,training,seen:[...seen],answers,elapsedMs,completed}))}catch(_){}}
function elapsedTick(){
 if(tickerStart!==null&&!completed){elapsedMs+=Math.max(0,performance.now()-tickerStart);tickerStart=performance.now()}
}
function stopClock(){elapsedTick();tickerStart=null;persist()}
function startClock(){if(!document.hidden&&!completed&&tickerStart===null)tickerStart=performance.now()}
function formatTime(ms){const sec=Math.floor(ms/1000),h=Math.floor(sec/3600),m=Math.floor(sec%3600/60),s=sec%60;return h?String(h)+" ч "+String(m).padStart(2,"0")+" мин":String(m)+" мин "+String(s).padStart(2,"0")+" с"}
function restore(){
 const saved=safeLoad();
 if(saved&&Number.isInteger(saved.index)&&saved.index>=0&&saved.index<data.steps.length)index=saved.index;
 if(saved&&typeof saved.training==="boolean")training=saved.training;
 if(saved&&Array.isArray(saved.seen)){seen=new Set(saved.seen.filter(i=>Number.isInteger(i)&&i>=0&&i<data.steps.length))}
 else if(saved&&Number.isInteger(saved.index)){seen=new Set(Array.from({length:index+1},(_,i)=>i))}
 if(saved&&saved.answers&&typeof saved.answers==="object"){
  answers={};
  for(const [key,value] of Object.entries(saved.answers)){
   const n=data.steps.findIndex(s=>s.id===key);
   if(n<0||n>=data.steps.length-1||!value||typeof value.selected!=="string")continue;
   const quiz=data.steps[n].quiz;
   if(quiz&&quiz.choices.some(c=>c.stepId===value.selected))answers[key]={selected:value.selected,correct:value.selected===quiz.correctStepId};
  }
 }
 elapsedMs=Number.isFinite(saved?.elapsedMs)&&saved.elapsedMs>=0?saved.elapsedMs:0;
 completed=saved?.completed===true;
 const hash=(location.hash||"").match(/^#step-(\d+)$/);
 if(hash){const target=Number(hash[1])-1;if(target>=0&&target<data.steps.length)index=target}
 seen.add(index);visibleName=!training;nodes.training.checked=training;
}
function setStep(n){
 if(n<0||n>=data.steps.length)return;
 elapsedTick();index=n;seen.add(n);visibleName=!training;lastIndex=n;
 nodes.more.open=false;persist();render();
 try{history.replaceState(null,"","#step-"+(index+1))}catch(_){}
}
function button(text,fn,cls){const b=el("button",text,cls);b.type="button";b.addEventListener("click",fn);return b}
function resetRun(){
 if(!window.confirm("Начать заново? Ответы и время текущего прохождения будут сброшены."))return;
 stopClock();index=0;training=nodes.training.checked;seen=new Set([0]);answers={};elapsedMs=0;completed=false;visibleName=!training;
 nodes.more.open=false;persist();startClock();setStep(0);
}
function renderSections(){
 nodes.section.replaceChildren();
 for(const section of sectionKeys){
  const n=data.steps.findIndex(s=>s.section===section),b=button(section,()=>setStep(n),"vg-section-button");
  b.setAttribute("aria-pressed",String(data.steps[index].section===section));nodes.section.append(b)
 }
}
function renderMap(){
 nodes.menu.replaceChildren();
 data.steps.forEach((s,i)=>{const b=button((i+1)+". "+s.title,()=>{setStep(i);nodes.map.open=false},"vg-map-item");if(i===index)b.setAttribute("aria-current","step");nodes.menu.append(b)})
}
function renderRibbon(){
 nodes.ribbon.replaceChildren();
 const visited=[...seen].sort((a,b)=>a-b);nodes.ribbonCount.textContent=visited.length+" / "+data.steps.length;
 let prev="";
 for(const i of visited){
  const s=data.steps[i];
  if(prev!==s.section){nodes.ribbon.append(el("div",s.section,"vg-ribbon-section"));prev=s.section}
  const b=button((i+1)+". "+s.title,()=>setStep(i),"vg-ribbon-item");
  if(i===index)b.setAttribute("aria-current","step");
  if(answers[s.id]?.correct)b.classList.add("is-correct");
  else if(answers[s.id]&&!answers[s.id].correct)b.classList.add("is-wrong");
  nodes.ribbon.append(b)
 }
 if(lastIndex!==null){
  const current=nodes.ribbon.querySelector('[aria-current="step"]');
  if(current)nodes.ribbon.scrollTop=Math.max(0,current.offsetTop-nodes.ribbon.offsetTop-nodes.ribbon.clientHeight/2);
  lastIndex=null;
 }
}
function renderCourse(){
 nodes.course.replaceChildren();
 for(const l of data.lessons){
  const pane=el("section",undefined,"vg-lesson");pane.append(el("h3",l.title),el("p",l.focus),el("p",l.duration,"vg-muted"));
  const list=el("ol");for(const [name,min] of l.blocks)list.append(el("li",name+" — "+min+" мин"));
  pane.append(list);nodes.course.append(pane)
 }
}
function renderDetails(s){
 nodes.question.textContent=s.question;nodes.answer.textContent=s.answer;
 nodes.parts.hidden=!s.subelements?.length;nodes.partsList.replaceChildren();
 for(const x of s.subelements||[])nodes.partsList.append(el("li",x));
 nodes.conditions.hidden=!s.conditions?.length;nodes.conditionsList.replaceChildren();
 for(const x of s.conditions||[]){const li=el("li");li.append(el("strong",x.condition+": "),document.createTextNode(x.text));nodes.conditionsList.append(li)}
 nodes.link.hidden=!s.compare;
 if(s.compare)nodes.link.href=root.dataset.compare+"?row="+encodeURIComponent(s.compare);
 const source=data.sources.find(x=>x.code===s.source);
 nodes.source.textContent="Источник: "+(source?.name||"Архиеп. Аверкий (Таушев)")+"; примеры Колобанова и игум. Кронида; уставные варианты — по Типикону.";
}
function renderChoices(s){
 nodes.choices.replaceChildren();nodes.feedback.replaceChildren();
 const quiz=s.quiz,answered=answers[s.id];
 quiz.choices.forEach((item,i)=>{
  const b=button((i+1)+". "+item.label,()=>chooseAnswer(s.id,item.stepId),"vg-choice");
  if(answered){
   b.disabled=true;
   if(item.stepId===quiz.correctStepId)b.classList.add("is-correct");
   else if(item.stepId===answered.selected)b.classList.add("is-wrong");
  }
  nodes.choices.append(b)
 });
 if(answered){
  const text=answered.correct?"Верно.":"Правильный ответ: "+data.steps[index+1].title+".";
  nodes.feedback.append(el("p",text,answered.correct?"vg-good":"vg-error"));
  if(!answered.correct)nodes.feedback.append(el("p","Следующий учебный шаг — "+data.steps[index+1].title+".","vg-muted"));
 }
}
function chooseAnswer(id,selected){
 if(answers[id]||completed)return;
 const s=data.steps[index];if(s.id!==id||!s.quiz)return;
 elapsedTick();answers[id]={selected,correct:selected===s.quiz.correctStepId};persist();render();
}
function renderSummary(){
 const entries=Object.values(answers),right=entries.filter(x=>x.correct).length,wrong=entries.length-right;
 const total=data.steps.length-1,missed=total-entries.length,rate=entries.length?Math.round(right/entries.length*100):0;
 nodes.summary.replaceChildren();
 for(const [title,value] of [["Правильных",right],["Ошибок",wrong],["Без ответа",missed],["Точность",rate+"%"],["Время",formatTime(elapsedMs)]]){
  const p=el("div",undefined,"vg-stat");p.append(el("span",title),el("strong",value));nodes.summary.append(p)
 }
 const missedSteps=data.steps.slice(0,-1).filter(s=>answers[s.id]&&!answers[s.id].correct);
 if(missedSteps.length){
  const p=el("p","Где были ошибки: "+missedSteps.map(s=>s.id.slice(1)+" — "+s.title).join("; "),"vg-muted");nodes.summary.append(p)
 }
}
function finishRun(){
 if(!seen.has(data.steps.length-1))return;
 elapsedTick();completed=true;tickerStart=null;persist();render();
}
function render(){
 const s=data.steps[index],last=index===data.steps.length-1,show=visibleName||!training;
 nodes.counter.textContent=(index+1)+" / "+data.steps.length;nodes.progress.max=data.steps.length;nodes.progress.value=index+1;
 nodes.role.textContent=s.actor;nodes.cue.textContent=s.cue;nodes.title.textContent=s.title;nodes.title.hidden=!show;
 nodes.definition.textContent=s.definition;nodes.definition.hidden=!show;nodes.showname.hidden=show;
 nodes.quiz.hidden=!show||last;nodes.completion.hidden=!last;nodes.finish.hidden=!last||completed;nodes.summary.hidden=!completed;
 nodes.newRun.hidden=!completed;
 if(show&&!last)renderChoices(s);
 if(completed)renderSummary();
 renderDetails(s);
 nodes.previous.disabled=index===0;nodes.next.disabled=last;nodes.next.textContent=last?"Последование завершено":"Далее →";
 renderSections();renderRibbon();if(nodes.map.open)renderMap();
}
nodes.next.addEventListener("click",()=>setStep(index+1));
nodes.previous.addEventListener("click",()=>setStep(index-1));
nodes.showname.addEventListener("click",()=>{visibleName=true;render()});
nodes.training.addEventListener("change",()=>{training=nodes.training.checked;visibleName=!training;persist();render()});
nodes.reset.addEventListener("click",resetRun);
nodes.finish.addEventListener("click",finishRun);
nodes.newRun.addEventListener("click",resetRun);
nodes.map.addEventListener("toggle",()=>{if(nodes.map.open)renderMap()});
document.addEventListener("visibilitychange",()=>{if(document.hidden)stopClock();else startClock()});
window.addEventListener("pagehide",stopClock);
setInterval(()=>{if(!document.hidden&&!completed){elapsedTick();persist()}},5000);
async function load(){
 const response=await fetch(root.dataset.source);if(!response.ok)throw Error("HTTP "+response.status);
 data=await response.json();
 if(data.steps.length!==72||!data.steps.slice(0,-1).every((s,i)=>s.quiz?.correctStepId===data.steps[i+1].id&&s.quiz.choices.length===3))throw Error("Неполное последование викторины");
 restore();renderCourse();render();nodes.status.hidden=true;nodes.loaded.hidden=false;startClock();
}
load().catch(err=>{nodes.status.textContent="Не удалось открыть последование. Обновите страницу.";console.error(err)});
})();