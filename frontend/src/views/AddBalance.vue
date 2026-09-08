<template>
  <div class="form-container">
    <h2>Добавление нового баланса</h2>

    <form @submit.prevent="addBalances" class="balance-form">
      <!-- Render an input for each category -->
      <div v-for="category in categories" :key="category.id" class="form-item">
        <label>{{ category.name }} ({{ category.currency }}):</label>

        <!-- Value input -->
        <div class="input-group">
          <label for="value">Введите сумму:</label>
          <input v-model="balances[category.id].value" type="number" placeholder="Сумма" />

          <!-- Hint showing the previous balance -->
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

      <!-- Blue confirm button -->
      <button type="submit" class="confirm">Добавить балансы</button>
    </form>

    <!-- Success or error message -->
    <p v-if="message">{{ message }}</p>
  </div>
</template>


<script setup>
import { ref, onMounted } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router';

// Categories, current balances, and previous balances
const categories = ref([]);
const balances = ref({});
const previousBalances = ref({}); // Holds the previous-day balances
const message = ref('');
const router = useRouter();

// Fetch the category list from the backend
async function fetchCategories() {
  try {
    const response = await axios.get('/categories/');
    categories.value = response.data;

    // Initialize empty values for each category
    categories.value.forEach(category => {
      balances.value[category.id] = { value: null };
      previousBalances.value[category.id] = null;
    });
  } catch (error) {
    console.error('Ошибка при получении категорий:', error.response ? error.response.data : error.message);
  }
}

// Fetch balances from the previous day
async function fetchPreviousBalances() {
  try {
    const previousDay = new Date();
    previousDay.setDate(previousDay.getDate() - 1);
    const formattedPreviousDay = previousDay.toISOString().split('T')[0];

    const response = await axios.get('/balances/', {
      params: { from_date: formattedPreviousDay, to_date: formattedPreviousDay }
    });

    // Store the previous balance value for each category
    response.data.forEach(balance => {
      previousBalances.value[balance.cat_id] = balance.value || null;
    });
  } catch (error) {
    console.error('An error occurred while getting previous balances:', error.response ? error.response.data : error.message);
  }
}

// Fill in the previous balance for a category
function setPreviousBalance(categoryId) {
  const previousBalance = previousBalances.value[categoryId];
  if (previousBalance) {
    balances.value[categoryId].value = previousBalance;
  }
}

// Load categories and previous balances on mount
onMounted(() => {
  fetchCategories();
  fetchPreviousBalances();
});

// Submit the entered balances to the backend
async function addBalances() {
  try {
    // Collect all entries into a single array
    const balanceData = Object.entries(balances.value)
      .filter(([_, { value }]) => value !== null) // Only keep filled-in values
      .map(([cat_id, { value }]) => ({
        cat_id: parseInt(cat_id),
        value: parseInt(value)
      }));

    if (!balanceData.length) {
      message.value = 'Заполни сумму хотя бы для одной категории.';
      return;
    }

    // Creates new entries; categories that already have a record for today are skipped here
    const response = await axios.post('/balance/', balanceData);
    const createdCatIds = new Set(response.data.map(item => item.cat_id));

    // For anything skipped (already recorded today), update it instead of silently dropping it
    const alreadyRecorded = balanceData.filter(item => !createdCatIds.has(item.cat_id));
    for (const item of alreadyRecorded) {
      await axios.patch('/balance/', item);
    }

    const parts = [];
    if (createdCatIds.size) parts.push(`добавлено: ${createdCatIds.size}`);
    if (alreadyRecorded.length) parts.push(`обновлено (уже было записано сегодня): ${alreadyRecorded.length}`);
    message.value = `Готово — ${parts.join(', ')}.`;

    // Redirect to the home page after a successful submit
    setTimeout(() => {
      router.push('/');
    }, 2000); // Wait 2s so the message is visible before redirecting
  } catch (error) {
    console.error('An error occurred while adding balances:', error.response ? error.response.data : error.message);
    message.value = `An error occurred while adding balances: ${error.response ? error.response.data.detail : error.message}`;
  }
}

</script>

<style scoped>
/* Center the form */
.form-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 100vh;
}

/* Form styles */
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

/* Hint showing the previous balance */
.previous-balance {
  color: #aaa; /* Gray */
  cursor: pointer;
  font-size: 0.9em;
  margin-left: 10px;
}

.previous-balance:hover {
  text-decoration: underline;
}

/* Blue rounded button */
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

/* Button background change on hover */
button.confirm:hover {
  background-color: #0056b3;
}
</style>
