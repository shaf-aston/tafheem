/**
 * Reader: open a book of your own and read it page by page.
 *
 * Books stay on this device (lib/reader/library.js keeps them, pdfSource.js
 * draws them); nothing is sent. The library reopens each at the page it was
 * left on. Next steps: docs/plans/2026-11-27-reader-tab.md.
 */
import { useCallback, useEffect, useRef, useState } from 'react'

import { accentOf } from '../../lib/nav/tabs'
import { openPdf } from '../../lib/reader/pdfSource'
import { addBook, keepPage, listBooks, removeBook, touchBook } from '../../lib/reader/library'

import SectionHeader from '../ui/display/SectionHeader'
import PrimaryButton from '../ui/buttons/PrimaryButton'
import SmallButton from '../ui/buttons/SmallButton'
import EmptyState from '../ui/feedback/EmptyState'
import BookView from './BookView'
import Library from './Library'

export default function ReaderPanel() {
  const [books, setBooks] = useState(null) // null while the library loads
  const [open, setOpen] = useState(null) // { book, name, id, start }
  const [error, setError] = useState('')
  const [opening, setOpening] = useState(false)
  const input = useRef(null)

  const reload = () => listBooks().then(setBooks, () => setBooks([]))
  useEffect(() => { reload() }, [])
  useEffect(() => () => open?.book.close(), [open])

  /** Open a book from the library, or a file just picked (which joins the library). */
  const read = async (from, kept) => {
    setOpening(true)
    setError('')
    try {
      const book = kept ?? await addBook(from)
      if (kept) touchBook(kept.id)
      setOpen({ book: await openPdf(book.file), name: book.name, id: book.id, start: book.page })
    } catch {
      setError(`${(kept ?? from).name} could not be opened as a PDF.`)
    } finally {
      setOpening(false)
      reload()
    }
  }

  const onPage = useCallback((page) => open && keepPage(open.id, page), [open])

  return (
    <div className="panel space-y-5">
      <SectionHeader tab="reader" />
      <div className="flex flex-wrap items-center gap-3">
        <div className="w-full max-w-xs">
          <PrimaryButton accent={accentOf('reader')} loading={opening} onClick={() => input.current?.click()}>
            Open a PDF
          </PrimaryButton>
        </div>
        {open && <SmallButton onClick={() => { setOpen(null); reload() }}>Your books</SmallButton>}
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0]
            event.target.value = ''
            if (file) read(file)
          }}
        />
      </div>
      {error && <p role="alert" className="type-body text-[var(--text-dim)]">{error}</p>}
      {open && <BookView key={open.id + open.start} book={open.book} name={open.name} start={open.start} onPage={onPage} />}
      {!open && books?.length > 0 && (
        <Library books={books} onOpen={(book) => read(null, book)} onRemove={(book) => removeBook(book.id).then(reload)} />
      )}
      {!open && books?.length === 0 && (
        <EmptyState detail="It stays on this device and is never uploaded.">Open a PDF to read it here.</EmptyState>
      )}
    </div>
  )
}
