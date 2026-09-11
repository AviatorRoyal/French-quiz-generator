# Conjugaison — French conjugation practice

A static quiz site for practising French verb conjugations. No build step, no
dependencies — it's plain HTML/CSS/JS and it runs straight off GitHub Pages.

All content lives in plain text files: quizzes in `quiz/`, verb tables in
`verbs/`. Adding material never means touching the code.

## Run it locally

```bash
python -m http.server 8000
```

Then open http://localhost:8000. (It must be served over HTTP — opening
`index.html` from disk won't work, because the browser blocks `fetch` on
`file://`.)

## Publish to GitHub Pages

1. Push this folder to a GitHub repo.
2. Repo **Settings → Pages → Source: Deploy from a branch**, branch `main`, folder `/ (root)`.
3. It goes live at `https://<user>.github.io/<repo>/` in a minute or so.

All paths are relative, so it works under a subpath without any config.

## Adding a quiz

Create `quiz/my-quiz.txt`, then add the filename to `quiz/index.txt`.

The format is blocks separated by a line containing only `---`, with
`key: value` lines inside. The first block describes the quiz; every block
after it is one question. Blank lines and lines starting with `#` are ignored.

```
id: french-present-er
subject: French
title: Présent — regular -er verbs
description: Conjugating first-group verbs in the present tense.
tags: présent, group 1
---
type: fill
prompt: Nous ___ (parler) français.
verb: parler
answer: parlons
alt: nous parlons
why: nous + -er verb → stem + -ons.
---
type: mcq
prompt: Tu ___ (manger) une pomme.
verb: manger
choices: mange | manges | mangez | mangeons
answer: manges
why: tu takes -es for -er verbs.
```

### Quiz header keys

| key | required | meaning |
|---|---|---|
| `id` | yes | URL-safe id; the quiz opens at `quiz.html?quiz=<id>` |
| `subject` | no | Shown on the card. Defaults to `General` |
| `title` | yes | Card heading |
| `description` | no | One line under the heading |
| `tags` | no | Comma- or pipe-separated. Also used to guess which tense to highlight in the hint table |

### Question keys

| key | required | meaning |
|---|---|---|
| `type` | no | `fill` (type the answer) or `mcq`. Defaults to `fill` |
| `prompt` | yes | The question text |
| `answer` | yes | The correct answer |
| `alt` | no | Other accepted answers, separated by `\|` or `,` |
| `choices` | mcq only | Options separated by `\|` |
| `verb` | no | Opens that verb's table from `verbs/` as the hint |
| `hint` | no | Inline hint text, for questions with no verb table |
| `why` | no | Explanation shown after answering |
| `tense` | no | Forces which tense the hint table highlights |

Grading ignores case, surrounding whitespace and trailing punctuation. Accents
are ignored too unless **Strict accents** is switched on in the quiz header.

## Adding a verb table

Create `verbs/<name>.txt`. The filename must be the accent-free, lowercase form
of the verb — `être` lives in `verbs/etre.txt` — because accented filenames
travel badly over the web. The `verb:` field inside keeps the real spelling.

```
verb: être
english: to be
group: irregular
auxiliary: avoir
participle present: étant
participle past: été
note: Optional footnote shown under the header.
---
tense: présent
je: suis
tu: es
il/elle/on: est
nous: sommes
vous: êtes
ils/elles: sont
---
tense: imparfait
je: étais
...
```

Person labels are free text and render in file order, so this works for any
language — or any subject where a reference table makes sense.

## Other subjects

Nothing here is French-specific. A question with a `hint:` line instead of a
`verb:` line shows that text as the hint — see `quiz/sample-other-subject.txt`.
Set `subject:` in the header and the card groups itself accordingly.

## Keyboard

| key | action |
|---|---|
| `1`–`9` | pick a multiple-choice option |
| `Enter` | submit a typed answer, then move to the next question |
| `H` | open the hint |
| `Esc` | close the hint |

## Layout

```
index.html        home — quiz picker
quiz.html         quiz runner
css/styles.css    design tokens, light + dark
js/parser.js      the text-file format
js/data.js        loading and caching
js/quiz.js        quiz engine and hint sheet
js/home.js        home page
js/theme.js       light/dark toggle
js/scores.js      best scores (localStorage)
quiz/             one .txt per quiz + index.txt
verbs/            one .txt per verb table
```
