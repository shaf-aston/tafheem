// @vitest-environment happy-dom
import { beforeEach, describe, expect, it } from 'vitest'

import theme from '../config/theme.json'
import { carryLook } from './carryLook'

const KEY = theme.themes['hint-key']
const here = { href: 'https://tafheem.test/', origin: 'https://tafheem.test', pathname: '/' }
const link = (href) => ({ href, pathname: new URL(href).pathname })

describe('carryLook', () => {
  beforeEach(() => localStorage.clear())

  it('hands the landing\'s look to a first visit into the app', () => {
    carryLook(link('https://tafheem.test/app'), here)
    expect(localStorage.getItem(KEY)).toBe(theme.themes.base)
  })

  it('leaves a look the device already has alone', () => {
    localStorage.setItem(KEY, 'system')
    carryLook(link('https://tafheem.test/app'), here)
    expect(localStorage.getItem(KEY)).toBe('system')
  })

  it('ignores links that leave the site or stay on the landing', () => {
    carryLook(link('https://elsewhere.test/app'), here)
    carryLook(link('https://tafheem.test/#story'), here)
    carryLook(null, here)
    expect(localStorage.getItem(KEY)).toBeNull()
  })
})
