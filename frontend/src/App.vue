<script setup>
import { ref } from 'vue'

const titleClass = ref('title')
const count = ref(0)
function notify() {
  alert("Clicked!")
}
</script>

<template>
    {{ count }}

  <h1 :class="titleClass">
  <a href="https://vuejs.org" @click.prevent="notify">
    Hello, World!
  </a>
  </h1>
  <h1 :class="titleClass">
 <button @click="count++" style="font-size: 20px;">Тыкни</button>
 </h1>


</template>

<style>



</style>
