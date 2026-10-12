import { describe, expect, it } from 'vitest'

import theme from '../src/theme.json'
import { bootShellPlugin } from './bootShell'

const run = (html) => bootShellPlugin.transformIndexHtml.handler(html)

describe('bootShellPlugin', () => {
  it('paints the theme ground before any CSS, on any page', () => {
    expect(run('<head></head><body><div id="root"></div></body>')).toContain(`background: ${theme.color.bg}`)
  })

  it('gives a page that is not themed no other look and no script', () => {
    const out = run('<html lang="en"><head></head></html>')
    expect(out).not.toContain('data-theme')
    expect(out).not.toContain('<script>')
  })

  it('gives a themed page every look’s ground and the hint reader', () => {
    const out = run('<html lang="en" data-themed><head></head></html>')
    expect(out).toContain(`html[data-theme="light"], html[data-theme="light"] body { background: ${theme.themes.light.color.bg}; }`)
    expect(out).toContain(`localStorage.getItem('${theme.themes['hint-key']}')`)
  })

  it('keeps the address bar, the manifest and the boot ground on the same colour', async () => {
    const { readFileSync } = await import('node:fs')
    const here = (path) => readFileSync(new URL(path, import.meta.url), 'utf8')
    const manifest = JSON.parse(here('../public/app.webmanifest'))
    expect(manifest.background_color).toBe(theme.color.bg)
    expect(manifest.theme_color).toBe(theme.color.bg)
    expect(here('../app.html')).toContain(`<meta name="theme-color" content="${theme.color.bg}" />`)
  })
})
