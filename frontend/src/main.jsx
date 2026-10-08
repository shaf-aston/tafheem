import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './styles/index.css'
import App from './App.jsx'
import { applySettings } from './lib/settings'
import { keepShelfInStep, pullBeforeStart } from './lib/shelf'
import { applyTheme } from './theme'

// The account's shelf first (lib/shelf.js), so settings and every panel start
// from what this name last chose on any device.
// A deploy replaces the hashed files, so a page open from before it asks for a
// tab file that is gone. Loading the page again picks up the new ones. Not when
// offline (a reload would only show the browser's error page), and not twice in
// a row, so a file that keeps failing cannot reload the page forever.
const RELOADED = 'reloaded-for-files'
window.addEventListener('vite:preloadError', (event) => {
  if (!navigator.onLine) return
  try {
    if (Date.now() - Number(sessionStorage.getItem(RELOADED)) < 10_000) return
    sessionStorage.setItem(RELOADED, String(Date.now()))
  } catch {
    return
  }
  event.preventDefault()
  location.reload()
})

applyTheme()
pullBeforeStart().then(() => {
  keepShelfInStep()
  applySettings()

  createRoot(document.getElementById('root')).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
})
