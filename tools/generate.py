"""Generates the verb tables in verbs/ and the question banks in quiz/.

Run from the project root:

    python tools/generate.py

Regular verbs are conjugated from their group's rule; spelling-change verbs
apply a named rule on top of it; irregular verbs carry their six forms
explicitly. Every verb produces one question per person, half fill-in and half
multiple choice, so a twenty-verb quiz yields a bank of 120.

Anything hand-written in quiz/ that isn't listed in QUIZZES is left alone.
"""

import os
import random
import unicodedata

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PICK = 25  # questions drawn at random per attempt

# person index -> (table label, subject words to vary between)
PERSONS = [
    ('je', ['Je']),
    ('tu', ['Tu']),
    ('il/elle/on', ['Il', 'Elle', 'On']),
    ('nous', ['Nous']),
    ('vous', ['Vous']),
    ('ils/elles', ['Ils', 'Elles']),
]

VOWELS = 'aáàâeéèêiíìîoóòôuúùûyh'


def slug(value):
    stripped = ''.join(
        c for c in unicodedata.normalize('NFD', value)
        if unicodedata.category(c) != 'Mn'
    )
    return ''.join(c if c.isalnum() else '-' for c in stripped.lower()).strip('-')


# --------------------------------------------------------------------------
# conjugation rules
# --------------------------------------------------------------------------

def er_forms(inf):
    stem = inf[:-2]
    return [stem + e for e in ('e', 'es', 'e', 'ons', 'ez', 'ent')]


def ir_forms(inf):
    stem = inf[:-2]
    return [stem + e for e in ('is', 'is', 'it', 'issons', 'issez', 'issent')]


def re_forms(inf):
    stem = inf[:-2]
    return [stem + e for e in ('s', 's', '', 'ons', 'ez', 'ent')]


def _replace_last(text, old, new):
    i = text.rfind(old)
    return text[:i] + new + text[i + 1:]


# Each rule reshapes the stem used by the "boot" forms — singular plus
# ils/elles — which is where the sound of the ending changes.
BOOT_STEM = {
    'eacute': lambda stem: _replace_last(stem, 'é', 'è'),
    'egrave': lambda stem: _replace_last(stem, 'e', 'è'),
    'double': lambda stem: stem + stem[-1],
    'yer': lambda stem: stem[:-1] + 'i',
}

RULE_NOTES = {
    'ger': 'Keeps the -e- before -ons so the g stays soft: nous mangeons.',
    'cer': 'c becomes ç before -ons so it stays soft: nous commençons.',
    'eacute': 'é becomes è in the singular and ils/elles — but not in nous/vous.',
    'egrave': 'e becomes è in the singular and ils/elles — but not in nous/vous.',
    'double': 'The final consonant doubles in the singular and ils/elles.',
    'yer': 'y becomes i before a silent ending: nous -yons but je -ie.',
    'ayer': 'y may become i before a silent ending — je paie and je paye are both correct.',
}


def spelling_forms(inf, rule):
    forms = er_forms(inf)
    stem = inf[:-2]
    if rule == 'ger':
        forms[3] = stem + 'eons'
    elif rule == 'cer':
        forms[3] = stem[:-1] + 'çons'
    else:
        boot = BOOT_STEM['yer' if rule == 'ayer' else rule](stem)
        for i, ending in zip((0, 1, 2, 5), ('e', 'es', 'e', 'ent')):
            forms[i] = boot + ending
    return forms


# --------------------------------------------------------------------------
# verb data
# --------------------------------------------------------------------------

class Verb:
    def __init__(self, inf, english, complement, forms, group, note='', alts=None):
        self.inf = inf
        self.english = english
        self.complement = complement
        self.forms = forms
        self.group = group
        self.note = note
        self.alts = alts or {}

    @property
    def slug(self):
        return slug(self.inf)


REGULAR_ER = [
    ('parler', 'to speak', 'français en classe'),
    ('aimer', 'to like, to love', 'le chocolat'),
    ('habiter', 'to live', 'à Paris'),
    ('chanter', 'to sing', 'une chanson italienne'),
    ('danser', 'to dance', 'très bien'),
    ('regarder', 'to watch', 'la télévision'),
    ('écouter', 'to listen to', 'la radio'),
    ('travailler', 'to work', 'le samedi matin'),
    ('jouer', 'to play', 'au football'),
    ('donner', 'to give', 'un cadeau à Marie'),
    ('trouver', 'to find', 'toujours les clés'),
    ('penser', 'to think', 'souvent à elle'),
    ('marcher', 'to walk', 'dans le parc'),
    ('arriver', 'to arrive', 'à huit heures'),
    ('entrer', 'to enter', 'dans la salle'),
    ('porter', 'to wear, to carry', 'un manteau rouge'),
    ('montrer', 'to show', 'le chemin'),
    ('chercher', 'to look for', 'un appartement'),
    ('demander', 'to ask', "l'heure"),
    ('rester', 'to stay', 'à la maison'),
]

SPELLING_ER = [
    ('manger', 'to eat', 'une pomme', 'ger'),
    ('nager', 'to swim', 'à la piscine', 'ger'),
    ('voyager', 'to travel', 'en Italie', 'ger'),
    ('ranger', 'to tidy up', 'la chambre', 'ger'),
    ('commencer', 'to begin', 'le travail', 'cer'),
    ('lancer', 'to throw', 'la balle', 'cer'),
    ('avancer', 'to move forward', 'lentement', 'cer'),
    ('remplacer', 'to replace', 'le professeur', 'cer'),
    ('préférer', 'to prefer', 'le thé au café', 'eacute'),
    ('espérer', 'to hope', 'gagner le match', 'eacute'),
    ('répéter', 'to repeat', 'la phrase', 'eacute'),
    ('posséder', 'to own', 'une vieille voiture', 'eacute'),
    ('acheter', 'to buy', 'du pain', 'egrave'),
    ('lever', 'to raise', 'la main', 'egrave'),
    ('promener', 'to walk (a dog)', 'le chien', 'egrave'),
    ('appeler', 'to call', 'un taxi', 'double'),
    ('jeter', 'to throw away', 'les vieux papiers', 'double'),
    ('payer', 'to pay', "l'addition", 'ayer'),
    ('essayer', 'to try', 'une nouvelle robe', 'ayer'),
    ('nettoyer', 'to clean', 'la cuisine', 'yer'),
]

REGULAR_IR = [
    ('finir', 'to finish', 'le devoir'),
    ('choisir', 'to choose', 'un dessert'),
    ('grandir', 'to grow up', 'très vite'),
    ('réussir', 'to succeed', "l'examen"),
    ('obéir', 'to obey', 'aux règles'),
    ('remplir', 'to fill in', 'le formulaire'),
    ('réfléchir', 'to think it over', 'avant de parler'),
    ('punir', 'to punish', 'les tricheurs'),
    ('bâtir', 'to build', 'une maison'),
    ('saisir', 'to seize', "l'occasion"),
    ('guérir', 'to heal', 'rapidement'),
    ('nourrir', 'to feed', 'le chat'),
    ('applaudir', 'to applaud', 'les acteurs'),
    ('rougir', 'to blush', 'facilement'),
    ('maigrir', 'to lose weight', 'un peu'),
    ('grossir', 'to put on weight', 'en hiver'),
    ('ralentir', 'to slow down', 'au carrefour'),
    ('avertir', 'to warn', 'les voisins'),
    ('définir', 'to define', 'le problème'),
    ('unir', 'to unite', 'les deux équipes'),
]

REGULAR_RE = [
    ('vendre', 'to sell', 'sa vieille voiture'),
    ('attendre', 'to wait for', 'le bus'),
    ('entendre', 'to hear', 'un bruit étrange'),
    ('répondre', 'to answer', 'à la question'),
    ('perdre', 'to lose', 'souvent les clés'),
    ('descendre', 'to go down', "l'escalier"),
    ('rendre', 'to give back', 'le livre à Paul'),
    ('défendre', 'to defend', 'son ami'),
    ('confondre', 'to mix up', 'les deux mots'),
    ('mordre', 'to bite', 'dans la pomme'),
    ('tondre', 'to mow', 'la pelouse'),
    ('fondre', 'to melt', 'au soleil'),
    ('dépendre', 'to depend', 'de la météo'),
    ('tendre', 'to hold out', 'la main'),
    ('pendre', 'to hang', 'le tableau au mur'),
    ('étendre', 'to hang out', 'le linge'),
    ('prétendre', 'to claim', 'le contraire'),
    ('correspondre', 'to correspond', 'avec un ami belge'),
    ('suspendre', 'to hang up', 'sa veste'),
    ('répandre', 'to spread', 'la nouvelle'),
]

# inf, english, complement, six forms, optional note
IRREGULAR_IR = [
    ('partir', 'to leave', 'en vacances', 'pars pars part partons partez partent',
     'partir-type: the singular drops the last stem consonant — je pars, nous partons.'),
    ('sortir', 'to go out', 'le samedi soir', 'sors sors sort sortons sortez sortent',
     'partir-type: je sors, nous sortons.'),
    ('dormir', 'to sleep', 'huit heures par nuit', 'dors dors dort dormons dormez dorment',
     'partir-type: je dors, nous dormons.'),
    ('sentir', 'to smell, to feel', 'le parfum des roses', 'sens sens sent sentons sentez sentent',
     'partir-type: je sens, nous sentons.'),
    ('servir', 'to serve', 'le dîner', 'sers sers sert servons servez servent',
     'partir-type: je sers, nous servons.'),
    ('mentir', 'to lie', 'très rarement', 'mens mens ment mentons mentez mentent',
     'partir-type: je mens, nous mentons.'),
    ('ouvrir', 'to open', 'la porte', 'ouvre ouvres ouvre ouvrons ouvrez ouvrent',
     'ouvrir-type: an -ir verb that takes -er endings — j\'ouvre, not je ouvris.'),
    ('offrir', 'to offer', 'des fleurs', 'offre offres offre offrons offrez offrent',
     'ouvrir-type: takes -er endings.'),
    ('couvrir', 'to cover', 'la casserole', 'couvre couvres couvre couvrons couvrez couvrent',
     'ouvrir-type: takes -er endings.'),
    ('découvrir', 'to discover', 'un secret', 'découvre découvres découvre découvrons découvrez découvrent',
     'ouvrir-type: takes -er endings.'),
    ('souffrir', 'to suffer', 'du froid', 'souffre souffres souffre souffrons souffrez souffrent',
     'ouvrir-type: takes -er endings.'),
    ('cueillir', 'to pick', 'des fraises', 'cueille cueilles cueille cueillons cueillez cueillent',
     'Takes -er endings like ouvrir.'),
    ('venir', 'to come', 'de Lyon', 'viens viens vient venons venez viennent',
     'venir-type: the stem becomes vienn- in the singular and ils/elles.'),
    ('revenir', 'to come back', 'demain matin', 'reviens reviens revient revenons revenez reviennent',
     'venir-type: revienn- in the singular and ils/elles.'),
    ('devenir', 'to become', 'célèbre', 'deviens deviens devient devenons devenez deviennent',
     'venir-type: devienn- in the singular and ils/elles.'),
    ('tenir', 'to hold', 'le sac', 'tiens tiens tient tenons tenez tiennent',
     'tenir-type: tienn- in the singular and ils/elles.'),
    ('obtenir', 'to obtain', 'un bon résultat', 'obtiens obtiens obtient obtenons obtenez obtiennent',
     'tenir-type: obtienn- in the singular and ils/elles.'),
    ('maintenir', 'to maintain', 'le contact', 'maintiens maintiens maintient maintenons maintenez maintiennent',
     'tenir-type: maintienn- in the singular and ils/elles.'),
    ('courir', 'to run', 'tous les matins', 'cours cours court courons courez courent',
     'Keeps the r of the stem throughout: je cours, nous courons.'),
    ('mourir', 'to die', 'de faim', 'meurs meurs meurt mourons mourez meurent',
     'Stem changes to meur- in the singular and ils/elles.'),
]

CORE_IRREGULAR = [
    ('être', 'to be', 'en retard', 'suis es est sommes êtes sont',
     'Completely irregular — this one has to be learnt by heart.', {}),
    ('avoir', 'to have', 'un chien', 'ai as a avons avez ont',
     'Completely irregular — learn the whole table.', {}),
    ('aller', 'to go', 'au marché', 'vais vas va allons allez vont',
     'Looks like an -er verb but is irregular: je vais, nous allons.', {}),
    ('faire', 'to do, to make', 'la cuisine', 'fais fais fait faisons faites font',
     'Watch vous faites and ils font — no -ez, no -ent.', {}),
    ('dire', 'to say', 'la vérité', 'dis dis dit disons dites disent',
     'Watch vous dites — not vous disez.', {}),
    ('prendre', 'to take', 'le train', 'prends prends prend prenons prenez prennent',
     'The d disappears in the plural, and nn appears in ils prennent.', {}),
    ('apprendre', 'to learn', 'le français', 'apprends apprends apprend apprenons apprenez apprennent',
     'Follows prendre: apprenons, apprennent.', {}),
    ('pouvoir', 'to be able to', 'venir ce soir', 'peux peux peut pouvons pouvez peuvent',
     'Stem peu- in the singular, pouv- for nous/vous, peuv- for ils/elles.', {}),
    ('vouloir', 'to want', 'un café', 'veux veux veut voulons voulez veulent',
     'Stem veu- / voul- / veul-.', {}),
    ('devoir', 'to have to', 'partir maintenant', 'dois dois doit devons devez doivent',
     'Stem doi- / dev- / doiv-.', {}),
    ('savoir', 'to know', 'la réponse', 'sais sais sait savons savez savent',
     'Stem sai- in the singular, sav- in the plural.', {}),
    ('voir', 'to see', 'la mer', 'vois vois voit voyons voyez voient',
     'The i becomes y in nous voyons and vous voyez.', {}),
    ('boire', 'to drink', "de l'eau", 'bois bois boit buvons buvez boivent',
     'Three stems: boi- / buv- / boiv-.', {}),
    ('écrire', 'to write', 'une lettre', 'écris écris écrit écrivons écrivez écrivent',
     'The plural adds -v-: nous écrivons.', {}),
    ('lire', 'to read', 'le journal', 'lis lis lit lisons lisez lisent',
     'The plural adds -s-: nous lisons.', {}),
    ('mettre', 'to put', 'la table', 'mets mets met mettons mettez mettent',
     'One t in the singular, two in the plural.', {}),
    ('connaître', 'to know (someone)', 'bien cette ville',
     'connais connais connaît connaissons connaissez connaissent',
     'Circumflex on il connaît; the plural adds -ss-.', {2: ['connait']}),
    ('croire', 'to believe', 'cette histoire', 'crois crois croit croyons croyez croient',
     'Like voir: the i becomes y in nous croyons.', {}),
    ('recevoir', 'to receive', 'un cadeau', 'reçois reçois reçoit recevons recevez reçoivent',
     'Cedilla before o: je reçois, but nous recevons.', {}),
    ('vivre', 'to live', 'en France', 'vis vis vit vivons vivez vivent',
     'The plural adds -v-: nous vivons.', {}),
]


def build(spec, kind):
    verbs = []
    for entry in spec:
        if kind == 'er':
            inf, english, complement = entry
            verbs.append(Verb(inf, english, complement, er_forms(inf), 'regular -er verb'))
        elif kind == 'ir':
            inf, english, complement = entry
            verbs.append(Verb(inf, english, complement, ir_forms(inf), '2nd-group -ir verb'))
        elif kind == 're':
            inf, english, complement = entry
            verbs.append(Verb(inf, english, complement, re_forms(inf), 'regular -re verb'))
        elif kind == 'spelling':
            inf, english, complement, rule = entry
            verbs.append(Verb(inf, english, complement, spelling_forms(inf, rule),
                              'spelling-change -er verb', RULE_NOTES[rule],
                              {i: [_ayer_variant(inf, i)] for i in (0, 1, 2, 5)}
                              if rule == 'ayer' else None))
        elif kind == 'irregular':
            inf, english, complement, forms, note = entry[:5]
            verbs.append(Verb(inf, english, complement, forms.split(), '3rd-group -ir verb', note))
        elif kind == 'core':
            inf, english, complement, forms, note, alts = entry
            verbs.append(Verb(inf, english, complement, forms.split(), 'irregular verb', note, alts))
    return verbs


def _ayer_variant(inf, index):
    """je paie / je paye — both spellings are accepted for -ayer verbs."""
    stem = inf[:-2]
    return stem + ('e', 'es', 'e', None, None, 'ent')[index]


# --------------------------------------------------------------------------
# rendering
# --------------------------------------------------------------------------

ENDINGS = {
    'regular -er verb': ('-e', '-es', '-e', '-ons', '-ez', '-ent'),
    'spelling-change -er verb': ('-e', '-es', '-e', '-ons', '-ez', '-ent'),
    '2nd-group -ir verb': ('-is', '-is', '-it', '-issons', '-issez', '-issent'),
    'regular -re verb': ('-s', '-s', 'no ending', '-ons', '-ez', '-ent'),
}


def why_for(verb, index):
    label = PERSONS[index][0]
    endings = ENDINGS.get(verb.group)
    if verb.note and (endings is None or verb.forms[index] != _plain(verb, index)):
        return verb.note
    if endings is None:
        return verb.note or 'Irregular — check the table with the Hint button.'
    ending = endings[index]
    stem_rule = {
        'regular -er verb': 'drop -er',
        'spelling-change -er verb': 'drop -er',
        '2nd-group -ir verb': 'drop -ir',
        'regular -re verb': 'drop -re',
    }[verb.group]
    if ending == 'no ending':
        return f'{label}: {stem_rule}, and -re verbs take no ending in the 3rd person singular.'
    return f'{label}: {stem_rule}, add {ending}.'


def _plain(verb, index):
    """The form the verb would have if it followed its group with no exception."""
    if verb.group in ('regular -er verb', 'spelling-change -er verb'):
        return er_forms(verb.inf)[index]
    if verb.group == '2nd-group -ir verb':
        return ir_forms(verb.inf)[index]
    if verb.group == 'regular -re verb':
        return re_forms(verb.inf)[index]
    return None


def verb_file(verb):
    lines = [
        f'verb: {verb.inf}',
        f'english: {verb.english}',
        f'group: {verb.group}',
    ]
    if verb.note:
        lines.append(f'note: {verb.note}')
    lines.append('---')
    lines.append('tense: présent')
    for i, (label, _) in enumerate(PERSONS):
        form = verb.forms[i]
        if i == 0 and form[0].lower() in VOWELS:
            label = "j'"  # tables show the elision: j'achète, not je achète
        if i in verb.alts and verb.alts[i]:
            form = f"{form} / {verb.alts[i][0]}"
        lines.append(f'{label}: {form}')
    return '\n'.join(lines) + '\n'


def questions_for(verb, verb_index, rng):
    blocks = []
    for i, (_, subjects) in enumerate(PERSONS):
        form = verb.forms[i]
        subject = subjects[verb_index % len(subjects)]
        if i == 0 and form[0].lower() in VOWELS:
            opening = "J'___"
        else:
            opening = f'{subject} ___'
        prompt = f'{opening} ({verb.inf}) {verb.complement}.'

        alts = [a for a in verb.alts.get(i, []) if a]
        block = {
            'type': 'mcq' if (verb_index + i) % 2 else 'fill',
            'prompt': prompt,
            'verb': verb.inf,
            'answer': form,
            'alt': alts,
            'why': why_for(verb, i),
        }
        if block['type'] == 'mcq':
            pool = [f for j, f in enumerate(verb.forms)
                    if f != form and f not in alts and f]
            pool = list(dict.fromkeys(pool))
            distractors = rng.sample(pool, min(3, len(pool)))
            choices = distractors + [form]
            rng.shuffle(choices)
            block['choices'] = choices
        blocks.append(block)
    return blocks


def quiz_file(meta, verbs):
    rng = random.Random(meta['id'])
    lines = [
        '# Generated by tools/generate.py — edit that file, not this one.',
        '',
        f"id: {meta['id']}",
        'subject: French',
        f"title: {meta['title']}",
        f"description: {meta['description']}",
        f"tags: {meta['tags']}",
        f'pick: {PICK}',
    ]
    for verb_index, verb in enumerate(verbs):
        for block in questions_for(verb, verb_index, rng):
            lines.append('---')
            lines.append(f"type: {block['type']}")
            lines.append(f"prompt: {block['prompt']}")
            lines.append(f"verb: {block['verb']}")
            if block['type'] == 'mcq':
                lines.append('choices: ' + ' | '.join(block['choices']))
            lines.append(f"answer: {block['answer']}")
            if block['alt']:
                lines.append('alt: ' + ' | '.join(block['alt']))
            lines.append(f"why: {block['why']}")
    return '\n'.join(lines) + '\n'


# --------------------------------------------------------------------------

GROUPS = {
    'er': build(REGULAR_ER, 'er'),
    'spelling': build(SPELLING_ER, 'spelling'),
    'ir': build(REGULAR_IR, 'ir'),
    'irregular_ir': build(IRREGULAR_IR, 'irregular'),
    're': build(REGULAR_RE, 're'),
    'core': build(CORE_IRREGULAR, 'core'),
}

QUIZZES = [
    {
        'id': 'er-regular',
        'file': 'er-regular.txt',
        'title': '-er verbs — regular',
        'description': 'First-group verbs, the pattern most French verbs follow.',
        'tags': 'présent, -er, 1st group',
        'verbs': GROUPS['er'],
    },
    {
        'id': 'er-spelling',
        'file': 'er-spelling.txt',
        'title': '-er verbs — spelling changes',
        'description': 'manger, commencer, préférer, acheter, appeler, payer and friends.',
        'tags': 'présent, -er, exceptions',
        'verbs': GROUPS['spelling'],
    },
    {
        'id': 'ir-regular',
        'file': 'ir-regular.txt',
        'title': '-ir verbs — regular',
        'description': 'Second-group verbs that take -iss- in the plural, like finir.',
        'tags': 'présent, -ir, 2nd group',
        'verbs': GROUPS['ir'],
    },
    {
        'id': 'ir-irregular',
        'file': 'ir-irregular.txt',
        'title': '-ir verbs — irregular',
        'description': 'Third-group -ir verbs: partir, ouvrir, venir, courir and the rest.',
        'tags': 'présent, -ir, 3rd group',
        'verbs': GROUPS['irregular_ir'],
    },
    {
        'id': 're-regular',
        'file': 're-regular.txt',
        'title': '-re verbs — regular',
        'description': 'vendre-type verbs, including the bare 3rd person singular.',
        'tags': 'présent, -re, 3rd group',
        'verbs': GROUPS['re'],
    },
    {
        'id': 'irregular-core',
        'file': 'irregular-core.txt',
        'title': 'Core irregular verbs',
        'description': 'être, avoir, aller, faire and the other twenty you cannot avoid.',
        'tags': 'présent, irregular, essential',
        'verbs': GROUPS['core'],
    },
    {
        'id': 'mixed-review',
        'file': 'mixed-review.txt',
        'title': 'Mixed review',
        'description': 'Every group at once — the closest thing to the real test.',
        'tags': 'présent, mixed, revision',
        'verbs': [v for group in GROUPS.values() for v in group[:6]],
    },
]

HAND_WRITTEN = ['sample-other-subject.txt']


def main():
    verbs_dir = os.path.join(ROOT, 'verbs')
    quiz_dir = os.path.join(ROOT, 'quiz')

    for name in os.listdir(verbs_dir):
        if name.endswith('.txt'):
            os.remove(os.path.join(verbs_dir, name))

    written = {}
    for group in GROUPS.values():
        for verb in group:
            written[verb.slug] = verb
    for name, verb in sorted(written.items()):
        with open(os.path.join(verbs_dir, f'{name}.txt'), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(verb_file(verb))

    for meta in QUIZZES:
        with open(os.path.join(quiz_dir, meta['file']), 'w', encoding='utf-8', newline='\n') as fh:
            fh.write(quiz_file(meta, meta['verbs']))

    index = ['# One quiz file per line. Lines starting with # are ignored.',
             '# Order here = order shown on the home page.',
             '']
    index += [meta['file'] for meta in QUIZZES]
    index += [''] + HAND_WRITTEN
    with open(os.path.join(quiz_dir, 'index.txt'), 'w', encoding='utf-8', newline='\n') as fh:
        fh.write('\n'.join(index) + '\n')

    total = sum(len(meta['verbs']) * 6 for meta in QUIZZES)
    print(f'{len(written)} verb tables, {len(QUIZZES)} quizzes, {total} questions')
    for meta in QUIZZES:
        print(f"  {meta['file']:24} {len(meta['verbs']) * 6:4} questions")


if __name__ == '__main__':
    main()
