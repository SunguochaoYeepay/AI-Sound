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
                  <!-- 待处理状态：显示对话语音生成按钮 -->
                  <template v-if="selectedChapterStatus === 'pending'">
                    <!-- 1. 对话语音生成 -->
                    <a-button
                      type="primary"
                      size="small"
                      :disabled="!canStart || synthesisStarting"
                      :loading="synthesisStarting"
                      @click="$emit('start-synthesis')"
                    >
                      🎤 对话语音生成
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

                  <!-- 失败状态：显示重新开始选项 -->
                  <template v-if="selectedChapterStatus === 'failed'">
                    <a-button type="primary" size="small" @click="$emit('restart-synthesis')">
                      🔄 重新合成
                    </a-button>
                  </template>
                  
                  <!-- 完成状态：独立的功能按钮 -->
                  <template v-if="selectedChapterStatus === 'completed' || selectedChapterStatus === 'partial_completed'">
                    <!-- 重新合成按钮 -->
                    <a-button size="small" @click="$emit('restart-synthesis')">
                      🔄 重新合成
                    </a-button>
                  </template>
                </a-space>
              </div>
            </div>
            
            <!-- 对话气泡 -->
            <div class="dialogue-bubbles">
              <DialogueBubble
                v-for="(segment, segmentIndex) in getDisplaySegments(chapterResult)"
                :key="`${chapterResult.chapter_id}-${segment.segment_id}`"
                :segment="segment"
                :segment-index="segment.segment_id"
                :is-completed="getSegmentStatus(chapterResult.chapter_id, segment.segment_id) === 'completed'"
                :is-playing="playingSegmentId === `${chapterResult.chapter_id}-${segment.segment_id}`"
                :project-status="project?.status"
                :current-segment="0"
                :project-id="project?.id"
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
import { getWebSocketUrl } from '@/config/services'
import DialogueBubble from './DialogueBubble.vue'
import apiClient, { llmAnalysisClient } from '@/api/config.js'

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
  'trigger-preparation-loading',
  'start-chapter-synthesis',
  'play-chapter', 
  'download-chapter',
  'start-synthesis',
  'pause-synthesis',
  'cancel-synthesis',
  'retry-synthesis',
  'play-audio',
  'download-audio',
  'restart-synthesis',
  'reset-project-status',
  'open-audio-editor'
])

const showAllSegments = ref(false)
const playingSegmentId = ref(null)

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

// 获取段落状态
const getSegmentStatus = (chapterId, segmentId) => {
  // 简化的状态判断，基于项目状态
  if (props.project?.status === 'completed') {
    return 'completed'
  }
  if (props.project?.status === 'processing') {
    const currentSegment = props.project?.current_segment || 0
    return segmentId < currentSegment ? 'completed' : 'processing'
  }
  return 'pending'
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
  let wsConnected = false
  
  try {
    console.log('🚀 用户确认开始智能准备，开始执行...')
    
    // 🔧 修复：确保只在用户确认后才显示loading状态
    emit('trigger-preparation-loading', true)
    
    // 🔧 先建立WebSocket连接并等待连接成功，再调用API
    try {
      const wsUrl = getWebSocketUrl('MAIN')
      console.log('📡 连接WebSocket:', wsUrl)
      websocket = new WebSocket(wsUrl)
      
      // 等待WebSocket连接建立
      await new Promise((resolve, reject) => {
        websocket.onopen = () => {
          console.log('✅ WebSocket连接成功，订阅智能准备进度主题')
          const subscribeMsg = {
            type: 'subscribe',
            topic: `analysis_session_${props.selectedChapter}`
          }
          console.log('📡 发送订阅消息:', subscribeMsg)
          websocket.send(JSON.stringify(subscribeMsg))
          wsConnected = true
          resolve()
        }
        
        websocket.onerror = (error) => {
          console.warn('⚠️ WebSocket连接失败:', error)
          reject(error)
        }
        
        // 3秒超时
        setTimeout(() => {
          if (!wsConnected) {
            console.warn('⚠️ WebSocket连接超时')
            resolve() // 仍然继续，不阻止API调用
          }
        }, 3000)
      })
      
      websocket.onmessage = (event) => {
        const message = JSON.parse(event.data)
        console.log('📨 收到WebSocket消息:', message)
        
        if (message.type === 'subscription_confirmed') {
          console.log('✅ WebSocket订阅确认:', message.topic)
          return
        }
        
        if (message.type === 'topic_message' && message.topic === `analysis_session_${props.selectedChapter}`) {
          const data = message.data
          if (data.type === 'progress_update') {
            console.log('📊 智能准备进度:', data.data)
            // 更新进度显示
            if (hideLoading) {
              hideLoading()
              const progress = data.data.progress || 0
              const progressMsg = data.data.message || '智能准备进行中'
              hideLoading = message.loading(`${progressMsg} (${progress}%)`, 0)
            }
          }
        }
      }
      
      websocket.onclose = () => {
        console.log('🔌 WebSocket连接关闭')
        wsConnected = false
      }
      
    } catch (wsError) {
      console.warn('⚠️ WebSocket初始化失败，将无法显示实时进度:', wsError)
    }
    
    // 显示初始loading消息
    hideLoading = message.loading('正在连接服务并准备智能分析...', 0)
    
    // 构造API调用URL
    const apiUrl = `/content-preparation/prepare-synthesis/${props.selectedChapter}`
    console.log('📡 调用API:', apiUrl)
    
    // 调用智能准备API - 使用长超时客户端和进度监控
    const response = await llmAnalysisClient.post(apiUrl, {
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
      message: error.message,
      code: error.code
    })
    
    // 详细的错误处理
    let errorDetail = '智能准备失败'
    let errorType = '未知错误'
    
    if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
      errorType = '请求超时'
      errorDetail = '智能准备处理时间过长，请重试或联系管理员'
    } else if (error.response) {
      // 服务器响应错误
      errorType = `服务器错误 (${error.response.status})`
      errorDetail = error.response.data?.detail || 
                   error.response.data?.message || 
                   error.response.statusText || 
                   `HTTP ${error.response.status} 错误`
    } else if (error.request) {
      // 网络错误
      errorType = '网络连接错误'
      errorDetail = '无法连接到服务器，请检查网络连接'
    } else {
      // 其他错误
      errorType = '客户端错误'
      errorDetail = error.message || '智能准备过程中发生未知错误'
    }
    
    Modal.error({
      title: `智能准备失败 - ${errorType}`,
      content: h('div', [
        h('p', '章节智能准备过程中发生错误：'),
        h('div', { 
          style: 'background: #fff2f0; padding: 12px; border-radius: 6px; margin: 12px 0; border-left: 4px solid #ff4d4f;' 
        }, [
          h('p', { style: 'color: #ff4d4f; font-weight: 600; margin: 0 0 8px 0;' }, errorType),
          h('p', { style: 'color: #333; margin: 0; font-family: monospace; font-size: 13px;' }, errorDetail)
        ]),
        h('div', { style: 'margin-top: 16px;' }, [
          h('p', { style: 'font-weight: 600; margin-bottom: 8px;' }, '解决建议：'),
          h('ul', { style: 'margin: 0; padding-left: 20px; color: #666;' }, [
            errorType.includes('超时') ? h('li', '请耐心等待或尝试分批处理较短的章节') : null,
            errorType.includes('网络') ? h('li', '检查网络连接是否稳定') : null,
            errorType.includes('服务器') ? h('li', '稍后重试或联系管理员') : null,
            h('li', '确保章节内容完整且格式正确'),
            h('li', '检查后端服务是否正常运行')
          ].filter(Boolean))
        ])
      ]),
      width: 600
    })
    
    message.error(`智能准备失败：${errorDetail}`)
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
  border-radius: 12px;
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
  gap: 8px;
  flex-wrap: wrap;
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

/* 暗黑模式适配 */
[data-theme="dark"] .content-preview {
  background: #1f1f1f !important;
}

[data-theme="dark"] .preparation-preview {
  background: #2d2d2d !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}

[data-theme="dark"] .chapter-divider {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .chapter-title {
  color: #fff !important;
}

[data-theme="dark"] .empty-preview {
  background: #1f1f1f !important;
}

[data-theme="dark"] .chapter-info {
  color: var(--primary-color) !important;
}

[data-theme="dark"] .help-text {
  color: #8c8c8c !important;
}

[data-theme="dark"] .no-preparation-content {
  color: #434343 !important;
}

[data-theme="dark"] .no-preparation-content p {
  color: #434343 !important;
}

/* 移动端响应式设计 */
@media (max-width: 768px) {
  .content-preview {
    padding: 16px;
  }
  
  .chapter-divider {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    margin: 16px 0 12px;
  }
  
  .chapter-title-section {
    flex: none;
  }
  
  .chapter-actions {
    flex-direction: column;
    gap: 8px;
    align-items: stretch;
  }
  
  /* 移动端按钮组适配 */
  .chapter-actions .ant-space {
    flex-direction: column !important;
    width: 100% !important;
  }
  
  .chapter-actions .ant-space-item {
    width: 100% !important;
  }
  
  .chapter-actions .ant-btn {
    width: 100% !important;
    margin: 0 !important;
  }
  
  .dialogue-list {
    padding: 16px;
  }
  
  .empty-preview {
    min-height: 200px;
    padding: 20px;
  }
}

@media (max-width: 480px) {
  .content-preview {
    padding: 12px;
  }
  
  .chapter-title {
    font-size: 14px;
  }
  
  .chapter-actions .ant-btn {
    font-size: 12px;
    padding: 4px 8px;
    height: 32px;
  }
  
  .dialogue-list {
    padding: 12px;
  }
}
</style> 