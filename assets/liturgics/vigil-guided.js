"use strict";
(()=>{
const root=document.querySelector("#vigil-guide");if(!root)return;
const by=id=>root.querySelector("#"+id);
const el=(tag,text,cls)=>{const n=document.createElement(tag);if(cls)n.className=cls;if(text!==undefined&&text!==null)n.textContent=String(text);return n};
const dataUrl=root.dataset.source,compareUrl=root.dataset.compare;
const storageKey="gos-exams-vigil-guided-2027-v1";
const sectionKeys=["Великая вечерня","Утреня","Первый час"];
const nodes={status:by("vg-status"),loaded:by("vg-loaded"),stream:by("vg-stream"),jump:by("vg-jump"),counter:by("vg-counter"),progress:by("vg-progress"),course:by("vg-course"),map:by("vg-map"),menu:by("vg-menu"),reset:by("vg-reset")};
const button=(label,fn,cls)=>{const b=el("button",label,cls);b.type="button";b.addEventListener("click",fn);return b};
let data,frontier=0,answers={},nameAnswers={},revealed=new Set(),quizShown=new Set(),elapsedMs=0,completed=false,tickStart=null;
let quizTimers=new Set(),advanceTimer=null,runVersion=0;
let scrollRevision=0,lastScrollY=window.scrollY,browsingHistory=false;
function readSaved(){try{return JSON.parse(localStorage.getItem(storageKey)||"null")}catch(_){return null}}
function store(){try{localStorage.setItem(storageKey,JSON.stringify({index:frontier,frontier,seen:Array.from({length:frontier+1},(_,i)=>i),answers,nameAnswers,revealed:[...revealed],quizShown:[...quizShown],elapsedMs,completed}))}catch(_){}}
function tick(){if(tickStart!==null&&!completed){elapsedMs+=Math.max(0,performance.now()-tickStart);tickStart=performance.now()}}
function pause(){tick();tickStart=null;store()}
function resume(){if(!document.hidden&&!completed&&tickStart===null)tickStart=performance.now()}
function prettyTime(ms){const sec=Math.floor(ms/1000),h=Math.floor(sec/3600),m=Math.floor(sec%3600/60),s=sec%60;return h?h+" ч "+String(m).padStart(2,"0")+" мин":m+" мин "+String(s).padStart(2,"0")+" с"}
function restore(){
 const save=readSaved();
 if(save){
  const n=Number.isInteger(save.frontier)?save.frontier:Number.isInteger(save.index)?save.index:0;
  frontier=Math.min(data.steps.length-1,Math.max(0,n));
  if(Array.isArray(save.seen))for(const i of save.seen)if(Number.isInteger(i)&&i>=0&&i<data.steps.length)frontier=Math.max(frontier,i);
  elapsedMs=Number.isFinite(save.elapsedMs)&&save.elapsedMs>=0?save.elapsedMs:0;
  completed=save.completed===true;
  for(const [id,value] of Object.entries(save.answers||{})){
   const s=data.steps.find(step=>step.id===id);
   if(s?.quiz&&s.quiz.choices.some(c=>c.stepId===value?.selected))
    answers[id]={selected:value.selected,correct:value.selected===s.quiz.correctStepId};
  }
  // Do not treat earlier "show name" reveals as passed naming tests.
  for(const [id,value] of Object.entries(save.nameAnswers||{})){
   const s=data.steps.find(step=>step.id===id);
   if(s?.nameQuiz?.choices.some(c=>c.stepId===value?.selected))
    nameAnswers[id]={selected:value.selected,correct:value.selected===s.nameQuiz.correctStepId};
  }
  revealed=new Set(Object.keys(nameAnswers));
  if(Array.isArray(save.quizShown))quizShown=new Set(save.quizShown.filter(x=>revealed.has(x)));
  for(const id of Object.keys(nameAnswers))if(id!==data.steps[frontier]?.id)quizShown.add(id);
  for(const id of Object.keys(answers))if(revealed.has(id))quizShown.add(id);
 }
 const hash=(location.hash||"").match(/^#step-(\d+)$/);
 if(hash){const i=Number(hash[1])-1;if(i>=0&&i<data.steps.length)frontier=Math.max(frontier,i)}
 if(completed&&!nameAnswers[data.steps[71].id])completed=false;
}
function currentCard(){return by("vg-step-"+(frontier+1))}
function latestTarget(){return completed&&by("vg-results")?by("vg-results"):currentCard()}
function setHash(i){try{history.replaceState(null,"","#step-"+(i+1))}catch(_){}}
function nearLatest(){
 const card=currentCard();if(!card)return true;
 const bounds=card.getBoundingClientRect();
 return bounds.top<window.innerHeight-80&&bounds.bottom>50;
}
function updateJump(){
 const card=latestTarget();if(!card)return;
 const r=card.getBoundingClientRect();
 // Visible only when the latest card lies below the viewport (after looking back up).
 nodes.jump.hidden=!(r.top>window.innerHeight-110||(browsingHistory&&r.top>120));
}
function scrollToEnd(behavior="smooth"){
 const n=latestTarget();if(!n)return;
 browsingHistory=false;n.scrollIntoView({behavior,block:"start"});updateJump();
}
function scrollToCard(i,behavior="smooth"){
 const n=by("vg-step-"+(i+1));if(!n)return;
 browsingHistory=false;n.scrollIntoView({behavior,block:"start"});updateJump()
}
function updateHeader(){
 nodes.counter.textContent=(frontier+1)+" / "+data.steps.length;
 nodes.progress.value=frontier+1;nodes.progress.max=data.steps.length;
}
function cardDetails(step){
 const d=el("details",undefined,"vg-details"),summary=el("summary","Подробнее");d.append(summary);
 d.append(el("p",step.question,"vg-more-question"),el("p",step.answer));
 if(step.subelements?.length){
  const block=el("details"),sum=el("summary","Состав последования"),ul=el("ul");
  for(const x of step.subelements)ul.append(el("li",x));block.append(sum,ul);d.append(block)
 }
 if(step.conditions?.length){
  const block=el("details"),sum=el("summary","Уставные варианты"),ul=el("ul");
  for(const x of step.conditions){const li=el("li");li.append(el("strong",x.condition+": "),document.createTextNode(x.text));ul.append(li)}
  block.append(sum,ul);d.append(block)
 }
 if(step.compare){
  const a=el("a","Сравнить службы","vg-source-link");
  a.href=compareUrl+"?row="+encodeURIComponent(step.compare);d.append(a)
 }
 const source=data.sources.find(s=>s.code===step.source);
 d.append(el("p","Источник: "+(source?.name||"Архиеп. Аверкий (Таушев)")+". Уставные варианты — по Типикону.","vg-source"));
 return d;
}
function makeCard(i){
 const step=data.steps[i],card=el("article",undefined,"vg-step");card.id="vg-step-"+(i+1);card.dataset.step=step.id;
 if(i===frontier)card.classList.add("vg-current");
 if(i===0||step.section!==data.steps[i-1].section)card.append(el("div",step.section,"vg-section-label"));
 const head=el("div",undefined,"vg-step-head");
 head.append(el("span","Шаг "+(i+1)+" / 72"),el("span",step.actor));card.append(head);
 card.append(el("div",step.cue,"vg-cue"));
 const nameQuiz=el("section",undefined,"vg-name-quiz");nameQuiz.id="vg-name-quiz-"+(i+1);
 nameQuiz.append(el("h3","Как это называется?"));
 const nameOptions=el("div",undefined,"vg-choices vg-name-choices"),nameSaved=nameAnswers[step.id];
 for(const [j,c] of step.nameQuiz.choices.entries()){
  const b=button((j+1)+". "+c.label,()=>chooseName(i,c.stepId),"vg-choice");
  if(nameSaved){
   b.disabled=true;
   if(c.stepId===step.nameQuiz.correctStepId)b.classList.add("is-correct");
   else if(c.stepId===nameSaved.selected)b.classList.add("is-wrong")
  }
  nameOptions.append(b)
 }
 nameQuiz.append(nameOptions);card.append(nameQuiz);
 const name=el("div",undefined,"vg-name");name.id="vg-name-"+(i+1);
 if(nameSaved&&!nameSaved.correct)name.append(el("p","Неверно. Правильный ответ: "+step.title+".","vg-error"));
 else if(nameSaved)name.append(el("p","Верно.","vg-good"));
 name.append(el("h2",step.title),el("p",step.definition));
 name.hidden=!nameSaved;card.append(name);
 if(i===data.steps.length-1){
  const terminal=el("div","Последование всенощного бдения завершено.","vg-terminal");
  terminal.hidden=!revealed.has(step.id);card.append(terminal)
 }else{
  const quiz=el("section",undefined,"vg-quiz");quiz.id="vg-quiz-"+(i+1);
  quiz.append(el("h3","Что следует дальше?"));
  const options=el("div",undefined,"vg-choices");
  for(const [j,c] of step.quiz.choices.entries()){
   const b=button((j+1)+". "+c.label,()=>answer(i,c.stepId),"vg-choice");
   const saved=answers[step.id];
   if(saved){
    b.disabled=true;
    if(c.stepId===step.quiz.correctStepId)b.classList.add("is-correct");
    else if(c.stepId===saved.selected)b.classList.add("is-wrong")
   }
   options.append(b)
  }
  quiz.append(options);
  const result=el("div",undefined,"vg-feedback");result.setAttribute("role","status");
  const chosen=answers[step.id];
  if(chosen){
   result.append(el("p",chosen.correct?"Верно.":"Неверно. Правильный ответ: "+data.steps[i+1].title+".",chosen.correct?"vg-good":"vg-error"))
  }
  quiz.append(result);quiz.hidden=!quizShown.has(step.id);card.append(quiz)
 }
 card.append(cardDetails(step));return card
}
function renderStream(changedIndex=null){
 // Preserve all earlier card DOM, open reference notes and page scroll position.
 for(let i=0;i<=frontier;i++){
  const old=by("vg-step-"+(i+1));
  if(!old)nodes.stream.append(makeCard(i));
  else if(i===changedIndex)old.replaceWith(makeCard(i));
  const card=by("vg-step-"+(i+1));
  card.classList.toggle("vg-current",i===frontier);
 }
 updateHeader();renderMap();updateJump();
 if(completed)renderSummary();
}
function renderMap(){
 if(!nodes.map.open)return;
 nodes.menu.replaceChildren();
 for(const [i,s] of data.steps.entries())nodes.menu.append(button((i+1)+". "+s.title,()=>{nodes.map.open=false;openStep(i)},"vg-map-item"))
}
function renderCourse(){
 const list=nodes.course;list.replaceChildren();
 for(const l of data.lessons){
  const block=el("section",undefined,"vg-lesson");block.append(el("h3",l.title),el("p",l.focus),el("p",l.duration));
  const ol=el("ol");for(const [title,mins] of l.blocks)ol.append(el("li",title+" — "+mins+" мин"));
  block.append(ol);list.append(block)
 }
}
function clearTimers(){for(const timer of quizTimers)clearTimeout(timer);quizTimers.clear();if(advanceTimer!==null)clearTimeout(advanceTimer);advanceTimer=null}
function chooseName(i,selected){
 const s=data.steps[i];
 if(!s?.nameQuiz||nameAnswers[s.id]||completed)return;
 tick();nameAnswers[s.id]={selected,correct:selected===s.nameQuiz.correctStepId};
 revealed.add(s.id);store();
 const follow=i===frontier&&nearLatest()&&!browsingHistory,revision=scrollRevision;
 renderStream(i);
 if(i===data.steps.length-1){finish();return}
 if(!quizShown.has(s.id)){
  const version=runVersion;
  const timer=setTimeout(()=>{
   quizTimers.delete(timer);
   if(runVersion!==version||!nameAnswers[s.id])return;
   quizShown.add(s.id);store();renderStream(i);
   if(follow&&!browsingHistory&&scrollRevision===revision){
    const nextQuestion=by("vg-quiz-"+(i+1));
    if(nextQuestion)nextQuestion.scrollIntoView({behavior:"smooth",block:"nearest"})
   }
  },1200);
  quizTimers.add(timer);
 }
}
function answer(i,chosen){
 const step=data.steps[i];
 if(!step?.quiz||answers[step.id]||!quizShown.has(step.id)||completed)return;
 tick();answers[step.id]={selected:chosen,correct:chosen===step.quiz.correctStepId};
 store();const follow=(i===frontier&&nearLatest()&&!browsingHistory),revision=scrollRevision;renderStream(i);
 if(i===frontier){
  if(advanceTimer!==null)clearTimeout(advanceTimer);
  advanceTimer=setTimeout(()=>{advanceTimer=null;advance(i,follow,revision)},1500)
 }
}
function advance(i,follow,revision){
 if(frontier!==i||completed)return;
 // Check before appending: the newly created card is naturally below the viewport.
 const stayedAtLatest=nearLatest()&&!browsingHistory&&scrollRevision===revision;
 frontier=Math.min(frontier+1,data.steps.length-1);store();setHash(frontier);renderStream();
 if(follow&&stayedAtLatest)scrollToCard(frontier);
 else updateJump();
}
function openStep(i){
 if(i>frontier){frontier=i;store();renderStream()}
 scrollToCard(i);setHash(i)
}
function renderSummary(){
 let block=by("vg-results");
 if(!block){block=el("section",undefined,"vg-results");block.id="vg-results";nodes.stream.append(block)}
 block.replaceChildren();block.append(el("h2","Итоги прохождения"));
 const nameArr=Object.values(nameAnswers),seqArr=Object.values(answers),arr=[...nameArr,...seqArr];
 const correct=arr.filter(x=>x.correct).length,wrong=arr.length-correct;
 const correctNames=nameArr.filter(x=>x.correct).length,wrongNames=nameArr.length-correctNames;
 const correctSeq=seqArr.filter(x=>x.correct).length,wrongSeq=seqArr.length-correctSeq;
 const stats=el("div",undefined,"vg-stats");
 for(const [label,value] of [["Верно",correct],["Ошибок",wrong],["Без ответа",143-arr.length],["Точность",arr.length?Math.round(correct/arr.length*100)+"%":"—"],["Время",prettyTime(elapsedMs)]]){
  const item=el("div",undefined,"vg-stat");item.append(el("span",label),el("strong",value));stats.append(item)
 }
 block.append(stats);
 const sections=el("div",undefined,"vg-stats");
 for(const [label,right,wrongCount,missed] of [
  ["Названия",correctNames,wrongNames,72-nameArr.length],
  ["Последовательность",correctSeq,wrongSeq,71-seqArr.length]
 ]){
  const item=el("div",undefined,"vg-stat vg-stat-detail");
  item.append(el("strong",label),el("span","Верно: "+right+" · Ошибок: "+wrongCount+" · Без ответа: "+missed));
  sections.append(item)
 }
 block.append(sections);
 const wrongSteps=data.steps.filter(s=>(nameAnswers[s.id]&&!nameAnswers[s.id].correct)||(answers[s.id]&&!answers[s.id].correct));
 if(wrongSteps.length){
  const d=el("details"),sum=el("summary","Повторить ошибки ("+wrongSteps.length+")");d.append(sum);
  for(const s of wrongSteps){const i=data.steps.indexOf(s);d.append(button((i+1)+". "+s.title,()=>scrollToCard(i),"vg-review"))}
  block.append(d)
 }
}
function finish(){
 if(frontier!==71||!nameAnswers[data.steps[71].id]||completed)return;
 const shouldFollow=nearLatest()&&!browsingHistory;
 tick();completed=true;tickStart=null;store();renderStream();
 if(shouldFollow)scrollToEnd();
}
function newRun(){
 if(!confirm("Начать заново? Ответы и время будут сброшены."))return;
 clearTimers();runVersion++;frontier=0;answers={};nameAnswers={};revealed=new Set();quizShown=new Set();elapsedMs=0;completed=false;tickStart=null;
 store();nodes.stream.replaceChildren();renderStream();resume();scrollToCard(0)
}
function wire(){
 nodes.jump.addEventListener("click",()=>scrollToEnd());
 nodes.map.addEventListener("toggle",renderMap);
 nodes.reset.addEventListener("click",newRun);
 window.addEventListener("scroll",()=>{
  const y=window.scrollY;
  if(y<lastScrollY-4){scrollRevision++;browsingHistory=true}
  else if(y>lastScrollY+4&&nearLatest())browsingHistory=false;
  lastScrollY=y;updateJump();
 },{passive:true});
 window.addEventListener("resize",updateJump);
 document.addEventListener("visibilitychange",()=>{if(document.hidden)pause();else resume()});
 window.addEventListener("pagehide",pause);
 setInterval(()=>{if(!document.hidden&&!completed){tick();store()}},5000)
}
async function load(){
 const response=await fetch(dataUrl);if(!response.ok)throw Error("HTTP "+response.status);
 data=await response.json();
 if(data.steps.length!==72||
  !data.steps.every(s=>s.nameQuiz?.correctStepId===s.id&&s.nameQuiz.choices.length>=2&&s.nameQuiz.choices.length<=5&&new Set(s.nameQuiz.choices.map(c=>c.stepId)).size===s.nameQuiz.choices.length&&s.nameQuiz.choices.filter(c=>c.stepId===s.id).length===1)||
  !data.steps.slice(0,-1).every((s,i)=>s.quiz?.correctStepId===data.steps[i+1].id&&s.quiz.choices.length===3))throw Error("Неполное последование");
 restore();renderCourse();wire();renderStream();
 nodes.status.hidden=true;nodes.loaded.hidden=false;resume();
 // Resume a pending question/transition across reload without inserting fabricated answers.
 const s=data.steps[frontier];
 if(nameAnswers[s.id]&&!quizShown.has(s.id)&&s.quiz){
  const i=frontier,version=runVersion;
  const timer=setTimeout(()=>{quizTimers.delete(timer);if(runVersion!==version)return;quizShown.add(s.id);store();renderStream(i)},1200);
  quizTimers.add(timer)
 }else if(s.quiz&&answers[s.id]){const i=frontier;advanceTimer=setTimeout(()=>{advanceTimer=null;advance(i,false,scrollRevision)},1500)}
 if(frontier>0){if(completed)scrollToEnd("instant");else scrollToCard(frontier,"instant")}
}
load().catch(err=>{nodes.status.textContent="Не удалось открыть последование. Обновите страницу.";console.error(err)});
})();