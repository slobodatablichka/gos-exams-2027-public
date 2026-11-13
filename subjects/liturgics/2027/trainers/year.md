---
layout: default
title: Литургика — богослужебный год
---

# Богослужебный год — учебные случаи

[Каталог 61 тренажёра](index.html) · [Программа занятий №1–10](../practicum/index.html) · [Последовательная самопроверка](sequence.html) · [Все вопросы ФОС](../index.html)

Здесь представлены готовые учебные случаи **и типовые схемы по прямо указанным условиям**. Неуказанные год, день недели, храм и совпадения не нужны для решения. Это не автоматический календарь на 2027 год.

## Типовые схемы по богослужебному периоду

{% assign prefix = '/subjects/liturgics/2027/' %}
{% for question in site.data.liturgics_trainers_2027.questions %}
{% for game in question.cases %}
{% if game.year.group == 'cycle' %}
<p><strong>{{ game.year.date }} — {{ game.year.label }}</strong> (ФОС №{{ question.number }}) · <a href="{{ prefix | append: game.path | relative_url }}">Собрать последование</a><small> — {{ game.year.qualifier }}</small></p>
{% endif %}
{% endfor %}
{% endfor %}

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

Никакие другие обстоятельства не подставляются: проверяется только прямо указанное в упражнении. Все проверки — учебные, не официальное экзаменационное оценивание.
