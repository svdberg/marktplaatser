# Frontend Integration: Pricing Models Support

## 🎯 Phase 2: Frontend Implementation Plan

This document outlines the frontend changes needed to support the new AI-powered pricing model selection (fixed vs bidding).

### **Backend Changes Already Implemented ✅**

The backend now provides enhanced API responses with pricing model intelligence:

```json
{
  "draftId": "draft_123",
  "title": "Vintage Camera",
  "categoryId": 1234,
  "categoryName": "Fotografica",
  "priceModel": {
    "modelType": "bidding",
    "askingPrice": 150,
    "minimalBid": 8,
    "auctionDuration": 7
  },
  "suggestedPricingModel": "bidding",
  "message": "Draft listing created successfully with bidding pricing model!"
}
```

### **Frontend Components to Implement**

#### **1. Price Model Selector Component**

Create a new component: `components/PriceModelSelector.vue`

```vue
<template>
  <div class="price-model-selector">
    <h3 class="text-lg font-semibold mb-4">Pricing Model</h3>
    
    <!-- AI Suggestion Banner -->
    <div v-if="suggestedModel" class="bg-blue-50 border border-blue-200 rounded-lg p-3 mb-4">
      <div class="flex items-center">
        <Icon name="sparkles" class="text-blue-500 mr-2" />
        <span class="text-blue-700">
          AI suggests <strong>{{ suggestedModel }}</strong> pricing for this category
        </span>
      </div>
    </div>

    <!-- Model Type Selection -->
    <div class="space-y-3">
      <label class="flex items-start space-x-3">
        <input 
          type="radio" 
          :value="'fixed'" 
          v-model="selectedModel"
          class="mt-1"
        />
        <div>
          <div class="font-medium">Fixed Price</div>
          <div class="text-sm text-gray-600">Set a fixed price for immediate purchase</div>
        </div>
      </label>

      <label class="flex items-start space-x-3">
        <input 
          type="radio" 
          :value="'bidding'" 
          v-model="selectedModel"
          class="mt-1"
        />
        <div>
          <div class="font-medium">Bidding/Auction</div>
          <div class="text-sm text-gray-600">Let buyers bid on your item</div>
        </div>
      </label>
    </div>

    <!-- Dynamic Configuration -->
    <div v-if="selectedModel === 'fixed'" class="mt-4">
      <FixedPriceConfig v-model="priceModel" />
    </div>

    <div v-if="selectedModel === 'bidding'" class="mt-4">
      <BiddingPriceConfig v-model="priceModel" />
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: Object,
  suggestedModel: String
})

const emit = defineEmits(['update:modelValue'])

const selectedModel = computed({
  get: () => props.modelValue?.modelType || 'fixed',
  set: (value) => {
    // Create appropriate price model structure
    const newModel = value === 'bidding' 
      ? { modelType: 'bidding', askingPrice: 0, minimalBid: 1, auctionDuration: 7 }
      : { modelType: 'fixed', askingPrice: 0 }
    
    emit('update:modelValue', newModel)
  }
})
</script>
```

#### **2. Fixed Price Configuration**

Create: `components/FixedPriceConfig.vue`

```vue
<template>
  <div class="fixed-price-config">
    <div class="grid grid-cols-1 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Asking Price
        </label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
          <input
            v-model.number="price"
            type="number"
            min="1"
            step="1"
            class="pl-8 w-full border border-gray-300 rounded-md px-3 py-2"
            placeholder="0"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  modelValue: Object
})

const emit = defineEmits(['update:modelValue'])

const price = computed({
  get: () => props.modelValue?.askingPrice || 0,
  set: (value) => {
    emit('update:modelValue', {
      ...props.modelValue,
      askingPrice: value
    })
  }
})
</script>
```

#### **3. Bidding Price Configuration**

Create: `components/BiddingPriceConfig.vue`

```vue
<template>
  <div class="bidding-price-config">
    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Starting Bid
        </label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
          <input
            v-model.number="startingBid"
            type="number"
            min="1"
            step="1"
            class="pl-8 w-full border border-gray-300 rounded-md px-3 py-2"
            placeholder="0"
          />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Minimum Bid Increment
        </label>
        <div class="relative">
          <span class="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">€</span>
          <input
            v-model.number="minimalBid"
            type="number"
            min="1"
            step="1"
            class="pl-8 w-full border border-gray-300 rounded-md px-3 py-2"
            placeholder="1"
          />
        </div>
      </div>

      <div>
        <label class="block text-sm font-medium text-gray-700 mb-2">
          Auction Duration
        </label>
        <select
          v-model.number="auctionDuration"
          class="w-full border border-gray-300 rounded-md px-3 py-2"
        >
          <option :value="3">3 days</option>
          <option :value="5">5 days</option>
          <option :value="7">7 days (recommended)</option>
          <option :value="10">10 days</option>
          <option :value="14">14 days</option>
        </select>
      </div>

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
            class="pl-8 w-full border border-gray-300 rounded-md px-3 py-2"
            placeholder="No reserve"
          />
        </div>
      </div>
    </div>

    <!-- Bidding Info -->
    <div class="mt-4 p-3 bg-gray-50 rounded-lg">
      <div class="text-sm text-gray-600">
        <div class="flex justify-between">
          <span>Starting bid:</span>
          <span class="font-medium">€{{ startingBid || 0 }}</span>
        </div>
        <div class="flex justify-between">
          <span>Minimum increment:</span>
          <span class="font-medium">€{{ minimalBid || 1 }}</span>
        </div>
        <div class="flex justify-between">
          <span>Auction ends in:</span>
          <span class="font-medium">{{ auctionDuration || 7 }} days</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
// Similar computed properties for each field
// startingBid, minimalBid, auctionDuration, reservePrice
</script>
```

### **4. Integration Points**

#### **Draft Creation Page Updates**

In your draft creation/editing page:

```vue
<template>
  <div class="draft-form">
    <!-- Existing fields -->
    <input v-model="draft.title" placeholder="Title" />
    <textarea v-model="draft.description" placeholder="Description"></textarea>
    
    <!-- NEW: Pricing Model Selector -->
    <PriceModelSelector
      v-model="draft.priceModel"
      :suggested-model="draft.suggestedPricingModel"
    />
    
    <!-- Existing submit -->
    <button @click="saveDraft">Save Draft</button>
  </div>
</template>

<script setup>
const draft = ref({
  title: '',
  description: '',
  priceModel: { modelType: 'fixed', askingPrice: 0 },
  suggestedPricingModel: 'fixed' // From API response
})
</script>
```

#### **API Integration Updates**

Update your API calls to handle the new pricing model fields:

```javascript
// When creating/updating drafts
const updateDraft = async (draftData) => {
  const payload = {
    ...draftData,
    priceModel: {
      modelType: draftData.priceModel.modelType,
      askingPrice: draftData.priceModel.askingPrice,
      // Include bidding fields if modelType === 'bidding'
      ...(draftData.priceModel.modelType === 'bidding' && {
        minimalBid: draftData.priceModel.minimalBid,
        auctionDuration: draftData.priceModel.auctionDuration
      })
    }
  }
  
  return await $fetch('/api/drafts', {
    method: 'PATCH',
    body: payload
  })
}
```

### **5. Display Updates**

#### **Draft List View**

Update draft cards to show pricing model:

```vue
<template>
  <div class="draft-card">
    <h3>{{ draft.title }}</h3>
    <p>{{ draft.description }}</p>
    
    <!-- Price Display -->
    <div class="price-info">
      <div v-if="draft.priceModel.modelType === 'fixed'" class="flex items-center">
        <Icon name="tag" class="w-4 h-4 mr-1" />
        <span>€{{ draft.priceModel.askingPrice }}</span>
      </div>
      
      <div v-else-if="draft.priceModel.modelType === 'bidding'" class="flex items-center">
        <Icon name="gavel" class="w-4 h-4 mr-1" />
        <span>Starting bid: €{{ draft.priceModel.askingPrice }}</span>
      </div>
    </div>
  </div>
</template>
```

### **6. Validation**

Add client-side validation:

```javascript
const validatePriceModel = (priceModel) => {
  const errors = []
  
  if (!priceModel.askingPrice || priceModel.askingPrice <= 0) {
    errors.push('Price must be greater than 0')
  }
  
  if (priceModel.modelType === 'bidding') {
    if (priceModel.minimalBid <= 0) {
      errors.push('Minimum bid increment must be greater than 0')
    }
    
    if (priceModel.minimalBid >= priceModel.askingPrice) {
      errors.push('Minimum bid increment must be less than starting bid')
    }
  }
  
  return errors
}
```

### **📋 Implementation Checklist**

- [ ] Create `PriceModelSelector.vue` component
- [ ] Create `FixedPriceConfig.vue` component  
- [ ] Create `BiddingPriceConfig.vue` component
- [ ] Update draft creation/editing pages
- [ ] Update API integration for price model fields
- [ ] Update draft list display for pricing models
- [ ] Add client-side validation
- [ ] Add icons for fixed vs bidding display
- [ ] Test AI suggestions work correctly
- [ ] Test form validation and error handling

### **🎯 Expected User Experience**

1. **AI Guidance**: User uploads vintage camera → AI suggests "bidding" model
2. **Smart Defaults**: Bidding form pre-filled with starting bid €150, increment €8, 7 days
3. **Easy Switch**: User can override AI suggestion and choose fixed price instead
4. **Visual Clarity**: Icons and labels clearly distinguish fixed vs bidding pricing
5. **Validation**: Real-time feedback prevents invalid pricing configurations

This implementation will provide a seamless user experience with intelligent defaults while maintaining full user control over pricing decisions.