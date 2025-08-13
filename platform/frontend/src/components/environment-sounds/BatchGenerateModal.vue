<template>
  <a-drawer
    :open="open"
    title="批量生成环境音确认"
    width="700px"
    placement="right"
    @close="handleCancel"
  >
    <div class="batch-generate-drawer">
      <!-- 生成概览 -->
      <div class="generate-overview">
        <a-alert
          message="生成计划确认"
          description="请确认以下环境音生成计划，生成后将无法撤销"
          type="info"
          show-icon
          style="margin-bottom: 16px"
        />
        
        <div class="overview-stats">
          <a-row :gutter="16">
            <a-col :span="6">
              <div class="stat-card">
                <div class="stat-number">{{ needGenerationCount }}</div>
                <div class="stat-label">需生成数量</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-card">
                <div class="stat-number">{{ estimatedTime }}</div>
                <div class="stat-label">预估时间</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-card">
                <div class="stat-number">{{ uniqueKeywords }}</div>
                <div class="stat-label">唯一关键词</div>
              </div>
            </a-col>
            <a-col :span="6">
              <div class="stat-card">
                <div class="stat-number">{{ totalDuration }}</div>
                <div class="stat-label">总时长</div>
              </div>
            </a-col>
          </a-row>
        </div>
      </div>

      <!-- 生成列表 -->
      <div class="generate-list">
        <div class="section-title">
          <SoundOutlined />
          生成列表
        </div>
        
        <div class="generate-items">
          <div 
            v-for="track in needGenerationTracks" 
            :key="track.segment_id"
            class="generate-item"
          >
            <div class="item-header">
              <div class="item-info">
                <div class="item-name">
                  {{ track.environment_keywords.join('_') }}
                </div>
                <div class="item-time">
                  {{ formatTime(track.start_time) }} - {{ formatTime(track.start_time + track.duration) }}
                </div>
              </div>
              <div class="item-actions">
                <a-button 
                  type="link" 
                  size="small"
                  @click="editTrack(track)"
                >
                  编辑
                </a-button>
              </div>
            </div>
            
            <div class="item-details">
              <div class="detail-row">
                <span class="label">场景描述：</span>
                <span class="value">{{ track.scene_description || '无' }}</span>
              </div>
              <div class="detail-row">
                <span class="label">生成时长：</span>
                <span class="value">{{ track.suggested_duration || track.duration }}秒</span>
              </div>
              <div class="detail-row">
                <span class="label">强度等级：</span>
                <span class="value">{{ track.intensity_level || 'medium' }}</span>
              </div>
              <div class="detail-row">
                <span class="label">置信度：</span>
                <span class="value">{{ (track.confidence * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 生成选项 -->
      <div class="generate-options">
        <div class="section-title">
          <SettingOutlined />
          生成选项
        </div>
        
        <a-form :model="generateOptions" layout="vertical">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-form-item label="默认强度等级">
                <a-select v-model:value="generateOptions.defaultIntensity">
                  <a-select-option value="low">低强度</a-select-option>
                  <a-select-option value="medium">中等强度</a-select-option>
                  <a-select-option value="high">高强度</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            <a-col :span="12">
              <a-form-item label="最大并发数">
                <a-input-number
                  v-model:value="generateOptions.maxConcurrent"
                  :min="1"
                  :max="5"
                  style="width: 100%"
                />
                <span class="unit">个</span>
              </a-form-item>
            </a-col>
          </a-row>
          
          <a-form-item label="生成质量">
            <a-radio-group v-model:value="generateOptions.quality">
              <a-radio value="fast">快速生成 (质量较低)</a-radio>
              <a-radio value="standard">标准生成 (推荐)</a-radio>
              <a-radio value="high">高质量生成 (时间较长)</a-radio>
            </a-radio-group>
          </a-form-item>
          
          <a-form-item label="生成策略">
            <a-checkbox v-model:checked="generateOptions.parallelGeneration">
              并行生成 (同时生成多个，速度更快)
            </a-checkbox>
            <a-checkbox v-model:checked="generateOptions.autoRetry">
              自动重试 (生成失败时自动重试)
            </a-checkbox>
          </a-form-item>
        </a-form>
      </div>

     
    </div>

    <!-- 抽屉底部按钮 -->
    <template #footer>
      <div class="drawer-footer">
        <a-space>
          <a-button @click="handleCancel">
            取消
          </a-button>
          <a-button 
            type="primary" 
            :loading="confirmLoading"
            @click="handleConfirm"
          >
            确认生成
          </a-button>
        </a-space>
      </div>
    </template>

    <!-- 编辑轨道对话框 -->
    <a-modal
      v-model:open="showEditModal"
      title="编辑生成参数"
      width="500px"
      @ok="confirmEdit"
      @cancel="cancelEdit"
    >
      <div v-if="editingTrack" class="edit-form">
        <a-form :model="editForm" layout="vertical">
          <a-form-item label="环境音名称">
            <a-input 
              v-model:value="editForm.name"
              placeholder="请输入环境音名称"
            />
          </a-form-item>
          
          <a-form-item label="生成时长">
            <a-input-number
              v-model:value="editForm.duration"
              :min="1"
              :max="300"
              style="width: 100%"
            />
            <span class="unit">秒</span>
            <div class="form-tip">建议时长：{{ editingTrack?.duration || 30 }}秒</div>
          </a-form-item>
          
          <a-form-item label="强度等级">
            <a-select v-model:value="editForm.intensity">
              <a-select-option value="low">低强度</a-select-option>
              <a-select-option value="medium">中等强度</a-select-option>
              <a-select-option value="high">高强度</a-select-option>
            </a-select>
          </a-form-item>
          
          <a-form-item label="生成提示词">
            <a-textarea
              v-model:value="editForm.prompt"
              :rows="3"
              placeholder="请输入生成提示词"
            />
          </a-form-item>
        </a-form>
      </div>
    </a-modal>
  </a-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { 
  SoundOutlined,
  SettingOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  open: {
    type: Boolean,
    default: false
  },
  selectedTracks: {
    type: Set,
    default: () => new Set()
  },
  analysisResult: {
    type: Object,
    default: null
  }
})

// Emits
const emit = defineEmits(['update:open', 'confirm'])

// 响应式数据
const confirmLoading = ref(false)
const showEditModal = ref(false)
const editingTrack = ref(null)
const editForm = ref({
  name: '',
  duration: 30,
  intensity: 'medium',
  prompt: ''
})

const generateOptions = ref({
  defaultIntensity: 'medium',
  quality: 'standard',
  parallelGeneration: true,
  autoRetry: true,
  maxConcurrent: 2
})

// 计算属性
const needGenerationTracks = computed(() => {
  if (!props.analysisResult) return []
  
  return props.analysisResult.environment_tracks?.filter(track => 
    props.selectedTracks.has(track.segment_id) && !track.has_match
  ) || []
})

const needGenerationCount = computed(() => needGenerationTracks.value.length)

const estimatedTime = computed(() => {
  const minutes = Math.ceil(needGenerationCount.value * 0.5)
  if (minutes < 60) {
    return `${minutes}分钟`
  } else {
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return `${hours}小时${remainingMinutes}分钟`
  }
})

const uniqueKeywords = computed(() => {
  const keywords = new Set()
  needGenerationTracks.value.forEach(track => {
    track.environment_keywords?.forEach(keyword => keywords.add(keyword))
  })
  return keywords.size
})

const totalDuration = computed(() => {
  const total = needGenerationTracks.value.reduce((sum, track) => {
    return sum + (track.suggested_duration || track.duration)
  }, 0)
  return `${Math.ceil(total / 60)}分钟`
})

// 方法
const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}

const handleConfirm = async () => {
  if (needGenerationCount.value === 0) {
    message.warning('没有需要生成的环境音')
    return
  }
  
  confirmLoading.value = true
  
  try {
    // 构建生成计划
    const generationPlan = {
      tracks: needGenerationTracks.value.map(track => ({
        segment_id: track.segment_id,
        name: track.environment_keywords.join('_'),
        duration: track.suggested_duration || track.duration, // 使用轨道自己的时长
        intensity: track.intensity_level || generateOptions.value.defaultIntensity,
        prompt: `生成${track.environment_keywords.join('、')}环境音，场景：${track.scene_description}`,
        keywords: track.environment_keywords,
        scene_description: track.scene_description
      })),
      options: {
        max_concurrent: generateOptions.value.maxConcurrent,
        quality: generateOptions.value.quality,
        auto_retry: generateOptions.value.autoRetry
      }
    }
    
    emit('confirm', generationPlan)
    emit('update:open', false)
    
  } catch (error) {
    console.error('确认生成失败:', error)
    message.error('确认生成失败: ' + error.message)
  } finally {
    confirmLoading.value = false
  }
}

const handleCancel = () => {
  emit('update:open', false)
}

const editTrack = (track) => {
  editingTrack.value = track
  editForm.value = {
    name: track.environment_keywords.join('_'),
    duration: track.suggested_duration || track.duration,
    intensity: track.intensity_level || 'medium',
    prompt: `生成${track.environment_keywords.join('、')}环境音，场景：${track.scene_description}`
  }
  showEditModal.value = true
}

const confirmEdit = () => {
  if (!editingTrack.value) return
  
  // 更新轨道参数
  Object.assign(editingTrack.value, {
    suggested_duration: editForm.value.duration,
    intensity_level: editForm.value.intensity,
    custom_prompt: editForm.value.prompt
  })
  
  showEditModal.value = false
  message.success('参数已更新')
}

const cancelEdit = () => {
  showEditModal.value = false
}

// 监听visible变化
watch(() => props.open, (newVal) => {
  if (newVal) {
    // 重置生成选项
    generateOptions.value = {
      defaultIntensity: 'medium',
      quality: 'standard',
      parallelGeneration: true,
      autoRetry: true,
      maxConcurrent: 2
    }
  }
})
</script>

<style scoped>
.batch-generate-drawer {
  max-height: 600px;
  overflow-y: auto;
}

.generate-overview {
  margin-bottom: 24px;
}

.overview-stats {
  margin-top: 16px;
}

.stat-card {
  text-align: center;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.stat-number {
  font-size: 20px;
  font-weight: 600;
  color: #1890ff;
  margin-bottom: 4px;
}

.stat-label {
  font-size: 12px;
  color: #666;
}

.generate-list,
.generate-options {
  margin-bottom: 24px;
}

.section-title {
  display: flex;
  align-items: center;
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin-bottom: 16px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.section-title .anticon {
  margin-right: 8px;
  color: #1890ff;
}

.generate-items {
  max-height: 300px;
  overflow-y: auto;
}

.generate-item {
  border: 1px solid #e9ecef;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
  background: white;
}

.item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.item-name {
  font-weight: 500;
  color: #333;
  margin-bottom: 4px;
}

.item-time {
  font-size: 12px;
  color: #666;
}

.item-details {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
}

.detail-row {
  display: flex;
  align-items: center;
}

.label {
  font-size: 12px;
  color: #666;
  margin-right: 4px;
  min-width: 60px;
}

.value {
  font-size: 12px;
  color: #333;
}

.generate-notice {
  margin-top: 24px;
}

.notice-list {
  margin: 0;
  padding-left: 16px;
}

.notice-list li {
  margin-bottom: 4px;
  font-size: 14px;
}

.unit {
  margin-left: 8px;
  color: #666;
}

.edit-form {
  padding: 8px 0;
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .overview-stats .ant-col {
    margin-bottom: 12px;
  }
  
  .item-details {
    grid-template-columns: 1fr;
  }
  
  .detail-row {
    margin-bottom: 4px;
  }
}
</style>
