import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { batchOf } from './journal'
import {
  allowanceLeft, byPlace, createRecitingSession, cutReason, problemOf, queueCheck, readyToSend, recentAsks, spokeSince, surer,
} from './recitingSession'

const ayahs = [{ key: '1:6', from: 17, count: 3 }, { key: '1:7', from: 20, count: 9 }]

describe('sureness by page place', () => {
  it('places each ayah at its words and leaves unreached and mismatched words out', () => {
    expect(byPlace({ '1:6': [0.2, null, 1], '1:7': [1, 1] }, ayahs)).toEqual({ 17: 0.2, 19: 1 })
  })

  it('lets a newer reading of the same recording replace an early guess', () => {
    // An early reading scored a word not said yet; the word was then said wrong.
    const early = byPlace({ '1:7': [1, 1, 0.95, null, null, null, null, null, null] }, ayahs)
    const later = byPlace({ '1:7': [1, 1, 0.02, 1, null, null, null, null, null] }, ayahs)
    expect({ ...early, ...later }[22]).toBe(0.02)
  })

  it('keeps the surer score across recordings, one clipped at its edge does not unsay a word', () => {
    expect(surer({ 28: 1, 20: 0.3 }, { 28: 0.002, 21: 0.5 })).toEqual({ 20: 0.3, 21: 0.5, 28: 1 })
  })
})

describe('cutReason', () => {
  const began = 100000
  it('never cuts before any voice has been heard, even past the max length', () => {
    expect(cutReason(began + 20000, began, 0, 400, 25000)).toBeNull()
    expect(cutReason(began + 30000, began, 0, 400, 25000)).toBeNull()
  })

  it('cuts at a pause after a voice, on the boundary', () => {
    const lastVoice = began + 5000
    expect(cutReason(lastVoice + 399, began, lastVoice, 400, 25000)).toBeNull()
    expect(cutReason(lastVoice + 400, began, lastVoice, 400, 25000)).toBe('pause')
  })

  it('cuts at the max length when voice is continuous, on the boundary', () => {
    const now = began + 25000
    const lastVoice = now - 50 // well inside the pause window
    expect(cutReason(now, began, lastVoice, 400, 25000)).toBe('max')
    expect(cutReason(now - 1, began, lastVoice, 400, 25000)).toBeNull()
  })
})

describe('spokeSince', () => {
  const began = 100000
  it('counts a voice stamped just before began, within the meter lag', () => {
    expect(spokeSince(began - 100, began, 250)).toBe(true)
  })

  it('does not count a voice a full second before began', () => {
    expect(spokeSince(began - 1000, began, 250)).toBe(false)
  })
})

describe('readyToSend', () => {
  it('is false while a reading is already on its way', () => {
    expect(readyToSend(10000, 0, 0, 4000, true, 5, 0)).toBe(false)
  })

  it('is false when there is no new chunk since the last request', () => {
    expect(readyToSend(10000, 0, 0, 4000, false, 3, 3)).toBe(false)
  })

  it('paces by how long the last reading took when that is longer than the step', () => {
    expect(readyToSend(3999, 0, 6000, 4000, false, 5, 0)).toBe(false)
    expect(readyToSend(6000, 0, 6000, 4000, false, 5, 0)).toBe(true)
  })

  it('holds a mid-phrase reading when the ear has no allowance left', () => {
    expect(readyToSend(10000, 0, 0, 4000, false, 5, 0, 1)).toBe(true)
    expect(readyToSend(10000, 0, 0, 4000, false, 5, 0, 0)).toBe(false)
  })
})

describe('allowanceLeft', () => {
  const minute = 60000

  it('counts only the asks of the last minute', () => {
    const asks = [0, 1000, 2000]
    expect(allowanceLeft(3000, asks, 20)).toBe(17)
    // The first has aged out a second before the third does.
    expect(allowanceLeft(minute + 500, asks, 20)).toBe(18)
    expect(allowanceLeft(minute + 2500, asks, 20)).toBe(20)
  })

  it('runs out at the allowance and goes negative past it, because a pause never waits', () => {
    const asks = Array.from({ length: 21 }, (_, i) => i * 100)
    expect(allowanceLeft(3000, asks.slice(0, 20), 20)).toBe(0)
    expect(allowanceLeft(3000, asks, 20)).toBe(-1)
    expect(readyToSend(3000, 0, 0, 3000, false, 5, 0, -1)).toBe(false)
  })

  it('drops the aged-out asks rather than growing without bound', () => {
    expect(recentAsks(minute + 1000, [0, 500, minute])).toEqual([minute])
  })
})

describe('problemOf', () => {
  it('reads no response as the server being unreachable', () => {
    expect(problemOf({ isAxiosError: true }).kind).toBe('unreachable')
  })

  it('reads the dev proxy\'s empty 500 as the server being unreachable', () => {
    expect(problemOf({ isAxiosError: true, response: { status: 500, data: '' } }).kind).toBe('unreachable')
  })

  it('reads a string detail as the server message itself', () => {
    const error = { isAxiosError: true, response: { status: 500, data: { detail: 'reading id abc123 failed' } } }
    expect(problemOf(error)).toEqual({ kind: 'server', text: 'reading id abc123 failed' })
  })

  it('reads a non-string detail, such as a 422 validation array, as a generic server message', () => {
    const error = { isAxiosError: true, response: { status: 422, data: { detail: [{ msg: 'bad' }] } } }
    expect(problemOf(error)).toEqual({ kind: 'server', text: 'The server failed on this reading (error 422).' })
  })

  it('reads a non-axios error as a page bug', () => {
    expect(problemOf(new TypeError('cannot read words of undefined')).kind).toBe('page')
  })
})

describe('queueCheck', () => {
  const job = (window, id, sent = false) => ({ window, id, sent })
  const add = (queue, j, max = 8) => queueCheck(queue, j, max).queue

  it('adds the first check for a recording', () => {
    expect(add([], job(1, 'a'))).toEqual([job(1, 'a')])
  })

  it('replaces a queued but unsent check for the same recording, latest wins', () => {
    const queue = add([], job(1, 'a'))
    expect(add(queue, job(1, 'b'))).toEqual([job(1, 'b')])
  })

  it('collapses an exact duplicate request to one entry', () => {
    let queue = add([], job(1, 'a'))
    queue = add(queue, job(1, 'a'))
    expect(queue).toEqual([job(1, 'a')])
  })

  it('leaves an already-sent check alone and queues the new one after it', () => {
    const queue = [job(1, 'a', true)]
    expect(add(queue, job(1, 'b'))).toEqual([job(1, 'a', true), job(1, 'b')])
  })

  it("keeps a recording's final check even once a later recording queues one", () => {
    const queue = add([], job(1, 'final', true))
    expect(add(queue, job(2, 'a'))).toEqual([job(1, 'final', true), job(2, 'a')])
  })

  it('runs different recordings in the order they queued, without reordering on a later replace', () => {
    let queue = add([], job(1, 'a'))
    queue = add(queue, job(2, 'a'))
    queue = add(queue, job(1, 'b')) // replaces window 1's job in place
    expect(queue.map((q) => q.window)).toEqual([1, 2])
    expect(queue[0].id).toBe('b')
  })
})

describe('queueCheck cap', () => {
  const job = (window, id, sent = false) => ({ window, id, sent })
  const fill = (n) => Array.from({ length: n }, (_, i) => job(i, `j${i}`))

  it('adds freely under the cap', () => {
    const { queue, dropped } = queueCheck(fill(3), job(9, 'new'), 8)
    expect(queue).toHaveLength(4)
    expect(dropped).toBeNull()
  })

  it('adds freely exactly at the cap', () => {
    const { queue, dropped } = queueCheck(fill(7), job(9, 'new'), 8)
    expect(queue).toHaveLength(8)
    expect(dropped).toBeNull()
  })

  it('drops the oldest unsent job past the cap', () => {
    const { queue, dropped } = queueCheck(fill(8), job(9, 'new'), 8)
    expect(queue).toHaveLength(8)
    expect(dropped).toEqual(job(0, 'j0'))
    expect(queue.map((q) => q.id)).not.toContain('j0')
  })

  it('a duplicate request collapsing in place never counts as growth, so nothing is dropped', () => {
    const { queue, dropped } = queueCheck(fill(8), job(3, 'j3'), 8)
    expect(queue).toHaveLength(8)
    expect(dropped).toBeNull()
  })

  it('never drops the in-flight job, even when it is the oldest', () => {
    const queue = [job(0, 'inflight', true), ...fill(8).slice(1)]
    const { queue: next, dropped } = queueCheck(queue, job(9, 'new'), 8)
    expect(next[0]).toEqual(job(0, 'inflight', true))
    expect(dropped).toEqual(job(1, 'j1'))
  })
})

describe('journal batchOf', () => {
  it('takes nothing from an empty queue', () => {
    expect(batchOf([], 20)).toEqual([])
  })

  it('takes every event when under the max', () => {
    const queue = [1, 2, 3]
    expect(batchOf(queue, 20)).toEqual([1, 2, 3])
  })

  it('takes exactly the max when the queue is exactly that long', () => {
    const queue = Array.from({ length: 20 }, (_, i) => i)
    expect(batchOf(queue, 20)).toEqual(queue)
  })

  it('takes only the first max when the queue is longer, keeping an exact duplicate event rather than folding it away', () => {
    const queue = ['dup', 'dup', ...Array.from({ length: 19 }, (_, i) => i)]
    const batch = batchOf(queue, 20)
    expect(batch).toHaveLength(20)
    expect(batch.filter((e) => e === 'dup')).toEqual(['dup', 'dup'])
    expect(batch).not.toContain(18) // the 21st event, left for the next batch
  })
})

/**
 * The whole loop, driven with a scripted recorder and a scripted ear. Each case
 * is a bug this loop has had: which recording an answer belongs to, and what
 * survives a pause, a stop, a jump and a second press.
 */
describe('a reciting session', () => {
  const PAGE = ['الحمد', 'لله', 'رب', 'العالمين', 'الرحمن', 'الرحيم']

  const harness = () => {
    const recorders = []
    const readings = []
    const checks = []
    const notes = []
    const track = { stop: vi.fn() }
    const page = { fusha: true, pageWords: PAGE, ayahs: [] }
    let voice = null
    const deps = {
      canRecord: () => true,
      openMicrophone: async () => ({ getTracks: () => [track] }),
      // The browser's recorder hands over its last piece and then says it
      // stopped, both after stop() returns.
      createRecorder: () => {
        const r = {
          state: 'inactive',
          mimeType: 'audio/webm',
          start() { this.state = 'recording' },
          stop() {
            if (this.state !== 'recording') return
            this.state = 'inactive'
            setTimeout(() => { this.chunk(); this.onstop() }, 0)
          },
          chunk() { this.ondataavailable({ data: new Blob(['x']) }) },
        }
        recorders.push(r)
        return r
      },
      watchForVoice: (_mic, handlers) => { voice = handlers; return () => { voice = null } },
      // Given up on the way axios gives up: rejected as cancelled.
      listen: (_blob, options) => new Promise((resolve, reject) => {
        options.signal.addEventListener('abort', () => reject({ code: 'ERR_CANCELED' }))
        readings.push({ options, answer: (said) => resolve(typeof said === 'string' ? { text: said } : said) })
      }),
      checkReading: (_blob, options) => new Promise((resolve) => {
        checks.push({ options, answer: (sure) => resolve({ sure }) })
      }),
      note: (kind, detail) => notes.push({ kind, ...detail }),
    }
    const session = createRecitingSession({ onChange: () => {}, deps })
    session.update(page)
    const heard = () => {
      const { before, now } = session.view()
      return [...before, ...now.words]
    }
    return {
      session, readings, checks, notes, track, page, heard,
      recorder: () => recorders.at(-1),
      speak: () => voice.onVoice(),
      wait: (ms) => vi.advanceTimersByTimeAsync(ms),
      // Speak, wait out the step, and hand over a piece: a mid-phrase reading.
      // The meter hears the voice on every read while somebody speaks.
      midPhrase: async () => {
        for (let t = 0; t < 3000; t += 100) {
          voice.onVoice()
          await vi.advanceTimersByTimeAsync(100)
        }
        voice.onVoice()
        recorders.at(-1).chunk()
        await vi.advanceTimersByTimeAsync(0)
      },
      // Say nothing past pause-s: the recording is cut and its last reading asked for.
      pause: () => vi.advanceTimersByTimeAsync(700),
      answer: async (i, text) => {
        readings[i].answer(text)
        await vi.advanceTimersByTimeAsync(0)
      },
    }
  }

  beforeEach(() => { vi.useFakeTimers() })
  afterEach(() => { vi.useRealTimers() })

  it('keeps every word of a phrase once it pauses', async () => {
    const h = harness()
    await h.session.start()
    await h.midPhrase()
    await h.answer(0, 'الحمد لله')
    expect(h.session.view().now.words).toEqual(['الحمد', 'لله'])
    await h.pause()
    expect(h.readings).toHaveLength(2)
    await h.answer(1, 'الحمد لله رب العالمين')
    expect(h.session.view().before).toEqual(PAGE.slice(0, 4))
    expect(h.session.view().now.words).toEqual([])
  })

  it('gives up on a reading still out when the phrase ends, and keeps the one taken at the pause', async () => {
    const h = harness()
    await h.session.start()
    await h.midPhrase()
    await h.pause()
    expect(h.notes.map((n) => n.kind)).toContain('reading.aborted')
    // The one given up on answering late changes nothing.
    await h.answer(0, 'الحمد')
    await h.answer(1, 'الحمد لله رب العالمين')
    expect(h.heard()).toEqual(PAGE.slice(0, 4))
  })

  it('joins two phrases without saying the overlap twice', async () => {
    const h = harness()
    await h.session.start()
    await h.midPhrase()
    await h.answer(0, 'الحمد لله رب')
    await h.pause()
    await h.answer(1, 'الحمد لله رب العالمين')
    await h.midPhrase()
    await h.answer(2, 'العالمين الرحمن الرحيم')
    await h.pause()
    await h.answer(3, 'العالمين الرحمن الرحيم')
    expect(h.session.view().before).toEqual(PAGE)
  })

  it('lets the microphone go at once on stop, and still keeps the last reading', async () => {
    const h = harness()
    await h.session.start()
    await h.midPhrase()
    h.session.stop()
    expect(h.session.view().state).toBe('idle')
    expect(h.track.stop).toHaveBeenCalledTimes(1)
    await h.wait(0)
    await h.answer(1, 'الحمد لله رب العالمين')
    expect(h.session.view().before).toEqual(PAGE.slice(0, 4))
    expect(h.session.view().ended).toBe(true)
  })

  it('stops once when stop is pressed twice', async () => {
    const h = harness()
    await h.session.start()
    h.session.stop()
    h.session.stop()
    expect(h.notes.filter((n) => n.kind === 'recite.stop')).toHaveLength(1)
    expect(h.track.stop).toHaveBeenCalledTimes(1)
  })

  it('forgets the recording under way when a start word is pressed mid-recitation, and keeps listening', async () => {
    const h = harness()
    await h.session.start()
    await h.midPhrase()
    h.session.forget()
    await h.wait(0)
    // No last reading is asked for about the old place.
    expect(h.readings).toHaveLength(1)
    expect(h.session.view().state).toBe('listening')
    await h.answer(0, 'الحمد لله')
    expect(h.heard()).toEqual([])
    await h.midPhrase()
    await h.answer(1, 'الرحمن الرحيم')
    expect(h.heard()).toEqual(['الرحمن', 'الرحيم'])
  })

  it('drops a sureness answer about the old place that arrives after a jump', async () => {
    const h = harness()
    h.page.ayahs = [{ key: '1:2', from: 0, count: 4 }]
    await h.session.start()
    h.speak()
    await h.pause()
    await h.answer(0, 'الحمد لله رب العالمين')
    h.session.forget()
    await h.wait(0)
    h.checks[0].answer({ '1:2': [1, 1, 1, 1] })
    await h.wait(0)
    expect(h.session.view().sure).toEqual({ before: {}, now: {} })
    expect(h.session.view().state).toBe('listening')
  })

  it('turns the page without cutting the recording, and carries on from what was said after its last word', async () => {
    const h = harness()
    h.page.ayahs = [{ key: '1:2', from: 0, count: 4 }]
    await h.session.start()
    h.speak()
    await h.pause()
    await h.answer(0, 'الحمد لله رب العالمين الرحمن الرحيم مالك')
    // The next recording is under way, the reciter already on the next page.
    await h.midPhrase()
    const recording = h.recorder()
    h.session.turn(['مالك'])
    h.session.update({ fusha: true, pageWords: ['مالك', 'يوم', 'الدين'], ayahs: [] })
    await h.wait(0)
    expect(recording.state).toBe('recording')
    expect(h.session.view().state).toBe('listening')
    expect(h.session.view().sure).toEqual({ before: {}, now: {} })
    // The old page's check answering late lands nowhere.
    h.checks[0].answer({ '1:2': [0.1, 0.1, 0.1, 0.1] })
    await h.wait(0)
    expect(h.session.view().sure).toEqual({ before: {}, now: {} })
    // The recording under way is read against the new page, after the word
    // carried over from the one that finished the old page.
    await h.answer(1, 'يوم الدين')
    expect(h.heard()).toEqual(['مالك', 'يوم', 'الدين'])
  })

  it('keeps the recording that was going when the page turned, and none of its old-page scores', async () => {
    const h = harness()
    h.page.ayahs = [{ key: '1:2', from: 0, count: 4 }]
    await h.session.start()
    h.speak()
    await h.pause()
    await h.answer(0, 'الحمد لله رب العالمين')
    h.checks[0].answer({ '1:2': [1, 1, 1, 1] })
    await h.wait(0)
    // Into the next page mid-recording; a word of it is also on the old page,
    // so the reading was kept and a check asked about the old page.
    await h.midPhrase()
    await h.answer(1, 'الرحمن')
    expect(h.checks).toHaveLength(2)
    // The reciter pauses: that recording is cut, its last reading asked for,
    // and the page turns before it answers.
    await h.pause()
    h.session.turn([])
    h.session.update({ fusha: true, pageWords: ['الرحمن', 'الرحيم', 'مالك'], ayahs: [{ key: '1:3', from: 0, count: 2 }] })
    expect(h.session.view().now.words).toEqual(['الرحمن'])
    h.checks[1].answer({ '1:2': [0.1, 0.1, 0.1, 0.1] })
    await h.wait(0)
    expect(h.session.view().sure).toEqual({ before: {}, now: {} })
    // Its last reading, whole, still lands, on the new page.
    await h.answer(2, 'الرحمن الرحيم مالك')
    expect(h.heard()).toEqual(['الرحمن', 'الرحيم', 'مالك'])
  })

  it('asks no more sureness checks about a page that is done, so they cannot hold its turn up', async () => {
    const h = harness()
    h.page.ayahs = [{ key: '1:2', from: 0, count: 4 }]
    await h.session.start()
    h.speak()
    await h.pause()
    await h.answer(0, 'الحمد لله رب العالمين')
    expect(h.checks).toHaveLength(1)
    h.session.update({ ...h.page, done: true })
    await h.midPhrase()
    await h.answer(1, 'الرحمن الرحيم')
    expect(h.checks).toHaveLength(1)
    expect(h.session.view().now.words).toEqual(['الرحمن', 'الرحيم'])
  })

  it("takes the server's place: sure elsewhere moves nothing onto the page, home clears it", async () => {
    const h = harness()
    h.page.ayahs = [{ key: '1:2', from: 0, count: 4 }]
    await h.session.start()
    await h.midPhrase()
    expect(h.readings[0].options.near).toBe('1:2-1:2')
    // 3:2 and the start of 2:255 are the same words: not sure, so nothing moves.
    h.readings[0].answer({ text: 'الله لا إله إلا هو الحي القيوم', place: { surah: 3, ayah: 2, sure: false, home: false } })
    await h.wait(0)
    expect(h.session.view().elsewhere).toBeNull()
    expect(h.heard()).toEqual([])
    await h.midPhrase()
    // 6:45 ends with this page's words, and is still not this page.
    h.readings[1].answer({ text: 'فقطع دابر القوم الذين ظلموا والحمد لله رب العالمين', place: { surah: 6, ayah: 45, sure: true, home: false } })
    await h.wait(0)
    expect(h.session.view().elsewhere).toEqual({ surah: 6, ayah: 45 })
    expect(h.heard()).toEqual([])
    await h.midPhrase()
    h.readings[2].answer({ text: 'الحمد لله رب العالمين', place: { surah: 1, ayah: 2, sure: true, home: true } })
    await h.wait(0)
    expect(h.session.view().elsewhere).toBeNull()
    expect(h.heard()).toEqual(['الحمد', 'لله', 'رب', 'العالمين'])
  })

  it('sends an unsure reading in front of the next so it is placed with it, and a home answer clears it', async () => {
    const h = harness()
    h.page.ayahs = [{ key: '1:2', from: 0, count: 4 }]
    const unsure = { surah: 2, ayah: 38, sure: false, home: false }
    await h.session.start()
    await h.midPhrase()
    expect(h.readings[0].options.before).toBe('')
    // Said twelve times in the Qur'an: not sure, and not this page. A reading
    // mid-phrase carries nothing: the one at the pause holds the same words.
    h.readings[0].answer({ text: 'ولا هم', place: unsure })
    await h.wait(0)
    await h.pause()
    expect(h.readings[1].options.before).toBe('')
    h.readings[1].answer({ text: 'ولا هم يحزنون', place: unsure })
    await h.wait(0)
    await h.midPhrase()
    expect(h.readings[2].options.before).toBe('ولا هم يحزنون')
    await h.pause()
    h.readings[3].answer({ text: 'الحمد لله رب العالمين', place: { surah: 1, ayah: 2, sure: true, home: true } })
    await h.wait(0)
    await h.midPhrase()
    expect(h.readings[4].options.before).toBe('')
    // A pause that places nowhere clears a carry too, or an old phrase rides along.
    await h.pause()
    h.readings[5].answer({ text: 'ولا هم يحزنون', place: unsure })
    await h.wait(0)
    await h.midPhrase()
    expect(h.readings[6].options.before).toBe('ولا هم يحزنون')
    await h.pause()
    h.readings[7].answer({ text: 'موسيقى', place: null })
    await h.wait(0)
    await h.midPhrase()
    expect(h.readings[8].options.before).toBe('')
  })

  it("asks no place for a page that is not the Qur'an, and keeps a reading too short to place by its words", async () => {
    const h = harness()
    await h.session.start()
    await h.midPhrase()
    expect(h.readings[0].options.near).toBeUndefined()
    h.readings[0].answer({ text: 'الحمد', place: null })
    await h.wait(0)
    expect(h.heard()).toEqual(['الحمد'])
  })

  it('writes nothing from the last press once the page has been cleared and started again', async () => {
    const h = harness()
    await h.session.start()
    await h.midPhrase()
    h.session.stop()
    await h.wait(0)
    h.session.forget()
    await h.session.start()
    await h.answer(1, 'الحمد لله رب العالمين')
    expect(h.heard()).toEqual([])
    expect(h.session.view().state).toBe('listening')
  })

  it('sends nothing while nobody speaks, and says so once', async () => {
    const h = harness()
    await h.session.start()
    for (let k = 0; k < 5; k += 1) {
      await h.wait(1000)
      h.recorder().chunk()
    }
    expect(h.readings).toHaveLength(0)
    expect(h.notes.filter((n) => n.kind === 'reading.skipped')).toHaveLength(1)
  })

  it('files a sureness answer that arrives after the fold under the words already kept', async () => {
    const h = harness()
    h.page.ayahs = [{ key: '1:2', from: 0, count: 4 }]
    await h.session.start()
    h.speak()
    await h.pause()
    await h.answer(0, 'الحمد لله رب العالمين')
    expect(h.checks).toHaveLength(1)
    h.checks[0].answer({ '1:2': [1, 1, 0.2, 1] })
    await h.wait(0)
    expect(h.session.view().sure).toEqual({ before: { 0: 1, 1: 1, 2: 0.2, 3: 1 }, now: {} })
  })

  it('holds mid-phrase readings once the allowance is spent, but never the one at a pause', async () => {
    const h = harness()
    await h.session.start()
    // Nine phrases, two readings each: the allowance of eighteen, spent.
    for (let k = 0; k < 9; k += 1) {
      await h.midPhrase()
      await h.answer(h.readings.length - 1, 'الحمد لله')
      await h.pause()
      await h.answer(h.readings.length - 1, 'الحمد لله')
    }
    expect(h.readings).toHaveLength(18)
    await h.midPhrase()
    expect(h.readings).toHaveLength(18)
    await h.pause()
    expect(h.readings).toHaveLength(19)
  })
})
