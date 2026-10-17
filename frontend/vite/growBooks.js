/**
 * Grow's book worlds, split for the page (src/lib/bookSplit.js): /grow/<book>/index.json and /grow/<book>/<part>.json,
 * made from the authored public/grow/<book>.json. The dev server answers them on request; the build writes them all.
 * A book is any file in public/grow with `parts`; the authored file is still copied, it is only not fetched.
 */
import { readFileSync, readdirSync } from 'node:fs'
import { join } from 'node:path'

import { indexOf, servedFile } from '../src/lib/bookSplit.js'

const DIR = join(import.meta.dirname, '../public/grow')
const SERVED = /^\/grow\/([\w-]+)\/([\w-]+\.json)$/

const bookAt = (name) => {
  try {
    const book = JSON.parse(readFileSync(join(DIR, `${name}.json`), 'utf8'))
    return Array.isArray(book.parts) ? book : null
  } catch {
    return null
  }
}

export const growBooks = {
  name: 'grow-books',
  configureServer(server) {
    server.middlewares.use((req, res, next) => {
      const [, name, file] = req.url.split('?')[0].match(SERVED) ?? []
      const book = name && bookAt(name)
      const body = book && servedFile(book, file)
      if (!body) return next()
      res.setHeader('Content-Type', 'application/json')
      res.end(JSON.stringify(body))
    })
  },
  generateBundle() {
    for (const file of readdirSync(DIR).filter((one) => one.endsWith('.json'))) {
      const name = file.replace(/\.json$/, '')
      const book = bookAt(name)
      if (!book) continue
      this.emitFile({ type: 'asset', fileName: `grow/${name}/index.json`, source: JSON.stringify(indexOf(book)) })
      for (const part of book.parts) {
        this.emitFile({ type: 'asset', fileName: `grow/${name}/${part.id}.json`, source: JSON.stringify(part) })
      }
    }
  },
}
