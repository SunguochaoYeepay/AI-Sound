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
        <a-card title="中文提示词" size="small" style="margin-top: 16px">
          <div class="prompt-section">
            <div v-if="!editingPrompt" class="prompt-display chinese-prompt">
              {{ task.generated_prompt_chinese || '暂无中文提示词' }}
            </div>
            <a-textarea
              v-else
              v-model:value="editablePrompt.generated_prompt_chinese"
              :rows="4"
              placeholder="请输入中文提示词，保存时将自动翻译为英文"
            />
          </div>
          
          <a-space style="margin-top: 8px">
            <a-button 
              v-if="!editingPrompt"
              size="small" 
              @click="startEditPrompt"
            >
              编辑提示词
            </a-button>
            <a-button 
              v-else
              size="small" 
              type="primary"
              @click="savePrompt"
            >
              保存
            </a-button>
            <a-button 
              v-if="editingPrompt"
              size="small" 
              @click="cancelEditPrompt"
            >
              取消
            </a-button>
            <a-button 
              size="small" 
              @click="copyToClipboard(task.generated_prompt_chinese)"
              v-if="task.generated_prompt_chinese && !editingPrompt"
            >
              复制中文提示词
            </a-button>
          </a-space>
        </a-card>

        
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
              <div class="style-keywords-container">
                <div class="keywords-grid">
                  <a-tag 
                    v-for="keyword in processedStyleKeywords" 
                    :key="keyword"
                    class="style-keyword-tag"
                    :color="getKeywordColor(keyword)"
                  >
                    {{ keyword }}
                  </a-tag>
                </div>
                <span v-if="processedStyleKeywords.length === 0" class="no-keywords">
                  暂无风格关键词
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
          v-if="parsedCharacterInfo && Object.keys(parsedCharacterInfo).length > 0"
        >
          <div class="character-info">
            <a-descriptions :column="1" size="small">
              <a-descriptions-item 
                v-for="(character, index) in formattedCharacterInfo" 
                :key="index"
                :label="character.name || `角色 ${index + 1}`"
              >
                <div v-if="character.description">
                  <div><strong>描述:</strong> {{ character.description }}</div>
                </div>
                <div v-if="character.appearance">
                  <div><strong>外观:</strong> {{ character.appearance }}</div>
                </div>
                <div v-if="character.personality">
                  <div><strong>性格:</strong> {{ character.personality }}</div>
                </div>
                <div v-if="character.age">
                  <div><strong>年龄:</strong> {{ character.age }}</div>
                </div>
                <div v-if="character.gender">
                  <div><strong>性别:</strong> {{ character.gender }}</div>
                </div>
                <!-- 显示其他属性 -->
                <div v-for="(value, key) in character.otherProps" :key="key">
                  <div><strong>{{ key }}:</strong> {{ value }}</div>
                </div>
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
              @click="onGenerate"
              :loading="generating"
            >
              {{ task.status === 'failed' ? '重新生成' : '开始生成' }}
            </a-button>
            
            <!-- 为已完成的任务添加重新生成按钮 -->
            <a-button 
              v-if="task.status === 'completed'"
              type="primary"
              @click="onRegenerate"
              :loading="generating"
            >
              重新生成
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
import { ref, watch, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useImageGenerationStore } from '@/stores/imageGeneration'

// Props
const props = defineProps({
  task: {
    type: Object,
    required: true
  }
})

// Emits
const emit = defineEmits(['update', 'close', 'refresh'])

// Store
const imageStore = useImageGenerationStore()

// Reactive data
const loading = ref(false)
const userRating = ref(0)
const generating = ref(false)
const editingPrompt = ref(false)
const editablePrompt = ref({
  original_prompt: '',
  generated_prompt: '',
  generated_prompt_chinese: ''
})

// Computed properties
const processedStyleKeywords = computed(() => {
  if (!props.task.style_keywords) return []
  
  let keywords = []
  
  if (typeof props.task.style_keywords === 'string') {
    keywords = props.task.style_keywords.split(',').map(k => k.trim()).filter(k => k.length > 0)
  } else if (Array.isArray(props.task.style_keywords)) {
    keywords = props.task.style_keywords.filter(k => k && k.trim().length > 0)
  }
  
  return keywords
})

const parsedCharacterInfo = computed(() => {
  if (!props.task.character_info) return null
  
  try {
    // 如果character_info是字符串，尝试解析JSON
    if (typeof props.task.character_info === 'string') {
      return JSON.parse(props.task.character_info)
    }
    // 如果已经是对象，直接返回
    return props.task.character_info
  } catch (error) {
    console.warn('解析角色信息失败:', error)
    return null
  }
})

const formattedCharacterInfo = computed(() => {
  if (!parsedCharacterInfo.value) return []
  
  // 如果是数组，直接处理
  if (Array.isArray(parsedCharacterInfo.value)) {
    return parsedCharacterInfo.value.map(character => formatCharacter(character))
  }
  
  // 如果是对象，转换为数组
  if (typeof parsedCharacterInfo.value === 'object') {
    return Object.entries(parsedCharacterInfo.value).map(([name, info]) => {
      if (typeof info === 'object') {
        return formatCharacter({ name, ...info })
      } else {
        return formatCharacter({ name, description: info })
      }
    })
  }
  
  return []
})

const formatCharacter = (character) => {
  const knownProps = ['name', 'description', 'appearance', 'personality', 'age', 'gender']
  const otherProps = {}
  
  // 分离已知属性和其他属性
  Object.keys(character).forEach(key => {
    if (!knownProps.includes(key)) {
      otherProps[key] = character[key]
    }
  })
  
  return {
    name: character.name,
    description: character.description,
    appearance: character.appearance,
    personality: character.personality,
    age: character.age,
    gender: character.gender,
    otherProps
  }
}

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

const getKeywordColor = (keyword) => {
  const colorMap = {
    'cinematic': 'orange',
    'historical': 'gold',
    'portrait': 'blue',
    'fantasy': 'purple',
    'anime': 'pink',
    'realistic': 'green',
    'artistic': 'cyan',
    'modern': 'geekblue',
    'vintage': 'volcano',
    'elegant': 'magenta',
    'dramatic': 'red',
    'soft': 'lime',
    'vibrant': 'gold',
    'dark': 'black',
    'bright': 'yellow',
    'warm': 'orange',
    'cool': 'blue',
    'neutral': 'default'
  }
  
  const lowerKeyword = keyword.toLowerCase()
  for (const [key, color] of Object.entries(colorMap)) {
    if (lowerKeyword.includes(key)) {
      return color
    }
  }
  
  // 根据关键词内容动态生成颜色
  const colors = ['blue', 'green', 'cyan', 'purple', 'pink', 'orange', 'gold', 'geekblue', 'magenta', 'volcano', 'lime', 'yellow']
  const hash = keyword.split('').reduce((acc, char) => acc + char.charCodeAt(0), 0)
  return colors[hash % colors.length]
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

const startEditPrompt = () => {
  editingPrompt.value = true
  editablePrompt.value = {
    original_prompt: props.task.original_prompt || '',
    generated_prompt: props.task.generated_prompt || '',
    generated_prompt_chinese: props.task.generated_prompt_chinese || ''
  }
}

const cancelEditPrompt = () => {
  editingPrompt.value = false
  editablePrompt.value = {
    original_prompt: '',
    generated_prompt: '',
    generated_prompt_chinese: ''
  }
}

const savePrompt = async () => {
  try {
    loading.value = true
    
    // 检查是否有中文提示词需要翻译
    const updateData = {
      original_prompt: editablePrompt.value.original_prompt
    }
    
    // 如果有中文提示词，则发送中文提示词进行自动翻译
    if (editablePrompt.value.generated_prompt_chinese && editablePrompt.value.generated_prompt_chinese.trim()) {
      updateData.generated_prompt_chinese = editablePrompt.value.generated_prompt_chinese
      updateData.auto_translate = true
      message.loading('正在翻译中文提示词...', 0)
    } else {
      // 如果没有中文提示词，直接更新英文提示词
      updateData.generated_prompt = editablePrompt.value.generated_prompt
    }
    
    // 调用API更新提示词
    await imageStore.updateTaskPrompt(props.task.id, updateData)
    
    message.destroy() // 清除loading消息
    message.success('提示词更新成功')
    editingPrompt.value = false
    emit('refresh')
  } catch (error) {
    message.destroy() // 清除loading消息
    console.error('更新提示词失败:', error)
    message.error('更新提示词失败')
  } finally {
    loading.value = false
  }
}

const onGenerate = async () => {
  try {
    generating.value = true
    await imageStore.generateSingleImage(props.task.id)
    message.success('生成请求已提交')
    emit('refresh')
  } catch (error) {
    console.error('生成失败:', error)
    message.error('生成失败')
  } finally {
    generating.value = false
  }
}

const onRegenerate = async () => {
  try {
    generating.value = true
    await imageStore.regenerateImage(props.task.id)
    message.success('重新生成请求已提交')
    emit('refresh')
  } catch (error) {
    console.error('重新生成失败:', error)
    message.error('重新生成失败')
  } finally {
    generating.value = false
  }
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
  
  .prompt-section {
    margin-bottom: 12px;
    
    &:last-child {
      margin-bottom: 0;
    }
  }
  
  .prompt-label {
    font-weight: 600;
    color: #333;
    margin-bottom: 6px;
    font-size: 13px;
  }
  
  .original-prompt {
    background: #e6f7ff;
    border-color: #91d5ff;
  }
  
  .chinese-prompt {
    background: #f6ffed;
    border-color: #b7eb8f;
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  }
  
  .prompt-hint {
    margin-top: 8px;
  }
  
  .tags-display {
    min-height: 32px;
    line-height: 1.4;
  }
  
  .analysis-content {
    min-height: 40px;
    line-height: 1.4;
  }

  .style-keywords-container {
    min-height: 40px;
    
    .keywords-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      align-items: flex-start;
    }
    
    .style-keyword-tag {
      margin: 0;
      padding: 4px 8px;
      font-size: 12px;
      border-radius: 12px;
      transition: all 0.2s ease;
      
      &:hover {
        transform: translateY(-1px);
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
      }
    }
    
    .no-keywords {
      color: #999;
      font-size: 12px;
      font-style: italic;
    }
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

/* 暗黑模式适配 */
[data-theme='dark'] .image-task-detail {
  .segment-text {
    background: #1f1f1f;
    color: #d9d9d9;
    border: 1px solid #434343;
  }
  
  .prompt-display {
    background: #1f1f1f;
    color: #d9d9d9;
    border: 1px solid #434343;
  }
  
  .original-prompt {
    background: #111b26;
    border-color: #177ddc;
  }
  
  .style-keywords-container {
    .keywords-grid {
      .style-keyword-tag {
        &:hover {
          box-shadow: 0 2px 4px rgba(255, 255, 255, 0.1);
        }
      }
      
      .no-keywords {
        color: #8c8c8c;
      }
    }
  }
  
  .character-info {
    :deep(.ant-descriptions-item-label) {
      color: #177ddc;
    }
  }
}

[data-theme='dark'] .preview-content .prompt-display {
  background: #1f1f1f;
  color: #d9d9d9;
  border: 1px solid #434343;
}
</style>