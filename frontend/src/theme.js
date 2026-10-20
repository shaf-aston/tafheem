/**
 * The only module that reads theme.json.
 *
 * Every group in the config becomes CSS custom properties named `--<group>-<key>`
 * (the `color` group drops its prefix, so `color.bg` is just `--bg`). Components
 * then reference `var(--role-fail)` and never a literal colour, which is what
 * makes the whole look editable from one file.
 *
 * A look is the groups as written with a named theme's overrides laid over,
 * key by key, except the toned groups (palette, pbs), which each look tones for its own grounds
 * (lib/tone.js). Switching looks rewrites the same variables on :root, so
 * nothing downstream knows there is more than one.
 */
import theme from './theme.json'
import { tonePalette } from './lib/tone'

const UNPREFIXED_GROUP = 'color'
const PRIVATE_KEY = '_'
const PALETTE_GROUP = 'palette'
/** Groups whose colours each look tones (lib/tone.js); their other keys pass through. */
const TONED_GROUPS = [PALETTE_GROUP, 'pbs']
const isColor = (value) => typeof value === 'string' && value.startsWith('#')
const THEMES_GROUP = 'themes'
const REFERENCE = '@'

const { base: BASE_THEME, 'hint-key': HINT_KEY, device: DEVICE, looks: LOOKS, tone: TONE } = theme[THEMES_GROUP]

/** The look the groups in theme.json describe, and what the landing page always wears. */
export { BASE_THEME }

/** Every look there is, in file order. Nothing else in the code names one. */
export const THEME_NAMES = Object.keys(LOOKS)

/** The reader's choices for Settings: each look, then "follow the device". */
export const themeChoices = () => [
  ...THEME_NAMES.map((id) => ({ id, label: LOOKS[id].label })),
  { id: DEVICE.choice, label: DEVICE.label },
]

const isPrivate = (key) => key.startsWith(PRIVATE_KEY)
const isReference = (value) => typeof value === 'string' && value.startsWith(REFERENCE)

/** What a token is written as in CSS: a pointer at a palette colour stays a pointer. */
const cssValue = (value) =>
  isReference(value) ? `var(${variableName(PALETTE_GROUP, value.slice(1))})` : String(value)

const withoutPrivate = (values) => Object.fromEntries(Object.entries(values).filter(([key]) => !isPrivate(key)))

/** A toned group as one look wears it: every colour toned for its grounds, then the look's exceptions. */
const toned = {}
function tonedOf(group, name) {
  const look = LOOKS[name] ?? {}
  const color = { ...theme.color, ...look.color }
  const values = withoutPrivate(theme[group])
  toned[`${group}/${name}`] ??= {
    ...values,
    ...tonePalette(
      Object.fromEntries(Object.entries(values).filter(([, value]) => isColor(value))),
      { ...TONE, ...look.tone },
      [color.bg, color.surface, color['surface-hi']],
      look.scheme === 'dark',
    ),
    ...look[group],
  }
  return toned[`${group}/${name}`]
}

/** The groups and keys of one look, in file order: [group, [[key, cssValue]...]]. */
function groupsOf(name) {
  return Object.entries(theme)
    .filter(([group, values]) => !isPrivate(group) && group !== THEMES_GROUP && typeof values === 'object')
    .map(([group, values]) => [
      group,
      Object.entries(TONED_GROUPS.includes(group) ? tonedOf(group, name) : { ...values, ...LOOKS[name]?.[group] })
        .filter(([key]) => !isPrivate(key))
        .map(([key, value]) => [key, cssValue(value)]),
    ])
}

let active = BASE_THEME

/** The groups of the look on screen (or of `name`), e.g. for the Kit's token cards. */
export const tokenGroups = (name = active) => groupsOf(name)

/** The CSS variable a token is written to, e.g. variableName('role', 'fail') is --role-fail. */
export const variableName = (group, key) =>
  `--${group === UNPREFIXED_GROUP ? '' : `${group}-`}${key}`

const variablesByTheme = {}
function variablesOf(name) {
  variablesByTheme[name] ??= Object.fromEntries(
    groupsOf(name).flatMap(([group, entries]) =>
      entries.map(([key, value]) => [variableName(group, key), value]),
    ),
  )
  return variablesByTheme[name]
}

const schemeOf = (name) => LOOKS[name].scheme

/** Which look a reader's choice means right now: the device choice asks the device. */
export function resolveTheme(choice, prefersLight = globalThis.matchMedia?.('(prefers-color-scheme: light)').matches) {
  if (choice === DEVICE.choice) return prefersLight ? DEVICE.light : DEVICE.dark
  return choice in LOOKS ? choice : BASE_THEME
}

/**
 * The choice a reader starts on: whatever their phone or computer is set to.
 * Someone whose device is light is not to be met with dark until they find
 * Settings, which is what a dark default did.
 */
export const FIRST_CHOICE = DEVICE.choice

/** Whether a stored choice is the device one, which has to be re-asked when the device changes. */
export const followsDevice = (choice) => choice === DEVICE.choice

/** Run `listener` whenever the device switches between light and dark. */
export function followDevice(listener) {
  globalThis.matchMedia?.('(prefers-color-scheme: light)').addEventListener('change', listener)
}

/**
 * Write one look onto :root. Called at startup and whenever the look changes.
 *
 * Besides the variables, the page itself is told: data-theme for any rule that
 * wants it, color-scheme so the browser's own controls match, and the
 * address-bar colour.
 */
export function applyTheme(root = document.documentElement, name = BASE_THEME) {
  active = name in LOOKS ? name : BASE_THEME
  const variables = variablesOf(active)
  for (const [property, value] of Object.entries(variables)) root.style.setProperty(property, value)

  const doc = root.ownerDocument
  if (!doc) return
  root.dataset.theme = active
  root.style.colorScheme = schemeOf(active)
  doc.querySelector('meta[name="theme-color"]')?.setAttribute('content', variables['--bg'])
}

/**
 * Keep the reader's choice where the next page load can see it before any script
 * runs. Only the app calls this: the landing page always wears the dark look and
 * must not overwrite what the reader chose here.
 */
export function rememberTheme(choice) {
  try {
    localStorage.setItem(HINT_KEY, choice)
  } catch {
    // Private browsing: the first paint is the dark ground, then the right one.
  }
}

/**
 * What this file writes for one variable on the look on screen, or undefined.
 *
 * Settings are the layer above the theme and land on the same :root, so a
 * setting that stops overriding has to put the theme's value back rather than
 * delete the property, deleting takes the theme's own value with it.
 */
export const themeVariable = (name) => variablesOf(active)[name]

/**
 * A themed colour as a CSS value, with a guaranteed fallback, e.g.
 * colorFor('role', 'fail'). A palette colour comes back as var(--palette-…), so
 * whatever it is put on follows the look on screen, including after a switch.
 */
export function colorFor(group, key) {
  const table = theme[group] ?? {}
  if (TONED_GROUPS.includes(group) && isColor(table[key])) return `var(${variableName(group, key)})`
  return cssValue(table[key] ?? table.default ?? theme.color['text-dim'])
}

/** The nth colour of a theme group, wrapping round (colorFor's fallback if it has none), e.g. colorAt('unit', 9) is the unit group's second. */
export function colorAt(group, n) {
  const colors = Object.entries(theme[group] ?? {}).filter(([key]) => !isPrivate(key))
  return colors.length ? cssValue(colors[n % colors.length][1]) : colorFor(group, n)
}

export const { motion } = theme
export default theme
