/**
 * The microphone, while somebody recites a page, and what the page should show.
 *
 * The page's handle on a reciting session (lib/recitingSession.js), which does
 * the recording, the readings and the checks. This holds only what the session
 * last showed and turns it into marks; the panel that uses it draws them and
 * decides nothing.
 */
import { useEffect, useMemo, useRef, useState } from 'react'

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
  const [view, setView] = useState(EMPTY_VIEW)

  // One session for the life of the page. Making one opens nothing; the
  // microphone waits for start().
  const [session] = useState(() => createRecitingSession({ onChange: setView }))


  // However this page is left, the microphone goes off with it.
  useEffect(() => () => session.dispose(), [session])

  const { state, problem, before, now, ended, sure, checking, elsewhere } = view
  const heard = before.length ? joinWindows(before, now.words) : now.words

  // The page is finished once its last word is in what has already been read
  // for the last time (`before`, folded at a pause), so no later reading can
  // take it back. Marked then from those words alone and as ended: waiting
  // for more words after the last would wait for ever, and anything said
  // since belongs to the next page, even where a word like ٱللَّهِ is on both.
  const final = useMemo(
    () => (before.length ? follow(pageWords, before, { startAt, ended: true }) : null),
    [pageWords, before, startAt],
  )
  const finished = final?.heardTo != null

  // What a recording in progress listens against, without a new session for it:
  // the dialect setting, the words of the page being recited, and whether that
  // page is done.
  useEffect(() => { session.update({ fusha, pageWords, ayahs, done: finished }) }, [session, fusha, pageWords, ayahs, finished])
  // What the finished recordings held after this page's last word goes with
  // the reciter; the recording still going is kept by the session. Read
  // when the page turns, not when it was found finished: the panel waits a
  // moment first, and words said in that moment belong to the next page too.
  const carry = useRef([])
  useEffect(() => { carry.current = finished ? before.slice(final.heardTo) : [] })

  return {
    state,
    problem,
    heard,
    marks: bySound(finished ? final : follow(pageWords, heard, { startAt, ended }), surer(sure.before, sure.now)),
    // Finished and weighed: every check of this page is back. The panel turns
    // the page on this, so the last ayah is marked by sound before it goes.
    finished: finished && checking === 0,
    listening: state === 'listening',
    elsewhere,
    start: session.start,
    stop: session.stop,
    forget: session.forget,
    turn: () => session.turn(carry.current),
  }
}
