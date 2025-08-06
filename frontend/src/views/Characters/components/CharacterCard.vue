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
    </div>

    <div class="voice-actions">
      <a-button type="text" size="small" @click.stop="$emit('play', character)">
        <template #icon>
          <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
            <path d="M8,5.14V19.14L19,12.14L8,5.14Z" />
          </svg>
        </template>
      </a-button>
      <a-dropdown @click.stop="">
        <a-button type="text" size="small">
          <template #icon>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
              <path
                d="M12,16A2,2 0 0,1 14,18A2,2 0 0,1 12,20A2,2 0 0,1 10,18A2,2 0 0,1 12,16M12,10A2,2 0 0,1 14,12A2,2 0 0,1 12,14A2,2 0 0,1 10,12A2,2 0 0,1 12,10M12,4A2,2 0 0,1 14,6A2,2 0 0,1 12,8A2,2 0 0,1 10,6A2,2 0 0,1 12,4Z"
              />
            </svg>
          </template>
        </a-button>
        <template #overlay>
          <a-menu>
            <a-menu-item key="edit" @click="$emit('edit', character)">编辑</a-menu-item>
            <a-menu-item key="duplicate" @click="$emit('duplicate', character)">复制</a-menu-item>
            <a-menu-item key="export" @click="$emit('export', character)">导出</a-menu-item>
            <a-menu-divider />
            <a-menu-item
              key="delete"
              @click="$emit('delete', character)"
              style="color: #ef4444"
            >删除</a-menu-item>
          </a-menu>
        </template>
      </a-dropdown>
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
  'edit',
  'duplicate',
  'export',
  'delete',
  'batch-select'
])

// Computed
const isSelected = computed(() => props.selectedCharacterId === props.character.id)
const isBatchSelected = computed(() => props.selectedCharacterIds.includes(props.character.id))
</script>

<style scoped>
.voice-card {
  position: relative;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 20px;
  cursor: pointer;
  transition: all 0.2s ease;
  display: flex;
  flex-direction: column;
  gap: 16px;
  min-height: 200px;
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

.voice-avatar {
  position: relative;
  display: flex;
  justify-content: center;
  margin-bottom: 8px;
}

.avatar-icon {
  width: 64px;
  height: 64px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 24px;
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
  text-align: center;
}

.voice-name {
  font-size: 16px;
  font-weight: 600;
  margin: 0 0 8px 0;
  color: #1f2937;
  line-height: 1.4;
}

.voice-desc {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 12px 0;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.book-info {
  margin-bottom: 12px;
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
  justify-content: center;
  gap: 16px;
  margin-top: auto;
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
  justify-content: center;
  gap: 8px;
  margin-top: 8px;
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
</style> 