<template>
  <div class="chapter-analysis">
    <!-- 加载状态 -->
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载智能分析结果...">
        <div style="width: 100%"></div>
      </a-spin>
    </div>

    <!-- 有分析数据 -->
    <div v-else-if="analysisData" class="analysis-content">
      <div class="analysis-tabs">
        <a-tabs v-model="activeTab" type="card">
          <template #rightExtra>
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
                v-if="bookId && chapterId"
                type="default"
                @click="showDetectionDrawer"
                size="small"
              >
                🔍 智能检测
              </a-button>

              <a-button
                type="primary"
                @click="saveChanges"
                size="small"
                :loading="saving"
              >
                💾 保存修改
              </a-button>
            </a-space>
          </template>

          <!-- 合成片段tab -->
          <a-tab-pane key="segments" tab="📝 合成片段">
            <SynthesisSegmentEditor
              :segments="editableSegments"
              :characters="allAvailableCharacters"
              :loading="loading"
              @update:segments="handleSegmentsUpdate"
              @segment-change="handleSegmentChange"
              @character-change="handleCharacterChange"
              @refresh-characters="loadBookCharacters"
            />
          </a-tab-pane>

          <!-- JSON数据tab -->
          <a-tab-pane key="json" tab="🔧 JSON数据">
            <JsonDataViewer
              :analysis-data="analysisData"
              :editable-segments="editableSegments"
              :editable-characters="editableCharacters"
              :chapter="chapter"
              @data-updated="handleJsonChanged"
            />
          </a-tab-pane>

          <!-- 角色信息tab -->
          <a-tab-pane key="characters" tab="🎭 角色信息">
            <CharacterInfoViewer
              :characters="editableCharacters"
              :batch-creating="batchCreating"
              :loading-book-characters="loadingBookCharacters"
              :total-segments="editableSegments.length"
              @batch-create="showBatchCreateModal"
              @refresh-library="refreshCharacterLibrary"
            />
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>

    <!-- 无分析数据 -->
    <div v-else class="no-analysis">
      <a-empty description="该章节暂无智能分析数据" :image="false">
        <div class="empty-icon">🤖</div>
        <p>请先对章节进行智能准备</p>
        <a-button type="primary" @click="$emit('prepare-chapter')" :loading="preparingChapter"> 🎭 开始智能准备 </a-button>
      </a-empty>
    </div>

    <!-- 批量创建角色抽屉组件 -->
    <BatchCreateCharacterDrawer
      ref="batchCreateDrawerRef"
      :chapter="chapter"
      :missing-characters="missingCharacters"
      v-model:visible="batchCreateModalVisible"
      v-model:batch-creating="batchCreating"
      @characters-created="handleCharactersCreated"
      @refresh-library="refreshCharacterLibrary"
    />

    <!-- 智能检测抽屉 -->
    <a-drawer
      v-model:open="detectionDrawerVisible"
      title="🔍 智能检测"
      placement="right"
      :width="900"
      :closable="true"
      :mask-closable="true"
    >
      <IntelligentDetector
        v-if="detectionDrawerVisible && bookId && chapterId"
        ref="intelligentDetectorRef"
        :book-id="bookId"
        :chapter-id="chapterId"
        :segments="editableSegments"
        :characters="allAvailableCharacters"
        @segments-updated="handleSegmentsUpdate"
        @locate-segment="locateToSegment"
        @auto-save-fixes="handleAutoSaveFixes"
        @refresh-chapter-data="handleRefreshChapterData"
      />
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch, onMounted, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { charactersAPI } from '@/api'
import SynthesisSegmentEditor from './SynthesisSegmentEditor.vue'
import IntelligentDetector from './IntelligentDetector.vue'
import BatchCreateCharacterDrawer from './BatchCreateCharacterDrawer.vue'
import CharacterInfoViewer from './CharacterInfoViewer.vue'
import JsonDataViewer from './JsonDataViewer.vue'

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

const emit = defineEmits(['refresh', 'save', 'reload-chapter', 'prepare-chapter'])

// 响应式数据
const activeTab = ref('segments')
const saving = ref(false)
const hasChanges = ref(false)




const editableCharacters = ref([])
const editableSegments = ref([])
const originalData = ref(null)
const loadingBookCharacters = ref(false)
const bookCharacters = ref([])
const batchCreating = ref(false)
const batchCreateModalVisible = ref(false)
const detectionDrawerVisible = ref(false)

// 组件引用
const intelligentDetectorRef = ref(null)

// 计算属性
const missingCharacters = computed(() => {
  return editableCharacters.value.filter((char) => !char.in_character_library)
})

const missingCharactersCount = computed(() => {
  return missingCharacters.value.length
})

const isPreparationDisabled = computed(() => {
  return (
    props.preparingChapter ||
    props.preparationStatus?.analysis_status === 'processing' ||
    props.preparationStatus?.synthesis_status === 'processing'
  )
})

const allAvailableCharacters = computed(() => {
  const combined = [...editableCharacters.value, ...bookCharacters.value]
  const uniqueCharacters = []
  const seen = new Set()
  
  for (const char of combined) {
    if (!seen.has(char.name)) {
      seen.add(char.name)
      uniqueCharacters.push(char)
    }
  }
  
  return uniqueCharacters
})

const bookId = computed(() => props.chapter?.book_id)
const chapterId = computed(() => props.chapter?.id)

// 方法
const loadBookCharacters = async () => {
  if (!props.chapter?.book_id) {
    console.warn('缺少书籍ID，无法加载角色')
    return
  }

  loadingBookCharacters.value = true
  try {
    const response = await charactersAPI.getCharacters({ book_id: props.chapter.book_id })
    // 🔧 修复：适配后端返回的CharacterListResponse格式
    if (response.data?.characters) {
      bookCharacters.value = response.data.characters.map((char) => ({
        ...char,
        is_voice_configured: char.is_voice_configured || false,
        avatarUrl: char.avatarUrl || null
      }))
      console.log('本书角色加载成功:', bookCharacters.value.length, '个角色')
    } else if (response.data?.success && response.data.data) {
      // 兼容旧格式
      bookCharacters.value = response.data.data.map((char) => ({
        ...char,
        is_voice_configured: char.is_voice_configured || false,
        avatarUrl: char.avatarUrl || null
      }))
      console.log('本书角色加载成功:', bookCharacters.value.length, '个角色')
    } else {
      console.warn('加载角色失败: 响应格式不正确', response.data)
    }
  } catch (error) {
    console.error('加载角色失败:', error)
  } finally {
    loadingBookCharacters.value = false
  }
}

const forceRefreshSegments = async () => {
  console.log('[角色分析] 强制刷新segments数据')
  await nextTick()
  const temp = [...editableSegments.value]
  editableSegments.value = []
  await nextTick()
  editableSegments.value = temp
  console.log('[角色分析] 强制刷新完成，当前segments数量:', editableSegments.value.length)
}

const initEditableData = async () => {
  if (!props.analysisData?.synthesis_json) {
    console.warn('[角色分析] 没有有效的分析结果数据')
    return
  }

  const synthesisJson = props.analysisData.synthesis_json

  try {
    console.log('[角色分析] 开始提取角色信息')

    if (synthesisJson.characters && synthesisJson.characters.length > 0) {
      console.log('[角色分析] 使用characters字段')
      editableCharacters.value = synthesisJson.characters.map((char) => ({
        ...char,
        character_id: char.character_id || null,
        voice_id: char.voice_id || '',
        voice_name: char.voice_name || char.name || '未分配',
        voice_type: char.voice_type || (char.name === '旁白' ? 'narrator' : 'neutral'),
        count: char.count || 0,
        in_character_library: char.in_character_library || false,
        is_voice_configured: char.is_voice_configured || false,
        avatarUrl: char.avatarUrl || null
      }))
    } else {
      console.log('[角色分析] 从synthesis_plan中提取角色信息')
      const segments = synthesisJson.synthesis_plan || []
      const characterMap = new Map()

      segments.forEach((segment) => {
        const speaker = segment.speaker || segment.speaker_name || segment.character_name || segment.character || '未知'
        if (!characterMap.has(speaker)) {
          characterMap.set(speaker, {
            name: speaker,
            character_id: segment.character_id || null,
            voice_id: segment.voice_id || '',
            voice_name: segment.voice_name || speaker,
            voice_type: speaker === '旁白' ? 'narrator' : 'neutral',
            count: 0,
            in_character_library: segment.character_id ? true : false,
            is_voice_configured: segment.voice_id ? true : false,
            avatarUrl: null
          })
        }
        characterMap.get(speaker).count++
      })

      editableCharacters.value = Array.from(characterMap.values())
    }

    editableCharacters.value.sort((a, b) => (b.count || 0) - (a.count || 0))

    const segments = synthesisJson.synthesis_plan || []
    editableSegments.value = segments.map((segment, index) => {
      const mappedSegment = {
        ...segment,
        id: segment.id || segment.segment_id || `segment_${index}_${Date.now()}`,
        segment_id: segment.segment_id || (index + 1),
        chapter_id: segment.chapter_id || props.chapter?.id || null,
        chapter_number: segment.chapter_number || props.chapter?.number || 1,
        speaker: segment.speaker || '未知说话人',
        text: segment.text || '',
        _forceUpdate: Date.now(),
        character_id: segment.character_id || null,
        voice_id: segment.voice_id || '',
        voice_name: segment.voice_name || '未分配',
        text_type: segment.text_type || 'narration',
        confidence: segment.confidence || 0.9,
        detection_rule: segment.detection_rule || 'manual_input',
        timeStep: segment.timeStep || 32,
        pWeight: segment.pWeight || 2,
        tWeight: segment.tWeight || 3,
        narrator_mode: segment.narrator_mode !== undefined ? segment.narrator_mode : true,
        skip_ai_analysis: segment.skip_ai_analysis !== undefined ? segment.skip_ai_analysis : false
      }

      if (!mappedSegment.text) {
        console.warn(`⚠️ 段落 ${index} 缺少文本内容:`, segment)
      }
      if (!mappedSegment.speaker || mappedSegment.speaker === '未知说话人') {
        console.warn(`⚠️ 段落 ${index} 缺少说话人信息:`, segment)
      }

      return mappedSegment
    })

    originalData.value = JSON.parse(
      JSON.stringify({
        characters: editableCharacters.value,
        segments: editableSegments.value
      })
    )

    console.log('[角色分析] 数据初始化完成')
    hasChanges.value = false
    
    await nextTick()
    console.log('[角色分析] 强制重新渲染完成')
    
    await forceRefreshSegments()
  } catch (error) {
    console.error('[角色分析] 初始化数据失败:', error)
    message.error('初始化角色分析数据失败')
  }
}

const refreshCharacterLibrary = async () => {
  console.log('[ChapterAnalysis] 开始刷新角色配音库')
  await loadBookCharacters()
  
  // 🔥 重新同步角色库中的角色信息到editableCharacters
  editableCharacters.value = editableCharacters.value.map(char => {
    const bookChar = bookCharacters.value.find(bc => bc.name === char.name)
    if (bookChar) {
      console.log('[ChapterAnalysis] 同步角色库角色信息:', char.name, '->', bookChar)
      return {
        ...char,
        character_id: bookChar.id,
        voice_id: bookChar.voice_id || bookChar.id?.toString() || '',
        voice_name: bookChar.name,
        voice_type: bookChar.voice_type || char.voice_type || 'neutral',
        in_character_library: true,
        is_voice_configured: bookChar.is_voice_configured || !!(bookChar.voice_id || bookChar.id),
        avatarUrl: bookChar.avatarUrl || null
      }
    }
    return char
  })
  
  // 🔥 新增：同步更新段落中的角色信息
  console.log('[ChapterAnalysis] 开始同步段落角色信息')
  editableSegments.value = editableSegments.value.map(segment => {
    const bookChar = bookCharacters.value.find(bc => bc.name === segment.speaker)
    if (bookChar) {
      console.log('[ChapterAnalysis] 同步段落角色信息:', segment.speaker, segment.segment_id, '->', bookChar)
      return {
        ...segment,
        character_id: bookChar.id,
        voice_id: bookChar.voice_id || bookChar.id?.toString() || '',
        voice_name: bookChar.name,
        voice_type: bookChar.voice_type || segment.voice_type || 'neutral',
        _forceUpdate: Date.now()
      }
    }
    return segment
  })
  
  markChanged()
  message.success('角色配音库已刷新，段落信息已同步更新')
}

const markChanged = () => {
  hasChanges.value = true
}

const fixMissingFields = (segments) => {
  const existingSegmentIds = segments.map((s) => s.segment_id).filter((id) => id)
  const maxSegmentId = Math.max(...existingSegmentIds, 0)
  let newSegmentCounter = 1

  return segments.map((segment, index) => {
    if (!segment.segment_id || !segment.chapter_id || !segment.text_type) {
      console.log(`[修复段落] 修复段落 ${index + 1} 的缺失字段`)

      let newSegmentId = segment.segment_id
      if (!newSegmentId) {
        newSegmentId = maxSegmentId + newSegmentCounter
        newSegmentCounter++
      }

      return {
        ...segment,
        segment_id: newSegmentId,
        chapter_id: segment.chapter_id || props.chapter?.id || null,
        chapter_number: segment.chapter_number || props.chapter?.number || 1,
        text_type: segment.text_type || 'narration',
        confidence: segment.confidence || 0.9,
        detection_rule: segment.detection_rule || 'manual_input',
        timeStep: segment.timeStep || 32,
        pWeight: segment.pWeight || 2,
        tWeight: segment.tWeight || 3,
        narrator_mode: segment.narrator_mode !== undefined ? segment.narrator_mode : true,
        skip_ai_analysis: segment.skip_ai_analysis !== undefined ? segment.skip_ai_analysis : false,
        character_id: segment.character_id || null,
        voice_id: segment.voice_id || ''
      }
    }
    return segment
  })
}

const saveChanges = async () => {
  if (!hasChanges.value) {
    console.log('📝 没有检测到数据变化，但仍允许保存')
  }

  saving.value = true
  try {
    console.log('🚀 开始保存智能分析数据...')
    
    const fixedSegments = fixMissingFields(editableSegments.value)
    const currentTotalSegments = fixedSegments.length

    const updatedData = {
      ...props.analysisData,
      synthesis_json: {
        ...props.analysisData.synthesis_json,
        project_info: {
          ...props.analysisData.synthesis_json.project_info,
          total_segments: currentTotalSegments
        },
        processing_info: {
          ...props.analysisData.synthesis_json.processing_info,
          total_segments: currentTotalSegments
        },
        characters: editableCharacters.value,
        synthesis_plan: fixedSegments
      }
    }

    emit('save', updatedData)
    hasChanges.value = false
    message.success('保存成功！数据已更新到服务器')
  } catch (error) {
    console.error('❌ 保存失败:', error)
    message.error('保存失败: ' + (error.message || '未知错误'))
  } finally {
    saving.value = false
  }
}

// 事件处理方法
const handleSegmentsUpdate = (_segments) => {
  console.log('[ChapterAnalysis] 片段更新:', _segments.length, '个片段')
  editableSegments.value = _segments
  markChanged()
}

const handleSegmentChange = () => {
  console.log('[ChapterAnalysis] 片段内容变化')
  markChanged()
}

const handleCharacterChange = (segment, speaker) => {
  console.log('[ChapterAnalysis] 角色变化:', segment.id, speaker)
  markChanged()
}

const locateToSegment = (segmentIndex) => {
  console.log('[ChapterAnalysis] 定位片段:', segmentIndex)
  const segmentElement = document.querySelector(`[data-segment-index="${segmentIndex}"]`)
  if (segmentElement) {
    segmentElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
    segmentElement.classList.add('segment-highlighted')
    setTimeout(() => {
      segmentElement.classList.remove('segment-highlighted')
    }, 3000)
  }
}

const handleAutoSaveFixes = async () => {
  console.log('[ChapterAnalysis] 智能修复完成，直接刷新数据')
  try {
    // 🔥 关键修复：修复后不需要保存，后端已经保存了
    // 只需要重新加载最新数据到前端组件
    console.log('[ChapterAnalysis] 重新加载章节数据以获取修复后的结果')
    emit('reload-chapter')
    
    // 延迟显示成功消息，确保数据加载完成
    setTimeout(() => {
      message.success('智能修复完成，数据已刷新')
    }, 500)
  } catch (error) {
    console.error('[ChapterAnalysis] 刷新数据失败:', error)
    message.error('修复完成，但数据刷新失败，请手动刷新页面')
  }
}

// 🔥 新增：处理修复后的数据刷新
const handleRefreshChapterData = async () => {
  console.log('[ChapterAnalysis] 智能修复完成，刷新章节数据')
  try {
    // 触发父组件重新获取最新的章节数据
    emit('refresh')
    message.success('数据已刷新，修复结果已生效')
  } catch (error) {
    console.error('[ChapterAnalysis] 刷新章节数据失败:', error)
    message.warning('数据刷新失败，请手动刷新页面')
  }
}

const showDetectionDrawer = async () => {
  detectionDrawerVisible.value = true
  // 等待组件渲染完成后自动触发检测
  await nextTick()
  if (intelligentDetectorRef.value && intelligentDetectorRef.value.runDetection) {
    intelligentDetectorRef.value.runDetection()
  }
}



// 角色相关事件处理方法

const showBatchCreateModal = () => {
  console.log('[ChapterAnalysis] 尝试显示批量创建模态框')
  console.log('[ChapterAnalysis] missingCharactersCount:', missingCharactersCount.value)
  console.log('[ChapterAnalysis] missingCharacters:', missingCharacters.value)
  console.log('[ChapterAnalysis] editableCharacters:', editableCharacters.value)
  console.log('[ChapterAnalysis] batchCreateModalVisible 当前值:', batchCreateModalVisible.value)
  
  batchCreateModalVisible.value = true
  console.log('[ChapterAnalysis] batchCreateModalVisible 设置为:', batchCreateModalVisible.value)
}

const handleJsonChanged = (data) => {
  console.log('[ChapterAnalysis] JSON 数据已更改')
  if (data.segments) {
    editableSegments.value = data.segments
  }
  if (data.characters) {
    editableCharacters.value = data.characters
  }
  markChanged()
  message.success('JSON 数据已更新')
}

const handleCharactersCreated = (createdCharacters) => {
  console.log('[ChapterAnalysis] 角色创建完成:', createdCharacters)
  
  // 🔥 更新editableCharacters中的角色信息
  editableCharacters.value = editableCharacters.value.map(char => {
    const created = createdCharacters.find(c => c.name === char.name)
    if (created) {
      console.log('[ChapterAnalysis] 更新角色信息:', char.name, '->', created)
      return {
        ...char,
        character_id: created.id || created.character_id,
        voice_id: created.voice_id || created.id?.toString() || '',
        voice_name: created.name || char.name,
        voice_type: created.voice_type || char.voice_type || 'neutral',
        in_character_library: true,
        is_voice_configured: !!(created.voice_id || created.id),
        avatarUrl: created.avatarUrl || null
      }
    }
    return char
  })
  
  // 🔥 同时更新segments中引用这些角色的片段
  editableSegments.value = editableSegments.value.map(segment => {
    const created = createdCharacters.find(c => c.name === segment.speaker)
    if (created) {
      console.log('[ChapterAnalysis] 更新片段角色信息:', segment.speaker, segment.segment_id)
      return {
        ...segment,
        character_id: created.id || created.character_id,
        voice_id: created.voice_id || created.id?.toString() || '',
        voice_name: created.name || segment.speaker,
        voice_type: created.voice_type || segment.voice_type || 'neutral',
        _forceUpdate: Date.now()
      }
    }
    return segment
  })
  
  // 🔥 刷新角色库数据
  loadBookCharacters()
  
  // 标记数据已更改并自动保存
  markChanged()
  
  // 延迟自动保存，确保数据完全更新
  setTimeout(async () => {
    try {
      console.log('[ChapterAnalysis] 自动保存更新后的角色数据')
      await saveChanges()
      message.success(`成功创建 ${createdCharacters.length} 个角色并自动保存`)
    } catch (error) {
      console.error('[ChapterAnalysis] 自动保存失败:', error)
      message.error('角色创建成功，但自动保存失败，请手动保存')
    }
  }, 1000)
}

// 监听器
watch(
  () => props.analysisData,
  async (newData) => {
    console.log('[角色分析] 监听到analysisData变化:', newData)
    if (newData) {
      console.log('[角色分析] 开始初始化可编辑数据...')
      await initEditableData()
      console.log('[角色分析] 初始化完成，当前角色数:', editableCharacters.value.length)
    } else {
      console.log('[角色分析] analysisData为空，清空编辑数据')
      editableCharacters.value = []
      editableSegments.value = []
    }
  },
  { immediate: true, deep: true }
)

watch(
  () => [props.analysisData, bookCharacters.value],
  ([analysisData, bookChars]) => {
    if (!analysisData && bookChars.length > 0 && editableCharacters.value.length === 0) {
      console.log('[角色分析] 基于角色库创建基础角色选项')
      editableCharacters.value = bookChars.map(char => ({
        name: char.name,
        character_id: char.id,
        voice_id: char.id.toString(),
        voice_name: char.name,
        voice_type: char.voice_type || 'neutral',
        count: 0,
        in_character_library: true,
        is_voice_configured: char.is_voice_configured || false,
        avatarUrl: char.avatarUrl || null
      }))
      console.log('[角色分析] 基础角色创建完成:', editableCharacters.value.length, '个角色')
    }
  },
  { deep: true }
)

watch(
  () => props.chapter,
  (newChapter) => {
    if (newChapter?.book_id) {
      loadBookCharacters()
    }
  },
  { immediate: true }
)

onMounted(() => {
  if (props.chapter?.book_id) {
    loadBookCharacters()
  }
})
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

.analysis-tabs {
  flex: 1;
  overflow: hidden;
}

.analysis-tabs :deep(.ant-tabs) {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.analysis-tabs :deep(.ant-tabs-nav) {
  background: var(--component-background);
  border-bottom: 1px solid var(--border-color-base);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.analysis-tabs :deep(.ant-tabs-nav::before) {
  display: none;
}

.analysis-tabs :deep(.ant-tabs-nav-wrap) {
  flex: 1;
}

.analysis-tabs :deep(.ant-tabs-extra-content) {
  margin-left: 16px;
}

.analysis-tabs :deep(.ant-tabs-content-holder) {
  flex: 1;
  overflow: auto;
}

.segment-highlighted {
  background: var(--ant-primary-1);
  border-left: 3px solid var(--ant-primary-color);
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
  color: var(--ant-text-color-secondary);
  margin: 8px 0 16px 0;
}
</style>
