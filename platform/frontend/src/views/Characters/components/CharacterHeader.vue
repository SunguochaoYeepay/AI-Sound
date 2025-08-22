<template>
  <div class="page-header">
    <div class="header-content">
      <div class="title-section">
        <h1 class="page-title">
          <UserOutlined class="title-icon" />
          角色管理
        </h1>
      </div>
      <div class="action-section">
        <a-button type="primary" size="large" @click="$emit('add-character')">
          <template #icon>
            <PlusOutlined />
          </template>
          新建角色
        </a-button>
        <a-button 
          type="default" 
          size="large"
          @click="$emit('batch-config')"
          :disabled="selectedCount === 0"
        >
          <template #icon><SettingOutlined /></template>
          批量配置 ({{ selectedCount }})
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { UserOutlined, PlusOutlined, SettingOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  selectedCount: {
    type: Number,
    default: 0
  }
})

defineEmits(['add-character', 'batch-config'])
</script>

<style scoped>
.page-header {
  margin-bottom: 24px;
  padding: 20px 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
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

.title-icon {
  margin-right: 8px;
  color: #ffffff;
}

.action-section {
  display: flex;
  gap: 16px;
}

/* 暗黑模式适配 */
[data-theme='dark'] .page-header {
  background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}
</style> 