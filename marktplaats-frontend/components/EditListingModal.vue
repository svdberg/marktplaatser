<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-lg p-6 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-2xl font-bold text-gray-900">
          ✏️ Edit Listing
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
        <p class="text-gray-600 mt-2">Loading listing details...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="loadError" class="bg-red-50 border border-red-200 rounded-lg p-4 mb-4">
        <p class="text-red-700">{{ loadError }}</p>
        <button
          @click="loadListingDetails"
          class="btn btn-primary mt-2"
        >
          🔄 Retry
        </button>
      </div>

      <!-- Edit Form -->
      <form v-else @submit.prevent="saveListing" class="space-y-6">
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
            maxlength="80"
            required
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
            :class="{ 'border-red-300': errors.title }"
          >
          <p v-if="errors.title" class="text-red-600 text-sm mt-1">{{ errors.title }}</p>
          <p class="text-gray-500 text-sm mt-1">{{ form.title?.length || 0 }}/80 characters</p>
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

        <!-- Price -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Price (€) *
          </label>
          <input
            v-model.number="form.price"
            type="number"
            min="0.01"
            step="0.01"
            required
            class="w-full rounded-md border-gray-300 shadow-sm focus:border-primary focus:ring-primary"
            :class="{ 'border-red-300': errors.price }"
          >
          <p v-if="errors.price" class="text-red-600 text-sm mt-1">{{ errors.price }}</p>
        </div>

        <!-- Category (Read-only for now) -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Category
          </label>
          <input
            :value="form.categoryName || 'Unknown Category'"
            type="text"
            readonly
            class="w-full rounded-md border-gray-300 bg-gray-50 shadow-sm"
          >
          <p class="text-gray-500 text-sm mt-1">Category cannot be changed after creation</p>
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

        <!-- Reserved Status -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">
            Listing Status
          </label>
          <div class="flex items-center space-x-3">
            <label class="flex items-center">
              <input
                v-model="form.reserved"
                type="checkbox"
                class="rounded border-gray-300 text-primary focus:ring-primary"
                :disabled="form.reserved"
              >
              <span class="ml-2 text-sm text-gray-700" :class="{ 'opacity-50': form.reserved }">
                🔒 Mark as reserved (during negotiations)
              </span>
            </label>
          </div>
          <p class="text-gray-500 text-sm mt-1">
            {{ form.reserved 
              ? '⚠️ Reserved status is permanent and cannot be changed back to available' 
              : '⚠️ WARNING: Marking as reserved appears to be PERMANENT. You will not be able to change it back.' 
            }}
          </p>
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
            {{ saving ? '⏳ Saving...' : '💾 Save Changes' }}
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  listing: {
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
  price: 0,
  categoryName: '',
  attributes: [],
  reserved: false
})

const loadingDetails = ref(false)
const loadError = ref(null)
const saving = ref(false)
const errors = ref({})

// Initialize form data
onMounted(() => {
  loadListingDetails()
})

// Computed
const isFormValid = computed(() => {
  return form.value.title && 
         form.value.title.length <= 80 &&
         form.value.description && 
         form.value.price > 0 &&
         Object.keys(errors.value).length === 0
})

// Methods
const loadListingDetails = async () => {
  loadingDetails.value = true
  loadError.value = null
  
  try {
    const userToken = localStorage.getItem('marktplaats_user_id')
    if (!userToken) {
      throw new Error('User not authenticated')
    }
    
    const listingId = props.listing.itemId || props.listing.id
    console.log('Loading details for listing:', listingId)
    
    const response = await fetch(`${config.public.apiBaseUrl}/manage-advertisement/${listingId}?user_id=${userToken}`, {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    console.log('Get listing details response status:', response.status)
    
    if (!response.ok) {
      const errorText = await response.text()
      console.error('Get listing details error:', errorText)
      throw new Error(`Failed to load listing details: ${response.status}`)
    }
    
    const data = await response.json()
    console.log('Listing details:', data)
    
    if (data.error) {
      throw new Error(data.error)
    }
    
    // Populate form with listing data
    form.value = {
      title: data.title || '',
      description: data.description || '',
      price: data.priceModel?.askingPrice ? (data.priceModel.askingPrice / 100) : 0,
      categoryName: data.category?.name || 'Unknown Category',
      attributes: data.attributes || [],
      reserved: data.reserved || false
    }
    
  } catch (err) {
    console.error('Load listing details error:', err)
    loadError.value = err.message
  } finally {
    loadingDetails.value = false
  }
}

const validateForm = () => {
  errors.value = {}
  
  if (!form.value.title) {
    errors.value.title = 'Title is required'
  } else if (form.value.title.length > 80) {
    errors.value.title = 'Title must be 80 characters or less'
  }
  
  if (!form.value.description) {
    errors.value.description = 'Description is required'
  }
  
  if (!form.value.price || form.value.price <= 0) {
    errors.value.price = 'Price must be greater than 0'
  }
  
  return Object.keys(errors.value).length === 0
}

const saveListing = async () => {
  if (!validateForm()) {
    return
  }
  
  saving.value = true
  
  try {
    const userToken = localStorage.getItem('marktplaats_user_id')
    if (!userToken) {
      throw new Error('User not authenticated')
    }
    
    const listingId = props.listing.itemId || props.listing.id
    console.log('Saving listing:', listingId)
    
    const updateData = {
      title: form.value.title,
      description: form.value.description,
      priceModel: {
        modelType: 'fixed',
        askingPrice: Math.round(form.value.price * 100) // Convert euros to cents
      },
      reserved: form.value.reserved
    }
    
    console.log('Update data:', updateData)
    
    const response = await fetch(`${config.public.apiBaseUrl}/manage-advertisement/${listingId}?user_id=${userToken}`, {
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
      
      throw new Error(`Failed to update listing (${response.status}). Please check your input and try again.`)
    }
    
    const data = await response.json()
    console.log('Update response:', data)
    
    if (data.error) {
      throw new Error(data.error)
    }
    
    // Create updated listing object for parent component
    const updatedListing = {
      ...props.listing,
      title: form.value.title,
      description: form.value.description,
      priceModel: {
        modelType: 'fixed',
        askingPrice: Math.round(form.value.price * 100)
      },
      reserved: form.value.reserved
    }
    
    emit('saved', updatedListing)
    
  } catch (err) {
    console.error('Save listing error:', err)
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
  
  if (Object.keys(errors.value).length > 0) {
    validateForm()
  }
}, { deep: true })
</script>