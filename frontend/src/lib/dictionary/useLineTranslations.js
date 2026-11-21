/**
 * Each line of a page translated, a few at a time, by the dictionary's own
 * sentence translation (GET /api/dictionary/sentence): one request a line,
 * kept in the query cache under ['sentence', text], so a line left unchanged
 * when the reader corrects the text is not asked again.
 *
 * A few at a time (dictionary.json page.together), not all at once: the first
 * lines arrive while the rest are asked. Each new line is one model call on the
 * server, and a visitor has ai_per_minute of those (backend/config.py), so a
 * long page runs into "too many" (429) part way. Then every line waits together
 * (page.paused-ms, a gate the workers share, kept across a correction), not
 * each on its own, and asks again: a 429 is never the line's fault, so it is
 * asked page.busy-tries times before it is called failed, long enough for the
 * server's minute to roll over more than once. The line says it is waiting.
 *
 * @returns {Record<string, {state: 'asking'|'paused'|'done'|'failed', data?: object, error?: Error}>}
 *   keyed by the line's text
 */
import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { translateSentence } from '../../api'
import config from '../../config/dictionary.json'
import { hasArabicWord } from '../text/arabicText'

const TOGETHER = config.page.together
const PAUSED_MS = config.page['paused-ms']
const TRIES = config.page['busy-tries']

export const sentenceQuery = (text, ask = translateSentence) => ({
  queryKey: ['sentence', text],
  queryFn: () => ask(text),
  staleTime: Infinity,
  retry: false,
})

const sleep = (ms) => new Promise((wake) => setTimeout(wake, ms))

export function useLineTranslations(lines, { ask = translateSentence, together = TOGETHER, pausedMs = PAUSED_MS, tries = TRIES } = {}) {
  const client = useQueryClient()
  const [found, setFound] = useState({})
  // When the server may be asked again: one gate for every worker, and for the next run after a correction.
  const resume = useRef(0)

  useEffect(() => {
    let live = true
    const queue = [...new Set(lines.map((line) => line.text).filter(hasArabicWord))]
    const note = (text, value) => { if (live) setFound((was) => ({ ...was, [text]: value })) }

    async function one(text) {
      for (let tried = 1; live; tried++) {
        const wait = resume.current - Date.now()
        if (wait > 0) { note(text, { state: 'paused' }); await sleep(wait); if (!live) return }
        note(text, { state: 'asking' })
        try {
          return note(text, { state: 'done', data: await client.fetchQuery(sentenceQuery(text, ask)) })
        } catch (error) {
          if (error?.response?.status !== 429 || tried >= tries) return note(text, { state: 'failed', error })
          resume.current = Math.max(resume.current, Date.now() + pausedMs)
        }
      }
    }
    async function worker() {
      while (live && queue.length) await one(queue.shift())
    }
    for (let i = 0; i < together; i++) worker()
    return () => { live = false }
  }, [lines, client, ask, together, pausedMs, tries])

  return found
}
