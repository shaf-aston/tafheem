/**
 * One recitation: the microphone, the recordings, the readings and the
 * sureness checks, with no React in it.
 *
 * lib/useReciting.js is the page's handle on this and holds nothing but the
 * view it is given. Kept apart so the part that has broken most, which
 * recording an answer belongs to, can be driven by tests with a scripted
 * recorder instead of a browser (recitingSession.test.js); the outside world
 * comes in through `deps`, and the real one is the default.
 *
 * Why it sends the whole recording each time, not the last few seconds
 * -------------------------------------------------------------------
 * A recording is only whole from its beginning: cutting the middle out of one
 * leaves something no engine can read. Everything said so far is always a real
 * recording, and sending it again costs nothing to be right about, because what
 * comes back is the whole thing read afresh with more of the sentence behind
 * it. That is how a mark corrects itself: nothing is remembered, the page is
 * simply drawn from the newest reading.
 *
 * A recording is not allowed to grow forever. At each pause, or after `window-s`
 * seconds with none, a fresh one starts, and what was heard up to then is kept
 * in front of it, joined so that words in both are said once. An hour of
 * reciting is many short recordings, never one long one.
 *
 * Nothing is recorded until the reader asks, the microphone is let go the
 * moment they stop, and it stops itself after a long silence, which is the same
 * promise ui/MicButton.jsx makes for a single spoken word.
 */
import * as api from '../api'
import dictationConfig from '../dictation.json'
import config from '../recite.json'
import * as dictation from './dictation'
import { isOfPage, joinWindows, wordsHeard } from './follow'
import * as journal from './journal'
import * as microphone from './microphone'

const STEP_MS = config['step-s'] * 1000
const TICK_MS = config['tick-s'] * 1000
const WINDOW_MS = config['window-s'] * 1000
const PAUSE_MS = config['pause-s'] * 1000
const CHECK_TIMEOUT_MS = config['check-timeout-s'] * 1000
const CHECK_QUEUE_MAX = config['check-queue-max']
const ASKS_PER_MINUTE = config['asks-per-minute']
// How far the voice meter can lag a cut and still count as "spoken in this
// window": the same tick length the meter itself reads at.
const LEVEL_LAG_MS = dictationConfig['level-check-ms']

/**
 * Why a recording should stop itself: a pause after a phrase, or long enough
 * is long enough. Null before any voice has been heard in this window at
 * all, on purpose: a reciter thinking before starting is never cut, that is
 * left to the microphone's own quiet-stop.
 */
export const cutReason = (now, began, lastVoice, pauseMs, windowMs) => {
  if (lastVoice < began) return null
  if (now - lastVoice >= pauseMs) return 'pause'
  if (now - began >= windowMs) return 'max'
  return null
}

/** Whether a voice has been heard since this recording began, allowing for the meter's own lag. */
export const spokeSince = (lastVoice, began, lagMs) => lastVoice >= began - lagMs

/**
 * The asks of the last minute, newest last, with the older ones dropped. What
 * the ear's allowance is counted against; see allowanceLeft.
 */
export const recentAsks = (now, asks) => asks.filter((at) => now - at < 60000)

/**
 * How many more readings may be asked for right now. Both kinds are counted,
 * the mid-phrase ones and the one at each pause, because the ear's allowance
 * does not tell them apart. Only the mid-phrase ones give way to it.
 */
export const allowanceLeft = (now, asks, perMinute) => perMinute - recentAsks(now, asks).length

/** Whether it is time to ask for a reading: free, something new to send, paced by how long the last one took, and inside the ear's allowance. */
export const readyToSend = (now, asked, took, stepMs, busy, chunksLen, sent, left = Infinity) =>
  !busy && chunksLen > sent && now - asked >= Math.max(stepMs, took) && left > 0

/**
 * What to tell a reciter when a reading fails, and how to log it: a network
 * drop, a server crash, and a bug in the page after the answer arrived are
 * told apart rather than shown as one grey "did not come back".
 */
export const problemOf = (error) => {
  if (!error?.isAxiosError) {
    return { kind: 'page', text: 'The page failed to show that reading. It has been logged.' }
  }
  // A body that is not the backend's JSON came from the dev proxy, which
  // answers 500 with nothing when the backend is down or restarting.
  const fromProxy = error.response && typeof error.response.data !== 'object'
  if (!error.response || fromProxy) {
    return { kind: 'unreachable', text: "The app's server did not answer. It may be restarting; the next phrase will try again." }
  }
  const detail = error.response.data?.detail
  if (typeof detail === 'string') return { kind: 'server', text: detail }
  return { kind: 'server', text: `The server failed on this reading (error ${error.response.status}).` }
}

/** One reading's per-ayah answer, keyed by page place; words it did not reach are left out. */
export const byPlace = (answer = {}, ayahs) => {
  const out = {}
  for (const { key, from, count } of ayahs) {
    // A count that differs is an ayah the two spellings split into different
    // words; its words cannot be told apart, so it keeps the page's marks.
    const scores = answer[key]
    if (scores?.length !== count) continue
    scores.forEach((score, k) => {
      if (score != null) out[from + k] = score
    })
  }
  return out
}

/** The surer of two recordings' scores for each page place. */
export const surer = (a, b) => {
  const out = { ...a }
  for (const [at, score] of Object.entries(b)) out[at] = Math.max(score, out[at] ?? 0)
  return out
}

/**
 * What a newly-finished words reading does to the sureness checks waiting to
 * be sent: at most one is ever in flight (the session's own runner enforces
 * that), so this is only about what waits.
 *
 * A queued job not yet sent is replaced by a newer one for the same recording,
 * latest wins, because a later reading holds more of the sound; two identical
 * jobs queued back to back collapse the same way, to one. A job already sent
 * is left alone, the same choice already made for words: nothing here aborts
 * an in-flight check for a newer one. A different recording's job is never
 * touched, so recordings are checked in the order they finished, even a
 * recording's own final check past a later recording's first.
 *
 * Past `max` entries the oldest not-yet-sent job is dropped to make room: a
 * check nobody has asked for yet is worth less than one already on its way,
 * so the in-flight job at the front, when it is sent, is never the one
 * dropped. Returns the dropped job too, so the caller can journal it.
 */
export const queueCheck = (queue, job, max) => {
  const at = queue.findIndex((q) => q.window === job.window && !q.sent)
  const next = at === -1 ? [...queue, job] : [...queue.slice(0, at), job, ...queue.slice(at + 1)]
  if (next.length <= max) return { queue: next, dropped: null }
  const drop = next.findIndex((q) => !q.sent)
  if (drop === -1) return { queue: next, dropped: null }
  return { queue: [...next.slice(0, drop), ...next.slice(drop + 1)], dropped: next[drop] }
}

/** What a session shows before anything has been said. */
export const EMPTY_VIEW = {
  state: 'idle',
  problem: '',
  // Two halves on purpose: the recordings already finished, and the reading of
  // the one still going. A new reading replaces the second half rather than
  // piling onto it, which is what lets a mark change its mind.
  before: [],
  // Whose words these are, as well as what they are. Recordings overlap: the
  // last reading of one is still being read when the next has begun, and on a
  // slow ear that overlap is most of a recording. Without a name on them, the
  // older recording finishing would clear the newer one's words off the page,
  // and a perfect recitation of al-Fatihah ended with one word showing.
  now: { from: 0, words: [] },
  ended: false,
  // How sure the ear has been of each page word, by its place on the page, in
  // the same two halves. Within a recording the newest reading wins: it holds
  // more of the sound, and an early reading scores words not said yet, up to
  // 0.1 for one word in six (measured on 69 cut recordings), which kept for
  // good would pass that word however it was then said. Across recordings the
  // surer one wins: a word is said once, and one clipped at a recording's
  // edge should not unsay it.
  sure: { before: {}, now: {} },
}

const REAL = {
  canRecord: microphone.canRecord,
  openMicrophone: microphone.openMicrophone,
  createRecorder: microphone.createRecorder,
  watchForVoice: dictation.watchForVoice,
  listen: api.listen,
  checkReading: api.checkReading,
  note: journal.note,
}

/**
 * `update(page)` tells the session what it is listening against, and the
 * newest one is read at the moment each value is needed, never kept per
 * recording: { fusha, pageWords, ayahs }. `ayahs` are the page's lines the ear
 * can check by sound, each { key, from, count }: its "surah:ayah", where its
 * words start on the page and how many; empty for a text the backend has no
 * plain spelling of, and marks are then the page's alone. `onChange` gets a new
 * view object every time anything shown changes.
 */
export function createRecitingSession({ onChange, deps = {} }) {
  const { canRecord, openMicrophone, createRecorder, watchForVoice, listen, checkReading, note } = { ...REAL, ...deps }

  let view = EMPTY_VIEW
  let page = { fusha: true, pageWords: [], ayahs: [] }
  const set = (patch) => {
    view = { ...view, ...(typeof patch === 'function' ? patch(view) : patch) }
    onChange(view)
  }

  let going = false
  // Which press of the button a recording belongs to. A reading still on its
  // way when the reader stops and starts again would otherwise fold the old
  // recitation's words into the new one; a stale one writes nothing. Stopping
  // alone does not end a session: the page stops itself a second after the
  // last word, and that word's reading is still on its way.
  let session = 0
  // This recitation's own id, for lib/journal.js and the server's X-Reading-Id
  // log to line up on: short, random, made fresh each time start() is pressed.
  let sessionId = ''
  // How many recordings this page has made. Only ever goes up, and only names
  // them; nothing is kept per recording but its own words.
  let windows = 0
  // The last recording thrown away by a start word pressed mid-recitation. Its
  // sound was said about the old place, so nothing of it may land on the new.
  let forgotten = 0
  let mic = null
  let recorder = null
  // The reading on its way, if there is one, so the last one can be waited for.
  let sending = null
  // How long the last reading actually took. This is the pacing: the ear on
  // this machine takes seconds and the ear on a server takes a fifth of one,
  // and neither number belongs in a config file, because it is also how busy
  // this machine is right now.
  let took = 0
  // When each reading of the last minute was asked for. The ear's allowance is
  // spent per key, not per recording, so this belongs to the recitation and not
  // to the recording inside it.
  let asks = []
  let cutTimer = null
  // When a voice was last heard, so a recording can end at the pause after a phrase.
  let lastVoice = 0
  let stopWatching = null

  // Sureness checks, queued and sent one at a time: see queueCheck. Words never
  // wait on this, a check is only ever fired and forgotten from send() below.
  let checkQueue = []
  let checkBusy = false

  /**
   * Send the front of the queue, if the ear is free and there is one. A
   * check that does not answer within check-timeout-s is given up on rather
   * than left to hold checkBusy true forever: the abort is the job's own,
   * held so start() can also give up on it when a new session begins.
   */
  const pumpChecks = () => {
    if (checkBusy) return
    const job = checkQueue[0]
    if (!job) return
    checkBusy = true
    job.sent = true
    job.abort = new AbortController()
    const timer = setTimeout(() => job.abort.abort(), CHECK_TIMEOUT_MS)
    note('check.sent', { session: sessionId, reading: job.reading })
    checkReading(job.blob, { heard: job.heard, check: job.ayahs, reading: job.reading, signal: job.abort.signal })
      .then(({ sure: scored }) => {
        note('check.answered', { session: sessionId, reading: job.reading })
        job.apply(scored)
      })
      .catch((error) => {
        if (job.abort.signal.aborted) {
          note('check.failed', { session: sessionId, reading: job.reading, kind: 'timeout' })
          return
        }
        const { text } = problemOf(error)
        note('check.failed', { session: sessionId, reading: job.reading, message: text })
      })
      .finally(() => {
        clearTimeout(timer)
        checkQueue = checkQueue.slice(1)
        checkBusy = false
        pumpChecks()
      })
  }

  /** Queue a sureness check, replacing a still-queued one for the same recording. */
  const enqueueCheck = (job) => {
    const was = checkQueue
    const { queue: next, dropped } = queueCheck(was, job, CHECK_QUEUE_MAX)
    if (dropped) {
      note('check.dropped', { session: sessionId, reading: dropped.reading })
    } else if (next.length === was.length) {
      // A queued job that was replaced in place never gets sent; say so.
      const at = next.findIndex((q, i) => q !== was[i])
      if (at !== -1) note('check.aborted', { session: sessionId, reading: was[at].reading })
    }
    checkQueue = next
    pumpChecks()
  }

  /** Let the microphone go and settle every mark still waiting for words. */
  const release = () => {
    going = false
    clearInterval(cutTimer)
    stopWatching?.()
    stopWatching = null
    mic?.getTracks().forEach((track) => track.stop())
    mic = null
    set({ ended: true, state: 'idle' })
  }

  /** One recording, sent as it grows, and the next one after it. */
  const record = () => {
    const made = createRecorder(mic)
    recorder = made
    // This recording's own sound. Not shared with the next one: the last
    // reading of a recording is still on its way when the next has begun.
    const chunks = []
    const began = Date.now()
    const mine = session
    // Which recording this is, so a reading is only ever written or cleared by
    // the recording it belongs to.
    const thisWindow = windows + 1
    windows = thisWindow
    const live = () => session === mine && thisWindow > forgotten
    // How much of the recording the last request carried, so the same sound is
    // never paid for twice.
    let sent = 0
    // When a request last went for this recording. The recording's own start,
    // not zero: from zero the very first piece of sound of every recording was
    // always "long enough ago" and a reading went at once, which is the
    // reading the pause a second later throws away.
    let asked = began
    // What the ear made of this recording, latest reading, for folding away.
    let latest = []
    // How to give up on this recording's reading when it is out of date. This
    // recording's own, not the page's: shared, each recording's stop killed
    // the *previous* recording's settling reading, which is the one reading
    // whose words are kept, and a perfect al-Fatihah ended with a blank page.
    let giveUp = null
    // Which reading of this window a request is, so a failure or an answer
    // can be journalled under the id the server saw. Only counted up when a
    // request is actually sent, not on every skipped tick.
    let seq = 0
    // Whether "no voice yet" has already been journalled for this window, so
    // a silent stretch logs once rather than on every free tick.
    let skipNoted = false
    // Whether this recording's words have already been folded into `before`
    // (see onstop). A sureness check answers after the words that asked for it
    // did, sometimes after that fold has already happened, so this is what
    // tells its result which half of `sure` to land in.
    let folded = false

    const send = async (last = false) => {
      // Sound nobody spoke into is never sent: the ear here spends seconds
      // reading a silent snippet twice to say it was silent.
      // lastVoice can lag one meter tick behind a cut made mid-speech; the next
      // tick catches it, and the chunk after that is sent.
      if (!spokeSince(lastVoice, began, LEVEL_LAG_MS)) {
        if (!skipNoted) {
          note('reading.skipped', { session: sessionId, window: thisWindow })
          skipNoted = true
        }
        return
      }
      sent = chunks.length
      asked = Date.now()
      // Counted whether it waited for the allowance or not: a reading at a
      // pause never waits, but it is spent all the same.
      asks = [...recentAsks(asked, asks), asked]
      seq += 1
      const reading = `${sessionId}-${thisWindow}-${seq}`
      const blob = new Blob(chunks, { type: made.mimeType })
      note('reading.sent', { session: sessionId, reading, bytes: blob.size, last })
      const stopper = new AbortController()
      giveUp = stopper
      const job = (async () => {
        let heard
        try {
          heard = await listen(blob, {
            recite: true,
            fusha: page.fusha,
            signal: stopper.signal,
            reading,
          })
        } catch (error) {
          // A reading we gave up on is not a failure and has nothing to say.
          if (stopper.signal.aborted || error?.code === 'ERR_CANCELED') {
            note('reading.aborted', { session: sessionId, reading })
            return
          }
          // A failed reading is not worth stopping a recitation for: the next
          // is seconds away and holds the same words.
          const { kind, text } = problemOf(error)
          if (live()) set({ problem: text })
          note('reading.failed', { session: sessionId, reading, kind, status: error?.response?.status, message: text })
          return
        }
        try {
          const words = wordsHeard(heard.text)
          // A window with nothing of this page in it is the room, not the
          // reciter. Letting one through put موسيقى on the page as a word said.
          if (!live()) return
          const ofPage = isOfPage(words, page.pageWords)
          if (ofPage) {
            latest = words
            set((was) => (was.now.from > thisWindow ? {} : { now: { from: thisWindow, words } }))
            // Marks are drawn from the words at once; how sure the ear is of
            // each one is scored separately and applied when it comes back,
            // never waited for here.
            const checkAyahs = page.ayahs
            if (checkAyahs.length && heard.text) {
              enqueueCheck({
                window: thisWindow,
                reading,
                blob,
                heard: heard.text,
                ayahs: checkAyahs.map((line) => line.key),
                sent: false,
                apply: (scored) => {
                  if (!live()) return
                  const placed = byPlace(scored, checkAyahs)
                  set(({ sure }) => ({
                    sure: folded
                      ? { ...sure, before: surer(sure.before, placed) }
                      : { ...sure, now: { ...sure.now, ...placed } },
                  }))
                },
              })
            }
          }
          set({ problem: '' })
          note('reading.answered', {
            session: sessionId,
            reading,
            ms: Date.now() - asked,
            chars: heard.text?.length || 0,
            words: words.length,
            kept: ofPage,
          })
        } catch (error) {
          // A bug in the page's own code after a good answer, not a network or
          // server failure: told apart so it is never shown as "did not come back".
          const { kind, text } = problemOf(error)
          if (live()) set({ problem: text })
          note('reading.failed', {
            session: sessionId,
            reading,
            kind,
            message: text,
            stack: String(error?.stack || '').slice(0, 2000),
          })
        }
      })()
      sending = job
      await job
      took = Date.now() - asked
      if (giveUp === stopper) giveUp = null
      if (sending === job) sending = null
    }

    made.ondataavailable = (event) => {
      if (event.data.size) chunks.push(event.data)
      // One request at a time, and no request that is going to be wasted.
      //
      // A reading part way through a recording is only worth asking for if it
      // comes back while that recording is still going. When the ear is slower
      // than that, the recording has already ended by the time it answers and
      // the reading taken at the pause, which holds every word this one held,
      // replaces it unread. Eight readings were being asked for where four
      // were wanted, and the four that mattered queued behind the four that
      // did not: a mark took eighteen seconds to appear instead of five.
      //
      // So: wait for the ear to be free, and then for as long as the last
      // reading actually took, never less than step-s. On a quick ear that is
      // step-s and readings keep flowing; on this machine it is five seconds
      // or so, which for an ayah-length recording means the only reading asked
      // for is the one at the pause, which is the one that settles the marks.
      //
      // And inside the ear's allowance: going over it is a refusal, not a slow
      // answer, and it rests the fast ear for a minute. The reading at a pause
      // is never held back for it (see asks-per-minute); this one is.
      const at = Date.now()
      const left = allowanceLeft(at, asks, ASKS_PER_MINUTE)
      if (readyToSend(at, asked, took, STEP_MS, !!sending, chunks.length, sent, left)) send()
    }

    made.onstop = async () => {
      // The next recording starts now, before any reading comes back. Waiting
      // for the ear first left the microphone live with nobody recording, for
      // as long as a reading took: nothing at a fifth of a second on Groq,
      // three to five seconds of every ayah on the ear here.
      if (going) record()
      // The reading on its way is of this same recording, one piece short, and
      // the one below holds every word it holds. Waiting for it to come back
      // before asking the question that settles the marks cost a whole
      // reading's seconds, three to five of them on the ear here, every time a
      // reciter paused. So it is given up on rather than waited for.
      giveUp?.abort()
      // Thrown away by a jump: its last reading would only be paid for and dropped.
      if (thisWindow <= forgotten) return
      // Then the last reading of this one. Dropping it cost two words of
      // al-Fatihah for good: the window was folded away holding a reading that
      // stopped short.
      await sending
      await send(true)
      // Settled, so it is folded into what came before and the live reading
      // starts from nothing. One step, so no word is ever counted twice.
      if (!live()) return
      // The live half is cleared only if what is showing is still this
      // recording's. Its scores are folded into `before` either way, which
      // loses nothing: the surer of the two always wins there.
      set((was) => ({
        before: joinWindows(was.before, latest),
        now: was.now.from === thisWindow ? { from: thisWindow, words: [] } : was.now,
        sure: { before: surer(was.sure.before, was.sure.now), now: {} },
      }))
      // From here on, this recording's words are `before`'s, not `now`'s; a
      // check that answers after this point (see `send`'s `apply`) must land there too.
      folded = true
      if (!going) release()
    }

    made.start(TICK_MS)
    // Stop, which starts the next one, at the pause after a phrase, or when
    // long enough is long enough. Cut at a pause, every recording starts on a
    // whole word; cut on the clock, the word under the cut was lost from both.
    const timer = setInterval(() => {
      const now = Date.now()
      const reason = cutReason(now, began, lastVoice, PAUSE_MS, WINDOW_MS)
      if (made.state === 'recording' && reason) {
        clearInterval(timer)
        note('window.cut', { session: sessionId, window: thisWindow, why: reason, seconds: (now - began) / 1000 })
        made.stop()
      }
    }, PAUSE_MS / 2)
    cutTimer = timer
  }

  /**
   * Stop, and let the microphone go now rather than when the last reading
   * comes back.
   *
   * Both, in this order and every time it is pressed. Waiting for the recording
   * to finish before releasing left the microphone on: press once and it kept
   * recording and sending, and it took three presses to stop, which for a
   * microphone is a promise broken. The last reading is still sent, because
   * stopping the recorder is what asks for it, but nothing waits on it.
   */
  const stop = (why = 'button') => {
    // The panel also calls this when nothing is recording (a page change);
    // only a real stop is worth a line.
    if (going) note('recite.stop', { session: sessionId, why })
    going = false
    if (recorder?.state === 'recording') recorder.stop()
    release()
  }

  /**
   * Throw away everything heard, so the page starts blank again.
   *
   * Its own call, and not something start() does for you, because whether
   * pressing record again carries on the same recitation or begins it afresh
   * is the reader's choice and cannot be made in here. The panel that owns
   * that setting calls this; it also calls it whenever the page or the word to
   * start on changes, which is never a choice, because what was heard was said
   * about somewhere else.
   */
  const forget = () => {
    // A stopped recording's last reading is still on its way and would write
    // the old page back over the blank one. Only once stopped: a start word
    // pressed mid-recitation forgets too, and must keep hearing the recording.
    if (!going) session += 1
    // Still recording: the recording under way holds words said about the old
    // place, so it is dropped and cut now, and the next begins on the new one.
    else {
      forgotten = windows
      clearInterval(cutTimer)
      if (recorder?.state === 'recording') recorder.stop()
    }
    set({ before: [], now: { from: windows, words: [] }, sure: { before: {}, now: {} }, ended: false })
  }

  const start = async () => {
    set({ problem: '', ended: false })
    if (!canRecord()) {
      set({ state: 'refused', problem: 'This browser cannot record.' })
      return
    }
    try {
      mic = await openMicrophone()
      going = true
      session += 1
      // A check still in flight belongs to the recitation that just ended;
      // waiting out its timeout would hold the new session's own checks
      // behind it. Queued-but-unsent ones are simply stale.
      checkQueue[0]?.abort?.abort()
      checkQueue = []
      sessionId = Math.random().toString(36).slice(2, 10)
      note('recite.start', { session: sessionId })
      // Nothing said for long enough is a microphone left on by mistake.
      // Patient, because a breath between ayahs is not the end.
      stopWatching = watchForVoice(mic, {
        onVoice: () => { lastVoice = Date.now() },
        onQuiet: () => stop('quiet'),
        patient: true,
      })
      set({ state: 'listening' })
      record()
    } catch {
      set({ state: 'refused', problem: 'The microphone was not allowed.' })
      note('mic.refused', {})
    }
  }

  /** However the page is left, the microphone goes off with it; nothing still on its way may write. */
  const dispose = () => {
    if (going) note('recite.stop', { session: sessionId, why: 'page left' })
    going = false
    session += 1
    clearInterval(cutTimer)
    stopWatching?.()
    if (recorder?.state === 'recording') recorder.stop()
    mic?.getTracks().forEach((track) => track.stop())
  }

  const update = (next) => { page = next }

  return { start, stop, forget, dispose, update, view: () => view }
}
