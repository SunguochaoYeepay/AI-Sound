<template>
  <a-drawer
    :open="visible"
    title="环境音详情"
    width="600px"
    placement="right"
    @close="handleClose"
    @update:open="$emit('update:visible', $event)"
  >
    <!-- 环境音信息 -->
    <div class="sound-info-section">
      <div class="sound-info">
        <div class="info-row">
          <span class="label">名称：</span>
          <span class="value">{{ soundInfo.name || '未命名' }}</span>
        </div>
        <div class="info-row">
          <span class="label">时长：</span>
          <span class="value">{{ soundInfo.duration || 30 }}秒</span>
        </div>
        <div class="info-row">
          <span class="label">状态：</span>
          <a-tag :color="hasGenerated ? 'success' : 'default'">
            {{ hasGenerated ? '已生成' : '未生成' }}
          </a-tag>
        </div>
        <div class="info-row">
          <span class="label">关键词：</span>
          <div class="keywords-list">
            <a-tag 
              v-for="keyword in getKeywordsList()" 
              :key="keyword"
              color="blue"
              size="small"
            >
              {{ keyword }}
            </a-tag>
          </div>
        </div>
        <div class="info-row">
          <span class="label">描述：</span>
          <div class="description-text">
            {{ soundInfo.description || '暂无场景描述' }}
          </div>
        </div>
        <div class="info-row" v-if="soundInfo.english_prompt">
          <span class="label">英文提示词：</span>
          <div class="description-text">
            {{ soundInfo.english_prompt }}
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
      </a-space>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { SoundOutlined } from '@ant-design/icons-vue'
import { environmentGenerationAPI } from '@/api'
import { playEnvironmentTrack } from '@/utils/audioService'

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
const generating = ref(false)
const playing = ref(false)

// 计算属性
const hasGenerated = computed(() => {
  return props.soundInfo?.status === 'completed' && props.soundInfo?.audioUrl
})

const canGenerate = computed(() => {
  return !generating.value && props.soundInfo?.keyword
})

// 方法
const getKeywordsList = () => {
  if (!props.soundInfo) return []
  
  // 尝试从不同字段获取关键词
  if (props.soundInfo.keyword) {
    return [props.soundInfo.keyword]
  }
  
  if (props.soundInfo.environment_keywords && Array.isArray(props.soundInfo.environment_keywords)) {
    return props.soundInfo.environment_keywords
  }
  
  if (props.soundInfo.name) {
    return [props.soundInfo.name]
  }
  
  return []
}

const generateSound = async () => {
  try {
    generating.value = true
    
    // 检查必需的参数
    if (!props.soundInfo?.projectId) {
      throw new Error('缺少项目ID信息')
    }
    
    if (props.soundInfo?.trackIndex === undefined) {
      throw new Error('缺少轨道索引信息')
    }
    
    // 调用正确的生成API
    const response = await environmentGenerationAPI.startGeneration(
      props.soundInfo.projectId,
      {
        track_indices: [props.soundInfo.trackIndex]
      }
    )

    if (response.data.success) {
      message.success('环境音生成任务已启动')
      emit('refresh')
    } else {
      throw new Error(response.data.message || '生成失败')
    }
  } catch (error) {
    console.error('生成环境音失败:', error)
    message.error(error.message || '环境音生成失败')
  } finally {
    generating.value = false
  }
}

const playSound = async () => {
  try {
    playing.value = true
    
    // 检查必需的参数
    if (!props.soundInfo?.projectId || props.soundInfo?.trackIndex === undefined) {
      throw new Error('缺少播放所需的项目信息')
    }
    
    // 构建轨道标题
    const trackTitle = `${props.soundInfo.name || '环境音'}`
    
    console.log('🎵 播放环境音:', {
      项目ID: props.soundInfo.projectId,
      轨道索引: props.soundInfo.trackIndex,
      轨道标题: trackTitle,
      文件路径: props.soundInfo.audioUrl
    })
    
    // 使用统一的音频播放服务
    await playEnvironmentTrack(props.soundInfo.projectId, props.soundInfo.trackIndex, trackTitle)
    message.success(`🎵 播放: ${trackTitle}`)
    
  } catch (error) {
    console.error('播放失败:', error)
    message.error('播放失败: ' + (error.message || '未知错误'))
  } finally {
    playing.value = false
  }
}

const downloadSound = async () => {
  try {
    // 检查必需的参数
    if (!props.soundInfo?.projectId || props.soundInfo?.trackIndex === undefined) {
      throw new Error('缺少下载所需的项目信息')
    }
    
    const response = await environmentGenerationAPI.downloadEnvironmentSound(
      props.soundInfo.projectId,
      props.soundInfo.trackIndex
    )
    
    const filename = `${props.soundInfo.name || '环境音'}_${props.soundInfo.projectId}_${props.soundInfo.trackIndex}.wav`
    
    const blob = new Blob([response.data], { type: 'audio/wav' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    message.success('环境音下载完成')
  } catch (error) {
    console.error('下载失败:', error)
    message.error('下载失败: ' + (error.response?.data?.detail || error.message || '未知错误'))
  }
}

const handleClose = () => {
  emit('update:visible', false)
}
</script>

<style scoped>
.sound-info-section,
.actions-section {
  margin-bottom: 24px;
}

/* 环境音信息样式 */
.sound-info {
  background: #fafafa;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  padding: 16px;
}

.info-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.info-row:last-child {
  margin-bottom: 0;
}

.info-row .label {
  font-weight: 500;
  color: #333;
  min-width: 80px;
  margin-right: 12px;
  flex-shrink: 0;
}

.info-row .value {
  color: #666;
}

.keywords-list {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.description-text {
  color: #666;
  line-height: 1.5;
  background: #fff;
  padding: 8px 12px;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
  flex: 1;
}

/* 暗色主题适配 */
[data-theme='dark'] .sound-info {
  background: var(--ant-color-bg-layout);
  border-color: var(--ant-border-color-split);
}

[data-theme='dark'] .info-row .label {
  color: var(--ant-color-text);
}

[data-theme='dark'] .info-row .value {
  color: var(--ant-color-text-secondary);
}

[data-theme='dark'] .description-text {
  color: var(--ant-color-text-secondary);
  background: var(--ant-color-bg-container);
  border-color: var(--ant-border-color-split);
}
</style>
