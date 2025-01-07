<template>
  <div class="balances-container">
    <h2>Balance chart</h2>

    <!-- Форма для ввода диапазона дат -->
    <form @submit.prevent="fetchBalances">
      <label for="from-date">От даты:</label>
      <input v-model="fromDate" type="date" id="from-date" />

      <label for="to-date">До даты:</label>
      <input v-model="toDate" type="date" id="to-date" />

      <button type="submit" class="confirm">Показать балансы</button>
    </form>

    <!-- Таблица с балансами -->
    <table v-if="categories.length && dates.length && balances.length" class="balances-table">
      <thead>
        <tr>
          <th>Категория</th>
          <th v-for="date in dates" :key="date">{{ formatDate(date) }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="category in categories" :key="category.id">
          <td>{{ category.name }}</td>
          <td v-for="date in dates" :key="date">
            <span class="clickable-cell" @click="openEditModal(category.id, date)">
                {{ getBalance(category.id, date) || '—' }}
            </span>
          </td>
        </tr>

        <!-- Строка с Итого -->
        <tr class="total-row">
          <td><strong>Итого:</strong></td>
          <td v-for="date in dates" :key="date">{{ calculateTotal(date) || '—' }}</td>
        </tr>
      </tbody>
    </table>

    <p v-if="!categories.length || !dates.length || !balances.length">Нет данных для отображения.</p>

    <!-- Модальное окно -->
    <EditBalanceModal
      v-if="showModal"
      :visible="showModal"
      :cat-id="selectedCatId"
      :date="selectedDate"
      :initial-value="getBalance(selectedCatId, selectedDate)"
      @close="closeModal"
      @update-balance="handleBalanceUpdate"
    />
  </div>
</template>


<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import EditBalanceModal from './Modal.vue';


// Переменные для хранения данных
const categories = ref([]);
const balances = ref([]);
const dates = ref([]);
const fromDate = ref('');
const toDate = ref('');
const showModal = ref(false);
const selectedCatId = ref(null);
const selectedDate = ref(null);


// Функция для получения данных о балансах
async function fetchBalances() {
  try {
    // Если не задан диапазон дат, выводим последние 3 дня
    const today = new Date().toISOString().split('T')[0];
    const threeDaysAgo = new Date();
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);

    fromDate.value = fromDate.value || threeDaysAgo.toISOString().split('T')[0];
    toDate.value = toDate.value || today;

    // Получаем балансы за указанный диапазон дат
    const response = await axios.get('http://localhost:8000/balances', {
      params: { from_date: fromDate.value, to_date: toDate.value }
    });

    // Проверяем, что данные приходят корректно
    if (response.data.length) {
      balances.value = response.data;

      // Создаем массив уникальных дат из балансов
      dates.value = Array.from(new Set(response.data.map(item => item.date)));
    } else {
      console.error('Некорректные данные о балансах:', response.data);
    }

    // Получаем категории
    const categoriesResponse = await axios.get('http://localhost:8000/categories');
    if (categoriesResponse.data) {
      categories.value = categoriesResponse.data;
    } else {
      console.error('Некорректные данные о категориях:', categoriesResponse.data);
    }
  } catch (error) {
    console.error('Ошибка при получении данных о балансах:', error.response ? error.response.data : error.message);
  }
}

// Функция для получения converted_value по категории и дате
function getBalance(categoryId, date) {
  const balance = balances.value.find(b => b.cat_id === categoryId && b.date.startsWith(date));
  return balance ? balance.converted_value : null; // Возвращаем converted_value вместо value
}

// Функция для форматирования даты в формате DD.MM.YYYY
function formatDate(date) {
  const parsedDate = new Date(date);
  return parsedDate.toLocaleDateString('ru-RU'); // Форматируем дату
}

// Функция для расчета суммы (Итого) по дате
function calculateTotal(date) {
  const total = balances.value
    .filter(b => b.date.startsWith(date)) // Ищем балансы за указанную дату
    .reduce((total, b) => total + (b.converted_value || 0), 0); // Суммируем значения converted_value

  return Math.floor(total); // Округляем вниз до целого числа
}

// Открытие модального окна с указанием catId и даты
function openEditModal(catId, date) {
  console.log("Opening modal for category:", catId, "date:", date);
  selectedCatId.value = catId;
  selectedDate.value = date;
  showModal.value = true;
}

// Закрытие модального окна
function closeModal() {
  showModal.value = false;
  selectedCatId.value = null;
  selectedDate.value = null;
}

function handleBalanceUpdate(updatedBalance) {
  const balanceToUpdate = balances.value.find(
    (balance) => balance.cat_id === updatedBalance.cat_id && balance.date.startsWith(updatedBalance.date)
  );
  if (balanceToUpdate) {
    balanceToUpdate.value = updatedBalance.value;
  }
  fetchBalances(); // Перезагружаем данные, чтобы отобразить актуальную информацию
}


// Сохранение отредактированного баланса
async function saveEditedBalance(newValue) {
  try {
    await axios.put('http://localhost:8000/balance', {
      cat_id: selectedCatId.value,
      date: selectedDate.value,
      value: newValue,
    });
    closeModal();
    fetchBalances();
  } catch (error) {
    console.error('Ошибка при сохранении баланса:', error);
  }
}

// Загружаем данные при монтировании компонента
onMounted(() => {
  fetchBalances();
});
</script>


<style scoped>
.balances-container {
  padding: 20px;
  text-align: center;
}

form {
  margin-bottom: 20px;
}

input {
  margin: 0 10px;
  padding: 5px;
}

.confirm {
  background-color: #1F91DC;
  color: white;
  border: none;
  border-radius: 5px;
  padding: 10px 20px;
  cursor: pointer;
}

.confirm:hover {
  background-color: #0056b3;
}

/* Таблица с балансами */
.balances-table {
  width: 100%; /* Таблица будет занимать всю ширину */
  border-collapse: collapse;
  margin-top: 20px;
}

.balances-table th, .balances-table td {
  border: 1px solid #ccc;
  padding: 15px; /* Увеличим padding для более читабельного отображения */
  text-align: center; /* Выравниваем текст по центру */
  vertical-align: middle; /* Выравнивание по вертикали */
}

.balances-table th {
  background-color: #f5f5f5;
  font-weight: bold;
}

.balances-table td {
  background-color: #fff;

}

/* Стиль для строки с Итого */
.total-row td {
  font-weight: bold;
  border-top: 2px solid #000; /* Жирная линия сверху строки Итого */
}

/* Ограничим ширину колонок с датами */
.balances-table th:not(:first-child),
.balances-table td:not(:first-child) {
  min-width: 100px; /* Минимальная ширина для столбцов с датами */
}
.clickable-cell {
  cursor: pointer;
  text-decoration: underline;
  color: blue;
}
</style>
