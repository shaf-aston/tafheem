// @vitest-environment happy-dom
// Grow's Prayer world on the real data, served as /api/grow/worlds/prayer serves it: its page, a lesson's first
// phrase taught with the scholar's line, then asked, and the answer filed under the world's module.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'

import { renderScreen } from './render'
import GrowPanel from '../components/grow/GrowPanel'

const FOLDER = join(import.meta.dirname, '../../../backend/data/grow')
const read = (file) => JSON.parse(readFileSync(join(FOLDER, file), 'utf8'))
const { sources } = read('sources.json')
const served = (step) => (step.ruling ? { ...step, ruling: { ...sources[step.ruling.source], ...step.ruling } } : step)
const world = {
  id: 'prayer',
  paths: read('worlds/prayer/world.json').paths.map((name) => {
    const path = read(`worlds/prayer/paths/${name}.json`)
    return { ...path, steps: path.steps.map(served) }
  }),
}

const click = (name) => fireEvent.click(screen.getByRole('button', { name }))

describe('prayer', () => {
  it('teaches the dua after wudu first, with its source, then asks what it means', async () => {
    const filed = []
    renderScreen(<GrowPanel incoming="prayer" handed />, {
      routes: {
        'GET /grow/worlds/prayer': world,
        'GET /progress/summary': { items: [] },
        'POST /progress/attempts': (config) => { filed.push(JSON.parse(config.data)); return { earned: 1 } },
      },
    })

    expect(await screen.findByText(/16 not met yet/)).toBeTruthy()
    click('Start a lesson')
    expect(await screen.findByText(/^I bear witness that there is no god but Allah/)).toBeTruthy()
    expect(screen.getByText(/^Muslim, Sahih Muslim:/)).toBeTruthy()

    click('Continue')
    fireEvent.click(screen.getByRole('radio', { name: /^I bear witness/ }))
    click('Check')
    await waitFor(() => expect(filed.at(-1)).toMatchObject({ module: 'prayer', item: 'wudu-dua', correct: true }))
  })
})
