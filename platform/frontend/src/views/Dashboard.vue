<template>
  <div class="dashboard">
    <!-- 顶部概览卡片 -->
    <a-row :gutter="[24, 24]" class="overview-cards">
      <a-col :span="6">
        <a-card :hoverable="true" class="stat-card">
          <a-statistic title="书籍总数" :value="stats.bookCount" :loading="loading">
            <template #prefix>
              <BookOutlined style="color: #1890ff" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>

      <a-col :span="6">
        <a-card :hoverable="true" class="stat-card">
          <a-statistic title="活跃合成任务" :value="stats.activeTasks" :loading="loading">
            <template #prefix>
              <SoundOutlined style="color: #52c41a" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>

      <a-col :span="6">
        <a-card :hoverable="true" class="stat-card">
          <a-statistic title="分析会话" :value="stats.activeSessions" :loading="loading">
            <template #prefix>
              <BulbOutlined style="color: #fa8c16" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>

      <a-col :span="6">
        <a-card :hoverable="true" class="stat-card">
          <a-statistic title="音频文件" :value="stats.audioFiles" :loading="loading">
            <template #prefix>
              <AudioOutlined style="color: #722ed1" />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>

    <!-- 快速操作和系统状态 -->
    <a-row :gutter="[24, 24]" style="margin-top: 24px">
      <!-- 快速操作 -->
      <a-col :span="12">
        <a-card title="快速操作" :hoverable="true">
          <template #extra>
            <a-button type="link" size="small">查看全部</a-button>
          </template>

          <div class="quick-actions">
            <a-button type="primary" size="large" class="action-btn" @click="goToPage('/books')">
              <template #icon>
                <PlusOutlined />
              </template>
              上传新书籍
            </a-button>

            <a-button size="large" class="action-btn" @click="goToPage('/novel-reader')">
              <template #icon>
                <RocketOutlined />
              </template>
              开始合成
            </a-button>

            <a-button size="large" class="action-btn" @click="goToPage('/characters')">
              <template #icon>
                <UserOutlined />
              </template>
              管理声音
            </a-button>

            <a-button size="large" class="action-btn" @click="goToPage('/audio-library')">
              <template #icon>
                <FolderOutlined />
              </template>
              音频库
            </a-button>
          </div>
        </a-card>
      </a-col>

      <!-- 系统状态详情 -->
      <a-col :span="12">
        <SystemStatus />
      </a-col>
    </a-row>

    <!-- 日志监控 -->
    <a-row :gutter="[24, 24]" style="margin-top: 24px">
      <a-col :span="24">
        <LogSummary />
      </a-col>
    </a-row>

    <!-- 最近活动 -->
    <a-row :gutter="[24, 24]" style="margin-top: 24px">
      <!-- 最近任务 -->
      <a-col :span="12">
        <a-card title="最近任务" :hoverable="true">
          <template #extra>
            <a-button type="link" size="small" @click="goToPage('/synthesis')"> 查看全部 </a-button>
          </template>

          <a-list :data-source="recentTasks" :loading="tasksLoading" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #title>
                    <span>{{ item.name }}</span>
                    <a-tag
                      :color="getTaskStatusColor(item.status)"
                      size="small"
                      style="margin-left: 8px"
                    >
                      {{ getTaskStatusText(item.status) }}
                    </a-tag>
                  </template>
                  <template #description>
                    <div class="task-meta">
                      <span>{{ formatTime(item.created_at) }}</span>
                      <a-progress
                        :percent="item.progress || 0"
                        size="small"
                        :show-info="false"
                        style="margin-left: 12px; flex: 1"
                      />
                    </div>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>

      <!-- 最近书籍 -->
      <a-col :span="12">
        <a-card title="最近书籍" :hoverable="true">
          <template #extra>
            <a-button type="link" size="small" @click="goToPage('/books')"> 查看全部 </a-button>
          </template>

          <a-list :data-source="recentBooks" :loading="booksLoading" size="small">
            <template #renderItem="{ item }">
              <a-list-item class="book-item" @click="goToBookDetail(item.id)">
                <a-list-item-meta>
                  <template #title>
                    <span>{{ item.title }}</span>
                  </template>
                  <template #description>
                    <div class="book-meta">
                      <span>{{ item.author }}</span>
                      <span class="separator">•</span>
                      <span>{{ item.chapter_count || 0 }} 章节</span>
                      <span class="separator">•</span>
                      <span>{{ formatTime(item.created_at) }}</span>
                    </div>
                  </template>
                </a-list-item-meta>
                <template #actions>
                  <a-button type="link" size="small"> 查看详情 </a-button>
                </template>
              </a-list-item>
            </template>
          </a-list>
        </a-card>
      </a-col>
    </a-row>

    <!-- 性能图表 -->
    <a-row :gutter="[24, 24]" style="margin-top: 24px">
      <a-col :span="24">
        <a-card title="系统性能" :hoverable="true">
          <template #extra>
            <a-button type="link" size="small">详细报告</a-button>
          </template>

          <div class="performance-chart">
            <a-empty v-if="!performanceData.length" description="暂无性能数据" />
            <div v-else class="chart-placeholder">
              <a-typography-text type="secondary"> 性能图表功能开发中... </a-typography-text>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted } from 'vue'
  import { useRouter } from 'vue-router'
  import { useBookStore } from '../stores/book.js'
  import { useSynthesisStore } from '../stores/synthesis.js'
  import { useAnalysisStore } from '../stores/analysis.js'
  import SystemStatus from '../components/SystemStatus.vue'
  import LogSummary from '../components/LogSummary.vue'
  import dayjs from 'dayjs'
  import {
    BookOutlined,
    SoundOutlined,
    BulbOutlined,
    AudioOutlined,
    PlusOutlined,
    RocketOutlined,
    UserOutlined,
    FolderOutlined
  } from '@ant-design/icons-vue'

  const router = useRouter()

  // Stores
  const bookStore = useBookStore()
  const synthesisStore = useSynthesisStore()
  const analysisStore = useAnalysisStore()

  // 响应式数据
  const loading = ref(false)
  const performanceData = ref([])

  // 计算属性
  const stats = computed(() => ({
    bookCount: bookStore.bookCount,
    activeTasks: synthesisStore.hasActiveTasks ? synthesisStore.activeTasks.length : 0,
    activeSessions: analysisStore.hasActiveSessions ? analysisStore.sessionCount : 0,
    audioFiles: synthesisStore.completedTasks.reduce((sum, task) => {
      return sum + (synthesisStore.getTaskAudioFiles(task.id)?.length || 0)
    }, 0)
  }))

  const recentTasks = computed(() => synthesisStore.tasks.slice(0, 5))

  const recentBooks = computed(() => bookStore.books.slice(0, 5))

  const tasksLoading = computed(() => synthesisStore.tasksLoading)
  const booksLoading = computed(() => bookStore.loading)

  // 方法
  const formatTime = (timestamp) => {
    return dayjs(timestamp).format('MM-DD HH:mm')
  }

  const getTaskStatusColor = (status) => {
    const colorMap = {
      pending: 'default',
      running: 'processing',
      completed: 'success',
      failed: 'error',
      stopped: 'warning'
    }
    return colorMap[status] || 'default'
  }

  const getTaskStatusText = (status) => {
    const textMap = {
      pending: '等待中',
      running: '进行中',
      completed: '已完成',
      failed: '失败',
      stopped: '已停止'
    }
    return textMap[status] || status
  }

  const goToPage = (path) => {
    router.push(path)
  }

  const goToBookDetail = (bookId) => {
    router.push(`/books/${bookId}`)
  }

  const loadDashboardData = async () => {
    loading.value = true
    try {
      // 并行加载数据
      await Promise.all([
        bookStore.fetchBooks({ limit: 5 }),
        synthesisStore.fetchTasks({ limit: 5 }),
        analysisStore.fetchSessions({ limit: 5 })
      ])
    } catch (error) {
      console.error('加载仪表板数据失败:', error)
    } finally {
      loading.value = false
    }
  }

  // 生命周期
  onMounted(() => {
    loadDashboardData()
  })
</script>

<style scoped>
  .dashboard {
    margin: 0 auto;
  }

  .overview-cards .stat-card {
    text-align: center;
    transition: all 0.3s;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .overview-cards .stat-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
  }

  .quick-actions {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .action-btn {
    height: 60px;
    border-radius: 8px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    transition: all 0.3s;
  }

  .action-btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  }

  .task-meta {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .book-item {
    cursor: pointer;
    transition: all 0.3s;
    border-radius: 6px;
    padding: 8px;
    margin: 4px 0;
  }

  .book-item:hover {
    background: #f8f9fa;
    transform: translateX(4px);
  }

  .book-meta {
    display: flex;
    align-items: center;
    gap: 4px;
    color: #666;
    font-size: 12px;
  }

  .separator {
    margin: 0 4px;
  }

  .performance-chart {
    height: 200px;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .chart-placeholder {
    text-align: center;
    color: #999;
  }

  /* 响应式设计 */
  @media (max-width: 1200px) {
    .overview-cards .ant-col {
      span: 12;
    }
  }

  @media (max-width: 768px) {
    .overview-cards .ant-col {
      span: 24;
    }

    .quick-actions {
      grid-template-columns: 1fr;
    }

    .dashboard .ant-row .ant-col {
      span: 24;
      margin-bottom: 16px;
    }
  }
</style>
