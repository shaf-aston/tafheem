// An arc over a line of words from one word's top centre to another's, with the
// chevron that ends it (pointing down into the governed word). `maxLift` caps
// how high a long span climbs, so a long sentence keeps a short band above it.
const ARC_LIFT = 18 // px above the words, plus a share of the span
const HEAD = 7 // px half-width of the arrowhead

export function arc([x1, y1], [x2, y2], maxLift = Infinity) {
  const lift = y1 - Math.min(ARC_LIFT + Math.abs(x2 - x1) / 6, maxLift)
  return {
    d: `M${x1} ${y1}C${x1} ${lift} ${x2} ${lift} ${x2} ${y2}`,
    head: `M${x2 - HEAD} ${y2 - HEAD}L${x2} ${y2}L${x2 + HEAD} ${y2 - HEAD}`,
  }
}
