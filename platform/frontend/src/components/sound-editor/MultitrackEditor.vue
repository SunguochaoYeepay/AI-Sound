<template>
  <div class="multitrack-editor">
    <!-- 主编辑区域 -->
    <div class="editor-container">
      <!-- 上半部分：资源库 + 预览 + 项目信息 -->
      <div class="top-section">
        <!-- 资源库面板 -->
        <ResourcePanel
          :audio-files="audioFiles"
          :loading="loadingAudioFiles"
          :search-keyword="searchKeyword"
          :playing-file-id="playingFileId"
          :active-tab="activeAudioTab"
          @refresh="refreshAudioFiles"
          @import-json="showImportDialog = true"
          @tab-change="activeAudioTab = $event"
          @upload="handleBeforeUpload"
          @search="handleSearch"
          @select-file="selectAudioFile"
          @play-file="playAudioFile"
          @delete-file="handleDeleteAudioFile"
          @add-to-project="handleAddAudioToProject"
          @drag-start="handleDragStart"
          @drag-end="handleDragEnd"
        />

        <!-- 预览面板 -->
        <PreviewPanel
          :current-time="currentTime"
          :total-duration="currentProject.project.totalDuration || 0"
          :is-playing="isPlaying"
          :is-loading="isLoadingPreview"
          :has-project="!!currentProject.project.id"
          @toggle-play="togglePlay"
          @stop="stopPlayback"
          @time-change="currentTime = $event"
        />

        <!-- 项目信息面板 -->
        <ProjectInfoPanel
          :project="currentProject.project"
          :selected-clip="selectedClip"
          :has-project="!!currentProject.project.id"
          :export-loading="exportLoading"
          @create-project="showCreateProject = true"
          @open-project="showProjectList = true"
          @save-project="saveCurrentProject"
          @export-project="exportCurrentProject"
          @update-project="updateProjectInfo"
          @update-clip="updateSelectedClip"
          @clear-selection="clearAllSelections"
        />
      </div>

      <!-- 下半部分：音轨编辑器 -->
      <div class="bottom-section">
        <TimelineEditor
          v-if="currentProject.project.id || currentProject.tracks.length > 0"
          ref="timelineEditor"
          :tracks="currentProject.tracks"
          :current-time="currentTime"
          :zoom-level="zoomLevel"
          :view-duration="viewDuration"
          :pixels-per-second="pixelsPerSecond"
          :timeline-width="timelineWidth"
          :total-duration="
            Math.max(calculateContentDuration, currentProject.project.totalDuration || 60)
          "
          :min-zoom="minZoom"
          :max-zoom="maxZoom"
          @zoom-change="handleZoomChange"
          @timeline-scroll="handleTimelineScroll"
          @update-track="updateTrack"
          @update-clip="updateClip"
          @delete-clip="deleteClip"
          @add-clip="addClip"
          @select-exclusive="handleExclusiveSelect"
          @fit-to-window="fitToWindow"
        />

        <!-- 空状态 -->
        <div v-else class="empty-state">
          <a-empty description="请创建或打开一个项目开始编辑">
            <a-button type="primary" @click="showCreateProject = true">创建新项目</a-button>
          </a-empty>
        </div>
      </div>
    </div>

    <!-- 对话框组件 -->
    <ProjectCreateForm
      :open="showCreateProject"
      @update:open="showCreateProject = $event"
      @success="handleProjectCreated"
    />

    <ProjectList
      :open="showProjectList"
      @update:open="showProjectList = $event"
      @select="handleProjectSelected"
    />

    <ImportJsonForm
      :open="showImportDialog"
      @update:open="showImportDialog = $event"
      @success="handleImportSuccess"
    />

    <!-- 导出进度对话框 -->
    <a-modal
      v-model:open="showExportProgress"
      title="导出进度"
      :footer="exportStatus === 'completed' ? null : undefined"
      :closable="exportStatus !== 'processing'"
      :maskClosable="false"
    >
      <div class="export-progress">
        <a-result
          v-if="exportStatus === 'completed'"
          status="success"
          title="导出完成"
          sub-title="音频文件已成功生成"
        >
          <template #extra>
            <a-button type="primary" @click="downloadExportedFile">下载文件</a-button>
            <a-button @click="showExportProgress = false">关闭</a-button>
          </template>
        </a-result>
        <a-result
          v-else-if="exportStatus === 'failed'"
          status="error"
          title="导出失败"
          :sub-title="exportMessage"
        >
          <template #extra>
            <a-button @click="showExportProgress = false">关闭</a-button>
          </template>
        </a-result>
        <div v-else>
          <a-spin size="large" />
          <p style="margin-top: 16px; text-align: center">
            {{ exportMessage || '正在处理音频...' }}
          </p>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
  import { ref, reactive, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
  import { message, Modal } from 'ant-design-vue'
  import { h } from 'vue'
  import { useRoute } from 'vue-router'

  // 导入子组件
  import ResourcePanel from './panels/ResourcePanel.vue'
  import PreviewPanel from './panels/PreviewPanel.vue'
  import ProjectInfoPanel from './panels/ProjectInfoPanel.vue'
  import TimelineEditor from './panels/TimelineEditor.vue'
  import ProjectCreateForm from './dialogs/ProjectCreateForm.vue'
  import ProjectList from './dialogs/ProjectList.vue'
  import ImportJsonForm from './dialogs/ImportJsonForm.vue'
  import EditableText from './common/EditableText.vue'

  // 导入API服务
  import {
    uploadMultipleAudioFiles,
    uploadAudioFile,
    listAudioFiles,
    deleteAudioFile
  } from '../../api/sound-editor/audioFiles'
  import {
    createProject,
    loadProject,
    saveProject,
    listProjects,
    deleteProject,
    convertToStandardFormat,
    validateProject,
    exportProject,
    getExportStatus,
    downloadExportedAudio,
    generatePreviewAudio,
    getPreviewAudioUrl,
    deletePreviewFile,
    createEmptyProject,
    calculateProjectDuration,
    formatTime,
    generateId
  } from '../../api/sound-editor/multitrackProject'

  // 定义emit
  const emit = defineEmits(['project-change'])

  // ========== 响应式数据 ==========
  // 音频文件相关
  const audioFiles = ref([])
  const loadingAudioFiles = ref(false)
  const searchKeyword = ref('')
  const activeAudioTab = ref('dialogue')
  const playingFileId = ref(null)

  // 项目相关
  const currentProject = reactive(createEmptyProject())

  // 播放控制
  const currentTime = ref(0)
  const isPlaying = ref(false)
  const isLoadingPreview = ref(false)

  // 选择状态
  const selectedClip = computed(() => {
    for (const track of currentProject.tracks) {
      for (const clip of track.clips) {
        if (clip.selected) {
          return { ...clip, trackType: track.type }
        }
      }
    }
    return null
  })

  // 时间轴相关
  const zoomLevel = ref(1)
  const basePixelsPerSecond = ref(50) // 基础像素密度（每秒像素数）
  const pixelsPerSecond = computed(() => basePixelsPerSecond.value * zoomLevel.value)

  // 计算实际音频内容长度
  const calculateContentDuration = computed(() => {
    let maxTime = 0

    if (currentProject.tracks && currentProject.tracks.length > 0) {
      currentProject.tracks.forEach((track) => {
        if (track.clips && track.clips.length > 0) {
          track.clips.forEach((clip) => {
            const endTime = (clip.startTime || 0) + (clip.duration || 0)
            if (endTime > maxTime) {
              maxTime = endTime
            }
          })
        }
      })
    }

    // 添加30秒缓冲区，最小60秒
    return Math.max(60, maxTime + 30)
  })

  // 时间轴总宽度：基于实际内容长度计算，考虑缩放
  const timelineWidth = computed(() => {
    const contentDuration = Math.max(
      calculateContentDuration.value,
      currentProject.project.totalDuration || 60
    )
    const calculatedWidth = contentDuration * pixelsPerSecond.value

    // 确保最小宽度，特别是在高度缩小时
    // 调整为更合理的最小宽度计算，适配新的左侧面板宽度(150px)
    const minWidth = Math.max(800, 1200 / zoomLevel.value) // 基础最小宽度800px

    return Math.max(minWidth, calculatedWidth)
  })

  // 视窗显示时长：缩放越大，显示的时间越短（越精细）
  const viewDuration = computed(() => {
    const baseViewTime = 60 // 基础视窗时间（秒）
    return baseViewTime / zoomLevel.value
  })
  const minZoom = ref(0.1) // 最小缩放10%，支持显示长时间音频
  const maxZoom = ref(8) // 最大缩放800%

  // 对话框显示状态
  const showCreateProject = ref(false)
  const showProjectList = ref(false)
  const showImportDialog = ref(false)
  const exportLoading = ref(false)
  const showExportProgress = ref(false)

  // 导出相关状态
  const exportStatus = ref('')
  const exportMessage = ref('')
  const currentExportTaskId = ref('')

  // 创建项目表单
  const createForm = reactive({
    title: '',
    description: '',
    author: 'AI-Sound'
  })

  // 导入表单
  const importForm = ref({
    type: 'dialogue',
    data: null
  })

  // 音频播放相关
  let currentAudio = null
  let currentAudioId = 0
  let playInterval = null

  // 预览播放相关
  let previewAudioElement = null
  let currentPreviewFile = null
  let autoSaveTimer = null

  // 拖拽状态
  const draggedAudioFile = ref(null)
  const isDragging = ref(false)

  // ========== 计算属性 ==========
  const filteredDialogueFiles = computed(() =>
    filterFilesByKeyword(
      audioFiles.value.filter((file) => file.category === 'dialogue' || !file.category)
    )
  )

  const filteredEnvironmentFiles = computed(() =>
    filterFilesByKeyword(audioFiles.value.filter((file) => file.category === 'environment'))
  )

  const filteredThemeFiles = computed(() =>
    filterFilesByKeyword(audioFiles.value.filter((file) => file.category === 'theme'))
  )

  // ========== 方法定义 ==========

  // 根据关键词过滤文件
  function filterFilesByKeyword(files) {
    if (!searchKeyword.value) return files

    const keyword = searchKeyword.value.toLowerCase()
    return files.filter((file) =>
      (file.original_name || file.filename).toLowerCase().includes(keyword)
    )
  }

  // 音频文件管理
  async function refreshAudioFiles() {
    loadingAudioFiles.value = true
    try {
      const response = await listAudioFiles()
      if (response.success) {
        audioFiles.value = response.files
      } else {
        message.error('获取音频文件列表失败')
      }
    } catch (error) {
      console.error('获取音频文件失败:', error)
      message.error('获取音频文件失败')
    } finally {
      loadingAudioFiles.value = false
    }
  }

  // 搜索处理
  function handleSearch(keyword) {
    searchKeyword.value = keyword
  }

  // 文件上传
  async function handleBeforeUpload(file, category) {
    try {
      const response = await uploadAudioFile(file, category)
      if (response.success) {
        message.success('文件上传成功')
        refreshAudioFiles()
      } else {
        message.error('文件上传失败')
      }
    } catch (error) {
      console.error('文件上传失败:', error)
      message.error('文件上传失败')
    }
    return false
  }

  // 文件选择
  function selectAudioFile(file) {
    console.log('选择音频文件:', file)
  }

  // 文件播放
  function playAudioFile(file) {
    if (isPlayingFile(file.id)) {
      stopAudioPlayback()
    } else {
      playFileAudio(file)
    }
  }

  function isPlayingFile(fileId) {
    return playingFileId.value === fileId
  }

  async function playFileAudio(file) {
    try {
      stopAudioPlayback()

      playingFileId.value = file.id

      // 创建音频元素
      currentAudio = new Audio()
      currentAudioId = Date.now().toString()
      currentAudio.audioId = currentAudioId

      // 设置音频源
      const fileUrl = `/api/v1/sound-editor/audio-files/download/${file.id}`
      currentAudio.src = fileUrl
      currentAudio.crossOrigin = 'anonymous'

      // 事件监听器
      const checkAudioId = (e) => e.target.audioId === currentAudioId

      currentAudio.addEventListener('ended', (e) => {
        if (!checkAudioId(e)) return
        stopAudioPlayback()
      })

      currentAudio.addEventListener('error', (e) => {
        if (!checkAudioId(e)) return
        console.error('音频播放错误:', e)
        stopAudioPlayback()
        message.error('音频播放失败')
      })

      await currentAudio.play()
    } catch (error) {
      console.error('播放音频失败:', error)
      stopAudioPlayback()
      message.error('播放音频失败')
    }
  }

  function stopAudioPlayback() {
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.currentTime = 0
      currentAudio.src = ''
      currentAudio = null
    }
    currentAudioId = 0
    playingFileId.value = null
  }

  // 文件删除
  async function handleDeleteAudioFile(file) {
    try {
      const response = await deleteAudioFile(file.id)
      if (response.success) {
        message.success('文件删除成功')
        refreshAudioFiles()
      } else {
        message.error('文件删除失败')
      }
    } catch (error) {
      console.error('文件删除失败:', error)
      message.error('文件删除失败')
    }
  }

  // 添加到项目
  function handleAddAudioToProject(file) {
    console.log('添加音频到项目:', file)
    // TODO: 实现添加到项目的逻辑
  }

  // 拖拽处理
  function handleDragStart(file, event) {
    draggedAudioFile.value = file
    isDragging.value = true

    // 设置拖拽数据
    event.dataTransfer.setData(
      'application/json',
      JSON.stringify({
        type: 'audio-file',
        file: file
      })
    )

    // 设置拖拽效果
    event.dataTransfer.effectAllowed = 'copy'

    // 添加拖拽样式
    event.target.classList.add('dragging')

    console.log('开始拖拽音频文件:', file.original_name || file.filename)
  }

  function handleDragEnd(event) {
    isDragging.value = false
    draggedAudioFile.value = null

    // 移除拖拽样式
    event.target.classList.remove('dragging')

    console.log('拖拽结束')
  }

  // 播放控制（完整版本）
  async function togglePlay() {
    // 如果正在加载，不处理
    if (isLoadingPreview.value) {
      console.log('正在加载预览，忽略播放切换')
      return
    }

    if (isPlaying.value) {
      pausePlayback()
    } else {
      // 重新开始播放（每次都生成新的预览音频）
      await startPlayback()
    }
  }

  async function startPlayback() {
    try {
      // 如果已在加载中，避免重复请求
      if (isLoadingPreview.value) {
        console.log('预览音频正在加载中，跳过重复请求')
        return
      }

      isLoadingPreview.value = true

      // 检查是否有项目
      if (!currentProject.project.id) {
        message.warning('请先创建或加载项目')
        isLoadingPreview.value = false
        return
      }

      // 计算预览时长
      const totalDuration = currentProject.project.totalDuration || 60 // 默认60秒，会根据内容自动扩展
      const remainingDuration = totalDuration - currentTime.value
      const previewDuration = Math.max(1.0, remainingDuration) // 至少1秒，不设上限

      console.log('预览播放参数:', {
        projectId: currentProject.project.id,
        currentTime: currentTime.value,
        totalDuration,
        previewDuration
      })

      // 生成预览音频
      const previewResult = await generatePreviewAudio(
        currentProject.project.id,
        currentTime.value,
        previewDuration
      )

      if (!previewResult.success) {
        message.error('生成预览音频失败: ' + (previewResult.message || '未知错误'))
        isLoadingPreview.value = false
        return
      }

      console.log('预览音频生成成功:', previewResult)

      // 停止当前播放并清理旧的音频元素
      if (previewAudioElement) {
        previewAudioElement.pause()
        previewAudioElement.src = ''
        previewAudioElement = null
      }

      // 创建新的音频元素
      currentAudioId++ // 增加音频ID
      const audioId = currentAudioId
      currentPreviewFile = previewResult.preview_file_id // 修复字段名
      const audioUrl = previewResult.preview_url // 直接使用后端返回的URL

      console.log('创建预览音频元素:', {
        audioId: audioId,
        previewFile: currentPreviewFile,
        audioUrl: audioUrl
      })

      previewAudioElement = new Audio()
      previewAudioElement.audioId = audioId // 为音频元素分配ID
      previewAudioElement.crossOrigin = 'anonymous'
      previewAudioElement.preload = 'auto'

      // 设置音频事件监听
      previewAudioElement.addEventListener('canplay', (e) => {
        if (e.target.audioId !== currentAudioId) return // 只处理当前音频元素的事件
        if (!previewAudioElement) return
        console.log('预览音频可以播放')

        // 重置加载状态
        isLoadingPreview.value = false
        isPlaying.value = true

        // 尝试播放音频
        const playPromise = previewAudioElement.play()

        if (playPromise !== undefined) {
          playPromise
            .then(() => {
              console.log('预览音频播放成功')
              // 开始更新播放时间
              const startTime = currentTime.value // 记录播放开始时的项目时间
              playInterval = setInterval(() => {
                if (previewAudioElement && !previewAudioElement.paused) {
                  // 计算项目中的绝对时间：开始时间 + 音频播放时间
                  const newTime = startTime + previewAudioElement.currentTime
                  const projectDuration = currentProject.project.totalDuration || 0

                  // 检查是否超过项目总时长
                  if (newTime >= projectDuration && projectDuration > 0) {
                    console.log('播放时间到达项目结尾，自动停止播放')
                    stopPlayback()
                    return
                  }

                  currentTime.value = newTime
                }
              }, 100)
            })
            .catch((error) => {
              console.error('预览音频播放失败:', error)

              if (error.name === 'NotAllowedError') {
                message.warning('浏览器需要用户交互才能播放音频，请再次点击预览按钮')
              } else {
                message.error('音频播放失败: ' + error.message)
              }

              // 播放失败时重置状态
              isLoadingPreview.value = false
              isPlaying.value = false
            })
        }
      })

      previewAudioElement.addEventListener('ended', (e) => {
        if (e.target.audioId !== currentAudioId) return // 只处理当前音频元素的事件
        if (!previewAudioElement) return
        console.log('预览音频播放结束')
        stopPlayback()
      })

      previewAudioElement.addEventListener('error', (e) => {
        if (e.target.audioId !== currentAudioId) return // 只处理当前音频元素的事件
        if (!previewAudioElement) return
        const error = e.target.error
        console.error('预览音频播放错误:', e, error)

        let errorMessage = '音频播放失败'
        if (error) {
          switch (error.code) {
            case 1: // MEDIA_ERR_ABORTED
              errorMessage = '音频播放被中止'
              break
            case 2: // MEDIA_ERR_NETWORK
              errorMessage = '网络错误导致音频播放失败'
              break
            case 3: // MEDIA_ERR_DECODE
              errorMessage = '音频解码失败'
              break
            case 4: // MEDIA_ERR_SRC_NOT_SUPPORTED
              errorMessage = '音频格式不支持或文件损坏'
              break
            default:
              errorMessage = '音频播放失败: ' + (error.message || '未知错误')
          }
        }

        message.error(errorMessage)
        isLoadingPreview.value = false
        isPlaying.value = false

        // 清理音频元素但不删除文件（可能还需要重试）
        if (previewAudioElement) {
          previewAudioElement.src = ''
          previewAudioElement.load()
          previewAudioElement = null
        }
      })

      // 设置音频源并开始加载
      previewAudioElement.src = audioUrl
      previewAudioElement.load()

      // 设置超时保护，如果10秒内没有触发canplay事件，则重置状态
      setTimeout(() => {
        if (isLoadingPreview.value) {
          console.warn('音频加载超时，重置加载状态')
          isLoadingPreview.value = false
          message.warning('音频加载超时，请重试')
        }
      }, 10000)
    } catch (error) {
      console.error('启动播放失败:', error)
      message.error('启动播放失败')
      isLoadingPreview.value = false
    }
  }

  // 兼容旧接口
  async function playPreview() {
    await startPlayback()
  }

  async function playPreviewAudio(previewFile) {
    try {
      stopPreviewAudio()

      currentAudio = new Audio()
      currentAudioId = Date.now().toString()
      currentAudio.audioId = currentAudioId

      currentAudio.src = `/api/v1/multitrack/preview/download/${previewFile}`

      const checkAudioId = (e) => e.target.audioId === currentAudioId

      currentAudio.addEventListener('canplay', (e) => {
        if (!checkAudioId(e)) return
        isLoadingPreview.value = false
      })

      // 使用setInterval实现平滑的时间更新，而不是依赖timeupdate事件
      // 记录播放开始时的项目时间
      const startTime = currentTime.value
      playInterval = setInterval(() => {
        if (currentAudio && !currentAudio.paused && !currentAudio.ended) {
          // 计算项目中的绝对时间：开始时间 + 音频播放时间
          const newTime = startTime + currentAudio.currentTime
          const projectDuration = currentProject.project.totalDuration || 0

          // 检查是否超过项目总时长
          if (newTime >= projectDuration && projectDuration > 0) {
            console.log('播放时间到达项目结尾，自动停止播放')
            stopPlayback()
            return
          }

          currentTime.value = newTime
        }
      }, 50) // 50ms间隔，比旧版本100ms更加流畅

      currentAudio.addEventListener('ended', (e) => {
        if (!checkAudioId(e)) return
        stopPlayback()
      })

      currentAudio.addEventListener('error', (e) => {
        if (!checkAudioId(e)) return
        console.error('预览播放错误:', e)
        stopPlayback()
        message.error('预览播放失败')
      })

      await currentAudio.play()
      isPlaying.value = true
    } catch (error) {
      console.error('播放预览音频失败:', error)
      isLoadingPreview.value = false
      message.error('播放预览失败')
    }
  }

  function pausePlayback() {
    isPlaying.value = false
    if (previewAudioElement) {
      previewAudioElement.pause()
      // 不重置currentTime，保持当前播放位置
    }
    if (playInterval) {
      clearInterval(playInterval)
      playInterval = null
    }
  }

  async function stopPlayback() {
    isPlaying.value = false
    currentTime.value = 0

    if (previewAudioElement) {
      previewAudioElement.pause()
      previewAudioElement.currentTime = 0
      previewAudioElement.src = ''
      previewAudioElement.load()
      previewAudioElement = null
    }

    if (playInterval) {
      clearInterval(playInterval)
      playInterval = null
    }

    // 删除临时预览文件
    if (currentPreviewFile) {
      try {
        // 添加preview_前缀，因为后端生成的文件名是preview_{uuid}.wav
        const previewFileName = `preview_${currentPreviewFile}.wav`
        const result = await deletePreviewFile(previewFileName)
        if (result.success) {
          console.log('预览文件已删除:', previewFileName)
        } else {
          console.warn('删除预览文件失败:', result.error)
        }
      } catch (error) {
        console.error('删除预览文件出错:', error)
      }
    }

    currentPreviewFile = null
  }

  // 兼容旧接口
  async function pausePreview() {
    pausePlayback()
  }

  function stopPreviewAudio() {
    stopPlayback()
  }

  // 项目管理
  function handleUpdateProject(updates) {
    Object.assign(currentProject.project, updates)
  }

  function updateProjectTitle(newTitle) {
    currentProject.project.title = newTitle
  }

  function updateProjectDescription(newDescription) {
    currentProject.project.description = newDescription
  }

  // 片段管理
  function updateSelectedClip(updates) {
    const clip = selectedClip.value
    if (!clip) return

    // 在所有音轨中找到对应的片段并更新
    for (const track of currentProject.tracks) {
      const targetClip = track.clips.find((c) => c.id === clip.id)
      if (targetClip) {
        Object.assign(targetClip, updates)
        updateProjectDuration()
        autoSaveProject()
        break
      }
    }
  }

  function getTrackTypeLabel(type) {
    const labels = {
      dialogue: '角色对话',
      environment: '环境音效',
      background: '背景音乐'
    }
    return labels[type] || type
  }

  // 时间轴控制
  function handleZoomChange(newZoom) {
    zoomLevel.value = newZoom
  }

  function handleTimelineScroll(scrollLeft) {
    // 同步时间轴滚动
  }

  // 音轨和片段管理
  function updateTrack(trackId, updates) {
    const track = currentProject.tracks.find((t) => t.id === trackId)
    if (track) {
      Object.assign(track, updates)
      updateProjectDuration()
    }
  }

  function updateClip(trackId, clipId, updates) {
    const track = currentProject.tracks.find((t) => t.id === trackId)
    if (track) {
      const clip = track.clips.find((c) => c.id === clipId)
      if (clip) {
        Object.assign(clip, updates)
        updateProjectDuration()
        autoSaveProject()
      }
    }
  }

  function deleteClip(trackId, clipId) {
    const track = currentProject.tracks.find((t) => t.id === trackId)
    if (track) {
      const index = track.clips.findIndex((c) => c.id === clipId)
      if (index !== -1) {
        track.clips.splice(index, 1)
        updateProjectDuration()
        autoSaveProject()
      }
    }
  }

  function addClip(trackId, clipData) {
    const track = currentProject.tracks.find((t) => t.id === trackId)
    if (track) {
      const newClip = {
        id: generateId('clip'),
        fileId: clipData.filePath || '', // 修复字段名：filePath -> fileId
        filename: clipData.name || '新音频片段', // 修复字段名：name -> filename
        startTime: clipData.startTime || 0,
        duration: clipData.duration || 3,
        volume: 1.0,
        offset: 0.0, // 添加offset字段
        fadeIn: 0.1,
        fadeOut: 0.1
      }
      track.clips.push(newClip)
      updateProjectDuration()
      autoSaveProject()
    }
  }

  function updateProjectDuration() {
    const calculatedDuration = calculateProjectDuration(currentProject)
    // 设置最小时长为60秒，并添加30秒缓冲
    currentProject.project.totalDuration = Math.max(60, calculatedDuration + 30)
    console.log('项目时长已更新:', currentProject.project.totalDuration, '秒')
  }

  function handleExclusiveSelect(trackId, clipId) {
    // 清除所有音频片段的选中状态
    currentProject.tracks.forEach((track) => {
      track.clips.forEach((clip) => {
        clip.selected = false
      })
    })

    // 选中指定的音频片段
    const track = currentProject.tracks.find((t) => t.id === trackId)
    if (track) {
      const clip = track.clips.find((c) => c.id === clipId)
      if (clip) {
        clip.selected = true
      }
    }
  }

  function clearSelectedClip() {
    currentProject.tracks.forEach((track) => {
      track.clips.forEach((clip) => {
        clip.selected = false
      })
    })
  }

  // 对话框事件处理
  async function handleProjectCreated(projectData) {
    try {
      const newProject = createEmptyProject(projectData.title)
      newProject.project.description = projectData.description
      newProject.project.author = projectData.author

      const result = await createProject(newProject)
      if (result.success) {
        // 正确地更新reactive对象的每个属性，保持响应性
        Object.assign(currentProject.project, result.data.project)
        currentProject.tracks.splice(0, currentProject.tracks.length, ...result.data.tracks)
        currentProject.markers = result.data.markers || []
        // 保存到本地存储
        saveCurrentProjectToLocalStorage()
        // 发送项目变化事件
        emit('project-change', currentProject.project)
        message.success('项目创建成功')
        console.log('项目创建成功，当前项目:', currentProject)
        // 关闭创建对话框并重置表单
        showCreateProject.value = false
        resetCreateForm()
      }
    } catch (error) {
      console.error('创建项目失败:', error)
      message.error('创建项目失败')
    }
  }

  // 表单重置功能
  function resetCreateForm() {
    createForm.title = ''
    createForm.description = ''
    createForm.author = 'AI-Sound'
  }

  function resetImportForm() {
    importForm.value = {
      type: 'dialogue',
      data: null
    }
  }

  async function handleProjectSelected(projectId) {
    try {
      const result = await loadProject(projectId)
      if (result.success) {
        // 正确地更新reactive对象的每个属性，保持响应性
        Object.assign(currentProject.project, result.data.project)
        currentProject.tracks.splice(0, currentProject.tracks.length, ...result.data.tracks)
        currentProject.markers = result.data.markers || []
        showProjectList.value = false
        // 保存到本地存储
        saveCurrentProjectToLocalStorage()
        // 发送项目变化事件
        emit('project-change', currentProject.project)
        message.success('项目加载成功')
        console.log('项目加载成功，当前项目:', currentProject)
      }
    } catch (error) {
      console.error('加载项目失败:', error)
      message.error('加载项目失败')
    }
  }

  async function handleDeleteProject(projectId) {
    try {
      const result = await deleteProject(projectId)
      if (result.success) {
        message.success('项目删除成功')
        // 如果删除的是当前项目，重置编辑器
        if (currentProject.project.id === projectId) {
          Object.assign(currentProject, createEmptyProject())
          // 清除本地缓存
          clearProjectCache()
        }
      }
    } catch (error) {
      console.error('删除项目失败:', error)
      message.error('删除项目失败')
    }
  }

  async function handleImportSuccess(importData) {
    try {
      // 格式化转换请求数据
      const conversionData = formatConversionData(importData)

      const result = await convertToStandardFormat(conversionData)
      if (result.success) {
        // 正确地更新reactive对象的每个属性，保持响应性
        Object.assign(currentProject.project, result.data.project)
        currentProject.tracks.splice(0, currentProject.tracks.length, ...result.data.tracks)
        currentProject.markers = result.data.markers || []
        // 发送项目变化事件
        emit('project-change', currentProject.project)
        message.success('JSON导入成功')
        console.log('JSON导入成功，当前项目:', currentProject)
      }
    } catch (error) {
      console.error('JSON导入失败:', error)
      message.error('JSON导入失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 手动保存项目
  async function saveCurrentProject() {
    const projectId = currentProject.project?.id

    if (!projectId || typeof projectId !== 'string' || projectId.trim() === '') {
      message.error('无效的项目，请先创建项目')
      return
    }

    try {
      // 更新总时长
      currentProject.project.totalDuration = calculateProjectDuration(currentProject)

      const result = await saveProject(projectId, currentProject)
      if (result.success) {
        message.success('项目保存成功')
      } else {
        message.error('项目保存失败: ' + (result.message || '未知错误'))
      }
    } catch (error) {
      console.error('保存项目失败:', error)
      if (error.response?.status === 422) {
        message.error('项目数据格式错误，请检查项目配置')
      } else {
        message.error('保存项目失败: ' + (error.response?.data?.detail || error.message))
      }
    }
  }

  // 音频导出（完整流程）
  async function exportAudio() {
    if (!currentProject.project.id) return

    try {
      exportLoading.value = true
      const result = await exportProject(currentProject.project.id)

      if (result.success) {
        currentExportTaskId.value = result.export_task_id
        exportStatus.value = 'processing'
        exportMessage.value = result.message
        showExportProgress.value = true

        // 开始轮询导出状态
        startExportPolling()
      }
    } catch (error) {
      console.error('导出失败:', error)
      message.error('导出失败')
    } finally {
      exportLoading.value = false
    }
  }

  function startExportPolling() {
    const pollInterval = setInterval(async () => {
      try {
        const status = await getExportStatus(currentExportTaskId.value)
        exportStatus.value = status.status
        exportMessage.value = status.message

        if (status.status === 'completed' || status.status === 'failed') {
          clearInterval(pollInterval)
        }
      } catch (error) {
        console.error('查询导出状态失败:', error)
        clearInterval(pollInterval)
      }
    }, 2000)
  }

  async function downloadExportedFile() {
    try {
      await downloadExportedAudio(currentExportTaskId.value)
      message.success('文件下载已开始')
    } catch (error) {
      console.error('下载失败:', error)
      message.error('下载失败')
    }
  }

  // 导出项目（兼容接口）
  async function exportCurrentProject() {
    await exportAudio()
  }

  // 更新项目信息
  function updateProjectInfo(updates) {
    Object.assign(currentProject.project, updates)
    // 触发自动保存
    autoSaveProject()
  }

  // 格式化转换数据
  function formatConversionData(importData) {
    const conversionRequest = {
      dialogueData: {},
      environmentData: null,
      backgroundMusic: null,
      projectInfo: null
    }

    if (importData.type === 'dialogue' && importData.data) {
      conversionRequest.dialogueData = importData.data
      conversionRequest.projectInfo = {
        title: importData.data.title || '导入的项目',
        description: importData.data.description || '',
        author: 'AI-Sound'
      }
    }

    return conversionRequest
  }

  // 自动保存项目到服务器（防抖处理）
  function autoSaveProject() {
    if (!currentProject.project.id) return

    // 清除之前的定时器
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer)
    }

    // 设置延迟保存，避免频繁请求
    autoSaveTimer = setTimeout(async () => {
      try {
        // 更新总时长
        currentProject.project.totalDuration = calculateProjectDuration(currentProject)

        const result = await saveProject(currentProject.project.id, currentProject)
        if (result.success) {
          console.log('项目已自动保存到服务器:', currentProject.project.title)
          // 同时保存到本地缓存
          saveCurrentProjectToLocalStorage()
        }
      } catch (error) {
        console.warn('自动保存项目失败:', error)
        if (error.response?.status === 422) {
          console.error('422错误详情:', error.response.data)
        }
      }
    }, 1000) // 1秒延迟
  }

  // 项目持久化
  function saveCurrentProjectToLocalStorage() {
    if (currentProject.project.id) {
      localStorage.setItem('sound-edit-current-project-id', currentProject.project.id)
      localStorage.setItem('sound-edit-current-project-data', JSON.stringify(currentProject))
      console.log('项目已自动保存到本地缓存:', currentProject.project.title)
    }
  }

  function clearProjectCache() {
    localStorage.removeItem('sound-edit-current-project-id')
    localStorage.removeItem('sound-edit-current-project-data')
    message.info('本地项目缓存已清除')
  }

  async function loadProjectFromLocalStorage() {
    try {
      const savedProjectId = localStorage.getItem('sound-edit-current-project-id')
      const savedProjectData = localStorage.getItem('sound-edit-current-project-data')

      if (savedProjectId && savedProjectData) {
        // 尝试从服务器加载最新的项目数据
        try {
          const result = await loadProject(savedProjectId)
          if (result.success) {
            // 正确地更新reactive对象的每个属性，保持响应性
            Object.assign(currentProject.project, result.data.project)
            currentProject.tracks.splice(0, currentProject.tracks.length, ...result.data.tracks)
            currentProject.markers = result.data.markers || []
            // 发送项目变化事件
            emit('project-change', currentProject.project)
            console.log('从服务器恢复项目:', currentProject.project.title)
            message.success('项目已从服务器恢复')
            return
          }
        } catch (error) {
          console.warn('从服务器加载项目失败，使用本地缓存:', error)
        }

        // 如果服务器加载失败，使用本地缓存
        try {
          const localProject = JSON.parse(savedProjectData)
          Object.assign(currentProject.project, localProject.project)
          currentProject.tracks.splice(0, currentProject.tracks.length, ...localProject.tracks)
          currentProject.markers = localProject.markers || []
          // 发送项目变化事件
          emit('project-change', currentProject.project)
          console.log('从本地缓存恢复项目:', currentProject.project.title)
          message.info('项目已从本地缓存恢复')
        } catch (parseError) {
          console.error('解析本地项目数据失败:', parseError)
          clearProjectCache()
        }
      }
    } catch (error) {
      console.error('加载本地项目失败:', error)
    }
  }

  // 格式化工具函数
  function formatDuration(seconds) {
    return formatTime(seconds)
  }

  // 全局键盘事件处理
  function handleKeyDown(event) {
    // 检查是否在输入框中
    if (event.target.tagName === 'INPUT' || event.target.tagName === 'TEXTAREA') {
      return
    }

    switch (event.key) {
      case ' ':
        // 空格键：播放/暂停
        if (currentProject.project.id) {
          togglePlay()
          event.preventDefault()
        }
        break
      case 'Delete':
      case 'Backspace':
        handleDeleteSelectedClips()
        event.preventDefault()
        break
      case 'Escape':
        clearAllSelections()
        event.preventDefault()
        break
      case '=':
      case '+':
        // 加号键：放大
        if (event.ctrlKey || event.metaKey) {
          zoomIn()
          event.preventDefault()
        }
        break
      case '-':
      case '_':
        // 减号键：缩小
        if (event.ctrlKey || event.metaKey) {
          zoomOut()
          event.preventDefault()
        }
        break
      case '0':
        // Ctrl+0：重置缩放
        if (event.ctrlKey || event.metaKey) {
          resetZoom()
          event.preventDefault()
        }
        break
      case 'f':
      case 'F':
        // Ctrl+F：适合窗口
        if (event.ctrlKey || event.metaKey) {
          fitToWindow()
          event.preventDefault()
        }
        break
    }
  }

  function handleGlobalClick(event) {
    // 如果点击的不是音频片段相关元素和项目信息面板，清除所有选中状态
    if (
      !event.target.closest('.audio-clip') &&
      !event.target.closest('.ant-modal') &&
      !event.target.closest('.project-panel') &&
      !event.target.closest('.clip-details')
    ) {
      clearAllSelections()
    }
  }

  function handleDeleteSelectedClips() {
    const selectedClips = []

    // 收集所有选中的音频片段
    currentProject.tracks.forEach((track) => {
      track.clips.forEach((clip) => {
        if (clip.selected) {
          selectedClips.push({ trackId: track.id, clipId: clip.id, clipName: clip.filename })
        }
      })
    })

    if (selectedClips.length === 0) {
      message.info('请先选择要删除的音频片段')
      return
    }

    // 显示确认对话框
    Modal.confirm({
      title: '确认删除',
      content: `确定要删除 ${selectedClips.length} 个音频片段吗？`,
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk() {
        selectedClips.forEach(({ trackId, clipId }) => {
          deleteClip(trackId, clipId)
        })
        message.success(`已删除 ${selectedClips.length} 个音频片段`)
      }
    })
  }

  function clearAllSelections() {
    currentProject.tracks.forEach((track) => {
      track.clips.forEach((clip) => {
        if (clip.selected) {
          clip.selected = false
        }
      })
    })
  }

  // 缩放功能
  function zoomIn() {
    const newZoom = Math.min(maxZoom.value, zoomLevel.value * 1.5)
    if (newZoom !== zoomLevel.value) {
      zoomLevel.value = newZoom
      message.success(`放大到 ${Math.round(newZoom * 100)}%`)
    }
  }

  function zoomOut() {
    const newZoom = Math.max(minZoom.value, zoomLevel.value / 1.5)
    if (newZoom !== zoomLevel.value) {
      zoomLevel.value = newZoom
      message.success(`缩小到 ${Math.round(newZoom * 100)}%`)
    }
  }

  function resetZoom() {
    zoomLevel.value = 1
    message.success('缩放重置到 100%')
  }

  // 适合窗口：自动调整缩放以显示所有内容
  function fitToWindow() {
    const contentDuration = Math.max(
      calculateContentDuration.value,
      currentProject.project.totalDuration || 60
    )

    // 获取实际可用宽度
    // 假设总宽度1400px，减去左侧面板150px，减去滚动条和边距50px，剩余约1200px
    const availableWidth = 1200
    const targetPixelsPerSecond = availableWidth / contentDuration
    const targetZoom = targetPixelsPerSecond / basePixelsPerSecond.value

    // 如果目标缩放小于最小值，调整最小缩放限制
    if (targetZoom < minZoom.value) {
      // 对于长时间音频，允许更小的缩放
      minZoom.value = Math.max(0.1, targetZoom * 0.9) // 最小不低于0.1
    }

    // 确保在缩放范围内
    const clampedZoom = Math.max(minZoom.value, Math.min(maxZoom.value, targetZoom))
    zoomLevel.value = clampedZoom

    console.log(
      `适配窗口计算: 内容时长=${contentDuration}s, 可用宽度=${availableWidth}px, 目标缩放=${Math.round(targetZoom * 100)}%, 实际缩放=${Math.round(clampedZoom * 100)}%`
    )
    message.success(
      `适合窗口：${Math.round(clampedZoom * 100)}% (${Math.round(contentDuration)}秒音频)`
    )
  }

  // ========== 生命周期 ==========
  onMounted(async () => {
    // 获取路由参数
    const route = useRoute()
    const projectId = route.params.projectId

    // 初始化音频文件列表
    await refreshAudioFiles()

    // 如果URL中有项目ID，优先加载该项目
    if (projectId && projectId !== 'new') {
      console.log('从URL加载项目:', projectId)
      await handleProjectSelected(projectId)
    } else {
      // 否则尝试从本地存储恢复项目
      await loadProjectFromLocalStorage()
    }

    // 添加全局键盘事件监听
    document.addEventListener('keydown', handleKeyDown)
    // 添加全局点击事件监听
    document.addEventListener('click', handleGlobalClick)
  })

  // 监听路由变化，重新加载项目
  const route = useRoute()
  watch(
    () => route.params.projectId,
    async (newProjectId) => {
      if (newProjectId && newProjectId !== 'new') {
        console.log('路由变化，加载新项目:', newProjectId)
        await handleProjectSelected(newProjectId)
      }
    }
  )

  onUnmounted(() => {
    // 清理音频播放
    stopAudioPlayback()
    stopPreviewAudio()

    // 清理所有定时器
    if (autoSaveTimer) {
      clearTimeout(autoSaveTimer)
      autoSaveTimer = null
    }
    if (playInterval) {
      clearInterval(playInterval)
      playInterval = null
    }

    // 确保音频元素完全清理
    if (currentAudio) {
      currentAudio.pause()
      currentAudio.src = ''
      currentAudio.load()
      currentAudio = null
    }
    
    if (previewAudioElement) {
      previewAudioElement.pause()
      previewAudioElement.src = ''
      previewAudioElement.load()
      previewAudioElement = null
    }

    // 清理临时预览文件
    if (currentPreviewFile) {
      currentPreviewFile = null
    }

    // 移除全局键盘事件监听
    document.removeEventListener('keydown', handleKeyDown)
    // 移除全局点击事件监听
    document.removeEventListener('click', handleGlobalClick)
  })
</script>

<style scoped>
  .multitrack-editor {
    background: #1a1a1a;
    height: 100vh;
    display: flex;
    flex-direction: column;
    color: #fff;
  }

  .editor-container {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #1a1a1a;
  }

  /* 上半部分：三栏布局 */
  .top-section {
    height: calc(50% - 8px);
    display: flex;
    gap: 16px;
    padding: 16px;
  }

  .bottom-section {
    flex: 1;
    padding: 0 16px 16px;
    overflow: hidden;
  }

  .empty-state {
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: #1e1e1e;
    border-radius: 8px;
    border: 1px solid #333;
  }

  .empty-state :deep(.ant-empty) {
    color: #999;
  }
</style>
