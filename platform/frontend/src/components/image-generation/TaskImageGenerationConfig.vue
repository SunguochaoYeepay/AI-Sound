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



    <!-- 操作按钮 -->
    <div class="action-buttons">
      <a-button 
        type="primary" 
        @click="handleApply"
        style="width: 100%"
      >
        应用配置
      </a-button>
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
const selectedCharacterInfo = ref(null)

// 角色一致性配置
const characterConsistency = reactive({
  enabled: false,
  selectedCharacterId: null,
  weight: 0.6,
  referenceImage: null
})

// 监听任务配置变化
watch(() => props.taskConfig, (newConfig) => {
  if (newConfig) {
    // 更新角色一致性配置
    if (newConfig.characterConsistency) {
      Object.assign(characterConsistency, newConfig.characterConsistency)
    }
  }
}, { deep: true, immediate: true })

// 监听配置变化，同步到外部
watch(characterConsistency, () => {
  const taskConfig = {
    characterConsistency: { ...characterConsistency }
  }
  emit('update:task-config', taskConfig)
}, { deep: true })

// 计算最终的生成配置
const finalConfig = computed(() => {
  const config = { ...props.bookConfig }
  
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

  .action-buttons {
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
}
</style>