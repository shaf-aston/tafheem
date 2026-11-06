/**
 * The rest of a Maqayees entry in English, fetched when the reader opens it.
 *
 * Three shapes from the backend, one per view of the card: the entry cut into
 * its words (Word by word), retold as prose (Together), and one English line
 * per Arabic line (One at a time).
 */
import { useQuery } from '@tanstack/react-query'

import { ENGLISH, SHAPE, englishQuery } from '../../lib/dictionary/entryEnglish'

import { LineSpotlight } from './EntryLines'
import EntryWords from './EntryWords'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import { Skeleton } from '../ui/feedback/Skeleton'
import MachineEnglish from './MachineEnglish'

/**
 * The rest of the entry in English, fetched when the reader opens it.
 *
 * Words: each word the entry explains beside its lines. Together: the entry
 * retold as prose under the Arabic. One at a time: one English
 * line for each Arabic line; the backend does the pairing and refuses an answer it
 * could not line up, so every English line belongs to the Arabic above it.
 * Each carries its own badge saying a machine wrote it, and never replaces
 * the Arabic beside it.
 */
export default function EntryEnglish({ view, root, accent }) {
  // 'lines' and 'one' are two ways to read the same pairs: one entry, one query.
  const english = ENGLISH[SHAPE[view]]
  const { data, isPending, isError, error, refetch } = useQuery(englishQuery(english, root))

  // Said in words, not only drawn: a root whose English is not kept is put into
  // English while the reader waits, a few seconds, and two grey bars alone read
  // as a page that has stuck.
  if (isPending) {
    return (
      <div className="space-y-2" role="status">
        <p className="type-small text-[var(--text-faint)]">Putting the entry into English…</p>
        <Skeleton className="h-4 w-3/4" />
        <Skeleton className="h-3 w-1/2" />
      </div>
    )
  }

  if (isError) {
    return (
      <ErrorAlert title={english.failed} error={error} fallback={english.fallback} onRetry={refetch}>
        {english.after}
      </ErrorAlert>
    )
  }

  if (!(data?.english || data?.lines?.length || data?.senses?.length)) return null

  return (
    <MachineEnglish source={data.source} wide={view === 'words'}>
      {/* The longest entries run past what the model is handed. Saying so is the
          difference between a short retelling and a retelling that stops. */}
      {data.truncated && (
        <p className="type-small text-[var(--text-faint)]">
          The entry was longer than could be read at once, so this covers its opening.
        </p>
      )}
      {view === 'words' && <EntryWords senses={data.senses} accent={accent} />}
      {view === 'one' && <LineSpotlight lines={data.lines} accent={accent} />}
      {view === 'together' && (
        <p className="type-body text-[var(--text)] whitespace-pre-line">
          {data.english}
        </p>
      )}
    </MachineEnglish>
  )
}
