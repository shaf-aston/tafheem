/**
 * The backdrops a world may stand in front of (public/grow/backdrops/manifest.json).
 * One lookup for the picture and the test both, so the manifest's shape is read
 * in one place. Rule from the manifest: no humans or animals; `subject` is the
 * reviewer's word on what is in the picture.
 */
import manifest from '../../../public/grow/backdrops/manifest.json'

/** What a backdrop may show. Anything with a person or an animal in it has no word here on purpose. */
export const SUBJECTS = ['architecture', 'nature-no-animals', 'objects', 'geometry', 'calligraphy', 'sky', 'water']

/** Where the manifest's files are served from. */
const BACKDROPS_URL = '/grow/backdrops/'

/** Every backdrop by id, as the manifest has it. */
export const BACKDROPS = manifest.backdrops

const urlOf = (file) => (file ? BACKDROPS_URL + file : undefined)

/**
 * A backdrop ready to show: its `image` and, when it has a loop, `video` and
 * the `poster` to stand in for it, each a full URL. Null for an id nobody named
 * (a world with no backdrop) or one the manifest does not have.
 */
export function backdropOf(id) {
  const entry = id ? BACKDROPS[id] : undefined
  if (!entry) return null
  return {
    id,
    subject: entry.subject,
    image: urlOf(entry.poster ?? entry.file),
    video: urlOf(entry.video),
    poster: urlOf(entry.poster ?? entry.file),
  }
}
