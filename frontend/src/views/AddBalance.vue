<template>
  <div class="form-container">
    <h2>Добавление нового баланса</h2>

    <form @submit.prevent="addBalances" class="balance-form">
      <!-- Перебираем категории и создаем поля для каждой категории -->
      <div v-for="category in categories" :key="category.id" class="form-item">
        <label>{{ category.name }} ({{ category.currency }}):</label>

        <!-- Поле для ввода суммы -->
        <div class="input-group">
          <label for="value">Введите сумму:</label>
          <input v-model="balances[category.id].value" type="number" placeholder="Сумма" required />

          <!-- Подсказка с предыдущим балансом -->
          <span
            v-if="previousBalances[category.id]"
            class="previous-balance"
            @click="setPreviousBalance(category.id)"
            :title="'Кликните, чтобы использовать баланс за предыдущий день: ' + previousBalances[category.id]"
          >
            {{ previousBalances[category.id] }} (пред.)
          </span>
        </div>
      </div>

      <!-- Синяя кнопка подтверждения операции -->
      <button type="submit" class="confirm">Добавить балансы</button>
    </form>

    <!-- Сообщение об успехе или ошибке -->
    <p v-if="message">{{ message }}</p>
  </div>
</template>


<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

// Храним категории, текущие балансы и предыдущие балансы
const categories = ref([]);
const balances = ref({});
const previousBalances = ref({}); // Для хранения предыдущих балансов
const message = ref('');
const router = useRouter(); // Инициализируем роутер

// Функция для получения списка категорий с бэкенда
async function fetchCategories() {
  try {
    const response = await axios.get('http://localhost:8000/categories');
    categories.value = response.data;

    // Инициализация пустых значений для каждой категории
    categories.value.forEach(category => {
      balances.value[category.id] = { value: null };
      previousBalances.value[category.id] = null; // Инициализация предыдущих балансов
    });
  } catch (error) {
    console.error('Ошибка при получении категорий:', error.response ? error.response.data : error.message);
  }
}

// Функция для получения балансов за предыдущий день
async function fetchPreviousBalances() {
  try {
    const previousDay = new Date();
    previousDay.setDate(previousDay.getDate() - 1);
    const formattedPreviousDay = previousDay.toISOString().split('T')[0];

    const response = await axios.get('http://localhost:8000/balances', {
      params: { from_date: formattedPreviousDay, to_date: formattedPreviousDay }
    });

    // Сохраняем предыдущие балансы (используем поле value) для каждой категории
    response.data.forEach(balance => {
      previousBalances.value[balance.cat_id] = balance.value || null;
    });
  } catch (error) {
    console.error('An error occurred while getting previous balances:', error.response ? error.response.data : error.message);
  }
}

// Функция для подстановки предыдущего баланса
function setPreviousBalance(categoryId) {
  const previousBalance = previousBalances.value[categoryId];
  if (previousBalance) {
    balances.value[categoryId].value = previousBalance; // Подставляем значение из value
  }
}

// Вызов функции для получения категорий при монтировании компонента
onMounted(() => {
  fetchCategories();
  fetchPreviousBalances(); // Загружаем предыдущие балансы
});

// Функция для отправки данных на бэкенд
async function addBalances() {
  try {
    // Собираем все данные для отправки в одном массиве
    const balanceData = Object.entries(balances.value)
      .filter(([_, { value }]) => value !== null) // Фильтруем только заполненные значения
      .map(([cat_id, { value }]) => ({
        cat_id: parseInt(cat_id),
        value: parseInt(value)
      }));
    // Отправляем один запрос с массивом данных
    const response = await axios.post('http://localhost:8000/balance/', balanceData);

    message.value = 'Success!';

    // После успешного добавления перенаправляем на главную страницу
    setTimeout(() => {
      router.push('/');
    }, 2000); // Ожидаем 2 секунды, чтобы показать сообщение, и затем перенаправляем
  } catch (error) {
    console.error('An error occurred while adding balances:', error.response ? error.response.data : error.message);
    message.value = `An error occurred while adding balances: ${error.response ? error.response.data.detail : error.message}`;
  }
}

</script>

<style scoped>
/* Центрирование формы */
.form-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

/* Стили формы */
.balance-form {
  width: 100%;
  max-width: 600px;
  background-color: #fff;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1);
}

.form-item {
  margin-bottom: 20px;
}

.input-group {
  margin-bottom: 10px;
  position: relative;
}

input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
}

/* Подсказка с предыдущим балансом */
.previous-balance {
  color: #aaa; /* Серый цвет */
  cursor: pointer;
  font-size: 0.9em;
  margin-left: 10px;
}

.previous-balance:hover {
  text-decoration: underline;
}

/* Синяя и закруглённая кнопка */
button.confirm {
  width: 100%;
  padding: 10px;
  background-color: #1F91DC;
  color: white;
  border: none;
  border-radius: 5px;
  cursor: pointer;
  font-size: 16px;
  margin-top: 20px;
}

/* Изменение фона кнопки при наведении */
button.confirm:hover {
  background-color: #0056b3;
}
</style>
