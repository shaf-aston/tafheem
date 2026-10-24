/**
 * An event's steps: which fold, the order they are read in, where each took
 * place, and how neighbouring paths become side-by-side lanes.
 */
import settings from '../../config/timelines.json'

const { steps: STEPS } = settings

/** A step worth folding: it holds moments, runs long, or is a side detail. */
export const canFold = (step) => (
  (step.steps ?? []).length > 0 || Boolean(step.aside) || step.summary.length >= STEPS['fold-from-chars']
)

/** The ids at any depth that pass `test`: which can fold, or which start folded. */
export const stepIds = (steps = [], test) => steps.flatMap((s) => [
  ...(test(s) ? [s.id] : []),
  ...stepIds(s.steps, test),
])

/** Every step at any depth in reading order, each with the steps it sits inside. */
export const readingOrder = (steps = [], above = []) => steps.flatMap((step) => [
  { step, above },
  ...readingOrder(step.steps, [...above, step]),
])

/** Where a step happened: its own place, else the nearest step above it with one, else the event's. */
export function placeOfStep(event, stepId) {
  const at = readingOrder(event.steps).find((r) => r.step.id === stepId)
  const chain = at ? [at.step, ...at.above.toReversed()] : []
  return chain.find((s) => s.place)?.place ?? event.place ?? null
}

/**
 * A run cut into rows: a lone step, or neighbouring steps that name a path,
 * read side by side as lanes. Lanes keep the order the data first names them
 * in, so reading order and drawn order agree. Each row carries its number:
 * lanes share one starting number, since they happen at the same time.
 */
export function pathRows(steps) {
  const rows = []
  let n = 1
  for (const step of steps) {
    const last = rows.at(-1)
    if (!step.path) {
      rows.push({ n, step })
      n += 1
    } else if (last?.lanes) {
      const lane = last.lanes.find((l) => l.path === step.path)
      if (lane) lane.steps.push(step)
      else last.lanes.push({ path: step.path, steps: [step] })
      n = last.n + Math.max(...last.lanes.map((l) => l.steps.length))
    } else {
      rows.push({ n, lanes: [{ path: step.path, steps: [step] }] })
      n += 1
    }
  }
  return rows
}
