import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// The landing page's public address is /welcome; landing.html is only the file
// behind it. One rewrite for both the dev server and preview.
const PRETTY = { '/welcome': '/landing.html' }
const prettyUrls = {
  name: 'pretty-urls',
  configureServer(server) { server.middlewares.use(rewrite) },
  configurePreviewServer(server) { server.middlewares.use(rewrite) },
}
function rewrite(req, _res, next) {
  const [path, query] = req.url.split('?')
  const to = PRETTY[path.replace(/\/$/, '')]
  if (to) req.url = query ? `${to}?${query}` : to
  next()
}

export default defineConfig({
  plugins: [react(), tailwindcss(), prettyUrls],
  build: {
    rollupOptions: {
      // A second real page, not a route: the app has no router, and the
      // landing page must never load the header/tabs/command bar shell.
      input: { main: 'index.html', landing: 'landing.html' },
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
