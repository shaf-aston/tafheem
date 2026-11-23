/**
 * A picture of a page handed from another place (Home, the Ask sheet) to the
 * Dictionary's page reader, which is the only place that reads one.
 *
 * Not through the tab's handed value: that is a place, written into the trail
 * and the address bar, and a File is no place. The picture waits here until the
 * Dictionary takes it, which it does as soon as it is mounted and the server has
 * said it can read pictures (DictionaryPanel). A second picture handed before
 * the first is taken replaces it: the last one chosen is the one wanted.
 */
import { useHealth } from '../api/useHealth'
import { pictureIn } from './shrinkPicture'

export const PAGE_TAB = 'dict'

let waiting = null
const listeners = new Set()

export const handPage = (file) => {
  waiting = file
  listeners.forEach((listen) => listen())
}

export const takePage = () => {
  const file = waiting
  waiting = null
  return file
}

export const onPageHanded = (listen) => {
  listeners.add(listen)
  return () => listeners.delete(listen)
}

/**
 * For a place that offers the page reader without being it: whether this server reads pictures,
 * `send(file)` to hand one over and go to the Dictionary, and `pasted`/`dropped`/`dragOver` handlers
 * that take a picture (a screenshot pasted on a laptop, a file dragged in) and leave everything else be.
 */
export function usePageHandoff(onGo) {
  const { pageReader } = useHealth()
  const canRead = Boolean(pageReader) && pageReader !== 'none'
  const send = (file) => {
    if (!file || !canRead) return
    handPage(file)
    onGo(PAGE_TAB)
  }
  const pasted = (event) => {
    const file = canRead && pictureIn(event.clipboardData)
    if (file) { event.preventDefault(); send(file) }
  }
  // Only a picture dropped here is taken; any other file is left to the browser, as before this existed.
  const dropped = (event) => {
    const file = canRead && pictureIn(event.dataTransfer)
    if (file) { event.preventDefault(); send(file) }
  }
  const dragOver = (event) => {
    if (canRead && [...(event.dataTransfer?.items ?? [])].some((item) => item.kind === 'file' && item.type.startsWith('image/'))) {
      event.preventDefault()
    }
  }
  return { canRead, send, pasted, dropped, dragOver }
}
