/** The answer to a word search: the word asked about in full, its root-mates beside it. */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { rootBabsQuery } from '../../api'
import { entrySpans } from '../../lib/entrySpan'
import { plainPronunciation } from '../../lib/pronounce'
import { useSetting } from '../../lib/settings'

import SenseBands from './SenseBands'
import WordGrid from './WordGrid'
import ArabicText from '../ui/ArabicText'
import EmptyState from '../ui/EmptyState'
import Pronunciation from '../ui/Pronunciation'
import RootActions from '../ui/RootActions'
import SourceBadge from '../ui/SourceBadge'
import StatusNote, { NoteWord } from '../ui/StatusNote'
import VerbFormTag from '../ui/VerbFormTag'

// Tailwind needs the literal class names present in source to keep them in the
// build; a computed string like `sm:col-span-${n}` would be purged.
const SM_SPAN = { 1: 'sm:col-span-1', 2: 'sm:col-span-2' }
const LG_SPAN = { 1: 'lg:col-span-1', 2: 'lg:col-span-2', 3: 'lg:col-span-3' }

/** A word that is no headword, found as the word it is a form of, or by its root. */
export function ReadAsNote({ readAs }) {
  if (!readAs) return null
  const { typed, lemma, root } = readAs
  return (
    <StatusNote>
      <NoteWord text={typed} /> is not a headword
      {lemma && <>; read as a form of <NoteWord text={lemma} /></>}
      {root && <>, root <NoteWord text={[...root].join(' ')} /></>}
    </StatusNote>
  )
}

export default function Results({ data, accent, onGo, onLookup, aside = null }) {
  // The badge at the top right opens the references behind the bab names.
  const [refs, setRefs] = useState(false)
  if (data.results.length === 0) {
    return (
      <EmptyState>No entries. Try the bare root, without prefixes or endings.</EmptyState>
    )
  }

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between gap-3 flex-wrap">
        {/* One is the usual answer for a whole Arabic word, the dictionary is
            indexed by headword, but a part-word, a spaced root, or an English
            search all come back with several. */}
        <p className="text-[var(--text-dim)] type-body">
          {data.results.length === 1 ? '1 entry' : `${data.results.length} entries`}
        </p>
        {/* The panel's own link, on this line rather than a row of its own above it. */}
        {aside}
        <button
          type="button"
          onClick={() => setRefs((on) => !on)}
          aria-expanded={refs}
          aria-label="Show where each bab is recorded"
        >
          <SourceBadge source={data.source} />
        </button>
      </div>

      {/* Two questions, two shapes. An Arabic word asks what it means, and the
          answer is one entry read in full. An English word asks which words
          carry that meaning, and the answer is the candidates side by side; the
          same full entries were a page and a half of scrolling to compare two
          of them. See dictionary/WordGrid.jsx. */}
      {data.lang === 'en' ? (
        <WordGrid results={data.results} query={data.query} accent={accent} onGo={onGo} />
      ) : (
        <Forms results={data.results} accent={accent} onGo={onGo} onLookup={onLookup} refs={refs} />
      )}
    </div>
  )
}

/**
 * The searched word in full, and the other words on its root as small cards.
 *
 * The first result is the word asked about (the service puts the exact word
 * first), and it is read the way a dictionary entry is read. The rest are
 * there to be compared, أطلع against استطلع against اطلاع, so they sit side by
 * side in a grid, each row full and a card wide only where its lines wrap
 * (lib/entrySpan.js), so the eye moves across rather than down.
 * A drop-down would have hidden the very thing worth comparing.
 */
function Forms({ results, accent, onGo, onLookup, refs }) {
  const [lead, ...others] = results
  const sm = entrySpans(others, 2)
  const lg = entrySpans(others, 3)
  return (
    <>
      <Entry entry={lead} accent={accent} i={0} onGo={onGo} onLookup={onLookup} refs={refs} />
      {others.length > 0 && (
        <>
          <p className="type-small text-[var(--text-faint)] pt-2">
            {others.length === 1 ? 'One more word on this root' : `${others.length} more words on this root`}
          </p>
          {/* Grid default (stretch) so every card in a row shares that row's
              height; a short card beside a tall one used to end early and read
              as a mismatched row rather than one grid. */}
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
            {others.map((entry, i) => (
              <Entry
                key={`${entry.arabic}-${entry.root || i}`}
                entry={entry}
                accent={accent}
                i={i + 1}
                onGo={onGo}
                onLookup={onLookup}
                compact
                span={`${SM_SPAN[sm[i]]} ${LG_SPAN[lg[i]]}`}
                wide={lg[i] >= 2}
                sameRoot={entry.root === lead.root}
              />
            ))}
          </div>
        </>
      )}
    </>
  )
}

/** The root's Form I باب from the classical books; nothing at all when none records one. */
function RootBabs({ root, refs }) {
  const { data } = useQuery(rootBabsQuery(root))
  return data?.readings.length ? <VerbFormTag readings={data.readings} plain showSources={refs} /> : null
}

/**
 * One dictionary entry. Full for the word searched; compact for the words
 * beside it, where the root is left off when it is the same one printed
 * above, and its columns (`span`) come from the whole set (lib/entrySpan.js).
 * One type scale throughout (styles/text.css tokens): a card holding eight senses
 * reads at the same size as one holding a single line, only its footprint
 * differs.
 */
function Entry({ entry, accent, i, onGo, onLookup, refs = false, compact = false, span = '', wide = false, sameRoot = false }) {
  // Off by default for nobody, but one switch away for anyone who finds the
  // extra words distracting. Read here rather than passed down, so the switch
  // reaches the one place that draws them.
  const showSynonyms = useSetting('synonyms')

  return (
    <div
      style={{ '--i': i }}
      className={`rise-in rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border)]
        ${compact ? 'p-3 space-y-2' : 'p-4 space-y-3'} ${span}`}
    >
      {/* Two rows: word beside its sound, root beside its bab (from the books, never typed in). */}
      <div className="grid grid-cols-[auto_auto] justify-between items-baseline gap-x-3 gap-y-0.5" dir="rtl">
        <ArabicText as="div" style={{ color: accent }}>{entry.arabic}</ArabicText>
        <Pronunciation size="body">{entry.transliteration}</Pronunciation>
        {entry.root && !sameRoot && (
          <ArabicText as="div" className="text-[var(--text-faint)]">جذر: {entry.root}</ArabicText>
        )}
        {!compact && entry.root && <div dir="ltr"><RootBabs root={entry.root} refs={refs} /></div>}
      </div>

      {/* A one-column card has no synonyms (that is what keeps it narrow), and
          the band's empty word column would squeeze its senses to a sliver. */}
      {entry.definitions?.length > 0 && (
        showSynonyms && !(compact && !wide) ? (
          <SenseBands
            definitions={entry.definitions}
            synonyms={entry.synonyms}
            accent={accent}
            onLookup={onLookup}
          />
        ) : (
          <ol className="list-decimal ps-6 min-w-0 space-y-1.5 type-body text-[var(--text)] marker:text-[var(--text-faint)]">
            {entry.definitions.map((d, n) => <li key={n}>{plainPronunciation(d)}</li>)}
          </ol>
        )
      )}

      {entry.root && (
        // showRoot=false: the root already prints above under "جذر:", so the
        // bare repeat inside RootActions is dropped.
        <RootActions root={entry.root} onGo={onGo} exclude="dict" showRoot={false} />
      )}
    </div>
  )
}
