import { fileURLToPath, URL } from 'node:url'
import 'dotenv/config'
const FRONTEND_PORT = process.env.FRONTEND_PORT || 7070;

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    host: "0.0.0.0",
    port: FRONTEND_PORT,
  }
})
