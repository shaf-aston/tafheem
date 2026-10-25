import theme from '../config/theme.json'

const clamp = (v) => Math.max(0, Math.min(1, v))

const KNOBS = {
  nameShare: Number(theme.landing['name-share']),
  drawShare: Number(theme.landing['draw-share']),
  whyAt: Number(theme.landing['why-at']),
}

// Which step the track is on and how far through it, 0 to 1. A step with a
// bigger weight gets that many steps' worth of scrolling.
export function locate(progress, weights) {
  const total = weights.reduce((a, b) => a + b, 0)
  const x = clamp(progress) * total
  let start = 0
  for (let i = 0; i < weights.length; i += 1) {
    if (x < start + weights[i] || i === weights.length - 1) return { active: i, lp: clamp((x - start) / weights[i]) }
    start += weights[i]
  }
}

// The one sentence step as a single timeline over lp (0 to 1): first each word is
// named in turn, then the governor arrows are drawn pair by pair. `focus` is the
// span of words the camera rests on. Pure, so scrolling back plays it backwards.
export function sentencePhase(lp, { words, pairs }, knobs = KNOBS) {
  if (lp < knobs.nameShare) {
    const named = Math.min(words, Math.floor((lp / knobs.nameShare) * (words + 1)))
    const at = Math.max(0, named - 1)
    return { phase: 'name', named, pair: -1, focus: [at, at], drawn: pairs.map(() => 0), why: false }
  }
  const g = clamp((lp - knobs.nameShare) / (1 - knobs.nameShare)) * pairs.length
  const pair = Math.min(pairs.length - 1, Math.floor(g))
  return {
    phase: 'govern',
    named: words,
    pair,
    focus: [pairs[pair].from, pairs[pair].to],
    drawn: pairs.map((_, k) => clamp((g - k) / knobs.drawShare)),
    why: g - pair > knobs.whyAt,
  }
}
