/**
 * Which ear hears the Qur'an better, counted rather than guessed.
 *
 * One misheard word found by accident says nothing about the next thousand. So
 * this reads real recitation of real ayahs through every engine we could use,
 * marks each one with the page's own follower, and counts what a reader would
 * have seen: words called wrong, words called missed, words invented. The
 * number, not an impression, is what picks the engine.
 *
 *   RECITATION_GROQ_API_KEY=... RECITATION_DEEPGRAM_API_KEY=... npx vitest run scripts/ears.test.js
 *
 * A local engine can be added to the same run: EARS_LOCAL_URL points at a
 * running backend's /api/listen (e.g. http://127.0.0.1:8011/api/listen) and
 * EARS_LOCAL_NAME names it, so two different local models keep separate
 * cached readings instead of overwriting each other's.
 *
 * That is also how to judge an ear whose key lives in .env and should stay
 * there: start the backend with RECITATION_EARS naming one engine (hosted,
 * letters or here), point EARS_LOCAL_URL at it, and the backend reads its own
 * key through its own env module. One pass per engine, each named.
 *
 * It costs money and minutes for the cloud ears, so the whole file is skipped
 * unless at least one ear has something to run with, and it is never part of
 * `npm test`.
 *
 * Ayahs are taken from the middle of a surah on purpose: the recordings of a
 * first ayah often carry the basmala, which is in the sound and not in the
 * printed line, and that would be counted as words invented by the engine.
 */
import { existsSync, readFileSync, writeFileSync } from 'node:fs'

import { describe, expect, it } from 'vitest'

import { localHears } from './ears-local'
import { score } from './ears-score'

// Every reading ever paid for, kept. Trying a different marking rule against the
// same recitations is then free and instant, and the engines are asked once.
// A kept reading is either a bare string (every reading before timing was
// tracked) or `{text, ms}`; `textOf`/timing below read both shapes so the old
// cache keeps working without a migration.
const HEARD = new URL('./ears-heard.json', import.meta.url)
const REPORT = new URL('./ears-report.txt', import.meta.url)
const kept = existsSync(HEARD) ? JSON.parse(readFileSync(HEARD, 'utf8')) : {}
const heardOf = (entry) => (typeof entry === 'string' ? entry : entry?.text)

const GROQ = process.env.RECITATION_GROQ_API_KEY
const DEEPGRAM = process.env.RECITATION_DEEPGRAM_API_KEY
const LOCAL_URL = process.env.EARS_LOCAL_URL
const LOCAL_NAME = process.env.EARS_LOCAL_NAME
if (LOCAL_URL && !LOCAL_NAME) {
  // Two local models sharing the default name would silently overwrite each
  // other's cached readings under the same key. Naming the ear is one env var;
  // making it required costs one line and removes the mistake entirely.
  throw new Error('EARS_LOCAL_URL is set but EARS_LOCAL_NAME is not - name the model, e.g. EARS_LOCAL_NAME=local-quran')
}

/**
 * Mid-surah ayahs, short and long, plain and heavily assimilated, two from
 * every surah that has two of between five and twenty words. Thirty-six ayahs
 * of one reciter was too thin to trust: one misheard word moved the score by a
 * third of a percent, and no number said whether a fast or a quiet voice is
 * heard worse. Generated once from backend/data/quran/imlaei.json, so every
 * pair exists, and checked once against every reciter below (1,050 of 1,050).
 */
const AYAHS = [
  [1, 7], [2, 42], [2, 127], [3, 104], [4, 38], [5, 30],
  [5, 69], [6, 78], [7, 39], [7, 104], [8, 38], [9, 32],
  [10, 28], [10, 60], [11, 69], [12, 20], [13, 13], [13, 26],
  [14, 15], [15, 17], [15, 49], [16, 65], [17, 25], [18, 25],
  [18, 62], [19, 50], [20, 37], [20, 79], [21, 60], [22, 16],
  [23, 29], [23, 68], [24, 29], [25, 17], [25, 42], [26, 113],
  [27, 23], [28, 18], [28, 47], [29, 37], [30, 14], [31, 8],
  [31, 18], [32, 8], [33, 18], [33, 43], [34, 30], [35, 9],
  [36, 21], [36, 48], [37, 75], [38, 15], [38, 43], [39, 46],
  [40, 17], [41, 11], [41, 29], [42, 32], [43, 20], [43, 49],
  [44, 29], [45, 9], [46, 7], [46, 19], [47, 23], [48, 8],
  [49, 4], [49, 8], [50, 10], [51, 23], [51, 39], [52, 31],
  [53, 11], [54, 11], [54, 31], [55, 41], [56, 41], [56, 62],
  [57, 9], [58, 10], [59, 8], [59, 17], [60, 6], [61, 4],
  [61, 9], [62, 7], [63, 3], [64, 5], [64, 11], [65, 8],
  [66, 5], [67, 7], [67, 16], [68, 17], [69, 11], [69, 24],
  [70, 34], [71, 6], [72, 7], [72, 16], [73, 11], [74, 25],
  [74, 43], [75, 16], [76, 7], [77, 27], [77, 38], [78, 35],
  [79, 16], [79, 26], [80, 34], [81, 24], [82, 6], [82, 17],
  [83, 17], [84, 7], [85, 8], [85, 10], [86, 4], [87, 7],
  [87, 13], [88, 7], [89, 9], [90, 5], [90, 14], [91, 14],
  [92, 11], [92, 19], [93, 4], [95, 4], [96, 11], [96, 14],
  [97, 3], [98, 4], [98, 5], [99, 7], [100, 9], [101, 4],
  [102, 5], [103, 3], [104, 4], [106, 4], [107, 3], [107, 5],
  [109, 4], [110, 2], [111, 2], [111, 5], [113, 3], [113, 4],
]

/**
 * Seven voices, slow and fast, measured and quick. An ear that hears Alafasy
 * perfectly and Ghamadi badly reads as one good average unless the reciters
 * are counted apart, which is the whole reason for more than one.
 *
 * EARS_RECITERS=Husary_64kbps,Ghamadi_40kbps narrows a run to a few of them,
 * so the hour this takes can be spent in pieces.
 */
const RECITERS = (process.env.EARS_RECITERS || [
  'Alafasy_64kbps',
  'Husary_64kbps',
  'Minshawy_Murattal_128kbps',
  'Abdul_Basit_Murattal_64kbps',
  'Abdurrahmaan_As-Sudais_64kbps',
  'Ghamadi_40kbps',
  'Hudhaify_64kbps',
].join(',')).split(',').filter(Boolean)

/**
 * Every recording this run judges: each ayah above, in each voice above.
 * EARS_LIMIT=3 keeps only the first few ayahs, which is how a change to this
 * file is proved in a minute instead of finding out an hour in.
 */
const LIMIT = Number(process.env.EARS_LIMIT) || AYAHS.length
const CLIPS = RECITERS.flatMap((reciter) => AYAHS.slice(0, LIMIT).map((ayah) => ({ reciter, ayah })))

const pad = (n, w) => String(n).padStart(w, '0')

/** Where one ear's reading of one recording is kept. The ear's name never has a
 *  space in it, which is what lets the name be read back off the front. */
const keyOf = (name, { reciter, ayah }) => `${name} ${reciter} ${ayah.join(':')}`

const audioOf = async ({ reciter, ayah: [surah, ayah] }) => {
  const url = `https://everyayah.com/data/${reciter}/${pad(surah, 3)}${pad(ayah, 3)}.mp3`
  const got = await fetch(url)
  if (!got.ok) throw new Error(`no audio for ${reciter} ${surah}:${ayah}`)
  return Buffer.from(await got.arrayBuffer())
}

/**
 * The printed words of an ayah, from the copy this project already holds.
 *
 * It used to ask api.alquran.cloud, one request per surah. At thirty-six ayahs
 * from a dozen surahs that worked; at a hundred and fifty from a hundred it is
 * refused as too many requests and the whole run dies before it listens. The
 * file is also the *right* text: imlaei is the plain vowelled spelling the ear
 * writes and the page checks against, where Uthmani counts right words wrong.
 */
const QURAN = JSON.parse(readFileSync(new URL('../../backend/data/quran/imlaei.json', import.meta.url), 'utf8'))
const textOf = async ([surah, ayah]) => {
  const text = QURAN[`${surah}:${ayah}`]
  if (!text) throw new Error(`no text for ${surah}:${ayah} in backend/data/quran/imlaei.json`)
  return text
}

/** Groq, as the app calls it today. */
const groqHears = async (mp3) => {
  const form = new FormData()
  form.append('file', new Blob([mp3], { type: 'audio/mpeg' }), 'a.mp3')
  form.append('model', 'whisper-large-v3-turbo')
  form.append('language', 'ar')
  const got = await fetch('https://api.groq.com/openai/v1/audio/transcriptions', {
    method: 'POST', headers: { Authorization: `Bearer ${GROQ}` }, body: form,
  })
  const body = await got.json()
  if (!got.ok) throw new Error(body.error?.message || got.status)
  return body.text ?? ''
}

/** Deepgram, one whole recording at a time, as a plain request. */
const deepgramHears = (model) => async (mp3) => {
  const got = await fetch(`https://api.deepgram.com/v1/listen?model=${model}&language=ar`, {
    method: 'POST',
    headers: { Authorization: `Token ${DEEPGRAM}`, 'Content-Type': 'audio/mpeg' },
    body: mp3,
  })
  const body = await got.json()
  if (!got.ok) throw new Error(body.err_msg || got.status)
  return body.results.channels[0].alternatives[0].transcript ?? ''
}

/**
 * Deepgram listening as the recitation happens, which is a different thing from
 * the same engine reading a finished recording, and the only one worth judging:
 * it is what the page would use. Sound goes up in small pieces at the speed it
 * would be spoken, and the readings it settles on are joined into one.
 *
 * The key travels as the socket's protocol rather than a header, because a
 * browser and node both refuse headers on a socket, and it saves a library.
 */
const deepgramLive = async (mp3) => {
  const url = 'wss://api.deepgram.com/v1/listen?model=nova-3&language=ar&endpointing=500'
  const ws = new WebSocket(url, ['token', DEEPGRAM])
  ws.binaryType = 'arraybuffer'
  const said = []
  const over = new Promise((done, fail) => {
    ws.onerror = () => fail(new Error('the socket would not open'))
    ws.onclose = () => done(said.join(' '))
    ws.onmessage = ({ data }) => {
      const what = JSON.parse(data)
      const text = what?.channel?.alternatives?.[0]?.transcript
      if (what.is_final && text) said.push(text)
    }
  })
  await new Promise((open, fail) => { ws.onopen = open; ws.onerror = fail })
  // At the speed the words were actually said, which for these recordings is
  // 64 kilobits a second, so eight hundred bytes is a tenth of a second of
  // sound. Sending five times that fast lost a word between one reading and the
  // next all the way down the surah, and the loss was the rig's, not the
  // engine's: a microphone can never hand it sound faster than it is spoken.
  const step = 800
  for (let at = 0; at < mp3.length; at += step) {
    ws.send(mp3.subarray(at, at + step))
    await new Promise((wait) => setTimeout(wait, 100))
  }
  ws.send(JSON.stringify({ type: 'CloseStream' }))
  return over
}

const AVAILABLE_CLOUD = {
  groq: Boolean(GROQ),
  'deepgram-nova-3': Boolean(DEEPGRAM),
  'deepgram-whisper': Boolean(DEEPGRAM),
  'deepgram-live': Boolean(DEEPGRAM),
}
// A prior run's local ear (a different model, a different EARS_LOCAL_NAME) left
// its readings in the cache under its own name, which never appears in this
// run's env. Without pulling those names in here, the scoring loop below never
// visits them and their 36 cached readings are never printed, however complete
// the cache is. Any key prefix that isn't one of the four cloud names is a past
// local ear; the live LOCAL_NAME (this run's) joins that set too.
const CACHED_LOCAL = new Set(
  Object.keys(kept)
    .map((k) => k.slice(0, k.indexOf(' ')))
    .filter((n) => !(n in AVAILABLE_CLOUD))
)
if (LOCAL_NAME) CACHED_LOCAL.add(LOCAL_NAME)

const EARS = {
  groq: groqHears,
  'deepgram-nova-3': deepgramHears('nova-3'),
  'deepgram-whisper': deepgramHears('whisper-large'),
  'deepgram-live': deepgramLive,
  // A cached-only local ear (not this run's LOCAL_NAME) has no URL to call and
  // is never fetched fresh - AVAILABLE below is false for it, so this function
  // is only reachable as a bug, and throwing says so loudly instead of quietly
  // hitting the live backend under the wrong ear's name.
  ...Object.fromEntries([...CACHED_LOCAL].map((n) => [
    n,
    n === LOCAL_NAME && LOCAL_URL ? localHears(LOCAL_URL) : () => { throw new Error(`${n} has no live URL this run`) },
  ])),
}
// Whether each ear has a live credential this run; a cached ear with none is
// still scored below (from CACHED_LOCAL/kept), it just cannot fetch a new
// reading.
const AVAILABLE = {
  ...AVAILABLE_CLOUD,
  ...Object.fromEntries([...CACHED_LOCAL].map((n) => [n, n === LOCAL_NAME && Boolean(LOCAL_URL)])),
}
// A down or 503 local backend would otherwise cost 30/60/90/120s of backoff
// per ayah and die inside the timeout before the report is ever written; the
// local ear gets one try and fails loudly instead.
const NO_BACKOFF = new Set(LOCAL_URL ? [LOCAL_NAME] : [])

// Nothing to ask and nothing already asked: only then is there no run. With
// readings in the cache the whole table can be rebuilt without a credential,
// which is what happens after a change to how a reading is marked.
describe.skipIf(!GROQ && !DEEPGRAM && !LOCAL_URL && !Object.keys(kept).length)('how well each ear hears real recitation', () => {
  it('counts what a reader would have seen', async () => {
    const printed = new Map()
    for (const { ayah } of CLIPS) {
      if (!printed.has(ayah.join(':'))) printed.set(ayah.join(':'), await textOf(ayah))
    }

    const blank = () => ({ words: 0, wrong: 0, check: 0, missed: 0, extra: 0, quiet: 0, failed: 0, ms: 0, timed: 0 })
    const totals = {}
    const perReciter = {}
    const notes = []
    let freshCount = 0

    const running = Object.entries(EARS).filter(([name]) => (
      // Neither a live credential nor a prior reading: this ear has nothing to
      // print and an all-zero row would read as a perfect score, not "unrun".
      AVAILABLE[name] || CLIPS.some((c) => kept[keyOf(name, c)] !== undefined)
    ))
    for (const [name] of running) {
      totals[name] = blank()
      perReciter[name] = Object.fromEntries(RECITERS.map((r) => [r, blank()]))
    }

    // Recording by recording, not ear by ear: the mp3 is fetched once and every
    // ear judges that same sound, instead of a thousand downloads per ear.
    for (const clip of CLIPS) {
      const ayahKey = clip.ayah.join(':')
      let sound
      for (const [name, hears] of running) {
        const available = AVAILABLE[name]
        const sum = totals[name]
        const mine = perReciter[name][clip.reciter]
        const key = keyOf(name, clip)
        let entry = kept[key]
        let said = heardOf(entry)
        // An empty reading is retried, not frozen: it may be a request that
        // failed to reach any words rather than a genuinely silent ayah, and
        // the backend's own untrimmed retry already covers real silence.
        if ((said === undefined || said === '') && available) {
          // Only now is the recording worth downloading, and only once however
          // many ears still need it.
          if (sound === undefined) sound = await audioOf(clip)
          const began = Date.now()
          const attempts = NO_BACKOFF.has(name) ? 1 : 5
          let fresh
          // Both cloud engines refuse a burst of requests, and the first run of
          // this lost a third of its readings that way and printed a table
          // that looked like an answer. A refusal is waited out, and if it
          // still will not answer the ayah is counted as unread rather than as
          // read badly, so a broken run can never read as a verdict.
          for (let go = 0; go < attempts && fresh === undefined; go += 1) {
            try {
              fresh = await hears(sound)
            } catch (err) {
              if (go === attempts - 1) {
                sum.failed += 1
                if (NO_BACKOFF.has(name)) {
                  throw new Error(`${name} could not be reached (${err.message}); check EARS_LOCAL_URL and the backend before re-running`)
                }
                break
              }
              await new Promise((wait) => setTimeout(wait, 30_000 * (go + 1)))
            }
          }
          if (fresh === undefined) continue
          said = fresh
          entry = { text: said, ms: Date.now() - began }
          kept[key] = entry
          // Not after every single reading: the cache is one file holding every
          // reading ever paid for, and rewriting all of it four thousand times
          // in a run costs more than the listening does. Losing the last few of
          // a crashed run only costs those few again.
          if ((freshCount += 1) % 25 === 0) writeFileSync(HEARD, JSON.stringify(kept, null, 1))
        }
        if (said === undefined) continue
        if (typeof entry === 'object' && entry?.ms !== undefined) {
          sum.ms += entry.ms
          sum.timed += 1
          mine.ms += entry.ms
          mine.timed += 1
        }
        const one = score(printed.get(ayahKey), said)
        for (const k of ['words', 'wrong', 'check', 'missed', 'extra', 'quiet']) {
          sum[k] += one[k]
          mine[k] += one[k]
        }
        if (one.wrong || one.missed || one.extra || one.quiet) {
          notes.push(`${name} ${clip.reciter} ${ayahKey}  wrong ${one.wrong} missed ${one.missed} extra ${one.extra}\n    said: ${said}`)
        }
      }
    }
    writeFileSync(HEARD, JSON.stringify(kept, null, 1))

    const HEAD = `${'ear'.padEnd(18)} ${'words'.padStart(5)} ${'wrong'.padStart(6)} ${'check'.padStart(6)} ${'missed'.padStart(7)} ${'extra'.padStart(6)} ${'quiet'.padStart(6)} ${'unread'.padStart(7)} ${'error'.padStart(8)} ${'each'.padStart(8)}`
    const row = (label, s) => {
      const bad = s.wrong + s.missed + s.extra
      const each = s.timed ? `${String(Math.round(s.ms / s.timed)).padStart(6)}ms` : '     -  '
      const error = s.words ? `${(100 * bad / s.words).toFixed(1).padStart(7)}%` : '      -  '
      return `${label.padEnd(18)} ${String(s.words).padStart(5)} ${String(s.wrong).padStart(6)} ${String(s.check).padStart(6)} ${String(s.missed).padStart(7)} ${String(s.extra).padStart(6)} ${String(s.quiet).padStart(6)} ${String(s.failed).padStart(7)} ${error} ${each}`
    }
    // An ear whose cached readings cover only a handful of this run's
    // recordings prints a row that looks like a verdict and rests on three
    // ayahs. It is left out and said aloud, never quietly averaged in.
    const wanted = CLIPS.reduce((n, c) => n + printed.get(c.ayah.join(':')).split(/\s+/).filter(Boolean).length, 0)
    const thin = Object.keys(totals).filter((name) => totals[name].words < wanted / 4)
    for (const name of thin) { delete totals[name]; delete perReciter[name] }

    // Every voice apart, under its ear. An ear that hears one reciter perfectly
    // and another badly averages to "fine", and the average is the lie the
    // second reciter was added to catch.
    const byVoice = Object.entries(perReciter).flatMap(([name, voices]) => [
      '',
      `${name}, voice by voice`,
      ...RECITERS.filter((r) => voices[r].words).map((r) => row(`  ${r.replace(/_.*/, '')}`, voices[r])),
    ])
    const SHOWN = 400
    // To a file, not the screen: the test reporter swallows a long log, and a
    // run of this costs an hour and, for the cloud ears, real money to repeat.
    writeFileSync(REPORT, [
      `\n${printed.size} ayahs x ${RECITERS.length} reciters = ${CLIPS.length} recordings, ${wanted} words each ear`,
      thin.length ? `left out, too few of these recordings read: ${thin.join(', ')}` : '',
      HEAD,
      ...Object.entries(totals).map(([name, s]) => row(name, s)),
      ...byVoice,
      '',
      ...notes.slice(0, SHOWN),
      notes.length > SHOWN ? `\n... and ${notes.length - SHOWN} more readings with a mistake, not printed.` : '',
    ].join('\n'))

    expect(Object.keys(totals).length).toBeGreaterThanOrEqual(1)
  }, 6 * 60 * 60 * 1000)
})
