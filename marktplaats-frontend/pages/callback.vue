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
  console.log('Callback page mounted')
  console.log('Current URL:', window.location.href)
  console.log('Route query:', route.query)
  
  // Try to get user ID from URL parameters (Nuxt route)
  let userIdParam = route.query.user_id
  
  // If not found in route.query, check URL hash (fragments survive redirects)
  if (!userIdParam) {
    console.log('User ID not found in route.query, checking window.location hash')
    const hash = window.location.hash.substring(1) // Remove the #
    const hashParams = new URLSearchParams(hash)
    userIdParam = hashParams.get('user_id')
    console.log('User ID from hash:', userIdParam)
  }
  
  // Fallback: check query parameters
  if (!userIdParam) {
    console.log('User ID not found in hash, checking window.location search')
    const urlParams = new URLSearchParams(window.location.search)
    userIdParam = urlParams.get('user_id')
    console.log('User ID from URLSearchParams:', userIdParam)
  }
  
  // Also check if user_id is in localStorage from previous redirect
  if (!userIdParam) {
    console.log('Checking localStorage for user_id')
    userIdParam = localStorage.getItem('marktplaats_user_id')
    console.log('User ID from localStorage:', userIdParam)
  }
  
  console.log('Final User ID param:', userIdParam)
  
  if (userIdParam) {
    console.log('User ID found, processing success path')
    // Store user ID in localStorage
    localStorage.setItem('marktplaats_user_id', userIdParam)
    userId.value = userIdParam
    status.value = 'success'
    message.value = 'Authorization Successful!'
    
    // Redirect to main app after 2 seconds
    setTimeout(() => {
      console.log('Redirecting to main page')
      // Use absolute URL to avoid relative path issues
      window.location.href = 'http://marktplaats-frontend-simple-prod-website.s3-website.eu-west-1.amazonaws.com/'
    }, 2000)
  } else {
    console.log('No user ID found, showing error')
    status.value = 'error'
    message.value = 'Authorization failed - no user ID received'
  }
})
</script>