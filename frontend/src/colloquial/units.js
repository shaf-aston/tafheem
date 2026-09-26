/**
 * The unit files, one lazy chunk each, so opening the tab loads none of them
 * and opening a unit loads only that one. The list of units is the files in
 * the folder: adding unit-17.json needs no code.
 *
 * Each unit is checked as it loads. Lesson ids unique across units needs every
 * file at once, so that one rule is left to `npm run validate:colloq`.
 */
import { validateAll } from './validate'

const FILES = import.meta.glob('../data/colloquial/*.json', { import: 'default' })
const idOf = (path) => path.split('/').pop().replace(/\.json$/, '')
const PATHS = Object.fromEntries(Object.keys(FILES).map((p) => [idOf(p), p]))

/** Every unit id, in file order. */
export const unitIds = () => Object.keys(PATHS).sort()

/** { id, unit } when valid, { id, problems } when not. */
export async function loadUnit(id, files = FILES) {
  const unit = await files[PATHS[id] ?? id]()
  const problems = validateAll({ [id]: unit })
  return problems.length ? { id, problems } : { id, unit }
}

/** Invalid units are shown (as unavailable) while developing and hidden once built. */
export const shown = (loaded, dev = import.meta.env.DEV) => Boolean(loaded.unit) || dev
