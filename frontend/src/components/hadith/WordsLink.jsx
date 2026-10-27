/**
 * "Words and terms": the link that opens the guide to the words between narrators and the terms of the science
 * (hadith/ChainSheet with no hadith, so the words alone). It stands in the reading-options row of every list of
 * hadith, in a book, in search and in Starred, so the guide is one tap away wherever a chain is read.
 */
import { useState } from 'react'

import ChainSheet from './ChainSheet'
import SheetLink from './SheetLink'

export default function WordsLink({ accent }) {
  const [open, setOpen] = useState(false)
  return (
    <>
      <SheetLink accent={accent} onClick={() => setOpen(true)}>Words and terms</SheetLink>
      {open && <ChainSheet accent={accent} onClose={() => setOpen(false)} />}
    </>
  )
}
