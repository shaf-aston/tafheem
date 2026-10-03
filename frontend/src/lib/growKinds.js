/**
 * What a step is made of, and how the ear weighs it. A registry, so a new kind
 * of step is one entry here and nothing else in Grow learns its name.
 *
 *   phrase  written out in the step: the ear scores each written word
 *   ayahs   named by place: the Qur'an tab's own check scores each ayah, and
 *           the scores land back on that ayah's words
 *   action  a posture, shown as an instruction and tapped Done: nothing to hear
 *
 * Each `check` gets the recording, the transcript, the step and its page
 * (lib/grow.js pageOf) and answers the ear's sureness per word of the step.
 * `byHand` kinds have no check: the reader says when they are done.
 */
import { checkReading, checkText } from '../api'
import { byPlace } from './recitingSession'

const KINDS = {
  phrase: { check: async (recording, heard, step, page, trial) => (await checkText(recording, { heard, expected: step.arabic, trial })).sure },
  ayahs: {
    check: async (recording, heard, step, page, trial) =>
      byPlace((await checkReading(recording, { heard, check: step.ayahs, trial })).sure, page.ayahs),
  },
  action: { byHand: true },
}

const kindOf = (step) => step.kind ?? (step.ayahs.length ? 'ayahs' : 'phrase')

/** Whether the reader ticks this step off themselves, instead of saying it to the ear. */
export const byHand = (step) => Boolean(KINDS[kindOf(step)].byHand)

export async function checkStep(step, recording, heard, page, trial) {
  try {
    return await KINDS[kindOf(step)].check(recording, heard, step, page, trial)
  } catch {
    return null
  }
}
