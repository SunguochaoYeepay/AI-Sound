<template>
  <div class="environment-sounds-page">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <SoundOutlined class="title-icon" />
            环境音管理
          </h1>
          <p class="page-description">
            使用TangoFlux AI模型生成各种环境音效，支持自然音、城市音、机械音等多种类型
          </p>
        </div>
        <div class="action-section">
          <a-button 
            type="primary" 
            size="large"
            @click="showGenerateModal = true"
            :loading="generating"
          >
            <PlusOutlined />
            生成环境音
          </a-button>
        </div>
      </div>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-section">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总环境音"
              :value="stats.total_sounds"
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
              :value="stats.completed_sounds"
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
              title="生成中"
              :value="stats.processing_sounds"
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
              title="总播放"
              :value="stats.total_plays"
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
              placeholder="搜索环境音名称、描述或提示词"
              style="width: 300px"
              @pressEnter="loadSounds"
            >
              <template #prefix>
                <SearchOutlined />
              </template>
            </a-input>
          </a-form-item>
          
          <a-form-item label="分类">
            <a-select
              v-model:value="searchForm.category_id"
              placeholder="选择分类"
              style="width: 150px"
              allowClear
              @change="loadSounds"
            >
              <a-select-option
                v-for="category in categories"
                :key="category.id"
                :value="category.id"
              >
                {{ category.name }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="标签">
            <a-select
              v-model:value="searchForm.tag_ids"
              mode="multiple"
              placeholder="选择标签"
              style="width: 200px"
              allowClear
              @change="loadSounds"
            >
              <a-select-option
                v-for="tag in tags"
                :key="tag.id"
                :value="tag.id"
              >
                <a-tag :color="tag.color" style="margin: 0;">
                  {{ tag.name }}
                </a-tag>
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="状态">
            <a-select
              v-model:value="searchForm.status"
              placeholder="生成状态"
              style="width: 120px"
              allowClear
              @change="loadSounds"
            >
              <a-select-option value="completed">已完成</a-select-option>
              <a-select-option value="processing">生成中</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item>
            <a-button type="primary" @click="loadSounds">
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

    <!-- 环境音列表 -->
    <div class="sounds-section">
      <a-card>
        <template #title>
          <div class="list-header">
            <span>环境音列表</span>
            <div class="list-actions">
              <a-switch
                v-model:checked="showFeaturedOnly"
                checkedChildren="精选"
                unCheckedChildren="全部"
                @change="loadSounds"
              />
              <a-select
                v-model:value="sortBy"
                style="width: 120px; margin-left: 8px"
                @change="loadSounds"
              >
                <a-select-option value="created_at">创建时间</a-select-option>
                <a-select-option value="play_count">播放次数</a-select-option>
                <a-select-option value="download_count">下载次数</a-select-option>
                <a-select-option value="favorite_count">收藏数</a-select-option>
                <a-select-option value="duration">时长</a-select-option>
              </a-select>
            </div>
          </div>
        </template>

        <div class="sounds-grid">
          <div
            v-for="sound in sounds"
            :key="sound.id"
            class="sound-card"
            :class="{ 'featured': sound.is_featured }"
          >
            <!-- 状态标识 -->
            <div class="status-badge">
              <a-badge
                :status="getStatusType(sound.generation_status)"
                :text="getStatusText(sound.generation_status)"
              />
            </div>

            <!-- 精选标识 -->
            <div v-if="sound.is_featured" class="featured-badge">
              <StarFilled />
            </div>

            <!-- 音频信息 -->
            <div class="sound-info">
              <h3 class="sound-name">{{ sound.name }}</h3>
              <p class="sound-prompt">{{ sound.prompt }}</p>
              <div class="sound-meta">
                <a-tag v-if="sound.category" :color="'blue'">
                  {{ sound.category.name }}
                </a-tag>
                <a-tag
                  v-for="tag in sound.tags"
                  :key="tag.id"
                  :color="tag.color"
                  style="margin: 2px;"
                >
                  {{ tag.name }}
                </a-tag>
              </div>
              <div class="sound-params">
                <span class="param">{{ sound.duration }}s</span>
                <span class="param">{{ sound.steps }} steps</span>
                <span class="param">CFG {{ sound.cfg_scale }}</span>
              </div>
            </div>

            <!-- 统计信息 -->
            <div class="sound-stats">
              <div class="stat-item">
                <PlayCircleOutlined />
                {{ sound.play_count }}
              </div>
              <div class="stat-item">
                <DownloadOutlined />
                {{ sound.download_count }}
              </div>
              <div class="stat-item">
                <HeartOutlined />
                {{ sound.favorite_count }}
              </div>
            </div>

            <!-- 操作按钮 -->
            <div class="sound-actions">
              <a-button-group size="small">
                <a-button
                  v-if="sound.generation_status === 'completed'"
                  type="primary"
                  @click="playSound(sound)"
                  :loading="playingId === sound.id"
                >
                  <PlayCircleOutlined />
                </a-button>
                
                <a-button
                  v-if="sound.generation_status === 'completed'"
                  @click="downloadSound(sound)"
                >
                  <DownloadOutlined />
                </a-button>

                <a-button
                  @click="toggleFavorite(sound)"
                  :type="sound.is_favorited ? 'primary' : 'default'"
                >
                  <HeartOutlined />
                </a-button>

                <a-dropdown>
                  <a-button>
                    <MoreOutlined />
                  </a-button>
                  <template #overlay>
                    <a-menu>
                      <a-menu-item
                        v-if="sound.generation_status === 'failed'"
                        @click="regenerateSound(sound)"
                      >
                        <RedoOutlined />
                        重新生成
                      </a-menu-item>
                      <a-menu-item @click="editSound(sound)">
                        <EditOutlined />
                        编辑
                      </a-menu-item>
                      <a-menu-item @click="copyPrompt(sound.prompt)">
                        <CopyOutlined />
                        复制提示词
                      </a-menu-item>
                      <a-menu-divider />
                      <a-menu-item danger @click="deleteSound(sound)">
                        <DeleteOutlined />
                        删除
                      </a-menu-item>
                    </a-menu>
                  </template>
                </a-dropdown>
              </a-button-group>
            </div>

            <!-- 错误信息 -->
            <div v-if="sound.generation_status === 'failed'" class="error-message">
              <a-alert
                type="error"
                :message="sound.error_message || '生成失败'"
                banner
              />
            </div>
          </div>
        </div>

        <!-- 空状态 -->
        <a-empty
          v-if="!loading && sounds.length === 0"
          description="暂无环境音"
        >
          <a-button type="primary" @click="showGenerateModal = true">
            立即生成
          </a-button>
        </a-empty>

        <!-- 分页 -->
        <div v-if="pagination.total > 0" class="pagination-section">
          <a-pagination
            v-model:current="pagination.current"
            v-model:page-size="pagination.pageSize"
            :total="pagination.total"
            show-size-changer
            show-quick-jumper
            :show-total="(total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`"
            @change="loadSounds"
            @showSizeChange="loadSounds"
          />
        </div>
      </a-card>
    </div>

    <!-- 生成环境音弹窗 -->
    <GenerateModal
      v-model:visible="showGenerateModal"
      :categories="categories"
      :tags="tags"
      :presets="presets"
      @generated="onSoundGenerated"
    />

    <!-- 编辑环境音弹窗 -->
    <EditModal
      v-model:visible="showEditModal"
      :sound="editingSound"
      :categories="categories"
      :tags="tags"
      @updated="onSoundUpdated"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { message, Modal } from 'ant-design-vue'
import {
  SoundOutlined, PlusOutlined, SearchOutlined, PlayCircleOutlined,
  DownloadOutlined, HeartOutlined, MoreOutlined, EditOutlined,
  DeleteOutlined, CopyOutlined, RedoOutlined, CheckCircleOutlined,
  LoadingOutlined, StarFilled
} from '@ant-design/icons-vue'

import GenerateModal from '@/components/environment-sounds/GenerateModal.vue'
import EditModal from '@/components/environment-sounds/EditModal.vue'
import { audioService } from '@/utils/audioService'
import api from '@/api'

// 响应式数据
const loading = ref(false)
const generating = ref(false)
const playingId = ref(null)
const sounds = ref([])
const categories = ref([])
const tags = ref([])
const presets = ref([])

// 统计数据
const stats = reactive({
  total_sounds: 0,
  completed_sounds: 0,
  processing_sounds: 0,
  failed_sounds: 0,
  total_plays: 0
})

// 搜索表单
const searchForm = reactive({
  search: '',
  category_id: null,
  tag_ids: [],
  status: null
})

// 排序和筛选
const showFeaturedOnly = ref(false)
const sortBy = ref('created_at')

// 分页
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0
})

// 弹窗控制
const showGenerateModal = ref(false)
const showEditModal = ref(false)
const editingSound = ref(null)

// 生命周期
onMounted(() => {
  loadInitialData()
})

// 方法
const loadInitialData = async () => {
  await Promise.all([
    loadCategories(),
    loadTags(),
    loadPresets(),
    loadStats(),
    loadSounds()
  ])
}

const loadCategories = async () => {
  try {
    const response = await api.get('/api/v1/environment-sounds/categories')
    categories.value = response.data
  } catch (error) {
    console.error('加载分类失败:', error)
  }
}

const loadTags = async () => {
  try {
    const response = await api.get('/api/v1/environment-sounds/tags')
    tags.value = response.data
  } catch (error) {
    console.error('加载标签失败:', error)
  }
}

const loadPresets = async () => {
  try {
    const response = await api.get('/api/v1/environment-sounds/presets')
    presets.value = response.data
  } catch (error) {
    console.error('加载预设失败:', error)
  }
}

const loadStats = async () => {
  try {
    const response = await api.get('/api/v1/environment-sounds/stats')
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('加载统计数据失败:', error)
  }
}

const loadSounds = async () => {
  loading.value = true
  try {
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      ...searchForm,
      featured_only: showFeaturedOnly.value,
      sort_by: sortBy.value,
      sort_order: 'desc'
    }

    // 处理数组参数
    if (params.tag_ids && params.tag_ids.length > 0) {
      params.tag_ids = params.tag_ids.join(',')
    } else {
      delete params.tag_ids
    }

    const response = await api.get('/api/v1/environment-sounds/', { params })
    const data = response.data

    sounds.value = data.sounds
    pagination.total = data.total
    pagination.current = data.page
    pagination.pageSize = data.page_size

  } catch (error) {
    console.error('加载环境音列表失败:', error)
    message.error('加载环境音列表失败')
  } finally {
    loading.value = false
  }
}

const resetSearch = () => {
  Object.assign(searchForm, {
    search: '',
    category_id: null,
    tag_ids: [],
    status: null
  })
  showFeaturedOnly.value = false
  sortBy.value = 'created_at'
  pagination.current = 1
  loadSounds()
}

const playSound = async (sound) => {
  try {
    playingId.value = sound.id
    
    // 记录播放日志
    await api.post(`/api/v1/environment-sounds/${sound.id}/play`)
    
    // 使用统一音频服务播放
    await audioService.playEnvironmentSound(sound)
    
    // 更新播放计数
    sound.play_count += 1
    
  } catch (error) {
    console.error('播放失败:', error)
    message.error('播放失败')
  } finally {
    playingId.value = null
  }
}

const downloadSound = async (sound) => {
  try {
    const response = await api.get(`/api/v1/environment-sounds/${sound.id}/download`, {
      responseType: 'blob'
    })
    
    // 创建下载链接
    const url = window.URL.createObjectURL(new Blob([response.data]))
    const link = document.createElement('a')
    link.href = url
    link.download = `${sound.name}.wav`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
    
    // 更新下载计数
    sound.download_count += 1
    message.success('下载成功')
    
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

const toggleFavorite = async (sound) => {
  try {
    const response = await api.post(`/api/v1/environment-sounds/${sound.id}/favorite`)
    const result = response.data
    
    sound.is_favorited = result.is_favorited
    sound.favorite_count = result.favorite_count
    
    message.success(result.is_favorited ? '已收藏' : '已取消收藏')
    
  } catch (error) {
    console.error('收藏操作失败:', error)
    message.error('收藏操作失败')
  }
}

const regenerateSound = async (sound) => {
  try {
    await api.post(`/api/v1/environment-sounds/${sound.id}/regenerate`)
    sound.generation_status = 'processing'
    sound.error_message = null
    message.success('重新生成任务已启动')
    
    // 定期检查生成状态
    checkGenerationStatus(sound.id)
    
  } catch (error) {
    console.error('重新生成失败:', error)
    message.error('重新生成失败')
  }
}

const editSound = (sound) => {
  editingSound.value = { ...sound }
  showEditModal.value = true
}

const deleteSound = (sound) => {
  Modal.confirm({
    title: '确认删除',
    content: `确定要删除环境音"${sound.name}"吗？此操作不可恢复。`,
    onOk: async () => {
      try {
        await api.delete(`/api/v1/environment-sounds/${sound.id}`)
        message.success('删除成功')
        loadSounds()
        loadStats()
      } catch (error) {
        console.error('删除失败:', error)
        message.error('删除失败')
      }
    }
  })
}

const copyPrompt = (prompt) => {
  navigator.clipboard.writeText(prompt).then(() => {
    message.success('提示词已复制到剪贴板')
  }).catch(() => {
    message.error('复制失败')
  })
}

const onSoundGenerated = (soundId) => {
  showGenerateModal.value = false
  loadSounds()
  loadStats()
  
  // 开始检查生成状态
  checkGenerationStatus(soundId)
}

const onSoundUpdated = () => {
  showEditModal.value = false
  editingSound.value = null
  loadSounds()
}

const checkGenerationStatus = (soundId) => {
  const interval = setInterval(async () => {
    try {
      const response = await api.get(`/api/v1/environment-sounds/${soundId}`)
      const sound = response.data
      
      // 更新列表中的对应项
      const index = sounds.value.findIndex(s => s.id === soundId)
      if (index !== -1) {
        sounds.value[index] = sound
      }
      
      // 如果生成完成或失败，停止检查
      if (sound.generation_status === 'completed' || sound.generation_status === 'failed') {
        clearInterval(interval)
        loadStats() // 更新统计数据
        
        if (sound.generation_status === 'completed') {
          message.success(`环境音"${sound.name}"生成完成`)
        } else {
          message.error(`环境音"${sound.name}"生成失败`)
        }
      }
      
    } catch (error) {
      clearInterval(interval)
      console.error('检查生成状态失败:', error)
    }
  }, 3000) // 每3秒检查一次
}

// 辅助方法
const getStatusType = (status) => {
  const statusMap = {
    'completed': 'success',
    'processing': 'processing',
    'failed': 'error',
    'pending': 'default'
  }
  return statusMap[status] || 'default'
}

const getStatusText = (status) => {
  const statusMap = {
    'completed': '已完成',
    'processing': '生成中',
    'failed': '失败',
    'pending': '等待中'
  }
  return statusMap[status] || '未知'
}
</script>

<style scoped>
.environment-sounds-page {
  padding: 24px;
}

.page-header {
  margin-bottom: 24px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title-section .page-title {
  display: flex;
  align-items: center;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: #1a1a1a;
}

.title-icon {
  margin-right: 12px;
  color: #1890ff;
}

.page-description {
  margin: 0;
  color: #666;
  font-size: 14px;
  line-height: 1.5;
}

.stats-section {
  margin-bottom: 24px;
}

.filter-section {
  margin-bottom: 24px;
}

.list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.list-actions {
  display: flex;
  align-items: center;
}

.sounds-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
  margin-bottom: 24px;
}

.sound-card {
  position: relative;
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  padding: 16px;
  background: #fff;
  transition: all 0.3s ease;
}

.sound-card:hover {
  border-color: #1890ff;
  box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
}

.sound-card.featured {
  border-color: #faad14;
  background: linear-gradient(135deg, #fff9e6 0%, #fff 100%);
}

.status-badge {
  position: absolute;
  top: 12px;
  right: 12px;
}

.featured-badge {
  position: absolute;
  top: 12px;
  left: 12px;
  color: #faad14;
  font-size: 16px;
}

.sound-info {
  margin-bottom: 12px;
}

.sound-name {
  margin: 0 0 8px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
  line-height: 1.4;
}

.sound-prompt {
  margin: 0 0 8px 0;
  color: #666;
  font-size: 14px;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.sound-meta {
  margin-bottom: 8px;
}

.sound-params {
  display: flex;
  gap: 8px;
}

.param {
  padding: 2px 6px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  color: #666;
}

.sound-stats {
  display: flex;
  gap: 16px;
  margin-bottom: 12px;
  padding: 8px 0;
  border-top: 1px solid #f0f0f0;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #666;
  font-size: 12px;
}

.sound-actions {
  display: flex;
  justify-content: flex-end;
}

.error-message {
  margin-top: 12px;
}

.pagination-section {
  display: flex;
  justify-content: center;
  margin-top: 24px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environment-sounds-page {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .sounds-grid {
    grid-template-columns: 1fr;
  }
  
  .filter-section :deep(.ant-form-inline) {
    display: block;
  }
  
  .filter-section :deep(.ant-form-item) {
    margin-bottom: 16px;
  }
}
</style> 