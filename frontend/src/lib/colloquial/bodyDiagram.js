/**
 * Where a body word sits on BodyDiagram's schematic figure, keyed by its
 * English name. A word with no entry here is still shown by WordGrid's own
 * tile grid below the diagram -- the diagram only adds a picture for the
 * words it knows a place for, it never gates what the grid shows.
 */
const POSITIONS = {
  eyebrow: [92, 34],
  cheek: [72, 58],
  chin: [100, 82],
  mouth: [100, 70],
  shoulder: [58, 118],
  lung: [100, 158],
  stomach: [100, 202],
  knee: [100, 300],
}

/** words with a known position, each as { word, x, y }; in viewBox units. */
export function hotspotsFor(words) {
  const placed = []
  for (const word of words) {
    const at = POSITIONS[word.english?.toLowerCase()]
    if (at) placed.push({ word, x: at[0], y: at[1] })
  }
  return placed
}
