import { describe, expect, it } from 'vitest'

import { fontPreloadTag } from './preloadFont'

describe('fontPreloadTag', () => {
  it('links the built Arabic face', () => {
    const bundle = { 'assets/noto-naskh-arabic-arabic-400-normal-Ab12_c.woff2': {}, 'assets/app-1.js': {} }
    expect(fontPreloadTag(bundle)).toBe(
      '<link rel="preload" as="font" type="font/woff2" href="/assets/noto-naskh-arabic-arabic-400-normal-Ab12_c.woff2" crossorigin>',
    )
  })

  it('nothing for a bold weight or another face', () => {
    expect(fontPreloadTag({ 'assets/noto-naskh-arabic-arabic-700-normal-x.woff2': {} })).toBe('')
    expect(fontPreloadTag({})).toBe('')
  })
})
