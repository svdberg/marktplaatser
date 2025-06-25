<template>
  <div class="p-4">
    <h1 class="text-2xl font-bold mb-4">Authorization Result</h1>
    <p v-if="code">Code: {{ code }}</p>
    <p v-else>Waiting for authorization...</p>
  </div>
</template>

<script setup lang="ts">
const route = useRoute()
const code = route.query.code as string | undefined
</script>
