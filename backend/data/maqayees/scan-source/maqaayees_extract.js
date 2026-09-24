export const meta = {
  name: 'maqaayees-extract-range',
  description: 'Extract+audit root-word entries from Maqaayees al-Lugha over a given page range',
  phases: [
    { title: 'Extract', detail: 'per-page-batch vision reading into JSON entries' },
    { title: 'Audit', detail: 'independent reviewer checks each batch against the scan' },
  ],
}

// Where the rendered pages are. Passed in rather than written here: this used
// to name a scratch directory under AppData\Local\Temp, which is cleared without
// warning; the script would then look runnable with its input gone.
//
// The pages are not a source. They are `page_<n>.png` rendered from
// "Maqaayees مقاييس اللغة.pdf", one image per PDF page, and can be made again
// at any resolution from the PDF, which is the thing worth keeping. Nothing here
// reads the PDF directly; the vision pass reads images.
const DIR = args.pagesDir

const START = args.start
const END = args.end
const BATCH = 3
const batches = []
for (let i = START; i <= END; i += BATCH) {
  const pages = []
  for (let j = i; j < Math.min(i + BATCH, END + 1); j++) pages.push(j)
  batches.push(pages)
}

const ENTRY_SCHEMA = {
  type: 'object',
  properties: {
    entries: {
      type: 'array',
      items: {
        type: 'object',
        properties: {
          root: { type: 'string', description: 'the Arabic root letters as printed, e.g. أح' },
          root_letters: { type: 'array', items: { type: 'string' } },
          core_meaning: { type: 'string', description: 'the classical/lexical primary meaning stated for the root, in Arabic, verbatim or near-verbatim as the text states it' },
          core_meaning_english: { type: 'string', description: 'concise, literal English gloss of the core meaning ONLY. Do not append any English explanation of Arabic grammar/morphology (sarf) terms - if the text names a sarf pattern, that goes in sarf_pattern instead, in Arabic, untranslated.' },
          sarf_pattern: { type: 'string', description: 'if the entry text explicitly names a morphological (sarf) category for this root, e.g. المضاعف, الأجوف, المثال, اللفيف, الناقص, المهموز - record that Arabic term verbatim here. Empty string if none is named.' },
          variances: {
            type: 'array',
            items: {
              type: 'object',
              properties: {
                usage: { type: 'string', description: 'the derived word/phrase form discussed' },
                meaning: { type: 'string', description: 'what this usage means, in Arabic as stated' },
                meaning_english: { type: 'string', description: 'concise literal English gloss only, no grammar commentary' },
                citation: { type: 'string', description: 'any poet/authority/verse cited as evidence, if present' },
              },
              required: ['usage', 'meaning'],
            },
          },
          printed_page_number: { type: 'string', description: 'the page number printed on the page (top corner), as a string' },
          pdf_page_index: { type: 'number' },
          notes: { type: 'string', description: 'anything uncertain, illegible, or ambiguous in the scan' },
        },
        required: ['root', 'core_meaning', 'pdf_page_index'],
      },
    },
  },
  required: ['entries'],
}

const AUDIT_SCHEMA = {
  type: 'object',
  properties: {
    entries: ENTRY_SCHEMA.properties.entries,
    issues_found: { type: 'array', items: { type: 'string' } },
  },
  required: ['entries'],
}

function imgList(pages) {
  return pages.map(p => `${DIR}\page_${String(p).padStart(4, '0')}.png`).join(', ')
}

const results = await pipeline(
  batches,
  async (pages) => {
    const imgs = imgList(pages)
    const prompt = `You are transcribing pages from Ibn Faris's classical Arabic dictionary "Maqaayees al-Lugha" (مقاييس اللغة), a root-based lexicon. Each entry starts with the root letters in brackets like ﴿ أح ﴾ followed by a sentence giving the CORE meaning of the root (usually "...أصل واحد يدل على..." = "one core meaning indicating..."), then goes on to give variant derived usages of that root with meanings and sometimes poetry citations as evidence.

Read these page images with the Read tool, in order: ${imgs}

For EACH root entry that begins or continues on these pages, extract:
- root: the root letters as printed
- core_meaning: the core/classical meaning as the text states it (Arabic)
- core_meaning_english: concise literal English gloss of the meaning ONLY - do not add English parentheticals explaining Arabic grammar/morphology (sarf) terms
- sarf_pattern: if the text explicitly names a sarf/morphology category for this root (e.g. المضاعف, الأجوف, المثال, اللفيف, الناقص, المهموز), put that Arabic term here verbatim untranslated; empty string if none is named
- variances: list of {usage, meaning, meaning_english, citation} for each derived word/usage discussed under that root
- printed_page_number: the page number printed in the page header
- pdf_page_index: the numeric index for that image (from the filename, e.g. page_0055.png -> 55)
- notes: flag anything illegible, uncertain, or where a poetry citation's meaning you're unsure of

If an entry's root began on a PREVIOUS page batch (i.e. this page continues an entry rather than starting one), still record it here with whatever content appears on THESE pages, and note in "notes" that it's a continuation.

Be literal and faithful to the text - do not paraphrase away the classical Arabic meaning. Accuracy over completeness: if something is truly illegible, say so in notes rather than guessing.`
    return agent(prompt, { label: `extract:${pages[0]}-${pages[pages.length-1]}`, phase: 'Extract', schema: ENTRY_SCHEMA })
  },
  async (extracted, pages) => {
    if (!extracted || !extracted.entries) return { entries: [], issues_found: ['extraction failed or returned nothing'] }
    const imgs = imgList(pages)
    const prompt = `You are an independent auditor verifying a transcription of a classical Arabic dictionary (Maqaayees al-Lugha, Ibn Faris) against the original scanned page images.

Read these page images with the Read tool: ${imgs}

Here is a prior agent's extraction to verify (JSON):
${JSON.stringify(extracted, null, 2)}

Check each entry against the actual page images for:
1. Root letters correct as printed
2. Core meaning is faithful to the Arabic text (not paraphrased incorrectly, not invented)
3. sarf_pattern is only filled when the page text actually names a morphology term, kept in Arabic, never invented in English
4. Variances/usages are actually present on the page and correctly attributed
5. No entries hallucinated (present in JSON but not on the page) or missing (present on page but not in JSON)

Return the CORRECTED, final entries array (fix anything wrong, add anything missing, remove anything hallucinated) plus an "issues_found" list of what you corrected (empty array if the extraction was already accurate).`
    return agent(prompt, { label: `audit:${pages[0]}-${pages[pages.length-1]}`, phase: 'Audit', schema: AUDIT_SCHEMA })
  }
)

const allEntries = results.filter(Boolean).flatMap(r => r.entries || [])
const allIssues = results.filter(Boolean).flatMap(r => r.issues_found || [])

log(`Collated ${allEntries.length} entries across ${batches.length} batches, ${allIssues.length} audit corrections made`)

return { entries: allEntries, issues_found: allIssues, batch_count: batches.length, range: [START, END] }
