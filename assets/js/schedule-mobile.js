(() => {
  "use strict";

  const root = document.querySelector(".main-content");
  if (!root) return;

  const headings = [...root.querySelectorAll("h2")]
    .filter((h) => /^Занятие\s+\d+\s*[—–-]/.test(h.textContent.trim()));

  const meetings = [];
  let totalQuestions = 0;

  for (const heading of headings) {
    const matched = heading.textContent.trim().match(/^Занятие\s+(\d+)\s*[—–-]\s*(.+)$/);
    if (!matched) return;

    const originalNodes = [heading];
    let cursor = heading.nextElementSibling;
    let table = null;
    let detailsText = "";

    while (cursor && originalNodes.length < 7 && cursor.tagName !== "H2") {
      originalNodes.push(cursor);
      if (cursor.tagName === "P") detailsText += cursor.textContent.trim() + " ";
      if (cursor.tagName === "TABLE") {
        table = cursor;
        break;
      }
      cursor = cursor.nextElementSibling;
    }
    if (!table) return;

    const rows = [...table.querySelectorAll("tbody tr")];
    const questions = [];
    for (const tr of rows) {
      const cells = [...tr.querySelectorAll("td")];
      if (cells.length !== 5) return;
      const fullLabel = cells[0].textContent.trim();
      const sep = fullLabel.lastIndexOf(", № ");
      const subject = sep === -1 ? fullLabel : fullLabel.slice(0, sep);
      const number = sep === -1 ? "" : fullLabel.slice(sep + 4);
      const originalLink = cells[0].querySelector("a[href]");
      questions.push({
        subject, number,
        question: cells[1].textContent.trim(),
        primary: cells[2].textContent.trim(),
        secondary: cells[3].textContent.trim(),
        others: cells[4].textContent.trim(),
        href: originalLink ? originalLink.getAttribute("href") : null
      });
    }
    totalQuestions += questions.length;
    meetings.push({
      number: matched[1], date: matched[2], detailsText,
      questions, originalNodes
    });
  }

  // Do not hide any original content unless the complete schedule was parsed.
  if (meetings.length !== 23 || totalQuestions !== 150) return;

  const make = (tag, className, value) => {
    const el = document.createElement(tag);
    if (className) el.className = className;
    if (value !== undefined) el.textContent = value;
    return el;
  };
  const label = (value) => {
    if (value.includes("Нового Завета")) return "Новый Завет";
    if (value.includes("Ветхого Завета")) return "Ветхий Завет";
    if (value.includes("Русской Православной Церкви")) return "История РПЦ";
    if (value.includes("Общецерковная")) return "Общецерковная история";
    if (value.includes("Догматическое")) return "Догматика";
    return value;
  };

  const mobile = make("section", "mobile-schedule", undefined);
  mobile.id = "mobile-schedule-top";
  mobile.setAttribute("aria-label", "Мобильное расписание первого круга");
  mobile.append(make("p", "mobile-schedule-help", "Выберите занятие, чтобы увидеть вопросы и распределение докладов."));

  const jumpWrap = make("div", "mobile-schedule-jump");
  const jumpLabel = make("label", "", "Быстрый переход к занятию");
  jumpLabel.htmlFor = "mobile-schedule-select";
  const jump = make("select", "");
  jump.id = "mobile-schedule-select";
  jump.append(new Option("Выберите занятие…", ""));
  jumpWrap.append(jumpLabel, jump);
  mobile.append(jumpWrap);

  const disclosures = [];
  for (const meeting of meetings) {
    const box = make("details", "mobile-schedule-meeting");
    box.id = "meeting-" + meeting.number;
    const summary = make("summary", "mobile-schedule-summary");
    summary.append(make("strong", "", "Занятие №" + meeting.number));
    summary.append(make("span", "mobile-schedule-date", meeting.date));
    const subjects = [...new Set(meeting.questions.map((q) => label(q.subject)))];
    summary.append(make("span", "mobile-schedule-subjects",
      subjects.join(" · ") + " · " + meeting.questions.length + " вопросов"));
    box.append(summary);

    const body = make("div", "mobile-schedule-body");
    body.append(make("p", "mobile-schedule-leader", meeting.detailsText.trim()));
    for (const q of meeting.questions) {
      const card = make("article", "mobile-schedule-card");
      card.append(make("p", "mobile-schedule-question-label",
        q.subject + (q.number ? ", № " + q.number : "")));
      card.append(make("p", "mobile-schedule-question-text", q.question));
      const grid = make("dl", "mobile-schedule-roles");
      for (const item of [
        ["Основной докладчик", q.primary],
        ["Второй докладчик", q.secondary],
        ["Дополнительные вопросы", q.others]
      ]) {
        const cell = make("div", "mobile-schedule-role");
        cell.append(make("dt", "", item[0]), make("dd", "", item[1]));
        grid.append(cell);
      }
      card.append(grid);
      if (q.href) {
        const a = make("a", "mobile-schedule-materials", "Открыть материал L3");
        a.href = q.href;
        card.append(a);
      }
      body.append(card);
    }

    const collapse = make("button", "mobile-schedule-collapse", "Свернуть занятие ↑");
    collapse.type = "button";
    collapse.addEventListener("click", () => {
      box.open = false;
      box.scrollIntoView({ block: "start" });
    });
    body.append(collapse);
    box.append(body);
    mobile.append(box);
    disclosures.push(box);

    const opt = make("option", "", "№" + meeting.number + " — " + meeting.date);
    opt.value = meeting.number;
    jump.append(opt);
  }

  jump.addEventListener("change", () => {
    const selected = disclosures.find((el) => el.id === "meeting-" + jump.value);
    if (!selected) return;
    for (const box of disclosures) box.open = box === selected;
    selected.scrollIntoView({ block: "start" });
  });

  headings[0].before(mobile);
  for (const meeting of meetings)
    for (const node of meeting.originalNodes)
      node.classList.add("schedule-desktop-only");

  mobile.classList.add("is-ready");

  const hash = window.location.hash.match(/^#meeting-(\d+)$/);
  if (hash) {
    const target = disclosures.find((el) => el.id === "meeting-" + hash[1]);
    if (target) target.open = true;
  }
})();