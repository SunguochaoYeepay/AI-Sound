<template>
  <div class="backup-details-drawer">
    <a-spin :spinning="loading" tip="加载详情中...">
      <div v-if="!loading && backupDetails">
        <!-- 基本信息 -->
        <a-card title="基本信息" size="small" style="margin-bottom: 16px">
          <a-descriptions bordered :column="2" size="small">
            <a-descriptions-item label="任务名称">
              {{ backupDetails.task_info.task_name }}
            </a-descriptions-item>
            <a-descriptions-item label="任务ID">
              {{ backupDetails.task_info.id }}
            </a-descriptions-item>
            <a-descriptions-item label="备份类型">
              <a-tag :color="getTypeColor(backupDetails.task_info.task_type)">
                {{ getTypeText(backupDetails.task_info.task_type) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="getStatusColor(backupDetails.task_info.status)">
                <template #icon>
                  <component :is="getStatusIcon(backupDetails.task_info.status)" />
                </template>
                {{ getStatusText(backupDetails.task_info.status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="开始时间">
              {{ formatDateTime(backupDetails.task_info.start_time) }}
            </a-descriptions-item>
            <a-descriptions-item label="结束时间">
              {{ formatDateTime(backupDetails.task_info.end_time) }}
            </a-descriptions-item>
            <a-descriptions-item label="耗时">
              {{ formatDuration(backupDetails.task_info.duration_seconds) }}
            </a-descriptions-item>
            <a-descriptions-item label="创建时间">
              {{ formatDateTime(backupDetails.task_info.created_at) }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 进度信息 -->
        <a-card title="进度信息" size="small" style="margin-bottom: 16px">
          <div class="progress-section">
            <a-progress
              :percent="backupDetails.task_info.progress_percentage"
              :status="backupDetails.task_info.status === 'failed' ? 'exception' : 'normal'"
              stroke-color="linear-gradient(to right, #108ee9, #87d068)"
            />

            <a-row :gutter="16" style="margin-top: 16px">
              <a-col :span="8">
                <a-statistic
                  title="当前步骤"
                  :value="backupDetails.progress_info.current_step"
                  :value-style="{ color: '#1890ff' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="已处理记录"
                  :value="backupDetails.progress_info.processed_records"
                  :value-style="{ color: '#52c41a' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="预估总数"
                  :value="backupDetails.progress_info.estimated_total"
                  :value-style="{ color: '#722ed1' }"
                />
              </a-col>
            </a-row>
          </div>
        </a-card>

        <!-- 文件信息 -->
        <a-card title="文件信息" size="small" style="margin-bottom: 16px">
          <a-descriptions bordered :column="1" size="small">
            <a-descriptions-item label="文件状态">
              <a-tag :color="backupDetails.file_info.exists ? 'green' : 'red'">
                {{ backupDetails.file_info.exists ? '文件存在' : '文件不存在' }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item v-if="backupDetails.file_info.exists" label="文件大小">
              {{ formatFileSize(backupDetails.file_info.size) }}
            </a-descriptions-item>
            <a-descriptions-item v-if="backupDetails.file_info.exists" label="创建时间">
              {{ formatDateTime(backupDetails.file_info.created_time) }}
            </a-descriptions-item>
            <a-descriptions-item v-if="backupDetails.file_info.exists" label="修改时间">
              {{ formatDateTime(backupDetails.file_info.modified_time) }}
            </a-descriptions-item>
          </a-descriptions>

          <div v-if="backupDetails.file_info.exists" style="margin-top: 16px">
            <a-button
              type="primary"
              :icon="h(DownloadOutlined)"
              @click="handleDownload"
              :loading="downloading"
            >
              下载备份文件
            </a-button>
          </div>
        </a-card>

        <!-- 错误信息 -->
        <a-card
          v-if="backupDetails.task_info.error_message"
          title="错误信息"
          size="small"
          style="margin-bottom: 16px"
        >
          <a-alert :message="backupDetails.task_info.error_message" type="error" show-icon />
        </a-card>

        <!-- 操作日志 -->
        <a-card title="操作日志" size="small">
          <div v-if="backupDetails.logs && backupDetails.logs.length > 0">
            <a-timeline>
              <a-timeline-item
                v-for="log in backupDetails.logs"
                :key="log.id"
                :color="getLogColor(log.level)"
              >
                <template #dot>
                  <component :is="getLogIcon(log.level)" />
                </template>
                <div class="log-item">
                  <div class="log-header">
                    <a-tag size="small" :color="getLogLevelColor(log.level)">
                      {{ log.level }}
                    </a-tag>
                    <a-tag size="small" color="blue">
                      {{ log.module }}
                    </a-tag>
                    <span class="log-time">{{ formatDateTime(log.created_at) }}</span>
                  </div>
                  <div class="log-message">{{ log.message }}</div>
                  <div v-if="log.details" class="log-details">
                    <a-typography-text type="secondary" style="font-size: 12px">
                      {{ log.details }}
                    </a-typography-text>
                  </div>
                </div>
              </a-timeline-item>
            </a-timeline>
          </div>
          <a-empty v-else description="暂无日志记录" />
        </a-card>

        <!-- 操作按钮 -->
        <div class="actions" style="margin-top: 24px; text-align: center">
          <a-space>
            <a-button @click="refreshDetails" :icon="h(ReloadOutlined)"> 刷新 </a-button>
            <a-button
              v-if="
                backupDetails.task_info.status === 'running' ||
                backupDetails.task_info.status === 'pending'
              "
              danger
              @click="handleCancel"
              :loading="cancelling"
            >
              取消任务
            </a-button>
          </a-space>
        </div>
      </div>

      <a-result v-else-if="!loading && error" status="error" title="加载失败" :sub-title="error">
        <template #extra>
          <a-button type="primary" @click="loadDetails">重试</a-button>
        </template>
      </a-result>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, onBeforeUnmount, h } from 'vue'
  import { message } from 'ant-design-vue'
  import {
    DownloadOutlined,
    ReloadOutlined,
    LoadingOutlined,
    CheckOutlined,
    CloseOutlined,
    ExclamationOutlined,
    ClockCircleOutlined,
    InfoCircleOutlined,
    WarningOutlined
  } from '@ant-design/icons-vue'

  import { getBackupDetails, downloadBackupFile, cancelRunningTask } from '@/api/backup'

  // Props
  interface Props {
    backupId: number
  }

  const props = defineProps<Props>()

  // Emits
  const emit = defineEmits<{
    taskCancelled: [taskId: number]
    taskCompleted: [taskId: number]
    taskFailed: [taskId: number]
    drawerClosed: []
  }>()

  // 响应式数据
  const loading = ref(false)
  const downloading = ref(false)
  const cancelling = ref(false)
  const error = ref('')
  const backupDetails = ref<any>(null)
  const previousStatus = ref<string>('')
  let pollingTimer: NodeJS.Timeout | null = null

  // 加载详情数据
  const loadDetails = async (showLoading = true) => {
    try {
      if (showLoading) loading.value = true
      error.value = ''
      const response = await getBackupDetails(props.backupId)

      // 检查状态变化并显示提示
      if (backupDetails.value && previousStatus.value) {
        const oldStatus = previousStatus.value
        const newStatus = response.data.task_info.status

        if (oldStatus !== newStatus) {
          if (newStatus === 'success') {
            message.success(`备份任务 "${response.data.task_info.task_name}" 已完成！`)
            // 停止轮询
            stopPolling()
            // 通知父组件刷新列表
            emit('taskCompleted', props.backupId)
          } else if (newStatus === 'failed') {
            message.error(`备份任务 "${response.data.task_info.task_name}" 执行失败`)
            stopPolling()
            emit('taskFailed', props.backupId)
          } else if (newStatus === 'cancelled') {
            stopPolling()
          }
        }
      }

      backupDetails.value = response.data
      previousStatus.value = response.data.task_info.status

      // 如果任务正在运行，启动轮询
      if (
        response.data.task_info.status === 'running' ||
        response.data.task_info.status === 'pending'
      ) {
        startPolling()
      } else {
        stopPolling()
      }
    } catch (err: any) {
      console.error('加载备份详情失败:', err)
      error.value = err.response?.data?.detail || '加载失败'
      if (showLoading) message.error('加载备份详情失败')
    } finally {
      if (showLoading) loading.value = false
    }
  }

  // 启动轮询
  const startPolling = () => {
    if (pollingTimer) return // 避免重复启动

    pollingTimer = setInterval(() => {
      loadDetails(false) // 轮询时不显示loading
    }, 3000) // 每3秒轮询一次
  }

  // 停止轮询
  const stopPolling = () => {
    if (pollingTimer) {
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  // 刷新详情
  const refreshDetails = () => {
    loadDetails(true)
  }

  // 下载文件
  const handleDownload = async () => {
    try {
      downloading.value = true
      await downloadBackupFile(props.backupId)
      message.success('下载开始')
    } catch (err) {
      console.error('下载失败:', err)
      message.error('下载失败')
    } finally {
      downloading.value = false
    }
  }

  // 取消任务
  const handleCancel = async () => {
    try {
      cancelling.value = true
      const response = await cancelRunningTask(props.backupId)
      if (response.success) {
        message.success('任务已取消')
        // 刷新详情数据以显示最新状态
        await loadDetails()
        emit('taskCancelled', props.backupId)
      } else {
        throw new Error(response.message || '取消失败')
      }
    } catch (err: any) {
      console.error('取消任务失败:', err)
      const errorMsg = err.response?.data?.detail || err.message || '取消任务失败'
      message.error(errorMsg)
    } finally {
      cancelling.value = false
    }
  }

  // 格式化方法
  const formatDateTime = (dateString: string) => {
    if (!dateString) return '-'
    return new Date(dateString).toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const formatFileSize = (bytes: number) => {
    if (!bytes || bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

  const formatDuration = (seconds: number) => {
    if (!seconds) return '-'
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

  // 状态颜色方法
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

  // 日志相关方法
  const getLogColor = (level: string) => {
    const colors: Record<string, string> = {
      DEBUG: 'gray',
      INFO: 'blue',
      WARNING: 'orange',
      ERROR: 'red',
      CRITICAL: 'red'
    }
    return colors[level] || 'blue'
  }

  const getLogIcon = (level: string) => {
    const icons: Record<string, any> = {
      DEBUG: InfoCircleOutlined,
      INFO: InfoCircleOutlined,
      WARNING: WarningOutlined,
      ERROR: CloseOutlined,
      CRITICAL: CloseOutlined
    }
    return icons[level] || InfoCircleOutlined
  }

  const getLogLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      DEBUG: 'default',
      INFO: 'blue',
      WARNING: 'orange',
      ERROR: 'red',
      CRITICAL: 'red'
    }
    return colors[level] || 'blue'
  }

  // 处理抽屉关闭
  const handleDrawerClose = () => {
    stopPolling()
    emit('drawerClosed')
  }

  // 组件挂载和销毁
  onMounted(() => {
    loadDetails()
  })

  onBeforeUnmount(() => {
    stopPolling()
  })
</script>

<style scoped>
  .backup-details-drawer {
    padding: 0;
  }

  .progress-section {
    padding: 16px 0;
  }

  .log-item {
    padding: 8px 0;
  }

  .log-header {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }

  .log-time {
    font-size: 12px;
    color: #999;
    margin-left: auto;
  }

  .log-message {
    margin-bottom: 4px;
    line-height: 1.4;
  }

  .log-details {
    padding: 4px 8px;
    background: #f5f5f5;
    border-radius: 4px;
    font-size: 12px;
  }

  .actions {
    border-top: 1px solid #f0f0f0;
    padding-top: 16px;
  }

  :deep(.ant-descriptions-item-label) {
    font-weight: 500;
  }

  :deep(.ant-timeline-item-content) {
    margin-left: 0;
    padding-left: 24px;
  }

  :deep(.ant-card-head-title) {
    font-size: 16px;
    font-weight: 600;
  }
</style>
