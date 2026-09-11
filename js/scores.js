// Best score per quiz, kept in this browser only.
const KEY = 'fc-scores';

function read() {
  try {
    return JSON.parse(localStorage.getItem(KEY)) || {};
  } catch {
    return {};
  }
}

export function bestScore(id) {
  const entry = read()[id];
  return entry && typeof entry.correct === 'number' ? entry : null;
}

export function recordScore(id, correct, total) {
  const all = read();
  const previous = all[id];
  if (!previous || correct / total > previous.correct / previous.total) {
    all[id] = { correct, total, at: Date.now() };
    try {
      localStorage.setItem(KEY, JSON.stringify(all));
    } catch { /* nothing to do */ }
  }
}
