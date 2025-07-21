<template>
  <div class="page-header">
    <div class="header-content">
      <div class="title-section">
        <div class="title-with-back">
          <a-button type="text" @click="$emit('back')" class="back-btn">
            <template #icon><ArrowLeftOutlined /></template>
          </a-button>
          <h1 class="page-title">
            {{ project?.book?.title || project?.name || '加载中...' }}
          </h1>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
  import { ArrowLeftOutlined, SoundOutlined } from '@ant-design/icons-vue'

  const props = defineProps({
    project: {
      type: Object,
      default: () => null
    },
    loading: {
      type: Boolean,
      default: false
    }
  })

  defineEmits(['back'])

  // 智能状态显示：根据实际完成情况显示状态
  const getDisplayStatus = (rawStatus) => {
    if (!rawStatus || !props.project) return rawStatus

    if (rawStatus === 'partial_completed') {
      const completed =
        props.project?.statistics?.completedSegments || props.project?.processed_segments || 0
      const total = props.project?.statistics?.totalSegments || props.project?.total_segments || 0
      const failed =
        props.project?.statistics?.failedSegments || props.project?.failed_segments || 0

      if (total > 0 && completed === total && failed === 0) {
        return 'completed'
      }
      if (failed > 0) {
        return 'failed'
      }
    }
    return rawStatus
  }

  const getStatusText = (status) => {
    if (!status) return '未知状态'

    const displayStatus = getDisplayStatus(status)
    const texts = {
      pending: '待开始',
      processing: '合成中',
      paused: '已暂停',
      completed: '已完成',
      partial_completed: '部分完成',
      failed: '失败',
      cancelled: '已取消'
    }
    return texts[displayStatus] || displayStatus
  }

  const getStatusColor = (status) => {
    if (!status) return 'default'

    const displayStatus = getDisplayStatus(status)
    const colors = {
      pending: 'orange',
      processing: 'blue',
      paused: 'purple',
      completed: 'green',
      partial_completed: 'gold',
      failed: 'red',
      cancelled: 'default'
    }
    return colors[displayStatus] || 'default'
  }
</script>

<style scoped>
  .page-header {
    margin-bottom: 16px;
    padding: 24px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 0;
    box-shadow: 0 2px 8px rgba(102, 126, 234, 0.15);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .title-with-back {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .back-btn {
    flex-shrink: 0;
    padding: 4px 8px;
    border-radius: 6px;
    transition: all 0.2s;
    color: rgba(255, 255, 255, 0.8);
  }

  .back-btn:hover {
    background: rgba(255, 255, 255, 0.1);
    color: #ffffff;
  }

  .page-title {
    display: flex;
    align-items: center;
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: white;
  }

  .title-icon {
    margin-right: 12px;
    color: #ffffff;
  }

  .project-info {
    margin-top: 8px;
  }

  .page-description {
    margin: 0 0 8px 0;
    color: rgba(255, 255, 255, 0.9);
    font-size: 16px;
    font-weight: 500;
    line-height: 1.4;
  }

  .project-meta {
    display: flex;
    align-items: center;
    gap: 8px;
    flex-wrap: wrap;
  }

  .project-subtitle {
    font-size: 12px;
    color: rgba(255, 255, 255, 0.7);
  }

  .status-tag {
    font-size: 11px;
    background: rgba(255, 255, 255, 0.15);
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  /* 暗黑模式适配 */
  [data-theme='dark'] .page-header {
    background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
  }

  /* 移动端响应式设计 */
  @media (max-width: 768px) {
    .page-header {
      padding: 16px;
      margin-bottom: 0;
    }

    .header-content {
      flex-direction: column;
      align-items: stretch;
      gap: 12px;
    }

    .title-with-back {
      gap: 6px;
    }

    .page-title {
      font-size: 20px;
    }

    .title-icon {
      margin-right: 8px;
    }

    .page-description {
      font-size: 14px;
      margin: 0 0 6px 0;
    }

    .project-meta {
      gap: 6px;
    }

    .project-subtitle {
      font-size: 11px;
    }

    .status-tag {
      font-size: 10px;
    }
  }

  @media (max-width: 480px) {
    .page-header {
      padding: 12px;
    }

    .page-title {
      font-size: 18px;
    }

    .title-icon {
      margin-right: 6px;
    }

    .page-description {
      font-size: 13px;
    }

    .back-btn {
      padding: 2px 6px;
    }
  }
</style>
