/** Vocabulary quiz, one word, four meanings, both directions. */
import { useEffect, useMemo, useState } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchReviewItems, recordAttempt } from '../lib/progress'
import { buildQuestion, DIRECTIONS, makeRandom, MEANINGS } from '../lib/quiz'
import {
  allWords, BANKS, bankInfo, groupsFor, moduleFor, QUIZ, sentencesQuery, WHOLE_SET_SCOPES, wordsFor,
} from '../lib/quizBanks'
import { ayahQueries } from '../lib/quizAyah'
import { fillIn, sayIn } from '../lib/say'
import { progressKey, readSaved, writeSaved } from '../lib/stored'
import { useQuizRound } from '../lib/useQuizRound'
import { useRemembered, useRememberedFlag } from '../lib/useRemembered'

import QuizAyah from './QuizAyah'
import QuizExample from './QuizExample'
import PracticeSentence from './PracticeSentence'
import QuizBoard from './QuizBoard'
import QuizInsights from './QuizInsights'
import EmptyState from './ui/EmptyState'
import ErrorAlert from './ui/ErrorAlert'
import SectionHeader from './ui/SectionHeader'
import Popover from './ui/Popover'
import FeedbackButton from './ui/FeedbackButton'
import Segmented from './ui/Segmented'
import { Skeleton } from './ui/Skeleton'
import WheelPicker from './ui/WheelPicker'

// What each remembered control is allowed to be, taken from the same tables the
// controls themselves are drawn from, so a set or a direction can never be
// added in one place and forgotten in the other.
const BANK_IDS = Object.keys(BANKS)
const DIRECTION_IDS = Object.keys(DIRECTIONS)
const LANGUAGE_IDS = Object.keys(MEANINGS)
// The running tally, under the learner's own record like the best streak.
const SCORE_KEY = progressKey('quiz-score')
const NO_SCORE = { right: 0, total: 0, streak: 0 }

// The two ways round a language can be asked. Derived rather than remembered, so
// there is no such thing as a language holding a direction from another one.
const directionsIn = (language) => [`ar-${language}`, `${language}-ar`]

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
  // Set once if the store cannot be reached, so a session is never silently
  // saved to nowhere: without it the review list is mysteriously empty later.
  const [saving, setSaving] = useState(true)
  // Kept like the best streak below, so a reload does not wipe the tally; only
  // Start over (or a new word set) does, and Start over in settings forgets it.
  const [score, setScore] = useState(() => ({ ...NO_SCORE, ...readSaved(SCORE_KEY, NO_SCORE) }))
  useEffect(() => writeSaved(SCORE_KEY, score), [score])
  // The one thing a round leaves behind. Stored as what it is, a number written
  // out, so nothing has to interpret it years later.
  const [best, rememberBest] = useRemembered(progressKey('quiz-best-streak'))
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
    // The review set is keyed by round as well, so it is re-read when a round
    // starts and never while one is being played.
    // The language is part of the key only because Review reads a different
    // pile for each; every other set is the same words either way.
    queryKey: ['quiz-words', bankId, groupId, bank.live ? language : '', bank.live ? round.at : 0],
    queryFn: () => wordsFor(bankId, groupId, language),
    refetchOnWindowFocus: false,
  })

  // Wrong options for a review question come from every word there is, not
  // from the due words themselves: three words of three different types
  // cannot fill a four-option question between them.
  const everyWord = useQuery({
    queryKey: ['quiz-words', 'all'],
    queryFn: allWords,
    enabled: bank.live,
  })

  // What to say about this set beside the question, the dialect it is in.
  // Kept with the words rather than repeated in the panel.
  const info = useQuery({
    queryKey: ['quiz-set', bankId],
    queryFn: () => bankInfo(bankId),
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

  // How many words are waiting to be put right, for the label on the Review
  // control. Read again after every answer, unlike the pool: which words a
  // round asks has to hold still while it is played, but the count on a
  // control the player is not looking at is only ever news, and a control
  // reading "1" while four are waiting is worse than one that moves.
  const review = useQuery({
    queryKey: ['quiz-review', language],
    queryFn: () => fetchReviewItems(moduleFor(language)),
    refetchOnWindowFocus: false,
  })
  const owed = review.data?.length ?? 0

  // How many questions this selection can actually ask. A question is keyed on
  // meaning, not spelling, so two words meaning the same thing are one question
  //, counting words would show a total the round can never reach.
  const questionCount = useMemo(() => new Set(pool.map((w) => w.meaningKey)).size, [pool])
  // A cut has to hold a whole question. The review set does not: its wrong
  // options come from everywhere, so a single due word is already
  // askable.
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

  // Fetch the answer word's ayah the moment its question appears, so it is
  // ready when the answer lands. Failures here are silent; QuizAyah reads the
  // same cache and draws nothing without data.
  // A word with no ayah shows an everyday sentence instead, from one file.
  const ayahAt = question?.ayah
  const asked = Boolean(question)
  useEffect(() => {
    if (!asked) return
    if (!ayahAt) client.prefetchQuery(sentencesQuery)
    else for (const query of ayahQueries(ayahAt[0], ayahAt[1])) client.prefetchQuery(query)
  }, [client, asked, ayahAt])

  // Everything one answer sets going. Filed and forgotten: the round never waits
  // for the store, and one that is not there costs a row of history rather than
  // the question in front of you. Sent as measured, however long; which timings
  // are honest enough to average is the store's rule, not this panel's.
  const onAnswer = ({ question: asked, correct: wasRight, ms }) => {
    recordAttempt({
      module: moduleFor(language),
      item: asked.answerId,
      correct: wasRight,
      ms,
      context: { bank: bankId, group: groupId, direction, word: asked.answerWord },
    }).then((result) => {
      setSaving(result.saved)
      // The answer just changed two numbers on screen: what is owed, on the
      // Review control, and the reading at the foot of the page. Both are
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

  const play = useQuizRound({
    question,
    onAnswer,
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
    setScore(NO_SCORE)
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
    <div className="panel" lang={language} dir={language === 'en' ? 'ltr' : 'rtl'}>
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
              <WheelPicker
                label={say('Which {kind}', { kind: say(section.label).toLowerCase() })}
                options={section.options.map((option) => ({
                  id: option.id,
                  label: `${option.label} (${option.size})`,
                  disabled: option.size < QUIZ.optionCount,
                }))}
                value={groupId}
                onChange={(group) => startRound({ group })}
                accent={accent}
                className="max-w-[13rem]"
              />
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
            onRestart={restart}
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
