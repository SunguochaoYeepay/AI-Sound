<template>
  <div class="environment-mixing-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <SoundOutlined class="title-icon" />
            环境混音
          </h1>
          <p class="page-description">
            智能分析书籍内容，自动匹配环境音效库，生成沉浸式环境混音作品<br/>
            <small style="color: rgba(255,255,255,0.7);">📚 基于书籍准备JSON + 🎵 环境音效库 → 🎬 最终混音文件</small>
          </p>
        </div>
        <div class="action-section">
          <a-space size="large">
            <a-button 
              type="primary" 
              size="large"
              @click="showEnvironmentConfigDrawer = true"
              :loading="loading"
            >
              <ThunderboltOutlined />
              智能配置混音
            </a-button>
            <a-button 
              size="large"
              @click="loadMixingResults"
              :loading="loading"
            >
              <ReloadOutlined />
              刷新列表
            </a-button>
          </a-space>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="混音作品"
              :value="stats.total_mixings"
              :value-style="{ color: '#1890ff' }"
            >
              <template #prefix>
                <SoundOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="已完成"
              :value="stats.completed_mixings"
              :value-style="{ color: '#52c41a' }"
            >
              <template #prefix>
                <CheckCircleOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="处理中"
              :value="stats.processing_mixings"
              :value-style="{ color: '#fa8c16' }"
            >
              <template #prefix>
                <LoadingOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="环境音轨"
              :value="stats.total_tracks"
              :value-style="{ color: '#722ed1' }"
            >
              <template #prefix>
                <PlayCircleOutlined />
              </template>
            </a-statistic>
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 筛选和搜索 -->
    <div class="filter-section">
      <a-card>
        <a-form layout="inline" :model="searchForm">
          <a-form-item label="搜索">
            <a-input
              v-model:value="searchForm.search"
              placeholder="搜索混音作品名称或描述"
              style="width: 300px"
              @pressEnter="loadMixingResults"
            >
              <template #prefix>
                <SearchOutlined />
              </template>
            </a-input>
          </a-form-item>
          
          <a-form-item label="项目">
            <a-select
              v-model:value="searchForm.project_id"
              placeholder="选择项目"
              style="width: 200px"
              allowClear
              @change="loadMixingResults"
            >
              <a-select-option
                v-for="project in projects"
                :key="project.id"
                :value="project.id"
              >
                {{ project.name }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="状态">
            <a-select
              v-model:value="searchForm.status"
              placeholder="处理状态"
              style="width: 120px"
              allowClear
              @change="loadMixingResults"
            >
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="processing">处理中</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item>
            <a-button type="primary" @click="loadMixingResults">
              <SearchOutlined />
              搜索
            </a-button>
          </a-form-item>

          <a-form-item>
            <a-button @click="resetSearch">
              重置
            </a-button>
          </a-form-item>
        </a-form>
      </a-card>
    </div>

    <!-- 混音作品列表 -->
    <div class="mixings-section">
      <a-card>
        <template #title>
          <div class="list-header">
            <span>环境混音作品</span>
            <a-tag color="blue">{{ mixingResults.length }} 个作品</a-tag>
          </div>
        </template>

        <a-spin :spinning="loading">
          <div v-if="mixingResults.length === 0" class="empty-state">
            <a-empty
              image="https://gw.alipayobjects.com/zos/antfincdn/ZHrcdLPrvN/empty.svg"
              description="暂无环境混音作品"
            >
              <template #image>
                <SoundOutlined style="color: #bfbfbf; font-size: 48px;" />
              </template>
              <a-button type="primary" @click="showEnvironmentConfigDrawer = true">
                <ThunderboltOutlined />
                智能配置混音
              </a-button>
            </a-empty>
          </div>

          <div v-else class="mixings-grid">
            <a-card 
              v-for="mixing in mixingResults" 
              :key="mixing.id"
              class="mixing-card"
              size="small"
              :hoverable="true"
            >
              <template #title>
                <div class="mixing-title">
                  <SoundOutlined />
                  {{ mixing.name || `环境混音 ${mixing.id}` }}
                </div>
              </template>
              
              <template #extra>
                <a-dropdown>
                  <a-button type="text" size="small">
                    <MoreOutlined />
                  </a-button>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item key="play" @click="previewMixing(mixing)">
                        <PlayCircleOutlined />
                        播放预览
                      </a-menu-item>
                      <a-menu-item key="download" @click="downloadMixing(mixing)">
                        <DownloadOutlined />
                        下载作品
                      </a-menu-item>
                      <a-menu-item key="edit" @click="editMixing(mixing)">
                        <EditOutlined />
                        编辑配置
                      </a-menu-item>
                      <a-menu-divider />
                      <a-menu-item key="delete" danger @click="deleteMixing(mixing)">
                        <DeleteOutlined />
                        删除作品
                      </a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </template>
              
              <div class="mixing-info">
                <p><strong>项目：</strong>{{ getProjectName(mixing.project_id) }}</p>
                <p><strong>章节：</strong>{{ getChapterName(mixing.chapter_id) }}</p>
                <p><strong>状态：</strong>
                  <a-tag :color="getMixingStatusColor(mixing.status)">
                    {{ getMixingStatusText(mixing.status) }}
                  </a-tag>
                </p>
                <p><strong>环境音轨：</strong>{{ mixing.environment_tracks_count || 0 }} 个</p>
                <p><strong>总时长：</strong>{{ formatDuration(mixing.duration) }}</p>
                <p><strong>创建时间：</strong>{{ formatDate(mixing.created_at) }}</p>
              </div>
              
              <div class="mixing-actions">
                <a-space>
                  <a-button 
                    type="primary" 
                    size="small" 
                    @click="previewMixing(mixing)"
                    :disabled="mixing.status !== 'completed'"
                    :loading="playingId === mixing.id"
                  >
                    <PlayCircleOutlined />
                    播放
                  </a-button>
                  <a-button 
                    size="small" 
                    @click="downloadMixing(mixing)"
                    :disabled="mixing.status !== 'completed'"
                  >
                    <DownloadOutlined />
                    下载
                  </a-button>
                </a-space>
              </div>
            </a-card>
          </div>
        </a-spin>
      </a-card>
    </div>



    <!-- 环境混音配置抽屉 -->
    <EnvironmentMixingAnalysisDrawer
      :visible="showEnvironmentConfigDrawer"
      @update:visible="showEnvironmentConfigDrawer = $event"
      @complete="handleMixingConfigComplete"
      @start-mixing="handleStartEnvironmentMixing"
    />

    <!-- 环境混音编辑抽屉 -->
    <EnvironmentMixingEditDrawer
      :visible="showEditDrawer"
      :mixing-id="editingMixingId"
      @update:visible="showEditDrawer = $event"
      @updated="handleMixingUpdated"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
import {
  SoundOutlined, SearchOutlined, PlayCircleOutlined,
  DownloadOutlined, MoreOutlined, EditOutlined,
  DeleteOutlined, CheckCircleOutlined, LoadingOutlined,
  ThunderboltOutlined, ReloadOutlined
} from '@ant-design/icons-vue'

import EnvironmentMixingAnalysisDrawer from '@/components/environment-mixing/EnvironmentMixingAnalysisDrawer.vue'
import EnvironmentMixingEditDrawer from '@/components/environment-mixing/EnvironmentMixingEditDrawer.vue'
import { getAudioService } from '@/utils/audioService'
import api from '@/api'

const router = useRouter()

// 响应式数据
const loading = ref(false)
const playingId = ref(null)
const mixingResults = ref([])
const projects = ref([])

// 抽屉状态
const showEnvironmentConfigDrawer = ref(false)
const showEditDrawer = ref(false)
const editingMixingId = ref(null)

// 统计数据
const stats = reactive({
  total_mixings: 0,
  completed_mixings: 0,
  processing_mixings: 0,
  failed_mixings: 0,
  total_tracks: 0
})

// 搜索表单
const searchForm = reactive({
  search: '',
  project_id: null,
  status: ''
})

// 初始化
onMounted(async () => {
  await loadProjects()
  await loadMixingResults()
  await loadStats()
})

// 加载项目列表
const loadProjects = async () => {
  try {
    const response = await api.getProjects()
    if (response.data.success) {
      projects.value = response.data.data || []
    }
  } catch (error) {
    console.error('加载项目列表失败:', error)
  }
}

// 加载混音结果
const loadMixingResults = async () => {
  try {
    loading.value = true
    const params = {
      search: searchForm.search || undefined,
      project_id: searchForm.project_id || undefined,
      status: searchForm.status || undefined
    }
    
    const response = await api.getEnvironmentMixingResults(params)
    if (response.data.success) {
      mixingResults.value = response.data.data || []
    }
  } catch (error) {
    console.error('加载环境混音结果失败:', error)
    message.error('加载环境混音结果失败')
  } finally {
    loading.value = false
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    const response = await api.getEnvironmentMixingStats()
    if (response.data.success) {
      Object.assign(stats, response.data.data)
    }
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}



// 预览混音
const previewMixing = async (mixing) => {
  try {
    playingId.value = mixing.id
    await getAudioService().playEnvironmentMixing(mixing)
    message.success('开始播放环境混音')
  } catch (error) {
    console.error('播放失败:', error)
    message.error('播放失败')
  } finally {
    playingId.value = null
  }
}

// 下载混音
const downloadMixing = async (mixing) => {
  try {
    const response = await api.downloadEnvironmentMixing(mixing.id)
    
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${mixing.name || `环境混音_${mixing.id}`}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    message.success('下载完成')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

// 编辑混音
const editMixing = (mixing) => {
  editingMixingId.value = mixing.id
  showEditDrawer.value = true
  console.log('打开编辑抽屉:', mixing)
}

// 删除混音
const deleteMixing = (mixing) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除环境混音作品"${mixing.name || mixing.id}"吗？此操作不可恢复。`,
    onOk: async () => {
      try {
        await api.deleteEnvironmentMixing(mixing.id)
        message.success('删除成功')
        loadMixingResults()
        loadStats()
      } catch (error) {
        console.error('删除失败:', error)
        message.error('删除失败')
      }
    }
  })
}

// 处理混音配置完成
const handleMixingConfigComplete = () => {
  message.success('环境混音配置完成！')
  showEnvironmentConfigDrawer.value = false
  loadMixingResults()
  loadStats()
}

// 处理开始环境混音
const handleStartEnvironmentMixing = async (environmentConfig) => {
  try {
    message.info('开始环境混音合成...')
    showEnvironmentConfigDrawer.value = false
    
    // environmentConfig应该包含项目信息
    const response = await api.startEnvironmentMixing(environmentConfig.project_id, {
      environment_config: environmentConfig
    })
    
    if (response.data.success) {
      message.success('环境混音合成已开始！')
      loadMixingResults()
      loadStats()
    } else {
      message.error(response.data.message || '启动环境混音失败')
    }
  } catch (error) {
    console.error('启动环境混音失败:', error)
    message.error('启动环境混音失败: ' + (error.response?.data?.detail || error.message))
  }
}

// 处理混音更新
const handleMixingUpdated = (updatedMixing) => {
  message.success('环境混音配置更新成功')
  
  // 更新列表中的对应项目
  const index = mixingResults.value.findIndex(m => m.id === updatedMixing.id)
  if (index !== -1) {
    mixingResults.value[index] = { ...mixingResults.value[index], ...updatedMixing }
  }
  
  // 重新加载数据以确保一致性
  loadMixingResults()
  loadStats()
}

// 重置搜索
const resetSearch = () => {
  searchForm.search = ''
  searchForm.project_id = null
  searchForm.status = ''
  loadMixingResults()
}

// 辅助函数
const getProjectName = (projectId) => {
  if (!projectId) return '未知项目'
  const project = projects.value.find(p => p.id === projectId)
  return project ? project.name : `项目 ${projectId}`
}

const getChapterName = (chapterId) => {
  return chapterId ? `第${chapterId}章` : '全书'
}

const getMixingStatusColor = (status) => {
  const colors = {
    'completed': 'green',
    'processing': 'orange',
    'failed': 'red',
    'pending': 'blue'
  }
  return colors[status] || 'default'
}

const getMixingStatusText = (status) => {
  const texts = {
    'completed': '已完成',
    'processing': '处理中',
    'failed': '失败',
    'pending': '待处理'
  }
  return texts[status] || status
}



const formatDuration = (seconds) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN') + ' ' + date.toLocaleTimeString('zh-CN', { 
    hour: '2-digit', 
    minute: '2-digit' 
  })
}
</script>

<style scoped>
.environment-mixing-page {
  padding: 24px;
  min-height: 100vh;
}

.page-header {
  background: rgba(255, 255, 255, 0.1);
  backdrop-filter: blur(10px);
  border-radius: 12px;
  padding: 24px;
  margin-bottom: 24px;
  border: 1px solid rgba(255, 255, 255, 0.2);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.title-section h1 {
  color: white;
  margin: 0;
  font-size: 28px;
  font-weight: 600;
}

.title-icon {
  margin-right: 12px;
  color: #ffd700;
}

.page-description {
  color: rgba(255, 255, 255, 0.9);
  margin: 8px 0 0 0;
  font-size: 16px;
  line-height: 1.5;
}

.stats-section {
  margin-bottom: 24px;
}

.filter-section {
  margin-bottom: 24px;
}

.mixings-section {
  margin-bottom: 24px;
}

.list-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.mixings-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.mixing-card {
  border-radius: 8px;
  transition: all 0.3s ease;
}

.mixing-card:hover {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.1);
  transform: translateY(-2px);
}

.mixing-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
}

.mixing-info p {
  margin: 4px 0;
  font-size: 13px;
  line-height: 1.4;
}

.mixing-info strong {
  color: #1f2937;
  font-weight: 500;
}

.mixing-actions {
  margin-top: 12px;
  padding-top: 12px;
  border-top: 1px solid #f0f0f0;
}

.project-selector-content {
  padding: 16px 0;
}

.projects-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.project-card {
  cursor: pointer;
  transition: all 0.3s ease;
}

.project-card:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  transform: translateY(-1px);
}

.project-info p {
  margin: 4px 0;
  font-size: 13px;
}

.empty-state {
  text-align: center;
  padding: 48px 16px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .environment-mixing-page {
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
    text-align: center;
  }
  
  .mixings-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }
}
</style> 