/**
 * The learner's last record of each module, as the server last gave it, kept on this device so Grow, the Quiz
 * and Review still plan a lesson with no signal.
 *
 * One copy per person and module, under a device key (never a shelf: it is the server's own answer, re-read
 * whenever there is a signal). With no signal the copy comes back with the answers still waiting to be sent
 * (lib/learner/outbox.js) counted in, so a lesson finished on the train is not dealt again.
 */
import PROFILE from '../../config/profile.json'
import { forgetDevice, readDevice, store, writeDevice } from '../store/device'
import { waiting } from './outbox'
import { deviceId, getProfile, profileHeaders } from './profile'

const { prefix: PREFIX, maxBytes: MAX_BYTES } = PROFILE.lastRecord

const whose = () => `${PREFIX}${getProfile() || deviceId()}:`

/** Keep the server's rows for `module`; a record too big for the device is simply not kept. */
export function keepRecord(module, rows) {
  const text = JSON.stringify(rows)
  if (text.length <= MAX_BYTES) writeDevice(whose() + module, text)
}

/** Pure: `rows` with this person's waiting answers in `module` counted in. A new item is seen, not yet due or known. */
export function withWaiting(rows, module, answers, who) {
  const byItem = new Map(rows.map((row) => [row.item, { ...row }]))
  for (const { body, headers } of answers) {
    if (body.module !== module || JSON.stringify(headers) !== who) continue
    const row = byItem.get(body.item) ?? { item: body.item, attempts: 0, wrong: 0, avgMs: null, due: false, known: false, dueAt: null, words: [] }
    byItem.set(body.item, { ...row, attempts: row.attempts + 1, wrong: row.wrong + (body.correct ? 0 : 1) })
  }
  return [...byItem.values()]
}

/** The kept rows for `module` with the waiting answers counted in, or null when none were kept. */
export function lastRecord(module) {
  try {
    const rows = JSON.parse(readDevice(whose() + module, 'null'))
    return Array.isArray(rows) ? withWaiting(rows, module, waiting(), JSON.stringify(profileHeaders())) : null
  } catch {
    return null
  }
}

/** Forget this person's kept records: Start over means these too. */
export function forgetRecords() {
  try {
    const all = Array.from({ length: store()?.length ?? 0 }, (_, index) => store().key(index))
    all.filter((key) => key?.startsWith(whose())).forEach(forgetDevice)
  } catch {
    /* nothing kept to forget */
  }
}
