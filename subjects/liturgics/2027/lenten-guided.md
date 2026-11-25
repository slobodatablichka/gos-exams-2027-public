---
layout: default
title: "Великопостное богослужение — изучение и самопроверка"
---

# Великопостное богослужение — изучение и самопроверка

[← Все последования](quiz/index.html)

Выберите богослужебный день, изучите суточную схему и отдельные службы. Уставные задания относятся к указанным условиям дня. Ссылки для сравнения ведут к другому, явно названному учебному случаю.

<style>
#lent-guide{max-width:850px;margin:0 auto;overflow-wrap:anywhere}
#lent-guide [hidden]{display:none!important}
#lent-guide select{width:100%;max-width:100%;padding:.65rem;font:inherit;border:1px solid #89999c;border-radius:6px;background:var(--bg,#fff);color:var(--text,#222)}
#lent-guide .lt-fields{display:grid;grid-template-columns:1fr 2fr;gap:12px}
#lent-guide label{display:block;font-weight:600}
#lent-guide .lt-panel{margin:1rem 0;padding:1rem;border:1px solid #9aabad;border-radius:9px}
#lent-guide .lt-nav{display:flex;gap:8px;flex-wrap:wrap}
#lent-guide .lt-nav button,#lent-guide .lt-nav a{padding:.6rem .85rem;border:1px solid #77979c;border-radius:6px;font:inherit;cursor:pointer;background:transparent;color:inherit}
#lent-guide .lt-nav button:disabled{cursor:default;opacity:.7}
#lent-guide .lt-service{display:block;width:100%;text-align:left;margin:.45rem 0;padding:.75rem;border:1px solid #96aeb2;border-radius:7px;background:transparent;color:inherit;font:inherit;cursor:pointer}
#lent-guide .lt-sub{display:block;font-size:.88rem;opacity:.85}
#lent-guide .lt-choice{display:block;width:100%;text-align:left;margin:.5rem 0;padding:.75rem;border:1px solid #8ea5a9;border-radius:7px;background:transparent;color:inherit;font:inherit;cursor:pointer}
#lent-guide .lt-choice:disabled{cursor:default}
#lent-guide .lt-choice.is-correct{border-color:#39835c;background:rgba(57,131,92,.12)}
#lent-guide .lt-choice.is-wrong{border-color:#b65350;background:rgba(182,83,80,.12)}
#lent-guide .lt-current{border-color:#397e89}
#lent-guide .lt-good{color:#28774e;font-weight:600}
#lent-guide .lt-bad{color:#aa3434;font-weight:600}
#lent-guide .lt-jump{position:fixed;bottom:1rem;right:1rem;z-index:20;border:1px solid #397e89;background:#397e89;color:#fff;border-radius:2rem;padding:.7rem 1rem;cursor:pointer}
#lent-guide progress{width:100%}
#lent-guide button:focus-visible,#lent-guide select:focus-visible{outline:3px solid #397e89;outline-offset:2px}
@media(max-width:550px){#lent-guide .lt-fields{grid-template-columns:1fr}#lent-guide .lt-panel{padding:.75rem}}
@media(prefers-color-scheme:dark){#lent-guide select{background:#202426;color:#eee}#lent-guide .lt-good{color:#8bd6a9}#lent-guide .lt-bad{color:#ffaaa6}}
</style>
<div id="lent-guide" data-source="{{ '/assets/liturgics/lenten-guided-data.json' | relative_url }}">
 <p id="lt-status" role="status">Загрузка последований…</p>
 <div id="lt-loaded" hidden>
  <section class="lt-panel" id="lt-picker">
   <div class="lt-fields">
    <label>Период<select id="lt-period"><option value="1">Основные службы</option><option value="2">Особые дни</option><option value="3">Страстная седмица</option></select></label>
    <label>Богослужебный день<select id="lt-day"></select></label>
   </div>
   <div id="lt-case"></div>
  </section>
  <section id="lt-route" hidden>
   <div class="lt-panel">
    <div class="lt-nav"><button id="lt-back" type="button">← К выбору службы</button><button id="lt-reset" type="button">Начать последование заново</button></div>
    <h2 id="lt-title"></h2><p id="lt-passport"></p>
    <p id="lt-counter" role="status"></p><progress id="lt-progress" value="0" max="1"></progress>
    <p id="lt-route-stats"></p>
   </div>
   <div id="lt-stream"></div>
   <button id="lt-jump" class="lt-jump" type="button" hidden>↓ К текущему шагу</button>
  </section>
 </div>
</div>
<script src="{{ '/assets/liturgics/lenten-guided.js' | relative_url }}" defer></script>

## Источники

Типикон, главы 17 и 49 и специальные главы; архиепископ Аверкий (Таушев), «Литургика»; Г. И. Шиманский, «Литургика»; преподавательские материалы БПДС.

[Вопрос №2](q02-l3.html) · [Вопрос №5](q05-l3.html) · [Вопрос №6](q06-l3.html) · [Вопрос №15](q15-l3.html)
