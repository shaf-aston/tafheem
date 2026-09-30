export const meta = {
  name: 'colloquial-dialects',
  description: 'Write and native-check every spine unit for new Arabic dialects',
  phases: [{ title: 'Write' }, { title: 'Check' }],
}
const ROOT = 'C:/Users/Shaf/Downloads/vibe-code-projs/aRABIC GRAMMAR TOOL/_wt-wheel'
const D = {
  egyptian: 'Egyptian Arabic (Cairene, as spoken in Cairo)',
  lebanese: 'Lebanese Arabic (Beiruti)',
  gulf: 'Gulf Arabic (Khaleeji, as spoken in the UAE and Kuwait)',
  iraqi: 'Iraqi Arabic (Baghdadi)',
  moroccan: 'Moroccan Arabic (Darija, as spoken in Casablanca and Rabat)',
}
const units = args.units
const items = args.dialects.flatMap(k => units.map(u => ({ k, u })))
const SHARED = (k, u) => `Working directory: ${ROOT} (run commands from there).
Dialect: ${D[k]}. Folder key: ${k}. Unit: ${u}.
- The authoring rules: docs/colloquial-authoring-prompt.md and backend/data/colloquial/FORMAT.md. Read both fully.
- The outline to fill: the "${u}" entry of backend/data/colloquial/spine.json (print it with: python -c "import json;print(json.dumps(next(x for x in json.load(open('backend/data/colloquial/spine.json',encoding='utf-8'))['units'] if x['unit']=='${u}'),ensure_ascii=False,indent=1))").
- A finished example of the same unit in another dialect: backend/data/colloquial/damascene/${u}.json. Match its structure and depth (same lessons, every slot, same kinds and counts of dialogue, de_book, culture, exercises, challenge). Never copy its Damascene words: everything said must be how ${D[k]} actually says it.
- Output file: backend/data/colloquial/${k}/${u}.json with "dialect": "${D[k].split(' (')[0]}". Keep the same transliteration_key convention (3, 7, 2, sh, kh, gh, aa, ee, oo), adding letters this dialect needs (e.g. g for Egyptian/Gulf ج or ق) to the key.
- Exercise ids start with "${u}.". "too_formal" items are the MSA form a learner might wrongly use.
- Culture notes must be true for this region; Islamic phrasing (in shaa Allah, al-hamdu lillah) as locals really use it.
- Validate: python -m backend.scripts.check_colloquial_unit ${k} ${u} must print "ok". Fix and rerun until it does.
- Do not edit any other file. Do not touch git.`
const results = await pipeline(items,
  it => agent(`You are a careful writer of spoken Arabic teaching material, deeply familiar with ${D[it.k]}.
${SHARED(it.k, it.u)}
Where you are unsure how this dialect says something, research it (WebSearch dialect dictionaries such as Lisaan Masry or Livingarabic, forums, textbooks) before writing. Write the file, validate, then return one line: "ok" plus any slot you remain unsure of.`,
    { label: `write:${it.k}/${it.u}`, phase: 'Write', model: 'sonnet' }),
  (w, it) => agent(`You are a native-level reviewer of ${D[it.k]}. Another writer produced backend/data/colloquial/${it.k}/${it.u}.json. Their note: ${w}
${SHARED(it.k, it.u)}
Check every Arabic line (phrases, replies, dialogue, de_book, exercises, challenge): is it what a person from there really says, not MSA and not a Levantine/Damascene carry-over? Is the transliteration faithful to the Arabic and the key? Do exercise answers match their options and accepted lists? Is the English right? Research anything doubtful (WebSearch). Fix mistakes in place, then validate until "ok".`,
    { label: `check:${it.k}/${it.u}`, phase: 'Check', model: 'sonnet',
      schema: { type: 'object', properties: { valid: { type: 'boolean' }, fixes: { type: 'integer' }, examples: { type: 'array', items: { type: 'string' } }, unsure: { type: 'array', items: { type: 'string' } } }, required: ['valid', 'fixes', 'examples', 'unsure'] } })
    .then(r => ({ ...it, ...r })))
return results.filter(Boolean)