<template>
  <div class="dialogue-audio-generation">
    <!-- 项目头部 -->
    <ProjectHeader 
      :project="project"
      :loading="loading"
      @back="handleBack"
      title="对话音生成"
    />

    <!-- 迷你进度条 (在抽屉关闭时显示) -->
    <div 
      v-if="synthesisRunning && !progressDrawerVisible" 
      class="mini-progress-bar"
      @click="progressDrawerVisible = true"
    >
      <div class="mini-progress-content">
        <span class="mini-progress-text">
          当前章节: {{ currentChapterProgress.completed }}/{{ currentChapterProgress.total }}
        </span>
        <a-progress 
          :percent="currentChapterProgress.percent" 
          :show-info="false"
          size="small"
          :stroke-color="progressData.status === 'failed' ? '#ff4d4f' : '#1890ff'"
        />
        <span class="mini-progress-tip">点击查看详情</span>
      </div>
    </div>

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
        :can-start="canStartSynthesis && !synthesisStarting"
        :synthesis-running="synthesisRunning"
        :selected-chapter-status="getSelectedChapterStatus()"
        @play-segment="handlePlaySegment"
        @refresh-preparation="handleRefreshPreparation"
        @trigger-preparation="handleTriggerPreparation"
        @trigger-preparation-loading="handleTriggerPreparationLoading"
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
        @reset-project-status="handleResetProjectStatus"
        @open-audio-editor="handleOpenAudioEditor"
      />

      <!-- 环境混音查询区域 (旧版，保持兼容) -->
      <div v-if="showEnvironmentMixing" class="environment-mixing-section" style="display: none;">
        <a-card title="🌍 环境音混合列表" :bordered="false">
          <template #extra>
            <a-space>
              <a-button 
                type="primary" 
                @click="showEnvironmentConfigDrawer = true"
                :loading="environmentLoading"
              >
                <SoundOutlined />
                配置环境音混合
              </a-button>
            </a-space>
          </template>
          
          <!-- 环境混音结果列表 -->
          <div class="environment-results-list">
            <a-empty v-if="environmentMixingResults.length === 0" description="暂无环境混音结果">
              <template #image>
                <SoundOutlined style="color: #bfbfbf; font-size: 48px;" />
              </template>
            </a-empty>
            
            <div v-else class="mixing-results-grid">
              <a-card 
                v-for="result in environmentMixingResults" 
                :key="result.id"
                class="mixing-result-card"
                size="small"
              >
                <template #title>
                  <div class="result-title">
                    <SoundOutlined />
                    {{ result.name || `环境混音 ${result.id}` }}
                  </div>
                </template>
                
                <template #extra>
                  <a-space>
                    <a-button type="text" size="small" @click="previewEnvironmentMixing(result)">
                      播放
                    </a-button>
                    <a-button type="text" size="small" @click="downloadEnvironmentMixing(result)">
                      下载
                    </a-button>
                  </a-space>
                </template>
                
                <div class="result-info">
                  <p><strong>章节：</strong>{{ getChapterName(result.chapter_id) }}</p>
                  <p><strong>状态：</strong>
                    <a-tag :color="result.status === 'completed' ? 'green' : 'orange'">
                      {{ result.status === 'completed' ? '已完成' : '处理中' }}
                    </a-tag>
                  </p>
                  <p><strong>创建时间：</strong>{{ formatDate(result.created_at) }}</p>
                  <p><strong>环境音轨数：</strong>{{ result.environment_tracks_count || 0 }}</p>
                </div>
              </a-card>
            </div>
          </div>
        </a-card>
      </div>


    </div>

    <!-- 进度监控抽屉 -->
    <ProgressDrawer
      :visible="progressDrawerVisible"
      :progress-data="progressData"
      :project-status="project?.status || 'pending'"
      :ws-connected="websocketStatus === 'connected'"
      :selected-chapter="selectedChapter"
      :chapters="chapters"
      @close="handleProgressDrawerClose"
      @update:visible="progressDrawerVisible = $event"
      @showFailureDetails="handleShowFailureDetails"
      @pauseSynthesis="handlePauseSynthesis"
      @cancelSynthesis="handleCancelSynthesis"
    />

    <!-- 环境音配置抽屉 -->
    <EnvironmentGenerationDrawer
      :visible="showEnvironmentConfigDrawer"
      :project-id="project?.id"
      :synthesis-data="preparationResults"
      @update:visible="showEnvironmentConfigDrawer = $event"
      @complete="handleEnvironmentGenerationComplete"
      @start-audio-mixing="handleStartEnvironmentMixing"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { SoundOutlined } from '@ant-design/icons-vue'
import api from '@/api'
import apiClient from '@/api/config.js'
import { playSegmentAudio, playChapterAudio } from '@/utils/audioService'
import ProjectHeader from '@/components/synthesis-center/ProjectHeader.vue'
import ChapterSelector from '@/components/synthesis-center/ChapterSelector.vue'
import ContentPreview from '@/components/synthesis-center/ContentPreview.vue'
import ProgressDrawer from '@/components/synthesis-center/ProgressDrawer.vue'

// 恢复环境音相关组件导入
import EnvironmentGenerationDrawer from '@/components/synthesis-center/EnvironmentGenerationDrawer.vue'
// import EnvironmentConfigManager from '@/components/synthesis-center/EnvironmentConfigManager.vue'
// 暂时注释掉失败详情模态框的导入
// import FailureDetailsModal from '@/components/synthesis-center/FailureDetailsModal.vue'

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

// 合成类型状态管理
const synthesisType = ref(null) // 'voice' | null
const synthesisStatus = ref('idle') // 'running' | 'completed' | 'failed' | 'idle'

// 失败详情相关状态
const failureDetailsVisible = ref(false)
const failedSegmentsList = ref([])
const retryLoading = ref(false)

// 环境混音相关状态
const showEnvironmentMixing = ref(false)
const showEnvironmentConfigDrawer = ref(false)
const environmentLoading = ref(false)
const environmentMixingResults = ref([])



// WebSocket 连接
let websocket = null
let progressRefreshInterval = null

// 🔧 新增：当前章节进度数据
const currentChapterProgress = ref({ completed: 0, total: 0, percent: 0 })

// 🔧 加载当前章节进度
const loadCurrentChapterProgress = async () => {
  if (!selectedChapter.value || !project.value?.id) {
    currentChapterProgress.value = { completed: 0, total: 0, percent: 0 }
    return
  }
  
  try {
    const response = await api.getChapterProgress(project.value.id, selectedChapter.value)
    if (response.data.success && response.data.data) {
      const data = response.data.data
      currentChapterProgress.value = {
        completed: data.completed_segments || 0,
        total: data.total_segments || 0,
        percent: data.progress_percentage || 0
      }
      console.log('📊 章节进度更新:', currentChapterProgress.value)
    }
  } catch (error) {
    console.error('获取章节进度失败:', error)
    // 回退到智能准备结果计算
    if (preparationResults.value?.data) {
      const chapterResult = preparationResults.value.data.find(
        result => result.chapter_id === selectedChapter.value
      )
      if (chapterResult?.synthesis_json?.synthesis_plan) {
        const totalSegments = chapterResult.synthesis_json.synthesis_plan.length
        currentChapterProgress.value = {
          completed: 0,
          total: totalSegments,
          percent: 0
        }
      }
    }
  }
}

// 计算属性
const canStartSynthesis = computed(() => {
  if (!selectedChapter.value || !project.value) {
    return false
  }
  
  // 检查本地合成状态
  if (synthesisRunning.value || synthesisStarting.value) {
    return false
  }
  
  // 检查项目的真实状态 - 防止重复合成
  const projectStatus = project.value.status
  if (projectStatus === 'processing' || projectStatus === 'paused') {
    console.log('⚠️ 项目正在处理中，禁用合成按钮', { projectStatus, synthesisRunning: synthesisRunning.value })
    return false
  }
  
  // 检查进度状态
  const progressStatus = progressData.value?.status
  if (progressStatus === 'processing' || progressStatus === 'running') {
    console.log('⚠️ 进度显示正在运行，禁用合成按钮', { progressStatus, synthesisRunning: synthesisRunning.value })
    return false
  }
  
  return true
})

// 初始化
onMounted(async () => {
  await loadProject()
  await loadChapters()
  
  // 如果有选中的章节，立即加载智能准备结果
  if (selectedChapter.value) {
    await loadPreparationResults()
    // 🔧 加载当前章节进度
    await loadCurrentChapterProgress()
  }
  
  // 🔧 如果项目正在合成，自动显示进度抽屉
  if (project.value?.status === 'processing') {
    progressDrawerVisible.value = true
    console.log('📊 页面初始化时发现项目正在合成，自动显示进度抽屉')
  }
  
  // 🎯 处理重新合成参数
  const restartType = route.query.restart
  if (restartType && selectedChapter.value) {
    console.log('🔄 检测到重新合成参数:', restartType)
    
    // 延迟执行，确保页面完全加载
    setTimeout(() => {
      if (restartType === 'voice') {
        console.log('🎤 自动触发TTS语音合成')
        handleStartSynthesis()
      } else if (restartType === 'environment') {
        console.log('🌍 自动显示环境音混合页面')
        showEnvironmentMixing.value = true
        loadEnvironmentMixingResults()
      }
      
      // 清除查询参数，避免重复触发
      router.replace({ path: route.path })
    }, 1000)
  }
  
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
      
      // 🔧 修复：正确解析API返回的数据格式
      const segments = progressInfo.segments || {}
      progressData.value = {
        progress: progressInfo.progress_percentage || 0,
        status: progressInfo.status || project.value?.status || 'pending',
        completed_segments: segments.completed || 0,
        total_segments: segments.total || 0,
        failed_segments: segments.failed || 0,
        current_processing: '正在生成语音...',
        synthesis_type: progressData.value?.synthesis_type // 保持合成类型标识
      }
      
      // 🔧 根据项目状态同步前端合成状态
      const projectStatus = project.value?.status
      if (projectStatus === 'processing') {
        synthesisRunning.value = true
        // 🔧 自动显示进度抽屉
        if (!progressDrawerVisible.value) {
          progressDrawerVisible.value = true
          console.log('📊 项目正在合成中，自动显示进度抽屉')
        }
      } else if (projectStatus === 'paused' || projectStatus === 'cancelled' || projectStatus === 'completed' || projectStatus === 'failed') {
        synthesisRunning.value = false
        console.log('📊 项目非运行状态，重置前端状态', projectStatus)
      }
      
      console.log('📊 加载进度信息 (API格式):', progressData.value)
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
          current_processing: '正在生成语音...',
          synthesis_type: progressData.value?.synthesis_type // 保持合成类型标识
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
          current_processing: '正在生成语音...',
          synthesis_type: progressData.value?.synthesis_type // 保持合成类型标识
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
        current_processing: '正在生成语音...',
        synthesis_type: progressData.value?.synthesis_type // 保持合成类型标识
      }
    } else {
      // 设置安全的默认值
      progressData.value = {
        progress: 0,
        status: project.value?.status || 'pending',
        completed_segments: 0,
        total_segments: 0,
        failed_segments: 0,
        current_processing: '正在生成语音...',
        synthesis_type: progressData.value?.synthesis_type // 保持合成类型标识
      }
    }
    console.log('📊 异常情况设置进度数据:', progressData.value)
  }
}

// 加载章节列表
const loadChapters = async (allowChapterReset = true) => {
  try {
    chaptersLoading.value = true
    console.log('Loading chapters, project:', project.value, 'allowChapterReset:', allowChapterReset)
    
    if (project.value?.book_id) {
      // 直接使用apiClient调用正确的API路径
      const response = await apiClient.get(`/books/${project.value.book_id}/chapters`)
      console.log('Chapters API response:', response.data)
      
      if (response.data.success && response.data.data) {
        chapters.value = response.data.data
        console.log('Found chapters:', chapters.value)
        
        if (chapters.value.length > 0) {
          // 🔧 根据allowChapterReset参数决定是否允许重置章节选择
          if (!selectedChapter.value && allowChapterReset) {
            selectedChapter.value = chapters.value[0].id
            console.log('✅ 设置默认选中章节:', selectedChapter.value)
          } else if (selectedChapter.value && allowChapterReset) {
            // 验证当前选中的章节是否还存在
            const currentChapterExists = chapters.value.some(ch => ch.id === selectedChapter.value)
            if (!currentChapterExists) {
              selectedChapter.value = chapters.value[0].id
              console.log('✅ 当前选中章节不存在，重置为默认章节:', selectedChapter.value)
            } else {
              console.log('✅ 保持当前选中章节:', selectedChapter.value)
            }
          } else if (!allowChapterReset) {
            console.log('🔒 跳过章节重置，保持当前选择:', selectedChapter.value)
          }
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

// 🔧 监控章节选择变化
watch(selectedChapter, (newChapter, oldChapter) => {
  if (newChapter !== oldChapter) {
    console.log('🔄 章节选择发生变化:', {
      从: oldChapter,
      到: newChapter,
      调用栈: new Error().stack
    })
  }
}, { immediate: false })

// 选择章节
const handleChapterSelect = async (chapterId) => {
  console.log('👆 用户手动选择章节:', chapterId)
  selectedChapter.value = chapterId
  
  // 自动加载智能准备结果
  if (selectedChapter.value) {
    await loadPreparationResults()
    // 🔧 加载当前章节进度
    await loadCurrentChapterProgress()
  } else {
    // 清空准备结果
    preparationResults.value = null
    currentChapterProgress.value = { completed: 0, total: 0, percent: 0 }
  }
}

// 加载智能准备结果
const loadPreparationResults = async () => {
  if (!project.value?.book_id) {
    console.warn('项目未关联书籍，无法加载智能准备结果')
    preparationResults.value = null
    return
  }
  
  if (!selectedChapter.value) {
    console.warn('请先选择要合成的章节')
    preparationResults.value = null
    return
  }
  
  contentLoading.value = true
  console.log(`🔍 开始加载章节 ${selectedChapter.value} 的智能准备结果...`)
  
  try {
    // 只获取选中章节的智能准备结果
    const response = await apiClient.get(`/books/${project.value.book_id}/analysis-results?chapter_ids=${selectedChapter.value}`)
    console.log('📊 API响应:', response.data)
    
    if (response.data.success) {
      // 检查是否有实际的准备结果数据
      if (response.data.data && Array.isArray(response.data.data) && response.data.data.length > 0) {
        // 进一步检查数据是否包含有效的合成计划
        const hasValidData = response.data.data.some(chapter => 
          chapter.synthesis_json && 
          chapter.synthesis_json.synthesis_plan && 
          chapter.synthesis_json.synthesis_plan.length > 0
        )
        
        if (hasValidData) {
          preparationResults.value = response.data
          console.log('✅ 智能准备结果加载成功，包含有效数据:', preparationResults.value)
        } else {
          preparationResults.value = null
          console.log('⚠️ 智能准备结果数据为空或无效，将显示准备按钮')
        }
      } else {
        preparationResults.value = null
        console.log('📋 该章节暂无智能准备结果，将显示准备按钮')
      }
    } else {
      console.error('加载智能准备结果失败:', response.data.message)
      preparationResults.value = null
    }
  } catch (error) {
    console.error('加载智能准备结果失败:', error)
    preparationResults.value = null
  } finally {
    contentLoading.value = false
    console.log(`🔍 章节 ${selectedChapter.value} 的准备结果加载完成，preparationResults:`, preparationResults.value)
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
          
          // 🔧 同时更新章节进度
          loadCurrentChapterProgress()
          
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
    // 🔧 防重复合成检查
    if (!canStartSynthesis.value) {
      message.warning('当前无法开始合成，请检查项目状态')
      return
    }
    
    // 🔧 重新获取最新项目状态进行二次确认
    await loadProject()
    if (project.value.status === 'processing' || project.value.status === 'paused') {
      message.warning(`项目正在${project.value.status === 'processing' ? '合成中' : '暂停状态'}，无法重复合成`)
      return
    }
    
    synthesisStarting.value = true
    
    // 🎯 设置合成类型
    synthesisType.value = 'voice'
    synthesisStatus.value = 'running'
    
    const response = await api.startGeneration(project.value.id, {
      chapter_ids: selectedChapter.value ? [selectedChapter.value] : undefined
    })
    
    if (response.data.success) {
      message.success('🎤 开始角色音合成')
      synthesisRunning.value = true
      progressDrawerVisible.value = true
      
      // 🔧 初始化进度数据
      progressData.value = {
        progress: 0,
        status: 'processing',
        completed_segments: 0,
        total_segments: 0,
        failed_segments: 0,
        current_processing: '🎤 正在进行角色音合成...',
        synthesis_type: 'voice' // 标记合成类型
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
          // 🔧 同时更新章节进度
          loadCurrentChapterProgress()
        }
      }, 3000) // 每3秒刷新一次
    }
  } catch (error) {
    console.error('Failed to start synthesis:', error)
    message.error('启动合成失败')
    synthesisType.value = null
    synthesisStatus.value = 'failed'
  } finally {
    synthesisStarting.value = false
  }
}

const handlePauseSynthesis = async () => {
  try {
    console.log('📌 开始暂停合成，项目ID:', project.value.id)
    await api.pauseGeneration(project.value.id)
    message.success('已暂停合成')
    synthesisRunning.value = false
    
    // 🔧 停止定期刷新
    if (progressRefreshInterval) {
      clearInterval(progressRefreshInterval)
      progressRefreshInterval = null
    }
    
    // 重新加载项目状态
    await loadProject()
  } catch (error) {
    console.error('Failed to pause synthesis:', error)
    message.error('暂停合成失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleCancelSynthesis = async () => {
  try {
    console.log('📌 开始取消合成，项目ID:', project.value.id)
    await api.cancelGeneration(project.value.id)
    message.success('已取消合成')
    synthesisRunning.value = false
    progressDrawerVisible.value = false
    
    // 🔧 停止定期刷新
    if (progressRefreshInterval) {
      clearInterval(progressRefreshInterval)
      progressRefreshInterval = null
    }
    
    // 重新加载项目状态
    await loadProject()
  } catch (error) {
    console.error('Failed to cancel synthesis:', error)
    message.error('取消合成失败: ' + (error.response?.data?.detail || error.message))
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

// 重置项目状态 - 解决项目状态卡死问题
const handleResetProjectStatus = async () => {
  try {
    console.log('🔧 重置项目状态，项目ID:', project.value.id)
    const response = await api.resetProjectStatus(project.value.id)
    
    if (response.data.success) {
      message.success('✅ 项目状态已重置')
      
      // 重新加载项目信息
      await loadProject()
      
      // 重置本地状态
      synthesisRunning.value = false
      progressDrawerVisible.value = false
      
      // 停止定期刷新
      if (progressRefreshInterval) {
        clearInterval(progressRefreshInterval)
        progressRefreshInterval = null
      }
    }
  } catch (error) {
    console.error('Failed to reset project status:', error)
    message.error('重置项目状态失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handlePlayAudio = async () => {
  try {
    playingChapterAudio.value = selectedChapter.value
    
    // 🎯 构建章节完整标题
    const currentChapter = chapters.value.find(ch => ch.id === selectedChapter.value)
    const chapterTitle = currentChapter ? 
      `第${currentChapter.chapter_number || currentChapter.id}章：${currentChapter.title || currentChapter.chapter_title || '未命名章节'}` : 
      `章节${selectedChapter.value}`
    
    console.log(`🎵 播放章节：`, {
      项目ID: project.value.id,
      章节ID: selectedChapter.value,
      章节标题: chapterTitle
    })
    
    await playChapterAudio(project.value.id, selectedChapter.value, chapterTitle)
    message.success(`🎵 播放：${chapterTitle}`)
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

// 打开音视频编辑器
const handleOpenAudioEditor = async () => {
  try {
    const projectId = route.params.projectId
    
    if (!projectId) {
      message.error('无效的项目ID')
      return
    }
    
    if (!project.value || project.value.status !== 'completed') {
      message.warning('请先完成语音合成后再进入编辑器')
      return
    }
    
    // 检查是否已有编辑器项目
    console.log('正在导入合成结果到音视频编辑器...')
    
    // 调用API导入合成结果到编辑器
    const response = await api.audioEditor.importFromSynthesis({
      synthesis_project_id: projectId,
      project_name: `${project.value.title} - 编辑项目`,
      description: `从合成项目"${project.value.title}"导入的音频编辑项目`
    })
    
    if (response.success) {
      message.success('导入成功，正在跳转到音视频编辑器...')
      // 跳转到音视频编辑器
      router.push(`/editor/project/${response.data.project_id}`)
    } else {
      message.error(response.message || '导入失败')
    }
  } catch (error) {
    console.error('打开音视频编辑器失败:', error)
    message.error('打开音视频编辑器失败')
  }
}

const handlePlaySegment = async (segment) => {
  try {
    // 🔧 修复：优先使用segment_id，其次是id，最后才是index
    const segmentId = segment.segment_id || segment.id || segment.index || segment.ui_index
    
    console.log('🎵 handlePlaySegment调用 - 完整调试信息:', {
      '当前选中章节': selectedChapter.value,
      '段落对象': segment,
      'segment_id字段': segment.segment_id,
      'id字段': segment.id,
      'index字段': segment.index,
      'ui_index字段': segment.ui_index,
      '最终使用的段落ID': segmentId,
      '项目ID': project.value.id,
      '文本预览': segment.text?.substring(0, 50),
      '即将调用API': `/api/v1/novel-reader/projects/${project.value.id}/segments/${segmentId}/download`
    })
    
    // 🚨 重要检查：如果segment_id异常大，发出警告
    if (segmentId > 50) {
      console.warn('🚨 异常检测：段落ID过大！', {
        异常段落ID: segmentId,
        当前选中章节: selectedChapter.value,
        可能原因: '这个segment_id可能是全局累计的，而不是当前章节的段落序号',
        建议: '需要修复segment_id生成逻辑或查找逻辑'
      })
      
      // 显示用户警告但不阻止播放
      message.warning(`⚠️ 段落ID为${segmentId}，可能播放错误的音频`)
    }
    
    if (!segmentId) {
      console.error('❌ 无法获取段落ID:', segment)
      message.error('无法获取段落ID')
      return
    }
    
    // 🎯 构建丰富的段落信息
    const currentChapter = chapters.value.find(ch => ch.id === selectedChapter.value)
    const chapterInfo = currentChapter ? 
      `第${currentChapter.chapter_number || currentChapter.id}章：${currentChapter.title || currentChapter.chapter_title || '未命名章节'}` : 
      `章节${selectedChapter.value}`
    
    const segmentText = segment.text || segment.content || ''
    const segmentPreview = segmentText.length > 30 ? 
      segmentText.substring(0, 30) + '...' : 
      segmentText
    
    const fullTitle = `${chapterInfo} - 段落${segmentId}: ${segmentPreview}`
    
    console.log(`🎵 即将播放：`, {
      项目ID: project.value.id,
      段落ID: segmentId,
      章节信息: chapterInfo,
      段落文本: segmentPreview,
      完整标题: fullTitle,
      '🔍 章节对象详情': currentChapter,
      '当前章节title字段': currentChapter?.title,
      '当前章节chapter_title字段': currentChapter?.chapter_title,
      '所有章节数据': chapters.value
    })
    
    // 🎯 传递丰富的标题信息给音频服务
    await playSegmentAudio(project.value.id, segmentId, fullTitle)
    message.success(`🎵 播放：${fullTitle}`)
  } catch (error) {
    console.error('❌ 播放段落失败 - 完整错误信息:', {
      段落对象: segment,
      使用的segmentId: segment.segment_id || segment.id || segment.index,
      项目ID: project.value.id,
      错误信息: error.message,
      API响应: error.response?.data,
      完整错误: error
    })
    message.error('播放片段失败: ' + (error.response?.data?.detail || error.message))
  }
}

const handleProgressDrawerClose = () => {
  progressDrawerVisible.value = false
  
  // 🔧 如果合成正在进行，提示用户可以通过底部进度条重新打开
  if (synthesisRunning.value) {
    message.info('合成进度已最小化到底部，点击底部进度条可重新打开', 3)
  }
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
  // 🔧 只刷新项目状态，不重新加载章节（避免章节选择重置）
  loadProject()
  // 🔧 如果有选中章节，只刷新准备结果
  if (selectedChapter.value) {
    loadPreparationResults()
  }
}

const handleTriggerPreparation = () => {
  // 这个事件已经由ContentPreview组件自己处理了
  // 父组件不需要额外处理
  console.log('📋 智能准备事件由ContentPreview组件处理')
}

const handleTriggerPreparationLoading = (loading) => {
  // 可以在这里添加全局loading状态管理
  console.log('📋 智能准备Loading状态:', loading)
  contentLoading.value = loading
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
    // 🔧 防重复合成检查
    if (!canStartSynthesis.value) {
      message.warning('当前无法重新合成，请检查项目状态')
      return
    }
    
    // 🔧 重新获取最新项目状态进行二次确认
    await loadProject()
    if (project.value.status === 'processing' || project.value.status === 'paused') {
      message.warning(`项目正在${project.value.status === 'processing' ? '合成中' : '暂停状态'}，无法重新合成`)
      return
    }
    
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
  
  // 🎯 智能状态判断逻辑重构
  const projectStatus = project.value?.status
  const chapterAnalysisStatus = chapter.analysis_status
  const chapterSynthesisStatus = chapter.synthesis_status
  
  console.log('🔍 章节状态判断调试:', {
    章节ID: selectedChapter.value,
    项目状态: projectStatus,
    章节分析状态: chapterAnalysisStatus,
    章节合成状态: chapterSynthesisStatus,
    章节标题: chapter.chapter_title
  })
  
  // 1. 如果项目正在处理中，章节也是处理中
  if (projectStatus === 'processing') {
    return 'processing'
  }
  
  // 2. 如果项目已完成，需要检查该章节是否有音频文件
  if (projectStatus === 'completed') {
    // 项目完成意味着有音频输出，章节应该显示为completed
    console.log('✅ 项目已完成，章节显示为completed状态')
    return 'completed'
  }
  
  // 3. 如果项目部分完成，需要检查具体的章节状态
  if (projectStatus === 'partial_completed') {
    // 这里需要检查该章节是否在已完成的范围内
    // 暂时返回completed，实际应该查询该章节的音频文件
    return 'completed'
  }
  
  // 4. 如果项目失败或暂停
  if (projectStatus === 'failed') {
    return 'failed'
  }
  
  if (projectStatus === 'paused') {
    return 'processing'  // 暂停也算处理中
  }
  
  // 5. 项目待开始或准备状态，检查章节的准备情况
  if (projectStatus === 'pending' || projectStatus === 'ready') {
    // 如果章节已完成智能准备，显示待合成状态（pending）
    if (chapterAnalysisStatus === 'completed' && chapterSynthesisStatus === 'ready') {
      console.log('📋 章节智能准备完成，显示待合成状态')
      return 'pending'
    }
    
    // 如果章节正在分析
    if (chapterAnalysisStatus === 'analyzing') {
      return 'processing'
    }
    
    // 如果章节分析失败
    if (chapterAnalysisStatus === 'failed') {
      return 'failed'
    }
    
    // 默认待开始
    return 'pending'
  }
  
  // 6. 兜底逻辑：根据章节自身状态
  const status = chapterAnalysisStatus || chapterSynthesisStatus || 'pending'
  const statusMap = {
    'pending': 'pending',
    'analyzing': 'processing',
    'processing': 'processing',
    'completed': 'completed',
    'failed': 'failed',
    'ready': 'pending',
    'not_started': 'pending'
  }
  
  const finalStatus = statusMap[status] || 'pending'
  console.log('🎯 最终章节状态:', finalStatus)
  return finalStatus
}

// 环境混音相关方法
const loadEnvironmentMixingResults = async () => {
  try {
    environmentLoading.value = true
    const projectId = route.params.projectId
    
    // 调用环境混音结果查询API
    const response = await api.getEnvironmentMixingResults(projectId)
    if (response.data.success) {
      environmentMixingResults.value = response.data.data || []
    }
  } catch (error) {
    console.error('加载环境混音结果失败:', error)
    message.error('加载环境混音结果失败')
  } finally {
    environmentLoading.value = false
  }
}

const previewEnvironmentMixing = async (result) => {
  try {
    // 播放环境混音结果
    const { getAudioService } = await import('@/utils/audioService')
    await getAudioService().playEnvironmentMixing(result)
    message.success('开始播放环境混音')
  } catch (error) {
    console.error('播放环境混音失败:', error)
    message.error('播放失败')
  }
}

const downloadEnvironmentMixing = async (result) => {
  try {
    // 下载环境混音结果
    const response = await api.downloadEnvironmentMixing(result.id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `环境混音_${result.name || result.id}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success('下载完成')
  } catch (error) {
    console.error('下载环境混音失败:', error)
    message.error('下载失败')
  }
}

const getChapterName = (chapterId) => {
  const chapter = chapters.value.find(ch => ch.id === chapterId)
  return chapter ? chapter.title : `章节 ${chapterId}`
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}

// 环境音配置抽屉处理方法
const handleEnvironmentGenerationComplete = () => {
  message.success('环境音配置完成！')
  showEnvironmentConfigDrawer.value = false
  // 刷新环境混音结果列表
  loadEnvironmentMixingResults()
}

const handleStartEnvironmentMixing = async (environmentConfig) => {
  try {
    const projectId = route.params.projectId
    
    message.info('开始环境音混合合成...')
    showEnvironmentConfigDrawer.value = false
    
    // 调用环境音混合API
    const response = await api.startEnvironmentMixing(projectId, {
      environment_config: environmentConfig,
      selected_chapter: selectedChapter.value
    })
    
    if (response.data.success) {
      message.success('环境音混合合成已开始！')
      // 刷新环境混音结果列表
      loadEnvironmentMixingResults()
    } else {
      message.error(response.data.message || '启动环境音混合失败')
    }
  } catch (error) {
    console.error('启动环境音混合失败:', error)
    message.error('启动环境音混合失败: ' + (error.response?.data?.detail || error.message))
  }
}




</script>

<style scoped>
.dialogue-audio-generation {
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

/* 章节选择器 - 固定较小宽度，可滚动 */
.main-content > :first-child {
  flex: 0 0 280px;
  min-width: 280px;
  max-width: 280px;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 内容预览区域 - 占用剩余空间，可滚动 */
.main-content > :last-child {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

/* 迷你进度条样式 */
.mini-progress-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #ffffff;
  border-top: 1px solid #e8e8e8;
  box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  cursor: pointer;
  transition: all 0.3s ease;
}

.mini-progress-bar:hover {
  background: #f5f5f5;
  box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.15);
}

.mini-progress-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 8px 16px;
  max-width: 600px;
  margin: 0 auto;
}

.mini-progress-text {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  white-space: nowrap;
}

.mini-progress-bar .ant-progress {
  flex: 1;
  margin: 0;
}

.mini-progress-tip {
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}



/* 主题颜色适配 - 使用CSS变量 */
.mini-progress-content .ant-progress {
  flex: 1;
  margin: 0;
}

.mini-progress-content .ant-progress .ant-progress-bg {
  background-color: var(--primary-color) !important;
}

/* 迷你进度条主题颜色悬停效果 */
.mini-progress-bar:hover .ant-progress .ant-progress-bg {
  background-color: var(--secondary-color) !important;
}

/* 暗黑模式适配 */
[data-theme="dark"] .dialogue-audio-generation {
  background: #141414 !important;
}

[data-theme="dark"] .main-content {
  background: #141414 !important;
}

[data-theme="dark"] .mini-progress-bar {
  background: #1f1f1f !important;
  border-top-color: #434343 !important;
  box-shadow: 0 -2px 8px rgba(0,0,0,0.3) !important;
}

[data-theme="dark"] .mini-progress-bar:hover {
  background: #2d2d2d !important;
  box-shadow: 0 -4px 12px rgba(0,0,0,0.5) !important;
}

[data-theme="dark"] .mini-progress-text {
  color: #fff !important;
}

[data-theme="dark"] .mini-progress-tip {
  color: #8c8c8c !important;
}

/* 迷你进度条在暗黑模式下的主题颜色适配 */
[data-theme="dark"] .mini-progress-content .ant-progress .ant-progress-bg {
  background-color: var(--primary-color) !important;
}

[data-theme="dark"] .mini-progress-bar:hover .ant-progress .ant-progress-bg {
  background-color: var(--secondary-color) !important;
}

/* 暗黑模式下的标签页样式 */
[data-theme="dark"] .function-tabs .ant-tabs-tab.ant-tabs-tab-active {
  background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
}

[data-theme="dark"] .function-tabs .ant-tabs-tab:hover {
  background: rgba(24, 144, 255, 0.1);
}

[data-theme="dark"] .voice-synthesis-content,
[data-theme="dark"] .music-generation-content,
[data-theme="dark"] .environment-audio-content {
  background: #141414;
}

/* 环境混音相关样式 */
.environment-mixing-section {
  flex: 1;
  min-width: 0;
  overflow-y: auto;
  overflow-x: hidden;
}

.environment-results-list {
  margin-top: 16px;
}

.mixing-results-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
  gap: 16px;
}

.mixing-result-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.mixing-result-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.result-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.result-info p {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.4;
}

.result-info strong {
  color: #1f2937;
  font-weight: 500;
}

/* 暗黑模式适配 */
[data-theme="dark"] .mixing-result-card:hover {
  box-shadow: 0 4px 12px rgba(255, 255, 255, 0.1);
}

[data-theme="dark"] .result-info strong {
  color: #f9fafb;
}

/* 移动端响应式设计 */
@media (max-width: 768px) {
  .dialogue-audio-generation {
    height: 100vh;
    overflow: hidden;
  }
  
  .main-content {
    flex-direction: column;
    gap: 0;
  }
  
  /* 移动端章节选择器 - 改为横向滚动 */
  .main-content > :first-child {
    flex: 0 0 auto;
    min-width: 100%;
    max-width: 100%;
    max-height: 120px;
    overflow-x: auto;
    overflow-y: hidden;
  }
  
  /* 移动端内容预览区域 - 占用剩余空间 */
  .main-content > :last-child {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    overflow-x: hidden;
  }
  
  /* 移动端环境混音卡片网格适配 */
  .mixing-results-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
  
  /* 移动端迷你进度条适配 */
  .mini-progress-content {
    flex-direction: column;
    gap: 8px;
    padding: 12px 16px;
  }
  
  .mini-progress-text {
    font-size: 12px;
  }
  
  .mini-progress-tip {
    font-size: 11px;
  }
}
</style> 