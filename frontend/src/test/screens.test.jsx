// @vitest-environment happy-dom
// Each core screen opens with no backend at all: nothing throws, and its
// heading is on screen. A screen that breaks on open fails here, not in use.
import { describe, expect, it } from 'vitest'
import { screen } from '@testing-library/react'

import { renderScreen } from './render'
import Dictionary from '../components/Dictionary'
import MemorisePanel from '../components/MemorisePanel'
import NahwPanel from '../components/NahwPanel'
import QuizPanel from '../components/QuizPanel'
import QuranLookup from '../components/QuranLookup'

const SCREENS = [
  ['Quiz', QuizPanel],
  ['Memorise', MemorisePanel],
  ['Quran', QuranLookup],
  ['Dictionary', Dictionary],
  ['Nahw', NahwPanel],
]

describe('core screens open with the backend down', () => {
  it.each(SCREENS)('%s', async (name, Screen) => {
    renderScreen(<Screen accent="#0a7" onGo={() => {}} onVisit={() => {}} onProgress={() => {}} />)
    expect(await screen.findByRole('heading', { name: new RegExp(name) })).toBeTruthy()
  })
})
