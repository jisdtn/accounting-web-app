import { createApp } from "vue";
import axios from 'axios';
import App from './App.vue';
import router from './router';

const app = createApp(App);

axios.defaults.withCredentials = true;
axios.defaults.baseURL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
axios.defaults.headers.common['Authorization'] = `Bearer ${import.meta.env.VITE_API_TOKEN}`;

app.use(router);
app.mount("#app");
