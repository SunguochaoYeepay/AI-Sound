<template>
  <a-modal :open="open" title="备份任务详情" :footer="null" @cancel="handleCancel" width="800px">
    <div v-if="backupTask" class="backup-details">
      <!-- 基本信息 -->
      <a-descriptions title="基本信息" bordered size="small" :column="2">
        <a-descriptions-item label="任务ID">
          {{ backupTask.id }}
        </a-descriptions-item>
        <a-descriptions-item label="任务名称">
          {{ backupTask.task_name }}
        </a-descriptions-item>
        <a-descriptions-item label="备份类型">
          <a-tag :color="getTypeColor(backupTask.task_type)">
            {{ getTypeText(backupTask.task_type) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="任务状态">
          <a-tag :color="getStatusColor(backupTask.status)">
            <template #icon>
              <component :is="getStatusIcon(backupTask.status)" />
            </template>
            {{ getStatusText(backupTask.status) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="创建时间">
          {{ formatDateTime(backupTask.created_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="开始时间">
          {{ formatDateTime(backupTask.started_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="完成时间">
          {{ formatDateTime(backupTask.completed_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="执行耗时">
          <span v-if="backupTask.duration_seconds">
            {{ formatDuration(backupTask.duration_seconds) }}
          </span>
          <span v-else>-</span>
        </a-descriptions-item>
      </a-descriptions>

      <!-- 进度信息 -->
      <a-card title="执行进度" size="small" style="margin-top: 16px">
        <div class="progress-info">
          <div class="progress-bar">
            <a-progress
              :percent="backupTask.progress_percentage"
              :status="backupTask.status === 'failed' ? 'exception' : 'normal'"
              :stroke-color="getProgressColor(backupTask.status)"
            />
          </div>
          <div class="progress-details">
            <a-row :gutter="16">
              <a-col :span="8">
                <a-statistic
                  title="完成进度"
                  :value="backupTask.progress_percentage"
                  suffix="%"
                  :value-style="{ fontSize: '18px' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="当前步骤"
                  :value="backupTask.current_step || '等待中'"
                  :value-style="{ fontSize: '16px' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="处理记录数"
                  :value="backupTask.processed_records || 0"
                  :value-style="{ fontSize: '16px' }"
                />
              </a-col>
            </a-row>
          </div>
        </div>
      </a-card>

      <!-- 文件信息 -->
      <a-card title="备份文件信息" size="small" style="margin-top: 16px">
        <a-descriptions bordered size="small" :column="2">
          <a-descriptions-item label="文件路径">
            <a-typography-text code copyable style="font-size: 12px">
              {{ backupTask.file_path || '暂无' }}
            </a-typography-text>
          </a-descriptions-item>
          <a-descriptions-item label="存储位置">
            <a-tag>{{ getStorageLocationText(backupTask.storage_location) }}</a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="文件大小">
            {{ formatFileSize(backupTask.file_size) }}
          </a-descriptions-item>
          <a-descriptions-item label="压缩后大小">
            {{ formatFileSize(backupTask.compressed_size) }}
          </a-descriptions-item>
          <a-descriptions-item label="压缩率">
            <span v-if="backupTask.file_size && backupTask.compressed_size">
              {{ getCompressionRatio(backupTask.file_size, backupTask.compressed_size) }}%
            </span>
            <span v-else>-</span>
          </a-descriptions-item>
          <a-descriptions-item label="MD5校验">
            <a-typography-text code copyable style="font-size: 12px" v-if="backupTask.md5_hash">
              {{ backupTask.md5_hash }}
            </a-typography-text>
            <span v-else>-</span>
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- 配置信息 -->
      <a-card title="备份配置" size="small" style="margin-top: 16px">
        <a-descriptions bordered size="small" :column="2">
          <a-descriptions-item label="包含音频文件">
            <a-tag :color="backupTask.include_audio ? 'green' : 'gray'">
              {{ backupTask.include_audio ? '是' : '否' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="启用加密">
            <a-tag :color="backupTask.encryption_enabled ? 'blue' : 'gray'">
              {{ backupTask.encryption_enabled ? '是' : '否' }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="保留天数">
            {{ backupTask.retention_days || '-' }} 天
          </a-descriptions-item>
          <a-descriptions-item label="自动清理">
            <a-tag :color="backupTask.auto_cleanup ? 'orange' : 'gray'">
              {{ backupTask.auto_cleanup ? '启用' : '禁用' }}
            </a-tag>
          </a-descriptions-item>
        </a-descriptions>
      </a-card>

      <!-- 错误信息 -->
      <a-card
        v-if="backupTask.status === 'failed' && backupTask.error_message"
        title="错误信息"
        size="small"
        style="margin-top: 16px"
      >
        <a-alert type="error" show-icon>
          <template #message>
            <div style="word-break: break-all">
              {{ backupTask.error_message }}
            </div>
          </template>
        </a-alert>
      </a-card>

      <!-- 日志信息 -->
      <a-card title="执行日志" size="small" style="margin-top: 16px">
        <div class="log-container">
          <a-textarea
            :value="formatLogs(backupTask.logs)"
            :rows="8"
            readonly
            style="font-family: 'Courier New', monospace; font-size: 12px"
            placeholder="暂无日志信息"
          />
        </div>
      </a-card>

      <!-- 操作按钮 -->
      <div class="action-buttons" style="margin-top: 16px; text-align: right">
        <a-space>
          <a-button
            v-if="backupTask.status === 'success' && backupTask.file_path"
            type="primary"
            @click="downloadBackup"
            :loading="downloading"
            :icon="h(DownloadOutlined)"
          >
            下载备份文件
          </a-button>
          <a-button
            v-if="backupTask.status === 'success'"
            type="primary"
            @click="showRestoreModal"
            :icon="h(RedoOutlined)"
          >
            恢复数据
          </a-button>
          <a-button
            v-if="backupTask.status === 'running'"
            danger
            @click="cancelTask"
            :loading="cancelling"
            :icon="h(StopOutlined)"
          >
            取消任务
          </a-button>
        </a-space>
      </div>
    </div>
  </a-modal>
</template>

<script setup lang="ts">
  import { ref, h } from 'vue'
  import { message } from 'ant-design-vue'
  import {
    DownloadOutlined,
    RedoOutlined,
    StopOutlined,
    LoadingOutlined,
    CheckOutlined,
    CloseOutlined,
    ExclamationOutlined,
    ClockCircleOutlined
  } from '@ant-design/icons-vue'
  import { cancelRunningTask, downloadBackupFile } from '@/api/backup'

  // Props
  interface Props {
    open: boolean
    backupTask: any
  }

  const props = withDefaults(defineProps<Props>(), {})

  // Emits
  const emit = defineEmits<{
    cancel: []
    restore: [backupTask: any]
    'task-cancelled': [taskId: number]
  }>()

  // 响应式数据
  const downloading = ref(false)
  const cancelling = ref(false)

  // 工具方法
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

  const getStorageLocationText = (location: string) => {
    const texts: Record<string, string> = {
      local: '本地存储',
      s3: 'Amazon S3',
      oss: '阿里云OSS'
    }
    return texts[location] || location
  }

  const getProgressColor = (status: string) => {
    if (status === 'failed') return '#ff4d4f'
    if (status === 'success') return '#52c41a'
    if (status === 'running') return '#1890ff'
    return '#d9d9d9'
  }

  const formatFileSize = (bytes: number) => {
    if (!bytes) return '-'
    if (bytes === 0) return '0 B'
    const k = 1024
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
    const i = Math.floor(Math.log(bytes) / Math.log(k))
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
  }

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

  const formatDuration = (seconds: number) => {
    if (!seconds) return '-'
    const hours = Math.floor(seconds / 3600)
    const minutes = Math.floor((seconds % 3600) / 60)
    const secs = seconds % 60

    if (hours > 0) {
      return `${hours}小时 ${minutes}分钟 ${secs}秒`
    } else if (minutes > 0) {
      return `${minutes}分钟 ${secs}秒`
    } else {
      return `${secs}秒`
    }
  }

  const getCompressionRatio = (originalSize: number, compressedSize: number) => {
    if (!originalSize || !compressedSize) return 0
    return ((1 - compressedSize / originalSize) * 100).toFixed(1)
  }

  const formatLogs = (logs: any) => {
    if (!logs) return ''
    if (typeof logs === 'string') return logs
    if (Array.isArray(logs)) {
      return logs
        .map((log) => {
          if (typeof log === 'string') return log
          return `[${log.timestamp || ''}] ${log.level || 'INFO'}: ${log.message || ''}`
        })
        .join('\n')
    }
    return JSON.stringify(logs, null, 2)
  }

  // 事件处理方法
  const handleCancel = () => {
    emit('cancel')
  }

  const downloadBackup = async () => {
    try {
      downloading.value = true
      const response = await downloadBackupFile(props.backupTask.id)
      if (response.success) {
        message.success(`备份文件下载完成: ${response.filename}`)
      }
    } catch (error) {
      console.error('下载备份文件失败:', error)
      message.error('下载备份文件失败')
    } finally {
      downloading.value = false
    }
  }

  const showRestoreModal = () => {
    emit('restore', props.backupTask)
  }

  const cancelTask = async () => {
    try {
      cancelling.value = true
      const response = await cancelRunningTask(props.backupTask.id)
      if (response.success) {
        message.success('任务已成功取消')
        // 发出事件通知父组件刷新列表
        emit('task-cancelled', props.backupTask.id)
      }
    } catch (error) {
      console.error('取消任务失败:', error)
      message.error('取消任务失败')
    } finally {
      cancelling.value = false
    }
  }
</script>

<style scoped>
  .backup-details {
    max-height: 70vh;
    overflow-y: auto;
  }

  .progress-info {
    margin-bottom: 16px;
  }

  .progress-bar {
    margin-bottom: 16px;
  }

  .progress-details {
    background-color: #fafafa;
    padding: 16px;
    border-radius: 6px;
  }

  .log-container {
    background-color: #000;
    color: #00ff00;
    padding: 12px;
    border-radius: 6px;
    margin-top: 8px;
  }

  .action-buttons {
    border-top: 1px solid #f0f0f0;
    padding-top: 16px;
  }

  :deep(.ant-descriptions-item-label) {
    background-color: #fafafa;
    font-weight: 500;
    width: 30%;
  }

  :deep(.ant-descriptions-item-content) {
    word-break: break-all;
  }

  :deep(.ant-card-head-title) {
    font-size: 16px;
    font-weight: 600;
  }

  :deep(.ant-statistic-title) {
    font-size: 12px;
    color: #666;
  }

  :deep(.ant-statistic-content) {
    color: #1890ff;
  }
</style>
