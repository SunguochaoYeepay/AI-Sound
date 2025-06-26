<template>
  <div class="tracks-area">
    <!-- 轨道头部控制栏 -->
    <div class="tracks-header">
      <div class="tracks-title">轨道</div>
      <div class="header-controls">
        
        
        <!-- 缩放控制 -->
        <div class="zoom-controls">
          <span class="zoom-label">缩放</span>
          <a-slider
            :value="zoomLevel"
            :min="0.1"
            :max="5"
            :step="0.1"
            :style="{ width: '80px' }"
            size="small"
            :tooltip-formatter="(value) => `${Math.round(value * 100)}%`"
            @change="handleZoomChange"
          />
        </div>
      </div>
    </div>
    
    <!-- 简化时间显示区域 - 参考剪映设计 -->
    <div class="timeline-info">
      <div class="timeline-info-content" :style="{ marginLeft: '200px' }">
        <div class="project-info">
          <span class="duration-display">总时长: {{ formatTime(totalDuration) }}</span>
          <span class="current-time-display">当前: {{ formatTime(currentTime) }}</span>
          
          <!-- 动态编辑操作栏 - 仅在选中片段时显示 -->
          <transition name="slide-fade">
            <div v-if="selectedSegment" class="timeline-operations">
              <span class="selected-track-name">{{ getSelectedTrackName() }}</span>
              
              <!-- 基础编辑组 -->
              <a-button-group size="small" class="operation-group">
                <a-button 
                  type="text" 
                  @click="handleCopySegment"
                  title="复制片段 (Ctrl+C)"
                >
                  <template #icon><CopyOutlined /></template>
                  复制
                </a-button>
                <a-button 
                  type="text" 
                  @click="handleCutSegment"
                  title="剪切片段 (Ctrl+X)"
                >
                  <template #icon><ScissorOutlined /></template>
                  剪切
                </a-button>
                <a-button 
                  type="text" 
                  danger
                  @click="handleDeleteSegment"
                  title="删除片段 (Delete)"
                >
                  <template #icon><DeleteOutlined /></template>
                  删除
                </a-button>
              </a-button-group>
              
              <!-- 音频处理组 -->
              <a-button-group size="small" class="operation-group">
                <a-button 
                  type="text" 
                  @click="handleSplitSegment"
                  title="分割片段"
                >
                  <template #icon><VerticalRightOutlined /></template>
                  分割
                </a-button>
                <a-button 
                  type="text" 
                  @click="handleFadeEffect"
                  title="淡入淡出"
                >
                  <template #icon><SlidersOutlined /></template>
                  淡化
                </a-button>
              </a-button-group>
              
              <!-- 撤销重做组 -->
              <a-button-group size="small" class="operation-group">
                <a-button 
                  type="text" 
                  @click="handleUndo"
                  :disabled="!canUndo"
                  title="撤销 (Ctrl+Z)"
                >
                  <template #icon><UndoOutlined /></template>
                  撤销
                </a-button>
                <a-button 
                  type="text" 
                  @click="handleRedo"
                  :disabled="!canRedo"
                  title="重做 (Ctrl+Y)"
                >
                  <template #icon><RedoOutlined /></template>
                  重做
                </a-button>
              </a-button-group>
              
              <!-- 更多操作 -->
              <a-dropdown :trigger="['click']" placement="bottomRight">
                <a-button type="text" size="small" title="更多操作">
                  <template #icon><MoreOutlined /></template>
                  更多
                </a-button>
                <template #overlay>
                  <a-menu>
                    <a-menu-item @click="handleDuplicateSegment">
                      <template #icon><PlusOutlined /></template>
                      复制到新轨道
                    </a-menu-item>
                    <a-menu-item @click="handleNormalizeVolume">
                      <template #icon><SoundOutlined /></template>
                      音量标准化
                    </a-menu-item>
                    <a-menu-item @click="handleReverseSegment">
                      <template #icon><SwapOutlined /></template>
                      反向播放
                    </a-menu-item>
                    <a-menu-divider />
                    <a-menu-item @click="handleExportSegment">
                      <template #icon><ExportOutlined /></template>
                      导出片段
                    </a-menu-item>
                  </a-menu>
                </template>
              </a-dropdown>
            </div>
          </transition>
        </div>
      </div>
    </div>
    
    <!-- 时间轴标尺 -->
    <TimelineViewer
      :tracks="tracks"
      :selected-track="selectedTrack"
      :selected-segment="selectedSegment"
      :zoom-level="zoomLevel"
      :current-time="currentTime"
      :total-duration="totalDuration"
      @select-segment="$emit('select-segment', $event)"
      @edit-segment="$emit('edit-segment', $event)"
      @track-drop="$emit('track-drop', $event)"
      @playhead-change="$emit('seek', $event)"
      @segment-drag-start="handleSegmentDragStart"
    />

    <!-- 轨道内容区域 -->
    <div class="tracks-container">
      <!-- 水平布局：左侧轨道控制，右侧轨道内容 -->
      <div class="tracks-horizontal-layout">
        <!-- 左侧轨道控制面板 -->
        <div class="tracks-control-panel">
          <div
            v-for="(track, index) in tracks"
            :key="track.id"
            class="track-control-row"
            :class="{ 
              active: selectedTrack === track,
              hidden: track.hidden,
              locked: track.locked 
            }"
            @click="selectTrack(track)"
          >
            <!-- 紧凑的工具栏布局 -->
            <div class="compact-track-controls">
              <!-- 静音/取消静音 -->
              <a-button 
                type="text" 
                size="small" 
                @click.stop="toggleTrackMute(track)"
                :class="{ 'control-active': track.muted }"
                title="静音/取消静音"
              >
                <template #icon>
                  <SoundOutlined v-if="!track.muted" />
                  <AudioMutedOutlined v-else />
                </template>
              </a-button>
              
              <!-- 显示/隐藏轨道 -->
              <a-button 
                type="text" 
                size="small" 
                @click.stop="toggleTrackVisibility(track)"
                :class="{ 'control-active': track.hidden }"
                title="显示/隐藏轨道"
              >
                <template #icon>
                  <EyeOutlined v-if="!track.hidden" />
                  <EyeInvisibleOutlined v-else />
                </template>
              </a-button>
              
              <!-- 锁定/解锁轨道 -->
              <a-button 
                type="text" 
                size="small" 
                @click.stop="toggleTrackLock(track)"
                :class="{ 'control-active': track.locked }"
                title="锁定/解锁轨道"
              >
                <template #icon>
                  <UnlockOutlined v-if="!track.locked" />
                  <LockOutlined v-else />
                </template>
              </a-button>
              
              <!-- 紧凑的轨道标签 -->
              <div class="track-label">
                <span class="track-name">{{ track.name }}</span>
                <span class="track-type">{{ getTrackTypeLabel(track.type) }}</span>
              </div>
            </div>
          </div>

        </div>
        
        <!-- 右侧轨道内容区域 -->
        <div 
          ref="tracksContentPanelRef"
          class="tracks-content-panel"
          @drop="handleTimelineDrop"
          @dragover.prevent
          @dragenter.prevent
        >
          <!-- 统一的主播放头 -->
          <div 
            class="master-playhead" 
            :style="{ left: timeToPercent(currentTime) + '%' }"
            v-show="totalDuration > 0"
            @mousedown="startPlayheadDrag"
          >
            <div class="playhead-line"></div>
            <div class="playhead-handle">
              <div class="playhead-time">{{ formatTime(currentTime) }}</div>
            </div>
          </div>
          
          <!-- 时间轴点击区域 - 移除点击跳转功能，只保留拖拽 -->
          <div class="timeline-click-area"></div>
          
          <div
            v-for="(track, index) in tracks"
            :key="track.id"
            class="track-content-row"
            :class="{ 
              hidden: track.hidden, 
              locked: track.locked,
              selected: selectedTrack === track
            }"
            :data-track-id="track.id"
            @drop="track.locked ? null : handleTrackDrop($event, track)"
            @dragover.prevent="!track.locked"
            @dragenter.prevent="!track.locked"
            @mousedown="handleTrackMouseDown($event, track)"
            v-show="!track.hidden"
          >
            <!-- 如果轨道有音频文件，直接使用完整的WaveformViewer -->
            <div v-if="track.segments && track.segments.length > 0" class="track-segments-container">
              <!-- 音频片段，支持横向拖拽 -->
              <div
                v-for="segment in track.segments"
                :key="segment.id"
                class="audio-segment"
                :class="{ 
                  'selected': selectedSegment === segment,
                  'dragging': draggingSegment === segment.id 
                }"
                :style="{
                  left: timeToPercent(segment.startTime) + '%',
                  width: timeToPercent(segment.endTime - segment.startTime) + '%'
                }"
                draggable="true"
                @dragstart="handleSegmentDragStart($event, segment)"
                @dragend="handleSegmentDragEnd($event, segment)"
                @click="handleSegmentClick($event, segment, track)"
              >
                <!-- 音频片段的WaveformViewer -->
                <WaveformViewer
                  :audio-url="segment.audioUrl"
                  :height="140"
                  wave-color="#1890ff"
                  progress-color="#52c41a"
                  cursor-color="#ff4d4f"
                  :responsive="true"
                  :normalize="true"
                  :zoom-level="zoomLevel"
                  :show-toolbar="false"
                  :show-controls="false"
                  :show-time="false"
                  :interactive="false"
                  :external-current-time="currentTime"
                  :external-control="false"
                  class="segment-waveform-viewer"
                  @ready="onSegmentWaveformReady"
                />
                
                <!-- 片段信息覆盖层 -->
                <div class="segment-overlay">
                  <div class="segment-name">{{ segment.name }}</div>
                  <div class="segment-time">{{ formatTime(segment.startTime) }} - {{ formatTime(segment.endTime) }}</div>
                </div>
                
                <!-- 拖拽调整手柄 -->
                <div class="segment-resize-handles">
                  <div 
                    class="resize-handle resize-left"
                    @mousedown="startResize($event, segment, 'left')"
                  ></div>
                  <div 
                    class="resize-handle resize-right"
                    @mousedown="startResize($event, segment, 'right')"
                  ></div>
                </div>
              </div>
              
              <!-- 轨道拖拽区域指示器 -->
              <div 
                class="track-drop-zone" 
                :class="{ 'drag-over': isDragOver }"
                @drop="handleTrackDrop($event, track)"
                @dragover="handleDragOver"
                @dragleave="handleDragLeave"
                @dragenter.prevent
              >
                <span class="drop-hint" v-show="isDragOver">拖放音频到此轨道</span>
              </div>
            </div>
            
            <!-- 空轨道提示 -->
            <div v-else class="empty-track-hint">
              <span>拖拽音频文件到此处</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-if="tracks.length === 0" class="empty-tracks">
        <div class="empty-content">
          <SoundOutlined class="empty-icon" />
          <p>暂无音轨，请从素材库拖拽音频到此处</p>
          <a-button type="primary" @click="$emit('import-audio')">
            <template #icon><ImportOutlined /></template>
            导入音频
          </a-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import WaveformViewer from '../WaveformViewer.vue'
import TimelineViewer from './TimelineViewer.vue'
import {
  SoundOutlined,
  AudioMutedOutlined,
  EyeOutlined,
  EyeInvisibleOutlined,
  LockOutlined,
  UnlockOutlined,
  PlusOutlined,
  ImportOutlined,
  CopyOutlined,
  ScissorOutlined,
  DeleteOutlined,
  VerticalRightOutlined,
  SlidersOutlined,
  UndoOutlined,
  RedoOutlined,
  MoreOutlined,
  ExportOutlined,
  SwapOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'TracksArea',
  components: {
    WaveformViewer,
    TimelineViewer,
    SoundOutlined,
    AudioMutedOutlined,
    EyeOutlined,
    EyeInvisibleOutlined,
    LockOutlined,
    UnlockOutlined,
    PlusOutlined,
    ImportOutlined,
    CopyOutlined,
    ScissorOutlined,
    DeleteOutlined,
    VerticalRightOutlined,
    SlidersOutlined,
    UndoOutlined,
    RedoOutlined,
    MoreOutlined,
    ExportOutlined,
    SwapOutlined
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
    currentTime: {
      type: Number,
      default: 0
    },
    totalDuration: {
      type: Number,
      default: 0
    },
    masterVolume: {
      type: Number,
      default: 1
    },
    zoomLevel: {
      type: Number,
      default: 1
    },
    isPlaying: {
      type: Boolean,
      default: false
    }
  },
  emits: [
    'select-track',
    'select-segment', 
    'toggle-track-mute',
    'toggle-track-visibility',
    'toggle-track-lock',
    'add-track',
    'timeline-drop',
    'track-drop',
    'update-master-volume',
    'update-zoom-level',
    'import-audio',
    'segment-waveform-ready',
    'segment-updated',
    'seek',
    'copy-segment',
    'cut-segment',
    'delete-segment',
    'split-segment',
    'apply-fade-effect',
    'duplicate-segment',
    'normalize-volume',
    'reverse-segment',
    'export-segment',
    'edit-segment'
  ],
  setup(props, { emit }) {
    // 拖拽相关状态
    const draggingSegment = ref(null)
    const isDragOver = ref(false)
    const resizing = ref(null)
    const draggingPlayhead = ref(false)
    
    // 格式化时间
    const formatTime = (seconds) => {
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    // 时间和像素转换
    const timeToPixel = (time) => {
      const containerWidth = 800 // 基础宽度
      const scaledWidth = containerWidth * props.zoomLevel
      return (time / props.totalDuration) * scaledWidth
    }
    
    const pixelToTime = (pixel) => {
      const containerWidth = 800 * props.zoomLevel
      return (pixel / containerWidth) * props.totalDuration
    }

    // 更新为百分比布局的时间转换函数
    const timeToPercent = (time) => {
      if (!props.totalDuration || props.totalDuration === 0) return 0
      return (time / props.totalDuration) * 100
    }
    
    const percentToTime = (percent, containerWidth) => {
      return (percent / 100) * props.totalDuration
    }
    
    // 播放头位置计算（保留原来的像素计算用于兼容）
    const playheadPosition = computed(() => {
      if (!props.totalDuration || props.totalDuration === 0) return 0
      return timeToPixel(props.currentTime)
    })

    // WaveformViewer组件处理播放头，不需要独立计算
    const tracksContentPanelRef = ref(null)

    // 播放头拖拽功能
    const startPlayheadDrag = (event) => {
      event.preventDefault()
      event.stopPropagation()
      draggingPlayhead.value = true
      
      document.addEventListener('mousemove', handlePlayheadDrag)
      document.addEventListener('mouseup', endPlayheadDrag)
    }
    
    const handlePlayheadDrag = (event) => {
      if (!draggingPlayhead.value || !tracksContentPanelRef.value) return
      
      const rect = tracksContentPanelRef.value.getBoundingClientRect()
      const x = event.clientX - rect.left
      
      // 计算百分比位置
      const percentPosition = (x / rect.width) * 100
      // 转换为时间
      const newTime = percentToTime(percentPosition)
      const clampedTime = Math.max(0, Math.min(newTime, props.totalDuration))
      
      emit('seek', clampedTime)
    }
    
    const endPlayheadDrag = () => {
      draggingPlayhead.value = false
      document.removeEventListener('mousemove', handlePlayheadDrag)
      document.removeEventListener('mouseup', endPlayheadDrag)
    }
    
    // 移除时间轴点击跳转功能，只保留拖拽播放头功能

    // 轨道操作方法
    const selectTrack = (track) => {
      emit('select-track', track)
    }

    const selectSegment = (segment) => {
      emit('select-segment', segment)
    }

    const handleSegmentClick = (event, segment, track) => {
      event.stopPropagation() // 阻止事件冒泡到轨道
      selectTrack(track) // 选中轨道
      selectSegment(segment) // 选中片段
    }

    // 轨道点击状态管理
    const trackClickState = ref({
      isMouseDown: false,
      startX: 0,
      startY: 0,
      hasMoved: false
    })

    const handleTrackMouseDown = (event, track) => {
      // 只有点击空白区域时才处理（不是点击音频片段）
      if (!event.target.closest('.audio-segment')) {
        trackClickState.value = {
          isMouseDown: true,
          startX: event.clientX,
          startY: event.clientY,
          hasMoved: false
        }
        
        // 添加全局鼠标移动和释放监听
        document.addEventListener('mousemove', handleTrackMouseMove)
        document.addEventListener('mouseup', handleTrackMouseUp)
      }
    }

    const handleTrackMouseMove = (event) => {
      if (trackClickState.value.isMouseDown) {
        const deltaX = Math.abs(event.clientX - trackClickState.value.startX)
        const deltaY = Math.abs(event.clientY - trackClickState.value.startY)
        
        // 如果鼠标移动超过3像素，则认为是拖拽
        if (deltaX > 3 || deltaY > 3) {
          trackClickState.value.hasMoved = true
        }
      }
    }

    const handleTrackMouseUp = (event) => {
      // 移除全局监听
      document.removeEventListener('mousemove', handleTrackMouseMove)
      document.removeEventListener('mouseup', handleTrackMouseUp)
      
      // 只有在没有移动的情况下才算作点击
      if (trackClickState.value.isMouseDown && !trackClickState.value.hasMoved) {
        // 找到对应的轨道
        const trackElement = event.target.closest('.track-content-row')
        if (trackElement) {
          const trackId = trackElement.dataset.trackId
          const track = props.tracks.find(t => t.id.toString() === trackId)
          if (track) {
            selectTrack(track)
            // 清除片段选中状态
            emit('select-segment', null)
          }
        }
      }
      
      // 重置状态
      trackClickState.value = {
        isMouseDown: false,
        startX: 0,
        startY: 0,
        hasMoved: false
      }
    }

    const toggleTrackMute = (track) => {
      emit('toggle-track-mute', track)
    }

    const toggleTrackVisibility = (track) => {
      emit('toggle-track-visibility', track)
    }

    const toggleTrackLock = (track) => {
      emit('toggle-track-lock', track)
    }

    const addNewTrack = () => {
      emit('add-track')
    }

    // 音频片段拖拽处理
    const handleSegmentDragStart = (eventOrObj, segmentParam) => {
      // 处理不同的参数格式
      let event, segment;
      
      if (eventOrObj.event && eventOrObj.segment) {
        // 来自TimelineViewer的格式: { event, segment }
        event = eventOrObj.event;
        segment = eventOrObj.segment;
      } else {
        // 直接传递的格式: (event, segment)
        event = eventOrObj;
        segment = segmentParam;
      }
      
      draggingSegment.value = segment.id
      const dragData = {
        type: 'audio-segment',
        segmentId: segment.id,
        offsetX: event.offsetX,
        originalStartTime: segment.startTime
      }
      event.dataTransfer.setData('application/json', JSON.stringify(dragData))
      event.dataTransfer.effectAllowed = 'move'
    }
    
    const handleSegmentDragEnd = (event, segment) => {
      draggingSegment.value = null
    }
    
    // 拖拽区域处理
    const handleDragOver = (event) => {
      event.preventDefault()
      event.dataTransfer.dropEffect = 'move'
      isDragOver.value = true
    }
    
    const handleDragLeave = (event) => {
      isDragOver.value = false
    }
    
    // 片段调整大小
    const startResize = (event, segment, direction) => {
      event.preventDefault()
      event.stopPropagation()
      
      resizing.value = {
        segment,
        direction,
        startX: event.clientX,
        originalStartTime: segment.startTime,
        originalEndTime: segment.endTime
      }
      
      document.addEventListener('mousemove', handleResizeMove)
      document.addEventListener('mouseup', handleResizeEnd)
    }
    
    const handleResizeMove = (event) => {
      if (!resizing.value) return
      
      // 获取容器宽度
      const containerRect = event.currentTarget.closest('.tracks-content-panel').getBoundingClientRect()
      const containerWidth = containerRect.width
      
      // 计算像素变化量
      const deltaX = event.clientX - resizing.value.startX
      
      // 转换为百分比变化量
      const deltaPercent = (deltaX / containerWidth) * 100
      
      // 转换为时间变化量
      const deltaTime = percentToTime(deltaPercent)
      
      const { segment, direction, originalStartTime, originalEndTime } = resizing.value
      
      if (direction === 'left') {
        const newStartTime = Math.max(0, originalStartTime + deltaTime)
        if (newStartTime < originalEndTime - 0.1) { // 最小0.1秒
          segment.startTime = newStartTime
        }
      } else if (direction === 'right') {
        const newEndTime = Math.min(props.totalDuration, originalEndTime + deltaTime)
        if (newEndTime > originalStartTime + 0.1) { // 最小0.1秒
          segment.endTime = newEndTime
        }
      }
    }
    
    const handleResizeEnd = () => {
      if (resizing.value) {
        // 发射更新事件
        emit('segment-updated', resizing.value.segment)
        resizing.value = null
      }
      
      document.removeEventListener('mousemove', handleResizeMove)
      document.removeEventListener('mouseup', handleResizeEnd)
    }

    // 拖拽处理
    const handleTimelineDrop = (event) => {
      event.preventDefault()
      
      try {
        const dragData = JSON.parse(event.dataTransfer.getData('application/json'))
        
        if (dragData.type === 'audio-material') {
          const audioFile = dragData.audioFile
          const rect = event.currentTarget.getBoundingClientRect()
          const relativeX = event.clientX - rect.left
          
          // 计算拖拽位置对应的时间（使用百分比）
          const percentPosition = (relativeX / rect.width) * 100
          let dropTime = percentToTime(percentPosition)
          
          // 边界处理
          dropTime = Math.max(0, Math.round(dropTime * 100) / 100)
          
          // 检查是否拖拽到现有轨道上
          const trackContentRows = Array.from(event.currentTarget.children)
          let targetTrack = null
          
          for (const contentRow of trackContentRows) {
            if (contentRow.classList.contains('track-content-row')) {
              const contentRect = contentRow.getBoundingClientRect()
              if (event.clientY >= contentRect.top && event.clientY <= contentRect.bottom) {
                const trackId = contentRow.dataset.trackId
                targetTrack = props.tracks.find(t => t.id.toString() === trackId)
                break
              }
            }
          }
          
          emit('timeline-drop', {
            audioFile,
            dropTime,
            targetTrack
          })
        }
      } catch (error) {
        console.error('处理时间轴拖拽失败:', error)
        message.error('添加到时间轴失败')
      }
    }

    const handleTrackDrop = (event, track) => {
      event.preventDefault()
      isDragOver.value = false
      
      try {
        const dragData = JSON.parse(event.dataTransfer.getData('application/json'))
        
        if (dragData.type === 'audio-material') {
          // 从素材库拖拽音频文件
          const audioFile = dragData.audioFile
          const rect = event.target.getBoundingClientRect()
          const relativeX = event.clientX - rect.left
          
          // 计算拖拽位置对应的时间（使用百分比）
          const percentPosition = (relativeX / rect.width) * 100
          let dropTime = percentToTime(percentPosition)
          
          // 边界处理
          dropTime = Math.max(0, Math.round(dropTime * 100) / 100)
          
          emit('track-drop', {
            audioFile,
            dropTime,
            track
          })
        } else if (dragData.type === 'audio-segment') {
          // 拖拽已存在的音频片段
          const { segmentId, offsetX, originalStartTime } = dragData
          const rect = event.target.getBoundingClientRect()
          const relativeX = event.clientX - rect.left - offsetX
          
          // 计算新的开始时间（使用百分比）
          const percentPosition = (relativeX / rect.width) * 100
          let newStartTime = percentToTime(percentPosition)
          newStartTime = Math.max(0, Math.round(newStartTime * 100) / 100)
          
          // 查找片段并移动
          const allSegments = []
          props.tracks.forEach(t => {
            t.segments?.forEach(s => {
              if (s.id === segmentId) {
                allSegments.push({ segment: s, track: t })
              }
            })
          })
          
          if (allSegments.length > 0) {
            const { segment, track: sourceTrack } = allSegments[0]
            const duration = segment.endTime - segment.startTime
            
            // 从原轨道移除
            if (sourceTrack !== track) {
              const segmentIndex = sourceTrack.segments.indexOf(segment)
              if (segmentIndex > -1) {
                sourceTrack.segments.splice(segmentIndex, 1)
                
                // 检查原轨道是否为空，如果为空则通知主编辑器删除轨道
                if (sourceTrack.segments.length === 0) {
                  emit('delete-empty-track', sourceTrack)
                }
              }
              
              // 添加到目标轨道
              if (!track.segments) {
                track.segments = []
              }
            }
            
            // 更新片段时间
            segment.startTime = newStartTime
            segment.endTime = newStartTime + duration
            
            // 确保片段在目标轨道中
            if (!track.segments.includes(segment)) {
              track.segments.push(segment)
            }
            
            // 发射更新事件
            emit('segment-updated', segment)
          }
        }
      } catch (error) {
        console.error('处理轨道拖拽失败:', error)
        message.error('拖拽失败')
      }
    }

    // 控制事件处理
    const handleMasterVolumeChange = (value) => {
      emit('update-master-volume', value)
    }

    const handleZoomChange = (value) => {
      emit('update-zoom-level', value)
    }

    // 波形事件处理
    const onSegmentWaveformReady = (data) => {
      emit('segment-waveform-ready', data)
    }

    // 新增方法
    const getTrackTypeLabel = (type) => {
      const labels = {
        audio: '音频',
        voice: '语音', 
        music: '音乐',
        environment: '环境音',
        effect: '音效'
      }
      return labels[type] || '音频'
    }

    const isTrackHasSelectedSegment = (track) => {
      if (!props.selectedSegment || !track.segments) return false
      return track.segments.some(segment => segment.id === props.selectedSegment.id)
    }

    // 撤销重做状态
    const canUndo = computed(() => {
      // 这里需要与主编辑器的撤销系统集成
      return false // 临时返回false，后续集成
    })

    const canRedo = computed(() => {
      // 这里需要与主编辑器的撤销系统集成
      return false // 临时返回false，后续集成
    })

    const handleCopySegment = () => {
      if (props.selectedSegment) {
        emit('copy-segment', props.selectedSegment)
        message.success('已复制片段')
      }
    }

    const handleCutSegment = () => {
      if (props.selectedSegment) {
        emit('cut-segment', props.selectedSegment)
        message.success('已剪切片段')
      }
    }

    const handleDeleteSegment = () => {
      if (props.selectedSegment) {
        emit('delete-segment', props.selectedSegment)
        message.success('已删除片段')
      }
    }

    const handleSplitSegment = () => {
      if (props.selectedSegment) {
        // 在当前播放时间位置分割片段
        const splitTime = props.currentTime
        emit('split-segment', {
          segment: props.selectedSegment,
          splitTime: splitTime
        })
        message.success('已分割片段')
      }
    }

    const handleFadeEffect = () => {
      if (props.selectedSegment) {
        emit('apply-fade-effect', props.selectedSegment)
        message.success('已应用淡入淡出效果')
      }
    }

    const handleUndo = () => {
      emit('undo')
    }

    const handleRedo = () => {
      emit('redo')
    }

    const handleDuplicateSegment = () => {
      if (props.selectedSegment) {
        emit('duplicate-segment', props.selectedSegment)
        message.success('已复制片段到新轨道')
      }
    }

    const handleNormalizeVolume = () => {
      if (props.selectedSegment) {
        emit('normalize-volume', props.selectedSegment)
        message.success('已标准化音量')
      }
    }

    const handleReverseSegment = () => {
      if (props.selectedSegment) {
        emit('reverse-segment', props.selectedSegment)
        message.success('已反向播放片段')
      }
    }

    const handleExportSegment = () => {
      if (props.selectedSegment) {
        emit('export-segment', props.selectedSegment)
        message.info('正在导出片段...')
      }
    }

    // 获取选中片段所在的轨道名称
    const getSelectedTrackName = () => {
      if (!props.selectedSegment) return ''
      
      for (const track of props.tracks) {
        if (track.segments?.some(segment => segment.id === props.selectedSegment.id)) {
          return track.name
        }
      }
      return '未知轨道'
    }

    return {
      formatTime,
      timeToPixel,
      pixelToTime,
      timeToPercent,
      percentToTime,
      tracksContentPanelRef,
      // professionalTimeMarks 已移除，使用WaveformViewer的专业时间轴
      selectTrack,
      selectSegment,
      handleSegmentClick,
      handleTrackMouseDown,
      handleTrackMouseMove,
      handleTrackMouseUp,
      toggleTrackMute,
      toggleTrackVisibility,
      toggleTrackLock,
      addNewTrack,
      handleTimelineDrop,
      handleTrackDrop,
      handleMasterVolumeChange,
      handleZoomChange,
      // 新的拖拽方法
      handleSegmentDragStart,
      handleSegmentDragEnd,
      handleDragOver,
      handleDragLeave,
      startResize,
      // 波形事件
      onSegmentWaveformReady,
      // 状态
      draggingSegment,
      isDragOver,
      resizing,
      playheadPosition,
      startPlayheadDrag,
      handlePlayheadDrag,
      endPlayheadDrag,
      getTrackTypeLabel,
      isTrackHasSelectedSegment,
      handleCopySegment,
      handleCutSegment,
      handleDeleteSegment,
      handleSplitSegment,
      handleFadeEffect,
      handleUndo,
      handleRedo,
      handleDuplicateSegment,
      handleNormalizeVolume,
      handleReverseSegment,
      handleExportSegment,
      // 新的状态
      canUndo,
      canRedo,
      getSelectedTrackName
    }
  }
}
</script>

<style scoped>
/* 轨道区域 */
.tracks-area {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #2c2c2c;
}

/* 时间轴标尺样式 */
.timeline-viewer {
  width: 100%;
  border-bottom: 1px solid #4a4a4a;
  height: 40px; /* 确保有足够的高度显示时间轴 */
}

/* 轨道头部 */
.tracks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 16px;
  background: #383838;
  border-bottom: 1px solid #4a4a4a;
  height: 40px;
}

.tracks-title {
  font-size: 13px;
  font-weight: 500;
  color: #e0e0e0;
}

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

/* 简化时间信息区域 */
.timeline-info {
  height: 40px;
  background: #383838;
  border-bottom: 1px solid #4a4a4a;
  display: flex;
  align-items: center;
}

.timeline-info-content {
  display: flex;
  align-items: center;
  height: 100%;
}

.project-info {
  display: flex;
  gap: 24px;
  align-items: center;
  padding: 0 16px;
}

.duration-display,
.current-time-display {
  font-size: 12px;
  color: #e0e0e0;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  background: rgba(0, 0, 0, 0.3);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid #555;
}

/* 动态时间轴操作栏 - 参考剪映设计 */
.timeline-operations {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-left: 32px;
  padding: 4px 12px;
  background: rgba(24, 144, 255, 0.1);
  border: 1px solid #1890ff;
  border-radius: 6px;
  animation: slideIn 0.3s ease-out;
}

.selected-track-name {
  font-size: 12px;
  color: #1890ff;
  font-weight: 500;
  white-space: nowrap;
}

.operation-group {
  display: flex;
  border-radius: 4px;
  overflow: hidden;
  background: rgba(255, 255, 255, 0.05);
}

.operation-group .ant-btn {
  border-radius: 0;
  border-color: transparent;
  color: #e0e0e0;
  transition: all 0.2s;
}

.operation-group .ant-btn:hover {
  background: rgba(24, 144, 255, 0.2);
  color: #1890ff;
}

.operation-group .ant-btn.ant-btn-dangerous:hover {
  background: rgba(255, 77, 79, 0.2);
  color: #ff4d4f;
}

.operation-group .ant-btn:disabled {
  color: #666;
  background: transparent;
}

/* 滑入动画 */
@keyframes slideIn {
  from {
    opacity: 0;
    transform: translateX(-20px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}

/* 过渡动画 */
.slide-fade-enter-active,
.slide-fade-leave-active {
  transition: all 0.3s ease;
}

.slide-fade-enter-from {
  opacity: 0;
  transform: translateX(-20px);
}

.slide-fade-leave-to {
  opacity: 0;
  transform: translateX(-20px);
}

/* 轨道容器 */
.tracks-container {
  flex: 1;
  overflow: hidden;
  min-height: 0;
}

.tracks-horizontal-layout {
  height: 100%;
  display: grid;
  grid-template-columns: 200px 1fr;
  gap: 1px;
  background: #4a4a4a;
}

/* 轨道控制面板 */
.tracks-control-panel {
  background: #383838;
  display: flex;
  flex-direction: column;
  overflow-y: auto;
}

.track-control-row {
  display: flex;
  align-items: center;
  min-height: 160px;
  padding: 12px 8px;
  border-bottom: 1px solid #4a4a4a;
  cursor: pointer;
  transition: background-color 0.2s;
}

.track-control-row:hover {
  background: #444;
}

.track-control-row.active {
  background: #1e3a8a;
}

.track-control-row.hidden {
  opacity: 0.5;
}

.track-control-row.locked {
  background: #3a3a3a;
}

.compact-track-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
}

.track-label {
  flex: 1;
  margin-left: 8px;
}

.track-name {
  font-size: 12px;
  color: #e0e0e0;
  font-weight: 500;
}

.track-type {
  font-size: 10px;
  color: #8c8c8c;
  font-weight: 400;
}

.add-track-row {
  padding: 8px;
  border-top: 1px solid #4a4a4a;
}

.control-active {
  background: #1890ff !important;
  color: white !important;
}

/* 轨道内容面板 */
.tracks-content-panel {
  background: #2c2c2c;
  overflow: auto;
  position: relative;
}

/* 轨道内容行 */
.track-content-row {
  min-height: 160px;
  border-bottom: 1px solid #4a4a4a;
  position: relative;
  display: flex;
  align-items: center;
  cursor: pointer;
  transition: background-color 0.2s ease;
}

.track-content-row:hover {
  background: rgba(255, 255, 255, 0.05);
}

.track-content-row.selected {
  background: rgba(24, 144, 255, 0.1);
  border-left: 3px solid #1890ff;
}

.track-content-row.hidden {
  display: none;
}

.track-content-row.locked {
  background: rgba(255, 193, 7, 0.1);
  cursor: not-allowed;
}

/* 音频片段容器 */
.track-segments-container {
  position: relative;
  width: 100%;
  height: 100%;
  min-height: 160px;
}

/* 音频片段 */
.audio-segment {
  position: absolute;
  top: 10px;
  height: 140px;
  background: rgba(24, 144, 255, 0.1);
  border: 2px solid #1890ff;
  border-radius: 4px;
  cursor: move;
  transition: all 0.2s ease;
  overflow: hidden;
}

.audio-segment:hover {
  border-color: #40a9ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.3);
}

.audio-segment.selected {
  border-color: #52c41a;
  box-shadow: 0 0 0 2px rgba(82, 196, 26, 0.2);
}

.audio-segment.dragging {
  opacity: 0.7;
  transform: rotate(2deg);
  z-index: 1000;
}

/* 片段波形查看器 */
.segment-waveform-viewer {
  width: 100%;
  height: 100%;
  pointer-events: none; /* 防止与拖拽冲突 */
}

/* 片段信息覆盖层 */
.segment-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: linear-gradient(to bottom, 
    rgba(0, 0, 0, 0.8) 0%, 
    rgba(0, 0, 0, 0.4) 30%, 
    transparent 60%);
  color: white;
  padding: 8px;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s;
}

.audio-segment:hover .segment-overlay {
  opacity: 1;
}

.segment-name {
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 4px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.segment-time {
  font-size: 10px;
  opacity: 0.8;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

/* 调整大小手柄 */
.segment-resize-handles {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 0;
  right: 0;
  pointer-events: none;
}

.resize-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 8px;
  cursor: ew-resize;
  pointer-events: auto;
  background: transparent;
  transition: background-color 0.2s;
}

.resize-handle:hover {
  background: rgba(24, 144, 255, 0.5);
}

.resize-left {
  left: 0;
  border-left: 2px solid transparent;
}

.resize-right {
  right: 0;
  border-right: 2px solid transparent;
}

.resize-handle:hover.resize-left {
  border-left-color: #1890ff;
}

.resize-handle:hover.resize-right {
  border-right-color: #1890ff;
}

/* 轨道拖拽区域 */
.track-drop-zone {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  pointer-events: none;
}

.track-drop-zone.drag-over {
  background: rgba(24, 144, 255, 0.1);
  border: 2px dashed #1890ff;
  pointer-events: auto;
}

.drop-hint {
  color: #1890ff;
  font-size: 14px;
  font-weight: 500;
  padding: 12px 24px;
  background: rgba(24, 144, 255, 0.1);
  border-radius: 4px;
  border: 1px solid #1890ff;
}

/* 空轨道提示 */
.empty-track-hint {
  width: 100%;
  height: 100%;
  min-height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #3a3a3a;
  border: 2px dashed #555;
  border-radius: 4px;
  color: #888;
  font-size: 14px;
  transition: all 0.2s;
}

.empty-track-hint:hover {
  border-color: #1890ff;
  color: #1890ff;
  background: rgba(24, 144, 255, 0.05);
}

/* 空状态 */
.empty-tracks {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #8c8c8c;
}

.empty-content {
  text-align: center;
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

/* 暗黑模式适配 */
[data-theme="dark"] .tracks-area {
  background: #1f1f1f;
}

[data-theme="dark"] .tracks-header {
  background: #2d2d2d;
  border-color: #434343;
}

[data-theme="dark"] .tracks-title {
  color: #fff;
}

[data-theme="dark"] .volume-label,
[data-theme="dark"] .zoom-label {
  color: #8c8c8c;
}

/* 统一主播放头 */
.master-playhead {
  position: absolute;
  top: 0;
  bottom: 0;
  width: 3px; /* 增加宽度方便点击 */
  z-index: 1000;
  pointer-events: auto;
  transition: left 0.1s ease-out;
  cursor: ew-resize;
}

.master-playhead:hover {
  width: 5px; /* 悬停时更宽 */
}

.playhead-line {
  width: 100%;
  height: 100%;
  background: #ff4d4f;
  box-shadow: 0 0 6px rgba(255, 77, 79, 0.8);
}

.playhead-handle {
  position: absolute;
  top: -10px;
  left: -10px;
  width: 22px; /* 增大拖拽手柄 */
  height: 22px;
  background: #ff4d4f;
  border: 3px solid #fff;
  border-radius: 50%;
  box-shadow: 0 3px 12px rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: grab;
  transition: transform 0.2s ease;
}

.playhead-handle:hover {
  transform: scale(1.1);
  box-shadow: 0 4px 16px rgba(255, 77, 79, 0.5);
}

.playhead-handle:active {
  cursor: grabbing;
  transform: scale(1.05);
}

.playhead-time {
  position: absolute;
  top: -32px;
  left: 50%;
  transform: translateX(-50%);
  background: rgba(0, 0, 0, 0.8);
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
  font-size: 11px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  white-space: nowrap;
  pointer-events: none;
  opacity: 0;
  transition: opacity 0.2s;
}

.master-playhead:hover .playhead-time {
  opacity: 1;
}

/* 时间轴区域 - 不再支持点击跳转 */
.timeline-click-area {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  z-index: 5;
  cursor: default; /* 改为默认光标 */
  pointer-events: none; /* 禁用点击事件 */
}

/* 时间轴标尺 */
.timeline-viewer {
  width: 100%;
  border-bottom: 1px solid #4a4a4a;
}
</style> 