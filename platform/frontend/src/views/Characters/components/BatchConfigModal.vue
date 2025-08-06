<template>
  <a-modal
    :open="visible"
    title="批量配置角色"
    width="800px"
    :footer="null"
    @cancel="$emit('close')"
  >
    <div class="batch-config-content">
      <!-- 步骤指示器 -->
      <a-steps :current="currentStep - 1" class="batch-steps">
        <a-step title="选择角色" description="确认要配置的角色" />
        <a-step title="配置文件" description="上传音频、NPY和头像文件" />
      </a-steps>

      <!-- 第一步：选择角色 -->
      <div v-if="currentStep === 1" class="batch-step-content">
        <div class="selected-characters-info">
          <h3>已选择 {{ selectedCount }} 个角色</h3>
          <div class="character-list">
            <div 
              v-for="character in selectedCharacters"
              :key="character.id"
              class="character-item"
            >
              <div class="character-avatar">
                <div 
                  class="avatar-icon"
                  :style="{ background: character.avatarUrl ? 'transparent' : character.color }"
                >
                  <img
                    v-if="character.avatarUrl"
                    :src="character.avatarUrl"
                    :alt="character.name"
                    class="avatar-image"
                  />
                  <span v-else>{{ character.name.charAt(0) }}</span>
                </div>
              </div>
              <div class="character-info">
                <div class="character-name">{{ character.name }}</div>
                <div class="character-desc">{{ character.description || '暂无描述' }}</div>
              </div>
            </div>
          </div>
        </div>
        
        <div class="step-actions">
          <a-button @click="$emit('close')">取消</a-button>
          <a-button type="primary" @click="$emit('next-step')" :disabled="selectedCount === 0">
            下一步
          </a-button>
        </div>
      </div>

      <!-- 第二步：配置文件 -->
      <div v-if="currentStep === 2" class="batch-step-content">
        <a-form layout="vertical">
          <a-form-item label="音频文件配置">
                         <a-checkbox :checked="configData.applyToAll.audio" @change="$emit('update:configData', { ...configData, applyToAll: { ...configData.applyToAll, audio: $event.target.checked } })">
               为所有选中角色应用相同的音频文件
             </a-checkbox>
             <div v-if="configData.applyToAll.audio" class="file-upload-section">
               <a-upload
                 :file-list="configData.audioFileList"
                 :before-upload="() => false"
                 @change="handleAudioChange"
                 accept=".wav,.mp3,.m4a,.flac,.ogg"
                 :max-count="1"
               >
                <a-button>
                  <template #icon><UploadOutlined /></template>
                  选择音频文件
                </a-button>
              </a-upload>
              <div class="upload-tips">
                <small>支持 WAV、MP3、M4A、FLAC、OGG 格式，建议使用高质量音频</small>
              </div>
            </div>
          </a-form-item>

          <a-form-item label="NPY特征文件配置">
                         <a-checkbox :checked="configData.applyToAll.npy" @change="$emit('update:configData', { ...configData, applyToAll: { ...configData.applyToAll, npy: $event.target.checked } })">
               为所有选中角色应用相同的NPY特征文件
             </a-checkbox>
             <div v-if="configData.applyToAll.npy" class="file-upload-section">
               <a-upload
                 :file-list="configData.npyFileList"
                 :before-upload="() => false"
                 @change="handleNpyChange"
                 accept=".npy"
                 :max-count="1"
               >
                <a-button>
                  <template #icon><UploadOutlined /></template>
                  选择NPY文件
                </a-button>
              </a-upload>
              <div class="upload-tips">
                <small>NPY特征文件用于语音克隆，提高合成质量</small>
              </div>
            </div>
          </a-form-item>

          <a-form-item label="头像配置">
                         <a-checkbox :checked="configData.applyToAll.avatar" @change="$emit('update:configData', { ...configData, applyToAll: { ...configData.applyToAll, avatar: $event.target.checked } })">
               为所有选中角色应用相同的头像
             </a-checkbox>
             <div v-if="configData.applyToAll.avatar" class="file-upload-section">
               <a-upload
                 :file-list="configData.avatarFileList"
                 :before-upload="() => false"
                 @change="handleAvatarChange"
                 accept=".jpg,.jpeg,.png,.webp"
                 :max-count="1"
                 list-type="picture-card"
               >
                <div>
                  <UploadOutlined />
                  <div style="margin-top: 8px">上传头像</div>
                </div>
              </a-upload>
              <div class="upload-tips">
                <small>支持 JPG、PNG、WebP 格式，建议尺寸 512x512</small>
              </div>
            </div>
          </a-form-item>
        </a-form>
        
        <div class="step-actions">
          <a-button @click="$emit('prev-step')">上一步</a-button>
          <a-button @click="$emit('close')">取消</a-button>
          <a-button 
            type="primary" 
            @click="$emit('execute')"
            :loading="loading"
            :disabled="!configData.applyToAll.audio && !configData.applyToAll.npy && !configData.applyToAll.avatar"
          >
            开始配置
          </a-button>
        </div>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { UploadOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  currentStep: {
    type: Number,
    default: 1
  },
  selectedCount: {
    type: Number,
    default: 0
  },
  selectedCharacters: {
    type: Array,
    default: () => []
  },
  configData: {
    type: Object,
    default: () => ({
      audioFile: null,
      audioFileList: [],
      npyFile: null,
      npyFileList: [],
      avatarFile: null,
      avatarFileList: [],
      applyToAll: {
        audio: false,
        npy: false,
        avatar: false
      }
    })
  },
  loading: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits(['close', 'next-step', 'prev-step', 'execute', 'audio-change', 'npy-change', 'avatar-change', 'update:configData'])

const handleAudioChange = (info) => {
  emit('audio-change', info)
}

const handleNpyChange = (info) => {
  emit('npy-change', info)
}

const handleAvatarChange = (info) => {
  emit('avatar-change', info)
}
</script>

<style scoped>
.batch-config-content {
  padding: 16px 0;
}

.batch-steps {
  margin-bottom: 24px;
}

.batch-step-content {
  min-height: 300px;
}

.selected-characters-info h3 {
  margin-bottom: 16px;
  color: #1890ff;
}

.character-list {
  max-height: 300px;
  overflow-y: auto;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  padding: 8px;
}

.character-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px;
  border-radius: 4px;
  margin-bottom: 8px;
  background: #fafafa;
}

.character-item:last-child {
  margin-bottom: 0;
}

.character-item .character-avatar {
  flex-shrink: 0;
}

.character-item .avatar-icon {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 14px;
}

.character-item .avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.character-item .character-info {
  flex: 1;
  min-width: 0;
}

.character-item .character-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.character-item .character-desc {
  font-size: 12px;
  color: #666;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.file-upload-section {
  margin-top: 12px;
  padding: 12px;
  background: #f9f9f9;
  border-radius: 6px;
}

.upload-tips {
  margin-top: 8px;
  color: #666;
}

.step-actions {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
}

/* 暗黑模式适配 */
[data-theme='dark'] .character-list {
  border-color: #434343;
  background: #1f1f1f;
}

[data-theme='dark'] .character-item {
  background: #2d2d2d;
}

[data-theme='dark'] .character-item .character-name {
  color: #fff;
}

[data-theme='dark'] .character-item .character-desc {
  color: #8c8c8c;
}

[data-theme='dark'] .file-upload-section {
  background: #2d2d2d;
}

[data-theme='dark'] .step-actions {
  border-top-color: #434343;
}

[data-theme='dark'] .upload-tips {
  color: #8c8c8c;
}
</style> 