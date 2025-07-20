<template>
  <div class="bidding-price-config">
    <h4 class="text-md font-medium text-gray-700 mb-3 flex items-center">
      <span class="text-lg mr-2">⚖️</span>
      Bidding/Auction Configuration
    </h4>
    
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <!-- Starting Bid -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Starting Bid *
        </label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
          <input
            v-model.number="startingBid"
            type="number"
            min="1"
            step="1"
            class="pl-8 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            :class="{ 'border-red-300': errors.price }"
            placeholder="0"
          />
        </div>
        <p v-if="errors.price" class="text-red-600 text-sm mt-1">{{ errors.price }}</p>
        <p class="text-gray-500 text-sm mt-1">Minimum starting price for bids</p>
      </div>

      <!-- Minimum Bid Increment -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Minimum Bid Increment *
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
        <p class="text-gray-500 text-sm mt-1">Minimum amount to increase each bid</p>
      </div>

      <!-- Auction Duration -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Auction Duration *
        </label>
        <select
          v-model.number="auctionDuration"
          class="w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
        >
          <option :value="3">3 days</option>
          <option :value="5">5 days</option>
          <option :value="7">7 days (recommended)</option>
          <option :value="10">10 days</option>
          <option :value="14">14 days</option>
        </select>
        <p class="text-gray-500 text-sm mt-1">How long the auction will run</p>
      </div>

      <!-- Reserve Price (Optional) -->
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Reserve Price (Optional)
        </label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
          <input
            v-model.number="reservePrice"
            type="number"
            min="0"
            step="1"
            class="pl-8 w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500"
            placeholder="No reserve"
          />
        </div>
        <p class="text-gray-500 text-sm mt-1">Hidden minimum price (optional)</p>
      </div>
    </div>

    <!-- Bidding Summary -->
    <div class="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
      <h5 class="text-sm font-medium text-blue-900 mb-2">📋 Auction Summary</h5>
      <div class="text-sm text-blue-700 space-y-1">
        <div class="flex justify-between">
          <span>Starting bid:</span>
          <span class="font-medium">€{{ formatPrice(startingBid || 0) }}</span>
        </div>
        <div class="flex justify-between">
          <span>Minimum increment:</span>
          <span class="font-medium">€{{ formatPrice(minimalBid || 1) }}</span>
        </div>
        <div class="flex justify-between">
          <span>Auction duration:</span>
          <span class="font-medium">{{ auctionDuration || 7 }} days</span>
        </div>
        <div v-if="reservePrice && reservePrice > 0" class="flex justify-between">
          <span>Reserve price:</span>
          <span class="font-medium">€{{ formatPrice(reservePrice) }}</span>
        </div>
        <div v-else class="flex justify-between">
          <span>Reserve price:</span>
          <span class="font-medium text-gray-500">No reserve</span>
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
      minimalBid: 1, 
      auctionDuration: 7,
      reservePrice: 0
    })
  },
  errors: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const startingBid = computed({
  get: () => props.modelValue?.askingPrice || 0,
  set: (value) => {
    const newModel = {
      ...props.modelValue,
      askingPrice: value
    }
    
    // Auto-adjust minimal bid to be reasonable (5% of starting bid, minimum €1)
    if (value > 0) {
      const suggestedMinimal = Math.max(1, Math.floor(value * 0.05))
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

const auctionDuration = computed({
  get: () => props.modelValue?.auctionDuration || 7,
  set: (value) => {
    emit('update:modelValue', {
      ...props.modelValue,
      auctionDuration: value
    })
  }
})

const reservePrice = computed({
  get: () => props.modelValue?.reservePrice || 0,
  set: (value) => {
    emit('update:modelValue', {
      ...props.modelValue,
      reservePrice: value || 0
    })
  }
})

const formatPrice = (price) => {
  return price.toFixed(2)
}

const validationWarnings = computed(() => {
  const warnings = []
  
  if (minimalBid.value >= startingBid.value && startingBid.value > 0) {
    warnings.push('Minimum bid increment should be less than starting bid')
  }
  
  if (reservePrice.value > 0 && reservePrice.value < startingBid.value) {
    warnings.push('Reserve price should be higher than starting bid')
  }
  
  if (minimalBid.value > 50) {
    warnings.push('Large bid increments may discourage bidders')
  }
  
  return warnings
})
</script>