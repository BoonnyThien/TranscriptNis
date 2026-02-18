<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'

// State
const url = ref('')
const language = ref('')
const isLoading = ref(false)
const result = ref(null)
const error = ref('')
const copied = ref(false)
const uploadedFile = ref(null)
const isDragging = ref(false)
const inputMode = ref('url') // 'url' or 'file'
const processingStep = ref('') // Current step being processed
const elapsedTime = ref(0)
const timerInterval = ref(null)

// Download & Format options
const isCheckingFormats = ref(false)
const showFormatModal = ref(false)
const availableFormats = ref(null)
const selectedFormatId = ref(null)
const isDownloading = ref(false)

// Result View Mode
const resultViewMode = ref('text') // 'text' or 'time'

// Available languages with descriptions
const languages = [
  { code: '', label: 'Tự động (Auto-detect)', hint: 'Whisper tự đoán ngôn ngữ' },
  { code: 'en', label: 'English' },
  { code: 'vi', label: 'Tiếng Việt' },
  { code: 'ja', label: '日本語 (Japanese)' },
  { code: 'ko', label: '한국어 (Korean)' },
  { code: 'zh', label: '中文 (Chinese)' },
  { code: 'fr', label: 'Français' },
  { code: 'de', label: 'Deutsch' },
  { code: 'es', label: 'Español' },
  { code: 'pt', label: 'Português' },
  { code: 'ru', label: 'Русский' },
  { code: 'th', label: 'ไทย' },
  { code: 'id', label: 'Bahasa Indonesia' },
]

// Platform icons mapping
const platformIcons = {
  youtube: '🎬',
  facebook: '📘',
  instagram: '📸',
  tiktok: '🎵',
  twitter: '🐦',
  vimeo: '🎥',
  soundcloud: '🎧',
  upload: '📁',
  other: '🌐',
}

// Computed
const isValidUrl = computed(() => {
  if (!url.value) return false
  try {
    new URL(url.value)
    return true
  } catch {
    return false
  }
})

const canSubmit = computed(() => {
  if (inputMode.value === 'url') {
    return isValidUrl.value && !isLoading.value
  } else {
    return uploadedFile.value && !isLoading.value
  }
})

const platformIcon = computed(() => {
  if (!result.value?.platform) return '🌐'
  return platformIcons[result.value.platform] || '🌐'
})

const formatDuration = (seconds) => {
  if (!seconds) return null
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatElapsedTime = computed(() => {
  const mins = Math.floor(elapsedTime.value / 60)
  const secs = elapsedTime.value % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
})

// Timer functions
function startTimer() {
  elapsedTime.value = 0
  timerInterval.value = setInterval(() => {
    elapsedTime.value++
  }, 1000)
}

function stopTimer() {
  if (timerInterval.value) {
    clearInterval(timerInterval.value)
    timerInterval.value = null
  }
}

// File handling
function handleFileSelect(event) {
  const file = event.target.files[0]
  if (file) {
    validateAndSetFile(file)
  }
}

function handleDrop(event) {
  event.preventDefault()
  isDragging.value = false
  const file = event.dataTransfer.files[0]
  if (file) {
    validateAndSetFile(file)
    inputMode.value = 'file'
  }
}

function validateAndSetFile(file) {
  const allowedTypes = ['audio/mpeg', 'audio/mp3', 'audio/wav', 'audio/m4a', 
                        'video/mp4', 'video/webm', 'audio/webm']
  const maxSize = 25 * 1024 * 1024 // 25MB
  
  if (file.size > maxSize) {
    error.value = 'File quá lớn. Tối đa 25MB.'
    return
  }
  
  const ext = file.name.split('.').pop().toLowerCase()
  const allowedExts = ['mp3', 'mp4', 'wav', 'm4a', 'webm', 'ogg']
  if (!allowedExts.includes(ext)) {
    error.value = `File không hỗ trợ. Chấp nhận: ${allowedExts.join(', ')}`
    return
  }
  
  uploadedFile.value = file
  error.value = ''
}

function handleDragOver(event) {
  event.preventDefault()
  isDragging.value = true
}

function handleDragLeave() {
  isDragging.value = false
}

function removeFile() {
  uploadedFile.value = null
}

function switchToUrl() {
  inputMode.value = 'url'
  uploadedFile.value = null
}

function switchToFile() {
  inputMode.value = 'file'
  url.value = ''
}

// Transcription
async function transcribe() {
  if (!canSubmit.value) return
  
  isLoading.value = true
  error.value = ''
  result.value = null
  copied.value = false
  startTimer()
  resultViewMode.value = 'text'

  try {
    let response
    
    if (inputMode.value === 'url') {
      processingStep.value = 'Đang tải video...'
      
      response = await fetch('/api/transcribe', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          url: url.value,
          language: language.value || null,
        }),
      })
    } else {
      processingStep.value = 'Đang upload file...'
      
      const formData = new FormData()
      formData.append('file', uploadedFile.value)
      if (language.value) {
        formData.append('language', language.value)
      }
      
      response = await fetch('/api/transcribe/upload', {
        method: 'POST',
        body: formData,
      })
    }

    processingStep.value = 'Đang chuyển đổi thành văn bản...'
    const data = await response.json()

    if (!response.ok) {
      throw new Error(data.detail || 'Transcription failed')
    }

    result.value = data
    processingStep.value = ''
  } catch (e) {
    error.value = e.message || 'Lỗi không mong đợi'
    processingStep.value = ''
  } finally {
    isLoading.value = false
    stopTimer()
  }
}

// Format Check & Download
async function checkFormats() {
  if (!url.value || !isValidUrl.value) return
  
  isCheckingFormats.value = true
  error.value = ''
  availableFormats.value = null
  
  try {
    const response = await fetch('/api/formats', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: url.value }),
    })
    
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Không thể lấy thông tin video')
    }
    
    availableFormats.value = await response.json()
    showFormatModal.value = true
    
    // Auto-select first option
    if (availableFormats.value.options.length > 0) {
      selectedFormatId.value = availableFormats.value.options[0].id
    }
  } catch (e) {
    error.value = e.message
  } finally {
    isCheckingFormats.value = false
  }
}

async function downloadSelectedFormat() {
  if (!selectedFormatId.value) return
  
  // Find selected option
  const option = availableFormats.value.options.find(o => o.id === selectedFormatId.value)
  if (!option) return
  
  isDownloading.value = true
  try {
    const body = {
      url: url.value,
      format: option.type === 'audio' ? 'mp3' : 'mp4',
    }
    
    if (option.id.startsWith('video_')) {
      const height = option.height
      if (height >= 1080) body.quality = 'high'
      else if (height >= 720) body.quality = 'medium'
      else body.quality = 'low'
      
    } else if (option.id === 'mp3') {
      body.format = 'mp3'
    } else {
      body.format_id = option.id
    }

    const response = await fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
    })
    
    if (!response.ok) {
      const data = await response.json()
      throw new Error(data.detail || 'Download failed')
    }
    
    const blob = await response.blob()
    const downloadUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = downloadUrl
    a.download = `download.${body.format}`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    URL.revokeObjectURL(downloadUrl)
    
    showFormatModal.value = false
  } catch (e) {
    // Fallback logic for TikTok/FB if format selection fails
    if (e.message.includes('not available') || e.message.includes('TikTok') || e.message.includes('Facebook')) {
        try {
            const response = await fetch('/api/download', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    url: url.value,
                    format: 'mp4',
                    quality: 'best'
                }),
            })
             if (response.ok) {
                const blob = await response.blob()
                const downloadUrl = URL.createObjectURL(blob)
                const a = document.createElement('a')
                a.href = downloadUrl
                a.download = `download_fallback.mp4`
                document.body.appendChild(a)
                a.click()
                document.body.removeChild(a)
                URL.revokeObjectURL(downloadUrl)
                showFormatModal.value = false
                return
             }
        } catch (e2) {}
    }
    error.value = e.message
  } finally {
    isDownloading.value = false
  }
}

async function copyToClipboard(text) {
  const content = (typeof text === 'string' ? text : null) || result.value?.text
  if (!content) return
  
  try {
    await navigator.clipboard.writeText(content)
    copied.value = true
    setTimeout(() => {
      copied.value = false
    }, 2000)
  } catch (e) {
    error.value = 'Không thể copy'
  }
}

function clearAll() {
  url.value = ''
  language.value = ''
  result.value = null
  error.value = ''
  copied.value = false
  uploadedFile.value = null
  processingStep.value = ''
  stopTimer()
}

// Cleanup
onUnmounted(() => {
  stopTimer()
})
</script>

<template>
  <div 
    class="min-h-screen py-8 px-4"
    @dragover="handleDragOver"
    @dragleave="handleDragLeave"
    @drop="handleDrop"
  >
    <!-- Format Modal -->
    <div v-if="showFormatModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm">
      <div class="bg-gray-800 rounded-xl shadow-2xl max-w-md w-full border border-gray-700 overflow-hidden">
        <div class="p-6">
          <h3 class="text-xl font-bold text-white mb-2">Chọn định dạng tải về</h3>
          <p v-if="availableFormats" class="text-gray-400 text-sm mb-4 truncate">{{ availableFormats.title }}</p>
          
          <div class="space-y-2 mb-6 max-h-60 overflow-y-auto custom-scrollbar">
            <div 
              v-for="option in availableFormats?.options" 
              :key="option.id"
              class="flex items-center p-3 rounded-lg border cursor-pointer hover:bg-gray-700 transition-colors"
              :class="selectedFormatId === option.id ? 'border-indigo-500 bg-indigo-500/10' : 'border-gray-700 bg-gray-800'"
              @click="selectedFormatId = option.id"
            >
              <div class="w-5 h-5 rounded-full border border-gray-500 mr-3 flex items-center justify-center p-0.5">
                <div v-if="selectedFormatId === option.id" class="w-full h-full rounded-full bg-indigo-500"></div>
              </div>
              <div class="flex-1">
                <div class="flex items-center justify-between">
                  <span class="font-medium text-gray-200">{{ option.label }}</span>
                  <span v-if="option.size_mb" class="text-xs text-gray-400 bg-gray-900 px-2 py-1 rounded">~{{ option.size_mb }} MB</span>
                </div>
              </div>
            </div>
          </div>
          
          <div class="flex gap-3">
            <button 
              @click="showFormatModal = false"
              class="flex-1 py-2 px-4 bg-gray-700 hover:bg-gray-600 text-gray-300 rounded-lg text-sm font-medium"
            >
              Đóng
            </button>
            <button 
              @click="downloadSelectedFormat"
              :disabled="isDownloading"
              class="flex-1 py-2 px-4 bg-gradient-to-r from-indigo-600 to-purple-600 hover:from-indigo-500 hover:to-purple-500 text-white rounded-lg text-sm font-medium disabled:opacity-50"
            >
              {{ isDownloading ? 'Đang tải...' : 'Tải ngay' }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- Drag overlay -->
    <div 
      v-if="isDragging"
      class="fixed inset-0 bg-indigo-600/20 backdrop-blur-sm z-50 flex items-center justify-center pointer-events-none"
    >
      <div class="text-center">
        <div class="text-6xl mb-4">📁</div>
        <p class="text-2xl text-white font-semibold">Thả file vào đây</p>
        <p class="text-gray-300">MP3, MP4, WAV, M4A, WebM (max 25MB)</p>
      </div>
    </div>

    <div class="max-w-4xl mx-auto">
      <!-- Header -->
      <header class="text-center mb-12">
        <div class="inline-flex items-center gap-3 mb-4">
          <div class="w-12 h-12 rounded-xl bg-gradient-to-br from-indigo-500 to-cyan-400 flex items-center justify-center">
            <svg class="w-7 h-7 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
            </svg>
          </div>
          <h1 class="text-4xl font-bold text-shimmer">Transcript AI</h1>
        </div>
        <p class="text-gray-400 text-lg mb-4">
          Chuyển đổi video/audio thành văn bản với AI
        </p>
        <!-- Supported Platforms -->
        <div class="flex flex-wrap justify-center gap-2 text-2xl">
          <span title="YouTube">🎬</span>
          <span title="Facebook">📘</span>
          <span title="Instagram">📸</span>
          <span title="TikTok">🎵</span>
          <span title="Twitter/X">🐦</span>
          <span title="File Upload">📁</span>
          <span title="1000+ more" class="text-sm text-gray-500 self-center">+1000</span>
        </div>
      </header>

      <!-- Info Banner -->
      <div class="glass-card p-4 mb-8 text-sm text-gray-400 border-l-4 border-indigo-500">
        <p class="mb-1">
          <strong class="text-indigo-400">📌 Lưu ý về ngôn ngữ:</strong> 
          Chọn ngôn ngữ giúp Whisper nhận dạng chính xác hơn
        </p>
        <p>
          <strong class="text-indigo-400">🎵 Về nhạc:</strong> 
          Whisper chỉ nhận dạng lời nói
        </p>
      </div>

      <!-- Main Form -->
      <div class="gradient-border mb-8">
        <div class="glass-card p-6 md:p-8">
          <div class="space-y-6">
            <!-- Input Mode Toggle -->
            <div class="flex gap-2 p-1 bg-gray-800 rounded-lg w-fit">
              <button
                @click="switchToUrl"
                :class="[
                  'px-4 py-2 rounded-md text-sm font-medium transition-all',
                  inputMode === 'url' 
                    ? 'bg-indigo-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                ]"
              >
                🔗 URL
              </button>
              <button
                @click="switchToFile"
                :class="[
                  'px-4 py-2 rounded-md text-sm font-medium transition-all',
                  inputMode === 'file' 
                    ? 'bg-indigo-600 text-white' 
                    : 'text-gray-400 hover:text-white'
                ]"
              >
                📁 Upload File
              </button>
            </div>

            <!-- URL Input -->
            <div v-if="inputMode === 'url'">
              <label for="url" class="block text-sm font-medium text-gray-300 mb-2">
                URL Video/Audio
              </label>
              <div class="flex gap-2">
                <input
                  id="url"
                  v-model="url"
                  type="url"
                  placeholder="Paste link YouTube, Facebook, Instagram, TikTok, hoặc bất kỳ URL..."
                  class="flex-1 px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-white placeholder-gray-500"
                  :disabled="isLoading"
                />
                <!-- Check Formats Button -->
                <button
                  @click="checkFormats"
                  :disabled="!isValidUrl || isLoading || isCheckingFormats"
                  class="px-4 py-3 bg-gray-700 text-gray-300 rounded-lg hover:bg-gray-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all flex items-center gap-2"
                  title="Tùy chọn tải xuống"
                >
                  <span v-if="!isCheckingFormats">⬇️</span>
                  <span v-else class="w-5 h-5 animate-spin border-2 border-white/30 border-t-white rounded-full"></span>
                </button>
              </div>
              <p class="mt-2 text-xs text-gray-500">
                Hỗ trợ: YouTube, Facebook, Instagram, TikTok, Twitter, Vimeo, SoundCloud...
              </p>
            </div>

            <!-- File Upload -->
            <div v-else>
              <label class="block text-sm font-medium text-gray-300 mb-2">
                Upload File
              </label>
              <div
                v-if="!uploadedFile"
                class="border-2 border-dashed border-gray-700 rounded-lg p-8 text-center hover:border-indigo-500 transition-colors cursor-pointer"
                @click="$refs.fileInput.click()"
              >
                <input
                  ref="fileInput"
                  type="file"
                  accept=".mp3,.mp4,.wav,.m4a,.webm,.ogg"
                  class="hidden"
                  @change="handleFileSelect"
                />
                <div class="text-4xl mb-3">📁</div>
                <p class="text-gray-400">
                  Kéo thả file hoặc <span class="text-indigo-400">chọn từ máy</span>
                </p>
                <p class="text-gray-500 text-sm mt-2">
                  MP3, MP4, WAV, M4A, WebM, OGG (max 25MB)
                </p>
              </div>
              <div
                v-else
                class="flex items-center gap-4 p-4 bg-gray-800/50 rounded-lg"
              >
                <div class="text-3xl">📎</div>
                <div class="flex-1">
                  <p class="text-white font-medium">{{ uploadedFile.name }}</p>
                  <p class="text-gray-400 text-sm">
                    {{ (uploadedFile.size / 1024 / 1024).toFixed(2) }} MB
                  </p>
                </div>
                <button
                  @click="removeFile"
                  class="text-red-400 hover:text-red-300"
                >
                  ✕
                </button>
              </div>
            </div>

            <!-- Language Select -->
            <div>
              <label for="language" class="block text-sm font-medium text-gray-300 mb-2">
                Ngôn ngữ 
                <span class="text-gray-500 text-xs">(giúp nhận dạng chính xác hơn)</span>
              </label>
              <select
                id="language"
                v-model="language"
                class="w-full px-4 py-3 bg-gray-800/50 border border-gray-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none transition-all text-white"
                :disabled="isLoading"
              >
                <option v-for="lang in languages" :key="lang.code" :value="lang.code">
                  {{ lang.label }}
                </option>
              </select>
            </div>

            <!-- Action Buttons -->
            <div class="flex gap-4">
              <button
                @click="transcribe"
                :disabled="!canSubmit"
                class="flex-1 py-3 px-6 bg-gradient-to-r from-indigo-600 to-purple-600 text-white font-semibold rounded-lg hover:from-indigo-500 hover:to-purple-500 focus:ring-4 focus:ring-indigo-500/30 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-300"
                :class="{ 'pulse-glow': !isLoading && canSubmit }"
              >
                <span v-if="!isLoading" class="flex items-center justify-center gap-2">
                  <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Transcribe
                </span>
                <span v-else class="flex items-center justify-center gap-2">
                  <svg class="animate-spin w-5 h-5" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  Đang xử lý...
                </span>
              </button>
              <button
                @click="clearAll"
                class="py-3 px-6 bg-gray-700 text-gray-300 font-semibold rounded-lg hover:bg-gray-600 transition-all"
              >
                Xóa
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Loading State with Progress -->
      <div v-if="isLoading" class="glass-card p-8 mb-8 text-center">
        <div class="flex flex-col items-center gap-4">
          <div class="spinner"></div>
          <div>
            <p class="text-gray-300 font-medium">{{ processingStep }}</p>
            <p class="text-indigo-400 text-xl mt-2">⏱️ {{ formatElapsedTime }}</p>
          </div>
          <p class="text-gray-500 text-sm">
            Video dài có thể mất vài phút...
          </p>
        </div>
      </div>

      <!-- Error Message -->
      <div v-if="error" class="glass-card p-6 mb-8 border-l-4 border-red-500 bg-red-500/10">
        <div class="flex items-start gap-3">
          <svg class="w-6 h-6 text-red-400 flex-shrink-0 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
          <div>
            <h3 class="font-semibold text-red-400">Lỗi</h3>
            <p class="text-gray-300 mt-1">{{ error }}</p>
          </div>
        </div>
      </div>

      <!-- Result -->
      <div v-if="result" class="glass-card overflow-hidden">
        <!-- Result Header -->
        <div class="p-4 bg-gradient-to-r from-green-500/10 to-cyan-500/10 border-b border-gray-700/50">
          <div class="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div class="flex items-center gap-3">
              <span class="text-2xl">{{ platformIcon }}</span>
              <div>
                <span class="font-semibold text-green-400">Hoàn thành!</span>
                <p v-if="result.title" class="text-sm text-gray-400 truncate max-w-md">
                  {{ result.title }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4 text-sm text-gray-400">
              <span v-if="result.platform" class="px-2 py-1 bg-gray-700 rounded capitalize">
                {{ result.platform }}
              </span>
              <span v-if="result.duration">
                🕐 {{ formatDuration(result.duration) }}
              </span>
              <span>📝 {{ result.word_count }} từ</span>
              <span>⚡ {{ result.processing_time }}s</span>
            </div>
          </div>
        </div>

        <!-- View Toggle (Text / Timeline) -->
        <div class="border-b border-gray-700/50 flex">
          <button 
            @click="resultViewMode = 'text'"
            class="px-6 py-3 text-sm font-medium transition-colors relative"
            :class="resultViewMode === 'text' ? 'text-indigo-400 border-b-2 border-indigo-400' : 'text-gray-400 hover:text-white'"
          >
            📄 Văn bản (Text)
          </button>
          <button 
             v-if="result.vtt"
            @click="resultViewMode = 'time'"
            class="px-6 py-3 text-sm font-medium transition-colors relative"
            :class="resultViewMode === 'time' ? 'text-indigo-400 border-b-2 border-indigo-400' : 'text-gray-400 hover:text-white'"
          >
            ⏱️ Mốc thời gian (Timeline)
          </button>
        </div>

        <!-- Result Content -->
        <div class="p-6">
          <div class="mb-4 flex items-center justify-between">
            <h3 class="text-lg font-semibold text-gray-200">
              {{ resultViewMode === 'text' ? 'Nội dung' : 'Timeline chi tiết' }}
            </h3>
            <button
              @click="copyToClipboard(resultViewMode === 'text' ? result.text : result.vtt)"
              class="flex items-center gap-2 px-4 py-2 text-sm bg-gray-700 hover:bg-gray-600 rounded-lg transition-all"
              :class="{ 'bg-green-600 hover:bg-green-600': copied }"
            >
              <svg v-if="!copied" class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 16H6a2 2 0 01-2-2V6a2 2 0 012-2h8a2 2 0 012 2v2m-6 12h8a2 2 0 002-2v-8a2 2 0 00-2-2h-8a2 2 0 00-2 2v8a2 2 0 002 2z" />
              </svg>
              <svg v-else class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
              </svg>
              {{ copied ? 'Đã copy!' : 'Copy' }}
            </button>
          </div>

          <!-- Text View -->
          <div v-if="resultViewMode === 'text'" class="bg-gray-800/50 rounded-lg p-4 max-h-96 overflow-y-auto custom-scrollbar">
            <p class="text-gray-200 whitespace-pre-wrap leading-relaxed space-y-4 font-normal">{{ result.text }}</p>
          </div>

          <!-- Timeline View -->
          <div v-else class="bg-gray-800/50 rounded-lg p-4 max-h-96 overflow-y-auto custom-scrollbar">
            <pre class="text-gray-300 font-mono text-sm whitespace-pre-wrap">{{ result.vtt }}</pre>
          </div>
        </div>
      </div>

      <!-- Footer -->
      <footer class="mt-12 text-center text-gray-500 text-sm">
        <p class="mb-2">Powered by Cloudflare Workers AI (Whisper) • Made with ❤️</p>
        <p class="text-xs">
          Hỗ trợ 1000+ nguồn video/audio thông qua 
          <a href="https://github.com/yt-dlp/yt-dlp" target="_blank" class="text-indigo-400 hover:underline">yt-dlp</a>
        </p>
      </footer>
    </div>
  </div>
</template>

<style scoped>
.custom-scrollbar::-webkit-scrollbar {
  width: 8px;
}
.custom-scrollbar::-webkit-scrollbar-track {
  background: rgba(31, 41, 55, 0.5);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb {
  background: rgba(75, 85, 99, 0.8);
  border-radius: 4px;
}
.custom-scrollbar::-webkit-scrollbar-thumb:hover {
  background: rgba(107, 114, 128, 1);
}
</style>
