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

        <!-- Current Images -->
        <div v-if="form.images && form.images.length > 0">
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Current Images
          </label>
          <div class="grid grid-cols-2 md:grid-cols-3 gap-3">
            <div
              v-for="(image, index) in form.images"
              :key="index"
              class="relative"
            >
              <img
                :src="image"
                :alt="`Draft image ${index + 1}`"
                class="w-full h-24 object-cover rounded-lg border"
              >
            </div>
          </div>
          <p class="text-gray-500 text-sm mt-1">Images cannot be changed after creation</p>
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
    
    const updateData = {
      title: form.value.title,
      description: form.value.description,
      priceModel: form.value.priceModel, // Send complete price model
      postcode: form.value.postcode.replace(/\s/g, '') // Remove spaces from postcode
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