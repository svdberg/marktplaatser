<template>
  <div class="min-h-screen bg-gray-50 flex items-center justify-center">
    <div class="card max-w-md text-center">
      <h1 class="text-2xl font-bold text-gray-900 mb-4">
        {{ status === 'success' ? '✅' : '⏳' }} {{ message }}
      </h1>
      <p v-if="userId" class="text-sm text-gray-600 mb-4">
        User ID: <code>{{ userId }}</code>
      </p>
      <p class="text-gray-600">
        {{ status === 'success' ? 'Redirecting to main app...' : 'Processing authorization...' }}
      </p>
    </div>
  </div>
</template>

<script setup>
const route = useRoute()
const router = useRouter()

const status = ref('processing')
const message = ref('Processing authorization...')
const userId = ref(null)

onMounted(() => {
  // Get user ID from URL parameters (passed from AWS callback)
  const userIdParam = route.query.user_id
  
  if (userIdParam) {
    // Store user ID in localStorage
    localStorage.setItem('marktplaats_user_id', userIdParam)
    userId.value = userIdParam
    status.value = 'success'
    message.value = 'Authorization Successful!'
    
    // Redirect to main app after 2 seconds
    setTimeout(() => {
      router.push('/')
    }, 2000)
  } else {
    status.value = 'error'
    message.value = 'Authorization failed - no user ID received'
  }
})
</script>