// Every page loads the one shared sheet, so a component the landing borrows
// from the app (MicMark) arrives with its styles.
import '../styles/index.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { applyTheme } from '../theme'
import { carryLook } from './carryLook'
import Landing from './Landing.jsx'

applyTheme()

// A click from here into the app carries the landing's look with it (./carryLook).
document.addEventListener('click', (event) => carryLook(event.target.closest?.('a[href]')))

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <Landing />
  </StrictMode>,
)
