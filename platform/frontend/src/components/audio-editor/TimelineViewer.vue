<template>
  <div class="timeline-viewer">
    <!-- 时间轴头部：时间刻度 -->
    <div class="timeline-ruler">
      <div class="ruler-offset"></div>
      <div class="ruler-content">
        <div
          v-for="(mark, index) in timeMarks"
          :key="index"
          class="time-mark"
          :style="{ left: mark.position + '%' }"
        >
          <div class="time-tick"></div>
          <span class="time-label">{{ mark.time }}</span>
        </div>
      </div>
    </div>

    <!-- 轨道内容区域 -->
    <div class="tracks-content-panel" @drop="$emit('track-drop', $event)" @dragover.prevent>
      <div
        v-for="(track, index) in tracks"
        :key="track.id"
        class="track-content-row"
        :class="{
          selected: selectedTrack === track,
          hidden: track.hidden,
          locked: track.locked
        }"
      >
        <!-- 轨道背景 -->
        <div class="track-background"></div>

        <!-- 音频片段 -->
        <div
          v-for="segment in track.segments"
          :key="segment.id"
          class="audio-segment"
          :class="{
            selected: selectedSegment === segment,
            locked: track.locked
          }"
          :style="getSegmentStyle(segment)"
          @click="$emit('select-segment', segment)"
          @dblclick="$emit('edit-segment', segment)"
          draggable="true"
          @dragstart="handleSegmentDragStart($event, segment)"
        >
          <!-- 波形显示 -->
          <WaveformViewer
            v-if="segment.audioUrl"
            :audio-url="segment.audioUrl"
            :container-width="getSegmentWidth(segment)"
            class="segment-waveform"
          />

          <!-- 片段信息 -->
          <div class="segment-info">
            <span class="segment-name">{{ segment.name }}</span>
            <span class="segment-time">{{ formatTime(segment.duration) }}</span>
          </div>

          <!-- 淡入淡出指示器 -->
          <div
            v-if="segment.fadeIn"
            class="fade-in"
            :style="{ width: getFadeWidth(segment.fadeIn, segment.duration) }"
          ></div>
          <div
            v-if="segment.fadeOut"
            class="fade-out"
            :style="{ width: getFadeWidth(segment.fadeOut, segment.duration) }"
          ></div>
        </div>
      </div>

      <!-- 播放头 -->
      <div
        class="playhead"
        :style="{ left: playheadPosition + '%' }"
        @mousedown="startPlayheadDrag"
      ></div>
    </div>
  </div>
</template>

<script>
  import { computed } from 'vue'
  import WaveformViewer from '../WaveformViewer.vue'

  export default {
    name: 'TimelineViewer',
    components: {
      WaveformViewer
    },
    props: {
      tracks: {
        type: Array,
        default: () => []
      },
      selectedTrack: {
        type: Object,
        default: null
      },
      selectedSegment: {
        type: Object,
        default: null
      },
      zoomLevel: {
        type: Number,
        default: 1
      },
      currentTime: {
        type: Number,
        default: 0
      },
      totalDuration: {
        type: Number,
        default: 300
      }
    },
    emits: [
      'select-segment',
      'edit-segment',
      'track-drop',
      'playhead-change',
      'segment-drag-start'
    ],
    setup(props, { emit }) {
      // 计算属性
      const timeMarks = computed(() => {
        const marks = []
        const markCount = 20 // 增加刻度密度

        for (let i = 0; i <= markCount; i++) {
          const time = (props.totalDuration / markCount) * i
          const position = (100 / markCount) * i

          marks.push({
            time: formatTime(time),
            position: position
          })
        }

        return marks
      })

      const playheadPosition = computed(() => {
        return (props.currentTime / props.totalDuration) * 100
      })

      // 方法
      const getSegmentStyle = (segment) => {
        const startPercent = (segment.startTime / props.totalDuration) * 100
        const widthPercent = ((segment.endTime - segment.startTime) / props.totalDuration) * 100

        return {
          left: `${startPercent}%`,
          width: `${widthPercent}%`
        }
      }

      const getSegmentWidth = (segment) => {
        return ((segment.endTime - segment.startTime) / props.totalDuration) * 100
      }

      const getFadeWidth = (fadeTime, duration) => {
        return `${(fadeTime / duration) * 100}%`
      }

      const handleSegmentDragStart = (event, segment) => {
        emit('segment-drag-start', { event, segment })
      }

      const startPlayheadDrag = (event) => {
        const startDrag = (e) => {
          const rect = event.target.parentElement.getBoundingClientRect()
          const relativeX = e.clientX - rect.left
          const newTime = (relativeX / rect.width) * props.totalDuration

          emit('playhead-change', Math.max(0, Math.min(newTime, props.totalDuration)))
        }

        const stopDrag = () => {
          document.removeEventListener('mousemove', startDrag)
          document.removeEventListener('mouseup', stopDrag)
        }

        document.addEventListener('mousemove', startDrag)
        document.addEventListener('mouseup', stopDrag)
      }

      const formatTime = (seconds) => {
        if (!seconds || isNaN(seconds)) return '00:00'
        const mins = Math.floor(seconds / 60)
        const secs = Math.floor(seconds % 60)
        return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
      }

      return {
        timeMarks,
        playheadPosition,
        getSegmentStyle,
        getSegmentWidth,
        getFadeWidth,
        handleSegmentDragStart,
        startPlayheadDrag,
        formatTime
      }
    }
  }
</script>

<style scoped>
  /* 时间轴主容器 */
  .timeline-viewer {
    height: 100%;
    display: flex;
    flex-direction: column;
    background: #2d2d2d;
    overflow: hidden;
  }

  /* 时间刻度尺 */
  .timeline-ruler {
    height: 30px;
    background: #1a1a1a;
    border-bottom: 1px solid #4a4a4a;
    display: flex;
    position: relative;
  }

  .ruler-offset {
    width: 0px; /* 对应轨道控制面板宽度 */
    background: #1a1a1a;
  }

  .ruler-content {
    flex: 1;
    position: relative;
    background: #1a1a1a;
  }

  .time-mark {
    position: absolute;
    height: 100%;
    display: flex;
    flex-direction: column;
    align-items: center;
  }

  .time-tick {
    width: 1px;
    height: 8px;
    background: #6b7280;
    margin-top: 2px;
  }

  .time-label {
    font-size: 10px;
    color: #9ca3af;
    margin-top: 2px;
    font-family:
      'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
  }

  /* 轨道内容面板 */
  .tracks-content-panel {
    flex: 1;
    background: #2d2d2d;
    overflow-y: auto;
    position: relative;
  }

  .track-content-row {
    height: 60px;
    position: relative;
    border-bottom: 1px solid #4a4a4a;
    background: #383838;
    overflow: hidden;
  }

  .track-content-row.selected {
    background: #2563eb;
    border-color: #3b82f6;
  }

  .track-content-row.hidden {
    opacity: 0.3;
  }

  .track-content-row.locked {
    filter: grayscale(50%);
    pointer-events: none;
  }

  .track-background {
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
      90deg,
      transparent 0px,
      transparent 49px,
      #4a4a4a 49px,
      #4a4a4a 50px
    );
    opacity: 0.3;
  }

  /* 音频片段 */
  .audio-segment {
    position: absolute;
    top: 8px;
    height: 44px;
    background: linear-gradient(135deg, #3b82f6 0%, #1e40af 100%);
    border: 1px solid #2563eb;
    border-radius: 4px;
    cursor: grab;
    overflow: hidden;
    transition: all 0.2s;
    display: flex;
    flex-direction: column;
  }

  .audio-segment:hover {
    transform: translateY(-1px);
    box-shadow: 0 4px 8px rgba(59, 130, 246, 0.3);
  }

  .audio-segment.selected {
    border-color: #fbbf24;
    box-shadow: 0 0 0 2px rgba(251, 191, 36, 0.3);
  }

  .audio-segment.locked {
    cursor: not-allowed;
    opacity: 0.6;
  }

  .audio-segment:active {
    cursor: grabbing;
  }

  /* 波形显示 */
  .segment-waveform {
    flex: 1;
    background: rgba(255, 255, 255, 0.1);
  }

  /* 片段信息 */
  .segment-info {
    position: absolute;
    top: 2px;
    left: 4px;
    right: 4px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    font-size: 10px;
    color: white;
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.8);
    pointer-events: none;
  }

  .segment-name {
    font-weight: 500;
    max-width: 60%;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .segment-time {
    font-family:
      'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
    opacity: 0.8;
  }

  /* 淡入淡出效果 */
  .fade-in,
  .fade-out {
    position: absolute;
    top: 0;
    bottom: 0;
    background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 100%);
    pointer-events: none;
  }

  .fade-in {
    left: 0;
    background: linear-gradient(90deg, transparent 0%, rgba(255, 255, 255, 0.2) 100%);
  }

  .fade-out {
    right: 0;
    background: linear-gradient(90deg, rgba(255, 255, 255, 0.2) 0%, transparent 100%);
  }

  /* 播放头 */
  .playhead {
    position: absolute;
    top: 0;
    bottom: 0;
    width: 2px;
    background: #ef4444;
    z-index: 10;
    cursor: ew-resize;
    box-shadow: 0 0 4px rgba(239, 68, 68, 0.8);
  }

  .playhead::before {
    content: '';
    position: absolute;
    top: -6px;
    left: -4px;
    width: 10px;
    height: 12px;
    background: #ef4444;
    clip-path: polygon(50% 100%, 0 0, 100% 0);
  }

  /* 暗黑模式适配 */
  [data-theme='dark'] .timeline-ruler,
  [data-theme='dark'] .ruler-offset,
  [data-theme='dark'] .ruler-content {
    background: #1a1a1a;
  }

  [data-theme='dark'] .tracks-content-panel {
    background: #2d2d2d;
  }

  [data-theme='dark'] .track-content-row {
    background: #383838;
    border-color: #434343;
  }

  [data-theme='dark'] .track-content-row.selected {
    background: #1e3a8a;
  }

  [data-theme='dark'] .audio-segment {
    background: linear-gradient(135deg, #1890ff 0%, #003a8c 100%);
    border-color: #1890ff;
  }
</style>
