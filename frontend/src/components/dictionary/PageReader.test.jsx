// @vitest-environment happy-dom
import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'

vi.mock('../../api', () => ({
  readPicture: vi.fn(async () => ({
    text: 'ذهب الولد إلى المدرسة.\n\nقرأ الكتاب.',
    source: { key: 'tesseract', label: 'Read by Tesseract', confidence: 'guessed' },
    unsure: false,
  })),
  translateSentence: vi.fn(async (text) => ({
    meaning: text.startsWith('ذهب') ? 'The boy went to school.' : 'He read the book.',
    words: text.replace('.', '').split(' ').map((arabic) => ({ arabic, english: `en:${arabic}`, base: arabic })),
  })),
}))
vi.mock('../../lib/dictionary/shrinkPicture', () => ({ shrinkPicture: async (file) => file }))

import PageReader from './PageReader'

afterEach(cleanup)

const show = (props = {}) => render(
  <QueryClientProvider client={new QueryClient()}>
    <PageReader picture={new File(['x'], 'page.png', { type: 'image/png' })} shown="blob:page" accent="#c90"
      onPicked={() => {}} onClose={() => {}} onLookup={() => {}} onGo={() => {}} {...props} />
  </QueryClientProvider>,
)

describe('PageReader', () => {
  it('reads the picture, cuts it into lines and translates each', async () => {
    show()
    expect(await screen.findByText('The boy went to school.')).toBeTruthy()
    expect(await screen.findByText('He read the book.')).toBeTruthy()
    expect(screen.getAllByRole('listitem')).toHaveLength(2)
    expect(screen.getByText('2 lines')).toBeTruthy()
  })

  it('looks a word up in the dictionary', async () => {
    const onLookup = vi.fn()
    show({ onLookup })
    await screen.findByText('The boy went to school.')
    const line = screen.getAllByRole('listitem')[0]
    fireEvent.click(within(line).getByText('الولد'))
    expect(onLookup).toHaveBeenCalledWith('الولد')
  })

  it('translates the corrected text when asked', async () => {
    show()
    await screen.findByText('He read the book.')
    fireEvent.change(screen.getByLabelText('Text read from the picture'), { target: { value: 'قرأ الكتاب.' } })
    fireEvent.click(screen.getByText('Translate the corrected text'))
    await waitFor(() => expect(screen.getAllByRole('listitem')).toHaveLength(1))
  })
})
