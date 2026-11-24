---
layout: default
title: "Всенощное бдение — последование"
---

<style>
.vg-root{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;max-width:840px;color:#243941;line-height:1.52}
.vg-root *{box-sizing:border-box}
.vg-root [hidden]{display:none!important}
.vg-root button,.vg-root summary{font:inherit}
.vg-root button{cursor:pointer;background:#fff;color:#176474;border:1px solid #c8d7da;border-radius:10px;min-height:42px;padding:9px 13px}
.vg-root button:hover:not(:disabled){background:#eef7f8}
.vg-root button:disabled{cursor:default;opacity:.85}
.vg-root button:focus-visible,.vg-root summary:focus-visible{outline:3px solid #c39a45;outline-offset:2px}
.vg-root .vg-heading{display:flex;justify-content:space-between;align-items:center;gap:12px;margin:12px 0;color:#59717a;font-size:.86rem}
.vg-root progress{width:100%;accent-color:#176776;height:9px;display:block;margin:7px 0 19px}
.vg-root .vg-step-picker{font-size:.87rem;margin:0 0 15px;color:#506a73}
.vg-root .vg-step-picker summary{cursor:pointer}
.vg-root .vg-stream{display:flex;flex-direction:column;gap:13px}
.vg-root .vg-step{border:1px solid #d1dfe2;border-radius:12px;padding:14px 17px;background:#fff;scroll-margin-top:15px}
.vg-root .vg-step.vg-current{border:2px solid #5b9ca5;background:#fbfefe}
.vg-root .vg-section-label{margin:0 0 10px;border-radius:7px;background:#e9f4f5;padding:7px 10px;color:#205b67;font-size:.87rem;font-weight:700}
.vg-root .vg-step-head{display:flex;justify-content:space-between;gap:8px;color:#667981;font-size:.8rem}
.vg-root .vg-cue{padding:14px;margin:10px 0;background:#f2f7f7;border-radius:9px;font-size:1.13rem;white-space:pre-wrap}
.vg-root .vg-reveal{background:#176776;color:#fff;border-color:#176776;margin:4px 0 10px}
.vg-root .vg-reveal:hover{color:#176776}
.vg-root .vg-name h2{font-size:1.17rem;margin:8px 0 4px}
.vg-root .vg-name p{color:#506872;margin:0 0 11px}
.vg-root .vg-quiz{border-top:1px solid #e3ebed;padding-top:11px;margin-top:12px}
.vg-root .vg-quiz h3,.vg-root .vg-name-quiz h3{font-size:1.03rem;margin:0 0 9px}
.vg-root .vg-name-quiz{margin-top:10px}
.vg-root .vg-name{margin-top:10px}
.vg-root .vg-name .vg-good,.vg-root .vg-name .vg-error{margin:0 0 4px}
.vg-root .vg-choices{display:grid;gap:7px}
.vg-root .vg-choice{text-align:left;line-height:1.45;min-height:45px;white-space:normal}
.vg-root .vg-choice.is-correct{background:#e4f4eb;border:2px solid #3d8b64;color:#145639;opacity:1}
.vg-root .vg-choice.is-wrong{background:#fff0ed;border:2px solid #bf6e61;color:#923a30;opacity:1}
.vg-root .vg-feedback{margin:8px 0 0;font-size:.92rem}
.vg-root .vg-feedback p{margin:5px 0}
.vg-root .vg-good{color:#236c4c;font-weight:600}
.vg-root .vg-error{color:#a14134;font-weight:600}
.vg-root .vg-details{margin-top:13px;border-top:1px dashed #d5e0e3;padding-top:8px;font-size:.88rem}
.vg-root .vg-details summary{cursor:pointer;color:#536d75}
.vg-root .vg-details details{padding:6px;margin:6px 0;border-left:2px solid #d4e2e4}
.vg-root .vg-details ul{padding-left:22px}
.vg-root .vg-source{font-size:.79rem;color:#647981}
.vg-root .vg-source-link{display:block;margin:10px 0}
.vg-root .vg-terminal{margin-top:8px;font-weight:650;color:#236c4c}
.vg-root .vg-jump{position:fixed;right:max(14px,calc((100vw - 850px)/2));bottom:22px;z-index:20;background:#176776;color:white;border-color:#176776;box-shadow:0 4px 16px #0002;padding:12px 18px}
.vg-root .vg-jump:hover:not(:disabled){color:#176776}
.vg-root .vg-results{border:2px solid #8ab3b9;border-radius:14px;padding:16px 14px}
.vg-root .vg-results h2{margin:0 0 12px;font-size:1.27rem}
.vg-root .vg-stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(110px,1fr));gap:9px}
.vg-root .vg-stat{background:#eff7f7;border-radius:8px;padding:12px;text-align:center}
.vg-root .vg-stat span{display:block;color:#59727b;font-size:.85rem}
.vg-root .vg-stat strong{display:block;font-size:1.32rem}
.vg-root .vg-review{display:block;margin:6px 0;text-align:left;width:100%}
.vg-root .vg-tools{margin:20px 0;border-top:1px solid #e2ebed;padding-top:10px}
.vg-root .vg-map{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,270px),1fr));gap:7px;padding:10px 0}
.vg-root .vg-map-item{text-align:left;font-size:.86rem}
.vg-root .vg-lessons{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,300px),1fr));gap:12px;padding:12px 0}
.vg-root .vg-lesson{border:1px solid #d4e0e3;padding:11px;border-radius:9px}
.vg-root .vg-lesson h3{margin:0;font-size:1rem}
.vg-root .vg-lesson ol{padding-left:21px}
.vg-root .vg-lesson li{margin:5px 0;font-size:.87rem}
@media(max-width:550px){.vg-root .vg-step{padding:12px}.vg-root .vg-cue{font-size:1.05rem}.vg-root .vg-stats{grid-template-columns:repeat(2,1fr)}.vg-root .vg-jump{right:14px;bottom:14px}}
@media(prefers-reduced-motion:reduce){.vg-root *{scroll-behavior:auto!important}}
</style>

# Всенощное бдение — восстанови последование

[← Все викторины Литургики](quiz/index.html) · [Литургика — вопросы](index.html) · [Сравнительная таблица служб](vespers-matins.html)

Узнавайте богослужебные молитвословия и действия по начальным словам. Восстанавливайте их порядок — от вечерни до первого часа.

<div class="vg-root" id="vigil-guide"
 data-source="{{ '/assets/liturgics/vigil-guided-data.json' | relative_url }}"
 data-compare="{{ '/subjects/liturgics/2027/vespers-matins.html' | relative_url }}">
 <div id="vg-status" role="status" aria-live="polite">Загрузка последования…</div>
 <div id="vg-loaded" hidden>
  <div class="vg-heading">
   <span>Великая вечерня → Утреня → Первый час</span>
   <span id="vg-counter">1 / 72</span>
  </div>
  <progress id="vg-progress" value="1" max="72" aria-label="Продвижение по последованию"></progress>
  <details id="vg-map" class="vg-step-picker">
   <summary>Перейти к нужному шагу (1–72)</summary>
   <div id="vg-menu" class="vg-map"></div>
  </details>
  <div id="vg-stream" class="vg-stream" aria-label="Последование всенощного бдения"></div>
  <button id="vg-jump" class="vg-jump" type="button" hidden aria-label="Долистать вниз до текущего шага">↓ К концу ленты</button>
  <div class="vg-tools">
   <details>
    <summary>План двух занятий</summary>
    <div id="vg-course" class="vg-lessons"></div>
   </details>
   <button id="vg-reset" type="button">Начать новое прохождение</button>
  </div>
 </div>
</div>
<script src="{{ '/assets/liturgics/vigil-guided.js' | relative_url }}" defer></script>

## Порядок работы

Начальные слова → **«Как это называется?»** (от двух до пяти близких названий) → проверка и краткое определение → автоматическое открытие вопроса **«Что следует дальше?»** (три варианта) → проверка ответа → появление следующего шага ниже.

Всё пройденное остаётся на одной странице. Прокручивайте ленту вверх для повторения; стрелка **«↓ К концу ленты»** возвращает к текущему шагу. После последней карточки появляются итоги прохождения. При необходимости раскройте «Подробнее» у любого шага.

## Учебники и основания

**Архиепископ Аверкий (Таушев), «Литургика», часть 2:** § 1 «Начало всенощного бдения. Вечерня»; § 2 «Вторая часть всенощного бдения. Утреня»; § 3 «Первый час и окончание всенощного бдения». Краткие объяснения составлены по соответствующим разделам учебника. Последование Колобанова (2017) используется как **образец бденной службы** при праздновании Введения во храм; воскресный образец игумена Кронида (Лысенко) показывает другой конкретный случай. Сведения об уставных развилках опираются на Типикон, в частности главы 2, 3 и 48. Оригинальный сборник Колобанова остаётся в закрытой библиотеке проекта.

Для сравнения видов служб используйте [цифровую таблицу](vespers-matins.html), а для конкретного календарного случая — Типикон и Богослужебные указания.
