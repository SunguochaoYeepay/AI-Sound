<template>
  <div class="content-review-container">
    <!-- 进度监控 -->
    <ProgressMonitor :project-id="projectId" />

    <!-- 章节选择器 -->
    <ChapterSelector
      :chapters="chapters"
      :chapters-loading="chaptersLoading"
      :selected-chapter="selectedChapter"
      :current-chapter-status="currentChapterStatus"
      :analyzing-chapter="analyzingChapter"
      :segmenting-chapter="segmentingChapter"
      :has-smart-segmentation="hasSmartSegmentation"
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
        :project-id="projectId"
        @six-card-analysis="handleSixCardAnalysis"
        @text-segment-click="handleTextSegmentClick"
      />

      <!-- 右侧：剧本详情 -->
      <ScriptDetailPanel 
        :loading="loading"
        :script-segments="scriptSegments"
        :review-data="reviewData"
        :chapter="reviewData?.chapter"
        :six-card-results="sixCardResults"
        :selected-segment-index="selectedSegmentIndex"
        :highlighted-segment-index="highlightedSegmentIndex"
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
import { ref, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import CardDetailDrawer from './CardDetailDrawer.vue'
import ProgressMonitor from './ProgressMonitor.vue'
import ChapterSelector from './ChapterSelector.vue'
import OriginalTextPanel from './OriginalTextPanel.vue'
import ScriptDetailPanel from './ScriptDetailPanel.vue'
import { storyboardAPI } from '@/api/storyboard'

// Props
const props = defineProps({
  projectId: {
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

// 智能分段状态
const hasSmartSegmentation = computed(() => {
  // 检查是否有智能分段数据
  return textSegments.value.length > 0
})

// 剧本详情
const scriptSegments = ref([])

// 章节分析状态
const analyzingChapter = ref(false)
const currentChapterStatus = ref('pending')

// 段落分析结果
const sixCardResults = ref([])
const selectedSegmentIndex = ref(null)
const highlightedSegmentIndex = ref(null)

// 处理段落分析结果
const handleSixCardAnalysis = (data) => {
  selectedSegmentIndex.value = data.segmentIndex
  
  // 分析完成后，重新从后端加载最新数据，避免重复
  if (data.results && data.results.length > 0) {
    console.log('收到段落分析结果:', data)
    
    // 延迟一下，确保后端数据已保存
    setTimeout(async () => {
      if (selectedChapter.value) {
        await loadSixCardResults(parseInt(selectedChapter.value))
        console.log('重新加载后的段落分析结果:', sixCardResults.value)
      }
    }, 1000)
  }
}

// 加载章节数据
const loadChapterData = async (chapterId) => {
  if (!props.projectId || !chapterId) return

  loading.value = true
  try {
    // 获取智能分段结果
    console.log('🔍 开始获取智能分段数据')
    const segmentationResponse = await storyboardAPI.getSegmentationResult(props.projectId, chapterId)
    
    if (segmentationResponse.data?.success && segmentationResponse.data?.data) {
      const segmentationData = segmentationResponse.data.data
      console.log('✅ 智能分段数据获取成功:', segmentationData)
      
      // 设置章节内容
      chapterContent.value = segmentationData.original_content || `第${chapterId}章\n\n[章节内容加载中...]`
      
      // 设置分段数据 - 转换格式
      const rawSegments = segmentationData.segments || []
      textSegments.value = rawSegments.map((segmentText, index) => ({
        text: segmentText,
        index: index,
        highlighted: false
      }))
      
      // 设置章节数据
      reviewData.value = {
        chapter: {
          id: chapterId,
          content: chapterContent.value
        },
        segments: textSegments.value,
        cards: []
      }
      
      console.log(`✅ 智能分段数据加载完成，共 ${textSegments.value.length} 个段落`)
    } else {
      console.log('⚠️ 未找到智能分段数据，使用默认数据')
      // 提供默认的章节数据
      reviewData.value = {
        chapter: {
          id: chapterId,
          content: `第${chapterId}章\n\n[章节内容加载中...]`
        },
        segments: [],
        cards: []
      }
      
      chapterContent.value = `第${chapterId}章\n\n[章节内容加载中...]`
      textSegments.value = []
    }
    
    // 加载已保存的段落分析结果
    await loadSixCardResults(chapterId)
    
    // 更新章节分析状态
    currentChapterStatus.value = 'pending'
    
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
    
    const response = await storyboardAPI.getSixCardResults(props.projectId, chapterId)
    
    if (response.data?.success && response.data.data.has_results) {
      sixCardResults.value = response.data.data.results
      console.log('🎬 [剧本日志] 已保存的段落分析结果加载成功:', sixCardResults.value)
      console.log('🎬 [剧本日志] sixCardResults数组长度:', sixCardResults.value.length)
      console.log('🎬 [剧本日志] sixCardResults详细内容:', JSON.stringify(sixCardResults.value, null, 2))
      
      // 同时设置scriptSegments用于剧本详情显示
      if (response.data.data.results && response.data.data.results.length > 0) {
        scriptSegments.value = response.data.data.results
        console.log('🎬 [剧本日志] scriptSegments设置完成，长度:', scriptSegments.value.length)
      }
      
      // 设置时间线详情
      if (response.data.data.timeline_details) {
        timelineDetails.value = response.data.data.timeline_details
        console.log('🎬 [剧本日志] timelineDetails设置完成，长度:', timelineDetails.value.length)
      }
      
      // 如果有结果，默认选择第一个段落
      if (sixCardResults.value.length > 0) {
        selectedSegmentIndex.value = 0
        console.log('🎬 [剧本日志] 默认选择段落索引:', selectedSegmentIndex.value)
      }
      
      console.log(`🎬 [剧本日志] ✅ 6卡分析结果加载完成，剧本段落: ${scriptSegments.value.length}，时间线: ${timelineDetails.value.length}`)
    } else {
      console.log('🎬 [剧本日志] 暂无已保存的段落分析结果，响应数据:', response.data)
      sixCardResults.value = []
      scriptSegments.value = []
      timelineDetails.value = []
      selectedSegmentIndex.value = null
    }
  } catch (error) {
    console.error('加载段落分析结果失败:', error)
    // 不显示错误消息，因为可能只是没有结果
  }
}



// 加载章节列表
const loadChapters = async () => {
  if (!props.projectId) return
  
  try {
    chaptersLoading.value = true
    const response = await storyboardAPI.getSessionChapters(props.projectId)
    console.log('🔍 章节API响应:', response.data)
    chapters.value = response.data.data?.chapters || response.data.chapters || []
    
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



// 监听projectId变化，强制刷新数据
watch(() => props.projectId, (newProjectId) => {
  if (newProjectId) {
    loadChapters()  // loadChapters内部会处理章节数据加载
  }
}, { immediate: true })

// 组件挂载时加载数据
onMounted(() => {
  loadChapters()  // loadChapters内部会处理章节数据加载
})



// 处理文本段落点击（左侧原始文本）
const handleTextSegmentClick = (index) => {
  // 清除之前的高亮
  textSegments.value.forEach((segment, i) => {
    segment.highlighted = false
  })
  
  // 高亮当前点击的文本段落
  if (index < textSegments.value.length) {
    textSegments.value[index].highlighted = true
  }
  
  // 设置右侧高亮的段落索引
  // 检查是否有对应的分析结果
  const hasAnalysisResult = sixCardResults.value.some(result => 
    result._metadata?.segment_index === index
  )
  
  if (hasAnalysisResult) {
    // 如果有分析结果，使用对应的segment_index
    highlightedSegmentIndex.value = index
  } else {
    // 如果没有分析结果，清除高亮
    highlightedSegmentIndex.value = null
  }
  
  console.log(`左侧点击段落 ${index}，是否有分析结果: ${hasAnalysisResult}，设置右侧高亮索引: ${highlightedSegmentIndex.value}`)
}

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
  
  // 设置右侧高亮的段落索引（用于高亮对应的段落剧本）
  // 根据智能分段的索引来设置
  if (textSegments.value[index] && textSegments.value[index].segmentIndex !== undefined) {
    highlightedSegmentIndex.value = textSegments.value[index].segmentIndex
  } else {
    // 如果没有智能分段索引，使用简单的索引对应
    highlightedSegmentIndex.value = index
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
    const response = await storyboardAPI.analyzeChapter(props.projectId, selectedChapter.value)
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
    const response = await storyboardAPI.smartSegmentation(props.projectId, selectedChapter.value)

    if (response.data?.success) {
      message.success({
        content: `🎉 智能分段完成！共生成 ${response.data.data.segmentation_data.segment_count} 个段落`,
        duration: 5,
        key: 'segmentation'
      })

      // 只刷新智能分段数据，不触发6卡分析
      await loadSmartSegmentationData(parseInt(selectedChapter.value))
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

// 只加载智能分段数据，不触发6卡分析
const loadSmartSegmentationData = async (chapterId) => {
  if (!props.projectId || !chapterId) return

  loading.value = true
  try {
    // 只获取智能分段数据
    const response = await storyboardAPI.getSegmentationResult(props.projectId, chapterId)
    
    if (response.data?.success && response.data?.data?.segments) {
      const segments = response.data.data.segments
      
      // 更新文本段落数据
      textSegments.value = segments.map((segment, index) => ({
        text: typeof segment === 'string' ? segment : segment.content || segment.text || '',
        highlighted: false,
        issues: [],
        segmentIndex: index + 1,
        isSmartSegmented: true
      }))
      
      console.log(`✅ 智能分段数据已更新，共 ${segments.length} 个段落`)
    } else {
      console.log('⚠️ 未获取到智能分段数据')
    }
    
  } catch (error) {
    console.error('加载智能分段数据失败:', error)
    message.error('加载智能分段数据失败')
  } finally {
    loading.value = false
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

/* 左右面板等宽布局 */
.content-review-layout > * {
  flex: 1;
  min-width: 0; /* 防止内容溢出 */
  max-width: 50%; /* 确保最大宽度不超过50% */
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
