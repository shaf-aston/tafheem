import { useState } from 'react'

// What this page session has already shown. A list entrance plays the first
// time it is seen; coming back to cached data appears at once.
const seen = new Set()

export const firstSight = (key) => !seen.has(key) && !!seen.add(key)

export const useFirstSight = (key) => useState(() => firstSight(key))[0]
