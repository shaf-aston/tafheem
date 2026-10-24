/**
 * The CSS color-scheme a look asks for. "only" stops a phone's forced dark mode
 * (Android Chrome's auto-dark) repainting a light look: without it a dark device
 * turned Parchment brown. One place, read by theme.js and the boot script.
 */
export const colorScheme = (scheme) => `only ${scheme}`
