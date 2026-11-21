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
vi.mock('../../lib/dictionary/shrinkPicture', () => {
  class NotAPicture extends Error {}
  return {
    NotAPicture,
    shrinkPicture: async (file) => { if (!file.type.startsWith('image/')) throw new NotAPicture('Send a screenshot.'); return file },
  }
})

import { readPicture } from '../../api'
import PageReader from './PageReader'

afterEach(cleanup)

const show = (props = {}) => render(
  <QueryClientProvider client={new QueryClient()}>
    <PageReader picture={new File(['x'], 'page.png', { type: 'image/png' })} shown="blob:page" accent="#c90"
      onClose={() => {}} onLookup={() => {}} onGo={() => {}} {...props} />
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
  it('shows the word pointed at in the bar, with a Look up button', async () => {
    const onLookup = vi.fn()
    show({ onLookup })
    await screen.findByText('The boy went to school.')
    expect(screen.getByText(/Point at a word/)).toBeTruthy()
    fireEvent.mouseEnter(within(screen.getAllByRole('listitem')[0]).getByText('المدرسة'))
    expect(screen.getByText('en:المدرسة')).toBeTruthy()
    fireEvent.click(screen.getByRole('button', { name: 'Look up' }))
    expect(onLookup).toHaveBeenCalledWith('المدرسة')
  })

  it('has no Look up when there is no dictionary to look in', async () => {
    show({ onLookup: null })
    await screen.findByText('The boy went to school.')
    fireEvent.mouseEnter(within(screen.getAllByRole('listitem')[0]).getByText('الولد'))
    expect(screen.getByText('en:الولد')).toBeTruthy()
    expect(screen.queryByRole('button', { name: 'Look up' })).toBeNull()
  })

  it('waits for an unsure page to be checked before translating it', async () => {
    readPicture.mockResolvedValueOnce({ text: 'قرأ الكتاب.', source: { key: 'tesseract', label: 'Tesseract' }, unsure: true })
    show()
    expect(await screen.findAllByText(/hard to read, so it waits for you/)).toHaveLength(2) // one beside the box on a phone, one in the column on a wide screen
    expect(screen.queryAllByRole('listitem')).toHaveLength(0)
    fireEvent.click(screen.getByText('Translate this text'))
    expect(await screen.findByText('He read the book.')).toBeTruthy()
  })

  it('says a file that is no picture cannot be read, with no retry', async () => {
    show({ picture: new File(['x'], 'notes.pdf', { type: 'application/pdf' }) })
    expect(await screen.findByText('Send a screenshot.')).toBeTruthy()
    expect(screen.queryByRole('button', { name: /try again|retry/i })).toBeNull()
    expect(screen.queryByRole('img')).toBeNull()
  })
})
