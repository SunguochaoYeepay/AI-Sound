<template>
  <a-drawer
    :open="visible"
    :title="character.id ? '编辑角色' : '新增角色'"
    width="600"
    placement="right"
    :maskClosable="false"
    @close="$emit('close')"
  >
    <template #extra>
      <a-space>
        <a-button @click="$emit('close')">取消</a-button>
        <a-button type="primary" @click="$emit('save', character)" :loading="saving">保存</a-button>
      </a-space>
    </template>

    <a-form
      ref="editForm"
      :model="character"
      :rules="editRules"
      layout="vertical"
      class="voice-edit-form"
    >
     

      <a-form-item label="角色名称" name="name" required>
        <a-input v-model:value="character.name" placeholder="请输入角色名称" />
      </a-form-item>

      <a-form-item label="角色头像" name="avatar">
        <div class="avatar-upload-section">
          <!-- 当前头像预览 -->
          <div class="current-avatar-preview">
            <div
              v-if="character.avatarUrl || character.avatarPreview"
              class="avatar-preview"
            >
              <img
                :src="character.avatarPreview || character.avatarUrl"
                alt="角色头像"
                class="avatar-image"
              />
            </div>
            <div
              v-else
              class="avatar-placeholder"
              :style="{ background: character.color || '#8b5cf6' }"
            >
              <svg width="32" height="32" viewBox="0 0 24 24" fill="white">
                <path
                  d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"
                />
              </svg>
            </div>
          </div>

          <!-- 头像上传 -->
          <a-upload
            v-model:fileList="character.avatarFileList"
            :multiple="false"
            :before-upload="beforeAvatarUpload"
            @change="handleAvatarChange"
            accept=".jpg,.jpeg,.png,.gif,.webp"
            :show-upload-list="true"
            :max-count="1"
            class="avatar-upload"
          >
            <a-button size="small" type="primary">
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
                </svg>
              </template>
              {{ character.avatarUrl ? '更换头像' : '上传头像' }}
            </a-button>
          </a-upload>

          <!-- AI生成头像按钮 -->
          <a-space style="margin-left: 8px">
            <a-button 
              size="small" 
              type="default"
              :loading="avatarGenerating"
              @click="$emit('generate-avatar')"
              :disabled="!character.name"
            >
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                </svg>
              </template>
              AI生成头像
            </a-button>
          </a-space>

          <!-- 移除头像按钮 -->
          <a-button
            v-if="character.avatarUrl || character.avatarPreview"
            size="small"
            danger
            type="text"
            @click="$emit('remove-avatar')"
          >
            移除头像
          </a-button>
        </div>
        <div class="upload-tips">支持 JPG、PNG、GIF、WebP 格式，最大10MB</div>
      </a-form-item>

      <a-form-item label="角色描述" name="description">
        <a-textarea
          v-model:value="character.description"
          placeholder="请输入角色描述信息（性格、特点等）"
          :rows="3"
        />
      </a-form-item>

      <a-form-item label="所属书籍" name="book_id">
        <a-select
          v-model:value="character.book_id"
          placeholder="选择角色所属的书籍（可选）"
          style="width: 100%"
          :loading="booksLoading"
          show-search
          allow-clear
          :filter-option="false"
          @search="$emit('book-search', $event)"
          @focus="$emit('load-books')"
        >
          <a-select-option value="">不关联书籍</a-select-option>
          <a-select-option v-for="book in availableBooks" :key="book.id" :value="book.id">
            {{ book.title }}
          </a-select-option>
        </a-select>
      </a-form-item>

      <!-- 声音配置 -->
      <a-divider orientation="left">声音配置</a-divider>

      <a-form-item label="声音类型" name="type" required>
        <a-select v-model:value="character.type" placeholder="选择声音类型">
          <a-select-option value="male">男声</a-select-option>
          <a-select-option value="female">女声</a-select-option>
          <a-select-option value="child">童声</a-select-option>
          <a-select-option value="elder">老人声</a-select-option>
          <a-select-option value="custom">自定义</a-select-option>
        </a-select>
      </a-form-item>

      <!-- 当前文件显示 -->
      <div
        v-if="character.id && (character.referenceAudioUrl || character.latentFileUrl)"
        class="current-files-section"
      >
        <a-divider>当前文件</a-divider>

        <!-- 当前音频文件 -->
        <div v-if="character.referenceAudioUrl" class="current-file-item">
          <div class="file-info">
            <div class="file-header">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="#10b981">
                <path
                  d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
                />
                <path
                  d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"
                />
              </svg>
              <span class="file-label">当前音频文件</span>
            </div>
            <div class="file-actions">
              <a-button size="small" type="text" @click="$emit('play-audio')">
                <template #icon>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M8,5.14V19.14L19,12.14L8,5.14Z" />
                  </svg>
                </template>
                播放
              </a-button>
            </div>
          </div>
        </div>

        <!-- 当前Latent文件 -->
        <div v-if="character.latentFileUrl" class="current-file-item">
          <div class="file-info">
            <div class="file-header">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="#10b981">
                <path
                  d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                />
              </svg>
              <span class="file-label">当前Latent文件</span>
            </div>
          </div>
        </div>
      </div>

      <a-form-item label="参考音频文件" :required="!character.id">
        <a-upload-dragger
          v-model:fileList="character.audioFileList"
          :multiple="false"
          :before-upload="beforeAudioUpload"
          @change="handleAudioChange"
          accept=".wav,.mp3,.m4a,.flac"
          class="edit-upload"
        >
          <div class="upload-content">
            <svg
              width="40"
              height="40"
              viewBox="0 0 24 24"
              fill="#06b6d4"
              style="margin-bottom: 12px"
            >
              <path
                d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
              />
              <path
                d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"
              />
            </svg>
            <p style="font-size: 14px; color: #374151; margin: 0">
              {{ character.id ? '更换音频文件（可选）' : '上传音频文件' }}
            </p>
            <p style="font-size: 12px; color: #9ca3af; margin: 4px 0 0 0">
              支持 WAV, MP3, M4A, FLAC 格式
            </p>
          </div>
        </a-upload-dragger>
      </a-form-item>

      <a-form-item label="Latent特征文件" :required="!character.id">
        <div
          style="
            margin-bottom: 8px;
            padding: 8px 12px;
            background: #fef3cd;
            border: 1px solid #fde68a;
            border-radius: 6px;
            color: #92400e;
            font-size: 13px;
          "
        >
          ⚠️ MegaTTS3必需文件：需要与音频文件配对的.npy特征文件
        </div>
        <a-upload
          v-model:fileList="character.latentFileList"
          :multiple="false"
          :before-upload="beforeLatentUpload"
          @change="handleLatentChange"
          accept=".npy"
          :show-upload-list="false"
        >
          <a-button>
            <template #icon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path
                  d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
                />
              </svg>
            </template>
            {{ character.id ? '更换 .npy 文件（可选）' : '选择 .npy 文件' }}
          </a-button>
        </a-upload>

        <div v-if="character.latentFileInfo" class="file-info" style="margin-top: 12px">
          <div class="file-item">
            <svg width="16" height="16" viewBox="0 0 24 24" fill="#10b981">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z" />
            </svg>
            <div class="file-details">
              <div class="file-name">{{ character.latentFileInfo.name }}</div>
              <div class="file-meta">{{ character.latentFileInfo.size }}</div>
            </div>
          </div>
        </div>
      </a-form-item>

      <a-divider orientation="left">技术参数</a-divider>

      <a-form-item label="Time Step">
        <a-slider v-model:value="character.params.timeStep" :min="5" :max="100" :step="5" />
        <div class="param-display">{{ character.params.timeStep }} steps</div>
      </a-form-item>

      <a-form-item label="智能权重 (p_w)">
        <a-slider v-model:value="character.params.pWeight" :min="0" :max="2" :step="0.1" />
        <div class="param-display">{{ (character.params.pWeight || 1.0).toFixed(1) }}</div>
      </a-form-item>

      <a-form-item label="相似度权重 (t_w)">
        <a-slider v-model:value="character.params.tWeight" :min="0" :max="2" :step="0.1" />
        <div class="param-display">{{ (character.params.tWeight || 1.0).toFixed(1) }}</div>
      </a-form-item>

      <a-form-item label="质量评分">
        <a-rate v-model:value="character.quality" allow-half />
        <span style="margin-left: 12px; color: #6b7280">{{ character.quality }} 星</span>
      </a-form-item>

      <a-form-item label="状态">
        <a-radio-group v-model:value="character.status">
          <a-radio value="active">可用</a-radio>
          <a-radio value="training">训练中</a-radio>
          <a-radio value="inactive">未激活</a-radio>
        </a-radio-group>
      </a-form-item>

      <a-form-item label="标签颜色">
        <div class="color-picker">
          <div
            v-for="color in colorOptions"
            :key="color"
            class="color-option"
            :class="{ selected: character.color === color }"
            :style="{ background: color }"
            @click="character.color = color"
          ></div>
        </div>
      </a-form-item>
    </a-form>
  </a-drawer>
</template>

<script setup>
import { ref } from 'vue'
import { message } from 'ant-design-vue'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  character: {
    type: Object,
    required: true
  },
  availableBooks: {
    type: Array,
    default: () => []
  },
  booksLoading: {
    type: Boolean,
    default: false
  },
  avatarGenerating: {
    type: Boolean,
    default: false
  },
  saving: {
    type: Boolean,
    default: false
  },
  editRules: {
    type: Object,
    default: () => ({})
  },
  colorOptions: {
    type: Array,
    default: () => [
      '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b', '#ef4444',
      '#ec4899', '#8b5cf6', '#06b6d4', '#10b981', '#f59e0b'
    ]
  }
})

// Emits
const emit = defineEmits([
  'close',
  'save',
  'generate-avatar',
  'remove-avatar',
  'book-search',
  'load-books',
  'play-audio'
])

// Refs
const editForm = ref(null)

// Methods
const beforeAvatarUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt10M = file.size / 1024 / 1024 < 10

  if (!isImage) {
    message.error('只能上传图片文件!')
    return false
  }
  if (!isLt10M) {
    message.error('图片大小不能超过 10MB!')
    return false
  }
  return false // 阻止自动上传到服务器，我们手动处理
}

// 暴露表单引用给父组件
defineExpose({
  editForm
})

const beforeAudioUpload = (file) => {
  const isAudio = file.type.startsWith('audio/') || file.name.match(/\.(wav|mp3|m4a|flac)$/i)
  const isLt50M = file.size / 1024 / 1024 < 50

  if (!isAudio) {
    message.error('只能上传音频文件!')
    return false
  }
  if (!isLt50M) {
    message.error('音频文件大小不能超过 50MB!')
    return false
  }
  return false
}

const beforeLatentUpload = (file) => {
  const isNpy = file.name.endsWith('.npy')
  const isLt100M = file.size / 1024 / 1024 < 100

  if (!isNpy) {
    message.error('只能上传 .npy 文件!')
    return false
  }
  if (!isLt100M) {
    message.error('文件大小不能超过 100MB!')
    return false
  }
  return false
}

const handleAvatarChange = (info) => {
  console.log('头像文件变化:', info)
  
  if (info.file.status === 'removed') {
    props.character.avatarFileList = []
    props.character.avatarFile = null
    props.character.avatarPreview = null
    props.character.removeAvatar = true
    return
  }
  
  // 处理头像文件上传
  if (info.file && (info.file.originFileObj || info.file)) {
    const file = info.file.originFileObj || info.file
    
    // 保存文件对象
    props.character.avatarFile = file
    
    // 更新文件列表，设置状态为done以显示成功状态
    const fileItem = {
      ...info.file,
      status: 'done',
      percent: 100
    }
    props.character.avatarFileList = [fileItem]
    
    // 创建预览URL
    const reader = new FileReader()
    reader.onload = (e) => {
      props.character.avatarPreview = e.target.result
    }
    reader.readAsDataURL(file)
    
    // 清除删除标记
    props.character.removeAvatar = false
    
    console.log('头像文件处理完成:', {
      fileName: file.name,
      fileSize: file.size,
      hasPreview: !!props.character.avatarPreview
    })
  }
}

const handleAudioChange = (info) => {
  if (info.file.status === 'removed') {
    props.character.audioFileList = []
    return
  }
  // 处理音频文件变化
}

const handleLatentChange = (info) => {
  if (info.file.status === 'removed') {
    props.character.latentFileList = []
    return
  }
  // 处理latent文件变化
}
</script>

<style scoped>
.voice-edit-form {
  height: 100%;
  overflow-y: auto;
}

.avatar-upload-section {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.current-avatar-preview {
  flex-shrink: 0;
}

.avatar-preview,
.avatar-placeholder {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  border: 2px solid #e5e7eb;
  overflow: hidden;
}

.avatar-image {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.upload-tips {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.current-files-section {
  margin-bottom: 24px;
}

.current-file-item {
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
  margin-bottom: 8px;
}

.file-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.file-header {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-label {
  font-weight: 500;
  color: #374151;
}

.file-actions {
  display: flex;
  gap: 8px;
}

.edit-upload {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
}

.upload-content {
  text-align: center;
  padding: 24px;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px;
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  border-radius: 6px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #166534;
}

.file-meta {
  font-size: 12px;
  color: #16a34a;
}

.param-display {
  text-align: center;
  margin-top: 8px;
  padding: 4px 8px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 12px;
  color: #6b7280;
}

.color-picker {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.color-option {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.2s;
}

.color-option:hover {
  transform: scale(1.1);
}

.color-option.selected {
  border-color: #1f2937;
  transform: scale(1.1);
}

/* 暗黑模式适配 */
[data-theme='dark'] .voice-edit-form {
  color: #d1d5db;
}

[data-theme='dark'] .avatar-preview,
[data-theme='dark'] .avatar-placeholder {
  border-color: #434343;
}

[data-theme='dark'] .upload-tips {
  color: #9ca3af;
}

[data-theme='dark'] .current-file-item {
  background: #1f1f1f;
  border-color: #434343;
}

[data-theme='dark'] .file-label {
  color: #d1d5db;
}

[data-theme='dark'] .edit-upload {
  border-color: #434343;
  background: #1f1f1f;
}

[data-theme='dark'] .file-item {
  background: #064e3b;
  border-color: #10b981;
}

[data-theme='dark'] .file-name {
  color: #34d399;
}

[data-theme='dark'] .file-meta {
  color: #6ee7b7;
}

[data-theme='dark'] .param-display {
  background: #374151;
  color: #9ca3af;
}

[data-theme='dark'] .color-option.selected {
  border-color: #f9fafb;
}
</style>