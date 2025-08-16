<template>
  <div class="dialogue-audio-generation">
    <!-- 项目头部 -->
    <ProjectHeader :project="project" :loading="loading" @back="handleBack" title="对话音生成" />

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
        :synthesis-running="synthesisRunning"
        :selected-chapter-status="getSelectedChapterStatus()"
        :progress-data="progressData"
        :chapter-progress="currentChapterProgress"
        :can-start="canStartNewSynthesis"
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
        @resume-synthesis="handleResumeSynthesis"
        @reset-project-status="handleResetProjectStatus"
      />

      <!-- 环境混音功能已迁移至单独的环境混合页面 -->
    </div>

    <!-- 进度监控抽屉 -->
    <ProgressDrawer
      :visible="progressDrawerVisible"
      :progress-data="progressData"
      :chapter-progress="currentChapterProgress"
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

    <!-- 环境音配置抽屉已迁移至单独的环境混合页面 -->
  </div>
</template>

<script setup>
  import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { message } from 'ant-design-vue'
  import { getWebSocketUrl } from '@/config/services'
  import { SoundOutlined } from '@ant-design/icons-vue'
  import api, { readerAPI } from '@/api'
import apiClient from '@/api/config.js'
  import { playSegmentAudio, playChapterAudio } from '@/utils/audioService'
  import ProjectHeader from '@/components/synthesis-center/ProjectHeader.vue'
  import ChapterSelector from '@/components/synthesis-center/ChapterSelector.vue'
  import ContentPreview from '@/components/synthesis-center/ContentPreview.vue'
  import ProgressDrawer from '@/components/synthesis-center/ProgressDrawer.vue'

  // 环境音相关组件已迁移至单独的环境混合页面
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

  // 环境混音相关状态已迁移至单独的环境混合页面

  // WebSocket 连接
  let websocket = null
  let progressRefreshInterval = null
  let statusSyncInterval = null // 🔥 新增：状态同步定时器

  // 🔧 新增：当前章节进度数据
  const currentChapterProgress = ref({ completed: 0, total: 0, percent: 0 })

  // 🔥 防止重复提醒的标志
  const hasShownCompletionMessage = ref(false)

  // 🔧 加载当前章节进度
  const loadCurrentChapterProgress = async () => {
    if (!selectedChapter.value || !project.value?.id) {
      currentChapterProgress.value = { completed: 0, total: 0, percent: 0 }
      return
    }

    try {
      const response = await readerAPI.getChapterProgress(project.value.id, selectedChapter.value)
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
          (result) => result.chapter_id === selectedChapter.value
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

  // 计算属性 - 🔥 重构：基于章节状态而不是项目状态
  const canStartSynthesis = computed(() => {
    if (!selectedChapter.value || !project.value) {
      return false
    }

    // 检查本地合成状态
    if (synthesisRunning.value || synthesisStarting.value) {
      return false
    }

    return true
  })

  // 🔥 新增：专门用于判断是否可以开始新的合成（不包括重新合成）
  const canStartNewSynthesis = computed(() => {
    if (!canStartSynthesis.value) {
      return false
    }

    // 检查当前章节状态
    const chapter = chapters.value.find((ch) => ch.id === selectedChapter.value)
    if (!chapter) {
      console.log('⚠️ 未找到当前章节，禁用合成按钮')
      return false
    }

    // 如果章节正在处理中，不允许开始新的合成
    if (chapter.synthesis_status === 'processing') {
      console.log('⚠️ 章节正在处理中，禁用合成按钮')
      return false
    }

    // 其他状态都允许开始合成
    return true
  })

  // 🔥 新增：专门用于判断是否可以重新合成
  const canRestartSynthesis = computed(() => {
    if (!selectedChapter.value || !project.value) {
      return false
    }

    // 检查本地合成状态
    if (synthesisRunning.value || synthesisStarting.value) {
      return false
    }

    // 检查进度状态（如果正在处理则不能重新合成）
    const progressStatus = progressData.value?.status
    if (progressStatus === 'processing' || progressStatus === 'running') {
      return false
    }

    // 🔥 重新合成时允许章节已完成的情况
    return true
  })

  // 初始化
  onMounted(async () => {
    await loadProject()
    await loadChapters()

    // 🔥 **页面初始化时同步所有章节状态**
    await syncAllChapterStatuses()

    // 如果有选中的章节，立即加载智能准备结果
    if (selectedChapter.value) {
      await loadPreparationResults()
      // 🔧 加载当前章节进度
      await loadCurrentChapterProgress()
    }

    // 🔥 基于合成状态而不是项目状态决定是否显示进度抽屉
    if (synthesisRunning.value) {
      progressDrawerVisible.value = true
      console.log('📊 页面初始化时发现正在合成，自动显示进度抽屉')
    }

    // 🔥 **启动定期状态同步机制**
    statusSyncInterval = setInterval(async () => {
      await syncAllChapterStatuses()
    }, 30000) // 每30秒同步一次状态

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
          console.log('🌍 环境音混合功能已迁移至单独页面')
          message.info('环境音混合功能已迁移至单独页面，请前往环境混合页面操作')
        }

        // 清除查询参数，避免重复触发
        router.replace({ path: route.path })
      }, 1000)
    }

    initWebSocket()
  })

  onUnmounted(() => {
    console.log('🧹 页面卸载，清理资源')

    // 🔧 清理WebSocket连接
    if (websocket) {
      console.log('🔌 关闭WebSocket连接')
      websocket.close()
      websocket = null
    }

    // 🔧 清理定时器
    if (progressRefreshInterval) {
      console.log('⏰ 清理进度轮询定时器')
      clearInterval(progressRefreshInterval)
      progressRefreshInterval = null
    }

    // 🔧 清理状态同步定时器
    if (statusSyncInterval) {
      console.log('⏰ 清理状态同步定时器')
      clearInterval(statusSyncInterval)
      statusSyncInterval = null
    }
  })

  // 加载项目详情
  const loadProject = async () => {
    try {
      loading.value = true
      const projectId = route.params.projectId

      const response = await readerAPI.getProjectDetail(projectId)
      if (response.data.success) {
        project.value = response.data.data
        console.log('📊 项目数据加载成功:', {
          项目ID: project.value.id,
          项目名称: project.value.name,
          项目状态: project.value.status,
          是否已开始: !!project.value.started_at,
          开始时间: project.value.started_at,
          关联书籍: project.value.book_id
        })
      } else {
        message.error('加载项目失败')
      }
    } catch (error) {
      console.error('加载项目失败:', error)
      message.error('加载项目失败')
    } finally {
      loading.value = false
    }
  }

  // 🔥 已移除 loadSynthesisProgress 函数 - 不再需要项目级别的进度数据
  const loadSynthesisProgress_REMOVED = async () => {
    try {
      const projectId = route.params.projectId
      // 使用正确的API获取项目的合成进度
      const response = await readerAPI.getProgress(projectId)
      if (response.data.success && response.data.data) {
        const progressInfo = response.data.data

        // 🔧 修复：正确解析API返回的数据格式
        const segments = progressInfo.segments || {}
        progressData.value = {
          progress: progressInfo.progress_percentage || 0,
          status: progressInfo.status || 'pending', // 🔥 不再依赖项目状态
          completed_segments: segments.completed || 0,
          total_segments: segments.total || 0,
          failed_segments: segments.failed || 0,
          current_processing: '正在生成语音...',
          synthesis_type: progressData.value?.synthesis_type // 保持合成类型标识
        }

        // 🔥 移除项目状态强制同步逻辑 - 我们不再依赖项目状态
        const apiStatus = progressInfo.status

        if (apiStatus === 'processing') {
          synthesisRunning.value = true
          // 🔧 自动显示进度抽屉
          if (!progressDrawerVisible.value) {
            progressDrawerVisible.value = true
            console.log('📊 项目正在合成中，自动显示进度抽屉')
          }
        } else if (
          apiStatus === 'paused' ||
          apiStatus === 'cancelled' ||
          apiStatus === 'completed' ||
          apiStatus === 'partial_completed' ||
          apiStatus === 'failed'
        ) {
          synthesisRunning.value = false
          console.log('📊 项目非运行状态，重置前端状态', apiStatus)

          // 🔥 确保进度抽屉关闭（页面初始化时不应该显示）
          progressDrawerVisible.value = false

          // 🔧 合成完成时停止轮询
          if (
            (apiStatus === 'completed' || apiStatus === 'partial_completed') &&
            progressRefreshInterval
          ) {
            console.log('✅ 合成完成，停止进度轮询')
            clearInterval(progressRefreshInterval)
            progressRefreshInterval = null
          }
        }

        console.log('📊 加载进度信息 (API格式):', progressData.value)
      } else {
        // 如果API返回空数据，从项目统计信息中推导
        if (project.value?.statistics) {
          const stats = project.value.statistics
          progressData.value = {
            progress: stats.progress || 0,
            status: 'pending', // 🔥 不依赖项目状态，始终使用pending
            completed_segments: stats.completedSegments || 0,
            total_segments: stats.totalSegments || 0,
            failed_segments: stats.failedSegments || 0,
            current_processing: '正在生成语音...',
            synthesis_type: progressData.value?.synthesis_type // 保持合成类型标识
          }
          console.log('📊 从项目统计推导进度:', progressData.value)
        } else {
          // 🔥 如果项目没有统计信息，设置默认值（不依赖项目状态）
          progressData.value = {
            progress: 0,
            status: 'pending',
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
          status: 'pending', // 🔥 不再依赖项目状态
          completed_segments: stats.completedSegments || 0,
          total_segments: stats.totalSegments || 0,
          failed_segments: stats.failedSegments || 0,
          current_processing: '正在生成语音...',
          synthesis_type: progressData.value?.synthesis_type // 保持合成类型标识
        }
      } else {
        // 🔥 设置安全的默认值（不依赖项目状态）
        progressData.value = {
          progress: 0,
          status: 'pending',
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
      console.log(
        'Loading chapters, project:',
        project.value,
        'allowChapterReset:',
        allowChapterReset
      )

      if (project.value?.book_id) {
        // 直接使用apiClient调用正确的API路径
        const response = await apiClient.get(`/books/${project.value.book_id}/chapters`, {
          params: {
            sort_by: 'chapter_number',
            sort_order: 'asc'
          }
        })
        console.log('Chapters API response:', response.data)

        if (response.data.success && response.data.data) {
          // 🔧 调试：查看原始章节数据结构
          console.log(
            '📋 原始章节数据结构示例:',
            response.data.data.slice(0, 3).map((ch) => ({
              id: ch.id,
              chapter_number: ch.chapter_number,
              number: ch.number,
              title: ch.title,
              chapter_title: ch.chapter_title,
              完整对象: ch
            }))
          )

          // 🔧 前端强制排序：确保章节按照chapter_number升序排列
          chapters.value = response.data.data.sort((a, b) => {
            // 兼容不同的字段名称
            const aNum = parseInt(a.chapter_number || a.number) || 0
            const bNum = parseInt(b.chapter_number || b.number) || 0
            console.log('🔢 排序比较:', {
              a: { id: a.id, chapter_number: a.chapter_number, number: a.number, aNum },
              b: { id: b.id, chapter_number: b.chapter_number, number: b.number, bNum },
              result: aNum - bNum
            })
            return aNum - bNum
          })
          console.log('Found chapters (sorted):', chapters.value)

          if (chapters.value.length > 0) {
            // 🔧 根据allowChapterReset参数决定是否允许重置章节选择
            if (!selectedChapter.value && allowChapterReset) {
              selectedChapter.value = chapters.value[0].id
              console.log('✅ 设置默认选中章节:', selectedChapter.value)
            } else if (selectedChapter.value && allowChapterReset) {
              // 验证当前选中的章节是否还存在
              const currentChapterExists = chapters.value.some(
                (ch) => ch.id === selectedChapter.value
              )
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
  watch(
    selectedChapter,
    (newChapter, oldChapter) => {
      if (newChapter !== oldChapter) {
        console.log('🔄 章节选择发生变化:', {
          从: oldChapter,
          到: newChapter,
          调用栈: new Error().stack
        })
      }
    },
    { immediate: false }
  )

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


    try {
      // 只获取选中章节的智能准备结果
      const response = await apiClient.get(
        `/books/${project.value.book_id}/analysis-results?chapter_ids=${selectedChapter.value}`
      )
      console.log('📊 API响应:', response.data)

      if (response.data.success) {
        // 检查是否有实际的准备结果数据
        if (
          response.data.data &&
          Array.isArray(response.data.data) &&
          response.data.data.length > 0
        ) {
          // 进一步检查数据是否包含有效的合成计划
          const hasValidData = response.data.data.some(
            (chapter) =>
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
      console.log(
        `🔍 章节 ${selectedChapter.value} 的准备结果加载完成，preparationResults:`,
        preparationResults.value
      )
    }
  }

  // WebSocket 初始化
  const initWebSocket = () => {
    const projectId = route.params.projectId
    const wsUrl = getWebSocketUrl('MAIN')

    console.log('🔌 初始化WebSocket连接:', { projectId, wsUrl })

    // 🔧 清理旧连接
    if (websocket && websocket.readyState !== WebSocket.CLOSED) {
      console.log('🧹 关闭旧WebSocket连接')
      websocket.close()
    }

    try {
      websocket = new WebSocket(wsUrl)

      // 🔧 立即检查连接状态


      websocket.onopen = () => {
        websocketStatus.value = 'connected'
        console.log('✅ WebSocket连接已建立')

        // 订阅合成进度主题
        const projectId = route.params.projectId
        if (projectId) {
          const subscribeMsg = {
            type: 'subscribe',
            topic: `synthesis_${projectId}`
          }
          console.log('📡 发送订阅消息:', subscribeMsg)
          // 🔥 修复：即使在onopen中也确保websocket存在
          if (websocket && websocket.readyState === WebSocket.OPEN) {
            websocket.send(JSON.stringify(subscribeMsg))
          } else {
            console.error('⚠️ WebSocket在onopen回调中不可用')
          }

          // 添加订阅确认机制
          setTimeout(() => {
  
            // 🔥 修复：先检查websocket是否存在，再检查连接状态
            if (websocket && websocket.readyState === WebSocket.OPEN) {
              websocket.send(JSON.stringify(subscribeMsg))
              console.log('📡 再次确认订阅')
            } else {
              console.log('⚠️ WebSocket连接不可用，跳过再次订阅')
            }
          }, 1000)
        }
      }

      websocket.onmessage = (event) => {
        const wsMessage = JSON.parse(event.data)
        console.log('📨 收到WebSocket消息:', wsMessage)

        // 🔧 订阅确认消息（匹配后端的实际响应类型）
        if (wsMessage.type === 'subscription_confirmed') {
          console.log('✅ WebSocket订阅成功:', wsMessage.topic)
          return
        }

        if (wsMessage.type === 'subscribe_success') {
          console.log('✅ WebSocket订阅成功 (备用格式):', wsMessage.topic)
          return
        }

        if (wsMessage.type === 'subscribe_error' || wsMessage.type === 'subscription_error') {
          console.error('❌ WebSocket订阅失败:', wsMessage)
          return
        }

        // 处理主题消息
        if (wsMessage.type === 'topic_message' && wsMessage.topic === `synthesis_${projectId}`) {
          const data = wsMessage.data
      

          // 更新进度数据
          if (data.type === 'progress_update' && data.data) {
            progressData.value = {
              progress: data.data.progress || 0,
              status: data.data.status || 'pending',
              completed_segments: data.data.completed_segments || 0,
              total_segments: data.data.total_segments || 0,
              failed_segments: data.data.failed_segments || 0,
              current_processing: data.data.current_processing || '',
              current_chapter_id: data.data.chapter_id, // 🔥 添加当前正在处理的章节ID
              synthesis_type: progressData.value?.synthesis_type // 保持合成类型
            }

            console.log('📊 WebSocket更新进度数据:', progressData.value)

            // 🔧 只更新当前正在合成的章节进度
            if (data.data.chapter_id) {
              loadCurrentChapterProgress()
            }

                      // 🔥 处理合成完成状态
          if (
            data.data.status === 'completed' ||
            data.data.status === 'partial_completed' ||
            data.data.status === 'failed'
          ) {
            console.log('🎉 WebSocket收到合成完成消息，更新项目状态', {
              状态: data.data.status,
              章节ID: data.data.chapter_id,
              完成段落: data.data.completed_segments,
              总段落: data.data.total_segments,
              失败段落: data.data.failed_segments,
              章节音频文件数: data.data.chapter_audio_files
            })

            // 🔥 立即显示完成提醒（避免重复）
            if (!hasShownCompletionMessage.value) {
              if (data.data.status === 'completed') {
                message.success('🎉 章节合成完成！', 5)
              } else if (data.data.status === 'partial_completed') {
                message.success('✅ 章节合成完成！', 5)
              } else if (data.data.status === 'failed') {
                message.error('❌ 合成失败！', 5)
              }
              hasShownCompletionMessage.value = true
            }

              // 🔥 立即更新状态
              synthesisRunning.value = false

              // 🔥 **使用正确的状态同步机制**
              if (data.data.chapter_id) {
                const finalStatus =
                  data.data.status === 'completed'
                    ? 'completed'
                    : data.data.status === 'failed'
                      ? 'failed'
                      : 'pending'

                // 调用状态同步方法，确保前后端一致
                syncChapterStatus(data.data.chapter_id, finalStatus)
              }

              // 🔥 删除临时方案，使用正确的状态同步
              // setTimeout(async () => {
              //   console.log('🔄 合成完成后重新加载章节数据')
              //   await loadChapters(false) // 不重置选中章节
              // }, 1000)

              // 🔧 停止定期刷新
              if (progressRefreshInterval) {
                clearInterval(progressRefreshInterval)
                progressRefreshInterval = null
              }

              // 🔥 如果章节完成，自动关闭进度抽屉
              if (data.data.status === 'completed' || data.data.status === 'partial_completed') {
                setTimeout(() => {
                  progressDrawerVisible.value = false
                }, 3000) // 3秒后自动关闭
              }
            }
          }
        } else if (message.type === 'topic_message') {
  
        }
      }

      websocket.onclose = (event) => {
        websocketStatus.value = 'disconnected'
        console.log('🔴 WebSocket连接关闭:', { code: event.code, reason: event.reason })

        // 🔧 自动重连机制（仅在合成进行中时重连）
        if (synthesisRunning.value) {
          console.log('🔄 合成进行中，5秒后尝试重连WebSocket...')
          setTimeout(() => {
            if (synthesisRunning.value && websocketStatus.value === 'disconnected') {
              console.log('🔄 开始重连WebSocket...')
              initWebSocket()
            }
          }, 5000)
        }
      }

      websocket.onerror = (error) => {
        websocketStatus.value = 'error'
        console.error('🔴 WebSocket错误:', error)
      }
    } catch (error) {
      console.error('WebSocket initialization failed:', error)
    }
  }

  // 🔧 WebSocket诊断函数
  const testWebSocketConnection = () => {
    console.log('🧪 开始WebSocket连接诊断')
    console.log('📊 当前状态:', {
      websocketStatus: websocketStatus.value,
      websocketExists: !!websocket,
      websocketReadyState: websocket?.readyState,
      projectId: route.params.projectId
    })

    if (websocket) {


      // 尝试发送测试消息
      if (websocket.readyState === WebSocket.OPEN) {
        const testMsg = {
          type: 'ping',
          timestamp: Date.now()
        }
        console.log('📡 发送测试ping消息:', testMsg)
        websocket.send(JSON.stringify(testMsg))
      } else {
        console.warn('⚠️ WebSocket未处于OPEN状态，无法发送消息')
      }
    } else {
      console.error('❌ WebSocket对象不存在')
    }
  }

  // 处理函数
  const handleBack = () => {
    router.push('/novel-reader')
  }

  const handleStartSynthesis = async () => {
    try {
      // 🔧 防重复合成检查
      if (!canStartNewSynthesis.value) {
        message.warning('当前无法开始合成，请检查项目状态')
        return
      }

      // 🔧 检查当前合成状态（不依赖项目状态）
      if (synthesisRunning.value) {
        message.warning('当前正在合成中，无法重复合成')
        return
      }

      synthesisStarting.value = true

      // 🎯 设置合成类型
      synthesisType.value = 'voice'
      synthesisStatus.value = 'running'

      const response = await readerAPI.startGeneration(project.value.id, {
        chapter_ids: selectedChapter.value ? [selectedChapter.value] : undefined,
        continue_synthesis: false // 重新合成模式
      })

      if (response.data.success) {
        message.success('🎤 开始角色音合成')
        synthesisRunning.value = true
        progressDrawerVisible.value = true

        // 🔥 重置完成提醒标志
        hasShownCompletionMessage.value = false

        // 🔧 确保WebSocket连接正常
        if (websocketStatus.value !== 'connected') {
          console.log('🔄 合成开始前，WebSocket未连接，重新初始化')
          initWebSocket()

          // 等待连接建立后再继续
          setTimeout(() => {
            if (websocketStatus.value !== 'connected') {
              console.warn('⚠️ WebSocket连接建立超时，将依赖轮询获取进度')
            }
          }, 3000)
        } else {
          // 即使已连接，也重新订阅主题确保订阅正常
          const subscribeMsg = {
            type: 'subscribe',
            topic: `synthesis_${project.value.id}`
          }
          console.log('🔄 合成开始，重新确认订阅:', subscribeMsg)
          try {
            // 🔥 修复：检查websocket是否存在且连接正常
            if (websocket && websocket.readyState === WebSocket.OPEN) {
              websocket.send(JSON.stringify(subscribeMsg))

              // 延迟再次订阅，确保成功
              setTimeout(() => {
                if (websocket && websocket.readyState === WebSocket.OPEN) {
                  websocket.send(JSON.stringify(subscribeMsg))
                  console.log('📡 第二次订阅确认')
                } else {
                  console.log('⚠️ WebSocket连接不可用，跳过第二次订阅')
                }
              }, 500)
            } else {
              console.log('⚠️ WebSocket未连接或不可用，跳过订阅')
            }
          } catch (error) {
            console.error('❌ 重新订阅失败:', error)
          }
        }

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

        // 🔧 1秒后更新当前章节进度（不影响其他章节）
        setTimeout(() => {
          loadCurrentChapterProgress()
        }, 1000)

        // 🔧 启动定期刷新进度（防止WebSocket消息丢失）
        if (progressRefreshInterval) {
          clearInterval(progressRefreshInterval)
        }
        progressRefreshInterval = setInterval(async () => {
          if (synthesisRunning.value) {
            // 🔥 只检查当前章节状态，不影响其他章节
            await loadCurrentChapterProgress()

            // 🔥 基于章节进度检查是否已完成（防止WebSocket消息丢失）
            const chapterProgress = currentChapterProgress.value
            const isChapterCompleted =
              chapterProgress.total > 0 && chapterProgress.completed === chapterProgress.total

            if (isChapterCompleted) {
      

              // 显示完成提醒（避免重复）
              if (!hasShownCompletionMessage.value) {
                message.success('✅ 章节合成完成！', 5)
                hasShownCompletionMessage.value = true
              }

              // 更新状态
              synthesisRunning.value = false

              // 停止轮询
              if (progressRefreshInterval) {
                clearInterval(progressRefreshInterval)
                progressRefreshInterval = null
              }

              // 自动关闭进度抽屉
              setTimeout(() => {
                progressDrawerVisible.value = false
              }, 3000)
            }
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
  
              await readerAPI.pauseGeneration(project.value.id)
      message.success('已暂停合成')
      synthesisRunning.value = false

      // 🔧 停止定期刷新
      if (progressRefreshInterval) {
        clearInterval(progressRefreshInterval)
        progressRefreshInterval = null
      }

      // 更新当前章节状态（不影响其他章节）
      await loadCurrentChapterProgress()
    } catch (error) {
      console.error('Failed to pause synthesis:', error)
      message.error('暂停合成失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleCancelSynthesis = async () => {
    try {
  
              await readerAPI.cancelGeneration(project.value.id)
      message.success('已取消合成')
      synthesisRunning.value = false
      progressDrawerVisible.value = false

      // 🔧 停止定期刷新
      if (progressRefreshInterval) {
        clearInterval(progressRefreshInterval)
        progressRefreshInterval = null
      }

      // 更新当前章节状态（不影响其他章节）
      await loadCurrentChapterProgress()
    } catch (error) {
      console.error('Failed to cancel synthesis:', error)
      message.error('取消合成失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleResetProjectStatus = async () => {
    try {
      console.log('🔧 开始重置项目状态，项目ID:', project.value.id)
      await api.resetProjectStatus(project.value.id)
      message.success('项目状态已重置为可用状态')

      // 重置前端状态
      synthesisRunning.value = false
      progressDrawerVisible.value = false

      // 停止定期刷新
      if (progressRefreshInterval) {
        clearInterval(progressRefreshInterval)
        progressRefreshInterval = null
      }

      // 重新加载项目和章节数据
      await loadProject()
      await loadCurrentChapterProgress()
    } catch (error) {
      console.error('Failed to reset project status:', error)
      message.error('重置项目状态失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  const handleRetrySynthesis = async () => {
    try {
      await readerAPI.resumeGeneration(project.value.id, {})
      message.success('重新开始合成')
      synthesisRunning.value = true
      progressDrawerVisible.value = true
    } catch (error) {
      console.error('Failed to retry synthesis:', error)
      message.error('重试合成失败')
    }
  }

  // 🔥 删除项目状态重置功能 - 不再需要，因为我们不依赖项目状态
  // 如果需要重置，可以直接重置本地状态：
  const handleResetLocalSynthesisState = () => {
    console.log('🔧 重置本地合成状态')
    synthesisRunning.value = false
    progressDrawerVisible.value = false
    hasShownCompletionMessage.value = false

    // 停止定期刷新
    if (progressRefreshInterval) {
      clearInterval(progressRefreshInterval)
      progressRefreshInterval = null
    }

    message.success('✅ 本地状态已重置')
  }

  const handlePlayAudio = async () => {
    try {
      playingChapterAudio.value = selectedChapter.value

      // 🎯 构建章节完整标题
      const currentChapter = chapters.value.find((ch) => ch.id === selectedChapter.value)
      const chapterTitle = currentChapter
        ? `第${currentChapter.chapter_number || currentChapter.id}章：${currentChapter.title || currentChapter.chapter_title || '未命名章节'}`
        : `章节${selectedChapter.value}`

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
      const response = await readerAPI.downloadChapterAudio(project.value.id, selectedChapter.value)

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
      // 🔧 修复：优先使用segment_id，其次是id，最后才是index
      const segmentId = segment.segment_id || segment.id || segment.index || segment.ui_index



      // 🚨 重要检查：如果segment_id异常大，发出警告
      if (segmentId > 50) {


        // 显示用户警告但不阻止播放
        message.warning(`⚠️ 段落ID为${segmentId}，可能播放错误的音频`)
      }

      if (!segmentId) {

        message.error('无法获取段落ID')
        return
      }

      // 🎯 构建丰富的段落信息
      const currentChapter = chapters.value.find((ch) => ch.id === selectedChapter.value)
      const chapterInfo = currentChapter
        ? `第${currentChapter.chapter_number || currentChapter.id}章：${currentChapter.title || currentChapter.chapter_title || '未命名章节'}`
        : `章节${selectedChapter.value}`

      const segmentText = segment.text || segment.content || ''
      const segmentPreview =
        segmentText.length > 30 ? segmentText.substring(0, 30) + '...' : segmentText

      const fullTitle = `${chapterInfo} - 段落${segmentId}: ${segmentPreview}`

      console.log(`🎵 即将播放：`, {
        项目ID: project.value.id,
        段落ID: segmentId,
        章节信息: chapterInfo,
        段落文本: segmentPreview,
        完整标题: fullTitle,
        '🔍 章节对象详情': currentChapter,
        当前章节title字段: currentChapter?.title,
        当前章节chapter_title字段: currentChapter?.chapter_title,
        所有章节数据: chapters.value
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
      const response = await readerAPI.getFailedSegments(project.value.id)
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
            loadCurrentChapterProgress()
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
        error_message: ['未找到对应的声音档案', 'TTS服务连接超时', '文本包含无法处理的特殊字符'][
          i % 3
        ]
      })
    }

    return mockSegments
  }

  // ContentPreview 事件处理
  const handleRefreshPreparation = () => {
    message.info('刷新智能准备结果')
    // 🔧 只刷新当前章节的准备结果，不影响其他章节
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

  const handlePlayChapter = async (chapterId) => {
    try {
      // 🔥 **修复：播放指定章节，不修改选中章节**
      playingChapterAudio.value = chapterId

      // 🎯 构建指定章节的完整标题
      const targetChapter = chapters.value.find((ch) => ch.id === chapterId)
      const chapterTitle = targetChapter
        ? `第${targetChapter.chapter_number || targetChapter.id}章：${targetChapter.title || targetChapter.chapter_title || '未命名章节'}`
        : `章节${chapterId}`

      console.log(`🎵 播放指定章节：`, {
        项目ID: project.value.id,
        章节ID: chapterId,
        章节标题: chapterTitle,
        当前选中章节: selectedChapter.value, // 不应该被修改
        播放章节: chapterId
      })

      // 🎯 **直接播放指定章节，不修改选中状态**
      await playChapterAudio(project.value.id, chapterId, chapterTitle)
      message.success(`🎵 播放：${chapterTitle}`)
    } catch (error) {
      console.error('Failed to play chapter audio:', error)
      message.error('播放章节音频失败')
    } finally {
      playingChapterAudio.value = null
    }
  }

  const handleDownloadChapter = async (chapterId) => {
    try {
      // 🔥 **修复：下载指定章节，不修改选中章节**
      const targetChapter = chapters.value.find((ch) => ch.id === chapterId)
      const chapterTitle = targetChapter
        ? `第${targetChapter.chapter_number || targetChapter.id}章：${targetChapter.title || targetChapter.chapter_title || '未命名章节'}`
        : `章节${chapterId}`

      console.log(`⬇️ 下载指定章节：`, {
        项目ID: project.value.id,
        章节ID: chapterId,
        章节标题: chapterTitle,
        当前选中章节: selectedChapter.value // 不应该被修改
      })

      // 🎯 **直接下载指定章节，不修改选中状态**
              const response = await readerAPI.downloadChapterAudio(project.value.id, chapterId)

      const blob = new Blob([response.data], { type: 'audio/wav' })
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `${chapterTitle}.wav`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      window.URL.revokeObjectURL(url)

      message.success(`⬇️ 下载完成：${chapterTitle}`)
    } catch (error) {
      console.error('Failed to download chapter audio:', error)
      message.error('下载章节音频失败')
    }
  }

  // 重新合成处理函数
  const handleRestartSynthesis = async () => {
    try {
      // 🔧 防重复合成检查
      if (!canRestartSynthesis.value) {
        message.warning('当前无法重新合成，请检查项目状态')
        return
      }

      // 🔧 检查当前合成状态（不依赖项目状态）
      if (synthesisRunning.value) {
        message.warning('当前正在合成中，无法重新合成')
        return
      }

      synthesisStarting.value = true

      // 🎯 设置合成类型
      synthesisType.value = 'voice'
      synthesisStatus.value = 'running'

      // 重新启动选中章节的合成
      const response = await readerAPI.startGeneration(project.value.id, {
        chapter_ids: selectedChapter.value ? [selectedChapter.value] : undefined,
        continue_synthesis: false // 表示这是重新合成，清理现有文件
      })

      if (response.data.success) {
        message.success('🎤 重新开始合成音频')
        synthesisRunning.value = true
        progressDrawerVisible.value = true // 显示进度抽屉

        // 🔥 重置完成提醒标志
        hasShownCompletionMessage.value = false

        // 🔧 确保WebSocket连接正常
        if (websocketStatus.value !== 'connected') {
          console.log('🔄 重新合成开始前，WebSocket未连接，重新初始化')
          initWebSocket()

          // 等待连接建立后再继续
          setTimeout(() => {
            if (websocketStatus.value !== 'connected') {
              console.warn('⚠️ WebSocket连接建立超时，将依赖轮询获取进度')
            }
          }, 3000)
        } else {
          // 即使已连接，也重新订阅主题确保订阅正常
          const subscribeMsg = {
            type: 'subscribe',
            topic: `synthesis_${project.value.id}`
          }
          console.log('🔄 重新合成开始，重新确认订阅:', subscribeMsg)
          try {
            // 🔥 修复：检查websocket是否存在且连接正常
            if (websocket && websocket.readyState === WebSocket.OPEN) {
              websocket.send(JSON.stringify(subscribeMsg))

              // 延迟再次订阅，确保成功
              setTimeout(() => {
                if (websocket && websocket.readyState === WebSocket.OPEN) {
                  websocket.send(JSON.stringify(subscribeMsg))
                  console.log('📡 第二次订阅确认')
                } else {
                  console.log('⚠️ WebSocket连接不可用，跳过第二次订阅')
                }
              }, 500)
            } else {
              console.log('⚠️ WebSocket未连接或不可用，跳过订阅')
            }
          } catch (error) {
            console.error('❌ 重新订阅失败:', error)
          }
        }

        // 🔧 初始化进度数据
        progressData.value = {
          progress: 0,
          status: 'processing',
          completed_segments: 0,
          total_segments: 0,
          failed_segments: 0,
          current_processing: '🎤 正在重新合成音频...',
          synthesis_type: 'voice' // 标记合成类型
        }

        // 🔧 1秒后更新当前章节进度（不影响其他章节）
        setTimeout(() => {
          loadCurrentChapterProgress()
        }, 1000)

        // 🔧 启动定期刷新进度（防止WebSocket消息丢失）
        if (progressRefreshInterval) {
          clearInterval(progressRefreshInterval)
        }
        progressRefreshInterval = setInterval(async () => {
          if (synthesisRunning.value) {
            // 🔥 只检查当前章节状态，不影响其他章节
            await loadCurrentChapterProgress()

            // 🔥 基于章节进度检查是否已完成（防止WebSocket消息丢失）
            const chapterProgress = currentChapterProgress.value
            const isChapterCompleted =
              chapterProgress.total > 0 && chapterProgress.completed === chapterProgress.total

            if (isChapterCompleted) {
      

              // 显示完成提醒（避免重复）
              if (!hasShownCompletionMessage.value) {
                message.success('✅ 章节重新合成完成！', 5)
                hasShownCompletionMessage.value = true
              }

              // 更新状态
              synthesisRunning.value = false

              // 停止轮询
              if (progressRefreshInterval) {
                clearInterval(progressRefreshInterval)
                progressRefreshInterval = null
              }

              // 自动关闭进度抽屉
              setTimeout(() => {
                progressDrawerVisible.value = false
              }, 3000)
            }
          }
        }, 3000) // 每3秒检查一次
      }
    } catch (error) {
      console.error('Failed to restart synthesis:', error)
      message.error('重新合成失败')
    } finally {
      synthesisStarting.value = false
    }
  }

  // 继续合成处理函数（用于部分完成的项目）
  const handleResumeSynthesis = async () => {
    try {
      // 🔧 防重复合成检查
      if (!canRestartSynthesis.value) {
        message.warning('当前无法继续合成，请检查项目状态')
        return
      }

      // 🔧 检查当前合成状态（不依赖项目状态）
      if (synthesisRunning.value) {
        message.warning('当前正在合成中，无法继续合成')
        return
      }

      synthesisStarting.value = true

      // 🎯 设置合成类型
      synthesisType.value = 'voice'
      synthesisStatus.value = 'running'

      // 继续合成剩余章节（不重新开始已完成的部分）
      const response = await readerAPI.startGeneration(project.value.id, {
        chapter_ids: selectedChapter.value ? [selectedChapter.value] : undefined,
        continue_synthesis: true // 表示这是继续合成，只生成缺失的段落
      })

      if (response.data.success) {
        message.success('🎤 继续合成剩余章节')
        synthesisRunning.value = true
        progressDrawerVisible.value = true // 显示进度抽屉

        // 🔥 重置完成提醒标志
        hasShownCompletionMessage.value = false

        // 🔧 确保WebSocket连接正常
        if (websocketStatus.value !== 'connected') {
          console.log('🔄 继续合成开始前，WebSocket未连接，重新初始化')
          initWebSocket()

          // 等待连接建立后再继续
          setTimeout(() => {
            if (websocketStatus.value !== 'connected') {
              console.warn('⚠️ WebSocket连接建立超时，将依赖轮询获取进度')
            }
          }, 3000)
        } else {
          // 即使已连接，也重新订阅主题确保订阅正常
          const subscribeMsg = {
            type: 'subscribe',
            topic: `synthesis_${project.value.id}`
          }
          console.log('🔄 继续合成开始，重新确认订阅:', subscribeMsg)
          try {
            // 🔥 修复：检查websocket是否存在且连接正常
            if (websocket && websocket.readyState === WebSocket.OPEN) {
              websocket.send(JSON.stringify(subscribeMsg))

              // 延迟再次订阅，确保成功
              setTimeout(() => {
                if (websocket && websocket.readyState === WebSocket.OPEN) {
                  websocket.send(JSON.stringify(subscribeMsg))
                  console.log('📡 第二次订阅确认')
                } else {
                  console.log('⚠️ WebSocket连接不可用，跳过第二次订阅')
                }
              }, 500)
            } else {
              console.log('⚠️ WebSocket未连接或不可用，跳过订阅')
            }
          } catch (error) {
            console.error('❌ 重新订阅失败:', error)
          }
        }

        // 🔧 初始化进度数据
        progressData.value = {
          progress: 0,
          status: 'processing',
          completed_segments: 0,
          total_segments: 0,
          failed_segments: 0,
          current_processing: '🎤 正在继续合成音频...',
          synthesis_type: 'voice' // 标记合成类型
        }

        // 🔧 1秒后更新当前章节进度（不影响其他章节）
        setTimeout(() => {
          loadCurrentChapterProgress()
        }, 1000)

        // 🔧 启动定期刷新进度（防止WebSocket消息丢失）
        if (progressRefreshInterval) {
          clearInterval(progressRefreshInterval)
        }
        progressRefreshInterval = setInterval(async () => {
          if (synthesisRunning.value) {
            // 🔥 只检查当前章节状态，不影响其他章节
            await loadCurrentChapterProgress()

            // 🔥 基于章节进度检查是否已完成（防止WebSocket消息丢失）
            const chapterProgress = currentChapterProgress.value
            const isChapterCompleted =
              chapterProgress.total > 0 && chapterProgress.completed === chapterProgress.total

            if (isChapterCompleted) {
      

              // 显示完成提醒（避免重复）
              if (!hasShownCompletionMessage.value) {
                message.success('✅ 章节继续合成完成！', 5)
                hasShownCompletionMessage.value = true
              }

              // 更新状态
              synthesisRunning.value = false

              // 停止轮询
              if (progressRefreshInterval) {
                clearInterval(progressRefreshInterval)
                progressRefreshInterval = null
              }

              // 自动关闭进度抽屉
              setTimeout(() => {
                progressDrawerVisible.value = false
              }, 3000)
            }
          }
        }, 3000) // 每3秒检查一次
      }
    } catch (error) {
      console.error('Failed to resume synthesis:', error)
      message.error('继续合成失败')
    } finally {
      synthesisStarting.value = false
    }
  }

  // 🔥 重构：基于实际AudioFile数据获取章节状态，不再依赖项目状态
  const getSelectedChapterStatus = () => {
    if (!selectedChapter.value || !chapters.value.length) {
      return 'pending'
    }

    const chapter = chapters.value.find((ch) => ch.id === selectedChapter.value)
    if (!chapter) return 'pending'

    // 1. 如果正在合成当前章节
    if (
      synthesisRunning.value &&
      progressData.value?.current_chapter_id === selectedChapter.value
    ) {
      return 'processing'
    }

    // 🔥 核心修复：始终基于项目级别的音频文件数据判断状态
    // 不再根据项目是否已开始来决定逻辑分支

    // 2. 使用当前章节的进度数据判断状态
    const chapterProgress = currentChapterProgress.value
    if (chapterProgress.total > 0 && chapterProgress.completed === chapterProgress.total) {
      return 'completed'
    } else if (chapterProgress.completed > 0) {
      return 'partial'
    } else {
      return 'pending' // 默认为待合成状态
    }
  }

  // 🔥 **状态同步核心方法** - 确保前端状态与数据库一致
  const syncChapterStatus = async (chapterId, newStatus) => {
    console.log('🔄 同步章节状态:', { chapterId, newStatus })

    // 1. 更新本地chapters数组
    const chapter = chapters.value.find((ch) => ch.id === chapterId)
    if (chapter) {
      const oldStatus = chapter.synthesis_status
      chapter.synthesis_status = newStatus
      console.log('✅ 本地状态更新:', {
        章节ID: chapterId,
        旧状态: oldStatus,
        新状态: newStatus
      })
    }

    // 2. 验证数据库状态（确保一致性）
    try {
      const response = await apiClient.get(`/books/${project.value.book_id}/chapters`)
      if (response.data.success && response.data.data) {
        const serverChapter = response.data.data.find((ch) => ch.id === chapterId)
        if (serverChapter && serverChapter.synthesis_status !== newStatus) {
          console.warn('⚠️ 前端状态与服务器不一致:', {
            前端状态: newStatus,
            服务器状态: serverChapter.synthesis_status,
            时间戳: new Date().toISOString()
          })

          // 🔥 智能状态同步：分析不一致原因
          if (newStatus === 'failed' && serverChapter.synthesis_status === 'completed') {
            // 情况1：WebSocket报告失败，但服务器显示完成
            // 可能是音频合并成功但WebSocket状态判断有误
    
            if (chapter) {
              chapter.synthesis_status = serverChapter.synthesis_status
            }
          } else if (newStatus === 'completed' && serverChapter.synthesis_status === 'failed') {
            // 情况2：WebSocket报告完成，但服务器显示失败
            // 可能是音频合并失败但WebSocket状态判断有误
    
            if (chapter) {
              chapter.synthesis_status = serverChapter.synthesis_status
            }
          } else {
            // 其他情况：以服务器状态为准
    
            if (chapter) {
              chapter.synthesis_status = serverChapter.synthesis_status
            }
          }
        }
      }
    } catch (error) {
      console.error('❌ 验证服务器状态失败:', error)
    }
  }

  // 🔥 **批量状态同步** - 处理多章节状态更新
  const syncAllChapterStatuses = async () => {
    if (!project.value?.book_id) return

    console.log('🔄 批量同步所有章节状态')
    try {
      const response = await apiClient.get(`/books/${project.value.book_id}/chapters`)
      if (response.data.success && response.data.data) {
        const serverChapters = response.data.data

        // 更新所有章节状态
        serverChapters.forEach((serverChapter) => {
          const localChapter = chapters.value.find((ch) => ch.id === serverChapter.id)
          if (localChapter && localChapter.synthesis_status !== serverChapter.synthesis_status) {
            console.log('🔄 更新章节状态:', {
              章节ID: serverChapter.id,
              章节标题: serverChapter.chapter_title,
              旧状态: localChapter.synthesis_status,
              新状态: serverChapter.synthesis_status
            })
            localChapter.synthesis_status = serverChapter.synthesis_status
            localChapter.analysis_status = serverChapter.analysis_status
            localChapter.updated_at = serverChapter.updated_at
          }
        })
      }
    } catch (error) {
      console.error('❌ 批量同步状态失败:', error)
    }
  }

  // 环境混音相关方法已迁移至单独的环境混合页面
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
  [data-theme='dark'] .dialogue-audio-generation {
    background: #141414 !important;
  }

  [data-theme='dark'] .main-content {
    background: #141414 !important;
  }

  [data-theme='dark'] .mini-progress-bar {
    background: #1f1f1f !important;
    border-top-color: #434343 !important;
    box-shadow: 0 -2px 8px rgba(0, 0, 0, 0.3) !important;
  }

  [data-theme='dark'] .mini-progress-bar:hover {
    background: #2d2d2d !important;
    box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.5) !important;
  }

  [data-theme='dark'] .mini-progress-text {
    color: #fff !important;
  }

  [data-theme='dark'] .mini-progress-tip {
    color: #8c8c8c !important;
  }

  /* 迷你进度条在暗黑模式下的主题颜色适配 */
  [data-theme='dark'] .mini-progress-content .ant-progress .ant-progress-bg {
    background-color: var(--primary-color) !important;
  }

  [data-theme='dark'] .mini-progress-bar:hover .ant-progress .ant-progress-bg {
    background-color: var(--secondary-color) !important;
  }

  /* 暗黑模式下的标签页样式 */
  [data-theme='dark'] .function-tabs .ant-tabs-tab.ant-tabs-tab-active {
    background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
  }

  [data-theme='dark'] .function-tabs .ant-tabs-tab:hover {
    background: rgba(24, 144, 255, 0.1);
  }

  [data-theme='dark'] .voice-synthesis-content,
  [data-theme='dark'] .music-generation-content {
    background: #141414;
  }

  /* 环境混音相关样式已迁移至单独的环境混合页面 */

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

    /* 移动端环境混音卡片样式已迁移至单独的环境混合页面 */

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
