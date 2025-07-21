<template>
  <div class="professional-timeline">
    <!-- 专业时间轴组件 -->
    <TimeLine
      ref="timelineRef"
      :initTime="currentTimeString"
      :initZoomIndex="zoomIndex"
      :enableZoom="true"
      :enableDrag="true"
      :showCenterLine="true"
      :showHoverTime="true"
      :timeSegments="timeSegments"
      :backgroundColor="#1a1a1a"
      :textColor="#ffffff"
      :hoverTextColor="#52c41a"
      :lineColor="#ffffff"
      :centerLineStyle="centerLineStyle"
      @timeChange="handleTimeChange"
      @dragTimeChange="handleDragTimeChange"
      @click_timeSegments="handleClickSegments"
      @click_timeline="handleClickTimeline"
      class="timeline-container"
    />
  </div>
</template>

<script>
  import { ref, computed, watch, onMounted } from 'vue'
  import dayjs from 'dayjs'

  export default {
    name: 'ProfessionalTimeline',
    props: {
      currentTime: {
        type: Number,
        default: 0
      },
      totalDuration: {
        type: Number,
        default: 300 // 默认5分钟
      },
      tracks: {
        type: Array,
        default: () => []
      },
      zoomLevel: {
        type: Number,
        default: 1
      }
    },
    emits: ['time-change', 'segment-click', 'timeline-click'],
    setup(props, { emit }) {
      const timelineRef = ref(null)

      // 将当前时间转换为日期时间字符串
      const currentTimeString = computed(() => {
        const baseDate = dayjs('2024-01-01 00:00:00')
        return baseDate.add(props.currentTime, 'second').format('YYYY-MM-DD HH:mm:ss')
      })

      // 缩放级别映射
      const zoomIndex = computed(() => {
        // 映射zoomLevel到时间轴组件的缩放级别
        if (props.zoomLevel <= 0.5) return 0 // 半小时
        if (props.zoomLevel <= 1) return 1 // 1小时
        if (props.zoomLevel <= 2) return 2 // 2小时
        if (props.zoomLevel <= 4) return 3 // 6小时
        return 4 // 12小时
      })

      // 中间线样式
      const centerLineStyle = {
        width: 2,
        color: '#ff4d4f'
      }

      // 将轨道转换为时间段
      const timeSegments = computed(() => {
        const segments = []
        const baseDate = dayjs('2024-01-01 00:00:00')

        props.tracks.forEach((track, trackIndex) => {
          if (track.segments) {
            track.segments.forEach((segment, segmentIndex) => {
              segments.push({
                name: segment.name || `片段${segmentIndex + 1}`,
                beginTime: baseDate.add(segment.startTime, 'second').valueOf(),
                endTime: baseDate.add(segment.endTime, 'second').valueOf(),
                color: getTrackColor(trackIndex),
                startRatio: 0.1 + trackIndex * 0.2, // 每个轨道不同高度
                endRatio: 0.3 + trackIndex * 0.2,
                trackIndex: trackIndex,
                segmentData: segment
              })
            })
          }
        })

        return segments
      })

      // 获取轨道颜色
      const getTrackColor = (trackIndex) => {
        const colors = ['#1890ff', '#52c41a', '#faad14', '#f5222d', '#722ed1', '#fa8c16']
        return colors[trackIndex % colors.length]
      }

      // 时间变化处理
      const handleTimeChange = (timeString) => {
        const baseDate = dayjs('2024-01-01 00:00:00')
        const currentDate = dayjs(timeString)
        const seconds = currentDate.diff(baseDate, 'second')
        emit('time-change', seconds)
      }

      // 拖拽时间变化处理
      const handleDragTimeChange = (timeString) => {
        handleTimeChange(timeString)
      }

      // 点击时间段处理
      const handleClickSegments = (segments) => {
        if (segments.length > 0) {
          const segment = segments[0]
          emit('segment-click', segment.segmentData, segment.trackIndex)
        }
      }

      // 点击时间轴处理
      const handleClickTimeline = (timestamp, dateString, x) => {
        emit('timeline-click', timestamp, dateString, x)
        handleTimeChange(dateString)
      }

      // 监听时间变化，更新时间轴
      watch(
        () => props.currentTime,
        (newTime) => {
          if (timelineRef.value) {
            const baseDate = dayjs('2024-01-01 00:00:00')
            const timeString = baseDate.add(newTime, 'second').format('YYYY-MM-DD HH:mm:ss')
            timelineRef.value.setTime(timeString)
          }
        }
      )

      return {
        timelineRef,
        currentTimeString,
        zoomIndex,
        centerLineStyle,
        timeSegments,
        handleTimeChange,
        handleDragTimeChange,
        handleClickSegments,
        handleClickTimeline
      }
    }
  }
</script>

<style scoped>
  .professional-timeline {
    width: 100%;
    height: 80px;
    background: #1a1a1a;
    border-radius: 4px;
    overflow: hidden;
  }

  .timeline-container {
    width: 100%;
    height: 100%;
  }

  /* 覆盖时间轴组件的默认样式 */
  :deep(.timeline-container) {
    background: #1a1a1a !important;
  }

  :deep(.timeline-container .time-axis) {
    color: #ffffff !important;
  }

  :deep(.timeline-container .time-segment) {
    border-radius: 3px;
  }

  :deep(.timeline-container .hover-time) {
    background: rgba(0, 0, 0, 0.8);
    color: #52c41a;
    border-radius: 4px;
    padding: 2px 6px;
    font-size: 12px;
  }
</style>
