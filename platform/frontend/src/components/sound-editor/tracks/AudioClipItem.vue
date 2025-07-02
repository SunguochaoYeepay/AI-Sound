<template>
  <div
    class="audio-clip"
    :class="{ 
      'selected': selected,
      'dragging': isDragging,
      'dialogue': trackType === 'dialogue',
      'environment': trackType === 'environment',
      'background': trackType === 'background'
    }"
    :style="clipStyle"
    @mousedown="startDrag"
    @click="selectClip"
    @dblclick="editClip"
    @contextmenu.prevent="showContextMenu"
  >
    <!-- 波形背景 -->
    <div v-if="waveformData && waveformData.length > 0" class="waveform-background">
      <WaveformDisplay
        :waveform-data="waveformData"
        :width="clipWidth"
        :height="clipHeight - 16"
        :interactive="false"
        :show-time-markers="false"
        :show-progress="false"
        :wave-color="waveformColor"
        :background-color="'transparent'"
      />
    </div>
    
    <!-- 片段内容 -->
    <div class="clip-content">
              <div class="clip-name">{{ clip.filename }}</div>
      <div v-if="clip.metadata?.text" class="clip-text">{{ clip.metadata.text }}</div>
      <div v-if="clip.metadata?.character" class="clip-character">{{ clip.metadata.character }}</div>
    </div>
    
    <!-- 音量指示器 -->
    <div v-if="clip.volume !== 1.0" class="volume-indicator">
      {{ Math.round(clip.volume * 100) }}%
    </div>
    
    <!-- 淡入淡出指示器 -->
    <div v-if="clip.fadeIn > 0" class="fade-in" :style="fadeInStyle"></div>
    <div v-if="clip.fadeOut > 0" class="fade-out" :style="fadeOutStyle"></div>
    
    <!-- 调整大小手柄 -->
    <div 
      class="resize-handle resize-left"
      @mousedown.stop="startResize('left')"
    ></div>
    <div 
      class="resize-handle resize-right"
      @mousedown.stop="startResize('right')"
    ></div>
    
    <!-- 播放按钮 -->
    <div class="clip-controls">
      <a-button size="small" @click.stop="playClip">
        <template #icon><PlayCircleOutlined /></template>
      </a-button>
    </div>
  </div>
  
  <!-- 右键菜单 -->
  <a-dropdown 
    v-model:open="contextMenuVisible" 
    :trigger="['contextmenu']"
    :get-popup-container="getPopupContainer"
  >
    <div></div>
    <template #overlay>
      <a-menu @click="handleContextMenu">
        <a-menu-item key="edit">
          <EditOutlined />
          编辑
        </a-menu-item>
        <a-menu-item key="copy">
          <CopyOutlined />
          复制
        </a-menu-item>
        <a-menu-item key="split">
          <ScissorOutlined />
          分割
        </a-menu-item>
        <a-menu-divider />
        <a-menu-item key="delete" danger>
          <DeleteOutlined />
          删除
        </a-menu-item>
      </a-menu>
    </template>
  </a-dropdown>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlayCircleOutlined,
  EditOutlined,
  CopyOutlined,
  ScissorOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'

import WaveformDisplay from '../audio/WaveformDisplay.vue'
import { getAudioWaveform } from '../../../api/sound-editor/audioFiles'

const props = defineProps({
  clip: {
    type: Object,
    required: true
  },
  trackType: {
    type: String,
    required: true
  },
  viewDuration: {
    type: Number,
    default: 60
  },
  pixelsPerSecond: {
    type: Number,
    default: 10
  }
})

const emit = defineEmits(['update', 'delete', 'move', 'resize', 'select-exclusive'])

const selected = computed({
  get: () => props.clip.selected || false,
  set: (value) => {
    emit('update', props.clip.id, { selected: value })
  }
})
const isDragging = ref(false)
const isResizing = ref(false)
const contextMenuVisible = ref(false)
const resizeDirection = ref('')
const waveformData = ref([])

// 计算音频片段尺寸
const clipWidth = computed(() => {
  return Math.max(props.clip.duration * props.pixelsPerSecond, 20)
})

const clipHeight = computed(() => {
  return 44 // 默认音频片段高度
})

// 根据音轨类型确定波形颜色
const waveformColor = computed(() => {
  switch (props.trackType) {
    case 'dialogue':
      return '#1890ff'
    case 'environment':
      return '#52c41a'
    case 'background':
      return '#fa8c16'
    default:
      return '#1890ff'
  }
})

// 计算样式
const clipStyle = computed(() => {
  // 使用绝对像素定位，基于pixelsPerSecond比例
  const left = props.clip.startTime * props.pixelsPerSecond
  const width = Math.max(props.clip.duration * props.pixelsPerSecond, 20)
  
  return {
    left: `${left}px`,
    width: `${width}px`
  }
})

const fadeInStyle = computed(() => {
  const fadeInWidth = (props.clip.fadeIn / props.clip.duration) * 100
  return {
    width: `${Math.min(fadeInWidth, 25)}%`
  }
})

const fadeOutStyle = computed(() => {
  const fadeOutWidth = (props.clip.fadeOut / props.clip.duration) * 100
  return {
    width: `${Math.min(fadeOutWidth, 25)}%`
  }
})

// 拖拽相关
let dragStartX = 0
let dragStartTime = 0
let mouseMoveHandler = null
let mouseUpHandler = null

function selectClip(event) {
  if (event.button === 0) { // 左键点击
    // 如果按住Ctrl/Cmd键，则切换选中状态，否则清除其他选中并选中当前
    if (event.ctrlKey || event.metaKey) {
      selected.value = !selected.value
    } else {
      // 触发清除其他选中状态的事件
      emit('select-exclusive', props.clip.id)
      selected.value = true
    }
  }
}

function startDrag(event) {
  if (event.button !== 0) return // 只响应左键
  
  event.preventDefault()
  event.stopPropagation() // 阻止触发click事件
  
  isDragging.value = true
  if (!selected.value) {
    selected.value = true
  }
  
  dragStartX = event.clientX
  dragStartTime = props.clip.startTime
  
  // 添加全局鼠标事件监听
  mouseMoveHandler = handleMouseMove
  mouseUpHandler = handleMouseUp
  
  document.addEventListener('mousemove', mouseMoveHandler)
  document.addEventListener('mouseup', mouseUpHandler)
}

function handleMouseMove(event) {
  if (!isDragging.value && !isResizing.value) return
  
  const deltaX = event.clientX - dragStartX
  const deltaTime = deltaX / props.pixelsPerSecond
  
  if (isDragging.value) {
    // 拖拽移动
    const newStartTime = Math.max(0, dragStartTime + deltaTime)
    emit('move', props.clip.id, newStartTime)
  } else if (isResizing.value) {
    // 调整大小
    handleResize(deltaTime)
  }
}

function handleMouseUp() {
  isDragging.value = false
  isResizing.value = false
  resizeDirection.value = ''
  
  // 移除全局事件监听
  if (mouseMoveHandler) {
    document.removeEventListener('mousemove', mouseMoveHandler)
    document.removeEventListener('mouseup', mouseUpHandler)
    mouseMoveHandler = null
    mouseUpHandler = null
  }
}

// 调整大小相关
function startResize(direction) {
  event.preventDefault()
  event.stopPropagation()
  
  isResizing.value = true
  resizeDirection.value = direction
  dragStartX = event.clientX
  
  // 添加全局鼠标事件监听
  mouseMoveHandler = handleMouseMove
  mouseUpHandler = handleMouseUp
  
  document.addEventListener('mousemove', mouseMoveHandler)
  document.addEventListener('mouseup', mouseUpHandler)
}

function handleResize(deltaTime) {
  if (resizeDirection.value === 'left') {
    // 左侧调整：改变开始时间和持续时间
    const newStartTime = Math.max(0, dragStartTime + deltaTime)
    const newDuration = props.clip.duration + (dragStartTime - newStartTime)
    
    if (newDuration > 0.1) {
      emit('update', props.clip.id, {
        startTime: newStartTime,
        duration: newDuration
      })
    }
  } else if (resizeDirection.value === 'right') {
    // 右侧调整：只改变持续时间
    const newDuration = Math.max(0.1, props.clip.duration + deltaTime)
    emit('resize', props.clip.id, newDuration)
  }
}

// 其他操作
function editClip() {
  // TODO: 打开编辑对话框
  message.info('编辑功能开发中...')
}

function playClip() {
  try {
    // 构建音频文件URL
    const audioUrl = `/api/v1/sound-editor/audio-files/download/${props.clip.fileId}`
    
    // 创建音频元素
    const audio = new Audio(audioUrl)
    
    audio.addEventListener('canplay', () => {
      audio.play()
      message.success(`播放音频片段: ${props.clip.filename}`)
    })
    
    audio.addEventListener('error', (e) => {
      console.error('音频播放失败:', e)
      message.error(`播放失败: ${props.clip.filename}`)
    })
    
    // 开始加载音频
    audio.load()
    
  } catch (error) {
    console.error('播放音频片段失败:', error)
    message.error('播放失败')
  }
}

function showContextMenu(event) {
  contextMenuVisible.value = true
  selected.value = true
}

function handleContextMenu({ key }) {
  switch (key) {
    case 'edit':
      editClip()
      break
    case 'copy':
      copyClip()
      break
    case 'split':
      splitClip()
      break
    case 'delete':
      deleteClip()
      break
  }
  contextMenuVisible.value = false
}

function copyClip() {
  // TODO: 复制片段
  message.info('复制功能开发中...')
}

function splitClip() {
  // TODO: 分割片段
  message.info('分割功能开发中...')
}

function deleteClip() {
  emit('delete', props.clip.id)
}

// 获取弹出容器
function getPopupContainer() {
  return document.body || document.documentElement
}

// 全局点击事件处理
function handleGlobalClick(event) {
  // 如果点击的不是音频片段、项目信息面板或模态框，则取消选中
  if (!event.target.closest('.audio-clip') && 
      !event.target.closest('.project-panel') &&
      !event.target.closest('.clip-details') &&
      !event.target.closest('.ant-modal')) {
    selected.value = false
  }
}

// 加载波形数据
async function loadWaveformData() {
  if (!props.clip.fileId) return
  
  try {
    // fileId现在直接存储文件ID
    const fileId = props.clip.fileId
    
    if (fileId) {
      const result = await getAudioWaveform(fileId, Math.round(clipWidth.value), Math.round(clipHeight.value - 16))
      if (result.success) {
        waveformData.value = result.data.waveform
      }
    }
  } catch (error) {
    console.warn('加载波形数据失败:', error)
  }
}

// 监听尺寸变化重新加载波形
watch([clipWidth, clipHeight], () => {
  if (waveformData.value.length > 0) {
    loadWaveformData()
  }
})

// 生命周期
onMounted(() => {
  document.addEventListener('click', handleGlobalClick)
  loadWaveformData()
})

onUnmounted(() => {
  document.removeEventListener('click', handleGlobalClick)
  
  // 清理拖拽事件监听
  if (mouseMoveHandler) {
    document.removeEventListener('mousemove', mouseMoveHandler)
    document.removeEventListener('mouseup', mouseUpHandler)
  }
})
</script>

<style scoped>
.audio-clip {
  position: absolute;
  top: 8px;
  bottom: 8px;
  background: #e6f7ff;
  border: 1px solid #91d5ff;
  border-radius: 4px;
  cursor: move;
  overflow: hidden;
  transition: all 0.2s ease;
  user-select: none;
}

.audio-clip:hover {
  border-color: #40a9ff;
  box-shadow: 0 2px 8px rgba(64, 169, 255, 0.3);
}

.audio-clip.selected {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.audio-clip.dragging {
  opacity: 0.8;
  z-index: 10;
}

/* 不同音轨类型的颜色 */
.audio-clip.dialogue {
  background: #e6f7ff;
  border-color: #91d5ff;
}

.audio-clip.environment {
  background: #f6ffed;
  border-color: #b7eb8f;
}

.audio-clip.background {
  background: #fff2e8;
  border-color: #ffbb96;
}

.waveform-background {
  position: absolute;
  top: 8px;
  left: 8px;
  right: 8px;
  bottom: 8px;
  opacity: 0.3;
  pointer-events: none;
  overflow: hidden;
}

.clip-content {
  padding: 4px 8px;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  position: relative;
  z-index: 1;
}

.clip-name {
  font-size: 12px;
  font-weight: 500;
  line-height: 1.2;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clip-text {
  font-size: 10px;
  color: #333;
  line-height: 1.2;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.clip-character {
  font-size: 10px;
  color: #1890ff;
  font-weight: 500;
}

.volume-indicator {
  position: absolute;
  top: 2px;
  right: 2px;
  font-size: 10px;
  color: #333;
  background: rgba(255, 255, 255, 0.9);
  padding: 1px 3px;
  border-radius: 2px;
}

.fade-in,
.fade-out {
  position: absolute;
  top: 0;
  bottom: 0;
  background: linear-gradient(to right, transparent, rgba(0, 0, 0, 0.1));
  pointer-events: none;
}

.fade-in {
  left: 0;
}

.fade-out {
  right: 0;
  background: linear-gradient(to left, transparent, rgba(0, 0, 0, 0.1));
}

.resize-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 4px;
  background: transparent;
  cursor: ew-resize;
  opacity: 0;
  transition: opacity 0.2s;
}

.resize-handle:hover,
.audio-clip:hover .resize-handle {
  opacity: 1;
  background: #1890ff;
}

.resize-left {
  left: 0;
}

.resize-right {
  right: 0;
}

.clip-controls {
  position: absolute;
  top: 2px;
  left: 2px;
  opacity: 0;
  transition: opacity 0.2s;
}

.audio-clip:hover .clip-controls {
  opacity: 1;
}
</style> 