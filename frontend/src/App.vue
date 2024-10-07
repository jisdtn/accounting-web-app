<template>
  <div id="app">
    <!-- Хедер с изменяемым фоном -->
    <header :class="headerClass">
      <h1>Мои финансы</h1>
    </header>

    <!-- Основной контент приложения -->
    <main>
      <router-view /> <!-- Здесь будут отображаться компоненты в зависимости от маршрута -->
    </main>

    <footer>
      <p>© 2024 Моё приложение</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute } from 'vue-router';
import axios from 'axios';

// Получаем текущий маршрут
const route = useRoute();
const headerClass = ref('header-default');

// Наблюдаем за изменением маршрута
watch(
  () => route.path,
  (newPath) => {
    // Если маршрут — это главная страница, проверяем балансы и меняем класс заголовка
    if (newPath === '/') {
      checkBalancesAndUpdateHeader();
    } else {
      headerClass.value = 'header-default';
    }
  }
);

// Функция для проверки балансов и изменения цвета заголовка
async function checkBalancesAndUpdateHeader() {
  try {
    const today = new Date().toISOString().split('T')[0]; // текущая дата
    const response = await axios.get('http://localhost:8000/balances', {
      params: { from_date: today, to_date: today },
    });

    const balances = response.data;

    // Если есть балансы за текущую дату, меняем цвет заголовка на зелёный, иначе красный
    headerClass.value = balances.length > 0 ? 'header-green' : 'header-red';
  } catch (error) {
    console.error('Ошибка при проверке балансов:', error);
  }
}

// Когда приложение загружается, проверяем балансы сразу
onMounted(() => {
  checkBalancesAndUpdateHeader();
});
</script>

<style>
/* Подключаем шрифт Roboto из Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

/* Применяем глобальные стили */
body, html {
  font-family: 'Roboto', sans-serif; /* Современный шрифт */
  background-color: #f5f5f5; /* Мягкий фон */
  margin: 0;
  padding: 0;
  color: #333;
  line-height: 1.6;
  height: 100%; /* Обеспечиваем, что body и html занимают всю высоту */
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh; /* Обеспечиваем, что #app занимает всю высоту экрана */
}

header {
  padding: 20px;
  color: white;
  border-radius: 8px;
  text-align: center; /* Добавляем выравнивание текста по центру */
}

h1 {
  margin: 0; /* Убираем отступы сверху и снизу, если они есть */
}
/* Стандартный фон для всех страниц */
.header-default {
  background-color: #1f91dc;
}

/* Красный фон для главной страницы, если балансы не внесены */
.header-red {
  background-color: #fe0000;
}

/* Зелёный фон для главной страницы, если балансы внесены */
.header-green {
  background-color: #1bc727;
}

/* Main занимает все доступное пространство */
main {
  flex: 1; /* Заставляем main занимать всё доступное пространство */
  padding: 20px;
}

/* Футер всегда внизу */
footer {
  background-color: #333;
  color: white;
  padding: 10px;
  border-radius: 8px;
  text-align: center;
}

/* Стили для кнопок */
button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px; /* Закругленные углы */
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease; /* Плавный переход при изменении цвета */
}

/* Синяя кнопка для подтверждения операций */
button.confirm {
  background-color: #1F91DC;
  color: white;
}

/* Изменение цвета при наведении */
button.confirm:hover {
  background-color: #006bb7;
}
</style>
