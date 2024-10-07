<template>
  <div>
    <h1>Проверка связи с бекендом</h1>
    <button @click="fetchData">Получить сообщение от бекенда</button>
    <p v-if="message">{{ message }}</p>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data() {
    return {
      message: '',  // Состояние для хранения ответа от бекенда
    };
  },
  methods: {
    async fetchData() {
      try {
        // Отправляем GET запрос на бекенд
        const response = await axios.get('/balances');
        this.message = response.data.message;  // Сохраняем ответ в состоянии
      } catch (error) {
        console.error('Ошибка при получении данных от бекенда:', error);
        this.message = 'Не удалось получить данные.';
      }
    },
  },
};
</script>
