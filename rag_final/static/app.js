"use strict";

const form = document.querySelector("#question-form");
const questionInput = document.querySelector("#question");
const submitButton = document.querySelector("#submit-button");
const conversation = document.querySelector("#conversation");
const suggestions = document.querySelectorAll(".suggestion");

function scrollToLatest() {
  conversation.scrollTop = conversation.scrollHeight;
}

function addUserMessage(text) {
  const message = document.createElement("article");
  message.className = "message user-message";
  const content = document.createElement("div");
  content.className = "message-content";
  content.textContent = text;
  message.appendChild(content);
  conversation.appendChild(message);
}

function createAssistantMessage(extraClass = "") {
  const message = document.createElement("article");
  message.className = `message assistant-message ${extraClass}`.trim();
  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.setAttribute("aria-hidden", "true");
  avatar.textContent = "AI";
  const content = document.createElement("div");
  content.className = "message-content";
  const author = document.createElement("p");
  author.className = "message-author";
  author.textContent = "Asistente RAG";
  content.appendChild(author);
  message.appendChild(avatar);
  message.appendChild(content);
  conversation.appendChild(message);
  return { message, content };
}

function addLoadingMessage() {
  const elements = createAssistantMessage("loading-message");
  const status = document.createElement("div");
  status.className = "answer-text";
  const spinner = document.createElement("span");
  spinner.className = "spinner";
  spinner.setAttribute("aria-hidden", "true");
  const label = document.createElement("span");
  label.textContent = "Consultando...";
  status.appendChild(spinner);
  status.appendChild(label);
  elements.content.appendChild(status);
  scrollToLatest();
  return elements.message;
}

function appendSources(container, sources) {
  const details = document.createElement("details");
  details.className = "sources";
  const summary = document.createElement("summary");
  summary.textContent = `Fuentes recuperadas (${sources.length})`;
  details.appendChild(summary);
  const list = document.createElement("div");
  list.className = "source-list";

  sources.forEach((source) => {
    const card = document.createElement("article");
    card.className = "source-card";
    const title = document.createElement("p");
    title.className = "source-title";
    title.textContent = `${source.rank}. ${source.source}`;
    card.appendChild(title);
    const meta = document.createElement("p");
    meta.className = "source-meta";
    const values = [
      `Chunk ${source.chunk_id}`,
      source.structure,
      `RRF ${Number(source.rrf_score).toFixed(6)}`,
      `Reranker ${Number(source.reranker_score).toFixed(6)}`,
    ];
    values.forEach((value) => {
      const item = document.createElement("span");
      item.textContent = value;
      meta.appendChild(item);
    });
    card.appendChild(meta);
    list.appendChild(card);
  });
  details.appendChild(list);
  container.appendChild(details);
}

function appendInlineFormatting(container, text) {
  const inlinePattern = /(\*\*[^*\r\n]+\*\*|\*[^*\r\n]+\*)/g;
  let cursor = 0;
  let match;

  while ((match = inlinePattern.exec(text)) !== null) {
    const token = match[0];
    const tokenEnd = match.index + token.length;
    const touchesAnotherAsterisk =
      text[match.index - 1] === "*" || text[tokenEnd] === "*";

    if (touchesAnotherAsterisk) {
      container.appendChild(document.createTextNode(text.slice(cursor, tokenEnd)));
      cursor = tokenEnd;
      continue;
    }

    if (match.index > cursor) {
      container.appendChild(
        document.createTextNode(text.slice(cursor, match.index)),
      );
    }

    const isStrong = token.startsWith("**");
    const element = document.createElement(isStrong ? "strong" : "em");
    element.textContent = isStrong ? token.slice(2, -2) : token.slice(1, -1);
    container.appendChild(element);
    cursor = tokenEnd;
  }

  if (cursor < text.length) {
    container.appendChild(document.createTextNode(text.slice(cursor)));
  }
}

function appendSafeMarkdown(container, markdown) {
  const lines = markdown.split(/\r?\n/);
  let currentList = null;

  lines.forEach((line) => {
    const normalizedLine = line.trim();
    if (!normalizedLine) {
      currentList = null;
      return;
    }

    const headingMatch = normalizedLine.match(/^(#{1,3})\s+(.+)$/);
    if (headingMatch) {
      currentList = null;
      const headingLevel = headingMatch[1].length;
      const headingTags = { 1: "h3", 2: "h4", 3: "h5" };
      const heading = document.createElement(headingTags[headingLevel]);
      heading.className = `answer-heading answer-heading-${headingLevel}`;
      appendInlineFormatting(heading, headingMatch[2]);
      container.appendChild(heading);
      return;
    }

    const listMatch = normalizedLine.match(/^[-*]\s+(.+)$/);
    if (listMatch) {
      if (!currentList) {
        currentList = document.createElement("ul");
        currentList.className = "answer-list";
        container.appendChild(currentList);
      }
      const item = document.createElement("li");
      appendInlineFormatting(item, listMatch[1]);
      currentList.appendChild(item);
      return;
    }

    currentList = null;
    const paragraph = document.createElement("p");
    paragraph.className = "answer-paragraph";
    appendInlineFormatting(paragraph, normalizedLine);
    container.appendChild(paragraph);
  });
}

function addAnswer(data) {
  const { content } = createAssistantMessage();
  const answer = document.createElement("div");
  answer.className = "answer-text rich-answer";
  appendSafeMarkdown(answer, data.answer);
  content.appendChild(answer);
  const badge = document.createElement("span");
  badge.className = "mode-badge";
  if (data.mode === "structured") {
    badge.classList.add("structured");
    badge.textContent = "Respuesta estructurada";
  } else {
    badge.textContent = "Respuesta grounded con Claude";
  }
  content.appendChild(badge);
  appendSources(content, Array.isArray(data.sources) ? data.sources : []);
  scrollToLatest();
}

function addError(text) {
  const { content } = createAssistantMessage("error-message");
  const error = document.createElement("p");
  error.className = "answer-text";
  error.textContent = text;
  content.appendChild(error);
  scrollToLatest();
}

function setBusy(isBusy) {
  submitButton.disabled = isBusy;
  questionInput.disabled = isBusy;
  suggestions.forEach((button) => { button.disabled = isBusy; });
}

function assertAnswerShape(data) {
  if (!data || typeof data.answer !== "string" || typeof data.mode !== "string") {
    throw new Error("Respuesta inesperada del servidor.");
  }
}

async function submitQuestion(question) {
  const cleanedQuestion = question.trim();
  if (!cleanedQuestion || submitButton.disabled) return;
  addUserMessage(cleanedQuestion);
  questionInput.value = "";
  questionInput.style.height = "auto";
  setBusy(true);
  const loading = addLoadingMessage();

  try {
    const response = await fetch("/api/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: cleanedQuestion }),
    });
    const data = await response.json().catch(() => ({}));
    loading.remove();
    if (!response.ok) {
      addError(data.error || "No se pudo completar la consulta.");
      return;
    }
    assertAnswerShape(data);
    addAnswer(data);
  } catch (error) {
    loading.remove();
    addError(error.message || "No fue posible conectar con el servidor local.");
  } finally {
    setBusy(false);
    questionInput.focus();
  }
}

function resizeInput() {
  questionInput.style.height = "auto";
  questionInput.style.height = `${Math.min(questionInput.scrollHeight, 130)}px`;
}

form.addEventListener("submit", (event) => {
  event.preventDefault();
  submitQuestion(questionInput.value);
});

questionInput.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    form.requestSubmit();
  }
});

questionInput.addEventListener("input", resizeInput);
suggestions.forEach((button) => {
  button.addEventListener("click", () => submitQuestion(button.textContent));
});
