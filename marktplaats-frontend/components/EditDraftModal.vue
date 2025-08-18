<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-gray-900">
          ✏️ Edit Draft
        </h2>
        <button
          @click="$emit('close')"
          class="text-gray-400 hover:text-gray-600"
        >
          ✕
        </button>
      </div>

      <!-- Loading State -->
      <div v-if="loadingDetails" class="text-center py-8">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
        <p class="text-gray-600 mt-2">Loading draft details...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <p class="text-red-700">{{ loadError }}</p>
        <button
          @click="loadDraftDetails"
          class="btn btn-primary mt-2"
        >
          🔄 Retry
        </button>
      </div>

      <!-- Edit Form -->
      <form v-else @submit.prevent="saveDraft" class="space-y-6">
        <!-- General Error Message -->
        <div v-if="errors.general" class="bg-red-50 border border-red-200 rounded-lg p-4">
          <p class="text-red-700">{{ errors.general }}</p>
        </div>
        
        <!-- Title -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Title *
          </label>
          <input
            v-model="form.title"
            type="text"
            maxlength="60"
            required
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
            :class="{ 'border-red-300': errors.title }"
          >
          <p v-if="errors.title" class="text-red-600 text-sm mt-1">{{ errors.title }}</p>
          <p class="text-gray-500 text-sm mt-1">{{ form.title?.length || 0 }}/60 characters</p>
        </div>

        <!-- Description -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Description *
          </label>
          <textarea
            v-model="form.description"
            rows="4"
            required
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
            :class="{ 'border-red-300': errors.description }"
          ></textarea>
          <p v-if="errors.description" class="text-red-600 text-sm mt-1">{{ errors.description }}</p>
        </div>

        <!-- Pricing Model -->
        <div>
          <PriceModelSelector
            v-model="form.priceModel"
            :suggested-model="form.suggestedPricingModel"
            :errors="errors"
          />
        </div>

        <!-- Postcode -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Postcode *
          </label>
          <input
            v-model="form.postcode"
            type="text"
            maxlength="7"
            required
            placeholder="1000AA"
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
            :class="{ 'border-red-300': errors.postcode }"
          >
          <p v-if="errors.postcode" class="text-red-600 text-sm mt-1">{{ errors.postcode }}</p>
          <p class="text-gray-500 text-sm mt-1">Dutch postcode (e.g., 1000AA)</p>
        </div>

        <!-- Category (Editable) -->
        <div>
          <CategorySelector
            :original-category-id="form.originalCategoryId"
            :original-category-name="form.originalCategoryName"
            v-model="form.selectedCategoryId"
            @category-changed="onCategoryChanged"
          />
        </div>

        <!-- Image Management -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Product Images
          </label>
          
          <!-- Current Images -->
          <div v-if="form.images && form.images.length > 0" class="mb-4">
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3 mb-3">
              <div
                v-for="(image, index) in form.images"
                :key="index"
                class="relative group"
              >
                <img
                  :src="image"
                  :alt="`Draft image ${index + 1}`"
                  class="w-full h-24 object-cover rounded-lg border"
                >
                <div class="absolute top-1 left-1 bg-black bg-opacity-70 text-white text-xs px-1.5 py-0.5 rounded">
                  {{ index + 1 }}
                </div>
                <button
                  @click="removeExistingImage(index)"
                  class="absolute top-1 right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold opacity-70 group-hover:opacity-100 transition-opacity"
                  title="Remove image"
                >
                  ×
                </button>
              </div>
            </div>
          </div>
          
          <!-- Add New Images -->
          <div v-if="(!form.images || form.images.length < 3)" class="mb-3">
            <input
              ref="imageInput"
              type="file"
              accept="image/*"
              multiple
              @change="handleNewImages"
              class="block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-primary file:text-white hover:file:bg-orange-700"
            >
            <p class="text-xs text-gray-500 mt-1">
              💡 Add {{ 3 - (form.images?.length || 0) }} more image{{ (3 - (form.images?.length || 0)) !== 1 ? 's' : '' }} (max 3 total)
            </p>
          </div>
          
          <!-- New Images Preview -->
          <div v-if="newImages.length > 0" class="mb-3">
            <p class="text-sm font-medium text-gray-700 mb-2">New Images to Add:</p>
            <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
              <div
                v-for="(imageObj, index) in newImages"
                :key="index"
                class="relative group"
              >
                <img
                  :src="imageObj.preview"
                  :alt="`New image ${index + 1}`"
                  class="w-full h-24 object-cover rounded-lg border border-blue-300"
                >
                <div class="absolute top-1 left-1 bg-blue-500 text-white text-xs px-1.5 py-0.5 rounded">
                  NEW
                </div>
                <button
                  @click="removeNewImage(index)"
                  class="absolute top-1 right-1 bg-red-500 text-white rounded-full w-5 h-5 flex items-center justify-center text-xs font-bold opacity-70 group-hover:opacity-100 transition-opacity"
                  title="Remove new image"
                >
                  ×
                </button>
                <div class="absolute bottom-1 left-1 right-1 bg-black bg-opacity-70 text-white text-xs p-1 rounded text-center">
                  {{ (imageObj.file.size / 1024 / 1024).toFixed(1) }}MB
                </div>
              </div>
            </div>
          </div>
          
          <p class="text-gray-500 text-sm">
            {{ (form.images?.length || 0) + newImages.length }}/3 images selected
          </p>
        </div>

        <!-- Attributes (if any) -->
        <div v-if="form.attributes && form.attributes.length > 0">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Attributes
          </label>
          <div class="space-y-2">
            <div
              v-for="(attr, index) in form.attributes"
              :key="index"
              class="flex items-center space-x-2"
            >
              <span class="text-sm text-gray-600 min-w-0 flex-1">{{ attr.key }}:</span>
              <span class="text-sm font-medium">{{ attr.value }}</span>
            </div>
          </div>
          <p class="text-gray-500 text-sm mt-1">Attributes are automatically set and cannot be modified</p>
        </div>

        <!-- Action Buttons -->
        <div class="flex space-x-3 pt-4 border-t">
          <button
            type="button"
            @click="$emit('close')"
            class="btn btn-secondary flex-1"
            :disabled="saving"
          >
            Cancel
          </button>
          <button
            type="submit"
            class="btn btn-primary flex-1"
            :disabled="saving || !isFormValid"
          >
            {{ saving ? '⏳ Saving...' : '💾 Save Draft' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import CategorySelector from '~/components/CategorySelector.vue'
import PriceModelSelector from '~/components/PriceModelSelector.vue'

const props = defineProps({
  draft: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['close', 'saved'])

const config = useRuntimeConfig()

// Reactive data
const form = ref({
  title: '',
  description: '',
  priceModel: { modelType: 'fixed', askingPrice: 0 },
  suggestedPricingModel: 'fixed',
  postcode: '',
  originalCategoryId: null,
  originalCategoryName: '',
  selectedCategoryId: null,
  categoryId: null,
  categoryName: '',
  images: [],
  attributes: []
})

const loadingDetails = ref(false)
const loadError = ref(null)
const saving = ref(false)
const errors = ref({})
const newImages = ref([])
const imageInput = ref()

// Initialize form data
onMounted(() => {
  loadDraftDetails()
})

// Computed
const isFormValid = computed(() => {
  // Basic validation
  const basicValid = form.value.title && 
         form.value.title.length <= 60 &&
         form.value.description && 
         form.value.priceModel?.askingPrice > 0 &&
         form.value.postcode &&
         Object.keys(errors.value).filter(key => key !== 'general').length === 0
  
  // Additional validation for bidding model
  if (form.value.priceModel?.modelType === 'bidding') {
    return basicValid && 
           form.value.priceModel.minimalBid > 0 &&
           form.value.priceModel.minimalBid < form.value.priceModel.askingPrice
  }
  
  return basicValid
})

// Methods
const loadDraftDetails = async () => {
  loadingDetails.value = true
  loadError.value = null
  
  try {
    const userToken = localStorage.getItem('marktplaats_user_id')
    if (!userToken) {
      throw new Error('User not authenticated')
    }
    
    const draftId = props.draft.draftId
    console.log('Loading details for draft:', draftId)
    
    const response = await fetch(`${config.public.apiBaseUrl}/drafts/${draftId}?user_id=${userToken}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    console.log('Get draft details response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('Get draft details error:', errorText)
      throw new Error(`Failed to load draft details: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('Draft details:', data)
    
    if (data.error) {
      throw new Error(data.error)
    }
    
    // Populate form with draft data
    form.value = {
      title: data.title || '',
      description: data.description || '',
      priceModel: data.priceModel || { modelType: 'fixed', askingPrice: 0 },
      suggestedPricingModel: data.suggestedPricingModel || 'fixed',
      postcode: data.postcode || '',
      originalCategoryId: data.categoryId || null,
      originalCategoryName: data.categoryName || 'Unknown Category',
      selectedCategoryId: null, // Start with null (AI suggestion)
      categoryId: data.categoryId || null,
      categoryName: data.categoryName || 'Unknown Category',
      images: data.images || [],
      attributes: data.attributes || []
    }
    
  } catch (err) {
    console.error('Load draft details error:', err)
    loadError.value = err.message
  } finally {
    loadingDetails.value = false
  }
}

const validateForm = () => {
  errors.value = {}
  
  if (!form.value.title) {
    errors.value.title = 'Title is required'
  } else if (form.value.title.length > 60) {
    errors.value.title = 'Title must be 60 characters or less'
  }
  
  if (!form.value.description) {
    errors.value.description = 'Description is required'
  }
  
  if (!form.value.priceModel?.askingPrice || form.value.priceModel.askingPrice <= 0) {
    errors.value.price = 'Price must be greater than 0'
  }
  
  // Validate bidding-specific fields if bidding model
  if (form.value.priceModel?.modelType === 'bidding') {
    // According to official API: both askingPrice and minimalBid are REQUIRED for bidding
    if (!form.value.priceModel.askingPrice || form.value.priceModel.askingPrice <= 0) {
      errors.value.askingPrice = 'Asking price is required for bidding and must be greater than 0'
    }
    
    if (!form.value.priceModel.minimalBid || form.value.priceModel.minimalBid <= 0) {
      errors.value.minimalBid = 'Minimal bid is required for bidding and must be greater than 0'
    } else if (form.value.priceModel.minimalBid >= form.value.priceModel.askingPrice) {
      errors.value.minimalBid = 'Minimal bid must be less than asking price'
    }
  }
  
  if (!form.value.postcode) {
    errors.value.postcode = 'Postcode is required'
  } else if (!/^[1-9][0-9]{3}\s?[A-Z]{2}$/i.test(form.value.postcode.replace(/\s/g, ''))) {
    errors.value.postcode = 'Please enter a valid Dutch postcode (e.g., 1000AA)'
  }
  
  return Object.keys(errors.value).length === 0
}

const onCategoryChanged = async (newCategoryId) => {
  // Update the category fields when user selects a new category
  if (newCategoryId === null) {
    // User chose AI suggestion
    form.value.categoryId = form.value.originalCategoryId
    form.value.categoryName = form.value.originalCategoryName
  } else {
    // User chose a different category - fetch the category name
    form.value.categoryId = newCategoryId
    
    try {
      // Fetch categories to get the name
      const response = await fetch(`${config.public.apiBaseUrl}/categories`)
      const data = await response.json()
      const category = data.categories.find(cat => cat.id === newCategoryId)
      if (category) {
        form.value.categoryName = category.displayName
      }
    } catch (error) {
      console.error('Failed to fetch category name:', error)
      // Keep the original name as fallback
      form.value.categoryName = form.value.originalCategoryName
    }
  }
}

const handleNewImages = async (event) => {
  const files = Array.from(event.target.files)
  
  if (files.length === 0) return
  
  // Calculate how many more images we can add
  const currentTotal = (form.value.images?.length || 0) + newImages.value.length
  const remainingSlots = 3 - currentTotal
  
  if (files.length > remainingSlots) {
    errors.value.general = `Can only add ${remainingSlots} more image${remainingSlots !== 1 ? 's' : ''}. Maximum 3 images total.`
    return
  }
  
  // Clear any existing errors
  errors.value.general = null
  
  // Process each file
  for (const file of files) {
    // Validate file size (max 10MB per image)
    if (file.size > 10 * 1024 * 1024) {
      errors.value.general = `Image "${file.name}" is too large (${(file.size / 1024 / 1024).toFixed(1)}MB). Please select images under 10MB.`
      continue
    }
    
    // Validate file type
    if (!file.type.startsWith('image/')) {
      errors.value.general = `"${file.name}" is not a valid image file.`
      continue
    }
    
    try {
      const preview = await fileToBase64(file)
      newImages.value.push({
        file: file,
        preview: preview,
        name: file.name
      })
    } catch (error) {
      errors.value.general = `Failed to read image "${file.name}"`
    }
  }
  
  // Reset file input
  if (imageInput.value) {
    imageInput.value.value = ''
  }
}

const removeExistingImage = (index) => {
  form.value.images.splice(index, 1)
  errors.value.general = null
}

const removeNewImage = (index) => {
  newImages.value.splice(index, 1)
  errors.value.general = null
}

const uploadNewImagesToS3 = async (userToken) => {
  if (newImages.value.length === 0) return []
  
  const uploadedUrls = []
  
  for (const imageObj of newImages.value) {
    try {
      // Compress image  
      const compressedBase64 = await resizeAndCompressImage(imageObj.file, 1024, 1024, 0.8)
      
      // Use the new draft image upload endpoint  
      const response = await fetch(`${config.public.apiBaseUrl}/draft-images/upload?user_id=${userToken}`, {
        method: 'POST', 
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          draft_id: props.draft.draftId,
          image: compressedBase64.split(',')[1] // Remove data:image/jpeg;base64, prefix
        })
      })
      
      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Failed to upload image (${response.status}): ${errorText}`)
      }
      
      const data = await response.json()
      if (data.error) {
        throw new Error(data.error)
      }
      
      uploadedUrls.push(data.imageUrl)
      
    } catch (error) {
      console.error('Error uploading image:', error)
      throw new Error(`Failed to upload image "${imageObj.name}": ${error.message}`)
    }
  }
  
  return uploadedUrls
}

const saveDraft = async () => {
  if (!validateForm()) {
    return
  }
  
  saving.value = true
  
  try {
    const userToken = localStorage.getItem('marktplaats_user_id')
    if (!userToken) {
      throw new Error('User not authenticated')
    }
    
    const draftId = props.draft.draftId
    console.log('Saving draft:', draftId)
    
    // Upload new images if any
    let newImageUrls = []
    if (newImages.value.length > 0) {
      try {
        newImageUrls = await uploadNewImagesToS3(userToken)
      } catch (error) {
        errors.value.general = error.message
        return
      }
    }
    
    // Combine existing and new image URLs
    const finalImageUrls = [...(form.value.images || []), ...newImageUrls]
    
    const updateData = {
      title: form.value.title,
      description: form.value.description,
      priceModel: form.value.priceModel, // Send complete price model
      postcode: form.value.postcode.replace(/\s/g, ''), // Remove spaces from postcode
      images: finalImageUrls // Update images array
    }
    
    // Include category change if user selected a different category
    if (form.value.selectedCategoryId !== null) {
      updateData.categoryId = form.value.categoryId
      updateData.categoryName = form.value.categoryName
    }
    
    console.log('Update data:', updateData)
    
    const response = await fetch(`${config.public.apiBaseUrl}/drafts/${draftId}?user_id=${userToken}`, {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify(updateData)
    })
    
    console.log('Update response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('Update error:', errorText)
      
      try {
        const errorData = JSON.parse(errorText)
        if (errorData.error && errorData.error.includes('validation error')) {
          throw new Error(`Validation error: ${errorData.error}`)
        } else if (errorData.error) {
          throw new Error(errorData.error)
        }
      } catch (parseError) {
        // If we can't parse the error, use a generic message
      }
      
      throw new Error(`Failed to update draft (${response.status}). Please check your input and try again.`)
    }
    
    const data = await response.json()
    console.log('Update response:', data)
    
    if (data.error) {
      throw new Error(data.error)
    }
    
    // Create updated draft object for parent component
    const updatedDraft = {
      ...props.draft,
      title: form.value.title,
      description: form.value.description,
      priceModel: form.value.priceModel,
      postcode: form.value.postcode.replace(/\s/g, ''),
      categoryId: form.value.categoryId,
      categoryName: form.value.categoryName || data.categoryName || form.value.originalCategoryName
    }
    
    emit('saved', updatedDraft)
    
  } catch (err) {
    console.error('Save draft error:', err)
    // Show error in form
    errors.value.general = err.message
  } finally {
    saving.value = false
  }
}

// Utility functions
const fileToBase64 = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.readAsDataURL(file)
    reader.onload = () => resolve(reader.result)
    reader.onerror = error => reject(error)
  })
}

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

// Watch form changes to clear errors
watch(form, () => {
  // Clear general error when user starts typing
  if (errors.value.general) {
    errors.value.general = null
  }
  
  if (Object.keys(errors.value).filter(key => key !== 'general').length > 0) {
    validateForm()
  }
}, { deep: true })
</script>