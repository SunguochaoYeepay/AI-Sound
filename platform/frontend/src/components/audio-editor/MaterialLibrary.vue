<template>
  <div class="material-library">
    <!-- 标签布局 -->
    <div class="material-layout">
      <!-- 左侧标签 -->
      <div class="material-tabs">
        <div 
          v-for="tab in materialTabs" 
          :key="tab.key"
          class="material-tab"
          :class="{ 'active': activeMaterialTab === tab.key }"
          @click="activeMaterialTab = tab.key"
        >
          {{ tab.name }}
        </div>
      </div>
      
      <!-- 右侧内容 -->
      <div class="material-content">
        <!-- 角色音 -->
        <div v-if="activeMaterialTab === 'voice'" class="tab-content">
          <div class="search-bar">
            <a-input 
              v-model:value="searchKeyword" 
              placeholder="搜索素材..." 
              prefix-icon="search" 
              @input="handleSearch"
            />
          </div>
          
          <!-- 显示已导入的音频文件 -->
          <div v-if="filteredAudioFiles.length > 0" class="material-list">
            <div 
              v-for="audioFile in filteredAudioFiles"
              :key="audioFile.id"
              class="material-item"
              draggable="true"
              @dragstart="handleMaterialDragStart($event, audioFile)"
            >
              <div class="material-icon">
                <SoundOutlined />
              </div>
              <div class="material-info">
                <div class="material-name">{{ audioFile.name }}</div>
                <div class="material-meta">{{ formatFileSize(audioFile.fileSize) }} · {{ formatTime(audioFile.duration || 30) }}</div>
              </div>
              <div class="material-actions">
                <a-button type="text" size="small" @click="previewAudio(audioFile)">
                  <PlayCircleOutlined />
                </a-button>
              </div>
            </div>
          </div>
          
          <div v-else class="empty-state">
            <div class="empty-icon">🎤</div>
            <p>{{ searchKeyword ? '未找到匹配的素材' : '暂无素材' }}</p>
            <a-button type="primary" size="small" @click="$emit('import-audio')">导入素材</a-button>
          </div>
        </div>
        
        <!-- 背景音乐 -->
        <div v-else-if="activeMaterialTab === 'music'" class="tab-content">
          <div class="search-bar">
            <a-input v-model:value="searchKeyword" placeholder="搜索素材..." prefix-icon="search" />
          </div>
          <div class="empty-state">
            <div class="empty-icon">🎵</div>
            <p>暂无素材</p>
            <a-button type="primary" size="small" @click="$emit('import-audio')">导入素材</a-button>
          </div>
        </div>
        
        <!-- 环境音 -->
        <div v-else-if="activeMaterialTab === 'environment'" class="tab-content">
          <div class="search-bar">
            <a-input v-model:value="searchKeyword" placeholder="搜索素材..." prefix-icon="search" />
          </div>
          <div class="empty-state">
            <div class="empty-icon">🌿</div>
            <p>暂无素材</p>
            <a-button type="primary" size="small" @click="$emit('import-audio')">导入素材</a-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed } from 'vue'
import { SoundOutlined, PlayCircleOutlined } from '@ant-design/icons-vue'

export default {
  name: 'MaterialLibrary',
  components: {
    SoundOutlined,
    PlayCircleOutlined
  },
  props: {
    importedAudioFiles: {
      type: Array,
      default: () => []
    }
  },
  emits: ['import-audio', 'preview-audio', 'material-drag-start'],
  setup(props, { emit }) {
    // 响应式数据
    const activeMaterialTab = ref('voice')
    const searchKeyword = ref('')
    
    const materialTabs = ref([
      { key: 'voice', name: '角色音' },
      { key: 'music', name: '背景音乐' },
      { key: 'environment', name: '环境音' }
    ])

    // 计算属性
    const filteredAudioFiles = computed(() => {
      if (!searchKeyword.value) {
        return props.importedAudioFiles
      }
      
      const keyword = searchKeyword.value.toLowerCase()
      return props.importedAudioFiles.filter(file => 
        file.name.toLowerCase().includes(keyword) ||
        file.originalName.toLowerCase().includes(keyword)
      )
    })

    // 方法
    const handleSearch = () => {
      // 搜索逻辑已通过计算属性实现
    }

    const handleMaterialDragStart = (event, audioFile) => {
      const dragData = {
        type: 'audio-material',
        audioFile: audioFile
      }
      event.dataTransfer.setData('application/json', JSON.stringify(dragData))
      emit('material-drag-start', { event, audioFile })
    }

    const previewAudio = (audioFile) => {
      emit('preview-audio', audioFile)
    }

    const formatFileSize = (size) => {
      if (!size) return '0 B'
      if (size < 1024) return size + ' B'
      if (size < 1024 * 1024) return (size / 1024).toFixed(1) + ' KB'
      return (size / 1024 / 1024).toFixed(1) + ' MB'
    }

    const formatTime = (seconds) => {
      if (!seconds || isNaN(seconds)) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    return {
      activeMaterialTab,
      searchKeyword,
      materialTabs,
      filteredAudioFiles,
      handleSearch,
      handleMaterialDragStart,
      previewAudio,
      formatFileSize,
      formatTime
    }
  }
}
</script>

<style scoped>
/* 素材库 */
.material-library {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.material-layout {
  flex: 1;
  display: flex;
  overflow: hidden;
}

.material-tabs {
  width: 80px;
  background: #f8f9fa;
  border-right: 1px solid #e5e7eb;
  display: flex;
  flex-direction: column;
  padding-top: 8px;
}

.material-tab {
  padding: 12px 8px;
  text-align: center;
  font-size: 12px;
  color: #6b7280;
  cursor: pointer;
  transition: all 0.2s;
  border-bottom: 1px solid transparent;
}

.material-tab:hover {
  background: #e5e7eb;
  color: #374151;
}

.material-tab.active {
  background: white;
  color: #3b82f6;
  border-right: 2px solid #3b82f6;
  font-weight: 600;
}

.material-content {
  flex: 1;
  background: white;
  display: flex;
  flex-direction: column;
}

.tab-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  padding: 16px;
}

.search-bar {
  margin-bottom: 16px;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  text-align: center;
  color: #6b7280;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.empty-state p {
  margin: 8px 0 16px 0;
  font-size: 14px;
}

/* 素材库材料列表 */
.material-list {
  padding: 8px;
  overflow-y: auto;
}

.material-item {
  display: flex;
  align-items: center;
  padding: 8px 12px;
  margin-bottom: 4px;
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: move;
  transition: all 0.2s;
}

.material-item:hover {
  background: #f8fafc;
  border-color: #d1d5db;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.material-item[draggable="true"]:hover {
  cursor: grab;
}

.material-item[draggable="true"]:active {
  cursor: grabbing;
}

.material-icon {
  margin-right: 8px;
  color: #6366f1;
  font-size: 16px;
}

.material-info {
  flex: 1;
  min-width: 0;
}

.material-name {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.material-meta {
  font-size: 11px;
  color: #6b7280;
  margin-top: 2px;
}

.material-actions {
  margin-left: 8px;
}

/* 暗黑模式适配 */
[data-theme="dark"] .material-tabs {
  background: #1f1f1f;
  border-color: #434343;
}

[data-theme="dark"] .material-tab {
  color: #8c8c8c;
}

[data-theme="dark"] .material-tab:hover {
  background: #434343;
  color: #fff;
}

[data-theme="dark"] .material-tab.active {
  background: #2d2d2d;
  color: #1890ff;
  border-right-color: #1890ff;
}

[data-theme="dark"] .material-content {
  background: #2d2d2d;
}

[data-theme="dark"] .empty-state {
  color: #8c8c8c;
}

[data-theme="dark"] .material-item {
  background: #1f1f1f;
  border-color: #434343;
}

[data-theme="dark"] .material-item:hover {
  background: #2d2d2d;
  border-color: #555;
}

[data-theme="dark"] .material-name {
  color: #fff;
}

[data-theme="dark"] .material-meta {
  color: #8c8c8c;
}
</style> 