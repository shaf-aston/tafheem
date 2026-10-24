/**
 * Putting a short list in a random order, the one copy of it.
 *
 * The quiz and Memorise both do this, to the four words a question offers and
 * to the words of a line, and they were doing it with the same eight lines
 * written out twice. The order comes from a generator the caller passes in,
 * never from Math.random, because both tabs need the same seed to give the
 * same result: that is what lets a page of gaps be handed back unchanged and
 * what makes the tests repeatable.
 *
 * The original is left alone; a copy comes back.
 */
export const shuffled = (list, random) => {
  const order = [...list]
  for (let i = order.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1))
    ;[order[i], order[j]] = [order[j], order[i]]
  }
  return order
}
