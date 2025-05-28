<template>
  <a-layout-sider 
    v-model:collapsed="collapsed"
    :trigger="null"
    collapsible
    class="sidebar"
  >
    <div class="logo">
      <span v-if="!collapsed" class="logo-text">AI-Sound</span>
    </div>
    
    <a-menu
      v-model:selectedKeys="selectedKeys"
      v-model:openKeys="openKeys"
      theme="dark"
      mode="inline"
    >
      <a-menu-item key="dashboard" @click="() => router.push('/')">
        <template #icon><dashboard-outlined /></template>
        <span>控制台</span>
      </a-menu-item>
      
      <a-menu-item key="engines" @click="() => router.push('/engines')">
        <template #icon><api-outlined /></template>
        <span>引擎状态</span>
      </a-menu-item>
      
      <!-- 声音管理分组 -->
      <a-sub-menu key="voice-management">
        <template #icon><audio-outlined /></template>
        <template #title>声音管理</template>
        
        <a-menu-item key="voice-feature" @click="() => router.push('/voice-feature')">
          <template #icon><audio-outlined /></template>
          <span>声纹特征提取</span>
        </a-menu-item>
        
        <a-menu-item key="voice-list" @click="() => router.push('/voice-list')">
          <template #icon><unordered-list-outlined /></template>
          <span>声音库</span>
        </a-menu-item>
        
        <a-menu-item key="character-mapper" @click="() => router.push('/character-mapper')">
          <template #icon><user-switch-outlined /></template>
          <span>角色声音映射</span>
        </a-menu-item>
        
        <a-menu-item key="tts" @click="() => router.push('/tts')">
          <template #icon><sound-outlined /></template>
          <span>语音试听</span>
        </a-menu-item>
      </a-sub-menu>
      
      <!-- 小说管理分组 -->
      <a-sub-menu key="novel-management">
        <template #icon><read-outlined /></template>
        <template #title>小说管理</template>
        
        <a-menu-item key="novels" @click="() => router.push('/novels')">
          <template #icon><file-outlined /></template>
          <span>小说列表</span>
        </a-menu-item>
        
        <a-menu-item key="novel" @click="() => router.push('/novel')">
          <template #icon><read-outlined /></template>
          <span>小说处理</span>
        </a-menu-item>
      </a-sub-menu>
      
      <!-- 任务与输出分组 -->
      <a-sub-menu key="task-output">
        <template #icon><schedule-outlined /></template>
        <template #title>任务与输出</template>
        
        <a-menu-item key="tasks" @click="() => router.push('/tasks')">
          <template #icon><schedule-outlined /></template>
          <span>任务监控</span>
        </a-menu-item>
        
        <a-menu-item key="library" @click="() => router.push('/library')">
          <template #icon><sound-filled /></template>
          <span>音频库</span>
        </a-menu-item>
      </a-sub-menu>
      
      <a-menu-item key="settings" @click="() => router.push('/settings')">
        <template #icon><setting-outlined /></template>
        <span>系统设置</span>
      </a-menu-item>
    </a-menu>
    
    <div class="collapse-trigger" @click="toggleCollapsed">
      <menu-fold-outlined v-if="!collapsed" />
      <menu-unfold-outlined v-else />
    </div>
  </a-layout-sider>
</template>

<script>
import { defineComponent, ref, watch, onMounted } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { 
  DashboardOutlined, 
  SoundOutlined, 
  ReadOutlined,
  MenuFoldOutlined,
  MenuUnfoldOutlined,
  SettingOutlined,
  FileOutlined,
  SoundFilled,
  ScheduleOutlined,
  AudioOutlined,
  UnorderedListOutlined,
  UserSwitchOutlined,
  ApiOutlined
} from '@ant-design/icons-vue';

export default defineComponent({
  name: 'AppSidebar',
  components: {
    DashboardOutlined,
    SoundOutlined,
    ReadOutlined,
    MenuFoldOutlined,
    MenuUnfoldOutlined,
    SettingOutlined,
    FileOutlined,
    SoundFilled,
    ScheduleOutlined,
    AudioOutlined,
    UnorderedListOutlined,
    UserSwitchOutlined,
    ApiOutlined
  },
  setup() {
    const collapsed = ref(false);
    const router = useRouter();
    const route = useRoute();
    const selectedKeys = ref(['dashboard']);
    const openKeys = ref(['voice-management', 'novel-management', 'task-output']);
    
    // 根据当前路由更新选中的菜单项
    const updateSelectedKeys = () => {
      const path = route.path;
      
      // 清除之前的选中状态
      selectedKeys.value = [];
      
      if (path === '/' || path === '/dashboard') {
        selectedKeys.value = ['dashboard'];
      } else if (path.startsWith('/engines')) {
        selectedKeys.value = ['engines'];
      } else if (path.startsWith('/tts')) {
        selectedKeys.value = ['tts'];
        openKeys.value = ['voice-management'];
      } else if (path.startsWith('/novel') && !path.startsWith('/novels')) {
        selectedKeys.value = ['novel'];
        openKeys.value = ['novel-management'];
      } else if (path.startsWith('/tasks')) {
        selectedKeys.value = ['tasks'];
        openKeys.value = ['task-output'];
      } else if (path.startsWith('/novels')) {
        selectedKeys.value = ['novels'];
        openKeys.value = ['novel-management'];
      } else if (path.startsWith('/voice-feature')) {
        selectedKeys.value = ['voice-feature'];
        openKeys.value = ['voice-management'];
      } else if (path.startsWith('/voice-list')) {
        selectedKeys.value = ['voice-list'];
        openKeys.value = ['voice-management'];
      } else if (path.startsWith('/character-mapper')) {
        selectedKeys.value = ['character-mapper'];
        openKeys.value = ['voice-management'];
      } else if (path.startsWith('/library')) {
        selectedKeys.value = ['library'];
        openKeys.value = ['task-output'];
      } else if (path.startsWith('/settings')) {
        selectedKeys.value = ['settings'];
      }
    };
    
    // 切换侧边栏展开/收起状态
    const toggleCollapsed = () => {
      collapsed.value = !collapsed.value;
    };
    
    // 监听路由变化
    watch(() => route.path, updateSelectedKeys);
    
    // 组件挂载时设置选中项
    onMounted(updateSelectedKeys);
    
    return {
      collapsed,
      selectedKeys,
      openKeys,
      router,
      toggleCollapsed
    };
  }
});
</script>

<style scoped>
.sidebar {
  height: 100vh;
  position: relative;
}

.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  transition: all 0.3s;
  background: #001529;
  padding: 0 24px;
}

.logo-text {
  color: white;
  font-size: 18px;
  font-weight: 600;
  white-space: nowrap;
  opacity: 1;
  transition: opacity 0.3s;
}

.collapse-trigger {
  position: absolute;
  bottom: 16px;
  left: 50%;
  transform: translateX(-50%);
  color: rgba(255, 255, 255, 0.65);
  font-size: 16px;
  cursor: pointer;
  transition: color 0.3s;
}

.collapse-trigger:hover {
  color: #fff;
}
</style> 