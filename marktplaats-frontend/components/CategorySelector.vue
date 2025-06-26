<template>
  <div class="category-selector">
    <div class="flex items-center justify-between mb-3">
      <label class="block text-sm font-medium text-gray-700">Category</label>
      <button
        v-if="!showSelector"
        @click="showSelector = true"
        type="button"
        class="text-sm text-primary hover:text-orange-700 font-medium"
      >
        Change Category
      </button>
      <button
        v-else
        @click="cancelSelection"
        type="button"
        class="text-sm text-gray-500 hover:text-gray-700"
      >
        Cancel
      </button>
    </div>

    <!-- Current/Selected Category Display -->
    <div v-if="!showSelector" class="mb-2">
      <div class="p-3 bg-gray-50 rounded-md border">
        <div class="flex items-center justify-between">
          <div>
            <span class="text-sm text-gray-500">{{ isOverridden ? 'Selected:' : 'AI Suggested:' }}</span>
            <div class="font-medium text-gray-900">{{ displayCategoryName }}</div>
          </div>
          <div v-if="isOverridden" class="text-green-600 text-sm">✓ Override</div>
          <div v-else class="text-blue-600 text-sm">🤖 AI</div>
        </div>
      </div>
    </div>

    <!-- Category Search/Selector -->
    <div v-else class="space-y-3">
      <!-- Search Input -->
      <div>
        <input
          v-model="searchQuery"
          @input="filterCategories"
          type="text"
          placeholder="Search categories... (e.g. 'kitesurfen', 'auto', 'computer')"
          class="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-primary focus:border-primary"
          ref="searchInput"
        >
      </div>

      <!-- Category List -->
      <div class="border border-gray-300 rounded-md max-h-60 overflow-y-auto bg-white">
        <div v-if="loading" class="p-4 text-center text-gray-500">
          <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-primary mx-auto mb-2"></div>
          Loading categories...
        </div>
        
        <div v-else-if="filteredCategories.length === 0" class="p-4 text-center text-gray-500">
          No categories found. Try a different search term.
        </div>
        
        <div v-else>
          <button
            v-for="category in filteredCategories.slice(0, 50)"
            :key="category.id"
            @click="selectCategory(category)"
            type="button"
            class="w-full text-left px-4 py-3 hover:bg-gray-50 border-b border-gray-100 last:border-b-0 focus:outline-none focus:bg-blue-50 transition-colors"
            :class="{ 
              'bg-blue-50 border-blue-200': selectedCategoryId === category.id,
              'bg-green-50': category.id === originalCategoryId && selectedCategoryId !== category.id
            }"
          >
            <div class="flex items-center justify-between">
              <div>
                <div class="font-medium text-gray-900">{{ category.level2 }}</div>
                <div class="text-sm text-gray-500">{{ category.level1 }}</div>
              </div>
              <div class="flex items-center space-x-2">
                <div v-if="category.id === originalCategoryId" class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                  AI Suggested
                </div>
                <div v-if="selectedCategoryId === category.id" class="text-green-600">
                  ✓
                </div>
              </div>
            </div>
          </button>
          
          <div v-if="filteredCategories.length > 50" class="p-3 text-center text-sm text-gray-500 border-t">
            Showing first 50 results. Try a more specific search to see more.
          </div>
        </div>
      </div>

      <!-- Action Buttons -->
      <div class="flex space-x-3">
        <button
          @click="confirmSelection"
          :disabled="!selectedCategoryId"
          type="button"
          class="flex-1 btn btn-primary disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Use Selected Category
        </button>
        <button
          @click="useAISuggestion"
          type="button"
          class="flex-1 btn btn-secondary"
        >
          Use AI Suggestion
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  originalCategoryId: {
    type: Number,
    required: true
  },
  originalCategoryName: {
    type: String,
    required: true
  },
  modelValue: {
    type: Number,
    default: null
  }
})

const emit = defineEmits(['update:modelValue', 'categoryChanged'])

const config = useRuntimeConfig()

// Reactive state
const categories = ref([])
const filteredCategories = ref([])
const searchQuery = ref('')
const showSelector = ref(false)
const loading = ref(false)
const selectedCategoryId = ref(null)
const searchInput = ref()

// Computed
const isOverridden = computed(() => {
  return props.modelValue !== null && props.modelValue !== props.originalCategoryId
})

const displayCategoryName = computed(() => {
  if (isOverridden.value) {
    const category = categories.value.find(cat => cat.id === props.modelValue)
    return category ? category.displayName : 'Unknown Category'
  }
  return props.originalCategoryName
})

// Methods
const fetchCategories = async () => {
  if (categories.value.length > 0) return // Already loaded
  
  loading.value = true
  try {
    const response = await fetch(`${config.public.apiBaseUrl}/categories`)
    const data = await response.json()
    categories.value = data.categories
    filteredCategories.value = data.categories
  } catch (error) {
    console.error('Failed to fetch categories:', error)
  } finally {
    loading.value = false
  }
}

const filterCategories = () => {
  const query = searchQuery.value.toLowerCase().trim()
  if (!query) {
    filteredCategories.value = categories.value
    return
  }
  
  filteredCategories.value = categories.value.filter(category => 
    category.displayName.toLowerCase().includes(query) ||
    category.level1.toLowerCase().includes(query) ||
    category.level2.toLowerCase().includes(query)
  )
}

const selectCategory = (category) => {
  selectedCategoryId.value = category.id
}

const confirmSelection = () => {
  if (selectedCategoryId.value) {
    emit('update:modelValue', selectedCategoryId.value)
    emit('categoryChanged', selectedCategoryId.value)
    showSelector.value = false
    searchQuery.value = ''
  }
}

const useAISuggestion = () => {
  emit('update:modelValue', null) // null means use original AI suggestion
  emit('categoryChanged', null)
  showSelector.value = false
  searchQuery.value = ''
}

const cancelSelection = () => {
  showSelector.value = false
  searchQuery.value = ''
  selectedCategoryId.value = props.modelValue
}

// Watch for when selector opens to fetch categories and focus input
watch(showSelector, (newValue) => {
  if (newValue) {
    fetchCategories()
    selectedCategoryId.value = props.modelValue
    nextTick(() => {
      searchInput.value?.focus()
    })
  }
})

// Watch for prop changes
watch(() => props.modelValue, (newValue) => {
  selectedCategoryId.value = newValue
})

// Initialize
onMounted(() => {
  selectedCategoryId.value = props.modelValue
})
</script>

<style scoped>
.category-selector {
  /* Component-specific styles if needed */
}
</style>