<template>
  <div class="properties-panel">
    <div class="panel-header">
     
    </div>
    <div class="panel-content">
      <!-- 选中音频片段的属性 -->
      <div v-if="selectedAudioClip" class="clip-properties">
        <h5>音频片段</h5>
        <div class="property-item">
          <label>名称:</label>
          <a-input 
            :value="selectedAudioClip.name" 
            size="small" 
            @input="updateClipProperty('name', $event.target.value)"
          />
        </div>
        <div class="property-item">
          <label>开始时间:</label>
          <span>{{ formatTime(selectedAudioClip.startTime) }}</span>
        </div>
        <div class="property-item">
          <label>持续时间:</label>
          <span>{{ formatTime(selectedAudioClip.duration || (selectedAudioClip.endTime - selectedAudioClip.startTime)) }}</span>
        </div>
        <div class="property-item">
          <label>音量:</label>
          <a-slider 
            :value="selectedAudioClip.volume" 
            :min="0" 
            :max="1" 
            :step="0.01"
            size="small"
            @change="updateClipProperty('volume', $event)"
            :tooltip-formatter="value => `${Math.round(value * 100)}%`"
          />
        </div>
        <div class="property-item">
          <label>淡入:</label>
          <a-input-number 
            :value="selectedAudioClip.fadeIn" 
            :min="0" 
            :max="5" 
            :step="0.1"
            size="small"
            addon-after="秒"
            @change="updateClipProperty('fadeIn', $event)"
          />
        </div>
        <div class="property-item">
          <label>淡出:</label>
          <a-input-number 
            :value="selectedAudioClip.fadeOut" 
            :min="0" 
            :max="5" 
            :step="0.1"
            size="small"
            addon-after="秒"
            @change="updateClipProperty('fadeOut', $event)"
          />
        </div>
      </div>
      
      <!-- 选中轨道的属性 -->
      <div v-else-if="selectedTrack" class="track-properties">
        <h5>轨道属性</h5>
        <div class="property-item">
          <label>轨道名称:</label>
          <a-input 
            :value="selectedTrack.name" 
            size="small" 
            @input="updateTrackProperty('name', $event.target.value)"
          />
        </div>
        <div class="property-item">
          <label>轨道类型:</label>
          <span>{{ getTrackTypeLabel(selectedTrack.type) }}</span>
        </div>
        <div class="property-item">
          <label>轨道音量:</label>
          <a-slider 
            :value="selectedTrack.volume" 
            :min="0" 
            :max="1" 
            :step="0.01"
            size="small"
            :disabled="selectedTrack.muted"
            @change="updateTrackProperty('volume', $event)"
            :tooltip-formatter="value => `${Math.round(value * 100)}%`"
          />
        </div>
        <div class="property-item">
          <label>平移:</label>
          <a-slider 
            :value="selectedTrack.pan || 0" 
            :min="-1" 
            :max="1" 
            :step="0.01"
            size="small"
            @change="updateTrackProperty('pan', $event)"
            :tooltip-formatter="value => {
              if (value === 0) return '居中'
              return value > 0 ? `右 ${Math.round(value * 100)}%` : `左 ${Math.round(-value * 100)}%`
            }"
          />
        </div>
        <div class="property-item">
          <label>片段数量:</label>
          <span>{{ selectedTrack.segments?.length || 0 }}</span>
        </div>
      </div>
      
      <!-- 项目属性 -->
      <div v-else class="project-properties">
       
        <div class="property-item">
          <label>项目名称:</label>
          <a-input 
            :value="projectSettings.name" 
            size="small" 
            @input="updateProjectProperty('name', $event.target.value)"
          />
        </div>
        <div class="property-item">
          <label>采样率:</label>
          <a-select 
            :value="projectSettings.sampleRate" 
            size="small"
            @change="updateProjectProperty('sampleRate', $event)"
          >
            <a-select-option value="44100">44.1 kHz</a-select-option>
            <a-select-option value="48000">48 kHz</a-select-option>
            <a-select-option value="96000">96 kHz</a-select-option>
          </a-select>
        </div>
        <div class="property-item">
          <label>位深度:</label>
          <a-select 
            :value="projectSettings.bitDepth" 
            size="small"
            @change="updateProjectProperty('bitDepth', $event)"
          >
            <a-select-option value="16">16 bit</a-select-option>
            <a-select-option value="24">24 bit</a-select-option>
            <a-select-option value="32">32 bit</a-select-option>
          </a-select>
        </div>
        <div class="property-item">
          <label>项目长度:</label>
          <span>{{ formatTime(projectStats.duration) }}</span>
        </div>
        <div class="property-item">
          <label>轨道数量:</label>
          <span>{{ projectStats.trackCount }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'PropertiesPanel',
  props: {
    selectedAudioClip: {
      type: Object,
      default: null
    },
    selectedTrack: {
      type: Object,
      default: null
    },
    projectSettings: {
      type: Object,
      default: () => ({
        name: '新建项目',
        sampleRate: '48000',
        bitDepth: '24'
      })
    },
    projectStats: {
      type: Object,
      default: () => ({
        duration: 0,
        trackCount: 0
      })
    }
  },
  emits: ['update-clip-property', 'update-track-property', 'update-project-property'],
  setup(props, { emit }) {
    // 方法
    const updateClipProperty = (property, value) => {
      emit('update-clip-property', { property, value })
    }

    const updateTrackProperty = (property, value) => {
      emit('update-track-property', { property, value })
    }

    const updateProjectProperty = (property, value) => {
      emit('update-project-property', { property, value })
    }

    const getTrackTypeLabel = (type) => {
      const labels = {
        audio: '音频',
        voice: '语音',
        music: '音乐',
        environment: '环境音',
        effect: '音效'
      }
      return labels[type] || type
    }

    const formatTime = (seconds) => {
      if (!seconds || isNaN(seconds)) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    return {
      updateClipProperty,
      updateTrackProperty,
      updateProjectProperty,
      getTrackTypeLabel,
      formatTime
    }
  }
}
</script>

<style scoped>
/* 属性面板 */
.properties-panel {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: #fafafa;
  padding: 16px;
}

.panel-header {
  margin-bottom: 16px;
}

.panel-header h4 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: #374151;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
}

.clip-properties,
.track-properties,
.project-properties {
  background: white;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 16px;
}

.clip-properties h5,
.track-properties h5,
.project-properties h5 {
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 600;
  color: #374151;
  padding-bottom: 8px;
  border-bottom: 1px solid #e5e7eb;
}

.property-item {
  margin-bottom: 12px;
}

.property-item label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  margin-bottom: 4px;
}

.property-item span {
  font-size: 12px;
  color: #374151;
  font-family: 'SF Mono', Monaco, 'Cascadia Code', 'Roboto Mono', Consolas, 'Courier New', monospace;
}

.property-item .ant-input,
.property-item .ant-select,
.property-item .ant-input-number {
  width: 100%;
}

.property-item .ant-slider {
  margin: 4px 0 8px 0;
}

/* 暗黑模式适配 */
[data-theme="dark"] .properties-panel {
  background: #1f1f1f;
}

[data-theme="dark"] .panel-header h4 {
  color: #fff;
}

[data-theme="dark"] .clip-properties,
[data-theme="dark"] .track-properties,
[data-theme="dark"] .project-properties {
  background: #2d2d2d;
  border-color: #434343;
}

[data-theme="dark"] .clip-properties h5,
[data-theme="dark"] .track-properties h5,
[data-theme="dark"] .project-properties h5 {
  color: #fff;
  border-bottom-color: #434343;
}

[data-theme="dark"] .property-item label {
  color: #8c8c8c;
}

[data-theme="dark"] .property-item span {
  color: #fff;
}
</style> 