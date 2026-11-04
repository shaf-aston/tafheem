/**
 * The shapes of a Maqayees entry's English the card can ask for, as queries.
 * Shared by the view that shows them (components/dictionary/EntryEnglish) and
 * the card that prefetches them on the press that opens the rest.
 */
import { getRootEntryEnglish, getRootEntryLines, getRootEntrySenses } from '../../api'

/** Said when the backend stops answering mid-visit. */
const STOPPED = 'The backend may have stopped since this page was opened.'

/**
 * The rest of the entry in English, in three shapes (one per view, see SHAPE).
 * Together is kept for every root, so a failure there is real and the message
 * offers to try again. Words and lines are kept for fewer, so they are often
 * made on the spot. The server asks again for words itself, a chunk at a time;
 * lines it does not, and fails a first try often enough that one more is worth it.
 */
export const ENGLISH = {
  words: {
    key: 'root-entry-senses',
    get: getRootEntrySenses,
    failed: "Couldn't find the words in the entry",
    fallback: STOPPED,
    after: ' The Together view still shows the whole entry.',
  },
  together: {
    key: 'root-entry-english',
    get: getRootEntryEnglish,
    failed: "Couldn't put this into English",
    fallback: 'The Arabic below is unaffected.',
  },
  lines: {
    key: 'root-entry-lines',
    get: getRootEntryLines,
    failed: "Couldn't line the English up",
    fallback: STOPPED,
    after: ' The Together view still shows the whole entry.',
    retry: 1,
  },
}

/** One shape of the English as a query, shared by the fetch and the prefetch. */
export const englishQuery = (english, root) => ({
  queryKey: [english.key, root],
  queryFn: () => english.get(root),
  retry: english.retry ?? false,
})

/** Which shape of English each view reads. */
export const SHAPE = { words: 'words', together: 'together', one: 'lines' }
