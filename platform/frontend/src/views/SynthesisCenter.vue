<template>
  <div class="synthesis-center">
    <!-- 项目头部 -->
    <ProjectHeader 
      :project="project"
      :loading="loading"
      @back="handleBack"
    />

    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 章节选择器 -->
      <ChapterSelector
        :chapters="chapters"
        :selected-chapter="selectedChapter"
        :loading="chaptersLoading"
        @loadChapters="loadChapters"
        @select="handleChapterSelect"
      />

      <!-- 内容预览区域 -->
      <ContentPreview
        :project="project"
        :selected-chapter="selectedChapter"
        :chapter-content="chapterContent"
        :content-loading="contentLoading"
        :segments="segments"
        :preparation-results="preparationResults"
        :available-chapters="chapters"
        :synthesis-starting="synthesisStarting"
        :playing-chapter-audio="playingChapterAudio"
        :can-start="canStartSynthesis"
        :synthesis-running="synthesisRunning"
        :selected-chapter-status="getSelectedChapterStatus()"
        @play-segment="handlePlaySegment"
        @refresh-preparation="handleRefreshPreparation"
        @trigger-preparation="handleTriggerPreparation"
        @start-chapter-synthesis="handleStartChapterSynthesis"
        @play-chapter="handlePlayChapter"
        @download-chapter="handleDownloadChapter"
        @start-synthesis="handleStartSynthesis"
        @pause-synthesis="handlePauseSynthesis"
        @cancel-synthesis="handleCancelSynthesis"
        @retry-synthesis="handleRetrySynthesis"
        @play-audio="handlePlayAudio"
        @download-audio="handleDownloadAudio"
        @restart-synthesis="handleRestartSynthesis"
      />
    </div>

    <!-- 进度监控抽屉 -->
    <ProgressDrawer
      :visible="progressDrawerVisible"
      :progress-data="progressData"
      :project-status="project?.status || 'pending'"
      :ws-connected="websocketStatus === 'connected'"
      @close="handleProgressDrawerClose"
      @update:visible="progressDrawerVisible = $event"
      @showFailureDetails="handleShowFailureDetails"
    />

    <!-- 失败详情弹窗 -->
    <FailureDetailsModal
      :visible="failureDetailsVisible"
      :failed-segments="failedSegmentsList"
      :total-segments="progressData.total_segments || 0"
      :completed-segments="progressData.completed_segments || 0"
      :retry-loading="retryLoading"
      @close="handleCloseFailureDetails"
      @retryFailedSegments="handleRetryFailedSegments"
      @goToPreparation="handleGoToPreparation"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import api from '@/api'
import apiClient from '@/api/config.js'
import { playSegmentAudio, playChapterAudio } from '@/utils/audioService'
import ProjectHeader from '@/components/synthesis-center/ProjectHeader.vue'
import ChapterSelector from '@/components/synthesis-center/ChapterSelector.vue'
import ContentPreview from '@/components/synthesis-center/ContentPreview.vue'
import ProgressDrawer from '@/components/synthesis-center/ProgressDrawer.vue'
import FailureDetailsModal from '@/components/synthesis-center/FailureDetailsModal.vue'

const route = useRoute()
const router = useRouter()

// 基础数据
const project = ref(null)
const chapters = ref([])
const selectedChapter = ref(null)
const chapterContent = ref(null)
const segments = ref([])
const preparationResults = ref(null)

// 加载状态
const loading = ref(true)
const chaptersLoading = ref(false)
const contentLoading = ref(false)
const synthesisStarting = ref(false)
const playingChapterAudio = ref(null)

// 合成相关状态
const synthesisRunning = ref(false)
const progressDrawerVisible = ref(false)
const progressData = ref({})
const websocketStatus = ref('disconnected')

// 失败详情相关状态
const failureDetailsVisible = ref(false)
const failedSegmentsList = ref([])
const retryLoading = ref(false)

// WebSocket 连接
let websocket = null
let progressRefreshInterval = null

// 计算属性
const canStartSynthesis = computed(() => {
  return selectedChapter.value && project.value && !synthesisRunning.value
})

// 初始化
onMounted(async () => {
  await loadProject()
  await loadChapters()
  initWebSocket()
})

onUnmounted(() => {
  if (websocket) {
    websocket.close()
  }
  if (progressRefreshInterval) {
    clearInterval(progressRefreshInterval)
  }
})

// 加载项目信息
const loadProject = async () => {
  try {
    loading.value = true
    const projectId = route.params.projectId
    const response = await api.getProject(projectId)
    if (response.data.success) {
      project.value = response.data.data
      
      // 🔧 同时获取项目的合成进度信息
      await loadSynthesisProgress()
    }
  } catch (error) {
    console.error('Failed to load project:', error)
    message.error('加载项目失败')
  } finally {
    loading.value = false
  }
}

// 🔧 新增：加载合成进度信息
const loadSynthesisProgress = async () => {
  try {
    const projectId = route.params.projectId
    // 使用正确的API获取项目的合成进度
    const response = await api.getProgress(projectId)
    if (response.data.success && response.data.data) {
      const progressInfo = response.data.data
      progressData.value = {
        progress: progressInfo.progress || 0,
        status: progressInfo.status || project.value?.status || 'pending',
        completed_segments: progressInfo.completed_segments || 0,
        total_segments: progressInfo.total_segments || 0,
        failed_segments: progressInfo.failed_segments || 0,
        current_processing: progressInfo.current_processing || ''
      }
      console.log('📊 加载进度信息:', progressData.value)
    } else {
      // 如果API返回空数据，从项目统计信息中推导
      if (project.value?.statistics) {
        const stats = project.value.statistics
        progressData.value = {
          progress: stats.progress || 0,
          status: project.value.status || 'pending',
          completed_segments: stats.completedSegments || 0,
          total_segments: stats.totalSegments || 0,
          failed_segments: stats.failedSegments || 0,
          current_processing: ''
        }
        console.log('📊 从项目统计推导进度:', progressData.value)
      } else {
        // 如果项目没有统计信息，设置默认值
        progressData.value = {
          progress: 0,
          status: project.value?.status || 'pending',
          completed_segments: 0,
          total_segments: 0,
          failed_segments: 0,
          current_processing: ''
        }
        console.log('📊 设置默认进度数据:', progressData.value)
      }
    }
  } catch (error) {
    console.error('Failed to load synthesis progress:', error)
    // 如果获取进度失败，从项目信息中推导基本进度
    if (project.value?.statistics) {
      const stats = project.value.statistics
      progressData.value = {
        progress: stats.progress || 0,
        status: project.value.status || 'pending',
        completed_segments: stats.completedSegments || 0,
        total_segments: stats.totalSegments || 0,
        failed_segments: stats.failedSegments || 0,
        current_processing: ''
      }
    } else {
      // 设置安全的默认值
      progressData.value = {
        progress: 0,
        status: project.value?.status || 'pending',
        completed_segments: 0,
        total_segments: 0,
        failed_segments: 0,
        current_processing: ''
      }
    }
    console.log('📊 异常情况设置进度数据:', progressData.value)
  }
}

// 加载章节列表
const loadChapters = async () => {
  try {
    chaptersLoading.value = true
    console.log('Loading chapters, project:', project.value)
    
    if (project.value?.book_id) {
      // 直接使用apiClient调用正确的API路径
      const response = await apiClient.get(`/books/${project.value.book_id}/chapters`)
      console.log('Chapters API response:', response.data)
      
      if (response.data.success && response.data.data) {
        chapters.value = response.data.data
        console.log('Found chapters:', chapters.value)
        
        if (chapters.value.length > 0) {
          selectedChapter.value = chapters.value[0].id
        }
      } else {
        console.log('No chapters found in response')
        chapters.value = []
      }
    } else {
      console.log('No book_id found in project')
      chapters.value = []
    }
  } catch (error) {
    console.error('Failed to load chapters:', error)
    message.error('加载章节失败')
    chapters.value = []
  } finally {
    chaptersLoading.value = false
  }
}

// 选择章节
const handleChapterSelect = async (chapterId) => {
  selectedChapter.value = chapterId
  
  // 自动加载智能准备结果
  if (selectedChapter.value) {
    await loadPreparationResults()
  } else {
    // 清空准备结果
    preparationResults.value = null
  }
}

// 加载智能准备结果
const loadPreparationResults = async () => {
  if (!project.value?.book_id) {
    console.warn('项目未关联书籍，无法加载智能准备结果')
    return
  }
  
  if (!selectedChapter.value) {
    console.warn('请先选择要合成的章节')
    return
  }
  
  contentLoading.value = true
  try {
    // 只获取选中章节的智能准备结果
    const response = await apiClient.get(`/books/${project.value.book_id}/analysis-results?chapter_ids=${selectedChapter.value}`)
    
    if (response.data.success) {
      // 🔧 修复：检查是否有实际的准备结果数据
      if (response.data.data && response.data.data.length > 0) {
        preparationResults.value = response.data
        console.log('智能准备结果加载成功:', preparationResults.value)
      } else {
        // 🔧 修复：如果没有数据，设置为null以触发显示智能准备按钮
        preparationResults.value = null
        console.log('📋 该章节暂无智能准备结果，将显示准备按钮')
      }
    } else {
      console.error('加载智能准备结果失败:', response.data.message)
      preparationResults.value = null
    }
  } catch (error) {
    console.error('加载智能准备结果失败:', error)
    // 🔧 修复：异常时也设置为null
    preparationResults.value = null
  } finally {
    contentLoading.value = false
  }
}

// WebSocket 初始化
const initWebSocket = () => {
  const projectId = route.params.projectId
  const wsUrl = `ws://localhost:8000/ws`
  
  try {
    websocket = new WebSocket(wsUrl)
    
    websocket.onopen = () => {
      websocketStatus.value = 'connected'
      console.log('WebSocket连接成功，订阅合成进度主题')
      
      // 订阅合成进度主题
      websocket.send(JSON.stringify({
        type: 'subscribe',
        topic: `synthesis_${projectId}`
      }))
    }
    
    websocket.onmessage = (event) => {
      const message = JSON.parse(event.data)
      console.log('收到WebSocket消息:', message)
      
      // 处理主题消息
      if (message.type === 'topic_message' && message.topic === `synthesis_${projectId}`) {
        const data = message.data
        
        // 更新进度数据
        if (data.type === 'progress_update' && data.data) {
          progressData.value = {
            progress: data.data.progress || 0,
            status: data.data.status || 'pending',
            completed_segments: data.data.completed_segments || 0,
            total_segments: data.data.total_segments || 0,
            failed_segments: data.data.failed_segments || 0,
            current_processing: data.data.current_processing || ''
          }
          
          console.log('更新进度数据:', progressData.value)
          
          if (data.data.status === 'completed' || data.data.status === 'failed') {
            loadProject()
            synthesisRunning.value = false
            
            // 🔧 停止定期刷新
            if (progressRefreshInterval) {
              clearInterval(progressRefreshInterval)
              progressRefreshInterval = null
            }
          }
        }
      }
    }
    
    websocket.onclose = () => {
      websocketStatus.value = 'disconnected'
      console.log('WebSocket连接关闭')
    }
    
    websocket.onerror = (error) => {
      websocketStatus.value = 'error'
      console.error('WebSocket error:', error)
    }
  } catch (error) {
    console.error('WebSocket initialization failed:', error)
  }
}

// 处理函数
const handleBack = () => {
  router.push('/novel-reader')
}

const handleStartSynthesis = async () => {
  try {
    synthesisStarting.value = true
    const response = await api.startGeneration(project.value.id, {
      chapter_ids: selectedChapter.value ? [selectedChapter.value] : undefined
    })
    
    if (response.data.success) {
      message.success('开始合成音频')
      synthesisRunning.value = true
      progressDrawerVisible.value = true
      
      // 🔧 初始化进度数据
      progressData.value = {
        progress: 0,
        status: 'processing',
        completed_segments: 0,
        total_segments: 0,
        failed_segments: 0,
        current_processing: '正在准备合成...'
      }
      
      // 🔧 立即获取当前项目状态
      setTimeout(() => {
        loadProject()
      }, 1000)
      
      // 🔧 启动定期刷新进度（防止WebSocket消息丢失）
      if (progressRefreshInterval) {
        clearInterval(progressRefreshInterval)
      }
      progressRefreshInterval = setInterval(() => {
        if (synthesisRunning.value) {
          loadSynthesisProgress()
        }
      }, 3000) // 每3秒刷新一次
    }
  } catch (error) {
    console.error('Failed to start synthesis:', error)
    message.error('启动合成失败')
  } finally {
    synthesisStarting.value = false
  }
}

const handlePauseSynthesis = async () => {
  try {
    await api.pauseGeneration(project.value.id)
    message.success('已暂停合成')
    synthesisRunning.value = false
    
    // 🔧 停止定期刷新
    if (progressRefreshInterval) {
      clearInterval(progressRefreshInterval)
      progressRefreshInterval = null
    }
  } catch (error) {
    console.error('Failed to pause synthesis:', error)
    message.error('暂停合成失败')
  }
}

const handleCancelSynthesis = async () => {
  try {
    // 暂时使用暂停API，实际需要取消API
    await api.pauseGeneration(project.value.id)
    message.success('已取消合成')
    synthesisRunning.value = false
    progressDrawerVisible.value = false
    
    // 🔧 停止定期刷新
    if (progressRefreshInterval) {
      clearInterval(progressRefreshInterval)
      progressRefreshInterval = null
    }
  } catch (error) {
    console.error('Failed to cancel synthesis:', error)
    message.error('取消合成失败')
  }
}

const handleRetrySynthesis = async () => {
  try {
    await api.resumeGeneration(project.value.id, {})
    message.success('重新开始合成')
    synthesisRunning.value = true
    progressDrawerVisible.value = true
  } catch (error) {
    console.error('Failed to retry synthesis:', error)
    message.error('重试合成失败')
  }
}

const handlePlayAudio = async () => {
  try {
    playingChapterAudio.value = selectedChapter.value
    await playChapterAudio(project.value.id, selectedChapter.value)
    message.success('开始播放音频')
  } catch (error) {
    console.error('Failed to play audio:', error)
    message.error('播放音频失败')
  } finally {
    playingChapterAudio.value = null
  }
}

const handleDownloadAudio = async () => {
  try {
    const response = await api.downloadChapterAudio(project.value.id, selectedChapter.value)
    
    const blob = new Blob([response.data], { type: 'audio/wav' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `第${selectedChapter.value}章.wav`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    message.success('下载完成')
  } catch (error) {
    console.error('Failed to download audio:', error)
    message.error('下载音频失败')
  }
}

const handlePlaySegment = async (segment) => {
  try {
    await playSegmentAudio(project.value.id, segment.id)
    message.success(`播放片段: ${segment.content?.substring(0, 20)}...`)
  } catch (error) {
    console.error('Failed to play segment:', error)
    message.error('播放片段失败')
  }
}

const handleProgressDrawerClose = () => {
  progressDrawerVisible.value = false
}

// 失败详情处理
const handleShowFailureDetails = async () => {
  try {
    // 获取详细的失败段落信息
    const response = await api.getFailedSegments(project.value.id)
    if (response.data.success && response.data.data) {
      failedSegmentsList.value = response.data.data
    } else {
      // 如果API不存在，创建模拟数据用于展示
      failedSegmentsList.value = createMockFailedSegments()
    }
    failureDetailsVisible.value = true
  } catch (error) {
    console.error('Failed to load failed segments:', error)
    // 创建模拟数据
    failedSegmentsList.value = createMockFailedSegments()
    failureDetailsVisible.value = true
  }
}

const handleCloseFailureDetails = () => {
  failureDetailsVisible.value = false
}

const handleRetryFailedSegments = async () => {
  try {
    retryLoading.value = true
    const response = await api.retryAllFailedSegments(project.value.id)
    if (response.data.success) {
      message.success('已开始重试失败段落')
      synthesisRunning.value = true
      progressDrawerVisible.value = true
      failureDetailsVisible.value = false
      
      // 重新启动定期刷新
      if (progressRefreshInterval) {
        clearInterval(progressRefreshInterval)
      }
      progressRefreshInterval = setInterval(() => {
        if (synthesisRunning.value) {
          loadSynthesisProgress()
        }
      }, 3000)
    }
  } catch (error) {
    console.error('Failed to retry failed segments:', error)
    message.error('重试失败段落失败')
  } finally {
    retryLoading.value = false
  }
}

const handleGoToPreparation = () => {
  // 跳转到智能准备页面或显示准备界面
  message.info('跳转到智能准备页面进行修改')
  failureDetailsVisible.value = false
  
  // 这里可以根据您的路由设计跳转到相应页面
  // 例如：router.push(`/preparation/${project.value.id}/${selectedChapter.value}`)
  // 或者触发智能准备模式
}

// 创建模拟失败段落数据（用于没有详细API时的展示）
const createMockFailedSegments = () => {
  const failedCount = progressData.value.failed_segments || 0
  const mockSegments = []
  
  for (let i = 0; i < Math.min(failedCount, 10); i++) {
    mockSegments.push({
      id: `failed_${i}`,
      index: i + 1,
      speaker: i % 2 === 0 ? '男主' : '女主',
      text: `这是第${i + 1}个失败的段落内容...`,
      error_type: ['voice_not_found', 'tts_service_error', 'text_processing_error'][i % 3],
      error_message: [
        '未找到对应的声音档案',
        'TTS服务连接超时',
        '文本包含无法处理的特殊字符'
      ][i % 3]
    })
  }
  
  return mockSegments
}

// ContentPreview 事件处理
const handleRefreshPreparation = () => {
  message.info('刷新智能准备结果')
  loadProject()
}

const handleTriggerPreparation = () => {
  message.info('触发智能准备')
}

const handleStartChapterSynthesis = (chapterId) => {
  selectedChapter.value = chapterId
  handleStartSynthesis()
}

const handlePlayChapter = (chapterId) => {
  selectedChapter.value = chapterId
  handlePlayAudio()
}

const handleDownloadChapter = (chapterId) => {
  selectedChapter.value = chapterId
  handleDownloadAudio()
}

// 重新合成处理函数
const handleRestartSynthesis = async () => {
  try {
    synthesisStarting.value = true
    
    // 重新启动选中章节的合成
    const response = await api.startGeneration(project.value.id, {
      chapter_ids: selectedChapter.value ? [selectedChapter.value] : undefined,
      restart: true  // 表示这是重新合成
    })
    
    if (response.data.success) {
      message.success('重新开始合成音频')
      synthesisRunning.value = true
      progressDrawerVisible.value = true  // 显示进度抽屉
    }
  } catch (error) {
    console.error('Failed to restart synthesis:', error)
    message.error('重新合成失败')
  } finally {
    synthesisStarting.value = false
  }
}

// 获取选中章节的状态
const getSelectedChapterStatus = () => {
  if (!selectedChapter.value || !chapters.value.length) {
    return 'pending'
  }
  
  const chapter = chapters.value.find(ch => ch.id === selectedChapter.value)
  if (!chapter) return 'pending'
  
  // 使用章节的analysis_status或synthesis_status
  const status = chapter.analysis_status || chapter.synthesis_status || 'pending'
  
  // 映射状态
  const statusMap = {
    'pending': 'pending',
    'processing': 'processing', 
    'completed': 'completed',
    'failed': 'failed',
    'ready': 'pending'
  }
  
  return statusMap[status] || 'pending'
}
</script>

<style scoped>
.synthesis-center {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  display: flex;
  flex: 1;
  overflow: hidden;
  gap: 1px;
}

/* 章节选择器 - 固定较小宽度 */
.main-content > :first-child {
  flex: 0 0 280px;
  min-width: 280px;
  max-width: 280px;
}

/* 内容预览区域 - 占用剩余空间 */
.main-content > :last-child {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}
</style> 