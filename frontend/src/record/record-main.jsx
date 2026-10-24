import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'

import '../styles/index.css'
import Studio from './Studio.jsx'
import { applySettings } from '../lib/store/settings'

applySettings()
createRoot(document.getElementById('root')).render(<StrictMode><Studio /></StrictMode>)
