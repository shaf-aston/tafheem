/**
 * The recording studio. One word at a time: Record (Space) → hear it back →
 * Keep (Enter) or Redo (R). Kept takes go to POST /api/recordings, which trims
 * them; backend/scripts/speech/export_recordings.py then makes them the "person" voice.
 *
 * The key is the server's recorder_key, kept in this browser only.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import { canRecord, CANNOT_RECORD, createRecorder, openMicrophone, refusal } from '../lib/speech/microphone'

const KEY = 'recorder-key'
const BATCH = 20
const remembered = () => { try { return localStorage.getItem(KEY) ?? '' } catch { return '' } }

async function call(path, key, init = {}) {
  const r = await fetch(`/api/recordings${path}`, { ...init, headers: { 'X-Recorder-Key': key } })
  if (r.status === 403) throw new Error('Wrong key.')
  if (r.status === 404) throw new Error('The studio is off on this server (no recorder_key set).')
  if (!r.ok) throw new Error(`The server said ${r.status}.`)
  return r.json()
}

export default function Studio() {
  const [key, setKey] = useState(remembered)
  const [typed, setTyped] = useState('')
  const [queue, setQueue] = useState([])
  const [counts, setCounts] = useState(null)
  const [take, setTake] = useState(null)        // { blob, url }
  const [state, setState] = useState('idle')    // idle | recording | sending
  const [error, setError] = useState('')
  const recorder = useRef(null)
  const word = queue[0]

  const load = useCallback(() => {
    if (!key) return
    call(`/todo?limit=${BATCH}`, key).then(
      (got) => { setQueue(got.words); setCounts({ left: got.left, done: got.done }); setError('') },
      (e) => setError(e.message),
    )
  }, [key])
  useEffect(load, [load])

  const record = useCallback(async () => {
    if (state === 'recording') { recorder.current?.stop(); return }
    if (!canRecord()) { setError(CANNOT_RECORD); return }
    try {
      const stream = await openMicrophone()
      const rec = createRecorder(stream)
      const parts = []
      rec.ondataavailable = (e) => parts.push(e.data)
      rec.onstop = () => {
        stream.getTracks().forEach((t) => t.stop())
        const blob = new Blob(parts, { type: rec.mimeType })
        setTake((old) => { if (old) URL.revokeObjectURL(old.url); return { blob, url: URL.createObjectURL(blob) } })
        setState('idle')
      }
      recorder.current = rec
      rec.start(); setState('recording'); setError('')
    } catch (e) { setError(refusal(e)) }
  }, [state])

  const keep = useCallback(async () => {
    if (!take || !word || state !== 'idle') return
    setState('sending')
    const body = new FormData()
    body.append('text', word.ar)
    body.append('audio', take.blob, 'take.webm')
    try {
      await call('', key, { method: 'POST', body })
      URL.revokeObjectURL(take.url); setTake(null)
      setCounts((c) => c && { left: c.left - 1, done: c.done + 1 })
      setQueue((q) => q.slice(1))
      if (queue.length <= 1) load()
    } catch (e) { setError(e.message) }
    setState('idle')
  }, [take, word, state, key, queue.length, load])

  const redo = useCallback(() => { if (take) URL.revokeObjectURL(take.url); setTake(null) }, [take])

  useEffect(() => {
    const onKey = (e) => {
      if (e.target.tagName === 'INPUT') return
      if (e.code === 'Space') { e.preventDefault(); record() }
      else if (e.key === 'Enter') keep()
      else if (e.key === 'r' || e.key === 'R') redo()
    }
    addEventListener('keydown', onKey)
    return () => removeEventListener('keydown', onKey)
  }, [record, keep, redo])

  if (!key) {
    return (
      <main className="mx-auto max-w-md p-4 pt-16 text-[var(--text)]">
        <h1 className="mb-4 text-xl">Recording studio</h1>
        <form onSubmit={(e) => { e.preventDefault(); try { localStorage.setItem(KEY, typed) } catch { /* this visit only */ } setKey(typed) }}>
          <input type="password" value={typed} onChange={(e) => setTyped(e.target.value)} placeholder="Recorder key"
            className="w-full rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)] p-3" />
        </form>
      </main>
    )
  }

  const button = 'rounded-[var(--radius-md)] border border-[var(--border-hi)] bg-[var(--surface-hi)] px-5 py-3 disabled:opacity-40'
  return (
    <main className="mx-auto flex min-h-dvh max-w-xl flex-col items-center gap-6 p-4 pt-12 text-center text-[var(--text)]">
      {counts && <p className="text-sm text-[var(--text-dim)]">{counts.done} kept · {counts.left} to go</p>}
      {error && <p className="text-[var(--danger)]">{error}</p>}
      {word ? (
        <>
          <p lang="ar" dir="rtl" className="arabic-lg" style={{ fontSize: '4rem' }}>{word.ar}</p>
          <p className="text-[var(--text-dim)]">{word.en}</p>
          <div className="flex flex-wrap justify-center gap-3">
            <button className={button} onClick={record} disabled={state === 'sending'}>
              {state === 'recording' ? 'Stop (Space)' : 'Record (Space)'}
            </button>
            <button className={button} onClick={keep} disabled={!take || state !== 'idle'}>Keep (Enter)</button>
            <button className={button} onClick={redo} disabled={!take}>Redo (R)</button>
          </div>
          {take && <audio key={take.url} src={take.url} controls autoPlay />}
          <p className="text-sm text-[var(--text-faint)]">Say the word once, clearly, with every ending. Quiet before and after is trimmed.</p>
        </>
      ) : counts && <p>Every word is recorded.</p>}
    </main>
  )
}
