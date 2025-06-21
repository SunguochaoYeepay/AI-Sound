<template>
  <div class="backup-management">
    <PageHeader 
      title="数据库备份管理"
      subtitle="管理数据库备份与恢复任务"
    />
    
    <!-- 操作工具栏 -->
    <div class="toolbar">
      <a-row :gutter="16" align="middle">
        <a-col :span="12">
          <a-space>
            <a-button 
              type="primary" 
              :icon="h(PlusOutlined)"
              @click="showCreateBackupModal"
              :loading="creating"
            >
              创建备份
            </a-button>
            <a-button 
              :icon="h(ReloadOutlined)"
              @click="refreshBackupList"
              :loading="loading"
            >
              刷新
            </a-button>
            <a-button 
              :icon="h(SettingOutlined)"
              @click="showConfigModal"
            >
              备份配置
            </a-button>
          </a-space>
        </a-col>
        <a-col :span="12" style="text-align: right">
          <a-space>
            <a-select
              v-model:value="filters.status"
              placeholder="状态筛选"
              style="width: 120px"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="pending">等待中</a-select-option>
              <a-select-option value="running">运行中</a-select-option>
              <a-select-option value="success">成功</a-select-option>
              <a-select-option value="failed">失败</a-select-option>
            </a-select>
            <a-select
              v-model:value="filters.type"
              placeholder="类型筛选"
              style="width: 120px"
              allow-clear
              @change="handleFilterChange"
            >
              <a-select-option value="full">全量备份</a-select-option>
              <a-select-option value="incremental">增量备份</a-select-option>
              <a-select-option value="manual">手动备份</a-select-option>
            </a-select>
          </a-space>
        </a-col>
      </a-row>
    </div>

    <!-- 统计卡片 -->
    <div class="stats-cards">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="总备份数"
              :value="stats.total_backups"
              :prefix="h(DatabaseOutlined)"
              :value-style="{ color: '#1890ff' }"
            />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="成功率"
              :value="stats.success_rate"
              suffix="%"
              :prefix="h(CheckCircleOutlined)"
              :value-style="{ color: '#52c41a' }"
            />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="存储使用"
              :value="stats.total_storage_gb"
              suffix="GB"
              :prefix="h(HddOutlined)"
              :value-style="{ color: '#faad14' }"
            />
          </a-card>
        </a-col>
        <a-col :span="6">
          <a-card>
            <a-statistic
              title="平均耗时"
              :value="stats.avg_backup_duration_minutes"
              suffix="分钟"
              :prefix="h(ClockCircleOutlined)"
              :value-style="{ color: '#722ed1' }"
            />
          </a-card>
        </a-col>
      </a-row>
    </div>

    <!-- 备份任务列表 -->
    <a-card title="备份任务列表" class="backup-list-card">
      <a-table
        :columns="columns"
        :data-source="backupList"
        :loading="loading"
        :pagination="pagination"
        row-key="id"
        @change="handleTableChange"
        :scroll="{ x: 1200 }"
      >
        <!-- 任务名称 -->
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'task_name'">
            <div class="task-name">
              <a-typography-text strong>{{ record.task_name }}</a-typography-text>
              <br>
              <a-typography-text type="secondary" style="font-size: 12px">
                ID: {{ record.id }}
              </a-typography-text>
            </div>
          </template>

          <!-- 状态 -->
          <template v-else-if="column.key === 'status'">
            <a-tag :color="getStatusColor(record.status)">
              <template #icon>
                <component :is="getStatusIcon(record.status)" />
              </template>
              {{ getStatusText(record.status) }}
            </a-tag>
          </template>

          <!-- 类型 -->
          <template v-else-if="column.key === 'task_type'">
            <a-tag :color="getTypeColor(record.task_type)">
              {{ getTypeText(record.task_type) }}
            </a-tag>
          </template>

          <!-- 进度 -->
          <template v-else-if="column.key === 'progress'">
            <a-progress 
              :percent="record.progress_percentage" 
              :status="record.status === 'failed' ? 'exception' : 'normal'"
              :show-info="false"
              size="small"
            />
            <div style="font-size: 12px; color: #999; margin-top: 2px">
              {{ record.progress_percentage }}%
            </div>
          </template>

          <!-- 文件大小 -->
          <template v-else-if="column.key === 'file_size'">
            <div v-if="record.file_size">
              <div>{{ formatFileSize(record.file_size) }}</div>
              <div v-if="record.compressed_size" style="font-size: 12px; color: #999">
                压缩后: {{ formatFileSize(record.compressed_size) }}
              </div>
            </div>
            <span v-else>-</span>
          </template>

          <!-- 时间信息 -->
          <template v-else-if="column.key === 'duration'">
            <div v-if="record.duration_seconds">
              {{ formatDuration(record.duration_seconds) }}
            </div>
            <span v-else>-</span>
          </template>

          <!-- 操作 -->
          <template v-else-if="column.key === 'actions'">
            <a-space>
              <a-button 
                size="small" 
                @click="viewBackupDetails(record)"
                :icon="h(EyeOutlined)"
              >
                详情
              </a-button>
              <a-button 
                size="small" 
                type="primary"
                @click="showRestoreModal(record)"
                :disabled="record.status !== 'success'"
                :icon="h(RedoOutlined)"
              >
                恢复
              </a-button>
              <a-popconfirm
                title="确定要删除这个备份吗？"
                ok-text="确定"
                cancel-text="取消"
                @confirm="deleteBackup(record.id)"
              >
                <a-button 
                  size="small" 
                  danger
                  :disabled="record.status === 'running'"
                  :icon="h(DeleteOutlined)"
                >
                  删除
                </a-button>
              </a-popconfirm>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 创建备份弹窗 -->
    <CreateBackupModal
      :open="createBackupVisible"
      @ok="handleCreateBackup"
      @cancel="createBackupVisible = false"
      :loading="creating"
    />

    <!-- 恢复备份弹窗 -->
    <RestoreBackupModal
      :open="restoreBackupVisible"
      :backup-task="selectedBackup"
      @ok="handleRestoreBackup"
      @cancel="restoreBackupVisible = false"
      :loading="restoring"
    />

    <!-- 备份详情抽屉 -->
    <a-drawer
      v-model:open="detailsVisible"
      title="备份任务详情"
      width="720"
      :closable="true"
      placement="right"
      @close="handleDrawerClose"
    >
      <BackupDetailsDrawer
        v-if="detailsVisible && selectedBackup"
        :backup-id="selectedBackup.id"
        @task-cancelled="handleTaskCancelled"
        @task-completed="handleTaskCompleted"
        @task-failed="handleTaskFailed"
        @drawer-closed="handleDrawerClosed"
      />
    </a-drawer>

    <!-- 配置弹窗 -->
    <BackupConfigModal
      :open="configVisible"
      @cancel="configVisible = false"
      @ok="handleConfigUpdate"
    />

    <!-- 恢复监控抽屉 -->
    <a-drawer
      v-model:open="restoreMonitorVisible"
      title="恢复任务监控"
      width="600"
      :closable="true"
      placement="right"
    >
      <RestoreMonitorPanel
        v-if="restoreMonitorVisible && currentRestoreId"
        :restore-id="currentRestoreId"
        @task-completed="handleRestoreCompleted"
        @task-failed="handleRestoreFailed"
      />
    </a-drawer>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { message } from 'ant-design-vue'
import {
  PlusOutlined,
  ReloadOutlined,
  SettingOutlined,
  DatabaseOutlined,
  CheckCircleOutlined,
  HddOutlined,
  ClockCircleOutlined,
  EyeOutlined,
  RedoOutlined,
  DeleteOutlined,
  LoadingOutlined,
  CheckOutlined,
  CloseOutlined,
  ExclamationOutlined
} from '@ant-design/icons-vue'

import PageHeader from '@/components/PageHeader.vue'
import CreateBackupModal from '@/components/backup/CreateBackupModal.vue'
import RestoreBackupModal from '@/components/backup/RestoreBackupModal.vue'
import BackupDetailsDrawer from '@/components/backup/BackupDetailsDrawer.vue'
import BackupConfigModal from '@/components/backup/BackupConfigModal.vue'
import RestoreMonitorPanel from '@/components/backup/RestoreMonitorPanel.vue'

import { getBackupList, getBackupStats, createBackup, deleteBackup as deleteBackupAPI, createRestore } from '@/api/backup'

// 响应式数据
const loading = ref(false)
const creating = ref(false)
const restoring = ref(false)
const backupList = ref([])
const selectedBackup = ref(null)

// 弹窗显示状态
const createBackupVisible = ref(false)
const restoreBackupVisible = ref(false)
const detailsVisible = ref(false)
const configVisible = ref(false)
const restoreMonitorVisible = ref(false)
const currentRestoreId = ref(null)

// 筛选条件
const filters = reactive({
  status: undefined,
  type: undefined
})

// 统计数据
const stats = reactive({
  total_backups: 0,
  success_rate: 0,
  total_storage_gb: 0,
  avg_backup_duration_minutes: 0
})

// 分页配置
const pagination = reactive({
  current: 1,
  pageSize: 20,
  total: 0,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total: number) => `共 ${total} 条`
})

// 表格列配置
const columns = [
  {
    title: '任务名称',
    key: 'task_name',
    width: 200,
    fixed: 'left'
  },
  {
    title: '状态',
    key: 'status',
    width: 100
  },
  {
    title: '类型',
    key: 'task_type',
    width: 100
  },
  {
    title: '进度',
    key: 'progress',
    width: 120
  },
  {
    title: '文件大小',
    key: 'file_size',
    width: 150
  },
  {
    title: '耗时',
    key: 'duration',
    width: 100
  },
  {
    title: '创建时间',
    dataIndex: 'created_at',
    width: 160,
    customRender: ({ text }: any) => formatDateTime(text)
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right'
  }
]

// 获取备份列表
const fetchBackupList = async () => {
  try {
    loading.value = true
    const params = {
      page: pagination.current,
      page_size: pagination.pageSize,
      status: filters.status,
      backup_type: filters.type
    }
    
    const response = await getBackupList(params)
    backupList.value = response.data.tasks
    pagination.total = response.data.pagination.total
  } catch (error) {
    console.error('获取备份列表失败:', error)
    message.error('获取备份列表失败')
  } finally {
    loading.value = false
  }
}

// 获取统计数据
const fetchStats = async () => {
  try {
    const response = await getBackupStats()
    Object.assign(stats, response.data)
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

// 状态相关方法
const getStatusColor = (status: string) => {
  const colors: Record<string, string> = {
    pending: 'blue',
    running: 'orange',
    success: 'green',
    failed: 'red',
    cancelled: 'gray'
  }
  return colors[status] || 'default'
}

const getStatusIcon = (status: string) => {
  const icons: Record<string, any> = {
    pending: ClockCircleOutlined,
    running: LoadingOutlined,
    success: CheckOutlined,
    failed: CloseOutlined,
    cancelled: ExclamationOutlined
  }
  return icons[status] || ClockCircleOutlined
}

const getStatusText = (status: string) => {
  const texts: Record<string, string> = {
    pending: '等待中',
    running: '运行中',
    success: '成功',
    failed: '失败',
    cancelled: '已取消'
  }
  return texts[status] || status
}

const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    full: 'purple',
    incremental: 'cyan',
    manual: 'lime'
  }
  return colors[type] || 'default'
}

const getTypeText = (type: string) => {
  const texts: Record<string, string> = {
    full: '全量备份',
    incremental: '增量备份',
    manual: '手动备份'
  }
  return texts[type] || type
}

// 格式化方法
const formatFileSize = (bytes: number) => {
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDuration = (seconds: number) => {
  const hours = Math.floor(seconds / 3600)
  const minutes = Math.floor((seconds % 3600) / 60)
  const secs = seconds % 60
  
  if (hours > 0) {
    return `${hours}h ${minutes}m ${secs}s`
  } else if (minutes > 0) {
    return `${minutes}m ${secs}s`
  } else {
    return `${secs}s`
  }
}

const formatDateTime = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 事件处理方法
const handleTableChange = (pag: any) => {
  pagination.current = pag.current
  pagination.pageSize = pag.pageSize
  fetchBackupList()
}

const handleFilterChange = () => {
  pagination.current = 1
  fetchBackupList()
}

const refreshBackupList = () => {
  fetchBackupList()
  fetchStats()
}

const showCreateBackupModal = () => {
  createBackupVisible.value = true
}

const showRestoreModal = (backup: any) => {
  selectedBackup.value = backup
  restoreBackupVisible.value = true
}

const showConfigModal = () => {
  configVisible.value = true
}

const viewBackupDetails = (backup: any) => {
  selectedBackup.value = backup
  detailsVisible.value = true
}

const showRestoreMonitor = (restoreId: number) => {
  currentRestoreId.value = restoreId
  restoreMonitorVisible.value = true
}

// 创建备份
const handleCreateBackup = async (backupData: any) => {
  try {
    creating.value = true
    await createBackup(backupData)
    message.success('备份任务创建成功')
    createBackupVisible.value = false
    refreshBackupList()
  } catch (error) {
    console.error('创建备份失败:', error)
    message.error('创建备份失败')
  } finally {
    creating.value = false
  }
}

// 恢复备份
const handleRestoreBackup = async (restoreData: any) => {
  try {
    restoring.value = true
    const response = await createRestore(restoreData)
    if (response.success) {
      message.success(`恢复任务创建成功！任务ID: ${response.data.restore_id}`)
      restoreBackupVisible.value = false
      
      // 打开恢复监控抽屉
      showRestoreMonitor(response.data.restore_id)
    } else {
      throw new Error(response.message || '创建失败')
    }
  } catch (error) {
    console.error('创建恢复任务失败:', error)
    message.error('创建恢复任务失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    restoring.value = false
  }
}

// 删除备份
const deleteBackup = async (backupId: number) => {
  try {
    await deleteBackupAPI(backupId)
    message.success('备份删除成功')
    refreshBackupList()
  } catch (error) {
    console.error('删除备份失败:', error)
    message.error('删除备份失败')
  }
}

// 更新配置
const handleConfigUpdate = () => {
  message.success('配置更新成功')
  configVisible.value = false
}

// 处理任务取消事件
const handleTaskCancelled = (taskId: number) => {
  console.log('任务已取消:', taskId)
  refreshBackupList()
}

// 处理任务完成事件
const handleTaskCompleted = (taskId: number) => {
  console.log('任务已完成:', taskId)
  refreshBackupList()
}

// 处理任务失败事件
const handleTaskFailed = (taskId: number) => {
  console.log('任务执行失败:', taskId)
  refreshBackupList()
}

// 处理抽屉关闭事件
const handleDrawerClosed = () => {
  refreshBackupList()
}

// 处理抽屉关闭
const handleDrawerClose = () => {
  detailsVisible.value = false
  refreshBackupList()
}

// 处理恢复任务完成事件
const handleRestoreCompleted = (restoreId: number) => {
  console.log('恢复任务已完成:', restoreId)
  message.success('恢复任务已完成！')
  refreshBackupList()
}

// 处理恢复任务失败事件
const handleRestoreFailed = (restoreId: number) => {
  console.log('恢复任务执行失败:', restoreId)
  message.error('恢复任务执行失败')
  refreshBackupList()
}

// 组件挂载时获取数据
onMounted(() => {
  fetchBackupList()
  fetchStats()
})
</script>

<style scoped>
.backup-management {
}

.toolbar {
  margin-bottom: 16px;
}

.stats-cards {
  margin-bottom: 16px;
}

.backup-list-card {
  margin-bottom: 16px;
}

.task-name {
  line-height: 1.4;
}

:deep(.ant-statistic-title) {
  font-size: 14px;
}

:deep(.ant-statistic-content) {
  font-size: 20px;
}
</style>