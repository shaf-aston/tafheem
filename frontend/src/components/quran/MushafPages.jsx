/**
 * A surah as the pages of one printed mushaf: every whole page it is on, line
 * for line as printed, in the printing's own face (QPC Hafs for the Madani
 * print). A page it shares shows the other surah's lines too, as the print does.
 *
 * Each page is drawn at one font size, the largest its widest line fits at
 * (lib/mushafFit), measured once the face has loaded. Tapping a word studies its
 * ayah, as tapping a row does in the list; one of another surah opens that surah.
 */
import { useEffect, useLayoutEffect, useMemo, useRef, useState } from 'react'
import { useQuery } from '@tanstack/react-query'

import { mushafPagesQuery } from '../../api'
import surahs from '../../data/surahs.json'
import { isCentred, pageFontPx, wordsOf } from '../../lib/mushafFit'
import { themeVariable } from '../../theme'
import ErrorAlert from '../ui/ErrorAlert'
import { Skeleton } from '../ui/Skeleton'

const knob = (key) => Number(themeVariable(`--mushaf-${key}`))
const BASMALA = 'بِسۡمِ ٱللَّهِ ٱلرَّحۡمَٰنِ ٱلرَّحِيمِ'
const END_MARK = /^[٠-٩]+$/

/** The face a printing's script is drawn in, as styles/components.css names it. */
const faceOf = (box) => getComputedStyle(box).fontFamily

/** Each ayah line's width at the measuring size, with the least room between its words. */
function measureLines(lines, face) {
  const pen = document.createElement('canvas').getContext('2d')
  if (!pen) return []
  const size = knob('measure-px')
  pen.font = `${size}px ${face}`
  return lines.filter(([kind]) => kind === 'ayah').map(([, runs]) => {
    const words = runs.flatMap(([, , text]) => wordsOf(text))
    return words.reduce((sum, word) => sum + pen.measureText(word).width, 0) + (words.length - 1) * knob('gap-em') * size
  })
}

function Line({ line, open }) {
  const [kind, value] = line
  if (kind === 'surah') {
    return <div className="mushaf-line mushaf-name"><span>سُورَةُ {surahs[value - 1]?.ar}</span></div>
  }
  if (kind === 'basmala') return <div className="mushaf-line mushaf-basmala">{BASMALA}</div>
  return (
    <div className="mushaf-line">
      {value.flatMap(([surah, ayah, text]) => wordsOf(text).map((word, i) => {
        const here = open?.surah === surah && open?.ayah === ayah
        const props = { 'data-surah': surah, 'data-ayah': ayah, 'data-open': here || undefined, className: 'mushaf-word' }
        return END_MARK.test(word)
          ? <button key={`${ayah}-${i}`} type="button" {...props} aria-label={`Study ${surah}:${ayah}`}>{word}</button>
          : <span key={`${ayah}-${i}`} {...props}>{word}</span>
      }))}
    </div>
  )
}

function Page({ page, lines, width, face, open }) {
  const natural = useMemo(() => (face ? measureLines(lines, face) : []), [lines, face])
  const px = pageFontPx(natural, width, { measure: knob('measure-px'), fill: knob(isCentred(page) ? 'centred-fill' : 'fill') })
  return (
    <section aria-label={`Page ${page}`} data-page={page} data-centred={isCentred(page) || undefined}
      className="mushaf-page" style={px ? { fontSize: `${px}px` } : undefined}>
      {lines.map((line, i) => <Line key={i} line={line} open={open} />)}
      <footer className="mushaf-folio">{page}</footer>
    </section>
  )
}

export default function MushafPages({ printing, surah, open, onOpen, className = '' }) {
  const { data, isPending, isError, error, refetch } = useQuery(mushafPagesQuery(printing.id, surah))
  const box = useRef(null)
  const [width, setWidth] = useState(0)
  const [face, setFace] = useState('')

  // The width every page shares, and the face once it can be measured in: a
  // line measured in the fallback face would be sized for letters not drawn.
  useLayoutEffect(() => {
    const node = box.current
    if (!node) return undefined
    const watch = new ResizeObserver(([entry]) => setWidth(entry.contentRect.width))
    watch.observe(node)
    const family = faceOf(node)
    let live = true
    document.fonts?.load(`${knob('measure-px')}px ${family}`).then(() => live && setFace(family), () => live && setFace(family))
    return () => { live = false; watch.disconnect() }
  }, [data])

  // Opened at an ayah, the page it is on is the one shown.
  const shown = useRef(false)
  useEffect(() => {
    if (shown.current || !data || !open) return
    shown.current = true
    box.current?.querySelector(`[data-surah="${open.surah}"][data-ayah="${open.ayah}"]`)?.closest('section')?.scrollIntoView({ block: 'start' })
  }, [data, open])

  const tap = (e) => {
    const word = e.target.closest?.('[data-ayah]')
    if (word) onOpen({ surah: Number(word.dataset.surah), ayah: Number(word.dataset.ayah) })
  }

  if (isError) {
    return <div className="p-4"><ErrorAlert title="The pages could not be read" error={error} fallback="The ayah list still works." onRetry={() => refetch()} /></div>
  }
  if (isPending) {
    return <div className="p-4 space-y-3">{Array.from({ length: 8 }, (_, i) => <Skeleton key={i} className="h-8 w-full" />)}</div>
  }
  return (
    <div className={`scroll-pane ${className}`}>
      <div ref={box} lang="ar" dir="rtl" data-script={printing.script} onClick={tap} className="mushaf">
        {data.pages.map(({ page, lines }) => (
          <Page key={page} page={page} lines={lines} width={width} face={face} open={open} />
        ))}
      </div>
    </div>
  )
}
