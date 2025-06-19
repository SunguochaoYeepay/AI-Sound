<template>
  <div class="synthesis-center">
    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载项目信息...">
        <div style="height: 400px;"></div>
      </a-spin>
    </div>

    <div v-else-if="project" class="synthesis-layout">
      <!-- 左侧：章节选择区域 -->
      <div class="left-panel">
        <div class="panel-header">
          <div class="header-with-back">
            <a-button type="text" @click="goBack" class="back-btn">
              <template #icon><ArrowLeftOutlined /></template>
            </a-button>
            <div class="project-info">
              <h3>📚 {{ project.book?.title || project.name }}</h3>
              <div class="project-meta">
                <span class="project-subtitle">{{ project.book?.author || '项目管理' }}</span>
                <a-tag :color="getStatusColor(project?.status)" size="small" class="status-tag">
                  {{ getStatusText(project?.status) }}
                </a-tag>
              </div>
            </div>
          </div>
        </div>
        
        <div class="chapter-selection-area">
          <!-- 章节控制栏 -->
          <div class="chapter-controls">
            <span class="selection-mode">📖 章节选择</span>
            <a-button size="small" @click="loadChapters" :loading="loadingChapters" type="text">
              <template #icon><ReloadOutlined /></template>
            </a-button>
          </div>
          
          <!-- 章节列表 -->
          <div class="chapters-list" v-if="project?.book?.id">
            <div v-if="loadingChapters" class="loading-state">
              <a-spin tip="加载章节列表..." />
            </div>
            
            <div v-else-if="availableChapters.length > 0" class="chapters-container">
              <div 
                v-for="chapter in availableChapters" 
                :key="chapter.id"
                class="chapter-menu-item"
                :class="{ 'active': selectedChapter === chapter.id }"
                @click="selectChapter(chapter.id)"
              >
                <div class="chapter-info">
                  <div class="chapter-title">
                    第{{ chapter.chapter_number }}章 {{ chapter.title || chapter.chapter_title || '未命名章节' }}
                  </div>
                  <div class="chapter-meta">
                    <span class="word-count">{{ formatNumber(chapter.word_count || 0) }} 字</span>
                    <span class="chapter-status" :class="getChapterStatusClass(chapter)">
                      {{ getChapterStatusText(chapter) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
            
            <div v-else class="empty-chapters">
              <a-empty description="暂无章节数据" :image="Empty.PRESENTED_IMAGE_SIMPLE">
                <a-button type="primary" @click="loadChapters">重新加载</a-button>
              </a-empty>
            </div>
          </div>
          
          <!-- 直接文本项目提示 -->
          <div v-else class="text-project-hint">
            <a-alert
              message="文本项目"
              description="该项目基于直接输入的文本，将自动按段落合成"
              type="info"
              show-icon
            />
          </div>
        </div>
      </div>

      <!-- 右侧：合成操作区域 -->
      <div class="right-panel">


        <!-- 合成内容预览区域 -->
        <div class="content-preview">


          <!-- 智能准备结果 -->
          <div v-if="preparationResults" class="preparation-preview">
            <!-- 角色对话预览 -->
            <div class="dialogue-preview">
              <!-- 对话列表 -->
              <div class="dialogue-list">
                <div v-for="(chapterResult, chapterIndex) in preparationResults.data" :key="chapterIndex">
                  <!-- 章节标题 -->
                  <div class="chapter-divider">
                    <div class="chapter-title-section">
                    <span class="chapter-title">
                      第{{ chapterResult.chapter_number }}章 {{ chapterResult.chapter_title }}
                    </span>
                      <!-- 章节统计信息 -->
                      <div class="chapter-stats">
                        <a-space>
                          <a-tag color="blue">📋 {{ chapterResult.synthesis_json?.synthesis_plan?.length || 0 }} 个段落</a-tag>
                          <a-tag color="green">🎭 {{ getChapterCharacterCount(chapterResult) }} 个角色</a-tag>
                          <a-tag color="orange">状态: {{ getStatusText(project.status) }}</a-tag>
                        </a-space>
                      </div>
                    </div>
                    <div class="chapter-actions">
                      <!-- 手动刷新按钮 -->
                      <a-button 
                        v-if="preparationResults && selectedChapter"
                        @click="refreshPreparationResults"
                        :loading="loadingResults"
                        size="small"
                        type="text"
                      >
                        🔄 刷新
                      </a-button>
                      
                      <!-- 章节级合成按钮组 -->
                      <a-space size="small">
                        <!-- 合成当前章节按钮 -->
                        <a-dropdown v-if="project.status === 'pending' || project.status === 'failed' || project.status === 'configured'">
                          <a-button
                            type="primary"
                            size="small"
                            :disabled="!canStartSynthesis"
                            :loading="synthesisStarting"
                            class="start-btn"
                          >
                            🎯 合成此章 <DownOutlined />
                          </a-button>
                          <template #overlay>
                            <a-menu>
                              <a-menu-item key="normal" @click="startChapterSynthesis(chapterResult.chapter_id, false)">
                                <div style="display: flex; align-items: center; gap: 8px;">
                                  <span>🎤</span>
                                  <div>
                                    <div style="font-weight: 500;">TTS语音合成</div>
                                    <div style="font-size: 11px; color: #666;">仅生成对话语音</div>
                                  </div>
                                </div>
                              </a-menu-item>
                              <a-menu-item key="environment" @click="showEnvironmentConfigModal(chapterResult.chapter_id)">
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

                        <!-- 已完成状态按钮：使用智能状态判断 -->
                        <template v-if="getDisplayStatus(project.status) === 'completed'">
                        <a-button
                          type="primary"
                            size="small"
                            @click="playChapterAudio(chapterResult.chapter_id)"
                            :loading="playingChapterAudio === chapterResult.chapter_id"
                            class="play-btn"
                          >
                            🔊 播放此章
                          </a-button>
                          <a-button
                            size="small"
                            @click="downloadChapterAudio(chapterResult.chapter_id)"
                            type="dashed"
                          >
                            📥 下载此章音频
                          </a-button>
                          <a-button
                            type="default"
                          size="small"
                          @click="restartChapterSynthesis(chapterResult.chapter_id)"
                          :loading="synthesisStarting"
                          class="restart-btn"
                        >
                          🔄 重新合成此章
                        </a-button>
                        </template>

                        <!-- 处理中状态按钮 -->
                        <template v-if="project.status === 'processing'">
                          <a-button
                            size="small"
                            @click="pauseSynthesis"
                            :loading="pausingGeneration"
                          >
                            ⏸️ 暂停
                          </a-button>
                          <a-button
                            size="small"
                            danger
                            @click="cancelSynthesis"
                            :loading="cancelingGeneration"
                          >
                            ⏹️ 取消
                          </a-button>
                        </template>

                        <a-button
                          v-if="project.status === 'paused' || (project.status === 'failed' && project.statistics?.completedSegments > 0)"
                          type="primary"
                          size="small"
                          @click="resumeChapterSynthesis(chapterResult.chapter_id)"
                          :loading="resumingGeneration"
                        >
                          ▶️ 继续合成此章
                        </a-button>
                        
                        <!-- Debug: 显示当前项目状态 -->
                        <a-tag :color="getStatusColor(project.status)" size="small">
                          {{ project.status }}
                        </a-tag>

                        <!-- 智能状态按钮：只有真正失败才显示重试 -->
                        <template v-if="getDisplayStatus(project.status) === 'failed'">
                          <a-button
                            type="primary"
                            size="small"
                            @click="retryChapterFailedSegments(chapterResult.chapter_id)"
                            :loading="resumingGeneration"
                          >
                            🔄 重试此章失败段落
                          </a-button>
                        </template>
                        
                        <!-- 有部分完成但失败的情况：显示下载按钮 -->
                        <template v-if="getDisplayStatus(project.status) === 'failed' && project.statistics?.completedSegments > 0">
                          <a-button
                            size="small"
                            @click="downloadChapterAudio(chapterResult.chapter_id)"
                            type="dashed"
                          >
                            📥 下载已完成部分
                          </a-button>
                        </template>
                      </a-space>
                    </div>
                  </div>
                  
                  <!-- 对话气泡 -->
                  <div class="dialogue-bubbles">
                    <div 
                      v-for="(segment, segmentIndex) in (chapterResult.synthesis_json?.synthesis_plan || []).slice(0, showAllSegments ? undefined : 10)" 
                      :key="segmentIndex"
                      class="dialogue-bubble"
                      :class="getCharacterClass(segment.speaker)"
                    >
                      <div class="bubble-header">
                        <span class="speaker-name">{{ segment.speaker }}</span>
                        <span class="segment-index">#{{ segmentIndex + 1 }}</span>
                      </div>
                      <div class="bubble-content">{{ segment.text }}</div>
                    </div>
                    
                    <div v-if="!showAllSegments && (chapterResult.synthesis_json?.synthesis_plan?.length || 0) > 10" class="show-more">
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
            <a-empty 
              description="未找到智能准备结果"
              :image="Empty.PRESENTED_IMAGE_SIMPLE"
            >
              <div class="empty-hint">
                <p v-if="!selectedChapter">{{ getStartHint() }}</p>
                <div v-else class="no-preparation-content">
                  <p>当前章节尚未进行智能准备</p>
                  <p class="chapter-info">选中章节: 第{{ getSelectedChapterInfo()?.chapter_number }}章 {{ getSelectedChapterInfo()?.chapter_title || getSelectedChapterInfo()?.title }}</p>
                  <a-space direction="vertical" style="margin-top: 16px;">
                    <a-button type="primary" @click="triggerIntelligentPreparation" :loading="loadingResults">
                      🎭 开始智能准备
                    </a-button>
                    <a-button type="dashed" @click="refreshPreparationResults" :loading="loadingResults">
                      🔄 重新加载
                    </a-button>
                  </a-space>
                  <p class="help-text">智能准备将分析章节内容，识别角色对话并生成合成配置</p>
                </div>
              </div>
            </a-empty>
          </div>
        </div>
      </div>
    </div>

    <!-- 合成进度监控抽屉 -->
    <a-drawer
      v-model:open="synthesisProgressDrawer"
      title="🎵 合成进度监控"
      placement="bottom"
      :height="220"
      :closable="true"
      @close="closeSynthesisDrawer"
    >
      <!-- 进度监控内容保持原有逻辑 -->
      <div class="progress-container">
                  <!-- 简化的进度显示 -->
        <div class="simple-progress">
          <!-- 标题和控制按钮在一行 -->
          <div class="progress-title-row">
            <span class="progress-title">{{ getSynthesisProgressTitle() }}</span>
            
            <!-- 实时通信状态指示器 -->
            <div class="websocket-status" v-if="project?.status === 'processing'">
              <a-tag 
                :color="wsStore.connected ? 'success' : 'warning'" 
                size="small"
                style="margin-right: 8px;"
              >
                <template #icon>
                  <svg width="10" height="10" viewBox="0 0 24 24" :fill="wsStore.connected ? '#52c41a' : '#fa8c16'">
                    <circle cx="12" cy="12" r="6"/>
                  </svg>
                </template>
                {{ wsStore.connected ? '实时连接' : '连接中断' }}
              </a-tag>
            </div>
            
            <!-- 合成控制按钮 -->
            <div class="synthesis-controls" v-if="project?.status === 'processing' || project?.status === 'paused'">
              <a-space size="small">
                <a-button 
                  v-if="project?.status === 'processing'"
                  size="small"
                  @click="pauseSynthesis"
                  :loading="pausingGeneration"
                  danger
                >
                  ⏸️ 暂停
                </a-button>
                <a-button 
                  size="small"
                  @click="cancelSynthesis"
                  :loading="cancelingGeneration"
                  danger
                >
                  ❌ 取消
                </a-button>
              </a-space>
            </div>
          </div>
          
          <!-- 进度条 -->
          <a-progress 
            :percent="getCorrectProgress()" 
            :status="getProgressStatus()"
            :stroke-color="getProgressColor()"
            :show-info="true"
            size="default"
          />
          
          <!-- 紧凑的统计信息 -->
          <div class="compact-stats">
            <span class="stat-item">
              <span class="stat-label">进度:</span>
              <span class="stat-value completed">{{ progressData.completed_segments }}</span>
              <span class="stat-separator">/</span>
              <span class="stat-value total">{{ progressData.total_segments }}</span>
            </span>
            
            <span class="stat-item" v-if="progressData.failed_segments > 0">
              <span class="stat-label">失败:</span>
              <span class="stat-value failed">{{ progressData.failed_segments }}</span>
            </span>
            
            <span class="stat-item">
              <span class="stat-label">用时:</span>
              <span class="stat-value time">{{ synthesisElapsedTime }}秒</span>
            </span>
        </div>

                  <!-- 当前处理状态 -->
          <div class="current-status" v-if="progressData.current_processing && progressData.status === 'processing'">
            <span class="status-text">{{ progressData.current_processing }}</span>
          </div>
          
          <!-- 持久化错误通知 -->
          <div class="persistent-error-notice" v-if="getDisplayStatus(progressData.status) === 'failed'">
            <a-alert
              type="error"
              :show-icon="true"
              :closable="false"
              style="margin-bottom: 16px;"
            >
              <template #message>
                <div class="error-notice-content">
                  <div class="error-title">
                    🚨 合成失败
                  </div>
                  <div class="error-summary">
                    {{ progressData.failed_segments }} 个段落合成失败，请检查配置后重试
                  </div>
                </div>
              </template>
            </a-alert>
          </div>
          
          <!-- 成功完成提示 -->
          <div class="persistent-success-notice" v-if="getDisplayStatus(progressData.status) === 'completed'">
            <a-alert
              type="success"
              :show-icon="true"
              :closable="false"
              style="margin-bottom: 16px;"
            >
              <template #message>
                <div class="success-notice-content">
                  <div class="success-title">
                    ✅ 合成完成
                  </div>
                  <div class="success-summary">
                    所有 {{ progressData.total_segments }} 个段落合成成功
                  </div>
                </div>
              </template>
            </a-alert>
          </div>
          
          <!-- 失败详情显示 -->
          <div class="failure-details" v-if="getDisplayStatus(progressData.status) === 'failed' && progressData.failed_segments > 0">
            <div class="failure-header">
              <span class="failure-title">❌ 失败详情 ({{ progressData.failed_segments }} 个段落)</span>
              <a-button size="small" type="primary" @click="retryFailedSegments" :loading="resumingGeneration">
                🔄 重试失败段落
              </a-button>
            </div>
            
            <!-- 失败原因说明 -->
            <div class="failure-reasons">
              <div class="failure-reason-item">
                <span class="reason-icon">🔧</span>
                <span class="reason-text">可能原因：声音配置缺失、TTS服务异常、或文本处理错误</span>
              </div>
              <div class="failure-reason-item">
                <span class="reason-icon">💡</span>
                <span class="reason-text">建议：检查角色声音分配，确保TTS服务正常运行</span>
              </div>
            </div>
            

          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 环境音配置弹窗 -->
    <a-modal
      v-model:open="environmentConfigModal"
      title="🌍 环境音混合配置"
      :width="500"
      @ok="startEnvironmentSynthesis"
      @cancel="environmentConfigModal = false"
      :ok-text="'开始环境音混合合成'"
      :cancel-text="'取消'"
      :ok-button-props="{ loading: synthesisStarting }"
    >
      <div class="environment-config-content">
        <div class="config-section">
          <h4>🎵 环境音效配置</h4>
          <p class="config-description">
            系统将自动分析文本内容，生成适合的环境音效并与语音进行智能混合。
          </p>
          
          <div class="config-item">
            <label class="config-label">环境音音量：</label>
            <a-slider
              v-model:value="synthesisConfig.environmentVolume"
              :min="0"
              :max="1"
              :step="0.1"
              :marks="{
                0: '0%',
                0.3: '30%',
                0.5: '50%',
                0.7: '70%',
                1: '100%'
              }"
              style="margin: 8px 0;"
            />
            <div class="volume-hint">
              当前音量：{{ Math.round(synthesisConfig.environmentVolume * 100) }}%
            </div>
          </div>
        </div>
        
        <div class="config-section">
          <h4>🎬 会生成的环境音效</h4>
          <div class="environment-examples">
            <a-tag color="blue">🌆 日出日落</a-tag>
            <a-tag color="green">🌳 森林鸟叫</a-tag>
            <a-tag color="cyan">🌊 海浪声</a-tag>
            <a-tag color="orange">🏏️ 城市噪音</a-tag>
            <a-tag color="purple">⛈️ 雷雨声</a-tag>
            <a-tag color="gold">🎵 背景音乐</a-tag>
          </div>
          <p class="examples-note">
            基于文本内容自动选择适合的环境音效
          </p>
        </div>
        
        <div class="config-section">
          <h4>⚠️ 注意事项</h4>
          <ul class="warning-list">
            <li>环境音生成需要额外时间，合成时间会显著增加</li>
            <li>需要足够的GPU资源来处理TTS和环境音生成</li>
            <li>最终文件大小会比普通TTS大一些</li>
          </ul>
        </div>
      </div>
    </a-modal>
    
    <!-- JSON测试弹窗保持原有 -->
    <!-- ... 其他弹窗组件 ... -->
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted, nextTick, h } from 'vue'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import { message, Modal, Empty } from 'ant-design-vue'
import { ArrowLeftOutlined, ReloadOutlined, DownOutlined } from '@ant-design/icons-vue'
import { readerAPI, charactersAPI, intelligentAnalysisAPI, systemAPI, booksAPI } from '@/api'
import { useWebSocketStore } from '@/stores/websocket.js'
import { useAudioPlayerStore } from '@/stores/audioPlayer'
import { getAudioService } from '@/utils/audioService'

const router = useRouter()
const route = useRoute()
const wsStore = useWebSocketStore()

// 使用统一的音频播放服务
const audioStore = useAudioPlayerStore()

// 响应式数据
const loading = ref(true)
const synthesisStarting = ref(false)
const pausingGeneration = ref(false)
const resumingGeneration = ref(false)
const cancelingGeneration = ref(false)
const refreshing = ref(false)
const project = ref(null)
const availableVoices = ref([])
const progressTimer = ref(null)
const previewLoading = ref(null)
const currentPlayingVoice = ref(null)
const currentAudio = ref(null)
const checkingService = ref(false)

// 章节选择相关 - 固定为章节模式
const synthesisMode = ref('chapters') // 固定为 'chapters'
const availableChapters = ref([])
const selectedChapter = ref(null) // 改为单选
const loadingChapters = ref(false)

// Mock分析相关代码已移除，如需要请使用智能准备功能

// 智能准备结果相关
const preparationResults = ref(null)
const loadingResults = ref(false)

// 合成进度和片段相关
const currentProcessingSegment = ref(null)
const synthesisProgressDrawer = ref(false)
const synthesisElapsedTime = ref(0)
const completedSegments = ref([])
const loadingCompletedSegments = ref(false)
const playingSegment = ref(null)
const showAllCompleted = ref(false)


// 音频播放相关
const loadingFinalAudio = ref(false)
const downloadingAudio = ref(false)
const playingFinalAudio = ref(false)
const playingChapterAudio = ref(null) // 正在播放的章节ID
const currentlyPlaying = ref(null) // 当前播放信息 { type, id, name }
// unifiedAudioPlayer已移除，统一使用audioStore

// 合成配置
const synthesisConfig = reactive({
  quality: 'standard',
  parallelTasks: 1,
  enableEnvironment: false,
  environmentVolume: 0.3
})

// 其他状态变量
const showAllSegments = ref(false)

// 环境音混合配置
const environmentConfigModal = ref(false)
const selectedChapterForEnvironment = ref(null)
// JSON测试功能已移除，请使用标准的智能准备流程
// 合成进度监控抽屉相关
const synthesisStartTime = ref(null)
const segmentStatuses = ref([]) // 段落状态列表
const elapsedTimer = ref(null)
const unsubscribeWebSocket = ref(null) // WebSocket取消订阅函数
const progressData = ref({
  progress: 0,
  status: 'pending',
  completed_segments: 0,
  total_segments: 0,
  failed_segments: 0,
  current_processing: ''
})

// 🚀 计算属性 - 统一进度数据源（基于当前选择，不显示历史数据）
const currentProgressData = computed(() => {
  console.log('🔍 currentProgressData计算触发')
  console.log('🔍 synthesisProgressDrawer.value:', synthesisProgressDrawer.value)
  console.log('🔍 progressData.value:', progressData.value)
  console.log('🔍 preparationResults.value:', preparationResults.value)
  
  // 如果合成监控抽屉已打开且有实时数据，优先使用实时数据
  if (synthesisProgressDrawer.value && progressData.value.total_segments > 0) {
    const result = {
      totalSegments: progressData.value.total_segments,
      completedSegments: progressData.value.completed_segments,
      failedSegments: progressData.value.failed_segments,
      percent: progressData.value.progress
    }
    console.log('🔍 使用progressData结果:', result)
    return result
  }
  
  // ⚠️ 重要修改：只有当用户选择了章节并加载了智能准备结果时，才显示统计
  // 不再显示项目的历史统计数据
  if (preparationResults.value?.data?.length > 0) {
    const totalSegments = getTotalSegments()
    const result = {
      totalSegments: totalSegments,
      completedSegments: 0, // 新准备的结果，还没有完成的
      failedSegments: 0,
      percent: 0
    }
    console.log('🔍 使用当前选择的准备结果:', result)
    return result
  }
  
  // 默认状态：没有选择章节或没有准备结果
  const defaultResult = {
    totalSegments: 0,
    completedSegments: 0,
    failedSegments: 0,
    percent: 0
  }
  console.log('🔍 使用默认结果（无选择）:', defaultResult)
  return defaultResult
})

const progressPercent = computed(() => {
  const result = currentProgressData.value.percent
  console.log('🔍 progressPercent计算:', {
    input: currentProgressData.value,
    result: result
  })
  return result
})

// 音频预览URL
const audioPreviewUrl = computed(() => {
  // 只有项目完成且有最终音频路径时才返回URL
  if (!project.value?.final_audio_path || !project.value?.id || project.value.status !== 'completed') {
    return null
  }
  // 构建音频预览URL
  return `/api/v1/novel-reader/projects/${project.value.id}/download`
})

const canStartSynthesis = computed(() => {
  const hasValidChapterSelection = selectedChapter.value !== null
  const hasPreparationResults = preparationResults.value?.data?.length > 0
  const hasSegments = getTotalSegments() > 0
  
  return project.value?.status !== 'processing' &&
         hasValidChapterSelection &&
         hasPreparationResults &&
         hasSegments
})

// 章节选择相关计算属性
// const chapterCheckAll = computed(() => {
//   return availableChapters.value.length > 0 && selectedChapters.value.length === availableChapters.value.length
// })

// const chapterIndeterminate = computed(() => {
//   return selectedChapters.value.length > 0 && selectedChapters.value.length < availableChapters.value.length
// })

// 方法
const goBack = () => {
  router.go(-1) // 返回上一页
}

const closeSynthesisDrawer = () => {
  synthesisProgressDrawer.value = false
}

// showJsonTestModal 方法已移除

// 智能状态显示：根据实际完成情况显示状态
// 注意：partial_completed 是后端返回的中间状态，需要根据实际数据智能转换
const getDisplayStatus = (rawStatus) => {
  // 如果是 partial_completed，检查是否实际已经全部完成
  if (rawStatus === 'partial_completed') {
    // 🔧 修复：使用项目统计数据，不是progressData
    const completed = project.value?.statistics?.completedSegments || project.value?.processed_segments || 0
    const total = project.value?.statistics?.totalSegments || project.value?.total_segments || 0
    const failed = project.value?.statistics?.failedSegments || project.value?.failed_segments || 0
    
    console.log('🔍 [getDisplayStatus] 智能转换partial_completed状态:', { 
      completed, total, failed,
      rawStatus, willConvertTo: total > 0 && completed === total && failed === 0 ? 'completed' : (failed > 0 ? 'failed' : 'partial_completed')
    })
    
    // 如果全部完成且没有失败，智能转换为已完成
    if (total > 0 && completed === total && failed === 0) {
      return 'completed'
    }
    // 如果有失败的，智能转换为失败
    if (failed > 0) {
      return 'failed'
    }
    // 否则保持部分完成状态
  }
  return rawStatus
}

const getStatusText = (status) => {
  // 🔧 修复：使用智能显示状态而不是原始状态
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
  console.log(`🏷️ [getStatusText] 原始状态: ${status}, 显示状态: ${displayStatus}, 文本: ${texts[displayStatus]}`)
  return texts[displayStatus] || displayStatus
}

const getStatusColor = (status) => {
  // 🔧 修复：使用智能显示状态而不是原始状态  
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
  console.log(`🎨 [getStatusColor] 原始状态: ${status}, 显示状态: ${displayStatus}, 颜色: ${colors[displayStatus]}`)
  return colors[displayStatus] || 'default'
}

const getStartHint = () => {
  if (!selectedChapter.value) {
    return '请选择要合成的章节，系统将自动加载智能准备结果'
  }
  if (loadingResults.value) {
    return '正在加载智能准备结果...'
  }
  if (!preparationResults.value?.data?.length) {
    return '正在自动加载智能准备结果，请稍候...'
  }
  if (getTotalSegments() === 0) {
    return '没有可合成的片段'
  }
  return '可以开始合成'
}

// 章节选择相关方法
const loadChapters = async () => {
  // 检查项目是否关联了书籍
  if (!project.value?.book?.id) {
    console.log('项目未关联书籍，跳过章节加载')
    availableChapters.value = []
    return
  }
  
  loadingChapters.value = true
  try {
    const response = await booksAPI.getBookChapters(project.value.book.id)
    if (response.data.success) {
      availableChapters.value = response.data.data || []
      message.success(`加载了 ${availableChapters.value.length} 个章节`)
      
      // 🎯 默认选中第一个章节
      if (availableChapters.value.length > 0 && !selectedChapter.value) {
        const firstChapter = availableChapters.value[0]
        console.log('🎯 默认选中第一个章节:', firstChapter.chapter_title)
        await selectChapter(firstChapter.id)
      }
    } else {
      message.error('加载章节失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('加载章节失败:', error)
    message.error('加载章节失败: ' + error.message)
  } finally {
    loadingChapters.value = false
  }
}

// 自动加载章节（因为现在固定为章节模式）
const autoLoadChapters = async () => {
  if (availableChapters.value.length === 0) {
    await loadChapters()
  }
}

const selectChapter = async (chapterId) => {
  selectedChapter.value = chapterId
  
  // 自动加载智能准备结果
  if (selectedChapter.value) {
    await loadPreparationResults()
  } else {
    // 清空准备结果
    preparationResults.value = null
  }
}

// 清空章节选择
const clearChapterSelection = () => {
  selectedChapter.value = null
  // 清空智能准备结果
  preparationResults.value = null
  message.info('已清空章节选择和智能准备结果')
}

const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toString()
}

const getChapterStatusText = (chapter) => {
  const status = chapter.analysis_status || chapter.synthesis_status || 'pending'
  const statusMap = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败',
    'ready': '准备就绪'
  }
  return statusMap[status] || '未知'
}

const getChapterStatusClass = (chapter) => {
  const status = chapter.analysis_status || chapter.synthesis_status || 'pending'
  return `status-${status}`
}

// Mock分析方法和相关代码已完全移除

// Mock相关的applyMockResult、updateCharactersFromAnalysis、getCharacterSampleText方法已移除

// clearMockResult 方法已移除

// JSON测试方法已全部移除

// formatJsonContent 方法已移除

// 所有JSON测试相关的残留方法已完全清理

// 加载项目详情
const loadProject = async () => {
  try {
    const projectId = route.params?.projectId
    if (!projectId) {
      throw new Error('项目ID不存在，请检查URL路径')
    }
    
    console.log('🔍 [loadProject] 项目ID:', projectId)
    const response = await readerAPI.getProjectDetail(projectId)
    
    if (response.data.success) {
      project.value = response.data.data
      
      // 初始化统计信息
      project.value.statistics = reactive({
        totalSegments: project.value.total_segments || 0,
        completedSegments: project.value.processed_segments || 0,
        failedSegments: 0,
        processingSegments: 0,
        pendingSegments: 0
      })
      
      // 🚀 修复：始终获取最新统计信息，不管项目状态
      try {
        const progressResponse = await readerAPI.getProgress(projectId)
        if (progressResponse.data.success) {
          const progress = progressResponse.data.data
          console.log('📊 获取到进度数据:', progress)
          
          // 更新统计信息，映射字段名
          Object.assign(project.value.statistics, {
            totalSegments: progress.segments.total,
            completedSegments: progress.segments.completed,
            failedSegments: progress.segments.failed,
            processingSegments: progress.segments.processing,
            pendingSegments: progress.segments.pending
          })
          
          // 同步更新项目基础字段
          project.value.total_segments = progress.segments.total
          project.value.processed_segments = progress.segments.completed
          project.value.status = progress.status
          project.value.current_segment = progress.current_segment
          
          // 同步更新进度数据用于显示
          progressData.value = {
            progress: progress.progress_percentage || 0,
            status: progress.status,
            completed_segments: progress.segments.completed,
            total_segments: progress.segments.total,
            failed_segments: progress.segments.failed,
            current_processing: progress.status === 'processing' ? `正在处理第 ${progress.current_segment || 1} 段` : '等待开始'
          }
          
          console.log('📊 更新后的statistics:', project.value.statistics)
          console.log('📊 更新后的progressData:', progressData.value)
        } else {
          console.warn('获取进度失败，使用项目基础数据:', progressResponse.data.message)
          // Fallback到项目基础数据
          progressData.value = {
            progress: project.value.total_segments > 0 ? Math.round((project.value.processed_segments / project.value.total_segments) * 100) : 0,
            status: project.value.status,
            completed_segments: project.value.processed_segments || 0,
            total_segments: project.value.total_segments || 0,
            failed_segments: Math.max(0, (project.value.total_segments || 0) - (project.value.processed_segments || 0)),
            current_processing: project.value.status === 'processing' 
              ? `正在处理第 ${project.value.current_segment || 1} 段` 
              : project.value.status === 'completed' 
                ? '合成已完成' 
                : '等待开始'
          }
        }
      } catch (error) {
        console.warn('获取进度异常，使用项目基础数据:', error)
        // Fallback到项目基础数据
        progressData.value = {
          progress: project.value.total_segments > 0 ? Math.round((project.value.processed_segments / project.value.total_segments) * 100) : 0,
          status: project.value.status,
          completed_segments: project.value.processed_segments || 0,
          total_segments: project.value.total_segments || 0,
          failed_segments: Math.max(0, (project.value.total_segments || 0) - (project.value.processed_segments || 0)),
          current_processing: project.value.status === 'processing' 
            ? `正在处理第 ${project.value.current_segment || 1} 段` 
            : project.value.status === 'completed' 
              ? '合成已完成' 
              : '等待开始'
        }
      }
      
      console.log('🔍 最终的currentProgressData:', currentProgressData.value)
      
    }
  } catch (error) {
    console.error('加载项目失败:', error)
    message.error('加载项目失败')
  } finally {
    loading.value = false
  }
}

// 刷新项目数据
const refreshProjectData = async () => {
  if (refreshing.value) return
  
  refreshing.value = true
  try {
    console.log('🔄 手动刷新项目数据...')
    const projectId = route.params?.projectId
    if (!projectId) {
      throw new Error('项目ID不存在，无法刷新数据')
    }
    
    // 重新加载项目数据
    const response = await readerAPI.getProjectDetail(projectId)
    if (response.data.success) {
      const newProject = response.data.data
      
      console.log('🔄 刷新前数据:', {
        total: project.value.total_segments,
        processed: project.value.processed_segments,
        statistics: project.value.statistics
      })
      
      // 更新项目数据
      project.value = newProject
      
      // 重新初始化统计信息
      project.value.statistics = reactive({
        totalSegments: newProject.total_segments || 0,
        completedSegments: newProject.processed_segments || 0,
        failedSegments: 0,
        processingSegments: 0,
        pendingSegments: 0
      })
      
      // 如果项目正在处理，获取最新进度
      if (newProject.status === 'processing' || newProject.total_segments > 0) {
        try {
          const progressResponse = await readerAPI.getProgress(projectId)
          if (progressResponse.data.success) {
            const progress = progressResponse.data.data
            Object.assign(project.value.statistics, {
              totalSegments: progress.segments.total,
              completedSegments: progress.segments.completed,
              failedSegments: progress.segments.failed,
              processingSegments: progress.segments.processing,
              pendingSegments: progress.segments.pending
            })
            
            // 同步更新项目原始字段
            project.value.total_segments = progress.segments.total
            project.value.processed_segments = progress.segments.completed
            project.value.status = progress.status
            project.value.current_segment = progress.current_segment
          }
        } catch (progressError) {
          console.warn('获取进度失败:', progressError)
        }
      }
      
      // 更新进度显示数据
      progressData.value = {
        progress: project.value.total_segments > 0 ? Math.round((project.value.processed_segments / project.value.total_segments) * 100) : 0,
        status: project.value.status,
        completed_segments: project.value.processed_segments || 0,
        total_segments: project.value.total_segments || 0,
        failed_segments: project.value.statistics?.failedSegments || 0,
        current_processing: project.value.status === 'processing' 
          ? `正在处理第 ${project.value.current_segment || 1} 段` 
          : project.value.status === 'completed' 
            ? '合成已完成' 
            : '等待开始'
      }
      
      console.log('🔄 刷新后数据:', {
        total: project.value.total_segments,
        processed: project.value.processed_segments,
        statistics: project.value.statistics,
        progressPercent: progressPercent.value
      })
      
      message.success('数据已刷新')
    } else {
      message.error('刷新失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('刷新项目数据失败:', error)
    message.error('刷新失败: ' + error.message)
  } finally {
    refreshing.value = false
  }
}

// 已删除：过时的角色分析方法，现在使用智能准备结果

// 加载可用声音
const loadVoices = async () => {
  try {
    const response = await charactersAPI.getVoiceProfiles({ status: 'active' })
    if (response.data.success) {
      availableVoices.value = response.data.data
    }
  } catch (error) {
    console.error('加载声音列表失败:', error)
  }
}

// 试听声音
const playVoicePreview = async (voiceId, sampleText) => {
  try {
    if (!voiceId) {
      message.warning('请选择声音')
      return
    }

    if (!sampleText) {
      message.warning('没有示例文本')
      return
    }

    previewLoading.value = voiceId
    
    // 找到对应的声音配置
    const selectedVoice = availableVoices.value.find(v => v.id === voiceId)
    if (!selectedVoice) {
      message.error('找不到声音配置')
      return
    }

    await getAudioService().playVoicePreview(voiceId, selectedVoice.name, sampleText)
    
  } catch (error) {
    console.error('试听失败:', error)
    
    if (error.name === 'AbortError') {
      message.error('试听请求超时（90秒），TTS服务可能正在处理中，请稍后重试')
    } else if (error.message.includes('GPU') || error.message.includes('CUDA')) {
      message.error('GPU处理出错，请等待几秒后重试')
    } else if (error.message.includes('TTS服务内部错误')) {
      message.error('TTS服务出现内部错误，可能是GPU显存不足')
    } else if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
      message.error('无法连接到TTS服务，请检查服务状态')
    } else {
      message.error('试听失败: ' + error.message)
    }
  } finally {
    previewLoading.value = null
  }
}

// 开始合成
const startSynthesis = async () => {
  synthesisStarting.value = true
  try {
    console.log('=== 启动章节合成流程 ===')
    console.log('选中章节:', selectedChapter.value)
    
    // 构建合成参数 - 固定为章节模式
    const synthesisParams = {
      parallel_tasks: synthesisConfig.parallelTasks,
      synthesis_mode: 'chapters',
      chapter_ids: selectedChapter.value ? [selectedChapter.value] : []
    }
    
    message.info(`开始合成选中的章节`)
    
    const response = await readerAPI.startGeneration(project.value.id, synthesisParams)
    
    if (response.data.success) {
      message.success('合成任务已启动')
      project.value.status = 'processing'
      
      // 初始化合成进度监控
      initializeSynthesisMonitoring()
      
      // 打开进度监控抽屉
      synthesisProgressDrawer.value = true
      
      startWebSocketProgressMonitoring()
    } else {
      throw new Error(response.data.message || '启动失败')
    }
  } catch (error) {
    console.error('启动合成失败:', error)
    message.error('启动合成失败: ' + error.message)
  } finally {
    synthesisStarting.value = false
  }
}

// 暂停合成
const pauseSynthesis = async () => {
  pausingGeneration.value = true
  try {
    // 先检查当前状态
    const currentStatus = project.value.status
    console.log('暂停前项目状态:', currentStatus)
    
    if (currentStatus !== 'processing') {
      message.warning(`当前状态为 ${currentStatus}，无法暂停`)
      return
    }
    
    await readerAPI.pauseGeneration(project.value.id)
    message.success('合成已暂停')
    project.value.status = 'paused'
    
    // 暂停时停止WebSocket监控和计时器，但保持抽屉打开
    stopWebSocketProgressMonitoring()
    stopElapsedTimer()
    
    // 更新进度数据状态为暂停
    if (synthesisProgressDrawer.value) {
      progressData.value.status = 'paused'
      progressData.value.current_processing = '⏸️ 合成已暂停'
    }
  } catch (error) {
    console.error('暂停合成失败:', error)
    
    // 如果是状态错误，尝试刷新项目状态
    if (error.response?.data?.message?.includes('无法暂停')) {
      message.warning('项目状态已改变，正在刷新...')
      await refreshProjectStatus()
    } else {
      message.error('暂停合成失败: ' + (error.response?.data?.message || error.message))
    }
  } finally {
    pausingGeneration.value = false
  }
}

// 继续合成
const resumeSynthesis = async () => {
  resumingGeneration.value = true
  try {
    // 先检查当前状态
    const currentStatus = project.value.status
    console.log('继续前项目状态:', currentStatus)
    
    if (currentStatus !== 'paused' && currentStatus !== 'failed' && currentStatus !== 'partial_completed') {
      message.warning(`当前状态为 ${currentStatus}，无法继续合成`)
      return
    }
    
    // 根据状态选择合适的API
    if (currentStatus === 'paused') {
      // 暂停状态使用resume接口，传递选中的章节
      await readerAPI.resumeGeneration(project.value.id, {
        parallel_tasks: synthesisConfig.parallelTasks,
        chapter_ids: selectedChapter.value ? [selectedChapter.value] : []
      })
    } else {
      // failed 和 partial_completed 状态使用start接口，传递选中的章节
      await readerAPI.startGeneration(project.value.id, {
        parallel_tasks: synthesisConfig.parallelTasks,
        synthesis_mode: 'chapters',
        chapter_ids: selectedChapter.value ? [selectedChapter.value] : []
      })
    }
    message.success('合成已继续')
    project.value.status = 'processing'
    
    // 继续合成时也要重新初始化监控
    initializeSynthesisMonitoring()
    
    // 打开进度监控抽屉
    synthesisProgressDrawer.value = true
    
    startWebSocketProgressMonitoring()
  } catch (error) {
    console.error('继续合成失败:', error)
    
    // 如果是状态错误，尝试刷新项目状态
    if (error.response?.data?.message?.includes('状态')) {
      message.warning('项目状态已改变，正在刷新...')
      await refreshProjectStatus()
    } else {
      message.error('继续合成失败: ' + (error.response?.data?.message || error.message))
    }
  } finally {
    resumingGeneration.value = false
  }
}

// 取消合成
const cancelSynthesis = async () => {
  // 显示确认对话框
  Modal.confirm({
    title: '确认取消合成',
    content: '取消后已完成的片段将保留，但未完成的部分需要重新开始。确定要取消合成吗？',
    okText: '确定取消',
    okType: 'danger',
    cancelText: '继续合成',
    onOk: async () => {
      cancelingGeneration.value = true
      try {
        // 先检查当前项目状态
        const currentStatus = project.value.status
        console.log('当前项目状态:', currentStatus)
        
        // 如果当前状态是 processing，先暂停
        if (currentStatus === 'processing') {
          await readerAPI.pauseGeneration(project.value.id)
        }
        
        // 更新项目状态为已取消（无论之前是什么状态）
        project.value.status = 'cancelled'
        
        // 停止所有监控
        stopWebSocketProgressMonitoring()
        stopElapsedTimer()
        
        // 更新进度数据状态
        if (synthesisProgressDrawer.value) {
          progressData.value.status = 'cancelled'
          progressData.value.current_processing = '⏹️ 合成已取消'
        }
        
        message.success('合成已取消')
      } catch (error) {
        console.error('取消合成失败:', error)
        
        // 如果是因为状态不匹配的错误，直接标记为取消
        if (error.response?.data?.message?.includes('无法暂停')) {
          project.value.status = 'cancelled'
          stopWebSocketProgressMonitoring()
          stopElapsedTimer()
          
          if (synthesisProgressDrawer.value) {
            progressData.value.status = 'cancelled'
            progressData.value.current_processing = '⏹️ 合成已取消'
          }
          
          message.success('合成已取消')
        } else {
          message.error('取消合成失败: ' + (error.response?.data?.message || error.message))
        }
      } finally {
        cancelingGeneration.value = false
      }
    }
  })
}

// audioStore重复声明已移除

const playAudio = async (type, audioUrl, id, name) => {
  try {
    // 构建音频信息对象
    const audioInfo = {
      id: `${type}_${id}`,
      title: name,
      url: audioUrl,
      type: type,
      metadata: {
        originalType: type,
        originalId: id
      }
    }
    
    // 使用统一的音频播放器
    await audioStore.playAudio(audioInfo)
    
    // 更新本地播放状态（用于UI显示）
    currentlyPlaying.value = { type, id, name }
    if (type === 'chapter') {
      playingChapterAudio.value = id
    } else if (type === 'final') {
      playingFinalAudio.value = true
    } else if (type === 'segment') {
      playingSegment.value = id
    }
    
  } catch (error) {
    console.error('播放音频失败:', error)
    message.error(`播放${name}失败: ` + error.message)
  }
}

// 播放章节音频
const playChapterAudio = async (chapterId) => {
  if (!project.value?.id || !chapterId) {
    message.warning('项目或章节信息不完整')
    return
  }

  try {
    await getAudioService().playChapterAudio(project.value.id, chapterId, `第${chapterId}章`)
  } catch (error) {
    console.error('播放章节音频失败:', error)
    message.error('播放章节音频失败')
  }
}

// 播放完整音频
const playFinalAudio = async () => {
  if (!project.value?.id) {
    message.warning('项目信息不完整')
    return
  }

  loadingFinalAudio.value = true
  try {
    await getAudioService().playProjectAudio(
      project.value.id, 
      `${project.value.name || '项目'} - 完整音频`
    )
  } catch (error) {
    console.error('播放完整音频失败:', error)
    message.error('播放完整音频失败')
  } finally {
    loadingFinalAudio.value = false
  }
}

// 下载完整音频
const downloadFinalAudio = async () => {
  if (!project.value?.id) {
    message.warning('项目信息不完整')
    return
  }

  downloadingAudio.value = true
  try {
    const response = await readerAPI.downloadAudio(project.value.id)
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value.name || 'AI-Sound合成音频'}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success('音频下载完成')
  } catch (error) {
    console.error('下载音频失败:', error)
    let errorMessage = '下载音频失败'
    
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.message === 'Network Error') {
      errorMessage = '网络连接失败，请检查网络连接或稍后重试'
    }
    
    message.error(errorMessage)
  } finally {
    downloadingAudio.value = false
  }
}

// 查看已完成片段
const viewCompletedSegments = () => {
  // 加载已完成的片段并显示详情
  loadCompletedSegments()
  message.info('正在加载已完成的片段详情...')
}

// 下载音频
const downloadAudio = async () => {
  // 检查项目状态
  if (project.value?.status !== 'completed') {
    const statusText = {
      'pending': '等待处理',
      'configured': '已配置但未开始生成',
      'processing': '正在生成中',
      'paused': '已暂停',
      'failed': '生成失败'
    }[project.value?.status] || '未知状态'
    
    message.warning(`无法下载：项目当前状态为"${statusText}"，请先完成音频生成`)
    return
  }
  
  try {
    const response = await readerAPI.downloadAudio(project.value.id)
    // 处理文件下载
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value.name}_final.wav`
    link.click()
    window.URL.revokeObjectURL(url)
    message.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    
    // 改进错误处理
    let errorMessage = '下载失败'
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message === 'Network Error') {
      errorMessage = '网络连接失败，请检查网络连接或稍后重试'
    } else if (error.code === 'ERR_CONNECTION_RESET') {
      errorMessage = '连接被重置，请检查后端服务状态'
    }
    
    message.error(errorMessage)
  }
}

// 重新合成
const restartSynthesis = async () => {
  if (!project.value) return
  
  synthesisStarting.value = true
  try {
    const response = await readerAPI.startGeneration(project.value.id, {
      parallel_tasks: synthesisConfig.parallelTasks
    })
    
    if (response.data.success) {
      message.success('重新合成任务已启动')
      project.value.status = 'processing'
      
      // 初始化合成进度监控（重新合成也需要）
      initializeSynthesisMonitoring()
      
      // 打开进度监控抽屉
      synthesisProgressDrawer.value = true
      
      startWebSocketProgressMonitoring()
    }
  } catch (error) {
    console.error('重新启动合成失败:', error)
    message.error('重新启动合成失败')
  } finally {
    synthesisStarting.value = false
  }
}

// 刷新项目状态
const refreshProjectStatus = async () => {
  try {
    const response = await readerAPI.getProjectDetail(project.value.id)
    if (response.data.success) {
      const newStatus = response.data.data.status
      console.log('刷新后项目状态:', newStatus)
      
      project.value.status = newStatus
      
      // 同步更新进度数据状态
      if (synthesisProgressDrawer.value) {
        progressData.value.status = newStatus
        
        if (newStatus === 'paused') {
          progressData.value.current_processing = '⏸️ 合成已暂停'
        } else if (newStatus === 'processing') {
          progressData.value.current_processing = '🎵 合成进行中...'
        } else if (newStatus === 'completed') {
          progressData.value.current_processing = '✅ 合成已完成'
        }
      }
      
      message.info(`项目状态已更新为: ${getStatusText(newStatus)}`)
    }
  } catch (error) {
    console.error('刷新项目状态失败:', error)
    message.error('无法获取最新状态')
  }
}

// 查看项目详情
const viewProjectDetail = () => {
  // 已删除简化版项目详情页，直接停留在当前合成中心
message.info('已在合成中心，查看项目详情')
}

// 音频预览相关处理
const handleAudioLoadStart = () => {
  console.log('音频开始加载')
}

const handleAudioError = (error) => {
  console.error('音频加载失败:', error)
  // 只在项目状态为completed时才显示错误，避免中间状态的误报
  if (project.value?.status === 'completed') {
    message.warning('音频文件暂时不可用，可能正在后处理中，请稍后刷新或尝试下载')
  } else {
    console.log('项目尚未完成，忽略音频加载错误')
  }
}

// 检查TTS服务状态
const checkTTSService = async () => {
  checkingService.value = true
  try {
    // 使用统一的健康检查API
    const response = await systemAPI.healthCheck()
    
    if (response.data) {
      const data = response.data
      if (data.services?.tts_client?.status === 'healthy') {
        message.success('TTS服务正常运行中')
      } else {
        message.warning('TTS服务已启动但状态异常')
      }
    } else {
      throw new Error('健康检查返回数据异常')
    }
  } catch (error) {
    console.error('TTS服务检查失败:', error)
    
    if (error.message.includes('Network')) {
      message.error('无法连接到TTS服务，请检查服务是否启动')
    } else {
      message.error('TTS服务异常: ' + error.message)
    }
  } finally {
    checkingService.value = false
  }
}

// WebSocket进度监控 - 替代轮询机制
const startWebSocketProgressMonitoring = () => {
  // 先停止之前的订阅（避免重复订阅）
  if (unsubscribeWebSocket.value) {
    stopWebSocketProgressMonitoring()
  }
  
  // 确保WebSocket连接
  wsStore.connect()
  
  // 订阅合成进度更新主题
  unsubscribeWebSocket.value = wsStore.subscribe('topic_message', (data, fullMessage) => {

    
    // 检查是否为当前项目的进度更新
    if (fullMessage.topic === `synthesis_${project.value?.id}` && data.type === 'progress_update') {
      const progressDataFromWS = data.data
      console.log('📨 [WEBSOCKET] 收到进度更新:', progressDataFromWS)
      
      // 更新项目统计信息
      console.log('📊 [WEBSOCKET] 更新前的project.statistics:', project.value.statistics)
      
      // 确保statistics存在且是响应式的
      if (!project.value.statistics) {
        project.value.statistics = reactive({
          totalSegments: 0,
          completedSegments: 0,
          failedSegments: 0,
          processingSegments: 0,
          pendingSegments: 0
        })
      }
      
      // 使用Object.assign保持响应式，同时同步项目原始字段
      Object.assign(project.value.statistics, {
        totalSegments: progressDataFromWS.total_segments,
        completedSegments: progressDataFromWS.completed_segments,
        failedSegments: progressDataFromWS.failed_segments,
        processingSegments: progressDataFromWS.total_segments - progressDataFromWS.completed_segments - progressDataFromWS.failed_segments,
        pendingSegments: 0
      })
      
      // 同步更新项目原始字段，确保数据一致性
      project.value.total_segments = progressDataFromWS.total_segments
      project.value.processed_segments = progressDataFromWS.completed_segments
      project.value.status = progressDataFromWS.status
      project.value.current_segment = progressDataFromWS.current_segment || 0
      
      // 同时更新progress抽屉的数据，确保数据一致性
      updateProgressDataFromWebSocket(progressDataFromWS)
      
      console.log('📊 [WEBSOCKET] 更新后的project.statistics:', project.value.statistics)

      
      // 更新当前处理段落信息
      currentProcessingSegment.value = getCurrentProcessingSegment()
      
      // 如果有新完成的片段，加载已完成片段列表
      if (progressDataFromWS.completed_segments > (completedSegments.value.length || 0)) {
        loadCompletedSegments()
      }
      
      // 简化：统一处理完成状态
      if (['completed', 'partial_completed', 'failed', 'cancelled'].includes(progressDataFromWS.status)) {
        stopWebSocketProgressMonitoring()
        stopElapsedTimer()
        loadProject()
        
        // 简化的通知
        const { status, completed_segments, total_segments, failed_segments } = progressDataFromWS
        showSimpleNotification(status, completed_segments, total_segments, failed_segments)
        
        // 简化的抽屉关闭逻辑：失败时不关闭，其他状态2秒后关闭
        if (status !== 'failed') {
          setTimeout(() => {
            synthesisProgressDrawer.value = false
          }, 2000)
        }
      }
    }
    // 如果不是期望的消息格式，也要处理其他类型的synthesis消息
    else if (fullMessage.topic === `synthesis_${project.value?.id}`) {
      console.log('🔍 收到其他synthesis消息:', data)
      // 如果直接是进度数据（没有嵌套在data.data中）
      if (data.total_segments !== undefined && data.completed_segments !== undefined) {
        console.log('📨 直接格式的进度更新:', data)
        updateProgressDataFromWebSocket(data)
      }
    }
  })
  
  // 发送主题订阅请求
  wsStore.sendMessage('subscribe', {
    topic: `synthesis_${project.value.id}`
  })
  
  console.log('🔌 WebSocket进度监控已启动，topic:', `synthesis_${project.value.id}`)
}

const stopWebSocketProgressMonitoring = () => {
  if (unsubscribeWebSocket.value) {
    // 发送取消订阅请求
    wsStore.sendMessage('unsubscribe', {
      topic: `synthesis_${project.value.id}`
    })
    
    // 取消本地订阅
    unsubscribeWebSocket.value()
    unsubscribeWebSocket.value = null
    console.log('🔌 WebSocket进度监控已停止')
  }
}

// 加载智能准备结果
const loadPreparationResults = async () => {
  if (!project.value?.book?.id) {
    message.warning('项目未关联书籍，无法加载智能准备结果')
    return
  }
  
  if (!selectedChapter.value) {
    message.warning('请先选择要合成的章节')
    return
  }
  
  loadingResults.value = true
  try {
    // 只获取选中章节的智能准备结果
    const response = await booksAPI.getBookAnalysisResults(project.value.book.id, {
      chapter_ids: [selectedChapter.value]
    })
    
    if (response.data.success) {
      preparationResults.value = response.data
      
      // 聚合所有章节的角色数据
      const allCharacters = {}
      let totalSegments = 0
      
      response.data.data.forEach(chapterResult => {
        const synthesisJson = chapterResult.synthesis_json
        
        // 聚合角色
        if (synthesisJson.characters) {
          synthesisJson.characters.forEach(char => {
            const charName = char.name
            if (!allCharacters[charName]) {
              allCharacters[charName] = {
                name: charName,
                voice_id: char.voice_id,
                voice_name: char.voice_name,
                frequency: 0,
                samples: []
              }
            }
            allCharacters[charName].frequency += 1
            
            // 收集示例文本
            if (synthesisJson.synthesis_plan) {
              const characterSegments = synthesisJson.synthesis_plan.filter(seg => seg.speaker === charName)
              characterSegments.slice(0, 3).forEach(seg => {
                if (seg.text && !allCharacters[charName].samples.includes(seg.text.slice(0, 30))) {
                  allCharacters[charName].samples.push(seg.text.slice(0, 30) + '...')
                }
              })
            }
          })
        }
        
        // 统计段落数
        if (synthesisJson.synthesis_plan) {
          totalSegments += synthesisJson.synthesis_plan.length
        }
      })
      
      // 静默加载完成，不显示提示
      
    } else {
      message.error('加载智能准备结果失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('加载智能准备结果失败:', error)
    message.error('加载智能准备结果失败: ' + error.message)
  } finally {
    loadingResults.value = false
  }
}

// 刷新智能准备结果
const refreshPreparationResults = async () => {
  preparationResults.value = null
  await loadPreparationResults()
}

// 获取选中章节信息
const getSelectedChapterInfo = () => {
  if (!selectedChapter.value || !availableChapters.value.length) return null
  return availableChapters.value.find(chapter => chapter.id === selectedChapter.value)
}

// 触发智能准备
const triggerIntelligentPreparation = async () => {
  if (!selectedChapter.value) {
    message.warning('请先选择章节')
    return
  }
  
  loadingResults.value = true
  try {
    console.log('🎭 开始智能准备章节:', selectedChapter.value)
    
    // 调用智能准备API
    const response = await systemAPI.prepareChapterSynthesis(selectedChapter.value)
    
    if (response.data.success) {
      message.success('智能准备完成！')
      // 重新加载智能准备结果
      await loadPreparationResults()
    } else {
      message.error('智能准备失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('智能准备失败:', error)
    message.error('智能准备失败: ' + error.message)
  } finally {
    loadingResults.value = false
  }
}

// 清空智能准备结果
const clearPreparationResults = () => {
  preparationResults.value = null
  message.info('智能准备结果已清空')
}

// 获取总段落数
const getTotalSegments = () => {
  if (!preparationResults.value?.data) return 0
  
  return preparationResults.value.data.reduce((total, chapterResult) => {
    const synthesisJson = chapterResult.synthesis_json
    return total + (synthesisJson.synthesis_plan?.length || 0)
  }, 0)
}

// 获取角色样式类
const getCharacterClass = (speaker) => {
  const colors = ['primary', 'warning', 'success', 'info', 'error']
  const hash = speaker.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return `character-${colors[hash % colors.length]}`
}

// 获取章节中的角色数量
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

// 获取合成进度标题
const getSynthesisProgressTitle = () => {
  const status = progressData.value.status
  const current = progressData.value.current_processing
  const completed = progressData.value.completed_segments
  const total = progressData.value.total_segments
  
  if (current && status === 'processing') {
    // 显示当前正在合成的段落信息
    return `正在合成: ${current} (${completed}/${total})`
  }
  
  if (status === 'completed') {
    return `合成完成 - 共${total}个段落`
  }
  
  if (status === 'failed') {
    return `合成失败 - 已完成${completed}/${total}`
  }
  
  if (status === 'paused') {
    return `合成暂停 - 已完成${completed}/${total}`
  }
  
  if (total > 0) {
    return `合成监控 - ${completed}/${total}`
  }
  
  return '合成进度监控'
}

// 获取当前处理段落信息
const getCurrentProcessingSegment = () => {
  if (!preparationResults.value?.data || !project.value?.current_segment) {
    return null
  }
  
  let segmentCounter = 0
  for (const chapterResult of preparationResults.value.data) {
    const segments = chapterResult.synthesis_json?.synthesis_plan || []
    for (const segment of segments) {
      segmentCounter++
      if (segmentCounter === project.value.current_segment) {
        return segment
      }
    }
  }
  return null
}

// 加载已完成的片段
const loadCompletedSegments = async () => {
  if (!project.value?.id) return
  
  try {
    // 这里应该调用API获取已完成的片段
    // 暂时使用模拟数据
    const mockCompletedSegments = []
    for (let i = 0; i < (project.value.statistics?.completedSegments || 0); i++) {
      mockCompletedSegments.push({
        id: i + 1,
        speaker: '角色' + ((i % 3) + 1),
        text: `这是第${i + 1}个已完成的合成片段，内容会在这里显示...`,
        audio_url: `/api/v1/novel-reader/projects/${project.value.id}/segments/${i + 1}/audio`,
        duration: 3.5 + Math.random() * 2 // 模拟时长
      })
    }
    completedSegments.value = mockCompletedSegments
  } catch (error) {
    console.error('加载已完成片段失败:', error)
  }
}

// 刷新已完成片段
const refreshCompletedSegments = async () => {
  loadingCompletedSegments.value = true
  try {
    await loadCompletedSegments()
  } finally {
    loadingCompletedSegments.value = false
  }
}

// 播放片段音频
const playSegmentAudio = async (segment) => {
  if (!segment.audio_url) {
    message.warning('该段落音频文件不存在')
      return
    }
    
  try {
    await getAudioService().playSegmentAudio(
      project.value.id,
      segment.id,
      segment.text
    )
    playingSegment.value = segment.id
  } catch (error) {
    console.error('播放段落音频失败:', error)
    message.error('播放段落音频失败')
  }
}

// 格式化时长
const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

// 声音选项过滤
const filterVoiceOption = (input, option) => {
  return option.children.toLowerCase().indexOf(input.toLowerCase()) >= 0
}

// WebSocket设置 - 已移除，统一使用startWebSocketProgressMonitoring方法

// 生命周期
onMounted(() => {
  // 使用立即执行的异步函数来处理初始化
  (async () => {
    try {
      console.log('🔍 [INIT] 开始初始化SynthesisCenter...')
      
      // 逐个加载，便于调试
      console.log('🔍 [INIT] 1. 加载项目信息...')
      await loadProject()
      console.log('🔍 [INIT] 项目加载完成:', project.value?.id)
      
      console.log('🔍 [INIT] 2. 加载声音列表...')
      await loadVoices()
      console.log('🔍 [INIT] 声音列表加载完成:', availableVoices.value?.length)
      
      // 自动加载章节（因为现在固定为章节模式）
      console.log('🔍 [INIT] 3. 自动加载章节...')
      await autoLoadChapters()
      console.log('🔍 [INIT] 章节加载完成:', availableChapters.value?.length)
      
      // 如果有已完成的片段，加载它们
      if (project.value?.statistics?.completedSegments > 0) {
        console.log('🔍 [INIT] 4. 加载已完成的片段...')
        await loadCompletedSegments()
      }
      
      // 根据项目状态进行相应处理
      console.log('🔍 [INIT] 项目状态:', project.value?.status)
      
      if (project.value?.status === 'processing') {
        console.log('🔍 [INIT] 项目正在处理中，启动WebSocket监控')
        currentProcessingSegment.value = getCurrentProcessingSegment()
        
        // 自动初始化合成进度监控
        initializeSynthesisMonitoring()
        
        // 自动打开进度监控抽屉
        synthesisProgressDrawer.value = true
        
        startWebSocketProgressMonitoring()
      } else {
        // 简化的进度数据初始化
        initializeProgressFromProject()
      }
      
      console.log('✅ [INIT] SynthesisCenter初始化完成!')
    } catch (error) {
      console.error('🔴 [INIT] 初始化过程中发生错误:', error)
      console.error('🔴 [INIT] 错误堆栈:', error.stack)
      message.error('页面初始化失败: ' + error.message)
    } finally {
      // 确保loading状态被正确重置
      loading.value = false
      console.log('🔍 [INIT] Loading状态已重置为false')
    }
  })()
})

// 页面切换前的清理
onBeforeRouteLeave(() => {
  stopWebSocketProgressMonitoring()
  return true
})

// 组件卸载时的清理
onUnmounted(() => {
  stopWebSocketProgressMonitoring()
  stopElapsedTimer()
  
  // 清理音频播放器
  audioStore.cleanup()
  currentlyPlaying.value = null
  playingChapterAudio.value = null
  playingFinalAudio.value = false
  playingSegment.value = null
  
  // 清理WebSocket监听器
  if (unsubscribeWebSocket.value) {
    unsubscribeWebSocket.value()
  }
})

// 浏览器刷新/关闭前的清理
window.addEventListener('beforeunload', () => {
  stopWebSocketProgressMonitoring()
})

// 简化的进度数据初始化
const initializeProgressFromProject = () => {
  if (!project.value) return
  
  // 在章节模式下，不显示项目历史数据，而是基于当前选择
  if (synthesisMode.value === 'chapters') {
    // 如果有智能准备结果，显示当前选择的数据
    if (preparationResults.value?.data?.length > 0) {
      const totalSegments = getTotalSegments()
      progressData.value = {
        progress: 0,
        status: 'ready',
        completed_segments: 0,
        total_segments: totalSegments,
        failed_segments: 0,
        current_processing: `已准备 ${totalSegments} 个段落`
      }
    } else {
      // 没有选择或准备结果时清零
      progressData.value = {
        progress: 0,
        status: 'pending',
        completed_segments: 0,
        total_segments: 0,
        failed_segments: 0,
        current_processing: '请选择章节并进行智能准备'
      }
    }
  } else {
    // 非章节模式使用项目数据（保留原逻辑）
    const status = project.value.status || 'unknown'
    const completed = project.value.completed_segments || 0
    const total = project.value.total_segments || 0
    const failed = project.value.failed_segments || 0
    
    progressData.value = {
      progress: total > 0 ? Math.round((completed / total) * 100) : 0,
      status: status,
      completed_segments: completed,
      total_segments: total,
      failed_segments: failed,
      current_processing: getSimpleStatusText(status, completed, total, failed)
    }
  }
  
  console.log('📊 简化初始化进度数据:', progressData.value)
}

// 简化的状态文本
const getSimpleStatusText = (status, completed, total, failed) => {
  if (status === 'completed') return '合成完成'
  if (status === 'failed') return '合成失败'
  if (status === 'partial_completed') return `${completed}/${total} 完成${failed > 0 ? `, ${failed} 失败` : ''}`
  if (status === 'processing') return '合成中...'
  return `${completed}/${total}`
}

// 简化的通知显示
const showSimpleNotification = (status, completed, total, failed) => {
  if (status === 'failed') {
    // 失败时显示详细弹窗
    const errorMsg = project.value?.error_message || '未知错误'
    Modal.error({
      title: '❌ 合成失败',
      content: h('div', [
        h('p', `合成过程中发生错误，请查看详细信息：`),
        h('div', { style: 'background: #fff2f0; padding: 12px; border-radius: 6px; margin: 8px 0; border-left: 4px solid #ff4d4f;' }, [
          h('strong', '错误详情：'),
          h('br'),
          h('span', { style: 'color: #cf1322;' }, errorMsg)
        ]),
        h('p', { style: 'margin-top: 12px; color: #666;' }, '您可以：'),
        h('ul', { style: 'color: #666; margin: 0; padding-left: 20px;' }, [
          h('li', '检查失败段落详情并进行重试'),
          h('li', '查看系统日志了解具体原因'),
          h('li', '联系技术支持获取帮助')
        ])
      ]),
      width: 500,
      okText: '我知道了'
    })
  } else {
    // 其他状态使用简单通知
    const messages = {
      completed: '🎉 合成完成！',
      partial_completed: `⚠️ 合成部分完成！${completed}/${total} 成功${failed > 0 ? `, ${failed} 失败` : ''}`,
      cancelled: '⏹️ 合成已取消'
    }
    
    const types = {
      completed: 'success',
      partial_completed: failed > 0 ? 'warning' : 'success',
      cancelled: 'info'
    }
    
    message[types[status]](messages[status])
  }
}

// 合成进度监控相关方法
const initializeSynthesisMonitoring = () => {
  // 计算当前选择章节的总段落数
  const totalSegments = getTotalSegments()
  
  console.log('🔍 [INIT] 初始化合成监控，总段落数:', totalSegments)
  
  // 重置进度数据，设置正确的总段落数
  progressData.value = {
    progress: 0,
    status: 'processing',
    completed_segments: 0,
    total_segments: totalSegments,
    failed_segments: 0,
    current_processing: '正在准备合成...'
  }
  
  console.log('🔍 [INIT] 初始化后的progressData:', progressData.value)
  
  // 初始化段落状态列表
  initializeSegmentStatuses()
  
  // 记录合成开始时间
  synthesisStartTime.value = Date.now()
  
  // 启动计时器
  startElapsedTimer()
}

const initializeSegmentStatuses = () => {
  // 从智能准备结果中初始化段落状态
  if (preparationResults.value?.data) {
    const segments = []
    let segmentIndex = 1
    
    preparationResults.value.data.forEach(chapterResult => {
      if (chapterResult.synthesis_json?.synthesis_plan) {
        chapterResult.synthesis_json.synthesis_plan.forEach(segment => {
          segments.push({
            segment_id: segmentIndex++,
            text: segment.text,
            speaker: segment.speaker,
            voice_id: segment.voice_id,
            voice_name: segment.voice_name,
            status: 'pending',
            playing: false,
            retrying: false,
            error_message: null,
            completion_time: null,
            audio_url: null
          })
        })
      }
    })
    
    segmentStatuses.value = segments
    progressData.value.total_segments = segments.length
  }
}

const startElapsedTimer = () => {
  if (elapsedTimer.value) {
    clearInterval(elapsedTimer.value)
  }
  
  elapsedTimer.value = setInterval(() => {
    if (synthesisStartTime.value) {
      synthesisElapsedTime.value = Math.floor((Date.now() - synthesisStartTime.value) / 1000)
    }
  }, 1000)
}

const stopElapsedTimer = () => {
  if (elapsedTimer.value) {
    clearInterval(elapsedTimer.value)
    elapsedTimer.value = null
  }
}

// 段落状态相关方法
const getSegmentStatusColor = (status) => {
  const colors = {
    pending: 'default',
    processing: 'processing',
    completed: 'success',
    failed: 'error'
  }
  return colors[status] || 'default'
}

const getSegmentStatusText = (status) => {
  const texts = {
    pending: '等待中',
    processing: '合成中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

// 播放段落音频（智能监控版本）
const playSegmentAudioAdvanced = async (segment) => {
  if (!segment.audio_url) {
    message.warning('该段落音频尚未生成')
    return
  }
  
  // 停止其他正在播放的音频
  segmentStatuses.value.forEach(s => s.playing = false)
  
  segment.playing = true
  
  try {
    // 创建音频元素播放
    const audio = new Audio(segment.audio_url)
    
    audio.addEventListener('ended', () => {
      segment.playing = false
    })
    
    audio.addEventListener('error', () => {
      segment.playing = false
      message.error('音频播放失败')
    })
    
    await audio.play()
    
  } catch (error) {
    segment.playing = false
    console.error('播放音频失败:', error)
    message.error('播放音频失败: ' + error.message)
  }
}

// 重试单个段落
const retrySegment = async (segment) => {
  segment.retrying = true
  
  try {
    // 调用重试API
    const response = await readerAPI.retrySegment(project.value.id, segment.segment_id)
    
    if (response.data.success) {
      segment.status = 'processing'
      segment.error_message = null
      segment.retrying = false
      message.success(`段落 ${segment.segment_id} 重试已启动`)
    } else {
      throw new Error(response.data.message || '重试失败')
    }
  } catch (error) {
    console.error('重试段落失败:', error)
    message.error('重试失败: ' + error.message)
  } finally {
    segment.retrying = false
  }
}

// 重试所有失败段落
const retryAllFailedSegments = async () => {
  if (!project.value?.id) {
    message.error('项目信息不存在')
    return
  }
  
  resumingGeneration.value = true
  try {
    const response = await readerAPI.retryAllFailedSegments(project.value.id)
    
    if (response.data.success) {
      const retryCount = response.data.data.retried_segments
      if (retryCount > 0) {
        message.success(`已启动重试 ${retryCount} 个失败段落`)
        
        // 更新项目状态
        project.value.status = 'processing'
        
        // 重新初始化监控
        initializeSynthesisMonitoring()
        
        // 确保抽屉打开
        synthesisProgressDrawer.value = true
        
        // 重新启动WebSocket监控
        startWebSocketProgressMonitoring()
      } else {
        message.info('没有失败的段落需要重试')
      }
    } else {
      throw new Error(response.data.message || '重试失败')
    }
  } catch (error) {
    console.error('重试所有失败段落失败:', error)
    message.error({
      content: '重试失败: ' + error.message + '。请检查网络连接和服务状态后再次尝试。',
      duration: 8
    })
  } finally {
    resumingGeneration.value = false
  }
}

// 重试失败段落（别名方法，供抽屉使用）
const retryFailedSegments = async () => {
  await retryAllFailedSegments()
}

// 获取错误摘要信息
const getErrorSummary = () => {
  console.log('🔍 getErrorSummary 调用，当前数据:', {
    status: progressData.value.status,
    completed: progressData.value.completed_segments,
    total: progressData.value.total_segments,
    failed: progressData.value.failed_segments,
    project_error: project.value?.error_message
  })
  
  if (progressData.value.status === 'failed') {
    const errorMsg = project.value?.error_message || '未知原因导致合成失败'
    return `所有段落合成失败，原因：${errorMsg}`
  } else if (progressData.value.status === 'partial_completed') {
    const successCount = progressData.value.completed_segments || 0
    const totalCount = progressData.value.total_segments || 0
    const failedCount = progressData.value.failed_segments || 0
    
            // 🚀 修复：如果没有失败段落，不应该显示错误信息
        if (failedCount === 0) {
          // 清除项目的历史错误信息，因为当前合成已成功
          if (project.value?.error_message) {
            console.log('🚀 清除历史错误信息:', project.value.error_message)
          }
          return `${successCount}/${totalCount} 个段落成功完成`
        }
    
    const errorMsg = project.value?.error_message || `${failedCount}个段落处理失败，具体原因未知`
    return `${successCount}/${totalCount} 个段落成功，${failedCount} 个失败。原因：${errorMsg}`
  }
  return '未知错误状态'
}

// 复制错误信息
const copyErrorInfo = async () => {
  try {
    const errorInfo = {
      项目名称: project.value?.name || '未知项目',
      项目ID: project.value?.id || '未知',
      错误状态: progressData.value.status,
      完成段落: progressData.value.completed_segments,
      总段落数: progressData.value.total_segments,
      失败段落: progressData.value.failed_segments,
      错误信息: project.value?.error_message || '无详细信息',
      时间戳: new Date().toLocaleString('zh-CN')
    }
    
    const errorText = Object.entries(errorInfo)
      .map(([key, value]) => `${key}: ${value}`)
      .join('\n')
    
    await navigator.clipboard.writeText(errorText)
    message.success('错误信息已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    message.error('复制失败，请手动选择文本复制')
  }
}

// 获取正确的进度百分比
const getCorrectProgress = () => {
  // 确保失败状态显示正确的进度
  if (progressData.value.status === 'failed') {
    // 完全失败时，显示实际完成的段落比例
    if (progressData.value.total_segments > 0) {
      return Math.round((progressData.value.completed_segments / progressData.value.total_segments) * 100)
    }
    return 0
  } else if (progressData.value.status === 'partial_completed') {
    // 部分完成时，显示实际完成的段落比例
    if (progressData.value.total_segments > 0) {
      return Math.round((progressData.value.completed_segments / progressData.value.total_segments) * 100)
    }
    return 0
  }
  
  // 其他状态使用原始进度值
  return progressData.value.progress || 0
}

// 获取进度条状态
const getProgressStatus = () => {
  if (progressData.value.status === 'failed') {
    return 'exception'
  } else if (progressData.value.status === 'completed') {
    return 'success'
  } else if (progressData.value.status === 'partial_completed') {
    return 'exception' // 部分完成也显示为异常状态
  }
  return 'active'
}

// 获取进度条颜色
const getProgressColor = () => {
  if (progressData.value.status === 'completed') {
    return '#52c41a' // 绿色
  } else if (progressData.value.status === 'failed') {
    return '#ff4d4f' // 红色
  } else if (progressData.value.status === 'partial_completed') {
    return '#faad14' // 橙色
  }
  return '#1890ff' // 蓝色（进行中）
}

// 注释：downloadFinalAudio函数已在上面定义，这里删除重复定义

// 下载部分音频（已完成的部分）
const downloadPartialAudio = async () => {
  try {
    const response = await readerAPI.downloadPartialAudio(project.value.id)
    
    // 处理文件下载
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value.name}_partial.wav`
    link.click()
    window.URL.revokeObjectURL(url)
    
    message.success('已完成部分音频下载成功')
  } catch (error) {
    console.error('下载部分音频失败:', error)
    message.error('下载失败: ' + error.message)
  }
}



// 时间格式化
const formatTime = (timestamp) => {
  if (!timestamp) return ''
  
  const date = new Date(timestamp)
  return date.toLocaleTimeString('zh-CN', {
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit'
  })
}

// 更新进度数据从WebSocket推送
const updateProgressDataFromWebSocket = (data) => {
  console.log('🔍 [WEBSOCKET] updateProgressDataFromWebSocket收到数据:', data)
  
  // 计算进度百分比 - 针对失败状态进行特殊处理
  let finalProgress = 0
  let finalCompletedSegments = data.completed_segments || 0
  
  // 🚨 失败状态特殊处理：进度应该基于实际完成的段落，不能是100%
  if (data.status === 'failed') {
    // 完全失败时，进度应该是0（除非有部分段落成功）
    if (data.total_segments > 0 && finalCompletedSegments > 0) {
      finalProgress = Math.round((finalCompletedSegments / data.total_segments) * 100)
    } else {
      finalProgress = 0
    }
    console.log('🚨 [WEBSOCKET] 失败状态修正：progress =', finalProgress)
  } else if (data.status === 'partial_completed') {
    // 部分完成时，进度基于实际完成的段落数
    if (data.total_segments > 0) {
      finalProgress = Math.round((finalCompletedSegments / data.total_segments) * 100)
    }
    console.log('⚠️ [WEBSOCKET] 部分完成状态修正：progress =', finalProgress)
  } else if (data.progress !== undefined && data.progress !== null && data.status !== 'failed') {
    // 其他状态优先使用后端传来的进度值（但排除失败状态）
    finalProgress = Math.round(data.progress)
    
    // 数据一致性检查：如果进度不为0但完成段落为0，估算完成段落数
    if (finalProgress > 0 && finalCompletedSegments === 0 && data.total_segments > 0) {
      finalCompletedSegments = Math.floor((finalProgress / 100) * data.total_segments)
      console.warn('⚠️ [WEBSOCKET] 数据修正：进度', finalProgress, '% 但完成段落为0，估算完成段落数:', finalCompletedSegments)
    }
  } else if (data.total_segments > 0) {
    // 备选：根据完成段落数计算
    finalProgress = Math.round((finalCompletedSegments / data.total_segments) * 100)
  }
  
  console.log('🔍 [WEBSOCKET] 进度计算:', {
    completed: data.completed_segments,
    total: data.total_segments,
    backendProgress: data.progress,
    calculatedProgress: data.total_segments > 0 ? Math.round((finalCompletedSegments / data.total_segments) * 100) : 0,
    finalProgress: finalProgress,
    finalCompletedSegments: finalCompletedSegments
  })
  
  // 更新总体进度数据 - 使用修正后的数据
  const newProgressData = {
    progress: finalProgress,
    status: data.status,
    completed_segments: finalCompletedSegments,
    total_segments: data.total_segments || 0,
    failed_segments: data.failed_segments || 0,
    current_processing: data.current_processing || `正在处理第 ${data.current_segment || 1} 段`
  }
  
  // 强制更新响应式数据
  progressData.value = { ...newProgressData }
  
  console.log('🔍 [WEBSOCKET] updateProgressDataFromWebSocket更新后progressData:', progressData.value)
  
  // 手动触发视图更新（如果需要）
  nextTick(() => {
    console.log('🔍 [WEBSOCKET] 视图更新后的progressData:', progressData.value)
  })
  
  // 更新段落状态
  if (data.segments_status) {
    data.segments_status.forEach(segmentStatus => {
      const segment = segmentStatuses.value.find(s => s.segment_id === segmentStatus.segment_id)
      if (segment) {
        segment.status = segmentStatus.status
        segment.error_message = segmentStatus.error_message
        segment.completion_time = segmentStatus.completion_time
        segment.audio_url = segmentStatus.audio_url
      }
    })
  }
  
  // 如果合成完成或失败，停止计时器
  if (data.status === 'completed' || data.status === 'failed') {
    stopElapsedTimer()
  }
}

// 章节级别合成方法
const startChapterSynthesis = async (chapterId, enableEnvironment = false) => {
  try {
    synthesisStarting.value = true
    
    console.log('开始合成章节:', chapterId, '环境音:', enableEnvironment)
    
    // 准备请求参数
    const requestParams = {
      parallel_tasks: synthesisConfig.parallelTasks,
      enable_environment: enableEnvironment,
      environment_volume: enableEnvironment ? synthesisConfig.environmentVolume : undefined
    }
    
    // 调用单章节合成API
    const response = await readerAPI.startChapterSynthesis(project.value.id, chapterId, requestParams)
    
    if (response.data.success) {
      const mode = enableEnvironment ? '环境音混合' : 'TTS语音'
      message.success(`章节${mode}合成已开始！`)
      project.value.status = 'processing'
      
      // 开始WebSocket监控
      startWebSocketProgressMonitoring()
      startElapsedTimer()
      
      // 显示进度抽屉
      synthesisProgressDrawer.value = true
    } else {
      message.error('启动章节合成失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('启动章节合成失败:', error)
    message.error('启动章节合成失败: ' + (error.response?.data?.message || error.message))
  } finally {
    synthesisStarting.value = false
  }
}

// 显示环境音配置弹窗
const showEnvironmentConfigModal = (chapterId) => {
  selectedChapterForEnvironment.value = chapterId
  environmentConfigModal.value = true
}

// 开始环境音合成
const startEnvironmentSynthesis = async () => {
  if (!selectedChapterForEnvironment.value) {
    message.error('未选择章节')
    return
  }
  
  environmentConfigModal.value = false
  await startChapterSynthesis(selectedChapterForEnvironment.value, true)
  selectedChapterForEnvironment.value = null
}

const restartChapterSynthesis = async (chapterId) => {
  try {
    synthesisStarting.value = true
    
    console.log('重新合成章节:', chapterId)
    
    // 调用单章节重新合成API
    const response = await readerAPI.restartChapterSynthesis(project.value.id, chapterId)
    
    if (response.data.success) {
      message.success('章节重新合成已开始！')
      project.value.status = 'processing'
      
      // 开始WebSocket监控
      startWebSocketProgressMonitoring()
      startElapsedTimer()
      
      // 显示进度抽屉
      synthesisProgressDrawer.value = true
    } else {
      message.error('重新合成章节失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('重新合成章节失败:', error)
    message.error('重新合成章节失败: ' + (error.response?.data?.message || error.message))
  } finally {
    synthesisStarting.value = false
  }
}

const resumeChapterSynthesis = async (chapterId) => {
  try {
    resumingGeneration.value = true
    
    console.log('继续合成章节:', chapterId)
    
    // 调用单章节继续合成API
    const response = await readerAPI.resumeChapterSynthesis(project.value.id, chapterId)
    
    if (response.data.success) {
      message.success('章节合成已继续！')
      project.value.status = 'processing'
      
      // 开始WebSocket监控
      startWebSocketProgressMonitoring()
      startElapsedTimer()
      
      // 显示进度抽屉
      synthesisProgressDrawer.value = true
    } else {
      message.error('继续合成章节失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('继续合成章节失败:', error)
    message.error('继续合成章节失败: ' + (error.response?.data?.message || error.message))
  } finally {
    resumingGeneration.value = false
  }
}

const retryChapterFailedSegments = async (chapterId) => {
  try {
    resumingGeneration.value = true
    
    console.log('重试章节失败段落:', chapterId)
    
    // 调用单章节重试失败段落API
    const response = await readerAPI.retryChapterFailedSegments(project.value.id, chapterId)
    
    if (response.data.success) {
      // 检查是否真的有失败段落需要重试
      if (response.data.message.includes('没有失败的段落需要重试')) {
        message.info('该章节所有段落已完成，无需重试')
        return
      }
      
      // 有失败段落需要重试的情况
      message.success('章节失败段落重试已开始！')
      project.value.status = 'processing'
      
      // 开始WebSocket监控
      startWebSocketProgressMonitoring()
      startElapsedTimer()
      
      // 显示进度抽屉
      synthesisProgressDrawer.value = true
    } else {
      message.error({
        content: '重试章节失败段落失败: ' + response.data.message + '。请检查章节状态和声音配置。',
        duration: 8
      })
    }
  } catch (error) {
    console.error('重试章节失败段落失败:', error)
    message.error({
      content: '重试章节失败段落失败: ' + (error.response?.data?.message || error.message) + '。请检查网络连接和服务状态。',
      duration: 8
    })
  } finally {
    resumingGeneration.value = false
  }
}

const downloadChapterAudio = async (chapterId) => {
  try {
    console.log('下载章节音频:', chapterId)
    
    // 调用单章节音频下载API
    const response = await readerAPI.downloadChapterAudio(project.value.id, chapterId)
    
    // 创建下载链接
    const blob = new Blob([response.data])
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // 找到对应的章节信息来设置文件名
    const chapterResult = preparationResults.value?.data?.find(ch => ch.chapter_id === chapterId)
    const fileName = chapterResult 
      ? `第${chapterResult.chapter_number}章_${chapterResult.chapter_title}.wav`
      : `章节${chapterId}.wav`
    
    link.download = fileName
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success('章节音频下载完成')
  } catch (error) {
    console.error('下载章节音频失败:', error)
    message.error('下载章节音频失败: ' + (error.response?.data?.message || error.message))
  }
}

// 章节选择相关计算属性
const getSelectedChapterNumber = () => {
  if (!selectedChapter.value) return ''
  const chapter = availableChapters.value.find(ch => ch.id === selectedChapter.value)
  return chapter ? chapter.chapter_number : ''
}


</script>

<style scoped>
/* 新的合成中心样式 */
.synthesis-center {
  height: 100vh;
  display: flex;
  align-items: center;
}

/* 主布局 */
.synthesis-layout {
  flex: 1;
  display: flex;
  height: calc(100vh - 64px);
}

/* 左侧面板 */
.left-panel {
  width: 350px;
  background: white;
  border-right: 1px solid #e8e8e8;
  display: flex;
  flex-direction: column;
}

.panel-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.header-with-back {
  display: flex;
  align-items: flex-start;
  gap: 12px;
}

.back-btn {
  flex-shrink: 0;
  margin-top: 2px;
  padding: 4px;
  border-radius: 6px;
  transition: all 0.2s;
}

.back-btn:hover {
  background: #f0f6ff;
  color: #1890ff;
}

.project-info {
  flex: 1;
  min-width: 0;
}

.project-info h3 {
  margin: 0 0 6px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.4;
}

.project-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
}

.project-subtitle {
  font-size: 12px;
  color: #666;
}

.status-tag {
  font-size: 11px;
}

.panel-header h3 {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.chapter-selection-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.chapter-controls {
  padding: 12px 24px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fafafa;
}

.selection-count {
  font-size: 12px;
  color: #666;
}

.chapters-list {
  flex: 1;
  overflow-y: auto;
}

.loading-state {
  padding: 40px 24px;
  text-align: center;
}

.chapters-container {
  padding: 8px;
}

.chapter-menu-item {
  padding: 12px 16px;
  margin-bottom: 8px;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e8e8e8;
  background: #fafafa;
}

.chapter-menu-item:hover {
  background: #f0f6ff;
  border-color: #91caff;
  transform: translateY(-1px);
}

.chapter-menu-item.active {
  background: #e6f4ff;
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.chapter-menu-item.active .chapter-title {
  color: #1890ff;
  font-weight: 600;
}

.chapter-radio {
  flex-shrink: 0;
  padding-top: 2px;
}

.chapter-info {
  flex: 1;
  min-width: 0;
}

.chapter-title {
  font-size: 14px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.4;
  margin-bottom: 4px;
}

.chapter-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}

.word-count {
  color: #666;
}

.chapter-status {
  padding: 2px 6px;
  border-radius: 3px;
  font-size: 11px;
}

.empty-chapters {
  padding: 40px 24px;
  text-align: center;
}

.text-project-hint {
  padding: 24px;
}

/* 右侧面板 */
.right-panel {
  flex: 1;
  display: flex;
  flex-direction: column;
  background: #fafbfc;
}

/* 内容标题栏 */
.content-header {
  background: white;
  border-bottom: 1px solid #e8e8e8;
  padding: 16px 24px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  min-height: 64px;
}

.content-title {
  display: flex;
  align-items: center;
  justify-content: space-between;
  width: 100%;
}

.title-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.title-stats {
  display: flex;
  align-items: center;
}

.content-title h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.content-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.start-btn,
.restart-btn {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3);
}

.start-btn:hover,
.restart-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.play-btn {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  border: none;
  box-shadow: 0 2px 8px rgba(82, 196, 26, 0.3);
  color: white;
}

.play-btn:hover {
  transform: translateY(-1px);
  box-shadow: 0 4px 12px rgba(82, 196, 26, 0.4);
}

/* 内容预览区域 */
.content-preview {
  flex: 1;
  overflow-y: auto;
  padding: 24px;
}

/* 统计卡片 */
.stats-card {
  background: white;
  border-radius: 12px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

.stats-row {
  display: flex;
  justify-content: space-around;
}

.stat-item {
  text-align: center;
}

.stat-number {
  display: block;
  font-size: 24px;
  font-weight: 700;
  color: #1890ff;
  line-height: 1.2;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #666;
  margin-top: 4px;
}

/* 准备结果预览 */
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

.preview-header {
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fafafa;
}

.preview-header {
  justify-content: flex-end;
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

.chapter-divider:first-child {
  margin-top: 0;
}

.dialogue-bubbles {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.dialogue-bubble {
  padding: 12px 16px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  transition: all 0.2s;
}

.dialogue-bubble:hover {
  background: #f1f5f9;
  border-color: #cbd5e1;
}

.dialogue-bubble.narrator {
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-color: #0ea5e9;
}

.dialogue-bubble.character {
  background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
  border-color: #f59e0b;
}

.bubble-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 6px;
}

.speaker-name {
  font-size: 13px;
  font-weight: 600;
  color: #1f2937;
}

.segment-index {
  font-size: 11px;
  color: #666;
  background: #f1f5f9;
  padding: 2px 6px;
  border-radius: 10px;
}

.bubble-content {
  font-size: 14px;
  color: #374151;
  line-height: 1.5;
}

.show-more {
  margin-top: 16px;
}

/* 空状态 */
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
}

/* 进度抽屉样式 */
.progress-container {
  padding: 16px 24px;
}

/* 简化的进度显示 */
.simple-progress {
  .progress-title-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.websocket-status {
  display: flex;
  align-items: center;
}
  
  .progress-title {
    font-size: 16px;
    font-weight: 500;
    color: #1f2937;
  }
  
  .synthesis-controls {
    flex-shrink: 0;
  }
  
  .compact-stats {
    display: flex;
    gap: 24px;
    margin-top: 12px;
    font-size: 13px;
    
    .stat-item {
      display: flex;
      align-items: center;
      gap: 4px;
    }
    
    .stat-label {
      color: #666;
      font-weight: 500;
    }
    
    .stat-value {
      font-weight: 600;
      
      &.completed {
        color: #52c41a;
      }
      
      &.total {
        color: #1890ff;
      }
      
      &.failed {
        color: #ff4d4f;
      }
      
      &.time {
        color: #1890ff;
      }
    }
    
    .stat-separator {
      color: #d9d9d9;
      font-weight: 400;
    }
  }
  
  .current-status {
    margin-top: 12px;
    
    .status-text {
      font-size: 12px;
      color: #1890ff;
      background: #f0f7ff;
      padding: 4px 8px;
      border-radius: 4px;
      border-left: 3px solid #1890ff;
    }
  }
}

.overall-progress h3 {
  margin-bottom: 16px;
  font-size: 18px;
  color: #1f2937;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 16px;
}

.current-status {
  margin-bottom: 24px;
}

/* 合成进度监控抽屉样式 */
.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.synthesis-controls {
  display: flex;
  gap: 8px;
}

.completion-section {
  margin-top: 24px;
}

.completion-controls {
  display: flex;
  justify-content: center;
  margin-top: 16px;
}

.segments-detail {
  margin-top: 16px;
}

.segments-summary {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

/* 响应式调整 */
@media (max-width: 1200px) {
  .left-panel {
    width: 300px;
  }
}

@media (max-width: 768px) {
  .synthesis-layout {
    flex-direction: column;
  }
  
  .left-panel {
    width: 100%;
    height: 300px;
  }
  
  .content-header {
    flex-direction: column;
    gap: 12px;
    align-items: stretch;
  }
}

/* 章节选择样式 */
.chapter-selection-card {
  margin-bottom: 16px;
}

.chapter-selection-content {
  .selection-mode {
    margin-bottom: 16px;
  }
  
  .chapter-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px;
    background: #fafafa;
    border-radius: 6px;
  }
  
  .selection-info {
    color: #666;
    font-size: 14px;
  }
  
  .chapters-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 12px;
    max-height: 400px;
    overflow-y: auto;
  }
  
  .chapter-item {
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    padding: 12px;
    cursor: pointer;
    transition: all 0.3s;
    background: white;
    
    &:hover {
      border-color: #1890ff;
      box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
    }
    
    &.selected {
      border-color: #1890ff;
      background: #f6ffed;
    }
  }
  
  .chapter-content {
    .chapter-title {
      font-weight: 500;
      margin-bottom: 8px;
      color: #333;
      line-height: 1.4;
    }
    
    .chapter-meta {
      display: flex;
      justify-content: space-between;
      align-items: center;
      font-size: 12px;
      color: #999;
      
      .chapter-status {
        padding: 2px 6px;
        border-radius: 4px;
        font-size: 11px;
        
        &.status-pending {
          background: #fff7e6;
          color: #fa8c16;
        }
        
        &.status-processing {
          background: #e6f7ff;
          color: #1890ff;
        }
        
        &.status-completed {
          background: #f6ffed;
          color: #52c41a;
        }
        
        &.status-failed {
          background: #fff2f0;
          color: #ff4d4f;
        }
        
        &.status-ready {
          background: #f0f5ff;
          color: #2f54eb;
        }
      }
    }
  }
  
  .loading-chapters {
    text-align: center;
    padding: 40px;
  }
  
  .no-chapters {
    text-align: center;
    padding: 40px;
    color: #999;
  }
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding: 24px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.header-content h1 {
  margin: 0;
  color: #1f2937;
  font-size: 24px;
}

.header-content p {
  margin: 8px 0 0 0;
  color: #6b7280;
}

.loading-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 400px;
}

.synthesis-content {
  margin-bottom: 24px;
}

.info-card, .analysis-card, .control-card, .progress-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.analysis-card {
  border: 2px solid #1890ff;
  background: #f8fffe;
}

.debug-controls {
  margin-bottom: 16px;
}

.synthesis-controls {
  padding: 8px 0;
}

.action-buttons {
  margin-top: 24px;
}

.synthesis-controls {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.status-hint {
  margin-top: 16px;
}

.progress-content {
  padding: 8px 0;
}

.progress-overview {
  margin-bottom: 16px;
}

.progress-stats {
  display: flex;
  justify-content: space-between;
  margin-top: 12px;
}

.stat-item {
  text-align: center;
}

.stat-value {
  display: block;
  font-size: 18px;
  font-weight: 600;
  color: #1f2937;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.download-section {
  margin-top: 16px;
}

.error-content {
  text-align: center;
  padding: 60px 0;
}

/* 合成完成区域样式 */
.completion-section {
  margin-top: 20px;
  padding-top: 20px;
  border-top: 1px solid #e5e7eb;
}

.audio-preview {
  margin-bottom: 20px;
  padding: 16px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.preview-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.preview-header h4 {
  margin: 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.audio-info {
  font-size: 12px;
  color: #6b7280;
  background: #e2e8f0;
  padding: 4px 8px;
  border-radius: 4px;
}

.audio-player-container {
  margin-top: 12px;
}

.audio-player-container audio {
  border-radius: 6px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.download-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 环境音配置弹窗样式 */
.environment-config-content {
  .config-section {
    margin-bottom: 24px;
    
    h4 {
      margin: 0 0 12px 0;
      font-size: 16px;
      font-weight: 600;
      color: #1f2937;
    }
    
    .config-description {
      margin-bottom: 16px;
      color: #6b7280;
      line-height: 1.6;
      background: #f8fafc;
      padding: 12px;
      border-radius: 6px;
      border-left: 3px solid #1890ff;
    }
    
    .config-item {
      margin-bottom: 16px;
      
      .config-label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
        color: #374151;
      }
      
      .volume-hint {
        text-align: center;
        font-size: 13px;
        color: #1890ff;
        font-weight: 600;
        margin-top: 8px;
      }
    }
    
    .environment-examples {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
      
      .ant-tag {
        margin: 0;
        padding: 4px 8px;
        border-radius: 4px;
        font-size: 12px;
      }
    }
    
    .examples-note {
      font-size: 12px;
      color: #6b7280;
      margin: 0;
      font-style: italic;
    }
    
    .warning-list {
      margin: 0;
      padding-left: 16px;
      color: #6b7280;
      
      li {
        margin-bottom: 6px;
        line-height: 1.5;
        font-size: 13px;
      }
    }
  }
}

/* 响应式设计 */
@media (max-width: 768px) {
  .synthesis-center-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .progress-stats {
    flex-direction: column;
    gap: 12px;
  }
  
  .preview-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .environment-config-content {
    .environment-examples {
      gap: 4px;
      
      .ant-tag {
        font-size: 11px;
        padding: 2px 6px;
      }
    }
  }
}

/* 智能准备结果样式 */
.preparation-results {
  margin-top: 16px;
}

.synthesis-segments-preview {
  margin-top: 16px;
}

.segments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.segments-header h4 {
  margin: 0;
  color: #1f2937;
  font-size: 16px;
  font-weight: 600;
}

.segments-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.chapter-segments {
  padding: 12px;
  background: #f8fafc;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}

.chapter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.chapter-header h5 {
  margin: 0;
  color: #1f2937;
  font-size: 14px;
  font-weight: 600;
}

.segments-container {
  margin-top: 8px;
}

.segment-item {
  display: flex;
  align-items: center;
  margin-bottom: 4px;
}

.segment-meta {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.segment-number {
  font-size: 12px;
  color: #64748b;
}

.segment-speaker {
  font-size: 12px;
  color: #1f2937;
  font-weight: 600;
}

.show-more {
  margin-top: 8px;
}

/* JSON测试弹窗样式 */
.json-test-modal {
  max-height: 600px;
  overflow-y: auto;
}

.json-test-modal .ant-textarea {
  font-size: 12px;
  line-height: 1.4;
  border-radius: 6px;
  border: 2px dashed #d9d9d9;
  transition: border-color 0.3s ease;
}

.json-test-modal .ant-textarea:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.validation-result {
  margin-top: 12px;
}

/* 角色样式类 */
.character-primary .segment-speaker {
  color: #1890ff !important;
}

.character-warning .segment-speaker {
  color: #fa8c16 !important;
}

.character-success .segment-speaker {
  color: #52c41a !important;
}

.character-info .segment-speaker {
  color: #13c2c2 !important;
}

.character-error .segment-speaker {
  color: #f5222d !important;
}

/* 当前处理段落样式 */
.current-segment {
  margin: 16px 0;
  padding: 16px;
  background: linear-gradient(135deg, #e6f7ff 0%, #f0f9ff 100%);
  border: 1px solid #91d5ff;
  border-radius: 8px;
  box-shadow: 0 2px 4px rgba(24, 144, 255, 0.1);
}

.current-segment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.current-segment-header h4 {
  margin: 0;
  color: #1890ff;
  font-size: 16px;
  font-weight: 600;
}

.current-segment-content {
  .segment-info {
    display: flex;
    gap: 12px;
    margin-bottom: 8px;
  }
  
  .segment-speaker {
    font-weight: 600;
    color: #1890ff;
    font-size: 14px;
  }
  
  .segment-position {
    color: #666;
    font-size: 12px;
  }
  
  .segment-text {
    color: #374151;
    line-height: 1.6;
    padding: 8px 12px;
    background: white;
    border-radius: 6px;
    border: 1px solid #e8f4f8;
  }
}

/* 已完成片段样式 */
.completed-segments {
  margin: 16px 0;
  padding: 16px;
  background: #f6ffed;
  border: 1px solid #b7eb8f;
  border-radius: 8px;
}

.completed-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.completed-header h4 {
  margin: 0;
  color: #52c41a;
  font-size: 16px;
  font-weight: 600;
}

.completed-list {
  .completed-item {
    margin-bottom: 8px;
    padding: 8px 12px;
    background: white;
    border: 1px solid #e8f5e8;
    border-radius: 6px;
    transition: all 0.2s ease;
    
    &:hover {
      border-color: #b7eb8f;
      box-shadow: 0 2px 4px rgba(82, 196, 26, 0.1);
    }
  }
  
  .segment-meta {
    display: flex;
    gap: 8px;
    align-items: center;
    margin-bottom: 4px;
    font-size: 12px;
  }
  
  .segment-number {
    background: #52c41a;
    color: white;
    padding: 2px 6px;
    border-radius: 4px;
    font-weight: 600;
    min-width: 24px;
    text-align: center;
  }
  
  .segment-speaker {
    color: #1890ff;
    font-weight: 600;
  }
  
  .segment-duration {
    color: #666;
    margin-left: auto;
  }
  
  .segment-content {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }
  
  .segment-text {
    flex: 1;
    color: #374151;
    line-height: 1.4;
    font-size: 13px;
  }
  
  .segment-controls {
    flex-shrink: 0;
  }
  
  .show-all-completed {
    margin-top: 8px;
    text-align: center;
  }
}

/* 合成进度监控抽屉样式 */
.synthesis-progress-drawer {
  .progress-container {
    padding: 24px;
  }

  .overall-progress {
    margin-bottom: 24px;
  }

  .overall-progress h3 {
  margin-bottom: 16px;
    font-size: 18px;
    color: #1f2937;
  }

  .synthesis-controls-panel {
    margin: 20px 0;
    
    .ant-card {
      border: 1px solid #e8f4fd;
      border-radius: 8px;
      box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
    }
    
    .ant-card-head {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      color: white;
      border-radius: 8px 8px 0 0;
      
      .ant-card-head-title {
        color: white;
        font-weight: 600;
      }
    }
    
    .ant-space {
      width: 100%;
      justify-content: center;
    }
    
    .control-hint {
      text-align: center;
      background: #f6f8fa;
      padding: 8px 12px;
      border-radius: 4px;
      border-left: 3px solid #1890ff;
    }
  }

  .progress-stats {
    display: flex;
    justify-content: space-between;
    margin-top: 16px;
  }

  .stat-item {
    text-align: center;
  }

  .stat-value {
    display: block;
    font-size: 16px;
  font-weight: 600;
  color: #1f2937;
  }

  .stat-label {
    display: block;
    font-size: 12px;
    color: #6b7280;
    margin-top: 4px;
  }

  .current-status {
    margin-bottom: 24px;
  }

  .current-status .ant-alert {
    padding: 8px 16px;
  }

  .current-alert {
    margin-bottom: 16px;
  }

  .segments-list {
    margin-bottom: 24px;
  }

  .segments-list h4 {
    margin-bottom: 16px;
    font-size: 16px;
    color: #1f2937;
  }

  .segments-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .segment-item {
    width: 100%;
    padding: 16px;
    background: #fff;
    border: 1px solid #e8e8e8;
    border-radius: 8px;
    transition: all 0.3s;

    &:hover {
      border-color: #1890ff;
      box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
    }

    .segment-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 8px;
    }

    .segment-id {
      font-size: 12px;
      color: #64748b;
    }

    .segment-speaker {
      font-size: 12px;
      color: #1f2937;
      font-weight: 600;
    }

    .status-tag {
      padding: 4px 8px;
      border-radius: 4px;
      font-size: 11px;
    }

    .segment-content {
      .segment-text {
        color: #374151;
        line-height: 1.6;
        padding: 8px 12px;
        background: white;
        border-radius: 6px;
        border: 1px solid #e8f4f8;
      }

      .segment-actions {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-top: 12px;

        .ant-button {
          padding: 4px 12px;
          font-size: 12px;
          border-radius: 4px;
        }

        .success-info, .error-info, .processing-info {
          font-size: 12px;
          color: #6b7280;
        }
      }
    }
  }

  .completion-actions {
    margin-top: 24px;
    padding-top: 24px;
    border-top: 1px solid #e5e7eb;

    .ant-result {
      padding: 16px;
    }

    .ant-result-title {
      font-size: 18px;
      color: #52c41a;
    }

    .ant-result-subtitle {
      font-size: 14px;
      color: #6b7280;
    }

    .ant-result-extra {
      margin-top: 16px;
    }
  }

  .failure-actions {
    margin-top: 16px;
    padding-top: 16px;
    border-top: 1px solid #e5e7eb;

    .ant-alert {
      padding: 12px;
    }

    .ant-alert-message {
      font-size: 14px;
      color: #ff4d4f;
    }

    .ant-alert-description {
      font-size: 12px;
      color: #6b7280;
    }

    .failure-buttons {
      display: flex;
      justify-content: space-between;
      margin-top: 16px;

      .ant-button {
        padding: 8px 24px;
        font-size: 14px;
      }
    }
  }

  /* 失败详情样式 */
  .failure-details {
    margin-top: 16px;
    padding: 16px;
    background: #fef2f2;
    border: 1px solid #fecaca;
    border-radius: 8px;
  }

  .failure-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .failure-title {
    font-size: 14px;
    font-weight: 600;
    color: #dc2626;
  }

  .failure-reasons {
    margin-bottom: 12px;
  }

  .failure-reason-item {
    display: flex;
    align-items: flex-start;
    margin-bottom: 8px;
  }

  .reason-icon {
    margin-right: 8px;
    font-size: 14px;
  }

  .reason-text {
    font-size: 12px;
    color: #6b7280;
    line-height: 1.4;
  }

  .project-error {
    padding: 8px 12px;
    background: #fee2e2;
    border-radius: 4px;

    .error-info-row {
      display: flex;
      flex-wrap: wrap;
      align-items: flex-start;
      margin-bottom: 8px;
    }
  }

  .error-label {
    font-size: 12px;
    font-weight: 600;
    color: #dc2626;
    margin-right: 8px;
    min-width: 60px;
  }

  .error-message {
    font-size: 12px;
    color: #991b1b;
    flex: 1;
    word-break: break-word;
  }

  /* 持久化错误通知样式 */
  .persistent-error-notice {
    .error-notice-content {
      .error-title {
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 4px;
      }
      
      .error-summary {
        font-size: 12px;
        line-height: 1.4;
        opacity: 0.9;
      }
    }
  }
}

.persistent-success-notice {
  .success-notice-content {
    .success-title {
      font-size: 14px;
      font-weight: 600;
      margin-bottom: 4px;
    }
    
    .success-summary {
      font-size: 12px;
      line-height: 1.4;
      opacity: 0.9;
    }
  }
}
</style>