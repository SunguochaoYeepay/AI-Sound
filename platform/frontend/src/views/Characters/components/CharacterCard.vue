<template>
  <div
    class="voice-card"
    @click="$emit('select', character)"
    :class="{ 
      selected: isSelected, 
      'batch-selected': isBatchSelected 
    }"
    :data-character="character.isCharacter"
  >
    <div class="batch-select-checkbox" @click.stop>
      <a-checkbox 
        :checked="isBatchSelected"
        @change="(e) => $emit('batch-select', character.id, e.target.checked)"
      />
    </div>
    
    <div class="voice-header">
      <div class="voice-avatar">
        <div
          class="avatar-icon"
          :style="{ background: character.avatarUrl ? 'transparent' : character.color }"
        >
          <img
            v-if="character.avatarUrl"
            :src="character.avatarUrl"
            :alt="character.name"
            class="avatar-image"
            @error="handleAvatarError"
          />
          <span v-else>{{ character.name.charAt(0) }}</span>
        </div>
        <div class="voice-status" :class="character.status">
          <div class="status-dot"></div>
        </div>
      </div>

      <div class="voice-info">
      <h3 class="voice-name">{{ character.name }}</h3>
      <p class="voice-desc">{{ character.description }}</p>

      <!-- 角色模式：显示书籍信息 -->
      <div v-if="managementType === 'character' && character.book" class="book-info">
        <div class="book-badge">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"
            />
          </svg>
          <span>{{ character.book.title }}</span>
        </div>
      </div>

      </div>
    </div>

    <div class="voice-meta">
      <!-- 声音样本模式：显示质量和使用次数 -->
      <template v-if="managementType === 'voice'">
        <div class="meta-item">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
            />
          </svg>
          <span>{{ (character.quality || 0).toFixed(1) }}</span>
        </div>
        <div class="meta-item">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
            />
          </svg>
          <span>{{ character.usageCount }}</span>
        </div>
      </template>

      <!-- 角色模式：显示配置状态 -->
      <template v-else>
        <div class="meta-item">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"
            />
          </svg>
          <span>{{ character.status === 'configured' ? '已配置' : '待配置' }}</span>
        </div>
        <div class="meta-item">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path
              d="M9 11H7v3h2v-3zm4 0h-2v3h2v-3zm4 0h-2v3h2v-3zm2-7h-1V2h-2v2H8V2H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V7c0-1.1-.9-2-2-2zm0 16H5V9h14v11z"
            />
          </svg>
          <span>{{ character.createdAt }}</span>
        </div>
      </template>
    </div>

    <div class="voice-actions">
      <a-button type="text" size="small" @click.stop="$emit('play', character)" title="播放">
        <template #icon>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8,5.14V19.14L19,12.14L8,5.14Z" />
          </svg>
        </template>
      </a-button>
      <a-button type="text" size="small" @click.stop="$emit('view', character)" title="详情">
        <template #icon>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12,9A3,3 0 0,0 9,12A3,3 0 0,0 12,15A3,3 0 0,0 15,12A3,3 0 0,0 12,9M12,17A5,5 0 0,1 7,12A5,5 0 0,1 12,7A5,5 0 0,1 17,12A5,5 0 0,1 12,17M12,4.5C7,4.5 2.73,7.61 1,12C2.73,16.39 7,19.5 12,19.5C17,19.5 21.27,16.39 23,12C21.27,7.61 17,4.5 12,4.5Z" />
          </svg>
        </template>
      </a-button>
      <a-button type="text" size="small" @click.stop="$emit('edit', character)" title="编辑">
        <template #icon>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M20.71,7.04C21.1,6.65 21.1,6 20.71,5.63L18.37,3.29C18,2.9 17.35,2.9 16.96,3.29L15.12,5.12L18.87,8.87M3,17.25V21H6.75L17.81,9.93L14.06,6.18L3,17.25Z" />
          </svg>
        </template>
      </a-button>
      <a-button type="text" size="small" @click.stop="$emit('delete', character)" title="删除" style="color: #ef4444">
        <template #icon>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M19,4H15.5L14.5,3H9.5L8.5,4H5V6H19M6,19A2,2 0 0,0 8,21H16A2,2 0 0,0 18,19V7H6V19Z" />
          </svg>
        </template>
      </a-button>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

// Props
const props = defineProps({
  character: {
    type: Object,
    required: true
  },
  selectedCharacterId: {
    type: Number,
    default: null
  },
  selectedCharacterIds: {
    type: Array,
    default: () => []
  },
  managementType: {
    type: String,
    default: 'character'
  }
})

// Emits
const emit = defineEmits([
  'select',
  'play',
  'view',
  'edit',
  'duplicate',
  'export',
  'delete',
  'batch-select'
])

// Computed
const isSelected = computed(() => props.selectedCharacterId === props.character.id)
const isBatchSelected = computed(() => props.selectedCharacterIds.includes(props.character.id))

// Methods
const handleAvatarError = (event) => {
  console.warn(`头像加载失败: ${props.character.name}`, event.target.src)
  // 清除错误的头像URL，让组件显示默认头像
  props.character.avatarUrl = null
}
</script>

<style scoped>
.voice-card {
  position: relative;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 12px;
  min-height: 200px;
  height: 100%;
}

.voice-card:hover {
  border-color: #8b5cf6;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.1);
  transform: translateY(-2px);
}

.voice-card.selected {
  border-color: #8b5cf6;
  background: #f8f7ff;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.15);
}

.voice-card.batch-selected {
  border-color: #10b981;
  background: #f0fdf4;
}

.batch-select-checkbox {
  position: absolute;
  top: 12px;
  right: 12px;
  z-index: 10;
  background: rgba(255, 255, 255, 0.9);
  border-radius: 4px;
  padding: 2px;
}

.voice-header {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 8px;
}

.voice-avatar {
  position: relative;
  flex-shrink: 0;
}

.avatar-icon {
  width: 56px;
  height: 56px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 20px;
  position: relative;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.voice-status {
  position: absolute;
  bottom: 0;
  right: 0;
  width: 16px;
  height: 16px;
  border-radius: 50%;
  border: 2px solid #fff;
}

.voice-status.configured {
  background: #10b981;
}

.voice-status.unconfigured {
  background: #f59e0b;
}

.voice-status.training {
  background: #3b82f6;
}

.status-dot {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  background: inherit;
}

.voice-info {
  flex: 1;
  min-width: 0;
}

.voice-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 6px 0;
  color: #1f2937;
  line-height: 1.3;
}

.voice-desc {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 8px 0;
  line-height: 1.3;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.book-info {
  margin-bottom: 8px;
}

.book-badge {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 8px;
  background: #f3f4f6;
  border-radius: 6px;
  font-size: 11px;
  color: #6b7280;
}

.voice-meta {
  display: flex;
  justify-content: flex-start;
  gap: 16px;
  margin-top: 4px;
}

.meta-item {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: #6b7280;
}

.voice-actions {
  display: flex;
  justify-content: space-between;
  gap: 4px;
  margin-top: 8px;
  padding-top: 8px;
  border-top: 1px solid #f3f4f6;
}

/* 暗黑模式适配 */
[data-theme='dark'] .voice-card {
  background: #1f1f1f;
  border-color: #434343;
  color: #d1d5db;
}

[data-theme='dark'] .voice-card:hover {
  border-color: #8b5cf6;
  box-shadow: 0 4px 12px rgba(139, 92, 246, 0.2);
}

[data-theme='dark'] .voice-card.selected {
  background: #2d1b69;
  border-color: #8b5cf6;
}

[data-theme='dark'] .voice-card.batch-selected {
  background: #064e3b;
  border-color: #10b981;
}

[data-theme='dark'] .batch-select-checkbox {
  background: rgba(31, 31, 31, 0.9);
}

[data-theme='dark'] .voice-name {
  color: #f9fafb;
}

[data-theme='dark'] .voice-desc {
  color: #9ca3af;
}

[data-theme='dark'] .book-badge {
  background: #374151;
  color: #9ca3af;
}

[data-theme='dark'] .meta-item {
  color: #9ca3af;
}

[data-theme='dark'] .voice-actions {
  border-top-color: #374151;
}
</style>