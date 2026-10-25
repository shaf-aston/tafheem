// @vitest-environment happy-dom
// The Jawhara's bayts carry OpenITI's " % " between their halves: no teach or choose card may print it, and a gap
// in one half is still filled.
import { readFileSync } from 'node:fs'
import { join } from 'node:path'
import { describe, expect, it } from 'vitest'
import { render } from '@testing-library/react'

import ChooseCard from '../components/grow/exercises/ChooseCard'
import TeachCard from '../components/grow/exercises/TeachCard'

const book = JSON.parse(readFileSync(join(import.meta.dirname, '../../public/grow/jawhara.json'), 'utf8'))
const cards = []
const walk = (node) => {
  if (Array.isArray(node)) node.forEach(walk)
  else if (node && typeof node === 'object') {
    if (typeof node.ar === 'string' && node.ar.includes('%')) cards.push(node)
    Object.values(node).forEach(walk)
  }
}
walk(book.parts)

describe('the Jawhara on a card', () => {
  it('has bayts to test', () => {
    expect(cards.length).toBeGreaterThan(0)
  })

  it('never prints the verse mark, and sets each bayt as two halves', () => {
    for (const card of cards) {
      const { container, unmount } = render(
        card.kind === 'choose' ? <ChooseCard card={{ ...card, options: card.options.map((text, i) => ({ id: String(i), text })) }} value={null} setValue={() => {}} result={null} /> : <TeachCard card={card} />,
      )
      expect(container.textContent).not.toContain('%')
      expect(container.querySelectorAll('.bayt-half')).toHaveLength(2)
      unmount()
    }
  })

  it('splits the blank after the halves', () => {
    const card = { id: 'x', tag: 't', ask: 'a', ar: 'أول ____ % ثاني', options: [{ id: 'a', text: 'كلمة' }], answer: 'a' }
    const { container } = render(<ChooseCard card={card} value="a" setValue={() => {}} result={null} />)
    const halves = container.querySelectorAll('.bayt-half')
    expect(halves[0].textContent).toContain('كلمة')
    expect(halves[1].textContent.trim()).toBe('ثاني')
  })
})
