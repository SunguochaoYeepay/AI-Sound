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

          <!-- 智能分析区域 -->
          <a-card title="🤖 智能分析" :bordered="false" class="analysis-card" style="margin-bottom: 16px;">
            <div class="debug-controls">
              <a-space>
                <a-button 
                  type="primary" 
                  @click="testMockAnalysis"
                  :loading="mockAnalyzing"
                >
                  🎯 开始智能分析
                </a-button>
                <a-button 
                  v-if="mockResult"
                  @click="applyMockResult"
                  :loading="applyingMock"
                >
                  ✅ 应用分析结果
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
            
            <div v-if="mockResult" class="mock-result-display" style="margin-top: 16px;">
              <a-tabs>
                <a-tab-pane tab="🎭 检测角色" key="characters">
                  <div class="characters-preview">
                    <div 
                      v-for="character in mockResult.detected_characters" 
                      :key="character.character_id"
                      class="character-preview-item enhanced"
                    >
                      <div class="character-header">
                        <h4>{{ character.name }}</h4>
                        <div class="character-tags">
                          <a-tag :color="character.gender === 'male' ? 'blue' : 'pink'">
                            {{ character.gender === 'male' ? '男' : '女' }}
                          </a-tag>
                          <a-tag color="purple">{{ character.estimated_age }}岁</a-tag>
                          <a-tag color="green">{{ (character.confidence_score * 100).toFixed(1) }}%</a-tag>
                        </div>
                      </div>
                      
                      <div class="character-details">
                        <p><strong>性格特征:</strong> {{ character.personality_traits?.join('、') }}</p>
                        <p><strong>台词示例:</strong> {{ character.sample_dialogues?.slice(0,2).join('；') }}</p>
                      </div>
                      
                      <!-- 声音配置区域 -->
                      <div class="voice-config-section">
                        <div class="recommended-voice">
                          <span class="recommend-label">💡 AI推荐:</span>
                          <a-tag color="orange">音色ID {{ character.recommended_voice_id }}</a-tag>
                        </div>
                        
                        <div class="voice-selector-inline">
                          <a-select
                            v-model:value="characterVoiceMapping[character.name]"
                            placeholder="选择声音配置"
                            style="width: 200px;"
                            allowClear
                            @change="updateVoiceMapping"
                          >
                            <a-select-option
                              v-for="voice in availableVoices"
                              :key="voice.id"
                              :value="voice.id"
                            >
                              <div class="voice-option">
                                <span class="voice-name">{{ voice.name }}</span>
                                <a-tag size="small" :color="voice.type === 'male' ? 'blue' : 'pink'">
                                  {{ voice.type === 'male' ? '男' : '女' }}
                                </a-tag>
                                <span v-if="voice.id === character.recommended_voice_id" class="recommended-marker">🌟</span>
                              </div>
                            </a-select-option>
                          </a-select>
                          
                          <!-- 试听按钮 -->
                          <a-button
                            v-if="characterVoiceMapping[character.name]"
                            type="primary"
                            size="small"
                            :loading="previewLoading === characterVoiceMapping[character.name]"
                            @click="playVoicePreview(characterVoiceMapping[character.name], character.sample_dialogues?.[0])"
                          >
                            <template v-if="!previewLoading">
                              <span v-if="currentPlayingVoice === characterVoiceMapping[character.name]">⏸️ 停止</span>
                              <span v-else>🔊 试听</span>
                            </template>
                          </a-button>
                        </div>
                        
                        <!-- 配置状态 -->
                        <div class="config-status">
                          <a-tag v-if="characterVoiceMapping[character.name]" color="success">
                            ✅ 已配置
                          </a-tag>
                          <a-tag v-else color="warning">
                            ⚠️ 待配置
                          </a-tag>
                        </div>
                      </div>
                    </div>
                  </div>
                </a-tab-pane>
                
                <a-tab-pane tab="📝 智能分段" key="segments">
                  <div class="segments-preview">
                    <div 
                      v-for="segment in mockResult.intelligent_segments?.slice(0, 10)" 
                      :key="segment.segment_id"
                      class="segment-preview-item"
                    >
                      <div class="segment-header">
                        <span class="segment-id">#{segment.segment_id}</span>
                        <a-tag :color="getSegmentTypeColor(segment.text_type)">
                          {{ segment.text_type }}
                        </a-tag>
                        <a-tag color="blue">{{ segment.speaker }}</a-tag>
                      </div>
                      <div class="segment-text">{{ segment.text }}</div>
                    </div>
                  </div>
                </a-tab-pane>
                
                <a-tab-pane tab="🔊 音色映射" key="mapping">
                  <div class="mapping-preview">
                    <div 
                      v-for="(mapping, charId) in mockResult.voice_mapping_recommendation" 
                      :key="charId"
                      class="mapping-preview-item"
                    >
                      <h4>{{ mapping.character_name }}</h4>
                      <p><strong>主推音色ID:</strong> {{ mapping.primary_voice_id }}</p>
                      <p><strong>备选音色:</strong> {{ mapping.alternative_voice_ids?.join(', ') || '无' }}</p>
                      <div class="matching-reasons">
                        <strong>推荐理由:</strong>
                        <ul>
                          <li v-for="reason in mapping.matching_reasons" :key="reason">{{ reason }}</li>
                        </ul>
                      </div>
                    </div>
                  </div>
                </a-tab-pane>
                
                <a-tab-pane tab="📊 分析总结" key="summary">
                  <div class="summary-preview">
                    <a-descriptions bordered :column="2">
                      <a-descriptions-item label="总段落数">
                        {{ mockResult.analysis_summary?.total_segments }}
                      </a-descriptions-item>
                      <a-descriptions-item label="对话段落">
                        {{ mockResult.analysis_summary?.character_dialogue_segments }}
                      </a-descriptions-item>
                      <a-descriptions-item label="旁白段落">
                        {{ mockResult.analysis_summary?.narration_segments }}
                      </a-descriptions-item>
                      <a-descriptions-item label="心理活动">
                        {{ mockResult.analysis_summary?.thought_segments }}
                      </a-descriptions-item>
                      <a-descriptions-item label="主要角色">
                        {{ mockResult.analysis_summary?.main_characters_count }}
                      </a-descriptions-item>
                      <a-descriptions-item label="置信度">
                        {{ (mockResult.analysis_summary?.quality_assessment?.overall_confidence * 100).toFixed(1) }}%
                      </a-descriptions-item>
                    </a-descriptions>
                  </div>
                </a-tab-pane>
                
                <a-tab-pane tab="🔧 原始数据" key="raw">
                  <a-textarea 
                    :value="JSON.stringify(mockResult, null, 2)"
                    :rows="20"
                    readonly
                    class="raw-data-display"
                  />
                </a-tab-pane>
              </a-tabs>
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
  if (mockResult.value?.detected_characters) {
    return mockResult.value.detected_characters.every(char => 
      characterVoiceMapping[char.name]
    )
  }
  // 否则基于原始检测的角色
  return detectedCharacters.value.every(char => 
    characterVoiceMapping[char.name]
  )
})

const canStartSynthesis = computed(() => {
  const hasCharacters = mockResult.value?.detected_characters?.length > 0 || detectedCharacters.value.length > 0
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
  if (detectedCharacters.value.length === 0) {
    return '请先分析角色'
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
    console.log('=== 开始Mock智能分析测试 ===')
    const response = await intelligentAnalysisAPI.analyzeProject(project.value.id)
    
    if (response.data.success) {
      mockResult.value = response.data.data
      message.success('Mock分析完成！查看各Tab了解分析结果')
      console.log('Mock分析结果:', mockResult.value)
    } else {
      message.error('Mock分析失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('Mock分析错误:', error)
    message.error('Mock分析失败: ' + error.message)
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
    console.log('=== 应用Mock分析结果 ===')
    const response = await intelligentAnalysisAPI.applyAnalysis(project.value.id, mockResult.value)
    
    if (response.data.success) {
      message.success('Mock结果已应用！')
      console.log('应用结果:', response.data.applied_mapping)
      
      // 使用智能分析的角色结果更新角色配置
      updateCharactersFromAnalysis()
      
      // 刷新项目数据以显示新的角色映射
      await loadProject()
    } else {
      message.error('应用失败: ' + response.data.message)
    }
  } catch (error) {
    console.error('应用Mock结果错误:', error)
    message.error('应用失败: ' + error.message)
  } finally {
    applyingMock.value = false
  }
}

// 从智能分析结果更新角色配置
const updateCharactersFromAnalysis = () => {
  if (!mockResult.value?.detected_characters) return
  
  // 清空现有角色数据
  detectedCharacters.value = []
  
  // 使用智能分析的角色数据
  detectedCharacters.value = mockResult.value.detected_characters.map(char => ({
    name: char.name,
    character_id: char.character_id,
    count: char.total_segments || 0,
    samples: char.sample_dialogues || [],
    gender: char.gender,
    age: char.estimated_age,
    personality: char.personality_traits?.join(', ') || '',
    recommended_voice_id: char.recommended_voice_id
  }))
  
  // 应用推荐的声音映射
  const voiceMapping = mockResult.value.voice_mapping_recommendation || {}
  Object.keys(characterVoiceMapping).forEach(key => delete characterVoiceMapping[key])
  
  Object.values(voiceMapping).forEach(mapping => {
    if (mapping.character_name && mapping.primary_voice_id) {
      characterVoiceMapping[mapping.character_name] = mapping.primary_voice_id
    }
  })
  
  console.log('已更新角色配置:', {
    characters: detectedCharacters.value,
    voiceMapping: characterVoiceMapping
  })
}

const clearMockResult = () => {
  mockResult.value = null
  message.info('Mock结果已清空')
}

const getSegmentTypeColor = (textType) => {
  const colors = {
    '对话': 'blue',
    '环境描述': 'green', 
    '心理活动': 'purple',
    '动作描述': 'orange',
    '场景转换': 'red'
  }
  return colors[textType] || 'default'
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
const updateVoiceMapping = async () => {
  try {
    // 必须传递完整的项目信息，避免name被设为undefined
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

    // 发送请求到后端API（不直接调用TTS），增加超时控制
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 90000) // 90秒超时，给TTS更多时间

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
      setTimeout(() => {
        message.info('💡 如果持续超时，可能是TTS服务需要更多时间加载模型或处理请求')
      }, 2000)
    } else if (error.message.includes('GPU') || error.message.includes('CUDA')) {
      message.error('GPU处理出错，请等待几秒后重试')
      // 自动延迟重试
      setTimeout(() => {
        message.info('💡 提示：如果持续出现GPU错误，可以点击"检查TTS服务"重启服务')
      }, 2000)
    } else if (error.message.includes('TTS服务内部错误')) {
      message.error('TTS服务出现内部错误，可能是GPU显存不足')
      setTimeout(() => {
        message.info('💡 建议：点击"检查TTS服务"或等待几秒后重试')
      }, 2000)
    } else if (error.message.includes('fetch') || error.message.includes('Failed to fetch')) {
      message.error('无法连接到TTS服务，请检查服务状态')
      setTimeout(() => {
        message.info('💡 建议：点击"检查TTS服务"按钮测试连接')
      }, 1500)
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
    
    // 提供恢复建议
    setTimeout(() => {
      message.info('建议：重启TTS服务或检查GPU状态')
    }, 1000)
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

.info-card, .character-card, .control-card, .progress-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

/* 角色配置样式 */
.no-characters {
  text-align: center;
  padding: 40px 0;
}

.character-item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
  transition: all 0.3s ease;
}

.character-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.character-info {
  flex: 1;
}

.character-name {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  flex-wrap: wrap;
}

.character-name .name {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}

.character-meta {
  display: flex;
  gap: 4px;
  margin-top: 4px;
}

.character-samples {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
}

.samples-label {
  font-weight: 500;
}

.sample-text {
  margin-left: 4px;
  font-style: italic;
}

.character-personality {
  font-size: 12px;
  color: #059669;
  margin-bottom: 8px;
}

.personality-label {
  font-weight: 500;
}

.personality-text {
  margin-left: 4px;
}

.recommended-voice {
  margin-top: 4px;
}

.voice-selector {
  display: flex;
  align-items: center;
  gap: 8px;
}

.voice-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.voice-name {
  font-weight: 500;
}

/* 合成控制样式 */
.synthesis-controls {
  padding: 8px 0;
}

.config-hint {
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.action-buttons {
  margin-top: 24px;
}

.status-hint {
  margin-top: 16px;
}

/* 进度样式 */
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

  /* 智能分析样式 */
  .analysis-card {
    border: 2px solid #1890ff;
    background: #f8fffe;
  }

  .character-preview-item {
    background: #f5f5f5;
    padding: 12px;
    margin-bottom: 12px;
    border-radius: 6px;
    border-left: 4px solid #1890ff;
  }

  .character-preview-item.enhanced {
    background: #fff;
    border: 1px solid #e8e8e8;
    border-left: 4px solid #1890ff;
    padding: 16px;
    margin-bottom: 16px;
  }

  .character-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }

  .character-header h4 {
    margin: 0;
    color: #1890ff;
    font-weight: bold;
    font-size: 16px;
  }

  .character-tags {
    display: flex;
    gap: 4px;
  }

  .character-details {
    margin-bottom: 16px;
  }

  .character-details p {
    margin: 4px 0;
    font-size: 13px;
    color: #666;
  }

  .voice-config-section {
    background: #f8f9fa;
    padding: 12px;
    border-radius: 6px;
    border: 1px solid #e9ecef;
  }

  .recommended-voice {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 12px;
  }

  .recommend-label {
    font-size: 12px;
    font-weight: 500;
  }

  .voice-selector-inline {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .recommended-marker {
    color: #faad14;
    margin-left: 4px;
  }

  .config-status {
    text-align: right;
  }

  .character-preview-item h4 {
    margin: 0 0 8px 0;
    color: #1890ff;
    font-weight: bold;
  }

  .character-preview-item p {
    margin: 4px 0;
    font-size: 13px;
  }

  .segment-preview-item {
    background: #fff;
    border: 1px solid #e8e8e8;
    padding: 12px;
    margin-bottom: 8px;
    border-radius: 6px;
  }

  .segment-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 8px;
  }

  .segment-id {
    font-weight: bold;
    color: #666;
    font-size: 12px;
  }

  .segment-text {
    color: #333;
    line-height: 1.5;
    font-size: 14px;
  }

  .mapping-preview-item {
    background: #fafafa;
    padding: 12px;
    margin-bottom: 12px;
    border-radius: 6px;
    border-left: 4px solid #52c41a;
  }

  .mapping-preview-item h4 {
    margin: 0 0 8px 0;
    color: #52c41a;
    font-weight: bold;
  }

  .matching-reasons {
    margin-top: 8px;
  }

  .matching-reasons ul {
    margin: 4px 0 0 16px;
    padding: 0;
  }

  .matching-reasons li {
    margin: 2px 0;
    font-size: 13px;
    color: #666;
  }

  .raw-data-display {
    font-family: 'Courier New', monospace;
    font-size: 12px;
    background: #f6f8fa;
  }

  .summary-preview {
    background: #fff;
    padding: 16px;
    border-radius: 6px;
  }
</style> 