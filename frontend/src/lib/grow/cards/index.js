/**
 * What a card is made of, one file per kind, so a new kind of card is one
 * file here and nothing else in Grow learns its name.
 *
 *   recite  said to the ear: a phrase written out, or ayahs named by place
 *   action  a posture, ticked off by hand
 *
 * A kind exports `check`, which gets the recording, the transcript, the card
 * and its page and answers the ear's sureness per word;
 * or `byHand`, when the reader says when they are done. Later a kind will
 * also offer `exercisesFrom(card)`, the exercises it can be practised as.
 */
import * as action from './action'
import * as recite from './recite'

export const CARDS = { recite, action }

const kindOf = (card) => CARDS[card.kind ?? 'recite']

/** Whether the reader ticks this card off themselves, instead of saying it to the ear. */
export const byHand = (card) => Boolean(kindOf(card).byHand)

export async function checkStep(card, recording, heard, page, trial) {
  try {
    return await kindOf(card).check(recording, heard, card, page, trial)
  } catch {
    return null
  }
}
