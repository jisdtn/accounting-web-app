<template>
  <div class="form-container">
    <h2>Добавление новой категории</h2>

    <form @submit.prevent="addCategory" class="category-form">
      <div class="form-item">
        <label for="name">Имя категории:</label>
        <input v-model="name" type="text" placeholder="Введите имя категории" required />
      </div>

      <div class="form-item">
        <label for="currency">Валюта категории:</label>
        <input v-model="currency" type="text" placeholder="Введите валюту (например, USD)" required />
      </div>

      <!-- Confirm button -->
      <button type="submit" class="confirm">Добавить категорию</button>
    </form>

    <!-- Success or error message -->
    <p v-if="message">{{ message }}</p>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';
import { useRouter } from 'vue-router'; // Used to redirect after submit

// Input fields
const name = ref('');
const currency = ref('');
const message = ref('');
const router = useRouter();

// Create a new category
async function addCategory() {
  try {
    const response = await axios.post('/categories/', {
      name: name.value,
      currency: currency.value
    });

    message.value = `Категория "${response.data.name}" успешно добавлена!`;
    // Reset the fields after a successful submit
    name.value = '';
    currency.value = '';

    // Redirect to the home page after 2 seconds
    setTimeout(() => {
      router.push('/');
    }, 2000);
  } catch (error) {
    console.error('Ошибка при добавлении категории:', error.response ? error.response.data : error.message);
    message.value = 'Ошибка при добавлении категории. Попробуйте снова.';
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
.category-form {
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

input {
  width: 100%;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
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
