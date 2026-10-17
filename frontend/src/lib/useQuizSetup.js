import { useMemo } from 'react'
import { useQuery } from '@tanstack/react-query'

import { DIRECTIONS, MEANINGS } from './quiz'
import { BANKS, groupsFor, QUIZ, WHOLE_SET_SCOPES } from './quizBanks'
import { useRemembered, useRememberedFlag } from './useRemembered'

// What each remembered control is allowed to be, taken from the same tables the
// controls themselves are drawn from, so a set or a direction can never be
// added in one place and forgotten in the other.
const BANK_IDS = Object.keys(BANKS)
const DIRECTION_IDS = Object.keys(DIRECTIONS)
const LANGUAGE_IDS = Object.keys(MEANINGS)

// The two ways round a language can be asked. Derived rather than remembered, so
// there is no such thing as a language holding a direction from another one.
const directionsIn = (language) => [`ar-${language}`, `${language}-ar`]

/**
 * What the Quiz tab is testing: the meaning's language, the direction, the set
 * of words and the cut of it. All remembered, all checked against what can be
 * chosen now. `change` applies one choice from the controls ({ bank }, { scope },
 * { group }, { direction } or { language }); starting a fresh round on it is
 * the caller's, because a round is not this hook's.
 */
export function useQuizSetup() {
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
  const bank = BANKS[bankId]

  const groupsQuery = useQuery({
    queryKey: ['quiz-groups', bankId],
    queryFn: () => groupsFor(bankId),
  })
  const groups = useMemo(() => groupsQuery.data ?? [], [groupsQuery.data])

  // The cut, remembered as the pair it is: kind of cut, then the one inside it.
  // Both are checked against what this set actually offers, so a surah
  // remembered under the Qur'anic set cannot quietly decide what Everyday asks:
  // a set with no cuts allows only the empty one.
  const scopeIds = useMemo(
    () => [...WHOLE_SET_SCOPES.map((s) => s.id), ...groups.map((s) => s.id)],
    [groups],
  )
  const groupIds = useMemo(
    () => (bank.grouped
      ? [
        ...WHOLE_SET_SCOPES.map((s) => s.group),
        ...groups.flatMap((s) => s.options.map((o) => o.id)),
      ]
      : ['']),
    [bank.grouped, groups],
  )
  const [scope, setScope] = useRemembered('quiz-scope', scopeIds)
  const [groupId, setGroupId] = useRemembered('quiz-group', groupIds)
  const section = groups.find((s) => s.id === scope) ?? null

  const change = (choice) => {
    if ('bank' in choice) { setBankId(choice.bank); setGroupId(''); setScope('all') }
    // Switching to Surah starts on the first surah rather than on nothing: the
    // control should never leave the quiz in a state you have to fix yourself.
    if ('scope' in choice) {
      setScope(choice.scope)
      const whole = WHOLE_SET_SCOPES.find((s) => s.id === choice.scope)
      const next = groups.find((s) => s.id === choice.scope)
      setGroupId(whole ? whole.group : next ? next.options[0].id : '')
    }
    if ('group' in choice) setGroupId(choice.group)
    if ('direction' in choice) setDirection(choice.direction)
    if ('language' in choice) setLanguage(choice.language)
  }

  return { language, direction, directions, bankId, bank, autoNext, setAutoNext, groups, scope, groupId, section, change }
}
