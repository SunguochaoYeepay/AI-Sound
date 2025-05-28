<template>
  <a-layout-header class="header">
    <div class="header-content">
      <div class="title">
        <span class="system-name">AI-Sound</span>
        <span class="version">v1.0.0</span>
      </div>
      
      <div class="actions">
        <a-space>
          <a-badge :dot="hasNewMessage" color="red">
            <bell-outlined class="icon" />
          </a-badge>
          
          <a-tooltip title="系统设置">
            <setting-outlined class="icon" />
          </a-tooltip>
          
          <a-dropdown>
            <a-avatar class="avatar">
              <template #icon><user-outlined /></template>
            </a-avatar>
            <template #overlay>
              <a-menu>
                <a-menu-item>
                  <user-outlined /> 个人中心
                </a-menu-item>
                <a-menu-item>
                  <setting-outlined /> 系统设置
                </a-menu-item>
                <a-menu-divider />
                <a-menu-item>
                  <logout-outlined /> 退出登录
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </div>
    </div>
  </a-layout-header>
</template>

<script>
import { defineComponent, ref } from 'vue';
import { BellOutlined, SettingOutlined, UserOutlined, LogoutOutlined } from '@ant-design/icons-vue';

export default defineComponent({
  name: 'AppHeader',
  components: {
    BellOutlined,
    SettingOutlined,
    UserOutlined,
    LogoutOutlined
  },
  setup() {
    const hasNewMessage = ref(false);
    
    return {
      hasNewMessage
    };
  }
});
</script>

<style scoped>
.header {
  background: #fff;
  padding: 0;
  box-shadow: 0 1px 4px rgba(0, 21, 41, 0.08);
  position: relative;
  z-index: 10;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 24px;
  height: 100%;
}

.title {
  display: flex;
  align-items: center;
}

.system-name {
  font-size: 18px;
  font-weight: 600;
  color: rgba(0, 0, 0, 0.85);
}

.version {
  font-size: 12px;
  color: rgba(0, 0, 0, 0.45);
  margin-left: 8px;
}

.actions {
  display: flex;
  align-items: center;
}

.icon {
  font-size: 16px;
  color: rgba(0, 0, 0, 0.65);
  padding: 0 12px;
  cursor: pointer;
}

.icon:hover {
  color: #1890ff;
}

.avatar {
  cursor: pointer;
  background-color: #f0f0f0;
}
</style> 