<template>
  <div class="audio-video-editor" :class="{ 'fullscreen-mode': isFullscreen }" ref="editorContainer">
    <!-- 顶部工具栏 -->
    <div class="editor-toolbar" v-show="!isFullscreen || showFloatingControls">
      <div class="toolbar-left">
        <h2 class="project-title">{{ project?.name || '新建项目' }}</h2>
      </div>
      
      <div class="toolbar-right">
        <a-button @click="handleSave" :loading="saving" size="small">
          <SaveOutlined />
          保存
        </a-button>
        
        <a-button type="primary" @click="handleExport" size="small">
          <ExportOutlined />
            导出
          </a-button>
        
        <a-button @click="toggleFullscreen" size="small" :title="isFullscreen ? '退出全屏 (ESC)' : '进入全屏 (F11)'">
          <FullscreenExitOutlined v-if="isFullscreen" />
          <FullscreenOutlined v-else />
          {{ isFullscreen ? '退出全屏' : '全屏' }}
        </a-button>
      </div>
    </div>

    <!-- 主编辑区域 - 剪映风格布局 -->
    <div class="editor-main">
      <!-- 上半部分：三栏布局 -->
      <div class="workspace-top">
        <!-- 左栏：素材库 -->
        <div class="workspace-left" v-show="showResourcePanel">
          <MaterialLibrary
            :imported-audio-files="importedAudioFiles"
            @import-audio="showImportModal"
            @preview-audio="previewAudio"
            @material-drag-start="handleMaterialDragStart"
          />
          </div>
          
        <!-- 中栏：预览面板 -->
        <div class="workspace-center">
          <PreviewPanel
            :audioData="selectedAudioData"
            :tracks="tracks"
            :totalDuration="totalDuration"
            :externalIsPlaying="isPlaying"
            :externalCurrentTime="currentTime"
            @pause="pauseAudio"
            @stop="handleStop"
            @seek="seekTo"
            @togglePlay="handlePlay"
            @volumeChange="setVolume"
            @importAudio="showImportModal"
          />
            </div>
            
        <!-- 右栏：属性面板 -->
        <div class="workspace-right">
          <PropertiesPanel
            :selected-audio-clip="selectedAudioClip"
            :selected-track="selectedTrack"
            :project-settings="{ name: projectName, sampleRate, bitDepth }"
            :project-stats="{ duration: totalDuration, trackCount: tracks.length }"
            @update-clip-property="handleUpdateClipProperty"
            @update-track-property="handleUpdateTrackProperty"
            @update-project-property="handleUpdateProjectProperty"
          />
          </div>
        </div>
        
      <!-- 下半部分：轨道区域 -->
      <div class="workspace-bottom">
        <TracksArea
          :tracks="tracks"
          :selected-track="selectedTrack"
          :selected-segment="selectedSegment"
          :current-time="currentTime"
          :total-duration="totalDuration"
          :master-volume="masterVolume"
          :zoom-level="zoomLevel"
          :is-playing="isPlaying"
          @select-track="selectTrack"
          @select-segment="selectSegment"
          @toggle-track-mute="toggleTrackMute"
          @toggle-track-visibility="toggleTrackVisibility"
          @toggle-track-lock="toggleTrackLock"
          @add-track="addNewTrack"
          @timeline-drop="handleTimelineDrop"
          @track-drop="handleTrackDrop"
          @update-master-volume="updateMasterVolume"
          @update-zoom-level="updateZoomLevel"
          @import-audio="showImportModal"
          @segment-waveform-ready="onSegmentWaveformReady"
          @segment-updated="handleSegmentUpdated"
          @seek="seekTo"
          @copy-segment="handleCopySegment"
          @cut-segment="handleCutSegment"
          @delete-segment="handleDeleteSegment"
          @split-segment="handleSplitSegment"
          @apply-fade-effect="handleApplyFadeEffect"
          @undo="handleUndo"
          @redo="handleRedo"
          @duplicate-segment="handleDuplicateSegment"
          @normalize-volume="handleNormalizeVolume"
          @reverse-segment="handleReverseSegment"
          @export-segment="handleExportSegment"
          @delete-empty-track="handleDeleteEmptyTrack"
        />
        </div>
      </div>

    <!-- 全屏模式浮动控制栏 -->
    <transition name="fade">
      <div v-show="isFullscreen && showFloatingControls" class="floating-controls" 
           @mouseenter="clearAutoHideTimer" @mouseleave="startAutoHideTimer">
        <!-- 资源库切换按钮 -->
        <div class="floating-left">
          <a-button size="small" type="text" @click="toggleResourcePanel" 
                   :title="showResourcePanel ? '隐藏资源库 (Tab)' : '显示资源库 (Tab)'">
            <MenuOutlined />
            {{ showResourcePanel ? '隐藏资源库' : '显示资源库' }}
            </a-button>
        </div>
        
        <!-- 播放控制 -->
        <div class="floating-center">
          <div class="playback-controls">
            <a-button type="text" @click="handleStop" title="停止 (Space)">
              <BorderOutlined />
                </a-button>
                
            <a-button type="primary" @click="handlePlay" :loading="playbackLoading" 
                     :title="isPlaying ? '暂停 (Space)' : '播放 (Space)'">
              <PauseCircleOutlined v-if="isPlaying" />
              <PlayCircleOutlined v-else />
            </a-button>
            </div>
            
        <!-- 时间显示 -->
        <div class="time-display">
          {{ formatTime(currentTime) }} / {{ formatTime(totalDuration) }}
            </div>
          </div>
          
      <!-- 右侧控制 -->
      <div class="floating-right">
        <a-button size="small" type="text" @click="toggleFullscreen" title="退出全屏 (ESC)">
          <FullscreenExitOutlined />
          退出全屏
      </a-button>
          </div>
        </div>
</transition>
    </div>

<!-- 导入音频文件模态框 -->
<ImportAudioModal
  v-model:visible="importModalVisible"
  @import-success="handleImportSuccess"
/>

<!-- 智能编辑助手 -->
<!-- <SmartEditingAssistant
  v-model:visible="smartAssistantVisible"
  :project="project"
  :tracks="tracks"
  @project-imported="onProjectImported"
  @jump-to-time="seekTo"
/> -->
          </template>

<script>
import { ref, computed, onMounted, onUnmounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { 
  ArrowLeftOutlined, PlayCircleOutlined, PauseCircleOutlined, 
  BorderOutlined, SaveOutlined, ExportOutlined, DownOutlined,
  PlusOutlined, SoundOutlined, CustomerServiceOutlined, 
  AudioOutlined, ThunderboltOutlined, StarOutlined,
  MenuOutlined, FullscreenExitOutlined, FullscreenOutlined, MoreOutlined
} from '@ant-design/icons-vue'
import ResourceLibrary from '@/components/ResourceLibrary.vue'
import PreviewPanel from '@/components/PreviewPanel.vue'
import CompositionInfo from '@/components/CompositionInfo.vue'
import WaveformViewer from '@/components/WaveformViewer.vue'
import MaterialLibrary from '@/components/audio-editor/MaterialLibrary.vue'
import PropertiesPanel from '@/components/audio-editor/PropertiesPanel.vue'
import TracksControlPanel from '@/components/audio-editor/TracksControlPanel.vue'
import TimelineViewer from '@/components/audio-editor/TimelineViewer.vue'
import TracksArea from '@/components/audio-editor/TracksArea.vue'
import ImportAudioModal from '@/components/audio-editor/ImportAudioModal.vue'
// import SmartEditingAssistant from '@/components/SmartEditingAssistant.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { useUndoRedo } from '@/composables/useUndoRedo'
import { useAutoSave } from '@/composables/useAutoSave'
import api from '@/api'

export default {
  name: 'AudioVideoEditor',
  components: {
    ArrowLeftOutlined, PlayCircleOutlined, PauseCircleOutlined,
    BorderOutlined, SaveOutlined, ExportOutlined, DownOutlined,
    PlusOutlined, SoundOutlined, CustomerServiceOutlined,
    AudioOutlined, ThunderboltOutlined, StarOutlined,
    MenuOutlined, FullscreenExitOutlined, FullscreenOutlined, MoreOutlined,
    ResourceLibrary, PreviewPanel, CompositionInfo,
    WaveformViewer, MaterialLibrary, PropertiesPanel,
    TracksControlPanel, TimelineViewer, TracksArea,
    ImportAudioModal
    // SmartEditingAssistant
  },
  setup() {
const route = useRoute()
const router = useRouter()

        // 响应式数据
const project = ref(null)
const tracks = ref([])
const selectedTrack = ref(null)
const selectedSegment = ref(null)
    const selectedAudioData = ref(null)
    const selectedAudioClip = ref(null) // 选中的音频片段
    
    // 项目设置
    const projectName = ref('新建项目')
    const sampleRate = ref('48000')
    const bitDepth = ref('24')

// 播放控制
const isPlaying = ref(false)
const playbackLoading = ref(false)
const currentTime = ref(0)
const totalDuration = ref(300) // 默认5分钟

// 编辑器状态
const saving = ref(false)
    const timelineWidth = ref(800)

    // UI控制
    const isFullscreen = ref(false)
    const showResourcePanel = ref(true)
    const showFloatingControls = ref(true)
    const autoHideControlsTimer = ref(null)
    // const smartAssistantVisible = ref(false)
    
    // 素材库标签
    const activeMaterialTab = ref('voice')
    const materialTabs = ref([
      { key: 'voice', name: '角色音' },
      { key: 'music', name: '背景音乐' },
      { key: 'environment', name: '环境音' }
    ])

    // 导入相关
const importModalVisible = ref(false)

const importedAudioFiles = ref([]) // 存储导入的音频文件，显示在素材库中

    // 高级功能状态
    const waveformReady = ref(false)
    const selectedRegion = ref(null)
    const zoomLevel = ref(1)
    const currentAudioUrl = ref('')
    const masterVolume = ref(0.8) // 主音量控制

    // DOM引用
    const editorContainer = ref(null)
    const waveformViewerRef = ref(null)

    // 初始化高级功能
const undoRedo = useUndoRedo({
  maxHistorySize: 100,
      enableBatching: true
})

const autoSave = useAutoSave({
      interval: 30000,
  storageKey: `ai-sound-project-${route.params.projectId}`,
      saveFn: async () => await handleSave()
    })

    const keyboardShortcuts = useKeyboardShortcuts({
      'Space': () => {
        console.log('🎤 空格键播放被触发')
        handlePlay()
      },
      'Escape': () => handleStop(),
      'Ctrl+Z': () => undoRedo.undo(),
      'Ctrl+Y': () => undoRedo.redo(),
      'Ctrl+S': () => handleSave(),
      'Delete': () => handleDeleteSelected()
    })

    // 计算属性
    const playheadPosition = computed(() => {
      return (currentTime.value / totalDuration.value) * timelineWidth.value
    })

    // 当前选中轨道的音频URL
    const selectedTrackAudioUrl = computed(() => {
      if (!selectedTrack.value || !selectedTrack.value.segments || selectedTrack.value.segments.length === 0) {
        return null
      }
      
      // 返回第一个音频片段的URL
      const firstSegment = selectedTrack.value.segments[0]
      return firstSegment?.audioUrl || null
    })

    const timeMarks = computed(() => {
      const marks = []
      const step = totalDuration.value / 20 // 增加刻度密度
      const baseWidth = 800 // 基础宽度
      for (let i = 0; i <= 20; i++) {
        marks.push({
          time: i * step,
          position: (i / 20) * baseWidth
        })
      }
      return marks
    })

    // 播放控制防抖定时器
    const playToggleDebounce = ref(null)

    // 方法
const loadProject = async () => {
  try {
    const projectId = route.params.projectId
    if (projectId && projectId !== 'new') {
      const response = await api.audioEditor.getProject(projectId)
      if (response.success) {
        project.value = response.data
        tracks.value = response.data.tracks || []
      }
    } else {
      // 创建新项目
      project.value = {
        name: '新建项目',
        status: 'draft',
        type: 'audio_only'
      }
      // 添加示例音轨用于演示
      tracks.value = [
        {
          id: 'demo-track-1',
          name: '主音轨',
          type: 'audio',
          volume: 0.8,
          pan: 0, // 平移控制 -1 to 1
          muted: false,
          hidden: false,
          locked: false,
          segments: [
            {
              id: 'demo-segment-1',
              name: '示例音频片段',
              startTime: 2,
              endTime: 15,
              volume: 1,
              fadeIn: 0,
              fadeOut: 0,
              audioUrl: 'https://www.w3schools.com/html/horse.ogg'
            },
            {
              id: 'demo-segment-2', 
              name: '语音片段',
              startTime: 18,
              endTime: 28,
              volume: 0.9,
              fadeIn: 0.5,
              fadeOut: 0.5,
              audioUrl: 'https://www.w3schools.com/html/horse.ogg'
            }
          ]
        },
        {
          id: 'demo-track-2',
          name: '背景音乐',
          type: 'music',
          volume: 0.4,
          pan: 0, // 平移控制 -1 to 1
          muted: false,
          hidden: false,
          locked: false,
          segments: [
            {
              id: 'demo-segment-3',
              name: '背景音乐',
              startTime: 0,
              endTime: 30,
              volume: 0.6,
              fadeIn: 1,
              fadeOut: 1,
              audioUrl: 'https://www.w3schools.com/html/horse.ogg'
            }
          ]
        }
      ]
      
      // 添加示例导入文件用于演示拖拽
      importedAudioFiles.value = [
        {
          id: 'demo-audio-1',
          name: '示例音频文件',
          originalName: 'sample_audio.wav',
          type: 'audio',
          audioUrl: 'https://www.w3schools.com/html/horse.ogg',
          filePath: '/uploads/demo/sample_audio.wav',
          fileSize: 1024000,
          duration: 25,
          uploadTime: new Date().toISOString()
        },
        {
          id: 'demo-audio-2',
          name: '语音录制',
          originalName: 'voice_record.mp3',
          type: 'voice',
          audioUrl: 'https://www.w3schools.com/html/horse.ogg',
          filePath: '/uploads/demo/voice_record.mp3',
          fileSize: 512000,
          duration: 18,
          uploadTime: new Date().toISOString()
        }
      ]
      
      // 默认选中第一个轨道
      if (tracks.value.length > 0) {
        selectedTrack.value = tracks.value[0]
      }
    }
    } catch (error) {
    console.error('加载项目失败:', error)
    message.error('加载项目失败')
  }
}

    const handleBack = () => {
      router.push('/editor')
    }

// 播放控制 - 改为直接触发PreviewPanel的播放
const handlePlay = () => {
  // 防抖保护，避免重复快速调用
  if (playToggleDebounce.value) {
    console.log('🚫 handlePlay: 防抖中，忽略重复调用')
      return
    }
    
  console.log('🎤 handlePlay被调用，当前播放状态:', isPlaying.value)
  
  // 设置防抖（延长到500ms，更严格的防抖）
  playToggleDebounce.value = setTimeout(() => {
    console.log('🔄 handlePlay: 防抖结束，允许下次调用')
    playToggleDebounce.value = null
  }, 500) // 500ms内不允许重复调用
  
  // 切换播放状态
  isPlaying.value = !isPlaying.value
}

const startPlayback = () => {
  // 时间同步现在由PreviewPanel的音频播放器处理
  console.log('🎵 startPlayback: 播放开始')
}

const pausePlayback = () => {
  isPlaying.value = false
}

const handleStop = () => {
  console.log('⏹️ handleStop被调用')
      isPlaying.value = false
      currentTime.value = 0
}

const handleSave = async () => {
  saving.value = true
  try {
    const projectData = {
      name: project.value.name,
      tracks: tracks.value
    }
    
    if (project.value.id) {
      await api.audioEditor.updateProject(project.value.id, projectData)
    } else {
      const response = await api.audioEditor.createProject(projectData)
      if (response.success) {
        project.value.id = response.data.id
        router.replace(`/editor/project/${project.value.id}`)
      }
    }
    
    message.success('保存成功')
  } catch (error) {
    console.error('保存失败:', error)
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}

const handleExport = ({ key }) => {
  switch (key) {
    case 'audio':
      message.info('音频导出功能开发中...')
      break
    case 'video':
      message.info('视频导出功能开发中...')
      break
    case 'project':
      message.info('项目导出功能开发中...')
      break
  }
}

    // 轨道管理
    const addTrack = () => {
      const newTrack = {
        id: Date.now(),
        name: `轨道 ${tracks.value.length + 1}`,
        type: 'audio',
        volume: 1,
        muted: false,
        solo: false,
        segments: []
      }
      tracks.value.push(newTrack)
      selectedTrack.value = newTrack
    }

    const selectTrack = (track) => {
      selectedTrack.value = track
      selectedSegment.value = null
    }

    const toggleTrackMute = (track) => {
      track.muted = !track.muted
    }

    const toggleTrackVisibility = (track) => {
      track.hidden = !track.hidden
    }

    const toggleTrackLock = (track) => {
      track.locked = !track.locked
      if (track.locked && selectedTrack.value === track) {
        selectedTrack.value = null
      }
    }

    const toggleTrackSolo = (track) => {
      track.solo = !track.solo
    }

    const selectSegment = (segment) => {
      selectedSegment.value = segment
      selectedAudioClip.value = segment // 同时更新选中的音频片段
    }

    const editSegment = (segment) => {
      selectedSegment.value = segment
      selectedAudioClip.value = segment
      // 这里可以打开编辑面板或模态框
    }

    // 选择音频片段
    const selectAudioClip = (clip) => {
      selectedAudioClip.value = clip
      selectedSegment.value = clip
    }

    // 属性更新处理函数
    const handleUpdateClipProperty = ({ property, value }) => {
      if (selectedAudioClip.value) {
        selectedAudioClip.value[property] = value
        // 同时更新对应的segment
        if (selectedSegment.value && selectedSegment.value.id === selectedAudioClip.value.id) {
          selectedSegment.value[property] = value
        }
      }
    }

    const handleUpdateTrackProperty = ({ property, value }) => {
      if (selectedTrack.value) {
        selectedTrack.value[property] = value
      }
    }

    const handleUpdateProjectProperty = ({ property, value }) => {
      switch (property) {
        case 'name':
          projectName.value = value
          break
        case 'sampleRate':
          sampleRate.value = value
          break
        case 'bitDepth':
          bitDepth.value = value
          break
      }
    }

    // 资源库相关
    const handleResourceSelected = (resource) => {
      selectedAudioData.value = resource
    }

    const handleAddToTrack = (resource) => {
      if (tracks.value.length === 0) {
        addTrack()
      }
      
      const targetTrack = selectedTrack.value || tracks.value[0]
      const newSegment = {
        id: Date.now(),
        name: resource.name,
          startTime: 0,
        endTime: resource.duration || 10,
          volume: 1,
          fadeIn: 0,
          fadeOut: 0,
        audioUrl: resource.url || resource.audioUrl
      }
      
      targetTrack.segments.push(newSegment)
      message.success(`已添加"${resource.name}"到${targetTrack.name}`)
    }

    // 音轨波形事件处理
    const onSegmentWaveformReady = ({ duration } = {}) => {
      console.log('音轨波形就绪，时长:', duration)
      waveformReady.value = true
    }

    const showImportModal = () => {
      importModalVisible.value = true
    }

    // 全屏相关
    const toggleFullscreen = async () => {
      try {
        if (!isFullscreen.value) {
          if (editorContainer.value.requestFullscreen) {
            await editorContainer.value.requestFullscreen()
          }
          isFullscreen.value = true
          showFloatingControls.value = true
          startAutoHideTimer()
    } else {
          if (document.exitFullscreen) {
            await document.exitFullscreen()
          }
          isFullscreen.value = false
          showFloatingControls.value = true
          clearAutoHideTimer()
    }
  } catch (error) {
        console.error('全屏切换失败:', error)
        message.error('全屏切换失败')
      }
    }

    const toggleResourcePanel = () => {
      showResourcePanel.value = !showResourcePanel.value
    }

    const startAutoHideTimer = () => {
      clearAutoHideTimer()
      if (isFullscreen.value) {
        autoHideControlsTimer.value = setTimeout(() => {
          showFloatingControls.value = false
        }, 3000)
      }
    }

    const clearAutoHideTimer = () => {
      if (autoHideControlsTimer.value) {
        clearTimeout(autoHideControlsTimer.value)
        autoHideControlsTimer.value = null
      }
    }

    const onMouseMove = () => {
      if (isFullscreen.value) {
        showFloatingControls.value = true
        startAutoHideTimer()
      }
    }

    const onFullscreenChange = () => {
      const isCurrentlyFullscreen = !!document.fullscreenElement
      if (!isCurrentlyFullscreen && isFullscreen.value) {
        isFullscreen.value = false
        showFloatingControls.value = true
        clearAutoHideTimer()
      }
    }

    const handleGlobalKeydown = (event) => {
      // 全局空格键播放控制
      if (event.code === 'Space' && !event.ctrlKey && !event.metaKey && !event.altKey) {
        // 检查是否在输入框中
        const activeElement = document.activeElement
        const isInput = activeElement && (
          activeElement.tagName === 'INPUT' ||
          activeElement.tagName === 'TEXTAREA' ||
          activeElement.contentEditable === 'true'
        )
        
        // 检查是否点击的是播放按钮（避免重复触发）
        const isClickingPlayButton = activeElement && (
          activeElement.classList.contains('ant-btn') ||
          activeElement.closest('.play-button-visual') ||
          activeElement.closest('.main-play-btn')
        )
        
        if (!isInput && !isClickingPlayButton) {
          event.preventDefault()
          console.log('🎤 全局空格键播放控制被触发')
          handlePlay()
        } else if (isClickingPlayButton) {
          console.log('🚫 跳过空格键事件，播放按钮正在被点击')
        }
      }
      
      // 全屏模式特定按键处理
      if (isFullscreen.value) {
        switch (event.key) {
          case 'Escape':
            event.preventDefault()
            toggleFullscreen()
            break
          case 'Tab':
            event.preventDefault()
            toggleResourcePanel()
            break
        }
      } else {
        if (event.key === 'f' || event.key === 'F') {
          if (!event.ctrlKey && !event.metaKey && !event.altKey) {
            event.preventDefault()
            toggleFullscreen()
          }
        }
      }
    }

    // 素材拖拽相关
    const handleMaterialDragStart = (eventData) => {
      // MaterialLibrary组件传递的格式是: { event, audioFile }
      const { event, audioFile } = eventData
      const dragData = {
        type: 'audio-material',
        audioFile: audioFile
      }
      event.dataTransfer.setData('application/json', JSON.stringify(dragData))
    }

    const handleTimelineDrop = (dropData) => {
      try {
        const { audioFile, dropTime, targetTrack } = dropData
        let track = targetTrack
        
        // 如果没有找到目标轨道，创建新轨道
        if (!track) {
          track = {
          id: Date.now(),
            name: `轨道 ${tracks.value.length + 1}`,
            type: 'audio',
          volume: 1,
            muted: false,
            solo: false,
            segments: []
          }
          tracks.value.push(track)
        }
        
        // 创建新的音频片段
        const newSegment = {
          id: `segment_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
          name: audioFile.name,
          startTime: dropTime,
          endTime: dropTime + (audioFile.duration || 10),
          volume: 1,
          fadeIn: 0,
          fadeOut: 0,
          audioUrl: audioFile.audioUrl,
          filePath: audioFile.filePath,
          fileSize: audioFile.fileSize
        }
        
        track.segments.push(newSegment)
        selectedTrack.value = track
        selectedSegment.value = newSegment
        
        message.success(`已将"${audioFile.name}"添加到${track.name}，起始时间: ${dropTime}s`)
  } catch (error) {
        console.error('处理时间轴拖拽失败:', error)
        message.error('添加到时间轴失败')
      }
    }

    const handleTrackDrop = (dropData) => {
      try {
        const { audioFile, dropTime, track } = dropData
        
        const newSegment = {
          id: `segment_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
          name: audioFile.name,
          startTime: dropTime,
          endTime: dropTime + (audioFile.duration || 10),
          volume: 1,
          fadeIn: 0,
          fadeOut: 0,
          audioUrl: audioFile.audioUrl,
          filePath: audioFile.filePath,
          fileSize: audioFile.fileSize
        }
        
        track.segments.push(newSegment)
        selectedTrack.value = track
        selectedSegment.value = newSegment
        
        message.success(`已添加"${audioFile.name}"到${track.name}，起始时间: ${dropTime}s`)
      } catch (error) {
        console.error('处理轨道拖拽失败:', error)
        message.error('添加到轨道失败')
      }
    }

    // 其他方法
    const startResize = (event, segment, direction) => {
      // 调整片段大小的逻辑
      console.log('开始调整片段大小:', segment.name, direction)
    }

    const seekTo = (time) => {
      console.log('🔄 seekTo被调用:', time)
      currentTime.value = time
    }

    const setVolume = (volume) => {
  // 设置音量
    }

    const updateProject = (projectData) => {
      Object.assign(project.value, projectData)
    }

    const updateTrack = (trackData) => {
      if (selectedTrack.value) {
        Object.assign(selectedTrack.value, trackData)
      }
    }

    const updateMasterVolume = (volume) => {
      masterVolume.value = volume
    }

    const updateZoomLevel = (zoom) => {
      zoomLevel.value = zoom
    }

    const addNewTrack = () => {
      const newTrack = {
        id: Date.now(),
        name: `轨道 ${tracks.value.length + 1}`,
        type: 'audio',
        volume: 1,
        muted: false,
        solo: false,
        hidden: false,
        locked: false,
        segments: []
      }
      tracks.value.push(newTrack)
      selectedTrack.value = newTrack
    }

    const handleExportProject = (settings) => {
      message.info('项目导出功能开发中...')
    }

        // 智能助手相关方法
    // const toggleSmartAssistant = () => {
    //   smartAssistantVisible.value = !smartAssistantVisible.value
    // }

    const handleDeleteSelected = () => {
      if (selectedSegment.value && selectedTrack.value) {
        const segmentIndex = selectedTrack.value.segments.indexOf(selectedSegment.value)
        if (segmentIndex > -1) {
          const trackToDelete = selectedTrack.value
          // 删除片段
          selectedTrack.value.segments.splice(segmentIndex, 1)
          selectedSegment.value = null
          
          // 检查轨道是否为空，如果为空则删除轨道
          if (trackToDelete.segments.length === 0) {
            const trackIndex = tracks.value.findIndex(t => t.id === trackToDelete.id)
            if (trackIndex > -1) {
              tracks.value.splice(trackIndex, 1)
              selectedTrack.value = null
              message.success(`已删除片段和空轨道 "${trackToDelete.name}"`)
            }
      } else {
            message.success('已删除选中片段')
          }
        }
      }
    }

    const onWaveformReady = () => {
      waveformReady.value = true
    }

    const onRegionCreated = (region) => {
      selectedRegion.value = region
    }

const onProjectImported = (importData) => {
      const { project: importedProject, segments, trackMapping } = importData
  
      // 清空现有轨道
    tracks.value = []
    
    // 根据轨道映射创建轨道
    const trackMap = new Map()
    Object.entries(trackMapping).forEach(([character, trackNumber]) => {
      if (!trackMap.has(trackNumber)) {
        const newTrack = {
          id: Date.now() + trackNumber,
          name: `轨道${trackNumber} - ${character}`,
          type: character === '环境音' ? 'environment' : 'voice',
          volume: 1,
          muted: false,
            solo: false,
          segments: []
        }
        trackMap.set(trackNumber, newTrack)
        tracks.value.push(newTrack)
      }
    })
    
      message.success(`已导入项目 "${importedProject.name}"，创建了 ${tracks.value.length} 个轨道`)
    }

    // 导入成功处理
    const handleImportSuccess = (importedFiles) => {
      // 将导入的文件添加到素材库
      importedAudioFiles.value.push(...importedFiles)
      
      // 设置当前音频URL用于预览（如果还没有设置的话）
      if (!currentAudioUrl.value && importedFiles.length > 0) {
        currentAudioUrl.value = importedFiles[0].audioUrl
      }
      
      console.log('成功导入音频文件:', importedFiles)
    }

    // 工具函数
    const getStatusColor = (status) => {
      const colors = {
        draft: 'default',
        processing: 'processing',
        completed: 'success',
        error: 'error'
      }
      return colors[status] || 'default'
    }

    const getStatusLabel = (status) => {
      const labels = {
        draft: '草稿',
        processing: '处理中',
        completed: '已完成',
        error: '错误'
      }
      return labels[status] || status
    }

    const formatTime = (seconds) => {
      if (!seconds || isNaN(seconds)) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }
    
    const previewAudio = (audioFile) => {
      currentAudioUrl.value = audioFile.audioUrl
      // 可以添加音频预览逻辑
      message.info(`正在预览: ${audioFile.name}`)
    }

    // 缩放控制
    const zoomIn = () => {
      if (zoomLevel.value < 3) {
        zoomLevel.value = Math.min(3, zoomLevel.value + 0.2)
        updateTimelineWidth()
      }
    }

    const zoomOut = () => {
      if (zoomLevel.value > 0.3) {
        zoomLevel.value = Math.max(0.3, zoomLevel.value - 0.2)
        updateTimelineWidth()
      }
    }

    const updateTimelineWidth = () => {
      // 根据缩放级别更新时间轴宽度
      const baseWidth = 1000
      timelineWidth.value = baseWidth * zoomLevel.value
    }

    const formatFileSize = (size) => {
      if (size < 1024) return size + ' B'
      if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
      return (size / 1024 / 1024).toFixed(1) + ' MB'
    }

    // 工具函数
    const getTrackTypeLabel = (type) => {
      const labels = {
        audio: '音频',
        voice: '语音',
        music: '音乐',
        environment: '环境音',
        effect: '音效'
      }
      return labels[type] || type
    }

    // 片段更新处理
    const handleSegmentUpdated = (segment) => {
      console.log('片段已更新:', segment)
      
      // 触发自动保存
      if (autoSave && autoSave.triggerSave) {
        autoSave.triggerSave()
      }
      
      // 更新总时长
      updateTotalDuration()
      
      message.success('片段已更新')
    }

    // 更新总时长
    const updateTotalDuration = () => {
      let maxEndTime = 0
      tracks.value.forEach(track => {
        track.segments?.forEach(segment => {
          if (segment.endTime > maxEndTime) {
            maxEndTime = segment.endTime
          }
        })
      })
      totalDuration.value = Math.max(maxEndTime, 60) // 最小1分钟
    }

    // 生命周期
    onMounted(async () => {
      await loadProject()
      
      // 添加全屏事件监听
      document.addEventListener('fullscreenchange', onFullscreenChange)
      document.addEventListener('keydown', handleGlobalKeydown)
      
      // 添加鼠标移动事件监听
      if (editorContainer.value) {
        editorContainer.value.addEventListener('mousemove', onMouseMove)
      }
    })

    onUnmounted(() => {
      // 清理事件监听
      document.removeEventListener('fullscreenchange', onFullscreenChange)
      document.removeEventListener('keydown', handleGlobalKeydown)
      
      clearAutoHideTimer()
      
      if (editorContainer.value) {
        editorContainer.value.removeEventListener('mousemove', onMouseMove)
      }
    })

    // 新增编辑操作处理函数
    const handleCopySegment = (segment) => {
      // 实现复制片段逻辑
      console.log('复制片段:', segment)
      // TODO: 实现剪贴板功能
    }

    const handleCutSegment = (segment) => {
      // 实现剪切片段逻辑
      console.log('剪切片段:', segment)
      handleCopySegment(segment)
      handleDeleteSegment(segment)
    }

    const handleDeleteSegment = (segment) => {
      // 删除选中的片段
      console.log('删除片段:', segment)
      
      // 找到包含该片段的轨道，使用索引遍历以便删除轨道
      for (let i = 0; i < tracks.value.length; i++) {
        const track = tracks.value[i]
        if (track.segments) {
          const index = track.segments.findIndex(s => s.id === segment.id)
          if (index > -1) {
            // 删除片段
            track.segments.splice(index, 1)
            selectedSegment.value = null
            
            // 检查轨道是否为空，如果为空则删除轨道
            if (track.segments.length === 0) {
              tracks.value.splice(i, 1)
              // 如果删除的是当前选中的轨道，清除选中状态
              if (selectedTrack.value === track) {
                selectedTrack.value = null
              }
              message.success(`已删除片段和空轨道 "${track.name}"`)
            } else {
              message.success('已删除片段')
            }
            break
          }
        }
      }
    }

    const handleSplitSegment = ({ segment, splitTime }) => {
      // 分割片段逻辑
      console.log('分割片段:', segment, '分割时间:', splitTime)
      
      if (splitTime < segment.startTime || splitTime > segment.endTime) {
        message.error('分割时间不在片段范围内')
        return
      }
      
      // 创建两个新片段
      const originalDuration = segment.endTime - segment.startTime
      const firstPart = {
        ...segment,
        id: `segment_${Date.now()}_${Math.floor(Math.random() * 1000)}`,
        endTime: splitTime
      }
      const secondPart = {
        ...segment,
        id: `segment_${Date.now() + 1}_${Math.floor(Math.random() * 1000)}`,
        startTime: splitTime
      }
      
      // 替换原片段
      for (const track of tracks.value) {
        if (track.segments) {
          const index = track.segments.findIndex(s => s.id === segment.id)
          if (index > -1) {
            track.segments.splice(index, 1, firstPart, secondPart)
            selectedSegment.value = firstPart
            message.success('已分割片段')
            break
          }
        }
      }
    }

    const handleApplyFadeEffect = (segment) => {
      // 应用淡入淡出效果
      console.log('应用淡入淡出:', segment)
      
      // 设置默认的淡入淡出时间
      segment.fadeIn = 0.5
      segment.fadeOut = 0.5
      
      message.success('已应用淡入淡出效果')
    }

    const handleDuplicateSegment = (segment) => {
      // 复制片段到新轨道
      console.log('复制片段到新轨道:', segment)
      
      // 创建新轨道
      const newTrack = {
        id: `track_${Date.now()}`,
        name: `复制轨道 ${tracks.value.length + 1}`,
        type: 'audio',
        volume: 1.0,
        muted: false,
        hidden: false,
        locked: false,
        segments: [{
          ...segment,
          id: `segment_${Date.now()}_${Math.floor(Math.random() * 1000)}`
        }]
      }
      
      tracks.value.push(newTrack)
      message.success('已复制片段到新轨道')
    }

    const handleNormalizeVolume = (segment) => {
      // 音量标准化
      console.log('音量标准化:', segment)
      segment.volume = 1.0
      message.success('已标准化音量')
    }

    const handleReverseSegment = (segment) => {
      // 反向播放
      console.log('反向播放:', segment)
      segment.reversed = !segment.reversed
      message.success(segment.reversed ? '已设置为反向播放' : '已取消反向播放')
    }

    const handleExportSegment = (segment) => {
      // 导出片段
      console.log('导出片段:', segment)
      message.info('导出功能开发中...')
    }

    const handleUndo = () => {
      // 撤销操作
      console.log('撤销操作')
      message.info('撤销功能开发中...')
    }

    const handleRedo = () => {
      console.log('重做操作')
      message.info('重做功能开发中...')
    }

    // 处理删除空轨道
    const handleDeleteEmptyTrack = (track) => {
      console.log('删除空轨道:', track)
      
      const trackIndex = tracks.value.findIndex(t => t.id === track.id)
      if (trackIndex > -1) {
        tracks.value.splice(trackIndex, 1)
        
        // 如果删除的是当前选中的轨道，清除选中状态
        if (selectedTrack.value === track) {
          selectedTrack.value = null
        }
        
        message.success(`已自动删除空轨道 "${track.name}"`)
      }
    }

    return {
      // 数据
      project,
      tracks,
      selectedTrack,
      selectedSegment,
      selectedAudioData,
      selectedAudioClip,
      projectName,
      sampleRate,
      bitDepth,
      isPlaying,
      playbackLoading,
      currentTime,
      totalDuration,
      saving,
      timelineWidth,
      isFullscreen,
      showResourcePanel,
      showFloatingControls,
      // smartAssistantVisible,
      activeMaterialTab,
      materialTabs,
      importModalVisible,

      importedAudioFiles,
      waveformReady,
      selectedRegion,
      zoomLevel,
      currentAudioUrl,
      masterVolume,
      editorContainer,
      waveformViewerRef,
      
      // 计算属性
      playheadPosition,
      selectedTrackAudioUrl,
      timeMarks,
      
      // 方法
      handleBack,
      handlePlay,
      pauseAudio: handleStop, // 暂停音频，复用停止逻辑
      handleStop,
      handleSave,
      handleExport,
      addTrack,
      selectTrack,
      toggleTrackMute,
      toggleTrackVisibility,
      toggleTrackLock,
      toggleTrackSolo,
      selectSegment,
      editSegment,
      selectAudioClip,
      handleUpdateClipProperty,
      handleUpdateTrackProperty,
      handleUpdateProjectProperty,
      handleResourceSelected,
      handleAddToTrack,
      showImportModal,
      toggleFullscreen,
      toggleResourcePanel,
      // toggleSmartAssistant,
      clearAutoHideTimer,
      startAutoHideTimer,

      handleTrackDrop,
      startResize,
      seekTo,
      setVolume,
      updateProject,
      updateTrack,
      updateMasterVolume,
      updateZoomLevel,
      addNewTrack,
      handleExportProject,
      handleDeleteSelected,
      onWaveformReady,
      onSegmentWaveformReady, // 添加这个缺少的方法
      onRegionCreated,
      onProjectImported,
      handleImportSuccess,
      getStatusColor,
      getStatusLabel,
      formatTime,
      formatFileSize,
      getTrackTypeLabel,
      handleMaterialDragStart,
      handleTimelineDrop,
      previewAudio,
      zoomIn,
      zoomOut,
      handleSegmentUpdated,
      // 新增编辑操作函数
      handleCopySegment,
      handleCutSegment,
      handleDeleteSegment,
      handleSplitSegment,
      handleApplyFadeEffect,
      handleUndo,
      handleRedo,
      handleDuplicateSegment,
      handleNormalizeVolume,
      handleReverseSegment,
      handleExportSegment,
      handleDeleteEmptyTrack
    }
  }
}
</script>

<style scoped>
/* 基础布局 */
.audio-video-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f6fa;
  overflow: hidden;
}

/* 顶部工具栏 */
.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
  z-index: 100;
  min-height: 48px;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.project-title {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.toolbar-right {
  display: flex;
  gap: 8px;
}

.playback-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-display {
  font-family: monospace;
  color: #6b7280;
  min-width: 120px;
  text-align: center;
}

/* 主编辑区域 */
.editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

/* 上半部分：三栏均分布局 */
.workspace-top {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr;
  gap: 12px;
  height: 60%;
  padding: 12px;
  padding-bottom: 0;
}

.workspace-left {
  background: white;
  display: flex;
  flex-direction: column;
}

/* 素材库 */
.material-library {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.material-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.material-tabs {
  width: 80px;
  background: #f8f9fa;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  padding-top: 8px;
}

.material-tab {
  padding: 12px 8px;
  text-align: center;
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid transparent;
}

.material-tab:hover {
  background: #e5e7eb;
  color: #374151;
}

.material-tab.active {
  background: white;
  color: #3b82f6;
  border-right: 2px solid #3b82f6;
  font-weight: 600;
}

.material-content {
  flex: 1;
  background: white;
  display: flex;
  flex-direction: column;
}

.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.search-bar {
  margin-bottom: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: #6b7280;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin: 8px 0 16px 0;
  font-size: 14px;
}

/* 素材库材料列表 */
.material-list {
  padding: 8px;
  overflow-y: auto;
}

.material-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 4px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: move;
  transition: all 0.2s;
}

.material-item:hover {
  background: #f8fafc;
  border-color: #d1d5db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.material-item[draggable="true"]:hover {
  cursor: grab;
}

.material-item[draggable="true"]:active {
  cursor: grabbing;
}

.material-icon {
  margin-right: 8px;
  color: #6366f1;
  font-size: 16px;
}

.material-info {
  flex: 1;
  min-width: 0;
}

.material-name {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.material-meta {
  font-size: 11px;
  color: #6b7280;
  margin-top: 2px;
}

.material-actions {
  margin-left: 8px;
}

.workspace-center {
  background: #f8f9fa;
}

.workspace-right {
  background: white;
  padding: 16px;
}

/* 属性面板 */
.properties-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.properties-panel .panel-header {
  margin-bottom: 16px;
}

.properties-panel .panel-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.properties-panel .panel-content {
  flex: 1;
  overflow-y: auto;
}

.clip-properties,
.track-properties,
.project-properties {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
}

.clip-properties h5,
.track-properties h5,
.project-properties h5 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.property-item {
  margin-bottom: 12px;
}

.property-item label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 4px;
}

.property-item span {
  font-size: 12px;
  color: #374151;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
}

.property-item .ant-input,
.property-item .ant-select,
.property-item .ant-input-number {
  width: 100%;
}

.property-item .ant-slider {
  margin: 4px 0 8px 0;
}

/* 智能助手面板 - 已注释 */
/*
.ai-assistant-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.panel-header {
  margin-bottom: 16px;
}

.panel-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
}

.ai-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 20px;
  text-align: center;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 16px;
}

.ai-card:hover {
  border-color: #3b82f6;
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
}

.ai-icon {
  font-size: 32px;
  color: #3b82f6;
  margin-bottom: 12px;
}

.ai-card h4 {
  margin: 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.ai-card p {
  margin: 8px 0 16px 0;
  font-size: 14px;
  color: #6b7280;
}

.track-info-card {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.track-info-card h5 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.track-info-card p {
  margin: 8px 0;
  font-size: 13px;
  color: #6b7280;
}
*/

/* 暗黑模式适配 - 智能助手相关已注释 */
/*
[data-theme="dark"] .ai-assistant-panel {
  background: #1f1f1f;
}

[data-theme="dark"] .panel-header h4 {
  color: #fff;
}

[data-theme="dark"] .ai-card {
  background: #2d2d2d;
  border-color: #434343;
}

[data-theme="dark"] .ai-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.15);
}

[data-theme="dark"] .ai-card h4 {
  color: #fff;
}

[data-theme="dark"] .ai-card p {
  color: #8c8c8c;
}

[data-theme="dark"] .track-info-card {
  background: #2d2d2d;
  border-color: #434343;
}

[data-theme="dark"] .track-info-card h5 {
  color: #fff;
}

[data-theme="dark"] .track-info-card p {
  color: #8c8c8c;
}
*/

[data-theme="dark"] .tracks-empty {
  color: #8c8c8c;
}

[data-theme="dark"] .tracks-empty .empty-icon {
  color: #434343;
}

[data-theme="dark"] .tracks-empty p {
  color: #8c8c8c;
}

/* 素材库暗黑模式 */
[data-theme="dark"] .workspace-left {
  background: #1f1f1f;
  border-color: #434343;
}

[data-theme="dark"] .material-tabs {
  background: #1f1f1f;
  border-color: #434343;
}

[data-theme="dark"] .material-tab {
  color: #8c8c8c;
}

[data-theme="dark"] .material-tab:hover {
  background: #434343;
  color: #fff;
}

[data-theme="dark"] .material-tab.active {
  background: #2d2d2d;
  color: #1890ff;
  border-right-color: #1890ff;
}

[data-theme="dark"] .material-content {
  background: #2d2d2d;
}

[data-theme="dark"] .empty-state {
  color: #8c8c8c;
}

/* 下半部分：轨道区域 */
.workspace-bottom {
  flex: 1;
  background: #2c2c2c;
  margin: 12px;
  margin-top: 0;
  border-radius: 8px;
  border: 1px solid #4a4a4a;
  overflow: hidden;
}

/* 轨道相关样式已移至TracksArea组件 */

.header-controls {
  display: flex;
  align-items: center;
  gap: 24px;
}

.master-volume-control,
.zoom-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.volume-label,
.zoom-label {
  font-size: 12px;
  color: #b0b0b0;
  white-space: nowrap;
}

.header-controls .ant-slider {
  margin: 0;
}

.header-controls .ant-slider .ant-slider-rail {
  background: #4a4a4a;
  height: 3px;
}

.header-controls .ant-slider .ant-slider-track {
  background: #3b82f6;
  height: 3px;
}

.header-controls .ant-slider .ant-slider-handle {
  width: 12px;
  height: 12px;
  border: 2px solid #3b82f6;
  background: #fff;
}

.tracks-title {
  font-size: 13px;
  font-weight: 500;
  color: #e0e0e0;
}

.tracks-toolbar {
  display: flex;
  align-items: center;
  gap: 12px;
}

.tracks-body {
  flex: 1;
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 1px;
  background: #4a4a4a;
}

/* 轨道控制面板 */
.track-controls {
  background: #383838;
  display: flex;
  flex-direction: column;
}

.track-controls-header {
  padding: 16px;
  border-bottom: 1px solid #e5e7eb;
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: white;
}

.track-controls-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
}

.track-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.track-control-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 2px;
  background: #2c2c2c;
  border: 1px solid #4a4a4a;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
}

.track-control-item:hover {
  border-color: #3b82f6;
  background: #3a3a3a;
}

.track-control-item.active {
  border-color: #3b82f6;
  background: #1e3a8a;
}

.track-type-icon {
  margin-right: 12px;
  color: #b0b0b0;
  font-size: 16px;
}

.track-info {
  flex: 1;
}

.track-name {
  font-size: 12px;
  font-weight: 500;
  color: #e0e0e0;
  margin-bottom: 4px;
}

.track-controls-buttons {
  display: flex;
  gap: 4px;
}

.tracks-empty {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}

.tracks-empty .empty-icon {
  font-size: 48px;
  color: #d1d5db;
  margin-bottom: 16px;
}

.tracks-empty p {
  margin: 16px 0;
  font-size: 16px;
  color: #6b7280;
}

/* 轨道相关样式已移至TracksArea组件 */

.track-item {
  border-bottom: 1px solid #4a4a4a;
}

.track-item.active {
  background: #3a3a3a;
  border-left: 3px solid #3b82f6;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 12px;
  background: #383838;
  border-bottom: 1px solid #4a4a4a;
}



/* 紧凑的轨道控制布局 */
.compact-track-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
}

.track-controls {
  display: flex;
  align-items: center;
  gap: 6px;
  justify-content: flex-start;
}

.track-controls .ant-btn,
.compact-track-controls .ant-btn {
  border: 1px solid #4a4a4a;
  background: #2c2c2c;
  color: #9ca3af;
  min-width: 26px;
  height: 26px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.track-controls .ant-btn:hover,
.compact-track-controls .ant-btn:hover {
  border-color: #6b7280;
  background: #374151;
  color: #d1d5db;
}

.track-controls .ant-btn.control-active,
.compact-track-controls .ant-btn.control-active {
  border-color: #3b82f6;
  background: #1e40af;
  color: #fff;
}

.track-controls .ant-slider {
  margin: 0;
}

.track-controls .ant-slider .ant-slider-rail {
  background: #4a4a4a;
  height: 3px;
}

.track-controls .ant-slider .ant-slider-track {
  background: #3b82f6;
  height: 3px;
}

.track-controls .ant-slider .ant-slider-handle {
  width: 12px;
  height: 12px;
  border: 2px solid #3b82f6;
  background: #fff;
}

/* 紧凑轨道标签 */
.track-label {
  flex: 1;
  margin-left: 8px;
}

.track-name {
  font-size: 11px;
  color: #b0b0b0;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 音频片段容器 */
.audio-segment-container {
  position: absolute;
  height: 50px;
  top: 5px;
  border-radius: 4px;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #4a4a4a;
  min-width: 20px; /* 确保最小宽度可见 */
}

.audio-segment-container:hover {
  border-color: #3b82f6;
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

/* 波形组件样式 */
.segment-waveform {
  width: 100%;
  height: 100%;
  background: #1f1f1f;
}

.segment-waveform :deep(.waveform-toolbar) {
  display: none; /* 隐藏音轨中的波形工具栏 */
}

.segment-waveform :deep(.waveform-container) {
  border: none;
  border-radius: 0;
  background: transparent;
}

.segment-waveform :deep(.timeline-ruler) {
  display: none; /* 隐藏音轨中的时间标尺 */
}

/* 片段信息叠加层 */
.segment-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(180deg, rgba(0,0,0,0.3) 0%, rgba(0,0,0,0.1) 100%);
  pointer-events: none;
  display: flex;
  align-items: flex-start;
  padding: 4px 8px;
}

.segment-name {
  color: #fff;
  font-size: 10px;
  font-weight: 500;
  text-shadow: 0 1px 2px rgba(0,0,0,0.5);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 播放头 */
.playhead {
  position: absolute;
  top: 0;
  width: 2px;
  height: 100%;
  background: #ff4d4f;
  z-index: 10;
  pointer-events: none;
  transition: left 0.1s ease-out;
}

/* 空状态 */
.empty-tracks {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  background: #2c2c2c;
}

.empty-content {
  text-align: center;
  color: #8c8c8c;
}

.empty-icon {
  font-size: 48px;
  color: #4a4a4a;
  margin-bottom: 16px;
}

.empty-content p {
  margin: 16px 0 24px 0;
  font-size: 14px;
}

/* 时间轴内容区域 */
.timeline-content {
  position: relative;
  height: 100%;
  overflow: auto;
  background: #2c2c2c;
}

.timeline-ruler {
  height: 30px;
  background: #383838;
  border-bottom: 1px solid #4a4a4a;
  position: relative;
}

.time-mark {
  position: absolute;
  height: 100%;
  display: flex;
  align-items: center;
  border-left: 1px solid #5a5a5a;
  padding-left: 4px;
}

.time-label {
  font-size: 11px;
  color: #b0b0b0;
  font-family: monospace;
}

.playhead {
  position: absolute;
  top: 0;
  width: 2px;
  height: 100%;
  background: #ef4444;
  z-index: 50;
  pointer-events: none;
  transition: left 0.1s ease-out;
}

.tracks-content {
  position: relative;
  padding-top: 8px;
}

.track-lane {
  height: 60px;
  border-bottom: 1px solid #4a4a4a;
  position: relative;
  margin-bottom: 4px;
  background: #3a3a3a;
}

.audio-clip {
  position: absolute;
  height: 48px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-radius: 4px;
  cursor: pointer;
  min-width: 20px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  transition: all 0.2s;
  user-select: none;
}

.audio-clip:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(59, 130, 246, 0.3);
}

.audio-clip.selected {
  border: 2px solid #f59e0b;
  background: linear-gradient(135deg, #f59e0b, #d97706);
}

.clip-content {
  flex: 1;
  overflow: hidden;
}

.clip-name {
  color: white;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.clip-waveform {
  height: 20px;
  background: rgba(255, 255, 255, 0.3);
  border-radius: 2px;
  margin-top: 4px;
}

.clip-handle {
  position: absolute;
  top: 0;
  width: 4px;
  height: 100%;
  background: rgba(255, 255, 255, 0.8);
  cursor: ew-resize;
}

.clip-handle-left {
  left: 0;
}

.clip-handle-right {
  right: 0;
}

/* 全屏模式 */
.fullscreen-mode {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  background: #fff;
  margin: 0 !important;
  padding: 0 !important;
}

.fullscreen-mode .editor-toolbar {
  display: none;
}

.fullscreen-mode .editor-main {
  height: 100vh;
}

.fullscreen-mode .workspace-top {
  height: 65%;
}

.fullscreen-mode .workspace-bottom {
  height: 35%;
}

.fullscreen-mode .workspace-left {
  transition: width 0.3s ease;
}

.fullscreen-mode .workspace-left:not(:hover) {
  width: 0;
}

/* 浮动控制栏 */
.floating-controls {
  position: fixed;
  bottom: 20px;
  left: 50%;
  transform: translateX(-50%);
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: rgba(0, 0, 0, 0.8);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 12px 20px;
  color: white;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
  z-index: 10000;
  min-width: 600px;
  max-width: 800px;
  transition: all 0.3s ease;
}

.floating-left,
.floating-right {
  flex: 0 0 auto;
}

.floating-center {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 20px;
}

.floating-controls .time-display {
  font-family: monospace;
  font-size: 14px;
  color: #fff;
  background: rgba(255, 255, 255, 0.1);
  padding: 6px 12px;
  border-radius: 6px;
  min-width: 140px;
  text-align: center;
}

.floating-controls :deep(.ant-btn) {
  border-color: rgba(255, 255, 255, 0.3) !important;
  background: rgba(255, 255, 255, 0.1) !important;
  color: #fff !important;
}

.floating-controls :deep(.ant-btn:hover) {
  border-color: #1890ff !important;
  background: rgba(24, 144, 255, 0.2) !important;
  color: #1890ff !important;
}

.floating-controls :deep(.ant-btn-primary) {
  background: #1890ff !important;
  border-color: #1890ff !important;
}

.floating-controls :deep(.ant-btn-primary:hover) {
  background: #40a9ff !important;
  border-color: #40a9ff !important;
}

/* 过渡动画 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 暗黑主题适配 */
[data-theme="dark"] .audio-video-editor {
  background: #141414 !important;
}

[data-theme="dark"] .editor-toolbar {
  background: #1f1f1f !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .project-title {
  color: #fff !important;
}

[data-theme="dark"] .time-display {
  color: #8c8c8c !important;
}

[data-theme="dark"] .workspace-left,
[data-theme="dark"] .workspace-right {
  background: #1f1f1f !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .workspace-center {
  background: #1f1f1f !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .workspace-bottom {
  background: #1f1f1f !important;
}

[data-theme="dark"] .track-controls {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .track-controls-header {
  background: #1f1f1f !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .track-controls-header h4 {
  color: #fff !important;
}

[data-theme="dark"] .track-control-item {
  background: #1f1f1f !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .track-control-item:hover {
  border-color: #3b82f6 !important;
}

[data-theme="dark"] .track-control-item.active {
  border-color: #1890ff !important;
  background: #162844 !important;
}

[data-theme="dark"] .track-info .track-name {
  color: #fff !important;
}

[data-theme="dark"] .timeline-content {
  background: #1f1f1f !important;
}

[data-theme="dark"] .timeline-ruler {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .time-label {
  color: #8c8c8c !important;
}

[data-theme="dark"] .track-lane {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .tracks-empty {
  color: #8c8c8c !important;
}

/* 全屏模式暗黑适配 */
[data-theme="dark"] .fullscreen-mode {
  background: #141414 !important;
}

.dark .track-control-item.active {
  background: #1e3a8a;
  border-color: #3b82f6;
}

.dark .track-name {
  color: #fff;
}

.dark .track-type-icon {
  color: #8c8c8c;
}

.dark .tracks-empty {
  color: #8c8c8c;
}

.dark .timeline-content {
  background: #1f1f1f;
}

.dark .timeline-ruler {
  background: #2d2d2d;
  border-color: #434343;
}

.dark .time-label {
  color: #8c8c8c;
}

.dark .track-lane {
  border-color: #434343;
}

.dark .floating-controls {
  background: rgba(31, 31, 31, 0.9);
  border: 1px solid #434343;
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .workspace-top {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr auto;
    height: 50%;
  }
  
  .workspace-left {
    order: 1;
    height: 200px;
  }
  
  .workspace-center {
    order: 2;
  }
  
  .workspace-right {
    order: 3;
    height: 150px;
  }
  
  .tracks-area {
    grid-template-columns: 1fr;
    grid-template-rows: auto 1fr;
  }
  
  .track-controls {
    height: 100px;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
  
  .track-list {
    display: flex;
    gap: 8px;
    overflow-x: auto;
  }
  
  .track-control-item {
    min-width: 150px;
    flex-shrink: 0;
  }
}

@media (max-width: 480px) {
  .editor-toolbar {
    padding: 8px 16px;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .toolbar-center {
    order: 3;
    width: 100%;
    margin-top: 8px;
  }
  
  .floating-controls {
    min-width: 90vw;
    padding: 8px 16px;
  }
  
  .floating-center {
    flex-direction: column;
    gap: 8px;
  }
  
  .floating-controls .time-display {
    font-size: 12px;
    padding: 4px 8px;
  }
}
</style> 