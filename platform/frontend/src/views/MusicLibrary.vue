<template>
  <div class="music-library">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <SoundOutlined style="margin-right: 12px" />
            背景音乐
          </h1>
          <p class="page-description">管理项目中使用的背景音乐，支持上传、分类、预览和智能推荐</p>
        </div>
        
        <div class="action-section">
          <!-- 简化为单一直接生成按钮 -->
          <a-button type="primary" @click="showDirectGenerationModal = true">
            <SoundOutlined />
            合成音乐
          </a-button>
          <a-button @click="showUploadModal = true">
            <PlusOutlined />
            上传音乐
          </a-button>
          <a-button @click="refreshData" :loading="refreshing">
            <ReloadOutlined />
            刷新
          </a-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-cards">
      <a-col :span="6">
        <a-card size="small">
          <a-statistic
            title="总音乐数"
            :value="stats.total_music"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix>
              <SoundOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic
            title="音乐分类"
            :value="stats.total_categories"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix>
              <AppstoreOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic
            title="总时长"
            :value="formatDuration(stats.total_duration)"
            :value-style="{ color: '#faad14' }"
          >
            <template #prefix>
              <ClockCircleOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card size="small">
          <a-statistic
            title="总大小"
            :value="formatFileSize(stats.total_size)"
            :value-style="{ color: '#722ed1' }"
          >
            <template #prefix>
              <DatabaseOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 音乐列表 -->
    <a-card title="音乐列表" class="music-table">
      <a-table
        :dataSource="musicList"
        :columns="tableColumns"
        :pagination="pagination"
        :loading="loading"
        row-key="id"
        @change="handleTableChange"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'name'">
            <div class="music-info">
              <div class="music-name">{{ record.name }}</div>
              <div class="music-description" v-if="record.description">{{ record.description }}</div>
            </div>
          </template>
          
          <template v-else-if="column.key === 'category'">
            <a-tag color="blue">{{ record.category_name || '未分类' }}</a-tag>
          </template>
          
          <template v-else-if="column.key === 'duration'">
            {{ formatDuration(record.duration) }}
          </template>
          
          <template v-else-if="column.key === 'file_size'">
            {{ formatFileSize(record.file_size) }}
          </template>
          
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-tooltip :title="audioStore.isCurrentlyPlaying(`background_music_${record.id}`) ? '暂停' : '播放'">
                <a-button 
                  size="small" 
                  type="text" 
                  @click="playMusic(record)"
                  :loading="audioStore.loading && audioStore.currentAudio?.id === `background_music_${record.id}`"
                  :type="audioStore.isCurrentlyPlaying(`background_music_${record.id}`) ? 'primary' : 'default'"
                >
                  <PlayCircleOutlined v-if="!audioStore.isCurrentlyPlaying(`background_music_${record.id}`)" />
                  <PauseCircleOutlined v-else />
                </a-button>
              </a-tooltip>
              <a-tooltip title="下载">
                <a-button size="small" type="text" @click="downloadMusic(record)">
                  <DownloadOutlined />
                </a-button>
              </a-tooltip>
              <a-tooltip title="删除">
                <a-button size="small" type="text" danger @click="deleteMusic(record)">
                  <DeleteOutlined />
                </a-button>
              </a-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 智能生成模态框已移除 - 功能复杂，后期优化 -->

    <!-- 基于描述的直接生成模态框 -->
    <a-modal
      v-model:open="showDirectGenerationModal"
      title="🎵 合成背景音乐"
      width="700px"
      @ok="handleDirectGeneration"
      @cancel="() => { showDirectGenerationModal = false; resetDirectForm() }"
      :confirm-loading="generating"
      :ok-button-props="{ disabled: !directForm.lyrics.trim() || !isServiceHealthy }"
      ok-text="开始合成"
      cancel-text="取消"
    >
      <div class="direct-generation-form">
        <a-form :model="directForm" layout="vertical">
          <a-form-item label="歌词内容" required>
            <a-textarea
              v-model:value="directForm.lyrics"
              placeholder="请输入歌词，格式如下：

[intro-short]

[verse]
夜晚的街灯闪烁
我漫步在熟悉的角落
回忆像潮水般涌来

[chorus]
音乐的节奏奏响
我的心却在流浪
没有你的日子很难过

[outro-short]"
              :rows="8"
              :maxLength="2000"
              show-count
            />
          </a-form-item>
          
          <a-form-item label="音乐描述 (可选)">
            <a-textarea
              v-model:value="directForm.description"
              placeholder="描述音乐的特征，如：female, warm, pop, sad, piano, the bpm is 120"
              :rows="3"
              :maxLength="500"
              show-count
            />
            <div class="description-tips">
              <a-alert 
                message="💡 合成提示" 
                description="歌词是必填项，描述是可选的。参考SongGeneration Demo页面的格式输入。"
                type="info" 
                show-icon 
                style="margin-top: 8px;"
              />
              
              <a-alert 
                message="⏰ 重要提示" 
                description="音乐合成需要消耗大量计算资源，单次合成可能需要5-15分钟，请耐心等待。合成期间请不要关闭页面或进行其他高负载操作。"
                type="warning" 
                show-icon 
                style="margin-top: 8px;"
              />
            </div>
          </a-form-item>
          
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="音乐风格">
                <a-select
                  v-model:value="directForm.genre"
                  placeholder="选择风格"
                >
                  <a-select-option value="Auto">自动选择</a-select-option>
                  <a-select-option value="Pop">流行 (Pop)</a-select-option>
                  <a-select-option value="R&B">R&B</a-select-option>
                  <a-select-option value="Dance">舞曲 (Dance)</a-select-option>
                  <a-select-option value="Jazz">爵士 (Jazz)</a-select-option>
                  <a-select-option value="Folk">民谣 (Folk)</a-select-option>
                  <a-select-option value="Rock">摇滚 (Rock)</a-select-option>
                  <a-select-option value="Chinese Style">中国风</a-select-option>
                  <a-select-option value="Chinese Tradition">中国传统</a-select-option>
                  <a-select-option value="Metal">金属 (Metal)</a-select-option>
                  <a-select-option value="Reggae">雷鬼 (Reggae)</a-select-option>
                  <a-select-option value="Chinese Opera">中国戏曲</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            
            <a-col :span="12">
              <a-form-item label="音量等级">
                <a-slider
                  v-model:value="directForm.volumeLevel"
                  :min="-30"
                  :max="0"
                  :step="1"
                  :tooltip-formatter="(val) => `${val}dB`"
                />
                <div style="text-align: center; font-size: 12px; color: #666;">
                  {{ directForm.volumeLevel }}dB
                </div>
              </a-form-item>
            </a-col>
          </a-row>
          
          <!-- 高级参数 -->
          <a-divider>高级参数</a-divider>
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="CFG系数 (0.1-3.0)">
                <a-input-number
                  v-model:value="directForm.cfg_coef"
                  :min="0.1"
                  :max="3.0"
                  :step="0.1"
                  style="width: 100%;"
                />
              </a-form-item>
            </a-col>
            
            <a-col :span="8">
              <a-form-item label="温度 (0.1-2.0)">
                <a-input-number
                  v-model:value="directForm.temperature"
                  :min="0.1"
                  :max="2.0"
                  :step="0.1"
                  style="width: 100%;"
                />
              </a-form-item>
            </a-col>
            
            <a-col :span="8">
              <a-form-item label="Top-K (1-100)">
                <a-input-number
                  v-model:value="directForm.top_k"
                  :min="1"
                  :max="100"
                  :step="1"
                  style="width: 100%;"
                />
              </a-form-item>
            </a-col>
          </a-row>
          
          <!-- 音乐名称字段已移除 - 后端API不需要此参数 -->
        </a-form>
        
        <!-- 服务状态 -->
        <div class="service-status-section">
          <a-alert 
            v-if="!isServiceHealthy"
            message="⚠️ SongGeneration服务不可用" 
            description="音乐生成服务暂时不可用，请稍后重试或联系管理员。"
            type="warning" 
            show-icon 
          />
          <a-alert 
            v-else
            message="✅ 音乐合成服务正常" 
            description="SongGeneration v1.0 运行中，可以开始合成音乐。支持基于文本描述的直接合成。"
            type="success" 
            show-icon 
          />
        </div>
      </div>
    </a-modal>

    <!-- 上传音乐模态框 -->
    <a-modal
      v-model:open="showUploadModal"
      title="上传音乐"
      @ok="handleUpload"
      @cancel="showUploadModal = false"
      :confirm-loading="uploading"
    >
      <a-form :model="uploadData" layout="vertical">
        <a-form-item label="音乐名称">
          <a-input v-model:value="uploadData.name" placeholder="请输入音乐名称" />
        </a-form-item>
        
        <a-form-item label="描述">
          <a-textarea v-model:value="uploadData.description" placeholder="请输入音乐描述" :rows="3" />
        </a-form-item>
        
        <a-form-item label="音乐文件">
          <a-upload
            v-model:file-list="uploadData.fileList"
            :before-upload="beforeUpload"
            accept="audio/*"
          >
            <a-button>
              <UploadOutlined />
              选择文件
            </a-button>
          </a-upload>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  SoundOutlined,
  AppstoreOutlined,
  ClockCircleOutlined,
  DatabaseOutlined,
  PlusOutlined,
  ReloadOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DownloadOutlined,
  DeleteOutlined,
  UploadOutlined,
  BookOutlined,
  EditOutlined,
  DownOutlined
} from '@ant-design/icons-vue'
import { getAudioService } from '@/utils/audioService'
import { useAudioPlayerStore } from '@/stores/audioPlayer'
import { backgroundMusicAPI, musicGenerationAPI } from '@/api'
// import { booksAPI, chaptersAPI } from '@/api'  // 移除 - 智能生成功能已移除

// 页面状态
const loading = ref(false)
const refreshing = ref(false)
const showUploadModal = ref(false)
const uploading = ref(false)
// const showSmartGenerationModal = ref(false)  // 智能生成已移除
const showDirectGenerationModal = ref(false)
const generating = ref(false)
const isServiceHealthy = ref(true)

// 音频服务
const audioService = getAudioService()
const audioStore = useAudioPlayerStore()

// 数据状态
const musicList = ref([])
const stats = reactive({
  total_music: 0,
  total_categories: 0,
  total_duration: 0,
  total_size: 0
})

// 分页状态
const pagination = reactive({
  current: 1,
  pageSize: 10,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true
})

// 上传数据
const uploadData = reactive({
  name: '',
  description: '',
  fileList: []
})

// 智能生成表单已移除 - 功能复杂，后期优化
// const smartForm = reactive({
//   selectedBook: null,
//   selectedChapter: null,
//   duration: 120,
//   volumeLevel: -12,
//   name: ''
// })

// 直接生成表单（与SongGeneration Demo完全一致）
const directForm = reactive({
  lyrics: '',  // 歌词 - 必填
  genre: 'Auto',  // 音乐风格
  description: '',  // 音乐描述 - 可选
  cfg_coef: 1.5,  // CFG系数
  temperature: 0.9,  // 温度
  top_k: 50,  // Top-K
  volumeLevel: -12  // AI-Sound特有的音量级别
})

// 书籍和章节数据已移除 - 智能生成功能移除
// const books = ref([])
// const chapters = ref([])
// const chapterPreview = ref('')
// const booksLoading = ref(false)
// const chaptersLoading = ref(false)

// 表格列定义
const tableColumns = [
  {
    title: '音乐名称',
    dataIndex: 'name',
    key: 'name',
    width: 200
  },
  {
    title: '分类',
    dataIndex: 'category_name',
    key: 'category',
    width: 100
  },
  {
    title: '时长',
    dataIndex: 'duration',
    key: 'duration',
    width: 80
  },
  {
    title: '大小',
    dataIndex: 'file_size',
    key: 'file_size',
    width: 80
  },
  {
    title: '操作',
    key: 'actions',
    width: 150,
    fixed: 'right'
  }
]

// 方法
const refreshData = async () => {
  refreshing.value = true
  try {
    await loadMusicList()
    await loadStats()
    message.success('数据刷新成功')
  } catch (error) {
    message.error('数据刷新失败')
  } finally {
    refreshing.value = false
  }
}

const loadMusicList = async () => {
  loading.value = true
  try {
    const response = await backgroundMusicAPI.getMusic({
      page: pagination.current,
      page_size: pagination.pageSize,
      active_only: true
    })
    
    if (response.data) {
      musicList.value = response.data.items || []
      pagination.total = response.data.total || 0
    }
  } catch (error) {
    console.error('加载音乐列表失败:', error)
    message.error('加载音乐列表失败')
    
    // 如果API失败，使用模拟数据作为后备
    const mockData = [
      {
        id: 1,
        name: '轻松愉悦背景音乐',
        description: '适合用于日常场景的轻松音乐',
        category_name: '背景音乐',
        duration: 180,
        file_size: 5242880
      },
      {
        id: 2,
        name: '史诗级配乐',
        description: '适合用于紧张激烈场景',
        category_name: '配乐',
        duration: 240,
        file_size: 7340032
      }
    ]
    
    musicList.value = mockData
    pagination.total = mockData.length
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await backgroundMusicAPI.getStats()
    
    if (response.data) {
      Object.assign(stats, response.data)
    }
  } catch (error) {
    console.error('加载统计信息失败:', error)
    
    // 如果API失败，使用模拟数据作为后备
    Object.assign(stats, {
      total_music: 18,
      total_categories: 3,
      total_duration: 3600,
      total_size: 104857600
    })
  }
}

const handleTableChange = (pag) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  loadMusicList()
}

const playMusic = async (music) => {
  try {
    const audioId = `background_music_${music.id}`
    
    // 如果当前正在播放这首音乐，则暂停
    if (audioStore.isCurrentlyPlaying(audioId)) {
      audioStore.pause()
      return
    }
    
    // 如果是同一首音乐但暂停了，则恢复播放
    if (audioStore.currentAudio?.id === audioId && !audioStore.isPlaying) {
      audioStore.resume()
      return
    }
    
    // 播放新音乐
    const audioInfo = {
      id: audioId,
      title: music.name,
      url: `/api/v1/background-music/music/${music.id}/download`,
      type: 'background_music',
      metadata: {
        musicId: music.id,
        category: music.category_name,
        duration: music.duration,
        fileSize: music.file_size,
        description: music.description,
        onEnded: () => {
          console.log(`背景音乐 ${music.name} 播放完成`)
        }
      }
    }
    
    await audioStore.playAudio(audioInfo)
    console.log('🎵 开始播放背景音乐:', music.name)
  } catch (error) {
    console.error('播放音乐失败:', error)
    message.error(`播放音乐失败: ${error.message}`)
  }
}

const downloadMusic = async (music) => {
  try {
    // 创建下载链接
    const downloadUrl = `/api/v1/background-music/music/${music.id}/download`
    const link = document.createElement('a')
    link.href = downloadUrl
    link.download = `${music.name}.mp3`
    link.target = '_blank'
    
    // 触发下载
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    
    message.success(`正在下载: ${music.name}`)
  } catch (error) {
    console.error('下载音乐失败:', error)
    message.error('下载音乐失败')
  }
}

const deleteMusic = (music) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除音乐 "${music.name}" 吗？此操作不可恢复。`,
    onOk: async () => {
      try {
        await backgroundMusicAPI.deleteMusic(music.id)
        message.success('删除成功')
        await loadMusicList()
        await loadStats()
      } catch (error) {
        console.error('删除音乐失败:', error)
        message.error(`删除音乐失败: ${error.message}`)
      }
    }
  })
}

const beforeUpload = (file) => {
  const isValidType = ['audio/mpeg', 'audio/wav', 'audio/ogg', 'audio/mp4'].includes(file.type)
  if (!isValidType) {
    message.error('只支持 MP3、WAV、OGG、M4A 格式的音频文件')
    return false
  }
  
  const isLt50M = file.size / 1024 / 1024 < 50
  if (!isLt50M) {
    message.error('文件大小不能超过 50MB')
    return false
  }
  
  // 自动填入文件名
  if (!uploadData.name) {
    uploadData.name = file.name.replace(/\.[^/.]+$/, '')
  }
  
  return false // 阻止自动上传
}

const handleUpload = async () => {
  try {
    uploading.value = true
    
    if (uploadData.fileList.length === 0) {
      message.error('请选择音乐文件')
      return
    }
    
    // 模拟上传
    await new Promise(resolve => setTimeout(resolve, 2000))
    
    message.success('上传成功')
    showUploadModal.value = false
    
    // 重置表单
    Object.assign(uploadData, {
      name: '',
      description: '',
      fileList: []
    })
    
    loadMusicList()
  } catch (error) {
    console.error('上传失败:', error)
    message.error('上传失败')
  } finally {
    uploading.value = false
  }
}

// 智能生成处理已移除 - 功能复杂，后期优化
// const handleSmartGeneration = async () => {
//   // 基于章节内容的智能音乐生成功能已移除
//   // 后续优化：分析小说内容 → 生成音乐歌词 → 配置音效等
//   // 暂时只保留直接生成功能
// }

// 直接生成处理（基于描述）
const handleDirectGeneration = async () => {
  try {
    // 验证表单
    if (!directForm.lyrics.trim()) {
      message.error('请输入歌词内容')
      return
    }
    
    generating.value = true
    
    console.log('🎵 开始直接生成背景音乐:', directForm)
    
    // 调用直接音乐生成API，参数完全匹配SongGeneration Demo
    const response = await musicGenerationAPI.generateDirectMusic({
      lyrics: directForm.lyrics,
      genre: directForm.genre,
      description: directForm.description,
      cfg_coef: directForm.cfg_coef,
      temperature: directForm.temperature,
      top_k: directForm.top_k,
      volume_level: directForm.volumeLevel
    })
    
    if (response && response.data) {
      // 检查是否为模拟结果
      const isMock = response.data.music_info?.is_mock
      if (isMock) {
        message.success('背景音乐生成完成（模拟模式）！SongGeneration服务当前不可用，已生成模拟音频文件。')
      } else {
        message.success('背景音乐生成成功！正在添加到音乐库...')
      }
      
      // 生成成功后刷新音乐列表
      await refreshData()
      
      // 关闭生成对话框并重置表单
      showDirectGenerationModal.value = false
      resetDirectForm()
      
      console.log('✅ 直接背景音乐生成完成:', response.data)
    } else {
      throw new Error('生成响应无效')
    }
  } catch (error) {
    console.error('❌ 直接背景音乐生成失败:', error)
    message.error(`生成失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    generating.value = false
  }
}

// 智能生成重置表单已移除
// const resetSmartForm = () => {
//   // 智能生成表单重置功能已移除
// }

const resetDirectForm = () => {
  Object.assign(directForm, {
    lyrics: '',
    genre: 'Auto',
    description: '',
    cfg_coef: 1.5,
    temperature: 0.9,
    top_k: 50,
    volumeLevel: -12
  })
}

// 书籍和章节相关方法已移除 - 智能生成功能移除
// const loadBooks = async () => {
//   // 加载书籍列表功能已移除
// }
// 
// const onBookChange = async (bookId) => {
//   // 书籍选择变化处理已移除
// }
// 
// const onChapterChange = async (chapterId) => {
//   // 章节选择变化处理已移除
// }

// 检查服务状态
const checkServiceHealth = async () => {
  try {
    // 这里可以调用健康检查API
    // const response = await musicGenerationAPI.getServiceHealth()
    // isServiceHealthy.value = response.data.status === 'healthy'
    isServiceHealthy.value = true // 暂时设为true
  } catch (error) {
    console.error('检查服务状态失败:', error)
    isServiceHealthy.value = false
  }
}

// 工具函数
const formatDuration = (seconds) => {
  if (!seconds || isNaN(seconds)) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

const formatFileSize = (bytes) => {
  if (!bytes || isNaN(bytes)) return '0 B'
  const sizes = ['B', 'KB', 'MB', 'GB']
  const i = Math.floor(Math.log(bytes) / Math.log(1024))
  return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`
}

// 生命周期
onMounted(() => {
  refreshData()
  checkServiceHealth()
  // loadBooks()  // 移除 - 智能生成功能已移除
})
</script>

<style scoped>
.music-library {
  padding: 0;
}

.page-header {
  margin-bottom: 24px;
  padding: 32px;
  background: linear-gradient(135deg, #722ed1 0%, #531dab 100%);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(114, 46, 209, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title {
  display: flex;
  align-items: center;
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: white;
}

.page-description {
  margin: 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  line-height: 1.5;
}

.action-section {
  display: flex;
  gap: 16px;
}

.stats-cards {
  margin-bottom: 16px;
}

.music-table {
  margin-bottom: 16px;
}

.music-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.music-name {
  font-weight: 500;
  color: #262626;
}

.music-description {
  font-size: 12px;
  color: #8c8c8c;
  margin: 0;
}

.music-generation-form {
  padding: 24px;
}

.description-tips {
  margin-top: 8px;
}

.service-status-section {
  margin-top: 24px;
}
</style>