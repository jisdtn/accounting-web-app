<template>
  <div class="modal-overlay" v-if="visible" @click="emit('close')">
    <div class="modal-content" @click.stop>
      <h3>Редактировать баланс</h3>
      <input v-model="localValue" type="number" />
      <button @click="saveBalance" class="save-button">Сохранить</button>
      <button @click="emit('close')" class="cancel-button">Отмена</button>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, defineEmits, defineProps } from 'vue';
import axios from 'axios';

const emit = defineEmits(['close']);
const props = defineProps(['catId', 'date', 'visible', 'initialValue']);
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
    await axios.put('http://localhost:8000/balance/', {
      cat_id: props.catId,
      date: props.date,
      value: localValue.value,
    });
    alert('Баланс успешно обновлен');
    emit('close'); // Закрываем модальное окно
    emit('update-balance', { catId: props.catId, date: props.date, value: localValue.value }); // Передаем обновленные данные
  } catch (error) {
    console.error('Ошибка при обновлении баланса:', error);
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
.cancel-button {
  flex: 1; /* Делает кнопки равной ширины */
  color: white;
  border: none;
  border-radius: 5px;
  padding: 10px 0;
  cursor: pointer;
  margin: 0 5px; /* Добавляет небольшой промежуток между кнопками */
}

.save-button {
  background-color: #28a745; /* Зеленый */
}

.save-button:hover {
  background-color: #218838;
}

.cancel-button {
  background-color: #007bff; /* Синий */
}

.cancel-button:hover {
  background-color: #0069d9;
}
</style>
