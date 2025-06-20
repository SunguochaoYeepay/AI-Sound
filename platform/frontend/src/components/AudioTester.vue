<template>
  <div class="audio-tester">
    <h3 class="tester-title">音频播放测试</h3>
    
    <div class="tester-content">
      <!-- 内置测试声音 -->
      <div class="test-section">
        <h4>1. 内置测试声音</h4>
        <div class="audio-controls">
          <a-button type="primary" @click="playBuiltInSound" :loading="isPlayingBuiltIn">
            播放内置测试声音
          </a-button>
          <span class="result-indicator" :class="builtInResult">
            {{ getResultText(builtInResult) }}
          </span>
        </div>
      </div>
      
      <!-- API音频测试 -->
      <div class="test-section">
        <h4>2. API音频测试</h4>
        <div class="audio-controls">
          <a-button @click="testApiAudio" :loading="isTestingApi">
            测试API音频
          </a-button>
          <span class="result-indicator" :class="apiResult">
            {{ getResultText(apiResult) }}
          </span>
        </div>
        <div v-if="apiAudioUrl" class="api-audio">
          <p>API音频:</p>
          <audio controls :src="apiAudioUrl"></audio>
        </div>
      </div>
      
      <!-- 自定义URL测试 -->
      <div class="test-section">
        <h4>3. 自定义URL测试</h4>
        <div class="url-input">
          <a-input v-model:value="customUrl" placeholder="输入音频URL..." />
          <a-button @click="testCustomUrl" :loading="isTestingCustom">测试</a-button>
        </div>
        <div v-if="customAudioElement" class="custom-audio">
          <p>自定义音频:</p>
          <div ref="customAudioContainer"></div>
        </div>
        <div v-if="customResult" class="test-result">
          <span class="result-indicator" :class="customResult">
            {{ getResultText(customResult) }}
          </span>
        </div>
      </div>
      
      <!-- 音频设置 -->
      <div class="test-section">
        <h4>4. 浏览器音频设置</h4>
        <div class="audio-settings">
          <p>音量: <span class="volume-value">{{ volume }}%</span></p>
          <a-slider v-model:value="volume" :min="0" :max="100" @change="updateVolume" />
          <div class="settings-info">
            <p>浏览器: {{ browserInfo }}</p>
            <p>音频支持: {{ audioSupport }}</p>
          </div>
        </div>
      </div>
    </div>
    
    <div class="test-results">
      <h4>测试报告</h4>
      <ul>
        <li v-for="(log, index) in testLogs" :key="index" :class="getLogClass(log)">
          {{ log }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { API_BASE_URL } from '@/api/config'

// 音频测试状态
const isPlayingBuiltIn = ref(false)
const isTestingApi = ref(false)
const isTestingCustom = ref(false)

// 测试结果
const builtInResult = ref('')
const apiResult = ref('')
const customResult = ref('')

// 测试URL和音频元素
const apiAudioUrl = ref('')
const customUrl = ref('')
const customAudioElement = ref(null)
const customAudioContainer = ref(null)

// 音量控制
const volume = ref(80)

// 测试日志
const testLogs = ref([])

// 浏览器信息
const browserInfo = ref('')
const audioSupport = ref('')

// 播放内置测试声音
const playBuiltInSound = () => {
  isPlayingBuiltIn.value = true
  builtInResult.value = 'pending'
  testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 播放内置测试声音...`)
  
  try {
    // 创建一个简单的音频上下文和振荡器
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const oscillator = audioContext.createOscillator()
    const gainNode = audioContext.createGain()
    
    // 设置音量
    gainNode.gain.value = volume.value / 100
    
    // 设置音调和类型
    oscillator.type = 'sine'
    oscillator.frequency.setValueAtTime(440, audioContext.currentTime) // A4音符
    
    // 连接节点
    oscillator.connect(gainNode)
    gainNode.connect(audioContext.destination)
    
    // 播放声音
    oscillator.start()
    
    // 1秒后停止
    setTimeout(() => {
      oscillator.stop()
      audioContext.close()
      isPlayingBuiltIn.value = false
      builtInResult.value = 'success'
      testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 内置声音播放成功`)
    }, 1000)
  } catch (error) {
    console.error('播放内置声音失败:', error)
    isPlayingBuiltIn.value = false
    builtInResult.value = 'error'
    testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 内置声音播放失败: ${error.message}`)
  }
}

// 测试API音频
const testApiAudio = async () => {
  isTestingApi.value = true
  apiResult.value = 'pending'
  apiAudioUrl.value = ''
  testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 测试API音频...`)
  
  try {
    // 构建测试URL – 优先使用相对路径（通过nginx代理）
    const relativeUrl = '/audio/test_static_service.wav'
    const absoluteUrl = `${API_BASE_URL}/audio/test_static_service.wav`
    
    // 优先尝试相对路径（nginx代理）
    try {
      const relativeCheck = await fetch(relativeUrl, { method: 'HEAD' })
      
      if (relativeCheck.ok) {
        apiAudioUrl.value = relativeUrl
        testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] API音频加载成功: ${relativeUrl}`)
        apiResult.value = 'success'
        return
      }
    } catch (e) {
      console.warn('相对路径检查失败', e)
    }
    
    // 如果相对路径失败，尝试绝对路径
    try {
      const absoluteCheck = await fetch(absoluteUrl, { method: 'HEAD' })
      
      if (absoluteCheck.ok) {
        apiAudioUrl.value = absoluteUrl
        testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] API音频加载成功: ${absoluteUrl}`)
        apiResult.value = 'success'
        return
      }
    } catch (e) {
      console.warn('绝对路径检查失败', e)
    }
    
    // 都失败了，抛出错误
    throw new Error('API音频文件不可访问')
  } catch (error) {
    console.error('API音频测试失败:', error)
    testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] API音频测试失败: ${error.message}`)
    apiResult.value = 'error'
    
    // 提供一个默认的测试音频
    apiAudioUrl.value = 'https://actions.google.com/sounds/v1/alarms/beep_short.ogg'
    testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 使用默认测试音频`)
  } finally {
    isTestingApi.value = false
  }
}

// 测试自定义URL
const testCustomUrl = async () => {
  if (!customUrl.value) {
    message.warning('请输入音频URL')
    return
  }
  
  isTestingCustom.value = true
  customResult.value = 'pending'
  
  // 移除之前的音频元素
  if (customAudioContainer.value) {
    while (customAudioContainer.value.firstChild) {
      customAudioContainer.value.removeChild(customAudioContainer.value.firstChild)
    }
  }
  
  customAudioElement.value = null
  testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 测试自定义URL: ${customUrl.value}`)
  
  try {
    // 创建新的音频元素
    const audio = document.createElement('audio')
    audio.controls = true
    audio.style.width = '100%'
    
    // 设置音量
    audio.volume = volume.value / 100
    
    // 监听事件
    audio.onloadeddata = () => {
      isTestingCustom.value = false
      customResult.value = 'success'
      testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 自定义音频加载成功: ${(audio.duration || 0).toFixed(2)}秒`)
    }
    
    audio.onerror = (e) => {
      isTestingCustom.value = false
      customResult.value = 'error'
      testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 自定义音频加载失败`)
    }
    
    // 设置源
    audio.src = customUrl.value
    
    // 添加到容器
    customAudioContainer.value.appendChild(audio)
    customAudioElement.value = audio
    
    // 触发加载
    audio.load()
    
    // 15秒超时
    setTimeout(() => {
      if (customResult.value === 'pending') {
        customResult.value = 'error'
        isTestingCustom.value = false
        testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 自定义音频加载超时`)
      }
    }, 15000)
  } catch (error) {
    console.error('自定义URL测试失败:', error)
    isTestingCustom.value = false
    customResult.value = 'error'
    testLogs.value.unshift(`[${new Date().toLocaleTimeString()}] 自定义URL测试失败: ${error.message}`)
  }
}

// 更新音量
const updateVolume = (val) => {
  // 更新自定义音频元素的音量
  if (customAudioElement.value) {
    customAudioElement.value.volume = val / 100
  }
}

// 获取结果文字
const getResultText = (result) => {
  switch (result) {
    case 'success': return '成功'
    case 'error': return '失败'
    case 'pending': return '测试中...'
    default: return ''
  }
}

// 获取日志类
const getLogClass = (log) => {
  if (log.includes('成功')) return 'success-log'
  if (log.includes('失败') || log.includes('错误')) return 'error-log'
  return ''
}

// 检测浏览器音频支持
const checkAudioSupport = () => {
  browserInfo.value = navigator.userAgent
  
  const support = []
  
  // 检查基本音频API
  if ('Audio' in window) support.push('HTML5 Audio')
  if ('AudioContext' in window || 'webkitAudioContext' in window) support.push('Web Audio API')
  
  // 检查音频格式支持
  const audio = document.createElement('audio')
  if (audio.canPlayType) {
    const formats = {
      'audio/wav': 'WAV',
      'audio/mpeg': 'MP3',
      'audio/ogg': 'OGG',
      'audio/mp4': 'AAC'
    }
    
    for (const [mime, name] of Object.entries(formats)) {
      const support = audio.canPlayType(mime)
      if (support) support.push(`${name} (${support})`)
    }
  }
  
  audioSupport.value = support.join(', ') || '未检测到音频支持'
}

// 组件挂载时
onMounted(() => {
  checkAudioSupport()
  testLogs.value.push(`[${new Date().toLocaleTimeString()}] 音频测试组件初始化完成`)
})
</script>

<style scoped>
.audio-tester {
  border: 1px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background-color: #f9f9f9;
}

.tester-title {
  margin: 0 0 16px 0;
  font-size: 18px;
  color: #1890ff;
  font-weight: 600;
}

.tester-content {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.test-section {
  padding: 16px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.test-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #444;
}

.audio-controls {
  display: flex;
  align-items: center;
  gap: 12px;
}

.result-indicator {
  font-size: 14px;
  font-weight: 500;
}

.result-indicator.success {
  color: #52c41a;
}

.result-indicator.error {
  color: #f5222d;
}

.result-indicator.pending {
  color: #faad14;
}

.url-input {
  display: flex;
  gap: 8px;
  margin-bottom: 12px;
}

.api-audio, .custom-audio {
  margin-top: 12px;
}

.audio-settings {
  margin-top: 12px;
}

.volume-value {
  font-weight: 600;
  color: #1890ff;
}

.settings-info {
  margin-top: 12px;
  font-size: 12px;
  color: #888;
}

.test-results {
  margin-top: 20px;
  padding: 16px;
  border-radius: 6px;
  box-shadow: 0 2px 6px rgba(0, 0, 0, 0.05);
}

.test-results h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  color: #444;
}

.test-results ul {
  max-height: 150px;
  overflow-y: auto;
  margin: 0;
  padding: 0 0 0 20px;
  font-family: monospace;
  font-size: 12px;
}

.success-log {
  color: #52c41a;
}

.error-log {
  color: #f5222d;
}
</style> 