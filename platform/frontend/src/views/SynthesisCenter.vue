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

          <!-- 自动匹配规则区域 -->
          <a-card title="🤖 自动匹配规则" :bordered="false" class="analysis-card" style="margin-bottom: 16px;">
            <div class="debug-controls">
              <a-space>
                <a-button 
                  type="primary" 
                  @click="testMockAnalysis"
                  :loading="mockAnalyzing"
                >
                  🎯 执行自动匹配
                </a-button>
                <a-button 
                  v-if="mockResult"
                  @click="applyMockResult"
                  :loading="applyingMock"
                >
                  ✅ 应用匹配结果
                </a-button>
                <a-button 
                  v-if="mockResult"
                  @click="clearMockResult"
                  type="dashed"
                >
                  🗑️ 清空结果
                </a-button>
              </a-space>
            </div>
            
            <!-- 使用新的自动匹配显示组件 -->
            <IntelligentAnalysisDisplay
              v-if="mockResult"
              :analysisResult="mockResult"
              :availableVoices="availableVoices"
              :voiceMapping="characterVoiceMapping"
              :previewLoading="previewLoading"
              :currentPlayingVoice="currentPlayingVoice"
              @updateVoiceMapping="updateVoiceMapping"
              @playVoicePreview="playVoicePreview"
            />
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
                <a-button
                  type="primary"
                  size="large"
                  block
                  :disabled="!canStartSynthesis"
                  :loading="synthesisStarting"
                  @click="startSynthesis"
                >
                  🎯 开始合成
                </a-button>

                <a-button
                  v-if="project.status === 'processing'"
                  size="large"
                  block
                  @click="pauseSynthesis"
                  style="margin-top: 8px;"
                >
                  ⏸️ 暂停合成
                </a-button>

                <a-button
                  v-if="project.status === 'paused'"
                  type="primary"
                  size="large"
                  block
                  @click="resumeSynthesis"
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

              <!-- 下载按钮 -->
              <div v-if="project.status === 'completed'" class="download-section">
                <a-button
                  type="primary"
                  size="large"
                  block
                  @click="downloadAudio"
                >
                  📥 下载音频
                </a-button>
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import { message } from 'ant-design-vue'
import { readerAPI, charactersAPI, intelligentAnalysisAPI } from '@/api'
import IntelligentAnalysisDisplay from '@/components/IntelligentAnalysisDisplay.vue'

const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(true)
const synthesisStarting = ref(false)
const project = ref(null)
const detectedCharacters = ref([])
const availableVoices = ref([])
const characterVoiceMapping = reactive({})
const progressTimer = ref(null)
const previewLoading = ref(null)
const currentPlayingVoice = ref(null)
const currentAudio = ref(null)
const checkingService = ref(false)

// Mock分析相关
const mockAnalyzing = ref(false)
const applyingMock = ref(false)
const mockResult = ref(null)

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

const allCharactersConfigured = computed(() => {
  // 如果有智能分析结果，基于智能分析的角色
  if (mockResult.value?.characters) {
    return mockResult.value.characters.every(char => 
      characterVoiceMapping[char.name]
    )
  }
  // 否则基于原始检测的角色
  return detectedCharacters.value.every(char => 
    characterVoiceMapping[char.name]
  )
})

const canStartSynthesis = computed(() => {
  const hasCharacters = mockResult.value?.characters?.length > 0 || detectedCharacters.value.length > 0
  return allCharactersConfigured.value && 
         project.value?.status !== 'processing' &&
         hasCharacters
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
  const hasCharacters = mockResult.value?.characters?.length > 0 || detectedCharacters.value.length > 0
  
  if (!hasCharacters) {
    return '请先进行自动匹配'
  }
  if (!allCharactersConfigured.value) {
    return '请为所有角色配置声音'
  }
  return '可以开始合成'
}

// Mock分析方法
const testMockAnalysis = async () => {
  if (!project.value?.id) {
    message.error('项目信息不完整')
    return
  }
  
  mockAnalyzing.value = true
  try {
    console.log('=== 开始自动匹配规则测试 ===')
    const response = await intelligentAnalysisAPI.analyzeProject(project.value.id)
    
    if (response.data.success) {
      mockResult.value = response.data.data
      message.success('自动匹配完成！AI已生成可直接执行的合成计划')
      console.log('自动匹配结果:', mockResult.value)
    } else {
      message.error('自动匹配失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('自动匹配错误:', error)
    message.error('自动匹配失败: ' + error.message)
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
    console.log('=== 应用自动匹配结果 ===')
    const response = await intelligentAnalysisAPI.applyAnalysis(project.value.id, mockResult.value)
    
    if (response.data.success) {
      message.success('匹配结果已应用！')
      console.log('应用结果:', response.data.applied_mapping)
      
      // 使用智能分析的角色结果更新角色配置
      updateCharactersFromAnalysis()
      
      // 刷新项目数据以显示新的角色映射
      await loadProject()
    } else {
      message.error('应用失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('应用自动匹配结果错误:', error)
    message.error('应用失败: ' + error.message)
  } finally {
    applyingMock.value = false
  }
}

// 从智能分析结果更新角色配置
const updateCharactersFromAnalysis = () => {
  if (!mockResult.value?.characters) return
  
  // 清空现有角色数据
  detectedCharacters.value = []
  
  // 使用智能分析的角色数据，添加简单的示例文本
  detectedCharacters.value = mockResult.value.characters.map(char => ({
    name: char.name,
    character_id: char.name, // 使用名称作为ID
    count: 1,
    samples: [getCharacterSampleText(char.name)],
    voice_id: char.voice_id,
    voice_name: char.voice_name
  }))
  
  // 只初始化空的映射，让用户可以看到AI推荐并手动选择
  // 不自动应用AI推荐，避免混淆
  console.log('已更新角色配置:', {
    characters: detectedCharacters.value,
    aiRecommendations: mockResult.value.characters.map(char => ({
      name: char.name,
      recommendedVoiceId: char.voice_id,
      recommendedVoiceName: char.voice_name
    }))
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
  message.info('匹配结果已清空')
}

// 加载项目详情
const loadProject = async () => {
  try {
    const projectId = route.params.projectId
    const response = await readerAPI.getProjectDetail(projectId)
    
    if (response.data.success) {
      project.value = response.data.data
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

// 更新声音映射
const updateVoiceMapping = async (characterName, voiceId) => {
  try {
    // 更新本地映射
    if (voiceId) {
      characterVoiceMapping[characterName] = voiceId
    } else {
      delete characterVoiceMapping[characterName]
    }
    
    // 保存到后端
    await readerAPI.updateProject(project.value.id, {
      name: project.value.name,
      description: project.value.description || '',
      character_mapping: JSON.stringify(characterVoiceMapping)
    })
    message.success('角色配置已保存')
  } catch (error) {
    console.error('保存角色配置失败:', error)
    message.error('保存角色配置失败')
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

    // 简化的试听文本
    const previewText = sampleText.slice(0, 30) || '你好，这是声音试听测试。'

    // 发送请求到后端API，增加超时控制
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 90000) // 90秒超时

    // 构建试听请求，使用后端API而不是直接调用TTS
    const testFormData = new FormData()
    testFormData.append('text', previewText)
    testFormData.append('time_step', '15')
    testFormData.append('p_weight', '1.0')
    testFormData.append('t_weight', '1.0')

    const response = await fetch(`/api/characters/${selectedVoice.id}/test`, {
      method: 'POST',
      body: testFormData,
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (response.ok) {
      // 后端API返回JSON格式，包含audioUrl
      const result = await response.json()
      
      if (result.success && result.audioUrl) {
        // 构建完整的音频URL
        const audioUrl = result.audioUrl.startsWith('http') ? result.audioUrl : result.audioUrl
        
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
        throw new Error(result.message || '后端API返回错误')
      }
    } else {
      const errorText = await response.text()
      console.error('后端API错误:', errorText)
      
      if (response.status === 500) {
        throw new Error('后端服务内部错误，可能是TTS服务异常')
      } else {
        throw new Error(`试听请求失败: ${response.status}`)
      }
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
    const response = await readerAPI.startGeneration(project.value.id, {
      parallel_tasks: synthesisConfig.parallelTasks
    })
    
    if (response.data.success) {
      message.success('合成任务已启动')
      project.value.status = 'processing'
      startProgressPolling()
    }
  } catch (error) {
    console.error('启动合成失败:', error)
    message.error('启动合成失败')
  } finally {
    synthesisStarting.value = false
  }
}

// 暂停合成
const pauseSynthesis = async () => {
  try {
    await readerAPI.pauseGeneration(project.value.id)
    message.success('合成已暂停')
    project.value.status = 'paused'
    stopProgressPolling()
  } catch (error) {
    console.error('暂停合成失败:', error)
    message.error('暂停合成失败')
  }
}

// 继续合成
const resumeSynthesis = async () => {
  try {
    await readerAPI.resumeGeneration(project.value.id, {
      parallel_tasks: synthesisConfig.parallelTasks
    })
    message.success('合成已继续')
    project.value.status = 'processing'
    startProgressPolling()
  } catch (error) {
    console.error('继续合成失败:', error)
    message.error('继续合成失败')
  }
}

// 下载音频
const downloadAudio = async () => {
  try {
    const response = await readerAPI.downloadAudio(project.value.id)
    // 处理文件下载
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value.name}_final.wav`
    link.click()
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

// 检查TTS服务状态
const checkTTSService = async () => {
  checkingService.value = true
  try {
    const response = await fetch('/api/v1/tts/health', {
      method: 'GET',
      timeout: 10000
    })
    
    if (response.ok) {
      const data = await response.json()
      if (data.model_loaded) {
        message.success('TTS服务正常运行中')
      } else {
        message.warning('TTS服务已启动但模型未加载')
      }
    } else {
      throw new Error(`服务响应错误: ${response.status}`)
    }
  } catch (error) {
    console.error('TTS服务检查失败:', error)
    
    if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
      message.error('无法连接到TTS服务，请检查服务是否启动 (端口:7929)')
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
        const progress = response.data.progress
        project.value.statistics = progress.statistics
        project.value.status = progress.status
        
        // 重置错误计数
        errorCount = 0
        
        // 检查停止条件
        const shouldStop = progress.status === 'completed' || 
                          progress.status === 'failed' ||
                          progress.status === 'cancelled' ||
                          // 如果没有段落在处理且没有待处理的段落，也停止轮询
                          (progress.statistics.processing === 0 && 
                           progress.statistics.pending === 0 && 
                           progress.statistics.total > 0)
        
        if (shouldStop) {
          stopProgressPolling()
          if (progress.status === 'completed') {
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

// 生命周期
onMounted(async () => {
  await loadProject()
  await loadVoices()
  
  // 如果正在处理中，启动进度轮询
  if (project.value?.status === 'processing') {
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
})

// 浏览器刷新/关闭前的清理
window.addEventListener('beforeunload', () => {
  stopProgressPolling()
})
</script>

<style scoped>
.synthesis-center-container {
  padding: 24px;
  background: #f5f5f5;
  min-height: 100vh;
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
</style>