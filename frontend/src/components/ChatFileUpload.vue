<template>
  <div class="file-upload">
    <input
      type="file"
      ref="fileInput"
      @change="handleFileSelect"
      :accept="acceptTypes"
      style="display: none"
    />
    <button
      @click="$refs.fileInput.click()"
      class="upload-btn"
      :disabled="isUploading"
      :title="uploadTitle"
    >
      <span v-if="!isUploading">📎 上传文件</span>
      <span v-else>上传中...</span>
    </button>

    <!-- 文件列表 -->
    <div v-if="uploadedFiles.length > 0" class="file-list">
      <div
        v-for="file in uploadedFiles"
        :key="file.id"
        class="file-item"
      >
        <span class="file-icon">📄</span>
        <span class="file-name">{{ file.name }}</span>
        <button
          @click="removeFile(file.id)"
          class="remove-btn"
          title="移除"
        >×</button>
      </div>
    </div>

    <!-- 错误提示 -->
    <div v-if="error" class="error-message">{{ error }}</div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { apiClient } from '@/services/apiClient'
import { useSessionStore } from '@/stores/sessionStore'

interface UploadedFile {
  id: string
  name: string
  content?: string
  mode: 'api' | 'text_extraction'
}

const emit = defineEmits<{
  (e: 'files-changed', files: UploadedFile[]): void
}>()

const sessionStore = useSessionStore()
const fileInput = ref<HTMLInputElement>()
const uploadedFiles = ref<UploadedFile[]>([])
const isUploading = ref(false)
const error = ref<string>('')

// 支持的文件类型
const acceptTypes = '.txt,.md,.pdf,.doc,.docx,.xls,.xlsx,.ppt,.pptx'

const uploadTitle = computed(() => {
  return `支持的文件类型: ${acceptTypes}`
})

async function handleFileSelect(event: Event) {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  if (!file) return

  isUploading.value = true
  error.value = ''

  try {
    const formData = new FormData()
    formData.append('file', file)

    // 获取当前选择的 provider
    // 从 currentModel 中提取 provider 部分（格式：provider:model_name）
    const modelValue = sessionStore.currentModel || 'deepseek:deepseek-chat'
    const provider = modelValue.split(':')[0] || 'deepseek'

    const response = await apiClient.post(
      `/files/upload?provider=${provider}`,
      formData,
      {
        headers: {
          'Content-Type': 'multipart/form-data'
        }
      }
    )

    const result = response.data

    if (result.success) {
      const newFile: UploadedFile = {
        id: result.file_id || crypto.randomUUID(),
        name: file.name,
        content: result.content,
        mode: result.mode
      }

      uploadedFiles.value.push(newFile)
      emit('files-changed', uploadedFiles.value)
    }
  } catch (err: any) {
    error.value = err.response?.data?.detail || '文件上传失败'
  } finally {
    isUploading.value = false
    // 清空 input 以便重复上传同一文件
    input.value = ''
  }
}

function removeFile(fileId: string) {
  uploadedFiles.value = uploadedFiles.value.filter(f => f.id !== fileId)
  emit('files-changed', uploadedFiles.value)
}

function clearFiles() {
  uploadedFiles.value = []
  emit('files-changed', uploadedFiles.value)
}

// 暴露给父组件
defineExpose({
  clearFiles,
  getFiles: () => uploadedFiles.value
})
</script>

<style scoped>
.file-upload {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.upload-btn {
  padding: 8px 16px;
  background: #f0f0f0;
  border: 1px solid #ddd;
  border-radius: 4px;
  cursor: pointer;
  font-size: 14px;
}

.upload-btn:hover:not(:disabled) {
  background: #e0e0e0;
}

.upload-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.file-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-height: 150px;
  overflow-y: auto;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 10px;
  background: #f9f9f9;
  border-radius: 4px;
  font-size: 13px;
}

.file-icon {
  font-size: 14px;
}

.file-name {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.remove-btn {
  background: none;
  border: none;
  color: #999;
  cursor: pointer;
  font-size: 18px;
  line-height: 1;
  padding: 0 4px;
}

.remove-btn:hover {
  color: #f56c6c;
}

.error-message {
  color: #f56c6c;
  font-size: 12px;
}
</style>
