---
layout: default
title: Литургика — богослужебный год
---

# Богослужебный год — учебные случаи

[Экзаменационные игры №1–15](index.html) · [Последовательная тренировка](sequence.html)

Здесь представлены **только уже подготовленные учебные случаи** с определённым праздником или местом в богослужебном круге. Они не являются автоматическим календарём на 2027 год: день недели, год, храм и совпадения сохраняются именно такими, как в источниковом примере.

## Неподвижный круг

{% assign prefix = '/subjects/liturgics/2027/' %}
{% for question in site.data.liturgics_trainers_2027.questions %}
{% for game in question.cases %}
{% if game.year.group == 'fixed' %}
<p><strong>{{ game.year.date }} — {{ game.year.label }}</strong> (ФОС №{{ question.number }}) · <a href="{{ prefix | append: game.path | relative_url }}">Собрать последование</a><small> — {{ game.year.qualifier }}</small></p>
{% endif %}
{% endfor %}
{% endfor %}

## Подвижный круг

{% for question in site.data.liturgics_trainers_2027.questions %}
{% for game in question.cases %}
{% if game.year.group == 'movable' %}
<p><strong>{{ game.year.date }} — {{ game.year.label }}</strong> (ФОС №{{ question.number }}) · <a href="{{ prefix | append: game.path | relative_url }}">Собрать последование</a><small> — {{ game.year.qualifier }}</small></p>
{% endif %}
{% endfor %}
{% endfor %}

Для других дат и сочетаний упражнение ещё не подготовлено. Вопросы №1 и №9 пока остаются только учебными схемами без полностью определённого календарного случая. Все проверки — в режиме самопроверки, не официального оценивания.
