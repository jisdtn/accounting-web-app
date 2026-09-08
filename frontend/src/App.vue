<template>
  <div id="app">
    <!-- Header with a color that changes based on state -->
    <header :class="headerClass">
      <button v-if="route.path !== '/'" class="back-button" @click="router.push('/')">
        ← На главную
      </button>
      <h1>Мои финансы</h1>
    </header>

    <!-- Main app content -->
    <main>
      <router-view /> <!-- Route components render here -->
    </main>

    <footer>
      <p>© {{ currentYear }} Моё приложение</p>
    </footer>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';

const currentYear = new Date().getFullYear();
const router = useRouter();

// The Telegram Web Apps script is loaded statically in index.html (before this
// module runs), so window.Telegram is already available here.
onMounted(() => {
  if (window.Telegram?.WebApp) {
    window.Telegram.WebApp.ready();
    console.log('Telegram user info:', window.Telegram.WebApp.initDataUnsafe.user);
  }
});


// Track the current route
const route = useRoute();
const headerClass = ref('header-default');

// Watch for route changes
watch(
  () => route.path,
  (newPath) => {
    // On the home page, check balances and update the header color
    if (newPath === '/') {
      checkBalancesAndUpdateHeader();
    } else {
      headerClass.value = 'header-default';
    }
  }
);

// Check balances and update the header color
async function checkBalancesAndUpdateHeader() {
  try {
    const today = new Date().toISOString().split('T')[0]; // today's date
    const response = await axios.get('/balances/', {
      params: { from_date: today, to_date: today },
    });

    const balances = response.data;

    // Green header if there are balances for today, red otherwise
    headerClass.value = balances.length > 0 ? 'header-green' : 'header-red';
  } catch (error) {
    console.error('Ошибка при проверке балансов:', error);
  }
}

// Check balances right away on app load
onMounted(() => {
  checkBalancesAndUpdateHeader();
});
</script>

<style>
/* Load the Roboto font from Google Fonts */
@import url('https://fonts.googleapis.com/css2?family=Roboto:wght@400;700&display=swap');

/* Global styles */
body, html {
  font-family: 'Roboto', sans-serif; /* Modern font */
  background-color: #f5f5f5; /* Soft background */
  margin: 0;
  padding: 0;
  color: #333;
  line-height: 1.6;
  height: 100%; /* Make body and html fill the full height */
}

#app {
  display: flex;
  flex-direction: column;
  min-height: 100vh; /* Make #app fill the full viewport height */
}

header {
  padding: 16px 20px;
  color: white;
  border-radius: 8px;
  display: grid;
  grid-template-columns: auto 1fr; /* button column collapses to 0 when absent */
  align-items: center;
  gap: 8px;
}

.back-button {
  justify-self: start;
  background: rgba(255, 255, 255, 0.2);
  color: white;
  border: none;
  border-radius: 6px;
  padding: 6px 12px;
  font-size: 13px;
  white-space: nowrap;
  cursor: pointer;
}

.back-button:hover {
  background: rgba(255, 255, 255, 0.35);
}

h1 {
  grid-column: 2;
  margin: 0; /* Remove top/bottom margin */
  text-align: center;
  font-size: 1.3rem;
}
/* Default background for all pages */
.header-default {
  background-color: #1f91dc;
}

/* Red background on the home page when balances are missing */
.header-red {
  background-color: #fe0000;
}

/* Green background on the home page when balances are entered */
.header-green {
  background-color: #1bc727;
}

/* Main takes up all available space */
main {
  flex: 1; /* Let main fill all available space */
  padding: 20px;
}

/* Footer always stays at the bottom */
footer {
  background-color: #333;
  color: white;
  padding: 10px;
  border-radius: 8px;
  text-align: center;
}

/* Button styles */
button {
  padding: 10px 20px;
  border: none;
  border-radius: 8px; /* Rounded corners */
  cursor: pointer;
  font-size: 16px;
  transition: background-color 0.3s ease; /* Smooth color transition */
}

/* Blue button for confirming actions */
button.confirm {
  background-color: #1F91DC;
  color: white;
}

/* Color change on hover */
button.confirm:hover {
  background-color: #006bb7;
}
</style>
