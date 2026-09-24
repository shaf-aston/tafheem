import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The landing page is the front door, so it is index.html and needs no rewrite.
// The tool's public address is /app; app.html is only the file behind it. A host
// serves a real file before it consults a rewrite, which is why the front door is
// a filename and not a rule. One rewrite for the dev server and preview both.
const PRETTY = { '/app': '/app.html' }
const prettyUrls = {
  name: 'pretty-urls',
  configureServer(server) { server.middlewares.use(rewrite) },
  configurePreviewServer(server) { server.middlewares.use(rewrite) },
}
function rewrite(req, _res, next) {
  const [path, query] = req.url.split('?')
  const to = PRETTY[path.replace(/(.)\/$/, '$1')]
  if (to) req.url = query ? `${to}?${query}` : to
  next()
}

export default defineConfig({
  plugins: [react(), tailwindcss(), prettyUrls],
  build: {
    rollupOptions: {
      // A second real page, not a route: the app has no router, and the
      // landing page must never load the header/tabs/command bar shell.
      input: { landing: 'index.html', app: 'app.html' },
    },
  },
  server: {
    proxy: {
      '/api': {
        // The address, not the name. "localhost" makes node try IPv6 first and
        // the backend listens on IPv4 only, so every single request waited for
        // that miss before being sent: two seconds of nothing per call.
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
      },
    },
  },
})
