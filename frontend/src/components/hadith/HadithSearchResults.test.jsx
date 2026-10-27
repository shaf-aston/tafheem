// @vitest-environment happy-dom
import { describe, expect, it } from 'vitest'
import { fireEvent, screen, waitFor } from '@testing-library/react'

import { renderScreen } from '../../test/render'
import HadithSearchResults from './HadithSearchResults'

const routes = {
  'GET /hadith/collections': [],
  'GET /hadith/search': { query: 'patience', hits: [], chapters: [], ready: true },
}
const open = () => renderScreen(
  <HadithSearchResults accent="#0a0" onOpenBook={() => {}} onNarrator={() => {}} onHadith={() => {}} places={<p>places</p>}>
    <p>the books</p>
  </HadithSearchResults>,
  { routes },
)
const search = async () => {
  const box = screen.getByRole('textbox')
  fireEvent.change(box, { target: { value: 'patience' } })
  fireEvent.keyDown(box, { key: 'Enter' })
  await screen.findByText(/Results for/)
}

describe('searching Hadith', () => {
  it('has no way back while the books are showing', () => {
    open()
    expect(screen.getByText('the books')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /Books/ })).toBeNull()
  })

  it.each([
    ['← Books', () => fireEvent.click(screen.getByRole('button', { name: /Books/ }))],
    ['the ✕', () => fireEvent.click(screen.getByRole('button', { name: 'Close search' }))],
    ['Esc', () => fireEvent.keyDown(document, { key: 'Escape' })],
  ])('goes back to the books with %s', async (_, leave) => {
    open()
    await search()
    expect(screen.queryByText('the books')).toBeNull()
    leave()
    await waitFor(() => expect(screen.getByText('the books')).toBeTruthy())
    expect(screen.queryByText(/Results for/)).toBeNull()
  })
})
