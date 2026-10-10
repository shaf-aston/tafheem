import { renderToStaticMarkup } from 'react-dom/server'
import { describe, expect, it } from 'vitest'
import ExerciseHost from '../ExerciseHost'
import { exerciseOf } from './registry'

const base = { id: 'u.l.x.01', prompt: 'Say hello', answer: 'مرحبا', accepted: ['مرحبا'] }
const draw = (exercise) => renderToStaticMarkup(<ExerciseHost exercise={exercise} />)

describe('exercise registry', () => {
  it('describes each of the five types and none for a stranger', () => {
    for (const type of ['reply', 'fill_blank', 'translate_to_arabic', 'choose', 'reorder']) {
      const kind = exerciseOf(type)
      expect(kind.Renderer).toBeTruthy()
      expect(kind.judge).toBeTypeOf('function')
    }
    expect(exerciseOf('telepathy')).toBeNull()
    expect(exerciseOf('reorder').blank).toEqual([])
    expect(exerciseOf('reply').blank).toBe('')
    expect(exerciseOf('choose').blank).toBe('')
  })
})

describe('ExerciseHost', () => {
  it('draws each type with its prompt and a disabled Check', () => {
    const types = {
      reply: {},
      choose: { options: ['مرحبا', 'شكرا', 'يلا'] },
      reorder: { answer: 'شو اسمك', accepted: ['شو اسمك'] },
    }
    for (const [type, extra] of Object.entries(types)) {
      const html = draw({ ...base, type, ...extra })
      expect(html).toContain('Say hello')
      expect(html).toContain('disabled')
    }
  })
  it('an unknown type is a visible note, not blank', () => {
    expect(draw({ ...base, type: 'telepathy' })).toContain('cannot show yet')
  })
  it('an answered exercise comes back as it was left, marked and read-only', () => {
    const html = renderToStaticMarkup(
      <ExerciseHost exercise={{ ...base, type: 'reply' }} saved={{ correct: false, value: 'هلا' }} />,
    )
    expect(html).toContain('value="هلا"')
    expect(html).toContain('The natural answer is')
    expect(html).not.toContain('Check')
  })
  it('a bookish note shows on a correct pick, and on a typed bookish form', () => {
    const too_formal = { item: 'كيف حالك', feedback: 'that is the bookish way' }
    const picked = renderToStaticMarkup(
      <ExerciseHost exercise={{ ...base, type: 'choose', options: ['مرحبا', 'شكرا', 'يلا'], too_formal }} saved={{ correct: true, value: 'مرحبا' }} />,
    )
    expect(picked).toContain('that is the bookish way')
    const typed = renderToStaticMarkup(
      <ExerciseHost exercise={{ ...base, type: 'reply', too_formal }} saved={{ correct: true, value: 'كيف حالك' }} />,
    )
    expect(typed).toContain('that is the bookish way')
  })
  it('picture options draw their labels', () => {
    const html = draw({ ...base, type: 'choose', options: [{ label: 'قهوة', image: 'a/b.jpg' }, 'شاي', 'ماء'] })
    expect(html).toContain('قهوة')
    expect(html).toContain('/colloquial/image/a/b.jpg')
  })
})
