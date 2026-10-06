/**
 * Say an Arabic word aloud. The only module that knows which voices exist.
 *
 * Voices are tried in speak.json's order and the first that starts plays. A
 * voice that cannot say a word, or whose file will not load, passes it on, so a
 * word is never silent while any voice can reach it.
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

const serverUrl = (text) => `${config.voices.server.url}?text=${encodeURIComponent(text)}&voice=${config.voices.server.version}`

/** Each voice resolves to { done } once sound has started, rejects if it cannot. */
const VOICES = {
  recorded: async (text) => playFile(await recordingOf(text)),
  server: (text) => playFile(serverUrl(text)),
  browser: (text) => new Promise((started, fail) => {
    const synth = globalThis.speechSynthesis
    if (!synth) return fail(new Error('no device voice'))
    stopAudio()
    synth.cancel()
    const line = new SpeechSynthesisUtterance(text)
    line.lang = config.voices.browser.lang
    line.rate = config.voices.browser.rate
    let finish
    const done = new Promise((resolve) => { finish = resolve })
    // A phone with no Arabic voice never starts and never says so.
    const silent = setTimeout(() => { synth.cancel(); fail(new Error('device voice never started')) }, config.voices.browser.startTimeoutMs)
    line.onstart = () => { clearTimeout(silent); started({ done }) }
    line.onend = finish
    // Cancelled or interrupted: before starting it failed, after it simply stopped.
    line.onerror = (e) => { clearTimeout(silent); fail(e); finish() }
    synth.speak(line)
  }),
}

/**
 * Say `text`. Resolves as soon as a voice starts, to { id, done },
 * where `done` settles when it falls quiet. Rejects if no voice could say it.
 */
let latest = 0

export async function speak(text) {
  const turn = ++latest
  for (const id of config.order) {
    try {
      const { done } = await VOICES[id](text)
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
export async function prepare(text) {
  if (prepared.has(text)) return
  prepared.add(text)
  if (await recordingOf(text)) return
  fetch(serverUrl(text)).catch(() => prepared.delete(text))
}

export function stop() {
  stopAudio()
  globalThis.speechSynthesis?.cancel()
}

/** Test seam: forget the loaded recording map. */
export function reset() {
  recordings = null
}
