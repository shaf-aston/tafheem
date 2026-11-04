// Daleel: find the quotation.
import { api } from './client'

// Find the quotation. One question in, passages out; the backend never answers
// the question, so nothing here has an answer field to render. `books` narrows
// it to those books by name; empty is every book, which is the ordinary case.
// `limit` is how many passages; left out, the server's own page size.
export const findDaleel = ({ q, books = [], limit }) =>
  api
    .get('/daleel', {
      params: { q, books, limit },
      // One `books=` per book. Left alone, axios writes `books[]=` and the
      // backend reads no books at all, so every filtered search quietly
      // searched the whole library instead.
      paramsSerializer: { indexes: null },
    })
    .then((r) => r.data)

// Which books the search can be narrowed to. Read from the built index, so a
// book is only offered if searching it would actually find something.
export const daleelBooksQuery = {
  queryKey: ['daleel-books'],
  queryFn: () => api.get('/daleel/books').then((r) => r.data),
}
