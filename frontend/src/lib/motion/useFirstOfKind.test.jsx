// @vitest-environment happy-dom
import { describe, expect, it } from 'vitest'
import { act, render } from '@testing-library/react'

import { useFirstOfKind } from './useFirstOfKind'

const Probe = ({ name }) => <span data-testid={name}>{useFirstOfKind('probe') ? 'first' : 'rest'}</span>

describe('useFirstOfKind', () => {
  it('gives the turn to the first mounted, and passes it on when that one leaves', () => {
    const view = render(<><Probe name="a" /><Probe name="b" /></>)
    expect(view.getByTestId('a').textContent).toBe('first')
    expect(view.getByTestId('b').textContent).toBe('rest')
    act(() => view.rerender(<Probe name="b" />))
    expect(view.getByTestId('b').textContent).toBe('first')
    view.unmount()
  })
})
