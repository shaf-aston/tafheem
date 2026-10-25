import { describe, expect, it } from 'vitest'

import { installKind, isIos, stripOpen } from './install'

const IPHONE_SAFARI = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 Version/17.0 Mobile/15E148 Safari/604.1'
const IPHONE_CHROME = 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 CriOS/120.0 Mobile/15E148 Safari/604.1'
const IPAD_AS_MAC = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15'
const ANDROID = 'Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 Chrome/120.0 Mobile Safari/537.36'
const LAPTOP = 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 Version/17.0 Safari/605.1.15'

describe('installKind', () => {
  it('Android with a browser prompt: the button', () => {
    expect(installKind({ ua: ANDROID, prompt: {} })).toBe('prompt')
  })
  it('Android before the browser offers one: told to use its menu', () => {
    expect(installKind({ ua: ANDROID })).toBe('menu')
  })
  it('iPhone Safari: the Share steps', () => {
    expect(installKind({ ua: IPHONE_SAFARI })).toBe('ios')
  })
  it('iPhone in Chrome cannot add to the home screen: told to open Safari', () => {
    expect(installKind({ ua: IPHONE_CHROME })).toBe('ios-other')
  })
  it('an iPad that calls itself a Mac is told apart from a laptop by its touchscreen', () => {
    expect(isIos(IPAD_AS_MAC, 5)).toBe(true)
    expect(installKind({ ua: LAPTOP, touchPoints: 0 })).toBe('none')
  })
  it('a laptop is never offered it, even when its browser offers a prompt', () => {
    expect(installKind({ ua: LAPTOP, prompt: {} })).toBe('none')
    expect(installKind({ ua: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0', prompt: {} })).toBe('none')
  })
  it('already installed: nothing, on any phone', () => {
    expect(installKind({ ua: IPHONE_SAFARI, standalone: true })).toBe('none')
    expect(installKind({ ua: ANDROID, standalone: true, prompt: {} })).toBe('none')
  })
})

describe('stripOpen', () => {
  it('opens by itself for a prompt or the iPhone steps, until closed on this device', () => {
    expect(stripOpen({ kind: 'prompt', dismissed: false, asked: false })).toBe(true)
    expect(stripOpen({ kind: 'ios', dismissed: false, asked: false })).toBe(true)
    expect(stripOpen({ kind: 'ios', dismissed: true, asked: false })).toBe(false)
  })
  it('waits for the icon where the advice is only "use your menu"', () => {
    expect(stripOpen({ kind: 'menu', dismissed: false, asked: false })).toBe(false)
    expect(stripOpen({ kind: 'menu', dismissed: false, asked: true })).toBe(true)
  })
  it('opens for the icon even after it was closed, but never where nothing can be installed', () => {
    expect(stripOpen({ kind: 'ios', dismissed: true, asked: true })).toBe(true)
    expect(stripOpen({ kind: 'none', dismissed: false, asked: true })).toBe(false)
  })
})
