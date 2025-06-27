<template>
  <div class="tracks-control-panel">
    <div
      v-for="(track, index) in tracks"
      :key="track.id"
      class="track-control-row"
      :class="{ 
        active: selectedTrack === track,
        hidden: track.hidden,
        locked: track.locked 
      }"
      @click="$emit('select-track', track)"
    >
      <!-- 紧凑的工具栏布局 -->
      <div class="compact-track-controls">
        <!-- 静音/取消静音 -->
        <a-button 
          type="text" 
          size="small" 
          @click.stop="$emit('toggle-track-mute', track)"
          :class="{ 'control-active': track.muted }"
          title="静音/取消静音"
        >
          <template #icon>
            <SoundOutlined v-if="!track.muted" />
            <AudioMutedOutlined v-else />
          </template>
        </a-button>
        
        <!-- 显示/隐藏轨道 -->
        <a-button 
          type="text" 
          size="small" 
          @click.stop="$emit('toggle-track-visibility', track)"
          :class="{ 'control-active': track.hidden }"
          title="显示/隐藏轨道"
        >
          <template #icon>
            <EyeOutlined v-if="!track.hidden" />
            <EyeInvisibleOutlined v-else />
          </template>
        </a-button>
        
        <!-- 锁定/解锁轨道 -->
        <a-button 
          type="text" 
          size="small" 
          @click.stop="$emit('toggle-track-lock', track)"
          :class="{ 'control-active': track.locked }"
          title="锁定/解锁轨道"
        >
          <template #icon>
            <UnlockOutlined v-if="!track.locked" />
            <LockOutlined v-else />
          </template>
        </a-button>
        
        <!-- 紧凑的轨道标签 -->
        <div class="track-label">
          <span class="track-name">{{ track.name }}</span>
        </div>
      </div>
    </div>
    
    <!-- 空状态 -->
    <div v-if="tracks.length === 0" class="empty-tracks">
      <div class="empty-content">
        <SoundOutlined class="empty-icon" />
        <p>暂无轨道</p>
        <a-button type="primary" size="small" @click="$emit('add-track')">
          <template #icon><PlusOutlined /></template>
          添加轨道
        </a-button>
      </div>
    </div>
  </div>
</template>

<script>
import { 
  SoundOutlined, 
  AudioMutedOutlined,
  EyeOutlined, 
  EyeInvisibleOutlined, 
  LockOutlined, 
  UnlockOutlined,
  PlusOutlined
} from '@ant-design/icons-vue'

export default {
  name: 'TracksControlPanel',
  components: {
    SoundOutlined,
    AudioMutedOutlined,
    EyeOutlined,
    EyeInvisibleOutlined,
    LockOutlined,
    UnlockOutlined,
    PlusOutlined
  },
  props: {
    tracks: {
      type: Array,
      default: () => []
    },
    selectedTrack: {
      type: Object,
      default: null
    }
  },
  emits: [
    'select-track', 
    'toggle-track-mute', 
    'toggle-track-visibility', 
    'toggle-track-lock',
    'add-track'
  ]
}
</script>

<style scoped>
/* 左侧轨道控制面板 */
.tracks-control-panel {
  width: 200px;
  background: #383838;
  border-right: 1px solid #4a4a4a;
  overflow-y: auto;
}

.track-control-row {
  height: 60px;
  display: flex;
  align-items: center;
  padding: 0 8px;
  background: #383838;
  border-bottom: 1px solid #4a4a4a;
  cursor: pointer;
  transition: all 0.2s;
}

.track-control-row:hover {
  background: #3a3a3a;
}

.track-control-row.active {
  background: #1e3a8a;
  border-color: #3b82f6;
}

.track-control-row.hidden {
  opacity: 0.5;
}

.track-control-row.locked {
  border-left: 3px solid #f59e0b;
}

/* 紧凑的轨道控制布局 */
.compact-track-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  width: 100%;
}

.compact-track-controls .ant-btn {
  border: 1px solid #4a4a4a;
  background: #2c2c2c;
  color: #9ca3af;
  min-width: 26px;
  height: 26px;
  padding: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
}

.compact-track-controls .ant-btn:hover {
  border-color: #6b7280;
  background: #374151;
  color: #d1d5db;
}

.compact-track-controls .ant-btn.control-active {
  border-color: #3b82f6;
  background: #1e40af;
  color: #fff;
}

/* 紧凑轨道标签 */
.track-label {
  flex: 1;
  margin-left: 8px;
}

.track-name {
  font-size: 11px;
  color: #b0b0b0;
  font-weight: 400;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 空状态 */
.empty-tracks {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 200px;
  padding: 20px;
}

.empty-content {
  text-align: center;
  color: #8c8c8c;
}

.empty-icon {
  font-size: 32px;
  color: #4a4a4a;
  margin-bottom: 12px;
}

.empty-content p {
  margin: 12px 0 16px 0;
  font-size: 12px;
}

/* 暗黑模式适配 */
[data-theme="dark"] .tracks-control-panel {
  background: #2d2d2d;
  border-color: #434343;
}

[data-theme="dark"] .track-control-row {
  background: #2d2d2d;
  border-color: #434343;
}

[data-theme="dark"] .track-control-row:hover {
  background: #434343;
}

[data-theme="dark"] .track-control-row.active {
  background: #162844;
  border-color: #1890ff;
}

[data-theme="dark"] .track-name {
  color: #8c8c8c;
}

[data-theme="dark"] .empty-content {
  color: #8c8c8c;
}

[data-theme="dark"] .empty-icon {
  color: #434343;
}
</style> 