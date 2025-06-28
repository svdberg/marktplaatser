<template>
  <div class="min-h-screen">
    <!-- Header -->
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center h-16">
          <div class="flex items-center">
            <h1 class="text-xl font-bold text-gray-900">
              🤖 Marktplaats AI Assistant
            </h1>
          </div>
          <div class="flex items-center space-x-4">
            <div v-if="userToken" class="text-sm text-gray-600">
              ✅ Authorized
            </div>
            <NuxtLink
              v-if="userToken"
              to="/listings"
              class="btn btn-secondary"
            >
              📋 My Listings
            </NuxtLink>
            <button
              v-if="!userToken"
              @click="authorize"
              class="btn btn-primary"
            >
              Authorize with Marktplaats
            </button>
            <button
              v-else
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
            Get Started
          </h2>
          <p class="text-gray-600 mb-6">
            To create advertisements on Marktplaats, you need to authorize this application with your Marktplaats account.
          </p>
          <button
            @click="authorize"
            class="btn btn-primary w-full"
          >
            🔑 Authorize with Marktplaats
          </button>
        </div>
      </div>

      <!-- Main Application -->
      <div v-else>
        <!-- Image Upload Section -->
        <div class="card mb-8">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">
            📸 Upload Product Image
          </h2>
          
          <div class="space-y-4">
            <!-- File Input -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Select an image of your product
              </label>
              <input
                ref="fileInput"
                type="file"
                accept="image/*"
                @change="handleFileSelect"
                class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-orange-700"
              >
            </div>

            <!-- Image Preview -->
            <div v-if="selectedImage" class="text-center">
              <img
                :src="selectedImage"
                alt="Selected product"
                class="max-w-sm mx-auto rounded-lg shadow-md"
              >
            </div>

            <!-- Generate Button -->
            <button
              v-if="selectedImage && !loading"
              @click="generateListing"
              class="btn btn-primary w-full"
            >
              🚀 Generate Listing
            </button>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-4">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p class="text-gray-600 mt-2">{{ loadingMessage }}</p>
            </div>
          </div>
        </div>

        <!-- Generated Listing -->
        <div v-if="generatedListing" class="card mb-8">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">
            📝 Generated Listing
          </h2>
          
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium text-gray-700">Title</label>
              <input
                v-model="generatedListing.title"
                type="text"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
              >
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Description</label>
              <textarea
                v-model="generatedListing.description"
                rows="3"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
              ></textarea>
            </div>

            <!-- Category Selector Component -->
            <CategorySelector
              :original-category-id="generatedListing.categoryId"
              :original-category-name="generatedListing.categoryName"
              v-model="categoryOverride"
              @category-changed="onCategoryChanged"
            />

            <!-- AI Price Estimation -->
            <div v-if="generatedListing.estimatedPrice" class="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <h3 class="text-sm font-medium text-blue-800 mb-2">🤖 AI Price Suggestion</h3>
              <div class="space-y-2">
                <div class="flex items-center justify-between">
                  <span class="text-sm text-blue-700">Estimated Price:</span>
                  <span class="text-lg font-bold text-blue-900">€{{ generatedListing.estimatedPrice }}</span>
                </div>
                <div v-if="generatedListing.priceRange" class="flex items-center justify-between">
                  <span class="text-sm text-blue-700">Price Range:</span>
                  <span class="text-sm text-blue-800">€{{ generatedListing.priceRange.min }} - €{{ generatedListing.priceRange.max }}</span>
                </div>
                <div v-if="generatedListing.priceConfidence" class="flex items-center justify-between">
                  <span class="text-sm text-blue-700">Confidence:</span>
                  <span 
                    :class="{
                      'text-green-600': generatedListing.priceConfidence === 'hoog',
                      'text-yellow-600': generatedListing.priceConfidence === 'gemiddeld', 
                      'text-red-600': generatedListing.priceConfidence === 'laag'
                    }"
                    class="text-sm font-medium"
                  >
                    {{ 
                      generatedListing.priceConfidence === 'hoog' ? '🟢 High' :
                      generatedListing.priceConfidence === 'gemiddeld' ? '🟡 Medium' :
                      '🔴 Low'
                    }}
                  </span>
                </div>
                <button
                  @click="useAIPrice"
                  class="w-full mt-2 px-3 py-1 bg-blue-600 text-white text-sm rounded hover:bg-blue-700 transition-colors"
                >
                  Use AI Suggested Price
                </button>
              </div>
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Price (€)</label>
              <input
                v-model.number="price"
                type="number"
                min="1"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
              >
            </div>

            <div>
              <label class="block text-sm font-medium text-gray-700">Postcode</label>
              <input
                v-model="postcode"
                type="text"
                placeholder="1234AB"
                class="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
              >
            </div>

            <button
              @click="createAdvertisement"
              :disabled="!price || !postcode || creating"
              class="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ creating ? '⏳ Creating...' : '🎯 Create Advertisement' }}
            </button>
          </div>
        </div>

        <!-- Success Message -->
        <div v-if="createdAd" class="card bg-green-50 border-green-200">
          <h2 class="text-xl font-semibold text-green-800 mb-4">
            ✅ Advertisement Created Successfully!
          </h2>
          <div class="space-y-2 text-green-700">
            <p><strong>Advertisement ID:</strong> {{ createdAd.advertisementId }}</p>
            <p><strong>Title:</strong> {{ createdAd.advertisement?.title }}</p>
            <a
              v-if="createdAd.imageUrl"
              :href="createdAd.imageUrl"
              target="_blank"
              class="text-primary hover:underline block"
            >
              View uploaded image
            </a>
          </div>
          <div class="mt-4 flex space-x-3">
            <NuxtLink to="/listings" class="btn btn-primary">
              📋 View All My Listings
            </NuxtLink>
            <button
              @click="createAnother"
              class="btn btn-secondary"
            >
              ➕ Create Another
            </button>
          </div>
        </div>

        <!-- Error Message -->
        <div v-if="error" class="card bg-red-50 border-red-200">
          <h2 class="text-xl font-semibold text-red-800 mb-2">
            ❌ Error
          </h2>
          <p class="text-red-700">{{ error }}</p>
          <button
            @click="error = null"
            class="btn btn-secondary mt-4"
          >
            Dismiss
          </button>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { generateUUID } from '~/utils/uuid.js'

const config = useRuntimeConfig()

// Reactive data
const userToken = ref(null)
const selectedImage = ref(null)
const selectedFile = ref(null)
const generatedListing = ref(null)
const createdAd = ref(null)
const loading = ref(false)
const creating = ref(false)
const loadingMessage = ref('')
const error = ref(null)
const price = ref(50)
const postcode = ref('1234AB')
const categoryOverride = ref(null)

// Check for stored user ID on mount
onMounted(() => {
  const userId = localStorage.getItem('marktplaats_user_id')
  if (userId) {
    userToken.value = userId
  }
})

// File input ref
const fileInput = ref()

// UUID utility is now imported from utils/uuid.js

// Methods
const authorize = () => {
  const userId = generateUUID()
  const authUrl = `${config.public.apiBaseUrl}/oauth/authorize?user_id=${userId}`
  window.location.href = authUrl
}

const logout = () => {
  localStorage.removeItem('marktplaats_user_id')
  userToken.value = null
  selectedImage.value = null
  generatedListing.value = null
  createdAd.value = null
  error.value = null
  categoryOverride.value = null
}

const handleFileSelect = (event) => {
  const file = event.target.files[0]
  if (file) {
    selectedFile.value = file
    const reader = new FileReader()
    reader.onload = (e) => {
      selectedImage.value = e.target.result
    }
    reader.readAsDataURL(file)
    
    // Clear previous results
    generatedListing.value = null
    createdAd.value = null
    error.value = null
    categoryOverride.value = null
  }
}

const generateListing = async () => {
  if (!selectedFile.value) return
  
  loading.value = true
  loadingMessage.value = 'Analyzing image with AI...'
  error.value = null
  
  try {
    // Convert file to base64
    const base64 = await fileToBase64(selectedFile.value)
    
    // Call generate listing API
    console.log('Calling API:', `${config.public.apiBaseUrl}/generate-listing`)
    
    const response = await fetch(`${config.public.apiBaseUrl}/generate-listing`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        image: base64.split(',')[1] // Remove data:image/jpeg;base64, prefix
      })
    })
    
    console.log('API response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('API error response:', errorText)
      throw new Error(`API returned ${response.status}: ${errorText}`)
    }
    
    const data = await response.json()
    console.log('API response data:', data)
    
    if (data.error) {
      throw new Error(data.error)
    }
    
    generatedListing.value = data
    
    // Auto-fill the estimated price if available
    if (data.estimatedPrice) {
      price.value = data.estimatedPrice
    }
    
  } catch (err) {
    error.value = `Failed to generate listing: ${err.message}`
  } finally {
    loading.value = false
    loadingMessage.value = ''
  }
}

const createAdvertisement = async () => {
  if (!generatedListing.value || !price.value || !postcode.value) return
  
  creating.value = true
  error.value = null
  
  try {
    const base64 = await fileToBase64(selectedFile.value)
    
    const response = await fetch(`${config.public.apiBaseUrl}/create-advertisement`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        listingData: {
          title: generatedListing.value.title,
          description: generatedListing.value.description,
          categoryId: generatedListing.value.categoryId,
          attributes: generatedListing.value.attributes
        },
        image: base64.split(',')[1],
        userDetails: {
          postcode: postcode.value,
          priceModel: {
            modelType: 'fixed',
            askingPrice: price.value
          }
        },
        userId: userToken.value,
        categoryOverride: categoryOverride.value
      })
    })
    
    const data = await response.json()
    
    if (data.error) {
      throw new Error(data.error)
    }
    
    createdAd.value = data
    
  } catch (err) {
    error.value = `Failed to create advertisement: ${err.message}`
  } finally {
    creating.value = false
  }
}

const onCategoryChanged = (newCategoryId) => {
  console.log('Category changed to:', newCategoryId)
  // Category override is automatically updated via v-model
}

const useAIPrice = () => {
  if (generatedListing.value?.estimatedPrice) {
    price.value = generatedListing.value.estimatedPrice
  }
}

const createAnother = () => {
  // Reset form to create another listing
  selectedImage.value = null
  selectedFile.value = null
  generatedListing.value = null
  createdAd.value = null
  error.value = null
  categoryOverride.value = null
  price.value = 50
  postcode.value = '1234AB'
  
  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// Utility function
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result)
    reader.onerror = error => reject(error)
  })
}
</script>