<template>
  <div>
    <h1>Добро пожаловать в Telegram Web App</h1>
  </div>
</template>

<script>
export default {
  mounted() {
    window.Telegram?.WebApp?.expand(); // Expand the WebApp to full screen
  },
};
</script>
