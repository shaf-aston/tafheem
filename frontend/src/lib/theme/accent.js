/**
 * Whose accent a speaker icon speaks in. A Colloquial dialect wraps its lessons
 * in it, so every SpeakButton inside says its lines in that dialect's own voice
 * with nothing passed down by hand; outside one it is null, the Fusha voice.
 */
import { createContext, useContext } from 'react'

export const Accent = createContext(null)
export const useAccent = () => useContext(Accent)
