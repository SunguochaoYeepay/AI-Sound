<template>
  <div class="music-library">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <SoundOutlined style="margin-right: 8px" />
            背景音效
          </h1>
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
              <div class="music-description" v-if="record.description">
                {{ record.description }}
              </div>
            </div>
          </template>

          <template v-else-if="column.key === 'category'">
            <a-tag color="blue">{{
              record.category?.name || record.category_name || '未分类'
            }}</a-tag>
          </template>

          <template v-else-if="column.key === 'duration'">
            {{ formatDuration(record.duration) }}
          </template>

          <template v-else-if="column.key === 'file_size'">
            {{ formatFileSize(record.file_size) }}
          </template>

          <template v-else-if="column.key === 'actions'">
            <a-space>
              <!-- 播放按钮 - 根据音乐类型和状态显示 -->
              <a-tooltip :title="getPlayButtonTooltip(record)">
                <a-button
                  size="small"
                  type="text"
                  @click="playMusic(record)"
                  :disabled="!canPlayMusic(record)"
                  :loading="
                    audioStore.loading && audioStore.currentAudio?.id === getMusicId(record)
                  "
                  :type="audioStore.isCurrentlyPlaying(getMusicId(record)) ? 'primary' : 'default'"
                >
                  <PlayCircleOutlined v-if="!audioStore.isCurrentlyPlaying(getMusicId(record))" />
                  <PauseCircleOutlined v-else />
                </a-button>
              </a-tooltip>

              <!-- 下载按钮 - 只有已完成的音乐才能下载 -->
              <a-tooltip :title="getDownloadButtonTooltip(record)">
                <a-button
                  size="small"
                  type="text"
                  @click="downloadMusic(record)"
                  :disabled="!canDownloadMusic(record)"
                >
                  <DownloadOutlined />
                </a-button>
              </a-tooltip>

              <!-- 删除按钮 -->
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

    <!-- 基于描述的直接生成抽屉 -->
    <a-drawer
      v-model:open="showDirectGenerationModal"
      title="🎵 合成背景音乐"
      width="600px"
      placement="right"
      @close="
        () => {
          showDirectGenerationModal = false
          resetDirectForm()
        }
      "
    >
      <template #extra>
        <a-space>
          <a-button
            @click="
              () => {
                showDirectGenerationModal = false
                resetDirectForm()
              }
            "
            >取消</a-button
          >
          <a-button
            type="primary"
            @click="handleDirectGeneration"
            :loading="generating"
            :disabled="
              !directForm.musicName.trim() || !directForm.lyrics.trim() || !isServiceHealthy
            "
          >
            开始合成
          </a-button>
        </a-space>
      </template>
      <div class="direct-generation-form">
        <a-form :model="directForm" layout="vertical">
          <a-form-item label="音乐名称" required>
            <a-input
              v-model:value="directForm.musicName"
              placeholder="请输入音乐名称（必填）"
              :maxlength="100"
              show-count
              :status="!directForm.musicName.trim() ? 'error' : ''"
            />
          </a-form-item>

          <a-form-item label="歌词内容" required>
            <SongStructureHelper v-model="directForm.lyrics" />
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
                message="⏰ 重要提示"
                description="音乐合成需要消耗大量计算资源，单次合成可能需要5-15分钟，请耐心等待。合成期间请不要关闭页面或进行其他高负载操作。"
                type="warning"
                show-icon
                style="margin-top: 8px"
              />
            </div>
          </a-form-item>

          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="音乐风格">
                <a-select v-model:value="directForm.genre" placeholder="选择风格">
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
                <div style="text-align: center; font-size: 12px; color: #666">
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
                  style="width: 100%"
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
                  style="width: 100%"
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
                  style="width: 100%"
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
    </a-drawer>

    <!-- 上传音乐模态框 -->
    <a-modal
      v-model:open="showUploadModal"
      title="上传音乐"
      @ok="handleUpload"
      @cancel="
        () => {
          showUploadModal = false
          // 重置表单
          Object.assign(uploadData, {
            name: '',
            description: '',
            category_id: categories.value.length > 0 ? categories.value[0].id : 1,
            fileList: []
          })
        }
      "
      :confirm-loading="uploading"
    >
      <a-form :model="uploadData" layout="vertical">
        <a-form-item label="音乐名称" required>
          <a-input v-model:value="uploadData.name" placeholder="请输入音乐名称" />
        </a-form-item>

        <a-form-item label="音乐分类">
          <a-select v-model:value="uploadData.category_id" placeholder="请选择音乐分类">
            <a-select-option v-for="category in categories" :key="category.id" :value="category.id">
              {{ category.name }}
            </a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="描述">
          <a-textarea
            v-model:value="uploadData.description"
            placeholder="请输入音乐描述"
            :rows="3"
          />
        </a-form-item>

        <a-form-item label="音乐文件" required>
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
  import SongStructureHelper from '@/components/synthesis-center/SongStructureHelper.vue'
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
    category_id: 1,
    fileList: []
  })

  // 音乐分类数据
  const categories = ref([])

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
    musicName: '', // 音乐名称 - 必填
    lyrics: '', // 歌词 - 必填
    genre: 'Pop', // 音乐风格 - 默认流行音乐
    description: '', // 音乐描述 - 可选
    cfg_coef: 1.5, // CFG系数
    temperature: 0.9, // 温度
    top_k: 50, // Top-K
    volumeLevel: -12 // AI-Sound特有的音量级别
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
      console.log('🔍 开始加载音乐列表（背景音乐 + 生成任务）...')

      // 🎯 同时获取背景音乐和音乐生成任务
      const [backgroundResponse, generationResponse] = await Promise.allSettled([
        backgroundMusicAPI.getMusic({
          page: pagination.current,
          page_size: pagination.pageSize,
          active_only: true
        }),
        fetch(
          `/api/v1/music-generation-async/music-tasks?page=${pagination.current}&page_size=${pagination.pageSize}`
        ).then((res) => res.json())
      ])

      let allItems = []
      let totalCount = 0

      // 处理背景音乐数据
      if (backgroundResponse.status === 'fulfilled' && backgroundResponse.value.data) {
        const bgItems = backgroundResponse.value.data.items || []
        allItems = allItems.concat(
          bgItems.map((item) => ({
            ...item,
            type: 'background_music',
            category_name: item.category?.name || item.category_name || '背景音乐',
            status: 'completed'
          }))
        )
        totalCount += backgroundResponse.value.data.total || 0
      } else {
        console.warn('❌ 背景音乐加载失败:', backgroundResponse.reason)
      }

      // 处理音乐生成任务数据
      if (generationResponse.status === 'fulfilled' && generationResponse.value.success) {
        const genItems = generationResponse.value.data.items || []
        allItems = allItems.concat(
          genItems.map((item) => ({
            ...item,
            type: 'generation_task',
            // ✅ 修复：使用用户输入的音乐名称，加上状态图标
            name:
              item.status === 'pending'
                ? `🎵 ${item.name}`
                : item.status === 'processing'
                  ? `🎵 ${item.name} (${Math.round((item.progress || 0) * 100)}%)`
                  : item.status === 'completed'
                    ? `✅ ${item.name}`
                    : item.status === 'failed'
                      ? `❌ ${item.name}`
                      : item.name,
            category_name: item.custom_style || '音乐生成', // 风格作为分类显示
            duration: item.duration || 0,
            file_size: item.file_size || 0
          }))
        )
        totalCount += generationResponse.value.data.total || 0
      } else {
        console.warn('❌ 音乐生成任务加载失败:', generationResponse.reason)
      }

      // 按创建时间排序（最新的在前）
      allItems.sort((a, b) => {
        const aTime = new Date(a.created_at || 0).getTime()
        const bTime = new Date(b.created_at || 0).getTime()
        return bTime - aTime
      })

      // 🔧 处理数据格式，确保字段正确映射
      musicList.value = allItems.map((item) => ({
        ...item,
        category_name: item.category_name || '未分类'
      }))

      pagination.total = totalCount
      console.log(`📋 加载了 ${musicList.value.length} 条音乐记录 (背景音乐+生成任务)`)
      console.log('🔍 处理后的数据:', musicList.value.length > 0 ? musicList.value[0] : '无数据')
    } catch (error) {
      console.error('❌ 加载音乐列表失败:', error)

      // 🔧 显示详细错误信息，不再默认使用模拟数据
      if (error.code === 'ECONNREFUSED' || error.code === 'ERR_NETWORK') {
        message.error('无法连接到后端服务，请确保服务正在运行在8001端口')
      } else if (error.response?.status === 404) {
        message.error('API端点不存在，请检查后端路由配置')
      } else {
        message.error(`加载音乐列表失败: ${error.response?.data?.detail || error.message}`)
      }

      // 清空列表，让用户知道没有数据
      musicList.value = []
      pagination.total = 0

      console.log('💡 提示：如果后端服务未启动，请运行 cd platform/backend && python main.py')
    } finally {
      loading.value = false
    }
  }

  const loadStats = async () => {
    try {
      console.log('📊 开始加载统计信息...')
      const response = await backgroundMusicAPI.getStats()

      if (response.data) {
        Object.assign(stats, response.data)
        console.log('✅ 统计信息加载成功:', response.data)
      }
    } catch (error) {
      console.error('❌ 加载统计信息失败:', error)

      // 🔧 显示统计信息为0，而不是模拟数据
      Object.assign(stats, {
        total_music: 0,
        total_categories: 0,
        total_duration: 0,
        total_size: 0
      })

      console.log('💡 统计信息无法加载，显示为0')
    }
  }

  const loadCategories = async () => {
    try {
      console.log('🔍 开始加载音乐分类...')
      const response = await backgroundMusicAPI.getCategories(true)
      console.log('✅ 分类API响应:', response)

      if (response.data) {
        categories.value = response.data
        // 设置默认分类ID
        if (categories.value.length > 0 && !uploadData.category_id) {
          uploadData.category_id = categories.value[0].id
        }
        console.log(`📋 加载了 ${categories.value.length} 个音乐分类`)
      }
    } catch (error) {
      console.error('❌ 加载音乐分类失败:', error)
      message.error('加载音乐分类失败')
    }
  }

  const handleTableChange = (pag) => {
    pagination.current = pag.current
    pagination.pageSize = pag.pageSize
    loadMusicList()
  }

  // 🎯 辅助函数：获取音乐唯一ID
  const getMusicId = (music) => {
    if (music.type === 'generation_task') {
      return `generation_task_${music.id}`
    } else {
      return `background_music_${music.id}`
    }
  }

  // 🎯 辅助函数：判断是否可以播放
  const canPlayMusic = (music) => {
    if (music.type === 'generation_task') {
      // 生成任务必须是已完成状态且有音频URL
      return music.status === 'completed' && music.audio_url
    } else {
      // 背景音乐默认可以播放
      return true
    }
  }

  // 🎯 辅助函数：判断是否可以下载
  const canDownloadMusic = (music) => {
    if (music.type === 'generation_task') {
      // 生成任务必须是已完成状态且有音频URL
      return music.status === 'completed' && music.audio_url
    } else {
      // 背景音乐默认可以下载
      return true
    }
  }

  // 🎯 辅助函数：获取播放按钮提示
  const getPlayButtonTooltip = (music) => {
    if (!canPlayMusic(music)) {
      if (music.type === 'generation_task') {
        if (music.status === 'pending') return '合成准备中，暂时无法播放'
        if (music.status === 'processing')
          return `正在合成中 ${Math.round((music.progress || 0) * 100)}%，请等待`
        if (music.status === 'failed') return '合成失败，无法播放'
        return '音频文件不可用'
      }
      return '无法播放'
    }

    const audioId = getMusicId(music)
    return audioStore.isCurrentlyPlaying(audioId) ? '暂停' : '播放'
  }

  // 🎯 辅助函数：获取下载按钮提示
  const getDownloadButtonTooltip = (music) => {
    if (!canDownloadMusic(music)) {
      if (music.type === 'generation_task') {
        if (music.status === 'pending') return '合成准备中，暂时无法下载'
        if (music.status === 'processing')
          return `正在合成中 ${Math.round((music.progress || 0) * 100)}%，请等待`
        if (music.status === 'failed') return '合成失败，无法下载'
        return '音频文件不可用'
      }
      return '无法下载'
    }
    return '下载'
  }

  const playMusic = async (music) => {
    try {
      // 检查是否可以播放
      if (!canPlayMusic(music)) {
        message.warning(getPlayButtonTooltip(music))
        return
      }

      const audioId = getMusicId(music)

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

      // 根据音乐类型构建播放信息
      let audioInfo
      if (music.type === 'generation_task') {
        // 音乐生成任务
        audioInfo = {
          id: audioId,
          title: music.name,
          url: music.audio_url, // 直接使用任务的音频URL
          type: 'generation_task',
          metadata: {
            taskId: music.task_id,
            musicId: music.id,
            category: music.category_name || 'AI生成',
            duration: music.duration,
            fileSize: music.file_size,
            description: music.content,
            onEnded: () => {
              console.log(`AI生成音乐 ${music.name} 播放完成`)
            }
          }
        }
      } else {
        // 背景音乐
        audioInfo = {
          id: audioId,
          title: music.name,
          url: `/api/v1/background-music/music/${music.id}/download`,
          type: 'background_music',
          metadata: {
            musicId: music.id,
            category: music.category?.name || music.category_name || '背景音乐',
            duration: music.duration,
            fileSize: music.file_size,
            description: music.description,
            onEnded: () => {
              console.log(`背景音乐 ${music.name} 播放完成`)
            }
          }
        }
      }

      await audioStore.playAudio(audioInfo)
      console.log('🎵 开始播放音乐:', music.name)
    } catch (error) {
      console.error('播放音乐失败:', error)
      message.error(`播放音乐失败: ${error.message}`)
    }
  }

  const downloadMusic = async (music) => {
    try {
      // 检查是否可以下载
      if (!canDownloadMusic(music)) {
        message.warning(getDownloadButtonTooltip(music))
        return
      }

      // 根据音乐类型构建下载URL
      let downloadUrl
      let filename

      if (music.type === 'generation_task') {
        // 音乐生成任务
        downloadUrl = music.audio_url
        filename = `AI生成_${music.custom_style}_${music.id}.wav`
      } else {
        // 背景音乐
        downloadUrl = `/api/v1/background-music/music/${music.id}/download`
        filename = `${music.name}.mp3`
      }

      // 创建下载链接
      const link = document.createElement('a')
      link.href = downloadUrl
      link.download = filename
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
    const musicType = music.type === 'generation_task' ? 'AI生成音乐' : '背景音乐'

    Modal.confirm({
      title: '确认删除',
      content: `确定要删除${musicType} "${music.name}" 吗？此操作不可恢复。`,
      onOk: async () => {
        try {
          if (music.type === 'generation_task') {
            // 删除音乐生成任务
            await fetch(`/api/v1/music-generation-async/task/${music.task_id}`, {
              method: 'DELETE'
            })
          } else {
            // 删除背景音乐
            await backgroundMusicAPI.deleteMusic(music.id)
          }

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

      if (!uploadData.name.trim()) {
        message.error('请输入音乐名称')
        return
      }

      const file = uploadData.fileList[0].originFileObj || uploadData.fileList[0]

      // 调用实际的上传API
      const musicData = {
        name: uploadData.name,
        description: uploadData.description || '',
        category_id: uploadData.category_id
      }

      console.log('🔄 开始上传音乐:', musicData)
      const response = await backgroundMusicAPI.uploadMusic(musicData, file)

      console.log('✅ 上传成功:', response)
      message.success('上传成功')
      showUploadModal.value = false

      // 重置表单
      Object.assign(uploadData, {
        name: '',
        description: '',
        category_id: categories.value.length > 0 ? categories.value[0].id : 1,
        fileList: []
      })

      // 重新加载音乐列表
      await loadMusicList()
    } catch (error) {
      console.error('❌ 上传失败:', error)
      message.error('上传失败: ' + (error.response?.data?.detail || error.message))
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

      // 🔧 修复：使用异步音乐生成API，避免60秒HTTP超时
      // 使用相对路径，让Vite代理处理（开发时代理到8001，生产时代理到8000）
      const response = await fetch('/api/v1/music-generation-async/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({
          name: directForm.musicName.trim(),
          lyrics: directForm.lyrics,
          genre: directForm.genre,
          description: directForm.description,
          cfg_coef: directForm.cfg_coef,
          temperature: directForm.temperature,
          top_k: directForm.top_k,
          volume_level: directForm.volumeLevel,
          target_duration: 30 // 默认30秒音乐
        })
      })

      if (!response.ok) {
        const errorText = await response.text().catch(() => '')
        let errorDetail = `HTTP ${response.status}`

        try {
          const errorJson = JSON.parse(errorText)
          errorDetail = errorJson.detail || errorJson.message || errorDetail
        } catch {
          errorDetail = errorText || errorDetail
        }

        throw new Error(`启动任务失败: ${errorDetail}`)
      }

      const result = await response.json()
      console.log('🎵 异步音乐生成任务已启动:', result.task_id)

      // 🔧 只有真正成功才关闭窗口
      if (result.task_id) {
        message.success('🎵 音乐生成任务已启动，正在合成中...')

        // 🎯 立即刷新音乐列表（显示"合成中"状态）
        await refreshData()

        // 关闭生成对话框并重置表单
        showDirectGenerationModal.value = false
        resetDirectForm()

        console.log('✅ 直接背景音乐生成任务启动完成:', result)
      } else {
        throw new Error('任务启动失败：服务器未返回task_id')
      }
    } catch (error) {
      console.error('❌ 直接背景音乐生成失败:', error)

      // 🔧 核心修复：错误时不关闭窗口！！！
      let errorMessage = error.message

      // 根据错误类型提供更友好的提示
      if (error.message.includes('NetworkError') || error.message.includes('fetch')) {
        errorMessage = '❌ 网络连接失败，请检查后端服务是否正常运行（端口8001）'
      } else if (error.message.includes('502')) {
        errorMessage = '🔄 SongGeneration服务忙碌，请稍后重试'
      } else if (error.message.includes('500')) {
        errorMessage = '⚠️ 服务器内部错误，请检查歌词格式或联系管理员'
      } else if (error.message.includes('404')) {
        errorMessage = '❌ API接口不存在，请检查后端路由配置'
      }

      message.error(`生成失败: ${errorMessage}`, 10) // 错误信息显示10秒

      console.error('🔍 详细错误信息:', {
        error: error.message,
        stack: error.stack,
        formData: directForm
      })

      // ✅ 不关闭窗口，让用户能看到错误并重试
      // showDirectGenerationModal.value = false // 这行被注释掉了！
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
      musicName: '',
      lyrics: '',
      genre: 'Pop',
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
    loadCategories()
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
    padding: 20px 32px;
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
    font-size: 20px;
    font-weight: 500;
    color: white;
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
