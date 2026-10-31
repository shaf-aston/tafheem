/**
 * The everyday diagrams behind WordPicture, beside the body and the maps
 * (wordPictures.js): a family tree, a house, a crossroads, a compass, a clock, the
 * weather, and grids of panels for positions, colours, shapes, days and months.
 *
 * Pure data. A spot is placed one of two ways, keyed by word id:
 *   [x, y]           a dot on the drawing (a person's head, a piece of furniture)
 *   [x, y, w, h]     an area to tap (a room, the garden)
 * `also` sends more words to a spot that means them too, so "inside" is answered on
 * the "in" panel. `lead` moves a dot out to [x, y] when its place is too crowded to
 * tap, and a line runs from the dot to the place. A panel board lays its panels out in a grid, only those the topic
 * teaches, in the order written; words/picture/SceneArt.jsx draws each one.
 * Move a part of a drawing there and move its spot here.
 */

// The clock's numbers sit on a ring; a dot per number, just outside the numeral.
const RING = 122
const onClock = (hour, r = RING) => {
  const a = (hour % 12) * Math.PI / 6
  return [Math.round(150 + r * Math.sin(a)), Math.round(150 - r * Math.cos(a))]
}
const NUMBERS = ['one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine', 'ten', 'eleven', 'twelve']

/** Drawn scenes: spots placed by hand on SceneArt's drawing of the same id. */
export const SCENES = [
  {
    id: 'family', label: 'Family tree', art: 'family', view: [0, 0, 360, 400],
    spots: {
      grandfather: [70, 30], grandmother: [125, 30],
      'uncle-paternal': [25, 115], 'aunt-paternal': [75, 115], father: [130, 115], parents: [180, 115],
      mother: [230, 115], 'uncle-maternal': [285, 115], 'aunt-maternal': [335, 115],
      cousin: [25, 200], brother: [80, 200], 'sister-in-law': [125, 200], wife: [225, 200],
      sister: [285, 200], 'brother-in-law': [335, 200],
      son: [180, 285], daughter: [225, 285], nephew: [285, 285], niece: [335, 285],
      grandson: [160, 365], granddaughter: [205, 365],
    },
    // The sister's husband is a husband and a brother-in-law at once.
    also: { husband: 'brother-in-law' },
  },
  {
    id: 'house', label: 'House', art: 'house', view: [0, 0, 360, 300],
    spots: {
      roof: [120, 50, 120, 44], garden: [0, 200, 56, 80], balcony: [302, 160, 46, 30],
      bedroom: [60, 100, 110, 90], bathroom: [170, 100, 60, 90], 'guest-room': [230, 100, 70, 90],
      kitchen: [60, 190, 80, 90], stairs: [140, 190, 40, 90], 'living-room': [180, 190, 120, 90],
      window: [140, 125], wardrobe: [77, 158], bed: [130, 176], mirror: [200, 125], bath: [200, 178],
      table: [255, 168], chair: [287, 166],
      cupboard: [112, 209], fridge: [76, 245], cooker: [110, 262],
      light: [210, 207], curtains: [250, 213], sofa: [216, 263], door: [280, 250],
    },
    also: { oven: 'cooker', lamp: 'light' },
  },
  {
    id: 'crossroads', label: 'Crossroads', art: 'crossroads', view: [0, 0, 300, 300],
    spots: {
      'straight-ahead': [150, 42], left: [42, 150], 'right-direction': [258, 150],
      corner: [112, 188], 'traffic-light': [198, 92], sign: [212, 222], masjid: [62, 62], pharmacy: [240, 62],
    },
  },
  {
    id: 'compass', label: 'Compass', art: 'compass', view: [0, 0, 300, 300],
    spots: { north: [150, 62], east: [238, 150], south: [150, 238], west: [62, 150] },
  },
  {
    id: 'clock', label: 'Clock', art: 'clock', view: [0, 0, 300, 300],
    spots: {
      ...Object.fromEntries(NUMBERS.map((id, i) => [id, onClock(i + 1)])),
      // The hands: the short one to half past four, the long one to twelve.
      hour: [189, 189], minute: [150, 70],
    },
  },
  {
    id: 'weather', label: 'Weather', art: 'weather', view: [0, 0, 360, 260],
    spots: {
      sun: [70, 62], cloud: [190, 52], rain: [290, 118], lightning: [330, 128], snow: [180, 150],
      wind: [96, 160], umbrella: [256, 178], hot: [30, 176], 'cold-weather': [30, 232],
    },
  },
]

/** Panel boards: one panel per word, in a grid, each drawn by SceneArt's panel of that board. */
export const PANELS = [
  {
    id: 'position', label: 'Where it is', art: 'position', cols: 3, cell: [120, 100],
    keys: ['on', 'in', 'under', 'above', 'next-to', 'behind', 'in-front-of', 'between', 'around', 'outside', 'opposite', 'middle'],
    also: { inside: 'in' },
  },
  {
    id: 'colours', label: 'Colours', art: 'colour', cols: 4, cell: [90, 70],
    keys: ['red', 'orange', 'yellow', 'green', 'blue', 'light-blue', 'navy-blue', 'turquoise', 'purple', 'pink', 'brown', 'grey', 'black', 'white', 'gold-colour', 'silver-colour'],
  },
  {
    id: 'shapes', label: 'Shapes', art: 'shape', cols: 4, cell: [90, 80],
    keys: ['circle', 'square-shape', 'triangle', 'rectangle', 'line-shape', 'point', 'cube'],
  },
  {
    id: 'week', label: 'Week', art: 'day', cols: 7, cell: [50, 72],
    keys: ['sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday'],
  },
  {
    id: 'gregorian', label: 'Months', art: 'month', cols: 4, cell: [90, 56],
    keys: ['january', 'february', 'march', 'april', 'may', 'june', 'july', 'august', 'september', 'october', 'november', 'december'],
  },
  {
    id: 'hijri', label: 'Hijri months', art: 'hijri', cols: 4, cell: [90, 56],
    keys: ['muharram', 'safar', 'rabi-al-awwal', 'rabi-al-akhir', 'jumada-al-ula', 'jumada-al-akhira', 'rajab', 'shaban', 'ramadan', 'shawwal', 'dhu-al-qadah', 'dhu-al-hijjah'],
  },
]

// The words a key gathers: its own, and every word sent to it by `also`.
const wordsAt = (key, also, byId) =>
  [key, ...Object.keys(also).filter((id) => also[id] === key)].map((id) => byId[id]).filter(Boolean)

const spotOf = (key, [x, y, w, h], words) =>
  (w ? { key, x: x + w / 2, y: y + h / 2, area: [x, y, w, h], words } : { key, x, y, words })

// A led spot's dot stands where `lead` puts it, pointing at its place (`to`).
const ledOut = (spot, lead) => (lead ? { ...spot, x: lead[0], y: lead[1], to: [spot.x, spot.y] } : spot)

/** A drawn board with only the spots this topic's words fill. */
export const sceneBoard = ({ spots, also = {}, lead = {}, ...board }, byId) => ({
  ...board,
  spots: Object.entries(spots)
    .map(([key, at]) => ledOut(spotOf(key, at, wordsAt(key, also, byId)), lead[key]))
    .filter((s) => s.words.length),
})

/** A panel board laid out in rows, only the panels this topic's words fill, each keeping its place in the set. */
export function panelBoard({ keys, cols, cell: [w, h], also = {}, ...board }, byId) {
  const shown = keys.filter((key) => wordsAt(key, also, byId).length)
  const across = Math.min(cols, Math.max(shown.length, 1))
  const spots = shown.map((key, i) => ({
    ...spotOf(key, [(i % across) * w, Math.floor(i / across) * h, w, h], wordsAt(key, also, byId)),
    // Its place in the whole set (a day's number in the week, a month's in the year).
    order: keys.indexOf(key) + 1,
  }))
  return { ...board, view: [0, 0, across * w, Math.ceil(shown.length / across) * h], spots }
}
