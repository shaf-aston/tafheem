import { useEffect, useRef, useState } from 'react'

import { useAnswerKeys } from './useAnswerKeys'
import { QUIZ } from './quizBanks'

/**
 * One quiz round's moving parts, shared by the Quiz tab and Colloquial's Review:
 * the answer on screen, the history behind it, looking back at an earlier
 * question, the answer clock, auto-advance and the keyboard. Which question is
 * next, and what an answer is worth, stay with the caller: it hands in the
 * `question` on screen and hears `onAnswer({ question, picked, correct, ms })`
 * and `onNext(question)`.
 */
export function useQuizRound({ question, onAnswer, onNext, autoNext, setAutoNext }) {
  const [picked, setPicked] = useState(null)
  // Every question already answered, in the order they were asked, so the strip
  // can send you back to one. The live question is not in here, it has not been
  // answered yet, so the strip shows it as the trailing chip.
  const [history, setHistory] = useState([])
  // Index into history while reviewing an earlier question, or null for the live one.
  const [reviewing, setReviewing] = useState(null)
  // When the question on screen was first shown, so an answer can be timed.
  // A ref, not state: nothing on screen depends on it, and re-rendering the
  // question in order to time it would be the render that resets the clock.
  // Null until the first question is actually on screen; the effect below starts it.
  const askedAt = useRef(null)
  const speakRef = useRef(null)

  // One pair of values feeds the whole card, whether it is the live question or
  // one being looked at again, so nothing below has to know which it is.
  const past = reviewing === null ? null : history[reviewing]
  const shown = past ? past.question : question
  const shownPick = past ? past.picked : picked
  const answered = shownPick !== null
  const correct = answered && shown && shownPick === shown.answerId

  // The clock for the answer in front of you: started when a new live question
  // appears, and restarted on coming back from an earlier one in the strip,
  // because time spent re-reading an old correction is not time spent on this
  // word. Started here rather than in the handlers because a question also
  // appears on its own, the moment the words finish loading.
  useEffect(() => {
    if (reviewing === null) askedAt.current = Date.now()
  }, [question, reviewing])

  const choose = (id) => {
    if (answered || !question || past) return
    setPicked(id)
    const correct = id === question.answerId
    setHistory((h) => [...h, { question, picked: id, correct }])
    onAnswer({
      question,
      picked: id,
      correct,
      ms: askedAt.current === null ? null : Date.now() - askedAt.current,
    })
  }

  const next = () => {
    setReviewing(null)
    if (past) return
    setPicked(null)
    onNext?.(question)
  }

  const reset = () => {
    setPicked(null)
    setReviewing(null)
    setHistory([])
  }

  // Auto-advance carries the whole round, not only the right answers. A wrong
  // one moves on by itself too, just later: the correction underneath has to be
  // readable first. A question being looked at again never moves on by itself.
  useEffect(() => {
    if (!autoNext || !answered || past) return
    const timer = setTimeout(next, correct ? QUIZ.autoNextMs : QUIZ.autoNextWrongMs)
    return () => clearTimeout(timer)
  })

  // Answer without reaching for the mouse. The app's own 1-5 tab shortcuts are
  // suppressed while a round is open so the digits mean answers here.
  // `shown`, not `question`: a missed word looked at again after the last one
  // still owns the keys. 'auto' works at any point in a round, including while
  // an answer is on screen and about to take itself away. One press answers
  // here, so there is no 'check'.
  useAnswerKeys(shown && { checked: answered, optionCount: shown.options.length }, {
    auto: () => setAutoNext(!autoNext),
    speak: () => speakRef.current?.click(),
    toggle: (e, index) => choose(shown.options[index].id),
    next: (e) => {
      // Enter on a focused button would also click it, on the next question.
      e.preventDefault()
      next()
    },
  })

  return {
    history, reviewing, past, shown, shownPick, answered, correct,
    choose, next, reset, speakRef,
    // `live`: the strip's trailing "the one you are on" square, only while a
    // question is actually waiting for an answer.
    strip: { history, reviewing, live: Boolean(question) && picked === null, onReview: setReviewing },
  }
}
