<template>
  <div class="audio-video-editor">
    <!-- 顶部工具栏 -->
    <div class="editor-toolbar">
      <div class="toolbar-left">
        <a-button @click="handleBack" type="text">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M20 11H7.83l5.59-5.59L12 4l-8 8 8 8 1.41-1.41L7.83 13H20v-2z"/>
            </svg>
          </template>
          返回
        </a-button>
        
        <a-divider type="vertical" />
        
        <h2 class="project-title">{{ project?.name || '新建项目' }}</h2>
        
        <a-tag v-if="project?.status" :color="getStatusColor(project.status)">
          {{ getStatusLabel(project.status) }}
        </a-tag>
      </div>
      
      <div class="toolbar-center">
        <!-- 播放控制 -->
        <div class="playback-controls">
          <a-button @click="handlePlay" type="primary" :loading="playbackLoading">
            <template #icon>
              <svg v-if="!isPlaying" width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M8 5v14l11-7z"/>
              </svg>
              <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M6 19h4V5H6v14zm8-14v14h4V5h-4z"/>
              </svg>
            </template>
            {{ isPlaying ? '暂停' : '播放' }}
          </a-button>
          
          <a-button @click="handleStop">
            <template #icon>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                <path d="M6 6h12v12H6z"/>
              </svg>
            </template>
          </a-button>
          
          <span class="time-display">
            {{ formatTime(currentTime) }} / {{ formatTime(totalDuration) }}
          </span>
        </div>
      </div>
      
      <div class="toolbar-right">
        <a-button @click="handleSave" :loading="saving">
          <template #icon>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
              <path d="M17 3H5c-1.11 0-2 .9-2 2v14c0 1.1.89 2 2 2h14c1.1 0 2-.9 2-2V7l-4-4zm-5 16c-1.66 0-3-1.34-3-3s1.34-3 3-3 3 1.34 3 3-1.34 3-3 3zm3-10H5V5h10v4z"/>
            </svg>
          </template>
          保存
        </a-button>
        
        <a-dropdown>
          <a-button>
            导出
            <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
              <path d="M7,10L12,15L17,10H7Z"/>
            </svg>
          </a-button>
          <template #overlay>
            <a-menu @click="handleExport">
              <a-menu-item key="audio">导出音频</a-menu-item>
              <a-menu-item key="video">导出视频</a-menu-item>
              <a-menu-item key="project">导出项目</a-menu-item>
            </a-menu>
          </template>
        </a-dropdown>
      </div>
    </div>

    <!-- 主编辑区域 -->
    <div class="editor-main">
      <!-- 预览区域 -->
      <div class="preview-section">
        <div class="preview-header">
          <h3>预览</h3>
          <div class="preview-controls">
            <a-slider
              v-model:value="zoomLevel"
              :min="0.1"
              :max="3"
              :step="0.1"
              style="width: 120px"
              :tip-formatter="(value) => `${Math.round(value * 100)}%`"
            />
          </div>
        </div>
        
        <div class="preview-content">
          <!-- 集成专业波形显示组件 -->
          <WaveformViewer
            v-if="currentAudioUrl"
            :audio-url="currentAudioUrl"
            :height="220"
            wave-color="#1890ff"
            progress-color="#52c41a"
            cursor-color="#ff4d4f"
            @ready="onWaveformReady"
            @play="onWaveformPlay"
            @pause="onWaveformPause"
            @seek="onWaveformSeek"
            @region-created="onRegionCreated"
            @region-selected="onRegionSelected"
          />
          
          <!-- 无音频时的占位符 -->
          <div v-else class="no-audio-placeholder">
            <div class="placeholder-content">
              <SoundOutlined class="placeholder-icon" />
              <h3>选择音频文件开始编辑</h3>
              <p>从左侧轨道中选择音频片段，或导入新的音频文件</p>
              <a-button type="primary" @click="showImportModal">
                <template #icon><ImportOutlined /></template>
                导入音频
              </a-button>
            </div>
          </div>
        </div>
      </div>

      <!-- 时间轴编辑区域 -->
      <div class="timeline-section">
        <div class="timeline-header">
          <h3>时间轴</h3>
          <div class="timeline-controls">
            <a-button size="small" @click="addTrack">
              <template #icon>
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M19 13h-6v6h-2v-6H5v-2h6V5h2v6h6v2z"/>
                </svg>
              </template>
              添加轨道
            </a-button>
          </div>
        </div>
        
        <!-- 轨道列表 -->
        <div class="tracks-container">
          <div
            v-for="(track, index) in tracks"
            :key="track.id"
            class="track-item"
            :class="{ active: selectedTrack === index }"
            @click="selectTrack(index)"
          >
            <div class="track-header">
              <div class="track-info">
                <h4>{{ track.name }}</h4>
                <span class="track-type">{{ getTrackTypeLabel(track.type) }}</span>
              </div>
              
              <div class="track-controls">
                <a-button type="text" size="small" @click.stop="toggleTrackMute(index)">
                  <template #icon>
                    <svg v-if="track.muted" width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M16.5 12c0-1.77-1.02-3.29-2.5-4.03v2.21l2.45 2.45c.03-.2.05-.41.05-.63zm2.5 0c0 .94-.2 1.82-.54 2.64l1.51 1.51C20.63 14.91 21 13.5 21 12c0-4.28-2.99-7.86-7-8.77v2.06c2.89.86 5 3.54 5 6.71zM4.27 3L3 4.27 7.73 9H3v6h4l5 5v-6.73l4.25 4.25c-.67.52-1.42.93-2.25 1.18v2.06c1.38-.31 2.63-.95 3.69-1.81L19.73 21 21 19.73l-9-9L4.27 3zM12 4L9.91 6.09 12 8.18V4z"/>
                    </svg>
                    <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M3 9v6h4l5 5V4L7 9H3zm13.5 3c0-1.77-1.02-3.29-2.5-4.03v8.05c1.48-.73 2.5-2.25 2.5-4.02zM14 3.23v2.06c2.89.86 5 3.54 5 6.71s-2.11 5.85-5 6.71v2.06c4.01-.91 7-4.49 7-8.77s-2.99-7.86-7-8.77z"/>
                    </svg>
                  </template>
                </a-button>
                
                <a-slider
                  v-model:value="track.volume"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  style="width: 60px"
                  size="small"
                />
              </div>
            </div>
            
            <!-- 轨道内容区域 -->
            <div class="track-content">
              <div
                v-for="segment in track.segments"
                :key="segment.id"
                class="audio-segment"
                :style="{
                  left: (segment.startTime / totalDuration) * 100 + '%',
                  width: ((segment.endTime - segment.startTime) / totalDuration) * 100 + '%'
                }"
                @click.stop="selectSegment(segment)"
              >
                <div class="segment-content">
                  <span class="segment-name">{{ segment.name }}</span>
                </div>
              </div>
            </div>
          </div>
          
          <!-- 空状态 -->
          <div v-if="tracks.length === 0" class="empty-tracks">
            <p>暂无轨道，点击"添加轨道"开始编辑</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 右侧智能编辑助手 -->
    <div class="smart-assistant-panel">
      <SmartEditingAssistant
        :audio-url="currentAudioUrl"
        :total-duration="totalDuration"
        @project-imported="onProjectImported"
        @speech-recognized="onSpeechRecognized"
        @music-recommended="onMusicRecommended"
        @batch-processed="onBatchProcessed"
        @jump-to-time="onJumpToTime"
      />
    </div>

    <!-- 右侧属性面板 -->
    <div class="properties-panel" v-if="selectedSegment">
      <div class="panel-header">
        <h3>属性设置</h3>
        <a-button 
          type="text" 
          size="small" 
          @click="selectedSegment = null"
          title="关闭属性面板"
        >
          ✕
        </a-button>
      </div>
      
      <a-form layout="vertical" size="small">
        <a-form-item label="片段名称">
          <a-input v-model:value="selectedSegment.name" />
        </a-form-item>
        
        <a-form-item label="开始时间">
          <a-input-number
            v-model:value="selectedSegment.startTime"
            :min="0"
            :max="totalDuration"
            :step="0.1"
            style="width: 100%"
          />
        </a-form-item>
        
        <a-form-item label="结束时间">
          <a-input-number
            v-model:value="selectedSegment.endTime"
            :min="selectedSegment.startTime"
            :max="totalDuration"
            :step="0.1"
            style="width: 100%"
          />
        </a-form-item>
        
        <a-form-item label="音量">
          <a-slider
            v-model:value="selectedSegment.volume"
            :min="0"
            :max="1"
            :step="0.01"
          />
        </a-form-item>
        
        <a-form-item label="淡入时长">
          <a-input-number
            v-model:value="selectedSegment.fadeIn"
            :min="0"
            :max="5"
            :step="0.1"
            style="width: 100%"
          />
        </a-form-item>
        
        <a-form-item label="淡出时长">
          <a-input-number
            v-model:value="selectedSegment.fadeOut"
            :min="0"
            :max="5"
            :step="0.1"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </div>
  </div>

  <!-- 状态栏 -->
  <div class="status-bar">
    <div class="status-left">
      <span class="status-item">
        <a-badge :status="saveStatusColor" />
        {{ saveStatusText }}
      </span>
      
      <span class="status-item" v-if="systems?.autoSave?.lastSaveTime">
        上次保存: {{ formatLastSaveTime() }}
      </span>
      
      <span class="status-item">
        缩放: {{ Math.round(zoomLevel * 100) }}%
      </span>
    </div>
    
    <div class="status-center">
      <span class="status-item">
        轨道: {{ tracks.length }} | 片段: {{ totalSegments }}
      </span>
    </div>
    
    <div class="status-right">
      <span class="status-item" v-if="systems?.undoRedo?.canUndo">
        <a-button type="text" size="small" @click="systems.undoRedo.undo()">
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M12.5 8c-2.65 0-5.05.99-6.9 2.6L2 7v9h9l-3.62-3.62c1.39-1.16 3.16-1.88 5.12-1.88 3.54 0 6.55 2.31 7.6 5.5l2.37-.78C21.08 11.03 17.15 8 12.5 8z"/>
            </svg>
          </template>
        </a-button>
      </span>
      
      <span class="status-item" v-if="systems?.undoRedo?.canRedo">
        <a-button type="text" size="small" @click="systems.undoRedo.redo()">
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M18.4 10.6C16.55 8.99 14.15 8 11.5 8c-4.65 0-8.58 3.03-9.96 7.22L3.9 16c1.05-3.19 4.05-5.5 7.6-5.5 1.95 0 3.73.72 5.12 1.88L13 16h9V7l-3.6 3.6z"/>
            </svg>
          </template>
        </a-button>
      </span>
      
      <span class="status-item">
        <a-button type="text" size="small" @click="keyboardManager?.showHelp()">
          <template #icon>?</template>
        </a-button>
      </span>
    </div>
  </div>

  <!-- 导入音频文件模态框 -->
  <a-modal
    v-model:open="importModalVisible"
    title="导入音频文件"
    width="600px"
    :confirm-loading="uploadLoading"
    @ok="handleImportConfirm"
    @cancel="importModalVisible = false"
  >
    <div class="import-modal-content">
      <a-upload-dragger
        v-model:fileList="uploadFileList"
        name="file"
        multiple
        accept="audio/*"
        :before-upload="beforeUpload"
        @change="handleFileChange"
        @drop="handleFileDrop"
      >
        <p class="ant-upload-drag-icon">
          <SoundOutlined style="font-size: 48px; color: #1890ff;" />
        </p>
        <p class="ant-upload-text">点击或拖拽音频文件到此区域上传</p>
        <p class="ant-upload-hint">
          支持的格式: MP3, WAV, FLAC, AAC, OGG
        </p>
      </a-upload-dragger>
      
      <div v-if="uploadFileList.length > 0" style="margin-top: 16px;">
        <h4>即将导入的文件:</h4>
        <a-list
          :dataSource="uploadFileList"
          size="small"
        >
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta>
                <template #title>{{ item.name }}</template>
                <template #description>
                  大小: {{ formatFileSize(item.size) }}
                  <a-tag v-if="item.status === 'uploading'" color="processing">上传中</a-tag>
                  <a-tag v-else-if="item.status === 'done'" color="success">就绪</a-tag>
                  <a-tag v-else-if="item.status === 'error'" color="error">错误</a-tag>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
        </a-list>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, onMounted, onUnmounted, computed, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { SoundOutlined, ImportOutlined } from '@ant-design/icons-vue'
import WaveformViewer from '@/components/WaveformViewer.vue'
import SmartEditingAssistant from '@/components/SmartEditingAssistant.vue'
import { useKeyboardShortcuts } from '@/composables/useKeyboardShortcuts'
import { useUndoRedo } from '@/composables/useUndoRedo'
import { useAutoSave } from '@/composables/useAutoSave'
import { useWorkerManager } from '@/composables/useWorkerManager'
import { useCacheManager } from '@/composables/useCacheManager'
import { useDragAndDrop } from '@/composables/useDragAndDrop'
import api from '@/api'

const route = useRoute()
const router = useRouter()

// 项目数据
const project = ref(null)
const tracks = ref([])
const selectedTrack = ref(null)
const selectedSegment = ref(null)

// 播放控制
const isPlaying = ref(false)
const playbackLoading = ref(false)
const currentTime = ref(0)
const totalDuration = ref(300) // 默认5分钟

// 编辑器状态
const zoomLevel = ref(1)
const saving = ref(false)
const currentAudioUrl = ref('')

// DOM引用
const waveformContainer = ref(null)
const waveformCanvas = ref(null)

// 波形相关状态
const waveformReady = ref(false)
const selectedRegion = ref(null)
const importModalVisible = ref(false)

// 文件上传相关
const uploadFileList = ref([])
const uploadLoading = ref(false)

// 计算属性
const playheadPosition = computed(() => {
  if (!waveformContainer.value) return 0
  const containerWidth = waveformContainer.value.clientWidth
  return (currentTime.value / totalDuration.value) * containerWidth
})

// 系统状态
const systems = ref(null)

// 状态栏相关计算属性
const totalSegments = computed(() => {
  return tracks.value.reduce((total, track) => total + track.segments.length, 0)
})

const saveStatusColor = computed(() => {
  if (!systems.value?.autoSave) return 'default'
  
  const status = systems.value.autoSave.saveStatus
  switch (status) {
    case 'saving': return 'processing'
    case 'saved': return 'success'
    case 'unsaved': return 'warning'
    case 'offline': return 'error'
    default: return 'default'
  }
})

const saveStatusText = computed(() => {
  if (!systems.value?.autoSave) return '未知状态'
  
  const status = systems.value.autoSave.saveStatus
  switch (status) {
    case 'saving': return '保存中...'
    case 'saved': return '已保存'
    case 'unsaved': return '未保存'
    case 'offline': return '离线模式'
    default: return '未知状态'
  }
})

// 格式化上次保存时间
const formatLastSaveTime = () => {
  if (!systems.value?.autoSave?.lastSaveTime) return ''
  
  const now = Date.now()
  const diff = now - systems.value.autoSave.lastSaveTime
  
  if (diff < 60000) return '刚刚'
  if (diff < 3600000) return `${Math.floor(diff / 60000)}分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)}小时前`
  
  return new Date(systems.value.autoSave.lastSaveTime).toLocaleString()
}

// 在setup()开始时立即初始化所有包含生命周期钩子的composable函数
// 这些必须在任何await语句之前调用

// 初始化撤销重做系统
const undoRedo = useUndoRedo({
  maxHistorySize: 100,
  enableBatching: true,
  batchTimeout: 1000
})

// 初始化自动保存系统
const autoSave = useAutoSave({
  interval: 30000, // 30秒自动保存
  storageKey: `ai-sound-project-${route.params.projectId}`,
  saveFn: async () => {
    return await saveProject()
  },
  loadFn: async (data) => {
    if (data.project) project.value = data.project
    if (data.tracks) tracks.value = data.tracks
  }
})

// 初始化WebWorker管理器
const workerManager = useWorkerManager({
  maxWorkers: 4,
  workerTimeout: 30000,
  enablePooling: true,
  enableRetry: true,
  maxRetries: 3
})

// 初始化缓存管理器
const cacheManager = useCacheManager({
  maxMemorySize: 100 * 1024 * 1024, // 100MB
  maxDiskSize: 500 * 1024 * 1024, // 500MB
  enablePreload: true,
  enableCompression: true,
  cacheExpiry: 7 * 24 * 60 * 60 * 1000 // 7天
})

// 初始化拖拽系统
const dragAndDrop = useDragAndDrop({
  snapThreshold: 10,
  enableSnapping: true,
  enableMultiSelect: true,
  enableCollisionDetection: true,
  enablePreview: true
})

// 手动创建键盘快捷键管理器，避免使用包含生命周期钩子的composable
const createKeyboardShortcuts = () => {
  const shortcuts = {
    'Space': () => handlePlay(),
    'Enter': () => { isPlaying.value = true; startPlayback() },
    'Escape': () => handleStop(),
    'Ctrl+Z': undoRedo.undo,
    'Ctrl+Y': undoRedo.redo,
    'Ctrl+C': () => handleCopy(),
    'Ctrl+V': () => handlePaste(),
    'Ctrl+X': () => handleCut(),
    'Ctrl+A': () => handleSelectAll(),
    'Delete': () => handleDelete(),
    'Ctrl+S': () => autoSave.manualSave(),
    'Ctrl+E': () => handleExport({ key: 'audio' }),
    'Ctrl+I': () => showImportModal(),
    'Ctrl++': () => { zoomLevel.value = Math.min(zoomLevel.value + 0.1, 3) },
    'Ctrl+-': () => { zoomLevel.value = Math.max(zoomLevel.value - 0.1, 0.1) },
    'Ctrl+0': () => { zoomLevel.value = 1 },
    'Home': () => { currentTime.value = 0 },
    'End': () => { currentTime.value = totalDuration.value },
    'ArrowLeft': () => { currentTime.value = Math.max(currentTime.value - 0.1, 0) },
    'ArrowRight': () => { currentTime.value = Math.min(currentTime.value + 0.1, totalDuration.value) },
    'Shift+ArrowLeft': () => { currentTime.value = Math.max(currentTime.value - 1, 0) },
    'Shift+ArrowRight': () => { currentTime.value = Math.min(currentTime.value + 1, totalDuration.value) },
    'Digit1': () => selectTrack(0),
    'Digit2': () => selectTrack(1),
    'Digit3': () => selectTrack(2),
    'Digit4': () => selectTrack(3),
    'Digit5': () => selectTrack(4),
    'Digit6': () => selectTrack(5),
    'Digit7': () => selectTrack(6),
    'Digit8': () => selectTrack(7),
    'Digit9': () => selectTrack(8),
    'M': () => {
      if (selectedTrack.value !== null) {
        toggleTrackMute(selectedTrack.value)
      }
    },
    'Ctrl+M': () => handleAddMarker(),
    'Ctrl+R': () => handleAddRegion(),
    'F5': () => location.reload()
  }
  
  const getKeyCombo = (event) => {
    const keys = []
    if (event.ctrlKey) keys.push('Ctrl')
    if (event.shiftKey) keys.push('Shift')
    if (event.altKey) keys.push('Alt')
    if (event.metaKey) keys.push('Meta')
    
    let key = event.key
    if (key === ' ') key = 'Space'
    if (key === '+') key = '+'
    if (key === '-') key = '-'
    if (key === '=') key = '='
    
    if (event.code && event.code.startsWith('Digit')) {
      key = event.code
    }
    
    keys.push(key)
    return keys.join('+')
  }
  
  const handleKeyDown = (event) => {
    const target = event.target
    if (target.tagName === 'INPUT' || 
        target.tagName === 'TEXTAREA' || 
        target.contentEditable === 'true') {
      return
    }
    
    const combo = getKeyCombo(event)
    const action = shortcuts[combo]
    if (action) {
      event.preventDefault()
      event.stopPropagation()
      try {
        action(event)
      } catch (error) {
        console.error(`快捷键执行失败 (${combo}):`, error)
      }
    }
  }
  
  return {
    handleKeyDown,
    showHelp: () => {
      console.log('键盘快捷键帮助:', shortcuts)
    }
  }
}

let keyboardManager = null

// 初始化延迟系统（在所有函数定义之后调用）
const initializeDelayedSystems = () => {
  // 创建键盘快捷键管理器
  keyboardManager = createKeyboardShortcuts()
  
  // 添加事件监听器
  document.addEventListener('keydown', keyboardManager.handleKeyDown)
  
  // 设置拖拽事件处理
  dragAndDrop.on('dragStart', handleDragStart)
  dragAndDrop.on('dragMove', handleDragMove)
  dragAndDrop.on('drop', handleDrop)
  dragAndDrop.on('move', handleMove)
  dragAndDrop.on('deleteSelected', handleDeleteSelected)
  
  // 保存系统引用以便在模板中使用
  systems.value = { 
    undoRedo, 
    autoSave, 
    shortcuts: keyboardManager, 
    workerManager, 
    cacheManager, 
    dragAndDrop 
  }
}

// 页面加载
onMounted(async () => {
  await loadProject()
  initializeWaveform()
  initializeDelayedSystems()
})

// 页面卸载时清理
onUnmounted(() => {
  if (keyboardManager) {
    document.removeEventListener('keydown', keyboardManager.handleKeyDown)
  }
})

// 加载项目
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
      tracks.value = []
    }
  } catch (error) {
    console.error('加载项目失败:', error)
    message.error('加载项目失败')
  }
}

// 初始化波形显示
const initializeWaveform = () => {
  nextTick(() => {
    if (!waveformCanvas.value) return
    
    const canvas = waveformCanvas.value
    const ctx = canvas.getContext('2d')
    const container = waveformContainer.value
    
    canvas.width = container.clientWidth
    canvas.height = 100
    
    // 绘制基本网格
    ctx.strokeStyle = '#e5e7eb'
    ctx.lineWidth = 1
    
    // 时间网格线
    for (let i = 0; i <= 10; i++) {
      const x = (i / 10) * canvas.width
      ctx.beginPath()
      ctx.moveTo(x, 0)
      ctx.lineTo(x, canvas.height)
      ctx.stroke()
    }
  })
}

// 播放控制
const handlePlay = () => {
  isPlaying.value = !isPlaying.value
  if (isPlaying.value) {
    startPlayback()
  } else {
    pausePlayback()
  }
}

const startPlayback = () => {
  // 模拟播放
  const playInterval = setInterval(() => {
    if (!isPlaying.value) {
      clearInterval(playInterval)
      return
    }
    
    currentTime.value += 0.1
    if (currentTime.value >= totalDuration.value) {
      currentTime.value = totalDuration.value
      isPlaying.value = false
      clearInterval(playInterval)
    }
  }, 100)
}

const pausePlayback = () => {
  isPlaying.value = false
}

const handleStop = () => {
  isPlaying.value = false
  currentTime.value = 0
}

// 轨道管理
const addTrack = () => {
  const newTrack = {
    id: Date.now(),
    name: `轨道 ${tracks.value.length + 1}`,
    type: 'audio',
    volume: 1,
    muted: false,
    segments: []
  }
  tracks.value.push(newTrack)
  selectedTrack.value = tracks.value.length - 1
}

const selectTrack = (index) => {
  selectedTrack.value = index
  selectedSegment.value = null
}

const toggleTrackMute = (index) => {
  tracks.value[index].muted = !tracks.value[index].muted
}

const selectSegment = (segment) => {
  selectedSegment.value = segment
}

// 项目操作
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

const handleBack = () => {
  router.push('/editor')
}

// 波形组件事件处理（已移至下方增强版）

// 波形事件处理函数已移至下方增强版，避免重复声明

// 从选区创建音频片段的逻辑已移至增强版 onRegionCreated 中

// 显示导入对话框
const showImportModal = () => {
  uploadFileList.value = []
  importModalVisible.value = true
}

// 文件上传相关方法
const beforeUpload = (file) => {
  // 检查文件类型
  const isAudio = file.type.startsWith('audio/')
  if (!isAudio) {
    message.error('只能上传音频文件!')
    return false
  }
  
  // 检查文件大小 (限制为100MB)
  const isLt100M = file.size / 1024 / 1024 < 100
  if (!isLt100M) {
    message.error('音频文件大小不能超过100MB!')
    return false
  }
  
  return false // 阻止自动上传，我们手动处理
}

const handleFileChange = (info) => {
  console.log('文件变化:', info)
}

const handleFileDrop = (e) => {
  console.log('文件拖拽:', e)
}

const formatFileSize = (size) => {
  if (size < 1024) return size + ' B'
  if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
  return (size / 1024 / 1024).toFixed(1) + ' MB'
}

const handleImportConfirm = async () => {
  if (uploadFileList.value.length === 0) {
    message.warning('请先选择要导入的音频文件')
    return
  }
  
  uploadLoading.value = true
  try {
    for (const file of uploadFileList.value) {
      if (file.originFileObj) {
        await importAudioFile(file.originFileObj)
      }
    }
    
    message.success(`成功导入 ${uploadFileList.value.length} 个音频文件`)
    importModalVisible.value = false
    uploadFileList.value = []
  } catch (error) {
    console.error('导入音频文件失败:', error)
    message.error('导入失败: ' + error.message)
  } finally {
    uploadLoading.value = false
  }
}

const importAudioFile = async (file) => {
  // 创建FormData
  const formData = new FormData()
  formData.append('file', file)
  
  try {
    // 上传文件到服务器
    const uploadResponse = await api.audioEditor.uploadFile(formData)
    console.log('[API响应]', '/audio-editor/upload', uploadResponse)
    
    // 修复：axios响应数据在data字段中
    const responseData = uploadResponse.data || uploadResponse
    
    if (responseData.success) {
      // 根据实际API响应结构处理数据
      const fileName = responseData.filename
      const filePath = responseData.file_path
      const fileSize = responseData.file_size
      
      // 构建文件访问URL - 将本地路径转换为API访问路径
      const fileUrl = `/api/v1/audio-editor/files/${fileName}`
      
      // 创建新的音频轨道
      const newTrack = {
        id: Date.now(),
        name: file.name.replace(/\.[^/.]+$/, ''), // 移除文件扩展名
        type: 'audio',
        volume: 1,
        muted: false,
        segments: [{
          id: Date.now() + 1,
          name: file.name,
          startTime: 0,
          endTime: 30, // 默认30秒，后续可以通过音频元数据获取实际时长
          volume: 1,
          fadeIn: 0,
          fadeOut: 0,
          audioUrl: fileUrl,
          filePath: filePath,
          fileSize: fileSize
        }]
      }
      
      tracks.value.push(newTrack)
      
      // 设置当前音频URL用于预览
      if (!currentAudioUrl.value) {
        currentAudioUrl.value = fileUrl
      }
      
      console.log('成功创建音频轨道:', newTrack)
      
    } else {
      throw new Error(responseData.message || '上传失败')
    }
  } catch (error) {
    console.error('上传文件详细错误:', error)
    throw new Error(`上传文件 ${file.name} 失败: ${error.message}`)
  }
}

// 设置当前音频URL（用于测试）
const setTestAudio = () => {
  // 这里可以设置一个测试音频URL
  currentAudioUrl.value = '/api/v1/audio-editor/test-audio.mp3'
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

const getTrackTypeLabel = (type) => {
  const labels = {
    audio: '音频',
    dialogue: '对话',
    environment: '环境音',
    music: '音乐',
    effect: '音效'
  }
  return labels[type] || type
}

const formatTime = (seconds) => {
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 智能编辑助手事件处理
const onProjectImported = (importData) => {
  console.log('项目导入结果:', importData)
  
  try {
    const { project, segments, trackMapping } = importData
    
    // 清空现有轨道（可选，也可以询问用户）
    tracks.value = []
    
    // 根据轨道映射创建轨道
    const trackMap = new Map()
    
    // 首先创建所有需要的轨道
    Object.entries(trackMapping).forEach(([character, trackNumber]) => {
      if (!trackMap.has(trackNumber)) {
        const newTrack = {
          id: Date.now() + trackNumber,
          name: `轨道${trackNumber} - ${character}`,
          type: character === '环境音' ? 'environment' : 'voice',
          volume: 1,
          muted: false,
          segments: []
        }
        trackMap.set(trackNumber, newTrack)
        tracks.value.push(newTrack)
      }
    })
    
    // 将音频片段分配到对应轨道
    let currentTime = 0
    segments.forEach((segment, index) => {
      const trackNumber = segment.trackNumber || trackMapping[segment.speaker] || 1
      const track = trackMap.get(trackNumber)
      
      if (track) {
        const audioSegment = {
          id: Date.now() + index * 1000,
          name: `${segment.speaker}: ${segment.text.substring(0, 20)}...`,
          startTime: currentTime,
          endTime: currentTime + (segment.endTime - segment.startTime || 3), // 默认3秒
          volume: 1,
          fadeIn: 0,
          fadeOut: 0,
          speaker: segment.speaker,
          text: segment.text,
          audioUrl: segment.audioUrl || null // 这里需要从项目中获取实际的音频文件URL
        }
        
        track.segments.push(audioSegment)
        currentTime = audioSegment.endTime + 0.1 // 添加小间隙
      }
    })
    
    // 更新总时长
    totalDuration.value = Math.max(totalDuration.value, currentTime)
    
    // 更新项目信息
    if (project.value.id !== project.id) {
      project.value = {
        ...project.value,
        sourceProject: {
          id: project.id,
          name: project.name,
          type: 'synthesis'
        }
      }
    }
    
    message.success(`已导入项目 "${project.name}"，创建了 ${tracks.value.length} 个轨道，${segments.length} 个音频片段`)
    
  } catch (error) {
    console.error('项目导入失败:', error)
    message.error('项目导入失败，请检查项目数据格式')
  }
}

const onSpeechRecognized = (results) => {
  console.log('语音识别结果:', results)
  // 可以将识别结果保存为字幕轨道
  const subtitleTrack = {
    id: Date.now(),
    name: '字幕轨道',
    type: 'subtitle',
    volume: 1,
    muted: false,
    segments: results.map((result, index) => ({
      id: Date.now() + index,
      name: result.text,
      startTime: result.startTime,
      endTime: result.startTime + 3, // 假设每句话持续3秒
      volume: 1,
      fadeIn: 0,
      fadeOut: 0,
      text: result.text,
      confidence: result.confidence
    }))
  }
  tracks.value.push(subtitleTrack)
  message.success(`已创建字幕轨道，包含 ${results.length} 个字幕片段`)
}

const onMusicRecommended = (recommendations) => {
  console.log('音乐推荐结果:', recommendations)
  // 可以显示推荐音乐列表，让用户选择添加
  message.success(`推荐了 ${recommendations.length} 首背景音乐`)
}

const onBatchProcessed = (tasks) => {
  console.log('批量处理任务:', tasks)
  // 应用批量处理结果到所有轨道
  message.success(`已完成 ${tasks.length} 个批量处理任务`)
}

const onJumpToTime = (time) => {
  currentTime.value = time
  console.log('跳转到时间:', time)
  // 如果有波形组件，也可以通知波形组件跳转
}

// 编辑操作处理函数
const handleCopy = () => {
  if (selectedSegment.value) {
    // 复制选中的音频片段
    const clipboardData = JSON.stringify(selectedSegment.value)
    navigator.clipboard.writeText(clipboardData).then(() => {
      message.success('已复制音频片段')
    }).catch(() => {
      message.error('复制失败')
    })
  } else {
    message.warning('请先选择要复制的音频片段')
  }
}

const handlePaste = async () => {
  try {
    const clipboardData = await navigator.clipboard.readText()
    const segmentData = JSON.parse(clipboardData)
    
    if (selectedTrack.value !== null) {
      // 在当前选中轨道粘贴音频片段
      const newSegment = {
        ...segmentData,
        id: Date.now(),
        startTime: currentTime.value
      }
      
      tracks.value[selectedTrack.value].segments.push(newSegment)
      message.success('已粘贴音频片段')
    } else {
      message.warning('请先选择目标轨道')
    }
  } catch (error) {
    message.error('粘贴失败，剪贴板数据无效')
  }
}

const handleCut = () => {
  if (selectedSegment.value) {
    handleCopy()
    handleDelete()
  } else {
    message.warning('请先选择要剪切的音频片段')
  }
}

const handleSelectAll = () => {
  if (selectedTrack.value !== null) {
    // 选择当前轨道的所有片段
    const track = tracks.value[selectedTrack.value]
    if (track.segments.length > 0) {
      // 这里可以实现多选逻辑
      message.info(`已选择轨道 ${track.name} 的所有片段`)
    }
  } else {
    message.warning('请先选择一个轨道')
  }
}

const handleDelete = () => {
  if (selectedSegment.value && selectedTrack.value !== null) {
    const track = tracks.value[selectedTrack.value]
    const segmentIndex = track.segments.findIndex(s => s.id === selectedSegment.value.id)
    
    if (segmentIndex !== -1) {
      track.segments.splice(segmentIndex, 1)
      selectedSegment.value = null
      message.success('已删除音频片段')
    }
  } else {
    message.warning('请先选择要删除的音频片段')
  }
}

// 标记和区域处理函数
const handleAddMarker = () => {
  // 在当前播放位置添加标记
  const marker = {
    id: Date.now(),
    time: currentTime.value,
    name: `标记 ${currentTime.value.toFixed(1)}s`,
    color: '#ff4d4f'
  }
  
  // 这里应该将标记添加到项目数据中
  message.success(`已在 ${currentTime.value.toFixed(1)}s 处添加标记`)
}

const handleAddRegion = () => {
  // 添加一个默认的区域
  const region = {
    id: Date.now(),
    start: currentTime.value,
    end: Math.min(currentTime.value + 10, totalDuration.value),
    name: `区域 ${currentTime.value.toFixed(1)}s`,
    color: '#52c41a'
  }
  
  // 这里应该将区域添加到项目数据中
  message.success(`已添加区域: ${region.start.toFixed(1)}s - ${region.end.toFixed(1)}s`)
}

// 项目保存函数
const saveProject = async () => {
  try {
    const projectData = {
      ...project.value,
      tracks: tracks.value,
      settings: {
        zoomLevel: zoomLevel.value,
        currentTime: currentTime.value
      }
    }
    
    if (project.value.id) {
      // 更新现有项目
      const response = await api.audioEditor.updateProject(project.value.id, projectData)
      if (response.success) {
        return { version: response.data.version }
      }
    } else {
      // 创建新项目
      const response = await api.audioEditor.createProject(projectData)
      if (response.success) {
        project.value = response.data
        return { version: response.data.version }
      }
    }
    
    throw new Error('保存失败')
  } catch (error) {
    console.error('保存项目失败:', error)
    throw error
  }
}

// 波形事件处理（增强版）
const onWaveformReady = async ({ duration } = {}) => {
  waveformReady.value = true
  if (duration) {
    totalDuration.value = duration
  }
  console.log('波形准备就绪，时长:', duration)
  
  // 预加载相关音频数据到缓存
  if (systems.value?.cacheManager && currentAudioUrl.value) {
    try {
      const audioKey = `audio_${currentAudioUrl.value.split('/').pop()}`
      await systems.value.cacheManager.preload('audioData', [audioKey])
    } catch (error) {
      console.warn('预加载音频数据失败:', error)
    }
  }
}

const onWaveformPlay = () => {
  isPlaying.value = true
}

const onWaveformPause = () => {
  isPlaying.value = false
}

const onWaveformSeek = (timeOrEvent) => {
  // 支持两种调用方式：onWaveformSeek(time) 或 onWaveformSeek({ time, progress })
  const time = typeof timeOrEvent === 'object' ? timeOrEvent.time : timeOrEvent
  const progress = typeof timeOrEvent === 'object' ? timeOrEvent.progress : undefined
  
  currentTime.value = time
  console.log('跳转到时间:', time, progress !== undefined ? `进度: ${progress}` : '')
}

const onRegionCreated = async (region) => {
  console.log('创建选区:', region)
  selectedRegion.value = region
  
  // 自动创建音频片段
  if (selectedTrack.value !== null) {
    const track = tracks.value[selectedTrack.value]
    const newSegment = {
      id: Date.now(),
      name: `片段 ${track.segments.length + 1}`,
      startTime: region.start,
      endTime: region.end,
      audioUrl: currentAudioUrl.value
    }
    
    track.segments.push(newSegment)
    selectedSegment.value = newSegment
    
    // 使用Worker生成波形数据并缓存
    if (systems.value?.workerManager && systems.value?.cacheManager) {
      try {
        const segmentKey = `segment_${newSegment.id}`
        const waveformData = await systems.value.workerManager.generateWaveform(
          new Float32Array(1000), // 模拟音频数据
          { width: 800, height: 60 }
        )
        await systems.value.cacheManager.setWaveform(segmentKey, waveformData)
      } catch (error) {
        console.warn('生成片段波形失败:', error)
      }
    }
    
    // 记录撤销操作
    if (systems.value?.undoRedo) {
      systems.value.undoRedo.execute({
        undo: () => {
          const index = track.segments.indexOf(newSegment)
          if (index > -1) track.segments.splice(index, 1)
        },
        redo: () => {
          track.segments.push(newSegment)
        },
        description: '创建音频片段'
      })
    }
    
    message.success('已创建音频片段')
  }
}

const onRegionSelected = (region) => {
  selectedRegion.value = region
}

// 拖拽事件处理
const handleDragStart = (event) => {
  console.log('开始拖拽:', event)
  
  // 记录拖拽开始状态用于撤销
  if (systems.value?.undoRedo) {
    systems.value.undoRedo.startBatch('拖拽操作')
  }
}

const handleDragMove = (event) => {
  // 实时更新拖拽预览，这里可以添加视觉反馈
}

const handleDrop = async (event) => {
  console.log('拖放完成:', event)
  
  const { data, sourceContainer, targetContainer, position, snapPoint } = event
  
  try {
    // 处理跨轨道拖放
    if (sourceContainer !== targetContainer) {
      // 移动音频片段到新轨道
      const sourceTrackId = sourceContainer.dataset.trackId
      const targetTrackId = targetContainer.dataset.trackId
      
      const sourceTrack = tracks.value.find(t => t.id == sourceTrackId)
      const targetTrack = tracks.value.find(t => t.id == targetTrackId)
      
      if (sourceTrack && targetTrack) {
        const segmentIndex = sourceTrack.segments.findIndex(s => s.id === data.id)
        if (segmentIndex > -1) {
          const segment = sourceTrack.segments.splice(segmentIndex, 1)[0]
          
          // 计算新的时间位置
          if (snapPoint) {
            segment.startTime = snapPoint.time || 0
          }
          
          targetTrack.segments.push(segment)
          
          // 使用Worker处理音频混合
          if (systems.value?.workerManager) {
            try {
              await systems.value.workerManager.mixTracks([
                { data: new Float32Array(1000), volume: sourceTrack.volume },
                { data: new Float32Array(1000), volume: targetTrack.volume }
              ])
            } catch (error) {
              console.warn('音频混合处理失败:', error)
            }
          }
          
          message.success('片段已移动到新轨道')
        }
      }
    }
    
    // 结束批量操作
    if (systems.value?.undoRedo) {
      systems.value.undoRedo.endBatch()
    }
    
  } catch (error) {
    console.error('拖放处理失败:', error)
    message.error('拖放操作失败')
  }
}

const handleMove = async (event) => {
  console.log('移动片段:', event)
  
  const { data, delta, snapPoint } = event
  
  // 在同一轨道内移动片段
  const segment = findSegmentById(data.id)
  if (segment) {
    const oldStartTime = segment.startTime
    const oldEndTime = segment.endTime
    
    // 计算新位置
    let newStartTime = oldStartTime + (delta.x / 800) * totalDuration.value
    
    // 应用磁吸
    if (snapPoint) {
      newStartTime = snapPoint.time || newStartTime
    }
    
    // 更新片段位置
    const duration = oldEndTime - oldStartTime
    segment.startTime = Math.max(0, newStartTime)
    segment.endTime = segment.startTime + duration
    
    // 记录撤销操作
    if (systems.value?.undoRedo) {
      systems.value.undoRedo.execute({
        undo: () => {
          segment.startTime = oldStartTime
          segment.endTime = oldEndTime
        },
        redo: () => {
          segment.startTime = newStartTime
          segment.endTime = newStartTime + duration
        },
        description: '移动音频片段'
      })
    }
    
    message.success('片段位置已更新')
  }
}

const handleDeleteSelected = (event) => {
  console.log('删除选中项:', event)
  
  const { items } = event
  const deletedSegments = []
  
  items.forEach(itemId => {
    const segment = findSegmentById(itemId)
    if (segment) {
      const track = findTrackBySegmentId(itemId)
      if (track) {
        const index = track.segments.indexOf(segment)
        if (index > -1) {
          track.segments.splice(index, 1)
          deletedSegments.push({ segment, track, index })
        }
      }
    }
  })
  
  // 记录撤销操作
  if (systems.value?.undoRedo && deletedSegments.length > 0) {
    systems.value.undoRedo.execute({
      undo: () => {
        deletedSegments.forEach(({ segment, track, index }) => {
          track.segments.splice(index, 0, segment)
        })
      },
      redo: () => {
        deletedSegments.forEach(({ segment, track }) => {
          const index = track.segments.indexOf(segment)
          if (index > -1) track.segments.splice(index, 1)
        })
      },
      description: `删除 ${deletedSegments.length} 个音频片段`
    })
  }
  
  message.success(`已删除 ${deletedSegments.length} 个片段`)
}

// 辅助函数
const findSegmentById = (segmentId) => {
  for (const track of tracks.value) {
    const segment = track.segments.find(s => s.id == segmentId)
    if (segment) return segment
  }
  return null
}

const findTrackBySegmentId = (segmentId) => {
  for (const track of tracks.value) {
    if (track.segments.some(s => s.id == segmentId)) {
      return track
    }
  }
  return null
}
</script>

<style scoped>
.audio-video-editor {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f5f6fa;
}

.editor-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 24px;
  background: white;
  border-bottom: 1px solid #e5e7eb;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.project-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.toolbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.playback-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.time-display {
  font-family: monospace;
  color: #6b7280;
  min-width: 100px;
}

.toolbar-right {
  display: flex;
  gap: 12px;
}

.editor-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.preview-section {
  background: white;
  border-bottom: 1px solid #e5e7eb;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #f3f4f6;
}

.preview-header h3 {
  margin: 0;
  color: #1f2937;
}

.preview-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.preview-content {
  padding: 24px;
}

.waveform-container {
  position: relative;
  height: 120px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  overflow: hidden;
}

.waveform-canvas {
  width: 100%;
  height: 100%;
  display: block;
}

.playhead {
  position: absolute;
  top: 0;
  width: 2px;
  height: 100%;
  background: #1890ff;
  pointer-events: none;
  z-index: 10;
}

.no-audio-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 220px;
  background: #fafafa;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
}

.placeholder-content {
  text-align: center;
  color: #666;
}

.placeholder-icon {
  font-size: 48px;
  color: #bbb;
  margin-bottom: 16px;
}

.placeholder-content h3 {
  margin: 16px 0 8px 0;
  color: #333;
}

.placeholder-content p {
  margin-bottom: 24px;
  color: #666;
}

.timeline-section {
  flex: 1;
  background: white;
  display: flex;
  flex-direction: column;
}

.timeline-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 24px;
  border-bottom: 1px solid #f3f4f6;
}

.timeline-header h3 {
  margin: 0;
  color: #1f2937;
}

.tracks-container {
  flex: 1;
  overflow-y: auto;
  padding: 16px 24px;
}

.track-item {
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  margin-bottom: 12px;
  cursor: pointer;
  transition: all 0.3s;
}

.track-item:hover {
  border-color: #d1d5db;
}

.track-item.active {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.1);
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.track-info h4 {
  margin: 0 0 4px 0;
  color: #1f2937;
  font-size: 14px;
}

.track-type {
  font-size: 12px;
  color: #6b7280;
}

.track-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.track-content {
  position: relative;
  height: 60px;
  padding: 8px;
  background: #ffffff;
}

.audio-segment {
  position: absolute;
  height: 44px;
  background: linear-gradient(135deg, #3b82f6, #1d4ed8);
  border-radius: 4px;
  cursor: pointer;
  min-width: 20px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  transition: all 0.2s;
}

.audio-segment:hover {
  transform: translateY(-1px);
  box-shadow: 0 2px 8px rgba(59, 130, 246, 0.3);
}

.segment-content {
  overflow: hidden;
}

.segment-name {
  color: white;
  font-size: 12px;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.empty-tracks {
  text-align: center;
  padding: 40px 20px;
  color: #6b7280;
}

.smart-assistant-panel {
  position: fixed;
  right: 0;
  top: 73px;
  width: 350px;
  background: white;
  border-left: 1px solid #e5e7eb;
  overflow-y: auto;
  z-index: 100;
}

.properties-panel {
  position: fixed;
  right: 350px;
  top: 73px;
  width: 300px;
  height: calc(100vh - 73px);
  background: white;
  border-left: 1px solid #e5e7eb;
  padding: 20px;
  overflow-y: auto;
  z-index: 100;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.properties-panel h3 {
  margin: 0;
  color: #1f2937;
}

.panel-header .ant-btn {
  color: #666;
  font-size: 16px;
  padding: 4px;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.panel-header .ant-btn:hover {
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}

/* 状态栏样式 */
.status-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #f8fafc;
  border-top: 1px solid #e5e7eb;
  font-size: 12px;
  color: #6b7280;
  height: 32px;
}

.status-left,
.status-center,
.status-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.status-center {
  flex: 1;
  justify-content: center;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 4px;
  white-space: nowrap;
}

.status-item .ant-badge {
  margin-right: 4px;
}

.status-item .ant-btn {
  border: none;
  box-shadow: none;
  padding: 2px 4px;
  height: auto;
  min-width: auto;
}

/* 暗黑模式适配 */
[data-theme="dark"] .audio-video-editor {
  background: #141414 !important;
}

[data-theme="dark"] .editor-toolbar {
  background: #1f1f1f !important;
  border-bottom-color: #434343 !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .project-title {
  color: #fff !important;
}

[data-theme="dark"] .time-display {
  color: #8c8c8c !important;
}

[data-theme="dark"] .preview-section {
  background: #1f1f1f !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .preview-header {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .preview-header h3 {
  color: #fff !important;
}

[data-theme="dark"] .preview-content {
  background: #1f1f1f !important;
}

[data-theme="dark"] .waveform-container {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .no-audio-placeholder {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .placeholder-content {
  color: #8c8c8c !important;
}

[data-theme="dark"] .placeholder-icon {
  color: #434343 !important;
}

[data-theme="dark"] .placeholder-content h3 {
  color: #fff !important;
}

[data-theme="dark"] .placeholder-content p {
  color: #8c8c8c !important;
}

[data-theme="dark"] .timeline-section {
  background: #1f1f1f !important;
}

[data-theme="dark"] .timeline-header {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .timeline-header h3 {
  color: #fff !important;
}

[data-theme="dark"] .tracks-container {
  background: #1f1f1f !important;
}

[data-theme="dark"] .track-item {
  border-color: #434343 !important;
  background: #2d2d2d !important;
}

[data-theme="dark"] .track-item:hover {
  border-color: #525252 !important;
}

[data-theme="dark"] .track-item.active {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
}

[data-theme="dark"] .track-header {
  background: #2d2d2d !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .track-info h4 {
  color: #fff !important;
}

[data-theme="dark"] .track-type {
  color: #8c8c8c !important;
}

[data-theme="dark"] .track-content {
  background: #1f1f1f !important;
}

[data-theme="dark"] .audio-segment {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
}

[data-theme="dark"] .audio-segment:hover {
  box-shadow: 0 2px 8px rgba(var(--primary-color-rgb), 0.4) !important;
}

[data-theme="dark"] .segment-name {
  color: #fff !important;
}

[data-theme="dark"] .empty-tracks {
  color: #8c8c8c !important;
}

[data-theme="dark"] .smart-assistant-panel {
  background: #1f1f1f !important;
  border-left-color: #434343 !important;
}

[data-theme="dark"] .properties-panel {
  background: #1f1f1f !important;
  border-left-color: #434343 !important;
}

[data-theme="dark"] .properties-panel h3 {
  color: #fff !important;
}

[data-theme="dark"] .status-bar {
  background: #1f1f1f !important;
  border-top-color: #434343 !important;
  color: #8c8c8c !important;
}

[data-theme="dark"] .no-audio-placeholder {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .placeholder-content {
  color: #8c8c8c !important;
}

[data-theme="dark"] .placeholder-content h3 {
  color: #fff !important;
}

[data-theme="dark"] .placeholder-content p {
  color: #8c8c8c !important;
}

[data-theme="dark"] .placeholder-icon {
  color: #434343 !important;
}

[data-theme="dark"] .timeline-section {
  background: #1f1f1f !important;
}

[data-theme="dark"] .timeline-header {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .timeline-header h3 {
  color: #fff !important;
}

[data-theme="dark"] .tracks-container {
  background: #1f1f1f !important;
}

[data-theme="dark"] .track-item {
  border-color: #434343 !important;
  background: #2d2d2d !important;
}

[data-theme="dark"] .track-item:hover {
  border-color: #525252 !important;
}

[data-theme="dark"] .track-item.active {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
}

[data-theme="dark"] .track-header {
  background: #2d2d2d !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .track-info h4 {
  color: #fff !important;
}

[data-theme="dark"] .track-type {
  color: #8c8c8c !important;
}

[data-theme="dark"] .track-content {
  background: #1f1f1f !important;
}

[data-theme="dark"] .empty-tracks {
  color: #8c8c8c !important;
}

[data-theme="dark"] .audio-segment {
  background: linear-gradient(135deg, var(--primary-color), var(--secondary-color)) !important;
}

[data-theme="dark"] .audio-segment:hover {
  box-shadow: 0 2px 8px rgba(var(--primary-color-rgb), 0.4) !important;
}

[data-theme="dark"] .segment-name {
  color: #fff !important;
}

[data-theme="dark"] .smart-assistant-panel {
  background: #1f1f1f !important;
  border-left-color: #434343 !important;
}

[data-theme="dark"] .properties-panel {
  background: #1f1f1f !important;
  border-left-color: #434343 !important;
}

[data-theme="dark"] .panel-header {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .properties-panel h3 {
  color: #fff !important;
}

[data-theme="dark"] .panel-header .ant-btn {
  color: #8c8c8c !important;
}

[data-theme="dark"] .panel-header .ant-btn:hover {
  color: #ff4d4f !important;
  background: rgba(255, 77, 79, 0.2) !important;
}

[data-theme="dark"] .status-bar {
  background: #1f1f1f !important;
  border-top-color: #434343 !important;
  color: #8c8c8c !important;
}

/* 暗黑模式下的表单组件适配 */
[data-theme="dark"] :deep(.ant-btn-default) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-btn-default:hover) {
  background-color: #3a3a3a !important;
  border-color: var(--primary-color) !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-btn-text) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-btn-text:hover) {
  background-color: #2d2d2d !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-divider-vertical) {
  border-left-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-tag) {
  background: #2d2d2d !important;
  border-color: #434343 !important;
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-dropdown-menu) {
  background: #2d2d2d !important;
  border-color: #434343 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] :deep(.ant-dropdown-menu-item) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-dropdown-menu-item:hover) {
  background: #3a3a3a !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-slider-rail) {
  background-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-slider-track) {
  background-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-slider-handle) {
  border-color: var(--primary-color) !important;
}

/* 暗黑模式下的模态框和抽屉适配 */
[data-theme="dark"] :deep(.ant-modal-content) {
  background: #1f1f1f !important;
  border: 1px solid #434343 !important;
}

[data-theme="dark"] :deep(.ant-modal-header) {
  background: #1f1f1f !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-modal-title) {
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-modal-body) {
  background: #1f1f1f !important;
  color: #d1d5db !important;
}

[data-theme="dark"] :deep(.ant-modal-footer) {
  background: #1f1f1f !important;
  border-top-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-drawer-content-wrapper) {
  background: #1f1f1f !important;
}

[data-theme="dark"] :deep(.ant-drawer-header) {
  background: #1f1f1f !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-drawer-title) {
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-drawer-body) {
  background: #1f1f1f !important;
  color: #d1d5db !important;
}

[data-theme="dark"] :deep(.ant-drawer-footer) {
  background: #1f1f1f !important;
  border-top-color: #434343 !important;
}

/* 表单控件暗黑模式适配 */
[data-theme="dark"] :deep(.ant-input) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-input:hover) {
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-input:focus) {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
}

[data-theme="dark"] :deep(.ant-input::placeholder) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-select) {
  background-color: #2d2d2d !important;
}

[data-theme="dark"] :deep(.ant-select-selector) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-select-selection-item) {
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-select-dropdown) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] :deep(.ant-select-item) {
  color: #d1d5db !important;
}

[data-theme="dark"] :deep(.ant-select-item-option-selected) {
  background-color: rgba(var(--primary-color-rgb), 0.2) !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-select-item:hover) {
  background-color: #3a3a3a !important;
}

/* 移动端响应式 */
@media (max-width: 768px) {
  .editor-toolbar {
    padding: 8px 16px;
    flex-wrap: wrap;
    gap: 8px;
  }
  
  .toolbar-center {
    order: 3;
    width: 100%;
    justify-content: center;
    margin-top: 8px;
  }
  
  .smart-assistant-panel {
    position: fixed;
    bottom: 40vh;
    right: 0;
    left: 0;
    width: auto;
    height: 40vh;
    top: auto;
  }
  
  .properties-panel {
    position: fixed;
    bottom: 0;
    right: 0;
    left: 0;
    width: auto;
    height: 40vh;
    top: auto;
  }
  
  /* 移动端暗黑模式适配 */
  [data-theme="dark"] .smart-assistant-panel,
  [data-theme="dark"] .properties-panel {
    background: #1f1f1f !important;
    border-color: #434343 !important;
  }
}
</style> 