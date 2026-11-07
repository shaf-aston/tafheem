// The plain shapes the board drawings share: soft fills and lines in theme colours, so they read in light and dark.
export const SOFT = { fill: 'var(--surface-hi)', stroke: 'var(--border-hi)', strokeWidth: 1.5 }
export const LINE = { fill: 'none', stroke: 'var(--border-hi)', strokeWidth: 2, strokeLinecap: 'round', strokeLinejoin: 'round' }
export const FAINT = { fill: 'var(--text-faint)' }
export const LABEL = { fill: 'var(--text-dim)', textAnchor: 'middle', fontFamily: 'inherit' }
// The thing being placed in a position panel: one colour, so the eye finds it at once.
export const BALL = { fill: 'var(--warn)', stroke: 'color-mix(in oklab, var(--warn) 60%, black)', strokeWidth: 1 }
