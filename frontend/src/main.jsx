import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import './styles/index.css'
import App from './App.jsx'
import { applySettings } from './lib/settings'
import { keepShelfInStep, pullBeforeStart } from './lib/shelf'
import { applyTheme } from './theme'

// The account's shelf first (lib/shelf.js), so settings and every panel start
// from what this name last chose on any device.
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
