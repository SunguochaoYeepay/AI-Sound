<template>
  <div class="flux-kontext-config">
    <!-- 预设选择 -->
    <div class="config-section">
      <h3>🎭 生成预设</h3>
      <a-select
        v-model:value="selectedPresetId"
        placeholder="选择生成预设"
        style="width: 100%"
        @change="onPresetChange"
      >
        <a-select-option
          v-for="preset in presets"
          :key="preset.id"
          :value="preset.id"
        >
          <div class="preset-option">
            <div class="preset-name">{{ preset.name }}</div>
            <div class="preset-desc">{{ preset.description }}</div>
          </div>
        </a-select-option>
      </a-select>
    </div>

    <!-- 生成参数 -->
    <div class="config-section">
      <h3>⚙️ 生成参数</h3>
      
      <!-- 风格选择 -->
      <div class="param-item">
        <label>艺术风格</label>
        <a-select
          v-model:value="localConfig.style"
          style="width: 100%"
        >
          <a-select-option value="cinematic">电影风格</a-select-option>
          <a-select-option value="historical">古风写实</a-select-option>
          <a-select-option value="portrait">人物特写</a-select-option>
          <a-select-option value="fantasy">奇幻风格</a-select-option>
          <a-select-option value="anime">动漫风格</a-select-option>
        </a-select>
      </div>

      <!-- 采样步数 -->
      <div class="param-item">
        <label>采样步数</label>
        <a-slider
          v-model:value="localConfig.steps"
          :min="10"
          :max="50"
          :step="5"
          :marks="{ 10: '10', 20: '20', 30: '30', 50: '50' }"
        />
        <div class="param-value">{{ localConfig.steps }} 步</div>
      </div>

      <!-- Flux引导强度 -->
      <div class="param-item">
        <label>引导强度</label>
        <a-slider
          v-model:value="localConfig.guidance"
          :min="1.0"
          :max="5.0"
          :step="0.1"
          :marks="{ 1.0: '1.0', 2.5: '2.5', 5.0: '5.0' }"
        />
        <div class="param-value">{{ localConfig.guidance.toFixed(1) }}</div>
      </div>
    </div>

    <!-- FluxKontext特有功能 -->
    <div class="config-section">
      <h3>🎨 FluxKontext 特性</h3>
      
      <!-- 角色一致性 -->
      <div class="param-item">
        <a-switch
          v-model:checked="localConfig.enableCharacterConsistency"
          checked-children="开启"
          un-checked-children="关闭"
        />
        <label style="margin-left: 8px">角色一致性</label>
        <div class="param-desc">
          使用参考图像保持角色外观一致
        </div>
      </div>

      <!-- 参考图像上传 -->
      <div class="param-item" v-if="localConfig.enableCharacterConsistency">
        <label>参考图像</label>
        <a-upload
          v-model:file-list="referenceImageList"
          :before-upload="beforeUpload"
          :remove="removeReferenceImage"
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
    </div>

    <!-- 模型信息 -->
    <div class="config-section">
      <h3>🚀 模型信息</h3>
      <div class="model-info">
        <div class="model-item">
          <strong>模型:</strong> {{ localConfig.model }}
        </div>
        <div class="model-item">
          <strong>类型:</strong> FluxKontext (专业级)
        </div>
        <div class="model-item">
          <strong>优势:</strong> 高质量、自然语言理解、电影级效果
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <a-space style="width: 100%">
        <a-button @click="resetToDefault" style="flex: 1">
          重置默认
        </a-button>
        <a-button 
          type="primary" 
          @click="handleSave"
          style="flex: 1"
        >
          保存配置
        </a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { message } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  presets: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['update:config', 'preset-change', 'save'])

// 响应式数据
const selectedPresetId = ref(null)
const referenceImageList = ref([])

// 本地配置副本
const localConfig = reactive({
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
const onPresetChange = (presetId) => {
  const preset = props.presets.find(p => p.id === presetId)
  if (preset) {
    Object.assign(localConfig, preset.config)
    emit('preset-change', preset)
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
  
  // 转换为base64用于预览
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

const resetToDefault = () => {
  const defaultConfig = {
    style: 'cinematic',
    steps: 20,
    guidance: 2.5,
    model: 'flux1-dev-kontext_fp8_scaled',
    enableCharacterConsistency: false,
    referenceImage: null
  }
  
  Object.assign(localConfig, defaultConfig)
  selectedPresetId.value = null
  referenceImageList.value = []
  
  message.success('已重置为默认配置')
}

const handleSave = () => {
  emit('save')
}
</script>

<style scoped lang="less">
.flux-kontext-config {
  .config-section {
    margin-bottom: 24px;
    
    h3 {
      margin-bottom: 16px;
      color: #1890ff;
      font-size: 16px;
      font-weight: 600;
    }
  }

  .preset-option {
    .preset-name {
      font-weight: 600;
      color: #262626;
    }
    
    .preset-desc {
      font-size: 12px;
      color: #8c8c8c;
      margin-top: 2px;
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
      text-align: center;
      margin-top: 4px;
      font-size: 12px;
      color: #1890ff;
      font-weight: 500;
    }
    
    .param-desc {
      margin-top: 4px;
      font-size: 12px;
      color: #8c8c8c;
      line-height: 1.4;
    }
  }

  .model-info {
    background: #f5f5f5;
    padding: 12px;
    border-radius: 6px;
    
    .model-item {
      margin-bottom: 8px;
      font-size: 13px;
      
      &:last-child {
        margin-bottom: 0;
      }
      
      strong {
        color: #262626;
        margin-right: 8px;
      }
    }
  }

  .action-buttons {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
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