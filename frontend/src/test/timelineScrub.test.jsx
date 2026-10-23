// @vitest-environment happy-dom
// The time bar previews while dragging, opens on release, and steps by key.
import { describe, expect, it, vi } from 'vitest'
import { fireEvent, screen } from '@testing-library/react'

import { renderScreen } from './render'
import TimelineScrub from '../components/timelines/TimelineScrub'

const ev = (id, at) => ({ id, at, title: id, when: `${at} CE` })
const section = { id: 'seerah', name: 'The Seerah', kind: 'dated', events: [ev('birth', 570), ev('hijrah', 622), ev('badr', 624)] }

describe('TimelineScrub', () => {
  it('previews the nearest event while dragging and opens it on release', () => {
    const onPreview = vi.fn()
    const onPick = vi.fn()
    renderScreen(<TimelineScrub section={section} index={null} onPreview={onPreview} onPick={onPick} />)
    const bar = screen.getByRole('slider')
    fireEvent.change(bar, { target: { value: '880' } })
    expect(onPreview).toHaveBeenLastCalledWith(1)
    expect(onPick).not.toHaveBeenCalled()
    fireEvent.pointerUp(bar)
    expect(onPick).toHaveBeenCalledWith('hijrah')
    expect(onPreview).toHaveBeenLastCalledWith(null)
  })

  it('steps one event with the arrow keys and the buttons', () => {
    const onPick = vi.fn()
    renderScreen(<TimelineScrub section={section} index={1} onPreview={() => {}} onPick={onPick} />)
    fireEvent.keyDown(screen.getByRole('slider'), { key: 'ArrowRight' })
    expect(onPick).toHaveBeenLastCalledWith('badr')
    fireEvent.click(screen.getByLabelText('Previous event'))
    expect(onPick).toHaveBeenLastCalledWith('birth')
    expect(screen.getByRole('slider').getAttribute('aria-valuetext')).toBe('hijrah, 622 CE')
  })

  it('offers no spacing choice for a section without years', () => {
    renderScreen(<TimelineScrub section={{ ...section, kind: 'undated' }} index={0} onPreview={() => {}} onPick={() => {}} />)
    expect(screen.queryByText('True years')).toBeNull()
  })
})
