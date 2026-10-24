import { beforeEach, describe, expect, it } from 'vitest'

import theme from '../../config/theme.json'
import { themeChoices, themeVariable } from '../../theme'
import { SETTINGS, applySettings, resetSettings, setSetting } from './settings'

// A fake :root that records what was written to it, so the CSS side can be
// checked without a browser.
function fakeRoot() {
  const written = new Map()
  return {
    written,
    style: {
      setProperty: (name, value) => written.set(name, value),
      removeProperty: (name) => written.delete(name),
    },
  }
}

const setting = (key) => SETTINGS.find((one) => one.key === key)
const option = (key, id) => setting(key).options.find((one) => one.id === id)

const applied = () => {
  const root = fakeRoot()
  applySettings(root)
  return root.written
}

describe('settings', () => {
  beforeEach(() => resetSettings())

  it('starts on the default option declared in settings.json', () => {
    const study = setting('study-size')
    expect(applied().get(study.css)).toBe(String(option('study-size', study.default).write))
  })

  it('writes the chosen option’s value', () => {
    setSetting('study-size', 'large')
    expect(applied().get('--study-zoom')).toBe(String(option('study-size', 'large').write))
  })

  it('falls back to the default when the stored option no longer exists', () => {
    setSetting('study-size', 'enormous')
    const study = setting('study-size')
    expect(applied().get('--study-zoom')).toBe(String(option('study-size', study.default).write))
  })

  it('ignores a key that settings.json does not declare', () => {
    setSetting('not-a-setting', 'small')
    expect(applied().has('--not-a-setting')).toBe(false)
  })

  it('writes a switch’s variables only while it is off', () => {
    setSetting('motion', false)
    expect(applied().get('--motion-base-ms')).toBe('0')

    // Back on, the theme's own duration must be there, not missing. Both this
    // module and theme.js write to the same :root, so removing the property
    // would delete the theme's value and leave every rule timing on nothing.
    setSetting('motion', true)
    expect(applied().get('--motion-base-ms')).toBe(themeVariable('--motion-base-ms'))
    expect(applied().get('--motion-base-ms')).not.toBe(undefined)
  })

  it('puts the chosen look on :root, and the base one back', () => {
    setSetting('theme', 'parchment')
    expect(applied().get('--bg')).toBe(theme.themes.looks.parchment.color.bg)
    // The palette is toned per look (lib/theme/tone.js), so paper's violet is its own.
    const paperViolet = applied().get('--palette-violet')
    expect(paperViolet).toBe(themeVariable('--palette-violet'))

    setSetting('theme', 'ink')
    expect(applied().get('--bg')).toBe(theme.color.bg)
    expect(applied().get('--palette-violet')).not.toBe(paperViolet)
  })

  it('lays the other settings over the look, not under it', () => {
    setSetting('theme', 'parchment')
    setSetting('motion', false)
    expect(applied().get('--motion-base-ms')).toBe('0')
    // Switched back on, it is the light look's own value, not a stale ink one.
    setSetting('motion', true)
    expect(applied().get('--motion-base-ms')).toBe(themeVariable('--motion-base-ms'))
  })

  it('offers exactly the looks theme.json has, then the device, and starts on the device', () => {
    expect(setting('theme').options.map((one) => one.id)).toEqual(themeChoices().map((one) => one.id))
    expect(setting('theme').default).toBe(theme.themes.device.choice)
  })

  it('ignores a look that does not exist', () => {
    setSetting('theme', 'neon')
    expect(applied().get('--bg')).toBe(theme.color.bg)
  })

  it('keeps a switch out of the CSS when it has no variables to write', () => {
    setSetting('synonyms', false)
    // Synonyms are a component decision, not a style; nothing lands on :root.
    expect([...applied().keys()].some((name) => name.includes('synonym'))).toBe(false)
  })

  it('resets every setting back to its default', () => {
    setSetting('study-size', 'small')
    resetSettings()
    const study = setting('study-size')
    expect(applied().get('--study-zoom')).toBe(String(option('study-size', study.default).write))
  })
})
