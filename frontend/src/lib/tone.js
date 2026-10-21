/**
 * A section's colour, toned for the look it sits in.
 *
 * theme.json's palette holds each section's own colour once. A look does not
 * repaint them; it gives a tone (themes.tone, overridden per look) and every
 * colour is worked out from it: same hue, so the section stays recognisable,
 * lightness and chroma set by the look, then moved away from the ground until
 * it reads. Pure colour maths, no theme.json and no DOM.
 */

const channel = (c) => ((c /= 255) <= 0.04045 ? c / 12.92 : ((c + 0.055) / 1.055) ** 2.4)
const encode = (c) => (c <= 0.0031308 ? 12.92 * c : 1.055 * c ** (1 / 2.4) - 0.055)
const rgbOf = (hex) => {
  const n = parseInt(hex.slice(1), 16)
  return [n >> 16, (n >> 8) & 255, n & 255].map(channel)
}

/** WCAG relative luminance and contrast ratio. */
const luminance = (hex) => {
  const [r, g, b] = rgbOf(hex)
  return 0.2126 * r + 0.7152 * g + 0.0722 * b
}
export const contrast = (a, b) => {
  const [hi, lo] = [luminance(a), luminance(b)].sort((x, y) => y - x)
  return (hi + 0.05) / (lo + 0.05)
}

/**
 * APCA-W3 0.0.98G lightness contrast (Lc) of text on a ground: about +106 for
 * black on white, -108 for white on black. Positive is dark text on light.
 * WCAG ratio is blind to polarity and to how thin small text is, so a pair
 * passing 7:1 can still be Lc 54; the comfort floor is held in Lc (themes.comfort.dim-min-lc).
 */
const sapcY = (hex) => {
  const [r, g, b] = [16, 8, 0].map((shift) => ((parseInt(hex.slice(1), 16) >> shift) & 255) / 255)
  const y = r ** 2.4 * 0.2126729 + g ** 2.4 * 0.7151522 + b ** 2.4 * 0.072175
  return y < 0.022 ? y + (0.022 - y) ** 1.414 : y
}
export const apca = (text, ground) => {
  const [yt, yb] = [sapcY(text), sapcY(ground)]
  if (Math.abs(yb - yt) < 0.0005) return 0
  const lc = yb > yt ? (yb ** 0.56 - yt ** 0.57) * 1.14 : (yb ** 0.65 - yt ** 0.62) * 1.14
  if (Math.abs(lc) < 0.1) return 0
  return (lc > 0 ? lc - 0.027 : lc + 0.027) * 100
}

/** OKLCH [lightness, chroma, hue in degrees] of a #rrggbb colour (Ottosson's matrices). */
export function oklch(hex) {
  const [r, g, b] = rgbOf(hex)
  const [l, m, s] = [
    0.4122214708 * r + 0.5363325363 * g + 0.0514459929 * b,
    0.2119034982 * r + 0.6806995451 * g + 0.1073969566 * b,
    0.0883024619 * r + 0.2817188376 * g + 0.6299787005 * b,
  ].map(Math.cbrt)
  const A = 1.9779984951 * l - 2.428592205 * m + 0.4505937099 * s
  const B = 0.0259040371 * l + 0.7827717662 * m - 0.808675766 * s
  const hue = (Math.atan2(B, A) * 180) / Math.PI
  return [0.2104542553 * l + 0.793617785 * m - 0.0040720468 * s, Math.hypot(A, B), (hue + 360) % 360]
}

/** The #rrggbb at that OKLCH, or null when the screen cannot show it. */
function hexAt(L, C, H) {
  const [A, B] = [C * Math.cos((H * Math.PI) / 180), C * Math.sin((H * Math.PI) / 180)]
  const l = (L + 0.3963377774 * A + 0.2158037573 * B) ** 3
  const m = (L - 0.1055613458 * A - 0.0638541728 * B) ** 3
  const s = (L - 0.0894841775 * A - 1.291485548 * B) ** 3
  const rgb = [
    4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
    -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
    -0.0041960863 * l - 0.7034186147 * m + 1.707614701 * s,
  ].map(encode)
  if (rgb.some((c) => !(c >= -1e-4 && c <= 1 + 1e-4))) return null
  return `#${rgb.map((c) => Math.round(Math.min(1, Math.max(0, c)) * 255).toString(16).padStart(2, '0')).join('')}`
}

const STEP = 0.005
const MAX_STEPS = 200

/** The nearest colour the screen can show: chroma given up first, hue never. */
function shown(L, C, H) {
  for (let c = C; c > 0; c -= STEP / 2) {
    const hex = hexAt(L, c, H)
    if (hex) return hex
  }
  return hexAt(L, 0, H)
}

/**
 * Every palette colour toned for one look.
 *
 * tone: { centre, spread, max-chroma, max-lightness, min-contrast }. A colour's
 * lightness lands at centre plus its distance from the palette's mean times
 * spread (negative on a light look, so an emphasis shade, lighter on dark, comes
 * out darker on paper). Then it steps away from the ground (lighter on dark,
 * darker on light), never past max-lightness, until it reaches min-contrast on
 * every ground it sits on; a tone that cannot get there stops the app loudly.
 * The mean is over the whole palette, so adding a colour nudges the rest.
 * Reading on a wash of itself is not promised here; theme.test.js holds that.
 */
export function tonePalette(palette, tone, grounds, dark) {
  const parts = Object.fromEntries(Object.entries(palette).map(([name, hex]) => [name, oklch(hex)]))
  const lights = Object.values(parts).map(([l]) => l)
  const mean = lights.reduce((sum, l) => sum + l, 0) / lights.length
  const away = dark ? STEP : -STEP
  return Object.fromEntries(
    Object.entries(parts).map(([name, [l, c, h]]) => {
      const cap = (L) => Math.max(0, Math.min(L, tone['max-lightness']))
      const C = Math.min(c, tone['max-chroma'])
      const reads = (hex) => Math.min(...grounds.map((g) => contrast(hex, g))) >= tone['min-contrast']
      let L = cap(tone.centre + (l - mean) * tone.spread)
      for (let i = 0; i < MAX_STEPS; i++, L = cap(L + away)) {
        const hex = shown(L, C, h)
        if (reads(hex)) return [name, hex]
      }
      throw new Error(`tone: ${name} cannot reach ${tone['min-contrast']}:1 on its grounds within max-lightness`)
    }),
  )
}
