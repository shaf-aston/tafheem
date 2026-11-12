// @vitest-environment happy-dom
// The lines under the Qur'an box say what Enter will do; once it has done it,
// they step aside for the answer, and typing again brings them back.
import { afterEach, describe, expect, it } from 'vitest'
import { cleanup, render, screen } from '@testing-library/react'

import QuranSearchBar from './QuranSearchBar'

const bar = (props) => (
  <QuranSearchBar value="2:255" onChange={() => {}} onClear={() => {}} onOpen={() => {}} onSearch={() => {}} onHeard={() => {}} accent="#0a7" {...props} />
)

describe('QuranSearchBar', () => {
  afterEach(cleanup)

  it('says what Enter will open, with the matching surah', () => {
    render(bar())
    expect(screen.getByText(/Enter opens/)).toBeTruthy()
    expect(screen.getByRole('list', { name: 'Matching surahs' })).toBeTruthy()
  })

  it('steps aside once the line is answered', () => {
    render(bar({ answered: true }))
    expect(screen.queryByText(/Enter opens/)).toBeNull()
    expect(screen.queryByRole('list', { name: 'Matching surahs' })).toBeNull()
  })
})
