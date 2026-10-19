import { useEffect, useMemo } from 'react'
import { useQuery, useQueryClient } from '@tanstack/react-query'

import { fetchReviewItems } from './progress'
import { buildQuestion, DIRECTIONS, makeRandom } from './quiz'
import { allWordsQuery, bankInfo, moduleFor, QUIZ, sentencesQuery, wordsFor } from './quizBanks'
import { ayahQueries } from './quizAyah'

/**
 * The question on screen and the words it is drawn from, for what `setup`
 * (useQuizSetup) is testing and the `round` ({ seed, asked, at }) being played.
 * A pure derivation of the two: the same setup and round always ask the same
 * question, so moving on is one change to the round.
 */
export function useQuizQuestion(setup, round) {
  const { language, direction, bankId, bank, groupId } = setup
  const client = useQueryClient()

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
  const everyWord = useQuery({ ...allWordsQuery, enabled: bank.live })

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
  // Told apart from a short surah: this set has words, they are just not
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

  return { words, question, questionCount, enough, noneInLanguage, owed, dialect: info.data?.dialect }
}
