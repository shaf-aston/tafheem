/**
 * Say an Arabic word aloud. The only module that knows which voices exist.
 *
 * Voices are tried in speak.json's order and the first that starts plays. A
 * voice that cannot say a word, or whose file will not load, passes it on, so a
 * word is never silent while any voice can reach it.
 *
 * An accent (a Colloquial dialect's key) asks the server for that dialect's own
 * speaker, and skips the reciters: a Qur'an reciter is not a Damascene.
 *
 * Recordings share lib/ayahAudio.js's one player, so a word stops an ayah and
 * an ayah stops a word: never two sounds at once.
 */
import config from '../speak.json'
import { play, stop as stopAudio, watch } from './ayahAudio'

let recordings = null
async function recordingOf(text) {
  recordings ??= fetch(config.voices.recorded.map)
    .then((r) => (r.ok ? r.json() : Promise.reject(new Error(r.status))))
    .catch(() => { recordings = null; return {} })  // asked again next press, not given up on
  const map = await recordings
  return Object.hasOwn(map, text) ? config.voices.recorded.host + map[text] : null
}

/** Starts the file; `done` settles when it stops. Rejects if it never started. */
async function playFile(url) {
  if (!url) throw new Error('no recording')
  await play(url)
  return {
    done: new Promise((finish) => {
      const off = watch((current) => { if (current !== url) { off(); finish() } })
    }),
  }
}

const serverUrl = (text, accent) => `${config.voices.server.url}?text=${encodeURIComponent(text)}&voice=${config.voices.server.version}${accent ? `&accent=${encodeURIComponent(accent)}` : ''}`

/** The device's voices. Many browsers list none until they have loaded, so wait once for them. */
async function deviceVoices() {
  const synth = globalThis.speechSynthesis
  const first = synth.getVoices()
  if (first.length) return first
  await new Promise((resolve) => {
    const timer = setTimeout(done, config.voices.browser.voicesTimeoutMs)
    function done() { clearTimeout(timer); synth.removeEventListener?.('voiceschanged', done); resolve() }
    synth.addEventListener?.('voiceschanged', done)
  })
  return synth.getVoices()
}

/** The best Arabic voice: a named favourite, else one on the device, else any. Null if none. */
export function pickVoice(voices, cfg = config) {
  const arabic = [...voices].filter((v) => /^ar([-_]|$)/i.test(v.lang))
  for (const name of cfg.voices.browser.preferred) {
    const hit = arabic.find((v) => v.name.toLowerCase().includes(name.toLowerCase()))
    if (hit) return hit
  }
  return arabic.find((v) => v.localService) ?? arabic[0] ?? null
}

/** Each voice resolves to { done } once sound has started, rejects if it cannot. */
const VOICES = {
  recorded: async (text, accent) => playFile(accent ? null : await recordingOf(text)),
  server: (text, accent) => playFile(serverUrl(text, accent)),
  browser: async (text) => {
    const synth = globalThis.speechSynthesis
    if (!synth) throw new Error('no device voice')
    // Never guess a voice: an Android with no Arabic pack spells the letters in English.
    const voice = pickVoice(await deviceVoices(), config)
    if (!voice) throw new Error('no Arabic device voice')
    return new Promise((started, fail) => {
      stopAudio()
      synth.cancel()
      const line = new SpeechSynthesisUtterance(text)
      line.voice = voice
      line.lang = voice.lang
      line.rate = config.voices.browser.rate
      let finish
      const done = new Promise((resolve) => { finish = resolve })
      // A voice that is listed but will not start never says so.
      const silent = setTimeout(() => { synth.cancel(); fail(new Error('device voice never started')) }, config.voices.browser.startTimeoutMs)
      line.onstart = () => { clearTimeout(silent); started({ done }) }
      line.onend = finish
      // Cancelled or interrupted: before starting it failed, after it simply stopped.
      line.onerror = (e) => { clearTimeout(silent); fail(e); finish() }
      synth.speak(line)
    })
  },
}

/**
 * Say `text`, in `accent` when given. Resolves as soon as a voice starts, to { id, done },
 * where `done` settles when it falls quiet. Rejects if no voice could say it.
 */
let latest = 0

export async function speak(text, { accent } = {}) {
  const turn = ++latest
  for (const id of config.order) {
    try {
      const { done } = await VOICES[id](text, accent)
      return { id, done }
    } catch (err) {
      // Cut off by a newer press or an ayah, not unable: the next voice must not talk over it.
      if (turn !== latest || err?.name === 'AbortError') throw Object.assign(new Error('Interrupted'), { interrupted: true })
    }
  }
  throw new Error('No voice could say this')
}

/**
 * Have the server make `text`'s voice now, so the press that follows plays at
 * once (a new phrase takes the server ~1.7s, a made one ~0.06s). Recorded words
 * need nothing. Once per text; a failure just leaves the press to make it.
 */
const prepared = new Set()
export async function prepare(text, { accent } = {}) {
  const key = `${accent ?? ''}|${text}`
  if (prepared.has(key)) return
  prepared.add(key)
  if (!accent && await recordingOf(text)) return
  // Marked as ahead, so a word actually pressed is made before it on the server.
  fetch(serverUrl(text, accent), { headers: { 'X-Speak-Ahead': '1' } }).catch(() => prepared.delete(key))
}

export function stop() {
  stopAudio()
  globalThis.speechSynthesis?.cancel()
}

/** Test seam: forget the loaded recording map. */
export function reset() {
  recordings = null
}
