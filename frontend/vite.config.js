import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { fileURLToPath, URL } from 'url';
import dotenv from 'dotenv';

// Загружаем переменные окружения из файла .env
dotenv.config();

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
    port: 7070,  // Используем переменную окружения
    proxy: {
      '/balances': {
        target: 'http://backend:8000',  // Используем имя сервиса из docker-compose
        changeOrigin: true,
        secure: false,
      },
    },
  },
});
