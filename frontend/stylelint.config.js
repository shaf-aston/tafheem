// The house rules for styles, the CSS counterpart of the className rules in eslint.config.js
// (CORE-FLOW.md, "Open first": a number is a token, never a literal in a component or sheet).
// npm run lint:css
const RADIUS = ['/(^|[\\s(])(-?[6-9]|\\d{2,})(\\.\\d+)?px\\b/', '/(^|[\\s(])-?\\d*\\.?\\d+(rem|em)\\b/']
const TEXT = ['/^-?\\d*\\.?\\d+(px|rem)$/']
const STACK = ['/^(?!-?[0-2]$)-?\\d+$/']
const MESSAGE = 'House rule (CORE-FLOW, "Open first"): a radius is var(--radius-*), a text size var(--type-*), '
  + 'a stacking order var(--layer-*). Corners up to 5px (a thin bar, a tick) and a local z-index of -1 to 2 '
  + 'inside an isolated box are allowed.'

const rule = (properties) => [properties, { message: MESSAGE }]
const radius = { '/^border(-.+)?-radius$/': RADIUS }

export default {
  rules: {
    'declaration-property-value-disallowed-list': rule({ ...radius, 'font-size': TEXT, 'z-index': STACK }),
  },
  overrides: [
    {
      // The welcome page is its own page with its own stacking (a cursor blob over everything, layers inside
      // one sticky story) and its own display type (clamp()ed sizes, tiny chip labels, the root 16px).
      // Radii still follow the tokens.
      files: ['src/landing/**/*.css'],
      rules: { 'declaration-property-value-disallowed-list': rule(radius) },
    },
    {
      // Grow's lesson skin sets the size of the Arabic on each card (3.4rem, 4.5rem...) on its own ladder:
      // --type-* is the ladder for Latin interface text. A non-Arabic size here still takes a token.
      files: ['src/styles/growWorlds.css'],
      rules: { 'declaration-property-value-disallowed-list': rule({ ...radius, 'z-index': STACK }) },
    },
  ],
}
