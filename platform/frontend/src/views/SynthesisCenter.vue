<template>
  <div class="synthesis-center-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>🎙️ 合成中心</h1>
        <p>配置角色声音，启动音频合成任务</p>
      </div>
      <div class="header-actions">
        <a-button @click="goBack">
          ← 返回项目
        </a-button>
      </div>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载项目信息...">
        <div style="height: 300px;"></div>
      </a-spin>
    </div>

    <div v-else-if="project" class="synthesis-content">
      <a-row :gutter="24">
        <!-- 左侧：项目信息和角色配置 -->
        <a-col :span="16">
          <!-- 项目概览 -->
          <a-card title="📋 项目概览" :bordered="false" class="info-card">
            <a-descriptions :column="2" bordered>
              <a-descriptions-item label="项目名称" :span="2">
                {{ project.name }}
              </a-descriptions-item>
              <a-descriptions-item label="关联书籍">
                {{ project.book?.title || '直接输入文本' }}
              </a-descriptions-item>
              <a-descriptions-item label="项目状态">
                <a-tag :color="getStatusColor(project.status)">
                  {{ getStatusText(project.status) }}
                </a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="总段落数">
                {{ project.statistics?.totalSegments || 0 }}
              </a-descriptions-item>
              <a-descriptions-item label="已完成">
                {{ project.statistics?.completedSegments || 0 }}
              </a-descriptions-item>
              <a-descriptions-item label="描述" :span="2">
                {{ project.description || '暂无描述' }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>

          <!-- 章节选择 -->
          <a-card title="📚 章节选择" :bordered="false" class="chapter-selection-card" style="margin-bottom: 16px;">
            <div class="chapter-selection-content">
              <div class="selection-mode">
                <a-alert
                  message="按章节合成"
                  description="为确保合成质量和系统稳定性，现在只支持按章节进行合成"
                  type="info"
                  show-icon
                  style="margin-bottom: 16px;"
                />
              </div>
              
              <div class="chapter-list">
                <div class="chapter-controls">
                  <a-space>
                    <a-checkbox 
                      :indeterminate="chapterIndeterminate" 
                      :checked="chapterCheckAll" 
                      @change="toggleAllChapters"
                    >
                      全选
                    </a-checkbox>
                    <span class="selection-info">
                      已选择 {{ selectedChapters.length }} / {{ availableChapters.length }} 章节
                    </span>
                    <a-button size="small" @click="loadChapters" :loading="loadingChapters">
                      🔄 刷新章节
                    </a-button>
                  </a-space>
                </div>
                
                <div v-if="loadingChapters" class="loading-chapters">
                  <a-spin tip="加载章节列表...">
                    <div style="height: 100px;"></div>
                  </a-spin>
                </div>
                
                <div v-else-if="availableChapters.length > 0" class="chapters-grid">
                  <div 
                    v-for="chapter in availableChapters" 
                    :key="chapter.id"
                    class="chapter-item"
                    :class="{ 'selected': selectedChapters.includes(chapter.id) }"
                    @click="toggleChapterSelection(chapter.id)"
                  >
                    <a-checkbox 
                      :checked="selectedChapters.includes(chapter.id)"
                      @click.stop="toggleChapterSelection(chapter.id)"
                    >
                      <div class="chapter-content">
                        <div class="chapter-title">
                          第{{ chapter.chapter_number }}章 {{ chapter.title || chapter.chapter_title || '未命名章节' }}
                        </div>
                        <div class="chapter-meta">
                          <span>字数: {{ formatNumber(chapter.word_count || 0) }}</span>
                          <span class="chapter-status" :class="getChapterStatusClass(chapter)">
                            {{ getChapterStatusText(chapter) }}
                          </span>
                        </div>
                      </div>
                    </a-checkbox>
                  </div>
                </div>
                
                <div v-else class="no-chapters">
                  <a-empty description="暂无章节数据">
                    <a-button type="primary" @click="loadChapters">
                      重新加载
                    </a-button>
                  </a-empty>
                </div>
              </div>
            </div>
          </a-card>

          <!-- 智能准备结果 -->
          <a-card title="📋 智能准备结果" :bordered="false" class="analysis-card" style="margin-bottom: 16px;">
            <div class="preparation-controls">
              <a-space>
                <a-button 
                  type="primary" 
                  @click="loadPreparationResults"
                  :loading="loadingResults"
                >
                  📥 加载智能准备结果
                </a-button>
                <a-button 
                  v-if="preparationResults"
                  @click="refreshPreparationResults"
                  :loading="loadingResults"
                >
                  🔄 刷新结果
                </a-button>
                <a-button 
                  v-if="preparationResults"
                  @click="clearPreparationResults"
                  type="dashed"
                >
                  🗑️ 清空结果
                </a-button>
                <a-button 
                  type="dashed"
                  @click="showJsonTestModal"
                  :disabled="loadingResults"
                >
                  🧪 测试JSON
                </a-button>
              </a-space>
            </div>
            
            <!-- 智能准备结果显示 -->
            <div v-if="preparationResults" class="preparation-results">
              <a-alert
                :message="`已加载 ${preparationResults.book_info?.analyzed_chapters || 0} 个章节的智能准备结果`"
                :description="`书籍: ${preparationResults.book_info?.title} | 总角色: ${detectedCharacters.length} 个 | 总段落: ${getTotalSegments()} 个`"
                type="success"
                show-icon
                style="margin: 16px 0;"
              />
              
              <!-- 合成片段预览 -->
              <div class="synthesis-segments-preview">
                <div class="segments-header">
                  <h4>📝 要合成的片段内容</h4>
                  <a-tag color="blue">共 {{ getTotalSegments() }} 个段落</a-tag>
                </div>
                
                <div class="segments-list">
                  <div v-for="(chapterResult, chapterIndex) in preparationResults.data" :key="chapterIndex" class="chapter-segments">
                    <div class="chapter-header">
                      <h5>第{{ chapterResult.chapter_number }}章 {{ chapterResult.chapter_title }}</h5>
                      <a-tag>{{ chapterResult.synthesis_json?.synthesis_plan?.length || 0 }} 个段落</a-tag>
                    </div>
                    
                    <div class="segments-container">
                      <div 
                        v-for="(segment, segmentIndex) in (chapterResult.synthesis_json?.synthesis_plan || []).slice(0, showAllSegments ? undefined : 10)" 
                        :key="segmentIndex"
                        class="segment-item"
                      >
                        <div class="segment-meta">
                          <span class="segment-number">{{ segmentIndex + 1 }}</span>
                          <span class="segment-speaker" :class="getCharacterClass(segment.speaker)">
                            {{ segment.speaker }}
                          </span>
                        </div>
                        <div class="segment-text">{{ segment.text }}</div>
                      </div>
                      
                      <div v-if="!showAllSegments && (chapterResult.synthesis_json?.synthesis_plan?.length || 0) > 10" class="show-more">
                        <a-button type="link" @click="showAllSegments = true">
                          显示全部 {{ chapterResult.synthesis_json?.synthesis_plan?.length }} 个段落
                        </a-button>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            

          </a-card>

        </a-col>

        <!-- 右侧：合成控制和进度 -->
        <a-col :span="8">
          <!-- 合成控制 -->
          <a-card title="🚀 合成控制" :bordered="false" class="control-card">
            <div class="synthesis-controls">
              <!-- 合成配置 -->
              <a-form layout="vertical">
                <a-form-item label="音质设置">
                  <a-radio-group v-model:value="synthesisConfig.quality" size="small">
                    <a-radio-button value="standard">标准</a-radio-button>
                    <a-radio-button value="high">高质量</a-radio-button>
                  </a-radio-group>
                </a-form-item>
              </a-form>

              <!-- 操作按钮 -->
              <div class="action-buttons">
                <!-- 开始合成按钮 - 只在未开始时显示 -->
                <a-button
                  v-if="project.status === 'pending' || project.status === 'failed' || project.status === 'configured'"
                  type="primary"
                  size="large"
                  block
                  :disabled="!canStartSynthesis"
                  :loading="synthesisStarting"
                  @click="startSynthesis"
                >
                  🎯 开始合成
                </a-button>

                <!-- 重新合成按钮 - 完成时显示 -->
                <a-button
                  v-if="project.status === 'completed'"
                  type="primary"
                  size="large"
                  block
                  @click="restartSynthesis"
                  :loading="synthesisStarting"
                >
                  🔄 重新合成
                </a-button>

                <!-- 合成控制按钮组 - 处理中时显示 -->
                <div v-if="project.status === 'processing'" class="synthesis-controls">
                <a-button
                  size="large"
                  block
                  @click="pauseSynthesis"
                    :loading="pausingGeneration"
                >
                  ⏸️ 暂停合成
                </a-button>
                  <a-button
                    danger
                    size="large"
                    block
                    @click="cancelSynthesis"
                    :loading="cancelingGeneration"
                    style="margin-top: 8px;"
                  >
                    ⏹️ 取消合成
                  </a-button>
                </div>

                <!-- 继续合成按钮 - 只在暂停时显示 -->
                <a-button
                  v-if="project.status === 'paused'"
                  type="primary"
                  size="large"
                  block
                  @click="resumeSynthesis"
                  :loading="resumingGeneration"
                  style="margin-top: 8px;"
                >
                  ▶️ 继续合成
                </a-button>

                <!-- TTS服务恢复按钮 -->
                <a-button
                  type="dashed"
                  size="small"
                  @click="checkTTSService"
                  style="margin-top: 8px;"
                  :loading="checkingService"
                >
                  🔧 检查TTS服务
                </a-button>

                <!-- 手动停止轮询按钮 -->
                <a-button
                  v-if="progressTimer"
                  danger
                  size="small"
                  @click="stopProgressPolling"
                  style="margin-top: 8px;"
                >
                  ⏹️ 停止监控
                </a-button>
              </div>

              <!-- 状态提示 -->
              <div v-if="!canStartSynthesis" class="status-hint">
                <a-alert
                  :message="getStartHint()"
                  type="warning"
                  show-icon
                  style="margin-top: 16px;"
                />
              </div>
            </div>
          </a-card>

          <!-- 合成进度 -->
          <a-card
            v-if="project.status === 'processing' || project.status === 'paused' || project.statistics?.completedSegments > 0"
            title="📊 合成进度"
            :bordered="false"
            class="progress-card"
          >
            <div class="progress-content">
              <div class="progress-overview">
                <a-progress
                  :percent="progressPercent"
                  :status="project.status === 'failed' ? 'exception' : 'active'"
                  stroke-color="#06b6d4"
                />
                <div class="progress-stats">
                  <div class="stat-item">
                    <span class="stat-value">{{ project.statistics?.completedSegments || 0 }}</span>
                    <span class="stat-label">已完成</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ project.statistics?.totalSegments || 0 }}</span>
                    <span class="stat-label">总数</span>
                  </div>
                  <div class="stat-item">
                    <span class="stat-value">{{ project.statistics?.failedSegments || 0 }}</span>
                    <span class="stat-label">失败</span>
                  </div>
                </div>
              </div>

              <!-- 当前处理段落 -->
              <div v-if="project.status === 'processing' && currentProcessingSegment" class="current-segment">
                <div class="current-segment-header">
                  <h4>🎯 当前合成段落</h4>
                  <a-tag color="processing">处理中</a-tag>
                </div>
                <div class="current-segment-content">
                  <div class="segment-info">
                    <span class="segment-speaker">{{ currentProcessingSegment.speaker }}</span>
                    <span class="segment-position">第 {{ project.current_segment || 1 }} 段</span>
                  </div>
                  <div class="segment-text">{{ currentProcessingSegment.text }}</div>
                </div>
              </div>

              <!-- 已完成片段 -->
              <div v-if="completedSegments.length > 0" class="completed-segments">
                <div class="completed-header">
                  <h4>✅ 已完成片段</h4>
                  <a-space>
                    <a-tag color="green">{{ completedSegments.length }} 个</a-tag>
                    <a-button size="small" @click="refreshCompletedSegments" :loading="loadingCompletedSegments">
                      🔄 刷新
                    </a-button>
                  </a-space>
                </div>
                
                <div class="completed-list">
                  <div 
                    v-for="(segment, index) in completedSegments.slice(-10)" 
                    :key="segment.id" 
                    class="completed-item"
                  >
                    <div class="segment-meta">
                      <span class="segment-number">{{ completedSegments.length - 9 + index }}</span>
                      <span class="segment-speaker">{{ segment.speaker }}</span>
                      <span class="segment-duration" v-if="segment.duration">{{ formatDuration(segment.duration) }}</span>
                    </div>
                    <div class="segment-content">
                      <div class="segment-text">{{ segment.text?.slice(0, 80) }}{{ segment.text?.length > 80 ? '...' : '' }}</div>
                      <div class="segment-controls">
                        <a-button 
                          v-if="segment.audio_url" 
                          size="small" 
                          type="link"
                          :loading="playingSegment === segment.id"
                          @click="playSegmentAudio(segment)"
                        >
                          {{ playingSegment === segment.id ? '⏸️' : '▶️' }} 播放
                        </a-button>
                        <a-button v-else size="small" type="link" disabled>
                          🔄 处理中
                        </a-button>
                      </div>
                    </div>
                  </div>
                  
                  <div v-if="completedSegments.length > 10" class="show-all-completed">
                    <a-button type="link" @click="showAllCompleted = !showAllCompleted">
                      {{ showAllCompleted ? '收起' : `查看全部 ${completedSegments.length} 个` }}
                    </a-button>
                  </div>
                </div>
              </div>

              <!-- 合成完成操作区 -->
              <div v-if="project.status === 'completed'" class="completion-section">
                <!-- 音频预览 -->
                <div class="audio-preview">
                  <div class="preview-header">
                    <h4>🎵 音频预览</h4>
                    <span class="audio-info">最终合成音频</span>
                  </div>
                  <div class="audio-player-container">
                    <audio 
                      ref="audioPlayer"
                      controls
                      style="width: 100%;"
                      :src="audioPreviewUrl"
                      @loadstart="handleAudioLoadStart"
                      @error="handleAudioError"
                    >
                      您的浏览器不支持音频播放
                    </audio>
                  </div>
                </div>
                
                <!-- 下载按钮 -->
                <div class="download-section">
                  <a-button
                    type="primary"
                    size="large"
                    block
                    @click="downloadAudio"
                    style="margin-bottom: 8px;"
                  >
                    📥 下载完整音频
                  </a-button>
                  <a-button
                    size="large"
                    block
                    @click="viewProjectDetail"
                  >
                    📋 查看详情
                  </a-button>
                </div>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <div v-else class="error-content">
      <a-result
        status="404"
        title="项目不存在"
        sub-title="找不到指定的项目"
      >
        <template #extra>
          <a-button type="primary" @click="goBack">返回项目列表</a-button>
        </template>
      </a-result>
    </div>

    <!-- JSON测试弹窗 -->
    <a-modal
      v-model:open="jsonTestModalVisible"
      title="🧪 JSON测试"
      width="800px"
      @cancel="cancelJsonTest"
    >
      <div class="json-test-modal">
        <a-form layout="vertical">
          <a-form-item label="JSON内容">
            <a-textarea
              v-model:value="jsonTestContent"
              :rows="15"
              placeholder="请输入或粘贴JSON数据..."
              style="font-family: 'Courier New', monospace;"
            />
          </a-form-item>
          
          <a-form-item>
            <a-space>
              <a-button @click="formatJsonContent">
                🎨 格式化
              </a-button>
              <a-button @click="validateJsonContent">
                ✅ 验证格式
              </a-button>
              <a-button @click="clearJsonContent" type="dashed">
                🗑️ 清空
              </a-button>
              <a-button 
                type="primary" 
                @click="executeJsonTest"
                :loading="jsonTestExecuting"
                :disabled="!jsonTestContent.trim()"
              >
                🚀 执行测试
              </a-button>
            </a-space>
          </a-form-item>
          
          <div v-if="jsonValidationResult" class="validation-result">
            <a-alert
              :type="jsonValidationResult.valid ? 'success' : 'error'"
              :message="jsonValidationResult.message"
              :description="jsonValidationResult.description"
              show-icon
            />
          </div>
        </a-form>
      </div>
    </a-modal>

    <!-- 合成进度监控抽屉 -->
    <a-drawer
      v-model:open="synthesisProgressDrawer"
      title="🎵 音频合成进度监控"
      placement="right"
      width="600"
      :closable="false"
      :mask-closable="false"
      :keyboard="false"
      class="synthesis-progress-drawer"
    >
      <div class="progress-container">
        <!-- 总体进度 -->
        <div class="overall-progress">
          <h3>
            🎵 合成总进度
          </h3>
          <a-progress 
            :percent="progressData.progress" 
            :status="progressData.status === 'failed' ? 'exception' : 'active'"
            :stroke-color="progressData.status === 'completed' ? '#52c41a' : '#1890ff'"
          />
          <div class="progress-stats">
            <a-statistic 
              title="已完成" 
              :value="progressData.completed_segments" 
              suffix="/ {{ progressData.total_segments }}"
              :value-style="{ color: '#52c41a' }"
            />
            <a-statistic 
              title="失败数" 
              :value="progressData.failed_segments" 
              :value-style="{ color: progressData.failed_segments > 0 ? '#ff4d4f' : '#666' }"
            />
            <a-statistic 
              title="处理时间" 
              :value="synthesisElapsedTime"
              suffix="秒"
              :value-style="{ color: '#1890ff' }"
            />
  </div>
        </div>

        <!-- 当前处理状态 -->
        <div class="current-status" v-if="progressData.current_processing">
          <a-alert 
            :message="progressData.current_processing" 
            type="info" 
            show-icon 
            class="current-alert"
          />
        </div>

        <!-- 段落详细列表 -->
        <div class="segments-list">
          <h4>📋 段落合成详情</h4>
          <div class="segments-container">
            <div 
              v-for="segment in segmentStatuses" 
              :key="segment.segment_id"
              class="segment-item"
              :class="segment.status"
            >
              <div class="segment-header">
                <span class="segment-id">段落 {{ segment.segment_id }}</span>
                <span class="segment-speaker">{{ segment.speaker }}</span>
                <a-tag 
                  :color="getSegmentStatusColor(segment.status)"
                  class="status-tag"
                >
                  {{ getSegmentStatusText(segment.status) }}
                </a-tag>
              </div>
              
              <div class="segment-content">
                <p class="segment-text">{{ segment.text || '准备中...' }}</p>
                
                <!-- 成功状态 -->
                <div v-if="segment.status === 'completed'" class="segment-actions">
                  <a-button 
                    type="primary" 
                    size="small" 
                    @click="playSegmentAudioAdvanced(segment)"
                    :loading="segment.playing"
                  >
                    ▶️ 播放试听
                  </a-button>
                  <span class="success-info">
                    ✅ {{ segment.completion_time ? formatTime(segment.completion_time) : '完成' }}
                  </span>
                </div>
                
                <!-- 失败状态 -->
                <div v-if="segment.status === 'failed'" class="segment-actions">
                  <a-button 
                    type="primary" 
                    danger 
                    size="small" 
                    @click="retrySegment(segment)"
                    :loading="segment.retrying"
                  >
                    🔄 重试合成
                  </a-button>
                  <span class="error-info">
                    ❌ {{ segment.error_message || '合成失败' }}
                  </span>
                </div>
                
                <!-- 处理中状态 -->
                <div v-if="segment.status === 'processing'" class="segment-actions">
                  <a-spin size="small" />
                  <span class="processing-info">🎵 正在合成中...</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 完成后操作 -->
        <div v-if="progressData.status === 'completed'" class="completion-actions">
          <a-result
            status="success"
            title="🎉 音频合成完成！"
            sub-title="所有段落已成功合成，您可以下载最终音频文件"
          >
            <template #extra>
              <a-button type="primary" size="large" @click="downloadFinalAudio">
                📥 下载完整音频
              </a-button>
              <a-button @click="closeSynthesisDrawer">
                ✅ 确认完成
              </a-button>
            </template>
          </a-result>
        </div>

        <!-- 部分失败后操作 -->
        <div v-if="progressData.status === 'failed' || (progressData.failed_segments > 0 && progressData.status === 'completed')" class="failure-actions">
          <a-alert
            message="⚠️ 部分段落合成失败"
            description="您可以重试失败的段落，或者下载已完成的部分"
            type="warning"
            show-icon
            class="failure-alert"
          />
          <div class="failure-buttons">
            <a-button type="primary" @click="retryAllFailedSegments">
              🔄 重试所有失败段落
            </a-button>
            <a-button @click="downloadPartialAudio" v-if="progressData.completed_segments > 0">
              📥 下载已完成部分
            </a-button>
          </div>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
  import { ref, reactive, computed, onMounted, onUnmounted, h } from 'vue'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import { readerAPI, charactersAPI, intelligentAnalysisAPI, systemAPI, booksAPI } from '@/api'
import { useWebSocketStore } from '@/stores/websocket.js'

const router = useRouter()
const route = useRoute()
const wsStore = useWebSocketStore()

// 响应式数据
const loading = ref(true)
const synthesisStarting = ref(false)
const pausingGeneration = ref(false)
const resumingGeneration = ref(false)
const cancelingGeneration = ref(false)
const project = ref(null)
const detectedCharacters = ref([])
const availableVoices = ref([])
const characterVoiceMapping = reactive({})
const progressTimer = ref(null)
const previewLoading = ref(null)
const currentPlayingVoice = ref(null)
const currentAudio = ref(null)
const checkingService = ref(false)

// 章节选择相关 - 固定为章节模式
const synthesisMode = ref('chapters') // 固定为 'chapters'
const availableChapters = ref([])
const selectedChapters = ref([])
const loadingChapters = ref(false)

// Mock分析相关
const mockAnalyzing = ref(false)
const applyingMock = ref(false)
const mockResult = ref(null)

// 智能准备结果相关
const preparationResults = ref(null)
const loadingResults = ref(false)

// 合成进度和片段相关
const currentProcessingSegment = ref(null)
const completedSegments = ref([])
const loadingCompletedSegments = ref(false)
const playingSegment = ref(null)
const showAllSegments = ref(false)
const showAllCompleted = ref(false)
const segmentAudioPlayer = ref(null)

// JSON测试相关
const jsonTestModalVisible = ref(false)
const jsonTestContent = ref('')
const jsonTestExecuting = ref(false)
const jsonValidationResult = ref(null)

// 合成进度监控抽屉相关
const synthesisProgressDrawer = ref(false)
const synthesisStartTime = ref(null)
const synthesisElapsedTime = ref(0)
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

const synthesisConfig = reactive({
  parallelTasks: 1, // 固定为1，避免GPU显存冲突
  quality: 'high'
})

// 计算属性
const progressPercent = computed(() => {
  if (!project.value?.statistics) return 0
  const { totalSegments, completedSegments } = project.value.statistics
  if (totalSegments === 0) return 0
  return Math.round((completedSegments / totalSegments) * 100)
})

// 音频预览URL
const audioPreviewUrl = computed(() => {
  if (!project.value?.final_audio_path) return null
  // 构建音频预览URL
  return `/api/v1/novel-reader/projects/${project.value.id}/download`
})

const canStartSynthesis = computed(() => {
  const hasValidChapterSelection = selectedChapters.value.length > 0
  const hasPreparationResults = preparationResults.value?.data?.length > 0
  const hasSegments = getTotalSegments() > 0
  
  return project.value?.status !== 'processing' &&
         hasValidChapterSelection &&
         hasPreparationResults &&
         hasSegments
})



// 章节选择相关计算属性
const chapterCheckAll = computed(() => {
  return availableChapters.value.length > 0 && selectedChapters.value.length === availableChapters.value.length
})

const chapterIndeterminate = computed(() => {
  return selectedChapters.value.length > 0 && selectedChapters.value.length < availableChapters.value.length
})

// 方法
const goBack = () => {
  router.push('/novel-reader')
}

const getStatusColor = (status) => {
  const colors = {
    pending: 'orange',
    processing: 'blue',
    paused: 'purple',
    completed: 'green',
    failed: 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    pending: '待开始',
    processing: '合成中',
    paused: '已暂停',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const getStartHint = () => {
  if (selectedChapters.value.length === 0) {
    return '请选择要合成的章节'
  }
  if (!preparationResults.value?.data?.length) {
    return '请先加载智能准备结果'
  }
  if (getTotalSegments() === 0) {
    return '没有可合成的片段'
  }
  return '可以开始合成'
}

// 章节选择相关方法
const loadChapters = async () => {
  if (!project.value?.book?.id) {
    message.warning('项目未关联书籍，无法加载章节')
    return
  }
  
  loadingChapters.value = true
  try {
    const response = await booksAPI.getBookChapters(project.value.book.id)
    if (response.data.success) {
      availableChapters.value = response.data.data || []
      message.success(`加载了 ${availableChapters.value.length} 个章节`)
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
const autoLoadChapters = () => {
  if (availableChapters.value.length === 0) {
    loadChapters()
  }
}

const toggleChapterSelection = (chapterId) => {
  const index = selectedChapters.value.indexOf(chapterId)
  if (index > -1) {
    selectedChapters.value.splice(index, 1)
  } else {
    selectedChapters.value.push(chapterId)
  }
}

const toggleAllChapters = () => {
  if (selectedChapters.value.length === availableChapters.value.length) {
    selectedChapters.value = []
  } else {
    selectedChapters.value = availableChapters.value.map(chapter => chapter.id)
  }
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

// Mock分析方法
const runMockAnalysis = async () => {
  if (!project.value?.id) {
    message.error('请先选择项目')
    return
  }
  
  mockAnalyzing.value = true
  try {
    console.log('=== 开始智能分析测试 ===')
    console.log('选中的章节:', selectedChapters.value)
    
    // 构建分析参数，包含选中的章节
    const analysisParams = {
      chapter_ids: selectedChapters.value.length > 0 ? selectedChapters.value : null
    }
    
    const response = await intelligentAnalysisAPI.analyzeProject(project.value.id, analysisParams)
    
    if (response.data.success) {
      mockResult.value = response.data.data
      message.success('智能分析完成！AI已生成可直接执行的合成计划')
      console.log('智能分析结果:', mockResult.value)
      
      // 记录数据源信息
      const source = response.data.source || 'unknown'
      if (source === 'chapter_analysis') {
        console.log('✅ 使用章节分析结果 (已去除Dify依赖)')
        
        // 显示新的统计信息
        const voiceSummary = mockResult.value.voice_assignment_summary
        if (voiceSummary) {
          message.info(`角色分析完成：${voiceSummary.assigned_voices}/${voiceSummary.total_characters} 个角色已分配声音`)
        }
      }
    } else {
      // 增强错误处理：特别处理章节未分析的情况
      const errorData = response.data.data || {}
      const errorStatus = errorData.status
      
      if (errorStatus === 'pending_analysis') {
        // 章节分析未完成的特殊处理
        const pendingCount = errorData.pending_chapters || 0
        const totalCount = errorData.total_chapters || 0
        const analyzedCount = errorData.analyzed_chapters || 0
        
        console.warn('❌ 章节分析未完成:', {
          total: totalCount,
          analyzed: analyzedCount,
          pending: pendingCount,
          pendingList: errorData.pending_chapter_list
        })
        
        // 显示详细的错误信息和解决方案
        Modal.warning({
          title: '需要先完成章节分析',
          width: 600,
          content: h('div', [
            h('p', `项目共有 ${totalCount} 个章节，已完成 ${analyzedCount} 个，还需要分析 ${pendingCount} 个章节。`),
            h('p', { style: 'margin-top: 12px; font-weight: bold;' }, '解决方案：'),
            h('ol', { style: 'margin: 8px 0; padding-left: 20px;' }, [
              h('li', '前往书籍管理页面'),
              h('li', '找到对应的书籍，点击"查看详情"'),
              h('li', '对未分析的章节点击"🎭 智能准备"按钮'),
              h('li', '等待所有章节分析完成后，再回到合成中心'),
            ]),
            errorData.pending_chapter_list && errorData.pending_chapter_list.length > 0 ? 
              h('div', { style: 'margin-top: 12px;' }, [
                h('p', { style: 'font-weight: bold; margin-bottom: 8px;' }, '待分析章节：'),
                h('ul', { style: 'margin: 0; padding-left: 20px; max-height: 120px; overflow-y: auto;' }, 
                  errorData.pending_chapter_list.slice(0, 10).map(ch => 
                    h('li', { key: ch.id }, `第${ch.chapter_number}章: ${ch.chapter_title}`)
                  )
                ),
                errorData.pending_chapter_list.length > 10 ? 
                  h('p', { style: 'color: #999; font-size: 12px; margin-top: 4px;' }, 
                    `... 等其他 ${errorData.pending_chapter_list.length - 10} 个章节`
                  ) : null
              ]) : null
          ]),
          okText: '我知道了'
        })
      } else {
        // 其他类型的错误
        message.error('智能分析失败: ' + response.data.message)
      }
    }
  } catch (error) {
    console.error('智能分析错误:', error)
    
    // 增强错误处理
    if (error.response && error.response.status === 500) {
      message.error('服务器内部错误，请稍后重试或联系管理员')
    } else if (error.response && error.response.status === 404) {
      message.error('项目不存在，请检查项目是否有效')
    } else {
      message.error('智能分析失败: ' + error.message)
    }
  } finally {
    mockAnalyzing.value = false
  }
}

const applyMockResult = async () => {
  if (!mockResult.value || !project.value?.id) {
    message.error('没有可应用的分析结果')
    return
  }
  
  applyingMock.value = true
  try {
    console.log('=== 应用智能分析结果 ===')
    const response = await intelligentAnalysisAPI.applyAnalysis(project.value.id, mockResult.value)
    
    if (response.data.success) {
      message.success('智能分析结果已应用！')
      console.log('应用结果:', response.data.applied_mapping)
      
      // 检查是否有章节映射信息
      if (mockResult.value.chapter_mapping) {
        const chapterCount = Object.keys(mockResult.value.chapter_mapping).length
        console.log(`✅ 应用了 ${chapterCount} 个章节的分析结果`)
      }
      
      // 检查声音分配统计
      if (mockResult.value.voice_assignment_summary) {
        const summary = mockResult.value.voice_assignment_summary
        message.info(`角色配置已更新：${summary.assigned_voices}/${summary.total_characters} 个角色已分配声音`)
      }
      
      // 使用智能分析的角色结果更新角色配置
      updateCharactersFromAnalysis()
      
      // 刷新项目数据以显示新的角色映射
      await loadProject()
    } else {
      message.error('应用失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('应用智能分析结果错误:', error)
    message.error('应用失败: ' + error.message)
  } finally {
    applyingMock.value = false
  }
}

// 从智能分析结果更新角色配置
const updateCharactersFromAnalysis = () => {
  if (!mockResult.value) return
  
  // 清空现有角色数据
  detectedCharacters.value = []
  
  // 优先从synthesis_plan中提取实际的角色
  const characterStats = {}
  
  if (mockResult.value.synthesis_plan) {
    mockResult.value.synthesis_plan.forEach(segment => {
      const speaker = segment.speaker
      if (speaker && speaker.trim()) {
        if (!characterStats[speaker]) {
          characterStats[speaker] = {
            name: speaker,
            count: 0,
            samples: [],
            voice_id: segment.voice_id,
            voice_name: segment.voice_name || '未分配'
          }
        }
        characterStats[speaker].count++
        
        // 收集示例文本（最多3个）
        if (characterStats[speaker].samples.length < 3 && segment.text) {
          const sampleText = segment.text.slice(0, 30) + (segment.text.length > 30 ? '...' : '')
          if (!characterStats[speaker].samples.includes(sampleText)) {
            characterStats[speaker].samples.push(sampleText)
          }
        }
        
        // 更新voice_id（如果segment中有更新的）
        if (segment.voice_id && !characterStats[speaker].voice_id) {
          characterStats[speaker].voice_id = segment.voice_id
          characterStats[speaker].voice_name = segment.voice_name || '未分配'
        }
      }
    })
  }
  
  // 如果synthesis_plan中没有角色，则使用characters数组作为备选
  if (Object.keys(characterStats).length === 0 && mockResult.value.characters) {
    mockResult.value.characters.forEach(char => {
      characterStats[char.name] = {
        name: char.name,
        count: 1,
        samples: [getCharacterSampleText(char.name)],
        voice_id: char.voice_id,
        voice_name: char.voice_name || '未分配'
      }
    })
  }
  
  // 转换为detectedCharacters格式
  detectedCharacters.value = Object.values(characterStats).map(char => ({
    name: char.name,
    character_id: char.name,
    count: char.count,
    samples: char.samples.length > 0 ? char.samples : [getCharacterSampleText(char.name)],
    voice_id: char.voice_id,
    voice_name: char.voice_name
  }))
  
  // 自动应用AI推荐的角色映射到characterVoiceMapping
  Object.values(characterStats).forEach(char => {
    if (char.voice_id) {
      characterVoiceMapping[char.name] = char.voice_id
    }
  })
  
  console.log('已更新角色配置:', {
    characters: detectedCharacters.value,
    characterVoiceMapping: characterVoiceMapping,
    extractedFromSynthesisPlan: Object.keys(characterStats).length,
    totalSegments: mockResult.value.synthesis_plan?.length || 0
  })
}

// 获取角色示例文本
const getCharacterSampleText = (characterName) => {
  // 从合成计划中找到该角色的文本示例
  if (mockResult.value?.synthesis_plan) {
    const characterSegment = mockResult.value.synthesis_plan.find(segment => 
      segment.speaker === characterName
    )
    if (characterSegment) {
      return characterSegment.text.slice(0, 30) + '...'
    }
  }
  
  // 默认示例文本
  const samples = {
    '李维': '数据的流动模式确实很有趣。',
    '艾莉': '你有没有觉得这些数据像是在讲故事？',
    '系统旁白': '在数字化时代的浪潮中，数据如同蚕茧般包裹着我们的生活。',
    '心理旁白': '李维思考着艾莉的话，意识到数据背后可能隐藏着更深层的含义。'
  }
  
  return samples[characterName] || '这是一段示例文本用于声音试听。'
}

const clearMockResult = () => {
  mockResult.value = null
  message.info('智能分析结果已清空')
}

// JSON测试方法
const showJsonTestModal = () => {
  jsonTestModalVisible.value = true
  jsonTestContent.value = ''
  jsonValidationResult.value = null
}

const cancelJsonTest = () => {
  jsonTestModalVisible.value = false
  jsonTestContent.value = ''
  jsonValidationResult.value = null
}

const formatJsonContent = () => {
  try {
    if (!jsonTestContent.value.trim()) {
      message.warning('请先输入JSON内容')
      return
    }
    
    const parsed = JSON.parse(jsonTestContent.value)
    jsonTestContent.value = JSON.stringify(parsed, null, 2)
    message.success('JSON格式化完成')
  } catch (error) {
    message.error('JSON格式错误: ' + error.message)
  }
}

const validateJsonContent = () => {
  try {
    if (!jsonTestContent.value.trim()) {
      jsonValidationResult.value = {
        valid: false,
        message: '请输入JSON内容',
        description: '输入框不能为空'
      }
      return
    }
    
    const parsed = JSON.parse(jsonTestContent.value)
    
    // 支持两种格式：直接包含字段 或 嵌套在data字段中
    const dataObj = parsed.data || parsed
    
    // 验证必要字段
    const requiredFields = ['project_info', 'characters']
    // segments字段改为synthesis_plan，这是实际使用的字段名
    const optionalFields = ['synthesis_plan', 'segments']
    const missingRequired = requiredFields.filter(field => !dataObj[field])
    const hasSegments = optionalFields.some(field => Array.isArray(dataObj[field]) && dataObj[field].length > 0)
    
    if (missingRequired.length > 0) {
      jsonValidationResult.value = {
        valid: false,
        message: '缺少必要字段',
        description: `缺少以下字段: ${missingRequired.join(', ')}`
      }
      return
    }
    
    // 检查角色数据
    if (!Array.isArray(dataObj.characters) || dataObj.characters.length === 0) {
      jsonValidationResult.value = {
        valid: false,
        message: '角色数据无效',
        description: 'characters字段必须是非空数组'
      }
      return
    }
    
    // 检查分段数据 (synthesis_plan 或 segments)
    if (!hasSegments) {
      jsonValidationResult.value = {
        valid: false,
        message: '分段数据无效',
        description: 'synthesis_plan 或 segments 字段必须是非空数组'
      }
      return
    }
    
    // 详细检查synthesis_plan的数据格式
    const segmentData = dataObj.synthesis_plan || dataObj.segments
    const segmentCount = segmentData.length
    const formatErrors = []
    
    segmentData.forEach((segment, index) => {
      const segmentNum = index + 1
      
      // 检查必要字段
      if (!segment.text || segment.text.trim() === '') {
        formatErrors.push(`第${segmentNum}段缺少text字段`)
      }
      
      // 检查voice_id字段（支持多种格式）
      const hasVoiceId = segment.voice_id || segment.voiceId || 
                        segment.voice_config?.voice_id || segment.voice_config?.voiceId
      const hasSpeaker = segment.speaker || segment.character
      
      if (!hasVoiceId && !hasSpeaker) {
        formatErrors.push(`第${segmentNum}段缺少voice_id或speaker字段`)
      }
      
      // 如果使用voice_config嵌套结构，给出格式建议
      if (segment.voice_config && !segment.voice_id) {
        formatErrors.push(`第${segmentNum}段使用了voice_config嵌套结构，建议改为直接的voice_id字段`)
      }
    })
    
    if (formatErrors.length > 0) {
      jsonValidationResult.value = {
        valid: false,
        message: 'synthesis_plan格式错误',
        description: `发现 ${formatErrors.length} 个问题:\n${formatErrors.join('\n')}\n\n推荐格式: 每个段落应包含 text, voice_id, speaker 字段`
      }
      return
    }
    
    jsonValidationResult.value = {
      valid: true,
      message: 'JSON格式验证通过',
      description: `包含 ${dataObj.characters.length} 个角色，${segmentCount} 个文本段落`
    }
    
  } catch (error) {
    jsonValidationResult.value = {
      valid: false,
      message: 'JSON语法错误',
      description: error.message
    }
  }
}

const clearJsonContent = () => {
  jsonTestContent.value = ''
  jsonValidationResult.value = null
  message.info('内容已清空')
}

const executeJsonTest = async () => {
  if (!jsonTestContent.value.trim()) {
    message.error('请输入JSON内容')
    return
  }
  
  jsonTestExecuting.value = true
  try {
    console.log('=== 开始执行JSON测试 ===')
    
    // 先验证JSON格式
    validateJsonContent()
    if (!jsonValidationResult.value?.valid) {
      message.error('JSON格式验证失败，请修正后重试')
      return
    }
    
    // 解析JSON数据
    const parsed = JSON.parse(jsonTestContent.value)
    console.log('解析的JSON数据:', parsed)
    
    // 支持两种格式：直接包含字段 或 嵌套在data字段中
    const dataObj = parsed.data || parsed
    mockResult.value = dataObj
    
    // 关闭弹窗
    jsonTestModalVisible.value = false
    
    // 更新角色配置
    updateCharactersFromAnalysis()
    
    message.success('JSON测试数据已加载！请查看匹配结果并应用配置')
    console.log('JSON测试结果已设置:', mockResult.value)
    
  } catch (error) {
    console.error('JSON测试执行错误:', error)
    message.error('执行失败: ' + error.message)
  } finally {
    jsonTestExecuting.value = false
  }
}

// 加载项目详情
const loadProject = async () => {
  try {
    const projectId = route.params.projectId
    const response = await readerAPI.getProjectDetail(projectId)
    
    if (response.data.success) {
      project.value = response.data.data
      
      // 如果项目处于processing状态或有段落，加载统计信息
      if (project.value.status === 'processing' || project.value.total_segments > 0) {
        const progressResponse = await readerAPI.getProgress(projectId)
        if (progressResponse.data.success) {
          const progress = progressResponse.data.data
          // 更新统计信息，映射字段名
          project.value.statistics = {
            totalSegments: progress.segments.total,
            completedSegments: progress.segments.completed,
            failedSegments: progress.segments.failed,
            processingSegments: progress.segments.processing,
            pendingSegments: progress.segments.pending
          }
          project.value.status = progress.status
          project.value.current_segment = progress.current_segment
        }
      }
      
      await analyzeCharacters()
    }
  } catch (error) {
    console.error('加载项目失败:', error)
    message.error('加载项目失败')
  } finally {
    loading.value = false
  }
}

// 分析角色
const analyzeCharacters = async () => {
  if (!project.value?.segments) return
  
  try {
    const characterStats = {}
    project.value.segments.forEach(segment => {
      const speaker = segment.detected_speaker || '温柔女声'
      if (!characterStats[speaker]) {
        characterStats[speaker] = {
          name: speaker,
          count: 0,
          samples: []
        }
      }
      characterStats[speaker].count++
      if (characterStats[speaker].samples.length < 3 && segment.text_content) {
        characterStats[speaker].samples.push(segment.text_content.slice(0, 30) + '...')
      }
    })
    
    detectedCharacters.value = Object.values(characterStats)
    
    // 加载现有的角色映射
    if (project.value.character_mapping) {
      Object.assign(characterVoiceMapping, project.value.character_mapping)
    }
    
  } catch (error) {
    console.error('分析角色失败:', error)
    message.error('分析角色失败')
  }
}

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
    // 检查是否正在播放，如果是则停止
    if (currentPlayingVoice.value === voiceId && currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
      currentPlayingVoice.value = null
      return
    }

    // 停止其他正在播放的音频
    if (currentAudio.value) {
      currentAudio.value.pause()
      currentAudio.value = null
      currentPlayingVoice.value = null
    }

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

    // 使用统一的API调用替代直接fetch
    const testParams = {
      text: sampleText || '这是声音预览测试',
      time_step: 20,
      p_weight: 1.0,
      t_weight: 1.0
    }
    
    const response = await charactersAPI.testVoiceSynthesis(selectedVoice.id, testParams)

    if (response.data && response.data.success && response.data.audioUrl) {
      // 构建完整的音频URL
      const audioUrl = response.data.audioUrl.startsWith('http') ? response.data.audioUrl : response.data.audioUrl
      
      // 创建音频元素
      const audio = new Audio(audioUrl)
      currentAudio.value = audio
      currentPlayingVoice.value = voiceId

      // 播放事件处理
      audio.addEventListener('loadstart', () => {
        message.success('开始播放试听')
      })

      audio.addEventListener('ended', () => {
        currentAudio.value = null
        currentPlayingVoice.value = null
      })

      audio.addEventListener('error', (e) => {
        console.error('音频播放错误:', e)
        currentAudio.value = null
        currentPlayingVoice.value = null
        message.error('音频播放失败')
      })

      // 开始播放
      await audio.play()
    } else {
      throw new Error(response.data?.message || '后端API返回错误')
    }
    
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
    console.log('选中章节:', selectedChapters.value)
    
    // 构建合成参数 - 固定为章节模式
    const synthesisParams = {
      parallel_tasks: synthesisConfig.parallelTasks,
      synthesis_mode: 'chapters',
      chapter_ids: selectedChapters.value
    }
    
    message.info(`开始合成选中的 ${selectedChapters.value.length} 个章节`)
    
    const response = await readerAPI.startGeneration(project.value.id, synthesisParams)
    
    if (response.data.success) {
      message.success('合成任务已启动')
      project.value.status = 'processing'
      
      // 初始化合成进度监控
      initializeSynthesisMonitoring()
      
      // 打开进度监控抽屉
      synthesisProgressDrawer.value = true
      
      startProgressPolling()
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
    await readerAPI.pauseGeneration(project.value.id)
    message.success('合成已暂停')
    project.value.status = 'paused'
    
    // 暂停时停止轮询和计时器，但保持抽屉打开
    stopProgressPolling()
    stopElapsedTimer()
    
    // 更新进度数据状态为暂停
    if (synthesisProgressDrawer.value) {
      progressData.value.status = 'paused'
      progressData.value.current_processing = '⏸️ 合成已暂停'
    }
  } catch (error) {
    console.error('暂停合成失败:', error)
    message.error('暂停合成失败')
  } finally {
    pausingGeneration.value = false
  }
}

// 继续合成
const resumeSynthesis = async () => {
  resumingGeneration.value = true
  try {
    // 使用start接口来恢复，因为后端可能没有单独的resume接口
    await readerAPI.startGeneration(project.value.id, {
      parallel_tasks: synthesisConfig.parallelTasks
    })
    message.success('合成已继续')
    project.value.status = 'processing'
    
    // 继续合成时也要重新初始化监控
    initializeSynthesisMonitoring()
    
    // 打开进度监控抽屉
    synthesisProgressDrawer.value = true
    
    startProgressPolling()
  } catch (error) {
    console.error('继续合成失败:', error)
    message.error('继续合成失败')
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
        // 使用暂停接口来停止合成，然后更新状态为cancelled
        await readerAPI.pauseGeneration(project.value.id)
        
        // 更新项目状态为已取消
        project.value.status = 'cancelled'
        
        // 停止所有监控
        stopProgressPolling()
        stopElapsedTimer()
        
        // 更新进度数据状态
        if (synthesisProgressDrawer.value) {
          progressData.value.status = 'cancelled'
          progressData.value.current_processing = '⏹️ 合成已取消'
        }
        
        message.success('合成已取消')
      } catch (error) {
        console.error('取消合成失败:', error)
        message.error('取消合成失败')
      } finally {
        cancelingGeneration.value = false
      }
    }
  })
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
      
      startProgressPolling()
    }
  } catch (error) {
    console.error('重新启动合成失败:', error)
    message.error('重新启动合成失败')
  } finally {
    synthesisStarting.value = false
  }
}

// 查看项目详情
const viewProjectDetail = () => {
  router.push(`/novel-reader/detail/${project.value.id}`)
}

// 音频预览相关处理
const handleAudioLoadStart = () => {
  console.log('音频开始加载')
}

const handleAudioError = (error) => {
  console.error('音频加载失败:', error)
  message.error('音频预览加载失败，请尝试下载完整音频')
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

// 进度轮询
const startProgressPolling = () => {
  let errorCount = 0
  const maxErrors = 5
  const maxDuration = 30 * 60 * 1000 // 30分钟最大轮询时间
  const startTime = Date.now()
  
  progressTimer.value = setInterval(async () => {
    try {
      // 检查轮询时间是否超过最大限制
      if (Date.now() - startTime > maxDuration) {
        console.warn('轮询超时，自动停止')
        stopProgressPolling()
        message.warning('进度监控超时，请刷新页面查看最新状态')
        return
      }

      const response = await readerAPI.getProgress(project.value.id)
      if (response.data.success) {
        const progress = response.data.data
        
        // 更新项目统计信息
        project.value.statistics = {
          totalSegments: progress.segments.total,
          completedSegments: progress.segments.completed,
          failedSegments: progress.segments.failed,
          processingSegments: progress.segments.processing,
          pendingSegments: progress.segments.pending
        }
        project.value.status = progress.status
        project.value.current_segment = progress.current_segment
        
        // 如果进度监控抽屉已打开，同步更新进度数据
        if (synthesisProgressDrawer.value) {
          updateProgressDataFromAPI(progress)
        }
        
        // 重置错误计数
        errorCount = 0
        
        // 更新当前处理段落信息
        currentProcessingSegment.value = getCurrentProcessingSegment()
        
        // 如果有新完成的片段，加载已完成片段列表
        if (progress.segments.completed > (completedSegments.value.length || 0)) {
          await loadCompletedSegments()
        }
        
        // 检查停止条件
        const shouldStop = progress.status === 'completed' || 
                          progress.status === 'failed' ||
                          progress.status === 'cancelled' ||
                          // 如果没有段落在处理且没有待处理的段落，也停止轮询
                          (progress.segments.processing === 0 && 
                           progress.segments.pending === 0 && 
                           progress.segments.total > 0)
        
        if (shouldStop) {
          stopProgressPolling()
          if (progress.status === 'completed') {
            // 重新加载项目以获取最新数据（包括音频文件）
            await loadProject()
            message.success('合成完成！')
          } else if (progress.status === 'failed') {
            message.error('合成失败')
          } else if (progress.status === 'cancelled') {
            message.info('合成已取消')
          } else {
            message.info('任务处理完成')
          }
        }
      } else {
        throw new Error('API响应失败')
      }
    } catch (error) {
      console.error('获取进度失败:', error)
      errorCount++
      
      // 连续错误过多时停止轮询
      if (errorCount >= maxErrors) {
        console.error(`连续${maxErrors}次获取进度失败，停止轮询`)
        stopProgressPolling()
        message.error('无法获取进度信息，请检查网络连接')
      }
    }
  }, 2000)
}

const stopProgressPolling = () => {
  if (progressTimer.value) {
    clearInterval(progressTimer.value)
    progressTimer.value = null
  }
}

// 加载智能准备结果
const loadPreparationResults = async () => {
  if (!project.value?.book?.id) {
    message.warning('项目未关联书籍，无法加载智能准备结果')
    return
  }
  
  loadingResults.value = true
  try {
    const response = await booksAPI.getBookAnalysisResults(project.value.book.id)
    
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
      
      // 更新检测到的角色
      detectedCharacters.value = Object.values(allCharacters)
      
      // 自动应用AI推荐的角色映射
      Object.values(allCharacters).forEach(char => {
        if (char.voice_id) {
          characterVoiceMapping[char.name] = char.voice_id
        }
      })
      
      message.success(`成功加载智能准备结果：${detectedCharacters.value.length} 个角色，${totalSegments} 个段落`)
      
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

// 清空智能准备结果
const clearPreparationResults = () => {
  preparationResults.value = null
  detectedCharacters.value = []
  Object.keys(characterVoiceMapping).forEach(key => {
    delete characterVoiceMapping[key]
  })
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
  try {
    // 停止当前播放
    if (segmentAudioPlayer.value) {
      segmentAudioPlayer.value.pause()
      segmentAudioPlayer.value.currentTime = 0
    }
    
    if (playingSegment.value === segment.id) {
      // 如果点击的是正在播放的，则停止播放
      playingSegment.value = null
      return
    }
    
    playingSegment.value = segment.id
    
    // 创建新的音频播放器
    segmentAudioPlayer.value = new Audio(segment.audio_url)
    
    segmentAudioPlayer.value.addEventListener('ended', () => {
      playingSegment.value = null
    })
    
    segmentAudioPlayer.value.addEventListener('error', (e) => {
      console.error('音频播放失败:', e)
      message.error('音频播放失败')
      playingSegment.value = null
    })
    
    await segmentAudioPlayer.value.play()
    
  } catch (error) {
    console.error('播放片段音频失败:', error)
    message.error('音频播放失败: ' + error.message)
    playingSegment.value = null
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

// WebSocket设置
const setupWebSocketListeners = () => {
  // 确保WebSocket连接
  wsStore.connect()
  
  // 订阅合成进度更新
  unsubscribeWebSocket.value = wsStore.subscribe('synthesis_progress', (data) => {
    if (data.project_id == project.value?.id) {
      console.log('收到WebSocket进度更新:', data)
      
      // 更新进度数据
      progressData.value = {
        progress: data.progress || 0,
        status: data.status || 'processing',
        completed_segments: data.completed_segments || 0,
        total_segments: data.total_segments || 0,
        failed_segments: data.failed_segments || 0,
        current_processing: data.current_processing || '合成中...'
      }
      
      // 更新对应段落的状态
      if (data.current_segment) {
        const segment = segmentStatuses.value.find(s => s.segment_id === data.current_segment)
        if (segment) {
          if (data.status === 'running') {
            segment.status = 'processing'
          } else if (data.status === 'completed' && data.progress === 100) {
            segment.status = 'completed'
            segment.completion_time = data.timestamp
          }
        }
      }
      
      // 如果合成完成，停止计时器并刷新项目数据
      if (data.status === 'completed') {
        stopElapsedTimer()
        stopProgressPolling()
        loadProject()
        message.success('🎉 音频合成完成！')
      } else if (data.status === 'failed') {
        stopElapsedTimer()
        stopProgressPolling()
        message.error('❌ 音频合成失败')
      }
    }
  })
}

// 生命周期
onMounted(async () => {
  await loadProject()
  await loadVoices()
  
  // 设置WebSocket监听器
  setupWebSocketListeners()
  
  // 自动加载章节（因为现在固定为章节模式）
  autoLoadChapters()
  
  // 如果有已完成的片段，加载它们
  if (project.value?.statistics?.completedSegments > 0) {
    await loadCompletedSegments()
  }
  
  // 如果正在处理中，启动进度轮询并自动打开监控抽屉
  if (project.value?.status === 'processing') {
    currentProcessingSegment.value = getCurrentProcessingSegment()
    
    // 自动初始化合成进度监控
    initializeSynthesisMonitoring()
    
    // 自动打开进度监控抽屉
    synthesisProgressDrawer.value = true
    
    startProgressPolling()
  }
})

// 页面切换前的清理
onBeforeRouteLeave(() => {
  stopProgressPolling()
  return true
})

// 组件卸载时的清理
onUnmounted(() => {
  stopProgressPolling()
  stopElapsedTimer()
  // 清理WebSocket监听器
  if (unsubscribeWebSocket.value) {
    unsubscribeWebSocket.value()
  }
})

// 浏览器刷新/关闭前的清理
window.addEventListener('beforeunload', () => {
  stopProgressPolling()
})

// 合成进度监控相关方法
const initializeSynthesisMonitoring = () => {
  // 重置进度数据
  progressData.value = {
    progress: 0,
    status: 'processing',
    completed_segments: 0,
    total_segments: 0,
    failed_segments: 0,
    current_processing: '正在准备合成...'
  }
  
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
  const failedSegments = segmentStatuses.value.filter(s => s.status === 'failed')
  
  if (failedSegments.length === 0) {
    message.info('没有失败的段落需要重试')
    return
  }
  
  message.info(`正在重试 ${failedSegments.length} 个失败段落...`)
  
  // 并发重试所有失败段落
  const retryPromises = failedSegments.map(segment => retrySegment(segment))
  
  try {
    await Promise.all(retryPromises)
    message.success('所有失败段落重试已启动')
  } catch (error) {
    console.error('批量重试失败:', error)
    message.error('批量重试失败')
  }
}

// 下载最终音频
const downloadFinalAudio = async () => {
  try {
    const response = await readerAPI.downloadAudio(project.value.id)
    
    // 处理文件下载
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value.name}_complete.wav`
    link.click()
    window.URL.revokeObjectURL(url)
    
    message.success('完整音频下载成功')
  } catch (error) {
    console.error('下载完整音频失败:', error)
    message.error('下载失败: ' + error.message)
  }
}

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

// 关闭合成抽屉
const closeSynthesisDrawer = () => {
  synthesisProgressDrawer.value = false
  stopElapsedTimer()
  
  // 如果合成已完成，刷新项目数据
  if (progressData.value.status === 'completed') {
    loadProject()
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

// 更新进度轮询以同步段落状态
const updateProgressDataFromAPI = (progress) => {
  // 更新总体进度数据
  progressData.value = {
    progress: Math.round((progress.statistics.completed / progress.statistics.total) * 100),
    status: progress.status,
    completed_segments: progress.statistics.completed,
    total_segments: progress.statistics.total,
    failed_segments: progress.statistics.failed,
    current_processing: progress.current_processing || `正在处理第 ${progress.current_segment || 1} 段`
  }
  
  // 更新段落状态
  if (progress.segments_status) {
    progress.segments_status.forEach(segmentStatus => {
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
  if (progress.status === 'completed' || progress.status === 'failed') {
    stopElapsedTimer()
  }
}
</script>

<style scoped>
.synthesis-center-container {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
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
}
</style>