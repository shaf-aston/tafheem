// @vitest-environment happy-dom
// Home lists every browsable tab from the registry, goes to one on a tap, and
// offers the places left open in other tabs.
import { describe, expect, it, vi } from 'vitest'
import { act, fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import HomePanel from '../components/home/HomePanel'
import { visit } from '../lib/journey'
import { LISTED } from '../lib/tabs'

const CARDS = LISTED.filter((tab) => tab.group !== 'start')

describe('Home', () => {
  it('shows one card per tab and opens it on a tap', async () => {
    const onGo = vi.fn()
    const { client } = renderScreen(<HomePanel accent="#0a7" onGo={onGo} />)
    client.setQueryData(['overview', null], { modules: [], attempts: 0, correct: 0, learnt: 0, streak: 0 })
    expect(await screen.findByRole('heading', { name: /Home/ })).toBeTruthy()
    for (const tab of CARDS) {
      expect(screen.getByRole('button', { name: new RegExp(tab.blurb.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')) }), tab.id).toBeTruthy()
    }
    fireEvent.click(screen.getByRole('button', { name: /Type a sentence/ }))
    expect(onGo).toHaveBeenCalledWith('nahw')
  })

  it('offers a place left open in another tab', async () => {
    const onGo = vi.fn()
    renderScreen(<HomePanel accent="#0a7" onGo={onGo} />)
    act(() => { visit('dict', 'كتب') })
    fireEvent.click(await screen.findByRole('button', { name: /Dictionary\s+كتب/ }))
    expect(onGo).toHaveBeenCalledWith('dict', 'كتب')
  })
})
