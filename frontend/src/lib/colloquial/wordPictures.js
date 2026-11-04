/**
 * The picture boards for a topic's words: where each word sits on a drawing, so a
 * learner can match the word to the place (words/picture/WordPicture.jsx).
 *
 * Pure data and one function. A board is a drawing (`art`), its viewBox, and its
 * spots; each spot is a place on the drawing and the words that mean it. A body
 * board puts one word on one spot. A map board puts a country and its people on the
 * same spot, so "Syrian" is answered by tapping Syria.
 *
 * Keyed by word id (backend/data/colloquial/words.json), the same in every dialect.
 * A word with no spot is only left out of the picture; the cards still teach it.
 */
import shapes from './countryShapes.json'
import { project, viewOf } from './countryMap'
import { PANELS, SCENES, panelBoard, sceneBoard } from './sceneBoards'

// Body boards: [x, y] in the drawing's own units (BodyArt.jsx draws to the same viewBox).
const BODY = [
  {
    id: 'face', label: 'Face', art: 'face', view: [0, 0, 240, 300],
    spots: {
      hair: [154, 40], forehead: [120, 80], eyebrow: [88, 98], eye: [152, 120], ear: [201, 142],
      nose: [120, 152], cheek: [170, 168], mouth: [156, 188], tooth: [110, 187], tongue: [120, 204],
      lip: [128, 214], chin: [120, 233], beard: [188, 200], neck: [120, 272],
    },
    // The mouth's parts sit too close to tap apart: their dots stand out to the side,
    // each on a thin line to its place.
    lead: { tooth: [20, 180], tongue: [20, 212], lip: [222, 236] },
  },
  {
    id: 'figure', label: 'Body', art: 'figure', view: [0, 0, 240, 400],
    spots: {
      head: [100, 30], brain: [128, 32], shoulder: [74, 86], chest: [120, 98], lung: [99, 124],
      heart: [131, 132], liver: [104, 162], stomach: [140, 164], kidney: [101, 194], muscle: [64, 122],
      elbow: [57, 160], arm: [184, 124], thigh: [102, 248], knee: [97, 292], leg: [146, 330],
      ankle: [95, 366], foot: [74, 384], heel: [143, 380],
    },
  },
  {
    id: 'hand', label: 'Hand', art: 'hand', view: [0, 0, 240, 300],
    spots: { fingernail: [131, 42], finger: [103, 76], thumb: [42, 146], 'palm-hand': [116, 178], hand: [176, 196], wrist: [116, 262] },
  },
]

// Map boards: one dot per country, at a spot inside it chosen by hand ([lon, lat]),
// since a box's middle can fall outside a country (Palestine's lands in Israel).
const CENTRE = {
  SY: [38.6, 35.1], LB: [35.85, 33.9], JO: [36.9, 30.9], PS: [35.25, 31.95], IQ: [43.6, 33.1], TR: [34.5, 39.1],
  SA: [44.5, 24.2], KW: [47.6, 29.3], QA: [51.2, 25.3], BH: [50.55, 26.05], AE: [54.4, 23.8], OM: [57, 21], YE: [47.5, 15.8],
  EG: [29.8, 26.6], LY: [17.5, 27.2], TN: [9.4, 34], DZ: [2.6, 28.2], MA: [-6.4, 32], SD: [30, 15.6],
}
const PLACE = {
  syria: 'SY', syrian: 'SY', lebanon: 'LB', jordan: 'JO', palestine: 'PS', palestinian: 'PS', iraq: 'IQ', iraqi: 'IQ',
  turkey: 'TR', turkish: 'TR', 'saudi-arabia': 'SA', saudi: 'SA', kuwait: 'KW', qatar: 'QA', bahrain: 'BH', uae: 'AE',
  oman: 'OM', yemen: 'YE', yemeni: 'YE', egypt: 'EG', egyptian: 'EG', libya: 'LY', tunisia: 'TN', algeria: 'DZ',
  morocco: 'MA', moroccan: 'MA', sudan: 'SD',
}
const MAPS = [
  { id: 'levant', label: 'Levant', codes: ['TR', 'SY', 'LB', 'PS', 'JO', 'IQ'] },
  { id: 'gulf', label: 'Gulf', codes: ['SA', 'KW', 'BH', 'QA', 'AE', 'OM', 'YE'] },
  { id: 'africa', label: 'North Africa', codes: ['EG', 'LY', 'TN', 'DZ', 'MA', 'SD'] },
]

// Fewer words than this on a board and it is no game, only a label.
const LEAST = 3

const mapBoard = ({ codes, ...board }, words) => {
  const spots = codes.map((code) => {
    const [x, y] = project(CENTRE[code])
    return { key: code, x, y, words: words.filter((w) => PLACE[w.id] === code) }
  }).filter((s) => s.words.length)
  const view = viewOf(spots.map((s) => shapes.countries[s.key].box), [], { aspect: 4 / 3, pad: 0.08 })
  return { ...board, art: 'map', view, spots }
}

/**
 * The boards this topic's words fill, each { id, label, art, view, spots: [{ key, x, y, area?, words }] };
 * [] if none. A spot with an `area` is tapped anywhere inside it; the rest are dots.
 */
export function pictureBoards(words) {
  const byId = Object.fromEntries(words.map((w) => [w.id, w]))
  const boards = [
    ...BODY.map((b) => sceneBoard(b, byId)),
    ...MAPS.map((b) => mapBoard(b, words)),
    ...SCENES.map((b) => sceneBoard(b, byId)),
    ...PANELS.map((b) => panelBoard(b, byId)),
  ]
  return boards.filter((b) => b.spots.reduce((n, s) => n + s.words.length, 0) >= LEAST)
}
