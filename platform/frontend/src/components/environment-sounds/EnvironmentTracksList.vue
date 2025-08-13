<template>
  <div class="environment-tracks-list">
    <a-card :loading="loading" class="tracks-card">
      <template #title>
        <div class="card-title">
          <SoundOutlined class="title-icon" />
          环境音轨道列表
          <span class="track-count">({{ tracks.length }})</span>
        </div>
      </template>
      
      <div class="tracks-content">
        <div v-if="tracks.length === 0" class="empty-state">
          <a-empty description="暂无环境音轨道" />
        </div>
        
        <div v-else class="tracks-grid">
          <div 
            v-for="track in filteredTracks" 
            :key="track.segment_id"
            class="track-item"
            :class="{ 
              'selected': selectedTracks.has(track.segment_id),
              'has-match': track.has_match,
              'need-generation': !track.has_match
            }"
          >
            <!-- 选择框 -->
            <div class="track-header">
              <a-checkbox
                :checked="selectedTracks.has(track.segment_id)"
                @change="(e) => handleSelectionChange(track.segment_id, e.target.checked)"
              />
              <div class="track-status">
                <CheckCircleOutlined v-if="track.has_match" class="status-icon success" />
                <ClockCircleOutlined v-else class="status-icon warning" />
                <span class="status-text">
                  {{ track.has_match ? '已匹配' : '需生成' }}
                </span>
              </div>
            </div>

            <!-- 轨道信息 -->
            <div class="track-info">
              <div class="track-time">
                <ClockCircleOutlined />
                {{ formatTime(track.start_time) }} - {{ formatTime(track.start_time + track.duration) }}
                <span class="duration">({{ track.duration.toFixed(1) }}s)</span>
              </div>
              
              <div class="track-narration">
                <span class="label">旁白内容：</span>
                <span class="content">{{ truncateText(track.narration_text, 100) }}</span>
              </div>
              
              <div class="track-keywords">
                <span class="label">环境关键词：</span>
                <div class="keywords">
                  <a-tag 
                    v-for="keyword in track.environment_keywords" 
                    :key="keyword"
                    :color="getKeywordColor(keyword)"
                    size="small"
                  >
                    {{ keyword }}
                  </a-tag>
                </div>
              </div>
              
              <div class="track-scene">
                <span class="label">场景描述：</span>
                <span class="content">{{ track.scene_description || '无' }}</span>
              </div>
              
              <div class="track-confidence">
                <span class="label">置信度：</span>
                <a-progress 
                  :percent="track.confidence * 100" 
                  :stroke-color="getConfidenceColor(track.confidence)"
                  :show-info="false"
                  size="small"
                  style="width: 100px"
                />
                <span class="confidence-text">{{ (track.confidence * 100).toFixed(0) }}%</span>
              </div>
            </div>

            <!-- 匹配结果 -->
            <div v-if="track.has_match && track.best_match" class="match-result">
              <div class="match-header">
                <span class="match-label">最佳匹配：</span>
                <span class="match-name">{{ track.best_match.sound_name }}</span>
              </div>
              <div class="match-details">
                <span class="match-confidence">
                  匹配度: {{ (track.best_match.confidence * 100).toFixed(0) }}%
                </span>
                <a-button 
                  type="link" 
                  size="small"
                  @click="previewSound(track.best_match.sound_id)"
                >
                  预览
                </a-button>
              </div>
            </div>

            <!-- 其他匹配结果 -->
            <div v-if="track.matching_results && track.matching_results.length > 1" class="other-matches">
              <div class="other-matches-header">
                <span class="label">其他匹配：</span>
                <a-button 
                  type="link" 
                  size="small"
                  @click="showOtherMatches(track)"
                >
                  查看全部 ({{ track.matching_results.length }})
                </a-button>
              </div>
            </div>

            <!-- 参数调整 -->
            <div v-if="!track.has_match" class="parameter-adjustment">
              <div class="parameter-header">
                <span class="label">生成参数：</span>
                <a-button 
                  type="link" 
                  size="small"
                  @click="showParameterModal(track)"
                >
                  调整
                </a-button>
              </div>
              <div class="parameter-preview">
                <span>时长: {{ track.suggested_duration || track.duration }}s</span>
                <span>强度: {{ track.intensity_level || 'medium' }}</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </a-card>

         <!-- 其他匹配结果对话框 -->
     <a-modal
       v-model:open="showMatchesModal"
       title="匹配结果详情"
       width="600px"
       :footer="null"
     >
      <div v-if="currentTrack" class="matches-detail">
        <div class="track-summary">
          <h4>轨道信息</h4>
          <p>{{ currentTrack.narration_text }}</p>
          <p>关键词: {{ currentTrack.environment_keywords.join(', ') }}</p>
        </div>
        
        <div class="matches-list">
          <h4>匹配结果</h4>
          <div 
            v-for="(match, index) in currentTrack.matching_results" 
            :key="index"
            class="match-item"
          >
            <div class="match-info">
              <div class="match-name">{{ match.sound_name }}</div>
              <div class="match-details">
                <span>匹配度: {{ (match.confidence * 100).toFixed(0) }}%</span>
                <span>类型: {{ match.match_type }}</span>
              </div>
            </div>
            <div class="match-actions">
              <a-button 
                type="primary" 
                size="small"
                @click="previewSound(match.sound_id)"
              >
                预览
              </a-button>
            </div>
          </div>
        </div>
      </div>
    </a-modal>

         <!-- 参数调整对话框 -->
     <a-modal
       v-model:open="parameterModalVisible"
       title="调整生成参数"
       width="500px"
       @ok="confirmParameterChange"
       @cancel="cancelParameterChange"
     >
      <div v-if="currentTrack" class="parameter-form">
        <a-form :model="parameterForm" layout="vertical">
          <a-form-item label="环境音名称">
            <a-input 
              v-model:value="parameterForm.name"
              placeholder="请输入环境音名称"
            />
          </a-form-item>
          
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
      </div>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { 
  SoundOutlined,
  CheckCircleOutlined,
  ClockCircleOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  tracks: {
    type: Array,
    default: () => []
  },
  selectedTracks: {
    type: Set,
    default: () => new Set()
  },
  loading: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['selection-change', 'parameter-change'])

// 响应式数据
const showMatchesModal = ref(false)
const parameterModalVisible = ref(false)
const currentTrack = ref(null)
const parameterForm = ref({
  name: '',
  duration: 30,
  intensity: 'medium',
  prompt: ''
})

// 计算属性
const filteredTracks = computed(() => {
  return props.tracks
})

// 方法
const handleSelectionChange = (segmentId, selected) => {
  emit('selection-change', segmentId, selected)
}

const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const truncateText = (text, maxLength) => {
  if (!text) return ''
  return text.length > maxLength ? text.substring(0, maxLength) + '...' : text
}

const getKeywordColor = (keyword) => {
  const colors = ['blue', 'green', 'orange', 'red', 'purple', 'cyan']
  const index = keyword.charCodeAt(0) % colors.length
  return colors[index]
}

const getConfidenceColor = (confidence) => {
  if (confidence >= 0.8) return '#52c41a'
  if (confidence >= 0.5) return '#fa8c16'
  return '#ff4d4f'
}

const previewSound = (soundId) => {
  // TODO: 实现音频预览功能
  message.info('音频预览功能开发中...')
}

const showOtherMatches = (track) => {
  currentTrack.value = track
  showMatchesModal.value = true
}

const showParameterModal = (track) => {
  currentTrack.value = track
  parameterForm.value = {
    name: track.environment_keywords.join('_'),
    duration: track.suggested_duration || track.duration,
    intensity: track.intensity_level || 'medium',
    prompt: `生成${track.environment_keywords.join('、')}环境音，场景：${track.scene_description}`
  }
  parameterModalVisible.value = true
}

const confirmParameterChange = () => {
  if (!currentTrack.value) return
  
  emit('parameter-change', currentTrack.value.segment_id, parameterForm.value)
  parameterModalVisible.value = false
  message.success('参数已更新')
}

const cancelParameterChange = () => {
  parameterModalVisible.value = false
}
</script>

<style scoped>
.environment-tracks-list {
  margin-bottom: 24px;
}

.tracks-card {
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.card-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
}

.title-icon {
  margin-right: 8px;
  color: var(--ant-primary-color);
}

.track-count {
  color: var(--ant-text-color-secondary);
  font-size: 14px;
  font-weight: normal;
  margin-left: 8px;
}

.tracks-content {
  padding: 8px 0;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}

.tracks-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
  gap: 16px;
}

.track-item {
  border: 1px solid var(--ant-border-color);
  border-radius: 8px;
  padding: 16px;
  background: var(--ant-component-background);
  transition: all 0.3s ease;
}

.track-item:hover {
  box-shadow: 0 4px 12px var(--ant-box-shadow);
  transform: translateY(-2px);
}

.track-item.selected {
  border-color: var(--ant-primary-color);
  background: var(--ant-primary-1);
}

.track-item.has-match {
  border-left: 4px solid #52c41a;
}

.track-item.need-generation {
  border-left: 4px solid #fa8c16;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.track-status {
  display: flex;
  align-items: center;
  gap: 4px;
}

.status-icon {
  font-size: 14px;
}

.status-icon.success {
  color: var(--ant-success-color);
}

.status-icon.warning {
  color: var(--ant-warning-color);
}

.status-text {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
}

.track-info {
  margin-bottom: 12px;
}

.track-time {
  display: flex;
  align-items: center;
  gap: 4px;
  font-size: 14px;
  color: var(--ant-text-color-secondary);
  margin-bottom: 8px;
}

.duration {
  color: var(--ant-text-color-tertiary);
  font-size: 12px;
}

.track-narration,
.track-keywords,
.track-scene,
.track-confidence {
  margin-bottom: 8px;
}

.label {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
  margin-right: 4px;
}

.content {
  font-size: 14px;
  color: var(--ant-text-color);
}

.keywords {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
  margin-top: 4px;
}

.match-result {
  background: var(--ant-success-bg);
  border: 1px solid var(--ant-success-border);
  border-radius: 4px;
  padding: 8px;
  margin-bottom: 8px;
}

.match-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.match-label {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
}

.match-name {
  font-size: 14px;
  font-weight: 500;
  color: var(--ant-success-color);
}

.match-details {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.match-confidence {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
}

.other-matches {
  margin-bottom: 8px;
}

.other-matches-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.parameter-adjustment {
  background: var(--ant-warning-bg);
  border: 1px solid var(--ant-warning-border);
  border-radius: 4px;
  padding: 8px;
}

.parameter-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 4px;
}

.parameter-preview {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--ant-text-color-secondary);
}

/* 对话框样式 */
.matches-detail {
  max-height: 400px;
  overflow-y: auto;
}

.track-summary {
  margin-bottom: 16px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--ant-border-color-split);
}

.track-summary h4 {
  margin-bottom: 8px;
  color: var(--ant-text-color);
}

.matches-list h4 {
  margin-bottom: 12px;
  color: var(--ant-text-color);
}

.match-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px;
  border: 1px solid var(--ant-border-color-split);
  border-radius: 4px;
  margin-bottom: 8px;
}

.match-info {
  flex: 1;
}

.match-name {
  font-weight: 500;
  margin-bottom: 4px;
}

.match-details {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: var(--ant-text-color-secondary);
}

.parameter-form {
  padding: 8px 0;
}

.unit {
  margin-left: 8px;
  color: #666;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .tracks-grid {
    grid-template-columns: 1fr;
  }
  
  .track-item {
    padding: 12px;
  }
  
  .track-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .match-details {
    flex-direction: column;
    gap: 4px;
  }
  
  .parameter-preview {
    flex-direction: column;
    gap: 4px;
  }
}
</style>
