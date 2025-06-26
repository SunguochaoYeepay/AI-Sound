<template>
  <a-drawer
    :open="visible"
    title="🧠 环境混音智能配置"
    placement="right"
    width="1000px"
    :closable="true"
    :maskClosable="false"
    destroyOnClose
    class="environment-mixing-drawer"
    @close="emit('update:visible', false)"
  >
    <div class="mixing-analysis-content">
      <!-- 步骤指示器 -->
      <div class="steps-container">
        <a-steps :current="currentStep" direction="horizontal" size="small">
          <a-step title="选择章节" description="选择小说章节进行分析" />
          <a-step title="智能分析" description="AI分析生成混音参数和时间轴" />
          <a-step title="确认配置" description="确认混音配置并持久化保存" />
          <a-step title="开始混音" description="启动环境混音生成" />
        </a-steps>
      </div>

      <!-- 步骤1: 章节选择 -->
      <div v-if="currentStep === 0" class="analysis-step">
        <h3>选择小说章节</h3>
        <p style="color: #666; margin-bottom: 16px;">从已导入的小说中选择章节进行环境音智能分析</p>

        <div>
          <a-select
            v-model:value="selectedBook"
            placeholder="选择书籍"
            style="width: 100%; margin-bottom: 16px;"
            :loading="bookLoading"
            @change="loadChapters"
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
            v-model:value="selectedChapterIds"
            mode="multiple"
            placeholder="选择已分析的章节（支持多选）"
            style="width: 100%; margin-bottom: 16px;"
            :max-tag-count="3"
            :loading="chapterLoading"
          >
            <a-select-option
              v-for="chapter in chapters"
              :key="chapter.id"
              :value="chapter.id"
            >
              <div style="display: flex; justify-content: space-between; align-items: center;">
                <span>{{ chapter.chapter_title || chapter.title }}</span>
                <a-tag color="blue" size="small">可分析</a-tag>
              </div>
            </a-select-option>
          </a-select>

          <!-- 提示信息 -->
          <div v-if="chapters.length === 0 && selectedBook" style="margin-bottom: 16px;">
            <a-alert
              message="该书籍暂无可用章节"
              description="请检查书籍是否包含章节数据，或者重新选择其他书籍。"
              type="info"
              show-icon
            />
          </div>

          <!-- 分析选项 -->
          <div v-if="selectedChapterIds.length > 0" style="margin-bottom: 16px;">
            <h4>分析选项</h4>
            <a-checkbox-group v-model:value="analysisOptions">
              <a-checkbox value="include_emotion">包含情感分析</a-checkbox>
              <a-checkbox value="precise_timing">精确时长计算</a-checkbox>
              <a-checkbox value="intensity_analysis">强度分析</a-checkbox>
            </a-checkbox-group>
          </div>
        </div>

        <div class="step-actions">
          <a-button 
            type="primary" 
            @click="startAnalysis" 
            :disabled="selectedChapterIds.length === 0"
          >
            开始智能分析
          </a-button>
        </div>
      </div>

      <!-- 步骤2: 分析进行中和结果，或环境音匹配 -->
      <div v-if="currentStep === 1" class="analysis-step">
        <div v-if="analyzing" class="analyzing-state">
          <a-spin size="large">
            <template #indicator>
              <BulbOutlined style="font-size: 24px" spin />
            </template>
          </a-spin>
          <h3 style="margin-top: 16px;">正在生成混音配置...</h3>
          <p>AI正在分析章节内容，生成环境音混音参数和时间轴配置</p>
          <a-progress :percent="analysisProgress" status="active" />
        </div>

        <div v-if="analysisResult && !analyzing" class="analysis-result">
          <h3>混音配置方案</h3>
          
          <!-- 分析摘要 -->
          <a-card title="配置摘要" style="margin-bottom: 16px;">
            <a-descriptions :column="2" size="small">
              <a-descriptions-item label="总轨道数">{{ analysisResult.total_tracks || analysisResult.total_scenes || 0 }}</a-descriptions-item>
              <a-descriptions-item label="分析模式">{{ analysisResult.llm_provider || '章节分析' }}</a-descriptions-item>
              <a-descriptions-item label="总时长">{{ analysisResult.total_duration || 0 }}秒</a-descriptions-item>
              <a-descriptions-item label="章节数">{{ analysisResult.chapters_analyzed || 1 }}</a-descriptions-item>
            </a-descriptions>
            
            <div v-if="analysisResult.narrative_analysis" style="margin-top: 16px;">
              <a-tag color="blue">{{ analysisResult.narrative_analysis.genre || '未知体裁' }}</a-tag>
              <a-tag color="green">{{ analysisResult.narrative_analysis.pace || '中等节奏' }}</a-tag>
              <span style="margin-left: 8px; color: #666;">
                {{ analysisResult.narrative_analysis.emotional_arc }}
              </span>
            </div>
          </a-card>

          <!-- 环境音轨道列表 -->
          <a-card title="混音时间轴">
            <template v-if="analysisResult.chapters && analysisResult.chapters.length > 0">
              <!-- 新的章节级分析结果格式 -->
              <div v-for="(chapter, chapterIndex) in analysisResult.chapters" :key="chapterIndex" class="chapter-tracks">
                <a-divider v-if="chapterIndex > 0" />
                <h4 style="margin-bottom: 16px;">
                  {{ chapter.chapter_info?.chapter_title || `第${chapter.chapter_info?.chapter_number}章` }}
                  <a-tag color="blue" style="margin-left: 8px;">
                    {{ (chapter.analysis_result?.environment_tracks || []).length }} 个轨道
                  </a-tag>
                </h4>
                
                <div class="tracks-list">
                  <div
                    v-for="(track, index) in chapter.analysis_result?.environment_tracks || []"
                    :key="`${chapterIndex}-${index}`"
                    class="track-item"
                  >
                    <div class="track-header">
                      <h5>轨道 {{ index + 1 }}</h5>
                      <a-tag :color="getIntensityColor(track.intensity_level)">{{ track.intensity_level || '中等' }}</a-tag>
                    </div>
                    <div class="track-details">
                      <a-space>
                        <a-tag>🕐 {{ track.start_time }}s - {{ (track.end_time || (track.start_time + track.duration)) }}s</a-tag>
                        <a-tag>⏱️ {{ track.duration }}s</a-tag>
                        <a-tag>📝 {{ track.scene_description || '环境音轨道' }}</a-tag>
                      </a-space>
                    </div>
                    <div v-if="track.environment_keywords && track.environment_keywords.length > 0" class="track-keywords">
                      <strong style="margin-right: 8px;">关键词:</strong>
                      <a-tag
                        v-for="keyword in track.environment_keywords"
                        :key="keyword"
                        size="small"
                        color="blue"
                      >
                        {{ keyword }}
                      </a-tag>
                    </div>
                  </div>
                </div>
              </div>
              
              <!-- 总计统计 -->
              <a-divider />
              <div class="total-stats">
                <a-space>
                  <a-statistic title="总章节数" :value="analysisResult.chapters_analyzed || analysisResult.chapters.length" />
                  <a-statistic title="总轨道数" :value="analysisResult.total_tracks" />
                  <a-statistic title="总时长" :value="analysisResult.total_duration" suffix="秒" />
                </a-space>
              </div>
            </template>
          </a-card>

          <div class="step-actions" style="margin-top: 16px;">
            <a-space>
              <a-button @click="currentStep = 0">重新分析</a-button>
              <a-button type="primary" @click="proceedToConfig">
                下一步：确认配置
              </a-button>
            </a-space>
          </div>
        </div>


      </div>

      <!-- 步骤3: 确认配置 -->
      <div v-if="currentStep === 2" class="analysis-step">
        <h3>📝 确认混音配置</h3>
        <p style="color: #666; margin-bottom: 16px;">确认混音配置参数并保存配置</p>

        <!-- 配置摘要 -->
        <a-card title="配置总览" style="margin-bottom: 16px;">
          <a-descriptions :column="2" size="small">
            <a-descriptions-item label="选择章节">{{ selectedChapterIds.length }} 个章节</a-descriptions-item>
            <a-descriptions-item label="总轨道数">{{ analysisResult?.total_tracks || 0 }}</a-descriptions-item>
            <a-descriptions-item label="预估时长">{{ analysisResult?.total_duration || 0 }} 秒</a-descriptions-item>
            <a-descriptions-item label="配置状态">{{ configSaved ? '已保存' : '未保存' }}</a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 混音参数配置 -->
        <a-card title="混音参数" style="margin-bottom: 16px;">
          <a-form layout="vertical">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="环境音总音量">
                  <a-slider 
                    v-model:value="mixingConfig.environmentVolume" 
                    :min="0" 
                    :max="1" 
                    :step="0.1"
                    :marks="{ 0: '静音', 0.5: '中等', 1: '最大' }"
                  />
                  <span>{{ (mixingConfig.environmentVolume * 100).toFixed(0) }}%</span>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="语音音量">
                  <a-slider 
                    v-model:value="mixingConfig.voiceVolume" 
                    :min="0" 
                    :max="1" 
                    :step="0.1"
                    :marks="{ 0: '静音', 0.5: '中等', 1: '最大' }"
                  />
                  <span>{{ (mixingConfig.voiceVolume * 100).toFixed(0) }}%</span>
                </a-form-item>
              </a-col>
            </a-row>
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="淡入时间 (秒)">
                  <a-input-number 
                    v-model:value="mixingConfig.fadeInDuration" 
                    :min="0" 
                    :max="10" 
                    :step="0.5"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="淡出时间 (秒)">
                  <a-input-number 
                    v-model:value="mixingConfig.fadeOutDuration" 
                    :min="0" 
                    :max="10" 
                    :step="0.5"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </a-card>

        <!-- 输出格式配置 -->
        <a-card title="输出格式" style="margin-bottom: 16px;">
          <a-form layout="vertical">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="文件格式">
                  <a-select v-model:value="mixingConfig.outputFormat" style="width: 100%">
                    <a-select-option value="wav">WAV (无损)</a-select-option>
                    <a-select-option value="mp3">MP3 (压缩)</a-select-option>
                    <a-select-option value="flac">FLAC (无损压缩)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="采样率">
                  <a-select v-model:value="mixingConfig.sampleRate" style="width: 100%">
                    <a-select-option value="44100">44.1 kHz (CD质量)</a-select-option>
                    <a-select-option value="48000">48 kHz (专业)</a-select-option>
                    <a-select-option value="96000">96 kHz (高保真)</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </a-card>

        <!-- 保存状态提示 -->
        <a-alert
          v-if="configSaved"
          message="配置已保存"
          description="混音配置已成功保存到数据库，可以开始混音制作"
          type="success"
          show-icon
          style="margin-bottom: 16px;"
        />

        <div class="step-actions">
          <a-space>
            <a-button @click="currentStep = 1">返回分析</a-button>
            <a-button @click="saveConfig" :loading="saving">
              {{ configSaved ? '重新保存配置' : '保存配置' }}
            </a-button>
            <a-button 
              type="primary" 
              @click="startMixing" 
              :disabled="!configSaved"
              :loading="startingMixing"
            >
              开始混音
            </a-button>
          </a-space>
        </div>
      </div>

      <!-- 步骤4: 开始混音 -->
      <div v-if="currentStep === 3" class="start-step">
        <h3>🚀 开始环境混音</h3>
        <p style="color: #666; margin-bottom: 16px;">确认配置并启动环境混音生成</p>

        <!-- 配置确认 -->
        <a-card title="配置确认" style="margin-bottom: 16px;">
          <a-descriptions :column="2" size="small">
            <a-descriptions-item label="总环境轨道">{{ analysisResult?.total_tracks || 0 }}个</a-descriptions-item>
            <a-descriptions-item label="匹配音效">{{ matchingResult?.matched_count || 0 }}个</a-descriptions-item>
            <a-descriptions-item label="新生成音效">{{ batchProgress.completed || 0 }}个</a-descriptions-item>
            <a-descriptions-item label="环境音音量">{{ (mixingConfig.environmentVolume * 100).toFixed(0) }}%</a-descriptions-item>
            <a-descriptions-item label="语音音量">{{ (mixingConfig.voiceVolume * 100).toFixed(0) }}%</a-descriptions-item>
            <a-descriptions-item label="输出格式">{{ mixingConfig.outputFormat.toUpperCase() }}</a-descriptions-item>
            <a-descriptions-item label="采样率">{{ (mixingConfig.sampleRate / 1000).toFixed(1) }} kHz</a-descriptions-item>
            <a-descriptions-item label="高级功能">{{ mixingConfig.advancedOptions.length }}项</a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 预计时间 -->
        <a-card title="预计信息" style="margin-bottom: 16px;">
          <a-alert
            :message="`预计处理时间：${estimatedTime}分钟`"
            :description="`将处理 ${analysisResult?.total_tracks || 0} 个环境音轨道，总时长 ${analysisResult?.total_duration || 0} 秒`"
            type="info"
            show-icon
          />
        </a-card>

        <div class="step-actions">
          <a-button @click="currentStep = 2">
            <template #icon><LeftOutlined /></template>
            上一步
          </a-button>
          <a-button 
            type="primary" 
            size="large"
            @click="startMixing"
            :loading="starting"
          >
            <template #icon><PlayCircleOutlined /></template>
            开始环境混音
          </a-button>
        </div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { message, notification } from 'ant-design-vue'
import {
  SearchOutlined, BulbOutlined, ReloadOutlined, 
  LeftOutlined, LinkOutlined, PlayCircleOutlined,
  SwapOutlined, SoundOutlined
} from '@ant-design/icons-vue'

import api from '@/api'
import { booksAPI, chaptersAPI } from '@/api'
import { getAudioService } from '@/utils/audioService'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:visible', 'complete', 'start-mixing'])

// 响应式数据
const currentStep = ref(0)
const analyzing = ref(false)
const matching = ref(false)
const generatingPrompts = ref(false)
const starting = ref(false)
const saving = ref(false)
const startingMixing = ref(false)
const configSaved = ref(false)
const analysisProgress = ref(0)
const matchingProgress = ref(0)
const loadingChapters = ref(false)
const bookLoading = ref(false)
const chapterLoading = ref(false)

const analysisOptions = ref(['include_emotion', 'precise_timing'])
const selectedBook = ref(null)
const selectedChapterIds = ref([])
const books = ref([])
const chapters = ref([])
const analyzedChapters = ref([])

const analysisResult = ref(null)
const matchingResult = ref(null)
const smartPrompts = ref(null)
const generationLogs = ref([])

const batchProgress = reactive({
  total: 0,
  completed: 0,
  processing: 0,
  failed: 0,
  status: 'normal',
  currentTask: null
})

// 混音配置
const mixingConfig = reactive({
  environmentVolume: 0.3,
  voiceVolume: 0.7,
  fadeInDuration: 1.0,
  fadeOutDuration: 1.0,
  outputFormat: 'wav',
  sampleRate: 44100,
  advancedOptions: ['crossfade', 'normalize']
})

// 计算属性
const estimatedTime = computed(() => {
  const baseTime = 5 // 基础混音时间
  const tracks = analysisResult.value?.total_tracks || 0
  return Math.ceil(baseTime + tracks * 0.5)
})

const hasSelectedPrompts = computed(() => {
  return smartPrompts.value?.smart_prompts?.some(p => p.selected) || false
})

const selectedPromptsCount = computed(() => {
  return smartPrompts.value?.smart_prompts?.filter(p => p.selected).length || 0
})

// 方法
const getIntensityColor = (intensity) => {
  const colors = {
    '低': 'green',
    '中等': 'blue',
    '高': 'orange',
    '极高': 'red'
  }
  return colors[intensity] || 'default'
}

const getPriorityColor = (priority) => {
  const colors = {
    '高': 'red',
    '中': 'orange',
    '低': 'green'
  }
  return colors[priority] || 'default'
}

const loadBooks = async () => {
  try {
    bookLoading.value = true
    // 使用正确的API调用方式
    const response = await booksAPI.getBooks()
    
    console.log('Books API response:', response)
    
    // 兼容多种响应格式
    let booksData = []
    if (response?.data?.success && response.data.data) {
      // 格式1: {data: {success: true, data: [...]}}
      booksData = response.data.data
    } else if (response?.data && Array.isArray(response.data)) {
      // 格式2: {data: [...]}
      booksData = response.data
    } else if (response?.success && response.data) {
      // 格式3: {success: true, data: [...]}
      booksData = response.data
    } else if (Array.isArray(response)) {
      // 格式4: [...]
      booksData = response
    }
    
    console.log('Processed books data:', booksData)
    books.value = booksData || []
  } catch (error) {
    console.error('加载书籍失败:', error)
    notification.error({
      message: '加载失败',
      description: '无法加载书籍列表，请稍后重试'
    })
    books.value = []
  } finally {
    bookLoading.value = false
  }
}

const loadChapters = async () => {
  if (!selectedBook.value) {
    chapters.value = []
    return
  }
  
  try {
    chapterLoading.value = true
    // 使用正确的API调用方式
    const response = await chaptersAPI.getChapters({ book_id: selectedBook.value })
    
    console.log('Chapters API response:', response)
    
    // 兼容多种响应格式
    let chaptersData = []
    if (response?.data?.success && response.data.data) {
      // 格式1: {data: {success: true, data: [...]}}
      chaptersData = response.data.data
    } else if (response?.data && Array.isArray(response.data)) {
      // 格式2: {data: [...]}
      chaptersData = response.data
    } else if (response?.success && response.data) {
      // 格式3: {success: true, data: [...]}
      chaptersData = response.data
    } else if (Array.isArray(response)) {
      // 格式4: [...]
      chaptersData = response
    }
    
    console.log('Processed chapters data:', chaptersData)
    chapters.value = chaptersData || []
  } catch (error) {
    console.error('加载章节失败:', error)
    notification.error({
      message: '加载失败',
      description: '无法加载章节列表，请稍后重试'
    })
    chapters.value = []
  } finally {
    chapterLoading.value = false
  }
}

const startAnalysis = async () => {
  try {
    analyzing.value = true
    analysisProgress.value = 0
    currentStep.value = 1
    
    // 模拟分析进度
    const progressInterval = setInterval(() => {
      if (analysisProgress.value < 90) {
        analysisProgress.value += Math.random() * 20
      }
    }, 500)

    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 3000))
    
    clearInterval(progressInterval)
    analysisProgress.value = 100

    // 模拟分析结果
    analysisResult.value = {
      total_tracks: 15,
      total_duration: 2400,
      chapters_analyzed: selectedChapterIds.value.length,
      chapters: selectedChapterIds.value.map((id, index) => ({
        chapter_info: {
          chapter_title: `第${index + 1}章`,
          chapter_number: index + 1
        },
        analysis_result: {
          environment_tracks: Array.from({ length: Math.floor(Math.random() * 5) + 2 }, (_, i) => ({
            start_time: i * 180,
            duration: 120 + Math.random() * 60,
            scene_description: `场景描述 ${i + 1}`,
            environment_keywords: ['关键词1', '关键词2'],
            intensity_level: ['低', '中等', '高'][i % 3]
          }))
        }
      }))
    }

    message.success('章节分析完成！')
    
  } catch (error) {
    console.error('章节分析失败:', error)
    message.error('章节分析失败: ' + error.message)
  } finally {
    analyzing.value = false
  }
}

const proceedToMatching = async () => {
  matching.value = true
  matchingProgress.value = 0
  
  // 模拟匹配进度
  const progressInterval = setInterval(() => {
    if (matchingProgress.value < 90) {
      matchingProgress.value += Math.random() * 15
    }
  }, 300)

  await new Promise(resolve => setTimeout(resolve, 2000))
  
  clearInterval(progressInterval)
  matchingProgress.value = 100
  matching.value = false

  matchingResult.value = {
    matched_count: 10,
    need_generation_count: 5,
    accuracy: 85
  }

  message.success('环境音匹配完成！')
}

const proceedToConfig = () => {
  currentStep.value = 2
}

const saveConfig = async () => {
  try {
    saving.value = true
    
    // 构建配置数据
    const configData = {
      chapters: selectedChapterIds.value,
      book_id: selectedBook.value,
      analysis_result: analysisResult.value,
      mixing_config: mixingConfig,
      created_at: new Date().toISOString()
    }
    
    // 模拟保存API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    configSaved.value = true
    message.success('混音配置已保存！')
    
  } catch (error) {
    console.error('保存配置失败:', error)
    message.error('保存配置失败: ' + error.message)
  } finally {
    saving.value = false
  }
}



const proceedToGeneration = async () => {
  generatingPrompts.value = true
  currentStep.value = 2
  
  await new Promise(resolve => setTimeout(resolve, 1500))
  
  smartPrompts.value = {
    soundscape_recommendation: {
      primary_elements: ['鸟鸣', '风声', '脚步声'],
      secondary_elements: ['水声', '叶片摩擦'],
      overall_duration: 2400,
      ambient_layers: ['前景', '中景', '背景']
    },
    smart_prompts: Array.from({ length: 5 }, (_, i) => ({
      title: `环境音 ${i + 1}`,
      prompt: `gentle wind through trees, birds chirping softly ${i + 1}`,
      duration: 120,
      priority: ['高', '中', '低'][i % 3],
      selected: true,
      dynamic_elements: ['风声变化', '鸟鸣节奏'],
      fade_settings: { fade_in: 2, fade_out: 2 },
      generation_tips: { complexity: '中等' }
    }))
  }
  
  generatingPrompts.value = false
}

const selectAllPrompts = () => {
  if (smartPrompts.value?.smart_prompts) {
    smartPrompts.value.smart_prompts.forEach(prompt => {
      prompt.selected = true
    })
  }
}

const selectNonePrompts = () => {
  if (smartPrompts.value?.smart_prompts) {
    smartPrompts.value.smart_prompts.forEach(prompt => {
      prompt.selected = false
    })
  }
}

const startBatchGeneration = async () => {
  currentStep.value = 3
  
  const selectedPrompts = smartPrompts.value.smart_prompts.filter(p => p.selected)
  batchProgress.total = selectedPrompts.length
  batchProgress.completed = 0
  batchProgress.status = 'active'
  
  for (let i = 0; i < selectedPrompts.length; i++) {
    batchProgress.currentTask = {
      title: selectedPrompts[i].title,
      progress: 0
    }
    
    // 模拟单个任务进度
    for (let progress = 0; progress <= 100; progress += 20) {
      batchProgress.currentTask.progress = progress
      await new Promise(resolve => setTimeout(resolve, 200))
    }
    
    batchProgress.completed++
    generationLogs.value.push({
      time: new Date().toLocaleTimeString(),
      message: `${selectedPrompts[i].title} 生成完成`,
      type: 'success'
    })
  }
  
  batchProgress.status = 'success'
  batchProgress.currentTask = null
  message.success('批量生成完成！')
}

const proceedToMixing = () => {
  currentStep.value = 4
}

const cancelBatchGeneration = () => {
  batchProgress.status = 'exception'
  message.warning('批量生成已取消')
}

const startMixing = async () => {
  try {
    starting.value = true
    
    // 构建简化的混音配置（新4步流程）
    const mixingData = {
      chapters: selectedChapterIds.value,
      book_id: selectedBook.value,
      analysis_result: analysisResult.value,
      mixing_config: mixingConfig,
      options: analysisOptions.value,
      project_id: `mixing_${Date.now()}`
    }

    message.success('环境混音任务已启动！')
    
    // 触发开始混音事件
    emit('start-mixing', mixingData)
    emit('update:visible', false)
    
  } catch (error) {
    console.error('启动混音失败:', error)
    message.error('启动混音失败: ' + error.message)
  } finally {
    starting.value = false
  }
}

// 监听visible变化，重置状态
watch(() => props.visible, (newVal) => {
  if (newVal) {
    loadBooks()
  } else {
    // 重置所有状态
    currentStep.value = 0
    analyzing.value = false
    matching.value = false
    generatingPrompts.value = false
    starting.value = false
    saving.value = false
    startingMixing.value = false
    configSaved.value = false
    analysisResult.value = null
    matchingResult.value = null
    smartPrompts.value = null
    selectedBook.value = null
    selectedChapterIds.value = []
    Object.assign(batchProgress, {
      total: 0,
      completed: 0,
      processing: 0,
      failed: 0,
      status: 'normal',
      currentTask: null
    })
    generationLogs.value = []
  }
})

onMounted(() => {
  loadBooks()
})
</script>

<style scoped>
.environment-mixing-drawer {
  --primary-color: #1890ff;
  --success-color: #52c41a;
  --warning-color: #fa8c16;
}

.mixing-analysis-content {
  padding: 0;
}

.steps-container {
  margin-bottom: 32px;
  padding: 20px;
  background: linear-gradient(135deg, #f0f9ff 0%, #e0f2fe 100%);
  border-radius: 8px;
}

.analysis-step, .config-step, .start-step {
  min-height: 400px;
}

.analysis-step h3, .config-step h3, .start-step h3 {
  color: var(--primary-color);
  margin-bottom: 8px;
  font-weight: 600;
}

.analyzing-state, .matching-state, .generating-state {
  text-align: center;
  padding: 60px 20px;
}

.chapter-tracks {
  margin-bottom: 24px;
}

.tracks-list {
  max-height: 300px;
  overflow-y: auto;
}

.track-item {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  background: #fafafa;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.track-header h5 {
  margin: 0;
  color: var(--primary-color);
}

.track-keywords {
  margin-top: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 4px;
}

.prompts-list {
  max-height: 500px;
  overflow-y: auto;
}

.prompt-item {
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 16px;
  margin-bottom: 16px;
  background: #fafafa;
}

.prompt-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.prompt-header h4 {
  margin: 0;
  color: var(--primary-color);
}

.prompt-content {
  margin-bottom: 12px;
}

.prompt-features, .prompt-settings {
  margin-top: 8px;
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
}

.generation-logs {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 8px;
}

.log-item {
  display: flex;
  margin-bottom: 4px;
  font-size: 12px;
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
  color: var(--success-color);
}

.step-actions {
  margin-top: 32px;
  text-align: right;
  padding-top: 20px;
  border-top: 1px solid #f0f0f0;
}

.step-actions .ant-btn {
  margin-left: 12px;
}

.total-stats {
  text-align: center;
  padding: 16px;
}

/* 暗黑模式适配 */
@media (prefers-color-scheme: dark) {
  .steps-container {
    background: linear-gradient(135deg, #001529 0%, #002140 100%);
  }
  
  .track-item, .prompt-item {
    background: #1f1f1f;
    border-color: #434343;
  }
  
  .generation-logs {
    background: #1f1f1f;
    border-color: #434343;
  }
}
</style> 