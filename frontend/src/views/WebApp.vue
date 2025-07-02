<template>
  <div>
    <h1>Добро пожаловать в Telegram Web App</h1>
  </div>
</template>

<script>
export default {
  mounted() {
    const tg = window.Telegram.WebApp;
    tg.expand(); // Разворачивает WebApp на весь экран
  },
};
</script>
