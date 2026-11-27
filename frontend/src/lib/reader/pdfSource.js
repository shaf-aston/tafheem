/**
 * A book the reader opened, as pages to draw. The only file that knows pdf.js,
 * so a different engine (or a photo as a one-page book) is a change here alone.
 *
 * The file never leaves the device: pdf.js reads it in the browser, one page at
 * a time, so a 300-page scan opens as fast as a short one.
 */
import { GlobalWorkerOptions, getDocument } from 'pdfjs-dist'
import worker from 'pdfjs-dist/build/pdf.worker.min.mjs?url'

GlobalWorkerOptions.workerSrc = worker

/** Open a PDF File. Resolves { pages, draw(n, canvas, width, height), close() }; rejects on a file that is no PDF. */
export async function openPdf(file) {
  const task = getDocument({ data: new Uint8Array(await file.arrayBuffer()) })
  const doc = await task.promise
  let drawing = null
  return {
    pages: doc.numPages,
    /** Draw page `n` (from 1) into `canvas`, as large as fits `width` and, if given, `height` CSS
     *  pixels, sharp on a dense screen. */
    async draw(n, canvas, width, height = Infinity) {
      drawing?.cancel()
      const page = await doc.getPage(n)
      const flat = page.getViewport({ scale: 1 })
      const fit = Math.min(width / flat.width, height / flat.height)
      const viewport = page.getViewport({ scale: fit * devicePixelRatio })
      canvas.width = viewport.width
      canvas.height = viewport.height
      canvas.style.width = `${Math.floor(flat.width * fit)}px`
      drawing = page.render({ canvas, viewport })
      try {
        await drawing.promise
      } catch (error) {
        if (error?.name !== 'RenderingCancelledException') throw error // a newer page took its place
      }
    },
    close: () => task.destroy(), // the loading task owns the worker; the document has no destroy of its own
  }
}
