/**
 * Each line of a page translated, a few at a time, by the dictionary's own
 * sentence translation: a line of a page and a sentence typed into the box get
 * one answer, kept in one cache, so a line left unchanged when the reader
 * corrects the text is not asked again.
 *
 * A few at a time (dictionary.json page.together), not all at once: the first
 * lines arrive while the rest are asked, and a long page stays inside a
 * visitor's share of the translator. When the server says too many at once
 * (429), that line waits (page.paused-ms) and asks again, three times at most,
 * and says it is waiting rather than failing.
 *
 * @returns {Record<string, {state: 'asking'|'paused'|'done'|'failed', data?: object, error?: Error}>}
 *   keyed by the line's text
 */
import { useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { translateSentence } from '../../api'
import config from '../../config/dictionary.json'
import { isArabic } from '../text/arabicText'

const TOGETHER = config.page.together
const PAUSED_MS = config.page['paused-ms']
const TRIES = 3

export const sentenceQuery = (text, ask = translateSentence) => ({
  queryKey: ['sentence', text],
  queryFn: () => ask(text),
  staleTime: Infinity,
  retry: false,
})

export function useLineTranslations(lines, { ask = translateSentence, together = TOGETHER, pausedMs = PAUSED_MS } = {}) {
  const client = useQueryClient()
  const [found, setFound] = useState({})

  useEffect(() => {
    let live = true
    const queue = [...new Set(lines.map((line) => line.text).filter(isArabic))]
    const note = (text, value) => { if (live) setFound((was) => ({ ...was, [text]: value })) }

    async function one(text) {
      for (let tries = 1; live; tries++) {
        note(text, { state: 'asking' })
        try {
          return note(text, { state: 'done', data: await client.fetchQuery(sentenceQuery(text, ask)) })
        } catch (error) {
          if (error?.response?.status !== 429 || tries >= TRIES) return note(text, { state: 'failed', error })
          note(text, { state: 'paused' })
          await new Promise((wake) => setTimeout(wake, pausedMs))
        }
      }
    }
    async function worker() {
      while (live && queue.length) await one(queue.shift())
    }
    for (let i = 0; i < together; i++) worker()
    return () => { live = false }
  }, [lines, client, ask, together, pausedMs])

  return found
}
