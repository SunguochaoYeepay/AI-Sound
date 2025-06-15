<!-- 智能分析结果显示组件 -->
<template>
  <div v-if="analysisResult" class="analysis-result-display">
    <a-tabs>
      <!-- 合成计划 Tab -->
      <a-tab-pane tab="🎯 合成计划" key="synthesis-plan">
        <div class="synthesis-plan-preview">
          <div class="plan-summary">
            <a-descriptions bordered :column="2" size="small">
              <a-descriptions-item label="项目类型">
                {{ analysisResult.project_info?.novel_type }}
              </a-descriptions-item>
              <a-descriptions-item label="AI模型">
                {{ analysisResult.project_info?.ai_model }}
              </a-descriptions-item>
              <a-descriptions-item label="总分段数">
                {{ analysisResult.project_info?.total_segments }}
              </a-descriptions-item>
              <a-descriptions-item label="生成时间">
                {{ formatTime(analysisResult.project_info?.analysis_time) }}
              </a-descriptions-item>
            </a-descriptions>
          </div>
          
          <div class="synthesis-segments">
            <h4 style="margin: 16px 0 12px 0;">📝 执行序列（可直接合成）</h4>
            <div class="segments-container">
              <div 
                v-for="segment in analysisResult.synthesis_plan" 
                :key="segment.segment_id"
                class="synthesis-segment-item"
              >
                <div class="segment-header">
                  <span class="segment-id">#{{ segment.segment_id }}</span>
                  <a-tag color="blue">{{ segment.speaker }}</a-tag>
                  <a-tag color="green">{{ segment.voice_name }}</a-tag>
                </div>
                <div class="segment-text">{{ segment.text }}</div>
                <div class="segment-params">
                  <small>
                    时间步长: {{ segment.parameters?.timeStep }}, 
                    P权重: {{ segment.parameters?.pWeight }}, 
                    T权重: {{ segment.parameters?.tWeight }}
                  </small>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-tab-pane>
      
      <!-- 角色配置 Tab -->
      <a-tab-pane tab="🎭 角色配置" key="characters">
        <div class="characters-preview">
          <div class="config-description">
            <a-alert
              message="角色声音配置"
              description="AI已自动完成角色与声音的匹配，您可以在这里进行微调"
              type="info"
              show-icon
              style="margin-bottom: 16px;"
            />
          </div>
          
          <div 
            v-for="character in analysisResult.characters" 
            :key="character.name"
            class="character-preview-item enhanced"
          >
            <div class="character-header">
              <h4>{{ character.name }}</h4>
              <div class="character-tags">
                <a-tag color="green">ID: {{ character.voice_id }}</a-tag>
                <a-tag color="blue">{{ character.voice_name }}</a-tag>
              </div>
            </div>
            
            <!-- 声音配置区域 -->
            <div class="voice-config-section">
              <div class="ai-recommendation">
                <span class="ai-label">🤖 AI推荐:</span>
                <a-tag color="orange">{{ character.voice_name }} (ID: {{ character.voice_id }})</a-tag>
              </div>
              
                              <div class="voice-adjustment">
                  <label class="adjustment-label">手动调整:</label>
                  <div class="voice-selector-inline">
                    <a-select
                      :value="voiceMapping[character.name] || character.voice_id"
                      placeholder="选择其他声音"
                      style="width: 200px;"
                      allowClear
                      @change="(value) => $emit('updateVoiceMapping', character.name, value)"
                    >
                    <a-select-option
                      v-for="voice in availableVoices"
                      :key="voice.id"
                      :value="voice.id"
                    >
                      <div class="voice-option">
                        <span class="voice-name">{{ voice.name }}</span>
                        <a-tag size="small" :color="getVoiceTypeColor(voice.type)">
                          {{ getVoiceTypeLabel(voice.type) }}
                        </a-tag>
                        <span v-if="voice.id === character.voice_id" class="ai-marker">🤖</span>
                      </div>
                    </a-select-option>
                  </a-select>
                  
                  <!-- 试听按钮 - 总是显示，优先试听用户选择，否则试听AI推荐 -->
                  <a-button
                    type="primary"
                    size="small"
                    :loading="previewLoading === getCurrentVoiceId(character)"
                    @click="$emit('playVoicePreview', getCurrentVoiceId(character), getCharacterSampleText(character.name))"
                  >
                    <template v-if="!previewLoading">
                      <span v-if="currentPlayingVoice === getCurrentVoiceId(character)">⏸️ 停止</span>
                      <span v-else>🔊 试听{{ voiceMapping[character.name] ? '(已选)' : '(AI推荐)' }}</span>
                    </template>
                  </a-button>
                </div>
              </div>
              
              <!-- 配置状态 -->
              <div class="config-status">
                <a-tag v-if="voiceMapping[character.name]" color="success">
                  ✅ 已手动配置 (ID: {{ voiceMapping[character.name] }})
                </a-tag>
                <a-tag v-else color="orange">
                  🤖 使用AI推荐 (ID: {{ character.voice_id }})
                </a-tag>
              </div>
            </div>
          </div>
        </div>
      </a-tab-pane>
      
      <!-- 原始数据 Tab -->
      <a-tab-pane tab="🔧 JSON数据" key="raw">
        <div class="json-preview">
          <div class="json-description">
            <a-alert
              message="统一JSON格式"
              description="此JSON包含项目信息、合成计划和角色配置，可直接用于TTS合成任务。大模型已完成所有智能分析和匹配工作。"
              type="info"
              show-icon
              style="margin-bottom: 16px;"
            />
          </div>
          <a-textarea 
            :value="JSON.stringify(analysisResult, null, 2)"
            :rows="25"
            readonly
            class="raw-data-display"
          />
        </div>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup>
import { defineProps, defineEmits } from 'vue'

// 组件 props
const props = defineProps({
  analysisResult: {
    type: Object,
    default: null
  },
  availableVoices: {
    type: Array,
    default: () => []
  },
  voiceMapping: {
    type: Object,
    default: () => ({})
  },
  previewLoading: {
    type: [String, Number],
    default: null
  },
  currentPlayingVoice: {
    type: [String, Number],
    default: null
  }
})

// 组件 emits
const emit = defineEmits(['updateVoiceMapping', 'playVoicePreview'])

// 获取角色示例文本
const getCharacterSampleText = (characterName) => {
  // 从合成计划中找到该角色的文本示例
  if (props.analysisResult?.synthesis_plan) {
    const characterSegment = props.analysisResult.synthesis_plan.find(segment => 
      segment.speaker === characterName
    )
    if (characterSegment) {
      return characterSegment.text.slice(0, 30) + '...'
    }
  }
  
  // 默认示例文本
  const samples = {
    '李维': '数据的流动模式确实很有趣。',
    '艾莉': '你有没有觉得这些数据像是在讲故事？',
    '系统旁白': '在数字化时代的浪潮中，数据如同蚕茧般包裹着我们的生活。',
    '心理旁白': '李维思考着艾莉的话，意识到数据背后可能隐藏着更深层的含义。'
  }
  
  return samples[characterName] || '这是一段示例文本用于声音试听。'
}

// 获取声音类型标签
const getVoiceTypeLabel = (type) => {
  const labels = {
    'male': '男声',
    'female': '女声',
    'child': '童声',
    'neutral': '中性',
    'narrator': '旁白'
  }
  return labels[type] || type
}

// 获取声音类型颜色
const getVoiceTypeColor = (type) => {
  const colors = {
    'male': 'blue',
    'female': 'pink',
    'child': 'orange',
    'neutral': 'purple',
    'narrator': 'green'
  }
  return colors[type] || 'default'
}

// 格式化时间
const formatTime = (timeStr) => {
  if (!timeStr) return ''
  try {
    const date = new Date(timeStr)
    return date.toLocaleString('zh-CN')
  } catch {
    return timeStr
  }
}

// 获取当前应该使用的声音ID（优先用户选择，否则AI推荐）
const getCurrentVoiceId = (character) => {
  return props.voiceMapping[character.name] || character.voice_id
}
</script>

<style scoped>
.analysis-result-display {
  margin-top: 16px;
}

.plan-summary {
  margin-bottom: 16px;
  padding: 12px;
  background: #f8f9fa;
  border-radius: 6px;
}

.synthesis-segments {
  max-height: 500px;
  overflow-y: auto;
}

.segments-container {
  background: #fafafa;
  border-radius: 6px;
  padding: 12px;
}

.synthesis-segment-item {
  background: #fff;
  border: 1px solid #e8e8e8;
  padding: 12px;
  margin-bottom: 8px;
  border-radius: 6px;
  border-left: 4px solid #1890ff;
}

.segment-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
}

.segment-id {
  font-weight: bold;
  color: #666;
  font-size: 12px;
  min-width: 30px;
}

.segment-text {
  color: #333;
  line-height: 1.5;
  font-size: 14px;
  margin-bottom: 4px;
}

.segment-params {
  color: #666;
  font-size: 11px;
}

.character-preview-item.enhanced {
  background: #fff;
  border: 1px solid #e8e8e8;
  border-left: 4px solid #52c41a;
  padding: 16px;
  margin-bottom: 16px;
  border-radius: 6px;
}

.character-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.character-header h4 {
  margin: 0;
  color: #52c41a;
  font-weight: bold;
  font-size: 16px;
}

.character-tags {
  display: flex;
  gap: 4px;
}

.voice-config-section {
  background: #f8f9fa;
  padding: 12px;
  border-radius: 6px;
  border: 1px solid #e9ecef;
}

.ai-recommendation {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 12px;
}

.ai-label {
  font-size: 12px;
  font-weight: 500;
  color: #1890ff;
}

.voice-adjustment {
  margin-bottom: 8px;
}

.adjustment-label {
  display: block;
  font-size: 12px;
  font-weight: 500;
  color: #666;
  margin-bottom: 4px;
}

.voice-selector-inline {
  display: flex;
  align-items: center;
  gap: 8px;
}

.voice-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

.voice-name {
  font-weight: 500;
}

.ai-marker {
  color: #1890ff;
  margin-left: 4px;
}

.config-status {
  text-align: right;
}

.json-preview {
  background: #fff;
  padding: 16px;
  border-radius: 6px;
}

.raw-data-display {
  font-family: 'Courier New', monospace;
  font-size: 12px;
  background: #f6f8fa;
}

.config-description {
  margin-bottom: 16px;
}
</style>