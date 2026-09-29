/**
 * What a step is made of, and how the ear weighs it. A registry, so a new kind
 * of step is one entry here and nothing else in Grow learns its name.
 *
 *   phrase  written out in the step: the ear scores each written word
 *   ayahs   named by place: the Qur'an tab's own check scores each ayah, and
 *           the scores land back on that ayah's words
 *
 * Each checker gets the recording, the transcript, the step and its page
 * (lib/grow.js pageOf) and answers the ear's sureness per word of the step.
 */
import { checkReading, checkText } from '../api'
import { byPlace } from './recitingSession'

const KINDS = {
  phrase: async (recording, heard, step) => (await checkText(recording, { heard, expected: step.arabic })).sure,
  ayahs: async (recording, heard, step, page) =>
    byPlace((await checkReading(recording, { heard, check: step.ayahs })).sure, page.ayahs),
}

export const kindOf = (step) => (step.ayahs?.length ? 'ayahs' : 'phrase')

export const checkStep = (step, recording, heard, page) => KINDS[kindOf(step)](recording, heard, step, page)
