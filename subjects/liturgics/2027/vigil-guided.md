---
layout: default
title: "Всенощное бдение — узнаём и понимаем последование"
---

<style>
.vg-root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.5;color:#20343c;max-width:900px}
.vg-root *{box-sizing:border-box}
.vg-root [hidden]{display:none!important}
.vg-root button,.vg-root summary{font:inherit}
.vg-root button{cursor:pointer;border:1px solid #c6d5d9;background:#fff;border-radius:10px;color:#174f5d;padding:10px 15px;min-height:43px}
.vg-root button:disabled{opacity:.5;cursor:default}
.vg-root button:focus-visible,.vg-root summary:focus-visible,.vg-root input:focus-visible{outline:3px solid #b08a39;outline-offset:3px}
.vg-root button:hover:not(:disabled){background:#eff7f7}
.vg-root .vg-toolbar,.vg-root .vg-controls{display:flex;align-items:center;justify-content:space-between;gap:8px;flex-wrap:wrap;margin:14px 0}
.vg-root .vg-mode{display:flex;align-items:center;gap:7px;font-size:.94rem;cursor:pointer}
.vg-root .vg-mode input{height:19px;width:19px;accent-color:#176776}
.vg-root .vg-sections{display:flex;gap:6px;flex-wrap:wrap;margin:12px 0}
.vg-root .vg-section-button{font-size:.84rem;padding:8px 11px}
.vg-root .vg-section-button[aria-pressed="true"]{background:#176776;color:#fff;border-color:#176776}
.vg-root .vg-main{border:1px solid #c9dadd;border-radius:14px;background:#fff;overflow:hidden}
.vg-root .vg-cardheader{background:#f3f8f8;padding:12px 17px;color:#46606b}
.vg-root .vg-meta{display:flex;justify-content:space-between;gap:10px;font-size:.84rem}
.vg-root progress{width:100%;height:8px;accent-color:#176776;display:block;margin:10px 0 0}
.vg-root .vg-content{padding:17px}
.vg-root .vg-cue{padding:18px 14px;background:#f1f7f7;border-radius:11px;text-align:center;font-size:1.23rem;margin:12px 0;line-height:1.55}
.vg-root h2{font-size:1.35rem;margin:5px 0 0}
.vg-root h3{font-size:1.06rem;margin:8px 0}
.vg-root #vg-show-name{display:block;margin:12px auto;background:#176776;color:#fff;border-color:#176776}
.vg-root #vg-show-name[hidden]{display:none}
.vg-root #vg-definition{color:#526c74;margin:5px 0 15px}
.vg-root .vg-quiz{margin-top:15px}
.vg-root .vg-choices{display:grid;gap:8px;margin-top:10px}
.vg-root .vg-choice{text-align:left;line-height:1.35;min-height:52px;white-space:normal}
.vg-root .vg-choice.is-correct{border:2px solid #348369;background:#e7f6ee;color:#15583c;opacity:1}
.vg-root .vg-choice.is-wrong{border:2px solid #bc675b;background:#fff0ed;color:#85372e;opacity:1}
.vg-root .vg-feedback{font-size:.93rem;margin-top:9px}
.vg-root .vg-good{color:#216a4b;font-weight:600}
.vg-root .vg-error{color:#994739;font-weight:600}
.vg-root .vg-footer{display:flex;justify-content:space-between;gap:12px;align-items:center;margin-top:16px;border-top:1px solid #e1e9ec;padding-top:13px}
.vg-root .vg-forward{background:#176776;color:#fff;border-color:#176776}
.vg-root .vg-forward:hover:not(:disabled){background:#105966;color:#fff}
.vg-root .vg-muted{font-size:.88rem;color:#536c75}
.vg-root details{border:1px solid #d3dfe2;border-radius:10px;margin-top:14px;padding:10px 14px}
.vg-root details summary{cursor:pointer;font-weight:600}
.vg-root .vg-details p{margin:8px 0}
.vg-root .vg-details ul{padding-left:23px}
.vg-root .vg-source{font-size:.8rem;color:#5e757b}
.vg-root .vg-ribbon-head{display:flex;justify-content:space-between;align-items:center;margin:24px 0 8px}
.vg-root .vg-ribbon{height:226px;overflow-y:auto;overscroll-behavior:contain;border:1px solid #d3dfe2;border-radius:11px;padding:6px;background:#fbfcfc}
.vg-root .vg-ribbon-section{font-size:.77rem;font-weight:700;color:#546d78;text-transform:uppercase;padding:9px 8px 3px}
.vg-root .vg-ribbon-item{display:block;width:100%;min-height:35px;padding:7px 10px;text-align:left;border:0;background:transparent;font-size:.87rem;color:#26434e}
.vg-root .vg-ribbon-item[aria-current="step"]{background:#dcecee;font-weight:700}
.vg-root .vg-ribbon-item.is-correct:before{content:"✓ ";color:#228257}
.vg-root .vg-ribbon-item.is-wrong:before{content:"• ";color:#b74e42}
.vg-root .vg-map{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:5px;margin:10px 0}
.vg-root .vg-map-item{text-align:left;padding:6px 8px;min-height:34px;font-size:.85rem}
.vg-root .vg-map-item[aria-current="step"]{background:#176776;color:#fff}
.vg-root .vg-lessons{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,280px),1fr));gap:12px}
.vg-root .vg-lesson{padding:12px;border:1px solid #d1dfe2;border-radius:8px}
.vg-root .vg-lesson ol{padding-left:23px}
.vg-root .vg-lesson li{font-size:.88rem;margin:5px 0}
.vg-root .vg-complete{text-align:center;padding:14px}
.vg-root .vg-complete button{background:#176776;color:white}
.vg-root .vg-summary{display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:9px;margin:16px 0}
.vg-root .vg-stat{border:1px solid #d4e1e3;border-radius:9px;padding:12px 10px;text-align:center}
.vg-root .vg-stat span{display:block;font-size:.83rem;color:#536d75}
.vg-root .vg-stat strong{display:block;font-size:1.35rem}
.vg-root .vg-summary .vg-muted{grid-column:1/-1;text-align:left}
.vg-root .vg-source-link{display:inline-block;margin:8px 0}
@media(max-width:550px){.vg-root .vg-content{padding:13px}.vg-root .vg-cardheader{padding:12px}.vg-root .vg-cue{font-size:1.07rem;padding:16px 10px}.vg-root .vg-footer button{flex:1}.vg-root .vg-summary{grid-template-columns:repeat(2,1fr)}}
</style>

# Всенощное бдение — восстанови последование

[← Литургика](index.html) · [Сравнительная таблица служб](vespers-matins.html) · [Богослужебный практикум](practicum/index.html)

Узнайте молитвословие по первым словам и выберите **что следует дальше**. Постепенно соберите всю службу — от вечерни до первого часа.

<div class="vg-root" id="vigil-guide"
 data-source="{{ '/assets/liturgics/vigil-guided-data.json' | relative_url }}"
 data-compare="{{ '/subjects/liturgics/2027/vespers-matins.html' | relative_url }}">
 <div id="vg-status" role="status" aria-live="polite">Загрузка последования…</div>
 <div id="vg-loaded" hidden>
  <div class="vg-toolbar">
   <label class="vg-mode"><input id="vg-training" type="checkbox" checked> Скрывать название для самопроверки</label>
  </div>
  <div class="vg-sections" id="vg-section" role="group" aria-label="Части всенощного бдения"></div>
  <article class="vg-main">
   <div class="vg-cardheader">
    <div class="vg-meta"><span id="vg-counter"></span><span id="vg-role"></span></div>
    <progress id="vg-progress" value="1" max="72"></progress>
   </div>
   <div class="vg-content">
    <div class="vg-cue" id="vg-cue"></div>
    <h2 id="vg-title" hidden></h2>
    <button id="vg-show-name" type="button">Узнать элемент</button>
    <p id="vg-definition" hidden></p>
    <section id="vg-quiz" class="vg-quiz" hidden aria-label="Викторина">
     <h3>Что дальше?</h3>
     <div id="vg-choices" class="vg-choices" role="group" aria-label="Три варианта следующего элемента"></div>
     <div id="vg-feedback" class="vg-feedback" role="status" aria-live="polite"></div>
    </section>
    <section id="vg-complete" class="vg-complete" hidden aria-label="Завершение прохождения">
     <h3>Последний элемент последования</h3>
     <button id="vg-finish" type="button">Подвести итоги</button>
    </section>
    <div id="vg-summary" class="vg-summary" hidden aria-label="Статистика прохождения"></div>
    <button id="vg-new-run" type="button" hidden>Новое прохождение</button>
    <div class="vg-footer">
     <button id="vg-back" type="button">← Назад</button>
     <button id="vg-forward" class="vg-forward" type="button">Далее →</button>
    </div>
   </div>
  </article>
  <div class="vg-ribbon-head">
   <strong>Лента последования</strong>
   <span class="vg-muted" id="vg-ribbon-count"></span>
  </div>
  <div id="vg-ribbon" class="vg-ribbon" tabindex="0" aria-label="Пройденные элементы богослужения. Список прокручивается."></div>
  <details id="vg-map">
   <summary>Все 72 шага · перейти к любому</summary>
   <div id="vg-menu" class="vg-map"></div>
  </details>
  <details id="vg-more" class="vg-details">
   <summary>Подробнее о текущем элементе</summary>
   <p id="vg-question"></p>
   <p id="vg-answer"></p>
   <details id="vg-detail-elements" hidden>
    <summary>Состав элемента</summary>
    <ul id="vg-detail-list"></ul>
   </details>
   <details id="vg-conditions" hidden>
    <summary>Уставные варианты</summary>
    <ul id="vg-conditions-list"></ul>
   </details>
   <a id="vg-table-link" class="vg-source-link" hidden href="vespers-matins.html">Сравнительная таблица служб</a>
   <p id="vg-source" class="vg-source"></p>
  </details>
  <details>
   <summary>План двух занятий</summary>
   <div id="vg-course" class="vg-lessons"></div>
  </details>
  <div class="vg-controls">
   <button id="vg-reset" type="button">Начать новое прохождение</button>
  </div>
 </div>
</div>
<script src="{{ '/assets/liturgics/vigil-guided.js' | relative_url }}" defer></script>

## Как устроена игра

На каждом шаге сначала узнаём элемент службы по начальным словам, затем выбираем следующий из трёх вариантов. Ошибка не мешает продолжить: правильный ответ появляется сразу. Пройденные элементы сохраняются в прокручиваемой ленте. Можно свободно переходить по шагам. При завершении показываются ответы, ошибки, пропуски, процент правильных ответов и время активности.

Если нужен уставный разбор, откройте «Подробнее». Уставные варианты и частные примеры не следует считать единым обязательным порядком всех служб.

## Учебники и основания

**Архиепископ Аверкий (Таушев), «Литургика», часть 2:** § 1 «Начало всенощного бдения. Вечерня»; § 2 «Вторая часть всенощного бдения. Утреня»; § 3 «Первый час и окончание всенощного бдения». Краткие объяснения составлены по соответствующим разделам учебника. Последование Колобанова (2017) используется как **образец бденной службы** при праздновании Введения во храм; воскресный образец игумена Кронида (Лысенко) показывает другой конкретный случай. Сведения об уставных развилках опираются на Типикон, в частности главы 2, 3 и 48. Оригинальный сборник Колобанова остаётся в закрытой библиотеке проекта.

Для сравнения видов служб используйте [цифровую таблицу](vespers-matins.html), а для конкретного календарного случая — Типикон и Богослужебные указания.
