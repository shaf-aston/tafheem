/** Vocabulary quiz, one word, four meanings, both directions. */
import { useEffect, useState } from 'react'

import { MEANINGS } from '../lib/quiz'
import { QUIZ } from '../lib/quizBanks'
import { quizNote } from '../lib/quizNote'
import { fillIn, sayIn } from '../lib/say'
import { PHONE, useMedia } from '../lib/useMedia'
import { useQuizQuestion } from '../lib/useQuizQuestion'
import { useQuizRound } from '../lib/useQuizRound'
import { useQuizScore } from '../lib/useQuizScore'
import { useQuizSetup } from '../lib/useQuizSetup'

import QuizAyah from './quiz/QuizAyah'
import QuizExample from './quiz/QuizExample'
import PracticeSentence from './quiz/PracticeSentence'
import QuizBoard from './QuizBoard'
import QuizInsights from './quiz/QuizInsights'
import QuizSetup from './quiz/QuizSetup'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import SectionHeader from './ui/SectionHeader'
import FeedbackButton from './ui/FeedbackButton'
import { Skeleton } from './ui/Skeleton'

// A fresh seed every time, so reloading the page gives a different first word
// instead of the same one forever. Inside the round the seed only counts up,
// which is what keeps each question a pure derivation of state.
const freshRound = (previous) => ({
  seed: (Math.random() * 0x7fffffff) | 0 || 1,
  asked: new Set(),
  // Bumped once per round, and the review list is read under it. The list
  // shrinks as the round is answered, so left to refetch on its own it would
  // rebuild the question already on screen underneath the player, and the
  // answer they then clicked would be scored against a different word.
  at: (previous?.at ?? 0) + 1,
})

/**
 * The Quiz tab: what is tested (useQuizSetup), the question that gives
 * (useQuizQuestion), the round being played (useQuizRound) and what the answers
 * add up to (useQuizScore). This file joins them and draws the page.
 */
export default function QuizPanel({ accent, onProgress }) {
  const setup = useQuizSetup()
  const { language, bank, autoNext, setAutoNext } = setup
  // Seed and seen-list travel together: the question is derived from them, so
  // moving on is one state change and the question is never stale.
  const [round, setRound] = useState(freshRound)
  const { words, question, questionCount, enough, noneInLanguage, owed, dialect } = useQuizQuestion(setup, round)
  const { score, bestStreak, saving, record, clear } = useQuizScore(setup)

  const phone = useMedia(PHONE)
  // Every English sentence on this tab goes through say(); fill() is for the
  // one sentence whose two halves are elements rather than text.
  const say = sayIn(language)
  const fill = fillIn(language)

  const play = useQuizRound({
    question,
    onAnswer: record,
    onNext: (asked) => setRound((r) => ({
      at: r.at,
      seed: r.seed + 1,
      asked: asked ? new Set(r.asked).add(asked.answerId) : r.asked,
    })),
    autoNext,
    setAutoNext,
  })
  const { shown, answered, correct, reviewing } = play

  // Tell the header pen how the round is going. Reported, not decided: what the
  // pen does with a streak or a wrong answer is `moodFrom`'s business. Reviewing
  // an earlier question is not a fresh answer, so it says nothing then.
  useEffect(() => {
    if (!onProgress) return
    const live = reviewing === null
    onProgress({
      streak: score.streak,
      answer: live && answered ? (correct ? 'correct' : 'wrong') : null,
    })
  }, [onProgress, score.streak, answered, correct, reviewing])

  // Everything a round owns, cleared in one place; the score, the seen-list,
  // the answer on screen and the strip of questions behind it.
  const resetRound = () => {
    play.reset()
    setRound(freshRound)
    clear()
  }

  // Changing what is being tested starts a fresh round: a score carried across
  // two different word sets would not mean anything.
  const startRound = (choice) => {
    setup.change(choice)
    resetRound()
  }

  const note = quizNote(shown, { language, dialect, say })

  return (
    // The tab reads the way its language reads. Urdu in a left-to-right page is
    // not merely untidy: a sentence built from two Urdu pieces with an element
    // between them comes out in the wrong order, because the element is neutral
    // and takes the direction of the text either side of it.
    <div className="panel" lang={language} dir={language === 'en' ? 'ltr' : 'rtl'}>
      <SectionHeader tab="quiz" title={say('Quiz')} />

      <QuizSetup setup={setup} owed={owed} say={say} phone={phone} accent={accent} onChange={startRound} />

      {words.isError && (
        <ErrorAlert
          title={say('Could not load those words')}
          error={words.error}
          fallback={say('Those word lists may not have been built yet.')}
        />
      )}

      {words.isPending && <Skeleton className="h-64 w-full" />}

      {/* A short surah can hold fewer words than a question has options. Say so
          instead of quietly padding the question out with words from elsewhere.
          A set with no meanings in the chosen language is a different problem
          with a different answer, so it is told apart rather than counted as a
          set that is merely short. */}
      {!words.isPending && !enough && !words.isError && (
        <EmptyState>
          {noneInLanguage
            ? say(
              "No {language} meaning has ever been written for these words."
              + " The Qur'an sets have one; the everyday list has no {language} source at all.",
              { language: say(MEANINGS[language].name) },
            )
            : bank.live
              ? say('Nothing due now. A word comes back here when it is time to see it again.')
              : say(
                'Only {n} words here, too few for a {k}-option question.'
                + ' Pick a longer surah or a whole juz.',
                { n: questionCount, k: QUIZ.optionCount },
              )}
        </EmptyState>
      )}

      {enough && (
        <>
          <QuizBoard
            round={play}
            accent={accent}
            say={say}
            fill={fill}
            autoNext={autoNext}
            setAutoNext={setAutoNext}
            score={score}
            bestStreak={bestStreak}
            onRestart={resetRound}
            note={note}
            afterAnswer={(word) => (word.ayah
              ? <QuizAyah key={word.ayah.join(':')} ayah={word.ayah} accent={accent} />
              : <QuizExample word={word.answerWord} accent={accent} say={say} />)}
          />

          {/* Said once, quietly, and only when it is true. A whole session
              saved to nowhere is worth knowing about while it is happening,
              not a week later when Review is mysteriously empty. */}
          {!saving && (
            <p className="text-center type-small text-[var(--text-faint)]">
              {say('Answers aren’t being saved right now, so they won’t reach Review.')}
            </p>
          )}

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <p className="type-small text-[var(--text-faint)]">
              {say('Keys 1–{k} answer', { k: QUIZ.optionCount })}
            </p>
            <FeedbackButton module="quiz" item={question?.answerId} accent={accent} />
          </div>

          <QuizInsights accent={accent} language={language} />
          <PracticeSentence say={say} />
        </>
      )}
    </div>
  )
}
