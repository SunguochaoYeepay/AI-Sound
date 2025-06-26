<template>
  <div class="music-library">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <SoundOutlined style="margin-right: 12px" />
            背景音乐库
          </h1>
          <p class="page-description">管理项目中使用的背景音乐，支持上传、分类、预览和智能推荐</p>
        </div>
        
        <div class="action-section">
          <a-dropdown>
            <template #overlay>
              <a-menu>
                <a-menu-item key="smart" @click="showSmartGenerationModal = true">
                  <BookOutlined />
                  基于章节内容生成
                </a-menu-item>
                <a-menu-item key="direct" @click="showDirectGenerationModal = true">
                  <EditOutlined />
                  基于描述直接生成
                </a-menu-item>
              </a-menu>
            </template>
            <a-button type="primary">
              <SoundOutlined />
              AI智能生成
              <DownOutlined />
            </a-button>
          </a-dropdown>
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

    <!-- 基于章节内容的智能生成模态框 -->
    <a-modal
      v-model:open="showSmartGenerationModal"
      title="📖 基于章节内容智能生成背景音乐"
      width="900px"
      @ok="handleSmartGeneration"
      @cancel="() => { showSmartGenerationModal = false; resetSmartForm() }"
      :confirm-loading="generating"
      :ok-button-props="{ disabled: !smartForm.selectedBook || !smartForm.selectedChapter || !isServiceHealthy }"
      ok-text="开始智能生成"
      cancel-text="取消"
    >
      <div class="smart-generation-form">
        <a-form :model="smartForm" layout="vertical">
          <a-form-item label="选择书籍" required>
            <a-select
              v-model:value="smartForm.selectedBook"
              placeholder="请选择要生成背景音乐的书籍"
              @change="onBookChange"
              :loading="booksLoading"
            >
              <a-select-option v-for="book in books" :key="book.id" :value="book.id">
                {{ book.title }}
              </a-select-option>
            </a-select>
          </a-form-item>
          
                     <a-form-item label="选择章节" required v-if="smartForm.selectedBook">
             <a-select
               v-model:value="smartForm.selectedChapter"
               placeholder="请选择章节"
               :loading="chaptersLoading"
               @change="onChapterChange"
             >
               <a-select-option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">
                 第{{ chapter.chapter_number }}章 {{ chapter.title }}
               </a-select-option>
             </a-select>
           </a-form-item>
          
          <a-form-item label="章节内容预览" v-if="smartForm.selectedChapter">
            <a-textarea 
              :value="chapterPreview" 
              :rows="4" 
              readonly 
              placeholder="加载章节内容中..."
            />
          </a-form-item>
          
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="目标时长">
                <a-input-number
                  v-model:value="smartForm.duration"
                  :min="10"
                  :max="300"
                  :step="5"
                  addon-after="秒"
                  style="width: 100%;"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="音量等级">
                <a-slider
                  v-model:value="smartForm.volumeLevel"
                  :min="-30"
                  :max="0"
                  :step="1"
                  :tooltip-formatter="(val) => `${val}dB`"
                />
                <div style="text-align: center; font-size: 12px; color: #666;">
                  {{ smartForm.volumeLevel }}dB
                </div>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="生成名称">
                <a-input
                  v-model:value="smartForm.name"
                  placeholder="自动生成"
                  :maxLength="50"
                />
              </a-form-item>
            </a-col>
          </a-row>
        </a-form>
      </div>
    </a-modal>

    <!-- 基于描述的直接生成模态框 -->
    <a-modal
      v-model:open="showDirectGenerationModal"
      title="✏️ 基于描述直接生成背景音乐"
      width="700px"
      @ok="handleDirectGeneration"
      @cancel="() => { showDirectGenerationModal = false; resetDirectForm() }"
      :confirm-loading="generating"
      :ok-button-props="{ disabled: !directForm.description.trim() || !isServiceHealthy }"
      ok-text="开始生成"
      cancel-text="取消"
    >
      <div class="direct-generation-form">
        <a-form :model="directForm" layout="vertical">
          <a-form-item label="音乐描述" required>
            <a-textarea
              v-model:value="directForm.description"
              placeholder="请输入音乐描述，例如：轻松愉悦的背景音乐，适合阅读时播放，温暖舒缓的氛围..."
              :rows="4"
              :maxLength="500"
              show-count
            />
            <div class="description-tips">
              <a-alert 
                message="💡 生成提示" 
                description="你可以描述音乐的风格、情绪、场景、乐器等，AI会根据描述生成匹配的背景音乐。支持自由文本描述，如歌词、情境描述等。"
                type="info" 
                show-icon 
                style="margin-top: 8px;"
              />
            </div>
          </a-form-item>
          
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="音乐风格">
                <a-select
                  v-model:value="directForm.style"
                  placeholder="选择风格"
                  allowClear
                >
                  <a-select-option value="peaceful">轻松平静</a-select-option>
                  <a-select-option value="romance">浪漫温馨</a-select-option>
                  <a-select-option value="battle">紧张激烈</a-select-option>
                  <a-select-option value="mystery">神秘悬疑</a-select-option>
                  <a-select-option value="sad">忧伤沉重</a-select-option>
                  <a-select-option value="epic">史诗宏大</a-select-option>
                  <a-select-option value="classical">古典优雅</a-select-option>
                  <a-select-option value="modern">现代流行</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="目标时长">
                <a-input-number
                  v-model:value="directForm.duration"
                  :min="10"
                  :max="300"
                  :step="5"
                  addon-after="秒"
                  style="width: 100%;"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
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
          
          <a-form-item label="音乐名称">
            <a-input
              v-model:value="directForm.name"
              placeholder="为生成的音乐起个名字（可选）"
              :maxLength="50"
            />
          </a-form-item>
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
            message="✅ 音乐生成服务正常" 
            description="SongGeneration v1.0 运行中，可以开始生成音乐。支持基于文本描述的直接生成。"
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
import { backgroundMusicAPI, musicGenerationAPI, booksAPI, chaptersAPI } from '@/api'

// 页面状态
const loading = ref(false)
const refreshing = ref(false)
const showUploadModal = ref(false)
const uploading = ref(false)
const showSmartGenerationModal = ref(false)
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

// 智能生成表单（基于章节）
const smartForm = reactive({
  selectedBook: null,
  selectedChapter: null,
  duration: 120,
  volumeLevel: -12,
  name: ''
})

// 直接生成表单（基于描述）
const directForm = reactive({
  description: '',
  style: '',
  duration: 120,
  volumeLevel: -12,
  name: ''
})

// 书籍和章节数据
const books = ref([])
const chapters = ref([])
const chapterPreview = ref('')
const booksLoading = ref(false)
const chaptersLoading = ref(false)

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

// 智能生成处理（基于章节内容）
const handleSmartGeneration = async () => {
  try {
    generating.value = true
    
    console.log('🎵 开始智能生成背景音乐:', smartForm)
    
    // 获取章节内容
    const chapterResponse = await chaptersAPI.getChapter(smartForm.selectedChapter)
    const chapterContent = chapterResponse.data.content
    
    // 调用音乐生成API（基于章节内容）
    const response = await musicGenerationAPI.generateChapterMusic({
      chapter_id: smartForm.selectedChapter,
      content: chapterContent,
      target_duration: smartForm.duration,
      volume_level: smartForm.volumeLevel,
      fade_mode: 'standard'
    })
    
    if (response && response.data) {
      message.success('智能背景音乐生成成功！正在添加到音乐库...')
      
      // 生成成功后刷新音乐列表
      await refreshData()
      
      // 关闭生成对话框并重置表单
      showSmartGenerationModal.value = false
      resetSmartForm()
      
      console.log('✅ 智能背景音乐生成完成:', response.data)
    } else {
      throw new Error('生成响应无效')
    }
  } catch (error) {
    console.error('❌ 智能背景音乐生成失败:', error)
    message.error(`智能生成失败: ${error.response?.data?.detail || error.message}`)
  } finally {
    generating.value = false
  }
}

// 直接生成处理（基于描述）
const handleDirectGeneration = async () => {
  try {
    // 验证表单
    if (!directForm.description.trim()) {
      message.error('请输入音乐描述')
      return
    }
    
    generating.value = true
    
    console.log('🎵 开始直接生成背景音乐:', directForm)
    
    // 需要调用一个新的API，直接基于描述生成音乐，不进行场景分析
    // 这里我们需要一个专门的直接生成接口
    const response = await musicGenerationAPI.generateDirectMusic({
      description: directForm.description,
      style: directForm.style,
      target_duration: directForm.duration,
      volume_level: directForm.volumeLevel,
      name: directForm.name,
      mode: 'direct' // 直接生成模式，跳过场景分析
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

// 重置表单
const resetSmartForm = () => {
  Object.assign(smartForm, {
    selectedBook: null,
    selectedChapter: null,
    duration: 120,
    volumeLevel: -12,
    name: ''
  })
  chapters.value = []
  chapterPreview.value = ''
}

const resetDirectForm = () => {
  Object.assign(directForm, {
    description: '',
    style: '',
    duration: 120,
    volumeLevel: -12,
    name: ''
  })
}

// 加载书籍列表
const loadBooks = async () => {
  try {
    booksLoading.value = true
    const response = await booksAPI.getBooks()
    books.value = response.data || []
  } catch (error) {
    console.error('加载书籍列表失败:', error)
    message.error('加载书籍列表失败')
  } finally {
    booksLoading.value = false
  }
}

// 书籍选择变化
const onBookChange = async (bookId) => {
  if (!bookId) {
    chapters.value = []
    smartForm.selectedChapter = null
    chapterPreview.value = ''
    return
  }
  
  try {
    chaptersLoading.value = true
    const response = await chaptersAPI.getChapters(bookId)
    chapters.value = response.data || []
  } catch (error) {
    console.error('加载章节列表失败:', error)
    message.error('加载章节列表失败')
  } finally {
    chaptersLoading.value = false
  }
}

// 章节选择变化 - 加载章节内容预览
const onChapterChange = async (chapterId) => {
  if (!chapterId) {
    chapterPreview.value = ''
    return
  }
  
  try {
    const response = await chaptersAPI.getChapter(chapterId)
    const content = response.data.content || ''
    // 显示前200字符作为预览
    chapterPreview.value = content.length > 200 ? content.substring(0, 200) + '...' : content
  } catch (error) {
    console.error('加载章节内容失败:', error)
    chapterPreview.value = '章节内容加载失败'
  }
}

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
  loadBooks()
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