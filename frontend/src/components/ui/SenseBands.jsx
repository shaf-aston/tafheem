/**
 * An entry's senses, with the other words that mean the same thing beside them.
 *
 * A word is only a synonym of one sense, so the list belongs under the sense and
 * not under the entry. But the same word answers several senses at once: كتب
 * lists رَسَمَ under both "to mark on a surface" and "to draw", and printing it
 * again under each one said the two senses were unrelated when the shared word
 * is the thing tying them together.
 *
 * So senses carrying the identical list are banded, the words are printed once
 * beside the band, and the accent line runs exactly the height of the senses it
 * covers. Nothing labels the line: an Arabic word sitting beside an English
 * sense, joined by the line, is already saying what it is, and the heading it
 * used to carry was longer than the thing it labelled.
 *
 * The banding is the data's, not a rule written here: consecutive senses are one
 * band when their synonym lists match word for word.
 */
import { Fragment } from 'react'

import { plainPronunciation } from '../../lib/pronounce'
import { synonymGloss } from '../../lib/synonymGloss'

import ArabicText from './ArabicText'

/** Consecutive senses whose synonym lists are identical, in the entry's order. */
function band(definitions, synonyms = []) {
  return definitions.reduce((bands, definition, n) => {
    const words = synonyms[n] ?? []
    const key = words.map((s) => s.word).join('|')
    const last = bands.at(-1)
    if (last && last.key === key) last.senses.push({ n, definition })
    else bands.push({ key, words, senses: [{ n, definition }] })
    return bands
  }, [])
}

export default function SenseBands({ definitions, synonyms, accent, onLookup }) {
  const bands = band(definitions, synonyms)

  return (
    /* One grid for the whole entry rather than a grid per band, so every band's
       words start on the same left edge no matter how long the senses beside
       them run. The two halves of a band stretch to a shared height, which is
       what makes the line stop where its senses stop. */
    <div className="grid gap-x-4 gap-y-2 sm:grid-cols-[1fr_15rem]">
      {bands.map((b) => (
        <Fragment key={b.senses[0].n}>
          <ol
            start={b.senses[0].n + 1}
            /* Centred against its own words, so a band whose words wrap to two
               lines does not leave its senses sitting at the top of the gap. */
            className="list-decimal ps-6 min-w-0 space-y-1.5 self-center text-[var(--text)] type-body
              marker:text-[var(--text-faint)]"
          >
            {b.senses.map((s) => <li key={s.n}>{plainPronunciation(s.definition)}</li>)}
          </ol>

          {/* An empty column where a sense has no other word, so the senses
              below it stay on the same left edge instead of stepping across. */}
          <div
            style={{ borderColor: b.words.length ? accent : 'transparent' }}
            className="flex flex-col justify-center gap-1.5 ps-3 border-s-2 leading-snug"
          >
            {b.words.map(({ word, meaning }) => (
              <button
                key={word}
                type="button"
                onClick={() => onLookup(word)}
                title={meaning || 'No entry for this word; press to search for it'}
                /* No underline: a dotted line under every word made the column
                   a wall of stitching. The pointer and the brightening on
                   hover say it is pressable, like the chips do. */
                className="group text-start transition-colors"
              >
                <ArabicText size="sm" className="text-[var(--text-dim)] group-hover:text-[var(--text)] group-focus-visible:text-[var(--text)] transition-colors">{word}</ArabicText>{' '}
                {/* About one word in five is a phrase the dictionary has no
                    entry for. Saying so is the point: an empty space beside it
                    would read as "this one means nothing". */}
                <span className={`type-body text-[var(--text-faint)] group-hover:text-[var(--text-dim)] group-focus-visible:text-[var(--text-dim)] transition-colors ${meaning ? '' : 'italic'}`}>
                  {plainPronunciation(synonymGloss(meaning)) || 'not in the dictionary'}
                </span>
              </button>
            ))}
          </div>
        </Fragment>
      ))}
    </div>
  )
}
