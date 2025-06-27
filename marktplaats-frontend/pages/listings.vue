<template>
  <div class="min-h-screen">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center space-x-4">
            <NuxtLink to="/" class="text-primary hover:text-orange-700">
              ← Back to Home
            </NuxtLink>
            <h1 class="text-xl font-bold text-gray-900">
              📋 My Listings
            </h1>
          </div>
          <div class="flex items-center space-x-4">
            <div v-if="userToken" class="text-sm text-gray-600">
              ✅ Authorized
            </div>
            <button
              v-if="userToken"
              @click="logout"
              class="btn btn-secondary"
            >
              Logout
            </button>
          </div>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Authorization Required -->
      <div v-if="!userToken" class="text-center py-12">
        <div class="card max-w-md mx-auto">
          <h2 class="text-2xl font-bold text-gray-900 mb-4">
            Authorization Required
          </h2>
          <p class="text-gray-600 mb-6">
            Please authorize with Marktplaats to view your listings.
          </p>
          <NuxtLink to="/" class="btn btn-primary w-full">
            🔑 Go to Authorization
          </NuxtLink>
        </div>
      </div>

      <!-- Loading State -->
      <div v-else-if="loading" class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p class="text-gray-600 mt-4">Loading your listings...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="card bg-red-50 border-red-200">
        <h2 class="text-xl font-semibold text-red-800 mb-2">
          ❌ Error Loading Listings
        </h2>
        <p class="text-red-700 mb-4">{{ error }}</p>
        <button
          @click="loadListings"
          class="btn btn-primary"
        >
          🔄 Retry
        </button>
      </div>

      <!-- Empty State -->
      <div v-else-if="listings && listings.length === 0" class="text-center py-12">
        <div class="card max-w-md mx-auto">
          <h2 class="text-2xl font-bold text-gray-900 mb-4">
            No Listings Found
          </h2>
          <p class="text-gray-600 mb-6">
            You haven't created any advertisements yet.
          </p>
          <NuxtLink to="/" class="btn btn-primary w-full">
            📸 Create Your First Listing
          </NuxtLink>
        </div>
      </div>

      <!-- Listings Grid -->
      <div v-else-if="listings" class="space-y-6">
        <div class="flex justify-between items-center">
          <h2 class="text-2xl font-bold text-gray-900">
            Your Advertisements ({{ listings.length }})
          </h2>
          <NuxtLink to="/" class="btn btn-primary">
            ➕ Create New Listing
          </NuxtLink>
        </div>

        <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="listing in listings"
            :key="listing.id"
            class="card hover:shadow-lg transition-shadow"
          >
            <!-- Listing Image -->
            <div v-if="listing.images && listing.images.length > 0" class="mb-4">
              <img
                :src="listing.images[0].url"
                :alt="listing.title"
                class="w-full h-48 object-cover rounded-lg"
              >
            </div>
            <div v-else class="mb-4 h-48 bg-gray-100 rounded-lg flex items-center justify-center">
              <span class="text-gray-400">📷 No Image</span>
            </div>

            <!-- Listing Details -->
            <div class="space-y-2">
              <h3 class="font-semibold text-lg text-gray-900 line-clamp-2">
                {{ listing.title }}
              </h3>
              
              <p class="text-gray-600 text-sm line-clamp-3">
                {{ listing.description }}
              </p>
              
              <div class="flex justify-between items-center">
                <span class="text-lg font-bold text-primary">
                  €{{ formatPrice(listing.priceModel?.askingPrice) }}
                </span>
                <span class="text-sm text-gray-500">
                  {{ listing.category?.name }}
                </span>
              </div>
              
              <div class="text-xs text-gray-400">
                ID: {{ listing.itemId || listing.id }}
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="mt-4 flex space-x-2">
              <button
                @click="editListing(listing)"
                class="btn btn-secondary flex-1"
              >
                ✏️ Edit
              </button>
              <button
                @click="deleteListing(listing)"
                class="btn btn-danger flex-1"
                :disabled="deletingIds.includes(listing.itemId || listing.id)"
              >
                {{ deletingIds.includes(listing.itemId || listing.id) ? '⏳' : '🗑️' }} Delete
              </button>
            </div>
          </div>
        </div>
      </div>
    </main>

    <!-- Edit Modal -->
    <EditListingModal
      v-if="editingListing"
      :listing="editingListing"
      @close="editingListing = null"
      @saved="onListingSaved"
    />

    <!-- Delete Confirmation Modal -->
    <div
      v-if="deletingListing"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    >
      <div class="bg-white rounded-lg p-6 max-w-md w-full mx-4">
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          Confirm Delete
        </h3>
        <p class="text-gray-600 mb-6">
          Are you sure you want to delete "{{ deletingListing.title }}"? This action cannot be undone.
        </p>
        <div class="flex space-x-3">
          <button
            @click="deletingListing = null"
            class="btn btn-secondary flex-1"
          >
            Cancel
          </button>
          <button
            @click="confirmDelete"
            class="btn btn-danger flex-1"
            :disabled="confirming"
          >
            {{ confirming ? '⏳ Deleting...' : 'Delete' }}
          </button>
        </div>
      </div>
    </div>

    <!-- Success Toast -->
    <div
      v-if="successMessage"
      class="fixed bottom-4 right-4 bg-green-500 text-white px-6 py-3 rounded-lg shadow-lg z-50"
    >
      {{ successMessage }}
    </div>
  </div>
</template>

<script setup>
const config = useRuntimeConfig()

// Reactive data
const userToken = ref(null)
const listings = ref(null)
const loading = ref(false)
const error = ref(null)
const editingListing = ref(null)
const deletingListing = ref(null)
const deletingIds = ref([])
const confirming = ref(false)
const successMessage = ref(null)

// Check for stored user ID on mount
onMounted(() => {
  const userId = localStorage.getItem('marktplaats_user_id')
  if (userId) {
    userToken.value = userId
    loadListings()
  }
})

// Methods
const loadListings = async () => {
  if (!userToken.value) return
  
  loading.value = true
  error.value = null
  
  try {
    console.log('Loading listings for user:', userToken.value)
    
    const response = await fetch(`${config.public.apiBaseUrl}/list-advertisements?user_id=${userToken.value}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    console.log('List advertisements response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('List advertisements error:', errorText)
      throw new Error(`Failed to load listings: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('List advertisements response:', data)
    
    if (data.error) {
      throw new Error(data.error)
    }
    
    // Extract the advertisements array from the response
    // Marktplaats API returns HAL format: _embedded["mp:advertisements"]
    if (data._embedded && data._embedded["mp:advertisements"]) {
      listings.value = data._embedded["mp:advertisements"]
    } else {
      listings.value = data.advertisements || data.items || []
    }
    
    // Load images for each listing
    await loadImagesForListings()
    
  } catch (err) {
    console.error('Load listings error:', err)
    error.value = err.message
  } finally {
    loading.value = false
  }
}

const editListing = (listing) => {
  editingListing.value = listing
}

const deleteListing = (listing) => {
  deletingListing.value = listing
}

const confirmDelete = async () => {
  if (!deletingListing.value) return
  
  confirming.value = true
  const listingId = deletingListing.value.itemId || deletingListing.value.id
  deletingIds.value.push(listingId)
  
  try {
    console.log('Deleting listing:', listingId)
    
    const response = await fetch(`${config.public.apiBaseUrl}/manage-advertisement/${listingId}?user_id=${userToken.value}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    console.log('Delete response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('Delete error:', errorText)
      throw new Error(`Failed to delete listing: ${response.status}`)
    }
    
    // Remove from local listings array
    listings.value = listings.value.filter(l => (l.itemId || l.id) !== listingId)
    
    successMessage.value = 'Listing deleted successfully!'
    setTimeout(() => {
      successMessage.value = null
    }, 3000)
    
  } catch (err) {
    console.error('Delete listing error:', err)
    error.value = err.message
  } finally {
    confirming.value = false
    deletingListing.value = null
    deletingIds.value = deletingIds.value.filter(id => id !== listingId)
  }
}

const onListingSaved = (updatedListing) => {
  // Update the listing in the local array
  const index = listings.value.findIndex(l => (l.itemId || l.id) === (updatedListing.itemId || updatedListing.id))
  if (index !== -1) {
    listings.value[index] = updatedListing
  }
  
  successMessage.value = 'Listing updated successfully!'
  setTimeout(() => {
    successMessage.value = null
  }, 3000)
  
  editingListing.value = null
}

const logout = () => {
  localStorage.removeItem('marktplaats_user_id')
  userToken.value = null
  listings.value = null
  error.value = null
  navigateTo('/')
}

const loadImagesForListings = async () => {
  if (!listings.value || listings.value.length === 0) return
  
  // Load images for each listing in parallel
  const imagePromises = listings.value.map(async (listing) => {
    try {
      const listingId = listing.itemId || listing.id
      if (!listingId) return
      
      console.log('Loading images for listing:', listingId)
      
      const response = await fetch(`${config.public.apiBaseUrl}/advertisement-images/${listingId}?user_id=${userToken.value}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json'
        }
      })
      
      if (!response.ok) {
        console.warn(`Failed to load images for listing ${listingId}:`, response.status)
        return
      }
      
      const imageData = await response.json()
      console.log(`Images for listing ${listingId}:`, imageData)
      
      // Add images to the listing object
      // Marktplaats API returns HAL format: _embedded["mp:advertisement-image"]
      if (imageData._embedded && imageData._embedded["mp:advertisement-image"]) {
        // Transform the API response to a simpler format for the frontend
        listing.images = imageData._embedded["mp:advertisement-image"].map(img => ({
          url: img.medium?.href || img.small?.href || img.large?.href, // Prefer medium, fallback to small or large
          mediaId: img.mediaId,
          status: img.status,
          small: img.small?.href,
          medium: img.medium?.href,
          large: img.large?.href,
          xlarge: img.xlarge?.href
        }))
      } else if (imageData.images && imageData.images.length > 0) {
        // Fallback for other response formats
        listing.images = imageData.images
      }
      
    } catch (err) {
      console.warn(`Error loading images for listing ${listing.itemId || listing.id}:`, err)
    }
  })
  
  // Wait for all image loading to complete
  await Promise.all(imagePromises)
}

const formatPrice = (priceInCents) => {
  if (!priceInCents) return '0'
  return (priceInCents / 100).toFixed(2)
}

// Auto-clear success message
watch(successMessage, (newVal) => {
  if (newVal) {
    setTimeout(() => {
      successMessage.value = null
    }, 3000)
  }
})
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>