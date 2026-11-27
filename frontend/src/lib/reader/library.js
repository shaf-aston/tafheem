/**
 * The reader's library: the books opened on this device and the page each was left on.
 *
 * Kept in IndexedDB, the one browser store that holds a 50 MB file; nothing is
 * uploaded. A book is { id, name, size, page, opened, file }. The same file
 * opened again (same name and size) is the same book, not a second copy.
 */
const DB = 'tafheem-reader'
const STORE = 'books'

let opening = null
const db = () => (opening ??= new Promise((resolve, reject) => {
  const request = indexedDB.open(DB, 1)
  request.onupgradeneeded = () => request.result.createObjectStore(STORE, { keyPath: 'id' })
  request.onsuccess = () => resolve(request.result)
  request.onerror = () => { opening = null; reject(request.error) }
}))

/** Run `work(store)` in one transaction; resolves with what its last request returned. */
async function inStore(mode, work) {
  const tx = (await db()).transaction(STORE, mode)
  const request = work(tx.objectStore(STORE))
  return new Promise((resolve, reject) => {
    tx.oncomplete = () => resolve(request?.result)
    tx.onerror = tx.onabort = () => reject(tx.error)
  })
}

const idOf = (file) => `${file.name}:${file.size}`

/** Every book, last opened first. */
export const listBooks = async () =>
  (await inStore('readonly', (s) => s.getAll())).sort((a, b) => b.opened - a.opened)

/** Put a picked file in the library (or find it there) and mark it opened now. Resolves the book. */
export async function addBook(file) {
  const id = idOf(file)
  const kept = await inStore('readonly', (s) => s.get(id))
  const book = { id, name: file.name, size: file.size, page: kept?.page ?? 1, opened: Date.now(), file: kept?.file ?? file }
  await inStore('readwrite', (s) => s.put(book))
  navigator.storage?.persist?.() // ask the browser not to clear it under storage pressure; a refusal changes nothing
  return book
}

/** Mark a book opened now. */
export const touchBook = async (id) => {
  const book = await inStore('readonly', (s) => s.get(id))
  if (book) await inStore('readwrite', (s) => s.put({ ...book, opened: Date.now() }))
}

/** Remember the page a book is on. */
export async function keepPage(id, page) {
  const book = await inStore('readonly', (s) => s.get(id))
  if (book && book.page !== page) await inStore('readwrite', (s) => s.put({ ...book, page }))
}

export const removeBook = (id) => inStore('readwrite', (s) => s.delete(id))
