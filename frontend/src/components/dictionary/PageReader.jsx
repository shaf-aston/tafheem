/**
 * A picture of a page, read and translated line by line.
 *
 * Four steps, each on screen as it is done:
 *   1. the picture, shrunk on this device before it is sent (shrinkPicture)
 *   2. its text, read on the server (POST /api/read/image), in a box the reader
 *      can correct against the picture: the reading is a start, not the last word
 *   3. that text cut into lines a sentence long (pageLines)
 *   4. each line's English under it, and each word's on hover (PageLine,
 *      useLineTranslations), the dictionary's own sentence translation
 *
 * The translating starts as soon as the text arrives; a correction asks again
 * only for the lines it changed. A word looked up leaves this mounted (the
 * panel hides it), so coming back finds the page as it was left.
 */
import { useEffect, useMemo, useState } from 'react'
import { useMutation } from '@tanstack/react-query'

import { readPicture } from '../../api'
import { pageLines } from '../../lib/dictionary/pageLines'
import { shrinkPicture } from '../../lib/dictionary/shrinkPicture'
import { useLineTranslations } from '../../lib/dictionary/useLineTranslations'
import ErrorAlert from '../ui/feedback/ErrorAlert'
import SourceBadge from '../ui/feedback/SourceBadge'
import { Skeleton } from '../ui/feedback/Skeleton'
import PictureButton from '../ui/buttons/PictureButton'
import SmallButton from '../ui/buttons/SmallButton'
import PageLine from './PageLine'

export default function PageReader({ picture, shown, accent, onPicked, onClose, onLookup, onGo }) {
  const [draft, setDraft] = useState('')
  const [text, setText] = useState('')
  const reading = useMutation({
    mutationFn: async (file) => readPicture(await shrinkPicture(file)),
    onSuccess: (read) => { setDraft(read.text); setText(read.text) },
  })
  const { mutate } = reading

  // One picture for this reader's life: the panel keys it by the picture, so a new one starts afresh.
  useEffect(() => { mutate(picture) }, [picture, mutate])

  const lines = useMemo(() => pageLines(text).map((line, i, all) => (
    { ...line, opensParagraph: i > 0 && line.paragraph !== all[i - 1].paragraph })), [text])
  const found = useLineTranslations(lines)
  const done = lines.filter((line) => found[line.text]?.state === 'done').length
  const read = reading.data

  return (
    <section aria-labelledby="page-reader-h" className="flex flex-col gap-4">
      <header className="flex items-center gap-x-3 gap-y-2 flex-wrap">
        <h3 id="page-reader-h" className="eyebrow">Page reader</h3>
        {read && <SourceBadge source={read.source} />}
        {lines.length > 0 && (
          <p className="type-small text-[var(--text-faint)] tabular-nums" aria-live="polite">
            {done < lines.length ? `${done} of ${lines.length} lines translated` : `${lines.length} lines`}
          </p>
        )}
        <div className="ms-auto flex items-center gap-2">
          <PictureButton onPicked={onPicked} title="Read another picture" />
          <SmallButton onClick={onClose}>Close</SmallButton>
        </div>
      </header>

      <div className="grid gap-5 lg:grid-cols-[minmax(0,2fr)_minmax(0,3fr)] items-start">
        <aside className="flex flex-col gap-3 min-w-0 lg:sticky lg:top-24">
          {shown && (
            <img src={shown} alt="The picture being read"
              className="w-full max-h-[45vh] lg:max-h-[60vh] object-contain rounded-[var(--radius-md)] border border-[var(--border)] bg-[var(--surface)]" />
          )}
          {read && (
            // Open when the reading was doubtful, folded otherwise: a clear page goes straight to its lines.
            <details open={read.unsure || !read.text} className="flex flex-col gap-2">
              <summary className="type-ui text-[var(--text-dim)] cursor-pointer">Text read from the picture</summary>
              {read.unsure && (
                <p className="type-small text-[var(--text-dim)] mt-2">
                  This page was hard to read. Check the text against the picture and fix what is wrong.
                </p>
              )}
              <textarea
                value={draft}
                onChange={(event) => setDraft(event.target.value)}
                dir="rtl"
                lang="ar"
                rows={8}
                aria-label="Text read from the picture"
                placeholder="No Arabic was found in the picture; type or paste it here."
                style={{ '--c': accent }}
                className="mt-2 w-full arabic p-3 rounded-[var(--radius-md)] bg-[var(--surface)] border border-[var(--border-hi)]
                  text-[var(--text)] focus:border-[var(--c)] focus:outline-none resize-y"
              />
              {draft.trim() !== text.trim() && (
                <SmallButton onClick={() => setText(draft)} className="mt-2 self-start">Translate the corrected text</SmallButton>
              )}
            </details>
          )}
        </aside>

        <div className="flex flex-col gap-3 min-w-0">
          {reading.isPending && (
            <>
              <p className="type-small text-[var(--text-dim)]" aria-live="polite">Reading the picture…</p>
              <Skeleton className="h-20" />
              <Skeleton className="h-20" />
            </>
          )}
          {reading.isError && (
            <ErrorAlert title="The picture could not be read" error={reading.error}
              fallback="Try a sharper photo, straight on, in good light." onRetry={() => mutate(picture)} />
          )}
          {read && lines.length === 0 && (
            <p className="type-body text-[var(--text-dim)]">
              No Arabic was found in this picture. Try a sharper photo, or type the text into the box.
            </p>
          )}
          {lines.length > 0 && (
            <ol className="flex flex-col gap-3">
              {lines.map((line, i) => (
                <PageLine key={`${i}:${line.text}`} line={line} found={found[line.text]} accent={accent} onLookup={onLookup} onGo={onGo} />
              ))}
            </ol>
          )}
        </div>
      </div>
    </section>
  )
}
