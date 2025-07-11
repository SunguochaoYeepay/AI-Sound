<template>
  <div class="chapter-analysis">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载智能分析结果...">
        <div style="height: 300px;"></div>
      </a-spin>
    </div>

    <!-- 有分析数据 -->
    <div v-else-if="analysisData" class="analysis-content">
      <!-- 分析结果tabs -->
      <div class="analysis-tabs">
        <a-tabs v-model:activeKey="activeSubTab" type="card">
          <template #rightExtra>
            <a-space>
              <!-- 🔥 新增：缓存状态指示器 -->
              <a-tooltip>
                <template #title>
                  <div>
                    <div>数据来源: {{ getCacheStatusText() }}</div>
                    <div v-if="cacheInfo.user_edited">用户已编辑</div>
                    <div>最后更新: {{ getLastUpdateTime() }}</div>
                  </div>
                </template>
                <a-tag 
                  :color="getCacheStatusColor()" 
                  size="small"
                  style="cursor: help;"
                >
                  {{ getCacheStatusIcon() }} {{ getCacheStatusText() }}
                </a-tag>
              </a-tooltip>
              
              <!-- 🔥 新增：缓存控制按钮 -->
              <a-dropdown>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="refreshCache">
                      <ReloadOutlined />
                      强制刷新缓存
                    </a-menu-item>
                    <a-menu-item @click="clearEditCache">
                      <ClearOutlined />
                      清除编辑缓存
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item @click="clearAllCache" style="color: #ff4d4f;">
                      <DeleteOutlined />
                      清除所有缓存
                    </a-menu-item>
                  </a-menu>
                </template>
                <a-button size="small" type="text">
                  <SettingOutlined />
                  缓存
                  <DownOutlined />
                </a-button>
              </a-dropdown>
              
              <a-button 
                type="primary"
                @click="$emit('refresh')" 
                size="small" 
                :loading="preparingChapter"
                :disabled="isPreparationDisabled"
              >
                🤖 智能准备
              </a-button>
              <a-button 
                type="primary" 
                @click="saveChanges" 
                size="small" 
                :loading="saving" 
                :disabled="!hasChanges"
              >
                💾 保存修改
              </a-button>
            </a-space>
          </template>

          <!-- 合成片段tab -->
          <a-tab-pane key="segments" tab="📝 合成片段">
            <div class="segments-view">
              <div class="segments-header">
                <h4>合成片段配置</h4>
                <a-space>
                  <span class="segment-count">
                    共 {{ editableSegments.length }} 个片段
                  </span>
                  <a-button size="small" @click="exportSegments">
                    📋 导出片段
                  </a-button>
                </a-space>
              </div>

              <div class="segments-list">
                <div 
                  v-for="(segment, index) in editableSegments" 
                  :key="index"
                  class="segment-item"
                  :class="{ 
                    'segment-highlighted': highlightedCharacter && segment.speaker === highlightedCharacter,
                    'segment-dimmed': highlightedCharacter && segment.speaker !== highlightedCharacter
                  }"
                >
                  <div class="segment-header">
                    <span class="segment-index">#{{ index + 1 }}</span>
                    <a-select
                      v-model:value="segment.speaker"
                      placeholder="选择说话人"
                      style="width: 140px;"
                      @change="markChanged"
                      allowClear
                    >
                      <a-select-option 
                        v-for="character in editableCharacters" 
                        :key="character.name"
                        :value="character.name"
                      >
                        {{ character.name }}
                      </a-select-option>
                    </a-select>
                    <a-tag 
                      v-if="segment.speaker"
                      :color="getCharacterColor(segment.speaker)"
                      size="small"
                    >
                      {{ segment.speaker }}
                    </a-tag>
                    <span 
                      v-if="highlightedCharacter && segment.speaker === highlightedCharacter"
                      class="highlight-indicator"
                    >
                      🔍
                    </span>
                  </div>
                  <div class="segment-content">
                    <a-textarea
                      v-model:value="segment.text"
                      placeholder="文本内容"
                      :rows="2"
                      @change="markChanged"
                    />
                  </div>
                </div>
              </div>
            </div>
          </a-tab-pane>

          <!-- JSON数据tab -->
          <a-tab-pane key="json" tab="🔧 JSON数据">
            <div class="json-view">
              <div class="json-header">
                <a-space>
                  <a-button 
                    size="small" 
                    @click="toggleJsonEditMode"
                    :type="jsonEditMode ? 'primary' : 'default'"
                  >
                    {{ jsonEditMode ? '📖 预览模式' : '✏️ 编辑模式' }}
                  </a-button>
                  <a-button size="small" @click="copyJson">
                    📋 复制JSON
                  </a-button>
                  <a-button size="small" @click="formatJson">
                    🎨 格式化
                  </a-button>
                  <a-button size="small" @click="downloadJson">
                    💾 下载JSON
                  </a-button>
                  <a-button 
                    v-if="jsonEditMode"
                    size="small" 
                    @click="saveJsonChanges"
                    type="primary"
                    :disabled="!hasJsonChanges"
                  >
                    💾 保存JSON
                  </a-button>
                </a-space>
              </div>
              
              <div class="json-editor">
                <!-- 编辑模式 -->
                <a-textarea
                  v-if="jsonEditMode"
                  v-model:value="editableJsonText"
                  :rows="25"
                  class="json-display editable"
                  placeholder="编辑JSON数据..."
                  @change="markJsonChanged"
                />
                <!-- 预览模式 -->
                <a-textarea
                  v-else
                  :value="getJsonPreview()"
                  :rows="25"
                  readonly
                  class="json-display"
                />
              </div>
            </div>
          </a-tab-pane>

          <!-- 角色信息tab -->
          <a-tab-pane key="characters" tab="🎭 角色信息">
            <div class="characters-view">
              <div class="characters-header">
                <h4>智能识别的角色 (共{{ editableCharacters.length }}个)</h4>
                <span class="character-stats">
                  总片段: {{ editableSegments.length }}个
                </span>
              </div>

              <div class="characters-grid">
                <div 
                  v-for="(character, index) in editableCharacters" 
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
                        <a-tag color="blue" size="small">
                          第{{ index + 1 }}位
                        </a-tag>
                        <a-tag :color="getCharacterStatusColor(character)" size="small">
                          {{ getCharacterStatusText(character) }}
                        </a-tag>
                        <a-tag v-if="character.in_character_library" color="green" size="small">
                          📚 配音库
                        </a-tag>
                        <a-tag v-else color="orange" size="small">
                          ❓ 待添加
                        </a-tag>
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
                        @click="highlightCharacterSegments(character.name)"
                        :type="highlightedCharacter === character.name ? 'primary' : 'default'"
                      >
                        {{ highlightedCharacter === character.name ? '🔍 取消高亮' : '🔍 高亮片段' }}
                      </a-button>
                      <a-button 
                        size="small"
                        @click="exportCharacterSegments(character.name)"
                      >
                        📋 导出片段
                      </a-button>
                      <a-button 
                        size="small"
                        @click="testCharacterVoice(character.name)"
                        :loading="testingVoice === character.name"
                      >
                        🔊 试听
                      </a-button>
                    </a-space>
                  </div>
                </div>
              </div>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>

    <!-- 无分析数据 -->
    <div v-else class="no-analysis">
      <a-empty description="该章节暂无智能分析数据" :image="false">
        <div class="empty-icon">🤖</div>
        <p>请先对章节进行智能准备</p>
        <a-button type="primary" @click="$emit('refresh')">
          🎭 开始智能准备
        </a-button>
      </a-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { useAudioPlayerStore } from '@/stores/audioPlayer'
import { charactersAPI } from '@/api'
import { 
  ReloadOutlined, 
  ClearOutlined, 
  DeleteOutlined, 
  SettingOutlined, 
  DownOutlined 
} from '@ant-design/icons-vue'

const props = defineProps({
  chapter: {
    type: Object,
    default: null
  },
  analysisData: {
    type: Object,
    default: null
  },
  loading: {
    type: Boolean,
    default: false
  },
  preparingChapter: {
    type: Boolean,
    default: false
  },
  preparationStatus: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['refresh', 'save'])

const audioStore = useAudioPlayerStore()

const activeSubTab = ref('segments')
const saving = ref(false)
const hasChanges = ref(false)
const highlightedCharacter = ref(null)
const testingVoice = ref(null)
const jsonEditMode = ref(false)
const editableJsonText = ref('')

// 🔥 新增：缓存状态信息
const cacheInfo = ref({
  data_source: 'synthesis_plan',
  user_edited: false,
  cache_status: 'cached',
  last_updated: null
})

// 可编辑的数据
const editableCharacters = ref([])
const editableSegments = ref([])
const originalData = ref(null)

// 处理信息
const processingInfo = computed(() => {
  return props.analysisData?.processing_info || {}
})

// 是否禁用准备按钮
const isPreparationDisabled = computed(() => {
  return props.preparingChapter || 
    (props.preparationStatus?.analysis_status === 'processing' || 
     props.preparationStatus?.synthesis_status === 'processing')
})

// 🔥 简化：初始化可编辑数据，直接使用JSON中的角色信息
const initEditableData = async () => {
  if (!props.analysisData?.synthesis_json) {
    console.warn('[角色分析] 没有有效的分析结果数据')
    return
  }

  const synthesisJson = props.analysisData.synthesis_json

  try {
    // 🔥 优化：直接使用JSON中的角色信息，确保包含所有必要字段
    console.log('[角色分析] 直接使用JSON中的角色信息')
    editableCharacters.value = (synthesisJson.characters || []).map(char => ({
      ...char,
      character_id: char.character_id || null,  // 🔥 修复：确保character_id字段存在
      voice_id: char.voice_id || '',
      in_character_library: char.in_character_library || false,
      is_voice_configured: char.is_voice_configured || false,
      avatarUrl: char.avatarUrl || null
    }))
    
    // 对角色按出现次数排序
    editableCharacters.value.sort((a, b) => (b.count || 0) - (a.count || 0))
    
    console.log('[角色分析] 角色信息:', editableCharacters.value)

    // 初始化可编辑的合成计划，确保包含所有必要字段
    editableSegments.value = (synthesisJson.synthesis_plan || []).map(segment => ({
      ...segment,
      character_id: segment.character_id || null,  // 🔥 修复：确保character_id字段存在
      voice_id: segment.voice_id || '',
      voice_name: segment.voice_name || '未分配'
    }))
    
    // 保存原始数据用于比较变化
    originalData.value = JSON.parse(JSON.stringify({
      characters: editableCharacters.value,
      segments: editableSegments.value
    }))

    console.log('[角色分析] 数据初始化完成')
  } catch (error) {
    console.error('[角色分析] 初始化数据失败:', error)
    message.error('初始化角色分析数据失败')
  }
}

// 🔥 简化：监听分析数据变化
watch(() => props.analysisData, (newData) => {
  try {
    if (newData?.synthesis_json) {
      initEditableData()
      originalData.value = JSON.parse(JSON.stringify(newData))
      hasChanges.value = false
      
      // 🔥 更新缓存状态信息
      const processingInfo = newData.processing_info || {}
      cacheInfo.value = {
        data_source: processingInfo.data_source || 'synthesis_plan',
        user_edited: processingInfo.user_edited || false,
        cache_status: processingInfo.cache_status || 'cached',
        last_updated: newData.last_updated || null
      }
    } else {
      // 重置数据
      editableCharacters.value = []
      editableSegments.value = []
      originalData.value = null
      hasChanges.value = false
      cacheInfo.value = {
        data_source: 'synthesis_plan',
        user_edited: false,
        cache_status: 'cached',
        last_updated: null
      }
    }
  } catch (error) {
    console.error('初始化分析数据失败:', error)
    message.error('初始化分析数据失败')
    // 重置数据
    editableCharacters.value = []
    editableSegments.value = []
    originalData.value = null
    hasChanges.value = false
    cacheInfo.value = {
      data_source: 'synthesis_plan',
      user_edited: false,
      cache_status: 'cached',
      last_updated: null
    }
  }
}, { immediate: true })

// 标记为已修改
const markChanged = () => {
  hasChanges.value = true
}

// 重置修改
const resetChanges = () => {
  if (originalData.value) {
    initEditableData()
    hasChanges.value = false
    message.info('已重置修改')
  }
}

// 保存修改
const saveChanges = async () => {
  if (!hasChanges.value) return
  
  saving.value = true
  try {
    const updatedData = {
      ...props.analysisData,
      synthesis_json: {
        ...props.analysisData.synthesis_json,
        characters: editableCharacters.value,
        synthesis_plan: editableSegments.value
      }
    }
    
    emit('save', updatedData)
    hasChanges.value = false
    message.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 获取JSON预览
const getJsonPreview = () => {
  if (!props.analysisData) return ''
  
  const previewData = {
    ...props.analysisData,
    synthesis_json: {
      ...props.analysisData.synthesis_json,
      characters: editableCharacters.value,
      synthesis_plan: editableSegments.value
    }
  }
  
  return JSON.stringify(previewData, null, 2)
}

// 复制JSON
const copyJson = async () => {
  try {
    await navigator.clipboard.writeText(getJsonPreview())
    message.success('JSON已复制到剪贴板')
  } catch (error) {
    message.error('复制失败')
  }
}

// 格式化JSON
const formatJson = () => {
  message.info('JSON已格式化显示')
}

// 下载JSON
const downloadJson = () => {
  const jsonContent = getJsonPreview()
  const blob = new Blob([jsonContent], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `第${props.chapter?.number}章_智能分析结果.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  message.success('JSON文件下载成功')
}

// 导出片段
const exportSegments = () => {
  const segments = editableSegments.value.map((segment, index) => 
    `${index + 1}. ${segment.speaker}: ${segment.text}`
  ).join('\n\n')
  
  const blob = new Blob([segments], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `第${props.chapter?.number}章_合成片段.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  message.success('片段导出成功')
}

// 获取角色颜色
const getCharacterColor = (name) => {
  const colors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[hash % colors.length]
}

// 获取角色图标
const getCharacterIcon = (name) => {
  if (name.includes('旁白')) return '📖'
  if (name.includes('男') || name.includes('先生')) return '👨'
  if (name.includes('女') || name.includes('小姐')) return '👩'
  return name.charAt(0)
}

// 获取角色类型颜色
const getCharacterTypeColor = (type) => {
  const colors = {
    male: 'blue',
    female: 'pink',
    narrator: 'purple',
    neutral: 'default'
  }
  return colors[type] || 'default'
}

// 获取角色类型文本
const getCharacterTypeText = (type) => {
  const texts = {
    male: '男性',
    female: '女性',
    narrator: '旁白',
    neutral: '中性'
  }
  return texts[type] || '未知'
}

// 获取角色占比
const getCharacterPercentage = (character) => {
  const total = editableSegments.value.length
  if (total === 0) return 0
  return Math.round((character.count / total) * 100)
}

// 🔥 修复：获取角色头像，需要从角色配音库API获取avatarUrl
const getCharacterAvatar = (character) => {
  // 由于JSON中没有直接包含avatarUrl，需要从角色配音库获取
  // 这里先返回null，等待后续从角色配音库API获取完整信息
  return character?.avatarUrl || null
}

// 获取角色首字母
const getCharacterInitial = (name) => {
  if (!name) return '?'
  if (name.includes('旁白')) return '📖'
  return name.charAt(0)
}

// 获取角色排名标识
const getCharacterRank = (character, index) => {
  if (index === 0) return '👑主角'
  if (index === 1) return '⭐重要配角'
  if (index <= 3) return '✨一般配角'
  if (character.name.includes('旁白')) return '📖旁白'
  return '👤其他'
}

// 获取性别颜色
const getGenderColor = (gender) => {
  const colors = {
    '男': 'blue',
    '女': 'pink',
    '男性': 'blue',
    '女性': 'pink',
    'male': 'blue',
    'female': 'pink'
  }
  return colors[gender] || 'default'
}

// 🔥 简化：直接从角色信息获取状态颜色
const getCharacterStatusColor = (character) => {
  if (!character?.in_character_library) return 'orange' // 不在角色配音库中
  if (character?.is_voice_configured) return 'green' // 已配置语音
  return 'blue' // 在配音库但未配置语音
}

// 🔥 简化：直接从角色信息获取状态文本
const getCharacterStatusText = (character) => {
  if (!character?.in_character_library) return '未在配音库'
  if (character?.is_voice_configured) return '✅ 已配置语音'
  return '🔧 在配音库中'
}

// 高亮角色片段
const highlightCharacterSegments = (characterName) => {
  if (highlightedCharacter.value === characterName) {
    highlightedCharacter.value = null
    message.info('取消高亮')
  } else {
    highlightedCharacter.value = characterName
    message.info(`高亮角色"${characterName}"的片段`)
    // 切换到片段tab
    activeSubTab.value = 'segments'
  }
}

// 导出角色片段
const exportCharacterSegments = (characterName) => {
  const characterSegments = editableSegments.value
    .filter(segment => segment.speaker === characterName)
    .map((segment, index) => `${index + 1}. ${segment.text}`)
    .join('\n\n')
  
  if (characterSegments) {
    const blob = new Blob([`角色"${characterName}"的片段：\n\n${characterSegments}`], 
      { type: 'text/plain;charset=utf-8' })
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `第${props.chapter?.number}章_${characterName}_片段.txt`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    URL.revokeObjectURL(url)
    message.success(`角色"${characterName}"的片段导出成功`)
  } else {
    message.warning(`角色"${characterName}"没有片段`)
  }
}

// 测试角色声音 - 简单直接，没配置就报错
const testCharacterVoice = async (characterName) => {
  testingVoice.value = characterName
  try {
    console.log(`[试听] 开始测试角色: ${characterName}`)
    
    // 获取角色信息
    const character = editableCharacters.value.find(c => c.name === characterName)
    const characterSegment = editableSegments.value.find(s => s.speaker === characterName)
    
    if (!character) {
      message.error(`未找到角色"${characterName}"的配置信息`)
      return
    }
    
    console.log(`[试听] 角色信息:`, {
      name: character.name,
      character_id: character.character_id,
      voice_id: character.voice_id,
      in_character_library: character.in_character_library,
      is_voice_configured: character.is_voice_configured
    })
    
    // 检查角色配音库配置
    if (character.character_id && character.in_character_library) {
      if (!character.is_voice_configured) {
        message.error(`角色"${characterName}"在配音库中但未配置音频文件，请前往角色管理页面上传音频`)
        return
      }
      
      console.log(`[试听] 使用角色配音库ID: ${character.character_id}`)
      
      // 获取示例文本
      const sampleText = characterSegment?.text?.slice(0, 50) + '...' || `你好，我是${characterName}。`
      
      try {
        const response = await charactersAPI.testVoiceSynthesis(character.character_id, {
          text: sampleText
        })
        
        if (response.data?.success && response.data.audioUrl) {
          const audioInfo = {
            id: `character_test_${characterName}_${Date.now()}`,
            title: `${characterName} - 角色配音库试听`,
            url: response.data.audioUrl,
            type: 'character_test',
            metadata: {
              characterName,
              characterId: character.character_id,
              source: 'character_library'
            }
          }
          
          await audioStore.playAudio(audioInfo)
          message.success(`正在播放角色"${characterName}"的声音（来源：角色配音库）`)
          return
        } else {
          message.error(`角色配音库试听失败: ${response.data?.message || '未知错误'}`)
          return
        }
      } catch (error) {
        console.error('[试听] 角色配音库API调用失败:', error)
        message.error(`角色配音库试听失败: ${error.response?.data?.detail || error.message}`)
        return
      }
    }
    
    // 检查传统VoiceProfile配置
    if (character.voice_id) {
      console.log(`[试听] 使用传统VoiceProfile ID: ${character.voice_id}`)
      
      const sampleText = characterSegment?.text?.slice(0, 50) + '...' || `你好，我是${characterName}。`
      
      try {
        const response = await charactersAPI.testVoiceSynthesis(character.voice_id, {
          text: sampleText
        })
        
        if (response.data?.success && response.data.audioUrl) {
          const audioInfo = {
            id: `character_test_${characterName}_${Date.now()}`,
            title: `${characterName} - 传统语音档案试听`,
            url: response.data.audioUrl,
            type: 'character_test',
            metadata: {
              characterName,
              voiceId: character.voice_id,
              source: 'voice_profile'
            }
          }
          
          await audioStore.playAudio(audioInfo)
          message.success(`正在播放角色"${characterName}"的声音（来源：传统语音档案）`)
          return
        } else {
          message.error(`传统语音档案试听失败: ${response.data?.message || '未知错误'}`)
          return
        }
      } catch (error) {
        console.error('[试听] 传统语音档案API调用失败:', error)
        message.error(`传统语音档案试听失败: ${error.response?.data?.detail || error.message}`)
        return
      }
    }
    
    // 没有任何配置
    console.log(`[试听] 角色"${characterName}"没有任何声音配置`)
    message.error(`角色"${characterName}"未配置声音，请：
1. 前往角色管理页面创建角色并上传音频文件
2. 或在书籍角色管理中为该角色分配已有的声音配置`)
    
  } catch (error) {
    console.error('[试听] 测试失败:', error)
    message.error(`试听失败: ${error.message}`)
  } finally {
    testingVoice.value = null
  }
}



// JSON编辑模式切换
const toggleJsonEditMode = () => {
  jsonEditMode.value = !jsonEditMode.value
  if (jsonEditMode.value) {
    editableJsonText.value = getJsonPreview()
  }
}

// 标记JSON为已修改
const markJsonChanged = () => {
  // 在编辑模式下，每次文本变化都视为修改
  // 在预览模式下，只有保存按钮点击时才视为修改
  if (jsonEditMode.value) {
    hasChanges.value = true
  }
}

// 保存JSON修改
const saveJsonChanges = async () => {
  if (!jsonEditMode.value) return
  if (!hasJsonChanges.value) return
  
  try {
    // 验证JSON格式
    const parsedJson = JSON.parse(editableJsonText.value)
    
    // 更新可编辑数据
    if (parsedJson.characters && Array.isArray(parsedJson.characters)) {
      editableCharacters.value = parsedJson.characters
    }
    if (parsedJson.synthesis_plan && Array.isArray(parsedJson.synthesis_plan)) {
      editableSegments.value = parsedJson.synthesis_plan
    }
    
    // 标记为已修改
    hasChanges.value = true
    message.success('JSON数据已应用到编辑器')
    
    // 切换回预览模式
    jsonEditMode.value = false
    
  } catch (error) {
    console.error('JSON格式错误:', error)
    message.error('JSON格式错误，请检查语法')
  }
}

// 判断JSON是否有变化
const hasJsonChanges = computed(() => {
  if (!jsonEditMode.value) return false
  try {
    // 尝试解析JSON来验证格式
    JSON.parse(editableJsonText.value)
    return editableJsonText.value !== getJsonPreview()
  } catch {
    return true // 如果JSON格式错误，也认为有变化
  }
})

// 🔥 新增：缓存控制方法
// 获取缓存状态文本
const getCacheStatusText = () => {
  switch (cacheInfo.value.data_source) {
    case 'final_config':
      return '用户编辑'
    case 'synthesis_plan':
      return '智能准备'
    default:
      return '未知'
  }
}

// 获取缓存状态颜色
const getCacheStatusColor = () => {
  if (cacheInfo.value.user_edited) return 'purple'
  if (cacheInfo.value.cache_status === 'fresh') return 'green'
  return 'blue'
}

// 获取缓存状态图标
const getCacheStatusIcon = () => {
  if (cacheInfo.value.user_edited) return '✏️'
  if (cacheInfo.value.cache_status === 'fresh') return '🔄'
  return '💾'
}

// 获取最后更新时间
const getLastUpdateTime = () => {
  if (!cacheInfo.value.last_updated) return '未知'
  try {
    const date = new Date(cacheInfo.value.last_updated)
    return date.toLocaleString('zh-CN')
  } catch {
    return '未知'
  }
}

// 强制刷新缓存
const refreshCache = async () => {
  try {
    message.loading('正在刷新缓存...', 0)
    // 发送带有force_refresh参数的请求
    emit('refresh', { force_refresh: true })
    message.destroy()
    message.success('缓存已刷新，将显示最新数据')
  } catch (error) {
    message.destroy()
    message.error('刷新缓存失败')
    console.error('刷新缓存失败:', error)
  }
}

// 清除编辑缓存
const clearEditCache = async () => {
  try {
    if (!props.chapter?.id) {
      message.error('缺少章节信息')
      return
    }
    
    message.loading('正在清除编辑缓存...', 0)
    
    // 调用API清除final_config缓存
    await charactersAPI.clearPreparationCache(props.chapter.id, 'final_config')
    
    message.destroy()
    message.success('编辑缓存已清除，将显示智能准备结果')
    
    // 刷新数据
    emit('refresh', { force_refresh: true })
  } catch (error) {
    message.destroy()
    message.error('清除编辑缓存失败')
    console.error('清除编辑缓存失败:', error)
  }
}

// 清除所有缓存
const clearAllCache = async () => {
  try {
    if (!props.chapter?.id) {
      message.error('缺少章节信息')
      return
    }
    
    // 确认操作
    const confirmed = await new Promise((resolve) => {
      const modal = Modal.confirm({
        title: '确认清除所有缓存',
        content: '这将删除所有智能准备结果，需要重新进行智能准备。确定继续吗？',
        okText: '确认清除',
        cancelText: '取消',
        okButtonProps: { danger: true },
        onOk: () => resolve(true),
        onCancel: () => resolve(false)
      })
    })
    
    if (!confirmed) return
    
    message.loading('正在清除所有缓存...', 0)
    
    // 调用API清除所有缓存
    await charactersAPI.clearPreparationCache(props.chapter.id, 'all')
    
    message.destroy()
    message.success('所有缓存已清除，请重新进行智能准备')
    
    // 刷新数据
    emit('refresh')
  } catch (error) {
    message.destroy()
    message.error('清除所有缓存失败')
    console.error('清除所有缓存失败:', error)
  }
}
</script>

<style scoped>
.chapter-analysis {
  height: 100%;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.loading-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}

.analysis-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.analysis-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
}

.analysis-tabs {
  flex: 1;
  overflow: hidden;
  
  :deep(.ant-tabs) {
    height: 100%;
    display: flex;
    flex-direction: column;
  }
  
  :deep(.ant-tabs-nav) {
    margin: 0;
    padding: 8px 12px;
    background: var(--component-background);
    border-bottom: 1px solid var(--border-color-base);
    display: flex;
    justify-content: space-between;
    align-items: center;
    
    &::before {
      display: none;
    }
    
    .ant-tabs-nav-wrap {
      flex: 1;
    }
    
    .ant-tabs-extra-content {
      margin-left: 16px;
    }
  }
  
  :deep(.ant-tabs-content-holder) {
    flex: 1;
    overflow: auto;
  }
}

.segments-view {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.segments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.segments-header h4 {
  margin: 0;
  color: #1f2937;
}

.segment-count {
  font-size: 12px;
  color: #6b7280;
}

.segments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.segment-item {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
}

.segment-item.segment-highlighted {
  background-color: #e0f2fe; /* 高亮背景色 */
  border-color: #90cdf4; /* 高亮边框色 */
  box-shadow: 0 0 8px rgba(139, 92, 246, 0.2); /* 高亮阴影 */
}

.segment-item.segment-dimmed {
  opacity: 0.6; /* 半透明效果 */
  background-color: #f0f2f5; /* 暗化背景色 */
  border-color: #e5e7eb; /* 暗化边框色 */
}

.segment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.segment-index {
  font-weight: 600;
  color: #6b7280;
  min-width: 40px;
}

.highlight-indicator {
  margin-left: auto;
  color: #8b5cf6;
  font-size: 16px;
  animation: pulse 2s infinite;
}

@keyframes pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.5; }
}

.segment-content {
  margin-top: 8px;
}

.json-view {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.json-header {
  margin-bottom: 16px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.json-editor {
  height: calc(100% - 100px);
}

.json-display {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  line-height: 1.4;
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  resize: none;
  height: 100%;
}

.json-display.editable {
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(64, 169, 255, 0.2);
  background-color: #fafafa;
}

.json-display.editable:focus {
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(64, 169, 255, 0.3);
}

.characters-view {
  padding: 16px;
  height: 100%;
  overflow-y: auto;
}

.characters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.characters-header h4 {
  margin: 0;
  color: #1f2937;
}

.character-stats {
  font-size: 12px;
  color: #6b7280;
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.character-card {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  background: #fff;
  transition: all 0.2s;
  position: relative;
  overflow: hidden;
}

.character-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.1);
}

.character-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
}

.character-avatar {
  flex-shrink: 0;
}

.character-info {
  flex: 1;
  min-width: 0;
}

.character-name {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.name-text {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.character-rank {
  font-size: 12px;
  color: #6b7280;
  flex-shrink: 0;
}

.character-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.character-details {
  margin-top: 12px;
}

.character-actions {
  margin-top: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 8px;
}

.no-analysis {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-analysis p {
  color: #6b7280;
  margin: 8px 0 16px 0;
}
</style> 