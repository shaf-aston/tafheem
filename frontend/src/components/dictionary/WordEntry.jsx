/** The answer to a word search: the word asked about in full, its root-mates beside it. */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { rootBabsQuery } from '../../api'
import { plainPronunciation } from '../../lib/speech/pronounce'
import { useSetting } from '../../lib/store/settings'

import SenseBands from './SenseBands'
import WordGrid from './WordGrid'
import ArabicText from '../ui/text/ArabicText'
import EmptyState from '../ui/feedback/EmptyState'
import Pronunciation from '../ui/text/Pronunciation'
import RootActions from '../ui/buttons/RootActions'
import SourceBadge from '../ui/feedback/SourceBadge'
import StatusNote, { NoteWord } from '../ui/feedback/StatusNote'
import VerbFormTag from '../ui/text/VerbFormTag'

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

export default function WordEntry({ data, accent, onGo, onLookup, aside = null }) {
  // The badge opens the references behind the bab names.
  const [refs, setRefs] = useState(false)
  if (data.results.length === 0) {
    return (
      <EmptyState>No entries. Try the bare root, without prefixes or endings.</EmptyState>
    )
  }

  const badge = (
    <button
      type="button"
      onClick={() => setRefs((on) => !on)}
      aria-expanded={refs}
      aria-label="Show where each bab is recorded"
    >
      <SourceBadge source={data.source} />
    </button>
  )
  const english = data.lang === 'en'

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
        {/* An Arabic answer carries its badge in its own card; the English grid has no one card to carry it. */}
        {english && badge}
      </div>

      {/* Two questions, two shapes. An Arabic word asks what it means, and the
          answer is one entry read in full. An English word asks which words
          carry that meaning, and the answer is the candidates side by side; the
          same full entries were a page and a half of scrolling to compare two
          of them. See dictionary/WordGrid.jsx. */}
      {english ? (
        <WordGrid results={data.results} query={data.query} accent={accent} onGo={onGo} />
      ) : (
        <Forms results={data.results} accent={accent} onGo={onGo} onLookup={onLookup} refs={refs} badge={badge} />
      )}
    </div>
  )
}

/**
 * The searched word in its card, and the other words on its root as rows under it.
 *
 * The first result is the word asked about (the service puts the exact word
 * first), and it is the answer: the one card on the page. The rest are context,
 * so they sit as quiet rows ruled off by a hairline. They were a grid of cards,
 * each its own box with the same Conjugate and Qur'an pills, and on a phone the
 * grid was one card wide: eight boxes, a screen and a half, saying the root's
 * name eight times.
 */
function Forms({ results, accent, onGo, onLookup, refs, badge }) {
  const [lead, ...others] = results
  return (
    <>
      <Entry entry={lead} accent={accent} onGo={onGo} onLookup={onLookup} refs={refs} badge={badge} />
      {others.length > 0 && (
        <section aria-labelledby="dict-more" className="space-y-2 pt-2">
          <h3 id="dict-more" className="eyebrow">
            {others.length === 1 ? 'One more word on this root' : `${others.length} more words on this root`}
          </h3>
          <ol className="dict-rows">
            {others.map((entry, i) => (
              <Row
                key={`${entry.arabic}-${entry.root || i}`}
                entry={entry}
                accent={accent}
                i={i + 1}
                onGo={onGo}
                onLookup={onLookup}
                sameRoot={entry.root === lead.root}
              />
            ))}
          </ol>
        </section>
      )}
    </>
  )
}

/** The root's Form I باب from the classical books; nothing at all when none records one. */
function RootBabs({ root, refs }) {
  const { data } = useQuery(rootBabsQuery(root))
  return data?.readings.length ? <VerbFormTag readings={data.readings} plain showSources={refs} /> : null
}

const hasSynonyms = (entry) => (entry.synonyms ?? []).some((list) => list.length > 0)

/** An entry's senses: banded beside their synonyms where it has any and they are wanted, else a plain list. */
function Senses({ entry, accent, onLookup, className }) {
  // Off by default for nobody, but one switch away for anyone who finds the
  // extra words distracting. Read here, the one place that draws them.
  const showSynonyms = useSetting('synonyms')
  if (!entry.definitions?.length) return null
  if (showSynonyms && hasSynonyms(entry)) {
    return <SenseBands definitions={entry.definitions} synonyms={entry.synonyms} accent={accent} onLookup={onLookup} />
  }
  return (
    <ol className={className}>
      {entry.definitions.map((d, n) => <li key={n}>{plainPronunciation(d)}</li>)}
    </ol>
  )
}

/**
 * The word searched, in full: the one card of the answer, its source badge in
 * its foot beside where the root goes next. One type scale throughout
 * (styles/text.css tokens).
 */
function Entry({ entry, accent, onGo, onLookup, refs, badge }) {
  return (
    <div style={{ '--i': 0 }} className="rise-in card space-y-3">
      {/* Two rows: word beside its sound, root beside its bab (from the books, never typed in). */}
      <div className="grid grid-cols-[auto_auto] justify-between items-baseline gap-x-3 gap-y-0.5" dir="rtl">
        <ArabicText as="div" style={{ color: accent }}>{entry.arabic}</ArabicText>
        <Pronunciation size="body">{entry.transliteration}</Pronunciation>
        {entry.root && <ArabicText as="div" className="text-[var(--text-faint)]">جذر: {entry.root}</ArabicText>}
        {entry.root && <div dir="ltr"><RootBabs root={entry.root} refs={refs} /></div>}
      </div>

      <Senses entry={entry} accent={accent} onLookup={onLookup}
        className="list-decimal ps-6 min-w-0 space-y-1.5 type-body text-[var(--text)] marker:text-[var(--text-faint)]" />

      <div className="flex flex-wrap items-center gap-2">
        {/* showRoot=false: the root already prints above under "جذر:". */}
        {entry.root && <RootActions root={entry.root} onGo={onGo} exclude="dict" showRoot={false} />}
        <span className="ms-auto">{badge}</span>
      </div>
    </div>
  )
}

/**
 * Another word on the root, as one row: the word at the edge Arabic starts
 * from, its sound and its senses run on beside it, one paragraph. Its root and
 * the ways on from it only when they differ from the card's: the same root's
 * Conjugate and Qur'an are one press away in the card above.
 */
function Row({ entry, accent, i, onGo, onLookup, sameRoot }) {
  const other = entry.root && !sameRoot
  return (
    <li style={{ '--i': i }} className="rise-in grid grid-cols-[minmax(0,1fr)_auto] items-baseline gap-x-4 gap-y-2">
      <div className="min-w-0">
        <Pronunciation className="me-2">{entry.transliteration}</Pronunciation>
        <Senses entry={entry} accent={accent} onLookup={onLookup}
          className="dict-run-on inline type-body text-[var(--text)]" />
      </div>
      <div className="text-end">
        <ArabicText as="div" style={{ color: accent }}>{entry.arabic}</ArabicText>
        {other && <ArabicText as="div" size="sm" className="text-[var(--text-faint)]">جذر: {entry.root}</ArabicText>}
      </div>
      {other && (
        <div className="col-span-full">
          <RootActions root={entry.root} onGo={onGo} exclude="dict" showRoot={false} />
        </div>
      )}
    </li>
  )
}
