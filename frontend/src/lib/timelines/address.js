/**
 * A place in the Timelines tab written as text after ?q=, read back, and named
 * the way a reader would say it.
 */
import { AYAH_REF } from '../quran/surahRef'

/**
 * A place in the tab as written after ?q=: "seerah", "seerah/hijrah", or
 * "seerah/badr/asbab/8:9" for one report on why an ayah came down.
 * Anything naming a section or event that does not exist is null, so a stale
 * link opens the tab plainly rather than half-open on nothing.
 */
export function parsePlace(q, sections) {
  if (!q) return null
  const [sectionId, eventId, word, ref, ...rest] = q.split('/')
  const section = sections.find((s) => s.id === sectionId)
  if (!section || rest.length) return null
  if (eventId === undefined) return { section: section.id, event: null, report: null }
  if (!section.events.some((e) => e.id === eventId)) return null
  if (word === undefined) return { section: section.id, event: eventId, report: null }
  if (word !== 'asbab' || !AYAH_REF.test(ref ?? '')) return null
  return { section: section.id, event: eventId, report: ref }
}


/** The address of a place, the inverse of parsePlace. */
export const placeOf = (section, event, report) => (
  report ? `${section}/${event}/asbab/${report}` : event ? `${section}/${event}` : section
)

/** A place as a reader names it: the event's title, else the section's name, the address itself when neither exists. */
export function nameOfPlace(q, sections) {
  const place = parsePlace(q, sections)
  const section = sections.find((s) => s.id === place?.section)
  if (!section) return q
  const event = section.events.find((e) => e.id === place.event)
  return event ? (place.report ? `${event.title} ${place.report}` : event.title) : section.name
}
