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
          <span class="info-label">角色数量</span>
          <span class="info-value">{{ getCharacterCount(currentProject) }} 个</span>
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

    

    <!-- 角色配置 -->
    <div v-if="characters.length > 0" class="characters-section">
      <div class="characters-card">
        <div class="characters-header">
          <h3>角色配置</h3>
          <div class="character-actions">
            <span class="character-count">{{ characters.length }} 个角色</span>
            <a-button type="primary" size="small" @click="autoAssignVoices" :loading="autoAssigning">
              <template #icon>
                <SoundOutlined />
              </template>
              自动分配声音
            </a-button>
            <a-button size="small" @click="showCharacterConfig = true">
              <template #icon>
                <SettingOutlined />
          </template>
              配置角色
            </a-button>
            </div>
        </div>
        <div class="characters-list">
          <div v-for="character in characters" :key="character.name" class="character-item">
                <div class="character-info">
              <div class="character-avatar">
                    {{ character.name.charAt(0) }}
                  </div>
                  <div class="character-details">
                    <div class="character-name">{{ character.name }}</div>
                <div class="character-lines">{{ character.line_count || 0 }} 句对话</div>
                  </div>
                </div>
            <div class="voice-assignment">
                  <a-select
                v-model:value="character.voice_id" 
                    placeholder="选择声音"
                style="width: 200px;"
                @change="updateCharacterMapping"
                :loading="loadingVoices"
              >
                <a-select-option value="">使用默认声音</a-select-option>
                    <a-select-option
                      v-for="voice in availableVoices"
                      :key="voice.id"
                      :value="voice.id"
                    >
                  {{ voice.name }} ({{ getVoiceTypeText(voice.type) }})
                    </a-select-option>
                  </a-select>
                  <a-button 
                v-if="character.voice_id" 
                    type="text" 
                    size="small" 
                @click="playVoicePreview(character)"
                  >
                    <template #icon>
                  <PlayCircleOutlined />
                    </template>
                  </a-button>
                </div>
              </div>
            </div>
          </div>
          </div>

    <!-- 空状态 - 等待角色配置 -->
    <div v-else-if="currentProject?.segments?.length > 0" class="empty-characters-section">
      <div class="empty-card">
        <div class="empty-content">
          <div class="empty-icon">
            <SoundOutlined style="font-size: 48px; color: #d9d9d9;" />
          </div>
          <div class="empty-text">
            <h3>暂无角色配置</h3>
            <p>系统将使用默认声音进行合成</p>
            <a-button type="primary" @click="extractCharacters" :loading="extracting">
              <template #icon>
                <UserOutlined />
              </template>
              提取角色
            </a-button>
          </div>
      </div>
              </div>
            </div>

    <!-- 生成结果 -->
    <div v-if="audioFiles.length > 0" class="results-section">
      <div class="results-card">
        <div class="results-header">
          <h3>生成结果</h3>
          <div class="results-actions">
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
          <div class="audio-list">
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

    <!-- 角色配置弹窗 -->
    <a-modal
      v-model:open="showCharacterConfig"
      title="角色配置管理"
      width="800"
      :footer="null"
    >
      <div class="character-config-content">
        <div class="config-header">
          <div class="config-stats">
            <div class="stat-item">
              <span class="stat-label">总角色数</span>
              <span class="stat-value">{{ characters.length }}</span>
              </div>
            <div class="stat-item">
              <span class="stat-label">已配置</span>
              <span class="stat-value">{{ characters.filter(c => c.voice_id).length }}</span>
              </div>
            <div class="stat-item">
              <span class="stat-label">未配置</span>
              <span class="stat-value">{{ characters.filter(c => !c.voice_id).length }}</span>
            </div>
          </div>
          <div class="config-actions">
            <a-button @click="autoAssignVoices" :loading="autoAssigning">
              <template #icon>
                <SoundOutlined />
              </template>
              自动分配
            </a-button>
            <a-button type="primary" @click="saveCharacterConfig">
              <template #icon>
                <SaveOutlined />
              </template>
              保存配置
            </a-button>
      </div>
    </div>

        <a-divider />

        <div class="character-config-list">
          <div v-for="character in characters" :key="character.name" class="config-character-item">
            <div class="config-character-info">
              <div class="config-character-avatar">
                {{ character.name.charAt(0) }}
              </div>
              <div class="config-character-details">
                <div class="config-character-name">{{ character.name }}</div>
                <div class="config-character-meta">
                  {{ character.line_count || 0 }} 句对话
                  <span v-if="character.voice_id" class="configured-badge">已配置</span>
                  <span v-else class="unconfigured-badge">未配置</span>
                </div>
              </div>
            </div>
            <div class="config-voice-selection">
              <a-select 
                v-model:value="character.voice_id" 
                placeholder="选择声音"
                style="width: 250px;"
                @change="updateCharacterMapping"
                :loading="loadingVoices"
              >
                <a-select-option value="">使用默认声音</a-select-option>
                <a-select-option 
                  v-for="voice in availableVoices" 
                  :key="voice.id" 
                  :value="voice.id"
                >
                  <div class="voice-option">
                    <span class="voice-option-name">{{ voice.name }}</span>
                    <span class="voice-option-type">{{ getVoiceTypeText(voice.type) }}</span>
                  </div>
                </a-select-option>
              </a-select>
            <a-button 
                v-if="character.voice_id" 
                type="text" 
                @click="playVoicePreview(character)"
                title="播放预览"
              >
                <template #icon>
                  <PlayCircleOutlined />
            </template>
              </a-button>
            </div>
          </div>
        </div>

        <div v-if="!characters.length" class="no-characters">
          <div class="no-characters-content">
            <UserOutlined style="font-size: 48px; color: #d9d9d9;" />
            <h3>暂无角色数据</h3>
            <p>请先提取文本中的角色信息</p>
            <a-button type="primary" @click="extractCharacters" :loading="extracting">
              <template #icon>
                <UserOutlined />
              </template>
              提取角色
            </a-button>
          </div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted, nextTick, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { 
  LeftOutlined, 
  PlayCircleOutlined, 
  DownloadOutlined, 
  SoundOutlined,
  CloseOutlined,
  SettingOutlined,
  UserOutlined,
  SaveOutlined
} from '@ant-design/icons-vue'
import { readerAPI } from '@/api'

const router = useRouter()
const route = useRoute()

// 响应式数据
const loading = ref(false)
const synthesizing = ref(false)
const downloading = ref(false)
const currentProject = ref(null)
const characters = ref([])
const audioFiles = ref([])
const currentAudio = ref(null)
const showFullText = ref(false)

// 角色配置相关
const availableVoices = ref([])
const loadingVoices = ref(false)
const autoAssigning = ref(false)
const extracting = ref(false)
const showCharacterConfig = ref(false)

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
      
      // 从characterMapping构建角色数组
      const characterMapping = currentProject.value.characterMapping || {}
      characters.value = Object.entries(characterMapping).map(([name, voiceId]) => ({
        name,
        voice_id: voiceId ? parseInt(voiceId) : null,
        line_count: currentProject.value.segments?.filter(s => 
          s.detectedSpeaker === name || 
          (s.text_content || s.textContent || '').includes(name)
        ).length || 0
      }))
      
      audioFiles.value = response.data.data.audio_files || []
      
      // 加载可用声音列表
      await loadAvailableVoices()
      
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

// 加载可用声音列表
const loadAvailableVoices = async () => {
  try {
    loadingVoices.value = true
    const { charactersAPI } = await import('@/api')
    const response = await charactersAPI.getCharacters()
    
    if (response.data.success) {
      availableVoices.value = response.data.data.filter(voice => voice.status === 'active')
    }
  } catch (error) {
    console.error('加载声音列表失败:', error)
    message.error('加载声音列表失败')
  } finally {
    loadingVoices.value = false
  }
}

// 提取角色
const extractCharacters = async () => {
  if (!currentProject.value) return
  
  extracting.value = true
  try {
    // 从项目的segments中提取角色信息
    const segments = currentProject.value.segments || []
    if (!segments.length) {
      message.warning('项目没有文本段落，无法提取角色')
      return
    }
    
    // 简单的角色提取逻辑：从段落文本中提取常见的对话格式
      const characterSet = new Set()
      
      segments.forEach(segment => {
      const text = segment.text_content || segment.text || ''
      
      // 匹配对话格式：「角色名:对话内容」或「角色名说：」
      const dialoguePatterns = [
        /「([^」:：]+)[：:]/g,        // 「角色名：」格式
        /([^」「\s]+)说[：:]/g,       // 角色名说：格式
        /"([^"]+)"[说道]/g,          // "角色名"说道格式
        /([^，。！？\s]{2,4})[：:]/g  // 简单的名字:格式
      ]
      
      dialoguePatterns.forEach(pattern => {
        let match
        while ((match = pattern.exec(text)) !== null) {
          const name = match[1].trim()
          if (name.length >= 2 && name.length <= 6) {
            characterSet.add(name)
          }
        }
      })
    })
    
    // 转换为角色数组
    const extractedCharacters = Array.from(characterSet).map(name => ({
      name,
      voice_id: null,
      line_count: segments.filter(s => (s.text_content || s.text || '').includes(name)).length
    }))
    
    if (extractedCharacters.length > 0) {
      characters.value = extractedCharacters
      message.success(`成功提取到 ${extractedCharacters.length} 个角色`)
    } else {
      // 如果没有提取到角色，创建一个默认的旁白角色
      characters.value = [{
          name: '旁白',
        voice_id: null,
        line_count: segments.length
      }]
      message.info('未检测到明显的角色对话，已创建默认旁白角色')
    }
    
  } catch (error) {
    console.error('角色提取失败:', error)
    message.error('角色提取失败')
  } finally {
    extracting.value = false
  }
}

// 自动分配声音
const autoAssignVoices = async () => {
  if (!characters.value.length || !availableVoices.value.length) {
    message.warning('没有可分配的角色或声音')
    return
  }
  
  autoAssigning.value = true
  try {
    // 简单的自动分配逻辑：根据角色名称特征分配声音类型
    characters.value.forEach(character => {
      if (!character.voice_id) {
        // 根据角色名称判断性别
        const name = character.name
        let preferredType = 'female' // 默认女声
        
        // 简单的性别判断逻辑
        const maleKeywords = ['先生', '公子', '少爷', '大哥', '老板', '师父', '爷爷', '父亲', '爸爸']
        const childKeywords = ['小', '儿', '宝', '娃', '童']
        
        if (maleKeywords.some(keyword => name.includes(keyword))) {
          preferredType = 'male'
        } else if (childKeywords.some(keyword => name.includes(keyword))) {
          preferredType = 'child'
        }
        
        // 找到匹配类型的声音
        const matchingVoice = availableVoices.value.find(voice => voice.type === preferredType)
        if (matchingVoice) {
          character.voice_id = matchingVoice.id
    } else {
          // 如果没有匹配的，使用第一个可用声音
          character.voice_id = availableVoices.value[0]?.id
    }
      }
    })
    
    // 更新角色映射
    await updateCharacterMapping()
    message.success('自动分配完成')
  } catch (error) {
    console.error('自动分配失败:', error)
    message.error('自动分配失败')
  } finally {
    autoAssigning.value = false
  }
}

// 更新角色映射
const updateCharacterMapping = async () => {
  if (!currentProject.value) return
  
  try {
    // 构建角色映射对象
    const characterMapping = {}
    characters.value.forEach(character => {
      if (character.voice_id) {
        characterMapping[character.name] = character.voice_id.toString()
      }
    })
    
    console.log('[DEBUG] 发送角色映射更新:', characterMapping)
    
    // 更新项目的角色映射，传递完整的项目信息
    const response = await readerAPI.updateProject(currentProject.value.id, {
      name: currentProject.value.name,  // 必须传递项目名称
      description: currentProject.value.description || '',  // 必须传递描述
      character_mapping: characterMapping
    })
    
    if (response.data.success) {
      console.log('角色映射更新成功:', characterMapping)
      // 更新本地项目数据
      currentProject.value.characterMapping = characterMapping
    }
  } catch (error) {
    console.error('更新角色映射失败:', error)
    message.error('更新角色映射失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 获取声音类型文本
const getVoiceTypeText = (type) => {
  const typeMap = {
    'male': '男声',
    'female': '女声', 
    'child': '童声'
  }
  return typeMap[type] || '未知'
}

// 播放声音预览
const playVoicePreview = async (character) => {
  if (!character.voice_id) {
    message.warning('请先为角色分配声音')
    return
  }
  
  try {
    const voice = availableVoices.value.find(v => v.id === character.voice_id)
    if (voice && (voice.sampleAudioUrl || voice.referenceAudioUrl)) {
      const audioUrl = voice.sampleAudioUrl || voice.referenceAudioUrl
      const audio = new Audio(audioUrl)
        await audio.play()
      message.success(`正在播放：${voice.name}`)
    } else {
      message.warning('该声音暂无可播放的音频样本')
    }
  } catch (error) {
    console.error('播放声音预览失败:', error)
    message.error('播放失败')
  }
}

// 保存角色配置
const saveCharacterConfig = async () => {
  try {
    await updateCharacterMapping()
    showCharacterConfig.value = false
    message.success('角色配置保存成功')
  } catch (error) {
    console.error('保存角色配置失败:', error)
    message.error('保存角色配置失败')
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
  const pollInterval = setInterval(async () => {
  try {
      const response = await readerAPI.getProgress(currentProject.value.id)
    if (response.data.success) {
      const progress = response.data.progress
        
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
        
      if (progress.status === 'completed') {
          clearInterval(pollInterval)
          synthesizing.value = false
          currentProject.value.status = 'completed'
          // 重新加载项目以获取音频文件
          loadProject()
          message.success('语音合成完成！')
      } else if (progress.status === 'failed') {
          clearInterval(pollInterval)
          synthesizing.value = false
          currentProject.value.status = 'failed'
          message.error('语音合成失败')
        }
      }
  } catch (error) {
    console.error('获取进度失败:', error)
    }
  }, 2000)

  // 组件卸载时清除定时器
  onUnmounted(() => {
    clearInterval(pollInterval)
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

const getCharacterCount = (project) => {
  if (!project) return 0
  return project.characters?.length || 0
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

/* 角色部分 */
.characters-section {
  margin-bottom: 24px;
}

.characters-card {
  background: white;
  padding: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.characters-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.characters-header h3 {
  margin: 0;
  color: #1f2937;
}

.character-count {
  font-size: 14px;
  color: #6b7280;
}

.character-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.characters-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.character-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.character-item:hover {
  border-color: #06b6d4;
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.1);
}

.character-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.character-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
}

.character-name {
  font-weight: 600;
  color: #1f2937;
}

.character-lines {
  font-size: 12px;
  color: #6b7280;
}

.voice-assignment {
  display: flex;
  align-items: center;
  gap: 8px;
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
.empty-characters-section,
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

/* 角色配置弹窗样式 */
.character-config-content {
  max-height: 600px;
  overflow-y: auto;
}

.config-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.config-stats {
  display: flex;
  gap: 24px;
}

.stat-item {
  text-align: center;
}

.stat-label {
  display: block;
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 4px;
}

.stat-value {
  display: block;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.config-actions {
  display: flex;
  gap: 12px;
}

.character-config-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.config-character-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  transition: all 0.2s ease;
}

.config-character-item:hover {
  border-color: #06b6d4;
  box-shadow: 0 2px 8px rgba(6, 182, 212, 0.1);
}

.config-character-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.config-character-avatar {
  width: 40px;
  height: 40px;
  border-radius: 8px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: 600;
}

.config-character-name {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 4px;
}

.config-character-meta {
  font-size: 12px;
  color: #6b7280;
  display: flex;
  align-items: center;
  gap: 8px;
}

.configured-badge {
  background: #dcfce7;
  color: #166534;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
}

.unconfigured-badge {
  background: #fef3cd;
  color: #92400e;
  padding: 2px 6px;
  border-radius: 4px;
  font-size: 10px;
}

.config-voice-selection {
  display: flex;
  align-items: center;
  gap: 8px;
}

.voice-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  width: 100%;
}

.voice-option-name {
  font-weight: 500;
}

.voice-option-type {
  font-size: 12px;
  color: #6b7280;
  background: #f3f4f6;
  padding: 2px 6px;
  border-radius: 4px;
}

.no-characters {
  text-align: center;
  padding: 48px 24px;
}

.no-characters-content h3 {
  margin: 16px 0 8px 0;
  color: #1f2937;
}

.no-characters-content p {
  margin: 0 0 24px 0;
  color: #6b7280;
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

  .character-item,
  .config-character-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .voice-assignment,
  .config-voice-selection {
    width: 100%;
    justify-content: flex-start;
  }
  
  .config-header {
    flex-direction: column;
    gap: 16px;
    align-items: flex-start;
  }
  
  .config-stats {
    width: 100%;
    justify-content: space-around;
  }
}
</style>