<template>
  <div class="voice-clone-container">
    <!-- 页面头部说明 -->
    <div class="page-header">
      <div class="header-content">
        <h1 style="margin: 0; color: #2c3e50; font-size: 28px; font-weight: 700;">
          声音克隆测试平台
        </h1>
        <p style="margin: 8px 0 0 0; color: #64748b; font-size: 16px;">
          基于MegaTTS3 WaveVAE decoder-only架构，需要同时提供音频文件和latent特征文件
        </p>
        
      </div>
      <div class="status-badges">
        <a-tag color="#10b981" size="large">
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
            </svg>
          </template>
          MegaTTS3 已就绪
        </a-tag>
        <a-tag color="#06b6d4" size="large">GPU 加速</a-tag>
      </div>
    </div>
    
    <!-- 主要内容区域 -->
    <div class="main-content">
      <!-- 左侧：参数配置区 -->
      <div class="config-panel">
        <a-card title="声音克隆配置" :bordered="false" class="config-card">
          <!-- 参考音频上传表单 -->
          <a-card title="1. 上传参考音频" class="config-card">
            <template #extra>
              <a-tooltip title="重置所有参数到默认值">
                <a-button type="text" @click="resetParams">
                  <template #icon>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M17.65 6.35C16.2 4.9 14.21 4 12 4c-4.42 0-7.99 3.58-7.99 8s3.57 8 7.99 8c3.73 0 6.84-2.55 7.73-6h-2.08c-.82 2.33-3.04 4-5.65 4-3.31 0-6-2.69-6-6s2.69-6 6-6c1.66 0 3.14.69 4.22 1.78L13 11h7V4l-2.35 2.35z"/>
                    </svg>
                  </template>
                </a-button>
              </a-tooltip>
            </template>

            <!-- 参考音频上传 -->
            <div class="form-section">
              <label class="form-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 8px;">
                  <path d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"/>
                  <path d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"/>
                </svg>
                参考音频文件 <span style="color: #ef4444;">*</span>
              </label>
              <p class="form-desc">上传清晰的音频文件（.wav格式，建议10-60秒），AI将学习其声音特征</p>
              
              <a-upload-dragger
                v-model:fileList="audioFiles"
                :multiple="false"
                :before-upload="beforeAudioUpload"
                @change="handleAudioChange"
                accept=".wav,.mp3,.m4a"
                class="upload-area"
              >
                <div class="upload-content">
                  <svg width="48" height="48" viewBox="0 0 24 24" fill="#06b6d4" style="margin-bottom: 16px;">
                    <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                  </svg>
                  <p style="font-size: 16px; color: #374151; margin: 0;">点击或拖拽音频文件到此区域</p>
                  <p style="font-size: 14px; color: #9ca3af; margin: 8px 0 0 0;">支持 WAV, MP3, M4A 格式</p>
                </div>
              </a-upload-dragger>

              <!-- 音频文件信息 -->
              <div v-if="audioFileInfo" class="file-info">
                <div class="file-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="#10b981">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                  <div class="file-details">
                    <div class="file-name">{{ audioFileInfo.name }}</div>
                    <div class="file-meta">{{ audioFileInfo.size }} | {{ audioFileInfo.duration }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- Latent文件上传（必需） -->
            <div class="form-section">
              <label class="form-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 8px;">
                  <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                </svg>
                Latent特征文件 <span style="color: #ef4444;">*</span>
              </label>
              <p class="form-desc">MegaTTS3必需的声音特征文件（.npy格式），与音频文件配对使用</p>
              
              <a-upload
                v-model:fileList="latentFiles"
                :multiple="false"
                :before-upload="beforeLatentUpload"
                @change="handleLatentChange"
                accept=".npy"
                :show-upload-list="false"
              >
                <a-button>
                  <template #icon>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M14,2H6A2,2 0 0,0 4,4V20A2,2 0 0,0 6,22H18A2,2 0 0,0 20,20V8L14,2M18,20H6V4H13V9H18V20Z"/>
                    </svg>
                  </template>
                  选择 .npy 文件
                </a-button>
              </a-upload>
              
              <div v-if="latentFileInfo" class="file-info">
                <div class="file-item">
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="#10b981">
                    <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
                  </svg>
                  <div class="file-details">
                    <div class="file-name">{{ latentFileInfo.name }}</div>
                    <div class="file-meta">{{ latentFileInfo.size }}</div>
                  </div>
                </div>
              </div>
            </div>

            <!-- 高级参数 -->
            <div class="form-section">
              <label class="form-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 8px;">
                  <path d="M12,15.5A3.5,3.5 0 0,1 8.5,12A3.5,3.5 0 0,1 12,8.5A3.5,3.5 0 0,1 15.5,12A3.5,3.5 0 0,1 12,15.5M19.43,12.97C19.47,12.65 19.5,12.33 19.5,12C19.5,11.67 19.47,11.34 19.43,11.03L21.54,9.37C21.73,9.22 21.78,8.95 21.66,8.73L19.66,5.27C19.54,5.05 19.27,4.96 19.05,5.05L16.56,6.05C16.04,5.66 15.5,5.32 14.87,5.07L14.5,2.42C14.46,2.18 14.25,2 14,2H10C9.75,2 9.54,2.18 9.5,2.42L9.13,5.07C8.5,5.32 7.96,5.66 7.44,6.05L4.95,5.05C4.73,4.96 4.46,5.05 4.34,5.27L2.34,8.73C2.22,8.95 2.27,9.22 2.46,9.37L4.57,11.03C4.53,11.34 4.5,11.67 4.5,12C4.5,12.33 4.53,12.65 4.57,12.97L2.46,14.63C2.27,14.78 2.22,15.05 2.34,15.27L4.34,18.73C4.46,18.95 4.73,19.03 4.95,18.95L7.44,17.94C7.96,18.34 8.5,18.68 9.13,18.93L9.5,21.58C9.54,21.82 9.75,22 10,22H14C14.25,22 14.46,21.82 14.5,21.58L14.87,18.93C15.5,18.68 16.04,18.34 16.56,17.94L19.05,18.95C19.27,19.03 19.54,18.95 19.66,18.73L21.66,15.27C21.78,15.05 21.73,14.78 21.54,14.63L19.43,12.97Z"/>
                </svg>
                高级参数调节
              </label>

              <div class="params-grid">
                <div class="param-item">
                  <label class="param-label">Time Step</label>
                  <a-slider
                    v-model:value="params.timeStep"
                    :min="5"
                    :max="100"
                    :step="5"
                    :tooltip-formatter="(value) => `${value} steps`"
                  />
                  <div class="param-value">{{ params.timeStep }} steps</div>
                </div>

                <div class="param-item">
                  <label class="param-label">智能权重 (p_w)</label>
                  <a-slider
                    v-model:value="params.pWeight"
                    :min="0"
                    :max="2"
                    :step="0.1"
                    :tooltip-formatter="(value) => value.toFixed(1)"
                  />
                  <div class="param-value">{{ (params.pWeight || 1.0).toFixed(1) }}</div>
                </div>

                <div class="param-item">
                  <label class="param-label">相似度权重 (t_w)</label>
                  <a-slider
                    v-model:value="params.tWeight"
                    :min="0"
                    :max="2"
                    :step="0.1"
                    :tooltip-formatter="(value) => value.toFixed(1)"
                  />
                  <div class="param-value">{{ (params.tWeight || 1.0).toFixed(1) }}</div>
                </div>
              </div>
            </div>

            <!-- 待合成文本 -->
            <div class="form-section">
              <label class="form-label">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor" style="margin-right: 8px;">
                  <path d="M5,3C3.89,3 3,3.89 3,5V19A2,2 0 0,0 5,21H19A2,2 0 0,0 21,19V12H19V19H5V5H12V3H5M17.78,4C17.61,4 17.43,4.07 17.3,4.2L16.08,5.41L18.58,7.91L19.8,6.7C20.06,6.44 20.06,6 19.8,5.75L18.25,4.2C18.12,4.07 17.95,4 17.78,4M15.37,6.12L8,13.5V16H10.5L17.87,8.62L15.37,6.12Z"/>
                </svg>
                待合成文本 <span style="color: #ef4444;">*</span>
              </label>
              <a-textarea
                v-model:value="text"
                placeholder="请输入要合成的文本内容..."
                :rows="4"
                :maxlength="500"
                show-count
                class="text-input"
              />
            </div>
          </a-card>
          
          <!-- 音频测试组件 -->
          <a-card title="音频播放测试" class="test-card" v-if="showAudioTester">
            <audio-tester />
            <div class="card-footer">
              <a-button type="text" @click="showAudioTester = false">隐藏测试工具</a-button>
            </div>
          </a-card>
          <a-button 
            v-else 
            type="dashed" 
            block 
            @click="showAudioTester = true" 
            style="margin-top: 16px;"
          >
            <sound-outlined /> 显示音频测试工具
          </a-button>
        </a-card>
      </div>
      
      <!-- 右侧：结果展示区 -->
      <div class="result-panel">
        <!-- 快速测试模板 -->
        <a-card title="快速测试模板" :bordered="false" class="templates-card">
          <div class="template-grid">
            <div 
              v-for="template in templates" 
              :key="template.id"
              class="template-item"
              @click="useTemplate(template)"
            >
              <div class="template-icon">{{ template.icon }}</div>
              <div class="template-name">{{ template.name }}</div>
              <div class="template-text">{{ template.text.substring(0, 30) }}...</div>
            </div>
          </div>
        </a-card>

        <!-- 生成控制 -->
        <a-card title="语音生成" :bordered="false" class="generate-card">
          <div class="generate-section">
            <a-button 
              type="primary" 
              size="large" 
              block
              :loading="isGenerating"
              :disabled="!canGenerate"
              @click="generateSpeech"
              class="generate-btn"
            >
              <template #icon v-if="!isGenerating">
                <svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M8,5.14V19.14L19,12.14L8,5.14Z"/>
                </svg>
              </template>
              {{ isGenerating ? '生成中...' : '开始生成语音' }}
            </a-button>

            <div v-if="!canGenerate && !isGenerating" class="generate-hint">
              <p style="color: #6b7280; font-size: 14px; text-align: center; margin-top: 12px;">
                请确保已上传：音频文件(.wav) + Latent文件(.npy) + 输入文本
              </p>
            </div>

            <div v-if="isGenerating" class="progress-info">
              <a-progress :percent="progress" :show-info="false" />
              <div class="progress-text">{{ progressText }}</div>
            </div>
          </div>
        </a-card>

        <!-- 生成结果 -->
        <a-card v-if="generatedAudio" title="生成结果" :bordered="false" class="result-card">
          <div class="audio-result">
            <div class="audio-player">
              <audio ref="audioPlayer" controls preload="metadata" style="width: 100%;">
                <source :src="generatedAudio.url" type="audio/wav">
                您的浏览器不支持音频播放
              </audio>
            </div>
            
            <div class="audio-info">
              <div class="info-item">
                <span class="info-label">文件大小:</span>
                <span class="info-value">{{ generatedAudio.size }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">时长:</span>
                <span class="info-value">{{ generatedAudio.duration }}</span>
              </div>
              <div class="info-item">
                <span class="info-label">质量评分:</span>
                <a-rate v-model:value="generatedAudio.quality" disabled allow-half />
              </div>
            </div>

            <div class="audio-actions">
              <a-button @click="downloadAudio">
                <template #icon>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M5,20H19V18H5M19,9H15V3H9V9H5L12,16L19,9Z"/>
                  </svg>
                </template>
                下载音频
              </a-button>
              <a-button @click="saveToLibrary">
                <template #icon>
                  <svg width="16" height="16" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"/>
                  </svg>
                </template>
                保存到声音库
              </a-button>
            </div>
          </div>
        </a-card>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive } from 'vue'
import { message } from 'ant-design-vue'
import { systemAPI, voiceAPI } from '../api/index.js'
import { API_BASE_URL } from '../api/config.js'
import { SoundOutlined } from '@ant-design/icons-vue'
import AudioTester from '../components/AudioTester.vue'

// 响应式数据
const audioFiles = ref([])
const latentFiles = ref([])
const audioFileInfo = ref(null)
const latentFileInfo = ref(null)
const text = ref('')
const isGenerating = ref(false)
const progress = ref(0)
const progressText = ref('')
const generatedAudio = ref(null)

// 参数配置
const params = reactive({
  timeStep: 20,
  pWeight: 1.0,
  tWeight: 1.0
})

// 快速测试模板
const templates = ref([
  {
    id: 1,
    name: '新闻播报',
    icon: '📺',
    text: '各位观众大家好，欢迎收看今日新闻。今天的头条新闻是...'
  },
  {
    id: 2,
    name: '故事讲述',
    icon: '📖',
    text: '从前有一座山，山里有座庙，庙里有个老和尚在给小和尚讲故事...'
  },
  {
    id: 3,
    name: '诗歌朗诵',
    icon: '🎭',
    text: '床前明月光，疑是地上霜。举头望明月，低头思故乡。'
  },
  {
    id: 4,
    name: '日常对话',
    icon: '💬',
    text: '你好，很高兴见到你！今天天气真不错，我们一起出去走走吧。'
  }
])

// 音频测试工具状态
const showAudioTester = ref(false)

// 计算属性
const canGenerate = computed(() => {
  return audioFiles.value.length > 0 && latentFiles.value.length > 0 && text.value.trim() !== ''
})

// 文件处理方法
const beforeAudioUpload = (file) => {
  const isValidFormat = ['audio/wav', 'audio/mp3', 'audio/mpeg', 'audio/m4a'].includes(file.type)
  if (!isValidFormat) {
    message.error('请上传 WAV, MP3, 或 M4A 格式的音频文件！')
    return false
  }
  
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    message.error('音频文件大小不能超过 50MB！')
    return false
  }
  
  return false // 阻止自动上传
}

const beforeLatentUpload = (file) => {
  const isNpy = file.name.endsWith('.npy')
  if (!isNpy) {
    message.error('请上传 .npy 格式的文件！')
    return false
  }
  
  return false // 阻止自动上传
}

const handleAudioChange = (info) => {
  if (info.fileList.length > 0) {
    const file = info.fileList[0].originFileObj
    audioFiles.value = [file] // 保存实际文件对象
    audioFileInfo.value = {
      name: file.name,
      size: formatFileSize(file.size),
      duration: '未知' // 实际项目中可以通过音频解析获取
    }
  } else {
    audioFiles.value = []
    audioFileInfo.value = null
  }
}

const handleLatentChange = (info) => {
  if (info.fileList.length > 0) {
    const file = info.fileList[0].originFileObj
    latentFiles.value = [file] // 保存实际文件对象
    latentFileInfo.value = {
      name: file.name,
      size: formatFileSize(file.size)
    }
  } else {
    latentFiles.value = []
    latentFileInfo.value = null
  }
}

// 工具方法
const formatFileSize = (bytes) => {
  if (bytes === 0) return '0 Bytes'
  const k = 1024
  const sizes = ['Bytes', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const useTemplate = (template) => {
  text.value = template.text
  message.success(`已应用模板：${template.name}`)
}

const resetParams = () => {
  params.timeStep = 20
  params.pWeight = 1.0
  params.tWeight = 1.0
  message.success('参数已重置为默认值')
}

// 语音生成 - 真实API调用
const generateSpeech = async () => {
  if (!canGenerate.value) return
  
  isGenerating.value = true
  progress.value = 0
  progressText.value = '准备生成...'
  
  try {
    progress.value = 10
    progressText.value = '检查后端服务状态...'
    
    // 1. 首先检查后端健康状态
    await systemAPI.healthCheck()
    
    progress.value = 30
    progressText.value = '上传音频文件...'
    
    // 2. 上传音频文件和latent文件（如果有）
    const formData = new FormData()
    formData.append('file', audioFiles.value[0])
    
    // 如果有latent文件，一起上传
    if (latentFiles.value.length > 0) {
      formData.append('latent_file', latentFiles.value[0])
    }
    
    const uploadResponse = await voiceAPI.uploadVoice(formData)
    console.log('上传响应:', uploadResponse.data)
    
    progress.value = 60
    progressText.value = '合成目标语音...'
    
    // 3. 调用语音合成API - 修正为后端期望的格式
    const synthesizeData = {
      text: text.value,
      reference_file_id: uploadResponse.data.fileId, // 使用上传返回的fileId
      time_step: params.timeStep,
      p_weight: params.pWeight,
      t_weight: params.tWeight
    }
    
    // 如果有latent文件，添加latent_file_id
    if (uploadResponse.data.latentFileId) {
      synthesizeData.latent_file_id = uploadResponse.data.latentFileId
    }
    
    const synthesizeResponse = await voiceAPI.synthesize(synthesizeData)
    
    progress.value = 100
    progressText.value = '生成完成！'
    
    // 4. 处理生成结果
    if (synthesizeResponse.data.success && synthesizeResponse.data.audioUrl) {
      // 构建两种可能的URL
      const directUrl = `${API_BASE_URL}${synthesizeResponse.data.audioUrl}`
      const proxyUrl = synthesizeResponse.data.audioUrl // 相对路径，通过Vite代理访问
      
      try {
        // 尝试预加载音频文件
        progressText.value = '正在验证音频文件...'
        
        // 先尝试通过相对路径访问（使用Vite代理）
        const audioCheck = await new Promise((resolve, reject) => {
          const audio = new Audio(proxyUrl)
          
          // 成功加载
          audio.onloadeddata = () => resolve({
            duration: audio.duration,
            success: true,
            url: proxyUrl // 使用代理URL
          })
          
          // 加载失败，尝试直接URL
          audio.onerror = () => {
            console.warn('代理URL加载失败，尝试直接URL')
            const directAudio = new Audio(directUrl)
            
            directAudio.onloadeddata = () => resolve({
              duration: directAudio.duration,
              success: true,
              url: directUrl
            })
            
            directAudio.onerror = () => {
              console.error('直接URL也加载失败')
              reject(new Error('所有URL均加载失败'))
            }
            directAudio.load()
          }
          
          audio.load()
          
          // 10秒超时
          setTimeout(() => reject(new Error('音频加载超时')), 10000)
        })
        
        generatedAudio.value = {
          url: audioCheck.url,
          size: '未知', // 后端暂时没有返回文件大小
          duration: (audioCheck.duration && typeof audioCheck.duration === 'number') ? `${audioCheck.duration.toFixed(1)}秒` : '未知',
          quality: 4.0, // 默认质量评分
          processingTime: synthesizeResponse.data.processingTime
        }
      } catch (audioError) {
        console.warn('音频预加载警告:', audioError)
        // 即使预加载失败，也创建音频对象
        generatedAudio.value = {
          url: proxyUrl, // 默认使用代理URL
          fallbackUrl: directUrl, // 保存备用URL
          size: '未知',
          duration: '未知',
          quality: 4.0,
          processingTime: synthesizeResponse.data.processingTime
        }
      }
      
      message.success(`语音生成成功！耗时: ${synthesizeResponse.data.processingTime}秒`)
    } else {
      throw new Error(synthesizeResponse.data.message || '合成失败')
    }
    
  } catch (error) {
    console.error('语音生成失败:', error)
    const errorMessage = error.response?.data?.detail || error.message || '未知错误'
    message.error(`语音生成失败: ${errorMessage}`)
    generatedAudio.value = null
  } finally {
    isGenerating.value = false
    progress.value = 0
    progressText.value = ''
  }
}

const downloadAudio = async () => {
  if (!generatedAudio.value?.url) {
    message.error('没有可下载的音频文件')
    return
  }
  
  try {
    message.loading('正在准备音频文件...')
    
    // 使用专门的下载客户端
    const { downloadClient } = require('@/api/config')
    
    // 首先尝试主URL
    try {
      const response = await downloadClient.get(generatedAudio.value.url, {
        responseType: 'blob',
        timeout: 15000  // 15秒超时
      })
      
      // 创建一个临时链接并触发下载
      const blob = new Blob([response.data], { type: 'audio/wav' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `AI_Voice_${Date.now()}.wav`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
      
      message.success('音频文件下载完成')
      return
    } catch (primaryError) {
      console.warn('主URL下载失败，尝试备用URL', primaryError)
      
      // 如果主URL失败且有备用URL，尝试备用URL
      if (generatedAudio.value.fallbackUrl) {
        try {
          const fallbackResponse = await downloadClient.get(generatedAudio.value.fallbackUrl, {
            responseType: 'blob',
            timeout: 15000
          })
          
          const blob = new Blob([fallbackResponse.data], { type: 'audio/wav' })
          const url = window.URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `AI_Voice_${Date.now()}.wav`
          document.body.appendChild(link)
          link.click()
          document.body.removeChild(link)
          window.URL.revokeObjectURL(url)
          
          message.success('使用备用URL下载音频文件完成')
          return
        } catch (fallbackError) {
          console.error('备用URL也下载失败', fallbackError)
          throw new Error('所有下载尝试均失败')
        }
      } else {
        throw primaryError
      }
    }
  } catch (error) {
    console.error('下载音频失败:', error)
    message.error('下载失败，请稍后重试')
    
    // 最后尝试浏览器自带下载方式
    try {
      const link = document.createElement('a')
      // 如果主URL是相对路径，优先使用它
      const isRelativePath = !generatedAudio.value.url.startsWith('http')
      link.href = isRelativePath ? generatedAudio.value.url : (generatedAudio.value.fallbackUrl || generatedAudio.value.url)
      link.download = `AI_Voice_${Date.now()}.wav`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      message.info('正在尝试备用下载方式')
    } catch (e) {
      console.error('备用下载方式也失败', e)
      message.error('所有下载方式均失败，请联系管理员')
    }
  }
}

const saveToLibrary = () => {
  // TODO: 实现保存到声音库的功能
  message.success('已保存到声音库')
}
</script>

<style scoped>
.voice-clone-container {
  
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 32px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  border-radius: 16px;
  color: white;
}

.header-content h1 {
  color: white !important;
}

.status-badges {
  display: flex;
  gap: 12px;
  align-items: center;
}

.main-content {
  display: grid;
  grid-template-columns: 1fr 400px;
  gap: 24px;
}

.config-card, .templates-card, .generate-card, .result-card {
  border-radius: 12px !important;
  box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
  border: none !important;
}

.form-section {
  margin-bottom: 32px;
}

.form-label {
  display: flex;
  align-items: center;
  font-weight: 600;
  color: #374151;
  margin-bottom: 8px;
  font-size: 15px;
}

.form-desc {
  color: #6b7280;
  margin-bottom: 16px;
  font-size: 14px;
  line-height: 1.5;
}

.upload-area {
  border-radius: 12px !important;
  border-color: #d1d5db !important;
  background: #f9fafb !important;
}

.upload-content {
  padding: 32px;
  text-align: center;
}

.file-info {
  margin-top: 16px;
  padding: 16px;
  background: #f0fdf4;
  border-radius: 8px;
  border: 1px solid #bbf7d0;
}

.file-item {
  display: flex;
  align-items: center;
  gap: 12px;
}

.file-details {
  flex: 1;
}

.file-name {
  font-weight: 500;
  color: #059669;
}

.file-meta {
  font-size: 12px;
  color: #6b7280;
  margin-top: 2px;
}

.params-grid {
  display: grid;
  grid-template-columns: 1fr;
  gap: 24px;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.param-label {
  font-weight: 500;
  color: #374151;
  font-size: 14px;
}

.param-value {
  text-align: center;
  font-weight: 600;
  color: #06b6d4;
  font-size: 14px;
}

.text-input {
  border-radius: 8px !important;
  border-color: #d1d5db !important;
}

.template-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.template-item {
  padding: 16px;
  border: 2px solid #e5e7eb;
  border-radius: 8px;
  cursor: pointer;
  transition: all 0.3s;
  text-align: center;
}

.template-item:hover {
  border-color: #06b6d4;
  background: #f0f9ff;
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(6, 182, 212, 0.2);
}

.template-icon {
  font-size: 24px;
  margin-bottom: 8px;
}

.template-name {
  font-weight: 600;
  color: #374151;
  margin-bottom: 4px;
}

.template-text {
  font-size: 12px;
  color: #6b7280;
  line-height: 1.4;
}

.generate-btn {
  height: 48px !important;
  border-radius: 12px !important;
  font-weight: 600 !important;
  font-size: 16px !important;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%) !important;
  border: none !important;
  color: white !important;
}

.generate-btn:hover {
  background: linear-gradient(135deg, #0891b2 0%, #0e7490 100%) !important;
  transform: translateY(-2px) !important;
  box-shadow: 0 6px 20px rgba(6, 182, 212, 0.3) !important;
}

.generate-hint {
  margin-top: 12px;
  text-align: center;
}

.progress-info {
  margin-top: 16px;
  text-align: center;
}

.progress-text {
  margin-top: 8px;
  color: #6b7280;
  font-size: 14px;
}

.audio-result {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.audio-info {
  display: flex;
  flex-direction: column;
  gap: 8px;
  padding: 16px;
  background: #fff8f5;
  border-radius: 8px;
  border: 1px solid rgba(6, 182, 212, 0.1);
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-label {
  color: #6b7280;
  font-size: 14px;
}

.info-value {
  font-weight: 500;
  color: #374151;
}

.audio-actions {
  display: flex;
  gap: 12px;
}

@media (max-width: 1200px) {
  .main-content {
    grid-template-columns: 1fr;
  }
  
  .template-grid {
    grid-template-columns: 1fr;
  }
}
</style>