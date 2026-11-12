"use strict";
/* Единый браузерный движок двух режимов Литургики. Данные случаев загружаются из JSON. */
async function initLiturgicsTrainer(){
 const root=document.querySelector("main.wrap[data-case]");
 if(!root)return;
 const reportEl=document.getElementById("report");
 let game;
 try{
  const response=await fetch(root.getAttribute("data-case"),{cache:"no-cache"});
  if(!response.ok)throw new Error("HTTP "+response.status);
  game=await response.json();
  if(!game||game.schema!==1||!Array.isArray(game.items)||!game.items.length)throw new Error("Неверный паспорт задания");
  if(!["assembly","diagnostic"].includes(game.mode))throw new Error("Неизвестный режим");
  const ids=game.items.map(x=>x.id);
  if(new Set(ids).size!==ids.length)throw new Error("Повторяются идентификаторы кирпичиков");
  if((game.initialPyramid||[]).some(id=>!ids.includes(id)))throw new Error("Неизвестный кирпичик в исходной Пирамиде");
 }catch(error){
  reportEl.replaceChildren();
  const strong=document.createElement("strong");strong.textContent="Не удалось открыть задание";
  const p=document.createElement("p");p.textContent="Проверьте соединение и обновите страницу. "+error.message;
  reportEl.append(strong,p);
  return;
 }
 const CASE_VERSION=game.version;
 const SOURCE=game.source;
 const L3=game.l3;
 const DATA=game.items;
 const START_PYRAMID=game.initialPyramid||[];
 const isDiagnostic=game.mode==="diagnostic";
const dataById=new Map(DATA.map(x=>[x.id,x]));
const required=DATA.filter(x=>!x.extra).map(x=>x.id);
const storageKey="bpds-sandbox-pyramid-"+CASE_VERSION;
const sandNode=document.getElementById("sand"), pyramidNode=document.getElementById("pyramid");
const report=document.getElementById("report"), modalHost=document.getElementById("modalHost");
let sand=[],pyramid=[],modalOpen=false,dragging=false,hintState={signature:"",level:0},keyboardPick=null,animationInProgress=false,activeTouch=false,layoutSwapped=false;
function shuffled(values){let a=[...values];for(let i=a.length-1;i>0;i--){let j=Math.floor(Math.random()*(i+1));[a[i],a[j]]=[a[j],a[i]]}return a}
function validSaved(s){return !!s&&Array.isArray(s.sand)&&Array.isArray(s.pyramid)&&[...s.sand,...s.pyramid].length===DATA.length&&new Set([...s.sand,...s.pyramid]).size===DATA.length&&[...s.sand,...s.pyramid].every(x=>dataById.has(x))}
function persist(){try{localStorage.setItem(storageKey,JSON.stringify({sand,pyramid,layoutSwapped}));document.getElementById("saveStatus").textContent="Сохранено на этом устройстве"}catch(e){document.getElementById("saveStatus").textContent="Сохранение недоступно"}}
function init(){let restored;try{restored=JSON.parse(localStorage.getItem(storageKey))}catch(e){}if(validSaved(restored)){sand=restored.sand;pyramid=restored.pyramid;layoutSwapped=restored.layoutSwapped===true}else{pyramid=isDiagnostic?[...START_PYRAMID]:[];sand=shuffled(DATA.map(x=>x.id).filter(id=>!pyramid.includes(id)));persist()}applyLayout();render()}
function render(keepScroll=true){const leftScroll=sandNode.scrollTop,rightScroll=pyramidNode.scrollTop;sandNode.replaceChildren();pyramidNode.replaceChildren();
 for(const [node,arr,zone] of [[sandNode,sand,"sand"],[pyramidNode,pyramid,"pyramid"]]){
  if(!arr.length){let e=document.createElement("div");e.className="placeholder";e.textContent=zone==="sand"?(isDiagnostic?"Запасные кирпичики использованы":"Все кирпичики перенесены"):(isDiagnostic?"Пирамида пуста":"Перенесите кирпичик сюда");node.append(e)}
  arr.forEach(id=>{const item=dataById.get(id),brick=document.createElement("div");brick.className="brick";brick.dataset.id=id;brick.dataset.zone=zone;brick.tabIndex=0;brick.setAttribute("role","button");brick.setAttribute("aria-label",item.name+", открыть или удержать для переноса");brick.title=item.name;
   const label=document.createElement("span");label.textContent=item.name;brick.append(label);
   brick.addEventListener("pointerdown",pointerStart);brick.addEventListener("touchstart",touchStart,{passive:true});brick.addEventListener("keydown",keyboardStart);
   node.append(brick)
  })
 }
 document.getElementById("sandCount").textContent=sand.length+" кирпичиков";
 document.getElementById("pyramidCount").textContent=isDiagnostic?pyramid.length+" кирпичиков":pyramid.length+" из "+required.length+" основных";
 if(keepScroll){sandNode.scrollTop=leftScroll;pyramidNode.scrollTop=rightScroll}
}
function showButtonFeedback(kind,title,lines){
 const target=document.getElementById(kind==="hint"?"hintFeedback":"checkFeedback");
 const other=document.getElementById(kind==="hint"?"checkFeedback":"hintFeedback");
 other.hidden=true;other.textContent="";
 target.hidden=false;
 target.textContent=(title?title+". ":"")+(lines&&lines.length?lines[0]:"");
 if(window.matchMedia("(max-width: 540px)").matches){
  requestAnimationFrame(()=>target.scrollIntoView({block:"nearest",behavior:"smooth"}));
 }
}
function showSuccessL3Link(){const link=document.createElement("a");link.href=L3;link.textContent="Перейти к разбору L3";link.className="result-l3-link";document.getElementById("checkFeedback").append(document.createTextNode(" "),link)}
function clearButtonFeedback(){
 for(const id of ["hintFeedback","checkFeedback"]){const node=document.getElementById(id);node.hidden=true;node.textContent="";}
}
function showReport(title,lines,type=""){report.className="report "+type;report.replaceChildren();let strong=document.createElement("strong");strong.textContent=title;report.append(strong);const ol=document.createElement("ol");for(let line of lines){const li=document.createElement("li");li.textContent=line;ol.append(li)}report.append(ol)}
function modalFor(id){const item=dataById.get(id);if(!item)return;modalOpen=true;const previous=document.activeElement;const shade=document.createElement("div");shade.className="shade";shade.setAttribute("role","presentation");const card=document.createElement("section");card.className="detail";card.tabIndex=-1;card.setAttribute("role","dialog");card.setAttribute("aria-modal","true");card.setAttribute("aria-label",item.name);
 const h=document.createElement("h2");h.textContent=item.name;card.append(h);
 const p=document.createElement("p");p.textContent=item.detail;card.append(p);
 if(item.why){const h3=document.createElement("h3");h3.textContent="Место в последовательности";card.append(h3);const q=document.createElement("p");q.textContent=item.why;card.append(q)}
 const h3=document.createElement("h3");h3.textContent="Учебные материалы";card.append(h3);
 const links=document.createElement("p");const a=document.createElement("a");a.href=SOURCE;a.textContent="Образец преподавателя";a.target="_blank";a.rel="noopener";links.append(a,document.createTextNode(" · "));const l=document.createElement("a");l.href=L3;l.textContent="Подробный ответ L3";l.target="_blank";l.rel="noopener";links.append(l);card.append(links);
 const fine=document.createElement("p");fine.className="muted";fine.textContent="Прокрутите содержимое, если оно длинное. Для закрытия нажмите вне карточки.";card.append(fine);
 shade.append(card);modalHost.append(shade);card.focus();
 function close(){shade.remove();modalOpen=false;document.removeEventListener("keydown",onKey);if(previous&&previous.isConnected)previous.focus({preventScroll:true})}
 function onKey(e){if(e.key==="Escape"){e.preventDefault();close()}else if(e.key==="Tab"){e.preventDefault();card.focus()}}
 shade.addEventListener("pointerdown",e=>{if(e.target===shade)close()});document.addEventListener("keydown",onKey)
}
function moveItem(id,targetZone,index,fromDrag=false){clearButtonFeedback();const from=sand.includes(id)?sand:pyramid;const to=targetZone==="sand"?sand:pyramid;let at=from.indexOf(id);if(at<0)return;from.splice(at,1);if(to===from&&!fromDrag&&index>at)index--;index=Math.max(0,Math.min(index,to.length));to.splice(index,0,id);hintState={signature:"",level:0};persist();render();document.getElementById("saveStatus").textContent="Сборка сохранена"}
function closestInsertion(node,y,ignoreId){const bricks=[...node.querySelectorAll(".brick")].filter(n=>n.dataset.id!==ignoreId);for(let i=0;i<bricks.length;i++){const r=bricks[i].getBoundingClientRect();if(y<r.top+r.height/2)return i}return bricks.length}
function touchStart(e){
 if(modalOpen||dragging||activeTouch||e.touches.length!==1)return;
 activeTouch=true;
 const brick=e.currentTarget,id=brick.dataset.id,first=e.touches[0],finger=first.identifier;
 const downX=first.clientX,downY=first.clientY;
 let held=false,aborted=false,ghost=null,lastX=downX,lastY=downY,scrollFrame=0;
 let timer=window.setTimeout(()=>{if(aborted||!brick.isConnected)return;held=true;dragging=true;brick.classList.add("drag-source");ghost=document.createElement("div");ghost.className="ghost";ghost.textContent=dataById.get(id).name;ghost.style.width=brick.getBoundingClientRect().width+"px";document.body.append(ghost);position(lastX,lastY);scrollFrame=requestAnimationFrame(scrollNearEdge)},245);
 function position(x,y){if(!ghost)return;ghost.style.left=(x-ghost.offsetWidth/2)+"px";ghost.style.top=(y-15)+"px"}
 function fingerIn(list){for(let i=0;i<list.length;i++)if(list[i].identifier===finger)return list[i];return null}
 function targetAt(x){const l=sandNode.getBoundingClientRect(),r=pyramidNode.getBoundingClientRect();if(x>=l.left&&x<=l.right)return sandNode;if(x>=r.left&&x<=r.right)return pyramidNode;return null}
 function scrollNearEdge(){scrollFrame=0;if(!held)return;const node=targetAt(lastX);if(node){const r=node.getBoundingClientRect();if(lastY<r.top+40&&lastY>=r.top-20)node.scrollTop-=9;else if(lastY>r.bottom-40&&lastY<=r.bottom+20)node.scrollTop+=9}scrollFrame=requestAnimationFrame(scrollNearEdge)}
 function cleanup(){window.clearTimeout(timer);if(scrollFrame)cancelAnimationFrame(scrollFrame);document.removeEventListener("touchmove",move);document.removeEventListener("touchend",end);document.removeEventListener("touchcancel",cancel);if(ghost)ghost.remove();brick.classList.remove("drag-source");dragging=false;activeTouch=false}
 function move(ev){if(ev.touches.length!==1){cleanup();return}const t=fingerIn(ev.touches);if(!t)return;lastX=t.clientX;lastY=t.clientY;if(!held){if(Math.hypot(lastX-downX,lastY-downY)>9){aborted=true;window.clearTimeout(timer)}return}if(ev.cancelable)ev.preventDefault();position(lastX,lastY)}
 function end(ev){const t=fingerIn(ev.changedTouches);if(!t)return;const active=held,x=t.clientX,y=t.clientY;cleanup();if(!active){if(!aborted){if(ev.cancelable)ev.preventDefault();modalFor(id)}return}if(ev.cancelable)ev.preventDefault();const node=targetAt(x);if(!node)return;moveItem(id,node===sandNode?"sand":"pyramid",closestInsertion(node,y,id),true)}
 function cancel(ev){if(fingerIn(ev.changedTouches))cleanup()}
 document.addEventListener("touchmove",move,{passive:false});document.addEventListener("touchend",end,{passive:false});document.addEventListener("touchcancel",cancel,{passive:true});
}
function zoneAtX(x){const a=sandNode.getBoundingClientRect(),b=pyramidNode.getBoundingClientRect();if(x>=a.left&&x<=a.right)return "sand";if(x>=b.left&&x<=b.right)return "pyramid";return null}
function applyLayout(){document.getElementById("gameBoard").classList.toggle("swapped",layoutSwapped);document.getElementById("swapBtn").setAttribute("aria-pressed",String(layoutSwapped))}
document.getElementById("swapBtn").addEventListener("click",()=>{layoutSwapped=!layoutSwapped;applyLayout();persist()});
function pointerStart(e){if(e.pointerType==="touch"&&"ontouchstart" in window)return;if(modalOpen||dragging||e.button!==0)return;const brick=e.currentTarget;const id=brick.dataset.id;const downX=e.clientX,downY=e.clientY;let held=false,aborted=false,ghost=null,lastX=downX,lastY=downY;let timer=window.setTimeout(()=>{if(aborted)return;held=true;dragging=true;brick.classList.add("drag-source");ghost=document.createElement("div");ghost.className="ghost";ghost.textContent=dataById.get(id).name;ghost.style.width=brick.getBoundingClientRect().width+"px";document.body.append(ghost);position(lastX,lastY);},245);
 function position(x,y){if(!ghost)return;ghost.style.left=(x-ghost.offsetWidth/2)+"px";ghost.style.top=(y-15)+"px"}
 function cleanup(){window.clearTimeout(timer);document.removeEventListener("pointermove",move);document.removeEventListener("pointerup",end);document.removeEventListener("pointercancel",cancel);if(ghost)ghost.remove();brick.classList.remove("drag-source");dragging=false}
 function move(ev){lastX=ev.clientX;lastY=ev.clientY;if(!held&&Math.hypot(lastX-downX,lastY-downY)>9){aborted=true;clearTimeout(timer);return}if(!held)return;ev.preventDefault();position(lastX,lastY);const target=zoneAtX(lastX);if(!target)return;const node=target==="sand"?sandNode:pyramidNode;if(ev.clientY<node.getBoundingClientRect().top+35)node.scrollTop-=10;if(ev.clientY>node.getBoundingClientRect().bottom-35)node.scrollTop+=10}
 function end(ev){const active=held,x=ev.clientX,y=ev.clientY;cleanup();if(!active){if(!aborted)modalFor(id);return}const l=sandNode.getBoundingClientRect(),r=pyramidNode.getBoundingClientRect();let zone=(x>r.left&&x<r.right)?"pyramid":(x>l.left&&x<l.right)?"sand":null;if(!zone)return;const node=zone==="sand"?sandNode:pyramidNode;moveItem(id,zone,closestInsertion(node,y,id),true)}
 function cancel(){cleanup()}
 document.addEventListener("pointermove",move,{passive:false});document.addEventListener("pointerup",end);document.addEventListener("pointercancel",cancel);
}
function keyboardStart(e){const id=e.currentTarget.dataset.id;if(e.key==="Enter"&&!keyboardPick){e.preventDefault();modalFor(id);return}if(e.key===" "){e.preventDefault();keyboardPick={id,zone:"pyramid",index:pyramid.length};showReport("Клавиатурный перенос",["Нажмите стрелки вверх/вниз для выбора места, стрелки влево/вправо для столбца, Enter для вставки, Esc для отмены."])}}
document.addEventListener("keydown",e=>{if(!keyboardPick||modalOpen)return;const k=keyboardPick;if(e.key==="Escape"){keyboardPick=null;showReport("Перенос отменён",["Кирпичики остались на своих местах."]);return}if(["ArrowUp","ArrowDown","ArrowLeft","ArrowRight","Enter"].includes(e.key)){e.preventDefault();if(e.key==="ArrowLeft")k.zone="sand";if(e.key==="ArrowRight")k.zone="pyramid";if(e.key==="ArrowUp")k.index=Math.max(0,k.index-1);if(e.key==="ArrowDown")k.index=Math.min((k.zone==="sand"?sand:pyramid).length,k.index+1);if(e.key==="Enter"){moveItem(k.id,k.zone,k.index);keyboardPick=null;showReport("Кирпичик перемещён",["Проверьте порядок или продолжайте сборку."])}else showReport("Место вставки",["Столбец: "+(k.zone==="sand"?"Песочница":"Пирамида")+", позиция: "+(k.index+1)])}});
function diagnose(){const present=new Set(pyramid),missing=required.filter(id=>!present.has(id)),extra=pyramid.filter(id=>dataById.get(id).extra),actual=pyramid.filter(id=>!dataById.get(id).extra);
 // LIS: minimum number of displaced items in the present required sequence.
 const indices=actual.map(id=>required.indexOf(id)),n=indices.length,dp=Array(n).fill(1),parent=Array(n).fill(-1);let best=0;
 for(let i=0;i<n;i++){for(let j=0;j<i;j++){if(indices[j]<indices[i]&&dp[j]+1>dp[i]){dp[i]=dp[j]+1;parent[i]=j}}if(n&&dp[i]>dp[best])best=i}
 const stable=new Set();if(n){let q=best;while(q>=0){stable.add(actual[q]);q=parent[q]}}
 const misplaced=actual.filter(id=>!stable.has(id));
 const errors=[];if(extra.length)errors.push({kind:"extra",ids:extra,message:"Посторонние элементы в Пирамиде: "+extra.map(id=>dataById.get(id).name).join(", ")+". Их следует вернуть в Песочницу."});
 if(missing.length)errors.push({kind:"missing",ids:missing,message:"Не хватает обязательных элементов: "+missing.length+". Они остаются в Песочнице."});
 if(misplaced.length)errors.push({kind:"order",ids:misplaced,message:"Нарушен порядок. Достаточно переставить "+misplaced.length+" "+(misplaced.length===1?"кирпичик.":"кирпичика(ов).")+" Проверьте взаимное расположение этапов."});
 return {missing,extra,misplaced,errors,correct:!missing.length&&!extra.length&&!misplaced.length}}

document.getElementById("checkBtn").addEventListener("click",()=>{
 const d=diagnose();
 if(d.correct){
   showReport(isDiagnostic?"Учебная последовательность восстановлена":"Порядок учебного образца собран верно",
    [game.successText, isDiagnostic?
    "Это учебная самопроверка, а не аттестованный автоматический экзаменационный ключ. Содержание молитв и история требуют отдельного ответа.":
    "Это самопроверка последовательности, а не официальный допуск: объяснение молитв, уставные детали и история оцениваются отдельно."],"good");
 }else{
   const msgs=d.errors.map(x=>x.message);
   if(!isDiagnostic&&d.misplaced.length)msgs.push("Подсказка под Песочницей поможет определить направление исправления.");
   showReport(isDiagnostic?"Остались нарушения: "+d.errors.length+" группы":"Обнаружены нарушения: "+d.errors.length+" групп(ы)",msgs,"warn");
 }
 showButtonFeedback("check",d.correct?(isDiagnostic?"Учебная последовательность восстановлена":"Порядок собран верно"):(isDiagnostic?"Проверьте нарушения":"Нарушения: "+d.errors.length+" групп(ы)"),d.correct?(isDiagnostic?[]:["Основные элементы в правильном порядке."]):d.errors.map(x=>x.message));
 if(d.correct)showSuccessL3Link();
});
function hintProblem(){
 const d=diagnose();
 if(d.extra.length){
  const id=d.extra[0];
  return{kind:"extra",id,signature:"extra:"+id,lines:[
   game.hintExtra,
   (isDiagnostic?"Откройте описание «":"Обратите внимание на кирпичик «")+dataById.get(id).name+"».",
   isDiagnostic?"Этот элемент в выбранном обычном случае не нужен. Верните его в Песочницу.":"Этот кирпичик относится к другому этапу Литургии. Верните его в Песочницу."
  ]};
 }
 if(d.missing.length){
  const id=d.missing[0],idx=required.indexOf(id),
   before=required.slice(0,idx).reverse().find(x=>pyramid.includes(x)),
   after=required.slice(idx+1).find(x=>pyramid.includes(x));
  return{kind:"missing",id,signature:"missing:"+id,lines:[
   isDiagnostic?"Не все молитвы и песнопения представлены в Пирамиде.":"Пирамида пока неполна. Проверьте недостающий этап в Песочнице.",
   (isDiagnostic?"Отыщите в Песочнице «":"Найдите кирпичик «")+dataById.get(id).name+"».",
   "Его место: "+(before?"после «"+dataById.get(before).name+"»":after?"перед «"+dataById.get(after).name+"»":"в начале")+(after&&before?" и перед «"+dataById.get(after).name+"»":"")+". Перенесите самостоятельно."
  ]};
 }
 if(d.misplaced.length){
  const id=d.misplaced[0],idx=required.indexOf(id),
   before=required.slice(0,idx).reverse().find(x=>pyramid.includes(x)),
   after=required.slice(idx+1).find(x=>pyramid.includes(x));
  return{kind:"order",id,signature:"order:"+pyramid.join(","),lines:[
   isDiagnostic?"Проверьте последовательность чтений Священного Писания.":"Состав близок к верному, но есть нарушение последовательности. Сравните соседние этапы.",
   (isDiagnostic?"Обратите внимание на место «":"Проверьте место кирпичика «")+dataById.get(id).name+"».",
   "Правильная опора: "+(before?"после «"+dataById.get(before).name+"»":"в начале")+(after?" и перед «"+dataById.get(after).name+"»":"")+". Переместите кирпичик сами."
  ]};
 }
 return null;
}
document.getElementById("hintBtn").addEventListener("click",()=>{
 const h=hintProblem();
 if(!h){
  showReport("Подсказка не требуется",[isDiagnostic?"Учебный порядок уже восстановлен.":"Основная последовательность учебного образца собрана. Для экзамена дополнительно изучите содержание молитв и толкование."]);
  showButtonFeedback("hint","Подсказка не требуется",[isDiagnostic?"Нарушений состава и порядка нет.":"Основная последовательность собрана."]);
  return;
 }
 if(h.signature!==hintState.signature)hintState={signature:h.signature,level:0};
 hintState.level=Math.min(3,hintState.level+1);
 const message=h.lines[hintState.level-1];
 showReport("Подсказка "+hintState.level+" из 3",[message]);
 showButtonFeedback("hint","Уровень "+hintState.level+" из 3",[message]);
});
document.getElementById("resetBtn").addEventListener("click",()=>{
 const prompt=isDiagnostic?"Вернуть исходную Пирамиду с ошибками? Все ваши исправления будут сброшены.":"Начать сборку заново? Текущая Пирамида будет очищена.";
 if(!confirm(prompt))return;
 clearButtonFeedback();
 pyramid=isDiagnostic?[...START_PYRAMID]:[];
 sand=shuffled(DATA.map(x=>x.id).filter(id=>!pyramid.includes(id)));
 hintState={signature:"",level:0};
 persist();render(false);
 showReport(isDiagnostic?"Начальная Пирамида восстановлена":"Новая сборка",
  [isDiagnostic?"Исправляйте ошибки заново. Расположение столбцов сохранено.":"Кирпичики перемешаны, Пирамида очищена."]);
});
function shuffleVisual(){if(modalOpen||dragging||animationInProgress||sand.length<2||document.hidden)return;const i=Math.floor(Math.random()*sand.length),j=Math.floor(Math.random()*sand.length);if(i===j)return;animationInProgress=true;const before=new Map([...sandNode.querySelectorAll(".brick")].map(n=>[n.dataset.id,n.getBoundingClientRect().top]));[sand[i],sand[j]]=[sand[j],sand[i]];persist();render();if(matchMedia("(prefers-reduced-motion: reduce)").matches){animationInProgress=false;return}
 const els=[...sandNode.querySelectorAll(".brick")];els.forEach(el=>{let dy=before.get(el.dataset.id)-el.getBoundingClientRect().top;el.style.transition="none";el.style.transform="translateY("+dy+"px)"});requestAnimationFrame(()=>requestAnimationFrame(()=>{els.forEach(el=>{el.style.transition="transform 1s ease-in-out";el.style.transform="translateY(0)"})}));setTimeout(()=>animationInProgress=false,1050)}
setInterval(shuffleVisual,4200);
init();

}
initLiturgicsTrainer().catch(error=>{
 const report=document.getElementById("report");
 if(report)report.textContent="Ошибка запуска учебного задания: "+error.message;
});
