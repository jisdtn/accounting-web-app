<!-- src/views/Home.vue -->
<template>
  <div class="home-container">
    <h2>Выбери действие</h2>

      <!-- Кнопки на главной странице -->
        <div class="buttons">
      <!-- Активная кнопка для перехода на экран с балансами -->
      <button class="confirm" @click="$router.push('/balances')">Текущие накопления</button>

      <!-- Активная кнопка для перехода на страницу добавления баланса -->
      <button @click="$router.push('/add-balance')" class="confirm">Добавить баланс</button>

      <!-- Активная кнопка для перехода на страницу добавления категории -->
      <button @click="$router.push('/add-category')" class="confirm">Добавить категорию</button>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// Логика для изменения фона заголовка через App.vue
const headerClass = ref('header-red');

onMounted(async () => {
  try {
    const today = new Date().toISOString().split('T')[0]; // Текущая дата в формате YYYY-MM-DD
    const response = await axios.get('http://localhost:8000/balances', {
      params: { from_date: today, to_date: today }
    });

    // Если есть балансы за текущую дату, меняем цвет фона заголовка на зелёный
    if (response.data.length > 0) {
      headerClass.value = 'header-green';
    }
  } catch (error) {
    console.error('Ошибка при получении балансов:', error);
  }
});
</script>

<style scoped>
/* Весь контейнер страницы */
.home-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  justify-content: center; /* Центрирование содержимого по вертикали */
  align-items: center;
  padding: 20px;
}

/* Кнопки на странице */
.buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

button {
  padding: 10px 20px;
  font-size: 16px;
  border-radius: 8px; /* Закругленные углы */
}

button.inactive {
  background-color: #ccc;
  cursor: not-allowed;
}

button.confirm {
  background-color: #1F91DC; /* Синий цвет */
  color: white;
  border: none;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

button.confirm:hover {
  background-color: #006bb7; /* Темнее при наведении */
}
</style>
