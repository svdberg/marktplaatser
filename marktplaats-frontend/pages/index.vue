<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Marktplaats Login</h1>
    <a :href="loginUrl" class="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded">
      Login with Marktplaats
    </a>
  </div>
</template>

<script setup lang="ts">
const config = useRuntimeConfig()
const scope = 'default'
const state = 'init'
const loginUrl = `${config.public.authBase}/authorize?response_type=code&client_id=${config.public.clientId}&redirect_uri=${encodeURIComponent(config.public.redirectUri)}&scope=${scope}&state=${state}`
</script>
