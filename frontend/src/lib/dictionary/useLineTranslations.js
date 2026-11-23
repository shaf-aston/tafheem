/**
 * Each line of a page translated by the dictionary's sentence translation, a batch
 * of lines a request (POST /api/dictionary/sentences: one model call on the server
 * for the whole batch, so a 120-line page is 15 calls, not 120). Each answer is
 * kept in the query cache under ['sentence', text], so a line left unchanged when
 * the reader corrects the text is not asked again.
 *
 * A few batches at a time (dictionary.json page.together), in page order, so the
 * first lines arrive while the rest are asked. A visitor has ai_per_minute model
 * calls (backend/config.py), so a very long page can still run into "too many"
 * (429). Then every batch waits together (page.paused-ms, a gate the workers
 * share, kept across a correction) and asks again, until the gate is truly past:
 * a 429 is never the lines' fault, so a batch is asked page.busy-tries times
 * before its lines are called failed. The lines say they are waiting.
 *
 * @returns {Record<string, {state: 'asking'|'paused'|'done'|'failed', data?: object, error?: Error}>}
 *   keyed by the line's text
 */
import { useEffect, useRef, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'

import { translateSentences } from '../../api'
import config from '../../config/dictionary.json'
import { hasArabicWord } from '../text/arabicText'

const BATCH = config.page.batch
const TOGETHER = config.page.together
const PAUSED_MS = config.page['paused-ms']
const TRIES = config.page['busy-tries']

const key = (text) => ['sentence', text]
const sleep = (ms) => new Promise((wake) => setTimeout(wake, ms))

export function useLineTranslations(lines, { ask = translateSentences, batch = BATCH, together = TOGETHER, pausedMs = PAUSED_MS, tries = TRIES } = {}) {
  const client = useQueryClient()
  const [found, setFound] = useState({})
  // When the server may be asked again: one gate for every worker, and for the next run after a correction.
  const resume = useRef(0)

  // The lines' texts, not the array: a parent that builds a new array of the same lines each render asks nothing again.
  const wantedKey = [...new Set(lines.map((line) => line.text).filter(hasArabicWord))].join('\n')

  useEffect(() => {
    let live = true
    const note = (texts, value) => {
      if (live) setFound((was) => ({ ...was, ...Object.fromEntries(texts.map((text) => [text, value(text)])) }))
    }
    const wanted = wantedKey ? wantedKey.split('\n') : []
    const known = wanted.filter((text) => client.getQueryData(key(text)))
    note(known, (text) => ({ state: 'done', data: client.getQueryData(key(text)) }))
    const asking = wanted.filter((text) => !known.includes(text))
    const queue = []
    for (let i = 0; i < asking.length; i += batch) queue.push(asking.slice(i, i + batch))

    async function one(texts) {
      for (let tried = 1; live; tried++) {
        // Loop, not one wait: another batch's 429 may move the gate on while this one sleeps.
        while (live && resume.current > Date.now()) {
          note(texts, () => ({ state: 'paused' }))
          await sleep(resume.current - Date.now())
        }
        if (!live) return
        note(texts, () => ({ state: 'asking' }))
        try {
          const answers = await ask(texts)
          texts.forEach((text, i) => client.setQueryData(key(text), answers[i]))
          return note(texts, (text) => ({ state: 'done', data: answers[texts.indexOf(text)] }))
        } catch (error) {
          if (error?.response?.status !== 429 || tried >= tries) return note(texts, () => ({ state: 'failed', error }))
          resume.current = Math.max(resume.current, Date.now() + pausedMs)
        }
      }
    }
    async function worker() {
      while (live && queue.length) await one(queue.shift())
    }
    for (let i = 0; i < together; i++) worker()
    return () => { live = false }
  }, [wantedKey, client, ask, batch, together, pausedMs, tries])

  return found
}
