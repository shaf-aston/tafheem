/**
 * The three answers the backend can give about the classical root book.
 *
 * These are backend/services/root_meaning.py's own names, written down once here
 * rather than retyped as bare text everywhere that reads them, a rename on one
 * side used to be a four-file edit across two languages with nothing to catch a
 * miss, and a miss shows the reader the wrong sentence.
 *
 * Three states rather than a flag, because the difference between them is the
 * whole point:
 *
 *   MISSING, no book on this machine. Nothing can be said about any root.
 *   BROKEN: a file is there and could not be read. Something is wrong; say so.
 *   READY: loaded, so a root with no entry really has no entry.
 *
 * "We do not have the book" must never be shown as "this root has no origin
 * sense". They are different sentences and they are never allowed to look alike.
 */
export const MISSING = 'missing'
export const BROKEN = 'broken'
export const READY = 'ready'
