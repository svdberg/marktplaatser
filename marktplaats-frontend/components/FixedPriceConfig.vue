<template>
  <div class="fixed-price-config">
    <h4 class="text-md font-medium text-gray-700 mb-3 flex items-center">
      <span class="text-lg mr-2">🏷️</span>
      Fixed Price Configuration
    </h4>
    
    <div class="space-y-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Asking Price *
        </label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
          <input
            v-model.number="askingPrice"
            type="number"
            min="0.01"
            step="0.01"
            class="pl-8 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            :class="{ 'border-red-300': errors.price }"
            placeholder="0.00"
          />
        </div>
        <p v-if="errors.price" class="text-red-600 text-sm mt-1">{{ errors.price }}</p>
        <p class="text-gray-500 text-sm mt-1">The price buyers will pay immediately</p>
      </div>

      <!-- Price Preview -->
      <div v-if="askingPrice > 0" class="bg-gray-50 rounded-lg p-3">
        <div class="text-sm text-gray-600">
          <div class="flex justify-between items-center">
            <span>Listing price:</span>
            <span class="font-semibold text-lg text-green-600">€{{ formatPrice(askingPrice) }}</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({ modelType: 'fixed', askingPrice: 0 })
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
    emit('update:modelValue', {
      ...props.modelValue,
      askingPrice: value
    })
  }
})

const formatPrice = (price) => {
  return price.toFixed(2)
}
</script>