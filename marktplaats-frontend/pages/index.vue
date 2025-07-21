<template>
  <div class="min-h-screen">
    <!-- Header -->
    <Header 
      :user-token="userToken" 
      current-page="home"
      @authorize="authorize"
      @logout="logout"
    />

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
            📸 Upload Product Images
          </h2>
          
          <div class="space-y-4">
            <!-- File Input -->
            <div>
              <label class="block text-sm font-medium text-gray-700 mb-2">
                Select up to 3 images of your product (more images = better results)
              </label>
              <input
                ref="fileInput"
                type="file"
                accept="image/*"
                multiple
                @change="handleFileSelect"
                class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-orange-700"
              >
              <p class="text-xs text-gray-500 mt-1">
                💡 Tip: Upload different angles for better AI analysis (max 3 images)
              </p>
            </div>

            <!-- Image Previews -->
            <div v-if="selectedImages.length > 0" class="space-y-3">
              <div class="text-sm font-medium text-gray-700">
                Selected Images ({{ selectedImages.length }}/3):
              </div>
              <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                <div 
                  v-for="(image, index) in selectedImages" 
                  :key="index"
                  class="relative group"
                >
                  <img
                    :src="image.preview"
                    :alt="`Product image ${index + 1}`"
                    class="w-full h-48 object-cover rounded-lg shadow-md"
                  >
                  <div class="absolute top-2 left-2 bg-black bg-opacity-70 text-white text-xs px-2 py-1 rounded">
                    {{ index + 1 }}
                  </div>
                  <button
                    @click="removeImage(index)"
                    class="absolute top-2 right-2 bg-red-500 text-white rounded-full w-6 h-6 flex items-center justify-center text-xs font-bold opacity-70 group-hover:opacity-100 transition-opacity"
                    title="Remove image"
                  >
                    ×
                  </button>
                  <div class="absolute bottom-2 left-2 right-2 bg-black bg-opacity-70 text-white text-xs p-1 rounded text-center">
                    {{ (image.file.size / 1024 / 1024).toFixed(1) }}MB
                  </div>
                </div>
              </div>
            </div>

            <!-- Generate Button -->
            <button
              v-if="selectedImages.length > 0 && !loading"
              @click="generateListing"
              class="btn btn-primary w-full"
            >
              🚀 Generate Listing{{ selectedImages.length > 1 ? ` from ${selectedImages.length} Images` : '' }}
            </button>

            <!-- Loading State -->
            <div v-if="loading" class="text-center py-4">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p class="text-gray-600 mt-2">{{ loadingMessage }}</p>
            </div>
          </div>
        </div>

        <!-- Draft Created Successfully -->
        <div v-if="generatedListing" class="card mb-8">
          <div class="flex items-center justify-between mb-4">
            <h2 class="text-xl font-semibold text-gray-900">
              📝 Draft Created Successfully!
            </h2>
            <NuxtLink 
              to="/drafts" 
              class="btn btn-primary text-sm"
            >
              📋 View All Drafts
            </NuxtLink>
          </div>
          
          <!-- Success Message -->
          <div class="bg-green-50 border border-green-200 rounded-lg p-4 mb-6">
            <div class="flex items-center">
              <div class="flex-shrink-0">
                <span class="text-green-600 text-lg">✅</span>
              </div>
              <div class="ml-3">
                <h3 class="text-sm font-medium text-green-800">
                  {{ generatedListing.message || 'Your draft listing has been created!' }}
                </h3>
                <p class="text-sm text-green-700 mt-1">
                  You can now review, edit, and publish your listing when ready.
                </p>
              </div>
            </div>
          </div>
          
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

            <!-- Pricing Model Selector -->
            <div>
              <PriceModelSelector
                v-model="priceModel"
                :suggested-model="generatedListing.suggestedPricingModel"
                :errors="{}"
              />
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

            <!-- Dual Action Buttons -->
            <div class="space-y-3">
              <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <h3 class="text-sm font-medium text-blue-800 mb-2">Choose your action:</h3>
                <div class="space-y-2">
                  <button
                    @click="publishNow"
                    :disabled="!priceModel?.askingPrice || !postcode || publishing"
                    class="btn btn-primary w-full disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {{ publishing ? '⏳ Publishing...' : '🚀 Publish to Marktplaats Now' }}
                  </button>
                  <button
                    @click="saveDraft"
                    :disabled="saving"
                    class="btn btn-secondary w-full"
                  >
                    {{ saving ? '⏳ Saving...' : '📝 Save as Draft for Later' }}
                  </button>
                </div>
              </div>
              
              <!-- Navigation Options -->
              <div class="flex space-x-3 pt-2 border-t">
                <NuxtLink 
                  to="/drafts" 
                  class="btn btn-outline flex-1 text-sm"
                >
                  📋 View All Drafts
                </NuxtLink>
                <button
                  @click="createAnotherDraft"
                  class="btn btn-outline flex-1 text-sm"
                >
                  ➕ Create Another
                </button>
              </div>
            </div>
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
import PriceModelSelector from '~/components/PriceModelSelector.vue'

const config = useRuntimeConfig()

// Reactive data
const userToken = ref(null)
const selectedImage = ref(null) // Keep for backward compatibility
const selectedFile = ref(null) // Keep for backward compatibility
const selectedImages = ref([]) // New: array of selected images
const generatedListing = ref(null)
const createdAd = ref(null)
const loading = ref(false)
const loadingMessage = ref('')
const error = ref(null)
const price = ref(50)
const priceModel = ref({ modelType: 'fixed', askingPrice: 50 })
const postcode = ref('1234AB')
const categoryOverride = ref(null)
const publishing = ref(false)
const saving = ref(false)

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
  selectedImages.value = []
  generatedListing.value = null
  createdAd.value = null
  error.value = null
  categoryOverride.value = null
}

const handleFileSelect = (event) => {
  const files = Array.from(event.target.files)
  
  if (files.length === 0) return
  
  // Validate file count
  if (files.length > 3) {
    error.value = 'Maximum 3 images allowed. Please select up to 3 images.'
    return
  }
  
  // Clear previous results
  generatedListing.value = null
  createdAd.value = null
  error.value = null
  categoryOverride.value = null
  
  // Process each file
  const newImages = []
  let processedCount = 0
  
  files.forEach((file, index) => {
    // Validate file size (max 10MB per image)
    if (file.size > 10 * 1024 * 1024) {
      error.value = `Image ${index + 1} is too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Please select images under 10MB.`
      return
    }
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      error.value = `File ${index + 1} is not a valid image file.`
      return
    }
    
    const reader = new FileReader()
    reader.onload = (e) => {
      newImages.push({
        file: file,
        preview: e.target.result,
        name: file.name
      })
      
      processedCount++
      
      // When all files are processed, update the reactive array
      if (processedCount === files.length) {
        selectedImages.value = newImages
        
        // Set backward compatibility values (use first image)
        if (newImages.length > 0) {
          selectedFile.value = newImages[0].file
          selectedImage.value = newImages[0].preview
        }
      }
    }
    reader.onerror = () => {
      error.value = `Failed to read image ${index + 1}`
    }
    reader.readAsDataURL(file)
  })
}

const removeImage = (index) => {
  selectedImages.value.splice(index, 1)
  
  // Update backward compatibility values
  if (selectedImages.value.length > 0) {
    selectedFile.value = selectedImages.value[0].file
    selectedImage.value = selectedImages.value[0].preview
  } else {
    selectedFile.value = null
    selectedImage.value = null
  }
  
  // Clear error if it was about too many images
  if (error.value && error.value.includes('Maximum 3 images')) {
    error.value = null
  }
}

const generateListing = async () => {
  if (selectedImages.value.length === 0) return
  
  // Check if user is authenticated
  if (!userToken.value) {
    error.value = 'Please authorize with Marktplaats first'
    return
  }
  
  loading.value = true
  loadingMessage.value = `Compressing and analyzing ${selectedImages.value.length} image${selectedImages.value.length > 1 ? 's' : ''}...`
  error.value = null
  
  try {
    // Compress all images
    loadingMessage.value = `Compressing ${selectedImages.value.length} image${selectedImages.value.length > 1 ? 's' : ''} for optimization...`
    
    const compressedImages = []
    let totalOriginalSize = 0
    let totalCompressedSize = 0
    
    for (let i = 0; i < selectedImages.value.length; i++) {
      const imageObj = selectedImages.value[i]
      const base64 = await resizeAndCompressImage(imageObj.file, 1024, 1024, 0.8)
      compressedImages.push(base64.split(',')[1]) // Remove data:image/jpeg;base64, prefix
      
      totalOriginalSize += imageObj.file.size
      totalCompressedSize += Math.round((base64.length * 3) / 4)
    }
    
    // Log compression results for debugging
    console.log(`Multi-image compression: ${(totalOriginalSize / 1024 / 1024).toFixed(2)}MB → ${(totalCompressedSize / 1024 / 1024).toFixed(2)}MB (${selectedImages.value.length} images)`)
    
    loadingMessage.value = `Analyzing ${selectedImages.value.length} image${selectedImages.value.length > 1 ? 's' : ''} with AI...`
    
    // Call generate listing API with user_id and postcode
    console.log('Calling API:', `${config.public.apiBaseUrl}/generate-listing`)
    
    // Prepare API payload - use new multi-image format if multiple images, else single image for compatibility
    const apiPayload = {
      user_id: userToken.value,
      postcode: postcode.value || '1000AA'
    }
    
    if (selectedImages.value.length === 1) {
      // Single image - use backward compatible format
      apiPayload.image = compressedImages[0]
    } else {
      // Multiple images - use new format
      apiPayload.images = compressedImages
    }
    
    loadingMessage.value = 'Creating draft listing...'
    
    const response = await fetch(`${config.public.apiBaseUrl}/generate-listing`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(apiPayload)
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
    
    // Update UI to show draft creation success
    generatedListing.value = data
    
    // Auto-fill the price model from AI generation
    if (data.priceModel) {
      priceModel.value = { ...data.priceModel }
      // Also update the legacy price field for backward compatibility
      price.value = data.priceModel.askingPrice || data.estimatedPrice || 50
    } else if (data.estimatedPrice) {
      // Fallback to estimated price if no price model
      price.value = data.estimatedPrice
      priceModel.value = { modelType: 'fixed', askingPrice: data.estimatedPrice }
    }
    
    loadingMessage.value = 'Draft created successfully!'
    
  } catch (err) {
    error.value = `Failed to generate listing: ${err.message}`
  } finally {
    loading.value = false
    setTimeout(() => {
      loadingMessage.value = ''
    }, 2000) // Keep success message visible for 2 seconds
  }
}

const createAnotherDraft = () => {
  // Reset form to create another draft
  selectedImage.value = null
  selectedFile.value = null
  selectedImages.value = []
  generatedListing.value = null
  createdAd.value = null
  error.value = null
  categoryOverride.value = null
  priceModel.value = { modelType: 'fixed', askingPrice: 50 }
  
  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

const publishNow = async () => {
  if (!generatedListing.value || !priceModel.value?.askingPrice || !postcode.value) return
  
  publishing.value = true
  error.value = null
  
  try {
    // Use the same compressed images for advertisement creation
    // For now, use the first image for backward compatibility with publish endpoint
    const primaryImageFile = selectedImages.value.length > 0 ? selectedImages.value[0].file : selectedFile.value
    const base64 = await resizeAndCompressImage(primaryImageFile, 1024, 1024, 0.8)
    
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
          priceModel: priceModel.value // Use the complete price model from selector
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
    generatedListing.value = null // Hide the draft options after successful publish
    
  } catch (err) {
    error.value = `Failed to publish advertisement: ${err.message}`
  } finally {
    publishing.value = false
  }
}

const saveDraft = async () => {
  if (!generatedListing.value) return
  
  saving.value = true
  error.value = null
  
  try {
    // The draft is already saved by the AI generation process
    // This function can be used for additional draft updates if needed
    
    // Show success message and navigate to drafts
    await navigateTo('/drafts')
    
  } catch (err) {
    error.value = `Failed to save draft: ${err.message}`
  } finally {
    saving.value = false
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
  selectedImages.value = []
  generatedListing.value = null
  createdAd.value = null
  error.value = null
  categoryOverride.value = null
  price.value = 50
  priceModel.value = { modelType: 'fixed', askingPrice: 50 }
  postcode.value = '1234AB'
  
  // Reset file input
  if (fileInput.value) {
    fileInput.value.value = ''
  }
}

// Utility function to resize and compress image
const resizeAndCompressImage = (file, maxWidth = 1024, maxHeight = 1024, quality = 0.8) => {
  return new Promise((resolve, reject) => {
    const canvas = document.createElement('canvas')
    const ctx = canvas.getContext('2d')
    const img = new Image()
    
    img.onload = () => {
      // Calculate new dimensions while maintaining aspect ratio
      let { width, height } = img
      
      if (width > height) {
        if (width > maxWidth) {
          height = (height * maxWidth) / width
          width = maxWidth
        }
      } else {
        if (height > maxHeight) {
          width = (width * maxHeight) / height
          height = maxHeight
        }
      }
      
      // Set canvas dimensions
      canvas.width = width
      canvas.height = height
      
      // Draw and compress image
      ctx.drawImage(img, 0, 0, width, height)
      
      // Convert to base64 with compression
      const base64 = canvas.toDataURL('image/jpeg', quality)
      resolve(base64)
    }
    
    img.onerror = reject
    
    // Load the image
    const reader = new FileReader()
    reader.onload = (e) => {
      img.src = e.target.result
    }
    reader.onerror = reject
    reader.readAsDataURL(file)
  })
}

// Legacy utility function (kept for backward compatibility)
// const fileToBase64 = (file) => {
//   return new Promise((resolve, reject) => {
//     const reader = new FileReader()
//     reader.readAsDataURL(file)
//     reader.onload = () => resolve(reader.result)
//     reader.onerror = error => reject(error)
//   })
// }
</script>