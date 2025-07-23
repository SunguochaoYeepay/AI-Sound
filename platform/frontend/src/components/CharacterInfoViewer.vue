<template>
  <div class="characters-view">
    <div class="characters-header">
      <div class="characters-title">
        <h4>智能识别的角色 (共{{ characters.length }}个)</h4>
        <span class="character-stats"> 总片段: {{ totalSegments }}个 </span>
      </div>

      <!-- 批量角色管理操作 -->
      <div class="characters-actions">
        <a-space>
          <a-tag v-if="missingCharactersCount > 0" color="orange" size="small">
            📝 {{ missingCharactersCount }} 个角色待添加到配音库
          </a-tag>
          <a-button
            v-if="missingCharactersCount > 0"
            type="primary"
            size="small"
            @click="handleBatchCreateClick"
            :loading="batchCreating"
            style="pointer-events: auto; z-index: 1000;"
          >
            🎭 批量添加到配音库
          </a-button>
          <a-button
            size="small"
            @click="$emit('refresh-library')"
            :loading="loadingBookCharacters"
          >
            🔄 刷新配音库
          </a-button>
        </a-space>
      </div>
    </div>

    <div class="characters-grid">
      <div
        v-for="(character, index) in characters"
        :key="index"
        class="character-card"
      >
        <!-- 角色头像和基本信息 -->
        <div class="character-header">
          <div class="character-avatar">
            <a-avatar
              :size="48"
              :src="getCharacterAvatar(character)"
              :style="{ backgroundColor: getCharacterColor(character.name) }"
            >
              {{ getCharacterInitial(character.name) }}
            </a-avatar>
          </div>

          <div class="character-info">
            <div class="character-name">
              <span class="name-text">{{ character.name }}</span>
              <span class="character-rank">
                {{ getCharacterRank(character, index) }}
              </span>
            </div>
            <div class="character-tags">
              <a-tag :color="getCharacterTypeColor(character.voice_type)" size="small">
                {{ getCharacterTypeText(character.voice_type) }}
              </a-tag>
              <a-tag color="blue" size="small"> 第{{ index + 1 }}位 </a-tag>
              <a-tag :color="getCharacterStatusColor(character)" size="small">
                {{ getCharacterStatusText(character) }}
              </a-tag>
              <a-tag v-if="character.in_character_library" color="green" size="small">
                📚 配音库
              </a-tag>
              <a-tag v-else color="orange" size="small"> ❓ 待添加 </a-tag>
            </div>
          </div>
        </div>

        <!-- 角色统计信息 -->
        <div class="character-stats-detail">
          <a-row :gutter="8">
            <a-col :span="12">
              <a-statistic
                title="出现次数"
                :value="character.count || 0"
                :value-style="{ fontSize: '16px', color: '#1890ff' }"
              />
            </a-col>
            <a-col :span="12">
              <a-statistic
                title="占比"
                :value="getCharacterPercentage(character)"
                suffix="%"
                :value-style="{ fontSize: '16px', color: '#52c41a' }"
              />
            </a-col>
          </a-row>
        </div>

        <!-- 角色操作按钮 -->
        <div class="character-actions">
          <a-space>
            <a-button
              size="small"
              @click="handleTestVoice(character)"
              :loading="testingVoice === character.name"
            >
              🔊 试听
            </a-button>
          </a-space>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, ref } from 'vue'
import { message } from 'ant-design-vue'
import { playVoicePreview } from '@/utils/audioService'

// Props
const props = defineProps({
  characters: {
    type: Array,
    default: () => []
  },
  totalSegments: {
    type: Number,
    default: 0
  },
  batchCreating: {
    type: Boolean,
    default: false
  },
  loadingBookCharacters: {
    type: Boolean,
    default: false
  }
})

// 本地状态
const testingVoice = ref(null)

// Emits
const emit = defineEmits([
  'batch-create',
  'refresh-library'
])

// 计算属性
const missingCharactersCount = computed(() => {
  return props.characters.filter(char => !char.in_character_library).length
})

// 方法
const handleBatchCreateClick = () => {
  console.log('[CharacterInfoViewer] 批量创建按钮被点击')
  console.log('[CharacterInfoViewer] missingCharactersCount:', missingCharactersCount.value)
  console.log('[CharacterInfoViewer] characters:', props.characters)
  console.log('[CharacterInfoViewer] 缺失的角色:', props.characters.filter(char => !char.in_character_library))
  console.log('[CharacterInfoViewer] batchCreating状态:', props.batchCreating)
  
  if (props.batchCreating) {
    console.log('[CharacterInfoViewer] 当前正在批量创建中，忽略点击')
    return
  }
  
  console.log('[CharacterInfoViewer] 发送batch-create事件')
  emit('batch-create')
}

// 试听角色声音
const handleTestVoice = async (character) => {
  if (testingVoice.value === character.name) {
    return // 防止重复点击
  }
  
  try {
    testingVoice.value = character.name
    
    // 检查角色是否有配置的声音
    if (!character.voice_id && !character.character_id) {
      message.warning(`角色"${character.name}"尚未配置声音，无法试听`)
      return
    }
    
    // 使用统一的播放组件播放角色声音
    await playVoicePreview(character.voice_id || character.character_id, character.name)
    
  } catch (error) {
    console.error('试听角色声音失败:', error)
    message.error(`试听角色"${character.name}"的声音失败`)
  } finally {
    testingVoice.value = null
  }
}

// 组件挂载时的调试信息
onMounted(() => {
  console.log('[CharacterInfoViewer] 组件已挂载')
  console.log('[CharacterInfoViewer] 初始characters:', props.characters)
  console.log('[CharacterInfoViewer] 初始missingCharactersCount:', missingCharactersCount.value)
})

// 工具方法
const getCharacterColor = (name) => {
  const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[hash % colors.length]
}

const getCharacterTypeColor = (type) => {
  const colors = {
    male: 'blue',
    female: 'pink',
    narrator: 'purple',
    neutral: 'default'
  }
  return colors[type] || 'default'
}

const getCharacterTypeText = (type) => {
  const texts = {
    male: '男性',
    female: '女性',
    narrator: '旁白',
    neutral: '中性'
  }
  return texts[type] || '未知'
}

const getCharacterPercentage = (character) => {
  if (props.totalSegments === 0) return 0
  return Math.round((character.count / props.totalSegments) * 100)
}

const getCharacterAvatar = (character) => {
  return character?.avatarUrl || null
}

const getCharacterInitial = (name) => {
  if (!name) return '?'
  if (name.includes('旁白')) return '📖'
  return name.charAt(0)
}

const getCharacterRank = (character, index) => {
  if (index === 0) return '👑主角'
  if (index === 1) return '⭐重要配角'
  if (index <= 3) return '✨一般配角'
  if (character.name.includes('旁白')) return '📖旁白'
  return '👤其他'
}

const getCharacterStatusColor = (character) => {
  if (!character?.in_character_library) return 'orange'
  if (character?.is_voice_configured) return 'green'
  return 'blue'
}

const getCharacterStatusText = (character) => {
  if (!character?.in_character_library) return '未在配音库'
  if (character?.is_voice_configured) return '✅ 已配置语音'
  return '🔧 在配音库中'
}
</script>

<style scoped>
.characters-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.characters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--ant-border-color-split);
}

.characters-title h4 {
  margin: 0;
  color: var(--ant-heading-color);
}

.character-stats {
  color: var(--ant-text-color-secondary);
  font-size: 14px;
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  overflow-y: auto;
  flex: 1;
}

.character-card {
  background: var(--ant-component-background);
  border: 1px solid var(--ant-border-color-split);
  border-radius: 8px;
  padding: 16px;
  transition: all 0.3s ease;
}

.character-card:hover {
  border-color: var(--ant-border-color-base);
  box-shadow: 0 2px 8px var(--ant-shadow-color);
}

.character-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.character-avatar {
  margin-right: 12px;
}

.character-info {
  flex: 1;
}

.character-name {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.name-text {
  font-size: 16px;
  font-weight: 500;
  color: var(--ant-heading-color);
  margin-right: 8px;
}

.character-rank {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
  background: var(--ant-background-color-base);
  padding: 2px 6px;
  border-radius: 4px;
}

.character-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

.character-stats-detail {
  margin: 12px 0;
  padding: 12px;
  background: var(--ant-background-color-base);
  border-radius: 6px;
}

.character-actions {
  display: flex;
  justify-content: center;
  margin-top: 12px;
}

.characters-actions {
  display: flex;
  align-items: center;
}
</style>