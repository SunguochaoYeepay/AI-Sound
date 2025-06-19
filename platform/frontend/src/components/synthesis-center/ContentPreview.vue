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
                    <a-dropdown>
                      <a-button
                        type="primary"
                        size="small"
                        :disabled="!canStart"
                        :loading="synthesisStarting"
                      >
                        🎯 开始合成 <DownOutlined />
                      </a-button>
                      <template #overlay>
                        <a-menu>
                          <a-menu-item key="normal" @click="$emit('start-synthesis')">
                            <div style="display: flex; align-items: center; gap: 8px;">
                              <span>🎤</span>
                              <div>
                                <div style="font-weight: 500;">TTS语音合成</div>
                                <div style="font-size: 11px; color: #666;">仅生成对话语音</div>
                              </div>
                            </div>
                          </a-menu-item>
                          <a-menu-item key="environment" @click="$emit('start-environment-synthesis')">
                            <div style="display: flex; align-items: center; gap: 8px;">
                              <span>🌍</span>
                              <div>
                                <div style="font-weight: 500;">环境音混合合成</div>
                                <div style="font-size: 11px; color: #666;">智能生成环境音效并混合</div>
                              </div>
                            </div>
                          </a-menu-item>
                        </a-menu>
                      </template>
                    </a-dropdown>
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
                  
                  <!-- 重新合成下拉菜单 -->
                  <a-dropdown v-if="selectedChapterStatus === 'completed' || selectedChapterStatus === 'partial_completed'">
                    <a-button size="small">
                      重新合成
                      <DownOutlined />
                    </a-button>
                    <template #overlay>
                      <a-menu>
                        <a-menu-item key="restart-normal" @click="$emit('restart-synthesis')">
                          <div style="display: flex; align-items: center; gap: 8px;">
                            <span>🎤</span>
                            <div>
                              <div style="font-weight: 500;">TTS语音合成</div>
                              <div style="font-size: 11px; color: #666;">仅生成对话语音</div>
                            </div>
                          </div>
                        </a-menu-item>
                        <a-menu-item key="restart-environment" @click="$emit('start-environment-synthesis')">
                          <div style="display: flex; align-items: center; gap: 8px;">
                            <span>🌍</span>
                            <div>
                              <div style="font-weight: 500;">环境音混合合成</div>
                              <div style="font-size: 11px; color: #666;">智能生成环境音效并混合</div>
                            </div>
                          </div>
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
            <p class="help-text">
              智能准备将自动分析章节内容，识别角色对话，生成语音合成配置。<br/>
              这是使用AI技术的一键式准备功能，通常需要1-3分钟完成。
            </p>
          </div>
        </div>
      </a-empty>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, h } from 'vue'
import { Empty, Modal, message } from 'ant-design-vue'
import { DownOutlined } from '@ant-design/icons-vue'
import DialogueBubble from './DialogueBubble.vue'
import apiClient from '@/api/config.js'

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
  'start-environment-synthesis',
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
  
  // 🔧 调试：输出段落数据结构
  if (segments.length > 0) {
    console.log('📝 段落数据结构示例:', {
      章节ID: chapterResult.chapter_id,
      段落总数: segments.length,
      第一个段落: segments[0],
      segment_id字段: segments[0]?.segment_id,
      前3个段落的ID: segments.slice(0, 3).map(s => ({ 
        segment_id: s.segment_id, 
        text: s.text?.substring(0, 20) 
      }))
    })
  }
  
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
    // 🔧 修复：使用segment对象中的真正segment_id，而不是数组索引
    const segmentWithCorrectId = {
      ...segment,
      // 保持原有的segment_id，如果没有则使用UI索引作为后备
      segment_id: segment.segment_id || segment.id || (segmentIndexOrSegment + 1),
      ui_index: segmentIndexOrSegment + 1 // 保留UI索引用于显示
    }
    console.log('🎵 播放段落 (来自DialogueBubble):', {
      ui_index: segmentIndexOrSegment + 1,
      segment_id: segmentWithCorrectId.segment_id,
      text: segment.text?.substring(0, 30)
    })
    emit('play-segment', segmentWithCorrectId)
  } else {
    // 第一种情况：segmentIndexOrSegment就是segment对象
    console.log('🎵 播放段落 (直接调用):', {
      segment_id: segmentIndexOrSegment.segment_id || segmentIndexOrSegment.id,
      text: segmentIndexOrSegment.text?.substring(0, 30)
    })
    emit('play-segment', segmentIndexOrSegment)
  }
}

const handleRefreshPreparation = () => {
  emit('refresh-preparation')
}

const handleTriggerPreparation = async () => {
  if (!props.selectedChapter) {
    message.warning('请先选择要智能准备的章节')
    return
  }
  
  console.log('🎭 准备智能准备章节:', {
    selectedChapter: props.selectedChapter,
    chapterInfo: getSelectedChapterInfo(),
    project: props.project?.name
  })
  
  // 显示确认对话框
  console.log('📋 显示智能准备确认对话框...')
  Modal.confirm({
    title: '智能准备章节',
    content: h('div', [
      h('p', '即将开始智能准备以下章节：'),
      h('p', { style: 'font-weight: 600; color: #1890ff; margin: 8px 0;' }, 
        `第${getSelectedChapterInfo()?.chapter_number}章 ${getSelectedChapterInfo()?.chapter_title || getSelectedChapterInfo()?.title}`
      ),
      h('br'),
      h('p', '智能准备将：'),
      h('ul', { style: 'margin: 8px 0; padding-left: 20px;' }, [
        h('li', '🎭 智能识别章节中的角色和对话'),
        h('li', '📝 自动分段并生成语音合成配置'),
        h('li', '🎨 为角色自动分配声音'),
        h('li', '📋 生成完整的合成计划')
      ]),
      h('br'),
      h('p', { style: 'color: #666; font-size: 13px;' }, '此操作可能需要1-3分钟，请耐心等待。'),
      h('p', { style: 'color: #52c41a; font-size: 12px; margin-top: 8px;' }, '🚀 使用快速模式，大幅减少处理时间')
    ]),
    width: 500,
    okText: '开始智能准备',
    cancelText: '取消',
    onOk: async () => {
      console.log('✅ 用户确认开始智能准备')
      await executePreparation()
    },
    onCancel: () => {
      console.log('❌ 用户取消智能准备')
    }
  })
}

const executePreparation = async () => {
  let hideLoading = null
  let websocket = null
  
  try {
    console.log('🚀 用户确认开始智能准备，开始执行...')
    
    // 🔧 修复：确保只在用户确认后才显示loading状态
    emit('trigger-preparation-loading', true)
    
    // 🔧 建立WebSocket连接监听进度
    try {
      const wsUrl = `ws://localhost:8000/api/v1/analysis/ws/progress/${props.selectedChapter}`
      websocket = new WebSocket(wsUrl)
      
      websocket.onmessage = (event) => {
        const data = JSON.parse(event.data)
        if (data.type === 'progress_update') {
          console.log('📊 智能准备进度:', data.data)
          // 可以在这里更新进度显示
        }
      }
      
      websocket.onerror = (error) => {
        console.warn('⚠️ WebSocket连接失败:', error)
      }
    } catch (wsError) {
      console.warn('⚠️ WebSocket初始化失败:', wsError)
    }
    
    // 🔧 延迟100ms显示loading消息，确保在确认对话框关闭后
    await new Promise(resolve => setTimeout(resolve, 100))
    hideLoading = message.loading('正在进行智能准备，请稍候...', 0)
    
    // 构造API调用URL
    const apiUrl = `/content-preparation/prepare-synthesis/${props.selectedChapter}`
    console.log('📡 调用API:', apiUrl)
    
    // 调用智能准备API - 复用书籍智能准备的API（优化版）
    const response = await apiClient.post(apiUrl, {
      auto_add_narrator: true,
      processing_mode: 'auto',
      tts_optimization: 'fast'  // 🚀 使用快速模式，减少token消耗
    })
    
    // 🔧 清除loading消息
    if (hideLoading) {
      hideLoading()
    }
    console.log('✅ 智能准备API响应:', response.data)
    
    if (response.data.success) {
      const result = response.data.data
      
      // 显示准备结果对话框
      Modal.success({
        title: '🎉 智能准备完成！',
        content: h('div', { style: 'text-align: left;' }, [
          h('p', { style: 'font-weight: 600;' }, 
            `第${getSelectedChapterInfo()?.chapter_number}章 ${getSelectedChapterInfo()?.chapter_title || getSelectedChapterInfo()?.title}`
          ),
          h('br'),
          h('div', { style: 'background: #f6f8fa; padding: 12px; border-radius: 6px; margin: 8px 0;' }, [
            h('p', { style: 'font-weight: 600; margin-bottom: 8px;' }, '📊 处理结果：'),
            h('p', { style: 'margin: 4px 0;' }, [
              '🎭 检测到 ',
              h('span', { style: 'color: #1890ff; font-weight: bold;' }, 
                result.processing_info?.characters_found || result.synthesis_json?.characters?.length || 0
              ),
              ' 个角色'
            ]),
            h('p', { style: 'margin: 4px 0;' }, [
              '📝 生成 ',
              h('span', { style: 'color: #52c41a; font-weight: bold;' }, 
                result.processing_info?.total_segments || result.synthesis_json?.synthesis_plan?.length || 0
              ),
              ' 个语音片段'
            ]),
            h('p', { style: 'margin: 4px 0;' }, [
              '🎙️ 自动添加旁白角色：',
              h('span', { 
                style: `color: ${result.processing_info?.narrator_added ? '#52c41a' : '#fa8c16'};` 
              }, result.processing_info?.narrator_added ? '是' : '否')
            ])
          ]),
          h('p', { style: 'color: #52c41a; margin-top: 12px;' }, '✅ 章节已准备就绪，可以开始语音合成！')
        ]),
        width: 500,
        okText: '开始合成',
        onOk: () => {
          // 刷新准备结果
          emit('refresh-preparation')
          message.info('数据已刷新，您现在可以开始合成了')
        }
      })
      
      message.success('智能准备完成，章节数据已更新')
      
      // 通知父组件刷新数据
      emit('refresh-preparation')
    }
  } catch (error) {
    console.error('❌ 智能准备失败:', error)
    console.error('📋 错误详情:', {
      status: error.response?.status,
      statusText: error.response?.statusText,
      data: error.response?.data,
      message: error.message
    })
    
    const errorDetail = error.response?.data?.detail || error.message || '智能准备失败'
    
    Modal.error({
      title: '智能准备失败',
      content: h('div', [
        h('p', '章节智能准备过程中发生错误：'),
        h('p', { 
          style: 'color: #ff4d4f; background: #fff2f0; padding: 8px; border-radius: 4px; margin: 8px 0; font-family: monospace;' 
        }, errorDetail),
        h('p', '请检查：'),
        h('ul', { style: 'margin: 8px 0; padding-left: 20px;' }, [
          h('li', '章节内容是否完整'),
          h('li', '网络连接是否正常'),
          h('li', '是否有足够的处理权限'),
          h('li', '后端服务是否正常运行')
        ])
      ]),
      width: 500
    })
    
    message.error('智能准备失败：' + errorDetail)
  } finally {
    // 🔧 确保在错误情况下也清理loading状态
    if (hideLoading) {
      hideLoading()
    }
    
    // 🔧 关闭WebSocket连接
    if (websocket && websocket.readyState === WebSocket.OPEN) {
      websocket.close()
    }
    
    emit('trigger-preparation-loading', false)
  }
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