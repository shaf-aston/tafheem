import '../styles/index.css'
import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import { applyTheme } from '../theme'
import NotFound from './NotFound.jsx'

applyTheme()

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <NotFound />
  </StrictMode>,
)
