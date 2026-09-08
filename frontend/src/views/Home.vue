<!-- src/views/Home.vue -->
<template>
  <div class="home-container">
    <h2>Выбери действие</h2>

      <!-- Home page buttons -->
        <div class="buttons">
      <!-- Go to the balances screen -->
      <button class="confirm" @click="$router.push('/balances')">Текущие накопления</button>

      <!-- Go to the add-balance page -->
      <button @click="$router.push('/add-balance')" class="confirm">Добавить баланс</button>

      <!-- Go to the add-category page -->
      <button @click="$router.push('/add-category')" class="confirm">Добавить категорию</button>

    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';

// Header background is controlled through App.vue's headerClass
const headerClass = ref('header-red');

onMounted(async () => {
  try {
    const today = new Date().toISOString().split('T')[0]; // Today's date as YYYY-MM-DD
    const response = await axios.get('/balances/', {
      params: { from_date: today, to_date: today }
    });

    // Turn the header green if there are balances for today
    if (response.data.length > 0) {
      headerClass.value = 'header-green';
    }
  } catch (error) {
    console.error('Ошибка при получении балансов:', error);
  }
});
</script>

<style scoped>
/* Full-page container */
.home-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  justify-content: center; /* Center content vertically */
  align-items: center;
  padding: 20px;
}

/* Page buttons */
.buttons {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-top: 20px;
}

button {
  padding: 10px 20px;
  font-size: 16px;
  border-radius: 8px; /* Rounded corners */
}

button.inactive {
  background-color: #ccc;
  cursor: not-allowed;
}

button.confirm {
  background-color: #1F91DC; /* Blue */
  color: white;
  border: none;
  cursor: pointer;
  transition: background-color 0.3s ease;
}

button.confirm:hover {
  background-color: #006bb7; /* Darker on hover */
}
</style>
