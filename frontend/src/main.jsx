import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './styles/index.css'
import App from './App.jsx'
import { applySettings } from './lib/store/settings'
import { keepShelfInStep, pullShelf } from './lib/store/shelf'
import { watchInstall } from './lib/shell/install'
import { startOffline } from './lib/shell/offline'

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

applySettings()
watchInstall()
startOffline()
keepShelfInStep()

// Never wait on the server to show: this device's copy draws at once, and the
// account's shelf (lib/store/shelf.js), landing behind it, updates every reader live
// (lib/store/stored.js), so what this name last chose on any device still arrives.
createRoot(document.getElementById('root')).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
pullShelf()
