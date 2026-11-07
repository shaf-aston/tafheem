/**
 * The rest of a Maqayees entry cut into the words it explains, each level with
 * the book's own lines about it.
 *
 * `senses` is [{arabic: [line], word, say, gloss, examples: [{arabic, say, english}]}],
 * cut by the backend (services/dictionary/root_senses), which finds every word
 * and saying in the book's lines and refuses an answer that does not cover them
 * in order. So the Arabic here is always the book's, never a model's spelling.
 *
 * The English used to be one numbered list beside one block of Arabic, and a
 * reader could not tell which Arabic went with "4. al-riṭāb". Here each word
 * has its row, the book's lines in the same row.
 *
 * Three choices, each remembered: the word in Arabic letters, Latin letters or
 * both; the sayings open or folded to a count; the book's lines beside or hidden.
 * And two layouts behind two icons: rows (the book level with each word) or
 * cards (the words at a glance, the book's lines at each card's foot).
 */
import { useState } from 'react'

import { entryLines } from '../../lib/dictionary/entryLines'
import { useRemembered } from '../../lib/store/useRemembered'

import { Line } from './EntryArabic'
import ArabicText from '../ui/text/ArabicText'
import Segmented from '../ui/inputs/Segmented'

const SCRIPT = [
  { id: 'both', label: 'Both' },
  { id: 'ar', label: 'Arabic' },
  { id: 'lat', label: 'Latin' },
]
const SAYINGS = [
  { id: 'open', label: 'Open' },
  { id: 'folded', label: 'Folded' },
]
const BOOK = [
  { id: 'beside', label: 'Beside' },
  { id: 'hidden', label: 'Hidden' },
]
const ids = (options) => options.map((o) => o.id)

/** The two layouts, each an icon: rows of the book beside its words, or a grid of word cards. */
const LAYOUTS = [
  { id: 'rows', label: 'Rows, the book beside each word', d: 'M4 6h16M4 12h16M4 18h16' },
  { id: 'cards', label: 'Cards, one per word', d: 'M4 4h7v7H4zM13 4h7v7h-7zM4 13h7v7H4zM13 13h7v7h-7z' },
]

export default function EntryWords({ senses, accent }) {
  const [script, setScript] = useRemembered('dict.words-script', ids(SCRIPT))
  const [sayings, setSayings] = useRemembered('dict.words-sayings', ids(SAYINGS))
  const [book, setBook] = useRemembered('dict.words-book', ids(BOOK))
  const [layout, setLayout] = useRemembered('dict.words-layout', ids(LAYOUTS))
  const show = { ar: script !== 'lat', lat: script !== 'ar' }
  const beside = book === 'beside'
  // The number goes only on rows that name a word: a closing formula or a
  // scholar's report is not the seventh word of the root.
  let n = 0

  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-x-6 gap-y-2">
        <div role="group" aria-label="Layout" className="flex gap-1">
          {LAYOUTS.map((l) => (
            <button
              key={l.id}
              type="button"
              aria-label={l.label}
              title={l.label}
              aria-pressed={layout === l.id}
              onClick={() => setLayout(l.id)}
              className="press grid place-items-center size-9 rounded-lg border border-[var(--border)]"
              style={layout === l.id ? { color: accent, borderColor: accent } : { color: 'var(--text-faint)' }}
            >
              <svg aria-hidden="true" viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinejoin="round" strokeLinecap="round">
                <path d={l.d} />
              </svg>
            </button>
          ))}
        </div>
        <Segmented captioned compact label="Words in" options={SCRIPT} value={script} onChange={setScript} accent={accent} />
        <Segmented captioned compact label="Sayings" options={SAYINGS} value={sayings} onChange={setSayings} accent={accent} />
        <Segmented captioned compact label="The book's lines" options={BOOK} value={book} onChange={setBook} accent={accent} />
      </div>
      {layout === 'cards' ? (
        <ol className="grid gap-x-6 gap-y-4 sm:grid-cols-2 xl:grid-cols-3">
          {senses.map((sense, i) => (
            <WordCard key={i} sense={sense} show={show} open={sayings === 'open'} beside={beside} accent={accent} />
          ))}
        </ol>
      ) : (
      <ol className="divide-y divide-[var(--border)]">
        {senses.map((sense, i) => (
          <Sense
            key={i}
            sense={sense}
            number={sense.word ? ++n : null}
            show={show}
            open={sayings === 'open'}
            beside={beside}
            accent={accent}
          />
        ))}
      </ol>
      )}
    </div>
  )
}

/** The book's lines for a sense, as the card's other views print them. */
const BookLines = ({ sense }) =>
  sense.arabic.flatMap((text) => entryLines(text)).map((line, j) => (
    <Line key={j} line={line} size="sm" style={{ color: 'var(--text-dim)' }} />
  ))

/** The sayings of a sense, open, or folded to a count; a folded one opens on its own. */
function Sayings({ sense, show, open, accent }) {
  const [opened, setOpened] = useState(false)
  const count = sense.examples.length
  if (!count) return null
  if (!(open || opened)) {
    return (
      <button type="button" className="type-small hover:underline text-start" style={{ color: accent }} onClick={() => setOpened(true)}>
        + {count} {count === 1 ? 'saying' : 'sayings'}
      </button>
    )
  }
  return (
    <ul className="space-y-2 ps-3 border-s-2 border-[var(--border)]">
      {sense.examples.map((example, j) => (
        <li key={j} className="space-y-0.5">
          {show.ar && <ArabicText as="p" size="sm" className="text-[var(--text-dim)] text-left">{example.arabic}</ArabicText>}
          {show.lat && example.say && <p className="type-small italic text-[var(--text-faint)]">{example.say}</p>}
          <p className="type-body text-[var(--text-dim)]">{example.english}</p>
        </li>
      ))}
    </ul>
  )
}

/**
 * One word as a card: the word large, its spelling and meaning under it, its
 * sayings, then the book's lines. Lines that name no word (a closing formula,
 * a scholar's report) span the grid as a note rather than pose as a word.
 * A hairline over each, not a box round it: the cards sit inside Ibn Faris's
 * section, and a box there was a box in a box.
 */
function WordCard({ sense, show, open, beside, accent }) {
  const word = (show.ar && sense.word) || (show.lat && sense.say)
  return (
    <li className={`border-t border-[var(--border)] pt-3 flex flex-col gap-1.5 min-w-0 ${sense.word ? '' : 'sm:col-span-full'}`}>
      {show.ar && sense.word && <ArabicText size="lg" className="text-[var(--text)] text-right">{sense.word}</ArabicText>}
      {show.lat && sense.say && (
        <span className={word === sense.say ? 'type-body font-semibold text-[var(--text)]' : 'type-small italic text-[var(--text-faint)]'}>{sense.say}</span>
      )}
      <span className="type-body text-[var(--text)]">{sense.gloss}</span>
      <Sayings sense={sense} show={show} open={open} accent={accent} />
      {beside && (
        <div className="mt-auto pt-2 border-t border-[var(--border)] space-y-1">
          <BookLines sense={sense} />
        </div>
      )}
    </li>
  )
}

function Sense({ sense, number, show, open, beside, accent }) {
  return (
    <li className={`py-3 gap-x-8 gap-y-2 ${beside ? 'grid lg:grid-cols-2 lg:items-start' : ''}`}>
      <div className="flex gap-3 min-w-0">
        <span className="type-small font-semibold w-5 shrink-0 pt-1" style={{ color: accent }} aria-hidden={!number}>
          {number ?? '·'}
        </span>
        <div className="space-y-1.5 min-w-0">
          <p className="flex flex-wrap items-baseline gap-x-3 gap-y-1">
            {show.ar && sense.word && <ArabicText size="base" className="text-[var(--text)]">{sense.word}</ArabicText>}
            {show.lat && sense.say && (
              <span className={show.ar && sense.word ? 'type-small italic text-[var(--text-faint)]' : 'type-body font-semibold text-[var(--text)]'}>
                {sense.say}
              </span>
            )}
            <span className="type-body text-[var(--text)]">{sense.word || sense.say ? `— ${sense.gloss}` : sense.gloss}</span>
          </p>
          <Sayings sense={sense} show={show} open={open} accent={accent} />
        </div>
      </div>
      {beside && (
        <div className="space-y-1 ps-8 lg:ps-0 lg:pe-4 lg:border-e-2 lg:border-[var(--border)]">
          <BookLines sense={sense} />
        </div>
      )}
    </li>
  )
}
