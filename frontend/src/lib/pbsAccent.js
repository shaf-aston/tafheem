/**
 * A chart's accent, lightened enough to read as text on the app's dark
 * surfaces.
 *
 * lib/pbsData's accents are tuned for the reference file's light background —
 * several (Jurisprudence's near-black #0f172a, Logic's slate #475569) are
 * backgrounds or borders there, never foreground text. Used as text colour on
 * a dark card, the same hex can sit near-invisible. This raises each colour's
 * HSL lightness to a floor before it is ever put behind text, keeping its hue
 * (so each science still reads as its own colour) while guaranteeing contrast.
 * Anywhere an accent sits on a colour already chosen to pair with it (a kid's
 * own `c.text`, white on a filled branch bar) is untouched — only bare accent
 * used as foreground text needs this.
 */
const hexToHsl = (hex) => {
  const r = parseInt(hex.slice(1, 3), 16) / 255
  const g = parseInt(hex.slice(3, 5), 16) / 255
  const b = parseInt(hex.slice(5, 7), 16) / 255
  const max = Math.max(r, g, b), min = Math.min(r, g, b)
  const l = (max + min) / 2
  if (max === min) return [0, 0, l]
  const d = max - min
  const s = l > 0.5 ? d / (2 - max - min) : d / (max + min)
  let h
  if (max === r) h = ((g - b) / d + (g < b ? 6 : 0)) / 6
  else if (max === g) h = ((b - r) / d + 2) / 6
  else h = ((r - g) / d + 4) / 6
  return [h * 360, s, l]
}

const hslToHex = (h, s, l) => {
  const c = (1 - Math.abs(2 * l - 1)) * s
  const x = c * (1 - Math.abs(((h / 60) % 2) - 1))
  const m = l - c / 2
  const [r, g, b] = h < 60 ? [c, x, 0] : h < 120 ? [x, c, 0] : h < 180 ? [0, c, x]
    : h < 240 ? [0, x, c] : h < 300 ? [x, 0, c] : [c, 0, x]
  const to255 = (v) => Math.round((v + m) * 255).toString(16).padStart(2, '0')
  return `#${to255(r)}${to255(g)}${to255(b)}`
}

const cache = new Map()

/** `hex`, lightened to at least `minLightness` (0-1) if it falls short. */
export function readableAccent(hex, minLightness = 0.62) {
  const key = `${hex}:${minLightness}`
  if (cache.has(key)) return cache.get(key)
  const [h, s, l] = hexToHsl(hex)
  const result = l >= minLightness ? hex : hslToHex(h, Math.max(s, 0.45), minLightness)
  cache.set(key, result)
  return result
}
