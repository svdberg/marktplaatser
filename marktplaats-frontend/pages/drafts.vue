<template>
  <div class="min-h-screen">
    <!-- Header -->
    <Header 
      :user-token="userToken" 
      current-page="drafts"
      @logout="logout"
    />

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Authorization Required -->
      <div v-if="!userToken" class="text-center py-12">
        <div class="card max-w-md mx-auto">
          <h2 class="text-2xl font-bold text-gray-900 mb-4">
            Authorization Required
          </h2>
          <p class="text-gray-600 mb-6">
            Please authorize with Marktplaats to view your drafts.
          </p>
          <NuxtLink to="/" class="btn btn-primary w-full">
            🔑 Go to Authorization
          </NuxtLink>
        </div>
      </div>

      <!-- Loading State -->
      <div v-else-if="loading" class="text-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
        <p class="text-gray-600 mt-4">Loading your drafts...</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="card bg-red-50 border-red-200 mb-8">
        <h2 class="text-xl font-semibold text-red-800 mb-2">
          ❌ Error
        </h2>
        <p class="text-red-700 mb-4">{{ error }}</p>
        <button
          @click="fetchDrafts"
          class="btn btn-secondary"
        >
          🔄 Try Again
        </button>
      </div>

      <!-- Empty State -->
      <div v-else-if="drafts.length === 0" class="text-center py-12">
        <div class="card max-w-md mx-auto">
          <div class="text-6xl mb-4">📝</div>
          <h2 class="text-2xl font-bold text-gray-900 mb-4">
            No Drafts Yet
          </h2>
          <p class="text-gray-600 mb-6">
            You haven't created any draft listings yet. Upload an image to generate your first draft!
          </p>
          <NuxtLink to="/" class="btn btn-primary w-full">
            🚀 Create Your First Draft
          </NuxtLink>
        </div>
      </div>

      <!-- Drafts List -->
      <div v-else>
        <!-- Header with Stats -->
        <div class="card mb-8">
          <div class="flex justify-between items-center mb-4">
            <div>
              <h2 class="text-xl font-semibold text-gray-900">
                Your Draft Listings
              </h2>
              <p class="text-gray-600">
                {{ drafts.length }} draft{{ drafts.length !== 1 ? 's' : '' }} ready to publish
              </p>
            </div>
            <div class="flex space-x-3">
              <button
                @click="fetchDrafts"
                :disabled="loading"
                class="btn btn-secondary text-sm"
              >
                🔄 Refresh
              </button>
              <NuxtLink to="/" class="btn btn-primary text-sm">
                ➕ Create New Draft
              </NuxtLink>
            </div>
          </div>
        </div>

        <!-- Drafts Grid -->
        <div class="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
          <div
            v-for="draft in drafts"
            :key="draft.draftId"
            class="card hover:shadow-lg transition-shadow"
          >
            <!-- Draft Image -->
            <div v-if="draft.images && draft.images.length > 0" class="mb-4">
              <img
                :src="draft.images[0]"
                :alt="draft.title"
                class="w-full h-48 object-cover rounded-lg"
              >
            </div>
            <div v-else class="bg-gray-100 h-48 rounded-lg flex items-center justify-center mb-4">
              <span class="text-gray-400 text-4xl">📷</span>
            </div>

            <!-- Draft Info -->
            <div class="space-y-3">
              <div>
                <h3 class="font-semibold text-gray-900 truncate">
                  {{ draft.title || 'Untitled Draft' }}
                </h3>
                <p class="text-sm text-gray-600 truncate">
                  {{ draft.categoryName || 'No category' }}
                </p>
              </div>

              <p class="text-sm text-gray-700 line-clamp-2">
                {{ draft.description || 'No description' }}
              </p>

              <!-- Price and Status -->
              <div class="flex justify-between items-center text-sm">
                <div class="flex items-center space-x-2">
                  <span v-if="draft.priceModel?.askingPrice" class="font-medium text-gray-900">
                    €{{ Math.round(draft.priceModel.askingPrice / 100) }}
                  </span>
                  <span v-else class="text-gray-500">No price set</span>
                </div>
                <div class="flex items-center space-x-1">
                  <span v-if="draft.aiGenerated" class="text-xs bg-blue-100 text-blue-800 px-2 py-1 rounded">
                    🤖 AI
                  </span>
                  <span class="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded">
                    📝 Draft
                  </span>
                </div>
              </div>

              <!-- Created Date -->
              <p class="text-xs text-gray-500">
                Created {{ formatDate(draft.createdAt) }}
              </p>

              <!-- Action Buttons -->
              <div class="space-y-2 pt-3 border-t">
                <button
                  @click="publishDraft(draft)"
                  :disabled="publishing === draft.draftId"
                  class="btn btn-primary w-full text-sm disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {{ publishing === draft.draftId ? '⏳ Publishing...' : '🚀 Publish to Marktplaats' }}
                </button>
                <div class="grid grid-cols-3 gap-2">
                  <button
                    @click="editDraft(draft)"
                    class="btn btn-secondary text-sm"
                  >
                    ✏️ Edit
                  </button>
                  <button
                    @click="previewDraft(draft)"
                    class="btn btn-secondary text-sm"
                  >
                    👁️ Preview
                  </button>
                  <button
                    @click="deleteDraft(draft.draftId)"
                    class="btn bg-red-100 text-red-700 hover:bg-red-200 text-sm"
                  >
                    🗑️ Delete
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Load More Button -->
        <div v-if="hasMore" class="text-center mt-8">
          <button
            @click="loadMore"
            :disabled="loadingMore"
            class="btn btn-secondary"
          >
            {{ loadingMore ? '⏳ Loading...' : '📄 Load More Drafts' }}
          </button>
        </div>
      </div>
    </main>

    <!-- Draft Preview Modal -->
    <div
      v-if="selectedDraft"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click="closePreview"
    >
      <div
        class="bg-white rounded-lg max-w-2xl w-full max-h-[90vh] overflow-y-auto"
        @click.stop
      >
        <div class="p-6">
          <div class="flex justify-between items-start mb-4">
            <h3 class="text-xl font-semibold text-gray-900">
              Draft Preview
            </h3>
            <button
              @click="closePreview"
              class="text-gray-400 hover:text-gray-600"
            >
              ✕
            </button>
          </div>

          <!-- Preview Content -->
          <div class="space-y-4">
            <!-- Image -->
            <div v-if="selectedDraft.images && selectedDraft.images.length > 0">
              <img
                :src="selectedDraft.images[0]"
                :alt="selectedDraft.title"
                class="w-full max-h-64 object-cover rounded-lg"
              >
            </div>

            <!-- Details -->
            <div class="space-y-3">
              <div>
                <label class="block text-sm font-medium text-gray-700">Title</label>
                <p class="text-gray-900">{{ selectedDraft.title || 'No title' }}</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Category</label>
                <p class="text-gray-900">{{ selectedDraft.categoryName || 'No category' }}</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Description</label>
                <p class="text-gray-900 whitespace-pre-wrap">{{ selectedDraft.description || 'No description' }}</p>
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700">Price</label>
                <p class="text-gray-900">
                  {{ selectedDraft.priceModel?.askingPrice ? `€${Math.round(selectedDraft.priceModel.askingPrice / 100)}` : 'No price set' }}
                </p>
              </div>

              <div v-if="selectedDraft.postcode">
                <label class="block text-sm font-medium text-gray-700">Location</label>
                <p class="text-gray-900">{{ selectedDraft.postcode }}</p>
              </div>

              <!-- Attributes -->
              <div v-if="selectedDraft.attributes && selectedDraft.attributes.length > 0">
                <label class="block text-sm font-medium text-gray-700 mb-2">Attributes</label>
                <div class="space-y-1">
                  <div
                    v-for="attr in selectedDraft.attributes"
                    :key="attr.key"
                    class="text-sm"
                  >
                    <span class="text-gray-600">{{ attr.key }}:</span>
                    <span class="text-gray-900 ml-2">{{ attr.value }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Action Buttons -->
          <div class="flex space-x-3 mt-6 pt-4 border-t">
            <button
              @click="publishDraft(selectedDraft)"
              :disabled="publishing === selectedDraft.draftId"
              class="btn btn-primary flex-1 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {{ publishing === selectedDraft.draftId ? '⏳ Publishing...' : '🚀 Publish to Marktplaats' }}
            </button>
            <button
              @click="closePreview"
              class="btn btn-secondary flex-1"
            >
              Close
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Edit Draft Modal -->
    <EditDraftModal
      v-if="draftToEdit"
      :draft="draftToEdit"
      @close="closeEditModal"
      @saved="handleDraftSaved"
    />

    <!-- Delete Confirmation Modal -->
    <div
      v-if="draftToDelete"
      class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center p-4 z-50"
      @click="cancelDelete"
    >
      <div
        class="bg-white rounded-lg max-w-md w-full p-6"
        @click.stop
      >
        <h3 class="text-lg font-semibold text-gray-900 mb-4">
          Delete Draft
        </h3>
        <p class="text-gray-700 mb-6">
          Are you sure you want to delete this draft? This action cannot be undone.
        </p>
        <div class="flex space-x-3">
          <button
            @click="confirmDelete"
            :disabled="deleting"
            class="btn bg-red-600 text-white hover:bg-red-700 flex-1"
          >
            {{ deleting ? '⏳ Deleting...' : '🗑️ Delete' }}
          </button>
          <button
            @click="cancelDelete"
            class="btn btn-secondary flex-1"
          >
            Cancel
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import EditDraftModal from '~/components/EditDraftModal.vue'

const config = useRuntimeConfig()

// Reactive data
const userToken = ref(null)
const drafts = ref([])
const loading = ref(false)
const loadingMore = ref(false)
const error = ref(null)
const hasMore = ref(false)
const selectedDraft = ref(null)
const draftToEdit = ref(null)
const draftToDelete = ref(null)
const deleting = ref(false)
const publishing = ref(null) // Track which draft is being published

// Check for stored user ID on mount
onMounted(() => {
  const userId = localStorage.getItem('marktplaats_user_id')
  if (userId) {
    userToken.value = userId
    fetchDrafts()
  }
})

// Methods
const fetchDrafts = async (loadMore = false) => {
  if (!userToken.value) return

  if (loadMore) {
    loadingMore.value = true
  } else {
    loading.value = true
    drafts.value = []
  }
  
  error.value = null

  try {
    const url = `${config.public.apiBaseUrl}/drafts?user_id=${userToken.value}`
    const response = await fetch(url)
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Failed to fetch drafts: ${errorText}`)
    }
    
    const data = await response.json()
    
    if (loadMore) {
      drafts.value.push(...data.drafts)
    } else {
      drafts.value = data.drafts
    }
    
    // Check if there are more drafts to load
    hasMore.value = data.drafts.length === 20 // Assuming API returns max 20 per page
    
  } catch (err) {
    error.value = err.message
  } finally {
    loading.value = false
    loadingMore.value = false
  }
}

const loadMore = () => {
  fetchDrafts(true)
}

const publishDraft = async (draft) => {
  if (!draft || publishing.value) return
  
  publishing.value = draft.draftId
  error.value = null
  
  try {
    console.log('Publishing draft:', draft.draftId)
    
    const response = await fetch(`${config.public.apiBaseUrl}/drafts/${draft.draftId}/publish?user_id=${userToken.value}`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        deleteDraft: true // Delete draft after successful publishing
      })
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Failed to publish draft: ${errorText}`)
    }
    
    const result = await response.json()
    console.log('Draft published successfully:', result)
    
    // Close preview modal if open
    if (selectedDraft.value?.draftId === draft.draftId) {
      selectedDraft.value = null
    }
    
    // Remove draft from local list if it was deleted
    if (result.draftDeleted) {
      drafts.value = drafts.value.filter(d => d.draftId !== draft.draftId)
    }
    
    // Show success message (you could also navigate to listings page)
    alert(`🎉 Draft published successfully!\nAdvertisement ID: ${result.advertisementId}`)
    
  } catch (err) {
    console.error('Error publishing draft:', err)
    error.value = `Failed to publish draft: ${err.message}`
  } finally {
    publishing.value = null
  }
}

const previewDraft = (draft) => {
  selectedDraft.value = draft
}

const closePreview = () => {
  selectedDraft.value = null
}

const deleteDraft = (draftId) => {
  draftToDelete.value = draftId
}

const confirmDelete = async () => {
  if (!draftToDelete.value || !userToken.value) return
  
  deleting.value = true
  
  try {
    const response = await fetch(`${config.public.apiBaseUrl}/drafts/${draftToDelete.value}?user_id=${userToken.value}`, {
      method: 'DELETE',
      headers: {
        'Content-Type': 'application/json'
      }
    })
    
    if (!response.ok) {
      const errorText = await response.text()
      throw new Error(`Failed to delete draft: ${errorText}`)
    }
    
    // Remove from local list
    drafts.value = drafts.value.filter(d => d.draftId !== draftToDelete.value)
    
    draftToDelete.value = null
    
  } catch (err) {
    error.value = err.message
  } finally {
    deleting.value = false
  }
}

const cancelDelete = () => {
  draftToDelete.value = null
}

const editDraft = (draft) => {
  draftToEdit.value = draft
}

const closeEditModal = () => {
  draftToEdit.value = null
}

const handleDraftSaved = (updatedDraft) => {
  // Update the draft in the local list
  const index = drafts.value.findIndex(d => d.draftId === updatedDraft.draftId)
  if (index !== -1) {
    drafts.value[index] = updatedDraft
  }
  
  // Close the edit modal
  draftToEdit.value = null
  
  // Show success message
  alert('📝 Draft updated successfully!')
}

const formatDate = (dateStr) => {
  try {
    const date = new Date(dateStr)
    return date.toLocaleDateString() + ' at ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
  } catch {
    return 'Unknown date'
  }
}

const logout = () => {
  localStorage.removeItem('marktplaats_user_id')
  userToken.value = null
  drafts.value = []
  navigateTo('/')
}
</script>

<style scoped>
.line-clamp-2 {
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>