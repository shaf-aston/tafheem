/**
 * What an ayah is about, from whichever commentary the reader is reading.
 *
 * The rest of the Qur'an tab answers what each word means and how the words
 * assemble. Neither of those says what the ayah is about, and that is the thing
 * a reader wants next. This is that, and nothing else.
 *
 * Open where one ayah is being studied, shut in the reading view. Studying an
 * ayah is asking what it is about, so it was two asks for one thing; a surah of
 * 286 ayahs, each with a commentary unfurled under it, is not a surah. Whoever
 * places the panel says which it is. Nothing is fetched while it is shut.
 *
 * One book is shown, never several stacked. Where more than one is installed
 * they sit as a single quiet row of names above the passage, so the page keeps
 * its whitespace and the other books are one click away rather than in the way.
 * The choice is remembered, because a reader who prefers one commentary prefers
 * it on the next ayah too.
 *
 * The opening and shutting is Disclosure, the app's one such control, so this
 * panel has no look of its own to keep in step with the others.
 *
 * The passage itself is cut to about twelve lines by ui/ShowRest, the same
 * fold every long passage in the app gets, nested inside the Disclosure. Tafsir runs to paragraphs;
 * without a second clamp the panel opening is a wall of text, and folding
 * the whole thing back under Disclosure would hide the badge and the
 * "covers" note along with it, which a reader wants to see before deciding
 * to expand.
 */
import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { getAyahEditions, getQuranEditions } from '../api'
import { smartError } from '../lib/apiError'
import { passageLabel } from '../lib/tafsir'
import { useRemembered } from '../lib/useRemembered'

import ArabicText from './ui/ArabicText'
import Disclosure from './ui/Disclosure'
import ErrorAlert from './ui/ErrorAlert'
import RetryButton from './ui/RetryButton'
import Segmented from './ui/Segmented'
import ShowRest from './ui/ShowRest'
import { Skeleton } from './ui/Skeleton'
import SourceBadge from './ui/SourceBadge'

/** What to call a book on a button: its short name, in its own script.
 *  Seven full titles is a wall of text to read through, so the picker uses the
 *  name a reader would say out loud and the badge below keeps the full one.
 *  Arabic goes through ArabicText, here as everywhere else, so it carries lang
 *  and dir rather than being bare text in a button.
 *
 *  The smallest rung, and inline spacing. At the reading rungs an Arabic name
 *  came out half again the size of the English one beside it and its tall line
 *  box made its button taller too, so a row of seven books stepped up and down
 *  instead of reading as one row. */
function bookLabel(book) {
  return book.language === 'ar'
    ? <ArabicText size="tiny" className="arabic-inline">{book.short}</ArabicText>
    : book.short
}

/** The books with each script kept together, English on the left and Arabic
 *  on the right, in the manifest's order within each. Nothing labels which is
 *  which, because a name written in Arabic has already said so; grouping them
 *  only saves the eye jumping between scripts four times along one row. */
function grouped(books) {
  return [...books].sort((a, b) => (a.language === 'ar' ? 1 : 0) - (b.language === 'ar' ? 1 : 0))
}

export default function AyahTafsir({ surah, ayah, accent, defaultOpen = false }) {
  const [opened, setOpened] = useState(defaultOpen)

  // Which books exist is one fact for the whole session, not one per ayah, so
  // it is keyed without the ayah and every panel on the page shares the answer.
  const { data: books = [], isFetching: findingBooks } = useQuery({
    queryKey: ['quran-editions', 'tafsir'],
    queryFn: () => getQuranEditions('tafsir'),
    enabled: opened,
    staleTime: Infinity,
  })

  const [chosen, choose] = useRemembered('tafsir-edition', books.map((book) => book.id))

  const { data, isFetching, isError, error, refetch } = useQuery({
    queryKey: ['ayah-editions', surah, ayah, chosen],
    queryFn: () => getAyahEditions(surah, ayah, [chosen]),
    enabled: opened && Boolean(chosen),
    staleTime: Infinity,
    // The text never changes, and an ayah this scholar did not comment on comes
    // back as an empty list rather than an error, so there is nothing to retry.
    retry: false,
  })

  const passage = data?.passages?.[0]
  const nothing = Boolean(data) && !passage

  return (
    <Disclosure label="Tafsir" defaultOpen={defaultOpen} onToggle={setOpened} bodyClassName="mt-2 space-y-2">
        {/* Drawn only where there is a choice to make. One book installed is not
            a picker with one option, it is no picker. */}
        {books.length > 1 && (
          <Segmented
            wrap
            label="Commentary"
            options={grouped(books).map((book) => ({ id: book.id, label: bookLabel(book) }))}
            value={chosen}
            onChange={choose}
            accent={accent}
            className="flex-wrap"
          />
        )}

        {(findingBooks || isFetching) && <Skeleton className="h-4 w-1/2" />}

        {/* Only once the book list has actually arrived. Read off the passage
            query's flag instead, this said "nothing is installed" as a fact
            while the list was still on its way, then took it back. */}
        {opened && !findingBooks && books.length === 0 && (
          <p className="type-small text-[var(--text-faint)]">
            No commentary is installed yet.
          </p>
        )}

        {nothing && (
          <p className="type-small text-[var(--text-faint)]">
            This commentary has nothing on {surah}:{ayah}.
          </p>
        )}

        {isError && (
          <ErrorAlert title="The commentary could not be read">
            {smartError(error, 'The ayah and its grammar above are unaffected.')}
            <RetryButton onClick={refetch} />
          </ErrorAlert>
        )}

        {passage && (
          <div className="space-y-2" role="status" aria-live="polite">
            {/* Said before the commentary, not after it: a reader handed four
                paragraphs about ten ayahs should know that at the top, or they
                will read it as four paragraphs about the one they clicked. */}
            {passage.covers?.length > 1 && (
              <p className="type-small text-[var(--text-faint)]">
                Written about {passageLabel(surah, passage.covers)} together.
              </p>
            )}
            <ShowRest height="calc(var(--arabic-line-height) * 12em)" accent={accent}>
              {passage.language === 'ar' ? (
                <ArabicText
                  as="p"
                  size="sm"
                  className="text-[var(--text-dim)] whitespace-pre-line"
                >
                  {passage.text}
                </ArabicText>
              ) : (
                <p
                  className="type-body text-[var(--text-dim)] leading-relaxed whitespace-pre-line"
                  style={{ unicodeBidi: 'isolate' }}
                >
                  {passage.text}
                </p>
              )}
            </ShowRest>
            <SourceBadge source={passage.source} />
          </div>
        )}
    </Disclosure>
  )
}
