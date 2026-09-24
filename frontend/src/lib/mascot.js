/**
 * The only module that reads mascot.json.
 *
 * Mirrors theme.js: config in one file, one reader, components ask this module
 * rather than importing the JSON themselves.
 */
import config from '../mascot.json'

export const captionFor = (mood) => config.captions[mood] ?? config.captions.idle

export const sizeRem = (place) => config['size-rem'][place] ?? config['size-rem'].header

export const streakAt = config['streak-at']
