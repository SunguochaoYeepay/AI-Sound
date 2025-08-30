<template>
  <div class="quality-assessment">
    <a-card title="分析质量评估" :loading="loading">
      <template #extra>
        <a-button @click="refreshAssessment" :loading="loading">
          刷新评估
        </a-button>
      </template>

      <div v-if="assessmentData" class="assessment-content">
        <!-- 总体评分 -->
        <div class="overall-score">
          <h3>总体评分</h3>
          <div class="score-display">
            <a-progress
              type="circle"
              :percent="assessmentData.overall_score"
              :stroke-color="getScoreColor(assessmentData.overall_score)"
              :format="(percent) => `${percent}分`"
              size="120"
            />
            <div class="score-label">
              <div class="score-text">{{ getScoreLevel(assessmentData.overall_score) }}</div>
              <div class="score-description">{{ getScoreDescription(assessmentData.overall_score) }}</div>
            </div>
          </div>
        </div>

        <!-- 各类型卡片评分 -->
        <div class="card-type-scores">
          <h3>各类型卡片评分</h3>
          <a-row :gutter="16">
            <a-col :span="8" v-for="(stats, type) in assessmentData.card_type_scores" :key="type">
              <a-card size="small" class="type-score-card">
                <div class="type-header">
                  <a-tag :color="getCardTypeColor(type)">
                    {{ getCardTypeName(type) }}
                  </a-tag>
                  <span class="type-count">{{ stats.count }}张</span>
                </div>
                <div class="type-score">
                  <a-progress
                    :percent="stats.score"
                    :stroke-color="getScoreColor(stats.score)"
                    :format="(percent) => `${percent}分`"
                  />
                </div>
                <div class="type-details">
                  <div class="detail-item">
                    <span>已确认:</span>
                    <span class="confirmed-count">{{ stats.confirmed_count }}/{{ stats.count }}</span>
                  </div>
                  <div class="detail-item">
                    <span>平均置信度:</span>
                    <span>{{ Math.round((stats.total_confidence / stats.count) * 100) }}%</span>
                  </div>
                </div>
              </a-card>
            </a-col>
          </a-row>
        </div>

        <!-- 建议 -->
        <div class="recommendations">
          <h3>改进建议</h3>
          <a-list :data-source="assessmentData.recommendations" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <a-list-item-meta>
                  <template #avatar>
                    <a-icon type="bulb" style="color: #1890ff" />
                  </template>
                  <template #title>
                    {{ item }}
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </div>

        <!-- 统计信息 -->
        <div class="statistics">
          <h3>统计信息</h3>
          <a-row :gutter="16">
            <a-col :span="6">
              <a-statistic title="总卡片数" :value="assessmentData.total_cards" />
            </a-col>
            <a-col :span="6">
              <a-statistic 
                title="已确认卡片" 
                :value="getConfirmedCount()" 
                :value-style="{ color: '#52c41a' }"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic 
                title="待确认卡片" 
                :value="assessmentData.total_cards - getConfirmedCount()" 
                :value-style="{ color: '#faad14' }"
              />
            </a-col>
            <a-col :span="6">
              <a-statistic 
                title="确认率" 
                :value="getConfirmationRate()" 
                suffix="%" 
                :value-style="{ color: '#1890ff' }"
              />
            </a-col>
          </a-row>
        </div>
      </div>

      <div v-else-if="!loading" class="empty-state">
        <a-empty description="暂无质量评估数据" />
      </div>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { storyboardAPI } from '@/api/storyboard'
import { CARD_TYPE_CONFIG } from '@/api/storyboard'

const props = defineProps({
  sessionId: {
    type: Number,
    required: true
  }
})

// 响应式数据
const loading = ref(false)
const assessmentData = ref(null)

// 方法
const loadAssessment = async () => {
  if (!props.sessionId) return
  
  loading.value = true
  try {
    const response = await storyboardAPI.assessQuality(props.sessionId)
    assessmentData.value = response.data
  } catch (error) {
    message.error('加载质量评估失败')
    console.error('Load assessment error:', error)
  } finally {
    loading.value = false
  }
}

const refreshAssessment = () => {
  loadAssessment()
}

const getScoreColor = (score) => {
  if (score >= 80) return '#52c41a'
  if (score >= 60) return '#faad14'
  return '#ff4d4f'
}

const getScoreLevel = (score) => {
  if (score >= 80) return '优秀'
  if (score >= 60) return '良好'
  if (score >= 40) return '一般'
  return '较差'
}

const getScoreDescription = (score) => {
  if (score >= 80) return '分析质量很高，可以进入审核阶段'
  if (score >= 60) return '分析质量良好，建议部分优化'
  if (score >= 40) return '分析质量一般，需要重点改进'
  return '分析质量较低，建议重新分析'
}

const getCardTypeColor = (type) => {
  return CARD_TYPE_CONFIG[type]?.color || '#d9d9d9'
}

const getCardTypeName = (type) => {
  return CARD_TYPE_CONFIG[type]?.name || '未知类型'
}

const getConfirmedCount = () => {
  if (!assessmentData.value?.card_type_scores) return 0
  return Object.values(assessmentData.value.card_type_scores)
    .reduce((total, stats) => total + stats.confirmed_count, 0)
}

const getConfirmationRate = () => {
  const confirmed = getConfirmedCount()
  const total = assessmentData.value?.total_cards || 0
  return total > 0 ? Math.round((confirmed / total) * 100) : 0
}

// 监听会话ID变化
watch(() => props.sessionId, () => {
  if (props.sessionId) {
    loadAssessment()
  }
}, { immediate: true })

// 生命周期
onMounted(() => {
  if (props.sessionId) {
    loadAssessment()
  }
})
</script>

<style scoped>
.quality-assessment {
  padding: 16px;
}

.assessment-content {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.overall-score {
  text-align: center;
}

.overall-score h3 {
  margin-bottom: 16px;
  color: #262626;
}

.score-display {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 24px;
}

.score-label {
  text-align: left;
}

.score-text {
  font-size: 18px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 8px;
}

.score-description {
  color: #666;
  font-size: 14px;
  line-height: 1.4;
}

.card-type-scores h3 {
  margin-bottom: 16px;
  color: #262626;
}

.type-score-card {
  margin-bottom: 16px;
}

.type-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.type-count {
  font-size: 12px;
  color: #666;
}

.type-score {
  margin-bottom: 12px;
}

.type-details {
  font-size: 12px;
  color: #666;
}

.detail-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 4px;
}

.confirmed-count {
  color: #52c41a;
  font-weight: 500;
}

.recommendations h3 {
  margin-bottom: 16px;
  color: #262626;
}

.statistics h3 {
  margin-bottom: 16px;
  color: #262626;
}

.empty-state {
  text-align: center;
  padding: 40px 0;
}
</style>
