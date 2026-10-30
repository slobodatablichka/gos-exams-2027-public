---
layout: default
title: "Докладчики по занятиям · группы 5, 6 и 7"
---

<link rel="stylesheet" href="assets/css/roleplan.css">

[Главная](index.html) › [Расписание и вопросы](schedule.html) › **Докладчики**

# План докладчиков первого круга

**23 занятия · 147 самостоятельных тем · 150 официальных номеров · группы от 5 до 7 студентов.**

Даты и темы одинаковы для всех групп. На каждую самостоятельную тему назначены **основной** и **второй** докладчики — разные участники. Дополнительные вопросы задают все остальные; отдельной нагрузкой они **не считаются**.

<div class="roleplan" id="roleplan" data-size="5">
  <div class="roleplan-toolbar">
    <label for="roleplan-size">Выберите группу или размер</label>
    <select id="roleplan-size">
      <option value="5a">Группа 1 · 5 студентов</option>
      <option value="5b">Группа 2 · 5 студентов</option>
      <option value="6">Группа из 6 студентов</option>
      <option value="7">Группа из 7 студентов</option>
    </select>
    <p class="roleplan-note" id="roleplan-note">Студенты 1–5 — условные номера первой пятёрки.</p>
    <label for="roleplan-jump">Перейти к занятию</label>
    <select id="roleplan-jump">
      <option value="">Выберите дату…</option>
      {% for day in site.data.meetings %}
      <option value="role-meeting-{{ day.meeting }}">№{{ day.meeting }} — {{ day.date }}, {{ day.start_time }}</option>
      {% endfor %}
    </select>
  </div>

  <p class="roleplan-help">Нажмите на занятие, чтобы развернуть вопросы и пары докладчиков. Полные официальные формулировки приведены в <a href="schedule.html">общем расписании</a>. Для готовых занятий доступны ссылки на учебные материалы. Если формулировка встречается под другим номером, это указано при объявлении темы.</p>

  {% for day in site.data.meetings %}
  {% assign session_published = site.data.published_sessions | where: "session", day.meeting | first %}
  {% assign session_path = day.meeting | prepend: "0" | slice: -2, 2 %}
  <details class="roleplan-meeting" id="role-meeting-{{ day.meeting }}" {% if forloop.first %}open{% endif %}>
    <summary>
      <strong>Занятие №{{ day.meeting }}</strong>
      <span>{{ day.date }} · {{ day.weekday }} · {{ day.start_time }}</span>
    </summary>
    <div class="roleplan-meeting-body">
      {% for size in (5..7) %}
      {% capture data_name %}roles_{{ size }}{% endcapture %}
      {% assign assignments = site.data[data_name] | where: "meeting", day.meeting %}
      <table class="roleplan-table" data-role-size="{{ size }}">
        <thead><tr><th>Вопрос</th><th>Основной</th><th>Второй</th></tr></thead>
        <tbody>
          {% for item in assignments %}
          <tr>
            <td>
            {% assign number_padded = item.question | prepend: "0" | slice: -2, 2 %}
            {% capture display_numbers %}{{ item.question }}{% if item.aliases != "" %}/{{ item.aliases }}{% endif %}{% endcapture %}
            {% if session_published %}
              <a href="sessions/{{ session_path }}/q{{ number_padded }}-l3.html">{{ item.subject }} №{{ display_numbers }}</a>
            {% else %}
              {{ item.subject }} №{{ display_numbers }}
            {% endif %}
            {% if item.aliases != "" %}<small class="roleplan-alias">Такая же официальная формулировка также под №{{ item.aliases }} — один доклад</small>{% endif %}
            </td>
            <td><span class="roleplan-person" data-slot="{{ item.primary }}">Студент {{ item.primary }}</span></td>
            <td><span class="roleplan-person" data-slot="{{ item.second }}">Студент {{ item.second }}</span></td>
          </tr>
          {% endfor %}
        </tbody>
      </table>
      {% endfor %}
      <p class="roleplan-meeting-links"><a href="schedule.html">Полные формулировки вопросов</a>{% if session_published %} · <a href="sessions/{{ session_path }}/index.html">Материалы занятия №{{ day.meeting }} (L3/L2/L1)</a>{% endif %}</p>
    </div>
  </details>
  {% endfor %}
</div>

## Как пользоваться планом

1. Выберите вверху свою группу. Сейчас у нас **две пятёрки**; варианты для шести и семи предназначены для дальнейшего комплектования.
2. Найдите дату и откройте занятие. **Обе группы проходят одинаковые самостоятельные темы**, которые назначены на этот день.
3. Если формулировка повторяется, объявляем оба официальных номера (например, ВЗ №5/14), но тему проходим один раз. Рядом с каждой темой стоят два докладчика: **основной** готовит полный ответ, **второй** независимо готовится по той же теме, дополняет и поправляет.
4. Другие участники заранее читают материалы и могут задавать дополнительные вопросы. Их **не назначаем отдельно** и не учитываем как докладную нагрузку.
5. Обозначения «Студент 1» и далее здесь — **плановые номера**, не фамилии. Для двух нынешних пятёрок предварительно показаны номера **1–5** и **6–10**; их нужно сопоставить с реальным составом групп. Если состав меняется, выбираем вариант 5/6/7 и уточняем соответствие номеров.
6. Ведущий выбирается и меняется внутри каждой группы; его назначение не является дополнительным докладом. Наставников нет.

**Что не меняется:** все 23 даты и 150 официальных номеров. Самостоятельных тем 147: ВЗ №5/14, ДБ №1/7 и ДБ №6/16 объединены. На каждую тему — одна пара докладчиков, нагрузка пересчитана для 5/6/7.

<script src="assets/js/roleplan.js" defer></script>
