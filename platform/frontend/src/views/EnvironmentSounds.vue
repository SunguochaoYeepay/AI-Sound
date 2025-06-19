<template>
  <div class="environment-sounds-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-with-back">
            
            <h1 class="page-title">
              <SoundOutlined class="title-icon" />
              环境音管理
            </h1>
          </div>
          <p class="page-description">
            使用TangoFlux AI模型生成各种环境音效，支持自然音、城市音、机械音等多种类型
          </p>
        </div>
        <div class="action-section">
          <a-space>
            <a-button 
              type="primary" 
              size="large"
              @click="showSmartAnalysisModal = true"
              :loading="analyzing"
              ghost
            >
              <BulbOutlined />
              🧠 智能分析
            </a-button>
            <a-button 
              type="primary" 
              size="large"
              @click="showGenerateModal = true"
              :loading="generating"
            >
              <PlusOutlined />
              生成环境音
            </a-button>
          </a-space>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总环境音"
              :value="stats.total_sounds"
              :value-style="{ color: '#1890ff' }"
            >
              <template #prefix>
                <SoundOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="已完成"
              :value="stats.completed_sounds"
              :value-style="{ color: '#52c41a' }"
            >
              <template #prefix>
                <CheckCircleOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="生成中"
              :value="stats.processing_sounds"
              :value-style="{ color: '#fa8c16' }"
            >
              <template #prefix>
                <LoadingOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总播放"
              :value="stats.total_plays"
              :value-style="{ color: '#722ed1' }"
            >
              <template #prefix>
                <PlayCircleOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <a-card>
        <a-form layout="inline" :model="searchForm">
          <a-form-item label="搜索">
            <a-input
              v-model:value="searchForm.search"
              placeholder="搜索环境音名称、描述或提示词"
              style="width: 300px"
              @pressEnter="loadSounds"
            >
              <template #prefix>
                <SearchOutlined />
              </template>
            </a-input>
          </a-form-item>
          
          <a-form-item label="分类">
            <a-select
              v-model:value="searchForm.category_id"
              placeholder="选择分类"
              style="width: 150px"
              allowClear
              @change="loadSounds"
            >
              <a-select-option
                v-for="category in categories"
                :key="category.id"
                :value="category.id"
              >
                {{ category.name }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="标签">
            <a-select
              v-model:value="searchForm.tag_ids"
              mode="multiple"
              placeholder="选择标签"
              style="width: 200px"
              allowClear
              @change="loadSounds"
            >
              <a-select-option
                v-for="tag in tags"
                :key="tag.id"
                :value="tag.id"
              >
                <a-tag :color="tag.color" style="margin: 0;">
                  {{ tag.name }}
                </a-tag>
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="状态">
            <a-select
              v-model:value="searchForm.status"
              placeholder="生成状态"
              style="width: 120px"
              allowClear
              @change="loadSounds"
            >
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="processing">生成中</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item>
            <a-button type="primary" @click="loadSounds">
              <SearchOutlined />
              搜索
            </a-button>
          </a-form-item>

          <a-form-item>
            <a-button @click="resetSearch">
              重置
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>

    <!-- 环境音列表 -->
    <div class="sounds-section">
      <a-card>
        <template #title>
          <div class="list-header">
            <span>环境音列表</span>
            <div class="list-actions">
              <a-switch
                v-model:checked="showFeaturedOnly"
                checkedChildren="精选"
                unCheckedChildren="全部"
                @change="loadSounds"
              />
              <a-select
                v-model:value="sortBy"
                style="width: 120px; margin-left: 8px"
                @change="loadSounds"
              >
                <a-select-option value="created_at">创建时间</a-select-option>
                <a-select-option value="play_count">播放次数</a-select-option>
                <a-select-option value="download_count">下载次数</a-select-option>
                <a-select-option value="favorite_count">收藏数</a-select-option>
                <a-select-option value="duration">时长</a-select-option>
              </a-select>
            </div>
          </div>
        </template>

        <div class="sounds-grid">
          <div
            v-for="sound in sounds"
            :key="sound.id"
            class="sound-card"
            :class="{ 'featured': sound.is_featured }"
          >
            <!-- 状态标识 -->
            <div class="status-badge">
              <a-badge
                :status="getStatusType(sound.generation_status)"
                :text="getStatusText(sound.generation_status)"
              />
            </div>

            <!-- 精选标识 -->
            <div v-if="sound.is_featured" class="featured-badge">
              <StarFilled />
            </div>

            <!-- 音频信息 -->
            <div class="sound-info">
              <h3 class="sound-name">{{ sound.name }}</h3>
              <p class="sound-prompt">{{ sound.prompt }}</p>
              <div class="sound-meta">
                <a-tag v-if="sound.category" :color="'blue'">
                  {{ sound.category.name }}
                </a-tag>
                <a-tag
                  v-for="tag in sound.tags"
                  :key="tag.id"
                  :color="tag.color"
                  style="margin: 2px;"
                >
                  {{ tag.name }}
                </a-tag>
              </div>
              <div class="sound-params">
                <span class="param">{{ sound.duration }}s</span>
                <span class="param">{{ sound.steps }} steps</span>
                <span class="param">CFG {{ sound.cfg_scale }}</span>
              </div>
            </div>

            <!-- 统计信息 -->
            <div class="sound-stats">
              <div class="stat-item">
                <PlayCircleOutlined />
                {{ sound.play_count }}
              </div>
              <div class="stat-item">
                <DownloadOutlined />
                {{ sound.download_count }}
              </div>
              <div class="stat-item">
                <HeartOutlined />
                {{ sound.favorite_count }}
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="sound-actions">
              <a-button-group size="small">
                <a-button
                  v-if="sound.generation_status === 'completed'"
                  type="primary"
                  @click="playSound(sound)"
                  :loading="playingId === sound.id"
                >
                  <PlayCircleOutlined />
                </a-button>
                
                <a-button
                  v-if="sound.generation_status === 'completed'"
                  @click="downloadSound(sound)"
                >
                  <DownloadOutlined />
                </a-button>

                <a-button
                  @click="toggleFavorite(sound)"
                  :type="sound.is_favorited ? 'primary' : 'default'"
                >
                  <HeartOutlined />
                </a-button>

                <a-dropdown>
                  <a-button>
                    <MoreOutlined />
                  </a-button>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item
                        v-if="sound.generation_status === 'failed'"
                        @click="regenerateSound(sound)"
                      >
                        <RedoOutlined />
                        重新生成
                      </a-menu-item>
                      <a-menu-item @click="editSound(sound)">
                        <EditOutlined />
                        编辑
                      </a-menu-item>
                      <a-menu-item @click="copyPrompt(sound.prompt)">
                        <CopyOutlined />
                        复制提示词
                      </a-menu-item>
                      <a-menu-divider />
                      <a-menu-item danger @click="deleteSound(sound)">
                        <DeleteOutlined />
                        删除
                      </a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </a-button-group>
            </div>

            <!-- 错误信息 -->
            <div v-if="sound.generation_status === 'failed'" class="error-message">
              <a-alert
                type="error"
                :message="sound.error_message || '生成失败'"
                banner
              />
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <a-empty
          v-if="!loading && sounds.length === 0"
          description="暂无环境音"
        >
          <a-button type="primary" @click="showGenerateModal = true">
            立即生成
          </a-button>
        </a-empty>

        <!-- 分页 -->
        <div v-if="pagination.total > 0" class="pagination-section">
          <a-pagination
            v-model:current="pagination.current"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            show-size-changer
            show-quick-jumper
            :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
            @change="loadSounds"
            @showSizeChange="loadSounds"
          />
        </div>
      </a-card>
    </div>

    <!-- 生成环境音抽屉 -->
    <GenerateDrawer
      v-model:visible="showGenerateModal"
      :categories="categories"
      :tags="tags"
      :presets="presets"
      @generated="onSoundGenerated"
    />

    <!-- 编辑环境音弹窗 -->
    <EditModal
      v-model:visible="showEditModal"
      :sound="editingSound"
      :categories="categories"
      :tags="tags"
      @updated="onSoundUpdated"
    />

    <!-- 智能分析抽屉 -->
    <a-drawer
      v-model:open="showSmartAnalysisModal"
      title="🧠 智能场景分析"
      placement="right"
      width="1000px"
      :closable="true"
      :maskClosable="false"
      destroyOnClose
      class="smart-analysis-drawer"
    >
      <div class="smart-analysis-content">
        <!-- 步骤指示器 -->
        <div class="steps-container">
          <a-steps :current="analysisStep" direction="horizontal" size="small">
            <a-step title="输入文本" description="导入小说章节或输入文本" />
            <a-step title="智能分析" description="AI分析场景和氛围" />
            <a-step title="生成计划" description="制定环境音生成计划" />
            <a-step title="批量生成" description="自动生成环境音" />
          </a-steps>
        </div>

        <!-- 步骤1: 文本输入 -->
        <div v-if="analysisStep === 0" class="analysis-step">
          <h3>选择文本来源</h3>
          <a-radio-group v-model:value="textSource" style="margin-bottom: 16px;">
            <a-radio value="manual">手动输入</a-radio>
            <a-radio value="chapter">导入章节</a-radio>
          </a-radio-group>

          <div v-if="textSource === 'manual'">
            <a-textarea
              v-model:value="analysisText"
              placeholder="请输入要分析的文本内容，例如小说片段、剧本等..."
              :rows="8"
              style="margin-bottom: 16px;"
            />
          </div>

          <div v-if="textSource === 'chapter'">
            <a-select
              v-model:value="selectedBook"
              placeholder="选择书籍"
              style="width: 100%; margin-bottom: 16px;"
              @change="loadBookChapters"
            >
              <a-select-option
                v-for="book in books"
                :key="book.id"
                :value="book.id"
              >
                {{ book.title }}
              </a-select-option>
            </a-select>

            <a-select
              v-model:value="selectedChapter"
              placeholder="选择章节"
              style="width: 100%; margin-bottom: 16px;"
              @change="loadChapterContent"
            >
              <a-select-option
                v-for="chapter in chapters"
                :key="chapter.id"
                :value="chapter.id"
              >
                {{ chapter.chapter_title || chapter.title }}
              </a-select-option>
            </a-select>

            <a-textarea
              v-model:value="analysisText"
              placeholder="章节内容将在这里显示..."
              :rows="8"
              style="margin-bottom: 16px;"
              readonly
            />
          </div>

          <div class="step-actions">
            <a-button type="primary" @click="startAnalysis" :disabled="!analysisText.trim()">
              开始分析
            </a-button>
          </div>
        </div>

        <!-- 步骤2: 分析进行中和结果 -->
        <div v-if="analysisStep === 1" class="analysis-step">
          <div v-if="analyzing" class="analyzing-state">
            <a-spin size="large">
              <template #indicator>
                <BulbOutlined style="font-size: 24px" spin />
              </template>
            </a-spin>
            <h3 style="margin-top: 16px;">正在分析场景...</h3>
            <p>AI正在深度理解文本内容，识别场景、氛围和情感变化</p>
            <a-progress :percent="analysisProgress" status="active" />
          </div>

          <div v-if="analysisResult && !analyzing" class="analysis-result">
            <h3>分析结果</h3>
            
            <!-- 分析摘要 -->
            <a-card title="分析摘要" style="margin-bottom: 16px;">
              <a-descriptions :column="2" size="small">
                <a-descriptions-item label="场景数量">{{ analysisResult.total_scenes }}</a-descriptions-item>
                <a-descriptions-item label="分析模式">{{ analysisResult.llm_provider || '基础分析' }}</a-descriptions-item>
                <a-descriptions-item label="置信度">{{ (analysisResult.confidence_score * 100).toFixed(1) }}%</a-descriptions-item>
                <a-descriptions-item label="处理时间">{{ analysisResult.processing_time.toFixed(2) }}s</a-descriptions-item>
              </a-descriptions>
              
              <div v-if="analysisResult.narrative_analysis" style="margin-top: 16px;">
                <a-tag color="blue">{{ analysisResult.narrative_analysis.genre || '未知体裁' }}</a-tag>
                <a-tag color="green">{{ analysisResult.narrative_analysis.pace || '中等节奏' }}</a-tag>
                <span style="margin-left: 8px; color: #666;">
                  {{ analysisResult.narrative_analysis.emotional_arc }}
                </span>
              </div>
            </a-card>

            <!-- 场景列表 -->
            <a-card title="识别的场景">
              <div class="scenes-list">
                <div
                  v-for="(scene, index) in analysisResult.analyzed_scenes"
                  :key="index"
                  class="scene-item"
                >
                  <div class="scene-header">
                    <h4>场景 {{ index + 1 }}</h4>
                    <a-tag :color="getSceneColor(scene.atmosphere)">{{ scene.atmosphere }}</a-tag>
                  </div>
                  <div class="scene-details">
                    <a-space>
                      <a-tag>📍 {{ scene.location }}</a-tag>
                      <a-tag>🌤️ {{ scene.weather }}</a-tag>
                      <a-tag>🕐 {{ scene.time_of_day }}</a-tag>
                      <a-tag>🎯 {{ (scene.confidence * 100).toFixed(0) }}%</a-tag>
                    </a-space>
                  </div>
                  <div v-if="scene.keywords && scene.keywords.length > 0" class="scene-keywords">
                    <a-tag
                      v-for="keyword in scene.keywords"
                      :key="keyword"
                      size="small"
                      color="default"
                    >
                      {{ keyword }}
                    </a-tag>
                  </div>
                </div>
              </div>
              
              <div class="step-actions" style="margin-top: 16px;">
                <a-space>
                  <a-button @click="analysisStep = 0">重新分析</a-button>
                  <a-button type="primary" @click="generateSmartPrompts">
                    生成智能提示词
                  </a-button>
                </a-space>
              </div>
            </a-card>
          </div>
        </div>

        <!-- 步骤3: 智能提示词和生成计划 -->
        <div v-if="analysisStep === 2" class="analysis-step">
          <div v-if="generatingPrompts" class="generating-state">
            <a-spin size="large" />
            <h3 style="margin-top: 16px;">正在生成智能提示词...</h3>
          </div>

          <div v-if="smartPrompts && !generatingPrompts" class="smart-prompts-result">
            <h3>智能提示词方案</h3>
            
            <!-- 音景推荐 -->
            <a-card v-if="smartPrompts.soundscape_recommendation" title="整体音景设计" style="margin-bottom: 16px;">
              <a-descriptions :column="2" size="small">
                <a-descriptions-item label="主要元素">
                  <a-tag v-for="element in smartPrompts.soundscape_recommendation.primary_elements" :key="element" color="blue">
                    {{ element }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="次要元素">
                  <a-tag v-for="element in smartPrompts.soundscape_recommendation.secondary_elements" :key="element" color="green">
                    {{ element }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="建议总时长">{{ smartPrompts.soundscape_recommendation.overall_duration }}秒</a-descriptions-item>
                <a-descriptions-item label="环境层次">{{ smartPrompts.soundscape_recommendation.ambient_layers?.join(', ') }}</a-descriptions-item>
              </a-descriptions>
            </a-card>

            <!-- 提示词列表 -->
            <a-card title="生成提示词">
              <div class="prompts-list">
                <div
                  v-for="(prompt, index) in smartPrompts.smart_prompts"
                  :key="index"
                  class="prompt-item"
                >
                  <div class="prompt-header">
                    <h4>{{ prompt.title }}</h4>
                    <a-space>
                      <a-tag color="orange">{{ prompt.duration }}s</a-tag>
                      <a-tag :color="getPriorityColor(prompt.priority)">优先级 {{ prompt.priority }}</a-tag>
                      <a-checkbox v-model:checked="prompt.selected">生成</a-checkbox>
                    </a-space>
                  </div>
                  
                  <div class="prompt-content">
                    <a-typography-paragraph :copyable="{ text: prompt.prompt }">
                      <code>{{ prompt.prompt }}</code>
                    </a-typography-paragraph>
                  </div>

                  <div v-if="prompt.dynamic_elements && prompt.dynamic_elements.length > 0" class="prompt-features">
                    <strong>动态元素:</strong>
                    <a-tag
                      v-for="element in prompt.dynamic_elements"
                      :key="element"
                      size="small"
                      color="purple"
                    >
                      {{ element }}
                    </a-tag>
                  </div>

                  <div class="prompt-settings">
                    <a-space>
                      <span>淡入: {{ prompt.fade_settings.fade_in }}s</span>
                      <span>淡出: {{ prompt.fade_settings.fade_out }}s</span>
                      <span>复杂度: {{ prompt.generation_tips.complexity }}</span>
                    </a-space>
                  </div>
                </div>
              </div>

              <div class="step-actions" style="margin-top: 16px;">
                <a-space>
                  <a-button @click="analysisStep = 1">返回分析</a-button>
                  <a-button @click="selectAllPrompts">全选</a-button>
                  <a-button @click="selectNonePrompts">全不选</a-button>
                  <a-button type="primary" @click="startBatchGeneration" :disabled="!hasSelectedPrompts">
                    开始批量生成 ({{ selectedPromptsCount }})
                  </a-button>
                </a-space>
              </div>
            </a-card>
          </div>
        </div>

        <!-- 步骤4: 批量生成进度 -->
        <div v-if="analysisStep === 3" class="analysis-step">
          <h3>批量生成进行中</h3>
          
          <a-card>
            <div class="generation-progress">
              <a-progress 
                :percent="Math.round((batchProgress.completed / batchProgress.total) * 100)"
                :status="batchProgress.status"
                style="margin-bottom: 16px;"
              />
              
              <a-descriptions :column="2" size="small">
                <a-descriptions-item label="总任务">{{ batchProgress.total }}</a-descriptions-item>
                <a-descriptions-item label="已完成">{{ batchProgress.completed }}</a-descriptions-item>
                <a-descriptions-item label="进行中">{{ batchProgress.processing }}</a-descriptions-item>
                <a-descriptions-item label="失败">{{ batchProgress.failed }}</a-descriptions-item>
              </a-descriptions>

              <div v-if="batchProgress.currentTask" style="margin-top: 16px;">
                <h4>当前任务</h4>
                <p>{{ batchProgress.currentTask.title }}</p>
                <a-progress :percent="batchProgress.currentTask.progress" size="small" />
              </div>
            </div>

            <!-- 生成日志 -->
            <div v-if="generationLogs.length > 0" class="generation-logs" style="margin-top: 16px;">
              <h4>生成日志</h4>
              <div class="logs-container">
                <div
                  v-for="(log, index) in generationLogs"
                  :key="index"
                  class="log-item"
                  :class="log.type"
                >
                  <span class="log-time">{{ log.time }}</span>
                  <span class="log-message">{{ log.message }}</span>
                </div>
              </div>
            </div>

            <div class="step-actions" style="margin-top: 16px;">
              <a-space>
                <a-button v-if="batchProgress.status !== 'active'" @click="showSmartAnalysisModal = false">
                  关闭
                </a-button>
                <a-button v-if="batchProgress.status === 'active'" @click="cancelBatchGeneration" danger>
                  取消生成
                </a-button>
              </a-space>
            </div>
          </a-card>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  SoundOutlined, PlusOutlined, SearchOutlined, PlayCircleOutlined,
  DownloadOutlined, HeartOutlined, MoreOutlined, EditOutlined,
  DeleteOutlined, CopyOutlined, RedoOutlined, CheckCircleOutlined,
  LoadingOutlined, StarFilled, ArrowLeftOutlined, BulbOutlined
} from '@ant-design/icons-vue'

import GenerateDrawer from '@/components/environment-sounds/GenerateDrawer.vue'
import EditModal from '@/components/environment-sounds/EditModal.vue'
import { getAudioService } from '@/utils/audioService'
import { environmentSoundsAPI, booksAPI, chaptersAPI } from '@/api'
import apiClient, { llmAnalysisClient } from '@/api/config'

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const generating = ref(false)
const playingId = ref(null)
const sounds = ref([])
const categories = ref([])
const tags = ref([])
const presets = ref([])

// 统计数据
const stats = reactive({
  total_sounds: 0,
  completed_sounds: 0,
  processing_sounds: 0,
  failed_sounds: 0,
  total_plays: 0
})

// 搜索表单
const searchForm = reactive({
  search: '',
  category_id: null,
  tag_ids: [],
  status: null
})

// 排序和筛选
const showFeaturedOnly = ref(false)
const sortBy = ref('created_at')

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 弹窗控制
const showGenerateModal = ref(false)
const showEditModal = ref(false)
const editingSound = ref(null)

// 智能分析相关
const showSmartAnalysisModal = ref(false)
const analyzing = ref(false)
const analysisStep = ref(0)
const analysisProgress = ref(0)
const textSource = ref('manual')
const analysisText = ref('')
const analysisResult = ref(null)
const smartPrompts = ref(null)
const generatingPrompts = ref(false)

// 书籍和章节数据
const books = ref([])
const chapters = ref([])
const selectedBook = ref(null)
const selectedChapter = ref(null)

// 批量生成相关
const batchProgress = reactive({
  total: 0,
  completed: 0,
  processing: 0,
  failed: 0,
  status: 'idle', // idle, active, completed, error
  currentTask: null
})
const generationLogs = ref([])

// 生命周期
onMounted(() => {
  loadInitialData()
})

// 方法
const loadInitialData = async () => {
  await Promise.all([
    loadCategories(),
    loadTags(),
    loadPresets(),
    loadStats(),
    loadSounds()
  ])
}

const loadCategories = async () => {
  try {
    const response = await environmentSoundsAPI.getCategories()
    categories.value = response.data
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const loadTags = async () => {
  try {
    const response = await environmentSoundsAPI.getTags()
    tags.value = response.data
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

const loadPresets = async () => {
  try {
    const response = await environmentSoundsAPI.getPresets()
    presets.value = response.data
  } catch (error) {
    console.error('加载预设失败:', error)
  }
}

const loadStats = async () => {
  try {
    const response = await environmentSoundsAPI.getStats()
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadSounds = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchForm,
      featured_only: showFeaturedOnly.value,
      sort_by: sortBy.value,
      sort_order: 'desc'
    }

    // 处理数组参数
    if (params.tag_ids && params.tag_ids.length > 0) {
      params.tag_ids = params.tag_ids.join(',')
    } else {
      delete params.tag_ids
    }

    const response = await environmentSoundsAPI.getEnvironmentSounds(params)
    const data = response.data

    sounds.value = data.sounds
    pagination.total = data.total
    pagination.current = data.page
    pagination.pageSize = data.page_size

  } catch (error) {
    console.error('加载环境音列表失败:', error)
    message.error('加载环境音列表失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  Object.assign(searchForm, {
    search: '',
    category_id: null,
    tag_ids: [],
    status: null
  })
  showFeaturedOnly.value = false
  sortBy.value = 'created_at'
  pagination.current = 1
  loadSounds()
}

const playSound = async (sound) => {
  try {
    playingId.value = sound.id
    
    // 记录播放日志
    await environmentSoundsAPI.playEnvironmentSound(sound.id)
    
    // 使用统一音频服务播放
    await getAudioService().playEnvironmentSound(sound)
    
    // 更新播放计数
    sound.play_count += 1
    
  } catch (error) {
    console.error('播放失败:', error)
    message.error('播放失败')
  } finally {
    playingId.value = null
  }
}

const downloadSound = async (sound) => {
  try {
    const response = await environmentSoundsAPI.downloadEnvironmentSound(sound.id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${sound.name}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    // 更新下载计数
    sound.download_count += 1
    message.success('下载成功')
    
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

const toggleFavorite = async (sound) => {
  try {
    const response = await environmentSoundsAPI.toggleFavorite(sound.id)
    const result = response.data
    
    sound.is_favorited = result.is_favorited
    sound.favorite_count = result.favorite_count
    
    message.success(result.is_favorited ? '已收藏' : '已取消收藏')
    
  } catch (error) {
    console.error('收藏操作失败:', error)
    message.error('收藏操作失败')
  }
}

const regenerateSound = async (sound) => {
  try {
    await environmentSoundsAPI.regenerateEnvironmentSound(sound.id)
    sound.generation_status = 'processing'
    sound.error_message = null
    message.success('重新生成任务已启动')
    
    // 定期检查生成状态
    checkGenerationStatus(sound.id)
    
  } catch (error) {
    console.error('重新生成失败:', error)
    message.error('重新生成失败')
  }
}

const editSound = (sound) => {
  editingSound.value = { ...sound }
  showEditModal.value = true
}

const deleteSound = (sound) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除环境音"${sound.name}"吗？此操作不可恢复。`,
    onOk: async () => {
      try {
        await environmentSoundsAPI.deleteEnvironmentSound(sound.id)
        message.success('删除成功')
        loadSounds()
        loadStats()
      } catch (error) {
        console.error('删除失败:', error)
        message.error('删除失败')
      }
    }
  })
}

const copyPrompt = (prompt) => {
  navigator.clipboard.writeText(prompt).then(() => {
    message.success('提示词已复制到剪贴板')
  }).catch(() => {
    message.error('复制失败')
  })
}

const onSoundGenerated = (soundId) => {
  showGenerateModal.value = false
  loadSounds()
  loadStats()
  
  // 开始检查生成状态
  checkGenerationStatus(soundId)
}

const onSoundUpdated = () => {
  showEditModal.value = false
  editingSound.value = null
  loadSounds()
}

const checkGenerationStatus = (soundId) => {
  const interval = setInterval(async () => {
    try {
      const response = await environmentSoundsAPI.getEnvironmentSound(soundId)
      const sound = response.data
      
      // 更新列表中的对应项
      const index = sounds.value.findIndex(s => s.id === soundId)
      if (index !== -1) {
        sounds.value[index] = sound
      }
      
      // 如果生成完成或失败，停止检查
      if (sound.generation_status === 'completed' || sound.generation_status === 'failed') {
        clearInterval(interval)
        loadStats() // 更新统计数据
        
        if (sound.generation_status === 'completed') {
          message.success(`环境音"${sound.name}"生成完成`)
        } else {
          message.error(`环境音"${sound.name}"生成失败`)
        }
      }
      
    } catch (error) {
      clearInterval(interval)
      console.error('检查生成状态失败:', error)
    }
  }, 3000) // 每3秒检查一次
}

// 智能分析方法
const loadBooks = async () => {
  try {
    const response = await booksAPI.getBooks()
    books.value = response.data.data || []
  } catch (error) {
    console.error('加载书籍失败:', error)
    message.error('加载书籍失败')
  }
}

const loadBookChapters = async () => {
  if (!selectedBook.value) return
  
  try {
    const response = await booksAPI.getBookChapters(selectedBook.value)
    chapters.value = response.data.data || response.data || []
  } catch (error) {
    console.error('加载章节失败:', error)
    message.error('加载章节失败')
  }
}

const loadChapterContent = async () => {
  if (!selectedChapter.value) return
  
  try {
    const response = await chaptersAPI.getChapter(selectedChapter.value)
    analysisText.value = response.data.data?.content || response.data.content || ''
  } catch (error) {
    console.error('加载章节内容失败:', error)
    message.error('加载章节内容失败')
  }
}

const startAnalysis = async () => {
  if (!analysisText.value.trim()) {
    message.error('请输入要分析的文本')
    return
  }

  analyzing.value = true
  analysisStep.value = 1
  analysisProgress.value = 0

  try {
    // 模拟进度更新
    const progressInterval = setInterval(() => {
      if (analysisProgress.value < 90) {
        analysisProgress.value += Math.random() * 20
      }
    }, 500)

    // 调用分析API - 使用专门的LLM分析客户端（超长超时）
    const response = await llmAnalysisClient.post('/scene-analysis/analyze-text', {
      text: analysisText.value,
      use_llm: true,
      llm_provider: 'auto',
      include_recommendations: true
    })

    clearInterval(progressInterval)
    analysisProgress.value = 100

    analysisResult.value = response.data
    message.success('场景分析完成！')

  } catch (error) {
    console.error('分析失败:', error)
    message.error('分析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    analyzing.value = false
  }
}

const generateSmartPrompts = async () => {
  if (!analysisResult.value) return

  generatingPrompts.value = true
  analysisStep.value = 2

  try {
    const response = await apiClient.post('/scene-analysis/generate-smart-prompts', {
      text: analysisText.value,
      llm_provider: 'auto'
    })

    smartPrompts.value = response.data
    
    // 为每个提示词添加选中状态
    smartPrompts.value.smart_prompts.forEach(prompt => {
      prompt.selected = true // 默认全选
    })

    message.success('智能提示词生成完成！')

  } catch (error) {
    console.error('生成提示词失败:', error)
    message.error('生成提示词失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generatingPrompts.value = false
  }
}

const startBatchGeneration = async () => {
  const selectedPrompts = smartPrompts.value.smart_prompts.filter(p => p.selected)
  
  if (selectedPrompts.length === 0) {
    message.error('请至少选择一个提示词')
    return
  }

  analysisStep.value = 3
  batchProgress.total = selectedPrompts.length
  batchProgress.completed = 0
  batchProgress.processing = 0
  batchProgress.failed = 0
  batchProgress.status = 'active'
  generationLogs.value = []

  // 添加开始日志
  addGenerationLog('info', '开始批量生成环境音...')

  try {
    // 逐个生成环境音
    for (let i = 0; i < selectedPrompts.length; i++) {
      const prompt = selectedPrompts[i]
      
      batchProgress.currentTask = {
        title: prompt.title,
        progress: 0
      }
      
      try {
        addGenerationLog('info', `开始生成: ${prompt.title}`)
        
        // 模拟进度更新
        const taskProgressInterval = setInterval(() => {
          if (batchProgress.currentTask && batchProgress.currentTask.progress < 90) {
            batchProgress.currentTask.progress += Math.random() * 15
          }
        }, 1000)

        // 调用生成API
        const response = await environmentSoundsAPI.generateEnvironmentSound({
          name: prompt.title,
          prompt: prompt.prompt,
          duration: prompt.duration,
          category_id: null,
          tag_ids: [],
          metadata: {
            generated_from_analysis: true,
            source_text: analysisText.value.substring(0, 200) + '...',
            scene_details: prompt.scene_details,
            generation_method: 'smart_analysis'
          }
        })

        clearInterval(taskProgressInterval)
        batchProgress.currentTask.progress = 100
        
        batchProgress.completed++
        addGenerationLog('success', `✅ ${prompt.title} 生成完成`)

        // 开始检查生成状态
        if (response.data.id) {
          checkGenerationStatus(response.data.id)
        }

      } catch (error) {
        batchProgress.failed++
        addGenerationLog('error', `❌ ${prompt.title} 生成失败: ${error.message}`)
        console.error(`生成 ${prompt.title} 失败:`, error)
      }
    }

    batchProgress.status = 'completed'
    batchProgress.currentTask = null
    addGenerationLog('info', '批量生成完成！')
    
    message.success('批量生成任务完成！')
    
    // 刷新环境音列表
    await loadSounds()
    await loadStats()

  } catch (error) {
    batchProgress.status = 'error'
    addGenerationLog('error', `批量生成失败: ${error.message}`)
    message.error('批量生成失败')
  }
}

const cancelBatchGeneration = () => {
  batchProgress.status = 'cancelled'
  batchProgress.currentTask = null
  addGenerationLog('warning', '批量生成已取消')
  message.info('批量生成已取消')
}

const addGenerationLog = (type, message) => {
  generationLogs.value.push({
    type,
    message,
    time: new Date().toLocaleTimeString()
  })
}

const selectAllPrompts = () => {
  if (smartPrompts.value && smartPrompts.value.smart_prompts) {
    smartPrompts.value.smart_prompts.forEach(prompt => {
      prompt.selected = true
    })
  }
}

const selectNonePrompts = () => {
  if (smartPrompts.value && smartPrompts.value.smart_prompts) {
    smartPrompts.value.smart_prompts.forEach(prompt => {
      prompt.selected = false
    })
  }
}

// 计算属性
const hasSelectedPrompts = computed(() => {
  return smartPrompts.value && smartPrompts.value.smart_prompts 
    ? smartPrompts.value.smart_prompts.some(p => p.selected)
    : false
})

const selectedPromptsCount = computed(() => {
  return smartPrompts.value && smartPrompts.value.smart_prompts 
    ? smartPrompts.value.smart_prompts.filter(p => p.selected).length
    : 0
})

// 样式相关方法
const getSceneColor = (atmosphere) => {
  const colorMap = {
    'calm': 'blue',
    'tense': 'red', 
    'romantic': 'pink',
    'action': 'orange',
    'mysterious': 'purple',
    'scary': 'volcano',
    'joyful': 'green',
    'sad': 'grey'
  }
  return colorMap[atmosphere] || 'default'
}

const getPriorityColor = (priority) => {
  if (priority >= 4) return 'red'
  if (priority >= 3) return 'orange'
  if (priority >= 2) return 'blue'
  return 'default'
}

// 监听智能分析模态框打开
watch(showSmartAnalysisModal, (newValue) => {
  if (newValue) {
    // 重置状态
    analysisStep.value = 0
    analysisText.value = ''
    analysisResult.value = null
    smartPrompts.value = null
    selectedBook.value = null
    selectedChapter.value = null
    textSource.value = 'manual'
    
    // 加载书籍数据
    loadBooks()
  }
})

// 辅助方法
const getStatusType = (status) => {
  const statusMap = {
    'completed': 'success',
    'processing': 'processing',
    'failed': 'error',
    'pending': 'default'
  }
  return statusMap[status] || 'default'
}

const getStatusText = (status) => {
  const statusMap = {
    'completed': '已完成',
    'processing': '生成中',
    'failed': '失败',
    'pending': '等待中'
  }
  return statusMap[status] || '未知'
}

const goBack = () => {
  router.go(-1) // 返回上一页
}
</script>

<style scoped>
.environment-sounds-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
  padding: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title-with-back {
  display: flex;
  align-items: center;
  gap: 8px;
}

.back-btn {
  font-size: 16px;
  padding: 4px 8px;
  display: flex;
  align-items: center;
  color: rgba(255, 255, 255, 0.8);
  transition: all 0.2s;
}

.back-btn:hover {
  color: #ffffff;
  background: rgba(255, 255, 255, 0.1);
}

.title-section .page-title {
  display: flex;
  align-items: center;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: white;
}

.title-icon {
  margin-right: 12px;
  color: #ffffff;
}

.page-description {
  margin: 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  line-height: 1.5;
}

.stats-section {
  margin-bottom: 24px;
}

.filter-section {
  margin-bottom: 24px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-actions {
  display: flex;
  align-items: center;
}

.sounds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.sound-card {
  position: relative;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: all 0.3s ease;
}

.sound-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.sound-card.featured {
  border-color: #faad14;
  background: linear-gradient(135deg, #fff9e6 0%, #fff 100%);
}

.status-badge {
  position: absolute;
  top: 12px;
  right: 12px;
}

.featured-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  color: #faad14;
  font-size: 16px;
}

.sound-info {
  margin-bottom: 12px;
}

.sound-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

.sound-prompt {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sound-meta {
  margin-bottom: 8px;
}

.sound-params {
  display: flex;
  gap: 8px;
}

.param {
  padding: 2px 6px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.sound-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  padding: 8px 0;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 12px;
}

.sound-actions {
  display: flex;
  justify-content: flex-end;
}

.error-message {
  margin-top: 12px;
}

.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 智能分析抽屉样式 */
.smart-analysis-drawer :deep(.ant-drawer-body) {
  padding: 24px;
  height: 100%;
  overflow-y: auto;
}

.smart-analysis-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.steps-container {
  margin-bottom: 24px;
  padding: 16px;
  background: #fafafa;
  border-radius: 8px;
  flex-shrink: 0;
}

.analysis-step {
  flex: 1;
  display: flex;
  flex-direction: column;
  min-height: 0;
}

.analyzing-state, .generating-state {
  text-align: center;
  padding: 40px 20px;
}

.analyzing-state h3, .generating-state h3 {
  color: #1890ff;
  margin-bottom: 8px;
}

.scenes-list {
  space-y: 16px;
}

.scene-item {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
}

.scene-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.scene-header h4 {
  margin: 0;
  color: #1890ff;
}

.scene-details {
  margin-bottom: 8px;
}

.scene-keywords {
  margin-top: 8px;
}

.prompts-list {
  space-y: 20px;
}

.prompt-item {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 20px;
  background: #fff;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.prompt-header h4 {
  margin: 0;
  color: #2c3e50;
  font-size: 16px;
}

.prompt-content {
  margin-bottom: 12px;
}

.prompt-content code {
  background: #f6f8fa;
  padding: 8px 12px;
  border-radius: 4px;
  font-size: 13px;
  line-height: 1.6;
  display: block;
  white-space: pre-wrap;
  word-break: break-word;
}

.prompt-features {
  margin-bottom: 8px;
  color: #666;
}

.prompt-settings {
  font-size: 12px;
  color: #888;
}

.step-actions {
  margin-top: 24px;
  text-align: center;
}

.generation-progress {
  text-align: center;
}

.generation-logs {
  max-height: 200px;
  overflow-y: auto;
}

.logs-container {
  background: #f8f9fa;
  border-radius: 4px;
  padding: 12px;
  font-family: monospace;
  font-size: 12px;
}

.log-item {
  display: flex;
  margin-bottom: 4px;
  line-height: 1.4;
}

.log-time {
  color: #666;
  margin-right: 8px;
  min-width: 80px;
}

.log-message {
  flex: 1;
}

.log-item.success .log-message {
  color: #52c41a;
}

.log-item.error .log-message {
  color: #ff4d4f;
}

.log-item.warning .log-message {
  color: #fa8c16;
}

.log-item.info .log-message {
  color: #1890ff;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environment-sounds-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .sounds-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-section :deep(.ant-form-inline) {
    display: block;
  }
  
  .filter-section :deep(.ant-form-item) {
    margin-bottom: 16px;
  }

  /* 移动端抽屉全屏显示 */
  .smart-analysis-drawer :deep(.ant-drawer) {
    width: 100vw !important;
  }
  
  .smart-analysis-drawer :deep(.ant-drawer-body) {
    padding: 16px;
  }

  .prompt-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .step-actions {
    margin-top: 16px;
  }
  
  .step-actions :deep(.ant-space) {
    width: 100%;
    justify-content: center;
  }
  
  .steps-container {
    margin-bottom: 16px;
    padding: 12px;
  }
  
  .steps-container :deep(.ant-steps) {
    font-size: 12px;
  }
}
</style> 