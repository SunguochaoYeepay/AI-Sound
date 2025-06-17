<template>
  <div class="synthesis-center">
    <!-- 顶部导航 -->
    <div class="top-navbar">
      <div class="nav-left">
        <a-button type="text" @click="goBack" class="back-btn">
          <template #icon><ArrowLeftOutlined /></template>
          返回项目
        </a-button>
        <a-divider type="vertical" />
        <h1 class="page-title">🎙️ 合成中心</h1>
      </div>
      <div class="nav-right">
        <a-tag :color="getStatusColor(project?.status)" v-if="project">
          {{ getStatusText(project?.status) }}
        </a-tag>
      </div>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载项目信息...">
        <div style="height: 400px;"></div>
      </a-spin>
    </div>

    <div v-else-if="project" class="synthesis-layout">
      <!-- 左侧：章节选择区域 -->
      <div class="left-panel">
        <div class="panel-header">
          <h3>📚 书籍章节</h3>
          <span class="project-name">{{ project.book?.title || project.name }}</span>
        </div>
        
        <div class="chapter-selection-area">
          <!-- 章节控制栏 -->
          <div class="chapter-controls">
            <a-checkbox 
              :indeterminate="chapterIndeterminate" 
              :checked="chapterCheckAll" 
              @change="toggleAllChapters"
            >
              全选
            </a-checkbox>
            <span class="selection-count">
              {{ selectedChapters.length }} / {{ availableChapters.length }} 个章节
            </span>
            <a-button size="small" @click="loadChapters" :loading="loadingChapters" type="text">
              <template #icon><ReloadOutlined /></template>
            </a-button>
          </div>
          
          <!-- 章节列表 -->
          <div class="chapters-list" v-if="project?.book?.id">
            <div v-if="loadingChapters" class="loading-state">
              <a-spin tip="加载章节列表..." />
            </div>
            
            <div v-else-if="availableChapters.length > 0" class="chapters-container">
              <div 
                v-for="chapter in availableChapters" 
                :key="chapter.id"
                class="chapter-card"
                :class="{ 'selected': selectedChapters.includes(chapter.id) }"
                @click="toggleChapterSelection(chapter.id)"
              >
                <div class="chapter-checkbox">
                  <a-checkbox 
                    :checked="selectedChapters.includes(chapter.id)"
                    @click.stop="toggleChapterSelection(chapter.id)"
                  />
                </div>
                <div class="chapter-info">
                  <div class="chapter-title">
                    第{{ chapter.chapter_number }}章 {{ chapter.title || chapter.chapter_title || '未命名章节' }}
                  </div>
                  <div class="chapter-meta">
                    <span class="word-count">{{ formatNumber(chapter.word_count || 0) }} 字</span>
                    <span class="chapter-status" :class="getChapterStatusClass(chapter)">
                      {{ getChapterStatusText(chapter) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="empty-chapters">
              <a-empty description="暂无章节数据" :image="Empty.PRESENTED_IMAGE_SIMPLE">
                <a-button type="primary" @click="loadChapters">重新加载</a-button>
              </a-empty>
            </div>
          </div>
          
          <!-- 直接文本项目提示 -->
          <div v-else class="text-project-hint">
            <a-alert
              message="文本项目"
              description="该项目基于直接输入的文本，将自动按段落合成"
              type="info"
              show-icon
            />
          </div>
        </div>
      </div>

      <!-- 右侧：合成操作区域 -->
      <div class="right-panel">
        <!-- 顶部操作栏 -->
        <div class="action-toolbar" style="background: #e6f7ff; border: 2px solid #1890ff;">
          <div class="toolbar-left">
            <a-button 
              type="primary" 
              @click="loadPreparationResults"
              :loading="loadingResults"
              size="large"
            >
              📥 加载智能准备结果
            </a-button>
            <a-button 
              v-if="preparationResults"
              @click="refreshPreparationResults"
              :loading="loadingResults"
            >
              🔄 刷新
            </a-button>
          </div>
          
          <div class="toolbar-right">
            <!-- 合成控制按钮 -->
            <a-button
              v-if="project.status === 'pending' || project.status === 'failed' || project.status === 'configured'"
              type="primary"
              size="large"
              :disabled="!canStartSynthesis"
              :loading="synthesisStarting"
              @click="startSynthesis"
              class="start-btn"
            >
              🎯 开始合成
            </a-button>

            <a-button
              v-if="project.status === 'completed'"
              type="primary"
              size="large"
              @click="restartSynthesis"
              :loading="synthesisStarting"
              class="restart-btn"
            >
              🔄 重新合成
            </a-button>

            <a-space v-if="project.status === 'processing'">
              <a-button
                @click="pauseSynthesis"
                :loading="pausingGeneration"
              >
                ⏸️ 暂停
              </a-button>
              <a-button
                danger
                @click="cancelSynthesis"
                :loading="cancelingGeneration"
              >
                ⏹️ 取消
              </a-button>
            </a-space>

            <a-button
              v-if="project.status === 'paused' || (project.status === 'failed' && project.statistics?.completedSegments > 0)"
              type="primary"
              size="large"
              @click="resumeSynthesis"
              :loading="resumingGeneration"
            >
              ▶️ 继续合成
            </a-button>

            <!-- 部分完成状态的按钮 -->
            <a-space v-if="project.status === 'partial_completed'">
              <a-button
                type="primary"
                size="large"
                @click="retryAllFailedSegments"
                :loading="resumingGeneration"
              >
                🔄 重试失败段落
              </a-button>
              <a-button
                size="large"
                @click="restartSynthesis"
                :loading="synthesisStarting"
              >
                🎯 重新合成
              </a-button>
              <a-button
                size="large"
                @click="downloadPartialAudio"
                type="dashed"
              >
                📥 下载已完成
              </a-button>
            </a-space>

            <!-- 调试按钮 - 显示当前状态 -->
            <a-tag color="orange" style="margin-left: 8px;">
              状态: {{ project.status }}
            </a-tag>
          </div>
        </div>

        <!-- 合成内容预览区域 -->
        <div class="content-preview">
          <!-- 项目统计卡片 -->
          <div class="stats-card">
            <div class="stats-row">
              <div class="stat-item">
                <span class="stat-number">{{ currentProgressData.totalSegments }}</span>
                <span class="stat-label">总段落</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ currentProgressData.completedSegments }}</span>
                <span class="stat-label">已完成</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ currentProgressData.failedSegments }}</span>
                <span class="stat-label">失败</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ currentProgressData.percent }}%</span>
                <span class="stat-label">进度</span>
              </div>
            </div>
            
            <!-- 章节和角色统计 -->
            <div class="stats-row" style="margin-top: 16px; padding-top: 16px; border-top: 1px solid #f0f0f0;" v-if="preparationResults">
              <div class="stat-item">
                <span class="stat-number">{{ detectedCharacters.length }}</span>
                <span class="stat-label">角色数</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ selectedChapters.length }}</span>
                <span class="stat-label">选中章节</span>
              </div>
              <div class="stat-item">
                <span class="stat-number">{{ getTotalSegments() }}</span>
                <span class="stat-label">智能片段</span>
              </div>
                             <div class="stat-item">
                 <span class="stat-number" :style="{ color: project.status === 'running' ? '#52c41a' : '#666' }">{{ project.status }}</span>
                 <span class="stat-label">项目状态</span>
               </div>
            </div>
          </div>

          <!-- 智能准备结果 -->
          <div v-if="preparationResults" class="preparation-preview">
            <!-- 角色对话预览 -->
            <div class="dialogue-preview">
              <div class="preview-header">
                <h4>📝 对话内容预览</h4>
                <a-space>
                  <a-button 
                    size="small" 
                    @click="showAllSegments = !showAllSegments"
                    type="text"
                  >
                    {{ showAllSegments ? '收起' : '展开全部' }}
                  </a-button>
                  <a-button 
                    size="small"
                    @click="showJsonTestModal"
                    type="text"
                  >
                    🧪 测试JSON
                  </a-button>
                </a-space>
              </div>
              
              <!-- 对话列表 -->
              <div class="dialogue-list">
                <div v-for="(chapterResult, chapterIndex) in preparationResults.data" :key="chapterIndex">
                  <!-- 章节标题 -->
                  <div class="chapter-divider">
                    <span class="chapter-title">
                      第{{ chapterResult.chapter_number }}章 {{ chapterResult.chapter_title }}
                    </span>
                    <a-tag size="small">{{ chapterResult.synthesis_json?.synthesis_plan?.length || 0 }} 段</a-tag>
                  </div>
                  
                  <!-- 对话气泡 -->
                  <div class="dialogue-bubbles">
                    <div 
                      v-for="(segment, segmentIndex) in (chapterResult.synthesis_json?.synthesis_plan || []).slice(0, showAllSegments ? undefined : 10)" 
                      :key="segmentIndex"
                      class="dialogue-bubble"
                      :class="getCharacterClass(segment.speaker)"
                    >
                      <div class="bubble-header">
                        <span class="speaker-name">{{ segment.speaker }}</span>
                        <span class="segment-index">#{{ segmentIndex + 1 }}</span>
                      </div>
                      <div class="bubble-content">{{ segment.text }}</div>
                    </div>
                    
                    <div v-if="!showAllSegments && (chapterResult.synthesis_json?.synthesis_plan?.length || 0) > 10" class="show-more">
                      <a-button type="dashed" @click="showAllSegments = true" block>
                        显示全部 {{ chapterResult.synthesis_json?.synthesis_plan?.length }} 个段落
                      </a-button>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="empty-preview">
            <a-empty 
              description="请先选择章节并加载智能准备结果"
              :image="Empty.PRESENTED_IMAGE_SIMPLE"
            >
              <p class="empty-hint">{{ getStartHint() }}</p>
            </a-empty>
          </div>
        </div>
      </div>
    </div>

    <!-- 合成进度监控抽屉 -->
    <a-drawer
      v-model:open="synthesisProgressDrawer"
      title="🎵 合成进度监控"
      placement="bottom"
      :height="400"
      :closable="true"
      @close="closeSynthesisDrawer"
    >
      <!-- 进度监控内容保持原有逻辑 -->
      <div class="progress-container">
        <!-- 总体进度 -->
        <div class="overall-progress">
          <h3>🎵 合成总进度</h3>
          <a-progress 
            :percent="progressData.progress" 
            :status="progressData.status === 'failed' ? 'exception' : 'active'"
            :stroke-color="progressData.status === 'completed' ? '#52c41a' : '#1890ff'"
          />
          <div class="progress-stats">
            <a-statistic 
              title="已完成" 
              :value="progressData.completed_segments" 
              :suffix="`/ ${progressData.total_segments}`"
              :value-style="{ color: '#52c41a' }"
            />
            <a-statistic 
              title="失败数" 
              :value="progressData.failed_segments" 
              :value-style="{ color: progressData.failed_segments > 0 ? '#ff4d4f' : '#666' }"
            />
            <a-statistic 
              title="处理时间" 
              :value="synthesisElapsedTime"
              suffix="秒"
              :value-style="{ color: '#1890ff' }"
            />
          </div>
        </div>

        <!-- 当前处理状态 -->
        <div class="current-status" v-if="progressData.current_processing">
          <a-alert 
            :message="progressData.current_processing" 
            type="info" 
            show-icon 
            class="current-alert"
          />
        </div>
      </div>
    </a-drawer>

    <!-- JSON测试弹窗保持原有 -->
    <!-- ... 其他弹窗组件 ... -->
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, h } from 'vue'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import { message, Modal, Empty } from 'ant-design-vue'
import { ArrowLeftOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { readerAPI, charactersAPI, intelligentAnalysisAPI, systemAPI, booksAPI } from '@/api'
import { useWebSocketStore } from '@/stores/websocket.js'

const router = useRouter()
const route = useRoute()
const wsStore = useWebSocketStore()

// 响应式数据
const loading = ref(true)
const synthesisStarting = ref(false)
const pausingGeneration = ref(false)
const resumingGeneration = ref(false)
const cancelingGeneration = ref(false)
const refreshing = ref(false)
const project = ref(null)
const detectedCharacters = ref([])
const availableVoices = ref([])
const characterVoiceMapping = reactive({})
const progressTimer = ref(null)
const previewLoading = ref(null)
const currentPlayingVoice = ref(null)
const currentAudio = ref(null)
const checkingService = ref(false)

// 章节选择相关 - 固定为章节模式
const synthesisMode = ref('chapters') // 固定为 'chapters'
const availableChapters = ref([])
const selectedChapters = ref([])
const loadingChapters = ref(false)

// Mock分析相关
const mockAnalyzing = ref(false)
const applyingMock = ref(false)
const mockResult = ref(null)

// 智能准备结果相关
const preparationResults = ref(null)
const loadingResults = ref(false)

// 合成进度和片段相关
const currentProcessingSegment = ref(null)
const synthesisProgressDrawer = ref(false)
const synthesisElapsedTime = ref(0)
const completedSegments = ref([])
const loadingCompletedSegments = ref(false)
const playingSegment = ref(null)
const showAllCompleted = ref(false)
const segmentAudioPlayer = ref(null)

// 合成配置
const synthesisConfig = reactive({
  quality: 'standard',
  parallelTasks: 1
})

// 其他状态变量
const showAllSegments = ref(false)
const jsonTestModalVisible = ref(false)
const jsonTestContent = ref('')
const jsonTestExecuting = ref(false)
const jsonValidationResult = ref(null)
// 合成进度监控抽屉相关
const synthesisStartTime = ref(null)
const segmentStatuses = ref([]) // 段落状态列表
const elapsedTimer = ref(null)
const unsubscribeWebSocket = ref(null) // WebSocket取消订阅函数
const progressData = ref({
  progress: 0,
  status: 'pending',
  completed_segments: 0,
  total_segments: 0,
  failed_segments: 0,
  current_processing: ''
})

// 🚀 计算属性 - 统一进度数据源（增加调试日志）
const currentProgressData = computed(() => {
  console.log('🔍 currentProgressData计算触发')
  console.log('🔍 synthesisProgressDrawer.value:', synthesisProgressDrawer.value)
  console.log('🔍 progressData.value:', progressData.value)
  console.log('🔍 project.value?.statistics:', project.value?.statistics)
  
  // 如果合成监控抽屉已打开且有实时数据，优先使用实时数据
  if (synthesisProgressDrawer.value && progressData.value.total_segments > 0) {
    const result = {
      totalSegments: progressData.value.total_segments,
      completedSegments: progressData.value.completed_segments,
      failedSegments: progressData.value.failed_segments,
      percent: progressData.value.progress
    }
    console.log('🔍 使用progressData结果:', result)
    return result
  }
  
  // 否则使用项目统计数据
  if (project.value?.statistics) {
    const { totalSegments, completedSegments, failedSegments } = project.value.statistics
    const percent = totalSegments > 0 ? Math.round((completedSegments / totalSegments) * 100) : 0
    const result = {
      totalSegments: totalSegments || 0,
      completedSegments: completedSegments || 0,
      failedSegments: failedSegments || 0,
      percent
    }
    console.log('🔍 使用statistics结果:', result)
    return result
  }
  
  const defaultResult = {
    totalSegments: 0,
    completedSegments: 0,
    failedSegments: 0,
    percent: 0
  }
  console.log('🔍 使用默认结果:', defaultResult)
  return defaultResult
})

const progressPercent = computed(() => {
  const result = currentProgressData.value.percent
  console.log('🔍 progressPercent计算:', {
    input: currentProgressData.value,
    result: result
  })
  return result
})

// 音频预览URL
const audioPreviewUrl = computed(() => {
  // 只有项目完成且有最终音频路径时才返回URL
  if (!project.value?.final_audio_path || project.value.status !== 'completed') {
    return null
  }
  // 构建音频预览URL
  return `/api/v1/novel-reader/projects/${project.value.id}/download`
})

const canStartSynthesis = computed(() => {
  const hasValidChapterSelection = selectedChapters.value.length > 0
  const hasPreparationResults = preparationResults.value?.data?.length > 0
  const hasSegments = getTotalSegments() > 0
  
  return project.value?.status !== 'processing' &&
         hasValidChapterSelection &&
         hasPreparationResults &&
         hasSegments
})

// 章节选择相关计算属性
const chapterCheckAll = computed(() => {
  return availableChapters.value.length > 0 && selectedChapters.value.length === availableChapters.value.length
})

const chapterIndeterminate = computed(() => {
  return selectedChapters.value.length > 0 && selectedChapters.value.length < availableChapters.value.length
})

// 方法
const goBack = () => {
  router.push('/novel-reader')
}

const closeSynthesisDrawer = () => {
  synthesisProgressDrawer.value = false
}

const showJsonTestModal = () => {
  jsonTestModalVisible.value = true
}

const getStatusColor = (status) => {
  const colors = {
    pending: 'orange',
    processing: 'blue',
    paused: 'purple',
    completed: 'green',
    partial_completed: 'gold',
    failed: 'red',
    cancelled: 'default'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待开始',
    processing: '合成中',
    paused: '已暂停',
    completed: '已完成',
    partial_completed: '部分完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getStartHint = () => {
  if (selectedChapters.value.length === 0) {
    return '请选择要合成的章节'
  }
  if (!preparationResults.value?.data?.length) {
    return '请先加载智能准备结果'
  }
  if (getTotalSegments() === 0) {
    return '没有可合成的片段'
  }
  return '可以开始合成'
}

// 章节选择相关方法
const loadChapters = async () => {
  // 检查项目是否关联了书籍
  if (!project.value?.book?.id) {
    console.log('项目未关联书籍，跳过章节加载')
    availableChapters.value = []
    return
  }
  
  loadingChapters.value = true
  try {
    const response = await booksAPI.getBookChapters(project.value.book.id)
    if (response.data.success) {
      availableChapters.value = response.data.data || []
      message.success(`加载了 ${availableChapters.value.length} 个章节`)
    } else {
      message.error('加载章节失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('加载章节失败:', error)
    message.error('加载章节失败: ' + error.message)
  } finally {
    loadingChapters.value = false
  }
}

// 自动加载章节（因为现在固定为章节模式）
const autoLoadChapters = () => {
  if (availableChapters.value.length === 0) {
    loadChapters()
  }
}

const toggleChapterSelection = (chapterId) => {
  const index = selectedChapters.value.indexOf(chapterId)
  if (index > -1) {
    selectedChapters.value.splice(index, 1)
  } else {
    selectedChapters.value.push(chapterId)
  }
}

const toggleAllChapters = () => {
  if (selectedChapters.value.length === availableChapters.value.length) {
    selectedChapters.value = []
  } else {
    selectedChapters.value = availableChapters.value.map(chapter => chapter.id)
  }
}

const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

const getChapterStatusText = (chapter) => {
  const status = chapter.analysis_status || chapter.synthesis_status || 'pending'
  const statusMap = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'ready': '准备就绪'
  }
  return statusMap[status] || '未知'
}

const getChapterStatusClass = (chapter) => {
  const status = chapter.analysis_status || chapter.synthesis_status || 'pending'
  return `status-${status}`
}

// Mock分析方法
const runMockAnalysis = async () => {
  if (!project.value?.id) {
    message.error('请先选择项目')
    return
  }
  
  mockAnalyzing.value = true
  try {
    console.log('=== 开始智能分析测试 ===')
    console.log('选中的章节:', selectedChapters.value)
    
    // 构建分析参数，包含选中的章节
    const analysisParams = {
      chapter_ids: selectedChapters.value.length > 0 ? selectedChapters.value : null
    }
    
    const response = await intelligentAnalysisAPI.analyzeProject(project.value.id, analysisParams)
    
    if (response.data.success) {
      mockResult.value = response.data.data
      message.success('智能分析完成！AI已生成可直接执行的合成计划')
      console.log('智能分析结果:', mockResult.value)
      
      // 记录数据源信息
      const source = response.data.source || 'unknown'
      if (source === 'chapter_analysis') {
        console.log('✅ 使用章节分析结果 (已去除Dify依赖)')
        
        // 显示新的统计信息
        const voiceSummary = mockResult.value.voice_assignment_summary
        if (voiceSummary) {
          message.info(`角色分析完成：${voiceSummary.assigned_voices}/${voiceSummary.total_characters} 个角色已分配声音`)
        }
      }
    } else {
      // 增强错误处理：特别处理章节未分析的情况
      const errorData = response.data.data || {}
      const errorStatus = errorData.status
      
      if (errorStatus === 'pending_analysis') {
        // 章节分析未完成的特殊处理
        const pendingCount = errorData.pending_chapters || 0
        const totalCount = errorData.total_chapters || 0
        const analyzedCount = errorData.analyzed_chapters || 0
        
        console.warn('❌ 章节分析未完成:', {
          total: totalCount,
          analyzed: analyzedCount,
          pending: pendingCount,
          pendingList: errorData.pending_chapter_list
        })
        
        // 显示详细的错误信息和解决方案
        Modal.warning({
          title: '需要先完成章节分析',
          width: 600,
          content: h('div', [
            h('p', `项目共有 ${totalCount} 个章节，已完成 ${analyzedCount} 个，还需要分析 ${pendingCount} 个章节。`),
            h('p', { style: 'margin-top: 12px; font-weight: bold;' }, '解决方案：'),
            h('ol', { style: 'margin: 8px 0; padding-left: 20px;' }, [
              h('li', '前往书籍管理页面'),
              h('li', '找到对应的书籍，点击"查看详情"'),
              h('li', '对未分析的章节点击"🎭 智能准备"按钮'),
              h('li', '等待所有章节分析完成后，再回到合成中心'),
            ]),
            errorData.pending_chapter_list && errorData.pending_chapter_list.length > 0 ? 
              h('div', { style: 'margin-top: 12px;' }, [
                h('p', { style: 'font-weight: bold; margin-bottom: 8px;' }, '待分析章节：'),
                h('ul', { style: 'margin: 0; padding-left: 20px; max-height: 120px; overflow-y: auto;' }, 
                  errorData.pending_chapter_list.slice(0, 10).map(ch => 
                    h('li', { key: ch.id }, `第${ch.chapter_number}章: ${ch.chapter_title}`)
                  )
                ),
                errorData.pending_chapter_list.length > 10 ? 
                  h('p', { style: 'color: #999; font-size: 12px; margin-top: 4px;' }, 
                    `... 等其他 ${errorData.pending_chapter_list.length - 10} 个章节`
                  ) : null
              ]) : null
          ]),
          okText: '我知道了'
        })
      } else {
        // 其他类型的错误
        message.error('智能分析失败: ' + response.data.message)
      }
    }
  } catch (error) {
    console.error('智能分析错误:', error)
    
    // 增强错误处理
    if (error.response && error.response.status === 500) {
      message.error('服务器内部错误，请稍后重试或联系管理员')
    } else if (error.response && error.response.status === 404) {
      message.error('项目不存在，请检查项目是否有效')
    } else {
      message.error('智能分析失败: ' + error.message)
    }
  } finally {
    mockAnalyzing.value = false
  }
}

const applyMockResult = async () => {
  if (!mockResult.value || !project.value?.id) {
    message.error('没有可应用的分析结果')
    return
  }
  
  applyingMock.value = true
  try {
    console.log('=== 应用智能分析结果 ===')
    const response = await intelligentAnalysisAPI.applyAnalysis(project.value.id, mockResult.value)
    
    if (response.data.success) {
      message.success('智能分析结果已应用！')
      console.log('应用结果:', response.data.applied_mapping)
      
      // 检查是否有章节映射信息
      if (mockResult.value.chapter_mapping) {
        const chapterCount = Object.keys(mockResult.value.chapter_mapping).length
        console.log(`✅ 应用了 ${chapterCount} 个章节的分析结果`)
      }
      
      // 检查声音分配统计
      if (mockResult.value.voice_assignment_summary) {
        const summary = mockResult.value.voice_assignment_summary
        message.info(`角色配置已更新：${summary.assigned_voices}/${summary.total_characters} 个角色已分配声音`)
      }
      
      // 使用智能分析的角色结果更新角色配置
      updateCharactersFromAnalysis()
      
      // 刷新项目数据以显示新的角色映射
      await loadProject()
    } else {
      message.error('应用失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('应用智能分析结果错误:', error)
    message.error('应用失败: ' + error.message)
  } finally {
    applyingMock.value = false
  }
}

// 从智能分析结果更新角色配置
const updateCharactersFromAnalysis = () => {
  if (!mockResult.value) return
  
  // 清空现有角色数据
  detectedCharacters.value = []
  
  // 优先从synthesis_plan中提取实际的角色
  const characterStats = {}
  
  if (mockResult.value.synthesis_plan) {
    mockResult.value.synthesis_plan.forEach(segment => {
      const speaker = segment.speaker
      if (speaker && speaker.trim()) {
        if (!characterStats[speaker]) {
          characterStats[speaker] = {
            name: speaker,
            count: 0,
            samples: [],
            voice_id: segment.voice_id,
            voice_name: segment.voice_name || '未分配'
          }
        }
        characterStats[speaker].count++
        
        // 收集示例文本（最多3个）
        if (characterStats[speaker].samples.length < 3 && segment.text) {
          const sampleText = segment.text.slice(0, 30) + (segment.text.length > 30 ? '...' : '')
          if (!characterStats[speaker].samples.includes(sampleText)) {
            characterStats[speaker].samples.push(sampleText)
          }
        }
        
        // 更新voice_id（如果segment中有更新的）
        if (segment.voice_id && !characterStats[speaker].voice_id) {
          characterStats[speaker].voice_id = segment.voice_id
          characterStats[speaker].voice_name = segment.voice_name || '未分配'
        }
      }
    })
  }
  
  // 如果synthesis_plan中没有角色，则使用characters数组作为备选
  if (Object.keys(characterStats).length === 0 && mockResult.value.characters) {
    mockResult.value.characters.forEach(char => {
      characterStats[char.name] = {
        name: char.name,
        count: 1,
        samples: [getCharacterSampleText(char.name)],
        voice_id: char.voice_id,
        voice_name: char.voice_name || '未分配'
      }
    })
  }
  
  // 转换为detectedCharacters格式
  detectedCharacters.value = Object.values(characterStats).map(char => ({
    name: char.name,
    character_id: char.name,
    count: char.count,
    samples: char.samples.length > 0 ? char.samples : [getCharacterSampleText(char.name)],
    voice_id: char.voice_id,
    voice_name: char.voice_name
  }))
  
  // 自动应用AI推荐的角色映射到characterVoiceMapping
  Object.values(characterStats).forEach(char => {
    if (char.voice_id) {
      characterVoiceMapping[char.name] = char.voice_id
    }
  })
  
  console.log('已更新角色配置:', {
    characters: detectedCharacters.value,
    characterVoiceMapping: characterVoiceMapping,
    extractedFromSynthesisPlan: Object.keys(characterStats).length,
    totalSegments: mockResult.value.synthesis_plan?.length || 0
  })
}

// 获取角色示例文本
const getCharacterSampleText = (characterName) => {
  // 从合成计划中找到该角色的文本示例
  if (mockResult.value?.synthesis_plan) {
    const characterSegment = mockResult.value.synthesis_plan.find(segment => 
      segment.speaker === characterName
    )
    if (characterSegment) {
      return characterSegment.text.slice(0, 30) + '...'
    }
  }
  
  // 默认示例文本
  const samples = {
    '李维': '数据的流动模式确实很有趣。',
    '艾莉': '你有没有觉得这些数据像是在讲故事？',
    '系统旁白': '在数字化时代的浪潮中，数据如同蚕茧般包裹着我们的生活。',
    '心理旁白': '李维思考着艾莉的话，意识到数据背后可能隐藏着更深层的含义。'
  }
  
  return samples[characterName] || '这是一段示例文本用于声音试听。'
}

const clearMockResult = () => {
  mockResult.value = null
  message.info('智能分析结果已清空')
}

// JSON测试方法

const cancelJsonTest = () => {
  jsonTestModalVisible.value = false
  jsonTestContent.value = ''
  jsonValidationResult.value = null
}

const formatJsonContent = () => {
  try {
    if (!jsonTestContent.value.trim()) {
      message.warning('请先输入JSON内容')
      return
    }
    
    const parsed = JSON.parse(jsonTestContent.value)
    jsonTestContent.value = JSON.stringify(parsed, null, 2)
    message.success('JSON格式化完成')
  } catch (error) {
    message.error('JSON格式错误: ' + error.message)
  }
}

const validateJsonContent = () => {
  try {
    if (!jsonTestContent.value.trim()) {
      jsonValidationResult.value = {
        valid: false,
        message: '请输入JSON内容',
        description: '输入框不能为空'
      }
      return
    }
    
    const parsed = JSON.parse(jsonTestContent.value)
    
    // 支持两种格式：直接包含字段 或 嵌套在data字段中
    const dataObj = parsed.data || parsed
    
    // 验证必要字段
    const requiredFields = ['project_info', 'characters']
    // segments字段改为synthesis_plan，这是实际使用的字段名
    const optionalFields = ['synthesis_plan', 'segments']
    const missingRequired = requiredFields.filter(field => !dataObj[field])
    const hasSegments = optionalFields.some(field => Array.isArray(dataObj[field]) && dataObj[field].length > 0)
    
    if (missingRequired.length > 0) {
      jsonValidationResult.value = {
        valid: false,
        message: '缺少必要字段',
        description: `缺少以下字段: ${missingRequired.join(', ')}`
      }
      return
    }
    
    // 检查角色数据
    if (!Array.isArray(dataObj.characters) || dataObj.characters.length === 0) {
      jsonValidationResult.value = {
        valid: false,
        message: '角色数据无效',
        description: 'characters字段必须是非空数组'
      }
      return
    }
    
    // 检查分段数据 (synthesis_plan 或 segments)
    if (!hasSegments) {
      jsonValidationResult.value = {
        valid: false,
        message: '分段数据无效',
        description: 'synthesis_plan 或 segments 字段必须是非空数组'
      }
      return
    }
    
    // 详细检查synthesis_plan的数据格式
    const segmentData = dataObj.synthesis_plan || dataObj.segments
    const segmentCount = segmentData.length
    const formatErrors = []
    
    segmentData.forEach((segment, index) => {
      const segmentNum = index + 1
      
      // 检查必要字段
      if (!segment.text || segment.text.trim() === '') {
        formatErrors.push(`第${segmentNum}段缺少text字段`)
      }
      
      // 检查voice_id字段（支持多种格式）
      const hasVoiceId = segment.voice_id || segment.voiceId || 
                        segment.voice_config?.voice_id || segment.voice_config?.voiceId
      const hasSpeaker = segment.speaker || segment.character
      
      if (!hasVoiceId && !hasSpeaker) {
        formatErrors.push(`第${segmentNum}段缺少voice_id或speaker字段`)
      }
      
      // 如果使用voice_config嵌套结构，给出格式建议
      if (segment.voice_config && !segment.voice_id) {
        formatErrors.push(`第${segmentNum}段使用了voice_config嵌套结构，建议改为直接的voice_id字段`)
      }
    })
    
    if (formatErrors.length > 0) {
      jsonValidationResult.value = {
        valid: false,
        message: 'synthesis_plan格式错误',
        description: `发现 ${formatErrors.length} 个问题:\n${formatErrors.join('\n')}\n\n推荐格式: 每个段落应包含 text, voice_id, speaker 字段`
      }
      return
    }
    
    jsonValidationResult.value = {
      valid: true,
      message: 'JSON格式验证通过',
      description: `包含 ${dataObj.characters.length} 个角色，${segmentCount} 个文本段落`
    }
    
  } catch (error) {
    jsonValidationResult.value = {
      valid: false,
      message: 'JSON语法错误',
      description: error.message
    }
  }
}

const clearJsonContent = () => {
  jsonTestContent.value = ''
  jsonValidationResult.value = null
  message.info('内容已清空')
}

const executeJsonTest = async () => {
  if (!jsonTestContent.value.trim()) {
    message.error('请输入JSON内容')
    return
  }
  
  jsonTestExecuting.value = true
  try {
    console.log('=== 开始执行JSON测试 ===')
    
    // 先验证JSON格式
    validateJsonContent()
    if (!jsonValidationResult.value?.valid) {
      message.error('JSON格式验证失败，请修正后重试')
      return
    }
    
    // 解析JSON数据
    const parsed = JSON.parse(jsonTestContent.value)
    console.log('解析的JSON数据:', parsed)
    
    // 支持两种格式：直接包含字段 或 嵌套在data字段中
    const dataObj = parsed.data || parsed
    mockResult.value = dataObj
    
    // 关闭弹窗
    jsonTestModalVisible.value = false
    
    // 更新角色配置
    updateCharactersFromAnalysis()
    
    message.success('JSON测试数据已加载！请查看匹配结果并应用配置')
    console.log('JSON测试结果已设置:', mockResult.value)
    
  } catch (error) {
    console.error('JSON测试执行错误:', error)
    message.error('执行失败: ' + error.message)
  } finally {
    jsonTestExecuting.value = false
  }
}

// 加载项目详情
const loadProject = async () => {
  try {
    const projectId = route.params.projectId
    const response = await readerAPI.getProjectDetail(projectId)
    
    if (response.data.success) {
      project.value = response.data.data
      
      // 初始化统计信息
      project.value.statistics = reactive({
        totalSegments: project.value.total_segments || 0,
        completedSegments: project.value.processed_segments || 0,
        failedSegments: 0,
        processingSegments: 0,
        pendingSegments: 0
      })
      
      // 🚀 修复：始终获取最新统计信息，不管项目状态
      try {
        const progressResponse = await readerAPI.getProgress(projectId)
        if (progressResponse.data.success) {
          const progress = progressResponse.data.data
          console.log('📊 获取到进度数据:', progress)
          
          // 更新统计信息，映射字段名
          Object.assign(project.value.statistics, {
            totalSegments: progress.segments.total,
            completedSegments: progress.segments.completed,
            failedSegments: progress.segments.failed,
            processingSegments: progress.segments.processing,
            pendingSegments: progress.segments.pending
          })
          
          // 同步更新项目基础字段
          project.value.total_segments = progress.segments.total
          project.value.processed_segments = progress.segments.completed
          project.value.status = progress.status
          project.value.current_segment = progress.current_segment
          
          // 同步更新进度数据用于显示
          progressData.value = {
            progress: progress.progress_percentage || 0,
            status: progress.status,
            completed_segments: progress.segments.completed,
            total_segments: progress.segments.total,
            failed_segments: progress.segments.failed,
            current_processing: progress.status === 'processing' ? `正在处理第 ${progress.current_segment || 1} 段` : '等待开始'
          }
          
          console.log('📊 更新后的statistics:', project.value.statistics)
          console.log('📊 更新后的progressData:', progressData.value)
        } else {
          console.warn('获取进度失败，使用项目基础数据:', progressResponse.data.message)
          // Fallback到项目基础数据
          progressData.value = {
            progress: project.value.total_segments > 0 ? Math.round((project.value.processed_segments / project.value.total_segments) * 100) : 0,
            status: project.value.status,
            completed_segments: project.value.processed_segments || 0,
            total_segments: project.value.total_segments || 0,
            failed_segments: Math.max(0, (project.value.total_segments || 0) - (project.value.processed_segments || 0)),
            current_processing: '等待开始'
          }
        }
      } catch (error) {
        console.warn('获取进度异常，使用项目基础数据:', error)
        // Fallback到项目基础数据
        progressData.value = {
          progress: project.value.total_segments > 0 ? Math.round((project.value.processed_segments / project.value.total_segments) * 100) : 0,
          status: project.value.status,
          completed_segments: project.value.processed_segments || 0,
          total_segments: project.value.total_segments || 0,
          failed_segments: Math.max(0, (project.value.total_segments || 0) - (project.value.processed_segments || 0)),
          current_processing: '等待开始'
        }
      }
      
      console.log('🔍 最终的currentProgressData:', currentProgressData.value)
      
      await analyzeCharacters()
    }
  } catch (error) {
    console.error('加载项目失败:', error)
    message.error('加载项目失败')
  } finally {
    loading.value = false
  }
}

// 刷新项目数据
const refreshProjectData = async () => {
  if (refreshing.value) return
  
  refreshing.value = true
  try {
    console.log('🔄 手动刷新项目数据...')
    const projectId = route.params.projectId
    
    // 重新加载项目数据
    const response = await readerAPI.getProjectDetail(projectId)
    if (response.data.success) {
      const newProject = response.data.data
      
      console.log('🔄 刷新前数据:', {
        total: project.value.total_segments,
        processed: project.value.processed_segments,
        statistics: project.value.statistics
      })
      
      // 更新项目数据
      project.value = newProject
      
      // 重新初始化统计信息
      project.value.statistics = reactive({
        totalSegments: newProject.total_segments || 0,
        completedSegments: newProject.processed_segments || 0,
        failedSegments: 0,
        processingSegments: 0,
        pendingSegments: 0
      })
      
      // 如果项目正在处理，获取最新进度
      if (newProject.status === 'processing' || newProject.total_segments > 0) {
        try {
          const progressResponse = await readerAPI.getProgress(projectId)
          if (progressResponse.data.success) {
            const progress = progressResponse.data.data
            Object.assign(project.value.statistics, {
              totalSegments: progress.segments.total,
              completedSegments: progress.segments.completed,
              failedSegments: progress.segments.failed,
              processingSegments: progress.segments.processing,
              pendingSegments: progress.segments.pending
            })
            
            // 同步更新项目原始字段
            project.value.total_segments = progress.segments.total
            project.value.processed_segments = progress.segments.completed
            project.value.status = progress.status
            project.value.current_segment = progress.current_segment
          }
        } catch (progressError) {
          console.warn('获取进度失败:', progressError)
        }
      }
      
      // 更新进度显示数据
      progressData.value = {
        progress: project.value.total_segments > 0 ? Math.round((project.value.processed_segments / project.value.total_segments) * 100) : 0,
        status: project.value.status,
        completed_segments: project.value.processed_segments || 0,
        total_segments: project.value.total_segments || 0,
        failed_segments: project.value.statistics?.failedSegments || 0,
        current_processing: project.value.status === 'processing' ? `正在处理第 ${project.value.current_segment || 1} 段` : '等待开始'
      }
      
      console.log('🔄 刷新后数据:', {
        total: project.value.total_segments,
        processed: project.value.processed_segments,
        statistics: project.value.statistics,
        progressPercent: progressPercent.value
      })
      
      message.success('数据已刷新')
    } else {
      message.error('刷新失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('刷新项目数据失败:', error)
    message.error('刷新失败: ' + error.message)
  } finally {
    refreshing.value = false
  }
}

// 分析角色
const analyzeCharacters = async () => {
  if (!project.value?.segments) return
  
  try {
    const characterStats = {}
    project.value.segments.forEach(segment => {
      const speaker = segment.detected_speaker || '温柔女声'
      if (!characterStats[speaker]) {
        characterStats[speaker] = {
          name: speaker,
          count: 0,
          samples: []
        }
      }
      characterStats[speaker].count++
      if (characterStats[speaker].samples.length < 3 && segment.text_content) {
        characterStats[speaker].samples.push(segment.text_content.slice(0, 30) + '...')
      }
    })
    
    detectedCharacters.value = Object.values(characterStats)
    
    // 加载现有的角色映射
    if (project.value.character_mapping) {
      Object.assign(characterVoiceMapping, project.value.character_mapping)
    }
    
  } catch (error) {
    console.error('分析角色失败:', error)
    message.error('分析角色失败')
  }
}

// 加载可用声音
const loadVoices = async () => {
  try {
    const response = await charactersAPI.getVoiceProfiles({ status: 'active' })
    if (response.data.success) {
      availableVoices.value = response.data.data
    }
  } catch (error) {
    console.error('加载声音列表失败:', error)
  }
}

// 试听声音
const playVoicePreview = async (voiceId, sampleText) => {
  try {
    // 检查是否正在播放，如果是则停止
    if (currentPlayingVoice.value === voiceId && currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
      currentPlayingVoice.value = null
      return
    }

    // 停止其他正在播放的音频
    if (currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
      currentPlayingVoice.value = null
    }

    if (!voiceId) {
      message.warning('请选择声音')
      return
    }

    if (!sampleText) {
      message.warning('没有示例文本')
      return
    }

    previewLoading.value = voiceId
    
    // 找到对应的声音配置
    const selectedVoice = availableVoices.value.find(v => v.id === voiceId)
    if (!selectedVoice) {
      message.error('找不到声音配置')
      return
    }

    // 使用统一的API调用替代直接fetch
    const testParams = {
      text: sampleText || '这是声音预览测试',
      time_step: 20,
      p_weight: 1.0,
      t_weight: 1.0
    }
    
    const response = await charactersAPI.testVoiceSynthesis(selectedVoice.id, testParams)

    if (response.data && response.data.success && response.data.audioUrl) {
      // 构建完整的音频URL
      const audioUrl = response.data.audioUrl.startsWith('http') ? response.data.audioUrl : response.data.audioUrl
      
      // 创建音频元素
      const audio = new Audio(audioUrl)
      currentAudio.value = audio
      currentPlayingVoice.value = voiceId

      // 播放事件处理
      audio.addEventListener('loadstart', () => {
        message.success('开始播放试听')
      })

      audio.addEventListener('ended', () => {
        currentAudio.value = null
        currentPlayingVoice.value = null
      })

      audio.addEventListener('error', (e) => {
        console.error('音频播放错误:', e)
        currentAudio.value = null
        currentPlayingVoice.value = null
        message.error('音频播放失败')
      })

      // 开始播放
      await audio.play()
    } else {
      throw new Error(response.data?.message || '后端API返回错误')
    }
    
  } catch (error) {
    console.error('试听失败:', error)
    
    if (error.name === 'AbortError') {
      message.error('试听请求超时（90秒），TTS服务可能正在处理中，请稍后重试')
    } else if (error.message.includes('GPU') || error.message.includes('CUDA')) {
      message.error('GPU处理出错，请等待几秒后重试')
    } else if (error.message.includes('TTS服务内部错误')) {
      message.error('TTS服务出现内部错误，可能是GPU显存不足')
    } else if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
      message.error('无法连接到TTS服务，请检查服务状态')
    } else {
      message.error('试听失败: ' + error.message)
    }
  } finally {
    previewLoading.value = null
  }
}

// 开始合成
const startSynthesis = async () => {
  synthesisStarting.value = true
  try {
    console.log('=== 启动章节合成流程 ===')
    console.log('选中章节:', selectedChapters.value)
    
    // 构建合成参数 - 固定为章节模式
    const synthesisParams = {
      parallel_tasks: synthesisConfig.parallelTasks,
      synthesis_mode: 'chapters',
      chapter_ids: selectedChapters.value
    }
    
    message.info(`开始合成选中的 ${selectedChapters.value.length} 个章节`)
    
    const response = await readerAPI.startGeneration(project.value.id, synthesisParams)
    
    if (response.data.success) {
      message.success('合成任务已启动')
      project.value.status = 'processing'
      
      // 初始化合成进度监控
      initializeSynthesisMonitoring()
      
      // 打开进度监控抽屉
      synthesisProgressDrawer.value = true
      
      startWebSocketProgressMonitoring()
    } else {
      throw new Error(response.data.message || '启动失败')
    }
  } catch (error) {
    console.error('启动合成失败:', error)
    message.error('启动合成失败: ' + error.message)
  } finally {
    synthesisStarting.value = false
  }
}

// 暂停合成
const pauseSynthesis = async () => {
  pausingGeneration.value = true
  try {
    // 先检查当前状态
    const currentStatus = project.value.status
    console.log('暂停前项目状态:', currentStatus)
    
    if (currentStatus !== 'processing') {
      message.warning(`当前状态为 ${currentStatus}，无法暂停`)
      return
    }
    
    await readerAPI.pauseGeneration(project.value.id)
    message.success('合成已暂停')
    project.value.status = 'paused'
    
    // 暂停时停止WebSocket监控和计时器，但保持抽屉打开
    stopWebSocketProgressMonitoring()
    stopElapsedTimer()
    
    // 更新进度数据状态为暂停
    if (synthesisProgressDrawer.value) {
      progressData.value.status = 'paused'
      progressData.value.current_processing = '⏸️ 合成已暂停'
    }
  } catch (error) {
    console.error('暂停合成失败:', error)
    
    // 如果是状态错误，尝试刷新项目状态
    if (error.response?.data?.message?.includes('无法暂停')) {
      message.warning('项目状态已改变，正在刷新...')
      await refreshProjectStatus()
    } else {
      message.error('暂停合成失败: ' + (error.response?.data?.message || error.message))
    }
  } finally {
    pausingGeneration.value = false
  }
}

// 继续合成
const resumeSynthesis = async () => {
  resumingGeneration.value = true
  try {
    // 先检查当前状态
    const currentStatus = project.value.status
    console.log('继续前项目状态:', currentStatus)
    
    if (currentStatus !== 'paused' && currentStatus !== 'failed' && currentStatus !== 'partial_completed') {
      message.warning(`当前状态为 ${currentStatus}，无法继续合成`)
      return
    }
    
    // 根据状态选择合适的API
    if (currentStatus === 'paused') {
      // 暂停状态使用resume接口
      await readerAPI.resumeGeneration(project.value.id, {
        parallel_tasks: synthesisConfig.parallelTasks
      })
    } else {
      // failed 和 partial_completed 状态使用start接口
      await readerAPI.startGeneration(project.value.id, {
        parallel_tasks: synthesisConfig.parallelTasks
      })
    }
    message.success('合成已继续')
    project.value.status = 'processing'
    
    // 继续合成时也要重新初始化监控
    initializeSynthesisMonitoring()
    
    // 打开进度监控抽屉
    synthesisProgressDrawer.value = true
    
    startWebSocketProgressMonitoring()
  } catch (error) {
    console.error('继续合成失败:', error)
    
    // 如果是状态错误，尝试刷新项目状态
    if (error.response?.data?.message?.includes('状态')) {
      message.warning('项目状态已改变，正在刷新...')
      await refreshProjectStatus()
    } else {
      message.error('继续合成失败: ' + (error.response?.data?.message || error.message))
    }
  } finally {
    resumingGeneration.value = false
  }
}

// 取消合成
const cancelSynthesis = async () => {
  // 显示确认对话框
  Modal.confirm({
    title: '确认取消合成',
    content: '取消后已完成的片段将保留，但未完成的部分需要重新开始。确定要取消合成吗？',
    okText: '确定取消',
    okType: 'danger',
    cancelText: '继续合成',
    onOk: async () => {
      cancelingGeneration.value = true
      try {
        // 先检查当前项目状态
        const currentStatus = project.value.status
        console.log('当前项目状态:', currentStatus)
        
        // 如果当前状态是 processing，先暂停
        if (currentStatus === 'processing') {
          await readerAPI.pauseGeneration(project.value.id)
        }
        
        // 更新项目状态为已取消（无论之前是什么状态）
        project.value.status = 'cancelled'
        
        // 停止所有监控
        stopWebSocketProgressMonitoring()
        stopElapsedTimer()
        
        // 更新进度数据状态
        if (synthesisProgressDrawer.value) {
          progressData.value.status = 'cancelled'
          progressData.value.current_processing = '⏹️ 合成已取消'
        }
        
        message.success('合成已取消')
      } catch (error) {
        console.error('取消合成失败:', error)
        
        // 如果是因为状态不匹配的错误，直接标记为取消
        if (error.response?.data?.message?.includes('无法暂停')) {
          project.value.status = 'cancelled'
          stopWebSocketProgressMonitoring()
          stopElapsedTimer()
          
          if (synthesisProgressDrawer.value) {
            progressData.value.status = 'cancelled'
            progressData.value.current_processing = '⏹️ 合成已取消'
          }
          
          message.success('合成已取消')
        } else {
          message.error('取消合成失败: ' + (error.response?.data?.message || error.message))
        }
      } finally {
        cancelingGeneration.value = false
      }
    }
  })
}

// 下载音频
const downloadAudio = async () => {
  // 检查项目状态
  if (project.value?.status !== 'completed') {
    const statusText = {
      'pending': '等待处理',
      'configured': '已配置但未开始生成',
      'processing': '正在生成中',
      'paused': '已暂停',
      'failed': '生成失败'
    }[project.value?.status] || '未知状态'
    
    message.warning(`无法下载：项目当前状态为"${statusText}"，请先完成音频生成`)
    return
  }
  
  try {
    const response = await readerAPI.downloadAudio(project.value.id)
    // 处理文件下载
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value.name}_final.wav`
    link.click()
    window.URL.revokeObjectURL(url)
    message.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    
    // 改进错误处理
    let errorMessage = '下载失败'
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message === 'Network Error') {
      errorMessage = '网络连接失败，请检查网络连接或稍后重试'
    } else if (error.code === 'ERR_CONNECTION_RESET') {
      errorMessage = '连接被重置，请检查后端服务状态'
    }
    
    message.error(errorMessage)
  }
}

// 重新合成
const restartSynthesis = async () => {
  if (!project.value) return
  
  synthesisStarting.value = true
  try {
    const response = await readerAPI.startGeneration(project.value.id, {
      parallel_tasks: synthesisConfig.parallelTasks
    })
    
    if (response.data.success) {
      message.success('重新合成任务已启动')
      project.value.status = 'processing'
      
      // 初始化合成进度监控（重新合成也需要）
      initializeSynthesisMonitoring()
      
      // 打开进度监控抽屉
      synthesisProgressDrawer.value = true
      
      startWebSocketProgressMonitoring()
    }
  } catch (error) {
    console.error('重新启动合成失败:', error)
    message.error('重新启动合成失败')
  } finally {
    synthesisStarting.value = false
  }
}

// 刷新项目状态
const refreshProjectStatus = async () => {
  try {
    const response = await readerAPI.getProjectDetail(project.value.id)
    if (response.data.success) {
      const newStatus = response.data.data.status
      console.log('刷新后项目状态:', newStatus)
      
      project.value.status = newStatus
      
      // 同步更新进度数据状态
      if (synthesisProgressDrawer.value) {
        progressData.value.status = newStatus
        
        if (newStatus === 'paused') {
          progressData.value.current_processing = '⏸️ 合成已暂停'
        } else if (newStatus === 'processing') {
          progressData.value.current_processing = '🎵 合成进行中...'
        } else if (newStatus === 'completed') {
          progressData.value.current_processing = '✅ 合成已完成'
        }
      }
      
      message.info(`项目状态已更新为: ${getStatusText(newStatus)}`)
    }
  } catch (error) {
    console.error('刷新项目状态失败:', error)
    message.error('无法获取最新状态')
  }
}

// 查看项目详情
const viewProjectDetail = () => {
  router.push(`/novel-reader/detail/${project.value.id}`)
}

// 音频预览相关处理
const handleAudioLoadStart = () => {
  console.log('音频开始加载')
}

const handleAudioError = (error) => {
  console.error('音频加载失败:', error)
  // 只在项目状态为completed时才显示错误，避免中间状态的误报
  if (project.value?.status === 'completed') {
    message.warning('音频文件暂时不可用，可能正在后处理中，请稍后刷新或尝试下载')
  } else {
    console.log('项目尚未完成，忽略音频加载错误')
  }
}

// 检查TTS服务状态
const checkTTSService = async () => {
  checkingService.value = true
  try {
    // 使用统一的健康检查API
    const response = await systemAPI.healthCheck()
    
    if (response.data) {
      const data = response.data
      if (data.services?.tts_client?.status === 'healthy') {
        message.success('TTS服务正常运行中')
      } else {
        message.warning('TTS服务已启动但状态异常')
      }
    } else {
      throw new Error('健康检查返回数据异常')
    }
  } catch (error) {
    console.error('TTS服务检查失败:', error)
    
    if (error.message.includes('Network')) {
      message.error('无法连接到TTS服务，请检查服务是否启动')
    } else {
      message.error('TTS服务异常: ' + error.message)
    }
  } finally {
    checkingService.value = false
  }
}

// WebSocket进度监控 - 替代轮询机制
const startWebSocketProgressMonitoring = () => {
  // 先停止之前的订阅（避免重复订阅）
  if (unsubscribeWebSocket.value) {
    stopWebSocketProgressMonitoring()
  }
  
  // 确保WebSocket连接
  wsStore.connect()
  
  // 订阅合成进度更新主题
  unsubscribeWebSocket.value = wsStore.subscribe('topic_message', (data, fullMessage) => {
    // 检查是否为当前项目的进度更新
    if (fullMessage.topic === `synthesis_${project.value?.id}` && data.type === 'progress_update') {
      const progressData = data.data
      console.log('📨 收到WebSocket进度更新:', progressData)
      
      // 更新项目统计信息
      console.log('📊 更新前的project.statistics:', project.value.statistics)
      
      // 确保statistics存在且是响应式的
      if (!project.value.statistics) {
        project.value.statistics = reactive({
          totalSegments: 0,
          completedSegments: 0,
          failedSegments: 0,
          processingSegments: 0,
          pendingSegments: 0
        })
      }
      
      // 使用Object.assign保持响应式，同时同步项目原始字段
      Object.assign(project.value.statistics, {
        totalSegments: progressData.total_segments,
        completedSegments: progressData.completed_segments,
        failedSegments: progressData.failed_segments,
        processingSegments: progressData.total_segments - progressData.completed_segments - progressData.failed_segments,
        pendingSegments: 0
      })
      
      // 同步更新项目原始字段，确保数据一致性
      project.value.total_segments = progressData.total_segments
      project.value.processed_segments = progressData.completed_segments
      project.value.status = progressData.status
      project.value.current_segment = progressData.current_segment || 0
      
      // 同时更新progress抽屉的数据，确保数据一致性
      updateProgressDataFromWebSocket(progressData)
      
      console.log('📊 更新后的project.statistics:', project.value.statistics)
      console.log('📊 更新后的project原始字段:', {
        total_segments: project.value.total_segments,
        processed_segments: project.value.processed_segments
      })
      console.log('🔢 计算的progressPercent:', progressPercent.value)
      console.log('🔢 统一的进度数据:', currentProgressData.value)
      
      // 如果进度监控抽屉已打开，同步更新进度数据
      if (synthesisProgressDrawer.value) {
        updateProgressDataFromWebSocket(progressData)
      }
      
      // 强制更新进度显示数据（确保进度条实时更新）
      updateProgressDataFromWebSocket(progressData)
      
      // 更新当前处理段落信息
      currentProcessingSegment.value = getCurrentProcessingSegment()
      
      // 如果有新完成的片段，加载已完成片段列表
      if (progressData.completed_segments > (completedSegments.value.length || 0)) {
        loadCompletedSegments()
      }
      
      // 检查完成状态
      if (progressData.status === 'completed') {
        stopWebSocketProgressMonitoring()
        stopElapsedTimer()
        loadProject()
        message.success('🎉 音频合成完成！')
      } else if (progressData.status === 'partial_completed') {
        stopWebSocketProgressMonitoring()
        stopElapsedTimer()
        loadProject()
        const failedCount = progressData.failed_segments || 0
        if (failedCount > 0) {
          message.warning(`⚠️ 合成部分完成！${progressData.completed_segments}/${progressData.total_segments} 个段落成功，${failedCount} 个失败`)
        } else {
          message.success('🎉 音频合成部分完成！')
        }
      } else if (progressData.status === 'failed') {
        stopWebSocketProgressMonitoring()  
        stopElapsedTimer()
        loadProject()
        message.error('❌ 音频合成失败')
      } else if (progressData.status === 'cancelled') {
        stopWebSocketProgressMonitoring()
        stopElapsedTimer()
        message.info('⏹️ 音频合成已取消')
      }
    }
  })
  
  // 发送主题订阅请求
  wsStore.sendMessage('subscribe', {
    topic: `synthesis_${project.value.id}`
  })
  
  console.log('🔌 WebSocket进度监控已启动，topic:', `synthesis_${project.value.id}`)
}

const stopWebSocketProgressMonitoring = () => {
  if (unsubscribeWebSocket.value) {
    // 发送取消订阅请求
    wsStore.sendMessage('unsubscribe', {
      topic: `synthesis_${project.value.id}`
    })
    
    // 取消本地订阅
    unsubscribeWebSocket.value()
    unsubscribeWebSocket.value = null
    console.log('🔌 WebSocket进度监控已停止')
  }
}

// 加载智能准备结果
const loadPreparationResults = async () => {
  if (!project.value?.book?.id) {
    message.warning('项目未关联书籍，无法加载智能准备结果')
    return
  }
  
  if (selectedChapters.value.length === 0) {
    message.warning('请先选择要合成的章节')
    return
  }
  
  loadingResults.value = true
  try {
    // 只获取选中章节的智能准备结果
    const response = await booksAPI.getBookAnalysisResults(project.value.book.id, {
      chapter_ids: selectedChapters.value
    })
    
    if (response.data.success) {
      preparationResults.value = response.data
      
      // 聚合所有章节的角色数据
      const allCharacters = {}
      let totalSegments = 0
      
      response.data.data.forEach(chapterResult => {
        const synthesisJson = chapterResult.synthesis_json
        
        // 聚合角色
        if (synthesisJson.characters) {
          synthesisJson.characters.forEach(char => {
            const charName = char.name
            if (!allCharacters[charName]) {
              allCharacters[charName] = {
                name: charName,
                voice_id: char.voice_id,
                voice_name: char.voice_name,
                frequency: 0,
                samples: []
              }
            }
            allCharacters[charName].frequency += 1
            
            // 收集示例文本
            if (synthesisJson.synthesis_plan) {
              const characterSegments = synthesisJson.synthesis_plan.filter(seg => seg.speaker === charName)
              characterSegments.slice(0, 3).forEach(seg => {
                if (seg.text && !allCharacters[charName].samples.includes(seg.text.slice(0, 30))) {
                  allCharacters[charName].samples.push(seg.text.slice(0, 30) + '...')
                }
              })
            }
          })
        }
        
        // 统计段落数
        if (synthesisJson.synthesis_plan) {
          totalSegments += synthesisJson.synthesis_plan.length
        }
      })
      
      // 更新检测到的角色
      detectedCharacters.value = Object.values(allCharacters)
      
      // 自动应用AI推荐的角色映射
      Object.values(allCharacters).forEach(char => {
        if (char.voice_id) {
          characterVoiceMapping[char.name] = char.voice_id
        }
      })
      
      message.success(`成功加载 ${selectedChapters.value.length} 个章节的智能准备结果：${detectedCharacters.value.length} 个角色，${totalSegments} 个段落`)
      
    } else {
      message.error('加载智能准备结果失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('加载智能准备结果失败:', error)
    message.error('加载智能准备结果失败: ' + error.message)
  } finally {
    loadingResults.value = false
  }
}

// 刷新智能准备结果
const refreshPreparationResults = async () => {
  preparationResults.value = null
  await loadPreparationResults()
}

// 清空智能准备结果
const clearPreparationResults = () => {
  preparationResults.value = null
  detectedCharacters.value = []
  Object.keys(characterVoiceMapping).forEach(key => {
    delete characterVoiceMapping[key]
  })
  message.info('智能准备结果已清空')
}

// 获取总段落数
const getTotalSegments = () => {
  if (!preparationResults.value?.data) return 0
  
  return preparationResults.value.data.reduce((total, chapterResult) => {
    const synthesisJson = chapterResult.synthesis_json
    return total + (synthesisJson.synthesis_plan?.length || 0)
  }, 0)
}

// 获取角色样式类
const getCharacterClass = (speaker) => {
  const colors = ['primary', 'warning', 'success', 'info', 'error']
  const hash = speaker.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return `character-${colors[hash % colors.length]}`
}

// 获取当前处理段落信息
const getCurrentProcessingSegment = () => {
  if (!preparationResults.value?.data || !project.value?.current_segment) {
    return null
  }
  
  let segmentCounter = 0
  for (const chapterResult of preparationResults.value.data) {
    const segments = chapterResult.synthesis_json?.synthesis_plan || []
    for (const segment of segments) {
      segmentCounter++
      if (segmentCounter === project.value.current_segment) {
        return segment
      }
    }
  }
  return null
}

// 加载已完成的片段
const loadCompletedSegments = async () => {
  if (!project.value?.id) return
  
  try {
    // 这里应该调用API获取已完成的片段
    // 暂时使用模拟数据
    const mockCompletedSegments = []
    for (let i = 0; i < (project.value.statistics?.completedSegments || 0); i++) {
      mockCompletedSegments.push({
        id: i + 1,
        speaker: '角色' + ((i % 3) + 1),
        text: `这是第${i + 1}个已完成的合成片段，内容会在这里显示...`,
        audio_url: `/api/v1/novel-reader/projects/${project.value.id}/segments/${i + 1}/audio`,
        duration: 3.5 + Math.random() * 2 // 模拟时长
      })
    }
    completedSegments.value = mockCompletedSegments
  } catch (error) {
    console.error('加载已完成片段失败:', error)
  }
}

// 刷新已完成片段
const refreshCompletedSegments = async () => {
  loadingCompletedSegments.value = true
  try {
    await loadCompletedSegments()
  } finally {
    loadingCompletedSegments.value = false
  }
}

// 播放片段音频
const playSegmentAudio = async (segment) => {
  try {
    // 停止当前播放
    if (segmentAudioPlayer.value) {
      segmentAudioPlayer.value.pause()
      segmentAudioPlayer.value.currentTime = 0
    }
    
    if (playingSegment.value === segment.id) {
      // 如果点击的是正在播放的，则停止播放
      playingSegment.value = null
      return
    }
    
    playingSegment.value = segment.id
    
    // 创建新的音频播放器
    segmentAudioPlayer.value = new Audio(segment.audio_url)
    
    segmentAudioPlayer.value.addEventListener('ended', () => {
      playingSegment.value = null
    })
    
    segmentAudioPlayer.value.addEventListener('error', (e) => {
      console.error('音频播放失败:', e)
      message.error('音频播放失败')
      playingSegment.value = null
    })
    
    await segmentAudioPlayer.value.play()
    
  } catch (error) {
    console.error('播放片段音频失败:', error)
    message.error('音频播放失败: ' + error.message)
    playingSegment.value = null
  }
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 声音选项过滤
const filterVoiceOption = (input, option) => {
  return option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

// WebSocket设置 - 已移除，统一使用startWebSocketProgressMonitoring方法

// 生命周期
onMounted(async () => {
  await loadProject()
  await loadVoices()
  
  // 自动加载章节（因为现在固定为章节模式）
  autoLoadChapters()
  
  // 如果有已完成的片段，加载它们
  if (project.value?.statistics?.completedSegments > 0) {
    await loadCompletedSegments()
  }
  
  // 如果正在处理中，启动WebSocket监控并自动打开监控抽屉
  if (project.value?.status === 'processing') {
    currentProcessingSegment.value = getCurrentProcessingSegment()
    
    // 自动初始化合成进度监控
    initializeSynthesisMonitoring()
    
    // 自动打开进度监控抽屉
    synthesisProgressDrawer.value = true
    
    startWebSocketProgressMonitoring()
  }
})

// 页面切换前的清理
onBeforeRouteLeave(() => {
  stopWebSocketProgressMonitoring()
  return true
})

// 组件卸载时的清理
onUnmounted(() => {
  stopWebSocketProgressMonitoring()
  stopElapsedTimer()
  // 清理WebSocket监听器
  if (unsubscribeWebSocket.value) {
    unsubscribeWebSocket.value()
  }
})

// 浏览器刷新/关闭前的清理
window.addEventListener('beforeunload', () => {
  stopWebSocketProgressMonitoring()
})

// 合成进度监控相关方法
const initializeSynthesisMonitoring = () => {
  // 重置进度数据
  progressData.value = {
    progress: 0,
    status: 'processing',
    completed_segments: 0,
    total_segments: 0,
    failed_segments: 0,
    current_processing: '正在准备合成...'
  }
  
  // 初始化段落状态列表
  initializeSegmentStatuses()
  
  // 记录合成开始时间
  synthesisStartTime.value = Date.now()
  
  // 启动计时器
  startElapsedTimer()
}

const initializeSegmentStatuses = () => {
  // 从智能准备结果中初始化段落状态
  if (preparationResults.value?.data) {
    const segments = []
    let segmentIndex = 1
    
    preparationResults.value.data.forEach(chapterResult => {
      if (chapterResult.synthesis_json?.synthesis_plan) {
        chapterResult.synthesis_json.synthesis_plan.forEach(segment => {
          segments.push({
            segment_id: segmentIndex++,
            text: segment.text,
            speaker: segment.speaker,
            voice_id: segment.voice_id,
            voice_name: segment.voice_name,
            status: 'pending',
            playing: false,
            retrying: false,
            error_message: null,
            completion_time: null,
            audio_url: null
          })
        })
      }
    })
    
    segmentStatuses.value = segments
    progressData.value.total_segments = segments.length
  }
}

const startElapsedTimer = () => {
  if (elapsedTimer.value) {
    clearInterval(elapsedTimer.value)
  }
  
  elapsedTimer.value = setInterval(() => {
    if (synthesisStartTime.value) {
      synthesisElapsedTime.value = Math.floor((Date.now() - synthesisStartTime.value) / 1000)
    }
  }, 1000)
}

const stopElapsedTimer = () => {
  if (elapsedTimer.value) {
    clearInterval(elapsedTimer.value)
    elapsedTimer.value = null
  }
}

// 段落状态相关方法
const getSegmentStatusColor = (status) => {
  const colors = {
    pending: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error'
  }
  return colors[status] || 'default'
}

const getSegmentStatusText = (status) => {
  const texts = {
    pending: '等待中',
    processing: '合成中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

// 播放段落音频（智能监控版本）
const playSegmentAudioAdvanced = async (segment) => {
  if (!segment.audio_url) {
    message.warning('该段落音频尚未生成')
    return
  }
  
  // 停止其他正在播放的音频
  segmentStatuses.value.forEach(s => s.playing = false)
  
  segment.playing = true
  
  try {
    // 创建音频元素播放
    const audio = new Audio(segment.audio_url)
    
    audio.addEventListener('ended', () => {
      segment.playing = false
    })
    
    audio.addEventListener('error', () => {
      segment.playing = false
      message.error('音频播放失败')
    })
    
    await audio.play()
    
  } catch (error) {
    segment.playing = false
    console.error('播放音频失败:', error)
    message.error('播放音频失败: ' + error.message)
  }
}

// 重试单个段落
const retrySegment = async (segment) => {
  segment.retrying = true
  
  try {
    // 调用重试API
    const response = await readerAPI.retrySegment(project.value.id, segment.segment_id)
    
    if (response.data.success) {
      segment.status = 'processing'
      segment.error_message = null
      segment.retrying = false
      message.success(`段落 ${segment.segment_id} 重试已启动`)
    } else {
      throw new Error(response.data.message || '重试失败')
    }
  } catch (error) {
    console.error('重试段落失败:', error)
    message.error('重试失败: ' + error.message)
  } finally {
    segment.retrying = false
  }
}

// 重试所有失败段落
const retryAllFailedSegments = async () => {
  if (!project.value?.id) {
    message.error('项目信息不存在')
    return
  }
  
  resumingGeneration.value = true
  try {
    const response = await readerAPI.retryAllFailedSegments(project.value.id)
    
    if (response.data.success) {
      const retryCount = response.data.data.retried_segments
      if (retryCount > 0) {
        message.success(`已启动重试 ${retryCount} 个失败段落`)
        
        // 更新项目状态
        project.value.status = 'processing'
        
        // 重新初始化监控
        initializeSynthesisMonitoring()
        
        // 确保抽屉打开
        synthesisProgressDrawer.value = true
        
        // 重新启动WebSocket监控
        startWebSocketProgressMonitoring()
      } else {
        message.info('没有失败的段落需要重试')
      }
    } else {
      throw new Error(response.data.message || '重试失败')
    }
  } catch (error) {
    console.error('重试所有失败段落失败:', error)
    message.error('重试失败: ' + error.message)
  } finally {
    resumingGeneration.value = false
  }
}

// 下载最终音频
const downloadFinalAudio = async () => {
  try {
    const response = await readerAPI.downloadAudio(project.value.id)
    
    // 处理文件下载
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value.name}_complete.wav`
    link.click()
    window.URL.revokeObjectURL(url)
    
    message.success('完整音频下载成功')
  } catch (error) {
    console.error('下载完整音频失败:', error)
    message.error('下载失败: ' + error.message)
  }
}

// 下载部分音频（已完成的部分）
const downloadPartialAudio = async () => {
  try {
    const response = await readerAPI.downloadPartialAudio(project.value.id)
    
    // 处理文件下载
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value.name}_partial.wav`
    link.click()
    window.URL.revokeObjectURL(url)
    
    message.success('已完成部分音频下载成功')
  } catch (error) {
    console.error('下载部分音频失败:', error)
    message.error('下载失败: ' + error.message)
  }
}



// 时间格式化
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 更新进度数据从WebSocket推送
const updateProgressDataFromWebSocket = (data) => {
  console.log('🔍 WebSocket数据更新:', data)
  
  // 计算进度百分比 - 确保一致性
  const calculatedProgress = data.total_segments > 0 
    ? Math.round((data.completed_segments / data.total_segments) * 100) 
    : 0
  
  console.log('🔍 进度计算:', {
    completed: data.completed_segments,
    total: data.total_segments,
    calculated: calculatedProgress,
    original: data.progress
  })
  
  // 更新总体进度数据 - 统一使用计算的进度
  progressData.value = {
    progress: calculatedProgress,
    status: data.status,
    completed_segments: data.completed_segments || 0,
    total_segments: data.total_segments || 0,
    failed_segments: data.failed_segments || 0,
    current_processing: data.current_processing || `正在处理第 ${data.current_segment || 1} 段`
  }
  
  console.log('🔍 更新后progressData:', progressData.value)
  
  // 更新段落状态
  if (data.segments_status) {
    data.segments_status.forEach(segmentStatus => {
      const segment = segmentStatuses.value.find(s => s.segment_id === segmentStatus.segment_id)
      if (segment) {
        segment.status = segmentStatus.status
        segment.error_message = segmentStatus.error_message
        segment.completion_time = segmentStatus.completion_time
        segment.audio_url = segmentStatus.audio_url
      }
    })
  }
  
  // 如果合成完成或失败，停止计时器
  if (data.status === 'completed' || data.status === 'failed') {
    stopElapsedTimer()
  }
}
</script>

<style scoped>
/* 新的合成中心样式 */
.synthesis-center {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f7fa;
}

/* 顶部导航栏 */
.top-navbar {
  height: 64px;
  background: white;
  border-bottom: 1px solid #e8e8e8;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.05);
}

.nav-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  color: #666;
  font-size: 14px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.nav-right {
  display: flex;
  align-items: center;
}

/* 主布局 */
.synthesis-layout {
  flex: 1;
  display: flex;
  height: calc(100vh - 64px);
}

/* 左侧面板 */
.left-panel {
  width: 350px;
  background: white;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 20px 24px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h3 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.project-name {
  font-size: 13px;
  color: #666;
}

.chapter-selection-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chapter-controls {
  padding: 12px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fafafa;
}

.selection-count {
  font-size: 12px;
  color: #666;
}

.chapters-list {
  flex: 1;
  overflow-y: auto;
}

.loading-state {
  padding: 40px 24px;
  text-align: center;
}

.chapters-container {
  padding: 8px;
}

.chapter-card {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 12px 16px;
  margin-bottom: 8px;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  background: white;
}

.chapter-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.chapter-card.selected {
  background: #e6f7ff;
  border-color: #1890ff;
}

.chapter-checkbox {
  flex-shrink: 0;
  padding-top: 2px;
}

.chapter-info {
  flex: 1;
  min-width: 0;
}

.chapter-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.4;
  margin-bottom: 4px;
}

.chapter-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}

.word-count {
  color: #666;
}

.chapter-status {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
}

.empty-chapters {
  padding: 40px 24px;
  text-align: center;
}

.text-project-hint {
  padding: 24px;
}

/* 右侧面板 */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fafbfc;
}

/* 顶部操作栏 */
.action-toolbar {
  background: white;
  border-bottom: 1px solid #e8e8e8;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.start-btn,
.restart-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.start-btn:hover,
.restart-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

/* 内容预览区域 */
.content-preview {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 统计卡片 */
.stats-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stats-row {
  display: flex;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #1890ff;
  line-height: 1.2;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

/* 准备结果预览 */
.preparation-preview {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.dialogue-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.preview-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fafafa;
}

.preview-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.dialogue-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.chapter-divider {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 24px 0 16px;
  padding-bottom: 8px;
  border-bottom: 2px solid #f0f0f0;
}

.chapter-divider:first-child {
  margin-top: 0;
}

.chapter-title {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
}

.dialogue-bubbles {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.dialogue-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.dialogue-bubble:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.dialogue-bubble.narrator {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-color: #0ea5e9;
}

.dialogue-bubble.character {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: #f59e0b;
}

.bubble-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.speaker-name {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.segment-index {
  font-size: 11px;
  color: #666;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 10px;
}

.bubble-content {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
}

.show-more {
  margin-top: 16px;
}

/* 空状态 */
.empty-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
}

.empty-hint {
  margin-top: 12px;
  font-size: 14px;
  color: #666;
}

/* 进度抽屉样式 */
.progress-container {
  padding: 24px;
}

.overall-progress h3 {
  margin-bottom: 16px;
  font-size: 18px;
  color: #1f2937;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
}

.current-status {
  margin-bottom: 24px;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .left-panel {
    width: 300px;
  }
}

@media (max-width: 768px) {
  .synthesis-layout {
    flex-direction: column;
  }
  
  .left-panel {
    width: 100%;
    height: 300px;
  }
  
  .action-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}

/* 章节选择样式 */
.chapter-selection-card {
  margin-bottom: 16px;
}

.chapter-selection-content {
  .selection-mode {
    margin-bottom: 16px;
  }
  
  .chapter-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px;
    background: #fafafa;
    border-radius: 6px;
  }
  
  .selection-info {
    color: #666;
    font-size: 14px;
  }
  
  .chapters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 12px;
    max-height: 400px;
    overflow-y: auto;
  }
  
  .chapter-item {
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 12px;
    cursor: pointer;
    transition: all 0.3s;
    background: white;
    
    &:hover {
      border-color: #1890ff;
      box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
    }
    
    &.selected {
      border-color: #1890ff;
      background: #f6ffed;
    }
  }
  
  .chapter-content {
    .chapter-title {
      font-weight: 500;
      margin-bottom: 8px;
      color: #333;
      line-height: 1.4;
    }
    
    .chapter-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: #999;
      
      .chapter-status {
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        
        &.status-pending {
          background: #fff7e6;
          color: #fa8c16;
        }
        
        &.status-processing {
          background: #e6f7ff;
          color: #1890ff;
        }
        
        &.status-completed {
          background: #f6ffed;
          color: #52c41a;
        }
        
        &.status-failed {
          background: #fff2f0;
          color: #ff4d4f;
        }
        
        &.status-ready {
          background: #f0f5ff;
          color: #2f54eb;
        }
      }
    }
  }
  
  .loading-chapters {
    text-align: center;
    padding: 40px;
  }
  
  .no-chapters {
    text-align: center;
    padding: 40px;
    color: #999;
  }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-content h1 {
  margin: 0;
  color: #1f2937;
  font-size: 24px;
}

.header-content p {
  margin: 8px 0 0 0;
  color: #6b7280;
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.synthesis-content {
  margin-bottom: 24px;
}

.info-card, .analysis-card, .control-card, .progress-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.analysis-card {
  border: 2px solid #1890ff;
  background: #f8fffe;
}

.debug-controls {
  margin-bottom: 16px;
}

.synthesis-controls {
  padding: 8px 0;
}

.action-buttons {
  margin-top: 24px;
}

.synthesis-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-hint {
  margin-top: 16px;
}

.progress-content {
  padding: 8px 0;
}

.progress-overview {
  margin-bottom: 16px;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.download-section {
  margin-top: 16px;
}

.error-content {
  text-align: center;
  padding: 60px 0;
}

/* 合成完成区域样式 */
.completion-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.audio-preview {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-header h4 {
  margin: 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.audio-info {
  font-size: 12px;
  color: #6b7280;
  background: #e2e8f0;
  padding: 4px 8px;
  border-radius: 4px;
}

.audio-player-container {
  margin-top: 12px;
}

.audio-player-container audio {
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.download-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .synthesis-center-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .progress-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}

/* 智能准备结果样式 */
.preparation-results {
  margin-top: 16px;
}

.synthesis-segments-preview {
  margin-top: 16px;
}

.segments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.segments-header h4 {
  margin: 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.segments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chapter-segments {
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.chapter-header h5 {
  margin: 0;
  color: #1f2937;
  font-size: 14px;
  font-weight: 600;
}

.segments-container {
  margin-top: 8px;
}

.segment-item {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.segment-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.segment-number {
  font-size: 12px;
  color: #64748b;
}

.segment-speaker {
  font-size: 12px;
  color: #1f2937;
  font-weight: 600;
}

.show-more {
  margin-top: 8px;
}

/* JSON测试弹窗样式 */
.json-test-modal {
  max-height: 600px;
  overflow-y: auto;
}

.json-test-modal .ant-textarea {
  font-size: 12px;
  line-height: 1.4;
  border-radius: 6px;
  border: 2px dashed #d9d9d9;
  transition: border-color 0.3s ease;
}

.json-test-modal .ant-textarea:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.validation-result {
  margin-top: 12px;
}

/* 角色样式类 */
.character-primary .segment-speaker {
  color: #1890ff !important;
}

.character-warning .segment-speaker {
  color: #fa8c16 !important;
}

.character-success .segment-speaker {
  color: #52c41a !important;
}

.character-info .segment-speaker {
  color: #13c2c2 !important;
}

.character-error .segment-speaker {
  color: #f5222d !important;
}

/* 当前处理段落样式 */
.current-segment {
  margin: 16px 0;
  padding: 16px;
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
  border: 1px solid #91d5ff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
}

.current-segment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.current-segment-header h4 {
  margin: 0;
  color: #1890ff;
  font-size: 16px;
  font-weight: 600;
}

.current-segment-content {
  .segment-info {
    display: flex;
    gap: 12px;
    margin-bottom: 8px;
  }
  
  .segment-speaker {
    font-weight: 600;
    color: #1890ff;
    font-size: 14px;
  }
  
  .segment-position {
    color: #666;
    font-size: 12px;
  }
  
  .segment-text {
    color: #374151;
    line-height: 1.6;
    padding: 8px 12px;
    background: white;
    border-radius: 6px;
    border: 1px solid #e8f4f8;
  }
}

/* 已完成片段样式 */
.completed-segments {
  margin: 16px 0;
  padding: 16px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
}

.completed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.completed-header h4 {
  margin: 0;
  color: #52c41a;
  font-size: 16px;
  font-weight: 600;
}

.completed-list {
  .completed-item {
    margin-bottom: 8px;
    padding: 8px 12px;
    background: white;
    border: 1px solid #e8f5e8;
    border-radius: 6px;
    transition: all 0.2s ease;
    
    &:hover {
      border-color: #b7eb8f;
      box-shadow: 0 2px 4px rgba(82, 196, 26, 0.1);
    }
  }
  
  .segment-meta {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 4px;
    font-size: 12px;
  }
  
  .segment-number {
    background: #52c41a;
    color: white;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;
    min-width: 24px;
    text-align: center;
  }
  
  .segment-speaker {
    color: #1890ff;
    font-weight: 600;
  }
  
  .segment-duration {
    color: #666;
    margin-left: auto;
  }
  
  .segment-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }
  
  .segment-text {
    flex: 1;
    color: #374151;
    line-height: 1.4;
    font-size: 13px;
  }
  
  .segment-controls {
    flex-shrink: 0;
  }
  
  .show-all-completed {
    margin-top: 8px;
    text-align: center;
  }
}

/* 合成进度监控抽屉样式 */
.synthesis-progress-drawer {
  .progress-container {
    padding: 24px;
  }

  .overall-progress {
    margin-bottom: 24px;
  }

  .overall-progress h3 {
  margin-bottom: 16px;
    font-size: 18px;
    color: #1f2937;
  }

  .synthesis-controls-panel {
    margin: 20px 0;
    
    .ant-card {
      border: 1px solid #e8f4fd;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .ant-card-head {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 8px 8px 0 0;
      
      .ant-card-head-title {
        color: white;
        font-weight: 600;
      }
    }
    
    .ant-space {
      width: 100%;
      justify-content: center;
    }
    
    .control-hint {
      text-align: center;
      background: #f6f8fa;
      padding: 8px 12px;
      border-radius: 4px;
      border-left: 3px solid #1890ff;
    }
  }

  .progress-stats {
    display: flex;
    justify-content: space-between;
    margin-top: 16px;
  }

  .stat-item {
    text-align: center;
  }

  .stat-value {
    display: block;
    font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  }

  .stat-label {
    display: block;
    font-size: 12px;
    color: #6b7280;
    margin-top: 4px;
  }

  .current-status {
    margin-bottom: 24px;
  }

  .current-status .ant-alert {
    padding: 8px 16px;
  }

  .current-alert {
    margin-bottom: 16px;
  }

  .segments-list {
    margin-bottom: 24px;
  }

  .segments-list h4 {
    margin-bottom: 16px;
    font-size: 16px;
    color: #1f2937;
  }

  .segments-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .segment-item {
    width: 100%;
    padding: 16px;
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    transition: all 0.3s;

    &:hover {
      border-color: #1890ff;
      box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
    }

    .segment-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .segment-id {
      font-size: 12px;
      color: #64748b;
    }

    .segment-speaker {
      font-size: 12px;
      color: #1f2937;
      font-weight: 600;
    }

    .status-tag {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
    }

    .segment-content {
      .segment-text {
        color: #374151;
        line-height: 1.6;
        padding: 8px 12px;
        background: white;
        border-radius: 6px;
        border: 1px solid #e8f4f8;
      }

      .segment-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;

        .ant-button {
          padding: 4px 12px;
          font-size: 12px;
          border-radius: 4px;
        }

        .success-info, .error-info, .processing-info {
          font-size: 12px;
          color: #6b7280;
        }
      }
    }
  }

  .completion-actions {
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #e5e7eb;

    .ant-result {
      padding: 16px;
    }

    .ant-result-title {
      font-size: 18px;
      color: #52c41a;
    }

    .ant-result-subtitle {
      font-size: 14px;
      color: #6b7280;
    }

    .ant-result-extra {
      margin-top: 16px;
    }
  }

  .failure-actions {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #e5e7eb;

    .ant-alert {
      padding: 12px;
    }

    .ant-alert-message {
      font-size: 14px;
      color: #ff4d4f;
    }

    .ant-alert-description {
      font-size: 12px;
      color: #6b7280;
    }

    .failure-buttons {
      display: flex;
      justify-content: space-between;
      margin-top: 16px;

      .ant-button {
        padding: 8px 24px;
        font-size: 14px;
      }
    }
  }
}
</style>