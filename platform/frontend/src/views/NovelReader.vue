<template>
  <div class="novel-reader-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>项目详情</h1>
        <p>{{ currentProject?.name || '加载中...' }}</p>
      </div>
      <div class="header-actions">
        <a-button @click="goBackToList">
          <template #icon>
            <LeftOutlined />
          </template>
          返回列表
        </a-button>
        <a-button type="primary" @click="startSynthesis" :loading="synthesizing" :disabled="!canSynthesize">
          <template #icon>
            <PlayCircleOutlined />
          </template>
          开始合成
        </a-button>
        </div>
        </div>

    <!-- 项目信息 -->
    <div v-if="currentProject" class="project-info-section">
      <div class="info-card">
        <div class="info-item">
          <span class="info-label">项目状态</span>
          <a-tag :color="getStatusColor(currentProject.status)">
            {{ getStatusText(currentProject.status) }}
          </a-tag>
      </div>

        <div class="info-item">
          <span class="info-label">文本段落</span>
          <span class="info-value">{{ getSegmentCount(currentProject) }} 段</span>
                </div>
        <div class="info-item">
          <span class="info-label">创建时间</span>
          <span class="info-value">{{ formatDate(currentProject.createdAt) }}</span>
                    </div>
                  </div>
                </div>

    <!-- 合成进度 -->
    <div v-if="synthesizing || currentProject?.status === 'processing'" class="progress-section">
      <div class="progress-card">
        <div class="progress-header">
          <h3>合成进度</h3>
          <span>{{ progressPercent }}%</span>
              </div>
        <a-progress :percent="progressPercent" :stroke-color="progressColor" />
        <div class="progress-details">
          <div class="progress-step">
            <span class="step-label">文本分析:</span>
            <span :class="['step-status', progressStatus.text]">{{ getStepText('text') }}</span>
          </div>
          <div class="progress-step">
            <span class="step-label">角色识别:</span>
            <span :class="['step-status', progressStatus.character]">{{ getStepText('character') }}</span>
          </div>
          <div class="progress-step">
            <span class="step-label">语音生成:</span>
            <span :class="['step-status', progressStatus.synthesis]">{{ getStepText('synthesis') }}</span>
          </div>
        </div>
            </div>
          </div>
          
    <!-- 文本内容预览 -->
    <div class="content-section">
      <div class="content-card">
        <div class="content-header">
          <h3>文本内容</h3>
          <div class="content-actions">
            <a-button type="text" size="small" @click="showFullText = !showFullText">
              {{ showFullText ? '收起' : '展开' }}
            </a-button>
          </div>
        </div>
        <div class="content-preview" :class="{ 'expanded': showFullText }">
          {{ currentProject?.originalText || '加载中...' }}
    </div>
              </div>
    </div>

    



    <!-- 合成配置 -->
    <div v-if="currentProject?.status === 'completed' || currentProject?.status === 'processing'" class="synthesis-config-section">
      <div class="config-card">
        <div class="config-header">
          <h3>合成配置</h3>
          <div class="config-actions">
            <a-button 
              v-if="currentProject?.status !== 'completed'"
              type="link" 
              size="small" 
              @click="$router.push(`/synthesis/${currentProject.id}`)"
            >
              编辑配置
            </a-button>
          </div>
        </div>
        <div class="config-content">
          <div class="config-row">
            <div class="config-item">
              <span class="config-label">音质设置</span>
              <span class="config-value">
                <a-tag color="blue">
                  {{ currentProject?.config?.audio_quality === 'high' ? '高质量' : '标准' }}
                </a-tag>
              </span>
            </div>
            <div class="config-item">
              <span class="config-label">智能检测</span>
              <span class="config-value">
                <a-tag :color="currentProject?.config?.enable_smart_detection ? 'green' : 'default'">
                  {{ currentProject?.config?.enable_smart_detection ? '已启用' : '已禁用' }}
                </a-tag>
              </span>
            </div>
            <div class="config-item">
              <span class="config-label">分段模式</span>
              <span class="config-value">
                <a-tag color="purple">
                  {{ currentProject?.config?.segment_mode === 'paragraph' ? '按段落' : '按章节' }}
                </a-tag>
              </span>
            </div>
            <div class="config-item">
              <span class="config-label">背景音乐</span>
              <span class="config-value">
                <a-tag :color="currentProject?.config?.enable_bg_music ? 'green' : 'default'">
                  {{ currentProject?.config?.enable_bg_music ? '已启用' : '已禁用' }}
                </a-tag>
              </span>
            </div>
          </div>
          
          <!-- 角色声音映射 -->
          <div v-if="currentProject?.config?.character_mapping" class="character-mapping">
            <div class="mapping-header">
              <span class="mapping-title">角色声音映射</span>
            </div>
            <div v-if="currentProject.config.character_mapping && Object.keys(currentProject.config.character_mapping).length > 0" class="mapping-list">
              <div 
                v-for="(voiceId, characterName) in currentProject.config.character_mapping" 
                :key="characterName"
                class="mapping-item"
              >
                <span class="character-name">{{ characterName }}</span>
                <span class="voice-name">声音ID: {{ voiceId }}</span>
              </div>
            </div>
            <div v-else class="no-mapping">
              <span style="color: #6b7280; font-style: italic;">使用默认声音</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 生成结果 -->
    <div v-if="currentProject?.status === 'completed' || audioFiles.length > 0" class="results-section">
      <div class="results-card">
        <div class="results-header">
          <h3>生成结果</h3>
          <div class="results-actions">
            <a-button 
              v-if="currentProject?.final_audio_path"
              type="primary"
              @click="downloadFinalAudio" 
              :loading="downloading"
            >
              <template #icon>
                <DownloadOutlined />
              </template>
              下载完整音频
            </a-button>
            <a-button @click="downloadAll" :loading="downloading">
              <template #icon>
                <DownloadOutlined />
              </template>
              下载全部
            </a-button>
            <a-button @click="viewInAudioLibrary">
              <template #icon>
                <SoundOutlined />
              </template>
              音频库
            </a-button>
          </div>
        </div>
        
        <!-- 合成统计 -->
        <div v-if="currentProject?.status === 'completed'" class="synthesis-stats">
          <div class="stats-row">
            <div class="stat-item">
              <span class="stat-label">总段落数</span>
              <span class="stat-value">{{ currentProject.total_segments || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">已完成</span>
              <span class="stat-value">{{ currentProject.processed_segments || 0 }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">处理时间</span>
              <span class="stat-value">{{ getProcessingTime() }}</span>
            </div>
            <div class="stat-item">
              <span class="stat-label">最终音频</span>
              <span class="stat-value">
                <a-tag v-if="currentProject.final_audio_path" color="green">已生成</a-tag>
                <a-tag v-else color="orange">处理中</a-tag>
              </span>
            </div>
          </div>
        </div>
        
        <!-- 段落详情列表 -->
        <div v-if="currentProject?.segments?.length > 0" class="segments-list">
          <div class="segments-header">
            <span class="segments-title">段落处理详情</span>
            <span class="segments-count">{{ currentProject.segments.length }} 个段落</span>
          </div>
          <div class="segments-content">
            <div 
              v-for="(segment, index) in currentProject.segments" 
              :key="segment.id"
              class="segment-item"
            >
              <div class="segment-index">{{ index + 1 }}</div>
              <div class="segment-content">
                <div class="segment-text">{{ segment.content || segment.text_content || '无内容' }}</div>
                <div class="segment-meta">
                  <span class="segment-speaker">{{ segment.speaker || '温柔女声' }}</span>
                  <span class="segment-duration">
                    {{ segment.processing_time ? `${segment.processing_time}s` : '未知时长' }}
                  </span>
                  <span class="segment-status">
                    <a-tag 
                      :color="getSegmentStatusColor(segment.status)"
                      size="small"
                    >
                      {{ getSegmentStatusText(segment.status) }}
                    </a-tag>
                  </span>
                </div>
              </div>
              <div class="segment-actions">
                <a-button 
                  v-if="segment.audio_file_path && segment.status === 'completed'"
                  type="text" 
                  size="small" 
                  @click="playSegmentAudio(segment)"
                  title="播放此段落"
                >
                  <template #icon>
                    <PlayCircleOutlined />
                  </template>
                </a-button>
                <a-button 
                  v-if="segment.audio_file_path && segment.status === 'completed'"
                  type="text" 
                  size="small" 
                  @click="downloadSegmentAudio(segment)"
                  title="下载此段落"
                >
                  <template #icon>
                    <DownloadOutlined />
                  </template>
                </a-button>
              </div>
            </div>
          </div>
        </div>
        
        <!-- 传统音频文件列表（兼容旧版本） -->
        <div v-if="audioFiles.length > 0" class="audio-list">
          <div v-for="audio in audioFiles" :key="audio.id" class="audio-item">
              <div class="audio-info">
              <div class="audio-icon">
                <SoundOutlined />
                </div>
              <div class="audio-details">
                <div class="audio-name">{{ audio.filename }}</div>
                <div class="audio-meta">{{ audio.duration }}s · {{ audio.size }}MB</div>
              </div>
            </div>
            <div class="audio-actions">
              <a-button type="text" size="small" @click="playAudio(audio)">
                  <template #icon>
                  <PlayCircleOutlined />
                </template>
              </a-button>
              <a-button type="text" size="small" @click="downloadAudio(audio)">
                <template #icon>
                  <DownloadOutlined />
                  </template>
                </a-button>
            </div>
          </div>
              </div>
            </div>
          </div>

    <!-- 音频播放器 -->
    <div v-if="currentAudio" class="audio-player">
      <div class="player-content">
        <div class="player-info">
          <span class="player-title">{{ currentAudio.filename }}</span>
          <span class="player-time">{{ formatTime(currentAudio.duration) }}</span>
        </div>
        <audio ref="audioElement" controls style="width: 100%;">
          <source :src="currentAudio.url" type="audio/wav">
        </audio>
      </div>
      <a-button type="text" @click="closePlayer">
              <template #icon>
          <CloseOutlined />
              </template>
            </a-button>
          </div>


  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute, onBeforeRouteLeave } from 'vue-router'
import { message } from 'ant-design-vue'
import { 
  LeftOutlined, 
  PlayCircleOutlined, 
  DownloadOutlined, 
  CloseOutlined,
  SoundOutlined
} from '@ant-design/icons-vue'
import { readerAPI } from '@/api'

const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(false)
const synthesizing = ref(false)
const downloading = ref(false)
const currentProject = ref(null)
const audioFiles = ref([])
const currentAudio = ref(null)
const showFullText = ref(false)



// 进度状态
const progressPercent = ref(0)
const progressStatus = ref({
  text: 'pending',
  character: 'pending', 
  synthesis: 'pending'
})

// 计算属性
const progressColor = computed(() => {
  if (progressPercent.value === 100) return '#52c41a'
  if (progressPercent.value > 0) return '#1890ff'
  return '#d9d9d9'
})

const canSynthesize = computed(() => {
  return currentProject.value && 
         currentProject.value.status !== 'processing' &&
         (currentProject.value.segments?.length > 0 || currentProject.value.originalText)
})

// 方法
const loadProject = async () => {
  const projectId = route.params.id
  if (!projectId) {
    message.error('项目ID不存在')
    router.push('/novel-reader')
    return
  }

  loading.value = true
  try {
    const response = await readerAPI.getProjectDetail(projectId)
    if (response.data.success) {
      currentProject.value = response.data.data
      
      audioFiles.value = response.data.data.audio_files || []
      
      // 如果项目正在处理中，开始轮询进度
      if (currentProject.value.status === 'processing') {
        startProgressPolling()
      }
    } else {
      message.error('获取项目详情失败')
      router.push('/novel-reader')
    }
  } catch (error) {
    console.error('获取项目详情失败:', error)
    message.error('获取项目详情失败')
    router.push('/novel-reader')
  } finally {
    loading.value = false
  }
}











const startSynthesis = async () => {
  try {
    synthesizing.value = true
    progressPercent.value = 0
    progressStatus.value = {
      text: 'processing',
      character: 'pending',
      synthesis: 'pending'
    }

    const response = await readerAPI.startGeneration(currentProject.value.id)
    if (response.data.success) {
      message.success('开始语音合成')
      currentProject.value.status = 'processing'
      startProgressPolling()
    } else {
      message.error('启动合成失败: ' + response.data.message)
      synthesizing.value = false
    }
  } catch (error) {
    message.error('启动合成失败')
    synthesizing.value = false
  }
}

const startProgressPolling = () => {
  let errorCount = 0
  const maxErrors = 5
  const maxDuration = 30 * 60 * 1000 // 30分钟最大轮询时间
  const startTime = Date.now()
  
  const pollInterval = setInterval(async () => {
  try {
      // 检查轮询时间是否超过最大限制
      if (Date.now() - startTime > maxDuration) {
        console.warn('轮询超时，自动停止')
        clearInterval(pollInterval)
        message.warning('进度监控超时，请刷新页面查看最新状态')
        return
      }

      const response = await readerAPI.getProgress(currentProject.value.id)
    if (response.data.success) {
      const progress = response.data.progress
        
        // 重置错误计数
        errorCount = 0
        
        progressPercent.value = progress.progressPercent || 0
        
        // 根据进度状态更新步骤状态
        if (progress.status === 'processing') {
          progressStatus.value = {
            text: 'completed',
            character: 'completed',
            synthesis: 'processing'
          }
        } else if (progress.status === 'completed') {
          progressStatus.value = {
            text: 'completed',
            character: 'completed',
            synthesis: 'completed'
          }
        } else if (progress.status === 'failed') {
          progressStatus.value = {
            text: 'completed',
            character: 'completed',
            synthesis: 'failed'
          }
        }
        
        // 检查停止条件
        const shouldStop = progress.status === 'completed' || 
                          progress.status === 'failed' ||
                          progress.status === 'cancelled' ||
                          // 如果没有段落在处理且没有待处理的段落，也停止轮询
                          (progress.statistics.processing === 0 && 
                           progress.statistics.pending === 0 && 
                           progress.statistics.total > 0)
        
        if (shouldStop) {
          clearInterval(pollInterval)
          synthesizing.value = false
          
          if (progress.status === 'completed') {
          currentProject.value.status = 'completed'
          // 重新加载项目以获取音频文件
          loadProject()
          message.success('语音合成完成！')
      } else if (progress.status === 'failed') {
          currentProject.value.status = 'failed'
          message.error('语音合成失败')
          } else if (progress.status === 'cancelled') {
            currentProject.value.status = 'cancelled'
            message.info('语音合成已取消')
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
        clearInterval(pollInterval)
        synthesizing.value = false
        message.error('无法获取进度信息，请检查网络连接')
      }
    }
  }, 2000)

  // 存储定时器ID以便全局清理
  window.novelReaderPollInterval = pollInterval

  // 组件卸载时清除定时器
  onUnmounted(() => {
    clearInterval(pollInterval)
    window.novelReaderPollInterval = null
  })
}

const goBackToList = () => {
  router.push('/novel-reader')
}

const playAudio = (audio) => {
  currentAudio.value = audio
  // 在下一个tick中播放，确保DOM已更新
  nextTick(() => {
    const audioElement = document.querySelector('audio')
    if (audioElement) {
      audioElement.play()
    }
  })
}

const closePlayer = () => {
  currentAudio.value = null
}

const downloadAudio = async (audio) => {
  try {
    const response = await fetch(audio.url)
    const blob = await response.blob()
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = audio.filename
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    message.success('下载成功')
  } catch (error) {
    message.error('下载失败')
  }
}

const downloadAll = async () => {
  downloading.value = true
  try {
    for (const audio of audioFiles.value) {
      await downloadAudio(audio)
      // 稍微延迟避免同时下载太多文件
      await new Promise(resolve => setTimeout(resolve, 500))
    }
    message.success('全部下载完成')
  } catch (error) {
    message.error('批量下载失败')
  } finally {
    downloading.value = false
  }
}

const viewInAudioLibrary = () => {
  router.push({
    path: '/audio-library',
    query: { search: currentProject.value.name }
  })
}

// 辅助函数
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN')
}

const formatTime = (seconds) => {
  if (!seconds) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}



const getSegmentCount = (project) => {
  if (!project) return 0
  return project.segments?.length || 0
}

const getStatusColor = (status) => {
  const colors = {
    'pending': 'orange',
    'processing': 'blue', 
    'completed': 'green',
    'failed': 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '待处理',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return texts[status] || '未知'
}

const getStepText = (step) => {
  const currentStatus = progressStatus.value[step]
  const texts = {
    'pending': '等待中',
    'processing': '进行中',
    'completed': '已完成',
    'failed': '失败'
  }
  return texts[currentStatus] || '等待中'
}



// 获取处理时间
const getProcessingTime = () => {
  if (!currentProject.value || !currentProject.value.started_at || !currentProject.value.completed_at) {
    return '未知'
  }
  
  const startTime = new Date(currentProject.value.started_at)
  const endTime = new Date(currentProject.value.completed_at)
  const diffMs = endTime - startTime
  const diffSeconds = Math.floor(diffMs / 1000)
  
  if (diffSeconds < 60) {
    return `${diffSeconds}秒`
  } else if (diffSeconds < 3600) {
    const minutes = Math.floor(diffSeconds / 60)
    const seconds = diffSeconds % 60
    return `${minutes}分${seconds}秒`
  } else {
    const hours = Math.floor(diffSeconds / 3600)
    const minutes = Math.floor((diffSeconds % 3600) / 60)
    return `${hours}小时${minutes}分钟`
  }
}

// 获取段落状态颜色
const getSegmentStatusColor = (status) => {
  const colors = {
    'pending': 'orange',
    'processing': 'blue',
    'completed': 'green',
    'failed': 'red'
  }
  return colors[status] || 'default'
}

// 获取段落状态文本
const getSegmentStatusText = (status) => {
  const texts = {
    'pending': '等待',
    'processing': '处理中',
    'completed': '已完成',
    'failed': '失败'
  }
  return texts[status] || '未知'
}

// 下载完整音频
const downloadFinalAudio = async () => {
  // 检查项目状态
  if (currentProject.value?.status !== 'completed') {
    const statusText = {
      'pending': '等待处理',
      'configured': '已配置但未开始生成',
      'processing': '正在生成中',
      'paused': '已暂停',
      'failed': '生成失败'
    }[currentProject.value?.status] || '未知状态'
    
    message.warning(`无法下载：项目当前状态为"${statusText}"，只有已完成的项目才能下载音频文件`)
    return
  }
  
  if (!currentProject.value?.final_audio_path) {
    message.error('没有可下载的最终音频文件')
    return
  }
  
  downloading.value = true
  try {
    const response = await readerAPI.downloadAudio(currentProject.value.id)
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${currentProject.value.name}_完整音频.wav`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    message.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    
    // 改进错误处理，显示具体的错误信息
    let errorMessage = '下载失败'
    if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message === 'Network Error') {
      errorMessage = '网络连接失败，请检查网络连接或稍后重试'
    } else if (error.code === 'ERR_CONNECTION_RESET') {
      errorMessage = '连接被重置，请检查后端服务状态'
    }
    
    message.error(errorMessage)
  } finally {
    downloading.value = false
  }
}

// 播放段落音频
const playSegmentAudio = async (segment) => {
  if (!segment.audio_file_path) {
    message.warning('此段落没有音频文件')
    return
  }
  
  try {
    // 构建音频URL - 需要通过后端API获取
    const audioUrl = `/api/v1/audio/segment/${segment.id}`
    
    // 创建音频对象并播放
    const audio = new Audio(audioUrl)
    currentAudio.value = {
      filename: `段落${segment.paragraph_index || segment.id}`,
      url: audioUrl,
      duration: segment.processing_time || 0
    }
    
    audio.addEventListener('loadeddata', () => {
      message.success('开始播放段落音频')
    })
    
    audio.addEventListener('error', () => {
      message.error('音频播放失败')
      currentAudio.value = null
    })
    
    await audio.play()
  } catch (error) {
    console.error('播放段落音频失败:', error)
    message.error('播放失败')
  }
}

// 下载段落音频
const downloadSegmentAudio = async (segment) => {
  if (!segment.audio_file_path) {
    message.warning('此段落没有音频文件')
    return
  }
  
  try {
    const audioUrl = `/api/v1/audio/segment/${segment.id}?download=true`
    const link = document.createElement('a')
    link.href = audioUrl
    link.download = `段落${segment.paragraph_index || segment.id}_${segment.speaker || '音频'}.wav`
    document.body.appendChild(link)
    link.click()
    link.remove()
    message.success('段落音频下载成功')
  } catch (error) {
    console.error('下载段落音频失败:', error)
    message.error('下载失败')
  }
}

// 生命周期
onMounted(() => {
  loadProject()
})

// 监听路由变化
watch(() => route.params.id, () => {
  if (route.params.id) {
    loadProject()
  }
})

// 页面切换前的清理
onBeforeRouteLeave(() => {
  if (window.novelReaderPollInterval) {
    clearInterval(window.novelReaderPollInterval)
    window.novelReaderPollInterval = null
  }
  return true
})

// 浏览器刷新/关闭前的清理
window.addEventListener('beforeunload', () => {
  if (window.novelReaderPollInterval) {
    clearInterval(window.novelReaderPollInterval)
    window.novelReaderPollInterval = null
  }
})
</script>

<style scoped>
.novel-reader-container {
  background: #faf9f8;
  min-height: 100vh;
}

/* 页面头部 */
.page-header {
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  padding: 40px;
  border-radius: 16px;
  margin-bottom: 32px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 8px 32px rgba(6, 182, 212, 0.2);
}

.header-content h1 {
  margin: 0;
  color: white;
  font-size: 28px;
  font-weight: 700;
}

.header-content p {
  margin: 8px 0 0 0;
  color: rgba(255,255,255,0.9);
  font-size: 16px;
}

.header-actions {
  display: flex;
  gap: 16px;
}

/* 项目信息 */
.project-info-section {
  margin-bottom: 24px;
}

.info-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 24px;
}

.info-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.info-label {
  font-size: 14px;
  color: #6b7280;
}

.info-value {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

/* 进度部分 */
.progress-section {
  margin-bottom: 24px;
}

.progress-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.progress-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.progress-header h3 {
  margin: 0;
  color: #1f2937;
}

.progress-details {
  margin-top: 16px;
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.progress-step {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.step-label {
  font-size: 14px;
  color: #6b7280;
}

.step-status {
  font-size: 14px;
  font-weight: 600;
}

.step-status.pending {
  color: #9ca3af;
}

.step-status.processing {
  color: #1890ff;
}

.step-status.completed {
  color: #52c41a;
}

.step-status.failed {
  color: #ef4444;
}

/* 内容部分 */
.content-section {
  margin-bottom: 24px;
}

.content-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.content-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.content-header h3 {
  margin: 0;
  color: #1f2937;
}

.content-preview {
  max-height: 200px;
  overflow: hidden;
  line-height: 1.6;
  color: #374151;
  white-space: pre-wrap;
  position: relative;
}

.content-preview.expanded {
  max-height: none;
}

.content-preview:not(.expanded)::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  height: 40px;
  background: linear-gradient(transparent, white);
}



/* 结果部分 */
.results-section {
  margin-bottom: 24px;
}

.results-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.results-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.results-header h3 {
  margin: 0;
  color: #1f2937;
}

.results-actions {
  display: flex;
  gap: 12px;
}

.audio-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.audio-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s;
}

.audio-item:hover {
  border-color: #06b6d4;
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.1);
}

.audio-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.audio-icon {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: #f3f4f6;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #06b6d4;
}

.audio-name {
  font-weight: 600;
  color: #1f2937;
}

.audio-meta {
  font-size: 12px;
  color: #6b7280;
}

.audio-actions {
  display: flex;
  gap: 8px;
}

/* 音频播放器 */
.audio-player {
  position: fixed;
  bottom: 24px;
  left: 50%;
  transform: translateX(-50%);
  background: white;
  padding: 16px;
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(0,0,0,0.1);
  display: flex;
  align-items: center;
  gap: 16px;
  min-width: 400px;
  z-index: 1000;
}

.player-content {
  flex: 1;
}

.player-info {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.player-title {
  font-weight: 600;
  color: #1f2937;
}

.player-time {
  font-size: 12px;
  color: #6b7280;
}

/* 操作引导部分 */
.action-guide-section {
  margin-bottom: 24px;
}

.action-guide-card {
  background: linear-gradient(135deg, #f8fafc 0%, #f1f5f9 100%);
  padding: 32px;
  border-radius: 12px;
  border: 1px solid #e2e8f0;
}

.guide-content {
  display: flex;
  align-items: center;
  gap: 24px;
}

.guide-icon {
  flex-shrink: 0;
}

.guide-text h3 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 20px;
}

.guide-text p {
  margin: 0 0 16px 0;
  color: #6b7280;
  font-size: 14px;
}

.guide-features {
  display: flex;
  gap: 24px;
  flex-wrap: wrap;
}

.feature-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: #374151;
}

.feature-icon {
  font-size: 16px;
}

/* 空状态部分 */
.empty-results-section {
  margin-bottom: 24px;
}

.empty-card {
  background: white;
  padding: 48px 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  text-align: center;
}

.empty-content {
  max-width: 400px;
  margin: 0 auto;
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-text h3 {
  margin: 0 0 8px 0;
  color: #1f2937;
  font-size: 18px;
}

.empty-text p {
  margin: 0 0 24px 0;
  color: #6b7280;
  font-size: 14px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .page-header {
  flex-direction: column;
    gap: 20px;
    text-align: center;
  }

  .info-card {
    grid-template-columns: repeat(2, 1fr);
  }

  .progress-details {
    grid-template-columns: 1fr;
  }

  .guide-content {
    flex-direction: column;
    text-align: center;
  }

  .guide-features {
    justify-content: center;
  }

  .audio-player {
    left: 16px;
    right: 16px;
    transform: none;
    min-width: auto;
  }
}

/* 新增样式 - 合成配置部分 */
.synthesis-config-section {
  margin-bottom: 24px;
}

.config-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.config-header h3 {
  margin: 0;
  color: #1f2937;
}

.config-content {
  margin-bottom: 16px;
}

.config-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 16px;
  margin-bottom: 20px;
}

.config-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.config-label {
  font-size: 14px;
  color: #6b7280;
  font-weight: 500;
}

.config-value {
  display: flex;
  align-items: center;
}

.character-mapping {
  border-top: 1px solid #e5e7eb;
  padding-top: 20px;
}

.mapping-header {
  margin-bottom: 12px;
}

.mapping-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.mapping-list {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 12px;
}

.mapping-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #f9fafb;
  border-radius: 8px;
  border: 1px solid #e5e7eb;
}



.voice-name {
  font-size: 14px;
  color: #6b7280;
}

/* 合成统计样式 */
.synthesis-stats {
  margin-bottom: 24px;
  padding: 20px;
  background: #f8fafc;
  border-radius: 8px;
  border: 1px solid #e2e8f0;
}

.stats-row {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px;
}

/* 段落详情列表样式 */
.segments-list {
  margin-bottom: 24px;
}

.segments-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #e5e7eb;
}

.segments-title {
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.segments-count {
  font-size: 14px;
  color: #6b7280;
}

.segments-content {
  max-height: 400px;
  overflow-y: auto;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
}

.segment-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px;
  border-bottom: 1px solid #f3f4f6;
  transition: background-color 0.2s ease;
}

.segment-item:last-child {
  border-bottom: none;
}

.segment-item:hover {
  background-color: #f9fafb;
}

.segment-index {
  flex-shrink: 0;
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #06b6d4;
  color: white;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
}

.segment-content {
  flex: 1;
  min-width: 0;
}

.segment-text {
  font-size: 14px;
  color: #1f2937;
  margin-bottom: 8px;
  line-height: 1.5;
  overflow: hidden;
  text-overflow: ellipsis;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
}

.segment-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  font-size: 12px;
}

.segment-speaker {
  color: #06b6d4;
  font-weight: 500;
}

.segment-duration {
  color: #6b7280;
}

.segment-status {
  margin-left: auto;
}

.segment-actions {
  flex-shrink: 0;
  display: flex;
  gap: 4px;
}

/* 响应式优化 */
@media (max-width: 768px) {
  .config-row {
    grid-template-columns: 1fr;
  }
  
  .mapping-list {
    grid-template-columns: 1fr;
  }
  
  .stats-row {
    grid-template-columns: repeat(2, 1fr);
  }
  
  .segment-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .segment-meta {
    width: 100%;
    justify-content: space-between;
  }
  
  .segment-actions {
    width: 100%;
    justify-content: flex-end;
  }
}
</style>