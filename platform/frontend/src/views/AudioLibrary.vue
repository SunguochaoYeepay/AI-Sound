<template>
  <div class="audio-library">
    <!-- 页面标题和说明 -->
    <div class="page-header">
      <a-page-header sub-title="统一管理所有生成的音频文件">
        <template #title>
          <div class="title-with-back">
            <a-button type="text" @click="goBack" class="back-btn">
              <template #icon><ArrowLeftOutlined /></template>
            </a-button>
            <span>音频资源库</span>
          </div>
        </template>
        <template #extra>
          <a-button type="primary" @click="syncAudioFiles" :loading="syncing">
            <ReloadOutlined />
            同步音频文件
          </a-button>
        </template>
      </a-page-header>
    </div>

    <!-- 统计卡片 -->
    <a-row :gutter="16" class="stats-cards">
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="音频总数"
            :value="stats.overview?.totalFiles || 0"
            :prefix="h(SoundOutlined)"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="存储大小"
            :value="stats.overview?.totalSizeMB || 0"
            suffix="MB"
            :precision="2"
            :prefix="h(DatabaseOutlined)"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="总时长"
            :value="stats.overview?.totalDurationFormatted || '00:00'"
            :prefix="h(ClockCircleOutlined)"
          />
        </a-card>
      </a-col>
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="今日新增"
            :value="stats.overview?.todayCount || 0"
            :prefix="h(PlusCircleOutlined)"
          />
        </a-card>
      </a-col>
    </a-row>

    <!-- 筛选工具栏 -->
    <div class="filter-section">
      <div class="filter-controls">
          <a-select
            v-model:value="filters.projectId"
            placeholder="选择项目"
          style="width: 200px;"
          size="large"
            allow-clear
            @change="refreshAudioList"
          >
            <a-select-option
              v-for="project in projectList"
              :key="project.id"
              :value="project.id"
            >
              {{ project.name }}
            </a-select-option>
          </a-select>
        
          <a-select
            v-model:value="filters.audioType"
            placeholder="音频类型"
          style="width: 120px;"
          size="large"
            allow-clear
            @change="refreshAudioList"
          >
            <a-select-option value="segment">分段音频</a-select-option>
            <a-select-option value="project">项目合成</a-select-option>
            <a-select-option value="single">单句合成</a-select-option>
            <a-select-option value="test">测试音频</a-select-option>
          </a-select>
        
          <a-input-search
            v-model:value="filters.search"
            placeholder="搜索文件名或内容"
          style="width: 300px;"
          size="large"
            @search="refreshAudioList"
          allow-clear
        />
        
        <a-button @click="refreshAudioList" :loading="loading" size="large">
          <template #icon>
            <ReloadOutlined />
          </template>
          刷新
        </a-button>
      </div>
      
      <div class="action-controls">
          <a-space>
            <a-button
              @click="batchDownload"
              :disabled="!selectedRowKeys.length"
              :loading="downloading"
            size="large"
            >
            <template #icon>
              <DownloadOutlined />
            </template>
              批量下载 ({{ selectedRowKeys.length }})
            </a-button>
            <a-button
              danger
              @click="batchDelete"
              :disabled="!selectedRowKeys.length"
              :loading="deleting"
            size="large"
            >
            <template #icon>
              <DeleteOutlined />
            </template>
              批量删除
            </a-button>
          </a-space>
      </div>
    </div>

    <!-- 音频文件表格 -->
    <a-card :bordered="false">
      <a-table
        :dataSource="audioList"
        :columns="columns"
        :pagination="paginationConfig"
        :loading="loading"
        :row-selection="rowSelection"
        @change="onTableChange"
        row-key="id"
        :scroll="{ x: 1200 }"
      >
        <!-- 文件名列 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'filename'">
            <div class="filename-cell">
              <SoundOutlined class="file-icon" />
              <div class="file-info">
                <div class="file-name">{{ record.originalName }}</div>
                <div class="file-size">{{ record.fileSizeMB }}MB</div>
              </div>
            </div>
          </template>
          
          <!-- 项目信息列 -->
          <template v-else-if="column.key === 'project'">
            <div v-if="record.projectName" class="project-info">
              <a-tag color="blue">{{ record.projectName }}</a-tag>
              <div v-if="record.segmentOrder" class="segment-info">
                第{{ record.segmentOrder }}段
              </div>
            </div>
            <span v-else class="text-gray">-</span>
          </template>
          
          <!-- 音频类型列 -->
          <template v-else-if="column.key === 'audioType'">
            <a-tag :color="getTypeColor(record.audioType)">
              {{ getTypeLabel(record.audioType) }}
            </a-tag>
          </template>
          
          <!-- 操作列 -->
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-tooltip title="播放">
                <a-button
                  type="text"
                  size="small"
                  @click="playAudio(record)"
                  :icon="h(PlayCircleOutlined)"
                />
              </a-tooltip>
              <a-tooltip title="下载">
                <a-button
                  type="text"
                  size="small"
                  @click="downloadSingle(record)"
                  :icon="h(DownloadOutlined)"
                />
              </a-tooltip>
              <a-tooltip title="收藏">
                <a-button
                  type="text"
                  size="small"
                  @click="toggleFavorite(record)"
                  :icon="h(record.isFavorite ? HeartFilled : HeartOutlined)"
                  :class="{ 'favorite-active': record.isFavorite }"
                />
              </a-tooltip>
              <a-tooltip title="删除">
                <a-button
                  type="text"
                  size="small"
                  danger
                  @click="deleteSingle(record)"
                  :icon="h(DeleteOutlined)"
                />
              </a-tooltip>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 音频播放器弹窗 -->
    <a-modal
      v-model:open="playerVisible"
      title="音频播放器"
      :footer="null"
      width="600px"
      centered
    >
      <div v-if="currentAudio" class="audio-player-modal">
        <div class="audio-info">
          <h3>{{ currentAudio.originalName }}</h3>
          <div class="audio-meta">
            <a-space split>
              <span>时长: {{ currentAudio.durationFormatted }}</span>
              <span>大小: {{ currentAudio.fileSizeMB }}MB</span>
              <span v-if="currentAudio.projectName">项目: {{ currentAudio.projectName }}</span>
            </a-space>
          </div>
        </div>
        
        <div class="audio-player">
          <audio
            ref="audioRef"
            controls
            style="width: 100%"
            :src="currentAudio.audioUrl"
            @loadedmetadata="onAudioLoaded"
            @error="onAudioError"
          />
        </div>
        
        <div v-if="currentAudio.textContent" class="audio-text">
          <h4>对应文本：</h4>
          <div class="text-content">{{ currentAudio.textContent }}</div>
        </div>
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  SoundOutlined,
  DatabaseOutlined,
  ClockCircleOutlined,
  PlusCircleOutlined,
  ReloadOutlined,
  DownloadOutlined,
  DeleteOutlined,
  PlayCircleOutlined,
  HeartOutlined,
  HeartFilled,
  ArrowLeftOutlined
} from '@ant-design/icons-vue'
import { audioAPI, readerAPI } from '@/api'
import apiClient from '@/api/config'

// 路由
const router = useRouter()

// 响应式数据
const loading = ref(false)
const syncing = ref(false)
const downloading = ref(false)
const deleting = ref(false)
const audioList = ref([])
const projectList = ref([])
const stats = ref({})
const selectedRowKeys = ref([])
const playerVisible = ref(false)
const currentAudio = ref(null)
const audioRef = ref(null)

// 筛选条件
const filters = reactive({
  projectId: undefined,
  audioType: undefined,
  search: ''
})

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
})

// 表格列配置
const columns = [
  {
    title: '文件名',
    key: 'filename',
    width: 300,
    ellipsis: true
  },
  {
    title: '项目信息',
    key: 'project',
    width: 200
  },
  {
    title: '类型',
    key: 'audioType',
    width: 120
  },
  {
    title: '时长',
    dataIndex: 'durationFormatted',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'createdAt',
    width: 180,
    customRender: ({ text }) => text ? new Date(text).toLocaleString() : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 160,
    fixed: 'right'
  }
]

// 行选择配置
const rowSelection = {
  selectedRowKeys,
  onChange: (keys) => {
    selectedRowKeys.value = keys
  },
  onSelectAll: (selected, selectedRows, changeRows) => {
    console.log('onSelectAll', selected, selectedRows, changeRows)
  }
}

// 计算属性
const paginationConfig = computed(() => ({
  ...pagination,
  onChange: (page, pageSize) => {
    pagination.current = page
    pagination.pageSize = pageSize
    refreshAudioList()
  },
  onShowSizeChange: (page, pageSize) => {
    pagination.current = 1
    pagination.pageSize = pageSize
    refreshAudioList()
  }
}))

// 工具函数
const formatDuration = (seconds) => {
  if (!seconds || seconds === 0) return '00:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
}

// 方法
const refreshAudioList = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...filters
    }
    
    // 移除空值
    Object.keys(params).forEach(key => {
      if (params[key] === undefined || params[key] === '') {
        delete params[key]
      }
    })
    
    const response = await audioAPI.getFiles(params)
    
    if (response.data.success) {
      // 转换API数据字段名为前端使用的驼峰命名
      audioList.value = response.data.data.map(item => ({
        ...item,
        originalName: item.original_name,
        fileName: item.filename,
        filePath: item.file_path,
        fileSize: item.file_size,
        fileSizeMB: item.file_size ? (item.file_size / 1024 / 1024).toFixed(2) : '0.00',
        audioType: item.audio_type,
        textContent: item.text_content,
        isFavorite: item.is_favorite,
        createdAt: item.created_at,
        updatedAt: item.updated_at,
        durationFormatted: formatDuration(item.duration),
        projectName: item.project?.name,
        segmentOrder: item.segment_order,
        audioUrl: item.filename ? `/audio/${item.filename}` : null
      }))
      pagination.total = response.data.pagination.total
      pagination.current = response.data.pagination.page
    } else {
      message.error('获取音频列表失败')
    }
  } catch (error) {
    console.error('获取音频列表失败:', error)
    message.error('获取音频列表失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    loading.value = false
  }
}

const loadStats = async () => {
  try {
    const response = await audioAPI.getStats()
    if (response.data.success) {
      stats.value = response.data.data
    }
  } catch (error) {
    console.error('获取统计信息失败:', error)
  }
}

const loadProjectList = async () => {
  try {
    const response = await readerAPI.getProjects()
    if (response.data.success) {
      projectList.value = response.data.data
    }
  } catch (error) {
    console.error('获取项目列表失败:', error)
  }
}

const syncAudioFiles = async () => {
  syncing.value = true
  try {
    const response = await audioAPI.syncFiles()
    if (response.data.success) {
      message.success(`同步完成: 新增${response.data.synced_count}个文件`)
      await Promise.all([refreshAudioList(), loadStats()])
    }
  } catch (error) {
    console.error('同步音频文件失败:', error)
    message.error('同步音频文件失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    syncing.value = false
  }
}

const playAudio = (record) => {
  currentAudio.value = record
  playerVisible.value = true
}

const downloadSingle = async (record) => {
  try {
    const response = await audioAPI.downloadFile(record.id)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', record.originalName || record.filename)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success('下载成功')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败: ' + (error.response?.data?.detail || error.message))
  }
}

const batchDownload = async () => {
  if (!selectedRowKeys.value.length) {
    message.warning('请选择要下载的文件')
    return
  }
  
  downloading.value = true
  try {
    const response = await audioAPI.batchDownload(selectedRowKeys.value)
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.setAttribute('download', `音频文件_${new Date().toISOString().slice(0, 10)}.zip`)
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success(`成功下载 ${selectedRowKeys.value.length} 个文件`)
    selectedRowKeys.value = []
  } catch (error) {
    console.error('批量下载失败:', error)
    message.error('批量下载失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    downloading.value = false
  }
}

const deleteSingle = (record) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除音频文件 "${record.originalName}" 吗？此操作不可撤销。`,
    okText: '确定',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      try {
        const response = await audioAPI.deleteFile(record.id)
        if (response.data.success) {
          message.success('删除成功')
          await Promise.all([refreshAudioList(), loadStats()])
        }
      } catch (error) {
        console.error('删除失败:', error)
        message.error('删除失败: ' + (error.response?.data?.detail || error.message))
      }
    }
  })
}

const batchDelete = () => {
  if (!selectedRowKeys.value.length) {
    message.warning('请选择要删除的文件')
    return
  }
  
  Modal.confirm({
    title: '确认批量删除',
    content: `确定要删除选中的 ${selectedRowKeys.value.length} 个音频文件吗？此操作不可撤销。`,
    okText: '确定',
    cancelText: '取消',
    okType: 'danger',
    onOk: async () => {
      deleting.value = true
      try {
        const response = await audioAPI.batchDelete(selectedRowKeys.value)
        if (response.data.success) {
          message.success(`成功删除 ${response.data.deleted_count} 个文件`)
          selectedRowKeys.value = []
          await Promise.all([refreshAudioList(), loadStats()])
        }
      } catch (error) {
        console.error('批量删除失败:', error)
        message.error('批量删除失败: ' + (error.response?.data?.detail || error.message))
      } finally {
        deleting.value = false
      }
    }
  })
}

const toggleFavorite = async (record) => {
  try {
    const response = await audioAPI.setFavorite(record.id, !record.isFavorite)
    if (response.data.success) {
      record.isFavorite = !record.isFavorite
      message.success(record.isFavorite ? '已收藏' : '已取消收藏')
    }
  } catch (error) {
    console.error('设置收藏失败:', error)
    message.error('设置收藏失败: ' + (error.response?.data?.detail || error.message))
  }
}

const onTableChange = (pag, filters, sorter) => {
  console.log('Table change:', pag, filters, sorter)
}

const onAudioLoaded = () => {
  console.log('Audio loaded')
}

const onAudioError = (error) => {
  console.error('Audio error:', error)
  message.error('音频加载失败')
}

const getTypeColor = (type) => {
  const colors = {
    segment: 'blue',
    project: 'green',
    single: 'orange',
    test: 'purple',
    unknown: 'gray'
  }
  return colors[type] || 'gray'
}

const getTypeLabel = (type) => {
  const labels = {
    segment: '分段音频',
    project: '项目合成',
    single: '单句合成',
    test: '测试音频',
    unknown: '未知类型'
  }
  return labels[type] || '未知类型'
}

const goBack = () => {
  router.go(-1)
}

// 生命周期
onMounted(() => {
  // 使用立即执行的异步函数处理初始化
  (async () => {
    try {
      await Promise.all([
        refreshAudioList(),
        loadStats(),
        loadProjectList()
      ])
    } catch (error) {
      console.error('🔴 [AudioLibrary] 初始化过程中发生错误:', error)
      message.error('页面初始化失败: ' + error.message)
    }
  })()
})
</script>

<style scoped>
.audio-library {
  padding: 0;
}

.page-header {
  background: white;
  margin-bottom: 16px;
}

.stats-cards {
  margin-bottom: 16px;
}

.stats-cards .ant-card {
  text-align: center;
}

/* 筛选部分 */
.filter-section {
  background: white;
  padding: 24px;
  border-radius: 12px;
  margin-bottom: 24px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}

.filter-controls {
  display: flex;
  gap: 16px;
  align-items: center;
}

.action-controls {
  display: flex;
  gap: 12px;
  align-items: center;
}

.filename-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.file-icon {
  color: #1890ff;
  font-size: 16px;
}

.file-info {
  flex: 1;
  min-width: 0;
}

.file-name {
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.file-size {
  font-size: 12px;
  color: #999;
}

.project-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.segment-info {
  font-size: 12px;
  color: #666;
}

.text-gray {
  color: #999;
}

.favorite-active {
  color: #ff4d4f !important;
}

.audio-player-modal {
  padding: 16px 0;
}

.audio-info {
  margin-bottom: 16px;
}

.audio-info h3 {
  margin: 0 0 8px 0;
  font-size: 16px;
}

.audio-meta {
  color: #666;
  font-size: 14px;
}

.audio-player {
  margin-bottom: 16px;
}

.audio-text {
  border-top: 1px solid #f0f0f0;
  padding-top: 16px;
}

.audio-text h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  color: #333;
}

.text-content {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 14px;
  line-height: 1.6;
  max-height: 120px;
  overflow-y: auto;
}

.title-with-back {
  display: flex;
  align-items: center;
  gap: 8px;
}

.back-btn {
  padding: 0;
  background: transparent;
  border: none;
}
</style> 