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
                  <div class="character-icon">
                    {{ getCharacterIcon(character.name) }}
                  </div>
                  <div class="character-info">
                    <div class="character-name">{{ character.name }}</div>
                    <div class="character-count">
                      <a-tag color="blue">{{ character.count || 0 }}次</a-tag>
                      <span class="character-type">{{ getCharacterTypeText(character.voice_type) }}</span>
                    </div>
                  </div>
                </div>
                
                <!-- 声音分配区域 -->
                <div class="voice-assignment">
                  <div class="voice-label">分配声音：</div>
                  <a-select
                    v-model:value="character.voice_id"
                    placeholder="选择声音"
                    style="width: 200px;"
                    @change="(value) => onVoiceAssign(character, value)"
                    allowClear
                    showSearch
                    :filterOption="filterVoiceOption"
                    optionFilterProp="children"
                  >
                    <a-select-option value="">未分配</a-select-option>
                    <a-select-option 
                      v-for="voice in availableVoices" 
                      :key="voice.id"
                      :value="voice.id"
                      :title="`${voice.name} - ${getVoiceTypeLabel(voice.type)} - ${voice.description || '暂无描述'}`"
                    >
                      {{ voice.name }} ({{ getVoiceTypeLabel(voice.type) }})
                    </a-select-option>
                  </a-select>
                  
                  <div class="voice-status" v-if="character.voice_id">
                    <a-tag color="green">{{ character.voice_name || '已分配' }}</a-tag>
                    <a-button 
                      type="link" 
                      size="small"
                      @click="testVoice(character)"
                      title="测试声音效果"
                    >
                      🔊 试听
                    </a-button>
                  </div>
                  <div class="voice-status" v-else>
                    <a-tag color="orange">未分配声音</a-tag>
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

// 新增：可用声音列表
const availableVoices = ref([])

// 音频服务实例
const audioService = getAudioService()

// 计算属性
const processingInfo = computed(() => {
  return analysisData.value?.processing_info || {}
})

// 监听visible变化
watch(() => props.visible, (newVal) => {
  if (newVal && props.chapterId) {
    loadAnalysisData()
    loadAvailableVoices()
  }
})

// 监听chapterId变化
watch(() => props.chapterId, (newVal) => {
  if (newVal && props.visible) {
    loadAnalysisData()
  }
})

// 监听visible变化，加载声音库
watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadVoiceLibrary()
  }
})

// 加载声音库
const loadVoiceLibrary = async () => {
  try {
    const response = await charactersAPI.getVoiceProfiles()
    if (response.data && response.data.success) {
      availableVoices.value = response.data.data || []
      console.log('[EditableAnalysisDrawer] 加载声音库:', availableVoices.value.length, '个声音')
    } else {
      console.warn('[EditableAnalysisDrawer] 声音库加载失败:', response.data)
      availableVoices.value = []
    }
  } catch (error) {
    console.error('[EditableAnalysisDrawer] 声音库加载错误:', error)
    availableVoices.value = []
  }
}

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



// 声音分配
const onVoiceAssign = (character, voiceId) => {
  console.log('[EditableAnalysisDrawer] 分配声音:', character.name, '→', voiceId)
  
  if (voiceId) {
    const voice = availableVoices.value.find(v => v.id == voiceId)
    if (voice) {
      character.voice_id = voiceId
      character.voice_name = voice.name
      console.log('[EditableAnalysisDrawer] 声音分配成功:', character.name, '→', voice.name)
      
      // 同步更新synthesis_plan中对应的segments
      editableSegments.value.forEach(segment => {
        if (segment.speaker === character.name) {
          segment.voice_id = voiceId
          segment.voice_name = voice.name
        }
      })
    }
  } else {
    character.voice_id = ''
    character.voice_name = '未分配'
    console.log('[EditableAnalysisDrawer] 取消声音分配:', character.name)
    
    // 同步更新synthesis_plan中对应的segments
    editableSegments.value.forEach(segment => {
      if (segment.speaker === character.name) {
        segment.voice_id = ''
        segment.voice_name = '未分配'
      }
    })
  }
  
  markChanged()
}

// 测试声音
const testVoice = async (character) => {
  if (!character.voice_id) {
    message.warning('请先分配声音')
    return
  }
  
  try {
    const testText = `你好，我是${character.name}，这是声音测试。`
    console.log('[EditableAnalysisDrawer] 测试声音:', character.name, testText)
    
    const response = await charactersAPI.testVoiceSynthesis(character.voice_id, {
      text: testText,
      time_step: 20,
      p_weight: 1.0,
      t_weight: 1.0
    })
    
    if (response.data && response.data.success) {
      console.log('[EditableAnalysisDrawer] API响应完整数据:', response.data)
      console.log('[EditableAnalysisDrawer] 音频URL详细检查:', {
        audio_url: response.data.audio_url,
        audioUrl: response.data.audioUrl, 
        keys: Object.keys(response.data)
      })
      // 🔧 修复：使用正确的字段名
      const audioUrl = response.data.audioUrl || response.data.audio_url
      
      console.log('[EditableAnalysisDrawer] 准备播放音频:', {
        audioUrl: audioUrl,
        title: `${character.name} - 声音试听`,
        audioService: audioService
      })
      
      if (!audioUrl) {
        console.error('[EditableAnalysisDrawer] 音频URL为空!')
        message.error('获取音频URL失败')
        return
      }
      
      // 🔍 测试音频URL是否可以直接访问
      console.log('[EditableAnalysisDrawer] 测试音频URL直接访问...')
      try {
        const testResponse = await fetch(audioUrl, { 
          method: 'HEAD',
          mode: 'cors'
        })
        console.log('[EditableAnalysisDrawer] URL访问测试结果:', {
          status: testResponse.status,
          headers: Object.fromEntries(testResponse.headers.entries()),
          url: audioUrl
        })
      } catch (fetchError) {
        console.error('[EditableAnalysisDrawer] URL访问测试失败:', fetchError)
      }
      
      try {
        await audioService.playCustomAudio(audioUrl, `${character.name} - 声音试听`, {
          voiceId: character.voice_id,
          voiceName: character.name,
          testText
        })
        console.log('[EditableAnalysisDrawer] playCustomAudio 调用成功')
        message.success(`正在播放${character.name}的声音测试`)
      } catch (playError) {
        console.error('[EditableAnalysisDrawer] playCustomAudio 调用失败:', playError)
        message.error('播放音频失败')
      }
    } else {
      message.error('声音测试失败')
    }
  } catch (error) {
    console.error('[EditableAnalysisDrawer] 声音测试错误:', error)
    message.error('声音测试失败')
  }
}

// 声音搜索过滤
const filterVoiceOption = (input, option) => {
  if (!input) return true
  
  const searchText = input.toLowerCase()
  
  // 获取对应的声音数据
  const voice = availableVoices.value.find(v => v.id == option.value)
  if (!voice) return false
  
  // 多维度搜索：名称、类型、描述
  const searchFields = [
    voice.name || '',
    voice.type || '',
    getVoiceTypeLabel(voice.type) || '',
    voice.description || '',
    voice.tags ? voice.tags.join(' ') : ''
  ].join(' ').toLowerCase()
  
  return searchFields.includes(searchText)
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

// 新增：加载可用声音列表
const loadAvailableVoices = async () => {
  try {
    const response = await charactersAPI.getVoiceProfiles({ status: 'active' })
    if (response.data.success) {
      availableVoices.value = response.data.data
      console.log('加载了可用声音:', availableVoices.value.length, '个')
    }
  } catch (error) {
    console.error('加载声音列表失败:', error)
    // 如果API调用失败，使用默认的声音列表
    availableVoices.value = [
      { id: '1', name: '孙悟空声音', type: 'male' },
      { id: '2', name: '唐僧声音', type: 'male' },
      { id: '3', name: '白骨精声音', type: 'female' },
      { id: '4', name: '玉皇大帝声音', type: 'male' },
      { id: '5', name: '如来佛祖声音', type: 'male' },
      { id: '6', name: '太上老君声音', type: 'male' },
      { id: '7', name: '系统旁白', type: 'narrator' },
      { id: '8', name: '女性旁白', type: 'female' },
      { id: '9', name: '男性旁白', type: 'male' }
    ]
  }
}

// 新增：获取声音类型标签
const getVoiceTypeLabel = (type) => {
  const labels = {
    'male': '男声',
    'female': '女声',
    'child': '童声',
    'neutral': '中性',
    'narrator': '旁白'
  }
  return labels[type] || type
}

// 新增：获取声音类型颜色
const getVoiceTypeColor = (type) => {
  const colors = {
    'male': 'blue',
    'female': 'pink',
    'child': 'orange',
    'neutral': 'purple',
    'narrator': 'green'
  }
  return colors[type] || 'default'
}

// 新增：处理声音选择变化
const handleVoiceChange = (character, voiceId) => {
  const selectedVoice = availableVoices.value.find(voice => voice.id === voiceId)
  if (selectedVoice) {
    character.voice_id = voiceId
    character.voice_name = selectedVoice.name
    character.voice_type = selectedVoice.type
  } else {
    character.voice_id = ''
    character.voice_name = ''
  }
  markChanged()
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

onMounted(() => {
  // 加载可用声音列表
  loadAvailableVoices()
})
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

.characters-stats {
  background: #f8fafc;
  border-radius: 8px;
  padding: 16px;
}

.stat-card {
  text-align: center;
  padding: 12px;
  background: white;
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

/* 声音分配样式 */
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

.voice-status {
  margin-top: 8px;
  display: flex;
  align-items: center;
  gap: 8px;
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
</style> 