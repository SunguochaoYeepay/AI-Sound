<template>
  <div class="synthesis-segment-editor">
    <!-- 头部工具栏 -->
    <div class="editor-toolbar">

      
      <div class="toolbar-left">
        <a-space>
           <a-tag color="blue" v-if="segments.length > 0">
          共 {{ segments.length }} 个片段
        </a-tag>
          <a-button size="small" @click="addSegment">
            <template #icon><PlusOutlined /></template>
            添加片段
          </a-button>
          <a-button size="small" @click="refreshCharacters" :loading="loadingCharacters">
            <template #icon><ReloadOutlined /></template>
            刷新角色
          </a-button>
          <a-select
            v-model:value="filterCharacter"
            placeholder="筛选角色"
            style="width: 120px"
            allowClear
            size="small"
          >
            <a-select-option v-for="char in availableCharacters" :key="char.name" :value="char.name">
              {{ char.name }}
            </a-select-option>
          </a-select>
        </a-space>
      </div>
    </div>

    <!-- 片段列表 -->
    <div class="segments-container">
      <div v-if="segments.length === 0" class="empty-state">
        <a-empty description="暂无片段数据">
          <a-button type="primary" @click="addSegment">添加第一个片段</a-button>
        </a-empty>
      </div>

      <div v-else class="segments-list">
        <div
          v-for="(segment, index) in filteredSegments"
          :key="segment.id"
          class="segment-item"
          :class="{
            'segment-highlighted': filterCharacter && segment.speaker === filterCharacter,
            'segment-dimmed': filterCharacter && segment.speaker !== filterCharacter
          }"
        >
          <!-- 片段头部 -->
          <div class="segment-header">
            <div class="segment-info">
              <span class="segment-number">#{{ index + 1 }}</span>
              
              <!-- 说话人选择 -->
              <a-select
                v-model:value="segment.speaker"
                placeholder="选择说话人"
                style="width: 160px"
                @change="handleSpeakerChange(segment, $event)"
                allowClear
                show-search
                :filter-option="filterSpeakerOption"
              >
                <a-select-option
                  v-for="character in availableCharacters"
                  :key="character.name"
                  :value="character.name"
                >
                  <div class="character-option">
                    <span>{{ character.name }}</span>
                    <a-tag
                      v-if="character.is_voice_configured"
                      color="green"
                      size="small"
                    >
                      已配音
                    </a-tag>
                    <a-tag v-else color="orange" size="small">未配音</a-tag>
                  </div>
                </a-select-option>
              </a-select>

              <!-- 角色标签 -->
              <a-tag
                v-if="segment.speaker"
                :color="getCharacterColor(segment.speaker)"
                size="small"
              >
                {{ segment.speaker }}
              </a-tag>
            </div>

            <!-- 操作按钮 -->
            <div class="segment-actions">
              <a-button-group size="small">
                <a-button @click="moveSegmentUp(index)" :disabled="index === 0" title="上移">
                  <template #icon><ArrowUpOutlined /></template>
                </a-button>
                <a-button 
                  @click="moveSegmentDown(index)" 
                  :disabled="index === segments.length - 1" 
                  title="下移"
                >
                  <template #icon><ArrowDownOutlined /></template>
                </a-button>
                <a-button @click="duplicateSegment(index)" title="复制">
                  <template #icon><CopyOutlined /></template>
                </a-button>
                <a-button 
                  @click="detectSegmentSplit(index)" 
                  title="智能检测"
                  :loading="detectingSegments.has(index)"
                  type="primary"
                  ghost
                >
                  <template #icon><SearchOutlined /></template>
                </a-button>
                <a-button 
                  @click="deleteSegment(index)" 
                  danger 
                  :disabled="segments.length <= 1"
                  title="删除"
                >
                  <template #icon><DeleteOutlined /></template>
                </a-button>
              </a-button-group>
            </div>
          </div>

          <!-- 文本内容 -->
          <div class="segment-content">
            <a-textarea
              v-model:value="segment.text"
              placeholder="请输入片段文本内容..."
              :auto-size="{ minRows: 2, maxRows: 8 }"
                             @change="handleTextChange"
              :class="{ 'empty-warning': !segment.text || segment.text.trim() === '' }"
            />
            
            <!-- 空文本提示 -->
            <div v-if="!segment.text || segment.text.trim() === ''" class="empty-hint">
              💡 此片段文本为空，请输入内容或从分析结果中导入
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { detectSingleSegment } from '@/api'
import {
  PlusOutlined,
  ReloadOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined,
  CopyOutlined,
  DeleteOutlined,
  SearchOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  // 片段数据
  segments: {
    type: Array,
    default: () => []
  },
  // 可用角色
  characters: {
    type: Array,
    default: () => []
  },
  // 是否加载中
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits([
  'update:segments',
  'segment-change',
  'character-change',
  'refresh-characters'
])

// 响应式数据
const filterCharacter = ref(null)
const loadingCharacters = ref(false)
const detectingSegments = ref(new Set()) // 正在检测的段落索引集合

// 内部片段数据
const internalSegments = ref([])

// 可用角色（包含基础角色选项）
const availableCharacters = computed(() => {
  const baseCharacters = [
    { name: '旁白', voice_type: 'narrator', is_voice_configured: true },
    { name: '未知角色', voice_type: 'neutral', is_voice_configured: false }
  ]
  
  return [...baseCharacters, ...props.characters]
})

// 过滤后的片段
const filteredSegments = computed(() => {
  if (!filterCharacter.value) {
    return internalSegments.value
  }
  return internalSegments.value.filter(segment => 
    segment.speaker === filterCharacter.value
  )
})

// 初始化数据
const initSegments = () => {
  console.log('[SynthesisSegmentEditor] 初始化片段数据:', props.segments.length)
  
  internalSegments.value = props.segments.map((segment, index) => ({
    ...segment, // 保留所有原始字段
    // 确保关键字段存在
    id: segment.id || `segment_${Date.now()}_${index}`,
    segment_id: segment.segment_id || index + 1,
    speaker: segment.speaker || '',
    text: segment.text || '',
    character_id: segment.character_id || null,
    voice_id: segment.voice_id || '',
    text_type: segment.text_type || 'dialogue',
    confidence: segment.confidence || 1.0,
    // 强制更新标记
    _forceUpdate: Date.now()
  }))
  
  console.log('[SynthesisSegmentEditor] 初始化完成:', {
    片段数量: internalSegments.value.length,
    第一个片段: internalSegments.value[0] || '无片段'
  })
}

// 监听props变化
watch(() => props.segments, initSegments, { immediate: true, deep: true })

// 发送数据变化
const emitChange = () => {
  emit('update:segments', internalSegments.value)
  emit('segment-change', internalSegments.value)
}

// 添加片段
const addSegment = () => {
  const newSegment = {
    id: `segment_${Date.now()}`,
    segment_id: internalSegments.value.length + 1,
    speaker: '',
    text: '',
    character_id: null,
    voice_id: '',
    voice_name: '未分配',
    text_type: 'dialogue',
    confidence: 1.0,
    detection_rule: 'manual_input',
    timeStep: 32,
    pWeight: 2,
    tWeight: 3,
    narrator_mode: true,
    skip_ai_analysis: false,
    _forceUpdate: Date.now()
  }
  
  internalSegments.value.push(newSegment)
  emitChange()
  message.success('已添加新片段')
}

// 删除片段
const deleteSegment = (index) => {
  if (internalSegments.value.length <= 1) {
    message.warning('至少需要保留一个片段')
    return
  }
  
  internalSegments.value.splice(index, 1)
  emitChange()
  message.success('片段已删除')
}

// 复制片段
const duplicateSegment = (index) => {
  const original = internalSegments.value[index]
  const duplicate = {
    ...original,
    id: `segment_${Date.now()}`,
    segment_id: internalSegments.value.length + 1,
    _forceUpdate: Date.now()
  }
  
  internalSegments.value.splice(index + 1, 0, duplicate)
  emitChange()
  message.success('片段已复制')
}

// 上移片段
const moveSegmentUp = (index) => {
  if (index === 0) return
  
  const temp = internalSegments.value[index]
  internalSegments.value[index] = internalSegments.value[index - 1]
  internalSegments.value[index - 1] = temp
  emitChange()
}

// 下移片段
const moveSegmentDown = (index) => {
  if (index === internalSegments.value.length - 1) return
  
  const temp = internalSegments.value[index]
  internalSegments.value[index] = internalSegments.value[index + 1]
  internalSegments.value[index + 1] = temp
  emitChange()
}

// 🔥 单段落智能检测
const detectSegmentSplit = async (index) => {
  const segment = internalSegments.value[index]
  if (!segment || !segment.text?.trim()) {
    message.warning('该段落没有文本内容，无法检测')
    return
  }

  console.log(`[段落检测] 开始检测段落 ${index}: ${segment.text.substring(0, 50)}...`)
  
  // 设置检测状态
  detectingSegments.value.add(index)
  
  try {
    const response = await detectSingleSegment(segment.text, index)
    const result = response.data

    if (result.success && result.issues && result.issues.length > 0) {
      const issue = result.issues[0] // 取第一个问题
      
      if (issue.issue_type === 'segment_split_needed' && issue.fix_data?.suggested_segments) {
        // 显示拆分建议
        showSplitSuggestion(index, issue.fix_data.suggested_segments, issue.description)
      } else {
        message.info('该段落无需拆分')
      }
    } else {
      message.info('该段落无需拆分')
    }
  } catch (error) {
    console.error('[段落检测] 检测失败:', error)
    message.error('检测失败: ' + (error.response?.data?.message || error.message))
  } finally {
    // 清除检测状态
    detectingSegments.value.delete(index)
  }
}

// 显示拆分建议
const showSplitSuggestion = (originalIndex, suggestedSegments, description) => {
  console.log('[段落检测] 收到拆分建议:', suggestedSegments)
  
  // 创建确认对话框
  Modal.confirm({
    title: '🔍 检测到混合文本',
    content: `${description}\n\n是否要拆分为 ${suggestedSegments.length} 个段落？`,
    okText: '拆分',
    cancelText: '取消',
    onOk: () => {
      applySplitSuggestion(originalIndex, suggestedSegments)
    }
  })
}

// 应用拆分建议
const applySplitSuggestion = (originalIndex, suggestedSegments) => {
  try {
    const originalSegment = internalSegments.value[originalIndex]
    
    // 创建新的段落数组
    const newSegments = suggestedSegments.map((suggested, subIndex) => ({
      ...originalSegment, // 继承原段落的其他属性
      id: `segment_${Date.now()}_${subIndex}`,
      segment_id: originalSegment.segment_id + subIndex,
      text: suggested.text || '',
      speaker: suggested.speaker || '旁白',
      text_type: suggested.text_type || 'narration',
      confidence: suggested.confidence || 0.9,
      detection_rule: 'ai_split_detection',
      _forceUpdate: Date.now()
    }))
    
    // 替换原段落
    internalSegments.value.splice(originalIndex, 1, ...newSegments)
    
    // 重新编号所有段落
    internalSegments.value.forEach((segment, index) => {
      segment.segment_id = index + 1
    })
    
    emitChange()
    message.success(`已拆分为 ${newSegments.length} 个段落`)
    
    console.log('[段落检测] 拆分应用成功:', newSegments)
  } catch (error) {
    console.error('[段落检测] 应用拆分失败:', error)
    message.error('拆分失败')
  }
}

// 说话人变化处理
const handleSpeakerChange = (segment, speaker) => {
  console.log('[SynthesisSegmentEditor] 说话人变化:', segment.id, speaker)
  
  // 查找角色信息
  const character = availableCharacters.value.find(char => char.name === speaker)
  if (character) {
    segment.character_id = character.id || null
    segment.voice_id = character.voice_id || ''
  }
  
  emitChange()
  emit('character-change', segment, speaker)
}

// 文本变化处理
const handleTextChange = () => {
  emitChange()
}

// 刷新角色
const refreshCharacters = async () => {
  loadingCharacters.value = true
  try {
    emit('refresh-characters')
    message.success('角色列表已刷新')
  } catch (error) {
    message.error('刷新角色失败')
  } finally {
    loadingCharacters.value = false
  }
}

// 角色搜索过滤
const filterSpeakerOption = (input, option) => {
  return option.children[0].children.toLowerCase().includes(input.toLowerCase())
}

// 获取角色颜色
const getCharacterColor = (name) => {
  const colors = ['blue', 'green', 'orange', 'purple', 'red', 'cyan']
  const hash = name.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[hash % colors.length]
}

// 组件挂载时初始化
onMounted(() => {
  console.log('[SynthesisSegmentEditor] 组件已挂载')
  initSegments()
})
</script>

<style scoped>
.synthesis-segment-editor {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border-bottom: 1px solid var(--ant-border-color-split);
  background: var(--ant-background-color-base);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-left h4 {
  margin: 0;
  color: var(--ant-heading-color);
}

.segments-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 300px;
}

.segments-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.segment-item {
  border: 1px solid var(--ant-border-color-base);
  border-radius: 8px;
  padding: 16px;
  background: var(--ant-component-background);
  transition: all 0.2s ease;
}

.segment-item:hover {
  border-color: var(--ant-primary-color);
  box-shadow: 0 2px 8px var(--ant-primary-color-shadow);
}

.segment-highlighted {
  border-color: var(--ant-success-color);
  background: var(--ant-success-bg);
}

.segment-dimmed {
  opacity: 0.6;
}

.segment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.segment-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.segment-number {
  font-weight: 600;
  color: var(--ant-primary-color);
  min-width: 40px;
}

.character-option {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.segment-actions {
  opacity: 0;
  transition: opacity 0.2s ease;
}

.segment-item:hover .segment-actions {
  opacity: 1;
}

.segment-content {
  margin-top: 8px;
}

.empty-warning {
  border-color: var(--ant-error-color) !important;
  background-color: var(--ant-error-bg) !important;
}

.empty-hint {
  margin-top: 8px;
  padding: 8px 12px;
  background: var(--ant-warning-bg);
  border: 1px solid var(--ant-warning-color-border);
  border-radius: 4px;
  font-size: 12px;
  color: var(--ant-warning-color);
}

/* 响应式设计 */
@media (max-width: 768px) {
  .editor-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: flex-start;
  }
  
  .segment-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .segment-actions {
    opacity: 1; /* 移动端始终显示 */
  }
}
</style>