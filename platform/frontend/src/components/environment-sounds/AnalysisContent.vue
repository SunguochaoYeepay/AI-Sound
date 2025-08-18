<template>
  <div class="analysis-content">
    <!-- 未选择章节 -->
    <div v-if="!selectedChapter" class="empty-state">
      <a-empty description="请先选择章节" />
    </div>
    
    <!-- 已选择章节但未分析状态 -->
    <div v-else-if="!hasAnalysis" class="analysis-prompt">
      <div class="prompt-content">
        <a-empty description="点击右上角按钮开始分析章节内容">
          <template #image>
            <BulbOutlined style="font-size: 64px; color: #d9d9d9;" />
          </template>
        </a-empty>
      </div>
    </div>
    
    <!-- 已分析状态 - 环境音轨道 -->
    <div v-else class="chapter-content">
      <!-- 筛选控制栏 -->
      <div class="filter-controls">
        <a-space>
          <span class="filter-label">显示模式：</span>
          <a-radio-group v-model:value="displayMode" size="small">
            <a-radio-button value="all">全部段落 ({{ totalParagraphs }})</a-radio-button>
            <a-radio-button value="environment">仅环境音 ({{ environmentParagraphs }})</a-radio-button>
          </a-radio-group>
        </a-space>
      </div>
      
      <!-- 环境音轨道分析结果 - 按段落分组 -->
      <div v-if="environmentTracks.length > 0" class="environment-tracks">
        
        
        <!-- 按段落分组显示 -->
        <div class="paragraphs-container">
          <div 
            v-for="(paragraph, paragraphIndex) in filteredGroupedTracks" 
            :key="paragraphIndex"
            class="paragraph-section"
            :class="{ 'no-environment': !paragraph.hasEnvironment }"
          >
            <div class="paragraph-header">
              <div class="paragraph-info">
                <span class="paragraph-number">段落 {{ paragraphIndex + 1 }}</span>
                <span class="paragraph-time">
                  {{ formatTime(paragraph.startTime) }} - {{ formatTime(paragraph.endTime) }}
                </span>
              </div>
              <div class="paragraph-stats">
                <a-tag v-if="paragraph.hasEnvironment" color="blue" size="small">{{ paragraph.tracks.length }} 个环境音</a-tag>
                <a-tag v-else color="default" size="small">无环境音</a-tag>
              </div>
            </div>
            
            <!-- 段落文本 -->
            <div class="paragraph-text">
              <div class="text-label">旁白内容：</div>
              <div class="text-content">{{ paragraph.narrationText || '暂无旁白内容' }}</div>
            </div>
            
            <!-- 该段落的环境音轨道 -->
            <div class="paragraph-tracks">
              <div 
                v-for="(track, trackIndex) in paragraph.tracks" 
                :key="track.segment_id"
                class="track-item"
                :class="{ 'has-match': track.has_match, 'has-generated': track.has_generated }"
              >
                <div class="track-header">
                  <div class="track-time">
                    {{ formatTime(track.start_time) }} - {{ formatTime(track.start_time + track.duration) }}
                  </div>
                  <div class="track-status">
                    <a-tag v-if="track.has_generated" color="success" size="small">已生成</a-tag>
                    <a-tag v-else-if="track.has_match" color="warning" size="small">已匹配</a-tag>
                    <a-tag v-else color="default" size="small">需生成</a-tag>
                  </div>
                </div>
                
                <div class="track-keywords">
                  <a-tag 
                    v-for="keyword in track.environment_keywords.slice(0, 3)" 
                    :key="keyword"
                    size="small"
                    color="blue"
                  >
                    {{ keyword }}
                  </a-tag>
                  <span v-if="track.environment_keywords.length > 3" class="more-keywords">
                    +{{ track.environment_keywords.length - 3 }}
                  </span>
                </div>
                
                <!-- 声音类型标签 -->
                <div class="track-type" v-if="track.duration_type">
                  <a-tag 
                    :color="track.duration_type === 'instant' ? 'orange' : 'green'"
                    size="small"
                  >
                    {{ track.duration_type === 'instant' ? '瞬时音' : '持续音' }}
                  </a-tag>
                </div>
                
                <div class="track-description">
                  {{ track.chinese_description || track.description || track.scene_description || (track.english_prompt ? `英文提示词: ${track.english_prompt}` : '暂无描述') }}
                </div>
                
                <div class="track-confidence">
                  <span class="confidence-label">置信度:</span>
                  <a-progress 
                    :percent="track.confidence * 100" 
                    :show-info="false"
                    size="small"
                    style="width: 100px; margin: 0 8px;"
                  />
                  <span class="confidence-text">{{ (track.confidence * 100).toFixed(0) }}%</span>
                </div>
                
                <!-- 轨道操作按钮 -->
                <div class="track-actions">
                  <a-space size="small">
                    <!-- 生成按钮 -->
                    <a-button 
                      v-if="!track.has_generated"
                      type="primary" 
                      size="small"
                      :loading="track.generating"
                      @click="$emit('generate-track', track, trackIndex)"
                    >
                      🎵 生成
                    </a-button>
                    
                    <!-- 播放按钮 -->
                    <a-button 
                      v-if="track.has_generated"
                      size="small"
                      :loading="track.playing"
                      @click="$emit('play-track', track, trackIndex)"
                    >
                      🎵 播放
                    </a-button>
                    
                    <!-- 下载按钮 -->
                    <a-button 
                      v-if="track.has_generated"
                      size="small"
                      @click="$emit('download-track', track, trackIndex)"
                    >
                      ⬇️ 下载
                    </a-button>
                    
                    <!-- 重新生成按钮 -->
                    <a-button 
                      v-if="track.has_generated"
                      size="small"
                      :loading="track.regenerating"
                      @click="$emit('regenerate-track', track, trackIndex)"
                    >
                      🔄 重新生成
                    </a-button>
                  </a-space>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 没有环境音轨道 -->
      <div v-else class="no-tracks">
        <a-empty description="未找到环境音轨道">
          <template #image>
            <SoundOutlined style="font-size: 64px; color: #d9d9d9;" />
          </template>
        </a-empty>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, ref } from 'vue'
import { BulbOutlined, SoundOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  selectedChapter: {
    type: Object,
    default: null
  },
  hasAnalysis: {
    type: Boolean,
    default: false
  },
  environmentTracks: {
    type: Array,
    default: () => []
  },
  generationLoading: {
    type: Boolean,
    default: false
  },
  mixingLoading: {
    type: Boolean,
    default: false
  },
  hasMixingFile: {
    type: Boolean,
    default: false
  }
})

// 显示模式
const displayMode = ref('all')

// Emits
const emit = defineEmits([
  'generate-all-sounds',
  'mix-sounds',
  'play-mixing',
  'download-mixing',
  'generate-track',
  'play-track',
  'download-track',
  'regenerate-track'
])

// 计算属性：按段落分组轨道
const groupedTracks = computed(() => {
  if (!props.environmentTracks || props.environmentTracks.length === 0) {
    return []
  }
  

  
  // 按段落分组
  const paragraphs = {}
  
  props.environmentTracks.forEach(track => {
    const paragraphKey = track.paragraph_index || track.segment_id || 0
    
    if (!paragraphs[paragraphKey]) {
      paragraphs[paragraphKey] = {
        paragraphIndex: paragraphKey,
        startTime: track.start_time,
        endTime: track.start_time + track.duration,
        narrationText: track.narration_text || track.text || '',
        tracks: []
      }
    }
    
    // 更新段落时间范围
    const trackEndTime = track.start_time + track.duration
    if (track.start_time < paragraphs[paragraphKey].startTime) {
      paragraphs[paragraphKey].startTime = track.start_time
    }
    if (trackEndTime > paragraphs[paragraphKey].endTime) {
      paragraphs[paragraphKey].endTime = trackEndTime
    }
    
    // 添加轨道
    const hasGenerated = track.generated_file_path && track.generated_file_path.length > 0
    paragraphs[paragraphKey].tracks.push({
      ...track,
      has_generated: hasGenerated,
      generating: false,
      playing: false,
      regenerating: false
    })
    

  })
  
  // 转换为数组并按段落索引排序
  const result = Object.values(paragraphs).sort((a, b) => a.paragraphIndex - b.paragraphIndex)
  
  // 为每个段落添加环境音标识
  result.forEach(paragraph => {
    paragraph.hasEnvironment = paragraph.tracks.some(track => 
      track.environment_keywords && track.environment_keywords.length > 0
    )
  })
  
  return result
})

// 筛选后的段落
const filteredGroupedTracks = computed(() => {
  if (displayMode.value === 'all') {
    return groupedTracks.value
  } else {
    return groupedTracks.value.filter(paragraph => paragraph.hasEnvironment)
  }
})

// 统计信息
const totalParagraphs = computed(() => groupedTracks.value.length)
const environmentParagraphs = computed(() => 
  groupedTracks.value.filter(paragraph => paragraph.hasEnvironment).length
)

// 工具函数：格式化时间
const formatTime = (seconds) => {
  if (!seconds || seconds === 0) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = Math.floor(seconds % 60)
  return `${mins}:${secs.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.analysis-content {
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.empty-state,
.analysis-prompt {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.filter-controls {
  margin-bottom: 16px;
  padding: 12px;
  background: #fafafa;
  border-radius: 6px;
  border: 1px solid #f0f0f0;
}

.filter-label {
  font-weight: 500;
  color: #666;
}

.tracks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 1px solid #f0f0f0;
}

.tracks-header h3 {
  margin: 0;
  color: #1890ff;
}

.batch-actions {
  display: flex;
  gap: 8px;
}

.paragraphs-container {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.paragraph-section {
  border: 1px solid #f0f0f0;
  border-radius: 8px;
  overflow: hidden;
}

.paragraph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.paragraph-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.paragraph-number {
  font-weight: 600;
  color: #1890ff;
}

.paragraph-time {
  color: #666;
  font-size: 12px;
}

.paragraph-text {
  padding: 12px 16px;
  background: #f9f9f9;
  border-bottom: 1px solid #f0f0f0;
}

.text-label {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.text-content {
  color: #666;
  line-height: 1.5;
}

.paragraph-tracks {
  padding: 16px;
}

.track-item {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 12px;
  background: #fff;
  transition: all 0.3s ease;
}

.track-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.track-item.has-match {
  border-left: 4px solid #faad14;
}

.track-item.has-generated {
  border-left: 4px solid #52c41a;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.track-time {
  font-size: 12px;
  color: #666;
}

.track-keywords {
  margin-bottom: 8px;
}

.more-keywords {
  color: #999;
  font-size: 12px;
  margin-left: 4px;
}

.track-description {
  color: #333;
  margin-bottom: 8px;
  line-height: 1.4;
}

.track-confidence {
  display: flex;
  align-items: center;
  margin-bottom: 12px;
}

.confidence-label {
  font-size: 12px;
  color: #666;
  margin-right: 8px;
}

.confidence-text {
  font-size: 12px;
  color: #666;
}

.track-actions {
  display: flex;
  justify-content: flex-end;
}

.no-tracks {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .analysis-content {
    padding: 12px;
  }
  
  .tracks-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 12px;
  }
  
  .batch-actions {
    width: 100%;
    justify-content: flex-start;
  }
  
  .paragraph-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
  }
  
  .track-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .track-actions {
    justify-content: flex-start;
  }
}

/* 暗色主题适配 */
[data-theme='dark'] .analysis-content {
  background: var(--ant-color-bg-container);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .tracks-header {
  border-bottom-color: var(--ant-border-color-split);
}

[data-theme='dark'] .tracks-header h3 {
  color: var(--ant-color-text);
}

[data-theme='dark'] .paragraph-section {
  border-color: var(--ant-border-color-split);
  background: var(--ant-color-bg-container);
}

[data-theme='dark'] .paragraph-section.no-environment {
  background: var(--ant-color-bg-layout);
  border-color: var(--ant-border-color-split);
}

[data-theme='dark'] .paragraph-header {
  background: var(--ant-color-bg-layout);
  border-bottom-color: var(--ant-border-color-split);
}

[data-theme='dark'] .paragraph-number {
  color: var(--ant-color-primary);
}

[data-theme='dark'] .paragraph-time {
  color: var(--ant-color-text-secondary);
}

[data-theme='dark'] .paragraph-text {
  background: var(--ant-color-bg-layout);
  border-bottom-color: var(--ant-border-color-split);
}

[data-theme='dark'] .text-label {
  color: var(--ant-color-text);
}

[data-theme='dark'] .text-content {
  color: var(--ant-color-text-secondary);
}

[data-theme='dark'] .track-item {
  border-color: var(--ant-border-color-split);
  background: var(--ant-color-bg-container);
}

[data-theme='dark'] .track-item:hover {
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
}

[data-theme='dark'] .track-time {
  color: var(--ant-color-text-secondary);
}

[data-theme='dark'] .more-keywords {
  color: var(--ant-color-text-tertiary);
}

[data-theme='dark'] .track-description {
  color: var(--ant-color-text);
}

[data-theme='dark'] .confidence-label {
  color: var(--ant-color-text-secondary);
}

[data-theme='dark'] .confidence-text {
  color: var(--ant-color-text-secondary);
}
</style>

