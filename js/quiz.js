import { loadQuizById, loadVerb } from './data.js';
import { initTheme } from './theme.js';
import { recordScore } from './scores.js';

initTheme();

const root = document.getElementById('quiz-root');
const sheet = document.getElementById('hint-sheet');
const sheetBody = document.getElementById('hint-body');
const sheetTitle = document.getElementById('hint-title');

const STRICT_KEY = 'fc-strict-accents';
let strictAccents = localStorage.getItem(STRICT_KEY) === '1';

const state = { quiz: null, questions: [], index: 0, results: [], answered: false };

// Fisher-Yates, in place.
function shuffle(items) {
  for (let i = items.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [items[i], items[j]] = [items[j], items[i]];
  }
  return items;
}

// A fresh draw from the bank, with the options in a fresh order too.
function drawQuestions(quiz) {
  const drawn = shuffle([...quiz.questions]);
  return (quiz.pick ? drawn.slice(0, quiz.pick) : drawn).map((question) =>
    question.choices.length ? { ...question, choices: shuffle([...question.choices]) } : question
  );
}

/* ---------- answer checking ---------- */

const stripAccents = (s) => s.normalize('NFD').replace(/[̀-ͯ]/g, '');

function normalise(value) {
  let out = value.trim().toLowerCase().replace(/\s+/g, ' ').replace(/[.!?]+$/, '');
  if (!strictAccents) out = stripAccents(out);
  return out;
}

const isCorrect = (given, accepted) =>
  accepted.some((option) => normalise(option) === normalise(given));

/* ---------- hint sheet ---------- */

// Which person is the question about? Used to highlight the right row.
const PRONOUNS = [
  [/\bnous\b/i, ['nous']],
  [/\bvous\b/i, ['vous']],
  [/\bils\b|\belles\b/i, ['ils', 'elles']],
  [/\bje\b|\bj'/i, ['je', "j'"]],
  [/\btu\b/i, ['tu']],
  [/\bil\b|\belle\b|\bon\b/i, ['il', 'elle', 'on']],
];

function personFor(prompt) {
  for (const [pattern, keys] of PRONOUNS) {
    if (pattern.test(prompt)) return keys;
  }
  return null;
}

const rowMatches = (label, keys) => {
  if (!keys) return false;
  const parts = label.toLowerCase().split(/[/\s]+/).filter(Boolean);
  return parts.some((part) => keys.includes(part));
};

function tenseFor(question) {
  if (question.tense) return stripAccents(question.tense.toLowerCase());
  const tags = state.quiz.tags.map((t) => stripAccents(t.toLowerCase()));
  const known = ['present', 'imparfait', 'futur', 'passe compose', 'conditionnel', 'subjonctif'];
  return tags.find((tag) => known.some((t) => tag.includes(t))) || null;
}

function renderVerbTable(verb, question) {
  const person = personFor(question.prompt);
  const wantedTense = tenseFor(question);

  const meta = [verb.english, verb.group, verb.auxiliary && `aux. ${verb.auxiliary}`]
    .filter(Boolean)
    .map((bit) => `<span>${bit}</span>`)
    .join('');

  const participles = verb.participles.length
    ? `<p class="participles">${verb.participles
        .map(([kind, form]) => `<span><em>${kind}</em> ${form}</span>`)
        .join('')}</p>`
    : '';

  const tables = verb.tenses
    .map((tense) => {
      // With a single tense there is nothing to pick out, so skip the flourish.
      const highlight =
        verb.tenses.length > 1 &&
        wantedTense &&
        stripAccents(tense.name.toLowerCase()).includes(wantedTense);
      const rows = tense.rows
        .map(
          ([label, form]) =>
            `<tr class="${rowMatches(label, person) ? 'row-hit' : ''}"><th>${label}</th><td>${form}</td></tr>`
        )
        .join('');
      return `<section class="tense ${highlight ? 'tense-hit' : ''}">
                <h3>${tense.name}${highlight ? '<span class="pill">this question</span>' : ''}</h3>
                <table>${rows}</table>
              </section>`;
    })
    .join('');

  return `<div class="verb-head"><h4>${verb.verb}</h4><div class="verb-meta">${meta}</div></div>
          ${participles}
          ${verb.note ? `<p class="note">${verb.note}</p>` : ''}
          <div class="tense-grid">${tables}</div>`;
}

async function openHint() {
  const question = state.questions[state.index];
  state.results[state.index] = { ...(state.results[state.index] || {}), hinted: true };
  root.querySelector('[data-hint-flag]')?.removeAttribute('hidden');

  sheet.hidden = false;
  document.body.classList.add('sheet-open');
  sheetTitle.textContent = 'Hint';
  sheetBody.innerHTML = '<p class="muted">Loading…</p>';

  if (question.verb) {
    const verb = await loadVerb(question.verb);
    sheetTitle.textContent = verb ? verb.verb : question.verb;
    sheetBody.innerHTML = verb
      ? renderVerbTable(verb, question)
      : `<p class="error">No table found for &ldquo;${question.verb}&rdquo;. Expected a file in <code>verbs/</code>.</p>`;
  } else if (question.hint) {
    sheetBody.innerHTML = `<p class="hint-text">${question.hint}</p>`;
  } else {
    sheetBody.innerHTML = '<p class="muted">No hint available for this question.</p>';
  }

  sheet.querySelector('[data-close-hint]').focus();
}

function closeHint() {
  sheet.hidden = true;
  document.body.classList.remove('sheet-open');
  root.querySelector('[data-answer-input]')?.focus();
}

sheet.addEventListener('click', (e) => {
  if (e.target.closest('[data-close-hint]')) closeHint();
});

/* ---------- question rendering ---------- */

function renderQuestion() {
  const question = state.questions[state.index];
  const hinted = state.results[state.index]?.hinted;
  state.answered = false;

  const progress = (state.index / state.questions.length) * 100;

  const body =
    question.type === 'mcq'
      ? `<div class="choices" role="group">
           ${question.choices
             .map(
               (choice, i) =>
                 `<button class="choice" type="button" data-choice="${i}">
                    <span class="choice-key">${i + 1}</span><span class="choice-text">${choice}</span>
                  </button>`
             )
             .join('')}
         </div>`
      : `<form class="answer-form" autocomplete="off">
           <input class="answer-input" data-answer-input type="text"
                  placeholder="Type your answer" aria-label="Your answer" spellcheck="false">
           <button class="button" type="submit">Check</button>
         </form>`;

  root.innerHTML = `
    <div class="quiz-head">
      <div>
        <p class="eyebrow">${state.quiz.subject} · ${state.quiz.title}</p>
        <p class="counter">Question ${state.index + 1} of ${state.questions.length}</p>
      </div>
      <label class="switch" title="Require correct accents (é, è, ê…)">
        <input type="checkbox" data-strict ${strictAccents ? 'checked' : ''}>
        <span>Strict accents</span>
      </label>
    </div>
    <div class="progress"><div class="progress-bar" style="width:${progress}%"></div></div>

    <article class="question-card">
      <p class="prompt">${question.prompt}</p>
      ${body}
      <div class="question-foot">
        <button class="button ghost" type="button" data-hint>Hint <kbd>H</kbd></button>
        <span class="hint-flag" data-hint-flag ${hinted ? '' : 'hidden'}>hint used</span>
      </div>
      <div class="feedback" data-feedback hidden></div>
    </article>`;

  root.removeAttribute('aria-busy');

  root.querySelector('[data-strict]').addEventListener('change', (e) => {
    strictAccents = e.target.checked;
    try {
      localStorage.setItem(STRICT_KEY, strictAccents ? '1' : '0');
    } catch { /* private mode */ }
  });
  root.querySelector('[data-hint]').addEventListener('click', openHint);

  if (question.type === 'mcq') {
    root.querySelectorAll('[data-choice]').forEach((button) => {
      button.addEventListener('click', () =>
        submit(question.choices[Number(button.dataset.choice)], button)
      );
    });
  } else {
    const form = root.querySelector('.answer-form');
    const send = () => {
      const input = form.querySelector('input');
      if (input.value.trim()) submit(input.value);
    };
    form.addEventListener('submit', (e) => {
      e.preventDefault();
      send();
    });
    // Some browsers don't fire implicit submission on Enter in a one-field form.
    form.querySelector('input').addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        e.preventDefault();
        send();
      }
    });
    root.querySelector('[data-answer-input]').focus();
  }
}

function submit(given, button) {
  if (state.answered) return;
  state.answered = true;

  const question = state.questions[state.index];
  const correct = isCorrect(given, question.accepted);
  state.results[state.index] = {
    ...(state.results[state.index] || {}),
    given,
    correct,
    question,
  };

  root.querySelectorAll('.choice').forEach((el, i) => {
    el.disabled = true;
    if (question.choices[i] === question.answer) el.classList.add('is-answer');
  });
  if (button && !correct) button.classList.add('is-wrong');
  root.querySelector('.answer-input')?.setAttribute('disabled', '');
  root.querySelector('.answer-form .button')?.setAttribute('disabled', '');

  const last = state.index + 1 === state.questions.length;
  const feedback = root.querySelector('[data-feedback]');
  feedback.hidden = false;
  feedback.className = `feedback ${correct ? 'is-correct' : 'is-wrong'}`;
  feedback.innerHTML = `
    <p class="verdict">${correct ? '✓ Correct' : `✗ Answer: <strong>${question.answer}</strong>`}</p>
    ${question.why ? `<p class="why">${question.why}</p>` : ''}
    <button class="button" type="button" data-next>${last ? 'See results' : 'Next'} <kbd>↵</kbd></button>`;

  const nextButton = feedback.querySelector('[data-next]');
  nextButton.addEventListener('click', next);
  nextButton.focus();
}

function next() {
  if (state.index + 1 === state.questions.length) {
    renderResults();
  } else {
    state.index += 1;
    renderQuestion();
  }
}

/* ---------- results ---------- */

function renderResults() {
  const total = state.questions.length;
  const correct = state.results.filter((r) => r?.correct).length;
  const hinted = state.results.filter((r) => r?.hinted).length;
  recordScore(state.quiz.id, correct, total);

  const review = state.results
    .map((result, i) => {
      const q = result.question;
      return `<li class="${result.correct ? 'ok' : 'bad'}">
        <p class="review-prompt">${i + 1}. ${q.prompt}</p>
        <p class="review-answer">
          You said <strong>${result.given || '—'}</strong>
          ${result.correct ? '' : ` · correct: <strong>${q.answer}</strong>`}
          ${result.hinted ? '<span class="hint-flag">hint used</span>' : ''}
        </p>
      </li>`;
    })
    .join('');

  root.innerHTML = `
    <div class="progress"><div class="progress-bar" style="width:100%"></div></div>
    <section class="results">
      <p class="eyebrow">${state.quiz.title}</p>
      <p class="score-big">${correct}<span>/${total}</span></p>
      <p class="muted">${Math.round((correct / total) * 100)}% · ${hinted} question${hinted === 1 ? '' : 's'} with a hint</p>
      <div class="results-actions">
        <button class="button" type="button" data-retry>Try again</button>
        <a class="button ghost" href="index.html">All quizzes</a>
      </div>
      <h2 class="review-head">Review</h2>
      <ol class="review">${review}</ol>
    </section>`;

  // A new attempt draws a new set of questions from the bank.
  root.querySelector('[data-retry]').addEventListener('click', () => {
    state.questions = drawQuestions(state.quiz);
    state.index = 0;
    state.results = [];
    renderQuestion();
  });
}

/* ---------- keyboard ---------- */

document.addEventListener('keydown', (e) => {
  if (!sheet.hidden) {
    if (e.key === 'Escape') closeHint();
    return;
  }
  const typing = e.target instanceof Element && e.target.matches('input[type="text"]');

  if ((e.key === 'h' || e.key === 'H') && !typing && root.querySelector('[data-hint]')) {
    e.preventDefault();
    openHint();
  } else if (e.key === 'Enter' && state.answered) {
    e.preventDefault();
    next();
  } else if (!typing && /^[1-9]$/.test(e.key)) {
    root.querySelector(`[data-choice="${Number(e.key) - 1}"]`)?.click();
  }
});

/* ---------- boot ---------- */

const id = new URLSearchParams(location.search).get('quiz');

loadQuizById(id)
  .then((quiz) => {
    if (!quiz) {
      root.removeAttribute('aria-busy');
      root.innerHTML = `<p class="error">Quiz not found.</p>
                        <p><a class="button ghost" href="index.html">Back to all quizzes</a></p>`;
      return;
    }
    state.quiz = quiz;
    state.questions = drawQuestions(quiz);
    document.title = `${quiz.title} — Conjugaison`;
    renderQuestion();
  })
  .catch((err) => {
    root.removeAttribute('aria-busy');
    root.innerHTML = `<p class="error">${err.message}</p>`;
  });
