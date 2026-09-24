/**
 * Hearing an ayah recited. The only module that knows where a recording lives.
 *
 * The fast path, and it is fast because of what it does not do. There is no
 * call to this app's backend, no API to ask which file to play, and no account
 * or key anywhere: the address of a recording can be worked out from the ayah's
 * own numbers, so pressing play is one request, straight to the file, and the
 * browser starts playing while the rest of it is still arriving. Measured
 * against EveryAyah: about 110ms before the first sound could start, and the
 * whole of Ayat al-Kursi, the longest ayah in the Qur'an, arrives in a third of
 * a second.
 *
 * Who recites and where their recordings sit is data/reciters.json, never here.
 *
 * One player for the whole app, not one per ayah. A reading view holds 286
 * ayahs, and 286 audio elements is 286 things the browser has to keep; more to
 * the point, starting a second ayah while the first is talking should stop the
 * first, which it cannot do if each one owns its own player and knows nothing
 * of the others.
 */
import config from '../data/reciters.json'

export const RECITERS = config.reciters

const pad = (n) => String(n).padStart(3, '0')

/** Where one reciter's recording of one ayah lives. */
export function ayahAudioUrl(surah, ayah, reciterId) {
  const reciter = RECITERS.find((r) => r.id === reciterId) ?? RECITERS[0]
  return config.url
    .replace('{folder}', reciter.folder)
    .replace('{surah}', pad(surah))
    .replace('{ayah}', pad(ayah))
}

let player = null
let listeners = new Set()
let playingUrl = ''

/** The one audio element, made on first use. Never on a server render. */
function audio() {
  if (!player) {
    player = new Audio()
    // Nothing is fetched until something is played. The prefetch below is the
    // deliberate exception, and it uses its own throwaway element.
    player.preload = 'none'
    const changed = () => {
      if (player.paused || player.ended) playingUrl = ''
      listeners.forEach((tell) => tell(playingUrl))
    }
    player.addEventListener('play', changed)
    player.addEventListener('pause', changed)
    player.addEventListener('ended', changed)
    player.addEventListener('error', () => { playingUrl = ''; changed() })
  }
  return player
}

/** Play this ayah, stopping whatever else was playing. Returns a promise that
 *  rejects only if the browser refused to play at all. */
export function play(url) {
  const a = audio()
  if (a.src !== url) {
    a.src = url
    a.load()
  }
  playingUrl = url
  listeners.forEach((tell) => tell(playingUrl))
  startClock()
  return a.play()
}

export function stop() {
  if (!player) return
  player.pause()
  player.currentTime = 0
}

/** Which url is playing right now, '' for none. */
export const nowPlaying = () => playingUrl

/**
 * How far into the recording we are, told every 50ms while something plays.
 *
 * 50ms rather than every drawn frame, because the only thing watching this is
 * a word lighting up, and a word is the better part of a second long: twenty
 * looks a second is already far finer than the thing being shown. The browser's
 * own timeupdate event fires about four times a second, which is too coarse to
 * land on the right word.
 *
 * The clock runs only while something is playing and only while someone is
 * listening, so a page of a hundred ayahs costs nothing until one is pressed.
 */
let clockWatchers = new Set()
let clock = 0

function beat() {
  const at = player ? player.currentTime * 1000 : 0
  clockWatchers.forEach((tell) => tell(playingUrl, at))
  if (!playingUrl) { clearInterval(clock); clock = 0 }
}

function startClock() {
  if (!clock && playingUrl && clockWatchers.size) clock = setInterval(beat, 50)
}

export function watchProgress(tell) {
  clockWatchers.add(tell)
  startClock()
  return () => {
    clockWatchers.delete(tell)
    if (!clockWatchers.size) { clearInterval(clock); clock = 0 }
  }
}

/** Told on every start and stop. Returns its own unsubscribe. */
export function watch(tell) {
  listeners.add(tell)
  return () => listeners.delete(tell)
}

/**
 * Ask the browser to start fetching a recording before anyone presses play.
 *
 * The recording of an ayah being looked at is very likely to be wanted, and a
 * few hundred kilobytes fetched early is the difference between a press that
 * plays and a press that waits. A throwaway element rather than the shared
 * player, so this can never interrupt something already playing; the browser
 * caches by url, so the real play reuses what this fetched.
 */
const fetched = new Set()

export function prefetch(url) {
  if (typeof Audio === 'undefined' || !url || fetched.has(url)) return
  // Once per address per visit. The pointer crossing a row of ayahs would
  // otherwise ask for the same file on every entry, and a panel that prefetches
  // on mount asks again on every re-render.
  fetched.add(url)
  const ghost = new Audio()
  ghost.preload = 'auto'
  ghost.src = url
}

/** Test seam: forget the shared player, as a fresh page would have. */
export function reset() {
  clearInterval(clock)
  clock = 0
  clockWatchers = new Set()
  fetched.clear()
  player = null
  listeners = new Set()
  playingUrl = ''
}
