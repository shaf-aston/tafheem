/** Confetti thrown up from the medal: where each piece lands sideways (px), how far it turns, its colour. Fixed, so a replay is the same throw. */
export const CONFETTI = Array.from({ length: 24 }, (_, i) => ({
  x: (((i * 37) % 100) - 50) * 3.2,
  turn: ((i * 73) % 300) + 180,
  tone: ['var(--w)', 'var(--grow-gold)', 'var(--success)', 'var(--palette-rose)'][i % 4],
}))
