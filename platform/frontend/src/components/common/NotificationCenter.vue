<template>
  <div class="notification-center">
    <a-badge :count="unreadCount" :offset="[10, 10]">
      <a-button 
        type="text" 
        @click="showNotifications = !showNotifications"
        class="notification-trigger"
      >
        <template #icon>
          <BellOutlined />
        </template>
      </a-button>
    </a-badge>

    <a-drawer
      v-model:open="showNotifications"
      title="通知中心"
      placement="right"
      width="400px"
    >
      <div class="notification-content">
        <div class="notification-header">
          <a-space>
            <a-button size="small" @click="markAllAsRead">全部已读</a-button>
            <a-button size="small" @click="clearAll">清空</a-button>
          </a-space>
        </div>

        <div class="notification-list">
          <div 
            v-for="notification in notifications" 
            :key="notification.id"
            class="notification-item"
            :class="{ 'unread': !notification.read }"
            @click="markAsRead(notification.id)"
          >
            <div class="notification-icon">
              <component :is="getNotificationIcon(notification.type)" />
            </div>
            <div class="notification-content">
              <div class="notification-title">{{ notification.title }}</div>
              <div class="notification-message">{{ notification.message }}</div>
              <div class="notification-time">{{ formatTime(notification.timestamp) }}</div>
            </div>
          </div>
        </div>

        <div v-if="notifications.length === 0" class="empty-notifications">
          <a-empty description="暂无通知" />
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { BellOutlined, CheckCircleOutlined, ExclamationCircleOutlined, InfoCircleOutlined, LoadingOutlined } from '@ant-design/icons-vue'

// 响应式数据
const showNotifications = ref(false)
const notifications = ref([])
const notificationId = ref(1)

// 计算属性
const unreadCount = computed(() => 
  notifications.value.filter(n => !n.read).length
)

// 方法
const addNotification = (type, title, message, duration = 5000) => {
  const notification = {
    id: notificationId.value++,
    type,
    title,
    message,
    timestamp: new Date(),
    read: false
  }
  
  notifications.value.unshift(notification)
  
  // 限制通知数量
  if (notifications.value.length > 50) {
    notifications.value = notifications.value.slice(0, 50)
  }
  
  // 自动标记为已读
  if (duration > 0) {
    setTimeout(() => {
      markAsRead(notification.id)
    }, duration)
  }
}

const markAsRead = (id) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.read = true
  }
}

const markAllAsRead = () => {
  notifications.value.forEach(n => n.read = true)
}

const clearAll = () => {
  notifications.value = []
}

const getNotificationIcon = (type) => {
  switch (type) {
    case 'success':
      return CheckCircleOutlined
    case 'error':
      return ExclamationCircleOutlined
    case 'warning':
      return ExclamationCircleOutlined
    case 'info':
      return InfoCircleOutlined
    case 'loading':
      return LoadingOutlined
    default:
      return InfoCircleOutlined
  }
}

const formatTime = (timestamp) => {
  const now = new Date()
  const diff = now - timestamp
  
  if (diff < 60000) { // 1分钟内
    return '刚刚'
  } else if (diff < 3600000) { // 1小时内
    return `${Math.floor(diff / 60000)}分钟前`
  } else if (diff < 86400000) { // 1天内
    return `${Math.floor(diff / 3600000)}小时前`
  } else {
    return timestamp.toLocaleDateString()
  }
}

// 暴露方法给父组件
defineExpose({
  addNotification
})
</script>

<style scoped>
.notification-center {
  position: relative;
}

.notification-trigger {
  color: #666;
}

.notification-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.notification-header {
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
  margin-bottom: 16px;
}

.notification-list {
  flex: 1;
  overflow-y: auto;
}

.notification-item {
  display: flex;
  padding: 12px;
  border-bottom: 1px solid #f0f0f0;
  cursor: pointer;
  transition: background-color 0.3s;
}

.notification-item:hover {
  background-color: #f5f5f5;
}

.notification-item.unread {
  background-color: #f0f8ff;
}

.notification-item.unread:hover {
  background-color: #e6f7ff;
}

.notification-icon {
  margin-right: 12px;
  font-size: 16px;
  color: #1890ff;
}

.notification-content {
  flex: 1;
}

.notification-title {
  font-weight: 500;
  margin-bottom: 4px;
  color: #262626;
}

.notification-message {
  color: #666;
  font-size: 14px;
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification-time {
  color: #999;
  font-size: 12px;
}

.empty-notifications {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
