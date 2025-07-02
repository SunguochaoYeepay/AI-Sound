<template>
  <div class="resource-panel">
    <div class="panel-header">
      <h4>资源库</h4>
      <a-space size="small">
        <a-button size="small" @click="$emit('refresh')" :icon="h(ReloadOutlined)" title="刷新资源库" />
      </a-space>
    </div>
    <div class="panel-content">
      <div class="resource-tabs">
        <a-tabs :activeKey="activeTab" size="small" @change="$emit('tab-change', $event)">
          <a-tab-pane key="dialogue" tab="对话音">
            <AudioFileList
              :files="filteredDialogueFiles"
              :loading="loading"
              :search-keyword="searchKeyword"
              :playing-file-id="playingFileId"
              :show-import-button="true"
              category="dialogue"
              placeholder="搜索对话音..."
              empty-icon="🎤"
              empty-text="暂无对话音文件"
              empty-desc="点击上传或导入按钮添加对话音文件"
              @upload="handleUpload"
              @import="$emit('import-json')"
              @search="$emit('search', $event)"
              @select="$emit('select-file', $event)"
              @play="$emit('play-file', $event)"
              @delete="$emit('delete-file', $event)"
              @add-to-project="$emit('add-to-project', $event)"
              @drag-start="(...args) => $emit('drag-start', ...args)"
              @drag-end="$emit('drag-end', $event)"
            />
          </a-tab-pane>
          <a-tab-pane key="environment" tab="环境音">
            <AudioFileList
              :files="filteredEnvironmentFiles"
              :loading="loading"
              :search-keyword="searchKeyword"
              :playing-file-id="playingFileId"
              :show-import-button="true"
              category="environment"
              placeholder="搜索环境音..."
              empty-icon="🌿"
              empty-text="暂无环境音文件"
              empty-desc="点击上传或导入按钮添加环境音文件"
              @upload="handleUpload"
              @import="$emit('import-json')"
              @search="$emit('search', $event)"
              @select="$emit('select-file', $event)"
              @play="$emit('play-file', $event)"
              @delete="$emit('delete-file', $event)"
              @add-to-project="$emit('add-to-project', $event)"
              @drag-start="(...args) => $emit('drag-start', ...args)"
              @drag-end="$emit('drag-end', $event)"
            />
          </a-tab-pane>
          <a-tab-pane key="theme" tab="主题音">
            <AudioFileList
              :files="filteredThemeFiles"
              :loading="loading"
              :search-keyword="searchKeyword"
              :playing-file-id="playingFileId"
              :show-import-button="true"
              category="theme"
              placeholder="搜索主题音..."
              empty-icon="🎼"
              empty-text="暂无主题音文件"
              empty-desc="点击上传或导入按钮添加主题音文件"
              @upload="handleUpload"
              @import="$emit('import-json')"
              @search="$emit('search', $event)"
              @select="$emit('select-file', $event)"
              @play="$emit('play-file', $event)"
              @delete="$emit('delete-file', $event)"
              @add-to-project="$emit('add-to-project', $event)"
              @drag-start="(...args) => $emit('drag-start', ...args)"
              @drag-end="$emit('drag-end', $event)"
            />
          </a-tab-pane>
        </a-tabs>
      </div>
    </div>
  </div>
</template>

<script setup>
import { h, computed } from 'vue'
import { ReloadOutlined } from '@ant-design/icons-vue'
import AudioFileList from './AudioFileList.vue'

// Props
const props = defineProps({
  audioFiles: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  searchKeyword: {
    type: String,
    default: ''
  },
  playingFileId: {
    type: String,
    default: null
  },
  activeTab: {
    type: String,
    default: 'dialogue'
  }
})

// Emits
const emit = defineEmits([
  'refresh',
  'import-json',
  'tab-change',
  'upload',
  'search',
  'select-file',
  'play-file',
  'delete-file',
  'add-to-project',
  'drag-start',
  'drag-end'
])

// 计算属性：分类过滤的音频文件
const filteredDialogueFiles = computed(() => {
  const files = props.audioFiles.filter(file => file.category === 'dialogue' || !file.category)
  return filterFilesByKeyword(files)
})

const filteredEnvironmentFiles = computed(() => {
  const files = props.audioFiles.filter(file => file.category === 'environment')
  return filterFilesByKeyword(files)
})

const filteredThemeFiles = computed(() => {
  const files = props.audioFiles.filter(file => file.category === 'theme')
  return filterFilesByKeyword(files)
})

// 根据关键词过滤文件
function filterFilesByKeyword(files) {
  if (!props.searchKeyword) return files
  
  const keyword = props.searchKeyword.toLowerCase()
  return files.filter(file => 
    (file.original_name || file.filename).toLowerCase().includes(keyword)
  )
}

// 处理上传
function handleUpload(file, category) {
  emit('upload', file, category)
}
</script>

<style scoped>
.resource-panel {
  background: #2a2a2a;
  display: flex;
  flex-direction: column;
  border-radius: 8px;
  border: 1px solid #333;
  flex: 3;
}

/* 面板头部 */
.panel-header {
  padding: 12px 16px;
  background: #333;
  border-bottom: 1px solid #444;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top-left-radius: 8px;
  border-top-right-radius: 8px;
}

.panel-header h4 {
  margin: 0;
  color: #fff;
  font-size: 14px;
  font-weight: 500;
}

/* 面板内容 */
.panel-content {
  flex: 1;
  padding: 12px;
  overflow: auto;
}

/* 资源库样式 */
.resource-tabs :deep(.ant-tabs-nav) {
  margin: 0;
}

.resource-tabs :deep(.ant-tabs-tab) {
  color: #ccc;
}

.resource-tabs :deep(.ant-tabs-tab-active) {
  color: #1890ff;
}

.resource-tabs :deep(.ant-tabs-content-holder) {
  padding-top: 8px;
}
</style>