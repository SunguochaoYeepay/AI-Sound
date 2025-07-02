<template>
  <div class="timeline-container">
    <!-- 工具栏 - 包含缩放控制 -->
    <div class="timeline-toolbar">
      <div class="toolbar-left">
        <span class="toolbar-title">时间轴</span>
      </div>
      <div class="toolbar-right">
        <!-- 缩放控制 -->
        <div class="zoom-controls">
          <span class="zoom-label">缩放:</span>
          
          <!-- 缩放滑块 -->
          <div class="zoom-slider-container">
            <a-slider
              :value="zoomLevel"
              :min="minZoom"
              :max="maxZoom"
              :step="0.01"
              :tooltip-formatter="(value) => `${Math.round(value * 100)}%`"
              @change="$emit('zoom-change', $event)"
              style="width: 150px; margin: 0 12px;"
            />
          </div>
          
          <!-- 缩放显示 -->
          <div class="zoom-display">
            <span class="zoom-percentage">{{ Math.round(zoomLevel * 100) }}%</span>
          </div>
          
          <!-- 当前显示范围 -->
          <span class="view-range">显示: {{ Math.round(viewDuration) }}s</span>
        </div>
      </div>
    </div>

    <!-- 时间轴主体区域 -->
    <div class="timeline-main">
      <!-- 时间标尺 -->
      <div class="timeline-ruler">
        <!-- 左侧固定区域 -->
        <div class="ruler-left-space"></div>
        <!-- 可滚动的时间标记区域 -->
        <div class="ruler-scroll-container" ref="rulerScrollContainer">
          <div class="time-markers" :style="{ width: timelineWidth + 'px' }">
            <div
              v-for="marker in timeMarkers"
              :key="marker.time"
              class="time-marker"
              :style="{ left: marker.time * pixelsPerSecond + 'px' }"
            >
              <span class="time-label">{{ formatTime(marker.time) }}</span>
            </div>
            <!-- 播放头 -->
            <div 
              class="playhead" 
              :style="{ left: currentTime * pixelsPerSecond + 'px' }"
            ></div>
          </div>
        </div>
      </div>

      <!-- 音轨容器 -->
      <div class="tracks-scroll-container" ref="tracksScrollContainer" @scroll="handleTimelineScroll">
        <div class="tracks-wrapper">
          <!-- 左侧音轨控制面板 -->
          <div class="tracks-controls">
            <div v-for="track in tracks" :key="track.id" class="track-control">
              <div class="track-color-bar" :style="{ backgroundColor: track.color }"></div>
              <div class="track-info">
                <span class="track-name">{{ track.name }}</span>
                <span class="track-type">{{ track.type }}</span>
              </div>
            </div>
          </div>
          
          <!-- 右侧音轨内容区域 -->
          <div class="tracks-content" :style="{ width: timelineWidth + 'px' }">
            <TrackEditor
              v-for="track in tracks"
              :key="track.id"
              :track="track"
              :viewDuration="viewDuration"
              :pixelsPerSecond="pixelsPerSecond"
              :currentTime="currentTime"
              :timelineWidth="timelineWidth"
              @update-track="(...args) => $emit('update-track', ...args)"
              @update-clip="(...args) => $emit('update-clip', ...args)"
              @delete-clip="(...args) => $emit('delete-clip', ...args)"
              @add-clip="(...args) => $emit('add-clip', ...args)"
              @select-exclusive="(...args) => $emit('select-exclusive', ...args)"
            />
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import TrackEditor from '../tracks/TrackEditor.vue'

// Props
const props = defineProps({
  tracks: {
    type: Array,
    default: () => []
  },
  currentTime: {
    type: Number,
    default: 0
  },
  zoomLevel: {
    type: Number,
    default: 1
  },
  viewDuration: {
    type: Number,
    default: 60
  },
  pixelsPerSecond: {
    type: Number,
    default: 50
  },
  timelineWidth: {
    type: Number,
    default: 3000
  },
  totalDuration: {
    type: Number,
    default: 60
  },
  minZoom: {
    type: Number,
    default: 0.25
  },
  maxZoom: {
    type: Number,
    default: 8
  }
})

// Emits
const emit = defineEmits([
  'zoom-change',
  'timeline-scroll',
  'update-track',
  'update-clip',
  'delete-clip',
  'add-clip',
  'select-exclusive'
])

// 模板引用
const rulerScrollContainer = ref(null)
const tracksScrollContainer = ref(null)

// 时间标记计算
const timeMarkers = computed(() => {
  const markers = []
  const totalDuration = Math.max(props.totalDuration || 60, props.viewDuration)
  
  // 根据缩放级别动态调整时间刻度间隔
  let step
  if (props.zoomLevel >= 4) {
    step = 0.5  // 高度放大时显示0.5秒间隔
  } else if (props.zoomLevel >= 2) {
    step = 1    // 中度放大时显示1秒间隔
  } else if (props.zoomLevel >= 1) {
    step = 5    // 默认显示5秒间隔
  } else if (props.zoomLevel >= 0.5) {
    step = 10   // 缩小时显示10秒间隔
  } else {
    step = 30   // 高度缩小时显示30秒间隔
  }
  
  for (let time = 0; time <= totalDuration; time += step) {
    markers.push({ time })
  }
  return markers
})

// 时间轴滚动同步
function handleTimelineScroll(event) {
  const scrollLeft = event.target.scrollLeft
  if (rulerScrollContainer.value) {
    rulerScrollContainer.value.scrollLeft = scrollLeft
  }
  emit('timeline-scroll', scrollLeft)
}

// 格式化时间
function formatTime(seconds) {
  if (!seconds || seconds < 0) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}

// 暴露方法供父组件调用
defineExpose({
  rulerScrollContainer,
  tracksScrollContainer
})
</script>

<style scoped>
.timeline-container {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #1e1e1e;
  border-radius: 8px;
  border: 1px solid #333;
  overflow: hidden;
}

/* 时间轴工具栏 */
.timeline-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #2a2a2a;
  border-bottom: 1px solid #333;
  padding: 8px 16px;
  height: 50px;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-title {
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

/* 时间轴主体区域 */
.timeline-main {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.timeline-ruler {
  height: 40px;
  display: flex;
  background: #2a2a2a;
  border-bottom: 1px solid #333;
}

.ruler-left-space {
  width: 200px;
  background: #333;
  border-right: 1px solid #444;
}

.ruler-scroll-container {
  flex: 1;
  overflow-x: auto;
  overflow-y: hidden;
}

.ruler-scroll-container::-webkit-scrollbar {
  display: none; /* 隐藏滚动条，因为主滚动条在下面 */
}

.time-markers {
  position: relative;
  height: 100%;
  flex: 1;
}

.time-marker {
  position: absolute;
  top: 0;
  height: 100%;
  border-left: 1px solid #444;
  padding-left: 4px;
  display: flex;
  align-items: center;
}

.time-label {
  font-size: 12px;
  color: #999;
}

.playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 2px;
  background: #ff4d4f;
  z-index: 10;
  pointer-events: none;
  transition: left 0.1s ease;
}

.playhead::before {
  content: '';
  position: absolute;
  top: -6px;
  left: -6px;
  width: 14px;
  height: 14px;
  background: #ff4d4f;
  border-radius: 50%;
  border: 2px solid white;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
}

.tracks-scroll-container {
  flex: 1;
  overflow: auto;
  background: #1e1e1e;
}

.tracks-wrapper {
  display: flex;
  min-height: 100%;
}

.tracks-controls {
  width: 200px;
  background: #333;
  border-right: 1px solid #444;
  flex-shrink: 0;
}

.tracks-content {
  flex: 1;
  min-width: 0;
}

.track-control {
  height: 60px;
  padding: 8px 12px;
  border-bottom: 1px solid #444;
  display: flex;
  align-items: center;
  position: relative;
}

.track-color-bar {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
}

.track-info {
  flex: 1;
}

.track-name {
  color: #fff;
  font-size: 13px;
  font-weight: 500;
  display: block;
  margin-bottom: 4px;
}

.track-type {
  color: #999;
  font-size: 11px;
  text-transform: uppercase;
}

.zoom-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.zoom-slider-container {
  display: flex;
  align-items: center;
}

.zoom-display {
  display: flex;
  align-items: center;
}

.zoom-percentage {
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  min-width: 50px;
  text-align: center;
}

.zoom-label,
.view-range {
  color: #ccc;
  font-size: 12px;
  white-space: nowrap;
}

.view-range {
  background: #2a2a2a;
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #444;
}
</style>