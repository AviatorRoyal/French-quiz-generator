// Theme: explicit choice wins, otherwise follow the system.
const KEY = 'fc-theme';

function apply(theme) {
  if (theme === 'light' || theme === 'dark') {
    document.documentElement.dataset.theme = theme;
  } else {
    delete document.documentElement.dataset.theme;
  }
}

function stored() {
  try {
    return localStorage.getItem(KEY);
  } catch {
    return null;
  }
}

function current() {
  const saved = stored();
  if (saved) return saved;
  return matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light';
}

export function initTheme() {
  apply(stored());

  const button = document.querySelector('[data-theme-toggle]');
  if (!button) return;

  const sync = () => {
    const dark = current() === 'dark';
    button.setAttribute('aria-label', dark ? 'Switch to light mode' : 'Switch to dark mode');
    button.textContent = dark ? '☀' : '☾';
  };

  button.addEventListener('click', () => {
    const next = current() === 'dark' ? 'light' : 'dark';
    try {
      localStorage.setItem(KEY, next);
    } catch { /* private mode — theme just won't stick */ }
    apply(next);
    sync();
  });

  matchMedia('(prefers-color-scheme: dark)').addEventListener('change', sync);
  sync();
}
