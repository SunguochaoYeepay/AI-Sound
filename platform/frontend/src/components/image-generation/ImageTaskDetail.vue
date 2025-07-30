<template>
  <div class="image-task-detail">
    <a-spin :spinning="loading">
      <div v-if="task">
        <!-- 基本信息 -->
        <a-descriptions 
          title="任务基本信息" 
          :column="2" 
          bordered
          size="small"
        >
          <a-descriptions-item label="任务ID">
            {{ task.id }}
          </a-descriptions-item>
          <a-descriptions-item label="段落索引">
            第 {{ task.segment_index + 1 }} 段
          </a-descriptions-item>
          <a-descriptions-item label="段落类型">
            <a-tag :color="getTypeColor(task.segment_type)">
              {{ getTypeText(task.segment_type) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="状态">
            <a-tag :color="getStatusColor(task.status)">
              {{ getStatusText(task.status) }}
            </a-tag>
          </a-descriptions-item>
          <a-descriptions-item label="创建时间">
            {{ formatDateTime(task.created_at) }}
          </a-descriptions-item>
          <a-descriptions-item label="完成时间">
            {{ formatDateTime(task.completed_at) || '未完成' }}
          </a-descriptions-item>
        </a-descriptions>
        
        <!-- 段落原文 -->
        <a-card title="段落原文" size="small" style="margin-top: 16px">
          <div class="segment-text">
            {{ task.segment_text }}
          </div>
        </a-card>
        
        <!-- 生成的图片 -->
        <a-card 
          title="生成结果" 
          size="small" 
          style="margin-top: 16px"
          v-if="task.generated_image_url"
        >
          <div class="image-result">
            <a-image
              :src="task.generated_image_url"
              :width="'100%'"
              style="max-width: 400px; border-radius: 8px"
            />
            
            <div class="image-info" style="margin-top: 12px">
              <a-descriptions :column="3" size="small">
                <a-descriptions-item label="尺寸">
                  {{ task.image_width }}×{{ task.image_height }}
                </a-descriptions-item>
                <a-descriptions-item label="生成时间">
                  {{ task.generation_time }}秒
                </a-descriptions-item>
                <a-descriptions-item label="生成种子">
                  {{ task.generation_seed }}
                </a-descriptions-item>
              </a-descriptions>
            </div>
          </div>
        </a-card>
        
        <!-- 提示词信息 -->
        <a-row :gutter="16" style="margin-top: 16px">
          <a-col :span="12">
            <a-card title="正面提示词" size="small">
              <div class="prompt-display">
                {{ task.generated_prompt || '暂无' }}
              </div>
              <a-button 
                size="small" 
                @click="copyToClipboard(task.generated_prompt)"
                style="margin-top: 8px"
                v-if="task.generated_prompt"
              >
                复制提示词
              </a-button>
            </a-card>
          </a-col>
          
          <a-col :span="12">
            <a-card title="负面提示词" size="small">
              <div class="prompt-display">
                {{ task.negative_prompt || '暂无' }}
              </div>
              <a-button 
                size="small" 
                @click="copyToClipboard(task.negative_prompt)"
                style="margin-top: 8px"
                v-if="task.negative_prompt"
              >
                复制提示词
              </a-button>
            </a-card>
          </a-col>
        </a-row>
        
        <!-- 分析结果 -->
        <a-row :gutter="16" style="margin-top: 16px">
          <a-col :span="8">
            <a-card title="场景描述" size="small">
              <div class="analysis-content">
                {{ task.scene_description || '暂无' }}
              </div>
            </a-card>
          </a-col>
          
          <a-col :span="8">
            <a-card title="情感色调" size="small">
              <div class="analysis-content">
                <a-tag 
                  v-if="task.emotional_tone"
                  :color="getEmotionColor(task.emotional_tone)"
                >
                  {{ task.emotional_tone }}
                </a-tag>
                <span v-else>暂无</span>
              </div>
            </a-card>
          </a-col>
          
          <a-col :span="8">
            <a-card title="风格关键词" size="small">
              <div class="analysis-content">
                <a-tag 
                  v-for="keyword in (task.style_keywords || [])" 
                  :key="keyword"
                  style="margin-bottom: 4px"
                >
                  {{ keyword }}
                </a-tag>
                <span v-if="!task.style_keywords || task.style_keywords.length === 0">
                  暂无
                </span>
              </div>
            </a-card>
          </a-col>
        </a-row>
        
        <!-- 角色信息 -->
        <a-card 
          title="角色信息" 
          size="small" 
          style="margin-top: 16px"
          v-if="task.character_info && Object.keys(task.character_info).length > 0"
        >
          <div class="character-info">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item 
                v-for="(description, name) in task.character_info" 
                :key="name"
                :label="name"
              >
                {{ description }}
              </a-descriptions-item>
            </a-descriptions>
          </div>
        </a-card>
        
        <!-- 用户评价 -->
        <a-card 
          title="用户评价" 
          size="small" 
          style="margin-top: 16px"
          v-if="task.status === 'completed'"
        >
          <div class="user-evaluation">
            <div class="rating-section">
              <span style="margin-right: 8px">用户评分:</span>
              <a-rate
                v-model:value="userRating"
                :count="5"
                @change="onRatingChange"
              />
              <span style="margin-left: 8px; color: #666">
                {{ userRating ? `${userRating}/5` : '未评分' }}
              </span>
            </div>
            
            <div class="approval-section" style="margin-top: 12px">
              <span style="margin-right: 8px">审核状态:</span>
              <a-tag 
                v-if="task.is_approved !== null"
                :color="task.is_approved ? 'green' : 'red'"
              >
                {{ task.is_approved ? '已通过' : '已拒绝' }}
              </a-tag>
              <span v-else>待审核</span>
              
              <a-space style="margin-left: 16px">
                <a-button 
                  size="small" 
                  type="primary"
                  @click="onApprove(true)"
                  :disabled="task.is_approved === true"
                >
                  通过
                </a-button>
                <a-button 
                  size="small" 
                  danger
                  @click="onApprove(false)"
                  :disabled="task.is_approved === false"
                >
                  拒绝
                </a-button>
              </a-space>
            </div>
          </div>
        </a-card>
        
        <!-- 生成参数 -->
        <a-card 
          title="生成参数" 
          size="small" 
          style="margin-top: 16px"
          v-if="task.generation_params"
        >
          <a-descriptions :column="3" size="small">
            <a-descriptions-item 
              v-for="(value, key) in task.generation_params" 
              :key="key"
              :label="getParamLabel(key)"
            >
              {{ value }}
            </a-descriptions-item>
          </a-descriptions>
        </a-card>
        
        <!-- 错误信息 -->
        <a-card 
          title="错误信息" 
          size="small" 
          style="margin-top: 16px"
          v-if="task.status === 'failed' && task.error_message"
        >
          <a-alert
            :message="task.error_message"
            type="error"
            show-icon
          />
        </a-card>
        
        <!-- 操作按钮 -->
        <div class="action-buttons" style="margin-top: 24px; text-align: center">
          <a-space>
            <a-button 
              v-if="task.status === 'pending' || task.status === 'failed'"
              type="primary"
              @click="onRegenerate"
            >
              {{ task.status === 'failed' ? '重新生成' : '开始生成' }}
            </a-button>
            
            <a-button 
              v-if="task.generated_image_url"
              @click="downloadImage"
            >
              下载图片
            </a-button>
            
            <a-button @click="onRefresh">
              刷新数据
            </a-button>
            
            <a-button danger @click="onDelete">
              删除任务
            </a-button>
          </a-space>
        </div>
      </div>
    </a-spin>
  </div>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'

// Props
const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

// Emits
const emit = defineEmits(['update', 'close'])

// Reactive data
const loading = ref(false)
const userRating = ref(0)

// Methods
const getStatusColor = (status) => {
  const colors = {
    pending: 'default',
    processing: 'blue',
    completed: 'green',
    failed: 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const getTypeColor = (type) => {
  const colors = {
    dialogue: 'blue',
    narrative: 'green',
    description: 'orange'
  }
  return colors[type] || 'default'
}

const getTypeText = (type) => {
  const texts = {
    dialogue: '对话',
    narrative: '叙述',
    description: '描述'
  }
  return texts[type] || type
}

const getEmotionColor = (emotion) => {
  const colors = {
    happy: 'gold',
    sad: 'blue',
    angry: 'red',
    peaceful: 'green',
    mysterious: 'purple',
    romantic: 'pink',
    epic: 'orange',
    dark: 'black'
  }
  return colors[emotion] || 'default'
}

const getParamLabel = (key) => {
  const labels = {
    steps: '采样步数',
    cfg: 'CFG强度',
    sampler_name: '采样器',
    scheduler: '调度器',
    denoise: '去噪强度',
    seed: '随机种子'
  }
  return labels[key] || key
}

const formatDateTime = (dateString) => {
  if (!dateString) return null
  return new Date(dateString).toLocaleString()
}

const copyToClipboard = async (text) => {
  if (!text) return
  
  try {
    await navigator.clipboard.writeText(text)
    message.success('已复制到剪贴板')
  } catch (error) {
    message.error('复制失败: ' + error.message)
  }
}

const downloadImage = () => {
  if (!props.task.generated_image_url) return
  
  try {
    const link = document.createElement('a')
    link.href = props.task.generated_image_url
    link.download = `image_${props.task.id}`
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    message.success('图片下载开始')
  } catch (error) {
    message.error('下载失败: ' + error.message)
  }
}

const onRatingChange = (value) => {
  emit('update', {
    type: 'rating',
    taskId: props.task.id,
    value: value
  })
}

const onApprove = (approved) => {
  emit('update', {
    type: 'approve',
    taskId: props.task.id,
    value: approved
  })
}

const onRegenerate = () => {
  emit('update', {
    type: 'regenerate',
    taskId: props.task.id
  })
}

const onRefresh = () => {
  emit('update', {
    type: 'refresh',
    taskId: props.task.id
  })
}

const onDelete = () => {
  emit('update', {
    type: 'delete',
    taskId: props.task.id
  })
}

// Watch for task changes
watch(() => props.task, (newTask) => {
  if (newTask) {
    userRating.value = newTask.user_rating || 0
  }
}, { immediate: true })
</script>

<style scoped>
.image-task-detail {
  .segment-text {
    background: #f5f5f5;
    padding: 12px;
    border-radius: 6px;
    line-height: 1.6;
    font-size: 14px;
  }
  
  .prompt-display {
    background: #f8f9fa;
    padding: 10px;
    border-radius: 4px;
    font-size: 12px;
    line-height: 1.5;
    max-height: 150px;
    overflow-y: auto;
    border: 1px solid #e8e8e8;
  }
  
  .analysis-content {
    min-height: 40px;
    line-height: 1.4;
  }
  
  .character-info {
    .ant-descriptions-item-label {
      font-weight: 600;
      color: #1890ff;
    }
  }
  
  .user-evaluation {
    .rating-section {
      display: flex;
      align-items: center;
    }
    
    .approval-section {
      display: flex;
      align-items: center;
    }
  }
  
  .image-result {
    text-align: center;
  }
}

:deep(.ant-descriptions-item-label) {
  font-weight: 500;
  width: 120px;
}

:deep(.ant-card-head-title) {
  font-size: 14px;
  font-weight: 600;
}

:deep(.ant-card-body) {
  padding: 12px;
}
</style> 