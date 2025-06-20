<template>
  <div class="synthesis-results-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>🎵 合成结果</h1>
        <p v-if="project">{{ project.name }} - 音频合成结果</p>
      </div>
      <div class="header-actions">
        <a-button @click="goBack">
          ← 返回项目列表
        </a-button>
        <a-button type="primary" @click="goToSynthesisCenter">
          🔄 重新合成
        </a-button>
      </div>
    </div>

    <div v-if="loading" class="loading-wrapper">
      <a-spin size="large" tip="加载合成结果...">
        <div style="height: 300px;"></div>
      </a-spin>
    </div>

    <div v-else-if="project" class="results-content">
      <a-row :gutter="24">
        <!-- 左侧：项目信息和统计 -->
        <a-col :span="8">
          <!-- 项目概览 -->
          <a-card title="📋 项目信息" :bordered="false" class="info-card">
            <a-descriptions :column="1" bordered size="small">
              <a-descriptions-item label="项目名称">
                {{ project.name }}
              </a-descriptions-item>
              <a-descriptions-item label="项目状态">
                <a-tag color="green">✅ 已完成</a-tag>
              </a-descriptions-item>
              <a-descriptions-item label="合成时间">
                {{ formatDate(project.completed_at) }}
              </a-descriptions-item>
              <a-descriptions-item label="总段落数">
                {{ audioFiles.length }}
              </a-descriptions-item>
              <a-descriptions-item label="总时长">
                {{ formatDuration(totalDuration) }}
              </a-descriptions-item>
              <a-descriptions-item label="文件大小">
                {{ formatFileSize(totalFileSize) }}
              </a-descriptions-item>
            </a-descriptions>
          </a-card>

          <!-- 快速操作 -->
          <a-card title="🎯 快速操作" :bordered="false" class="action-card">
            <div class="action-buttons">
              <a-button 
                type="primary" 
                size="large" 
                block
                @click="downloadFinalAudio"
                :loading="downloading"
                v-if="project.final_audio_path"
              >
                <DownloadOutlined />
                下载完整音频
              </a-button>
              
              <a-button 
                size="large" 
                block
                @click="downloadAllSegments"
                :loading="downloadingAll"
                style="margin-top: 12px;"
              >
                <FileZipOutlined />
                打包下载所有段落
              </a-button>
              
              <a-button 
                size="large" 
                block
                @click="playAllSequentially"
                :loading="playingAll"
                style="margin-top: 12px;"
              >
                <PlayCircleOutlined />
                连续播放所有段落
              </a-button>
            </div>
          </a-card>

          <!-- 统计信息 -->
          <a-card title="📊 合成统计" :bordered="false" class="stats-card">
            <div class="stats-grid">
              <div class="stat-item">
                <div class="stat-value">{{ audioFiles.length }}</div>
                <div class="stat-label">音频段落</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ characterCount }}</div>
                <div class="stat-label">角色数量</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ Math.round(avgDuration) }}s</div>
                <div class="stat-label">平均时长</div>
              </div>
              <div class="stat-item">
                <div class="stat-value">{{ formatFileSize(avgFileSize) }}</div>
                <div class="stat-label">平均大小</div>
              </div>
            </div>
          </a-card>
        </a-col>

        <!-- 右侧：音频段落列表 -->
        <a-col :span="16">
          <a-card title="🎵 音频段落" :bordered="false" class="segments-card">
            <template #extra>
              <a-space>
                <a-input-search
                  v-model:value="searchKeyword"
                  placeholder="搜索段落内容..."
                  style="width: 200px;"
                  @search="onSearch"
                  allow-clear
                />
                <a-select
                  v-model:value="characterFilter"
                  placeholder="筛选角色"
                  style="width: 120px;"
                  @change="onFilterChange"
                  allow-clear
                >
                  <a-select-option value="">全部角色</a-select-option>
                  <a-select-option 
                    v-for="character in characters" 
                    :key="character"
                    :value="character"
                  >
                    {{ character }}
                  </a-select-option>
                </a-select>
              </a-space>
            </template>

            <div class="segments-list">
              <div 
                v-for="(audio, index) in filteredAudioFiles" 
                :key="audio.id"
                class="segment-item"
                :class="{ 'playing': currentPlayingId === audio.id }"
              >
                <div class="segment-header">
                  <div class="segment-info">
                    <span class="segment-number">段落 {{ index + 1 }}</span>
                    <a-tag 
                      :color="getCharacterColor(audio.character_name || '旁白')"
                      class="character-tag"
                    >
                      {{ audio.character_name || '旁白' }}
                    </a-tag>
                    <span class="segment-duration">{{ formatDuration(audio.duration) }}</span>
                  </div>
                  <div class="segment-actions">
                    <a-button 
                      type="text"
                      size="small"
                      @click="playAudio(audio)"
                      :loading="audio.loading"
                    >
                      <PlayCircleOutlined v-if="currentPlayingId !== audio.id" />
                      <PauseCircleOutlined v-else />
                    </a-button>
                    <a-button 
                      type="text"
                      size="small"
                      @click="downloadSegment(audio)"
                      :loading="audio.downloading"
                    >
                      <DownloadOutlined />
                    </a-button>
                  </div>
                </div>
                
                <div class="segment-content">
                  <p class="segment-text">{{ audio.text_content || '无文本内容' }}</p>
                  
                  <!-- 音频进度条 -->
                  <div v-if="currentPlayingId === audio.id" class="audio-progress">
                    <a-slider
                      v-model:value="audioProgress"
                      :max="100"
                      :tip-formatter="null"
                      @change="seekAudio"
                    />
                    <div class="progress-time">
                      <span>{{ formatTime(currentTime) }}</span>
                      <span>{{ formatTime(audio.duration) }}</span>
                    </div>
                  </div>
                  
                  <!-- 音频信息 -->
                  <div class="audio-meta">
                    <span class="meta-item">📁 {{ audio.filename }}</span>
                    <span class="meta-item">📏 {{ formatFileSize(audio.file_size) }}</span>
                    <span class="meta-item">🎵 {{ audio.sample_rate }}Hz</span>
                    <span class="meta-item">⏱️ {{ formatDuration(audio.processing_time) }}s 合成</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- 分页 -->
            <div class="pagination-wrapper" v-if="filteredAudioFiles.length > pageSize">
              <a-pagination
                v-model:current="currentPage"
                :total="filteredAudioFiles.length"
                :page-size="pageSize"
                :show-size-changer="true"
                :show-quick-jumper="true"
                :show-total="(total, range) => `显示 ${range[0]}-${range[1]} 条，共 ${total} 条`"
                @change="onPageChange"
                @show-size-change="onPageSizeChange"
              />
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 音频播放器 -->
    <audio
      ref="audioPlayer"
      @loadstart="onAudioLoadStart"
      @loadedmetadata="onAudioLoadedMetadata"
      @timeupdate="onAudioTimeUpdate"
      @ended="onAudioEnded"
      @error="onAudioError"
      style="display: none;"
    />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { 
  DownloadOutlined, 
  PlayCircleOutlined, 
  PauseCircleOutlined,
  FileZipOutlined 
} from '@ant-design/icons-vue'
import { readerAPI } from '@/api'

const router = useRouter()
const route = useRoute()
const audioPlayer = ref(null)

// 响应式数据
const loading = ref(true)
const project = ref(null)
const audioFiles = ref([])
const downloading = ref(false)
const downloadingAll = ref(false)
const playingAll = ref(false)
const currentPlayingId = ref(null)
const audioProgress = ref(0)
const currentTime = ref(0)
const searchKeyword = ref('')
const characterFilter = ref('')
const currentPage = ref(1)
const pageSize = ref(10)

// 计算属性
const filteredAudioFiles = computed(() => {
  let filtered = [...audioFiles.value]
  
  // 搜索过滤
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    filtered = filtered.filter(audio => 
      audio.text_content?.toLowerCase().includes(keyword) ||
      audio.filename?.toLowerCase().includes(keyword)
    )
  }
  
  // 角色过滤
  if (characterFilter.value) {
    filtered = filtered.filter(audio => 
      (audio.character_name || '旁白') === characterFilter.value
    )
  }
  
  return filtered
})

const characters = computed(() => {
  const chars = new Set()
  audioFiles.value.forEach(audio => {
    chars.add(audio.character_name || '旁白')
  })
  return Array.from(chars).sort()
})

const characterCount = computed(() => characters.value.length)

const totalDuration = computed(() => {
  return audioFiles.value.reduce((sum, audio) => sum + (audio.duration || 0), 0)
})

const avgDuration = computed(() => {
  return audioFiles.value.length > 0 ? totalDuration.value / audioFiles.value.length : 0
})

const totalFileSize = computed(() => {
  return audioFiles.value.reduce((sum, audio) => sum + (audio.file_size || 0), 0)
})

const avgFileSize = computed(() => {
  return audioFiles.value.length > 0 ? totalFileSize.value / audioFiles.value.length : 0
})

// 方法
const loadProject = async () => {
  const projectId = route.params.projectId
  if (!projectId) {
    message.error('项目ID无效')
    goBack()
    return
  }

  loading.value = true
  try {
    // 加载项目信息
    const projectResponse = await readerAPI.getProject(projectId)
    if (projectResponse.data.success) {
      project.value = projectResponse.data.data
    } else {
      throw new Error(projectResponse.data.message)
    }

    // 加载音频文件
    const audioResponse = await readerAPI.getProjectAudioFiles(projectId)
    if (audioResponse.data.success) {
      audioFiles.value = audioResponse.data.data || []
    } else {
      throw new Error(audioResponse.data.message)
    }

  } catch (error) {
    console.error('加载项目失败:', error)
    message.error('加载项目失败: ' + error.message)
    goBack()
  } finally {
    loading.value = false
  }
}

const goBack = () => {
  router.push('/novel-reader')
}

const goToSynthesisCenter = () => {
  router.push(`/synthesis/${route.params.projectId}`)
}

const playAudio = (audio) => {
  if (currentPlayingId.value === audio.id) {
    // 如果是当前播放的音频，暂停
    audioPlayer.value.pause()
    currentPlayingId.value = null
  } else {
    // 播放新音频
    currentPlayingId.value = audio.id
    audioPlayer.value.src = `/api/v1/audio-library/files/${audio.id}/download`
    audioPlayer.value.play()
  }
}

const downloadSegment = async (audio) => {
  audio.downloading = true
  try {
    const response = await fetch(`/api/v1/audio-library/files/${audio.id}/download`)
    const blob = await response.blob()
    
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = audio.filename || `segment_${audio.id}.wav`
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.URL.revokeObjectURL(url)
    
    message.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  } finally {
    audio.downloading = false
  }
}

const downloadFinalAudio = async () => {
  downloading.value = true
  try {
    const response = await readerAPI.downloadAudio(project.value.id)
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${project.value.name}_完整音频.wav`
    link.click()
    window.URL.revokeObjectURL(url)
    
    message.success('下载成功')
  } catch (error) {
    console.error('下载完整音频失败:', error)
    message.error('下载失败')
  } finally {
    downloading.value = false
  }
}

const downloadAllSegments = async () => {
  downloadingAll.value = true
  try {
    message.info('正在打包下载所有段落，请稍候...')
    
    // 这里需要后端支持批量打包下载
    // 暂时使用逐个下载的方式
    for (let i = 0; i < audioFiles.value.length; i++) {
      const audio = audioFiles.value[i]
      await downloadSegment(audio)
      
      // 避免同时下载太多文件
      if (i < audioFiles.value.length - 1) {
        await new Promise(resolve => setTimeout(resolve, 300))
      }
    }
    
    message.success('所有段落下载完成')
  } catch (error) {
    console.error('批量下载失败:', error)
    message.error('批量下载失败')
  } finally {
    downloadingAll.value = false
  }
}

const playAllSequentially = async () => {
  playingAll.value = true
  try {
    for (const audio of audioFiles.value) {
      await new Promise((resolve) => {
        currentPlayingId.value = audio.id
        audioPlayer.value.src = `/api/v1/audio-library/files/${audio.id}/download`
        audioPlayer.value.play()
        
        audioPlayer.value.onended = () => {
          resolve()
        }
      })
    }
    message.success('连续播放完成')
  } catch (error) {
    console.error('连续播放失败:', error)
    message.error('播放失败')
  } finally {
    playingAll.value = false
    currentPlayingId.value = null
  }
}

const seekAudio = (value) => {
  if (audioPlayer.value) {
    const newTime = (value / 100) * audioPlayer.value.duration
    audioPlayer.value.currentTime = newTime
  }
}

const onSearch = () => {
  currentPage.value = 1
}

const onFilterChange = () => {
  currentPage.value = 1
}

const onPageChange = (page, size) => {
  currentPage.value = page
}

const onPageSizeChange = (current, size) => {
  pageSize.value = size
  currentPage.value = 1
}

// 音频事件处理
const onAudioLoadStart = () => {
  audioProgress.value = 0
  currentTime.value = 0
}

const onAudioLoadedMetadata = () => {
  // 音频元数据加载完成
}

const onAudioTimeUpdate = () => {
  if (audioPlayer.value) {
    currentTime.value = audioPlayer.value.currentTime
    if (audioPlayer.value.duration) {
      audioProgress.value = (audioPlayer.value.currentTime / audioPlayer.value.duration) * 100
    }
  }
}

const onAudioEnded = () => {
  currentPlayingId.value = null
  audioProgress.value = 0
  currentTime.value = 0
}

const onAudioError = (error) => {
  console.error('音频播放错误:', error)
  message.error('音频播放失败')
  currentPlayingId.value = null
}

// 辅助函数
const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatTime = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatFileSize = (bytes) => {
  if (!bytes) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i]
}

const getCharacterColor = (character) => {
  const colors = ['blue', 'green', 'orange', 'red', 'purple', 'cyan', 'magenta', 'lime']
  const hash = character.split('').reduce((a, b) => a + b.charCodeAt(0), 0)
  return colors[hash % colors.length]
}

// 生命周期
onMounted(() => {
  loadProject()
})

onUnmounted(() => {
  if (audioPlayer.value) {
    audioPlayer.value.pause()
  }
})
</script>

<style scoped>
.synthesis-results-container {
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

.info-card, .action-card, .stats-card, .segments-card {
  margin-bottom: 24px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.action-buttons {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.stats-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.stat-item {
  text-align: center;
  padding: 16px;
  background: #fafafa;
  border-radius: 6px;
}

.stat-value {
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.segments-list {
  max-height: 600px;
  overflow-y: auto;
}

.segment-item {

  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 16px;
  transition: all 0.3s;
}

.segment-item:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.segment-item.playing {
  border-color: #52c41a;
  background: #f6ffed;
}

.segment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.segment-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.segment-number {
  font-weight: 600;
  color: #1f2937;
}

.character-tag {
  font-weight: 500;
}

.segment-duration {
  font-size: 12px;
  color: #6b7280;
}

.segment-actions {
  display: flex;
  gap: 8px;
}

.segment-text {
  color: #374151;
  line-height: 1.6;
  margin-bottom: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
}

.audio-progress {
  margin-bottom: 12px;
}

.progress-time {
  display: flex;
  justify-content: space-between;
  font-size: 12px;
  color: #6b7280;
  margin-top: 4px;
}

.audio-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  font-size: 12px;
  color: #6b7280;
}

.meta-item {
  background: #f0f0f0;
  padding: 4px 8px;
  border-radius: 4px;
}

.pagination-wrapper {
  margin-top: 24px;
  text-align: center;
}
</style>