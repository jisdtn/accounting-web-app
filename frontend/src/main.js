import 'bootstrap/dist/css/bootstrap.css';
import { createApp } from "vue";
import axios from 'axios';
import App from './App.vue';
import router from './router';

const app = createApp(App);

const script = document.createElement('script');
script.src = "https://telegram.org/js/telegram-web-app.js";
script.onload = () => {
  console.log("Telegram Web App API подключен");
};
document.head.appendChild(script);

axios.defaults.withCredentials = true;
axios.defaults.baseURL = 'http://backend:8000';  // the FastAPI backend

app.use(router);
app.mount("#app");
