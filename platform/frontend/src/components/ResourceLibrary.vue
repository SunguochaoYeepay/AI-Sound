<template>
  <div class="resource-library">
    <!-- 资源库头部 -->
    <div class="resource-header">
      <h3>素材库</h3>
      <a-button type="primary" size="small" @click="showImportModal = true">
        <PlusOutlined /> 导入
      </a-button>
    </div>

    <!-- 资源分类标签 -->
    <div class="resource-tabs">
      <a-tabs v-model:activeKey="activeTab" size="small" @change="handleTabChange">
        <a-tab-pane key="voice" tab="角色音">
          <template #tab>
            <SoundOutlined /> 角色音
          </template>
        </a-tab-pane>
        <a-tab-pane key="music" tab="背景音乐">
          <template #tab>
            <CustomerServiceOutlined /> 背景音乐
          </template>
        </a-tab-pane>
        <a-tab-pane key="environment" tab="环境音">
          <template #tab>
            <AudioOutlined /> 环境音
          </template>
        </a-tab-pane>
        <a-tab-pane key="effect" tab="音效">
          <template #tab>
            <ThunderboltOutlined /> 音效
          </template>
        </a-tab-pane>
      </a-tabs>
    </div>

    <!-- 搜索框 -->
    <div class="resource-search">
      <a-input-search
        v-model:value="searchQuery"
        placeholder="搜索素材..."
        size="small"
        @search="handleSearch"
      />
    </div>

    <!-- 资源列表 -->
    <div class="resource-list">
      <div 
        v-for="resource in filteredResources" 
        :key="resource.id"
        class="resource-item"
        :draggable="true"
        @dragstart="handleDragStart($event, resource)"
        @click="selectResource(resource)"
        :class="{ active: selectedResource?.id === resource.id }"
      >
        <!-- 资源图标 -->
        <div class="resource-icon">
          <SoundOutlined v-if="resource.category === 'voice'" />
          <CustomerServiceOutlined v-else-if="resource.category === 'music'" />
          <AudioOutlined v-else-if="resource.category === 'environment'" />
          <ThunderboltOutlined v-else />
        </div>

        <!-- 资源信息 -->
        <div class="resource-info">
          <div class="resource-name" :title="resource.name">{{ resource.name }}</div>
          <div class="resource-meta">
            <span class="resource-duration">{{ formatDuration(resource.duration) }}</span>
            <span class="resource-size">{{ formatFileSize(resource.fileSize) }}</span>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="resource-actions">
          <a-button 
            type="text" 
            size="small" 
            @click.stop="playResource(resource)"
            :loading="playingResource?.id === resource.id"
          >
            <PlayCircleOutlined v-if="playingResource?.id !== resource.id" />
            <LoadingOutlined v-else />
          </a-button>
          <a-dropdown :trigger="['click']">
            <a-button type="text" size="small" @click.stop>
              <MoreOutlined />
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item @click="addToTrack(resource)">添加到轨道</a-menu-item>
                <a-menu-item @click="showResourceInfo(resource)">查看详情</a-menu-item>
                <a-menu-divider />
                <a-menu-item danger @click="deleteResource(resource)">删除</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>

      <!-- 空状态 -->
      <div v-if="filteredResources.length === 0" class="resource-empty">
        <a-empty description="暂无素材" size="small">
          <a-button type="primary" size="small" @click="showImportModal = true">
            导入素材
          </a-button>
        </a-empty>
      </div>
    </div>

    <!-- 导入模态框 -->
    <a-modal
      v-model:open="showImportModal"
      title="导入素材"
      @ok="handleImport"
      @cancel="showImportModal = false"
    >
      <a-upload-dragger
        v-model:fileList="importFileList"
        multiple
        :before-upload="beforeUpload"
        accept="audio/*"
      >
        <p class="ant-upload-drag-icon">
          <InboxOutlined />
        </p>
        <p class="ant-upload-text">点击或拖拽文件到此区域上传</p>
        <p class="ant-upload-hint">
          支持单个或批量上传音频文件
        </p>
      </a-upload-dragger>
    </a-modal>
  </div>
</template>

<script>
import { ref, computed, onMounted, watch } from 'vue'
import { 
  PlusOutlined, SoundOutlined, CustomerServiceOutlined, 
  AudioOutlined, ThunderboltOutlined, PlayCircleOutlined, 
  LoadingOutlined, MoreOutlined, InboxOutlined 
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import ResourceManager from '@/utils/resourceManager.js'

export default {
  name: 'ResourceLibrary',
  components: {
    PlusOutlined, SoundOutlined, CustomerServiceOutlined,
    AudioOutlined, ThunderboltOutlined, PlayCircleOutlined,
    LoadingOutlined, MoreOutlined, InboxOutlined
  },
  emits: ['resourceSelected', 'addToTrack'],
  setup(props, { emit }) {
    // 响应式数据
    const activeTab = ref('voice')
    const searchQuery = ref('')
    const selectedResource = ref(null)
    const playingResource = ref(null)
    const showImportModal = ref(false)
    const importFileList = ref([])
    
    // 资源管理器
    const resourceManager = new ResourceManager()
    const loading = ref(true)

    // 计算属性
    const filteredResources = computed(() => {
      let resources = resourceManager.getResourcesByCategory(activeTab.value)
      
      if (searchQuery.value) {
        resources = resourceManager.searchResources(searchQuery.value, activeTab.value)
      }
      
      return resources
    })

    // 方法
    const loadResources = async () => {
      loading.value = true
      try {
        await resourceManager.loadAllResources()
      } catch (error) {
        message.error('加载资源失败')
      } finally {
        loading.value = false
      }
    }

    const handleTabChange = (tab) => {
      activeTab.value = tab
      selectedResource.value = null
    }

    const handleSearch = () => {
      // 搜索逻辑已在computed中处理
    }

    const selectResource = (resource) => {
      selectedResource.value = resource
      emit('resourceSelected', resource)
    }

    const playResource = async (resource) => {
      if (playingResource.value?.id === resource.id) {
        // 停止播放
        playingResource.value = null
        return
      }

      try {
        playingResource.value = resource
        // 这里应该调用全局音频播放器
        // 暂时模拟播放
        setTimeout(() => {
          playingResource.value = null
        }, 3000)
      } catch (error) {
        message.error('播放失败')
        playingResource.value = null
      }
    }

    const addToTrack = (resource) => {
      emit('addToTrack', resource)
      message.success(`已添加"${resource.name}"到轨道`)
    }

    const showResourceInfo = (resource) => {
      // 显示资源详情
      console.log('资源详情:', resource)
    }

    const deleteResource = (resource) => {
      // 删除资源逻辑
      message.success(`已删除"${resource.name}"`)
    }

    const handleDragStart = (event, resource) => {
      event.dataTransfer.setData('application/json', JSON.stringify(resource))
      event.dataTransfer.effectAllowed = 'copy'
    }

    const beforeUpload = () => {
      return false // 阻止自动上传
    }

    const handleImport = () => {
      // 处理文件导入
      if (importFileList.value.length === 0) {
        message.warning('请选择要导入的文件')
        return
      }
      
      // 这里应该处理文件上传逻辑
      message.success(`成功导入 ${importFileList.value.length} 个文件`)
      showImportModal.value = false
      importFileList.value = []
    }

    const formatDuration = (seconds) => {
      return resourceManager.formatDuration(seconds)
    }

    const formatFileSize = (bytes) => {
      return resourceManager.formatFileSize(bytes)
    }

    // 生命周期
    onMounted(() => {
      loadResources()
    })

    return {
      activeTab,
      searchQuery,
      selectedResource,
      playingResource,
      showImportModal,
      importFileList,
      loading,
      filteredResources,
      handleTabChange,
      handleSearch,
      selectResource,
      playResource,
      addToTrack,
      showResourceInfo,
      deleteResource,
      handleDragStart,
      beforeUpload,
      handleImport,
      formatDuration,
      formatFileSize
    }
  }
}
</script>

<style scoped>
.resource-library {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-color-container);
  border-right: 1px solid var(--border-color);
}

.resource-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.resource-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

.resource-tabs {
  border-bottom: 1px solid var(--border-color);
}

.resource-tabs :deep(.ant-tabs-nav) {
  margin: 0;
  padding: 0 16px;
}

.resource-tabs :deep(.ant-tabs-tab) {
  padding: 8px 4px;
  font-size: 12px;
}

.resource-search {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
}

.resource-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px;
}

.resource-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 4px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid transparent;
}

.resource-item:hover {
  background: var(--hover-color);
}

.resource-item.active {
  background: var(--primary-color-deprecated-l-35);
  border-color: var(--primary-color);
}

.resource-icon {
  margin-right: 8px;
  color: var(--text-color-secondary);
  font-size: 16px;
}

.resource-info {
  flex: 1;
  min-width: 0;
}

.resource-name {
  font-size: 13px;
  color: var(--text-color);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  margin-bottom: 2px;
}

.resource-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: var(--text-color-secondary);
}

.resource-actions {
  display: flex;
  gap: 4px;
  opacity: 0;
  transition: opacity 0.2s;
}

.resource-item:hover .resource-actions {
  opacity: 1;
}

.resource-empty {
  text-align: center;
  padding: 40px 20px;
}

/* 暗黑主题适配 */
[data-theme="dark"] .resource-library {
  background: #1f1f1f !important;
  border-right-color: #434343 !important;
}

[data-theme="dark"] .resource-header {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .resource-header h3 {
  color: #fff !important;
}

[data-theme="dark"] .resource-tabs {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .resource-search {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .resource-item {
  background: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .resource-item:hover {
  background: #363636 !important;
  border-color: #1890ff !important;
}

[data-theme="dark"] .resource-item.active {
  background: #162844 !important;
  border-color: #1890ff !important;
}

[data-theme="dark"] .resource-name {
  color: #fff !important;
}

[data-theme="dark"] .resource-meta {
  color: #8c8c8c !important;
}

[data-theme="dark"] .resource-icon {
  color: #8c8c8c !important;
}
</style>