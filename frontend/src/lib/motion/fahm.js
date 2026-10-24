/**
 * The two decisions behind Home's quiet word (components/home/FahmWord.jsx)
 * that are not drawing: when a hover earns a party, and how the party flies.
 * Both take the random source, so a test can pin them.
 */

/**
 * A counter that says yes once every min to max calls (a fresh draw after
 * each yes), so the party stays a surprise and never every time. It lives in
 * memory only: a reload starts the count over.
 */
export function ration({ min, max }, random = Math.random) {
  const draw = () => min + Math.floor(random() * (max - min + 1))
  let count = 0
  let due = draw()
  return () => {
    count += 1
    if (count < due) return false
    count = 0
    due = draw()
    return true
  }
}

const between = (random, a, b) => a + random() * (b - a)

/**
 * The bits of one party, launched from (x, y): each rises on a fan opening
 * upward, then falls away. kind cycles through the four marks (a nuqta, a
 * fatha, a sukun, a small nuqta), so every party carries all of them.
 */
export function burst({ count, x, y, spread }, random = Math.random) {
  return Array.from({ length: count }, (_, i) => {
    const angle = -Math.PI / 2 + between(random, -1.25, 1.25)
    const speed = between(random, 40, 92)
    return {
      kind: i % 4,
      x: x + between(random, -spread, spread),
      y,
      dx: Math.cos(angle) * speed,
      dy: Math.sin(angle) * speed,
      spin: between(random, -260, 260),
      pace: between(random, 0.8, 1.13),
    }
  })
}
