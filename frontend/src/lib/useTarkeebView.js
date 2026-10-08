import { useState } from 'react'

import { runs } from './tarkeebLayout'

/**
 * How one tarkeeb chart is being looked at: split into the pieces of each written word
 * or merged back to whole words, and shown larger or not. Held by whoever draws the
 * chart's header, so the controls sit beside that header's own buttons and the figure
 * below carries none of its own.
 *
 * `canSplit` is false for a chart with no written word cut into pieces, where the two
 * views are the same picture.
 */
export function useTarkeebView(tarkeeb) {
  const [mode, setMode] = useState('split')
  const [big, setBig] = useState(false)
  const canSplit = !!tarkeeb?.written && runs(tarkeeb.words, tarkeeb.written).length < tarkeeb.words.length
  return { mode, setMode, big, setBig, canSplit }
}
