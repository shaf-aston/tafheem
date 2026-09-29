/**
 * The pictures on Grow's map. Drawn in the tab's own colour (--c) and the
 * theme's, never a colour of their own, so they match whatever they sit on.
 *
 * A step is a lock, a seed, a sprout or a flower (a posture shows its figure
 * until done): nodeState says which, this file only draws it. A group is a small figure of what it holds; its `icon`
 * is a name in paths.json, and the backend schema (GrowGroup.icon) holds it
 * to the names below. The figures are plain lines with a round head and no face.
 */

export function Lock() {
  return (
    <svg className="grow-ic" viewBox="0 0 24 24" aria-hidden="true">
      <rect x="5" y="11" width="14" height="9" rx="2.5" />
      <path d="M8 11V8a4 4 0 018 0v3" />
    </svg>
  )
}

export function Seed() {
  return (
    <svg className="grow-seed" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 3c4 3 6.5 7 6.5 11a6.5 6.5 0 0 1-13 0c0-4 2.5-8 6.5-11z" />
      <path d="M12 9v9" fill="none" />
    </svg>
  )
}

export function Sprout() {
  return (
    <svg className="grow-seed" viewBox="0 0 24 24" aria-hidden="true">
      <path d="M12 21V11" fill="none" />
      <path d="M12 14c-5 0-7.5-3-7.5-6.5 5 0 7.5 2.5 7.5 6.5z" />
      <path d="M12 11.5c0-4.5 2.5-7 7.5-7 0 4.5-2.5 7-7.5 7z" />
      <path d="M7 21h10" fill="none" />
    </svg>
  )
}

const PETALS = [0, 72, 144, 216, 288]

/** A clean bloom: five petals round a warm centre with a tick in it. It sways, and pops in as it appears. */
export function Flower() {
  return (
    <svg className="grow-bloom" viewBox="-30 -30 60 60" aria-hidden="true">
      {PETALS.map((a) => (
        <ellipse key={a} cx="0" cy="-15" rx="8.5" ry="13" transform={`rotate(${a})`} className="grow-petal" />
      ))}
      <circle r="8" className="grow-heart" />
      <path d="M-4 0l3 3 5-6" className="grow-tick" />
    </svg>
  )
}

/**
 * What a step's circle holds for each state nodeState can give. A posture
 * (`figure`, the group's picture) shows that figure until it is done.
 */
export function StateIcon({ state, figure = null }) {
  if (state === 'locked') return <Lock />
  if (state === 'learnt') return <Flower />
  if (figure) return <GroupIcon name={figure} />
  return state === 'started' ? <Sprout /> : <Seed />
}

const FIGURES = {
  stand: <><circle cx="20" cy="7" r="3.5" /><path d="M20 13v19M13 36h14" /></>,
  bow: <><circle cx="8" cy="15" r="3.5" /><path d="M13 18h19M32 18v15M27 36h10" /></>,
  prostrate: <><circle cx="8" cy="27" r="3.5" /><path d="M13 29l13-8 7 9M5 36h32" /></>,
  sit: <><circle cx="14" cy="8" r="3.5" /><path d="M14 13v15h17l-5 6H14" /></>,
  book: <path d="M20 10c-4-3-9-3-14-2v22c5-1 10-1 14 2 4-3 9-3 14-2V8c-5-1-10-1-14 2zM20 10v22" />,
  lock: <><rect x="9" y="18" width="22" height="15" rx="4" /><path d="M13 18v-5a7 7 0 0114 0v5" /></>,
  drop: <path d="M20 5c6 7 10 12 10 18a10 10 0 0 1-20 0c0-6 4-11 10-18z" />,
}

export function GroupIcon({ name }) {
  return (
    <svg className="grow-gi" viewBox="0 0 40 40" aria-hidden="true">
      {FIGURES[name]}
    </svg>
  )
}
