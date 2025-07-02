<template>
  <div class="waveform-display" ref="containerRef">
    <canvas 
      ref="canvasRef" 
      :width="width" 
      :height="height"
      @mousedown="handleMouseDown"
      @mousemove="handleMouseMove"
      @mouseup="handleMouseUp"
      @click="handleClick"
      @contextmenu.prevent="handleRightClick"
    />
    
    <!-- 播放进度指示器 -->
    <div 
      v-if="showProgress" 
      class="progress-line"
      :style="{ left: `${progressPosition}px` }"
    />
    
    <!-- 选择区域 -->
    <div 
      v-if="selectionVisible" 
      class="selection-area"
      :style="{ 
        left: `${selectionStart}px`, 
        width: `${selectionWidth}px` 
      }"
    />
    
    <!-- 时间标记 -->
    <div v-if="showTimeMarkers" class="time-markers">
      <div 
        v-for="marker in timeMarkers"
        :key="marker.time"
        class="time-marker"
        :style="{ left: `${marker.position}px` }"
      >
        <span class="time-label">{{ formatTime(marker.time) }}</span>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, nextTick } from 'vue'

const props = defineProps({
  // 波形数据
  waveformData: {
    type: Array,
    default: () => []
  },
  // 画布尺寸
  width: {
    type: Number,
    default: 800
  },
  height: {
    type: Number,
    default: 100
  },
  // 颜色配置
  waveColor: {
    type: String,
    default: '#1890ff'
  },
  progressColor: {
    type: String,
    default: '#ff4d4f'
  },
  backgroundColor: {
    type: String,
    default: '#fafafa'
  },
  // 播放进度（0-1）
  progress: {
    type: Number,
    default: 0
  },
  // 音频时长（秒）
  duration: {
    type: Number,
    default: 0
  },
  // 显示控制
  showProgress: {
    type: Boolean,
    default: true
  },
  showTimeMarkers: {
    type: Boolean,
    default: true
  },
  // 交互控制
  interactive: {
    type: Boolean,
    default: true
  },
  // 选择模式
  selectionMode: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'seek',        // 拖拽进度
  'select',      // 选择区域
  'contextmenu'  // 右键菜单
])

// 引用
const containerRef = ref(null)
const canvasRef = ref(null)

// 状态
const isDrawing = ref(false)
const isDragging = ref(false)
const isSelecting = ref(false)
const selectionStart = ref(0)
const selectionEnd = ref(0)

// 计算属性
const progressPosition = computed(() => {
  return props.progress * props.width
})

const selectionVisible = computed(() => {
  return props.selectionMode && (selectionStart.value !== selectionEnd.value)
})

const selectionWidth = computed(() => {
  return Math.abs(selectionEnd.value - selectionStart.value)
})

const timeMarkers = computed(() => {
  if (!props.showTimeMarkers || props.duration <= 0) return []
  
  const markers = []
  const interval = getTimeInterval(props.duration)
  
  for (let time = 0; time <= props.duration; time += interval) {
    const position = (time / props.duration) * props.width
    markers.push({ time, position })
  }
  
  return markers
})

// 方法
function drawWaveform() {
  const canvas = canvasRef.value
  if (!canvas) return
  
  const ctx = canvas.getContext('2d')
  const { width, height } = props
  
  // 清空画布
  ctx.fillStyle = props.backgroundColor
  ctx.fillRect(0, 0, width, height)
  
  if (!props.waveformData || props.waveformData.length === 0) {
    // 显示空状态
    ctx.fillStyle = '#ccc'
    ctx.font = '14px Arial'
    ctx.textAlign = 'center'
    ctx.fillText('无波形数据', width / 2, height / 2)
    return
  }
  
  // 绘制波形
  ctx.fillStyle = props.waveColor
  ctx.beginPath()
  
  const barWidth = width / props.waveformData.length
  const middleY = height / 2
  
  props.waveformData.forEach((amplitude, index) => {
    const x = index * barWidth
    const barHeight = amplitude * middleY * 0.8 // 限制最大高度
    
    // 绘制上半部分
    ctx.fillRect(x, middleY - barHeight, Math.max(barWidth - 1, 1), barHeight)
    // 绘制下半部分（镜像）
    ctx.fillRect(x, middleY, Math.max(barWidth - 1, 1), barHeight)
  })
}

function getTimeInterval(duration) {
  if (duration <= 10) return 1
  if (duration <= 60) return 5
  if (duration <= 300) return 30
  if (duration <= 1800) return 60
  return 300
}

function formatTime(seconds) {
  const minutes = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${minutes}:${secs.toString().padStart(2, '0')}`
}

function getTimeFromPosition(x) {
  return (x / props.width) * props.duration
}

function getPositionFromTime(time) {
  return (time / props.duration) * props.width
}

// 事件处理
function handleMouseDown(event) {
  if (!props.interactive) return
  
  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  
  if (props.selectionMode) {
    isSelecting.value = true
    selectionStart.value = x
    selectionEnd.value = x
  } else {
    isDragging.value = true
    handleSeek(x)
  }
}

function handleMouseMove(event) {
  if (!props.interactive) return
  
  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  
  if (isSelecting.value) {
    selectionEnd.value = x
  } else if (isDragging.value) {
    handleSeek(x)
  }
}

function handleMouseUp(event) {
  if (!props.interactive) return
  
  if (isSelecting.value) {
    const startTime = getTimeFromPosition(Math.min(selectionStart.value, selectionEnd.value))
    const endTime = getTimeFromPosition(Math.max(selectionStart.value, selectionEnd.value))
    
    if (Math.abs(selectionEnd.value - selectionStart.value) > 5) {
      emit('select', { startTime, endTime })
    }
  }
  
  isSelecting.value = false
  isDragging.value = false
}

function handleClick(event) {
  if (!props.interactive || props.selectionMode) return
  
  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  handleSeek(x)
}

function handleSeek(x) {
  const time = getTimeFromPosition(x)
  emit('seek', time)
}

function handleRightClick(event) {
  if (!props.interactive) return
  
  const rect = canvasRef.value.getBoundingClientRect()
  const x = event.clientX - rect.left
  const time = getTimeFromPosition(x)
  
  emit('contextmenu', {
    time,
    position: { x: event.clientX, y: event.clientY }
  })
}

// 清除选择
function clearSelection() {
  selectionStart.value = 0
  selectionEnd.value = 0
}

// 设置选择区域
function setSelection(startTime, endTime) {
  selectionStart.value = getPositionFromTime(startTime)
  selectionEnd.value = getPositionFromTime(endTime)
}

// 暴露方法
defineExpose({
  clearSelection,
  setSelection
})

// 监听变化重绘
watch([
  () => props.waveformData,
  () => props.width,
  () => props.height,
  () => props.waveColor,
  () => props.backgroundColor
], () => {
  nextTick(() => {
    drawWaveform()
  })
})

// 生命周期
onMounted(() => {
  drawWaveform()
})
</script>

<style scoped>
.waveform-display {
  position: relative;
  display: inline-block;
  cursor: pointer;
  user-select: none;
}

.waveform-display canvas {
  display: block;
  border: 1px solid #e8e8e8;
  border-radius: 4px;
}

.progress-line {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #ff4d4f;
  pointer-events: none;
  z-index: 2;
}

.selection-area {
  position: absolute;
  top: 0;
  bottom: 0;
  background: rgba(24, 144, 255, 0.2);
  border: 1px solid #1890ff;
  pointer-events: none;
  z-index: 1;
}

.time-markers {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  height: 20px;
  pointer-events: none;
}

.time-marker {
  position: absolute;
  top: 0;
  height: 100%;
  border-left: 1px solid #d9d9d9;
}

.time-label {
  position: absolute;
  left: 4px;
  top: 2px;
  font-size: 12px;
  color: #666;
  white-space: nowrap;
}

/* 交互状态 */
.waveform-display:hover canvas {
  border-color: #1890ff;
}

.waveform-display.selecting {
  cursor: crosshair;
}

.waveform-display.dragging {
  cursor: grabbing;
}
</style>