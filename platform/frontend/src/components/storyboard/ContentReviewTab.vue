<template>
  <div class="content-review-container">
    <!-- 进度监控 -->
    <ProgressMonitor :session-id="sessionId" />

    <!-- 章节选择器 -->
    <ChapterSelector
      :chapters="chapters"
      :chapters-loading="chaptersLoading"
      :selected-chapter="selectedChapter"
      :current-chapter-status="currentChapterStatus"
      :analyzing-chapter="analyzingChapter"
      :segmenting-chapter="segmentingChapter"
      @chapter-change="handleChapterChange"
      @analyze-chapter="analyzeCurrentChapter"
      @smart-segmentation="handleSmartSegmentation"
    />

    <!-- 主要内容区域 -->
    <div class="content-review-layout">
      <!-- 左侧：原始文本 -->
      <OriginalTextPanel 
        :loading="loading"
        :chapter-content="chapterContent"
        :text-segments="textSegments"
        :timeline-details="timelineDetails"
        :chapter="reviewData?.chapter"
        @six-card-analysis="handleSixCardAnalysis"
      />

      <!-- 右侧：剧本详情 -->
      <ScriptDetailPanel 
        :loading="loading"
        :script-segments="scriptSegments"
        :review-data="reviewData"
        :chapter="reviewData?.chapter"
        :six-card-results="sixCardResults"
        :selected-segment-index="selectedSegmentIndex"
        @segment-click="handleScriptSegmentClick"
        @card-click="openCardDrawer"
      />
    </div>

    <!-- 卡片详情抽屉 -->
    <CardDetailDrawer 
      :open="cardDrawerVisible"
      :card="selectedCard"
      @update:visible="cardDrawerVisible = $event"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import CardDetailDrawer from './CardDetailDrawer.vue'
import ProgressMonitor from './ProgressMonitor.vue'
import ChapterSelector from './ChapterSelector.vue'
import OriginalTextPanel from './OriginalTextPanel.vue'
import ScriptDetailPanel from './ScriptDetailPanel.vue'
import { storyboardAPI } from '@/api/storyboard'

// Props
const props = defineProps({
  sessionId: {
    type: [String, Number],
    required: true
  }
})



// 响应式数据
const cardDrawerVisible = ref(false)
const selectedCard = ref(null)
const selectedChapter = ref('')  // 不设置初始值，让loadChapters来设置

// 添加章节列表数据
const chapters = ref([])
const chaptersLoading = ref(false)

// 文本段落数据
const textSegments = ref([])
const chapterContent = ref('')
const reviewData = ref(null)
const loading = ref(false)

// 时间轴详情
const timelineDetails = ref([])



// 分段状态
const segmentingChapter = ref(false)

// 剧本详情
const scriptSegments = ref([])

// 章节分析状态
const analyzingChapter = ref(false)
const currentChapterStatus = ref('pending')

// 段落分析结果
const sixCardResults = ref(null)
const selectedSegmentIndex = ref(null)

// 处理段落分析结果
const handleSixCardAnalysis = (data) => {
  selectedSegmentIndex.value = data.segmentIndex
  
  // 如果是单个段落分析，追加到现有结果中
  if (data.results && data.results.length > 0) {
    if (!sixCardResults.value) {
      sixCardResults.value = []
    }
    
    // 检查是否已存在相同段落的分析结果
    const newResults = data.results.filter(newResult => {
      const newSegmentIndex = newResult._metadata?.segment_index
      if (newSegmentIndex === undefined) return true
      
      // 移除已存在的相同段落分析结果
      sixCardResults.value = sixCardResults.value.filter(existingResult => {
        const existingSegmentIndex = existingResult._metadata?.segment_index
        return existingSegmentIndex !== newSegmentIndex
      })
      
      return true
    })
    
    // 追加新结果
    sixCardResults.value.push(...newResults)
  }
  
  // 显示分析结果在右侧面板
  console.log('收到段落分析结果:', data)
  console.log('当前所有段落分析结果:', sixCardResults.value)
}

// 加载章节数据
const loadChapterData = async (chapterId) => {
  if (!props.sessionId || !chapterId) return

  loading.value = true
  try {
         // 获取分镜确认页面的数据（包含智能分段和卡片数据）
     const response = await storyboardAPI.getStoryboardReviewData(props.sessionId, chapterId)
     
     console.log('🔍 API响应数据:', response.data)

     // 直接使用响应数据，不需要额外的API调用
     reviewData.value = response.data
    
    // 从响应数据中获取章节内容
    if (response.data.chapter?.content) {
      chapterContent.value = response.data.chapter.content
    } else {
      chapterContent.value = `第${chapterId}章\n\n[章节内容加载中...]`
    }
    
    // 处理音频剧本卡片数据，转换为剧本格式
    const scriptCards = response.data.cards?.audio_script || []
    if (scriptCards.length > 0) {
             const scriptCard = scriptCards[0]
      
      // 确保script_segments是数组格式
      let segmentsData = scriptCard.content?.script_segments || []
      if (typeof segmentsData === 'string') {
        try {
          segmentsData = JSON.parse(segmentsData)
        } catch (e) {
          console.error('解析script_segments失败:', e)
          segmentsData = []
        }
      }
      
      // 转换为剧本格式
      scriptSegments.value = segmentsData.map((segment, index) => {
        // 从dialogue.content中提取对话内容
        let dialogueContent = []
        if (segment.dialogue && segment.dialogue.content) {
          if (Array.isArray(segment.dialogue.content)) {
            dialogueContent = segment.dialogue.content
          } else {
            dialogueContent = [{ content: segment.dialogue.content, speaker: segment.dialogue.speaker || '旁白' }]
          }
        }
        
        // 判断是对话还是旁白
        const isDialogue = dialogueContent.length > 0 && 
                          dialogueContent.some(item => item.content && item.content !== '对话内容')
        
        // 获取主要对话内容
        const mainDialogue = dialogueContent.find(item => item.content && item.content !== '对话内容') || 
                           dialogueContent[0] || 
                           { content: segment.original_text || '旁白内容', speaker: '旁白' }
        
        return {
          id: segment.segment_id || `script_${index}`,
          startTime: segment.start_time?.toString() || '0',
          endTime: segment.end_time?.toString() || '0',
          type: isDialogue ? 'dialogue' : 'narration',
          speaker: mainDialogue.speaker || segment.dialogue?.speaker || '旁白',
          text: mainDialogue.content || segment.original_text || '',
          originalText: segment.original_text || '', // 保存原文用于对比
          character_id: segment.character_id || null,
          voice_id: segment.dialogue?.voice_id || '',
          voice_name: segment.dialogue?.voice_id || '未分配',
          audioElements: segment.sound_effects || {},
          issues: [], // 问题标记
          highlighted: false
        }
      })
      
                    // 同时保留时间轴详情用于分镜视图（从audio_storyboard获取）
      const audioCards = response.data.cards?.audio_storyboard || []
      if (audioCards.length > 0) {
        const audioCard = audioCards[0]
        let timeline = audioCard.content?.timeline || []
        if (typeof timeline === 'string') {
          try {
            timeline = JSON.parse(timeline)
          } catch (e) {
            console.error('解析timeline失败:', e)
            timeline = []
          }
        }
        
        timelineDetails.value = timeline.map((item, index) => ({
          startTime: item.start_time?.toString() || '0',
          endTime: item.end_time?.toString() || '0',
          type: item.audio_type === 'dialogue' ? '对话' : '旁白',
          text: item.content || '场景描述',
          audioElements: {},
          text_mapping: item.text_mapping || { paragraph_range: [index, index] }
        }))
      } else {
        timelineDetails.value = []
      }
    } else {
      scriptSegments.value = []
      timelineDetails.value = []
    }
    
    // 处理文本段落（优先使用智能分段结果）
    let segmentsData = []
    
    // 添加调试日志
    console.log('🔍 检查智能分段数据:', {
      hasSegmentationData: !!response.data.segmentation_data,
      segmentationData: response.data.segmentation_data,
      hasSegments: !!(response.data.segmentation_data?.segments),
      segmentsLength: response.data.segmentation_data?.segments?.length || 0
    })

    // 检查是否有智能分段数据
    if (response.data.segmentation_data && response.data.segmentation_data.segments && response.data.segmentation_data.segments.length > 0) {
      segmentsData = response.data.segmentation_data.segments
      console.log('✅ 使用智能分段数据:', segmentsData.length, '段')
    } else {
      console.log('⚠️ 未找到智能分段数据，左侧将显示空')
    }

    textSegments.value = segmentsData.map((segment, index) => ({
      text: typeof segment === 'string' ? segment : segment.content || segment.text || '',
      highlighted: false,
      issues: [],
      segmentIndex: index,
      isSmartSegmented: segmentsData.length > 0
    }))
    
              // 更新章节分析状态
    
    // 更新章节分析状态
    const hasScriptCards = (response.data.cards?.audio_script || []).length > 0
    currentChapterStatus.value = hasScriptCards ? 'completed' : 'pending'
    
    // 加载已保存的段落分析结果
    await loadSixCardResults(chapterId)
    
  } catch (error) {
    console.error('加载章节数据失败:', error)
    message.error('加载章节数据失败')
  } finally {
    loading.value = false
  }
}

  // 加载已保存的段落分析结果
const loadSixCardResults = async (chapterId) => {
  if (!chapterId) return
  
  try {
    console.log('开始加载已保存的段落分析结果:', chapterId)
    
    const response = await storyboardAPI.getSixCardResults(chapterId)
    
    if (response.data?.success && response.data.data.has_results) {
      sixCardResults.value = response.data.data.results
      console.log('已保存的段落分析结果加载成功:', sixCardResults.value)
      
      // 如果有结果，默认选择第一个段落
      if (sixCardResults.value.length > 0) {
        selectedSegmentIndex.value = 0
      }
    } else {
      console.log('暂无已保存的段落分析结果，响应数据:', response.data)
      sixCardResults.value = []
      selectedSegmentIndex.value = null
    }
  } catch (error) {
    console.error('加载段落分析结果失败:', error)
    // 不显示错误消息，因为可能只是没有结果
  }
}



// 加载章节列表
const loadChapters = async () => {
  if (!props.sessionId) return
  
  try {
    chaptersLoading.value = true
    const response = await storyboardAPI.getSessionChapters(props.sessionId)
    chapters.value = response.data.chapters || []
    
           // 如果有章节数据，默认选择第一个章节
       if (chapters.value.length > 0) {
         // 使用正确的字段：id 而不是 chapter_id
         const firstChapter = chapters.value[0]
         selectedChapter.value = (firstChapter.id || firstChapter.chapter_id || '').toString()
      
      // 立即加载选中的章节数据
      if (selectedChapter.value) {
        await loadChapterData(parseInt(selectedChapter.value))
      }
    } else {
      selectedChapter.value = ''
    }
  } catch (error) {
    console.error('加载章节列表失败:', error)
    message.error('加载章节列表失败')
  } finally {
    chaptersLoading.value = false
  }
}



// 监听sessionId变化，强制刷新数据
watch(() => props.sessionId, (newSessionId) => {
  if (newSessionId) {
    loadChapters()  // loadChapters内部会处理章节数据加载
  }
}, { immediate: true })

// 组件挂载时加载数据
onMounted(() => {
  loadChapters()  // loadChapters内部会处理章节数据加载
})



// 处理剧本段落点击
const handleScriptSegmentClick = (index) => {
        // 清除所有高亮
  textSegments.value.forEach((segment, i) => {
    segment.highlighted = false
  })
  scriptSegments.value.forEach((script, i) => {
    script.highlighted = false
  })
  
  // 高亮当前点击的剧本段落
  if (index < scriptSegments.value.length) {
         scriptSegments.value[index].highlighted = true
  }
  
  // 根据音频分镜卡的对应关系高亮文本段落
  if (timelineDetails.value[index]) {
    const audioSegment = timelineDetails.value[index]
    
    if (audioSegment.text_mapping && audioSegment.text_mapping.paragraph_range) {
      const [startParagraph, endParagraph] = audioSegment.text_mapping.paragraph_range
      
      // 高亮对应的文本段落
      for (let i = startParagraph; i <= endParagraph && i < textSegments.value.length; i++) {
        textSegments.value[i].highlighted = true
      }
      
      // 滚动到第一个高亮的段落
      if (startParagraph < textSegments.value.length) {
        const firstHighlightedElement = document.querySelectorAll('.text-segment')[startParagraph]
        if (firstHighlightedElement) {
          firstHighlightedElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
      }
      
      message.info(`高亮段落 ${startParagraph + 1}-${endParagraph + 1}`)
    } else {
      // 如果没有对应关系，使用简单的索引对应
      if (index < textSegments.value.length) {
        textSegments.value[index].highlighted = true
        const element = document.querySelectorAll('.text-segment')[index]
        if (element) {
          element.scrollIntoView({ behavior: 'smooth', block: 'center' })
        }
        message.info(`高亮段落 ${index + 1}`)
      }
    }
  } else {
    // 如果没有timelineDetails，使用简单的索引对应
    if (index < textSegments.value.length) {
      textSegments.value[index].highlighted = true
      const element = document.querySelectorAll('.text-segment')[index]
      if (element) {
        element.scrollIntoView({ behavior: 'smooth', block: 'center' })
      }
      message.info(`高亮段落 ${index + 1}`)
    }
  }
}

// 处理章节选择变化
const handleChapterChange = (chapterId) => {
  selectedChapter.value = chapterId
  if (chapterId) {
    loadChapterData(parseInt(chapterId))
         // 加载章节数据
  }
}



const getCardTypeName = (cardType) => {
  const names = {
    'story': '故事',
    'character': '角色',
    'scene': '场景',
    'event': '事件',
    'emotion': '情绪',
    'audio_storyboard': '音频分镜'
  }
  return names[cardType] || cardType
}









const analyzeCurrentChapter = async () => {
  if (!selectedChapter.value || analyzingChapter.value) return

  analyzingChapter.value = true
  try {
    const response = await storyboardAPI.analyzeChapter(props.sessionId, selectedChapter.value)
    message.success('章节分析已开始')

    // 更新状态
    currentChapterStatus.value = 'analyzing'

    // 等待一段时间后刷新数据
    setTimeout(() => {
      loadChapterData(parseInt(selectedChapter.value))
      currentChapterStatus.value = 'completed'
    }, 3000)

  } catch (error) {
    console.error('章节分析失败:', error)
    message.error('章节分析失败: ' + (error.response?.data?.detail || error.message))
    currentChapterStatus.value = 'failed'
  } finally {
    analyzingChapter.value = false
  }
}

const handleSmartSegmentation = async () => {
  if (!selectedChapter.value || segmentingChapter.value) return

  segmentingChapter.value = true
  try {
              // 显示长时间操作提示
    message.info({
      content: '智能分段正在进行中，这可能需要1-2分钟，请耐心等待...',
      duration: 5,
      key: 'segmentation'
    })

    // 调用智能分段API
    const response = await storyboardAPI.smartSegmentation(selectedChapter.value)

    if (response.data?.success) {
      message.success({
        content: `🎉 智能分段完成！共生成 ${response.data.data.segmentation_data.segment_count} 个段落`,
        duration: 5,
        key: 'segmentation'
      })

             // 刷新章节数据，显示分段结果
       await loadChapterData(parseInt(selectedChapter.value))
    } else {
      throw new Error(response.data?.message || '智能分段失败')
    }
  } catch (error) {
    console.error('[ContentReviewTab] 智能分段失败:', error)
    message.error({
      content: `❌ 智能分段失败: ${error.message || '未知错误'}`,
      duration: 5,
      key: 'segmentation'
    })
  } finally {
    segmentingChapter.value = false
  }
}





// 打开卡片抽屉
const openCardDrawer = (cardType, script) => {
  if (!reviewData.value?.cards) return
  
  // 获取对应类型的卡片
  let cards = reviewData.value.cards[cardType] || []
  if (cards.length === 0 && reviewData.value.book_cards) {
    cards = reviewData.value.book_cards[cardType] || []
  }
  
  if (cards.length > 0) {
    const card = cards[0]
    selectedCard.value = {
      id: card.id,
      type: cardType,
      title: `${getCardTypeName(cardType)}卡片`,
      content: card.content || {},
      confidence_score: card.confidence_score,
      related_script: script // 添加关联的剧本信息
    }
    cardDrawerVisible.value = true
  } else {
    message.warning(`暂无${getCardTypeName(cardType)}卡片数据`)
  }
}
</script>

<style scoped>
.content-review-container {
  min-height: 100vh;
  color: var(--text-color, #333);
}

.content-review-layout {
  display: flex;
  gap: 12px;
  height: calc(100vh - 200px);
}

/* 深色主题变量 */
:root {
  /* 浅色主题 */
  --bg-color: #f5f5f5;
  --card-bg: white;
  --content-bg: transparent;
  --header-bg: #fafafa;
  --segment-bg: transparent;
  --item-bg: transparent;
  --text-color: #333;
  --text-secondary: #666;
  --border-color: #e8e8e8;
  --shadow-color: rgba(0, 0, 0, 0.1);
  --primary-color: #1890ff;
  --primary-bg: #f0f8ff;
  --primary-border: rgba(24, 144, 255, 0.2);
  --hover-bg: #f6ffed;
  --highlight-bg: #e6f7ff;
  --warning-bg: #fff2f0;
  --warning-border: #ffccc7;
}

/* 深色主题 */
[data-theme="dark"] {
  --bg-color: #0f0f0f;
  --card-bg: #1a1a1a;
  --content-bg: #1a1a1a;
  --header-bg: #262626;
  --segment-bg: #262626;
  --item-bg: #1a1a1a;
  --text-color: #e0e0e0;
  --text-secondary: #888888;
  --border-color: #333333;
  --shadow-color: rgba(0, 0, 0, 0.5);
  --primary-color: #4a9eff;
  --primary-bg: rgba(74, 158, 255, 0.08);
  --primary-border: rgba(74, 158, 255, 0.2);
  --hover-bg: rgba(74, 158, 255, 0.08);
  --highlight-bg: rgba(74, 158, 255, 0.15);
  --warning-bg: rgba(255, 77, 79, 0.08);
  --warning-border: rgba(255, 77, 79, 0.2);
}
</style>
