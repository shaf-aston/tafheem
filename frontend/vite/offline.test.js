import { describe, expect, it } from 'vitest'

import { planOffline } from './offline.js'

const file = (path, bytes = 10) => ({ path, bytes })
const BUILT = [
  file('app.html'), file('index.html'), file('assets/app-1.js', 100), file('assets/inter-1.woff2'),
  file('assets/inter-1.woff'), file('assets/clip-1.mp4', 9000), file('icon-192.png'),
  file('words/words.json', 50), file('grow/quduri.json', 500), file('grow/quduri/index.json', 20),
  file('grow/nawawi40.json', 30), file('grow/backdrops/manifest.json'), file('jazariyya/poem.json'),
  file('sw.js'), file('offline-files.json'),
]

describe('planOffline', () => {
  const plan = planOffline(BUILT)

  it('keeps the app, its fonts and small data in the core, and leaves the landing page and its films out', () => {
    expect(plan.core).toEqual(expect.arrayContaining(['/app.html', '/assets/app-1.js', '/assets/inter-1.woff2', '/icon-192.png', '/jazariyya/poem.json', '/grow/backdrops/manifest.json']))
    for (const out of ['/index.html', '/assets/inter-1.woff', '/assets/clip-1.mp4', '/sw.js', '/offline-files.json', '/words/words.json']) {
      expect(plan.core).not.toContain(out)
    }
  })

  it('gives each pack its files, never an authored book that is fetched split', () => {
    expect(plan.packs.words.files).toEqual(['/words/words.json'])
    expect(plan.packs.books.files).toEqual(['/grow/quduri/index.json', '/grow/nawawi40.json'])
    expect(plan.packs.books.bytes).toBe(50)
    expect(plan.core).not.toContain('/grow/quduri.json')
  })

  it('names every surah for the Qur’an pack', () => {
    expect(plan.packs.quran.files).toHaveLength(114)
    expect(plan.packs.quran.files.at(-1)).toBe('/api/quran/surah/114')
  })

  it('changes version only when the core changes', () => {
    expect(planOffline(BUILT).version).toBe(plan.version)
    expect(planOffline([...BUILT, file('assets/app-2.js')]).version).not.toBe(plan.version)
  })
})
