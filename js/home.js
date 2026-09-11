import { loadQuizList } from './data.js';
import { initTheme } from './theme.js';
import { bestScore } from './scores.js';

initTheme();

const list = document.getElementById('quiz-list');

function card(quiz) {
  const best = bestScore(quiz.id);
  const el = document.createElement('a');
  el.className = 'card';
  el.href = `quiz.html?quiz=${encodeURIComponent(quiz.id)}`;

  const tags = quiz.tags.map((t) => `<span class="tag">${t}</span>`).join('');
  const count = quiz.pick
    ? `${quiz.pick} of ${quiz.questions.length}, at random`
    : `${quiz.questions.length} question${quiz.questions.length === 1 ? '' : 's'}`;
  const score = best
    ? `<span class="score">Best ${best.correct}/${best.total}</span>`
    : '<span class="score muted">Not attempted</span>';

  el.innerHTML = `
    <span class="card-subject">${quiz.subject}</span>
    <h2 class="card-title">${quiz.title}</h2>
    <p class="card-desc">${quiz.description}</p>
    <div class="card-tags">${tags}</div>
    <div class="card-foot">
      <span class="muted">${count}</span>
      ${score}
    </div>`;
  return el;
}

loadQuizList()
  .then((quizzes) => {
    list.removeAttribute('aria-busy');
    list.innerHTML = '';
    if (quizzes.length === 0) {
      list.innerHTML = '<p class="muted">No quizzes found. Check <code>quiz/index.txt</code>.</p>';
      return;
    }
    for (const quiz of quizzes) list.append(card(quiz));
  })
  .catch((err) => {
    list.removeAttribute('aria-busy');
    list.innerHTML = `<p class="error">${err.message}</p>`;
  });
