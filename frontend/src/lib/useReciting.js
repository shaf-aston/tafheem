/**
 * The microphone, while somebody recites a page, and what the page should show.
 *
 * The page's handle on a reciting session (lib/recitingSession.js), which does
 * the recording, the readings and the checks. This holds only what the session
 * last showed and turns it into marks; the panel that uses it draws them and
 * decides nothing.
 */
import { useEffect, useState } from 'react'

import { bySound, follow, joinWindows } from './follow'
import { createRecitingSession, EMPTY_VIEW, surer } from './recitingSession'
import { useSetting } from './settings'

/**
 * `ayahs` are the page's lines the ear can check by sound, each { key, from,
 * count }: its "surah:ayah", where its words start on the page and how many.
 * Empty for a text the backend has no plain spelling of; marks are then the
 * page's alone.
 */
export function useReciting(pageWords, { startAt = 0, ayahs = [] } = {}) {
  const fusha = useSetting('fusha')
  const level = useSetting('reciting-level')
  const [view, setView] = useState(EMPTY_VIEW)

  // One session for the life of the page. Making one opens nothing; the
  // microphone waits for start().
  const [session] = useState(() => createRecitingSession({ onChange: setView }))

  // What a recording in progress listens against, without a new session for it:
  // the dialect setting, and the words of the page being recited.
  useEffect(() => { session.update({ fusha, pageWords, ayahs }) }, [session, fusha, pageWords, ayahs])

  // However this page is left, the microphone goes off with it.
  useEffect(() => () => session.dispose(), [session])

  const { state, problem, before, now, ended, sure } = view
  const heard = before.length ? joinWindows(before, now.words) : now.words

  return {
    state,
    problem,
    heard,
    marks: bySound(follow(pageWords, heard, { startAt, ended }), surer(sure.before, sure.now), level),
    listening: state === 'listening',
    start: session.start,
    stop: session.stop,
    forget: session.forget,
  }
}
