<template>
  <div class="bidding-price-config">
    <h4 class="text-md font-medium text-gray-700 mb-3 flex items-center">
      <span class="text-lg mr-2">⚖️</span>
      Bidding Configuration
    </h4>
    
    <div class="space-y-4">
      <!-- Asking Price -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Asking Price *
        </label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
          <input
            v-model.number="askingPrice"
            type="number"
            min="1"
            step="1"
            class="pl-8 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            :class="{ 'border-red-300': errors.askingPrice }"
            placeholder="0"
          />
        </div>
        <p v-if="errors.askingPrice" class="text-red-600 text-sm mt-1">{{ errors.askingPrice }}</p>
        <p class="text-gray-500 text-sm mt-1">The price you're asking for this item</p>
      </div>

      <!-- Minimal Bid -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Minimal Bid *
        </label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
          <input
            v-model.number="minimalBid"
            type="number"
            min="1"
            step="1"
            class="pl-8 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            :class="{ 'border-red-300': errors.minimalBid }"
            placeholder="1"
          />
        </div>
        <p v-if="errors.minimalBid" class="text-red-600 text-sm mt-1">{{ errors.minimalBid }}</p>
        <p class="text-gray-500 text-sm mt-1">Minimum bid amount required</p>
      </div>
    </div>

    <!-- Bidding Summary -->
    <div class="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
      <h5 class="text-sm font-medium text-blue-900 mb-2">📋 Bidding Summary</h5>
      <div class="text-sm text-blue-700 space-y-1">
        <div class="flex justify-between">
          <span>Asking price:</span>
          <span class="font-medium">€{{ formatPrice(askingPrice || 0) }}</span>
        </div>
        <div class="flex justify-between">
          <span>Minimal bid:</span>
          <span class="font-medium">€{{ formatPrice(minimalBid || 1) }}</span>
        </div>
      </div>
      
      <!-- Validation Warnings -->
      <div v-if="validationWarnings.length > 0" class="mt-3 pt-3 border-t border-blue-300">
        <div v-for="warning in validationWarnings" :key="warning" class="text-sm text-orange-600 flex items-center">
          <span class="mr-1">⚠️</span>
          {{ warning }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ 
      modelType: 'bidding', 
      askingPrice: 0, 
      minimalBid: 1
    })
  },
  errors: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const askingPrice = computed({
  get: () => props.modelValue?.askingPrice || 0,
  set: (value) => {
    const newModel = {
      ...props.modelValue,
      askingPrice: value
    }
    
    // Auto-adjust minimal bid to be reasonable (10% of asking price, minimum €1)
    if (value > 0) {
      const suggestedMinimal = Math.max(1, Math.floor(value * 0.10))
      if (!props.modelValue?.minimalBid || props.modelValue.minimalBid === 1) {
        newModel.minimalBid = suggestedMinimal
      }
    }
    
    emit('update:modelValue', newModel)
  }
})

const minimalBid = computed({
  get: () => props.modelValue?.minimalBid || 1,
  set: (value) => {
    emit('update:modelValue', {
      ...props.modelValue,
      minimalBid: value
    })
  }
})

const formatPrice = (price) => {
  return price.toFixed(2)
}

const validationWarnings = computed(() => {
  const warnings = []
  
  if (minimalBid.value >= askingPrice.value && askingPrice.value > 0) {
    warnings.push('Minimal bid should be less than asking price')
  }
  
  if (minimalBid.value < 1) {
    warnings.push('Minimal bid must be at least €1')
  }
  
  if (askingPrice.value < 1) {
    warnings.push('Asking price must be at least €1')
  }
  
  return warnings
})
</script>