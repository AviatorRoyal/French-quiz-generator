// Parsers for the plain-text data files in quiz/ and verbs/.
//
// Both formats are the same shape: blocks separated by a line containing
// only "---", and inside each block "key: value" lines. Lines starting
// with "#" and blank lines are ignored. The first block is the header.

function parseBlocks(text) {
  return text
    .replace(/\r\n/g, '\n')
    .split(/^---[ \t]*$/m)
    .map((block) => {
      const fields = [];
      for (const line of block.split('\n')) {
        const trimmed = line.trim();
        if (!trimmed || trimmed.startsWith('#')) continue;
        const sep = trimmed.indexOf(':');
        if (sep === -1) continue;
        fields.push([trimmed.slice(0, sep).trim(), trimmed.slice(sep + 1).trim()]);
      }
      return fields;
    })
    .filter((fields) => fields.length > 0);
}

// Fields as an object, for header blocks where keys are known and unique.
function asObject(fields) {
  const out = {};
  for (const [key, value] of fields) out[key.toLowerCase()] = value;
  return out;
}

function splitList(value) {
  if (!value) return [];
  return value.split(/\s*[|,]\s*/).map((s) => s.trim()).filter(Boolean);
}

// "être" -> "etre", so data filenames stay ASCII and URL-safe.
export function slug(value) {
  return value
    .normalize('NFD')
    .replace(/[\u0300-\u036f]/g, '')
    .toLowerCase()
    .trim()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-|-$/g, '');
}

export function parseQuiz(text, filename) {
  const blocks = parseBlocks(text);
  if (blocks.length === 0) throw new Error(`${filename} is empty`);

  const head = asObject(blocks[0]);
  const questions = blocks.slice(1).map((fields, i) => {
    const q = asObject(fields);
    const type = (q.type || 'fill').toLowerCase();
    if (!q.prompt) throw new Error(`${filename}: question ${i + 1} has no prompt`);
    if (!q.answer) throw new Error(`${filename}: question ${i + 1} has no answer`);
    return {
      type: type === 'mcq' ? 'mcq' : 'fill',
      prompt: q.prompt,
      verb: q.verb || null,
      answer: q.answer,
      // "alt" lets a question accept more than one spelling.
      accepted: [q.answer, ...splitList(q.alt)],
      choices: splitList(q.choices),
      hint: q.hint || null,
      why: q.why || null,
      tense: q.tense || null,
    };
  });

  return {
    file: filename,
    id: head.id || slug(filename.replace(/\.txt$/, '')),
    subject: head.subject || 'General',
    title: head.title || filename,
    description: head.description || '',
    tags: splitList(head.tags),
    questions,
  };
}

export function parseVerb(text, name) {
  const blocks = parseBlocks(text);
  if (blocks.length === 0) throw new Error(`verb table for ${name} is empty`);

  const head = asObject(blocks[0]);
  const participles = Object.entries(head)
    .filter(([key]) => key.startsWith('participle'))
    .map(([key, value]) => [key.replace(/^participle\s*/, ''), value]);

  const tenses = blocks.slice(1).map((fields) => {
    const tense = fields.find(([key]) => key.toLowerCase() === 'tense');
    return {
      name: tense ? tense[1] : 'tense',
      // Keep file order, and keep duplicates out of the way of asObject().
      rows: fields.filter(([key]) => key.toLowerCase() !== 'tense'),
    };
  });

  return {
    verb: head.verb || name,
    english: head.english || '',
    group: head.group || '',
    auxiliary: head.auxiliary || '',
    note: head.note || '',
    participles,
    tenses,
  };
}
