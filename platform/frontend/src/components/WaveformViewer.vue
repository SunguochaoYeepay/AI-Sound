<template>
  <div class="waveform-viewer">
    <!-- 波形控制工具栏 -->
    <div class="waveform-toolbar">
      <div class="toolbar-left">
        <a-button-group size="small">
          <a-button @click="playPause" :icon="isPlaying ? 'pause' : 'play'" />
          <a-button @click="stop" icon="stop" />
          <a-button @click="skipBackward" icon="backward" />
          <a-button @click="skipForward" icon="forward" />
        </a-button-group>
        
        <div class="time-display">
          <span class="current-time">{{ formatTime(currentTime) }}</span>
          <span class="separator">/</span>
          <span class="total-time">{{ formatTime(duration) }}</span>
        </div>
      </div>
      
      <div class="toolbar-center">
        <div class="zoom-controls">
          <a-button size="small" @click="zoomOut" icon="minus" />
          <a-slider 
            v-model:value="zoomLevel" 
            :min="1" 
            :max="100" 
            :step="1"
            class="zoom-slider"
            @change="onZoomChange"
          />
          <a-button size="small" @click="zoomIn" icon="plus" />
          <span class="zoom-label">{{ zoomLevel }}%</span>
        </div>
      </div>
      
      <div class="toolbar-right">
        <a-button size="small" @click="toggleRegionMode" :type="regionMode ? 'primary' : 'default'">
          <template #icon><ScissorOutlined /></template>
          选区
        </a-button>
        <a-button size="small" @click="clearRegions">
          <template #icon><ClearOutlined /></template>
          清除
        </a-button>
        <div class="volume-control">
          <a-button size="small" @click="toggleMute" :icon="isMuted ? 'sound-muted' : 'sound'" />
          <a-slider 
            v-model:value="volume" 
            :min="0" 
            :max="100" 
            :step="1"
            class="volume-slider"
            @change="onVolumeChange"
          />
        </div>
      </div>
    </div>
    
    <!-- 波形显示区域 -->
    <div class="waveform-container" :class="{ 'loading': loading }">
      <div v-if="loading" class="loading-overlay">
        <a-spin size="large" />
        <div class="loading-text">加载音频文件中...</div>
      </div>
      
      <!-- WaveSurfer容器 -->
      <div ref="waveformRef" class="waveform-canvas"></div>
      
      <!-- 时间轴标尺 -->
      <div class="timeline-ruler">
        <div 
          v-for="(mark, index) in timeMarks" 
          :key="index"
          class="time-mark"
          :style="{ left: mark.position + '%' }"
        >
          <div class="mark-line"></div>
          <div class="mark-label">{{ formatTime(mark.time) }}</div>
        </div>
      </div>
    </div>
    
    <!-- 区域信息面板 -->
    <div v-if="selectedRegion" class="region-info-panel">
      <div class="panel-header">
        <h4>选区信息</h4>
        <a-button size="small" @click="closeRegionPanel" icon="close" />
      </div>
      <div class="panel-content">
        <div class="info-row">
          <label>开始时间:</label>
          <span>{{ formatTime(selectedRegion.start) }}</span>
        </div>
        <div class="info-row">
          <label>结束时间:</label>
          <span>{{ formatTime(selectedRegion.end) }}</span>
        </div>
        <div class="info-row">
          <label>持续时间:</label>
          <span>{{ formatTime(selectedRegion.end - selectedRegion.start) }}</span>
        </div>
        <div class="panel-actions">
          <a-button size="small" @click="playRegion">播放选区</a-button>
          <a-button size="small" @click="exportRegion">导出选区</a-button>
          <a-button size="small" @click="deleteRegion" danger>删除选区</a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, computed } from 'vue'
import { ScissorOutlined, ClearOutlined } from '@ant-design/icons-vue'
import WaveSurfer from 'wavesurfer.js'
import RegionsPlugin from 'wavesurfer.js/dist/plugins/regions.js'
import TimelinePlugin from 'wavesurfer.js/dist/plugins/timeline.js'
import { message } from 'ant-design-vue'

// Props
const props = defineProps({
  audioUrl: {
    type: String,
    required: true
  },
  height: {
    type: Number,
    default: 200
  },
  waveColor: {
    type: String,
    default: '#1890ff'
  },
  progressColor: {
    type: String,
    default: '#52c41a'
  },
  cursorColor: {
    type: String,
    default: '#ff4d4f'
  },
  responsive: {
    type: Boolean,
    default: true
  },
  normalize: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits([
  'ready',
  'play',
  'pause',
  'finish',
  'seek',
  'region-created',
  'region-selected',
  'region-updated',
  'region-removed'
])

// Refs
const waveformRef = ref(null)
const wavesurfer = ref(null)
const regionsPlugin = ref(null)
const timelinePlugin = ref(null)

// State
const loading = ref(false)
const isPlaying = ref(false)
const isMuted = ref(false)
const currentTime = ref(0)
const duration = ref(0)
const volume = ref(80)
const zoomLevel = ref(1)
const regionMode = ref(false)
const selectedRegion = ref(null)
const regions = ref([])

// Computed
const timeMarks = computed(() => {
  const marks = []
  const markCount = Math.min(10, Math.floor(duration.value / 10))
  for (let i = 0; i <= markCount; i++) {
    const time = (duration.value / markCount) * i
    const position = (time / duration.value) * 100
    marks.push({ time, position })
  }
  return marks
})

// Methods
const initWaveSurfer = async () => {
  if (!waveformRef.value) return
  
  loading.value = true
  
  try {
    // 创建插件实例
    regionsPlugin.value = RegionsPlugin.create({
      dragSelection: {
        slop: 5
      }
    })
    
    timelinePlugin.value = TimelinePlugin.create({
      height: 20,
      insertPosition: 'beforebegin',
      timeInterval: 10,
      primaryLabelInterval: 5,
      secondaryLabelInterval: 1,
      style: {
        fontSize: '10px',
        color: '#666'
      }
    })
    
    // 初始化WaveSurfer
    wavesurfer.value = WaveSurfer.create({
      container: waveformRef.value,
      height: props.height,
      waveColor: props.waveColor,
      progressColor: props.progressColor,
      cursorColor: props.cursorColor,
      cursorWidth: 2,
      responsive: props.responsive,
      normalize: props.normalize,
      backend: 'WebAudio',
      mediaControls: false,
      plugins: [regionsPlugin.value, timelinePlugin.value]
    })
    
    // 绑定事件
    setupEventListeners()
    
    // 加载音频
    await wavesurfer.value.load(props.audioUrl)
    
  } catch (error) {
    console.error('WaveSurfer初始化失败:', error)
    message.error('音频加载失败')
  } finally {
    loading.value = false
  }
}

const setupEventListeners = () => {
  if (!wavesurfer.value) return
  
  // 播放状态事件
  wavesurfer.value.on('ready', () => {
    duration.value = wavesurfer.value.getDuration()
    emit('ready', { duration: duration.value })
  })
  
  wavesurfer.value.on('play', () => {
    isPlaying.value = true
    emit('play')
  })
  
  wavesurfer.value.on('pause', () => {
    isPlaying.value = false
    emit('pause')
  })
  
  wavesurfer.value.on('finish', () => {
    isPlaying.value = false
    emit('finish')
  })
  
  wavesurfer.value.on('audioprocess', (time) => {
    currentTime.value = time
  })
  
  wavesurfer.value.on('seek', (progress) => {
    currentTime.value = progress * duration.value
    emit('seek', { time: currentTime.value, progress })
  })
  
  // 区域事件
  regionsPlugin.value.on('region-created', (region) => {
    regions.value.push(region)
    emit('region-created', region)
  })
  
  regionsPlugin.value.on('region-clicked', (region) => {
    selectedRegion.value = region
    emit('region-selected', region)
  })
  
  regionsPlugin.value.on('region-updated', (region) => {
    emit('region-updated', region)
  })
  
  regionsPlugin.value.on('region-removed', (region) => {
    regions.value = regions.value.filter(r => r.id !== region.id)
    if (selectedRegion.value && selectedRegion.value.id === region.id) {
      selectedRegion.value = null
    }
    emit('region-removed', region)
  })
}

// 播放控制
const playPause = () => {
  if (!wavesurfer.value) return
  wavesurfer.value.playPause()
}

const stop = () => {
  if (!wavesurfer.value) return
  wavesurfer.value.stop()
}

const skipBackward = () => {
  if (!wavesurfer.value) return
  const newTime = Math.max(0, currentTime.value - 10)
  wavesurfer.value.seekTo(newTime / duration.value)
}

const skipForward = () => {
  if (!wavesurfer.value) return
  const newTime = Math.min(duration.value, currentTime.value + 10)
  wavesurfer.value.seekTo(newTime / duration.value)
}

// 音量控制
const onVolumeChange = (value) => {
  if (!wavesurfer.value) return
  wavesurfer.value.setVolume(value / 100)
}

const toggleMute = () => {
  if (!wavesurfer.value) return
  isMuted.value = !isMuted.value
  wavesurfer.value.setMuted(isMuted.value)
}

// 缩放控制
const onZoomChange = (value) => {
  if (!wavesurfer.value) return
  wavesurfer.value.zoom(value)
}

const zoomIn = () => {
  zoomLevel.value = Math.min(100, zoomLevel.value + 10)
  onZoomChange(zoomLevel.value)
}

const zoomOut = () => {
  zoomLevel.value = Math.max(1, zoomLevel.value - 10)
  onZoomChange(zoomLevel.value)
}

// 区域控制
const toggleRegionMode = () => {
  regionMode.value = !regionMode.value
  if (regionsPlugin.value) {
    regionsPlugin.value.enableDragSelection(regionMode.value)
  }
}

const clearRegions = () => {
  if (regionsPlugin.value) {
    regionsPlugin.value.clearRegions()
    regions.value = []
    selectedRegion.value = null
  }
}

const closeRegionPanel = () => {
  selectedRegion.value = null
}

const playRegion = () => {
  if (selectedRegion.value && wavesurfer.value) {
    selectedRegion.value.play()
  }
}

const exportRegion = () => {
  if (selectedRegion.value) {
    // 导出选区逻辑
    message.info('导出功能开发中...')
  }
}

const deleteRegion = () => {
  if (selectedRegion.value) {
    selectedRegion.value.remove()
  }
}

// 工具函数
const formatTime = (seconds) => {
  if (!seconds || isNaN(seconds)) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 生命周期
onMounted(() => {
  initWaveSurfer()
})

onUnmounted(() => {
  if (wavesurfer.value) {
    wavesurfer.value.destroy()
  }
})

// 监听音频URL变化
watch(() => props.audioUrl, (newUrl) => {
  if (newUrl && wavesurfer.value) {
    loading.value = true
    wavesurfer.value.load(newUrl).finally(() => {
      loading.value = false
    })
  }
})
</script>

<style scoped>
.waveform-viewer {
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}

.waveform-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #d9d9d9;
}

.toolbar-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.time-display {
  font-family: 'Monaco', 'Menlo', 'Consolas', monospace;
  font-size: 14px;
  color: #666;
}

.separator {
  margin: 0 4px;
}

.toolbar-center {
  flex: 1;
  display: flex;
  justify-content: center;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 8px;
}

.zoom-slider {
  width: 120px;
}

.zoom-label {
  font-size: 12px;
  color: #666;
  min-width: 32px;
  text-align: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.volume-control {
  display: flex;
  align-items: center;
  gap: 8px;
}

.volume-slider {
  width: 80px;
}

.waveform-container {
  position: relative;
  min-height: 200px;
}

.loading-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(255, 255, 255, 0.8);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  z-index: 10;
}

.loading-text {
  margin-top: 16px;
  color: #666;
}

.waveform-canvas {
  position: relative;
}

.timeline-ruler {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 20px;
  pointer-events: none;
}

.time-mark {
  position: absolute;
  height: 100%;
}

.mark-line {
  width: 1px;
  height: 8px;
  background: #d9d9d9;
  margin-bottom: 2px;
}

.mark-label {
  font-size: 10px;
  color: #999;
  transform: translateX(-50%);
}

.region-info-panel {
  position: absolute;
  top: 12px;
  right: 12px;
  width: 240px;
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  z-index: 20;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h4 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
}

.panel-content {
  padding: 16px;
}

.info-row {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
  font-size: 12px;
}

.info-row label {
  color: #666;
}

.panel-actions {
  margin-top: 16px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .waveform-toolbar {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
  
  .toolbar-left,
  .toolbar-center,
  .toolbar-right {
    justify-content: center;
  }
  
  .region-info-panel {
    position: relative;
    top: auto;
    right: auto;
    width: 100%;
    margin-top: 12px;
  }
}
</style> 