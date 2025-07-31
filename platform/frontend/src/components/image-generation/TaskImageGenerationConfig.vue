<template>
  <div class="task-image-generation-config">
    <!-- 配置头部 -->
    <div class="config-header">
      <h3>🎯 任务生成配置</h3>
      <p>此配置仅适用于当前生成任务，会继承书籍的通用配置</p>
    </div>

    <!-- 角色一致性配置 -->
    <div class="config-section">
      <CharacterConsistencyConfig
        v-model:config="characterConsistency"
        :available-characters="availableCharacters"
        :loading-characters="loadingCharacters"
        :selected-character-info="selectedCharacterInfo"
        @character-select="onCharacterSelect"
        @search-characters="searchCharacters"
        @toggle="onCharacterConsistencyToggle"
      />
    </div>

    <!-- 任务特定参数覆盖 -->
    <a-collapse v-model:activeKey="overridePanelKey" ghost>
      <a-collapse-panel key="override" header="🔧 参数覆盖">
        <div class="override-info">
          <a-alert
            message="参数覆盖说明"
            description="以下参数将覆盖书籍通用配置，仅对当前任务生效。留空则使用书籍默认配置。"
            type="info"
            show-icon
            style="margin-bottom: 16px"
          />
        </div>

        <!-- 风格覆盖 -->
        <div class="param-item">
          <label>
            <a-checkbox v-model:checked="overrides.style.enabled">
              覆盖艺术风格
            </a-checkbox>
          </label>
          <a-select
            v-model:value="overrides.style.value"
            :disabled="!overrides.style.enabled"
            style="width: 100%"
            placeholder="使用书籍默认配置"
          >
            <a-select-option value="cinematic">电影风格</a-select-option>
            <a-select-option value="historical">古风写实</a-select-option>
            <a-select-option value="portrait">人物特写</a-select-option>
            <a-select-option value="fantasy">奇幻风格</a-select-option>
            <a-select-option value="anime">动漫风格</a-select-option>
          </a-select>
        </div>

        <!-- 步数覆盖 -->
        <div class="param-item">
          <label>
            <a-checkbox v-model:checked="overrides.steps.enabled">
              覆盖采样步数
            </a-checkbox>
          </label>
          <a-slider
            v-model:value="overrides.steps.value"
            :disabled="!overrides.steps.enabled"
            :min="10"
            :max="50"
            :step="5"
            :marks="{ 10: '10', 20: '20', 30: '30', 50: '50' }"
          />
          <div class="param-value" v-if="overrides.steps.enabled">
            {{ overrides.steps.value }} 步
          </div>
        </div>

        <!-- 引导强度覆盖 -->
        <div class="param-item">
          <label>
            <a-checkbox v-model:checked="overrides.guidance.enabled">
              覆盖引导强度
            </a-checkbox>
          </label>
          <a-slider
            v-model:value="overrides.guidance.value"
            :disabled="!overrides.guidance.enabled"
            :min="1.0"
            :max="5.0"
            :step="0.1"
            :marks="{ 1.0: '1.0', 2.5: '2.5', 5.0: '5.0' }"
          />
          <div class="param-value" v-if="overrides.guidance.enabled">
            {{ overrides.guidance.value.toFixed(1) }}
          </div>
        </div>

        <!-- 种子覆盖 -->
        <div class="param-item">
          <label>
            <a-checkbox v-model:checked="overrides.seed.enabled">
              覆盖随机种子
            </a-checkbox>
          </label>
          <a-input-number
            v-model:value="overrides.seed.value"
            :disabled="!overrides.seed.enabled"
            placeholder="留空为随机"
            style="width: 100%"
            :min="-1"
            :max="2147483647"
          />
        </div>
      </a-collapse-panel>
    </a-collapse>

    <!-- 操作按钮 -->
    <div class="action-buttons">
      <a-space style="width: 100%">
        <a-button @click="resetOverrides" style="flex: 1">
          清除覆盖
        </a-button>
        <a-button 
          type="primary" 
          @click="handleApply"
          style="flex: 1"
        >
          应用配置
        </a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { message } from 'ant-design-vue'
import CharacterConsistencyConfig from './CharacterConsistencyConfig.vue'

// Props
const props = defineProps({
  bookConfig: {
    type: Object,
    default: () => ({})
  },
  taskConfig: {
    type: Object,
    default: () => ({})
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
const emit = defineEmits([
  'update:task-config', 
  'character-select', 
  'search-characters', 
  'apply'
])

// 响应式数据
const overridePanelKey = ref([])
const selectedCharacterInfo = ref(null)

// 角色一致性配置
const characterConsistency = reactive({
  enabled: false,
  selectedCharacterId: null,
  weight: 0.6,
  referenceImage: null
})

// 参数覆盖配置
const overrides = reactive({
  style: {
    enabled: false,
    value: 'cinematic'
  },
  steps: {
    enabled: false,
    value: 20
  },
  guidance: {
    enabled: false,
    value: 2.5
  },
  seed: {
    enabled: false,
    value: null
  }
})

// 监听任务配置变化
watch(() => props.taskConfig, (newConfig) => {
  if (newConfig) {
    // 更新角色一致性配置
    if (newConfig.characterConsistency) {
      Object.assign(characterConsistency, newConfig.characterConsistency)
    }
    
    // 更新参数覆盖配置
    if (newConfig.overrides) {
      Object.assign(overrides, newConfig.overrides)
    }
  }
}, { deep: true, immediate: true })

// 监听配置变化，同步到外部
watch([characterConsistency, overrides], () => {
  const taskConfig = {
    characterConsistency: { ...characterConsistency },
    overrides: { ...overrides }
  }
  emit('update:task-config', taskConfig)
}, { deep: true })

// 计算最终的生成配置
const finalConfig = computed(() => {
  const config = { ...props.bookConfig }
  
  // 应用参数覆盖
  Object.keys(overrides).forEach(key => {
    if (overrides[key].enabled) {
      config[key] = overrides[key].value
    }
  })
  
  // 添加角色一致性配置
  if (characterConsistency.enabled) {
    config.characterConsistency = { ...characterConsistency }
  }
  
  return config
})

// 方法定义
const onCharacterSelect = (characterId) => {
  characterConsistency.selectedCharacterId = characterId
  emit('character-select', characterId)
}

const searchCharacters = (searchText) => {
  emit('search-characters', searchText)
}

const onCharacterConsistencyToggle = (enabled) => {
  characterConsistency.enabled = enabled
  if (!enabled) {
    characterConsistency.selectedCharacterId = null
    characterConsistency.referenceImage = null
    selectedCharacterInfo.value = null
  }
}

const resetOverrides = () => {
  Object.keys(overrides).forEach(key => {
    overrides[key].enabled = false
  })
  message.success('已清除所有参数覆盖')
}

const handleApply = () => {
  emit('apply', finalConfig.value)
}
</script>

<style scoped lang="less">
.task-image-generation-config {
  .config-header {
    margin-bottom: 24px;
    padding: 16px;
    background: linear-gradient(135deg, #fff7e6 0%, #fef3e2 100%);
    border-radius: 8px;
    border-left: 4px solid #fa8c16;
    
    h3 {
      margin: 0 0 8px 0;
      color: #fa8c16;
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
  }

  .override-info {
    margin-bottom: 16px;
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
      color: #fa8c16;
      font-weight: 500;
    }
  }

  .action-buttons {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
}
</style>