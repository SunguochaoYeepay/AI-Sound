<template>
  <a-drawer
    :open="visible"
    title="环境音详情"
    width="600px"
    placement="right"
    @close="handleClose"
    @update:open="$emit('update:visible', $event)"
  >
    <!-- 基本信息 -->
    <div class="info-section">
      <h3>基本信息</h3>
      <a-descriptions :column="2" bordered>
        <a-descriptions-item label="环境音名称">
          <a-tag color="blue">{{ soundInfo.name || '未命名' }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="类型分类">
          <a-tag :color="getCategoryColor(soundInfo.category)">
            {{ soundInfo.category || '未分类' }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="描述信息" :span="2">
          {{ soundInfo.description || '暂无描述' }}
        </a-descriptions-item>
        <a-descriptions-item label="来源">
          <a-tag color="green">{{ soundInfo.source || '书籍分析' }}</a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="章节">
          第{{ soundInfo.chapter_number || '?' }}章
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <!-- 生成参数 -->
    <div class="params-section">
      <h3>生成参数</h3>
      <a-form :model="soundParams" layout="vertical">
        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="时长设置">
              <a-input-number 
                v-model:value="soundParams.duration" 
                :min="1" 
                :max="300" 
                addon-after="秒"
                :disabled="generating"
              />
            </a-form-item>
          </a-col>
          <a-col :span="12">
            <a-form-item label="强度等级">
              <a-select 
                v-model:value="soundParams.intensity"
                :disabled="generating"
              >
                <a-select-option value="low">低</a-select-option>
                <a-select-option value="medium">中</a-select-option>
                <a-select-option value="high">高</a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>
        <a-form-item label="音量控制">
          <a-slider 
            v-model:value="soundParams.volume" 
            :min="0" 
            :max="100"
            :disabled="generating"
          />
          <div class="slider-label">{{ soundParams.volume }}%</div>
        </a-form-item>
        <a-form-item label="循环设置">
          <a-switch 
            v-model:checked="soundParams.loop"
            :disabled="generating"
          />
          <span class="switch-label">{{ soundParams.loop ? '循环播放' : '单次播放' }}</span>
        </a-form-item>
      </a-form>
    </div>

    <!-- 生成状态 -->
    <div class="status-section">
      <h3>生成状态</h3>
      <a-steps :current="generationStep" size="small">
        <a-step title="准备中" />
        <a-step title="生成中" />
        <a-step title="完成" />
      </a-steps>
      
      <div v-if="generationProgress > 0" class="progress-section">
        <a-progress 
          :percent="generationProgress" 
          :status="generationStatus === 'failed' ? 'exception' : 'active'"
        />
        <p class="progress-text">{{ generationStatusText }}</p>
      </div>

      <div v-if="generationLogs.length > 0" class="logs-section">
        <h4>生成日志</h4>
        <div class="logs-container">
          <div 
            v-for="(log, index) in generationLogs" 
            :key="index"
            class="log-item"
            :class="log.type"
          >
            <span class="log-time">{{ log.time }}</span>
            <span class="log-message">{{ log.message }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 操作按钮 -->
    <div class="actions-section">
      <a-space>
        <a-button 
          type="primary" 
          @click="generateSound" 
          :loading="generating"
          :disabled="!canGenerate"
        >
          {{ hasGenerated ? '重新生成' : '生成环境音' }}
        </a-button>
        <a-button 
          @click="playSound" 
          :disabled="!hasGenerated || playing"
          :loading="playing"
        >
          {{ playing ? '播放中...' : '播放' }}
        </a-button>
        <a-button 
          @click="downloadSound" 
          :disabled="!hasGenerated"
        >
          下载
        </a-button>
        <a-button 
          danger
          @click="deleteSound"
          :disabled="!hasGenerated"
        >
          删除
        </a-button>
      </a-space>
    </div>

    <!-- 预览功能 -->
    <div v-if="hasGenerated" class="preview-section">
      <h3>音频预览</h3>
      <div class="waveform-container">
        <div class="waveform-placeholder">
          <SoundOutlined style="font-size: 24px; color: #1890ff;" />
          <p>音频波形图</p>
          <p class="audio-info">
            时长: {{ soundInfo.duration }}秒 | 
            文件大小: {{ soundInfo.fileSize }}MB | 
            质量: {{ soundInfo.quality }}
          </p>
        </div>
      </div>
      
      <div class="audio-controls">
        <a-space>
          <a-button 
            size="small" 
            @click="playSound"
            :disabled="playing"
            :loading="playing"
          >
            {{ playing ? '播放中...' : '播放' }}
          </a-button>
          <a-button 
            size="small" 
            @click="pauseSound"
            :disabled="!playing"
          >
            暂停
          </a-button>
          <a-button 
            size="small" 
            @click="stopSound"
            :disabled="!playing"
          >
            停止
          </a-button>
        </a-space>
      </div>
    </div>

    <!-- 模板区域 -->
    <div class="template-section">
      <h3>保存为模板</h3>
      <a-form layout="inline">
        <a-form-item>
          <a-input 
            v-model:value="templateName" 
            placeholder="模板名称"
            style="width: 200px"
          />
        </a-form-item>
        <a-form-item>
          <a-button @click="saveAsTemplate" :disabled="!templateName">
            保存模板
          </a-button>
        </a-form-item>
      </a-form>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { SoundOutlined } from '@ant-design/icons-vue'
import { environmentGenerationAPI } from '@/api'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  soundInfo: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:visible', 'refresh'])

// 响应式数据
const soundParams = ref({
  duration: 30,
  intensity: 'medium',
  volume: 50,
  loop: false
})

const generating = ref(false)
const playing = ref(false)
const generationProgress = ref(0)
const generationStatus = ref('pending')
const generationLogs = ref([])
const templateName = ref('')

// 计算属性
const hasGenerated = computed(() => {
  return soundInfo.value.status === 'completed' && soundInfo.value.audioUrl
})

const canGenerate = computed(() => {
  return !generating.value && soundInfo.value.keyword
})

const generationStep = computed(() => {
  if (generationStatus.value === 'pending') return 0
  if (generationStatus.value === 'generating') return 1
  if (generationStatus.value === 'completed') return 2
  if (generationStatus.value === 'failed') return 1
  return 0
})

const generationStatusText = computed(() => {
  switch (generationStatus.value) {
    case 'pending': return '等待生成'
    case 'generating': return '正在生成环境音...'
    case 'completed': return '生成完成'
    case 'failed': return '生成失败'
    default: return '未知状态'
  }
})

// 方法
const getCategoryColor = (category) => {
  const colors = {
    '自然音': 'green',
    '城市音': 'blue',
    '室内音': 'orange',
    '动作音': 'red'
  }
  return colors[category] || 'default'
}

const generateSound = async () => {
  try {
    generating.value = true
    generationProgress.value = 0
    generationStatus.value = 'generating'
    generationLogs.value = []

    // 添加生成日志
    addLog('info', '开始生成环境音...')
    addLog('info', `参数: 时长${soundParams.value.duration}秒, 强度${soundParams.value.intensity}`)

    // 调用生成API
    const response = await environmentGenerationAPI.generateSingleSound({
      keyword: soundInfo.value.keyword,
      description: soundInfo.value.description,
      duration: soundParams.value.duration,
      intensity: soundParams.value.intensity,
      volume: soundParams.value.volume,
      loop: soundParams.value.loop
    })

    if (response.data.success) {
      generationStatus.value = 'completed'
      generationProgress.value = 100
      addLog('success', '环境音生成完成')
      
      message.success('环境音生成完成')
      emit('refresh')
    } else {
      throw new Error(response.data.error || '生成失败')
    }
  } catch (error) {
    console.error('生成环境音失败:', error)
    generationStatus.value = 'failed'
    addLog('error', `生成失败: ${error.message}`)
    message.error('环境音生成失败')
  } finally {
    generating.value = false
  }
}

const playSound = async () => {
  try {
    playing.value = true
    // 实现播放逻辑
    message.info('开始播放环境音')
    
    // 模拟播放
    setTimeout(() => {
      playing.value = false
    }, 3000)
  } catch (error) {
    console.error('播放失败:', error)
    message.error('播放失败')
    playing.value = false
  }
}

const pauseSound = () => {
  playing.value = false
  message.info('暂停播放')
}

const stopSound = () => {
  playing.value = false
  message.info('停止播放')
}

const downloadSound = async () => {
  try {
    // 实现下载逻辑
    message.success('开始下载环境音')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败')
  }
}

const deleteSound = () => {
  // 实现删除逻辑
  message.success('环境音已删除')
  emit('refresh')
}

const saveAsTemplate = () => {
  // 实现保存模板逻辑
  message.success(`模板"${templateName.value}"已保存`)
  templateName.value = ''
}

const addLog = (type, message) => {
  generationLogs.value.push({
    type,
    message,
    time: new Date().toLocaleTimeString()
  })
}

const handleClose = () => {
  emit('update:visible', false)
}

// 监听props变化
watch(() => props.soundInfo, (newInfo) => {
  if (newInfo) {
    // 更新参数
    soundParams.value = {
      duration: newInfo.duration || 30,
      intensity: newInfo.intensity || 'medium',
      volume: newInfo.volume || 50,
      loop: newInfo.loop || false
    }
    
    // 更新状态
    generationStatus.value = newInfo.status || 'pending'
    generationProgress.value = newInfo.progress || 0
  }
}, { immediate: true })
</script>

<style scoped>
.info-section,
.params-section,
.status-section,
.actions-section,
.preview-section,
.template-section {
  margin-bottom: 24px;
}

.info-section h3,
.params-section h3,
.status-section h3,
.preview-section h3,
.template-section h3 {
  margin-bottom: 16px;
  color: #1890ff;
  font-weight: 600;
}

.slider-label {
  text-align: center;
  margin-top: 8px;
  color: #666;
}

.switch-label {
  margin-left: 8px;
  color: #666;
}

.progress-section {
  margin-top: 16px;
}

.progress-text {
  text-align: center;
  margin-top: 8px;
  color: #666;
}

.logs-section {
  margin-top: 16px;
}

.logs-section h4 {
  margin-bottom: 8px;
  color: #333;
}

.logs-container {
  max-height: 200px;
  overflow-y: auto;
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 8px;
}

.log-item {
  display: flex;
  margin-bottom: 4px;
  font-size: 12px;
}

.log-item.info {
  color: #1890ff;
}

.log-item.success {
  color: #52c41a;
}

.log-item.error {
  color: #ff4d4f;
}

.log-time {
  margin-right: 8px;
  color: #999;
  min-width: 80px;
}

.log-message {
  flex: 1;
}

.waveform-container {
  border: 1px solid #f0f0f0;
  border-radius: 4px;
  padding: 16px;
  text-align: center;
  background: #fafafa;
}

.waveform-placeholder {
  color: #666;
}

.audio-info {
  font-size: 12px;
  color: #999;
  margin-top: 8px;
}

.audio-controls {
  margin-top: 16px;
  text-align: center;
}
</style>
