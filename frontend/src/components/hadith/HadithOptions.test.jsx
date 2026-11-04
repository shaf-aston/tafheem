// @vitest-environment happy-dom
import { describe, expect, it } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from '../../test/render'
import HadithOptions from './HadithOptions'

describe('HadithOptions', () => {
  it('carries the words link beside the reading options, and it opens the words alone', () => {
    renderScreen(<HadithOptions accent="#0a0" />, { routes: { 'GET /usul/guide': { glossary: [] } } })
    fireEvent.click(screen.getByRole('button', { name: 'Words and terms' }))
    expect(screen.getByRole('heading', { name: 'Words and terms' })).toBeTruthy()
  })
})
