/**
 * How a timeline is labelled: each section's picture and hue, event pictures,
 * and the words printed where a date or a place needs qualifying.
 */
import settings from '../../timelines.json'

const { sections: LOOKS, 'event-icons': EVENT_ICONS } = settings

/** A section's picture and hue, from timelines.json; an unlisted section wears `unknown`. */
export const sectionLook = (id) => LOOKS[id] ?? LOOKS.unknown

/** The picture on the k-th event card of a section: the config's set, cycled. */
export const eventIcon = (k) => EVENT_ICONS[k % EVENT_ICONS.length]

/** The flag that says a place is known from tradition; printed beside the place, not as a pill. */
export const TRAD = 'tradplace'

/** Said where a section gives dates and this event has none a source states. */
export const NO_DATE = 'No sourced date'

/** Whether any event in the section carries a sourced date. */
export const isDated = (section) => section.events.some((e) => e.dates.length > 0)
