import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      // Proxy backend API requests to the kids-game-utilities backend
      '/api': {
        target: 'http://localhost:8790',
        changeOrigin: true,
      },
      // Proxy chat/harness requests to the Pensieve frontend backend
      '/chat': 'http://localhost:8767',
      '/poll': 'http://localhost:8767',
      '/history': 'http://localhost:8767',
      '/transcribe': 'http://localhost:8767',
      '/upload-image': 'http://localhost:8767',
    },
  },
})
