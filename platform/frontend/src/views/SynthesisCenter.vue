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
                  type="dashed"
                  @click="showJsonTestModal"
                  :disabled="mockAnalyzing"
                >
                  🧪 测试JSON
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

                <!-- 暂停合成按钮 - 只在处理中时显示 -->
                <a-button
                  v-if="project.status === 'processing'"
                  size="large"
                  block
                  @click="pauseSynthesis"
                  style="margin-top: 8px;"
                >
                  ⏸️ 暂停合成
                </a-button>

                <!-- 继续合成按钮 - 只在暂停时显示 -->
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
      title="🧪 JSON测试输入"
      width="800px"
      :destroyOnClose="true"
      @ok="executeJsonTest"
      @cancel="cancelJsonTest"
      :okButtonProps="{ loading: jsonTestExecuting, disabled: !jsonTestContent.trim() }"
      okText="自动执行匹配"
      cancelText="取消"
    >
      <div class="json-test-container">
        <div class="json-description">
          <a-alert
            message="JSON格式说明"
            description="请粘贴包含project_info、characters、segments的完整JSON数据。系统将解析此JSON并应用到当前项目的角色配置中。"
            type="info"
            show-icon
            style="margin-bottom: 16px;"
          />
        </div>
        
        <a-form layout="vertical">
          <a-form-item label="JSON数据" required>
            <a-textarea
              v-model:value="jsonTestContent"
              placeholder="请粘贴您的JSON数据..."
              :rows="15"
              style="font-family: 'Consolas', 'Monaco', 'Courier New', monospace;"
            />
          </a-form-item>
          
          <a-form-item>
            <a-space>
              <a-button @click="formatJsonContent" size="small">
                🎨 格式化JSON
              </a-button>
              <a-button @click="validateJsonContent" size="small">
                ✅ 验证格式
              </a-button>
              <a-button @click="clearJsonContent" size="small" type="dashed">
                🗑️ 清空内容
              </a-button>
            </a-space>
          </a-form-item>
          
          <!-- 验证结果显示 -->
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import { message } from 'ant-design-vue'
import { readerAPI, charactersAPI, intelligentAnalysisAPI, systemAPI } from '@/api'
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

// JSON测试相关
const jsonTestModalVisible = ref(false)
const jsonTestContent = ref('')
const jsonTestExecuting = ref(false)
const jsonValidationResult = ref(null)

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

const allCharactersConfigured = computed(() => {
  // 如果有智能分析结果，基于智能分析的角色
  if (mockResult.value?.characters) {
    return mockResult.value.characters.every(char => {
      // 检查用户是否手动选择了声音，如果没有，则检查AI是否推荐了声音
      const userSelected = characterVoiceMapping[char.name]
      const aiRecommended = char.voice_id
      return userSelected || aiRecommended
    })
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
  
  // 自动应用AI推荐的角色映射到characterVoiceMapping
  // 这样在合成时就能找到正确的voice_id
  mockResult.value.characters.forEach(char => {
    if (char.voice_id) {
      characterVoiceMapping[char.name] = char.voice_id
    }
  })
  
  console.log('已更新角色配置:', {
    characters: detectedCharacters.value,
    characterVoiceMapping: characterVoiceMapping,
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
      
      // 如果项目处于processing状态或有segments，加载统计信息
      if (project.value.status === 'processing' || project.value.segments?.length > 0) {
        const progressResponse = await readerAPI.getProgress(projectId)
        if (progressResponse.data.success) {
          const progress = progressResponse.data.progress
          // 更新统计信息，映射字段名
          project.value.statistics = {
            totalSegments: progress.statistics.total,
            completedSegments: progress.statistics.completed,
            failedSegments: progress.statistics.failed,
            processingSegments: progress.statistics.processing,
            pendingSegments: progress.statistics.pending
          }
          project.value.status = progress.status
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

    // 使用统一的API调用替代直接fetch
    const testParams = {
      text: sampleText || '这是声音预览测试',
      time_step: 20,
      p_weight: 1.0,
      t_weight: 1.0
    }
    
    console.log('=== 声音试听调试信息 ===')
    console.log('voiceId:', selectedVoice.id)
    console.log('voiceName:', selectedVoice.name)
    console.log('sampleText:', sampleText)
    console.log('testParams:', testParams)
    console.log('========================')
    
    const response = await charactersAPI.testVoiceSynthesis(selectedVoice.id, testParams)
    
    console.log('=== API响应调试信息 ===')
    console.log('response.data:', response.data)
    console.log('audioUrl:', response.data?.audioUrl)
    console.log('=====================')

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

// 直接对JSON数据进行TTS合成
const synthesizeJsonDirectly = async (synthesisPlans) => {
  try {
    message.success('开始JSON测试数据合成')
    project.value.status = 'processing'
    
    // 验证合成计划数据
    if (!Array.isArray(synthesisPlans) || synthesisPlans.length === 0) {
      throw new Error('合成计划数据为空或格式错误')
    }
    
    console.log('=== 合成计划验证 ===')
    console.log('合成计划数量:', synthesisPlans.length)
    console.log('前3个计划样本:', synthesisPlans.slice(0, 3))
    
    // 预检查所有计划的必要字段
    const invalidPlans = []
    synthesisPlans.forEach((plan, index) => {
      const voiceId = plan.voice_id || plan.voiceId || plan.character_id || plan.speaker_id
      if (!voiceId) {
        invalidPlans.push(`第${index + 1}段缺少voice_id`)
      }
      if (!plan.text || plan.text.trim() === '') {
        invalidPlans.push(`第${index + 1}段缺少文本内容`)
      }
    })
    
    if (invalidPlans.length > 0) {
      console.error('发现无效的合成计划:', invalidPlans)
      throw new Error(`数据验证失败:\n${invalidPlans.join('\n')}`)
    }
    
    // 模拟进度统计
    const totalSegments = synthesisPlans.length
    let completedSegments = 0
    
    project.value.statistics = {
      totalSegments,
      completedSegments: 0,
      failedSegments: 0,
      processingSegments: 0,
      pendingSegments: totalSegments
    }
    
    console.log(`开始合成 ${totalSegments} 个JSON段落`)
    
    // 逐个合成
    for (let i = 0; i < synthesisPlans.length; i++) {
      const plan = synthesisPlans[i]
      
      try {
        console.log(`正在合成第 ${i + 1}/${totalSegments} 段落:`, plan.text?.slice(0, 50))
        console.log(`段落 ${i + 1} 详细信息:`, {
          voice_id: plan.voice_id,
          voiceId: plan.voiceId,
          character: plan.character,
          speaker: plan.speaker,
          text_length: plan.text?.length
        })
        
        // 获取voice_id，优先使用直接字段
        let voiceId = plan.voice_id || plan.voiceId
        
        // 如果没有直接的voice_id，尝试从角色映射中查找
        if (!voiceId && (plan.speaker || plan.character)) {
          const characterName = plan.speaker || plan.character
          voiceId = characterVoiceMapping[characterName]
          console.log(`从角色映射中查找voice_id: ${characterName} -> ${voiceId}`)
        }
        
        if (!voiceId) {
          console.error(`第 ${i + 1} 段落缺少voice_id:`, plan)
          console.error('可用的角色映射:', characterVoiceMapping)
          throw new Error(`第 ${i + 1} 段落缺少voice_id字段。请确保JSON格式正确，每个段落都有voice_id或speaker字段`)
        }
        
        if (!plan.text || plan.text.trim() === '') {
          console.error(`第 ${i + 1} 段落缺少文本内容:`, plan)
          throw new Error(`第 ${i + 1} 段落缺少文本内容`)
        }
        
        // 调用TTS API
        const response = await charactersAPI.testVoiceSynthesis(voiceId, {
          text: plan.text,
          time_step: plan.parameters?.timeStep || 20,
          p_weight: plan.parameters?.pWeight || 1.0,
          t_weight: plan.parameters?.tWeight || 1.0
        })
        
        if (response.data?.success) {
          completedSegments++
          console.log(`第 ${i + 1} 段落合成成功`)
        } else {
          throw new Error(response.data?.message || '合成失败')
        }
        
      } catch (error) {
        console.error(`第 ${i + 1} 段落合成失败:`, error)
        console.error(`失败段落详情:`, {
          index: i + 1,
          plan: plan,
          error_message: error.message
        })
        project.value.statistics.failedSegments++
        
        // 如果是关键错误（如voice_id缺失），显示更详细的错误信息
        if (error.message.includes('voice_id') || error.message.includes('文本内容')) {
          message.error(`第 ${i + 1} 段落: ${error.message}`)
        }
      }
      
      // 更新进度
      project.value.statistics.completedSegments = completedSegments
      project.value.statistics.pendingSegments = totalSegments - completedSegments - project.value.statistics.failedSegments
      
      // 短暂等待，避免过快调用
      if (i < synthesisPlans.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 1000))
      }
    }
    
    // 完成合成
    project.value.status = 'completed'
    const failedCount = project.value.statistics.failedSegments
    
    if (failedCount === 0) {
      message.success(`JSON测试数据合成完成！成功 ${completedSegments} 个段落`)
    } else {
      message.warning(`JSON测试数据合成完成！成功 ${completedSegments} 个，失败 ${failedCount} 个段落`)
    }
    
  } catch (error) {
    console.error('JSON合成失败:', error)
    project.value.status = 'failed'
    message.error('JSON测试数据合成失败: ' + error.message)
  }
}

// 开始合成
const startSynthesis = async () => {
  synthesisStarting.value = true
  try {
    // 优先使用项目的正式生成流程，而不是JSON测试数据
    console.log('=== 启动项目正式合成流程 ===')
    const response = await readerAPI.startGeneration(project.value.id, {
      parallel_tasks: synthesisConfig.parallelTasks
    })
    
    if (response.data.success) {
      message.success('合成任务已启动')
      project.value.status = 'processing'
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
        const progress = response.data.progress
        // 映射统计数据字段名
        project.value.statistics = {
          totalSegments: progress.statistics.total,
          completedSegments: progress.statistics.completed,
          failedSegments: progress.statistics.failed,
          processingSegments: progress.statistics.processing,
          pendingSegments: progress.statistics.pending
        }
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

/* JSON测试弹窗样式 */
.json-test-container {
  max-height: 600px;
  overflow-y: auto;
}

.json-test-container .ant-textarea {
  font-size: 12px;
  line-height: 1.4;
  border-radius: 6px;
  border: 2px dashed #d9d9d9;
  transition: border-color 0.3s ease;
}

.json-test-container .ant-textarea:focus {
  border-color: #1890ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}

.validation-result {
  margin-top: 12px;
}

.json-description {
  margin-bottom: 16px;
}

.json-test-container .ant-form-item-label > label {
  font-weight: 600;
  color: #1f2937;
}
</style>