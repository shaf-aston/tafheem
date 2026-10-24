/**
 * Which Grow world to suggest on Home, and the exact step in it. Pure maths, no AI: each live world is scored from the
 * learner's own record (the progress overview, one row per module), then the top one is narrowed to a lesson.
 *
 *   score = recent use + level fit
 *   recent use = 0.5^(days since last answer / half-life) × log2(1 + answers) × (1 + share wrong)
 *
 * So a world used yesterday beats one used last month, a lot of use beats a little, and a world being got wrong is
 * pulled up (it needs the practice). A world never used scores only its level fit: the world the learner's level starts
 * from (levels.json `grow`). Knobs: home.json `suggest`.
 */
import knobs from '../../config/home.json'
import { REVIEW } from './useBookWorld'

const DAY = 24 * 60 * 60 * 1000
export const KNOBS = knobs.suggest

/** A module row's answers in `world`, every meaning language of its record together ("quiz", "quiz:ur"). */
function usageOf(world, modules) {
  let used = null
  for (const row of modules) {
    if (row.module.split(':')[0] !== world.module) continue
    used ??= { answers: 0, right: 0, lastAt: '' }
    used.answers += row.attempts
    used.right += row.correct
    if (row.lastAt > used.lastAt) used.lastAt = row.lastAt
  }
  return used
}

/** One world's score and the main reason for it: 'recent' (used lately), 'level' (fits the level) or null. */
export function scoreOf(world, modules, level, now, k = KNOBS) {
  const used = usageOf(world, modules)
  const fit = world.id === level ? k['level-fit'] : 0
  if (!used) return { score: fit, why: fit ? 'level' : null }
  const days = Math.max(0, (now - Date.parse(used.lastAt)) / DAY)
  const wrong = used.answers ? 1 - used.right / used.answers : 0
  const recent = 0.5 ** (days / k['half-life-days']) * Math.log2(1 + used.answers) * (1 + wrong)
  return { score: recent + fit, why: recent >= fit ? 'recent' : 'level' }
}

/** The live worlds worth suggesting, best first, each with `score` and `why`; ties keep worlds.json order. */
export function rankWorlds(worlds, modules = [], level = null, now = Date.now(), k = KNOBS) {
  return worlds
    .filter((world) => world.live)
    .map((world, at) => ({ world, at, ...scoreOf(world, modules, level, now, k) }))
    .filter((one) => one.score > 0)
    .sort((a, b) => b.score - a.score || a.at - b.at)
}

/**
 * The step to offer in a book world, from its state (lib/grow/useBookWorld.js): the review once enough is due, else the
 * next lesson, else any review; null when the book is finished and nothing is due.
 * `{ value, trail, due? }`: the Grow address and the names down to it (book › part › lesson).
 */
export function bookStep(world, state, k = KNOBS) {
  const due = state.due.length
  const review = { value: `${world.id}/${REVIEW}`, trail: [world.name], due }
  if (due >= k['review-at']) return review
  if (state.next) {
    const part = state.parts.find((one) => one.id === state.next.part)
    return { value: `${world.id}/${state.next.part}/${state.next.id}`, trail: [world.name, part?.title, state.next.title].filter(Boolean) }
  }
  return due ? review : null
}

/** The step in a lessons world (Basics, Words, Hadith, Qur'an): its next lesson. */
export const lessonStep = (world) => ({ value: `${world.id}/lesson`, trail: [world.name] })
