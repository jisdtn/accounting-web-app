<template>
  <div class="modal-overlay" v-if="visible" @click="emit('close')">
    <div class="modal-content" @click.stop>
      <h3>Редактировать баланс</h3>
      <input v-model="localValue" type="number" />
      <div class="button-container">
        <button @click="saveBalance" class="save-button">Сохранить</button>
        <button v-if="props.balanceId" @click="deleteBalance" class="delete-button">Удалить</button>
        <button @click="emit('close')" class="cancel-button">Отмена</button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue';
import axios from 'axios';

const emit = defineEmits(['close']);
const props = defineProps(['catId', 'date', 'visible', 'initialValue', 'balanceId']);
const localValue = ref(props.initialValue);

watch(() => props.initialValue, (newVal) => {
  localValue.value = newVal;
});

async function saveBalance() {
  try {
    console.log("Отправляемые данные:", {
      cat_id: props.catId,
      date: props.date,
      value: localValue.value,
    });
    await axios.put('/balance/', {
      cat_id: props.catId,
      date: props.date,
      value: localValue.value,
    });
    alert('Баланс успешно обновлен');
    emit('close'); // Close the modal
    emit('update-balance', { catId: props.catId, date: props.date, value: localValue.value }); // Pass the updated data
  } catch (error) {
    console.error('Ошибка при обновлении баланса:', error);
  }
}

async function deleteBalance() {
  if (!confirm('Удалить эту запись баланса?')) {
    return;
  }
  try {
    await axios.delete(`/balance/${props.balanceId}`);
    emit('close');
    emit('update-balance', { catId: props.catId, date: props.date, value: null });
  } catch (error) {
    console.error('Ошибка при удалении баланса:', error);
  }
}
</script>

<style scoped>
.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background-color: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;
}

.modal-content {
  background-color: white;
  padding: 20px;
  border-radius: 8px;
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  width: 300px;
  text-align: center;
}

.modal-content input {
  margin-bottom: 20px;
  padding: 10px;
  border: 1px solid #ccc;
  border-radius: 4px;
  width: 100%;
}

.button-container {
  display: flex;
  justify-content: space-between;
}

.save-button,
.delete-button,
.cancel-button {
  flex: 1; /* Equal-width buttons */
  color: white;
  border: none;
  border-radius: 5px;
  padding: 10px 0;
  cursor: pointer;
  margin: 0 5px; /* Small gap between the buttons */
}

.save-button {
  background-color: #28a745; /* Green */
}

.save-button:hover {
  background-color: #218838;
}

.delete-button {
  background-color: #dc3545; /* Red */
}

.delete-button:hover {
  background-color: #c82333;
}

.cancel-button {
  background-color: #007bff; /* Blue */
}

.cancel-button:hover {
  background-color: #0069d9;
}
</style>
