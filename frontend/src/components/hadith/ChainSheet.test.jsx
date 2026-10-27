// @vitest-environment happy-dom
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, fireEvent, screen } from '@testing-library/react'

import { renderScreen } from '../../test/render'
import ChainSheet from './ChainSheet'

afterEach(cleanup)

const links = { main: [{ name: 'أبو هريرة', id: 1, word: 'عن' }], branches: [] }
const rulings = [{ scholar: 'Al-Albani', grade: 'Sahih', quote: 'صحيح', book: 'Sahih al-Jami' }]
const open = (props) => renderScreen(<ChainSheet accent="#0a0" onClose={() => {}} {...props} />, { routes: { 'GET /usul/guide': { glossary: [] } } })
const tabNames = () => screen.queryAllByRole('button', { pressed: true }).concat(screen.queryAllByRole('button', { pressed: false })).map((b) => b.textContent)

describe('ChainSheet', () => {
  it('has a tab for each thing there is to read, and the words always', () => {
    open({ links, rulings })
    expect(tabNames()).toEqual(expect.arrayContaining(['Chain', 'Verdicts', 'Words']))
    expect(tabNames()).not.toContain('Weak points')
    expect(screen.getByRole('heading', { name: 'The chain' })).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Verdicts' }))
    expect(screen.getByRole('heading', { name: 'What scholars said' })).toBeTruthy()
  })

  it('is the words alone, with no tabs, when opened with no hadith', () => {
    open({})
    expect(screen.getByRole('heading', { name: 'Words and terms' })).toBeTruthy()
    expect(screen.queryByRole('group', { name: 'Parts of this hadith' })).toBeNull()
  })

  it('leaves the chain tab out of a hadith with no chain', () => {
    open({ links: { main: [], branches: [] }, chainless: true, rulings })
    expect(screen.queryByRole('button', { name: 'Chain' })).toBeNull()
    expect(screen.getByRole('heading', { name: 'What scholars said' })).toBeTruthy()
  })
})
