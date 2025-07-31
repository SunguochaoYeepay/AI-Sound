<template>
  <div class="book-image-generation-config">
    <!-- 配置头部 -->    
    <div class="config-header">
      <h3>📚 书籍通用配置</h3>
      <p>此配置将作为该书籍所有图片生成任务的默认设置</p>
    </div>

    <!-- 预设选择 -->
    <div class="config-section">
      <h4>🎭 生成预设</h4>
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

    <!-- 基础参数 -->
    <div class="config-section">
      <h4>⚙️ 基础参数</h4>
      
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

      <!-- 质量等级 -->
      <div class="param-item">
        <label>生成质量</label>
        <a-radio-group v-model:value="qualityLevel" @change="onQualityChange">
          <a-radio-button value="fast">快速 (10步)</a-radio-button>
          <a-radio-button value="balanced">平衡 (20步)</a-radio-button>
          <a-radio-button value="high">高质量 (30步)</a-radio-button>
        </a-radio-group>
      </div>
    </div>

    <!-- 高级参数折叠面板 -->
    <a-collapse v-model:activeKey="advancedPanelKey" ghost>
      <a-collapse-panel key="advanced" header="🔧 高级参数">
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
        
        <!-- 模型选择 -->
        <div class="param-item">
          <label>生成模型</label>
          <a-select
            v-model:value="localConfig.model"
            style="width: 100%"
          >
            <a-select-option value="flux1-dev-kontext_fp8_scaled">FluxKontext (推荐)</a-select-option>
            <a-select-option value="flux1-dev">Flux Dev</a-select-option>
            <a-select-option value="flux1-schnell">Flux Schnell (快速)</a-select-option>
          </a-select>
        </div>
        
        <!-- 种子值 -->
        <div class="param-item">
          <label>随机种子</label>
          <a-input-number
            v-model:value="localConfig.seed"
            placeholder="留空为随机"
            style="width: 100%"
            :min="-1"
            :max="2147483647"
          />
          <div class="param-desc">
            固定种子可以重现相同的生成结果
          </div>
        </div>

        <!-- 批次大小 -->
        <div class="param-item">
          <label>批次大小</label>
          <a-input-number
            v-model:value="localConfig.batchSize"
            :min="1"
            :max="4"
            style="width: 100%"
          />
          <div class="param-desc">
            每次生成的图片数量，建议保持为1
          </div>
        </div>
      </a-collapse-panel>
    </a-collapse>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <a-space style="width: 100%">
        <a-button @click="resetToDefault" style="flex: 1">
          重置默认
        </a-button>
        <a-button 
          type="primary" 
          @click="handleSave"
          :loading="saving"
          style="flex: 1"
        >
          保存配置
        </a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed, onMounted } from 'vue'
import { message } from 'ant-design-vue'

// Props
const props = defineProps({
  bookId: {
    type: Number,
    required: true
  },
  config: {
    type: Object,
    default: () => ({})
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
const qualityLevel = ref('balanced')
const advancedPanelKey = ref([])
const saving = ref(false)

// 默认配置
const defaultConfig = {
  style: 'cinematic',
  steps: 20,
  guidance: 2.5,
  model: 'flux1-dev-kontext_fp8_scaled',
  seed: null,
  batchSize: 1
}

// 本地配置副本
const localConfig = reactive({
  ...defaultConfig,
  ...props.config
})

// 根据步数设置质量等级
const updateQualityLevel = () => {
  if (localConfig.steps <= 15) {
    qualityLevel.value = 'fast'
  } else if (localConfig.steps <= 25) {
    qualityLevel.value = 'balanced'
  } else {
    qualityLevel.value = 'high'
  }
}

// 监听外部配置变化
watch(() => props.config, (newConfig) => {
  Object.assign(localConfig, defaultConfig, newConfig)
  updateQualityLevel()
}, { deep: true, immediate: true })

// 监听本地配置变化，同步到外部
watch(localConfig, (newConfig) => {
  emit('update:config', { ...newConfig })
}, { deep: true })

// 监听步数变化，更新质量等级
watch(() => localConfig.steps, () => {
  updateQualityLevel()
})

// 方法定义
const onPresetChange = (presetId) => {
  const preset = props.presets.find(p => p.id === presetId)
  if (preset) {
    Object.assign(localConfig, preset.config)
    emit('preset-change', preset)
  }
}

const onQualityChange = (e) => {
  const level = e.target.value
  switch (level) {
    case 'fast':
      localConfig.steps = 10
      localConfig.guidance = 2.0
      break
    case 'balanced':
      localConfig.steps = 20
      localConfig.guidance = 2.5
      break
    case 'high':
      localConfig.steps = 30
      localConfig.guidance = 3.0
      break
  }
}

const resetToDefault = () => {
  Object.assign(localConfig, defaultConfig)
  selectedPresetId.value = null
  message.success('已重置为默认配置')
}

const handleSave = () => {
  saving.value = true
  emit('save')
  // 保存状态将由父组件控制
  setTimeout(() => {
    saving.value = false
  }, 1000)
}

// 组件挂载时初始化质量等级
onMounted(() => {
  updateQualityLevel()
})
</script>

<style scoped lang="less">
.book-image-generation-config {
  .config-header {
    margin-bottom: 24px;
    padding: 16px;
    background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
    border-radius: 8px;
    border-left: 4px solid #1890ff;
    
    h3 {
      margin: 0 0 8px 0;
      color: #1890ff;
      font-size: 16px;
      font-weight: 600;
    }
    
    p {
      margin: 0;
      color: #666;
      font-size: 14px;
      line-height: 1.5;
    }
  }

  .config-section {
    margin-bottom: 24px;
    
    h4 {
      margin-bottom: 16px;
      color: #1890ff;
      font-size: 14px;
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

  .action-buttons {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
}

/* 暗黑模式适配 */
[data-theme='dark'] .book-image-generation-config {
  .config-header {
    background: linear-gradient(135deg, #111b26 0%, #0f172a 100%);
    border-left-color: #177ddc;
    
    h3 {
      color: #177ddc;
    }
    
    p {
      color: #d9d9d9;
    }
  }

  .config-section {
    h4 {
      color: #177ddc;
    }
  }

  .preset-option {
    .preset-name {
      color: #d9d9d9;
    }
    
    .preset-desc {
      color: #8c8c8c;
    }
  }

  .param-item {
    label {
      color: #d9d9d9;
    }
    
    .param-value {
      color: #177ddc;
    }
    
    .param-desc {
      color: #8c8c8c;
    }
  }

  .action-buttons {
    border-top-color: #303030;
  }
}
</style>