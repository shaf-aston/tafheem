// @vitest-environment happy-dom
// The topic tiles fill the empty tab; once a topic is open they fold to one
// row of chips so the answer has the screen, and All topics opens them again.
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from '../../test/render'
import DawahPanel from './DawahPanel'

const question = (id, q) => ({ id, q, short: 'A short answer.', points: [], discussion: [] })
const ROUTES = {
  'GET /dawah': {
    topics: [
      { id: 'god', title: 'God', arabic: 'الله', blurb: 'Who made God', questions: [question('who-made-god', 'Who made God?')] },
      { id: 'prophet', title: 'The Prophet', arabic: 'النبي', blurb: 'His life', questions: [question('why-many-wives', 'Why many wives?')] },
    ],
  },
}

describe('the Dawah tab', () => {
  it('folds the tiles to a chip row once a topic is open', async () => {
    renderScreen(<DawahPanel accent="#0a7" onGo={() => {}} onVisit={() => {}} />, { routes: ROUTES })
    fireEvent.click(await screen.findByRole('button', { name: /Who made God/ }))
    const row = await screen.findByRole('group', { name: 'Topics' })
    expect(row.querySelector('[aria-pressed="true"]').textContent).toBe('God')
    expect(screen.queryByRole('button', { name: /His life/ })).toBeNull()
    fireEvent.click(screen.getByRole('button', { name: 'All topics' }))
    expect(screen.queryByRole('group', { name: 'Topics' })).toBeNull()
    expect(screen.getByRole('button', { name: /His life/ })).toBeTruthy()
  })
})
