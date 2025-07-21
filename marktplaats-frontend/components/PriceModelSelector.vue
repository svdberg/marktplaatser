<template>
  <div class="price-model-selector">
    <h3 class="text-lg font-semibold mb-4">Pricing Model</h3>
    
    <!-- AI Suggestion Banner -->
    <div v-if="suggestedModel && suggestedModel !== 'fixed'" class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
      <div class="flex items-center">
        <span class="text-xl mr-2">✨</span>
        <span class="text-blue-700">
          AI suggests <strong>{{ suggestedModel }}</strong> pricing for this category
        </span>
      </div>
    </div>

    <!-- Model Type Selection -->
    <div class="space-y-4">
      <label class="flex items-start space-x-3 cursor-pointer">
        <input 
          type="radio" 
          value="fixed" 
          v-model="selectedModel"
          class="mt-1 text-blue-600 focus:ring-blue-500"
        />
        <div>
          <div class="font-medium flex items-center">
            <span class="text-xl mr-2">🏷️</span>
            Fixed Price
          </div>
          <div class="text-sm text-gray-600">Set a fixed price for immediate purchase</div>
        </div>
      </label>

      <label class="flex items-start space-x-3 cursor-pointer">
        <input 
          type="radio" 
          value="bidding" 
          v-model="selectedModel"
          class="mt-1 text-blue-600 focus:ring-blue-500"
        />
        <div>
          <div class="font-medium flex items-center">
            <span class="text-xl mr-2">⚖️</span>
            Bidding/Auction
          </div>
          <div class="text-sm text-gray-600">Let buyers bid on your item</div>
        </div>
      </label>
    </div>

    <!-- Dynamic Configuration -->
    <div class="mt-6">
      <div v-if="selectedModel === 'fixed'">
        <FixedPriceConfig 
          v-model="internalPriceModel" 
          :errors="errors"
        />
      </div>

      <div v-if="selectedModel === 'bidding'">
        <BiddingPriceConfig 
          v-model="internalPriceModel"
          :errors="errors"
        />
      </div>
    </div>
  </div>
</template>

<script setup>
import FixedPriceConfig from './FixedPriceConfig.vue'
import BiddingPriceConfig from './BiddingPriceConfig.vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ modelType: 'fixed', askingPrice: 0 })
  },
  suggestedModel: {
    type: String,
    default: 'fixed'
  },
  errors: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

// Flag to prevent infinite update loops
const isUpdatingFromParent = ref(false)

// Internal price model to manage the complete state
const internalPriceModel = ref({
  modelType: 'fixed',
  askingPrice: 0,
  minimalBid: 1, // Only used for bidding
  ...props.modelValue
})

// Computed for the selected model type
const selectedModel = computed({
  get: () => internalPriceModel.value.modelType || 'fixed',
  set: (value) => {
    if (value === 'bidding') {
      // When switching to bidding, according to official API specification
      // Both askingPrice and minimalBid are REQUIRED
      const currentPrice = internalPriceModel.value.askingPrice || 0
      internalPriceModel.value = {
        modelType: 'bidding',
        askingPrice: currentPrice,
        minimalBid: Math.max(1, Math.floor(currentPrice * 0.10)) // 10% of asking price or minimum €1
      }
    } else {
      // When switching to fixed, preserve the price
      const currentPrice = internalPriceModel.value.askingPrice || 0
      internalPriceModel.value = {
        modelType: 'fixed',
        askingPrice: currentPrice
      }
    }
    
    // Emit the updated model
    emit('update:modelValue', { ...internalPriceModel.value })
  }
})

// Watch for external updates (prevent infinite loops)
watch(() => props.modelValue, (newValue) => {
  if (newValue && !isUpdatingFromParent.value) {
    isUpdatingFromParent.value = true
    internalPriceModel.value = { 
      modelType: 'fixed',
      askingPrice: 0,
      minimalBid: 1, // Only used for bidding
      ...newValue 
    }
    nextTick(() => {
      isUpdatingFromParent.value = false
    })
  }
}, { deep: true, immediate: true })

// Watch internal changes and emit (only when not updating from parent)
watch(internalPriceModel, (newValue) => {
  if (!isUpdatingFromParent.value) {
    emit('update:modelValue', { ...newValue })
  }
}, { deep: true })

// Initialize with suggested model if provided and no current model type
onMounted(() => {
  if (!props.modelValue?.modelType && props.suggestedModel) {
    selectedModel.value = props.suggestedModel
  }
})
</script>