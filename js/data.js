import { parseQuiz, parseVerb, slug } from './parser.js';

async function fetchText(path) {
  const res = await fetch(path, { cache: 'no-cache' });
  if (!res.ok) throw new Error(`Could not load ${path} (${res.status})`);
  return res.text();
}

export async function loadQuizList() {
  const index = await fetchText('quiz/index.txt');
  const files = index
    .split(/\r?\n/)
    .map((line) => line.trim())
    .filter((line) => line && !line.startsWith('#'));

  const quizzes = await Promise.all(
    files.map(async (file) => {
      try {
        return parseQuiz(await fetchText(`quiz/${file}`), file);
      } catch (err) {
        console.error(err);
        return null;
      }
    })
  );
  return quizzes.filter(Boolean);
}

export async function loadQuizById(id) {
  const quizzes = await loadQuizList();
  return quizzes.find((quiz) => quiz.id === id) || null;
}

const verbCache = new Map();

export async function loadVerb(name) {
  const key = slug(name);
  if (!verbCache.has(key)) {
    verbCache.set(
      key,
      fetchText(`verbs/${key}.txt`)
        .then((text) => parseVerb(text, name))
        .catch((err) => {
          console.error(err);
          return null;
        })
    );
  }
  return verbCache.get(key);
}
