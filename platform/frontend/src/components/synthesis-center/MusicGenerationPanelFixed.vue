<template>
  <div class="music-generation-panel">
    <a-card title="🎵 背景音乐生成" :bordered="false">
      <!-- 生成表单 -->
      <a-form layout="vertical" @submit="handleGenerate">
        <!-- 歌词输入 -->
        <a-form-item label="歌词内容" required>
          <SongStructureHelper v-model="formData.lyrics" :disabled="isGenerating" />
        </a-form-item>

        <!-- 高级参数 -->
        <a-collapse v-if="!isGenerating">
          <a-collapse-panel key="advanced" header="🎛️ 高级参数">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-form-item label="音乐风格">
                  <a-select v-model:value="formData.genre" placeholder="选择风格">
                    <a-select-option value="Auto">自动</a-select-option>
                    <a-select-option value="Pop">流行</a-select-option>
                    <a-select-option value="R&B">R&B</a-select-option>
                    <a-select-option value="Dance">舞曲</a-select-option>
                    <a-select-option value="Rock">摇滚</a-select-option>
                    <a-select-option value="Jazz">爵士</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="CFG系数">
                  <a-input-number
                    v-model:value="formData.cfg_coef"
                    :min="0.1"
                    :max="3.0"
                    :step="0.1"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="温度">
                  <a-input-number
                    v-model:value="formData.temperature"
                    :min="0.1"
                    :max="2.0"
                    :step="0.1"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="Top-K">
                  <a-input-number
                    v-model:value="formData.top_k"
                    :min="1"
                    :max="100"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="音量级别(dB)">
                  <a-input-number
                    v-model:value="formData.volume_level"
                    :min="-30"
                    :max="0"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>
            <a-form-item label="描述(可选)">
              <a-input v-model:value="formData.description" placeholder="为音乐添加描述..." />
            </a-form-item>
          </a-collapse-panel>
        </a-collapse>

        <!-- 生成按钮 -->
        <div class="action-buttons">
          <a-button
            type="primary"
            size="large"
            :loading="isGenerating"
            @click="handleGenerate"
            :disabled="!formData.lyrics.trim()"
          >
            <template #icon>
              <PlayCircleOutlined v-if="!isGenerating" />
            </template>
            {{ isGenerating ? '正在生成音乐...' : '🎵 生成背景音乐' }}
          </a-button>

          <a-button v-if="isGenerating" @click="handleCancel" danger> 取消生成 </a-button>
        </div>
      </a-form>

      <!-- 实时进度显示 -->
      <div v-if="isGenerating" class="progress-section">
        <a-divider />
        <div class="progress-info">
          <div class="progress-header">
            <span class="progress-title">🎵 音乐生成进度</span>
            <span class="progress-percent">{{ Math.round(progress) }}%</span>
          </div>
          <a-progress
            :percent="progress"
            :status="progressStatus"
            :stroke-color="progressColor"
            size="small"
          />
          <div class="progress-details">
            <div class="current-stage">{{ currentMessage }}</div>
            <div class="task-info" v-if="currentTaskId">
              <a-tag color="blue">任务ID: {{ currentTaskId.slice(0, 8) }}...</a-tag>
              <a-tag v-if="elapsedTime" color="green">已用时: {{ formatTime(elapsedTime) }}</a-tag>
            </div>
          </div>
        </div>
      </div>

      <!-- 生成结果 -->
      <div v-if="generationResult" class="result-section">
        <a-divider />
        <a-result
          status="success"
          title="🎉 音乐生成完成！"
          :sub-title="`耗时: ${formatTime(generationResult.generation_time || 0)}`"
        >
          <template #extra>
            <div class="result-actions">
              <a-button type="primary" @click="playMusic">
                <template #icon><PlayCircleOutlined /></template>
                播放音乐
              </a-button>
              <a-button @click="downloadMusic">
                <template #icon><DownloadOutlined /></template>
                下载音乐
              </a-button>
              <a-button @click="resetForm"> 重新生成 </a-button>
            </div>
          </template>
        </a-result>

        <!-- 音频播放器 -->
        <div v-if="audioUrl" class="audio-player">
          <audio ref="audioElement" :src="audioUrl" controls style="width: 100%" />
        </div>

        <!-- 生成信息 -->
        <div v-if="generationResult.music_description" class="generation-info">
          <a-descriptions title="生成信息" bordered size="small">
            <a-descriptions-item label="音乐描述">
              {{ generationResult.music_description }}
            </a-descriptions-item>
            <a-descriptions-item label="使用风格">
              {{ generationResult.final_style || formData.genre }}
            </a-descriptions-item>
            <a-descriptions-item label="音频时长">
              {{ formatTime(generationResult.duration || 30) }}
            </a-descriptions-item>
          </a-descriptions>
        </div>
      </div>
    </a-card>
  </div>
</template>

<script setup>
  import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
  import { message } from 'ant-design-vue'
  import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons-vue'
  import { useWebSocket } from '@/composables/useWebSocketSimple'
  import SongStructureHelper from './SongStructureHelper.vue'

  const emit = defineEmits(['musicGenerated', 'generationCompleted'])

  // 响应式数据
  const isGenerating = ref(false)
  const progress = ref(0)
  const currentMessage = ref('')
  const currentTaskId = ref('')
  const elapsedTime = ref(0)
  const generationResult = ref(null)
  const audioElement = ref(null)

  const formData = reactive({
    lyrics: '',
    genre: 'Auto',
    description: '',
    cfg_coef: 1.5,
    temperature: 0.9,
    top_k: 50,
    volume_level: -12.0
  })

  // WebSocket连接
  const { connect, disconnect, isConnected } = useWebSocket()

  // 计算属性
  const progressStatus = computed(() => {
    if (progress.value < 0) return 'exception'
    if (progress.value >= 100) return 'success'
    return 'active'
  })

  const progressColor = computed(() => {
    if (progress.value < 0) return '#ff4d4f'
    if (progress.value >= 100) return '#52c41a'
    return '#1890ff'
  })

  const audioUrl = computed(() => {
    if (!generationResult.value?.result?.audio_url) return null
    const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
    return `${baseUrl}${generationResult.value.result.audio_url}`
  })

  // 时间格式化
  const formatTime = (seconds) => {
    const mins = Math.floor(seconds / 60)
    const secs = Math.floor(seconds % 60)
    return `${mins}:${secs.toString().padStart(2, '0')}`
  }

  // 处理生成音乐
  const handleGenerate = async () => {
    if (!formData.lyrics.trim()) {
      message.warning('请输入歌词内容')
      return
    }

    try {
      isGenerating.value = true
      progress.value = 0
      currentMessage.value = '正在启动音乐生成...'
      generationResult.value = null

      // 连接WebSocket
      if (!isConnected.value) {
        await connect()
      }

      // 启动异步音乐生成任务
      const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'
      const response = await fetch(`${baseUrl}/api/v1/music-generation-async/generate`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          lyrics: formData.lyrics,
          genre: formData.genre,
          description: formData.description,
          cfg_coef: formData.cfg_coef,
          temperature: formData.temperature,
          top_k: formData.top_k,
          volume_level: formData.volume_level
        })
      })

      if (!response.ok) {
        throw new Error(`启动任务失败: ${response.status}`)
      }

      const result = await response.json()
      currentTaskId.value = result.task_id

      console.log('🎵 异步音乐生成任务已启动:', result.task_id)
      message.info('音乐生成任务已启动，正在监控进度...')
    } catch (error) {
      console.error('启动音乐生成失败:', error)
      message.error(`启动失败: ${error.message}`)
      isGenerating.value = false
    }
  }

  // 处理取消
  const handleCancel = () => {
    if (currentTaskId.value) {
      // TODO: 调用取消API
      message.info('正在取消任务...')
    }
    resetGenerationState()
  }

  // 重置生成状态
  const resetGenerationState = () => {
    isGenerating.value = false
    progress.value = 0
    currentMessage.value = ''
    currentTaskId.value = ''
    elapsedTime.value = 0
  }

  // 重置表单
  const resetForm = () => {
    resetGenerationState()
    generationResult.value = null
    Object.assign(formData, {
      lyrics: '',
      genre: 'Auto',
      description: '',
      cfg_coef: 1.5,
      temperature: 0.9,
      top_k: 50,
      volume_level: -12.0
    })
  }

  // 播放音乐
  const playMusic = () => {
    if (audioElement.value) {
      audioElement.value.play()
    }
  }

  // 下载音乐
  const downloadMusic = () => {
    if (audioUrl.value) {
      const link = document.createElement('a')
      link.href = audioUrl.value
      link.download = `generated_music_${Date.now()}.wav`
      link.click()
    }
  }

  // WebSocket消息处理
  const handleWebSocketMessage = (message) => {
    try {
      const data = JSON.parse(message)

      if (data.type === 'music_generation_progress' && data.data.task_id === currentTaskId.value) {
        const progressData = data.data

        progress.value = Math.round(progressData.progress * 100)
        currentMessage.value = progressData.message || '处理中...'

        // 更新已用时间
        elapsedTime.value = Date.now() / 1000 - startTime

        console.log(`📊 进度更新: ${progress.value}% - ${currentMessage.value}`)

        // 检查是否完成
        if (progressData.status === 'completed' && progressData.result) {
          // 生成成功
          generationResult.value = progressData

          emit('musicGenerated', progressData)
          emit('generationCompleted', progressData)

          message.success('🎵 背景音乐生成完成！')
          resetGenerationState()
        } else if (progressData.status === 'failed') {
          // 生成失败
          console.error('音乐生成失败:', progressData.error)
          message.error(`生成失败: ${progressData.error || '未知错误'}`)
          resetGenerationState()
        }
      }
    } catch (error) {
      console.error('处理WebSocket消息失败:', error)
    }
  }

  let startTime = 0

  // 生命周期
  onMounted(async () => {
    try {
      // 连接WebSocket并监听消息
      await connect()

      // 监听WebSocket消息
      window.addEventListener('websocket_message', (event) => {
        handleWebSocketMessage(event.detail)
      })

      startTime = Date.now() / 1000
    } catch (error) {
      console.error('初始化WebSocket失败:', error)
      message.warning('WebSocket连接失败，进度监控不可用')
    }
  })

  onUnmounted(() => {
    disconnect()
    window.removeEventListener('websocket_message', handleWebSocketMessage)
  })
</script>

<style scoped>
  .music-generation-panel {
    max-width: 800px;
    margin: 0 auto;
  }

  .action-buttons {
    display: flex;
    gap: 12px;
    margin-top: 16px;
  }

  .progress-section {
    margin-top: 16px;
  }

  .progress-info {
    padding: 16px;
    background: #f8f9fa;
    border-radius: 6px;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .progress-title {
    font-weight: 500;
    color: #1890ff;
  }

  .progress-percent {
    font-weight: bold;
    font-size: 16px;
  }

  .progress-details {
    margin-top: 8px;
  }

  .current-stage {
    color: #666;
    margin-bottom: 8px;
  }

  .task-info {
    display: flex;
    gap: 8px;
  }

  .result-section {
    margin-top: 16px;
  }

  .result-actions {
    display: flex;
    gap: 12px;
    justify-content: center;
  }

  .audio-player {
    margin: 16px 0;
    text-align: center;
  }

  .generation-info {
    margin-top: 16px;
  }
</style>
