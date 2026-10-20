/**
 * A card said aloud, and how the ear weighs it. A phrase is written out in
 * the card, and the ear scores each written word; ayahs are named by place,
 * and the Qur'an tab's own check scores each ayah, the scores landing back
 * on that ayah's words (lib/grow.js pageOf).
 */
import { checkReading, checkText } from '../../../api'
import { byPlace, scoreOf } from '../../recitingSession'

export const check = async (recording, heard, card, page, trial) => {
  if (card.ayahs.length) {
    const { sure, detail } = await checkReading(recording, { heard, check: card.ayahs, trial })
    return byPlace(sure, page.ayahs, detail)
  }
  const { sure, detail = [] } = await checkText(recording, { heard, expected: card.arabic, trial })
  return sure.map((one, i) => scoreOf(one, detail[i]))
}
