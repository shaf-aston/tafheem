// @vitest-environment happy-dom
// Home offers where you stopped and the recent tabs from the journey, a first-visit
// start when there is no path, and every tab in view under its group.
import { describe, expect, it, vi } from 'vitest'
import { act, fireEvent, screen, within } from '@testing-library/react'

import { renderScreen } from './render'
import HomePanel from '../components/home/HomePanel'
import { visit } from '../lib/nav/journey'
import { HOME, LISTED } from '../lib/nav/tabs'
import { LEVEL_KEY, LEVELS, levelOf } from '../lib/learner/learnerLevel'
import { readRaw, writeRaw } from '../lib/store/stored'
import knobs from '../config/home.json'

describe('Home', () => {
  it('on a first visit asks how much Arabic you know, one row a level', () => {
    renderScreen(<HomePanel accent="var(--primary)" onGo={vi.fn()} />)
    const fork = screen.getByRole('region', { name: knobs.copy['fork-label'] })
    expect(within(fork).getAllByRole('button').map((row) => row.textContent)).toEqual(
      LEVELS.map((level) => expect.stringContaining(level.title)),
    )
  })

  it.each(LEVELS.map((level) => [level.id, level]))('one tap on %s keeps it and starts there', (id, level) => {
    const onGo = vi.fn()
    renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />)
    const fork = screen.getByRole('region', { name: knobs.copy['fork-label'] })
    fireEvent.click(within(fork).getByRole('button', { name: new RegExp(level.title) }))
    expect(onGo).toHaveBeenCalledWith(...level.start)
    expect(readRaw(LEVEL_KEY)).toBe(id)
  })

  it('marks a level already chosen', () => {
    writeRaw(LEVEL_KEY, 'intermediate')
    renderScreen(<HomePanel accent="var(--primary)" onGo={vi.fn()} />)
    const fork = screen.getByRole('region', { name: knobs.copy['fork-label'] })
    const marked = within(fork).getAllByRole('button').filter((row) => row.getAttribute('aria-current'))
    expect(marked.map((row) => row.textContent)).toEqual([expect.stringContaining(knobs.copy['fork-yours'])])
    expect(marked[0].textContent).toContain(levelOf('intermediate').title)
  })

  it('shows every other tab without opening anything', async () => {
    const onGo = vi.fn()
    const { container } = renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />)
    expect(container.querySelector('details')).toBeNull()
    const others = LISTED.filter((tab) => tab.id !== HOME)
    // Each tab once in the list; the first-lesson card above is the only other place one shows.
    const list = screen.getByRole('region', { name: knobs.copy.all })
    for (const tab of others) {
      expect(within(list).getAllByText(tab.blurb), tab.id).toHaveLength(1)
    }
  })

  it('carries on where you stopped, with the word', async () => {
    const onGo = vi.fn()
    renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />)
    act(() => { visit('dict', 'كتب') })
    fireEvent.click(await screen.findByRole('button', { name: /Continue/ }))
    expect(onGo).toHaveBeenCalledWith('dict', 'كتب')
    expect(screen.queryByRole('region', { name: knobs.copy['fork-label'] })).toBeNull()
  })

  it("names a Grow lesson as a reader says it, and still goes back to the address", async () => {
    const onGo = vi.fn()
    renderScreen(<HomePanel accent="var(--primary)" onGo={onGo} />)
    act(() => { visit('grow', 'basics/lesson') })
    const card = await screen.findByRole('region', { name: knobs.copy['resume-label'] })
    expect(within(card).getByText('Basics lesson')).toBeTruthy()
    expect(within(card).queryByText('basics/lesson')).toBeNull()
    fireEvent.click(within(card).getByRole('button', { name: /Continue/ }))
    expect(onGo).toHaveBeenCalledWith('grow', 'basics/lesson')
  })
})
