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
const PALETTE_GROUP = 'palette'
const REFERENCE = '@'

const isReference = (value) => typeof value === 'string' && value.startsWith(REFERENCE)

/** The palette colour a token points at, as the colour itself (for script and canvas). */
const resolve = (value) => (isReference(value) ? theme[PALETTE_GROUP][value.slice(1)] : value)

/** What a token is written as in CSS: a pointer at a palette colour stays a pointer. */
const cssValue = (value) =>
  isReference(value) ? `var(${variableName(PALETTE_GROUP, value.slice(1))})` : String(value)

/** The groups and keys that become variables, in file order: [group, [[key, cssValue]...]]. */
export function tokenGroups() {
  return Object.entries(theme)
    .filter(([group, values]) => !group.startsWith(PRIVATE_KEY) && typeof values === 'object')
    .map(([group, values]) => [
      group,
      Object.entries(values)
        .filter(([key]) => !key.startsWith(PRIVATE_KEY))
        .map(([key, value]) => [key, cssValue(value)]),
    ])
}

/** The CSS variable a token is written to, e.g. variableName('role', 'fail') is --role-fail. */
export const variableName = (group, key) =>
  `--${group === UNPREFIXED_GROUP ? '' : `${group}-`}${key}`

function cssVariables() {
  const vars = {}
  for (const [group, entries] of tokenGroups()) {
    for (const [key, value] of entries) vars[variableName(group, key)] = value
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
  return resolve(table[key] ?? table.default ?? theme.color['text-dim'])
}

/** The nth colour of a theme group, wrapping round (colorFor's fallback if it has none), e.g. colorAt('unit', 9) is the unit group's second. */
export function colorAt(group, n) {
  const colors = Object.entries(theme[group] ?? {}).filter(([key]) => !key.startsWith(PRIVATE_KEY))
  return colors.length ? resolve(colors[n % colors.length][1]) : colorFor(group, n)
}

export const { motion } = theme
export default theme
