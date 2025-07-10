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
      <!-- 工具栏 -->
      <div class="analysis-toolbar">
        <div class="toolbar-right">
          <a-space>
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
        </div>
        <!-- <div class="toolbar-right">
          <a-space>
            <a-tag color="green">
              {{ processingInfo.total_segments || editableSegments.length }} 个片段
            </a-tag>
            <a-tag color="blue">
              {{ processingInfo.characters_found || editableCharacters.length }} 个角色
            </a-tag>
          </a-space>
        </div> -->
      </div>

      <!-- 分析结果tabs -->
      <div class="analysis-tabs">
        <a-tabs v-model:activeKey="activeSubTab" type="card">
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
                  </div>
                  <div class="segment-content">
                    <a-textarea
                      v-model:value="segment.text"
                      placeholder="文本内容"
                      :rows="2"
                      @change="markChanged"
                      :readonly="true"
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
                  <a-button size="small" @click="copyJson">
                    📋 复制JSON
                  </a-button>
                  <a-button size="small" @click="formatJson">
                    🎨 格式化
                  </a-button>
                  <a-button size="small" @click="downloadJson">
                    💾 下载JSON
                  </a-button>
                </a-space>
              </div>
              
              <div class="json-editor">
                <a-textarea
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
                  class="character-item"
                >
                  <div class="character-info">
                    <div class="character-avatar" :style="{ background: getCharacterColor(character.name) }">
                      <span>{{ getCharacterIcon(character.name) }}</span>
                    </div>
                    <div class="character-details">
                      <div class="character-name">
                        {{ character.name }}
                        <a-tag :color="getCharacterTypeColor(character.voice_type)" size="small">
                          {{ getCharacterTypeText(character.voice_type) }}
                        </a-tag>
                      </div>
                      <div class="character-count">
                        <a-tag color="blue">
                          第{{ index + 1 }}位 · {{ character.count || 0 }}次
                        </a-tag>
                        <span class="character-percentage">
                          ({{ getCharacterPercentage(character) }}%)
                        </span>
                      </div>
                    </div>
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
import { message } from 'ant-design-vue'

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

const activeSubTab = ref('segments')
const saving = ref(false)
const hasChanges = ref(false)

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

// 初始化可编辑数据
const initEditableData = () => {
  try {
    const synthesisJson = props.analysisData?.synthesis_json
    if (!synthesisJson) {
      console.log('没有synthesis_json数据')
      editableCharacters.value = []
      editableSegments.value = []
      return
    }
    
    console.log('synthesis_json结构:', synthesisJson)
    console.log('characters数据:', synthesisJson.characters)
    console.log('synthesis_plan数据:', synthesisJson.synthesis_plan)
    
    // 初始化角色数据
    if (synthesisJson.characters && Array.isArray(synthesisJson.characters)) {
      editableCharacters.value = synthesisJson.characters.map(char => ({
        name: char?.name || '未知角色',
        voice_type: char?.voice_type || 'neutral',
        count: 0
      }))
      
      // 统计角色使用次数
      const segments = Array.isArray(synthesisJson.synthesis_plan) ? synthesisJson.synthesis_plan : []
      segments.forEach(segment => {
        if (!segment?.speaker) return
        const character = editableCharacters.value.find(c => c.name === segment.speaker)
        if (character) {
          character.count = (character.count || 0) + 1
        }
      })
      
      // 按使用次数排序
      editableCharacters.value.sort((a, b) => (b.count || 0) - (a.count || 0))
    } else {
      // 从片段中提取角色
      const segments = Array.isArray(synthesisJson.synthesis_plan) ? synthesisJson.synthesis_plan : []
      console.log('从片段中提取角色，segments:', segments)
      const speakerMap = new Map()
      
      segments.forEach(segment => {
        if (!segment?.speaker) return
        const speaker = segment.speaker
        if (!speakerMap.has(speaker)) {
          speakerMap.set(speaker, {
            name: speaker,
            voice_type: speaker === '旁白' ? 'narrator' : 'neutral',
            count: 0
          })
        }
        const character = speakerMap.get(speaker)
        character.count = (character.count || 0) + 1
      })
      
      editableCharacters.value = Array.from(speakerMap.values())
        .sort((a, b) => (b.count || 0) - (a.count || 0))
    }
    
    // 初始化片段数据
    editableSegments.value = (Array.isArray(synthesisJson.synthesis_plan) ? synthesisJson.synthesis_plan : [])
      .filter(segment => segment && typeof segment === 'object') // 过滤掉无效片段
      .map(segment => ({
        segment_id: segment.segment_id || 0,
        speaker: segment.speaker || '',
        text: segment.text || '',
        voice_id: segment.voice_id || '',
        voice_name: segment.voice_name || ''
      }))
      
    console.log('处理后的角色数据:', editableCharacters.value)
    console.log('处理后的片段数据:', editableSegments.value)
  } catch (error) {
    console.error('初始化可编辑数据失败:', error)
    message.error('初始化可编辑数据失败')
    editableCharacters.value = []
    editableSegments.value = []
  }
}

// 监听分析数据变化
watch(() => props.analysisData, (newData) => {
  try {
    if (newData?.synthesis_json) {
      initEditableData()
      originalData.value = JSON.parse(JSON.stringify(newData))
      hasChanges.value = false
    } else {
      // 重置数据
      editableCharacters.value = []
      editableSegments.value = []
      originalData.value = null
      hasChanges.value = false
    }
  } catch (error) {
    console.error('初始化分析数据失败:', error)
    message.error('初始化分析数据失败')
    // 重置数据
    editableCharacters.value = []
    editableSegments.value = []
    originalData.value = null
    hasChanges.value = false
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
</script>

<style scoped>
.chapter-analysis {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100%;
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
}

.analysis-tabs :deep(.ant-tabs-content-holder) {
  height: calc(100vh - 400px);
  overflow: hidden;
}

.analysis-tabs :deep(.ant-tabs-tabpane) {
  height: 100%;
  overflow-y: auto;
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
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 12px;
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
}

.character-item {
  background: #f8fafc;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.character-info {
  display: flex;
  align-items: center;
  gap: 12px;
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
}

.character-details {
  flex: 1;
}

.character-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.character-count {
  display: flex;
  align-items: center;
  gap: 8px;
}

.character-percentage {
  font-size: 12px;
  color: #6b7280;
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