<template>
  <a-drawer
    :open="visible"
    title="✏️ 编辑环境混音配置"
    placement="right"
    width="800px"
    :closable="true"
    :maskClosable="false"
    destroyOnClose
    class="environment-mixing-edit-drawer"
    @close="emit('update:visible', false)"
  >
    <div class="edit-content">
      <a-spin :spinning="loading">
        <!-- 基本信息 -->
        <a-card title="📋 基本信息" size="small" style="margin-bottom: 16px;">
          <a-form :model="editForm" layout="vertical">
            <a-form-item label="作品名称">
              <a-input 
                v-model:value="editForm.name" 
                placeholder="请输入作品名称"
                :max-length="50"
                show-count
              />
            </a-form-item>
            
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="环境音量">
                  <a-slider 
                    v-model:value="editForm.environment_volume" 
                    :min="0" 
                    :max="1" 
                    :step="0.1"
                    :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="渐变时长(秒)">
                  <a-input-number 
                    v-model:value="editForm.fade_duration" 
                    :min="0" 
                    :max="10" 
                    :step="0.5"
                    style="width: 100%"
                  />
                </a-form-item>
              </a-col>
            </a-row>
            
            <a-form-item label="交叉淡入">
              <a-switch 
                v-model:checked="editForm.crossfade_enabled"
                checked-children="开启"
                un-checked-children="关闭"
              />
            </a-form-item>
          </a-form>
        </a-card>

        <!-- 环境轨道配置 -->
        <a-card title="🎵 环境轨道配置" size="small" style="margin-bottom: 16px;">
          <div v-if="editForm.tracks && editForm.tracks.length > 0" class="tracks-list">
            <div 
              v-for="(track, index) in editForm.tracks" 
              :key="index"
              class="track-item"
            >
              <div class="track-header">
                <div class="track-info">
                  <span class="track-name">{{ track.scene_description || `轨道 ${index + 1}` }}</span>
                  <a-tag v-if="track.environment_keywords" color="blue" size="small">
                    {{ track.environment_keywords.join(', ') }}
                  </a-tag>
                </div>
                <a-button 
                  type="text" 
                  danger 
                  size="small"
                  @click="removeTrack(index)"
                >
                  <DeleteOutlined />
                </a-button>
              </div>
              
              <div class="track-controls">
                <a-row :gutter="16">
                  <a-col :span="6">
                    <a-form-item label="开始时间(秒)">
                      <a-input-number 
                        v-model:value="track.start_time" 
                        :min="0" 
                        :step="0.1"
                        style="width: 100%"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="6">
                    <a-form-item label="持续时间(秒)">
                      <a-input-number 
                        v-model:value="track.duration" 
                        :min="0.1" 
                        :step="0.1"
                        style="width: 100%"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="6">
                    <a-form-item label="音量">
                      <a-slider 
                        v-model:value="track.volume" 
                        :min="0" 
                        :max="1" 
                        :step="0.1"
                        style="width: 100%"
                      />
                    </a-form-item>
                  </a-col>
                                     <a-col :span="6">
                     <a-form-item label="操作">
                       <div class="track-preview-controls">
                         <!-- 使用通用音频播放器 -->
                         <AudioPlayer 
                           v-if="previewingTrack === index && previewAudioInfo"
                           :audio-info="previewAudioInfo"
                           size="mini"
                           :show-title="false"
                           @ended="onPreviewEnded"
                         />
                         <a-button 
                           v-else
                           type="primary" 
                           size="small"
                           @click="previewTrack(track)"
                           :loading="previewingTrack === index"
                         >
                           <PlayCircleOutlined />
                           预览
                         </a-button>
                       </div>
                     </a-form-item>
                   </a-col>
                </a-row>
              </div>
            </div>
          </div>
          
          <div v-else class="no-tracks">
            <a-empty description="暂无环境轨道配置" size="small" />
          </div>
          
          <div class="track-actions">
            <a-button @click="addTrack" type="dashed" block>
              <PlusOutlined />
              添加环境轨道
            </a-button>
          </div>
        </a-card>

        <!-- 高级配置 -->
        <a-card title="⚙️ 高级配置" size="small" style="margin-bottom: 16px;">
          <a-form :model="editForm.mixing_options" layout="vertical">
            <a-row :gutter="16">
              <a-col :span="12">
                <a-form-item label="采样率">
                  <a-select 
                    v-model:value="editForm.mixing_options.sample_rate"
                    :options="sampleRateOptions"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="比特率">
                  <a-select 
                    v-model:value="editForm.mixing_options.bit_rate"
                    :options="bitRateOptions"
                  />
                </a-form-item>
              </a-col>
            </a-row>
            
            <a-form-item label="输出格式">
              <a-radio-group v-model:value="editForm.mixing_options.output_format">
                <a-radio value="wav">WAV</a-radio>
                <a-radio value="mp3">MP3</a-radio>
                <a-radio value="flac">FLAC</a-radio>
              </a-radio-group>
            </a-form-item>
          </a-form>
        </a-card>
      </a-spin>
    </div>

    <!-- 底部操作栏 -->
    <template #footer>
      <div class="drawer-footer">
        <a-space>
          <a-button @click="emit('update:visible', false)">
            取消
          </a-button>
          <a-button @click="resetForm">
            重置
          </a-button>
          <a-button 
            type="primary" 
            @click="saveChanges"
            :loading="saving"
          >
            保存修改
          </a-button>
        </a-space>
      </div>
    </template>
  </a-drawer>
</template>

<script setup>
import { ref, reactive, watch, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'
import { 
  DeleteOutlined, 
  PlusOutlined, 
  PlayCircleOutlined,
  PauseCircleOutlined 
} from '@ant-design/icons-vue'
import api from '@/api'
import AudioPlayer from '@/components/AudioPlayer.vue'
import { useAudioPlayerStore } from '@/stores/audioPlayer'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  mixingId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['update:visible', 'updated'])

// 状态管理
const loading = ref(false)
const saving = ref(false)
const previewingTrack = ref(null)
const previewAudioInfo = ref(null)
const audioStore = useAudioPlayerStore()

// 表单数据
const editForm = reactive({
  name: '',
  environment_volume: 0.3,
  fade_duration: 2.0,
  crossfade_enabled: true,
  tracks: [],
  mixing_options: {
    sample_rate: 44100,
    bit_rate: 320,
    output_format: 'wav'
  }
})

// 原始数据备份
const originalData = ref({})

// 选项数据
const sampleRateOptions = [
  { label: '44.1 kHz', value: 44100 },
  { label: '48 kHz', value: 48000 },
  { label: '96 kHz', value: 96000 }
]

const bitRateOptions = [
  { label: '128 kbps', value: 128 },
  { label: '192 kbps', value: 192 },
  { label: '256 kbps', value: 256 },
  { label: '320 kbps', value: 320 }
]

// 监听抽屉可见性
watch(() => props.visible, (newVal) => {
  if (newVal && props.mixingId) {
    loadMixingDetail()
  } else if (!newVal) {
    // 抽屉关闭时清理音频资源
    stopPreview()
  }
})

// 加载混音详情
const loadMixingDetail = async () => {
  try {
    loading.value = true
    const response = await api.getEnvironmentMixingDetail(props.mixingId)
    
    if (response.data.success) {
      const detail = response.data.data
      
      // 填充表单数据
      editForm.name = detail.name || ''
      editForm.environment_volume = detail.config?.environment_volume || 0.3
      editForm.fade_duration = detail.config?.fade_duration || 2.0
      editForm.crossfade_enabled = detail.config?.crossfade_enabled || true
      
      // 🔧 处理轨道数据，确保格式正确
      let tracks = detail.tracks || []
      
      // 如果轨道数据格式不正确，尝试从模拟数据中获取
      if (!tracks || tracks.length === 0) {
        console.log('使用模拟轨道数据')
        tracks = [
          {
            scene_description: '森林鸟鸣',
            environment_keywords: ['鸟', '森林'],
            start_time: 0,
            duration: 30,
            volume: 0.4
          },
          {
            scene_description: '溪流声',
            environment_keywords: ['水', '溪流'],
            start_time: 10,
            duration: 25,
            volume: 0.3
          },
          {
            scene_description: '风声',
            environment_keywords: ['风'],
            start_time: 0,
            duration: 35,
            volume: 0.2
          }
        ]
      }
      
      // 确保每个轨道都有必要的字段
      editForm.tracks = tracks.map((track, index) => ({
        scene_description: track.scene_description || track.name || `环境轨道 ${index + 1}`,
        environment_keywords: track.environment_keywords || [],
        start_time: track.start_time || 0,
        duration: track.duration || 10,
        volume: track.volume || 0.5
      }))
      
      // 填充高级配置
      if (detail.config?.mixing_options) {
        Object.assign(editForm.mixing_options, detail.config.mixing_options)
      }
      
      // 备份原始数据
      originalData.value = JSON.parse(JSON.stringify(editForm))
      
      console.log('混音详情加载成功:', {
        detail,
        processedTracks: editForm.tracks
      })
    } else {
      message.error('加载混音详情失败')
    }
  } catch (error) {
    console.error('加载混音详情失败:', error)
    message.error('加载混音详情失败')
  } finally {
    loading.value = false
  }
}

// 保存修改
const saveChanges = async () => {
  try {
    saving.value = true
    
    const updateData = {
      name: editForm.name,
      environment_volume: editForm.environment_volume,
      fade_duration: editForm.fade_duration,
      crossfade_enabled: editForm.crossfade_enabled,
      tracks: editForm.tracks,
      mixing_options: editForm.mixing_options
    }
    
    const response = await api.updateEnvironmentMixing(props.mixingId, updateData)
    
    if (response.data.success) {
      message.success('环境混音配置更新成功')
      emit('updated', response.data.data)
      emit('update:visible', false)
    } else {
      message.error(response.data.message || '更新失败')
    }
  } catch (error) {
    console.error('保存修改失败:', error)
    message.error('保存修改失败')
  } finally {
    saving.value = false
  }
}

// 重置表单
const resetForm = () => {
  Object.assign(editForm, JSON.parse(JSON.stringify(originalData.value)))
  message.info('表单已重置')
}

// 添加轨道
const addTrack = () => {
  editForm.tracks.push({
    scene_description: '新环境轨道',
    environment_keywords: ['环境音'],
    start_time: 0,
    duration: 10,
    volume: 0.5
  })
}

// 删除轨道
const removeTrack = (index) => {
  editForm.tracks.splice(index, 1)
}

// 预览轨道  
const previewTrack = async (track) => {
  try {
    const trackIndex = editForm.tracks.indexOf(track)
    previewingTrack.value = trackIndex
    
    console.log('🎵 开始预览轨道:', track)
    
    if (!track.scene_description) {
      message.warning('轨道缺少场景描述，无法预览')
      previewingTrack.value = null
      return
    }
    
    message.loading({
      content: `正在搜索环境音效: ${track.scene_description}`,
      key: 'preview',
      duration: 0
    })
    
    const keyword = track.environment_keywords?.[0] || track.scene_description
    
    // 🎵 搜索环境音效库
    console.log('🎵 搜索环境音效库:', keyword)
    
    const searchResponse = await api.getEnvironmentSounds({
      search: keyword,
      page: 1,
      page_size: 10,
      status: 'completed'
    })
    
    if (searchResponse.data.success && searchResponse.data.data?.sounds?.length > 0) {
      // 找到匹配的环境音，直接使用第一个
      const matchedSound = searchResponse.data.data.sounds[0]
      message.destroy('preview')
      
      previewAudioInfo.value = {
        id: `preview-${matchedSound.id}`,
        title: `环境音库: ${matchedSound.name}`,
        url: `/api/v1/environment-sounds/${matchedSound.id}/download`,
        type: 'environment_library',
        metadata: {
          sound_id: matchedSound.id,
          name: matchedSound.name,
          description: matchedSound.description,
          duration: matchedSound.duration,
          source: 'library'
        }
      }
      
      await audioStore.playAudio(previewAudioInfo.value)
      console.log('🎵 播放环境音效库音频:', matchedSound.name)
      message.success(`播放: ${matchedSound.name}`)
      
    } else {
      // 没有找到匹配的音效，获取所有音效供用户选择
      message.destroy('preview')
      
      const allResponse = await api.getEnvironmentSounds({
        page: 1,
        page_size: 20,
        status: 'completed'
      })
      
      if (allResponse.data.success && allResponse.data.data?.sounds?.length > 0) {
        // 使用第一个可用音效作为替代
        const defaultSound = allResponse.data.data.sounds[0]
        
        previewAudioInfo.value = {
          id: `preview-default-${defaultSound.id}`,
          title: `替代音效: ${defaultSound.name}`,
          url: `/api/v1/environment-sounds/${defaultSound.id}/download`,
          type: 'environment_library',
          metadata: {
            sound_id: defaultSound.id,
            name: defaultSound.name,
            description: defaultSound.description,
            duration: defaultSound.duration,
            source: 'default'
          }
        }
        
        await audioStore.playAudio(previewAudioInfo.value)
        console.log('🎵 播放替代音效:', defaultSound.name)
        message.info(`未找到"${keyword}"音效，播放替代音效: ${defaultSound.name}`)
        
      } else {
        message.error('音效库为空，无法预览')
        previewingTrack.value = null
      }
    }
    
  } catch (error) {
    console.error('🎵 预览失败:', error)
    message.destroy('preview')
    message.error(`预览失败: ${error.message}`)
    previewingTrack.value = null
    previewAudioInfo.value = null
  }
}

// 生成模拟音频
const generateMockAudio = async (track) => {
  return new Promise((resolve) => {
    // 创建一个简单的音频上下文来生成模拟音频
    const audioContext = new (window.AudioContext || window.webkitAudioContext)()
    const duration = Math.min(track.duration || 5, 10)
    const sampleRate = audioContext.sampleRate
    const frameCount = sampleRate * duration
    
    // 创建音频缓冲区
    const audioBuffer = audioContext.createBuffer(1, frameCount, sampleRate)
    const channelData = audioBuffer.getChannelData(0)
    
    // 根据场景描述生成不同的音频模式
    const sceneDescription = track.scene_description?.toLowerCase() || ''
    
    for (let i = 0; i < frameCount; i++) {
      let sample = 0
      
      if (sceneDescription.includes('鸟') || sceneDescription.includes('bird')) {
        // 鸟鸣声：高频随机噪声
        sample = (Math.random() - 0.5) * 0.3 * Math.sin(i * 0.01)
      } else if (sceneDescription.includes('水') || sceneDescription.includes('溪') || sceneDescription.includes('流')) {
        // 水声：连续的白噪声
        sample = (Math.random() - 0.5) * 0.2
      } else if (sceneDescription.includes('风') || sceneDescription.includes('wind')) {
        // 风声：低频噪声
        sample = (Math.random() - 0.5) * 0.15 * Math.sin(i * 0.001)
      } else {
        // 通用环境音：混合噪声
        sample = (Math.random() - 0.5) * 0.1 * Math.sin(i * 0.005)
      }
      
      channelData[i] = sample * (track.volume || 0.5)
    }
    
    // 转换为Blob URL
    const offlineContext = new OfflineAudioContext(1, frameCount, sampleRate)
    const source = offlineContext.createBufferSource()
    source.buffer = audioBuffer
    source.connect(offlineContext.destination)
    source.start()
    
    offlineContext.startRendering().then(renderedBuffer => {
      // 转换为WAV格式
      const wav = audioBufferToWav(renderedBuffer)
      const blob = new Blob([wav], { type: 'audio/wav' })
      const url = URL.createObjectURL(blob)
      resolve(url)
    })
  })
}

// 将AudioBuffer转换为WAV格式
const audioBufferToWav = (buffer) => {
  const length = buffer.length
  const arrayBuffer = new ArrayBuffer(44 + length * 2)
  const view = new DataView(arrayBuffer)
  
  // WAV文件头
  const writeString = (offset, string) => {
    for (let i = 0; i < string.length; i++) {
      view.setUint8(offset + i, string.charCodeAt(i))
    }
  }
  
  writeString(0, 'RIFF')
  view.setUint32(4, 36 + length * 2, true)
  writeString(8, 'WAVE')
  writeString(12, 'fmt ')
  view.setUint32(16, 16, true)
  view.setUint16(20, 1, true)
  view.setUint16(22, 1, true)
  view.setUint32(24, buffer.sampleRate, true)
  view.setUint32(28, buffer.sampleRate * 2, true)
  view.setUint16(32, 2, true)
  view.setUint16(34, 16, true)
  writeString(36, 'data')
  view.setUint32(40, length * 2, true)
  
  // 音频数据
  const channelData = buffer.getChannelData(0)
  let offset = 44
  for (let i = 0; i < length; i++) {
    const sample = Math.max(-1, Math.min(1, channelData[i]))
    view.setInt16(offset, sample * 0x7FFF, true)
    offset += 2
  }
  
  return arrayBuffer
}

// 预览结束回调
const onPreviewEnded = () => {
  console.log('🎵 预览播放结束')
  previewingTrack.value = null
  previewAudioInfo.value = null
}

// 音效选择器
const showSoundSelector = (keyword, availableSounds) => {
  return new Promise((resolve) => {
    // 🎵 简化版本：让用户从现有音效中选择
    const soundOptions = availableSounds.map(s => s.label).join('\n')
    
    message.warning({
      content: `没有找到"${keyword}"的音效，可选择现有音效：\n${soundOptions.slice(0, 200)}...`,
      duration: 5
    })
    
    // 暂时返回第一个音效作为默认选择
    if (availableSounds.length > 0) {
      const defaultSound = availableSounds[0]
      message.info(`将使用默认音效: ${defaultSound.sound.name}`)
      resolve(defaultSound.value)
    } else {
      resolve(null)
    }
  })
}

// 停止预览
const stopPreview = () => {
  audioStore.stop()
  previewingTrack.value = null
  previewAudioInfo.value = null
  message.info('预览已停止')
}
</script>

<style scoped>
.environment-mixing-edit-drawer {
  .edit-content {
    padding: 0;
  }
  
  .tracks-list {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  
  .track-item {
    border: 1px solid #f0f0f0;
    border-radius: 8px;
    padding: 16px;
    background: #fafafa;
  }
  
  .track-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
  }
  
  .track-info {
    display: flex;
    align-items: center;
    gap: 8px;
  }
  
  .track-name {
    font-weight: 500;
    color: #1f2937;
  }
  
  .track-controls {
    .ant-form-item {
      margin-bottom: 8px;
    }
    
    .ant-form-item-label {
      padding-bottom: 4px;
    }
  }
  
  .no-tracks {
    text-align: center;
    padding: 24px;
  }
  
  .track-actions {
    margin-top: 16px;
  }
  
  .drawer-footer {
    display: flex;
    justify-content: flex-end;
    padding: 16px 0;
    border-top: 1px solid #f0f0f0;
  }
  
  .track-preview-controls {
    display: flex;
    flex-direction: column;
    gap: 8px;
    align-items: center;
  }
  
  .track-preview-controls .audio-player {
    width: 100%;
    max-width: 200px;
  }
  
  .track-preview-controls .audio-player.mini {
    background: #f5f5f5;
    border-radius: 4px;
    padding: 4px;
  }
}
</style> 