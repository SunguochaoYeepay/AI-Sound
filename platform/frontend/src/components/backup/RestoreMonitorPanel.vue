<template>
  <div class="restore-monitor">
    <a-spin :spinning="loading" tip="加载恢复状态中...">
      <div v-if="!loading && restoreTask">
        <!-- 基本信息 -->
        <a-card title="恢复任务信息" size="small" style="margin-bottom: 16px">
          <a-descriptions bordered :column="2" size="small">
            <a-descriptions-item label="任务名称">
              {{ restoreTask.task_name }}
            </a-descriptions-item>
            <a-descriptions-item label="任务ID">
              {{ restoreTask.id }}
            </a-descriptions-item>
            <a-descriptions-item label="恢复类型">
              <a-tag color="purple">{{ getRestoreTypeText(restoreTask.restore_type) }}</a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="状态">
              <a-tag :color="getStatusColor(restoreTask.status)">
                <template #icon>
                  <component :is="getStatusIcon(restoreTask.status)" />
                </template>
                {{ getStatusText(restoreTask.status) }}
              </a-tag>
            </a-descriptions-item>
            <a-descriptions-item label="目标数据库">
              {{ restoreTask.target_database || '-' }}
            </a-descriptions-item>
            <a-descriptions-item label="创建时间">
              {{ formatDateTime(restoreTask.created_at) }}
            </a-descriptions-item>
            <a-descriptions-item v-if="restoreTask.start_time" label="开始时间">
              {{ formatDateTime(restoreTask.start_time) }}
            </a-descriptions-item>
            <a-descriptions-item v-if="restoreTask.end_time" label="结束时间">
              {{ formatDateTime(restoreTask.end_time) }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>

        <!-- 进度信息 -->
        <a-card title="恢复进度" size="small" style="margin-bottom: 16px">
          <div class="progress-section">
            <a-progress
              :percent="restoreTask.progress_percentage || 0"
              :status="restoreTask.status === 'failed' ? 'exception' : 'normal'"
              stroke-color="linear-gradient(to right, #52c41a, #108ee9)"
            />

            <a-row :gutter="16" style="margin-top: 16px">
              <a-col :span="8">
                <a-statistic
                  title="当前步骤"
                  :value="getCurrentStep(restoreTask.status)"
                  :value-style="{ color: '#1890ff' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="耗时"
                  :value="formatDuration(restoreTask.duration_seconds)"
                  :value-style="{ color: '#52c41a' }"
                />
              </a-col>
              <a-col :span="8">
                <a-statistic
                  title="包含音频"
                  :value="restoreTask.include_audio ? '是' : '否'"
                  :value-style="{ color: '#722ed1' }"
                />
              </a-col>
            </a-row>
          </div>
        </a-card>

        <!-- 错误信息 -->
        <a-card
          v-if="restoreTask.error_message"
          title="错误信息"
          size="small"
          style="margin-bottom: 16px"
        >
          <a-alert :message="restoreTask.error_message" type="error" show-icon />
        </a-card>

        <!-- 恢复日志 -->
        <a-card title="恢复日志" size="small">
          <div v-if="restoreLogs && restoreLogs.length > 0">
            <a-timeline>
              <a-timeline-item
                v-for="log in restoreLogs"
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
                    <span class="log-time">{{ formatDateTime(log.created_at) }}</span>
                  </div>
                  <div class="log-message">{{ log.message }}</div>
                </div>
              </a-timeline-item>
            </a-timeline>
          </div>
          <a-empty v-else description="暂无恢复日志" />
        </a-card>

        <!-- 操作按钮 -->
        <div class="actions" style="margin-top: 24px; text-align: center">
          <a-space>
            <a-button @click="refreshStatus" :icon="h(ReloadOutlined)"> 刷新状态 </a-button>
            <a-button
              v-if="restoreTask.status === 'running' || restoreTask.status === 'pending'"
              danger
              @click="cancelTask"
              :loading="cancelling"
            >
              取消恢复
            </a-button>
          </a-space>
        </div>
      </div>

      <a-result v-else-if="!loading && error" status="error" title="加载失败" :sub-title="error">
        <template #extra>
          <a-button type="primary" @click="loadRestoreStatus">重试</a-button>
        </template>
      </a-result>
    </a-spin>
  </div>
</template>

<script setup lang="ts">
  import { ref, onMounted, onBeforeUnmount, h } from 'vue'
  import { message } from 'ant-design-vue'
  import {
    ReloadOutlined,
    LoadingOutlined,
    CheckOutlined,
    CloseOutlined,
    ExclamationOutlined,
    ClockCircleOutlined,
    InfoCircleOutlined,
    WarningOutlined
  } from '@ant-design/icons-vue'
  import { getRestoreDetails, cancelRestoreTask } from '@/api/backup'

  // Props
  interface Props {
    restoreId: number
  }

  const props = defineProps<Props>()

  // Emits
  const emit = defineEmits<{
    taskCompleted: [taskId: number]
    taskFailed: [taskId: number]
    taskDeleted: [taskId: number]
  }>()

  // 响应式数据
  const loading = ref(false)
  const cancelling = ref(false)
  const error = ref('')
  const restoreTask = ref<any>(null)
  const restoreLogs = ref<any[]>([])
  const previousStatus = ref<string>('')
  let pollingTimer: NodeJS.Timeout | null = null

  // 加载恢复状态
  const loadRestoreStatus = async () => {
    try {
      loading.value = true
      error.value = ''

      console.log('正在获取恢复任务详情，ID:', props.restoreId)
      const response = await getRestoreDetails(props.restoreId)

      if (response.success) {
        // 检查状态变化
        if (restoreTask.value && previousStatus.value) {
          const oldStatus = previousStatus.value
          const newStatus = response.data.task.status

          if (oldStatus !== newStatus) {
            if (newStatus === 'success') {
              message.success(`恢复任务 "${response.data.task.task_name}" 已完成！`)
              stopPolling()
              emit('taskCompleted', props.restoreId)
            } else if (newStatus === 'failed') {
              message.error(`恢复任务 "${response.data.task.task_name}" 执行失败`)
              stopPolling()
              emit('taskFailed', props.restoreId)
            } else if (newStatus === 'cancelled') {
              message.warning(`恢复任务 "${response.data.task.task_name}" 已取消`)
              stopPolling()
            }
          }
        }

        restoreTask.value = response.data.task
        restoreLogs.value = response.data.logs || []
        previousStatus.value = response.data.task.status

        console.log('恢复任务状态:', response.data.task.status)

        // 如果任务正在运行，启动轮询
        if (response.data.task.status === 'running' || response.data.task.status === 'pending') {
          startPolling()
        } else {
          stopPolling()
        }
      } else {
        throw new Error(response.message || '获取失败')
      }
    } catch (err: any) {
      console.error('加载恢复状态失败:', err)

      // 如果是404错误，说明任务已被删除，停止轮询
      if (err.response?.status === 404) {
        console.log('恢复任务不存在，停止轮询')
        stopPolling()
        error.value = '恢复任务不存在或已被删除'

        // 通知父组件任务已被删除
        emit('taskDeleted', props.restoreId)

        // 只在第一次遇到404时显示提示，避免重复提示
        if (!restoreTask.value) {
          message.warning('恢复任务已被删除')
        }
        return
      }

      // 其他错误才显示错误消息
      error.value = err.response?.data?.detail || err.message || '加载失败'
      message.error('加载恢复状态失败: ' + error.value)
    } finally {
      loading.value = false
    }
  }

  // 启动轮询
  const startPolling = () => {
    if (pollingTimer) return

    console.log('启动恢复任务状态轮询')
    pollingTimer = setInterval(() => {
      loadRestoreStatus()
    }, 3000)
  }

  // 停止轮询
  const stopPolling = () => {
    if (pollingTimer) {
      console.log('停止恢复任务状态轮询')
      clearInterval(pollingTimer)
      pollingTimer = null
    }
  }

  // 刷新状态
  const refreshStatus = () => {
    console.log('手动刷新恢复任务状态')
    loadRestoreStatus()
  }

  // 取消任务
  const cancelTask = async () => {
    try {
      cancelling.value = true
      console.log('正在取消恢复任务，ID:', props.restoreId)

      const response = await cancelRestoreTask(props.restoreId)

      if (response.success) {
        message.success('恢复任务已取消')
        await loadRestoreStatus()
      } else {
        throw new Error(response.message || '取消失败')
      }
    } catch (err: any) {
      console.error('取消恢复任务失败:', err)
      message.error('取消恢复任务失败: ' + (err.response?.data?.detail || err.message))
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
      running: '恢复中',
      success: '成功',
      failed: '失败',
      cancelled: '已取消'
    }
    return texts[status] || status
  }

  const getRestoreTypeText = (type: string) => {
    const texts: Record<string, string> = {
      full: '全量恢复',
      partial: '部分恢复',
      point_in_time: '时间点恢复'
    }
    return texts[type] || type
  }

  const getCurrentStep = (status: string) => {
    const steps: Record<string, string> = {
      pending: '等待开始',
      running: '正在恢复',
      success: '恢复完成',
      failed: '恢复失败',
      cancelled: '已取消'
    }
    return steps[status] || '未知状态'
  }

  // 日志相关方法
  const getLogColor = (level: string) => {
    const colors: Record<string, string> = {
      debug: 'gray',
      info: 'blue',
      warning: 'orange',
      error: 'red',
      critical: 'red'
    }
    return colors[level] || 'blue'
  }

  const getLogIcon = (level: string) => {
    const icons: Record<string, any> = {
      debug: InfoCircleOutlined,
      info: InfoCircleOutlined,
      warning: WarningOutlined,
      error: CloseOutlined,
      critical: CloseOutlined
    }
    return icons[level] || InfoCircleOutlined
  }

  const getLogLevelColor = (level: string) => {
    const colors: Record<string, string> = {
      debug: 'default',
      info: 'blue',
      warning: 'orange',
      error: 'red',
      critical: 'red'
    }
    return colors[level] || 'blue'
  }

  // 组件挂载和销毁
  onMounted(() => {
    console.log('RestoreMonitorPanel 组件已挂载，恢复任务ID:', props.restoreId)
    loadRestoreStatus()
  })

  onBeforeUnmount(() => {
    console.log('RestoreMonitorPanel 组件即将销毁，清理轮询定时器')
    stopPolling()
  })
</script>

<style scoped>
  .restore-monitor {
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

  .actions {
    border-top: 1px solid #f0f0f0;
    padding-top: 16px;
  }

  :deep(.ant-descriptions-item-label) {
    font-weight: 500;
  }
</style>
