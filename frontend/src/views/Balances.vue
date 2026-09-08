<template>
  <div class="balances-container">
    <h2>Balance chart</h2>

    <!-- Date range form -->
    <form @submit.prevent="fetchBalances">
      <label for="from-date">От даты:</label>
      <input v-model="fromDate" type="date" id="from-date" />

      <label for="to-date">До даты:</label>
      <input v-model="toDate" type="date" id="to-date" />

      <button type="submit" class="confirm">Показать балансы</button>
    </form>

    <!-- Balances table -->
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

        <!-- Total row -->
        <tr class="total-row">
          <td><strong>Итого:</strong></td>
          <td v-for="date in dates" :key="date">{{ calculateTotal(date) || '—' }}</td>
        </tr>
      </tbody>
    </table>

    <p v-if="!categories.length || !dates.length || !balances.length">Нет данных для отображения.</p>

    <!-- Edit modal -->
    <EditBalanceModal
      v-if="showModal"
      :visible="showModal"
      :cat-id="selectedCatId"
      :date="selectedDate"
      :initial-value="getBalance(selectedCatId, selectedDate)"
      :balance-id="getBalanceId(selectedCatId, selectedDate)"
      @close="closeModal"
      @update-balance="handleBalanceUpdate"
    />
  </div>
</template>


<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import EditBalanceModal from './Modal.vue';


// State
const categories = ref([]);
const balances = ref([]);
const dates = ref([]);
const fromDate = ref('');
const toDate = ref('');
const showModal = ref(false);
const selectedCatId = ref(null);
const selectedDate = ref(null);


// Fetch balance data
async function fetchBalances() {
  try {
    // Default to the last 3 days if no range is set
    const today = new Date().toISOString().split('T')[0];
    const threeDaysAgo = new Date();
    threeDaysAgo.setDate(threeDaysAgo.getDate() - 3);

    fromDate.value = fromDate.value || threeDaysAgo.toISOString().split('T')[0];
    toDate.value = toDate.value || today;

    // Fetch balances for the selected date range
    const response = await axios.get('/balances/', {
      params: { from_date: fromDate.value, to_date: toDate.value }
    });

    // Make sure the data looks right
    if (response.data.length) {
      balances.value = response.data;

      // Build the list of unique dates from the balances
      dates.value = Array.from(new Set(response.data.map(item => item.date)));
    } else {
      console.error('Некорректные данные о балансах:', response.data);
    }

    // Fetch categories
    const categoriesResponse = await axios.get('/categories/');
    if (categoriesResponse.data) {
      categories.value = categoriesResponse.data;
    } else {
      console.error('Некорректные данные о категориях:', categoriesResponse.data);
    }
  } catch (error) {
    console.error('Ошибка при получении данных о балансах:', error.response ? error.response.data : error.message);
  }
}

// Get converted_value for a category/date pair
function getBalance(categoryId, date) {
  const balance = balances.value.find(b => b.cat_id === categoryId && b.date.startsWith(date));
  return balance ? balance.converted_value : null; // Show converted_value, not the raw value
}

// Get the balance row id for a category/date pair (needed to delete it)
function getBalanceId(categoryId, date) {
  const balance = balances.value.find(b => b.cat_id === categoryId && b.date.startsWith(date));
  return balance ? balance.id : null;
}

// Format a date as DD.MM.YYYY
function formatDate(date) {
  const parsedDate = new Date(date);
  return parsedDate.toLocaleDateString('ru-RU');
}

// Calculate the total for a given date
function calculateTotal(date) {
  const total = balances.value
    .filter(b => b.date.startsWith(date)) // Balances for this date
    .reduce((total, b) => total + (b.converted_value || 0), 0); // Sum converted_value

  return Math.floor(total); // Round down to a whole number
}

// Open the edit modal for a category/date pair
function openEditModal(catId, date) {
  console.log("Opening modal for category:", catId, "date:", date);
  selectedCatId.value = catId;
  selectedDate.value = date;
  showModal.value = true;
}

// Close the edit modal
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
  fetchBalances(); // Reload to reflect the latest data
}


// Save the edited balance
async function saveEditedBalance(newValue) {
  try {
    await axios.put('/balance/', {
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

// Load data on mount
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

/* Balances table */
.balances-table {
  width: 100%; /* Take up the full width */
  border-collapse: collapse;
  margin-top: 20px;
}

.balances-table th, .balances-table td {
  border: 1px solid #ccc;
  padding: 15px; /* Extra padding for readability */
  text-align: center; /* Center the text */
  vertical-align: middle;
}

.balances-table th {
  background-color: #f5f5f5;
  font-weight: bold;
}

.balances-table td {
  background-color: #fff;

}

/* Total row style */
.total-row td {
  font-weight: bold;
  border-top: 2px solid #000; /* Bold line above the total row */
}

/* Cap the width of the date columns */
.balances-table th:not(:first-child),
.balances-table td:not(:first-child) {
  min-width: 100px; /* Minimum width for date columns */
}
.clickable-cell {
  cursor: pointer;
  text-decoration: underline;
  color: blue;
}
</style>
