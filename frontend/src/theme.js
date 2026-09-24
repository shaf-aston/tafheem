/**
 * The only module that reads theme.json.
 *
 * Every group in the config becomes CSS custom properties named `--<group>-<key>`
 * (the `color` group drops its prefix, so `color.bg` is just `--bg`). Components
 * then reference `var(--role-fail)` and never a literal colour, which is what
 * makes the whole look editable from one file.
 */
import theme from './theme.json'

const UNPREFIXED_GROUP = 'color'
const PRIVATE_KEY = '_'

function cssVariables() {
  const vars = {}
  for (const [group, values] of Object.entries(theme)) {
    if (group.startsWith(PRIVATE_KEY) || typeof values !== 'object') continue
    const prefix = group === UNPREFIXED_GROUP ? '' : `${group}-`
    for (const [key, value] of Object.entries(values)) {
      if (key.startsWith(PRIVATE_KEY)) continue
      vars[`--${prefix}${key}`] = String(value)
    }
  }
  return vars
}

const VARIABLES = cssVariables()

/** Write every token onto :root. Called once at startup. */
export function applyTheme(root = document.documentElement) {
  for (const [name, value] of Object.entries(VARIABLES)) {
    root.style.setProperty(name, value)
  }
}

/**
 * What this file writes for one variable, or undefined if it writes none.
 *
 * Settings are the layer above the theme and land on the same :root, so a
 * setting that stops overriding has to put the theme's value back rather than
 * delete the property, deleting takes the theme's own value with it.
 */
export const themeVariable = (name) => VARIABLES[name]

/** Look up a themed colour with a guaranteed fallback, e.g. colorFor('role', 'fail'). */
export function colorFor(group, key) {
  const table = theme[group] ?? {}
  return table[key] ?? table.default ?? theme.color['text-dim']
}

export const { motion } = theme
export default theme
