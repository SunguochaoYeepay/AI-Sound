<template>
  <div class="project-panel" @click.stop>
    <div class="panel-header">
      <h4>{{ selectedClip ? '音频片段信息' : '项目信息' }}</h4>
      <a-space size="small" v-if="!selectedClip">
        <a-button size="small" @click="$emit('create-project')" type="primary">
          <template #icon><PlusOutlined /></template>
          新建
        </a-button>
        <a-button size="small" @click="$emit('open-project')">
          <template #icon><FolderOpenOutlined /></template>
          打开
        </a-button>
        <a-button size="small" @click="$emit('save-project')" :disabled="!hasProject">
          <template #icon><SaveOutlined /></template>
          保存
        </a-button>
        <a-button 
          size="small" 
          @click="$emit('export-project')" 
          :disabled="!hasProject" 
          :loading="exportLoading" 
          type="primary"
        >
          <template #icon><ExportOutlined /></template>
          导出
        </a-button>
      </a-space>
    </div>
    <div class="panel-content">
      <!-- 音频片段信息 -->
      <div v-if="selectedClip" class="clip-details" @click.stop>
        <div class="project-field">
          <label>片段名称：</label>
          <EditableText 
            :value="selectedClip.filename" 
            @change="(newName) => $emit('update-clip', { filename: newName })"
            placeholder="音频片段名称"
          />
        </div>
        <div class="project-field">
          <label>音轨类型：</label>
          <span>{{ getTrackTypeLabel(selectedClip.trackType) }}</span>
        </div>
        <div class="project-field">
          <label>开始时间：</label>
          <span>{{ formatTime(selectedClip.startTime) }}</span>
        </div>
        <div class="project-field">
          <label>持续时间：</label>
          <span>{{ formatTime(selectedClip.duration) }}</span>
        </div>
        <div class="project-field">
          <label>音量：</label>
          <a-slider 
            :value="selectedClip.volume * 100" 
            :min="0" 
            :max="200" 
            :step="1"
            @change="(value) => $emit('update-clip', { volume: value / 100 })"
          />
          <span>{{ Math.round(selectedClip.volume * 100) }}%</span>
        </div>
        <div class="project-field">
          <label>淡入时间：</label>
          <a-input-number 
            :value="selectedClip.fadeIn || 0" 
            :min="0" 
            :max="selectedClip.duration / 2"
            :step="0.1"
            @change="(value) => $emit('update-clip', { fadeIn: value })"
            addon-after="秒"
          />
        </div>
        <div class="project-field">
          <label>淡出时间：</label>
          <a-input-number 
            :value="selectedClip.fadeOut || 0" 
            :min="0" 
            :max="selectedClip.duration / 2"
            :step="0.1"
            @change="(value) => $emit('update-clip', { fadeOut: value })"
            addon-after="秒"
          />
        </div>
        <div class="project-actions">
          <a-button block @click="$emit('clear-selection')">
            取消选择
          </a-button>
        </div>
      </div>
      
      <!-- 项目信息 -->
      <div v-else-if="hasProject" class="project-details" @click.stop>
        <div class="project-field">
          <label>项目名称：</label>
          <EditableText 
            :value="project.title" 
            @change="(newTitle) => $emit('update-project', { title: newTitle })"
            placeholder="项目标题"
          />
        </div>
        <div class="project-field">
          <label>项目描述：</label>
          <EditableText 
            :value="project.description" 
            @change="(newDesc) => $emit('update-project', { description: newDesc })"
            placeholder="项目描述"
          />
        </div>
        <div class="project-field">
          <label>作者：</label>
          <span>{{ project.author }}</span>
        </div>
        <div class="project-field">
          <label>总时长：</label>
          <span>{{ formatTime(project.totalDuration) }}</span>
        </div>
        <div class="project-field">
          <label>采样率：</label>
          <span>{{ project.sampleRate }} Hz</span>
        </div>
        <div class="project-field">
          <label>声道数：</label>
          <span>{{ project.channels }}</span>
        </div>
      </div>
      
      <!-- 空状态 -->
      <div v-else class="project-empty">
        <div class="empty-icon">📁</div>
        <div class="empty-text">暂无项目</div>
        <div class="empty-desc">请创建或打开一个项目</div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { h } from 'vue'
import {
  PlusOutlined,
  FolderOpenOutlined,
  SaveOutlined,
  ExportOutlined
} from '@ant-design/icons-vue'
import EditableText from '../common/EditableText.vue'

// Props
const props = defineProps({
  project: {
    type: Object,
    default: () => ({})
  },
  selectedClip: {
    type: Object,
    default: null
  },
  hasProject: {
    type: Boolean,
    default: false
  },
  exportLoading: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits([
  'create-project',
  'open-project',
  'save-project',
  'export-project',
  'update-project',
  'update-clip',
  'clear-selection'
])

// 获取音轨类型标签
function getTrackTypeLabel(type) {
  const labels = {
    dialogue: '角色对话',
    environment: '环境音效',
    background: '背景音乐'
  }
  return labels[type] || type
}

// 格式化时间
function formatTime(seconds) {
  if (!seconds || seconds < 0) return '00:00'
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.project-panel {
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

/* 项目信息样式 */
.project-details,
.clip-details {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.project-field {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.project-field label {
  color: #999;
  font-size: 12px;
  font-weight: 500;
}

.project-field span {
  color: #fff;
  font-size: 14px;
}

.project-actions {
  margin-top: 16px;
}

.project-empty {
  text-align: center;
  color: #666;
  padding: 32px 0;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-text {
  font-size: 16px;
  margin-bottom: 8px;
}

.empty-desc {
  font-size: 14px;
  color: #999;
}
</style>