import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// https://vite.dev/config/
export default defineConfig({
  plugins: [svelte()],
  server: {
    proxy: {
      // All backend requests go to the kids-game-utilities backend
      // It bridges chat/history/poll to the Pensieve harness internally
      '/api': {
        target: 'http://localhost:8790',
        changeOrigin: true,
      },
      '/chat': 'http://localhost:8790',
      '/poll': 'http://localhost:8790',
      '/history': 'http://localhost:8790',
      '/uploads': 'http://localhost:8790',
      '/bootstrap': 'http://localhost:8790',
      '/artifacts': 'http://localhost:8790',
      '/sessions': 'http://localhost:8790',
      '/agent-status': 'http://localhost:8790',
      '/health': 'http://localhost:8790',
      '/transcribe': 'http://localhost:8767', // Whisper stays direct for now
    },
  },
})
