"use strict";
(()=>{
const root=document.querySelector("#full-day-guide");if(!root)return;
const $=id=>root.querySelector("#"+id), E=(tag,t,cls)=>{let x=document.createElement(tag);if(t!=null)x.textContent=t;if(cls)x.className=cls;return x}, B=(t,f,cls)=>{let x=E("button",t,cls);x.type="button";x.onclick=f;return x};
const prefix="gos-exams-lenten-full-day-v1:", get=k=>{try{return JSON.parse(localStorage.getItem(k)||"null")}catch{return null}}, put=(k,v)=>{try{localStorage.setItem(k,JSON.stringify(v))}catch{}};
let data,day,state,mode=null,items=[],timer=null,epoch=0,paused=false,back=false,lastY=0,lastTick=0,visible=true;
const key=()=>prefix+day.id+":r"+day.revision, fresh=()=>({answers:{},cursors:{},completed:{},visited:{},elapsed:0});
function save(){if(day&&state)put(key(),state)}
function stop(){clearTimeout(timer);timer=null;epoch++}
function tick(){let now=Date.now();if(mode&&!paused&&visible&&lastTick)state.elapsed+=(Math.min(15000,now-lastTick));lastTick=now;save()}
setInterval(tick,5000);document.addEventListener("visibilitychange",()=>{tick();visible=!document.hidden;lastTick=Date.now()});window.addEventListener("pagehide",tick);
const all=()=>day.services.flatMap(s=>s.steps), questions=steps=>steps.flatMap(s=>[s.nameQuiz,s.nextQuiz].filter(Boolean)), stat=steps=>{let qs=questions(steps),done=qs.filter(q=>q.choices.some(c=>c.id===state.answers[q.id])),right=done.filter(q=>q.correct===state.answers[q.id]).length;return "Ответы: "+done.length+"/"+qs.length+" · Верно: "+right+" · Ошибки: "+(done.length-right)};
const pos=()=>Math.max(0,Math.min(items.length-1,state.cursors[mode]||0)), finished=()=>!!state.completed[mode], target=()=>$("fd-card-"+pos());
function scroll(n){if(n)n.scrollIntoView({block:"nearest",behavior:matchMedia("(prefers-reduced-motion: reduce)").matches?"auto":"smooth"})}
function normalize(bank, raw, routeId) {
 const route=Array.isArray(raw.routes)?raw.routes.find(x=>x.id===routeId):raw;
 if(!route || !Array.isArray(route.steps) || !route.steps.length) throw Error("Missing route "+routeId);
 const sourceNames=new Map((raw.sources||[]).map(s=>[s.code,s.name]));
 const q=(x)=>x?{choices:x.choices.map(c=>({id:c.id??c.stepId,label:c.label})),correct:x.correct??x.correctStepId}:null;
 return route.steps.map(s=>({id:s.id,title:s.title,cue:s.cue,definition:s.definition,section:s.section??route.title??"",actor:s.actor??null,sourceRefs:[sourceNames.get(s.source)||s.source].filter(Boolean),sourcePositions:s.sourcePositions??[],conditions:s.conditions??[],subelements:s.subelements??[],nameQuiz:q(s.nameQuiz),nextQuiz:q(s.nextQuiz??s.quiz),nextId:s.nextNodeId??s.nextStepId??null}));
}

"use strict";
// Questions derive solely from the existing service sequence and its titles.
function completeQuestions(steps,instanceId){
 const canonical=s=>s.trim().replace(/\s+/g," ").toLocaleLowerCase("ru");
 const seed=s=>{let h=2166136261;for(let i=0;i<s.length;i++)h=Math.imul(h^s.charCodeAt(i),16777619);return h>>>0};
 const make=(target,kind,context)=>{
  const answer={id:target.id,label:target.title};
  let pool=steps.map((s,i)=>({s,i})).filter(({s})=>canonical(s.title)!==canonical(target.title)&&s.id!==context.id).sort((a,b)=>Math.abs(a.i-steps.indexOf(target))-Math.abs(b.i-steps.indexOf(target))||seed(instanceId+kind+a.s.id)-seed(instanceId+kind+b.s.id));
  let choices=[answer],seen=new Set([canonical(answer.label)]);
  for(const {s} of pool){if(seen.has(canonical(s.title)))continue;seen.add(canonical(s.title));choices.push({id:s.id,label:s.title});if(choices.length===3)break}
  if(choices.length<3)for(const s of steps){if(seen.has(canonical(s.title)))continue;seen.add(canonical(s.title));choices.push({id:s.id,label:s.title});if(choices.length===3)break}
  if(choices.length<2)throw Error("Insufficient alternatives "+instanceId+"/"+target.id);
  choices.sort((a,b)=>seed(instanceId+"/"+context.id+"/"+kind+"/"+a.id)-seed(instanceId+"/"+context.id+"/"+kind+"/"+b.id));
  return {choices,correct:answer.id};
 };
 const valid=(q,target,kind)=>q&&q.correct===target.id&&q.choices.length>=(kind==="next"?3:2)&&q.choices.length<=(kind==="next"?3:5)&&new Set(q.choices.map(c=>c.id)).size===q.choices.length&&new Set(q.choices.map(c=>canonical(c.label))).size===q.choices.length&&q.choices.filter(c=>c.id===q.correct).length===1&&canonical(q.choices.find(c=>c.id===q.correct).label)===canonical(target.title);
 return steps.map((s,i)=>{
  let cue=s.cue; if(canonical(cue)===canonical(s.title))cue=s.definition;
  let nameQuiz=valid(s.nameQuiz,s,"name")?s.nameQuiz:make(s,"name",s);
  const next=steps[i+1];let nextQuiz=next?(valid(s.nextQuiz,next,"next")?s.nextQuiz:make(next,"next",s)):null;
  if(!nameQuiz||next&&!nextQuiz||!cue.trim())throw Error("Missing question "+instanceId+"/"+s.id);
  return {...s,cue,nameQuiz,nextQuiz};
 });
}

const bankCache=new Map();
function loadBank(k){if(!bankCache.has(k)){let promise=fetch(new URL(data.banks[k],new URL(root.dataset.source,location.href))).then(r=>{if(!r.ok)throw Error("HTTP "+r.status+" "+k);return r.json()});bankCache.set(k,promise);promise.catch(()=>bankCache.delete(k))}return bankCache.get(k)}
async function materialize(entry){if(entry.loaded)return;const services=await Promise.all(entry.services.map(async s=>{const b=s.binding,raw=await loadBank(b.bank),all=normalize(b.bank,raw,b.route),a=all.findIndex(x=>x.id===b.from),z=all.findIndex(x=>x.id===b.to);if(a<0||z<a)throw Error("Invalid service "+s.id);const steps=completeQuestions(all.slice(a,z+1),s.id).map((x,k,arr)=>{const q=(v,kind)=>v&&({...v,id:s.id+"/"+x.id+":"+kind});if(!x.nameQuiz||k<arr.length-1&&!x.nextQuiz)throw Error("Missing question "+x.id);return {id:s.id+"/"+x.id,title:x.title,cue:x.cue,definition:x.definition,source:x.sourceRefs.join("; "),nameQuiz:q(x.nameQuiz,"name"),nextQuiz:q(x.nextQuiz,"next")}});return {...s,steps}}));const lent=await loadBank("lent");Object.assign(entry,{services,features:lent.cases?.find(c=>c.id===entry.id)?.features||"",loaded:true})}

let selectionEpoch=0;async function select(id){let version=++selectionEpoch;stop();tick();mode=null;const entry=data.days.find(d=>d.id===id);$("fd-overview").replaceChildren(E("p","Загрузка последования…"));try{await materialize(entry);if(version!==selectionEpoch)return;day=entry;}catch(e){console.error(e);if(version===selectionEpoch)$("fd-overview").replaceChildren(E("p","Не удалось загрузить последование. Выберите день повторно."));return;}state=get(key())||fresh();state.answers??={};state.cursors??={};state.completed??={};state.visited??={};state.elapsed??=0;put(prefix+"selection",{day:id});$("fd-reader").hidden=true;$("fd-picker").hidden=false;overview()}
async function periods(selected){let list=data.days.filter(d=>d.queue===Number($("fd-period").value));$("fd-day").replaceChildren(...list.map(d=>{let o=E("option",d.title);o.value=d.id;return o}));if(list.some(d=>d.id===selected))$("fd-day").value=selected;return select($("fd-day").value)}
function details(title){let d=E("details");d.append(E("summary",title));return d}
function serviceState(s){let n=s.steps.filter(x=>state.visited[x.id]).length;return n===s.steps.length&&n?"Изучено":n?"Продолжить · "+n+"/"+s.steps.length:s.missing?"Нет последования":"Не начато"}
function overview(){let box=$("fd-overview");box.replaceChildren(E("h2",day.title),E("p",day.condition));let missing=day.services.some(s=>s.missing||!s.steps.length),primary=B(state.completed.day?"Посмотреть последование":(state.cursors.day||all().some(s=>s.nameQuiz&&Object.hasOwn(state.answers,s.nameQuiz.id)))?"Продолжить последование":"Пройти всё последование",()=>open("day"),"fd-primary");primary.disabled=missing;box.append(primary);if(missing)box.append(E("p","Некоторые службы пока отсутствуют."));
let map=E("ol",null,"fd-map");for(const s of day.services){let li=E("li");li.append(E("span",s.title),E("small",serviceState(s)));map.append(li)}box.append(E("h3","Суточное последование"),map);
let d=details("Выбрать отдельную службу");for(const s of day.services){let b=B(s.title+" · "+serviceState(s),()=>open(s.id),"fd-service");b.disabled=s.missing||!s.steps.length;d.append(b)}box.append(d);
let f=details("Уставные особенности");f.append(E("p",day.features||day.condition));box.append(f);
let r=details("Результаты изучения");r.append(E("p",stat(all())),E("p","Изучено: "+all().filter(s=>state.visited[s.id]).length+"/"+all().length+" · Активное время: "+Math.floor(state.elapsed/60000)+" мин."));box.append(r)}
function open(m){stop();tick();mode=m;paused=false;back=false;pendingName=null;items=(m==="day"?day.services:day.services.filter(s=>s.id===m)).flatMap(s=>s.steps.map((x,i)=>({...x,service:s.title,first:i===0})));if(!items.length){mode=null;return}put(prefix+"selection",{day:day.id,mode});$("fd-picker").hidden=true;$("fd-reader").hidden=false;$("fd-title").textContent=m==="day"?day.title:items[0].service;$("fd-stream").replaceChildren();lastTick=Date.now();render();scroll(target())}
function answer(q,id){if(paused||Object.hasOwn(state.answers,q.id))return;state.answers[q.id]=id;save()}
function question(q,label,onAnswer){let sec=E("section",null,"fd-question");sec.append(E("h4",label));let chosen=state.answers[q.id];for(let c of q.choices){let b=B(c.label,()=>{answer(q,c.id);onAnswer()},"fd-choice");b.disabled=paused||chosen!==undefined;if(chosen!==undefined){if(c.id===q.correct)b.classList.add("fd-correct");else if(c.id===chosen)b.classList.add("fd-wrong")}sec.append(b)}if(chosen!==undefined){let f=E("p",chosen===q.correct?"Верно.":"Правильный ответ: "+q.choices.find(c=>c.id===q.correct)?.label);f.setAttribute("role","status");sec.append(f)}return sec}
let pendingName=null;
function schedule(fn,ms){stop();const e=epoch;timer=setTimeout(()=>{if(e===epoch&&!paused&&mode)fn()},ms)}
function advance(){if(paused||finished())return;stop();const i=pos(),s=items[i];if([s.nameQuiz,s.nextQuiz].some(q=>q&&!Object.hasOwn(state.answers,q.id)))return;state.visited[s.id]=true;if(i===items.length-1)state.completed[mode]=true;else state.cursors[mode]=i+1;save();render(i);if(!back)scroll(target())}
function card(i){let s=items[i],a=E("article",null,"fd-card");a.id="fd-card-"+i;if(s.first)a.append(E("h2",s.service,"fd-heading"));a.append(E("small","Шаг "+(i+1)+" из "+items.length));let nq=s.nameQuiz,sq=s.nextQuiz,known=!nq||Object.hasOwn(state.answers,nq.id);if(nq){a.append(E("p",s.cue),question(nq,"Как это называется?",()=>{pendingName=s.id;render(i);schedule(()=>{pendingName=null;render(i)},1200)}))}if(known){a.append(E("h3",s.title),E("p",s.definition));if(s.source){let d=details("Источник");d.append(E("p",s.source));a.append(d)}if(sq&&pendingName!==s.id)a.append(question(sq,"Что следует дальше?",()=>{render(i);if(i===pos()&&!finished())schedule(advance,1500)}));if(i===pos()&&!finished()&&(!sq||Object.hasOwn(state.answers,sq.id))&&pendingName!==s.id){let b=B(i===items.length-1?"Завершить последование":"Далее",advance,"fd-primary");b.disabled=paused;a.append(b)}}return a}
function render(changed=-1){let stream=$("fd-stream"),i=pos();for(let j=0;j<=i;j++){let old=$("fd-card-"+j);if(!old)stream.append(card(j));else if(j===changed||j===i||changed===-2)old.replaceWith(card(j));$("fd-card-"+j).classList.toggle("fd-current",j===i)}$("fd-count").textContent=(finished()?items.length:i+1)+" / "+items.length;$("fd-progress").max=items.length;$("fd-progress").value=finished()?items.length:i;$("fd-stats").textContent=stat(items);$("fd-pause").textContent=paused?"Возобновить":"Пауза";$("fd-result")?.remove();if(finished()){let r=E("section",null,"fd-card");r.id="fd-result";r.append(E("h2","Последование изучено"),E("p",stat(items)));let wrong=items.filter(s=>[s.nameQuiz,s.nextQuiz].some(q=>q&&state.answers[q.id]!==undefined&&state.answers[q.id]!==q.correct));if(wrong.length){let d=details("Разобрать ошибки");for(let s of wrong)d.append(B(s.title,()=>scroll($("fd-card-"+items.indexOf(s))),"fd-service"));r.append(d)}r.append(B("К выбору дня",returnDay,"fd-primary"));stream.append(r)}jump()}
function returnDay(){stop();pendingName=null;tick();mode=null;put(prefix+"selection",{day:day.id});$("fd-reader").hidden=true;$("fd-picker").hidden=false;overview();scroll($("fd-picker"))}
function jump(){let t=mode&&target();$("fd-jump").hidden=!t||t.getBoundingClientRect().top<innerHeight-80&&t.getBoundingClientRect().bottom>0}
$("fd-period").onchange=()=>periods();$("fd-day").onchange=()=>select($("fd-day").value);$("fd-back").onclick=returnDay;$("fd-jump").onclick=()=>{back=false;scroll(target())};$("fd-pause").onclick=()=>{tick();stop();pendingName=null;paused=!paused;lastTick=Date.now();render(-2)};
$("fd-reset").onclick=()=>{if(!mode||!confirm("Начать это последование заново?"))return;stop();pendingName=null;if(mode==="day")state=fresh();else{for(let s of items){delete state.visited[s.id];for(let q of [s.nameQuiz,s.nextQuiz])if(q)delete state.answers[q.id]}delete state.cursors[mode];delete state.completed[mode];delete state.completed.day;delete state.cursors.day}save();open(mode)};
window.addEventListener("scroll",()=>{if(scrollY<lastY-4)back=true;else if(scrollY>lastY+4&&target()?.getBoundingClientRect().top<innerHeight)back=false;lastY=scrollY;jump()},{passive:true});
fetch(root.dataset.source).then(r=>{if(!r.ok)throw Error("HTTP "+r.status);return r.json()}).then(async d=>{if(d.schemaVersion!==1||!d.days?.length)throw Error("Invalid data");data=d;let s=get(prefix+"selection"),initial=d.days.find(x=>x.id===s?.day)||d.days[0];$("fd-period").value=initial.queue;$("fd-status").hidden=true;$("fd-loaded").hidden=false;await periods(initial.id);if(day&&s?.mode&&(s.mode==="day"||day.services.some(x=>x.id===s.mode)))open(s.mode)}).catch(e=>{$("fd-status").textContent="Не удалось загрузить последования. Обновите страницу.";console.error(e)});
})();