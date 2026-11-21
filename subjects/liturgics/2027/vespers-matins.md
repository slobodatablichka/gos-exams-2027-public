---
layout: default
title: "Вечерня и утреня — цифровая таблица служб"
---

<style>
.vm-tool{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;line-height:1.45;color:#182a32}
.vm-tool *{box-sizing:border-box}
.vm-tool .vm-controls{display:flex;align-items:flex-end;flex-wrap:wrap;gap:.6rem;margin:1rem 0}
.vm-tool label{display:grid;gap:.25rem;font-size:.85rem;font-weight:600;color:#31444a}
.vm-tool select,.vm-tool button{font:inherit;font-size:.95rem;min-height:42px;border:1px solid #b4c5ca;border-radius:7px;background:white;color:#13252b;padding:.48rem .7rem}
.vm-tool select{max-width:min(90vw,460px)}
.vm-tool button{cursor:pointer}
.vm-tool button[aria-pressed="true"]{background:#176776;color:white;border-color:#176776}
.vm-tool button:focus-visible,.vm-tool select:focus-visible{outline:3px solid #e3a34c;outline-offset:2px}
.vm-tool .vm-status{margin:.7rem 0}
.vm-tool .vm-scroller{max-width:100%;max-height:75vh;overflow:auto;border:1px solid #c8d3d6;border-radius:6px;isolation:isolate;overscroll-behavior:contain}
.vm-tool table{border-collapse:separate;border-spacing:0;width:max-content;table-layout:fixed;font-size:14px}
.vm-tool th,.vm-tool td{border-right:1px solid #bdc9ce;border-bottom:1px solid #bdc9ce;padding:9px;vertical-align:top;min-width:145px;max-width:220px;overflow-wrap:anywhere;white-space:pre-wrap}
.vm-tool thead th{position:sticky;top:0;z-index:5;background:#e9f2f3;text-align:left}
.vm-tool th.vm-sticky{position:sticky;left:0;z-index:6;background:#ecf4f5;min-width:210px;max-width:210px}
.vm-tool thead th.vm-sticky{z-index:8}
.vm-tool .vm-icon{width:24px;height:24px;vertical-align:middle;margin-right:6px;object-fit:contain}
.vm-tool .vm-sub{font-size:.8rem;font-weight:400;color:#42575e;margin-top:3px}
.vm-tool .vm-card{border:1px solid #cbd7db;border-radius:8px;background:#fff;padding:12px 15px;margin:.5rem 0}
.vm-tool .vm-card h3,.vm-tool .vm-card h4{font-size:1rem;margin:0 0 .4rem}
.vm-tool .vm-entry{white-space:pre-wrap;overflow-wrap:anywhere}
.vm-tool .vm-grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(min(100%,260px),1fr));gap:10px}
.vm-tool [hidden]{display:none!important}
.vm-tool .vm-zoom{margin-left:auto;display:flex;gap:.4rem;align-items:center}
.vm-tool .vm-scrollhint{font-size:.85rem;color:#485e65;margin:.35rem 0}
@media(max-width:640px){.vm-tool .vm-controls{display:grid;grid-template-columns:1fr 1fr}.vm-tool .vm-controls .vm-select-control,.vm-tool .vm-controls .vm-zoom{grid-column:1/-1}.vm-tool .vm-zoom{margin-left:0}.vm-tool th,.vm-tool td{min-width:130px}.vm-tool th.vm-sticky{min-width:165px;max-width:165px}}
@media print{.vm-tool .vm-controls{display:none}.vm-tool .vm-scroller{max-height:none;overflow:visible}.vm-tool table{font-size:10px}}
</style>

# Вечерня и утреня. Состав службы

[← Литургика](index.html) · [Знаки служб](service-signs.html) · [Исходная таблица](vespers-matins-scan.html) · [Разбор вопросов №1–6](practicum/materials/evening-matins-comparison-2026-11-22.html)

<div class="vm-tool" id="vm-digital"
 data-source="{{ '/assets/liturgics/vespers-matins-data.deflate.b64' | relative_url }}"
 data-icons="{{ '/assets/liturgics/service-signs/' | relative_url }}">
  <div class="vm-controls" role="group" aria-label="Способ просмотра">
    <button type="button" data-vm-view="full" aria-pressed="true">Вся таблица</button>
    <button type="button" data-vm-view="service" aria-pressed="false">Одна служба</button>
    <button type="button" data-vm-view="compare" aria-pressed="false">Сравнение</button>
    <label class="vm-select-control">Вид службы<select id="vm-service" aria-label="Выберите вид службы"></select></label>
    <label class="vm-select-control">Элемент последования<select id="vm-row" aria-label="Выберите элемент последования"></select></label>
    <div class="vm-zoom"><label for="vm-scale">Размер текста</label><select id="vm-scale"><option value="12">Мелкий</option><option value="14" selected>Обычный</option><option value="17">Крупный</option><option value="20">Очень крупный</option></select></div>
  </div>
  <div id="vm-status" class="vm-status" role="status" aria-live="polite">Загрузка таблицы…</div>
  <section id="vm-full"><p class="vm-scrollhint">Прокручивайте таблицу по горизонтали и вертикали.</p><div class="vm-scroller"><table id="vm-table"></table></div></section>
  <section id="vm-one" hidden></section>
  <section id="vm-compare" hidden></section>
</div>
<script src="{{ '/assets/liturgics/vespers-matins-digital.js' | relative_url }}" defer></script>

## Вопросы ФОС №1–6

[№1. Седмичная и субботняя службы](q01-l3.html) · [№2. Воскресное бдение](q02-l3.html) · [№3. Великие праздники](q03-l3.html) · [№4. Предпразднство и попразднство](q04-l3.html) · [№5. Великий пост](q05-l3.html) · [№6. Страстная и Светлая седмицы](q06-l3.html)
