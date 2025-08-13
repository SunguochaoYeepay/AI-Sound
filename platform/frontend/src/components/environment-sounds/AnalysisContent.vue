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
      <!-- 环境音轨道分析结果 - 按段落分组 -->
      <div v-if="environmentTracks.length > 0" class="environment-tracks">
        <div class="tracks-header">
          <h3>环境音分析结果</h3>
          <a-tag color="green">{{ environmentTracks.length }} 个轨道</a-tag>
        </div>
        
        <!-- 按段落分组显示 -->
        <div class="paragraphs-container">
          <div 
            v-for="(paragraph, paragraphIndex) in groupedTracks" 
            :key="paragraphIndex"
            class="paragraph-section"
          >
            <div class="paragraph-header">
              <div class="paragraph-info">
                <span class="paragraph-number">段落 {{ paragraphIndex + 1 }}</span>
                <span class="paragraph-time">
                  {{ formatTime(paragraph.startTime) }} - {{ formatTime(paragraph.endTime) }}
                </span>
              </div>
              <div class="paragraph-stats">
                <a-tag color="blue" size="small">{{ paragraph.tracks.length }} 个环境音</a-tag>
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
                v-for="track in paragraph.tracks" 
                :key="track.segment_id"
                class="track-item"
                :class="{ 'has-match': track.has_match }"
              >
                <div class="track-header">
                  <div class="track-time">
                    {{ formatTime(track.start_time) }} - {{ formatTime(track.start_time + track.duration) }}
                  </div>
                  <div class="track-status">
                    <a-tag v-if="track.has_match" color="success" size="small">已匹配</a-tag>
                    <a-tag v-else color="warning" size="small">需生成</a-tag>
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
                
                <div class="track-description">
                  {{ track.description || track.scene_description || '暂无描述' }}
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
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 无环境音轨道 -->
      <div v-else class="no-tracks">
        <a-empty description="未检测到环境音轨道" />
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { BulbOutlined } from '@ant-design/icons-vue'

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
  }
})

// 按段落分组的计算属性
const groupedTracks = computed(() => {
  if (!props.environmentTracks || props.environmentTracks.length === 0) {
    return []
  }
  
  // 按segment_id分组（假设segment_id包含段落信息）
  const groups = {}
  
  props.environmentTracks.forEach((track, index) => {
    const segmentId = track.segment_id || `segment_${index + 1}`
    if (!groups[segmentId]) {
      groups[segmentId] = {
        segmentId,
        startTime: track.start_time,
        endTime: track.start_time + track.duration,
        narrationText: track.narration_text || track.scene_description || '',
        tracks: []
      }
    }
    groups[segmentId].tracks.push(track)
    
    // 更新时间范围
    const trackEndTime = track.start_time + track.duration
    if (trackEndTime > groups[segmentId].endTime) {
      groups[segmentId].endTime = trackEndTime
    }
  })
  
  // 转换为数组并按时间排序
  const result = Object.values(groups).sort((a, b) => a.startTime - b.startTime)
  
  return result
})

const formatTime = (seconds) => {
  const minutes = Math.floor(seconds / 60)
  const remainingSeconds = Math.floor(seconds % 60)
  return `${minutes}:${remainingSeconds.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.analysis-content {
  height: 100%;
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
  min-height: 300px;
}

.analysis-prompt {
  display: flex;
  align-items: center;
  justify-content: center;
  height: 100%;
}

.prompt-content {
  text-align: center;
}

.chapter-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.environment-tracks {
  background-color: var(--ant-item-hover-bg);
  border-radius: 8px;
  padding: 20px;
}

.tracks-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.tracks-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 600;
  color: var(--ant-text-color);
}

.paragraphs-container {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.paragraph-section {
  background-color: var(--ant-component-background);
  border: 1px solid var(--ant-border-color-split);
  border-radius: 6px;
  padding: 16px;
  transition: all 0.2s ease;
}

.paragraph-section:hover {
  border-color: var(--ant-primary-color);
  box-shadow: 0 2px 8px var(--ant-box-shadow);
}

.paragraph-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.paragraph-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.paragraph-number {
  font-size: 14px;
  font-weight: 500;
  color: var(--ant-text-color);
}

.paragraph-time {
  font-size: 14px;
  color: var(--ant-text-color-secondary);
}

.paragraph-stats {
  display: flex;
  align-items: center;
}

.paragraph-text {
  margin-bottom: 16px;
}

.text-label {
  font-size: 14px;
  font-weight: 500;
  color: var(--ant-text-color);
  margin-bottom: 8px;
}

.text-content {
  line-height: 1.6;
  color: var(--ant-text-color);
  max-height: 200px;
  overflow-y: auto;
  white-space: pre-wrap;
}

.paragraph-tracks {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.track-item {
  background-color: var(--ant-item-hover-bg);
  border: 1px solid var(--ant-border-color-split);
  border-radius: 6px;
  padding: 12px;
  transition: all 0.2s ease;
}

.track-item:hover {
  border-color: var(--ant-primary-color);
  box-shadow: 0 2px 8px var(--ant-box-shadow);
}

.track-item.has-match {
  border-color: var(--ant-success-color);
  background-color: rgba(82, 196, 26, 0.05);
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.track-time {
  font-size: 14px;
  font-weight: 500;
  color: var(--ant-text-color);
}

.track-keywords {
  margin-bottom: 8px;
}

.more-keywords {
  font-size: 12px;
  color: var(--ant-text-color-secondary);
  margin-left: 4px;
}

.track-description {
  font-size: 13px;
  color: var(--ant-text-color-secondary);
  line-height: 1.4;
  margin-bottom: 8px;
}

.track-confidence {
  display: flex;
  align-items: center;
  font-size: 12px;
}

.confidence-label {
  color: var(--ant-text-color-secondary);
  margin-right: 4px;
}

.confidence-text {
  color: var(--ant-text-color-secondary);
  font-weight: 500;
}

.no-tracks {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 200px;
}
</style>
