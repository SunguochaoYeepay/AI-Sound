<template>
  <div class="script-panel">
    <div class="panel-header">
      <h3>📝 剧本详情</h3>
      <div class="panel-actions">
        <a-button
          type="primary"
          size="small"
          @click="analyzeAllSegments"
          :loading="analyzingAll"
        >
          <template #icon>
            <AppstoreOutlined />
          </template>
                     段落分析 (全部)
        </a-button>

        
      </div>
    </div>

    <div class="script-content">
      <!-- 剧本详情 -->
      <div class="script-details">
        <div v-if="loading" class="loading-container">
          <a-spin size="large" />
          <p>加载中...</p>
        </div>
        
        <div v-else-if="scriptSegments.length > 0" class="script-segment-list">
          <ScriptSegment
            v-for="(script, index) in scriptSegments"
            :key="index"
            :script="script"
            :related-cards="getRelatedCards(script)"
            @segment-click="handleSegmentClick(index)"
            @card-click="handleCardClick"
            @six-card-analysis="handleSegmentAnalysis"
          />
        </div>
        
        <!-- 段落分析结果展示 -->
        <div v-if="sixCardResults && sixCardResults.length > 0" class="six-card-results">
          <h4>🎯 段落分析结果</h4>
          <div class="card-results">
            <div 
              v-for="(result, index) in sixCardResults" 
              :key="index"
              class="card-result-item"
            >
              <div class="result-header">
                <span class="result-title">段落 {{ result._metadata?.segment_index || index + 1 }} 分析结果</span>
                <span class="result-time">{{ result._metadata?.analysis_time ? new Date(result._metadata.analysis_time).toLocaleString() : '' }}</span>
              </div>
              
              <!-- 故事卡 -->
              <div class="card-section">
                <h5>📖 故事卡</h5>
                <div class="card-content">
                  <p><strong>主题:</strong> {{ result.story_card?.theme }}</p>
                  <p><strong>情节要点:</strong> {{ result.story_card?.plot_point }}</p>
                  <p><strong>叙述目的:</strong> {{ result.story_card?.narrative_purpose }}</p>
                </div>
              </div>
              
              <!-- 角色卡 -->
              <div class="card-section">
                <h5>🎭 角色卡</h5>
                <div class="card-content">
                  <div v-for="(character, charIndex) in result.character_card?.characters" :key="charIndex">
                    <p><strong>角色:</strong> {{ character.name }}</p>
                    <p><strong>动作:</strong> {{ character.actions }}</p>
                    <p><strong>情绪:</strong> {{ Array.isArray(character.emotions) ? character.emotions.join(', ') : character.emotions || '无' }}</p>
                  </div>
                </div>
              </div>
              
              <!-- 场景卡 -->
              <div class="card-section">
                <h5>🎬 场景卡</h5>
                <div class="card-content">
                  <p><strong>地点:</strong> {{ result.scene_card?.location }}</p>
                  <p><strong>时间:</strong> {{ result.scene_card?.time }}</p>
                  <p><strong>氛围:</strong> {{ result.scene_card?.atmosphere }}</p>
                  <p><strong>环境音:</strong> {{ Array.isArray(result.scene_card?.environment_sounds) ? result.scene_card.environment_sounds.join(', ') : result.scene_card?.environment_sounds || '无' }}</p>
                </div>
              </div>
              
              <!-- 事件卡 -->
              <div class="card-section">
                <h5>📝 事件卡</h5>
                <div class="card-content">
                  <p><strong>主要事件:</strong> {{ result.event_card?.main_event }}</p>
                  <p><strong>子事件:</strong> {{ Array.isArray(result.event_card?.sub_events) ? result.event_card.sub_events.join(', ') : result.event_card?.sub_events || '无' }}</p>
                  <p><strong>意义:</strong> {{ result.event_card?.significance }}</p>
                </div>
              </div>
              
              <!-- 情绪卡 -->
              <div class="card-section">
                <h5>💝 情绪卡</h5>
                <div class="card-content">
                  <p><strong>整体基调:</strong> {{ result.emotion_card?.overall_tone }}</p>
                  <div v-for="(change, changeIndex) in result.emotion_card?.emotion_changes" :key="changeIndex">
                    <p><strong>情绪变化:</strong> {{ change.from }} → {{ change.to }} (触发: {{ change.trigger }})</p>
                  </div>
                </div>
              </div>
              
              <!-- 音频剧本卡 -->
              <div class="card-section">
                <h5>🎵 音频剧本卡</h5>
                <div class="card-content">
                  <p><strong>配音指导:</strong> {{ result.audio_script_card?.voice_direction }}</p>
                  <p><strong>节奏:</strong> {{ result.audio_script_card?.pacing }}</p>
                  <p><strong>背景音乐:</strong> {{ result.audio_script_card?.background_music }}</p>
                  <p><strong>音效:</strong> {{ Array.isArray(result.audio_script_card?.sound_effects) ? result.audio_script_card.sound_effects.join(', ') : result.audio_script_card?.sound_effects || '无' }}</p>
                </div>
              </div>
              
              <!-- 音频分镜卡 -->
              <div class="card-section">
                <h5>🎬 音频分镜卡</h5>
                <div class="card-content">
                  <!-- 时间轴信息 -->
                  <div v-if="result.audio_storyboard_card?.timeline" class="timeline-info">
                    <p><strong>⏱️ 总时长:</strong> {{ result.audio_storyboard_card.timeline.total_duration }} 秒</p>
                    <p><strong>📊 分段数:</strong> {{ result.audio_storyboard_card.timeline.segments?.length || 0 }}</p>
                    <div v-if="result.audio_storyboard_card.timeline.segments" class="timeline-segments">
                      <p><strong>时间轴详情:</strong></p>
                      <div v-for="(segment, segIndex) in result.audio_storyboard_card.timeline.segments" :key="segIndex" class="timeline-segment">
                        <span class="segment-time">{{ segment.start_time }}-{{ segment.end_time }}s</span>
                        <span class="segment-speaker">{{ segment.speaker }}</span>
                        <span class="segment-emotion">{{ segment.emotion }}</span>
                      </div>
                    </div>
                  </div>
                  
                  <!-- 音轨配置 -->
                  <div v-if="result.audio_storyboard_card?.audio_tracks" class="audio-tracks-info">
                    <p><strong>🎵 音轨配置:</strong></p>
                    <div v-for="(track, trackName) in result.audio_storyboard_card.audio_tracks" :key="trackName" class="audio-track">
                      <span class="track-name">{{ track.name }}</span>
                      <span class="track-priority">优先级: {{ track.priority }}</span>
                      <span class="track-volume">音量: {{ track.volume }}%</span>
                    </div>
                  </div>
                  
                  <!-- 角色语音配置 -->
                  <div v-if="result.audio_storyboard_card?.voice_assignments?.characters" class="voice-assignments-info">
                    <p><strong>🎤 角色语音:</strong></p>
                    <div v-for="(char, charIndex) in result.audio_storyboard_card.voice_assignments.characters" :key="charIndex" class="voice-character">
                      <span class="char-name">{{ char.name }}</span>
                      <span class="char-role">{{ char.role_type }}</span>
                      <span class="char-voice">{{ char.voice_name }}</span>
                    </div>
                  </div>
                  
                  <!-- 背景音乐 -->
                  <div v-if="result.audio_storyboard_card?.background_music" class="background-music-info">
                    <p><strong>🎼 背景音乐:</strong></p>
                    <p>类型: {{ result.audio_storyboard_card.background_music.type }}</p>
                    <p>情绪: {{ result.audio_storyboard_card.background_music.mood }}</p>
                    <p>节奏: {{ result.audio_storyboard_card.background_music.tempo }}</p>
                    <p>音量: {{ result.audio_storyboard_card.background_music.volume }}%</p>
                  </div>
                  
                  <!-- 混音参数 -->
                  <div v-if="result.audio_storyboard_card?.mixing_parameters" class="mixing-params-info">
                    <p><strong>🎚️ 混音参数:</strong></p>
                    <p>主音量: {{ result.audio_storyboard_card.mixing_parameters.main_volume }}%</p>
                    <p>背景音量: {{ result.audio_storyboard_card.mixing_parameters.background_volume }}%</p>
                    <p>环境音量: {{ result.audio_storyboard_card.mixing_parameters.environment_volume }}%</p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
        
        <div v-else class="empty-content">
          <p>暂无数据</p>
        </div>
      </div>
    </div>

    <!-- 问题抽屉 -->
    <a-drawer
      :open="showIssuesDrawer"
      title="🔍 检测到的问题"
      placement="right"
      width="400"
      :closable="true"
      @close="showIssuesDrawer = false"
    >
      <div class="issues-drawer-content">
        <div v-if="loading" class="loading-container">
          <a-spin size="large" />
          <p>加载中...</p>
        </div>
        <div v-else-if="detectedIssues.length > 0" class="issue-list">
          <div v-for="(issue, index) in detectedIssues" :key="index" class="issue-item">
            <div class="issue-header">
              <a-tag :color="getIssueColor(issue.type)">{{ issue.type }}</a-tag>
              <span class="issue-time">{{ issue.time }}</span>
            </div>
            <div class="issue-description">{{ issue.description }}</div>
          </div>
        </div>
        <div v-else class="empty-content">
          <p>暂无问题</p>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ExclamationCircleOutlined, AppstoreOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import { storyboardAPI } from '@/api/storyboard'
import ScriptSegment from './ScriptSegment.vue'

// Props
const props = defineProps({
  loading: {
    type: Boolean,
    default: false
  },
  scriptSegments: {
    type: Array,
    default: () => []
  },
  detectedIssues: {
    type: Array,
    default: () => []
  },
  reviewData: {
    type: Object,
    default: () => ({})
  },
  chapter: {
    type: Object,
    default: () => ({})
  },
  sixCardResults: {
    type: Array,
    default: () => []
  },
  selectedSegmentIndex: {
    type: Number,
    default: null
  }
})

// Emits
const emit = defineEmits(['segment-click', 'card-click'])

// Reactive data
const showIssuesDrawer = ref(false)
const analyzingAll = ref(false)

// Methods
const handleSegmentClick = (index) => {
  emit('segment-click', index)
}

const handleCardClick = (card) => {
  emit('card-click', card)
}

const analyzeAllSegments = async () => {
  if (analyzingAll.value) return

  // 检查是否有智能分段数据
  const hasSegments = props.scriptSegments.length > 0 || 
                     (props.reviewData?.segmentation_data?.segments && 
                      props.reviewData.segmentation_data.segments.length > 0)
  
  if (!hasSegments) {
    message.warning('请先进行智能分段，然后再进行段落分析')
    return
  }

  analyzingAll.value = true
  try {
          console.log('开始对所有段落进行段落分析...')
    
    // 获取段落数量（优先使用智能分段数据）
    const segmentCount = props.reviewData?.segmentation_data?.segments?.length || props.scriptSegments.length
    console.log('段落数量:', segmentCount)

    // 显示长时间操作提示
    message.info({
              content: `正在对 ${segmentCount} 个段落进行段落分析，这可能需要几分钟，请耐心等待...`,
      duration: 5,
      key: 'six-card-analysis'
    })

          // 调用段落分析API
    try {
      const response = await storyboardAPI.sixCardAnalysis(props.chapter?.id)

      if (response.data?.success) {
        message.success({
          content: `🎉 段落分析完成！共分析 ${response.data.data.analyzed_segments} 个段落`,
          duration: 5,
          key: 'six-card-analysis'
        })
        console.log('段落分析完成:', response.data)
      } else {
        throw new Error(response.data?.message || '段落分析失败')
      }
    } catch (apiError) {
              console.error('段落分析API调用失败:', apiError)
      message.error({
                  content: `❌ 段落分析失败: ${apiError.message || '未知错误'}`,
        duration: 5,
        key: 'six-card-analysis'
      })
    }

    analyzingAll.value = false

  } catch (error) {
    console.error('段落分析失败:', error)
    message.error({
              content: `❌ 段落分析失败: ${error.message || '未知错误'}`,
      duration: 5,
      key: 'six-card-analysis'
    })
    analyzingAll.value = false
  }
}

const handleSegmentAnalysis = async (data) => {
      console.log('收到单个段落段落分析请求:', data.segmentIndex)
  try {
    // 显示分析提示
    message.info({
      content: `正在分析段落 ${data.segmentIndex + 1}，请稍候...`,
      duration: 3,
      key: `segment-${data.segmentIndex}`
    })

          // 调用单个段落的段落分析API
    const response = await storyboardAPI.sixCardAnalysis(props.chapter?.id, [data.segmentIndex])

    if (response.data?.success) {
      message.success({
        content: `✅ 段落 ${data.segmentIndex + 1} 段落分析完成！`,
        duration: 3,
        key: `segment-${data.segmentIndex}`
      })
              console.log('单个段落段落分析完成:', data.segmentIndex, response.data)
    } else {
              throw new Error(response.data?.message || '段落分析失败')
    }

  } catch (error) {
    console.error('单个段落段落分析失败:', error)
    message.error({
              content: `❌ 段落 ${data.segmentIndex + 1} 段落分析失败`,
      duration: 3,
      key: `segment-${data.segmentIndex}`
    })
  }
}

const getRelatedCards = (script) => {
  const cards = []
  
  // 检查是否有对应的卡片数据
  if (!props.reviewData?.cards) return cards
  
  // 根据剧本内容类型和内容智能关联卡片
  if (script.type === 'dialogue' && script.speaker) {
    // 对话类型：关联角色卡、事件卡、情绪卡
    if (props.reviewData.cards.character?.length > 0) {
      cards.push({ type: 'character', name: '角色卡', icon: '🎭' })
    }
    if (props.reviewData.cards.event?.length > 0) {
      cards.push({ type: 'event', name: '事件卡', icon: '📝' })
    }
    if (props.reviewData.cards.emotion?.length > 0) {
      cards.push({ type: 'emotion', name: '情绪卡', icon: '💝' })
    }
  }
  
  if (script.type === 'narration') {
    // 旁白类型：关联场景卡、故事卡
    if (props.reviewData.cards.scene?.length > 0) {
      cards.push({ type: 'scene', name: '场景卡', icon: '🎬' })
    }
    if (props.reviewData.cards.story?.length > 0) {
      cards.push({ type: 'story', name: '故事卡', icon: '📖' })
    }
  }
  
  // 如果内容较长，可能包含更多信息，添加更多关联
  if (script.text && script.text.length > 30) {
    if (props.reviewData.cards.story?.length > 0 && !cards.find(c => c.type === 'story')) {
      cards.push({ type: 'story', name: '故事卡', icon: '📖' })
    }
    if (props.reviewData.cards.event?.length > 0 && !cards.find(c => c.type === 'event')) {
      cards.push({ type: 'event', name: '事件卡', icon: '📝' })
    }
  }
  
  // 音频相关卡片：根据时间范围关联
  if (script.startTime && script.endTime) {
    if (props.reviewData.cards.audio_storyboard?.length > 0) {
      cards.push({ type: 'audio_storyboard', name: '音频分镜卡', icon: '🎬' })
    }
    if (props.reviewData.cards.audio_script?.length > 0) {
      cards.push({ type: 'audio_script', name: '音频剧本卡', icon: '📝' })
    }
  }
  
  return cards
}

const getIssueColor = (type) => {
  const colors = {
    missing_speaker: 'red',
    missing_voice: 'orange',
    empty_content: 'purple',
    invalid_time: 'blue',
    timing: 'orange',
    emotion: 'red',
    background: 'blue',
    quality: 'purple'
  }
  return colors[type] || 'default'
}
</script>

<style scoped>
.script-panel {
  flex: 1;
  border-radius: 12px;
  box-shadow: 0 4px 16px var(--shadow-color, rgba(0, 0, 0, 0.1));
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  padding: 20px 24px;
  border-bottom: 1px solid var(--border-color, #000000);
  display: flex;
  justify-content: space-between;
  align-items: center;
  background: var(--header-bg, #262626);
  border-radius: 12px 12px 0 0;
}

.panel-header h3 {
  margin: 0;
  color: var(--text-color, #333);
  font-size: 18px;
  font-weight: 600;
}

.panel-actions {
  display: flex;
  gap: 8px;
}

.script-content {
  flex: 1;
  padding: 24px;
  overflow-y: auto;
  background: var(--content-bg, #262626);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-color, #666);
}

.empty-content {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: var(--text-color, #999);
  font-style: italic;
}

/* 问题抽屉样式 */
.issues-drawer-content {
  padding: 16px 0;
}

.issues-drawer-content .issue-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.issues-drawer-content .issue-item {
  padding: 12px;
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 6px;
  background: var(--card-bg, #fff);
}

.issues-drawer-content .issue-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.issues-drawer-content .issue-time {
  font-size: 12px;
  color: var(--text-secondary, #666);
}

.issues-drawer-content .issue-description {
  color: var(--text-color, #333);
  line-height: 1.5;
}

/* 滚动条样式 */
.script-content::-webkit-scrollbar {
  width: 6px;
}

.script-content::-webkit-scrollbar-track {
  background: var(--border-color, #f1f1f1);
  border-radius: 3px;
}

.script-content::-webkit-scrollbar-thumb {
  background: var(--text-secondary, #c1c1c1);
  border-radius: 3px;
}

.script-content::-webkit-scrollbar-thumb:hover {
  background: var(--text-color, #a8a8a8);
}

/* 智能分段样式 */
.segmentation-info {
  margin-bottom: 20px;
  padding: 16px;
  background: var(--primary-bg, #f0f8ff);
  border: 1px solid var(--primary-border, rgba(24, 144, 255, 0.2));
  border-radius: 8px;
}

.segmentation-info h4 {
  margin: 0 0 8px 0;
  color: var(--primary-color, #1890ff);
  font-size: 16px;
}

.segmentation-info p {
  margin: 0;
  color: var(--text-secondary, #666);
  font-size: 14px;
}

.segmentation-segments {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.segment-item {
  padding: 16px;
  border: 1px solid var(--border-color, #e8e8e8);
  border-radius: 8px;
  background: var(--card-bg, white);
}

.segment-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.segment-index {
  font-weight: 600;
  color: var(--text-color, #333);
  font-size: 14px;
}

  .segment-text {
    color: var(--text-color, #333);
    line-height: 1.6;
    font-size: 14px;
    text-align: justify;
  }

  /* 段落分析结果样式 */
  .six-card-results {
    margin-bottom: 24px;
    padding: 20px;
    background: var(--success-bg, #f6ffed);
    border: 1px solid var(--success-border, #b7eb8f);
    border-radius: 8px;
  }

  .six-card-results h4 {
    margin: 0 0 16px 0;
    color: var(--success-color, #52c41a);
    font-size: 18px;
    font-weight: 600;
  }

  .card-results {
    display: flex;
    flex-direction: column;
    gap: 20px;
  }

  .card-result-item {
    padding: 16px;
    background: white;
    border: 1px solid var(--border-color, #e8e8e8);
    border-radius: 8px;
  }

  .result-header {
    margin-bottom: 16px;
    padding-bottom: 8px;
    border-bottom: 2px solid var(--primary-color, #1890ff);
  }

  .result-title {
    font-size: 16px;
    font-weight: 600;
    color: var(--primary-color, #1890ff);
  }

  .card-section {
    margin-bottom: 16px;
    padding: 12px;
    background: var(--card-bg, #fafafa);
    border-radius: 6px;
  }

  .card-section h5 {
    margin: 0 0 8px 0;
    color: var(--text-color, #333);
    font-size: 14px;
    font-weight: 600;
  }

  .card-content p {
    margin: 4px 0;
    color: var(--text-color, #333);
    font-size: 13px;
    line-height: 1.5;
  }

  .card-content strong {
    color: var(--text-color, #000);
  }

/* 音频分镜卡样式 */
.timeline-info {
  margin-bottom: 16px;
}

.timeline-segments {
  margin-top: 8px;
}

.timeline-segment {
  display: flex;
  gap: 12px;
  margin: 4px 0;
  padding: 4px 8px;
  background: var(--segment-bg, #f5f5f5);
  border-radius: 4px;
  font-size: 12px;
}

.segment-time {
  color: var(--time-color, #1890ff);
  font-weight: 500;
}

.segment-speaker {
  color: var(--speaker-color, #52c41a);
  font-weight: 500;
}

.segment-emotion {
  color: var(--emotion-color, #eb2f96);
  font-weight: 500;
}

.audio-tracks-info {
  margin-bottom: 16px;
}

.audio-track {
  display: flex;
  gap: 12px;
  margin: 4px 0;
  padding: 4px 8px;
  background: var(--track-bg, #f0f8ff);
  border-radius: 4px;
  font-size: 12px;
}

.track-name {
  color: var(--track-name-color, #1890ff);
  font-weight: 500;
}

.track-priority {
  color: var(--priority-color, #fa8c16);
}

.track-volume {
  color: var(--volume-color, #52c41a);
}

.voice-assignments-info {
  margin-bottom: 16px;
}

.voice-character {
  display: flex;
  gap: 12px;
  margin: 4px 0;
  padding: 4px 8px;
  background: var(--voice-bg, #fff7e6);
  border-radius: 4px;
  font-size: 12px;
}

.char-name {
  color: var(--char-name-color, #1890ff);
  font-weight: 500;
}

.char-role {
  color: var(--role-color, #722ed1);
}

.char-voice {
  color: var(--voice-color, #52c41a);
}

.background-music-info {
  margin-bottom: 16px;
}

.mixing-params-info {
  margin-bottom: 16px;
}

/* 深色主题下的特殊样式覆盖 */
[data-theme="dark"] .panel-header {
  background: var(--header-bg, #262626) !important;
  border-color: var(--border-color, #333333) !important;
}

[data-theme="dark"] .script-content {
  background: var(--content-bg, #1a1a1a) !important;
}

[data-theme="dark"] .six-card-results {
  background: var(--success-bg, #1a1a1a) !important;
  border-color: var(--success-border, #52c41a) !important;
}

[data-theme="dark"] .card-result-item {
  background: var(--card-bg, #262626) !important;
  border-color: var(--border-color, #333333) !important;
}

[data-theme="dark"] .card-section {
  background: var(--card-bg, #1a1a1a) !important;
}

[data-theme="dark"] .card-content p {
  color: var(--text-color, #e0e0e0) !important;
}

[data-theme="dark"] .card-content strong {
  color: var(--text-color, #ffffff) !important;
}

[data-theme="dark"] .result-title {
  color: var(--primary-color, #4a9eff) !important;
}

[data-theme="dark"] .card-section h5 {
  color: var(--text-color, #e0e0e0) !important;
}

/* 暗色主题适配 */
[data-theme="dark"] .timeline-segment {
  background: var(--segment-bg, #1f1f1f);
}

[data-theme="dark"] .audio-track {
  background: var(--track-bg, #1a1a2e);
}

[data-theme="dark"] .voice-character {
  background: var(--voice-bg, #2a1a0a);
}
</style>
