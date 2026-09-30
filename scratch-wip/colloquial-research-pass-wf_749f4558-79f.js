export const meta = {
  name: 'colloquial-research-pass',
  description: 'Haiku researches each dialect\'s unsure phrases online; Sonnet re-opens every source and applies only proven changes',
  phases: [{ title: 'Research', model: 'haiku' }, { title: 'Verify and apply', model: 'sonnet' }],
}
const ROOT = 'C:/Users/Shaf/Downloads/vibe-code-projs/aRABIC GRAMMAR TOOL/_wt-wheel'
const DIALECTS = [
  { key: 'egyptian', name: 'Egyptian (Cairene) Arabic' },
  { key: 'lebanese', name: 'Lebanese (Beiruti) Arabic' },
  { key: 'gulf', name: 'Gulf Arabic (UAE and Kuwait)' },
  { key: 'iraqi', name: 'Iraqi (Baghdadi) Arabic' },
  { key: 'moroccan', name: 'Moroccan Arabic (Darija, Casablanca/Rabat)' },
]
const ITEMS = {
  type: 'object', required: ['items'],
  properties: { items: { type: 'array', items: { type: 'object',
    required: ['unit', 'where', 'current', 'verdict', 'sources'],
    properties: {
      unit: { type: 'string' }, where: { type: 'string', description: 'slot name, or lesson + dialogue/exercise location' },
      current: { type: 'string' }, verdict: { enum: ['keep', 'change', 'unverified'] },
      proposed_arabic: { type: 'string' }, proposed_transliteration: { type: 'string' }, reason: { type: 'string' },
      sources: { type: 'array', items: { type: 'object', required: ['url', 'quote'], properties: { url: { type: 'string' }, quote: { type: 'string' } } } },
    } } } },
}
const RESULT = {
  type: 'object', required: ['applied', 'rejected', 'checker'],
  properties: {
    applied: { type: 'array', items: { type: 'object', required: ['unit', 'where', 'from', 'to', 'source'], properties: { unit: { type: 'string' }, where: { type: 'string' }, from: { type: 'string' }, to: { type: 'string' }, source: { type: 'string' } } } },
    rejected: { type: 'array', items: { type: 'object', required: ['unit', 'where', 'why'], properties: { unit: { type: 'string' }, where: { type: 'string' }, why: { type: 'string' } } } },
    checker: { type: 'string', description: 'ok, or the faults the unit checker still prints' },
  },
}
const results = await pipeline(DIALECTS,
  d => agent(`You are checking doubtful words in a ${d.name} course. Repo: ${ROOT}.
Read ${ROOT}/backend/data/colloquial/review-notes.json. The keys starting "${d.key}/" (unit-01..unit-17) each have an "unsure" list of notes the original writer was not sure about. The unit files are ${ROOT}/backend/data/colloquial/${d.key}/unit-NN.json.
For every unsure note, search the web for AUTHORITATIVE evidence of how ${d.name} actually says it: dialect dictionaries (e.g. Lisaan Masry for Egyptian, Wiktionary dialect entries with citations, Hans Wehr-level dialect dictionaries such as Qafisheh for Gulf, Woodhead & Beene for Iraqi, Harrell for Moroccan), university or Peace Corps dialect course books, and native-speaker language sites. Forums and AI-written pages do not count.
Rules, strict: never make anything up. Every source must be a URL you actually opened, with a short exact quote copied from that page showing the word. If you cannot find such a source, the verdict is "unverified" and nothing changes. Say "change" only when a source shows the current wording is wrong or clearly unnatural, and give the proposed Arabic and matching transliteration in the style the file already uses. Say "keep" when a source confirms the current wording. Do NOT edit any file.
Work through all 17 units. Return every item.`, { label: `research:${d.key}`, phase: 'Research', model: 'haiku', schema: ITEMS }),
  (found, d) => agent(`You are the checker for a ${d.name} course. Repo: ${ROOT}. A cheaper researcher produced these findings:
${JSON.stringify(found.items.filter(i => i.verdict === 'change'))}
For every item: open each source URL yourself (WebFetch) and confirm the quote really is on that page and really supports the proposed wording for ${d.name}. The researcher may have invented quotes or URLs; assume nothing. If the evidence does not hold, reject it with the reason.
For each approved item, edit ${ROOT}/backend/data/colloquial/${d.key}/<unit>.json: change the Arabic and its transliteration wherever that exact phrase appears (phrase, reply, dialogue, de_book, exercise answer/accepted/options), keeping every exercise consistent (answer must stay in accepted, options must contain the answer). Keep the old form in an exercise's accepted list if it is still understood. Change nothing else.
Then for every unit you touched run from ${ROOT}: python -m backend.scripts.check_colloquial_unit ${d.key} <unit> (set PYTHONIOENCODING=utf-8). Fix until it prints ok.
Return what you applied (with the source URL), what you rejected and why, and the checker result.`, { label: `verify:${d.key}`, phase: 'Verify and apply', model: 'sonnet', schema: RESULT })
    .then(r => ({ dialect: d.key, found: found.items, ...r })),
)
return results.filter(Boolean)