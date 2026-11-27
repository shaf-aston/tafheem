/**
 * Reader: open a book of your own and read it page by page.
 *
 * The book stays on this device (lib/reader/pdfSource.js); nothing is sent.
 * Next steps (docs/plans/2026-11-27-reader-tab.md): the library remembers
 * books, then notes, then the class follow-along.
 */
import { useEffect, useRef, useState } from 'react'

import { accentOf } from '../../lib/nav/tabs'
import { openPdf } from '../../lib/reader/pdfSource'

import SectionHeader from '../ui/display/SectionHeader'
import PrimaryButton from '../ui/buttons/PrimaryButton'
import EmptyState from '../ui/feedback/EmptyState'
import BookView from './BookView'

export default function ReaderPanel() {
  const [open, setOpen] = useState(null) // { book, name }
  const [error, setError] = useState('')
  const [opening, setOpening] = useState(false)
  const input = useRef(null)

  useEffect(() => () => open?.book.close(), [open])

  const picked = async (file) => {
    setOpening(true)
    setError('')
    try {
      setOpen({ book: await openPdf(file), name: file.name })
    } catch {
      setError(`${file.name} could not be opened as a PDF.`)
    } finally {
      setOpening(false)
    }
  }

  return (
    <div className="panel space-y-5">
      <SectionHeader tab="reader" />
      <div className="max-w-xs">
        <PrimaryButton accent={accentOf('reader')} loading={opening} onClick={() => input.current?.click()}>
          {open ? 'Open another book' : 'Open a PDF'}
        </PrimaryButton>
        <input
          ref={input}
          type="file"
          accept="application/pdf,.pdf"
          hidden
          onChange={(event) => {
            const file = event.target.files?.[0]
            event.target.value = ''
            if (file) picked(file)
          }}
        />
      </div>
      {error && <p role="alert" className="type-body text-[var(--text-dim)]">{error}</p>}
      {open
        ? <BookView key={open.name} book={open.book} name={open.name} />
        : <EmptyState detail="It opens on this device and is never uploaded.">Open a PDF to read it here.</EmptyState>}
    </div>
  )
}
