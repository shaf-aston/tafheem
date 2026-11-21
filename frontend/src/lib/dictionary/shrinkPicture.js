/**
 * A picture made small enough to send quickly, before it leaves the device.
 *
 * A phone photo is three to twelve megabytes, most of it detail no reader
 * needs: at send-longest pixels on its long side Tesseract reads print as well
 * as at full size, and the upload is about half a megabyte. Drawn the way up
 * the camera meant (imageOrientation). Anything the browser cannot draw (an
 * old browser, a format it does not know) goes as it came, and the server
 * says whether it can read it.
 */
import config from '../../config/dictionary.json'

const LONGEST = config.page['send-longest']
const QUALITY = config.page['send-quality']
// Small already and in a format every reader takes: sent untouched, so a crisp screenshot stays a PNG.
const SMALL_BYTES = 1_500_000
const AS_IS = new Set(['image/png', 'image/jpeg', 'image/webp'])

export async function shrinkPicture(file) {
  try {
    const bitmap = await createImageBitmap(file, { imageOrientation: 'from-image' })
    const scale = Math.min(1, LONGEST / Math.max(bitmap.width, bitmap.height))
    if (scale === 1 && file.size <= SMALL_BYTES && AS_IS.has(file.type)) return file
    const canvas = document.createElement('canvas')
    canvas.width = Math.round(bitmap.width * scale)
    canvas.height = Math.round(bitmap.height * scale)
    const paint = canvas.getContext('2d')
    paint.fillStyle = 'white' // a clear background is a light page, not a black one
    paint.fillRect(0, 0, canvas.width, canvas.height)
    paint.drawImage(bitmap, 0, 0, canvas.width, canvas.height)
    bitmap.close?.()
    const blob = await new Promise((done) => canvas.toBlob(done, 'image/jpeg', QUALITY))
    return blob ? new File([blob], 'page.jpg', { type: 'image/jpeg' }) : file
  } catch {
    return file
  }
}

/** The first picture among what was pasted or dropped, or null. */
export const pictureIn = (transfer) => [...(transfer?.files ?? [])].find((file) => file.type.startsWith('image/')) ?? null
