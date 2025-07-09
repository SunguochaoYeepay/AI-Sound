<!-- 可编辑的智能分析结果抽屉组件 -->
<template>
  <a-drawer
    :open="visible"
    title="📋 智能准备结果"
    placement="right"
    :width="800"
    @close="handleClose"
  >
    <template #extra>
      <a-space>
        <a-button @click="handleReset" :disabled="!hasChanges">
          🔄 重置
        </a-button>
        <a-button 
          type="primary" 
          @click="handleSave" 
          :loading="saving"
          :disabled="!hasChanges"
        >
          💾 保存修改
        </a-button>
      </a-space>
    </template>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载分析结果...">
        <div style="height: 300px;"></div>
      </a-spin>
    </div>

    <div v-else-if="analysisData" class="analysis-content">
      <a-tabs v-model:activeKey="activeTab">
        <!-- 基本信息 Tab -->
        <a-tab-pane tab="📊 基本信息" key="info">
          <a-card title="处理信息" size="small" style="margin-bottom: 16px;">
            <a-descriptions :column="1" bordered size="small">
              <a-descriptions-item label="处理模式">
                {{ processingInfo.mode || '未知' }}
              </a-descriptions-item>
              <a-descriptions-item label="生成片段">
                {{ processingInfo.total_segments || analysisData.synthesis_json?.synthesis_plan?.length || 0 }} 个
              </a-descriptions-item>
              <a-descriptions-item label="检测角色">
                {{ processingInfo.characters_found || analysisData.synthesis_json?.characters?.length || 0 }} 个
              </a-descriptions-item>
              <a-descriptions-item label="估算tokens">
                {{ processingInfo.estimated_tokens || '未知' }}
              </a-descriptions-item>
              <a-descriptions-item label="旁白角色">
                {{ processingInfo.narrator_added ? '已添加' : '未添加' }}
              </a-descriptions-item>
              <a-descriptions-item label="数据库存储">
                {{ processingInfo.saved_to_database ? '已保存' : '未保存' }}
              </a-descriptions-item>
              <a-descriptions-item label="最后更新">
                {{ analysisData.last_updated || '未知' }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>
        </a-tab-pane>

        <!-- 相关角色 Tab -->
        <a-tab-pane tab="🎭 相关角色" key="characters">
          <div class="characters-display">
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
                class="character-edit-item"
              >
                <div class="character-header">
                  <!-- 角色头像 -->
                  <div class="character-avatar" :style="{ background: character.color || '#8b5cf6' }">
                    <img v-if="character.avatarUrl" :src="character.avatarUrl" :alt="character.name" class="avatar-image" />
                    <span v-else>{{ getCharacterIcon(character.name) }}</span>
                  </div>
                  <div class="character-info">
                    <div class="character-name">
                      {{ character.name }}
                      <!-- 角色配置状态标签 -->
                      <a-tag v-if="character.exists_in_library" :color="getCharacterStatusColor(character)" size="small">
                        {{ getCharacterStatusText(character) }}
                      </a-tag>
                      <a-tag v-else color="orange" size="small">未配置</a-tag>
                    </div>
                    <div class="character-count">
                      <a-tag color="blue">{{ character.count || 0 }}次</a-tag>
                      <span class="character-type">{{ getCharacterTypeText(character.voice_type) }}</span>
                    </div>
                    <!-- 角色详细信息 -->
                    <div v-if="character.exists_in_library" class="character-details">
                      <div class="character-description">{{ character.description || '暂无描述' }}</div>
                      <div class="character-quality">
                        <span>质量: </span>
                        <a-rate :value="character.quality || 0" disabled allow-half size="small" />
                        <span class="quality-text">{{ character.quality || 0 }} 星</span>
                      </div>
                    </div>
                  </div>
                </div>
                
                <!-- 音频配置状态区域 -->
                <div class="voice-assignment">
                  <div class="voice-label">音频配置状态：</div>
                  
                  <!-- 角色存在于角色库中 -->
                  <div v-if="character.exists_in_library" class="voice-config-status">
                    <div v-if="character.is_voice_configured" class="voice-configured">
                      <a-tag color="green">
                        <template #icon>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
                          </svg>
                        </template>
                        已配置音频文件
                      </a-tag>
                      <a-button 
                        v-if="character.referenceAudioUrl"
                        type="link" 
                        size="small"
                        @click="testVoice(character)"
                        title="试听角色音频"
                      >
                        🔊 试听
                      </a-button>
                    </div>
                    <div v-else class="voice-not-configured">
                      <a-tag color="orange">
                        <template #icon>
                          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
                          </svg>
                        </template>
                        需要配置音频文件
                      </a-tag>
                      <a-button 
                        type="link" 
                        size="small"
                        @click="goToCharacterConfig(character)"
                        title="前往角色管理页面配置音频"
                      >
                        去配置
                      </a-button>
                    </div>
                  </div>
                  
                  <!-- 角色不存在于角色库中 -->
                  <div v-else class="voice-not-in-library">
                    <a-tag color="red">
                      <template #icon>
                        <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 13.59L15.59 17 12 13.41 8.41 17 7 15.59 10.59 12 7 8.41 8.41 7 12 10.59 15.59 7 17 8.41 13.41 12 17 15.59z"/>
                        </svg>
                      </template>
                      角色未创建
                    </a-tag>
                    <a-button 
                      type="link" 
                      size="small"
                      @click="goToCharacterCreation(character)"
                      title="前往角色管理页面创建角色"
                    >
                      去创建
                    </a-button>
                  </div>
                </div>
              </div>
            </div>

            <!-- 角色统计 -->
            <div class="characters-stats">
              <a-row :gutter="16">
                <a-col :span="8">
                  <div class="stat-card">
                    <div class="stat-value">{{ editableCharacters.length }}</div>
                    <div class="stat-label">识别角色</div>
                  </div>
                </a-col>
                <a-col :span="8">
                  <div class="stat-card">
                    <div class="stat-value">{{ editableSegments.length }}</div>
                    <div class="stat-label">语音片段</div>
                  </div>
                </a-col>
                <a-col :span="8">
                  <div class="stat-card">
                    <div class="stat-value">{{ getDialogueRatio() }}%</div>
                    <div class="stat-label">对话比例</div>
                  </div>
                </a-col>
              </a-row>
            </div>
          </div>
        </a-tab-pane>

        <!-- 合成片段 Tab -->
        <a-tab-pane tab="📝 合成片段" key="segments">
          <div class="segments-editor">
            <div class="editor-header">
              <h4>合成片段配置</h4>
              <a-space>
                <span class="segment-count">
                  共 {{ editableSegments.length }} 个片段
                </span>

              </a-space>
            </div>

            <div class="segments-list">
              <div 
                v-for="(segment, index) in editableSegments" 
                :key="index"
                class="segment-edit-item"
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
                </div>
                <a-textarea
                  v-model:value="segment.text"
                  placeholder="文本内容"
                  :rows="3"
                  style="margin-top: 8px;"
                  @change="markChanged"
                  readonly
                />
              </div>
            </div>
          </div>
        </a-tab-pane>

        <!-- JSON数据 Tab -->
        <a-tab-pane tab="🔧 JSON数据" key="json">
          <div class="json-editor">
            <a-alert
              message="JSON数据预览"
              description="这里显示当前编辑的结果的JSON格式，保存后将更新到数据库"
              type="info"
              show-icon
              style="margin-bottom: 16px;"
            />
            <a-textarea
              :value="getJsonPreview()"
              :rows="25"
              readonly
              class="json-display"
            />
          </div>
        </a-tab-pane>
      </a-tabs>
    </div>

    <div v-else class="no-data">
      <a-empty description="暂无分析数据" />
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, computed, watch, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { useRouter } from 'vue-router'
import { booksAPI } from '@/api'
import { charactersAPI } from '@/api'
import { getAudioService } from '@/utils/audioService'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  chapterId: {
    type: [String, Number],
    default: null
  }
})

// Emits
const emit = defineEmits(['update:visible', 'saved'])

// Router
const router = useRouter()

// 响应式数据
const loading = ref(false)
const saving = ref(false)

const activeTab = ref('info')
const analysisData = ref(null)
const originalData = ref(null)
const hasChanges = ref(false)

// 可编辑的数据
const editableCharacters = ref([])
const editableSegments = ref([])

// 音频服务实例（保留用于其他功能）
const audioService = getAudioService()

// 计算属性
const processingInfo = computed(() => {
  return analysisData.value?.processing_info || {}
})

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (newVal && props.chapterId) {
    loadAnalysisData()
  }
})

// 监听chapterId变化
watch(() => props.chapterId, (newVal) => {
  if (newVal && props.visible) {
    loadAnalysisData()
  }
})



// 加载分析数据
const loadAnalysisData = async () => {
  if (!props.chapterId) return
  
  loading.value = true
  try {
    const response = await booksAPI.getPreparationResult(props.chapterId)
    if (response.data && response.data.success) {
      analysisData.value = response.data.data
      originalData.value = JSON.parse(JSON.stringify(response.data.data))
      
      // 初始化可编辑数据
      initEditableData()
      hasChanges.value = false
    } else {
      message.error('加载分析数据失败')
    }
  } catch (error) {
    console.error('加载分析数据失败:', error)
    message.error('加载分析数据失败')
  } finally {
    loading.value = false
  }
}

// 初始化可编辑数据
const initEditableData = () => {
  const synthesisJson = analysisData.value?.synthesis_json || {}
  
  console.log('[EditableAnalysisDrawer] 初始化数据:', {
    analysisData: analysisData.value,
    synthesisJson,
    characters: synthesisJson.characters,
    synthesis_plan: synthesisJson.synthesis_plan
  })
  console.log('[EditableAnalysisDrawer] characters详细内容:', JSON.stringify(synthesisJson.characters, null, 2))
  console.log('[EditableAnalysisDrawer] synthesis_plan详细内容:', JSON.stringify(synthesisJson.synthesis_plan, null, 2))
  
  // 优先使用characters字段，如果为空则从synthesis_plan提取
  if (synthesisJson.characters && synthesisJson.characters.length > 0) {
    // 使用JSON中定义的角色
    console.log('[EditableAnalysisDrawer] 使用characters字段的角色配置')
    editableCharacters.value = synthesisJson.characters.map(char => ({
      name: char.name || char.character_name || '未知角色',
      voice_id: char.voice_id || '',
      voice_name: char.voice_name || '未分配',
      voice_type: char.voice_type || char.type || 'neutral',
      count: 0 // 后续会统计使用次数
    }))
    
    // 统计每个角色在synthesis_plan中的使用次数
    const segments = synthesisJson.synthesis_plan || []
    segments.forEach(segment => {
      const character = editableCharacters.value.find(c => c.name === segment.speaker)
      if (character) {
        character.count++
      }
    })
  } else {
    // 从synthesis_plan中提取角色（fallback方案）
    console.log('[EditableAnalysisDrawer] characters字段为空，从synthesis_plan提取角色')
    const segments = synthesisJson.synthesis_plan || []
    const speakerMap = new Map()
    
    // 统计所有说话人及其出现次数
    console.log('[EditableAnalysisDrawer] 所有原始speaker值:', segments.map(s => s.speaker))
    segments.forEach(segment => {
      const speaker = segment.speaker || '未知'
      
      if (!speakerMap.has(speaker)) {
        speakerMap.set(speaker, {
          name: speaker,
          voice_id: segment.voice_id || '',
          voice_name: segment.voice_name || '未分配',
          voice_type: speaker === '旁白' ? 'narrator' : 
                     speaker.includes('孙悟空') ? 'male' :
                     speaker.includes('唐僧') ? 'male' :
                     speaker.includes('猪八戒') ? 'male' :
                     speaker.includes('沙僧') ? 'male' :
                     speaker.includes('白骨精') ? 'female' :
                     'neutral',
          count: 0
        })
      }
      speakerMap.get(speaker).count++
    })
    
    // 转换为数组，按出现次数排序
    editableCharacters.value = Array.from(speakerMap.values())
      .sort((a, b) => b.count - a.count)
      .map(char => ({
        name: char.name,
        voice_id: char.voice_id,
        voice_name: char.voice_name,
        voice_type: char.voice_type,
        count: char.count
      }))
  }
  
  console.log('[EditableAnalysisDrawer] 最终角色列表:', JSON.stringify(editableCharacters.value, null, 2))
  
  // 如果仍然没有角色，添加默认的旁白角色
  if (editableCharacters.value.length === 0) {
    editableCharacters.value.push({
      name: '旁白',
      voice_id: '1',
      voice_name: '系统旁白',
      voice_type: 'narrator',
      count: 0
    })
  }
  
  // 🔧 加载角色库信息，匹配角色详细信息
  loadCharacterLibraryInfo()
  
  // 初始化片段数据 - 保持完整的原始结构
  editableSegments.value = (synthesisJson.synthesis_plan || []).map(segment => ({
    segment_id: segment.segment_id || 0,
    speaker: segment.speaker || '',
    text: segment.text || '',
    voice_id: segment.voice_id || '',
    voice_name: segment.voice_name || '',
    parameters: segment.parameters || {
      timeStep: 32,
      pWeight: 1.4,
      tWeight: 3.0
    }
  }))
  
  console.log('[EditableAnalysisDrawer] 初始化完成:', {
    editableCharacters: JSON.stringify(editableCharacters.value, null, 2),
    editableSegments: JSON.stringify(editableSegments.value.slice(0, 5), null, 2) // 只显示前5个片段
  })
}

// 🔧 加载角色库信息，匹配角色详细信息
const loadCharacterLibraryInfo = async () => {
  try {
    const response = await charactersAPI.getCharacters({
      page: 1,
      page_size: 100
    })
    
    if (response.data?.success && response.data.data?.length > 0) {
      const characterLibrary = response.data.data
      
      // 为每个角色匹配角色库中的信息
      editableCharacters.value.forEach(character => {
        const matchedCharacter = characterLibrary.find(libChar => 
          libChar.name === character.name || 
          libChar.name.toLowerCase() === character.name.toLowerCase()
        )
        
        if (matchedCharacter) {
          // 角色存在于角色库中，更新详细信息
          character.exists_in_library = true
          character.id = matchedCharacter.id
          character.description = matchedCharacter.description
          character.status = matchedCharacter.status
          character.color = matchedCharacter.color
          character.avatarUrl = matchedCharacter.avatarUrl
          character.quality = matchedCharacter.quality_score
          character.usageCount = matchedCharacter.usage_count
          character.is_voice_configured = matchedCharacter.is_voice_configured
          character.referenceAudioUrl = matchedCharacter.referenceAudioUrl
        } else {
          // 角色不存在于角色库中
          character.exists_in_library = false
        }
      })
      
      console.log('[EditableAnalysisDrawer] 角色库信息匹配完成:', editableCharacters.value)
    }
  } catch (error) {
    console.error('[EditableAnalysisDrawer] 加载角色库信息失败:', error)
  }
}

// 🔧 获取角色状态颜色
const getCharacterStatusColor = (character) => {
  if (!character.exists_in_library) return 'default'
  
  if (character.is_voice_configured && character.status === 'active') {
    return 'green' // 已配置且可用
  } else if (character.status === 'active') {
    return 'orange' // 可用但需配置音频
  } else {
    return 'red' // 未激活
  }
}

// 🔧 获取角色状态文本
const getCharacterStatusText = (character) => {
  if (!character.exists_in_library) return '未知'
  
  if (character.is_voice_configured && character.status === 'active') {
    return '已配置'
  } else if (character.status === 'active') {
    return '需配置音频'
  } else {
    return '未激活'
  }
}

// 标记已修改
const markChanged = () => {
  hasChanges.value = true
}

// 添加角色
const addCharacter = () => {
  editableCharacters.value.push({
    name: '',
    voice_id: '',
    voice_name: '',
    voice_type: 'neutral'
  })
  markChanged()
}

// 添加旁白角色
const addNarratorCharacter = () => {
  editableCharacters.value.push({
    name: '旁白',
    voice_id: '1',
    voice_name: '系统旁白',
    voice_type: 'narrator'
  })
  markChanged()
}

// 删除角色
const removeCharacter = (index) => {
  editableCharacters.value.splice(index, 1)
  markChanged()
}



// 跳转到角色配置
const goToCharacterConfig = (character) => {
  // 跳转到角色管理页面并定位到该角色
  router.push({
    name: 'Characters',
    query: { highlight: character.name }
  })
  message.info(`请在角色管理页面为 ${character.name} 配置音频文件`)
}

// 跳转到角色创建
const goToCharacterCreation = (character) => {
  // 跳转到角色管理页面并预填角色名称
  router.push({
    name: 'Characters',
    query: { create: character.name }
  })
  message.info(`请在角色管理页面创建角色 ${character.name}`)
}

// 测试声音
const testVoice = async (character) => {
  if (!character.referenceAudioUrl) {
    message.warning('该角色暂无音频文件可试听')
    return
  }
  
  try {
    console.log('[EditableAnalysisDrawer] 播放角色音频:', character.name, character.referenceAudioUrl)
    
    // 直接播放角色的参考音频文件
    const audio = new Audio(character.referenceAudioUrl)
    audio.play()
    message.info(`正在播放角色 ${character.name} 的音频...`)
    
    // 监听播放事件
    audio.addEventListener('loadstart', () => {
      console.log('[EditableAnalysisDrawer] 音频开始加载')
    })
    
    audio.addEventListener('canplay', () => {
      console.log('[EditableAnalysisDrawer] 音频可以播放')
    })
    
    audio.addEventListener('error', (e) => {
      console.error('[EditableAnalysisDrawer] 音频播放错误:', e)
      message.error('音频播放失败')
    })
    
  } catch (error) {
    console.error('[EditableAnalysisDrawer] 播放音频失败:', error)
    message.error('播放音频失败')
  }
}





// 重置修改
const handleReset = () => {
  if (originalData.value) {
    analysisData.value = JSON.parse(JSON.stringify(originalData.value))
    initEditableData()
    hasChanges.value = false
    message.info('已重置所有修改')
  }
}

// 保存修改
const handleSave = async () => {
  saving.value = true
  try {
    console.log('[EditableAnalysisDrawer] 保存前的数据检查:', {
      editableCharacters: editableCharacters.value,
      editableSegments: editableSegments.value.slice(0, 3) // 只显示前3个段落
    })
    
    // 构造完整的synthesis_plan，确保包含所有必要字段
    const completeSynthesisPlan = editableSegments.value.map(segment => ({
      segment_id: segment.segment_id,
      speaker: segment.speaker,
      text: segment.text,
      voice_id: segment.voice_id || '',
      voice_name: segment.voice_name || '未分配',
      parameters: segment.parameters || {
        timeStep: 32,
        pWeight: 1.4,
        tWeight: 3.0
      }
    }))
    
    // 构造更新后的数据
    const updatedData = {
      ...analysisData.value,
      synthesis_json: {
        ...analysisData.value.synthesis_json,
        characters: editableCharacters.value,
        synthesis_plan: completeSynthesisPlan
      }
    }
    
    console.log('[EditableAnalysisDrawer] 即将保存的数据:', {
      characters: updatedData.synthesis_json.characters,
      synthesis_plan: updatedData.synthesis_json.synthesis_plan.slice(0, 3)
    })
    
    // 调用保存API
    const response = await booksAPI.updatePreparationResult(props.chapterId, updatedData)
    if (response.data && response.data.success) {
      message.success('保存成功')
      hasChanges.value = false
      originalData.value = JSON.parse(JSON.stringify(updatedData))
      analysisData.value = updatedData
      emit('saved', updatedData)
    } else {
      message.error('保存失败')
    }
  } catch (error) {
    console.error('保存失败:', error)
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

// 关闭抽屉
const handleClose = () => {
  if (hasChanges.value) {
    // 可以在这里添加确认对话框
    // Modal.confirm({ ... })
  }
  emit('update:visible', false)
}

// 获取JSON预览
const getJsonPreview = () => {
  if (!analysisData.value) return ''
  
  // 构造完整的synthesis_plan预览
  const completeSynthesisPlan = editableSegments.value.map(segment => ({
    segment_id: segment.segment_id,
    speaker: segment.speaker,
    text: segment.text,
    voice_id: segment.voice_id || '',
    voice_name: segment.voice_name || '未分配',
    parameters: segment.parameters || {
      timeStep: 32,
      pWeight: 1.4,
      tWeight: 3.0
    }
  }))
  
  const previewData = {
    ...analysisData.value,
    synthesis_json: {
      ...analysisData.value.synthesis_json,
      characters: editableCharacters.value,
      synthesis_plan: completeSynthesisPlan
    }
  }
  
  return JSON.stringify(previewData, null, 2)
}



// 新增：获取角色图标
const getCharacterIcon = (characterName) => {
  const icons = {
    '孙悟空': '🐒',
    '唐僧': '🧘',
    '猪八戒': '🐷',
    '沙僧': '🗿',
    '白骨精': '👻',
    '如来佛祖': '🙏',
    '观音菩萨': '🕉️',
    '玉皇大帝': '👑',
    '太上老君': '⚗️',
    '龙王': '🐲',
    '牛魔王': '🐂',
    '铁扇公主': '🌪️',
    '红孩儿': '🔥',
    '二郎神': '👁️',
    '哪吒': '⚡',
    '旁白': '📖',
    '系统旁白': '🔊',
    '心理旁白': '💭'
  }
  return icons[characterName] || '👤'
}

// 新增：获取角色类型文本
const getCharacterTypeText = (voiceType) => {
  const types = {
    'male': '男声',
    'female': '女声',
    'child': '童声',
    'narrator': '旁白',
    'neutral': '中性'
  }
  return types[voiceType] || '未知'
}

// 新增：计算对话比例
const getDialogueRatio = () => {
  if (!editableSegments.value.length) return 0
  
  const dialogueCount = editableSegments.value.filter(segment => 
    segment.speaker && segment.speaker !== '旁白' && segment.speaker !== '系统旁白'
  ).length
  
  return Math.round((dialogueCount / editableSegments.value.length) * 100)
}


</script>

<style scoped>
.loading-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.analysis-content {
  height: calc(100vh - 120px);
  overflow-y: auto;
}

.editor-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.editor-header h4 {
  margin: 0;
  color: #1f2937;
}

.segment-count, .character-stats {
  color: #666;
  font-size: 12px;
}

.character-header {
  margin-bottom: 8px;
  padding-bottom: 6px;
  border-bottom: 1px solid #e8e8e8;
}

.character-name-with-count {
  font-weight: 500;
  color: #1f2937;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 角色显示样式 */
.characters-display {
  padding: 0;
}

.characters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.characters-header h4 {
  margin: 0;
  color: #1f2937;
}

.characters-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.character-edit-item {
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  transition: all 0.2s ease;
}

.character-edit-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.character-header {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}

.character-avatar {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
  font-size: 16px;
  flex-shrink: 0;
  margin-right: 12px;
}

.character-avatar .avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.character-icon {
  font-size: 24px;
  margin-right: 12px;
}

.character-info {
  flex: 1;
}

.character-name {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.character-count {
  display: flex;
  align-items: center;
  gap: 8px;
}

.character-type {
  font-size: 12px;
  color: #666;
}

.character-details {
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f0f0f0;
}

.character-description {
  font-size: 12px;
  color: #666;
  margin-bottom: 6px;
  line-height: 1.4;
}

.character-quality {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #666;
}

.quality-text {
  margin-left: 4px;
}

.characters-stats {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
}

.stat-card {
  text-align: center;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e8e8e8;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

/* 片段编辑样式 */
.segments-list {
  max-height: 600px;
  overflow-y: auto;
}

.segment-edit-item {
  background: #fafafa;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
}

.segment-header {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 8px;
}

.segment-index {
  font-weight: bold;
  color: #1890ff;
  min-width: 30px;
}

.segment-params {
  font-size: 12px;
}

/* JSON编辑器样式 */
.json-editor {
  height: 100%;
}

.json-display {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
}

.no-data {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

/* 音频配置状态样式 */
.voice-assignment {
  border-top: 1px solid #e8e8e8;
  padding-top: 12px;
  margin-top: 8px;
}

.voice-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.voice-config-status {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.voice-configured,
.voice-not-configured,
.voice-not-in-library {
  display: flex;
  align-items: center;
  gap: 8px;
}

.voice-configured .ant-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.voice-not-configured .ant-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

.voice-not-in-library .ant-tag {
  display: flex;
  align-items: center;
  gap: 4px;
}

/* 声音选择样式 */
.voice-option {
  display: flex;
  align-items: center;
  gap: 8px;
  width: 100%;
}

.voice-name {
  font-weight: 500;
  flex: 1;
}

.voice-id {
  color: #666;
  font-size: 12px;
}

.voice-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

/* 暗黑模式适配 */
[data-theme="dark"] .analysis-content {
  background: transparent !important;
}

[data-theme="dark"] .loading-wrapper {
  background: transparent !important;
}

[data-theme="dark"] .editor-header {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .editor-header h4 {
  color: #fff !important;
}

[data-theme="dark"] .segment-count,
[data-theme="dark"] .character-stats {
  color: #8c8c8c !important;
}

[data-theme="dark"] .character-edit-item,
[data-theme="dark"] .segment-edit-item {
  background: #2d2d2d !important;
  border-color: #434343 !important;
  color: #434343 !important;
}

[data-theme="dark"] .character-edit-item:hover {
  border-color: #4a9eff !important;
  box-shadow: 0 2px 8px rgba(74, 158, 255, 0.2) !important;
}

[data-theme="dark"] .character-header {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .character-name {
  color: #fff !important;
}

[data-theme="dark"] .character-type {
  color: #8c8c8c !important;
}

[data-theme="dark"] .characters-stats {
  background: #1a1a1a !important;
}

[data-theme="dark"] .stat-card {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .stat-value {
  color: #4a9eff !important;
}

[data-theme="dark"] .stat-label {
  color: #8c8c8c !important;
}

[data-theme="dark"] .segment-index {
  color: #4a9eff !important;
}

[data-theme="dark"] .segment-params {
  color: #8c8c8c !important;
}

[data-theme="dark"] .json-display {
  background: #1a1a1a !important;
  border-color: #434343 !important;
  color: #434343 !important;
}

[data-theme="dark"] .voice-label {
  color: #8c8c8c !important;
}

[data-theme="dark"] .voice-name {
  color: #fff !important;
}

[data-theme="dark"] .voice-id {
  color: #8c8c8c !important;
}
</style> 