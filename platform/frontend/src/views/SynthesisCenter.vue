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

          <!-- 角色声音配置 -->
          <a-card title="🎭 角色声音配置" :bordered="false" class="character-card">
            <div v-if="detectedCharacters.length === 0" class="no-characters">
              <a-empty description="暂无检测到的角色">
                <a-button type="primary" @click="analyzeCharacters">
                  🔍 分析角色
                </a-button>
              </a-empty>
            </div>

            <div v-else class="characters-config">
              <div
                v-for="character in detectedCharacters"
                :key="character.name"
                class="character-item"
              >
                <div class="character-info">
                  <div class="character-name">
                    <span class="name">{{ character.name }}</span>
                    <a-tag size="small" color="blue">
                      {{ character.count }} 段落
                    </a-tag>
                  </div>
                  <div class="character-samples" v-if="character.samples">
                    <span class="samples-label">示例台词：</span>
                    <span class="sample-text">{{ character.samples.slice(0, 2).join('；') }}</span>
                  </div>
                </div>

                <div class="voice-selector">
                  <a-select
                    v-model:value="characterVoiceMapping[character.name]"
                    placeholder="选择声音"
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
                      </div>
                    </a-select-option>
                  </a-select>
                  
                  <!-- 试听按钮 -->
                  <a-button
                    v-if="characterVoiceMapping[character.name]"
                    type="link"
                    size="small"
                    :loading="previewLoading === characterVoiceMapping[character.name]"
                    @click="playVoicePreview(characterVoiceMapping[character.name], character.samples?.[0])"
                  >
                    <template v-if="!previewLoading">
                      <span v-if="currentPlayingVoice === characterVoiceMapping[character.name]">⏸️ 停止</span>
                      <span v-else>🔊 试听</span>
                    </template>
                  </a-button>
                </div>
              </div>

              <!-- 配置完成提示 -->
              <div v-if="allCharactersConfigured" class="config-complete">
                <a-alert
                  message="✅ 所有角色已配置声音"
                  type="success"
                  show-icon
                  style="margin-top: 16px;"
                />
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
                <a-form-item label="并行任务数">
                  <a-slider
                    v-model:value="synthesisConfig.parallelTasks"
                    :min="1"
                    :max="4"
                    :marks="{ 1: '1', 2: '2', 3: '3', 4: '4' }"
                  />
                  <div class="config-hint">
                    当前设置：{{ synthesisConfig.parallelTasks }} 个并行任务
                  </div>
                </a-form-item>

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
import { readerAPI, charactersAPI } from '@/api'

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

const synthesisConfig = reactive({
  parallelTasks: 2,
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
  return detectedCharacters.value.every(char => 
    characterVoiceMapping[char.name]
  )
})

const canStartSynthesis = computed(() => {
  return allCharactersConfigured.value && 
         project.value?.status !== 'processing' &&
         detectedCharacters.value.length > 0
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
    await readerAPI.updateProject(project.value.id, {
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
    const voice = availableVoices.value.find(v => v.id === voiceId)
    if (!voice) {
      message.error('找不到声音配置')
      return
    }

    // 简化的试听文本
    const previewText = sampleText.slice(0, 30) || '你好，这是声音试听测试。'

    // 构建试听请求
    const formData = new FormData()
    
    // 添加音频文件 - 使用正确的字段名
    if (voice.referenceAudioUrl) {
      // 获取参考音频文件
      const audioResponse = await fetch(voice.referenceAudioUrl)
      if (!audioResponse.ok) {
        throw new Error('音频文件加载失败')
      }
      const audioBlob = await audioResponse.blob()
      formData.append('audio_file', audioBlob, 'voice.wav')
    } else {
      message.error('声音文件不存在')
      return
    }

    // 添加latent文件（如果有）
    if (voice.latentFileUrl) {
      const latentResponse = await fetch(voice.latentFileUrl)
      if (!latentResponse.ok) {
        throw new Error('Latent文件加载失败')
      }
      const latentBlob = await latentResponse.blob()
      formData.append('latent_file', latentBlob, 'voice.npy')
    }

    // 添加文本和参数 - 使用较快的设置
    formData.append('text', previewText)
    formData.append('time_step', '15') // 更快的推理步数
    formData.append('p_w', '1.0')
    formData.append('t_w', '1.0')

    // 发送请求到TTS API，增加超时控制
    const controller = new AbortController()
    const timeoutId = setTimeout(() => controller.abort(), 30000) // 30秒超时

    const response = await fetch('/api/tts/synthesize_file', {
      method: 'POST',
      body: formData,
      signal: controller.signal
    })

    clearTimeout(timeoutId)

    if (response.ok) {
      // 获取音频数据并播放
      const audioBlob = await response.blob()
      const audioUrl = URL.createObjectURL(audioBlob)
      
      // 创建音频元素
      const audio = new Audio(audioUrl)
      currentAudio.value = audio
      currentPlayingVoice.value = voiceId

      // 播放事件处理
      audio.addEventListener('loadstart', () => {
        message.success('开始播放试听')
      })

      audio.addEventListener('ended', () => {
        URL.revokeObjectURL(audioUrl)
        currentAudio.value = null
        currentPlayingVoice.value = null
      })

      audio.addEventListener('error', (e) => {
        console.error('音频播放错误:', e)
        URL.revokeObjectURL(audioUrl)
        currentAudio.value = null
        currentPlayingVoice.value = null
        message.error('音频播放失败')
      })

      // 开始播放
      await audio.play()
    } else {
      const errorText = await response.text()
      console.error('TTS API错误:', errorText)
      
      if (response.status === 500) {
        throw new Error('TTS服务内部错误，可能是GPU显存不足')
      } else {
        throw new Error(`试听请求失败: ${response.status}`)
      }
    }
    
  } catch (error) {
    console.error('试听失败:', error)
    
    if (error.name === 'AbortError') {
      message.error('试听请求超时，请重试')
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
    const response = await fetch('/api/tts/health', {
      method: 'GET',
      timeout: 5000
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
  align-items: center;
  padding: 16px;
  margin-bottom: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  background: #f8fafc;
}

.character-info {
  flex: 1;
}

.character-name {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 4px;
}

.character-name .name {
  font-weight: 600;
  color: #1f2937;
}

.character-samples {
  font-size: 12px;
  color: #6b7280;
}

.samples-label {
  font-weight: 500;
}

.sample-text {
  margin-left: 4px;
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
</style> 