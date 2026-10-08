/** The Quiz's round board: the question card, how the round is going, and every answer so far. */
import { useState } from 'react'

import { QUIZ } from '../lib/quizBanks'

import AnswerSquare from './ui/AnswerSquare'
import ArabicText from './ui/ArabicText'
import AutoAdvanceToggle from './ui/AutoAdvanceToggle'
import SpeakButton from './ui/SpeakButton'

// Arabic and Urdu are both read right to left and both go through ArabicText;
// English is the only side that is plain Latin text. So what each side needs
// is its language, not a yes-or-no about Arabic.
const rtl = (code) => code !== 'en'

/**
 * `round` is useQuizRound's return. `note` is `{text, why}` or null; `afterAnswer(shown)`
 * is what sits under an answered card; `children` stands in for the card when
 * there is no question on screen.
 */
export default function QuizBoard({
  round, accent, say, fill, autoNext, setAutoNext, score, bestStreak, onRestart, note, afterAnswer, children,
}) {
  const { history, reviewing, shown, strip } = round
  // The answered squares: a column on the far right until the round outgrows it.
  const railSide = history.length > 0 && history.length < QUIZ.stripSideMax

  return (
    <>
      {/* Three columns of one height: the question, how the round is going, and
          every answer so far on the far right. Stacked on phones. The answers
          move under the quiz as a row once there are too many for the column. */}
      <div className={`grid gap-4 ${railSide ? 'lg:grid-cols-[minmax(0,1fr)_17rem_auto]' : 'lg:grid-cols-[minmax(0,1fr)_17rem]'}`}>
        {shown ? (
          <QuestionCard
            key={shown.answerId}
            round={round}
            accent={accent}
            say={say}
            fill={fill}
            autoNext={autoNext}
            setAutoNext={setAutoNext}
            note={note}
            afterAnswer={afterAnswer}
          />
        ) : children}

        {/* Its contents sit absolutely on wide screens, so a long list scrolls
            inside the column instead of making the row taller than the question. */}
        <aside
          aria-label={say('This round')}
          className="relative rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] min-h-0"
        >
          <div className="p-4 flex flex-col gap-4 lg:absolute lg:inset-0">
            <Scoreboard score={score} bestStreak={bestStreak} say={say} onRestart={onRestart} />
            <MissedList history={history} reviewing={reviewing} say={say} onReview={strip.onReview} />
          </div>
        </aside>

        {railSide && (
          <aside
            aria-label={say('Questions answered so far')}
            className="hidden lg:block rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] p-3"
          >
            <QuestionStrip side say={say} {...strip} />
          </aside>
        )}
      </div>

      {/* Phones, or a round too long for the column: the same squares as a row. */}
      <div className={railSide ? 'lg:hidden' : ''}><QuestionStrip say={say} {...strip} /></div>
    </>
  )
}

// Keyed by the answer, so the "why" note closes by itself on the next question.
function QuestionCard({ round, accent, say, fill, autoNext, setAutoNext, note, afterAnswer }) {
  const { shown, shownPick, answered, correct, past, choose, next, speakRef } = round
  // Whether the "why" behind the phrase/dialect badge is expanded.
  const [noteOpen, setNoteOpen] = useState(false)
  const arabicPrompt = shown.promptLang === 'ar'

  return (
    <div className="rise-in rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] p-5 space-y-4">
      <div className="relative flex items-center justify-center">
        {/* One note slot, for whatever this question needs said before you
            answer rather than after you get it wrong: which Arabic is being
            asked for, or that its English came from a phrase. A button, not
            a span: the "why" was title-only tooltip before, unreachable on
            touch. Tapping reveals the same text inline, title stays for mouse. */}
        {note && (
          <div className="absolute end-0 top-0 flex flex-col items-end gap-1">
            <button
              type="button"
              title={note.why}
              aria-expanded={noteOpen}
              onClick={() => setNoteOpen((o) => !o)}
              className="type-tiny text-[var(--text-faint)] hover:text-[var(--text-dim)]
                px-2 py-0.5 rounded-full border border-[var(--border)] transition-colors"
            >
              {note.text}
            </button>
            {noteOpen && (
              <p className="type-small text-[var(--text-faint)] max-w-[14rem] text-end">
                {note.why}
              </p>
            )}
          </div>
        )}
        <div className="text-center space-y-1">
          <div className="eyebrow">
            {say(shown.listen ? 'Which word did you hear?' : arabicPrompt ? 'What does this mean?' : 'Which word is this?')}
          </div>
          {/* The speaker sits beside the word, not under it, so it costs no row.
              A heard question shows only the speaker until it is answered. */}
          <div className="inline-flex items-center gap-3">
            {(!shown.listen || answered) && (rtl(shown.promptLang) ? (
              <ArabicText as="div" size="lg" lang={shown.promptLang} className="text-[var(--text)]">
                {shown.prompt}
              </ArabicText>
            ) : (
              <div className="text-3xl font-semibold text-[var(--text)]">{shown.prompt}</div>
            ))}
            {/* Only the Arabic prompt: speaking an Arabic answer option would give it away. */}
            {shown.listen
              ? <SpeakButton key={shown.answerId} ref={speakRef} shortcut="S" text={shown.say} early />
              : arabicPrompt && <SpeakButton key={shown.answerId} ref={speakRef} shortcut="S" text={shown.prompt} />}
          </div>
        </div>
      </div>

      <div className="grid sm:grid-cols-2 gap-2.5" role="group" aria-label={say('Answers')}>
        {shown.options.map((option, i) => (
          <Option
            key={option.id}
            option={option}
            index={i}
            lang={shown.answerLang}
            say={say}
            answered={answered}
            picked={shownPick}
            answerId={shown.answerId}
            accent={accent}
            onChoose={choose}
          />
        ))}
      </div>

      {/* One row under the answers, always there so the card never changes
          height: what the word meant on the left, auto-advance and the way
          on at the right. */}
      <div className="flex items-center justify-between gap-3 flex-wrap min-h-9">
        <div aria-live="polite">
          {answered && (
            <p className="text-sm" style={{ color: correct ? 'var(--success)' : 'var(--danger)' }}>
              {/* A right answer already says so on the option it was; the
                  words are kept here for screen readers only, since this is
                  the line that gets announced. */}
              {correct ? <span className="sr-only">{say('Correct.')}</span> : fill('{word} means {meaning}', {
                // Whichever side is Arabic gets the Arabic face, otherwise the
                // correction renders the word smaller than the question. The
                // meaning half carries its own language too: in an Urdu round
                // both halves read right to left, in two scripts. Where the
                // two land in the sentence is the language's business, which
                // is why fill() places them rather than this file.
                word: (
                  <ArabicText lang="ar">
                    {arabicPrompt ? shown.prompt : shown.answerText}
                  </ArabicText>
                ),
                meaning: rtl(arabicPrompt ? shown.answerLang : shown.promptLang) ? (
                  <ArabicText
                    lang={arabicPrompt ? shown.answerLang : shown.promptLang}
                    className="text-[var(--text)] font-semibold"
                  >
                    {arabicPrompt ? shown.answerText : shown.prompt}
                  </ArabicText>
                ) : (
                  <strong className="text-[var(--text)]">
                    {arabicPrompt ? shown.answerText : shown.prompt}
                  </strong>
                ),
              })}
            </p>
          )}
        </div>
        <div className="flex items-center gap-3 ms-auto">
          <AutoAdvanceToggle value={autoNext} onChange={setAutoNext} accent={accent} say={say} />
          {answered && (
            <button
              type="button"
              onClick={next}
              autoFocus
              style={{ background: accent, color: 'var(--bg)', '--c': accent }}
              className="flex items-center gap-2 ps-5 pe-3 py-2 rounded-[var(--radius-md)]
                text-sm font-semibold glow hover:brightness-110 active:translate-y-px
                transition-[filter,transform]"
            >
              {say(past ? 'Back to the question' : 'Next word')}
              {/* The key printed on the button it fires, so the shortcut is
                  learnt where it is used rather than from a line of hints. */}
              <kbd
                aria-hidden="true"
                className="px-1.5 py-0.5 rounded type-tiny font-semibold leading-none
                  bg-[var(--bg)]/25 border border-current/30"
              >
                Enter ↵
              </kbd>
            </button>
          )}
        </div>
      </div>

      {answered && afterAnswer?.(shown)}
    </div>
  )
}

function Option({ option, index, lang, say, answered, picked, answerId, accent, onChoose }) {
  const isAnswer = option.id === answerId
  const isPicked = option.id === picked

  // Before answering the accent guides; after, only right and wrong matter.
  let border = 'var(--border)'
  let color = 'var(--text)'
  if (answered && isAnswer) {
    border = 'var(--success)'
    color = 'var(--success)'
  } else if (answered && isPicked) {
    border = 'var(--danger)'
    color = 'var(--danger)'
  }

  // The verdict rides on the option itself. That keeps the answer and the word
  // it belongs to in one place, and saves a whole row below the grid.
  let verdict = null
  if (answered && isAnswer) verdict = say(isPicked ? 'Correct' : 'Answer')
  else if (answered && isPicked) verdict = say('Not this')

  return (
    <button
      type="button"
      onClick={() => onChoose(option.id)}
      disabled={answered}
      style={{ '--i': index, '--c': accent, borderColor: border, color }}
      className={`rise-in option flex items-center gap-3 px-4 py-3 rounded-[var(--radius-md)] text-start
        bg-[var(--surface-hi)] border
        ${answered ? 'cursor-default' : ''}
        ${answered && !isAnswer && !isPicked ? 'opacity-50' : ''}`}
    >
      <span
        className="shrink-0 w-6 h-6 grid place-items-center rounded-full type-small
          bg-[var(--surface)] text-[var(--text-faint)]"
        aria-hidden="true"
      >
        {index + 1}
      </span>
      {lang === 'en' ? (
        <span className="text-sm">{option.text}</span>
      ) : (
        <ArabicText lang={lang} className="leading-tight">{option.text}</ArabicText>
      )}
      {verdict && <span className="ms-auto type-small font-medium shrink-0">{verdict}</span>}
    </button>
  )
}

function Scoreboard({ score, bestStreak, say, onRestart }) {
  const wrong = score.total - score.right
  const right = score.total ? (score.right / score.total) * 100 : 0
  // Right runs green from the top, wrong takes the rest; before any answer it is an empty ring.
  const ring = score.total
    ? `conic-gradient(var(--success) 0 ${right}%, var(--danger) 0)`
    : 'var(--border)'

  return (
    <div className="flex items-center gap-4">
      <div
        role="img"
        aria-label={say('{n}% right', { n: Math.round(right) })}
        className="shrink-0 w-14 h-14 rounded-full grid place-items-center"
        style={{ background: ring }}
      >
        <span className="w-11 h-11 rounded-full bg-[var(--surface)] grid place-items-center type-small font-semibold tabular-nums">
          {score.total ? `${Math.round(right)}%` : '–'}
        </span>
      </div>
      <div className="type-small text-[var(--text-faint)] space-y-0.5 min-w-0">
        <p><span className="text-[var(--success)] font-medium tabular-nums">{score.right}</span> {say('right')}</p>
        <p><span className="text-[var(--danger)] font-medium tabular-nums">{wrong}</span> {say('wrong')}</p>
        {bestStreak > 1 && <p>{say('streak {n}', { n: score.streak })} · {say('best {n}', { n: bestStreak })}</p>}
        {score.total > 0 && (
          <button
            type="button"
            onClick={onRestart}
            className="hover:text-[var(--text)] underline underline-offset-2 transition-colors"
          >
            {say('Start over')}
          </button>
        )}
      </div>
    </div>
  )
}

/**
 * The words got wrong this round, newest first: the Arabic and what it means.
 * Pressing one puts that question back on screen.
 */
function MissedList({ history, reviewing, say, onReview }) {
  const missed = history
    .map((entry, i) => ({ ...entry, i }))
    .filter((entry) => !entry.correct)
    .reverse()

  return (
    <div className="flex flex-col gap-2 min-h-0 flex-1">
      <h3 className="eyebrow">
        {say('Got wrong')}
      </h3>
      {missed.length === 0 ? (
        <p className="type-small text-[var(--text-faint)]">{say('Nothing yet.')}</p>
      ) : (
        <ul className="space-y-1.5 max-h-72 lg:max-h-none overflow-y-auto">
          {missed.map(({ question, i }) => {
            const arabicFirst = question.promptLang === 'ar'
            const word = arabicFirst ? question.prompt : question.answerText
            const meaning = arabicFirst ? question.answerText : question.prompt
            const meaningLang = arabicFirst ? question.answerLang : question.promptLang
            return (
              <li key={i}>
                <button
                  type="button"
                  onClick={() => onReview(reviewing === i ? null : i)}
                  aria-current={reviewing === i || undefined}
                  className={`w-full flex items-center justify-between gap-3 px-3 py-1 rounded-[var(--radius-md)]
                    border text-start transition-colors hover:border-[var(--danger)]
                    ${reviewing === i ? 'border-[var(--danger)] bg-[var(--surface-hi)]' : 'border-[var(--border)]'}`}
                >
                  {meaningLang === 'en'
                    ? <span className="type-small text-[var(--text-dim)] truncate">{meaning}</span>
                    : <ArabicText size="sm" lang={meaningLang} className="text-[var(--text-dim)] truncate">{meaning}</ArabicText>}
                  <ArabicText size="sm" lang="ar" className="text-[var(--text)] shrink-0 leading-normal">{word}</ArabicText>
                </button>
              </li>
            )
          })}
        </ul>
      )}
    </div>
  )
}

/**
 * Every question of the round so far, one small square each, newest last: a tick
 * for right, a cross for wrong, and the question's number under it. Clicking one
 * puts that question back on screen exactly as it was answered.
 *
 * It earns its place by being the only way back to a word you got wrong, the
 * round otherwise moves on and the correction is gone in a second or two.
 */
function QuestionStrip({ history, reviewing, live, say, onReview, side = false }) {
  if (!history.length) return null

  return (
    <div
      role="group"
      // Down the column first, then a new column beside it.
      style={side ? { gridTemplateRows: `repeat(${QUIZ.stripRows}, auto)` } : undefined}
      className={side ? 'grid grid-flow-col gap-x-2 gap-y-1.5 justify-center' : 'flex flex-wrap items-start justify-center gap-1.5'}
      aria-label={say('Questions answered so far')}>
      {history.map((entry, i) => {
        const right = entry.correct
        const open = reviewing === i
        return (
          <AnswerSquare
            key={i}
            status={right ? 'right' : 'wrong'}
            number={i + 1}
            current={open}
            label={`Question ${i + 1}, ${right ? 'correct' : 'wrong'}`}
            onClick={() => onReview(open ? null : i)}
          />
        )
      })}

      {/* The question you are on, so the strip does not stop short of where you
          actually are, and so there is a way back from reviewing an old one. */}
      {live && (
        <AnswerSquare
          number={history.length + 1}
          current={reviewing === null}
          label={`Question ${history.length + 1}, the one you are on`}
          onClick={() => onReview(null)}
        />
      )}
    </div>
  )
}
