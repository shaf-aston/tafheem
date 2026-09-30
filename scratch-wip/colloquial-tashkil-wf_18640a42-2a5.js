export const meta = {
  name: 'colloquial-tashkil',
  description: 'Haiku vowels every phrase and reply in six dialects; Sonnet checks a fresh 30% each round and fixes or sends it back',
  phases: [{ title: 'Vowel' }, { title: 'Check' }, { title: 'Redo' }],
}
const ROOT = 'C:/Users/Shaf/Downloads/vibe-code-projs/aRABIC GRAMMAR TOOL/_wt-wheel'
const T = 'C:/Users/Shaf/AppData/Local/Temp/claude/C--Users-Shaf-Downloads-vibe-code-projs-aRABIC-GRAMMAR-TOOL/ccede42c-0972-4906-92e6-3ff097927b4c/scratchpad'
const TOOL = `python "${T}/tashkil_tools.py"`
const D = {
  damascene: 'Damascene Arabic (Damascus, Syria)',
  egyptian: 'Egyptian Arabic (Cairene)',
  lebanese: 'Lebanese Arabic (Beiruti)',
  gulf: 'Gulf Arabic (Khaleeji, UAE and Kuwait)',
  iraqi: 'Iraqi Arabic (Baghdadi)',
  moroccan: 'Moroccan Arabic (Darija, Casablanca and Rabat)',
}
const UNITS = Array.from({ length: 17 }, (_, i) => `unit-${String(i + 1).padStart(2, '0')}`)
const RULES = `Tashkil rules:
- Vowel the words as a person from there actually SAYS them, following the "sound" field (the phrase in English letters), not as MSA. Example Damascene "kifak" -> كِيفَك, Egyptian "3aamil eeh" -> عَامِل إِيه.
- Mark every short vowel (fatha, kasra, damma), every shadda, and sukun where a consonant closes a syllable mid-word. Do not add case endings or tanween the dialect does not pronounce; a fixed religious formula keeps its real ending (السَّلَامُ عَلَيْكُم).
- Never change, add or remove a letter, hamza seat, or punctuation. Only harakat (U+064B to U+0652 and U+0670) may be added or changed.`
const HOW = (k, u) => `Working directory: ${ROOT} (run commands from there, with PYTHONIOENCODING=utf-8).
Dialect: ${D[k]}. Unit: ${u}.
1. Print the strings: ${TOOL} list ${k} ${u}
2. Use the Write tool to create ${T}/tk-${k}-${u}.json holding a JSON array of {"old": <arabic exactly as listed>, "new": <same with harakat>} for every listed string.
3. Apply: ${TOOL} apply ${k} ${u} ${T}/tk-${k}-${u}.json then ${TOOL} guard ${k} ${u}. Both must print "ok". If a line says letters changed, fix that entry and rerun.
Edit nothing else by hand. Do not touch git. Return one line: "ok N strings" or what failed.`
const CHECK = {
  type: 'object',
  properties: {
    checked: { type: 'integer' }, wrong: { type: 'integer' },
    examples: { type: 'array', items: { type: 'string' }, description: 'up to 8, as "old -> right (why)"' },
    patterns: { type: 'string', description: 'the recurring mistakes, as guidance for a rewrite' },
    applied: { type: 'boolean' },
  },
  required: ['checked', 'wrong', 'examples', 'patterns', 'applied'],
}
const vowel = (k, u, note) => agent(`You add tashkil (vowel marks) to spoken ${D[k]} teaching phrases.
${RULES}
${note ? `This unit was vowelled before and a native checker found too many mistakes. Re-read every string (they already carry harakat) and correct it. The checker's notes:\n${note}\n` : ''}${HOW(k, u)}`,
  { label: `${note ? 'redo' : 'vowel'}:${k}/${u}`, phase: note ? 'Redo' : 'Vowel', model: 'haiku' })

async function oneDialect(k) {
  await parallel(UNITS.map(u => () => vowel(k, u, '')))
  const rounds = []
  for (let r = 0; r < 3; r++) {
    const c = await agent(`You are a native-level checker of ${D[k]} pronunciation and of Arabic tashkil. Working directory: ${ROOT} (use PYTHONIOENCODING=utf-8).
Another writer vowelled every phrase and reply. Print your sample (about 30%, different each round): ${TOOL} sample ${k} ${r}
Each item gives the vowelled Arabic and its "sound" in English letters.
${RULES}
Judge each item: are the harakat what a speaker from there says, consistent with "sound", complete, and letters untouched? Count wrong items (an item with any wrong or missing mark is wrong). Research a word online if unsure.
If wrong/checked is 15% or less: correct the wrong ones yourself. For each unit with corrections write ${T}/fix-${k}-<unit>-r${r}.json as [{"old": <current vowelled text>, "new": <corrected>}] with the Write tool and run ${TOOL} apply ${k} <unit> <that file>, then ${TOOL} guard ${k}; both must print "ok". Set applied true.
If more than 15%: change nothing, set applied false, and write clear patterns so a rewriter can fix the whole dialect.
Do not touch git.`, { label: `check:${k} r${r}`, phase: 'Check', model: 'sonnet', schema: CHECK })
    if (!c) break
    rounds.push({ round: r, ...c })
    const rate = c.wrong / Math.max(1, c.checked)
    log(`${k} round ${r}: ${c.wrong}/${c.checked} wrong`)
    if (rate > 0.15) { await parallel(UNITS.map(u => () => vowel(k, u, c.patterns + '\nExamples: ' + c.examples.join('; ')))); continue }
    if (rate <= 0.05) break
  }
  return { dialect: k, rounds }
}
return await pipeline(Object.keys(D), oneDialect)