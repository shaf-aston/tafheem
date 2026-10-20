import { Fragment } from 'react'

import { isQuranic, recitedForm } from '../../lib/arabicText'
import { wordsOf } from '../../lib/memorise'

import ArabicText from '../ui/ArabicText'
import AyahNumber from './AyahNumber'
import Gap from './Gap'
import RecitedWord from './RecitedWord'
import { withinPart } from './hooks'

/**
 * One line of the book, right to left, with a box where each missing word was.
 *
 * The English sits under it throughout. It is a translation of the whole line,
 * never of the missing word on its own, so it is a reminder of where you are
 * rather than the answer.
 */
export default function Line({ line, flow, index, blanks, answers, checked, meaning, choices, accent, recite, onStartAt, onAnswer }) {
  const words = wordsOf(line.arabic)
  // One width for every typed blank on this line, from the longest recited
  // word among them: sizing each blank to its own answer leaks the length.
  const typeWidth = Math.max(
    3,
    ...words
      .map((word, w) => (blanks.has(`${index}:${w}`) ? recitedForm(word).length : 0)),
  ) + 1
  const drawn = words.map((word, w) => {
    const key = `${index}:${w}`
    // A poem's bayt is two hemistichs, sadr then ajuz, printed as one
    // line but never run together, forcing a wrap here after the sadr
    // shows that split without needing a second Line per bayt, which
    // would let pagesOf and the blank-picker split them across a page.
    const hemistichBreak = line.breakAfter === w && (
      <span key={`${key}:break`} className="basis-full h-0" aria-hidden="true" />
    )
    if (!blanks.has(key)) {
      return (
        <Fragment key={key}>
          {/* The display size, as the Qur'an tab and the surah reader set the
              text being read; the reading size made the mushaf look smaller. */}
          {recite
            ? <RecitedWord word={word} at={recite.from + w} recite={recite} accent={accent} onStartAt={onStartAt} />
            : <ArabicText size="lg">{word}</ArabicText>}
          {hemistichBreak}
        </Fragment>
      )
    }
    // Reciting a page you can read is not a test of remembering it. So
    // the same words that would be gaps to type stay covered here, and
    // the only thing that uncovers one is saying it.
    if (recite) {
      return (
        <Fragment key={key}>
          <RecitedWord
            word={word}
            at={recite.from + w}
            recite={recite}
            accent={accent}
            coverWidth={typeWidth}
            onStartAt={onStartAt}
          />
          {hemistichBreak}
        </Fragment>
      )
    }
    return (
      <Fragment key={key}>
        <Gap
          word={word}
          options={choices?.get(key)}
          value={answers[key] ?? ''}
          checked={checked}
          accent={accent}
          lineLabel={line.label}
          typeWidth={typeWidth}
          onChange={(value) => onAnswer(key, value)}
        />
        {hemistichBreak}
      </Fragment>
    )
  })
  const number = flow
    ? <AyahNumber aria-label={`ayah ${withinPart(line.label)}`}>{withinPart(line.label)}</AyahNumber>
    : <AyahNumber>{line.label}</AyahNumber>
  // Flowing, the line's two boxes step aside (display: contents) so its words
  // join the page's one run; the words themselves are drawn the same either way.
  return (
    <div className={flow ? 'contents' : 'space-y-1'}>
      {/* Right to left, wrapping downward, exactly as the line is printed. The
          reference goes last so it sits at the end of the line the way a mushaf
          puts the ayah number, in a right-to-left row, last is leftmost. */}
      <div
        className={flow ? 'contents' : 'flex flex-wrap items-baseline gap-x-2 gap-y-1'}
        dir="rtl"
        data-script={isQuranic(line.arabic) ? 'quran' : undefined}
      >
        {flow ? (
          <>
            {drawn.slice(0, -1)}
            {/* The last word and the ayah's number wrap as one, so a number
                is never left alone at the start of a row. */}
            <span className="inline-flex items-baseline gap-x-2">
              {drawn.at(-1)}
              {number}
            </span>
          </>
        ) : (
          <>
            {drawn}
            {number}
          </>
        )}
      </div>
      {/* The body size, not a label size: this is the translation being read,
          and it is the same text the surah reader one tab away already sets at
          this size. */}
      {!flow && meaning && line.english && (
        <p className="type-body text-[var(--text-dim)] leading-relaxed max-w-prose">
          {line.english}
        </p>
      )}
    </div>
  )
}
