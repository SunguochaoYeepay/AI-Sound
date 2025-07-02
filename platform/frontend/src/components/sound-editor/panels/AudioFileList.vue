<template>
  <div class="audio-list">
    <!-- 工具栏 -->
    <div class="toolbar-section">
      <div class="toolbar-left">
        <a-input-search
          :value="searchKeyword"
          :placeholder="placeholder"
          size="small"
          @change="$emit('search', $event.target.value)"
          @search="$emit('search', $event)"
        />
      </div>
      <div class="toolbar-right">
        <a-upload
          :multiple="true"
          :show-upload-list="false"
          :before-upload="(file) => handleBeforeUpload(file)"
          accept="audio/*"
        >
          <a-button type="primary" size="small">
            <template #icon><UploadOutlined /></template>
            上传
          </a-button>
        </a-upload>
        <a-button v-if="showImportButton" size="small" @click="$emit('import')">
          <template #icon><ImportOutlined /></template>
          导入
        </a-button>
      </div>
    </div>
    
    <!-- 音频文件列表 -->
    <div class="audio-files">
      <a-spin :spinning="loading">
        <div v-if="files.length === 0" class="empty-audio">
          <div class="empty-icon">{{ emptyIcon }}</div>
          <div class="empty-text">{{ emptyText }}</div>
          <div class="empty-desc">{{ emptyDesc }}</div>
        </div>
        <div v-else>
          <div 
            class="audio-item" 
            v-for="file in files" 
            :key="file.file_id"
            :draggable="true"
            @click="$emit('select', file)"
            @dblclick="$emit('add-to-project', file)"
            @dragstart="handleDragStart(file, $event)"
            @dragend="handleDragEnd($event)"
          >
            <div class="audio-preview">
              <a-button 
                size="small" 
                type="text" 
                @click.stop="$emit('play', file)"
                :icon="isPlayingFile(file.file_id) ? h(PauseCircleOutlined) : h(PlayCircleOutlined)"
              />
            </div>
            <div class="audio-info">
              <div class="audio-name" :title="file.original_name || file.filename">
                {{ file.original_name || file.filename || '未知文件' }}
              </div>
              <div class="audio-meta">
                <span class="audio-duration">{{ formatDuration(file.duration || 0) }}</span>
                <span v-if="file.format" class="audio-format">{{ file.format.toUpperCase() }}</span>
                <span v-else class="audio-format">WAV</span>
              </div>
            </div>
            <div class="audio-actions">
              <a-popconfirm
                title="确定要删除这个音频文件吗？"
                ok-text="删除"
                cancel-text="取消"
                @confirm="$emit('delete', file)"
              >
                <a-button 
                  size="small" 
                  type="text"
                  danger
                  @click.stop
                  :icon="h(DeleteOutlined)"
                  title="删除文件"
                />
              </a-popconfirm>
            </div>
          </div>
        </div>
      </a-spin>
    </div>
  </div>
</template>

<script setup>
import { h } from 'vue'
import {
  UploadOutlined,
  ImportOutlined,
  PlayCircleOutlined,
  PauseCircleOutlined,
  DeleteOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  files: {
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
  category: {
    type: String,
    required: true
  },
  placeholder: {
    type: String,
    default: '搜索音频...'
  },
  emptyIcon: {
    type: String,
    default: '🎵'
  },
  emptyText: {
    type: String,
    default: '暂无音频文件'
  },
  emptyDesc: {
    type: String,
    default: '点击上传按钮添加音频文件'
  },
  showImportButton: {
    type: Boolean,
    default: true
  }
})

// Emits
const emit = defineEmits([
  'upload',
  'import',
  'search',
  'select',
  'play',
  'delete',
  'add-to-project',
  'drag-start',
  'drag-end'
])

// 处理上传前
async function handleBeforeUpload(file) {
  emit('upload', file, props.category)
  return false // 阻止默认上传行为
}

// 处理拖拽开始
function handleDragStart(file, event) {
  emit('drag-start', file, event)
}

// 处理拖拽结束
function handleDragEnd(event) {
  emit('drag-end', event)
}

// 检查是否正在播放文件
function isPlayingFile(fileId) {
  return props.playingFileId === fileId
}

// 格式化时长
function formatDuration(seconds) {
  if (!seconds) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.audio-list {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.toolbar-section {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  gap: 8px;
}

.toolbar-left {
  flex: 1;
  min-width: 120px;
  max-width: 180px;
}

.toolbar-left .ant-input-search {
  width: 100%;
}

.toolbar-right {
  display: flex;
  gap: 6px;
  align-items: center;
}

.audio-files {
  flex: 1;
  overflow: auto;
}

.empty-audio {
  text-align: center;
  padding: 24px 12px;
  color: #666;
}

.empty-icon {
  font-size: 28px;
  margin-bottom: 8px;
}

.empty-text {
  font-size: 13px;
  margin-bottom: 6px;
}

.empty-desc {
  font-size: 11px;
  color: #999;
}

.audio-item {
  display: flex;
  align-items: center;
  padding: 6px 10px;
  background: #3a3a3a;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  margin-bottom: 6px;
  border: 1px solid transparent;
}

.audio-item:hover {
  background: #404040;
  border-color: #555;
}

.audio-item:last-child {
  margin-bottom: 0;
}

.audio-item.dragging {
  opacity: 0.5;
  transform: scale(0.95);
  border-color: #52c41a;
  background: #1f2f1f;
}

.audio-item:active {
  transform: scale(0.98);
}

.audio-preview {
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #555;
  border-radius: 4px;
  margin-right: 10px;
}

.audio-info {
  flex: 1;
  min-width: 0;
}

.audio-name {
  color: #fff;
  font-size: 12px;
  font-weight: 500;
  margin-bottom: 2px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.audio-meta {
  display: flex;
  gap: 6px;
  align-items: center;
}

.audio-duration, .audio-format {
  font-size: 10px;
  color: #999;
}

.audio-format {
  background: #555;
  padding: 2px 6px;
  border-radius: 3px;
  font-weight: 500;
}

.audio-actions {
  margin-left: 8px;
}

.audio-actions .ant-btn-text.ant-btn-dangerous {
  color: #ff7875;
  opacity: 0.7;
  transition: all 0.2s;
}

.audio-actions .ant-btn-text.ant-btn-dangerous:hover {
  opacity: 1;
  color: #ff4d4f;
  background: rgba(255, 77, 79, 0.1);
}
</style>