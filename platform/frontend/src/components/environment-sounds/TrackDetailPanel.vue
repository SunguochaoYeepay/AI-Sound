<template>
  <div class="track-detail-panel">
    <div class="panel-header">
      <h3>轨道详情</h3>
      <div class="track-status">
        <CheckCircleOutlined v-if="track.has_match" class="status-icon success" />
        <ClockCircleOutlined v-else class="status-icon warning" />
        <span class="status-text">
          {{ track.has_match ? '已匹配' : '需生成' }}
        </span>
      </div>
    </div>

    <div class="track-content">
      <!-- 基本信息 -->
      <div class="info-section">
        <h4>基本信息</h4>
        <div class="info-grid">
          <div class="info-item">
            <span class="label">时间范围：</span>
            <span class="value">{{ formatTime(track.start_time) }} - {{ formatTime(track.start_time + track.duration) }}</span>
          </div>
          <div class="info-item">
            <span class="label">时长：</span>
            <span class="value">{{ track.duration.toFixed(1) }}秒</span>
          </div>
          <div class="info-item">
            <span class="label">置信度：</span>
            <span class="value">
              <a-progress 
                :percent="track.confidence * 100" 
                :show-info="false"
                size="small"
                style="width: 100px"
              />
              {{ (track.confidence * 100).toFixed(0) }}%
            </span>
          </div>
        </div>
      </div>

      <!-- 环境关键词 -->
      <div class="info-section">
        <h4>环境关键词</h4>
        <div class="keywords-list">
          <a-tag 
            v-for="keyword in track.environment_keywords" 
            :key="keyword"
            :color="getKeywordColor(keyword)"
            size="medium"
          >
            {{ keyword }}
          </a-tag>
        </div>
      </div>

      <!-- 场景描述 -->
      <div class="info-section">
        <h4>场景描述</h4>
        <div class="scene-description">
          {{ track.scene_description || '无场景描述' }}
        </div>
      </div>

      <!-- 旁白内容 -->
      <div class="info-section">
        <h4>旁白内容</h4>
        <div class="narration-content">
          {{ track.narration_text }}
        </div>
      </div>

      <!-- 匹配结果 -->
      <div v-if="track.has_match && track.best_match" class="info-section">
        <h4>最佳匹配</h4>
        <div class="match-result">
          <div class="match-info">
            <div class="match-name">{{ track.best_match.sound_name }}</div>
            <div class="match-confidence">
              匹配度: {{ (track.best_match.confidence * 100).toFixed(0) }}%
            </div>
          </div>
          <div class="match-actions">
            <a-button type="primary" size="small" @click="previewSound(track.best_match.sound_id)">
              预览
            </a-button>
          </div>
        </div>
      </div>

      <!-- 生成参数（仅当需要生成时显示） -->
      <div v-if="!track.has_match" class="info-section">
        <h4>生成参数</h4>
        <div class="parameter-form">
          <a-form :model="parameterForm" layout="vertical">
            <a-form-item label="生成时长">
              <a-input-number
                v-model:value="parameterForm.duration"
                :min="1"
                :max="300"
                style="width: 100%"
              />
              <span class="unit">秒</span>
            </a-form-item>
            
            <a-form-item label="强度等级">
              <a-select v-model:value="parameterForm.intensity">
                <a-select-option value="low">低强度</a-select-option>
                <a-select-option value="medium">中等强度</a-select-option>
                <a-select-option value="high">高强度</a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="生成提示词">
              <a-textarea
                v-model:value="parameterForm.prompt"
                :rows="3"
                placeholder="请输入生成提示词"
              />
            </a-form-item>
          </a-form>
          
          <div class="parameter-actions">
            <a-button type="primary" @click="saveParameters">
              保存参数
            </a-button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import { message } from 'ant-design-vue'
import { CheckCircleOutlined, ClockCircleOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  track: {
    type: Object,
    required: true
  }
})

const emit = defineEmits(['parameter-change'])

const parameterForm = ref({
  duration: 30,
  intensity: 'medium',
  prompt: ''
})

// 监听轨道变化，更新表单
watch(() => props.track, (newTrack) => {
  if (newTrack) {
    parameterForm.value = {
      duration: newTrack.suggested_duration || newTrack.duration,
      intensity: newTrack.intensity_level || 'medium',
      prompt: newTrack.custom_prompt || `生成${newTrack.environment_keywords.join('、')}环境音，场景：${newTrack.scene_description}`
    }
  }
}, { immediate: true })

const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const getKeywordColor = (keyword) => {
  const colors = ['blue', 'green', 'orange', 'purple', 'cyan', 'magenta']
  const index = keyword.charCodeAt(0) % colors.length
  return colors[index]
}

const previewSound = (soundId) => {
  // TODO: 实现音频预览功能
  message.info('音频预览功能待实现')
}

const saveParameters = () => {
  emit('parameter-change', props.track.segment_id, parameterForm.value)
  message.success('参数已保存')
}
</script>

<style scoped>
.track-detail-panel {
  height: 100%;
  overflow-y: auto;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--ant-border-color-split);
}

.panel-header h3 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: var(--ant-text-color);
}

.track-status {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-icon {
  font-size: 16px;
}

.status-icon.success {
  color: var(--ant-success-color);
}

.status-icon.warning {
  color: var(--ant-warning-color);
}

.status-text {
  font-size: 14px;
  color: var(--ant-text-color-secondary);
}

.track-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.info-section {
  background: var(--ant-item-hover-bg);
  border-radius: 6px;
  padding: 16px;
}

.info-section h4 {
  margin: 0 0 12px 0;
  font-size: 14px;
  font-weight: 600;
  color: var(--ant-text-color);
}

.info-grid {
  display: grid;
  gap: 8px;
}

.info-item {
  display: flex;
  align-items: center;
  gap: 8px;
}

.info-item .label {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
  min-width: 60px;
}

.info-item .value {
  font-size: 12px;
  color: var(--ant-text-color);
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.scene-description,
.narration-content {
  font-size: 14px;
  color: var(--ant-text-color);
  line-height: 1.6;
  background: var(--ant-component-background);
  padding: 12px;
  border-radius: 4px;
  border: 1px solid var(--ant-border-color-split);
}

.match-result {
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--ant-component-background);
  padding: 12px;
  border-radius: 4px;
  border: 1px solid var(--ant-border-color-split);
}

.match-name {
  font-weight: 500;
  color: var(--ant-text-color);
  margin-bottom: 4px;
}

.match-confidence {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
}

.parameter-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.unit {
  margin-left: 8px;
  color: var(--ant-text-color-secondary);
}

.parameter-actions {
  display: flex;
  justify-content: flex-end;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .panel-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .match-result {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
}
</style>
