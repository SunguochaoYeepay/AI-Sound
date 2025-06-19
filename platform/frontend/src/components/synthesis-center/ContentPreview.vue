<template>
  <div class="content-preview">
    <!-- 智能准备结果 -->
    <div v-if="preparationResults && preparationResults.data && preparationResults.data.length > 0" class="preparation-preview">
      <div class="dialogue-preview">
        <div class="dialogue-list">
          <div v-for="(chapterResult, chapterIndex) in preparationResults.data" :key="chapterIndex">
            <!-- 章节标题 -->
            <div class="chapter-divider">
              <div class="chapter-title-section">
                <span class="chapter-title">
                  第{{ chapterResult.chapter_number }}章 {{ chapterResult.chapter_title }}
                </span>
                <div class="chapter-stats">
                  <a-space>
                    <a-tag color="blue">📋 {{ chapterResult.synthesis_json?.synthesis_plan?.length || 0 }} 个段落</a-tag>
                    <a-tag color="green">🎭 {{ getChapterCharacterCount(chapterResult) }} 个角色</a-tag>
                    <a-tag :color="getStatusColor(project?.status)">状态: {{ getStatusText(project?.status) }}</a-tag>
                  </a-space>
                </div>
              </div>
              <div class="chapter-actions">
                <!-- 刷新按钮 -->
                <a-button 
                  v-if="preparationResults && selectedChapter"
                  @click="handleRefreshPreparation"
                  :loading="contentLoading"
                  size="small"
                  type="text"
                >
                  🔄 刷新
                </a-button>
                
                <!-- 合成控制按钮 -->
                <a-space size="small">
                  <!-- 待处理状态：显示开始合成按钮 -->
                  <template v-if="selectedChapterStatus === 'pending'">
                    <a-button
                      type="primary"
                      size="small"
                      :disabled="!canStart"
                      :loading="synthesisStarting"
                      @click="$emit('start-synthesis')"
                    >
                      开始合成
                    </a-button>
                  </template>

                  <!-- 已完成状态：显示播放和下载按钮 -->
                  <template v-if="selectedChapterStatus === 'completed'">
                    <a-button
                      type="primary"
                      size="small"
                      @click="$emit('play-audio')"
                      :loading="playingChapterAudio === selectedChapter"
                    >
                      播放
                    </a-button>
                    <a-button
                      size="small"
                      @click="$emit('download-audio')"
                    >
                      下载
                    </a-button>
                  </template>

                  <!-- 处理中状态：显示暂停和取消按钮 -->
                  <template v-if="selectedChapterStatus === 'processing'">
                    <a-button
                      size="small"
                      @click="$emit('pause-synthesis')"
                    >
                      暂停
                    </a-button>
                    <a-button
                      size="small"
                      @click="$emit('cancel-synthesis')"
                    >
                      取消
                    </a-button>
                  </template>

                  <!-- 失败状态：显示重试按钮 -->
                  <template v-if="selectedChapterStatus === 'failed'">
                    <a-button
                      type="primary"
                      size="small"
                      @click="$emit('retry-synthesis')"
                    >
                      重试
                    </a-button>
                  </template>
                  
                  <!-- 更多操作下拉菜单 -->
                  <a-dropdown v-if="selectedChapterStatus === 'completed' || selectedChapterStatus === 'partial_completed'">
                    <a-button size="small">
                      更多
                      <DownOutlined />
                    </a-button>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item @click="$emit('restart-synthesis')">
                          重新合成
                        </a-menu-item>
                        <a-menu-item @click="handleRefreshPreparation">
                          刷新数据
                        </a-menu-item>
                      </a-menu>
                    </template>
                  </a-dropdown>
                </a-space>
              </div>
            </div>
            
            <!-- 对话气泡 -->
            <div class="dialogue-bubbles">
              <DialogueBubble
                v-for="(segment, segmentIndex) in getDisplaySegments(chapterResult)"
                :key="segmentIndex"
                :segment="segment"
                :segment-index="segmentIndex"
                :project-id="project?.id"
                :is-completed="isSegmentCompleted(segmentIndex)"
                :project-status="project?.status || 'pending'"
                :current-segment="project?.current_segment || 0"
                @play-segment="handlePlaySegment"
              />
              
              <div v-if="!showAllSegments && shouldShowMoreButton(chapterResult)" class="show-more">
                <a-button type="dashed" @click="showAllSegments = true" block>
                  显示全部 {{ chapterResult.synthesis_json?.synthesis_plan?.length }} 个段落
                </a-button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-preview">
      <a-empty description="未找到智能准备结果" :image="Empty.PRESENTED_IMAGE_SIMPLE">
        <div class="empty-hint">
          <p v-if="!selectedChapter">{{ getStartHint() }}</p>
          <div v-else class="no-preparation-content">
            <p>当前章节尚未进行智能准备</p>
            <p class="chapter-info">选中章节: 第{{ getSelectedChapterInfo()?.chapter_number }}章 {{ getSelectedChapterInfo()?.chapter_title || getSelectedChapterInfo()?.title }}</p>
            <a-space direction="vertical" style="margin-top: 16px;">
              <a-button type="primary" @click="handleTriggerPreparation" :loading="contentLoading">
                🎭 开始智能准备
              </a-button>
              <a-button type="dashed" @click="handleRefreshPreparation" :loading="contentLoading">
                🔄 重新加载
              </a-button>
            </a-space>
            <p class="help-text">智能准备将分析章节内容，识别角色对话并生成合成配置</p>
          </div>
        </div>
      </a-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Empty } from 'ant-design-vue'
import { DownOutlined } from '@ant-design/icons-vue'
import DialogueBubble from './DialogueBubble.vue'

const props = defineProps({
  project: Object,
  selectedChapter: [String, Number],
  chapterContent: Object,
  contentLoading: Boolean,
  segments: Array,
  preparationResults: Object,
  availableChapters: Array,
  synthesisStarting: Boolean,
  pausingGeneration: Boolean,
  cancelingGeneration: Boolean,
  resumingGeneration: Boolean,
  playingChapterAudio: [String, Number],
  canStart: Boolean,
  synthesisRunning: Boolean,
  selectedChapterStatus: String
})

const emit = defineEmits([
  'play-segment',
  'refresh-preparation',
  'trigger-preparation',
  'start-chapter-synthesis',
  'pause-synthesis',
  'cancel-synthesis',
  'resume-chapter',
  'restart-chapter',
  'retry-chapter-failed',
  'play-chapter',
  'download-chapter',
  'start-synthesis',
  'pause-synthesis',
  'cancel-synthesis',
  'retry-synthesis',
  'play-audio',
  'download-audio',
  'restart-synthesis'
])

const showAllSegments = ref(false)

const canStartSynthesis = computed(() => {
  const hasValidChapterSelection = props.selectedChapter !== null
  const hasPreparationResults = props.preparationResults?.data?.length > 0
  const hasSegments = getTotalSegments() > 0
  
  return props.project?.status !== 'processing' &&
         hasValidChapterSelection &&
         hasPreparationResults &&
         hasSegments
})

const getDisplaySegments = (chapterResult) => {
  const segments = chapterResult.synthesis_json?.synthesis_plan || []
  return showAllSegments.value ? segments : segments.slice(0, 10)
}

const shouldShowMoreButton = (chapterResult) => {
  const totalSegments = chapterResult.synthesis_json?.synthesis_plan?.length || 0
  return totalSegments > 10
}

const getTotalSegments = () => {
  if (!props.preparationResults?.data) return 0
  return props.preparationResults.data.reduce((total, chapterResult) => {
    const synthesisJson = chapterResult.synthesis_json
    return total + (synthesisJson.synthesis_plan?.length || 0)
  }, 0)
}

const getChapterCharacterCount = (chapterResult) => {
  if (!chapterResult?.synthesis_json?.synthesis_plan) return 0
  const speakers = new Set()
  chapterResult.synthesis_json.synthesis_plan.forEach(segment => {
    if (segment.speaker) {
      speakers.add(segment.speaker)
    }
  })
  return speakers.size
}

const getSelectedChapterInfo = () => {
  if (!props.selectedChapter || !props.availableChapters.length) return null
  return props.availableChapters.find(chapter => chapter.id === props.selectedChapter)
}

// 判断段落是否已完成合成
const isSegmentCompleted = (segmentIndex) => {
  // 如果项目状态是已完成，则所有段落都已完成
  if (props.project?.status === 'completed') {
    return true
  }
  
  // 如果项目状态是部分完成，检查具体段落状态
  if (props.project?.status === 'partial_completed') {
    const processedSegments = props.project?.processed_segments || 0
    return segmentIndex < processedSegments
  }
  
  // 如果项目正在处理，检查当前进度
  if (props.project?.status === 'processing') {
    const currentSegment = props.project?.current_segment || 0
    return segmentIndex < currentSegment
  }
  
  return false
}

const getStartHint = () => {
  if (!props.selectedChapter) {
    return '请选择要合成的章节，系统将自动加载智能准备结果'
  }
  if (props.contentLoading) {
    return '正在加载智能准备结果...'
  }
  if (!props.preparationResults?.data?.length) {
    return '正在自动加载智能准备结果，请稍候...'
  }
  if (getTotalSegments() === 0) {
    return '没有可合成的片段'
  }
  return '可以开始合成'
}

const getDisplayStatus = (rawStatus) => {
  if (rawStatus === 'partial_completed') {
    const completed = props.project?.statistics?.completedSegments || props.project?.processed_segments || 0
    const total = props.project?.statistics?.totalSegments || props.project?.total_segments || 0
    const failed = props.project?.statistics?.failedSegments || props.project?.failed_segments || 0
    
    if (total > 0 && completed === total && failed === 0) {
      return 'completed'
    }
    if (failed > 0) {
      return 'failed'
    }
  }
  return rawStatus
}

const getStatusText = (status) => {
  const displayStatus = getDisplayStatus(status)
  const texts = {
    pending: '待开始',
    processing: '合成中',
    paused: '已暂停',
    completed: '已完成',
    partial_completed: '部分完成',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[displayStatus] || displayStatus
}

const getStatusColor = (status) => {
  const displayStatus = getDisplayStatus(status)
  const colors = {
    pending: 'orange',
    processing: 'blue',
    paused: 'purple',
    completed: 'green',
    partial_completed: 'gold',
    failed: 'red',
    cancelled: 'default'
  }
  return colors[displayStatus] || 'default'
}

const handlePlaySegment = (segmentIndexOrSegment, segment) => {
  // 兼容两种调用方式：
  // 1. handlePlaySegment(segment) - 直接传递segment
  // 2. handlePlaySegment(segmentIndex, segment) - 从DialogueBubble传递的
  
  if (typeof segmentIndexOrSegment === 'number' && segment) {
    // 第二种情况：segmentIndexOrSegment是索引，segment是真正的segment对象
    // 添加索引信息到segment对象
    const segmentWithIndex = {
      ...segment,
      index: segmentIndexOrSegment + 1, // 转换为1基础索引
      segment_id: segmentIndexOrSegment + 1
    }
    emit('play-segment', segmentWithIndex)
  } else {
    // 第一种情况：segmentIndexOrSegment就是segment对象
    emit('play-segment', segmentIndexOrSegment)
  }
}

const handleRefreshPreparation = () => {
  emit('refresh-preparation')
}

const handleTriggerPreparation = () => {
  emit('trigger-preparation')
}

const handleStartChapterSynthesis = (chapterId) => {
  emit('start-chapter-synthesis', chapterId)
}

const handlePlayChapter = (chapterId) => {
  emit('play-chapter', chapterId)
}

const handleDownloadChapter = (chapterId) => {
  emit('download-chapter', chapterId)
}
</script>

<style scoped>
.content-preview {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

.preparation-preview {
  background: white;
  border-radius: 12px;
  overflow: hidden;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.dialogue-preview {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.dialogue-list {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.chapter-divider {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin: 24px 0 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #f0f0f0;
}

.chapter-title-section {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chapter-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.chapter-stats {
  margin-top: 4px;
}

.chapter-actions {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.dialogue-bubbles {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.show-more {
  margin-top: 16px;
}

.empty-preview {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
}

.empty-hint {
  margin-top: 12px;
  font-size: 14px;
  color: #666;
}

.no-preparation-content {
  text-align: center;
}

.chapter-info {
  color: #1890ff;
  font-weight: 500;
  margin: 8px 0;
}

.help-text {
  color: #999;
  font-size: 12px;
  margin-top: 12px;
  line-height: 1.4;
}
</style> 