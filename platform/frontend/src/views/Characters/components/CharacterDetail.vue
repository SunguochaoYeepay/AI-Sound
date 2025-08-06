<template>
  <a-drawer
    :open="visible"
    title="声音详情"
    placement="right"
    width="500"
    :closable="true"
    @close="$emit('close')"
  >
    <div v-if="character" class="voice-detail">
      <div class="detail-header">
        <div
          class="detail-avatar"
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
        <div class="detail-info">
          <h2>{{ character.name }}</h2>
          <p>{{ character.description }}</p>
          <a-rate v-model:value="character.quality" disabled allow-half />
        </div>
      </div>

      <a-divider />

      <div class="detail-section">
        <h3>音频样本</h3>
        <div class="audio-sample">
          <div v-if="character.audioUrl">
            <audio controls style="width: 100%">
              <source :src="character.audioUrl" type="audio/wav" />
              您的浏览器不支持音频播放
            </audio>
          </div>
          <div v-else class="no-audio-message">
            <div style="text-align: center; padding: 20px; color: #6b7280">
              <svg
                width="48"
                height="48"
                viewBox="0 0 24 24"
                fill="#d1d5db"
                style="margin-bottom: 12px"
              >
                <path
                  d="M12 14c1.66 0 3-1.34 3-3V5c0-1.66-1.34-3-3-3S9 3.34 9 5v6c0 1.66 1.34 3 3 3z"
                />
                <path
                  d="M17 11c0 2.76-2.24 5-5 5s-5-2.24-5-5H5c0 3.53 2.61 6.43 6 6.92V21h2v-3.08c3.39-.49 6-3.39 6-6.92h-2z"
                />
              </svg>
              <p>暂无音频样本</p>
            </div>
          </div>
        </div>
      </div>

      <div class="detail-section">
        <h3>技术参数</h3>
        <div class="params-list">
          <div class="param-row">
            <span class="param-label">Time Step:</span>
            <span class="param-value">{{ character.params?.timeStep || 'N/A' }}</span>
          </div>
          <div class="param-row">
            <span class="param-label">智能权重 (p_w):</span>
            <span class="param-value">{{ character.params?.pWeight || 'N/A' }}</span>
          </div>
          <div class="param-row">
            <span class="param-label">相似度权重 (t_w):</span>
            <span class="param-value">{{ character.params?.tWeight || 'N/A' }}</span>
          </div>
        </div>
      </div>

      <div class="detail-section">
        <h3>使用统计</h3>
        <div class="stats-list">
          <div class="stat-row">
            <span class="stat-label">使用次数:</span>
            <span class="stat-value">{{ character.usageCount || 0 }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">创建时间:</span>
            <span class="stat-value">{{ character.createdAt || 'N/A' }}</span>
          </div>
          <div class="stat-row">
            <span class="stat-label">最后使用:</span>
            <span class="stat-value">{{ character.lastUsed || 'N/A' }}</span>
          </div>
        </div>
      </div>

      <div class="detail-actions">
        <a-button type="primary" block size="large" @click="$emit('use', character)">
          使用此声音
        </a-button>
        <div style="display: flex; gap: 12px; margin-top: 12px">
          <a-button @click="$emit('edit', character)" style="flex: 1">编辑</a-button>
          <a-button @click="$emit('duplicate', character)" style="flex: 1">复制</a-button>
          <a-button danger @click="$emit('delete', character)" style="flex: 1">删除</a-button>
        </div>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  character: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['close', 'use', 'edit', 'duplicate', 'delete'])
</script>

<style scoped>
.voice-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.detail-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.detail-avatar {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-weight: bold;
  font-size: 32px;
  flex-shrink: 0;
}

.avatar-image {
  width: 100%;
  height: 100%;
  border-radius: 50%;
  object-fit: cover;
}

.detail-info {
  flex: 1;
}

.detail-info h2 {
  margin: 0 0 8px 0;
  font-size: 20px;
  font-weight: 600;
  color: #1f2937;
}

.detail-info p {
  margin: 0 0 12px 0;
  color: #6b7280;
  line-height: 1.5;
}

.detail-section {
  margin-bottom: 24px;
}

.detail-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1f2937;
}

.audio-sample {
  background: #f9fafb;
  border-radius: 8px;
  padding: 16px;
  border: 1px solid #e5e7eb;
}

.no-audio-message {
  text-align: center;
  padding: 20px;
  color: #6b7280;
}

.params-list,
.stats-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.param-row,
.stat-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f3f4f6;
}

.param-row:last-child,
.stat-row:last-child {
  border-bottom: none;
}

.param-label,
.stat-label {
  font-weight: 500;
  color: #374151;
}

.param-value,
.stat-value {
  color: #6b7280;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
}

.detail-actions {
  margin-top: auto;
  padding-top: 24px;
  border-top: 1px solid #e5e7eb;
}

/* 暗黑模式适配 */
[data-theme='dark'] .voice-detail {
  color: #d1d5db;
}

[data-theme='dark'] .detail-info h2,
[data-theme='dark'] .detail-section h3 {
  color: #f9fafb;
}

[data-theme='dark'] .detail-info p {
  color: #9ca3af;
}

[data-theme='dark'] .audio-sample {
  background: #1f1f1f;
  border-color: #434343;
}

[data-theme='dark'] .param-row,
[data-theme='dark'] .stat-row {
  border-bottom-color: #374151;
}

[data-theme='dark'] .param-label,
[data-theme='dark'] .stat-label {
  color: #d1d5db;
}

[data-theme='dark'] .param-value,
[data-theme='dark'] .stat-value {
  color: #9ca3af;
}

[data-theme='dark'] .detail-actions {
  border-top-color: #434343;
}
</style>