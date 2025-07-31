<template>
  <div class="character-consistency-config">
    <!-- 角色一致性开关 -->
    <div class="config-section">
      <h3>🎭 角色一致性</h3>
      <div class="param-item">
        <a-switch
          v-model:checked="localConfig.enabled"
          checked-children="开启"
          un-checked-children="关闭"
          @change="onToggleChange"
        />
        <label style="margin-left: 8px">启用角色一致性</label>
        <div class="param-desc">
          开启后，生成的图片将保持角色外观一致性
        </div>
      </div>
    </div>

    <!-- 角色选择和配置 -->
    <div class="config-section" v-if="localConfig.enabled">
      <h3>👤 角色选择</h3>
      
      <!-- 角色选择器 -->
      <div class="param-item">
        <label>选择角色</label>
        <a-select
          v-model:value="localConfig.selectedCharacterId"
          placeholder="选择要保持一致性的角色"
          style="width: 100%"
          :loading="loadingCharacters"
          show-search
          :filter-option="false"
          @search="searchCharacters"
          @change="onCharacterSelect"
        >
          <a-select-option 
            v-for="character in availableCharacters" 
            :key="character.id" 
            :value="character.id"
          >
            <div class="character-option">
              <img 
                v-if="character.avatar_url" 
                :src="character.avatar_url" 
                class="character-avatar-mini"
                alt="头像"
              />
              <div 
                v-else 
                class="character-avatar-placeholder"
                :style="{ background: character.color }"
              >
                {{ character.name[0] }}
              </div>
              <span class="character-name">{{ character.name }}</span>
              <a-tag v-if="character.consistency_tag" size="small" color="blue">
                {{ character.consistency_tag }}
              </a-tag>
            </div>
          </a-select-option>
        </a-select>
        <div class="param-desc">
          从已识别的角色中选择需要保持一致性的角色
        </div>
      </div>

      <!-- 一致性权重 -->
      <div class="param-item" v-if="localConfig.selectedCharacterId">
        <label>一致性权重</label>
        <a-slider
          v-model:value="localConfig.weight"
          :min="0.3"
          :max="1.0"
          :step="0.1"
          :marks="{ 0.3: '弱', 0.6: '中', 0.9: '强' }"
        />
        <div class="param-value">{{ localConfig.weight.toFixed(1) }}</div>
        <div class="param-desc">
          权重越高，角色特征越明显
        </div>
      </div>

      <!-- 参考图像上传 -->
      <div class="param-item">
        <label>参考图像</label>
        <a-upload
          v-model:file-list="referenceImageList"
          :before-upload="beforeUpload"
          @remove="removeReferenceImage"
          list-type="picture-card"
          :max-count="1"
        >
          <div v-if="referenceImageList.length < 1">
            <plus-outlined />
            <div style="margin-top: 8px">上传参考图</div>
          </div>
        </a-upload>
        <div class="param-desc">
          上传角色参考图像，系统会根据此图像保持角色一致性
        </div>
      </div>

      <!-- 角色信息预览 -->
      <div class="param-item" v-if="selectedCharacterInfo">
        <label>角色信息预览</label>
        <div class="character-info-preview">
          <a-descriptions :column="1" size="small">
            <a-descriptions-item label="角色名称">
              {{ selectedCharacterInfo.name }}
            </a-descriptions-item>
            <a-descriptions-item label="外貌描述" v-if="selectedCharacterInfo.appearance_description">
              {{ selectedCharacterInfo.appearance_description }}
            </a-descriptions-item>
            <a-descriptions-item label="特殊特征" v-if="selectedCharacterInfo.distinctive_features">
              {{ selectedCharacterInfo.distinctive_features }}
            </a-descriptions-item>
            <a-descriptions-item label="角色提示词" v-if="selectedCharacterInfo.avatar_prompt">
              <a-textarea 
                :value="selectedCharacterInfo.avatar_prompt"
                :rows="3"
                disabled
                style="background: #f5f5f5;"
              />
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'
import { useImageGenerationStore } from '@/stores/imageGeneration'

// Props
const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  availableCharacters: {
    type: Array,
    default: () => []
  },
  loadingCharacters: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:config', 'search-characters', 'character-select'])

// Store
const imageStore = useImageGenerationStore()

// 响应式数据
const referenceImageList = ref([])
const selectedCharacterInfo = ref(null)

// 本地配置副本
const localConfig = reactive({
  enabled: false,
  selectedCharacterId: null,
  weight: 0.6,
  referenceImage: null,
  ...props.config
})

// 监听外部配置变化
watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, newConfig)
}, { deep: true })

// 监听本地配置变化，同步到外部
watch(localConfig, (newConfig) => {
  emit('update:config', { ...newConfig })
}, { deep: true })

// 方法定义
const onToggleChange = (enabled) => {
  if (!enabled) {
    // 关闭时清空相关配置
    localConfig.selectedCharacterId = null
    localConfig.referenceImage = null
    selectedCharacterInfo.value = null
    referenceImageList.value = []
  }
}

const searchCharacters = (searchText) => {
  emit('search-characters', searchText)
}

const onCharacterSelect = async (characterId) => {
  if (characterId) {
    try {
      // 获取角色详细信息
      const character = props.availableCharacters.find(c => c.id === characterId)
      if (character) {
        selectedCharacterInfo.value = character
        emit('character-select', character)
      }
    } catch (error) {
      console.error('获取角色信息失败:', error)
      message.error('获取角色信息失败')
    }
  } else {
    selectedCharacterInfo.value = null
  }
}

const beforeUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  if (!isImage) {
    message.error('只能上传图片文件!')
    return false
  }
  
  const isLt10M = file.size / 1024 / 1024 < 10
  if (!isLt10M) {
    message.error('图片大小不能超过 10MB!')
    return false
  }
  
  // 转换为base64
  const reader = new FileReader()
  reader.onload = (e) => {
    localConfig.referenceImage = e.target.result
  }
  reader.readAsDataURL(file)
  
  return false // 阻止自动上传
}

const removeReferenceImage = () => {
  localConfig.referenceImage = null
  referenceImageList.value = []
}
</script>

<style lang="less" scoped>
.character-consistency-config {
  .config-section {
    margin-bottom: 24px;
    
    h3 {
      margin-bottom: 16px;
      font-size: 16px;
      font-weight: 600;
      color: #262626;
      display: flex;
      align-items: center;
      gap: 8px;
    }
  }

  .param-item {
    margin-bottom: 16px;
    
    label {
      display: block;
      margin-bottom: 8px;
      font-weight: 500;
      color: #262626;
    }
    
    .param-value {
      margin-top: 8px;
      text-align: center;
      font-size: 12px;
      color: #666;
    }
    
    .param-desc {
      margin-top: 4px;
      font-size: 12px;
      color: #8c8c8c;
      line-height: 1.4;
    }
  }

  .character-option {
    display: flex;
    align-items: center;
    gap: 8px;
    
    .character-avatar-mini {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      object-fit: cover;
    }
    
    .character-avatar-placeholder {
      width: 24px;
      height: 24px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: 12px;
      font-weight: bold;
    }
    
    .character-name {
      flex: 1;
      font-size: 14px;
    }
  }

  .character-info-preview {
    background: #f8f9fa;
    border: 1px solid #e9ecef;
    border-radius: 6px;
    padding: 12px;
    
    :deep(.ant-descriptions-item-label) {
      font-weight: 500;
      color: #495057;
    }
    
    :deep(.ant-descriptions-item-content) {
      color: #6c757d;
    }
  }
}

:deep(.ant-upload-select-picture-card) {
  width: 80px;
  height: 80px;
}

:deep(.ant-upload-list-picture-card .ant-upload-list-item) {
  width: 80px;
  height: 80px;
}
</style>