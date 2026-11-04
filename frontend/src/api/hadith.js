// Hadith: collections and books, narrators (rijal), the usul guide and search.
import { keepPreviousData } from '@tanstack/react-query'

import { api } from './client'

// Every hadith collection the module can browse or search. Small and fixed,
// fetched once like timelinesQuery.
export const hadithCollectionsQuery = {
  queryKey: ['hadith-collections'],
  queryFn: () => api.get('/hadith/collections').then((r) => r.data),
}

// One collection's books (chapters), each carrying how many hadiths it holds.
export const hadithBooksQuery = (collection) => ({
  queryKey: ['hadith-books', collection],
  queryFn: () => api.get(`/hadith/${collection}/books`).then((r) => r.data),
})

// Opening Hadith: the collections, then every collection's books. Errors stay
// quiet, like prefetchQuery: the panel shows its own when it is opened.
export const hadithOpen = (client) =>
  client.fetchQuery(hadithCollectionsQuery)
    .then((list) => Promise.all(list.map((c) => client.prefetchQuery(hadithBooksQuery(c.id)))))
    .catch(() => {})

// One book's hadiths in full, Arabic and English.
export const hadithBookQuery = (collection, number) => ({
  queryKey: ['hadith-book', collection, number],
  queryFn: () => api.get(`/hadith/${collection}/books/${number}`).then((r) => r.data),
})

// Where each narrator is named in one book's Arabic, and one narrator's sheet.
export const rijalChainsQuery = (collection, book) => ({
  queryKey: ['rijal-chains', collection, book],
  queryFn: () => api.get(`/rijal/chains/${collection}/${book}`).then((r) => r.data),
})
// The narrations sharing one number, each laid against `part`.
export const narrationFamilyQuery = (collection, number, part) => ({
  queryKey: ['rijal-family', collection, number, part],
  queryFn: () => api.get(`/rijal/family/${collection}/${number}`, { params: { part } }).then((r) => r.data),
  retry: false,
})
export const narratorHadithQuery = (id) => ({
  queryKey: ['narrator-hadith', id],
  queryFn: () => api.get(`/rijal/narrators/${id}/hadith`).then((r) => r.data),
})
export const rijalSearchQuery = (q) => ({
  queryKey: ['rijal-search', q],
  queryFn: () => api.get('/rijal/search', { params: { q } }).then((r) => r.data),
})
export const narratorQuery = (id) => ({
  queryKey: ['narrator', id],
  queryFn: () => api.get(`/rijal/narrators/${id}`).then((r) => r.data),
  // No page built for him stays that way, so a 404 is not retried.
  retry: (count, error) => error?.response?.status !== 404 && count < 1,
})

// What every chain is read against, fetched once: the twelve levels, what each doubtful link says, the terms of the science.
export const usulGuideQuery = {
  queryKey: ['usul-guide'],
  queryFn: () => api.get('/usul/guide').then((r) => r.data),
}
// The sorts of ruling the classical books give (with their plain meaning and count), and the hadith carrying one, a page at a time.
export const usulTermsQuery = {
  queryKey: ['usul-terms'],
  queryFn: () => api.get('/usul/terms').then((r) => r.data),
}
export const usulTermQuery = (kind) => ({
  queryKey: ['usul-term', kind],
  queryFn: ({ pageParam }) => api.get(`/usul/terms/${kind}`, { params: { offset: pageParam } }).then((r) => r.data),
  initialPageParam: 0,
  // A 404 is an index not built: it stays so, so it is not retried.
  retry: (count, error) => error?.response?.status !== 404 && count < 1,
  getNextPageParam: (last, pages) => {
    const seen = pages.reduce((n, p) => n + p.items.length, 0)
    return last.items.length && seen < last.total ? seen : undefined
  },
})

// The narrator list, most hadith first, a page at a time; the server fixes the page size.
export const narratorListQuery = (generation) => ({
  queryKey: ['narrator-list', generation],
  placeholderData: keepPreviousData, // the filter chips and list stay while another generation loads
  queryFn: ({ pageParam }) => api.get('/rijal/narrators', { params: { generation, offset: pageParam } }).then((r) => r.data),
  initialPageParam: 0,
  getNextPageParam: (last, pages) => {
    const seen = pages.reduce((n, p) => n + p.items.length, 0)
    return last.items.length && seen < last.total ? seen : undefined
  },
})

// Every word typed must appear, in Arabic or English, across the named
// collections; empty collections means every collection, the ordinary case.
export const searchHadith = ({ q, collections = [] }) =>
  api
    .get('/hadith/search', {
      params: { q, collections },
      // One `collections=` per id, the same paramsSerializer findDaleel uses
      // for `books`; left alone, axios writes `collections[]=` and nothing
      // filters.
      paramsSerializer: { indexes: null },
    })
    .then((r) => r.data)
