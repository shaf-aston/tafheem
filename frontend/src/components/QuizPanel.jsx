/** Vocabulary quiz, one word, four meanings, both directions. */
import { useEffect, useMemo, useRef, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { keyAction, typingElsewhere } from '../lib/answerKeys'
import { smartError } from '../lib/apiError'
import { fetchReviewItems, recordAttempt } from '../lib/progress'
import { buildQuestion, DIRECTIONS, makeRandom, MEANINGS } from '../lib/quiz'
import {
  allWords, BANKS, bankInfo, groupsFor, moduleFor, QUIZ, WHOLE_SET_SCOPES, wordsFor,
} from '../lib/quizBanks'
import { fillIn, sayIn } from '../lib/say'
import { useRemembered, useRememberedFlag } from '../lib/useRemembered'

import QuizInsights from './QuizInsights'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import SectionHeader from './ui/SectionHeader'
import Popover from './ui/Popover'
import FeedbackButton from './ui/FeedbackButton'
import Segmented from './ui/Segmented'
import { Skeleton } from './ui/Skeleton'
import AnswerSquare from './ui/AnswerSquare'
import ArabicText from './ui/ArabicText'
import AutoAdvanceToggle from './ui/AutoAdvanceToggle'

// What each remembered control is allowed to be, taken from the same tables the
// controls themselves are drawn from, so a set or a direction can never be
// added in one place and forgotten in the other.
const BANK_IDS = Object.keys(BANKS)
const DIRECTION_IDS = Object.keys(DIRECTIONS)
const LANGUAGE_IDS = Object.keys(MEANINGS)

// The two ways round a language can be asked. Derived rather than remembered, so
// there is no such thing as a language holding a direction from another one.
const directionsIn = (language) => [`ar-${language}`, `${language}-ar`]

// A fresh seed every time, so reloading the page gives a different first word
// instead of the same one forever. Inside the round the seed only counts up,
// which is what keeps each question a pure derivation of state.
const freshRound = (previous) => ({
  seed: (Math.random() * 0x7fffffff) | 0 || 1,
  asked: new Set(),
  // Bumped once per round, and the mistakes list is read under it. The list
  // shrinks as the round is answered, so left to refetch on its own it would
  // rebuild the question already on screen underneath the player, and the
  // answer they then clicked would be scored against a different word.
  at: (previous?.at ?? 0) + 1,
})

export default function QuizPanel({ accent, onProgress }) {
  // The setup is remembered, the round is not: a half-answered question put
  // back on screen would start a clock on a word last seen a week ago.
  // Defaults stay quiz.json's to set, so a first visit is unchanged.
  const [language, setLanguage] = useRemembered('quiz-language', LANGUAGE_IDS, QUIZ.language)
  const [savedDirection, setDirection] = useRemembered('quiz-direction', DIRECTION_IDS, QUIZ.direction)
  // A direction remembered while another language was on is not wrong, it just
  // belongs to that one. Switching language lands on plain Arabic-to-yours
  // rather than clearing what the other language had.
  // Held still across renders: the question is memoised on the direction, and a
  // fresh array every render would rebuild it under the player.
  const directions = useMemo(() => directionsIn(language), [language])
  const direction = directions.includes(savedDirection) ? savedDirection : directions[0]
  const [bankId, setBankId] = useRemembered('quiz-bank', BANK_IDS, QUIZ.bank)
  const [autoNext, setAutoNext] = useRememberedFlag('quiz-auto-next', QUIZ.autoNext)

  // Seed and seen-list travel together: the question is derived from them, so
  // moving on is one state change and the question is never stale.
  const [round, setRound] = useState(freshRound)
  // When the question on screen was first shown, so an answer can be timed.
  // A ref, not state: nothing on screen depends on it, and re-rendering the
  // question in order to time it would be the render that resets the clock.
  // Null until the first question is actually on screen; the effect below
  // starts it. An initial Date.now() here would be the moment the panel
  // mounted, which is before the words have even been fetched.
  const askedAt = useRef(null)
  // Set once if the store cannot be reached, so a session is never silently
  // saved to nowhere: without it the mistakes list is mysteriously empty later.
  const [saving, setSaving] = useState(true)
  const [picked, setPicked] = useState(null)
  // Whether the "why" behind the phrase/dialect badge is expanded. Reset per
  // question below, so an explanation left open does not follow onto the next word.
  const [noteOpen, setNoteOpen] = useState(false)
  // Every question already answered, in the order they were asked, so the strip
  // at the bottom can send you back to one. The live question is not in here, 
  // it has not been answered yet, so the strip shows it as the trailing chip.
  const [history, setHistory] = useState([])
  // Index into history while reviewing an earlier question, or null for the live one.
  const [reviewing, setReviewing] = useState(null)
  const [score, setScore] = useState({ right: 0, total: 0, streak: 0 })
  // The one thing a round leaves behind. Stored as what it is, a number written
  // out, so nothing has to interpret it years later.
  const [best, rememberBest] = useRemembered('quiz-best-streak')
  const bestStreak = Number(best) || 0

  const bank = BANKS[bankId]
  const client = useQueryClient()
  // Every English sentence on this tab goes through say(); fill() is for the
  // one sentence whose two halves are elements rather than text.
  const say = sayIn(language)
  const fill = fillIn(language)

  const groups = useQuery({
    queryKey: ['quiz-groups', bankId],
    queryFn: () => groupsFor(bankId),
    staleTime: Infinity,
  })

  // The cut, remembered as the pair it is: kind of cut, then the one inside it.
  // Both are checked against what this set actually offers, so a surah
  // remembered under the Qur'anic set cannot quietly decide what Everyday asks:
  // a set with no cuts allows only the empty one.
  const scopeIds = useMemo(
    () => [...WHOLE_SET_SCOPES.map((s) => s.id), ...(groups.data ?? []).map((s) => s.id)],
    [groups.data],
  )
  const groupIds = useMemo(
    () => (bank.grouped
      ? [
        ...WHOLE_SET_SCOPES.map((s) => s.group),
        ...(groups.data ?? []).flatMap((s) => s.options.map((o) => o.id)),
      ]
      : ['']),
    [bank.grouped, groups.data],
  )
  const [scope, setScope] = useRemembered('quiz-scope', scopeIds)
  const [groupId, setGroupId] = useRemembered('quiz-group', groupIds)

  // A surah's words are fetched, the bundled sets are not; react-query hides
  // the difference and remembers what has already been loaded.
  const words = useQuery({
    // The mistakes set is keyed by round as well, so it is re-read when a round
    // starts and never while one is being played.
    // The language is part of the key only because Mistakes reads a different
    // pile for each; every other set is the same words either way.
    queryKey: ['quiz-words', bankId, groupId, bank.live ? language : '', bank.live ? round.at : 0],
    queryFn: () => wordsFor(bankId, groupId, language),
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })

  // Wrong options for a mistakes question come from every word there is, not
  // from the mistakes themselves: three mistakes of three different types
  // cannot fill a four-option question between them.
  const everyWord = useQuery({
    queryKey: ['quiz-words', 'all'],
    queryFn: allWords,
    staleTime: Infinity,
    enabled: bank.live,
  })

  // What to say about this set beside the question, the dialect it is in.
  // Kept with the words rather than repeated in the panel.
  const info = useQuery({
    queryKey: ['quiz-set', bankId],
    queryFn: () => bankInfo(bankId),
    staleTime: Infinity,
  })

  // Only the words written in the language being shown. Everything outside the
  // Qur'an has no Urdu, so this is what empties the everyday set in an Urdu
  // round rather than letting a blank option reach the screen.
  const shape = DIRECTIONS[direction]
  const pool = useMemo(
    () => (words.data ?? []).filter((word) => word[shape.promptKey] && word[shape.answerKey]),
    [words.data, shape],
  )
  // Told apart from a short surah below: this set has words, they are just not
  // written in this language, and picking a longer one would not help.
  const noneInLanguage = pool.length === 0 && (words.data ?? []).length > 0

  // How many words are waiting to be put right, for the label on the Mistakes
  // control. Read again after every answer, unlike the pool: which words a
  // round asks has to hold still while it is played, but the count on a
  // control the player is not looking at is only ever news, and a control
  // reading "1" while four are waiting is worse than one that moves.
  const mistakes = useQuery({
    queryKey: ['quiz-review', language],
    queryFn: () => fetchReviewItems(moduleFor(language)),
    staleTime: Infinity,
    refetchOnWindowFocus: false,
  })
  const owed = mistakes.data?.length ?? 0

  // How many questions this selection can actually ask. A question is keyed on
  // meaning, not spelling, so two words meaning the same thing are one question
  //, counting words would show a total the round can never reach.
  const questionCount = useMemo(() => new Set(pool.map((w) => w.meaningKey)).size, [pool])
  // A cut has to hold a whole question. The mistakes set does not: its wrong
  // options come from everywhere, so a single word got wrong is already
  // askable, which is the point of it on the day the first mistake is made.
  const enough = questionCount >= (bank.live ? 1 : QUIZ.optionCount)

  const question = useMemo(() => {
    if (!enough) return null
    // Nothing to draw wrong options from yet; a question built now would be
    // the answer standing on its own.
    if (bank.live && !everyWord.data) return null
    return buildQuestion(pool, {
      direction,
      optionCount: QUIZ.optionCount,
      exclude: round.asked,
      random: makeRandom(round.seed),
      distractorBank: bank.live ? everyWord.data : null,
    })
  }, [pool, enough, direction, round, bank.live, everyWord.data])

  // One pair of values feeds the whole card, whether it is the live question or
  // one being looked at again, so nothing below has to know which it is.
  const past = reviewing === null ? null : history[reviewing]
  const shown = past ? past.question : question
  const shownPick = past ? past.picked : picked

  const answered = shownPick !== null
  const correct = answered && shown && shownPick === shown.answerId

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

  // The clock for the answer in front of you: started when a new live question
  // appears, and restarted on coming back from an earlier one in the strip,
  // because time spent re-reading an old correction is not time spent on this
  // word. Started here rather than in the handlers because a question also
  // appears on its own, the moment the words finish loading. It writes a ref
  // and no state: nothing on screen depends on the clock, and re-rendering the
  // question to time it would be the render that resets it.
  useEffect(() => {
    if (reviewing === null) askedAt.current = Date.now()
  }, [question, reviewing])

  const nextQuestion = () => {
    setReviewing(null)
    setNoteOpen(false)
    if (past) return
    setPicked(null)
    setRound((r) => ({
      seed: r.seed + 1,
      asked: question ? new Set(r.asked).add(question.answerId) : r.asked,
    }))
  }

  // Everything a round owns, cleared in one place; the score, the seen-list,
  // the answer on screen and the strip of questions behind it.
  const resetRound = () => {
    setPicked(null)
    setNoteOpen(false)
    setReviewing(null)
    setHistory([])
    setRound(freshRound())
    setScore({ right: 0, total: 0, streak: 0 })
  }

  // Changing what is being tested starts a fresh round: a score carried across
  // two different word sets would not mean anything.
  const startRound = (change) => {
    if ('bank' in change) { setBankId(change.bank); setGroupId(''); setScope('all') }
    if ('group' in change) setGroupId(change.group)
    if ('direction' in change) setDirection(change.direction)
    if ('language' in change) setLanguage(change.language)
    resetRound()
  }

  const section = (groups.data ?? []).find((s) => s.id === scope) ?? null

  // Switching to Surah starts on the first surah rather than on nothing: the
  // control should never leave the quiz in a state you have to fix yourself.
  const chooseScope = (id) => {
    setScope(id)
    const whole = WHOLE_SET_SCOPES.find((s) => s.id === id)
    const next = (groups.data ?? []).find((s) => s.id === id)
    startRound({ group: whole ? whole.group : next ? next.options[0].id : '' })
  }

  const restart = () => resetRound()

  const choose = (optionId) => {
    if (answered || !question || past) return
    setPicked(optionId)
    setHistory((h) => [...h, { question, picked: optionId }])

    const wasRight = optionId === question.answerId

    // Filed and forgotten: the round never waits for it, and a store that is
    // not there costs a row of history rather than the question in front of
    // you. Sent as measured, however long; which timings are honest enough to
    // average is the store's rule, not this panel's.
    recordAttempt({
      module: moduleFor(language),
      item: question.answerId,
      correct: wasRight,
      ms: askedAt.current === null ? null : Date.now() - askedAt.current,
      context: { bank: bankId, group: groupId, direction },
    }).then((result) => {
      setSaving(result.saved)
      // The answer just changed two numbers on screen: what is owed, on the
      // Mistakes control, and the reading at the foot of the page. Both are
      // re-read; the words of the round being played are not, so the question
      // in front of you cannot change underneath your hand.
      if (result.saved) {
        client.invalidateQueries({ queryKey: ['quiz-review'] })
        client.invalidateQueries({ queryKey: ['quiz-progress'] })
      }
    })

    // One answer, one streak, worked out here rather than inside the state
    // update so that the record it might beat is written once and in the open.
    const streak = wasRight ? score.streak + 1 : 0
    if (streak > bestStreak) rememberBest(String(streak))
    setScore((s) => ({ right: s.right + (wasRight ? 1 : 0), total: s.total + 1, streak }))
  }

  // Auto-advance carries the whole round, not only the right answers. A wrong
  // one moves on by itself too, just later: the correction underneath has to be
  // readable first. A question being looked at again never moves on by itself.
  useEffect(() => {
    if (!autoNext || !answered || past) return
    const timer = setTimeout(nextQuestion, correct ? QUIZ.autoNextMs : QUIZ.autoNextWrongMs)
    return () => clearTimeout(timer)
  })

  // Answer without reaching for the mouse. The app's own 1–5 tab shortcuts are
  // suppressed while this panel is open so the digits mean answers here.
  useEffect(() => {
    const onKeyDown = (e) => {
      if (typingElsewhere(e) || !question) return
      const action = keyAction(e.key, { checked: answered, optionCount: question.options.length })
      if (!action) return
      // Immediate, not plain stopPropagation: the app's tab shortcut listens on
      // window too, and plain stopPropagation does not stop a second listener on
      // the same target, so 2 would answer the question AND open Quran, and a 2
      // pressed with an answer already on screen would leave the quiz outright.
      if (action.do !== 'check' && action.do !== 'next') e.stopImmediatePropagation()
      // 'auto' before anything else, so the switch can be flipped at any point in
      // a round, including while an answer is on screen and about to take itself
      // away. One press answers here, so 'check' is nothing to do.
      if (action.do === 'auto') setAutoNext(!autoNext)
      if (action.do === 'toggle') choose(question.options[action.index].id)
      if (action.do === 'next') nextQuestion()
    }
    window.addEventListener('keydown', onKeyDown, true)
    return () => window.removeEventListener('keydown', onKeyDown, true)
  })

  const arabicPrompt = shown?.promptLang === 'ar'
  // Arabic and Urdu are both read right to left and both go through ArabicText;
  // English is the only side that is plain Latin text. So what each side needs
  // is its language, not a yes-or-no about Arabic.
  const rtl = (code) => code !== 'en'

  // What has to be said about this question before it is answered. A word that
  // never stands on its own in the Qur'an is the one thing that outranks the
  // dialect: its English is not quite a dictionary meaning, and you should know
  // that while you read it, not afterwards.
  // An Urdu speaker meeting a word they already half-know is the one thing this
  // tab can say that nothing else can, so it outranks the other two notes. Only
  // ever set on a word a person has checked, and only while Urdu is the meaning
  // being shown: in an English round it is answering a question nobody asked.
  const knownInUrdu = language !== 'en' ? shown?.urdu : null
  const note = knownInUrdu
    ? knownInUrdu.kind === 'false-friend'
      ? {
        text: say('not what it looks like'),
        why: say('These letters are an Urdu word too, and there they mean something else: {sense}.',
          { sense: knownInUrdu.sense }),
      }
      : {
        text: say('you know this one'),
        why: say('These letters are an Urdu word too, and there they mean the same thing.'),
      }
    : shown?.attached
    ? {
        text: say('from a phrase'),
        // "its meaning", not "its English": in an Urdu round the meaning shown
        // is Urdu, and the old wording said something that was no longer true.
        why: say('This word never stands on its own in the Qur’an, so its meaning '
          + 'is taken from a place where it was attached to another word.'),
      }
    : info.data?.dialect
      ? { text: info.data.dialect, why: say('Which Arabic this word is.') }
      : null

  return (
    // The tab reads the way its language reads. Urdu in a left-to-right page is
    // not merely untidy: a sentence built from two Urdu pieces with an element
    // between them comes out in the wrong order, because the element is neutral
    // and takes the direction of the text either side of it.
    <div className="space-y-4" lang={language} dir={language === 'en' ? 'ltr' : 'rtl'}>
      <SectionHeader title={say('Quiz')} arabic="اختبار" />

      {/* One quiet line of setup, so the question is the first thing you see
          rather than something you scroll past three panels to reach. */}
      <div className="flex flex-wrap items-center gap-x-4 gap-y-2">
        <Segmented
          captioned
          label={say('Words')}
          options={Object.entries(BANKS).map(([id, b]) => ({
            id,
            // The count rides on the control that goes there: a number sitting
            // anywhere else is a badge nobody connects to the button.
            label: b.live && owed > 0 ? `${say(b.label)} · ${owed}` : say(b.label),
          }))}
          value={bankId}
          accent={accent}
          onChange={(id) => startRound({ bank: id })}
        />
        {bank.grouped && (
          <>
            {/* Which kind of cut, then which one; two short controls instead of
                one dropdown holding 28 topics, 114 surahs and 30 juz at once. */}
            <Segmented
              label={say('Narrow by')}
              options={[
                ...WHOLE_SET_SCOPES.map(({ id, label }) => ({ id, label: say(label) })),
                ...(groups.data ?? []).map((s) => ({ id: s.id, label: say(s.label) })),
              ]}
              value={scope}
              accent={accent}
              onChange={chooseScope}
            />
            {section && (
              <select
                aria-label={say('Which {kind}', { kind: say(section.label).toLowerCase() })}
                value={groupId}
                onChange={(e) => startRound({ group: e.target.value })}
                style={{ '--c': accent }}
                className="py-1 px-2.5 rounded-full text-xs max-w-[13rem]
                  bg-[var(--surface)] border border-[var(--border)] text-[var(--text-dim)]
                  hover:text-[var(--text)] focus:border-[var(--c)] focus:outline-none transition-colors"
              >
                {section.options.map((option) => (
                  <option key={option.id} value={option.id} disabled={option.size < QUIZ.optionCount}>
                    {option.label} ({option.size})
                  </option>
                ))}
              </select>
            )}
          </>
        )}
        {/* The two settings chosen once and left, folded behind one pill that
            says what they are. All four controls on the line needed 1,170px of
            a 1,120px column, so English wrapped on every screen. */}
        <Popover
          label={`${MEANINGS[language].label} · ${DIRECTIONS[direction].short}`}
          title={`${say('Meaning in')}, ${say('Direction')}`}
        >
          {/* A grid with each Segmented's own wrapper dissolved, so the two
              captions share one column and the two rows start level. */}
          <div className="grid grid-cols-[auto_auto] items-center gap-x-2 gap-y-2.5 [&>div]:contents">
            <Segmented
              captioned
              label={say('Meaning in')}
              options={Object.entries(MEANINGS).map(([id, meaning]) => ({ id, label: meaning.label }))}
              value={language}
              accent={accent}
              onChange={(id) => startRound({ language: id })}
            />
            <Segmented
              captioned
              label={say('Direction')}
              // AR → UR stays as it is in every language: it is a pair of codes, not a
              // sentence, and an arrow glyph flips its own direction inside
              // right-to-left text, which would make the label say the opposite.
              options={directions.map((id) => ({ id, label: DIRECTIONS[id].short }))}
              value={direction}
              accent={accent}
              onChange={(id) => startRound({ direction: id })}
            />
          </div>
        </Popover>
      </div>

      {words.isError && (
        <ErrorAlert title={say('Could not load those words')}>
          {smartError(words.error, say('Those word lists may not have been built yet.'))}
        </ErrorAlert>
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
              ? say('Nothing to put right yet. A word you get wrong is kept here until you have got it right twice.')
              : say(
                'Only {n} words here, too few for a {k}-option question.'
                + ' Pick a longer surah or a whole juz.',
                { n: questionCount, k: QUIZ.optionCount },
              )}
        </EmptyState>
      )}

      {shown && (
        <div
          key={shown.prompt}
          className="rise-in rounded-[var(--radius-lg)] bg-[var(--surface)] border border-[var(--border)] p-6 space-y-5"
        >
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
              <div className="type-tiny uppercase tracking-wide text-[var(--text-faint)]">
                {say(arabicPrompt ? 'What does this mean?' : 'Which word is this?')}
              </div>
              {rtl(shown.promptLang) ? (
                <ArabicText as="div" size="lg" lang={shown.promptLang} className="text-[var(--text)]">
                  {shown.prompt}
                </ArabicText>
              ) : (
                <div className="text-3xl font-semibold text-[var(--text)]">{shown.prompt}</div>
              )}
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

          {/* Centred under the whole grid rather than under option 4, where it
              read as a stray label attached to that one answer. Always in the
              same place instead of appearing and vanishing with the answer. */}
          <div className="flex justify-center">
            <AutoAdvanceToggle value={autoNext} onChange={setAutoNext} accent={accent} say={say} />
          </div>

          {/* The row every answer gets: what the word meant, and the way on. */}
          <div aria-live="polite" className={answered ? '' : 'sr-only'}>
            {answered && (
              <div className="fade-in flex items-center justify-between gap-3 flex-wrap">
                <p className="text-sm" style={{ color: correct ? 'var(--success)' : 'var(--danger)' }}>
                  {correct ? say('Correct.') : fill('{word} means {meaning}', {
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
                <button
                  type="button"
                  onClick={nextQuestion}
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
              </div>
            )}
          </div>
        </div>
      )}

      {enough && (
        <>
          <Scoreboard
            score={score}
            bestStreak={bestStreak}
            bankSize={questionCount}
            asked={round.asked.size}
            accent={accent}
            say={say}
            onRestart={restart}
          />
          {/* The round so far, one chip a question: go back to any of them; 
              the ones you got wrong being the point of it. */}
          <QuestionStrip
            history={history}
            reviewing={reviewing}
            liveAnswered={picked !== null}
            accent={accent}
            say={say}
            onReview={(i) => { setReviewing(i); setNoteOpen(false) }}
          />

          {/* Said once, quietly, and only when it is true. A whole session
              saved to nowhere is worth knowing about while it is happening,
              not a week later when Mistakes is mysteriously empty. */}
          {!saving && (
            <p className="text-center type-small text-[var(--text-faint)]">
              {say('Answers aren’t being saved right now, so they won’t reach Mistakes.')}
            </p>
          )}

          <div className="flex items-center justify-center gap-4 flex-wrap">
            <p className="type-small text-[var(--text-faint)]">
              {say('Keys 1–{k} answer', { k: QUIZ.optionCount })}
            </p>
            <FeedbackButton module="quiz" item={question?.answerId} accent={accent} />
          </div>

          <QuizInsights accent={accent} language={language} />
        </>
      )}
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

function Scoreboard({ score, bestStreak, bankSize, asked, accent, say, onRestart }) {
  const percent = score.total ? Math.round((score.right / score.total) * 100) : 0
  const progress = Math.min(100, (asked / bankSize) * 100)

  return (
    <div className="space-y-1.5">
      <div className="h-1 rounded-full bg-[var(--surface)] overflow-hidden" aria-hidden="true">
        <div
          className="h-full rounded-full transition-[width] duration-[calc(var(--motion-spring-ms)*1ms)]"
          style={{ width: `${progress}%`, background: accent }}
        />
      </div>
      <div className="flex items-center justify-between gap-4 type-small text-[var(--text-faint)] flex-wrap">
        <p>
          <span className="text-[var(--text)] font-medium tabular-nums">
            {score.total ? `${score.right}/${score.total}` : '0/0'}
          </span>
          {score.total > 0 && <> · {percent}%</>}
          {score.streak > 1 && <> · {say('streak {n}', { n: score.streak })}</>}
          {bestStreak > 1 && <> · {say('best {n}', { n: bestStreak })}</>}
          {' · '}{say('{asked} of {total} seen', { asked, total: bankSize })}
        </p>
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
 * Every question of the round so far, one small square each, newest last: a tick
 * for right, a cross for wrong, and the question's number under it. Clicking one
 * puts that question back on screen exactly as it was answered.
 *
 * It earns its place by being the only way back to a word you got wrong, the
 * round otherwise moves on and the correction is gone in a second or two.
 */
function QuestionStrip({ history, reviewing, liveAnswered, accent, say, onReview }) {
  if (!history.length) return null

  return (
    <div className="flex flex-wrap items-start justify-center gap-1.5" role="group"
      aria-label={say('Questions answered so far')}>
      {history.map((entry, i) => {
        const right = entry.picked === entry.question.answerId
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
      {!liveAnswered && (
        <AnswerSquare
          number={history.length + 1}
          current={reviewing === null}
          label={`Question ${history.length + 1}, the one you are on`}
          accent={accent}
          onClick={() => onReview(null)}
        />
      )}
    </div>
  )
}
