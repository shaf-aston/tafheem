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
// tab file that is gone. Loading the page again picks up the new ones.
window.addEventListener('vite:preloadError', () => location.reload())

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
