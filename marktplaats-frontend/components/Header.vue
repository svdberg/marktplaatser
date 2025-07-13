<template>
  <header class="bg-white shadow-sm border-b">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between items-center h-16">
        <div class="flex items-center space-x-4">
          <NuxtLink 
            v-if="currentPage !== 'home'" 
            to="/" 
            class="btn btn-secondary text-sm"
          >
            🏠 Home
          </NuxtLink>
          <h1 class="text-xl font-bold text-gray-900">
            {{ pageTitle }}
          </h1>
        </div>
        <div class="flex items-center space-x-4">
          <!-- Navigation Links -->
          <div v-if="userToken" class="flex items-center space-x-3">
            <NuxtLink
              v-if="currentPage !== 'drafts'"
              to="/drafts"
              class="btn btn-secondary text-sm"
            >
              📝 My Drafts
            </NuxtLink>
            <NuxtLink
              v-if="currentPage !== 'listings'"
              to="/listings"
              class="btn btn-secondary text-sm"
            >
              📋 My Listings
            </NuxtLink>
            <NuxtLink
              v-if="currentPage === 'drafts'"
              to="/listings"
              class="btn btn-secondary text-sm"
            >
              📋 Published Listings
            </NuxtLink>
          </div>
          
          <!-- User Status -->
          <div v-if="userToken" class="text-sm text-gray-600">
            ✅ Authorized
          </div>
          
          <!-- Auth Actions -->
          <button
            v-if="!userToken"
            @click="emit('authorize')"
            class="btn btn-primary"
          >
            Authorize with Marktplaats
          </button>
          <button
            v-else
            @click="emit('logout')"
            class="btn btn-secondary"
          >
            Logout
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script setup>
const props = defineProps({
  userToken: String,
  currentPage: {
    type: String,
    default: 'home',
    validator: (value) => ['home', 'drafts', 'listings'].includes(value)
  }
})

const emit = defineEmits(['authorize', 'logout'])

const pageTitle = computed(() => {
  switch (props.currentPage) {
    case 'home':
      return '🤖 Marktplaatser'
    case 'drafts':
      return '📝 My Drafts'
    case 'listings':
      return '📋 My Listings'
    default:
      return '🤖 Marktplaatser'
  }
})
</script>