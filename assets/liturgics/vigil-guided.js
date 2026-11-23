"use strict";
(()=>{
const root=document.querySelector("#vigil-guide");
if(!root)return;
const el=(tag,content,cls)=>{const node=document.createElement(tag);if(cls)node.className=cls;if(content!==undefined&&content!==null)node.textContent=String(content);return node};
const nodes={
status:root.querySelector("#vg-status"),
menu:root.querySelector("#vg-menu"),section:root.querySelector("#vg-section"),
counter:root.querySelector("#vg-counter"),progress:root.querySelector("#vg-progress"),
title:root.querySelector("#vg-title"),role:root.querySelector("#vg-role"),cue:root.querySelector("#vg-cue"),
definition:root.querySelector("#vg-definition"),explanation:root.querySelector("#vg-explanation"),
question:root.querySelector("#vg-question"),answer:root.querySelector("#vg-answer"),
whatnext:root.querySelector("#vg-what-next"),nextanswer:root.querySelector("#vg-next-answer"),
link:root.querySelector("#vg-table-link"),source:root.querySelector("#vg-source"),
next:root.querySelector("#vg-forward"),previous:root.querySelector("#vg-back"),
showname:root.querySelector("#vg-show-name"),showexplanation:root.querySelector("#vg-show-explanation"),
showanswer:root.querySelector("#vg-show-answer"),shownext:root.querySelector("#vg-show-next"),
training:root.querySelector("#vg-training"),fullmap:root.querySelector("#vg-map"),
course:root.querySelector("#vg-course")
};
const storageKey="gos-exams-vigil-guided-2027-v1";
let data,index=0,training=false,visibleName=false,visibleExplanation=false,visibleAnswer=false,visibleNext=false;
const sectionKeys=["Великая вечерня","Утреня","Первый час"];
function store(){
 try{localStorage.setItem(storageKey,JSON.stringify({index,training}))}catch(_){}
}
function restore(){
 try{const saved=JSON.parse(localStorage.getItem(storageKey)||"null");if(saved&&Number.isInteger(saved.index)&&saved.index>=0&&saved.index<data.steps.length)index=saved.index;training=saved?.training===true}catch(_){}
 const hash=(window.location.hash||"").match(/^#step-(\d+)$/);
 if(hash){const idx=Number(hash[1])-1;if(idx>=0&&idx<data.steps.length)index=idx}
 nodes.training.checked=training;
}
function setStep(next){
 if(next<0||next>=data.steps.length)return;
 index=next;visibleName=!training;visibleExplanation=false;visibleAnswer=false;visibleNext=false;
 store();render();
 try{window.history.replaceState(null,"","#step-"+(index+1))}catch(_){}
}
function makeButton(text,action,cls){
 const button=el("button",text,cls);button.type="button";button.addEventListener("click",action);return button;
}
function renderSections(){
 nodes.section.replaceChildren();
 for(const name of sectionKeys){
  const start=data.steps.findIndex(s=>s.section===name),button=makeButton(name,()=>setStep(start),"vg-section-button");
  button.setAttribute("aria-pressed",String(data.steps[index].section===name));
  nodes.section.append(button);
 }
}
function renderMap(){
 nodes.menu.replaceChildren();
 data.steps.forEach((step,i)=>{
  const item=makeButton((i+1)+". "+step.title,()=>{setStep(i);nodes.fullmap.open=false},"vg-map-item");
  if(i===index)item.setAttribute("aria-current","step");
  nodes.menu.append(item);
 });
}
function renderCourse(){
 nodes.course.replaceChildren();
 for(const lesson of data.lessons){
  const pane=el("section",undefined,"vg-lesson"),h=el("h3",lesson.title);
  pane.append(h,el("p",lesson.focus),el("p",lesson.duration,"vg-muted"));
  const ol=el("ol");
  lesson.blocks.forEach(([name,minutes])=>{const li=el("li",name+" — "+minutes+" мин");ol.append(li)});
  pane.append(ol);nodes.course.append(pane);
 }
}
function render(){
 const step=data.steps[index],next=data.steps[index+1];
 nodes.counter.textContent=(index+1)+" / "+data.steps.length;
 nodes.progress.value=index+1;nodes.progress.max=data.steps.length;
 nodes.role.textContent=step.actor;
 nodes.cue.textContent=step.cue;
 nodes.title.textContent=step.title;nodes.title.hidden=training&&!visibleName;
 nodes.showname.hidden=!training||visibleName;
 nodes.definition.textContent=step.definition;
 nodes.question.textContent=step.question;
 nodes.answer.textContent=step.answer;
 nodes.nextanswer.textContent=next?next.title:"Всенощное бдение завершено.";
 nodes.whatnext.textContent=next?"Какой элемент следует дальше?":"Чем оканчивается всенощное бдение?";
 nodes.explanation.hidden=!visibleExplanation;
 nodes.answer.hidden=!visibleAnswer;
 nodes.nextanswer.hidden=!visibleNext;
 nodes.showexplanation.textContent=visibleExplanation?"Скрыть пояснение":"Что это такое?";
 nodes.showanswer.textContent=visibleAnswer?"Скрыть ответ":"Показать ответ";
 nodes.shownext.textContent=visibleNext?"Скрыть следующий элемент":"Что дальше? — проверить";
 nodes.link.hidden=!step.compare;
 if(step.compare){
  nodes.link.href=root.dataset.compare+"?row="+encodeURIComponent(step.compare);
  nodes.link.textContent="Открыть сравнительную таблицу: "+step.title;
 }
 const labels={E:"Вечерня",M:"Утреня",H:"Первый час"};
 const source=data.sources.find(x=>x.code===step.source);nodes.source.textContent="Источник определения: "+(source?.name||"").trim()+". Последовательность: преподавательский эталон № 2; первый час — по Аверкию.";
 nodes.previous.disabled=index===0;nodes.next.disabled=index===data.steps.length-1;
 nodes.next.textContent=next?"Следующий элемент":"Последование завершено";
 renderSections();
 if(nodes.fullmap.open)renderMap();
}
nodes.next.addEventListener("click",()=>setStep(index+1));
nodes.previous.addEventListener("click",()=>setStep(index-1));
nodes.showname.addEventListener("click",()=>{visibleName=true;render()});
nodes.showexplanation.addEventListener("click",()=>{visibleExplanation=!visibleExplanation;render()});
nodes.showanswer.addEventListener("click",()=>{visibleAnswer=!visibleAnswer;render()});
nodes.shownext.addEventListener("click",()=>{visibleNext=!visibleNext;render()});
nodes.training.addEventListener("change",()=>{training=nodes.training.checked;visibleName=!training;visibleExplanation=false;visibleAnswer=false;visibleNext=false;store();render()});
nodes.fullmap.addEventListener("toggle",()=>{if(nodes.fullmap.open)renderMap()});
const reset=nodes.rootReset=root.querySelector("#vg-reset");
reset.addEventListener("click",()=>setStep(0));
async function load(){
 const response=await fetch(root.dataset.source);
 if(!response.ok)throw Error("HTTP "+response.status);
 data=await response.json();
 if(!Array.isArray(data.steps)||data.steps.length<60||!data.steps.every(s=>s.definition&&s.source&&s.question&&s.answer))throw Error("Неполное последование");
 restore();renderCourse();render();nodes.status.hidden=true;root.querySelector("#vg-loaded").hidden=false;
}
load().catch(err=>{nodes.status.textContent="Не удалось открыть последование. Обновите страницу.";console.error(err)});
})();