import { describe, expect, it } from 'vitest'

import { fontPreloadTag, quranPreloadScript } from './preloadFont'

describe('fontPreloadTag', () => {
  it('links the built Arabic face', () => {
    const bundle = { 'assets/noto-naskh-arabic-arabic-400-normal-Ab12_c.woff2': {}, 'assets/app-1.js': {} }
    expect(fontPreloadTag(bundle)).toBe(
      '<link rel="preload" as="font" type="font/woff2" href="/assets/noto-naskh-arabic-arabic-400-normal-Ab12_c.woff2" crossorigin>',
    )
  })

  it('links the interface face too', () => {
    const bundle = { 'assets/inter-latin-wght-normal-Zz9.woff2': {}, 'assets/inter-cyrillic-wght-normal-q.woff2': {} }
    expect(fontPreloadTag(bundle)).toBe(
      '<link rel="preload" as="font" type="font/woff2" href="/assets/inter-latin-wght-normal-Zz9.woff2" crossorigin>',
    )
  })

  it('nothing for a bold weight or another face', () => {
    expect(fontPreloadTag({ 'assets/noto-naskh-arabic-arabic-700-normal-x.woff2': {} })).toBe('')
    expect(fontPreloadTag({})).toBe('')
  })
})

describe('quranPreloadScript', () => {
  const bundle = { 'assets/scheherazade-new-arabic-400-normal-Qq1.woff2': {}, 'assets/scheherazade-new-latin-400-normal-x.woff2': {} }

  it('adds the Qur\'an face\'s link on its tabs only', () => {
    const script = quranPreloadScript(bundle)
    expect(script).toContain('href="/assets/scheherazade-new-arabic-400-normal-Qq1.woff2"')
    expect(script).not.toContain('latin')
    const tabs = new Function('location', `return ${script.match(/if \((\/.*\/)\.test/)[1]}`)
    const on = tabs()
    expect(['/mem/4:106', '/memorise', '/quran/2:255'].every((path) => on.test(path))).toBe(true)
    expect(['/home', '/similar/x', '/memo'].some((path) => on.test(path))).toBe(false)
  })

  it('nothing when the face is not built', () => {
    expect(quranPreloadScript({})).toBe('')
  })

  it('is not part of the links every page gets', () => {
    expect(fontPreloadTag(bundle)).toBe('')
  })
})
