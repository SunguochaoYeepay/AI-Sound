<template>
  <div class="overview-tab">
    <a-card title="分析概览">
      <template #extra>
                 <a-space>
           <a-button @click="handleExportSessionReport">导出报告</a-button>
           <a-button @click="exportCardsData">导出卡片</a-button>
         </a-space>
      </template>
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic title="总卡片数" :value="cards?.length || 0" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="已确认" :value="confirmedCount" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="待确认" :value="pendingCount" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="章节数" :value="session?.total_chapters || 0" />
        </a-col>
      </a-row>
      
      <!-- 卡片类型分布 -->
      <div class="card-type-distribution">
        <h4>卡片类型分布</h4>
        <a-row :gutter="16">
          <a-col :span="4" v-for="type in cardTypes" :key="type">
            <a-card size="small" class="type-card">
              <a-statistic 
                :title="type.name" 
                :value="type.count"
                :value-style="{ color: type.color }"
              />
            </a-card>
          </a-col>
        </a-row>
      </div>
      
             <!-- 分析进度 -->
       <div class="analysis-progress" v-if="session">
         <h4>分析进度</h4>
         <a-progress 
           :percent="session.progress || 0" 
           :status="getProgressStatus(session.status)"
           :stroke-color="getProgressColor(session.status)"
         />
         <div class="progress-details">
           <span>已分析章节: {{ session.analyzed_chapters || 0 }}/{{ session.total_chapters || 0 }}</span>
           <span v-if="session.current_step">当前步骤: {{ session.current_step }}</span>
         </div>
       </div>

       <!-- 质量评估 -->
       <div class="quality-assessment-section" v-if="session && session.status === 'completed'">
         <h4>质量评估</h4>
         <QualityAssessment :session-id="session.id" />
       </div>
     </a-card>
   </div>
 </template>

<script setup>
import { computed } from 'vue'
import { message } from 'ant-design-vue'
import { CARD_TYPE_CONFIG } from '@/api/storyboard'
import { exportSessionReport, exportSessionCards } from '@/utils/exportUtils'
import QualityAssessment from './QualityAssessment.vue'

const props = defineProps({
  session: Object,
  cards: Array,
  loading: Boolean
})

const confirmedCount = computed(() => 
  props.cards?.filter(c => c.is_confirmed)?.length || 0
)

const pendingCount = computed(() => 
  props.cards?.filter(c => !c.is_confirmed)?.length || 0
)

const cardTypes = computed(() => {
  if (!props.cards) return []
  
  const typeCounts = {}
  props.cards.forEach(card => {
    typeCounts[card.card_type] = (typeCounts[card.card_type] || 0) + 1
  })
  
  return Object.entries(typeCounts).map(([type, count]) => ({
    type,
    name: CARD_TYPE_CONFIG[type]?.name || '未知类型',
    color: CARD_TYPE_CONFIG[type]?.color || '#d9d9d9',
    count
  }))
})

const getProgressStatus = (status) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed' || status === 'confirmed') return 'success'
  if (status === 'analyzing') return 'active'
  return 'normal'
}

const getProgressColor = (status) => {
  if (status === 'failed') return '#ff4d4f'
  if (status === 'completed' || status === 'confirmed') return '#52c41a'
  if (status === 'analyzing') return '#1890ff'
  return '#d9d9d9'
}

const handleExportSessionReport = () => {
  try {
    // 这里需要传入章节数据，暂时使用空数组
    exportSessionReport(props.session, props.cards || [], [])
    message.success('会话报告导出成功')
  } catch (error) {
    message.error('导出失败: ' + error.message)
    console.error('Export error:', error)
  }
}

const exportCardsData = () => {
  try {
    exportSessionCards(props.cards || [], props.session?.session_name || '未知会话')
    message.success('卡片数据导出成功')
  } catch (error) {
    message.error('导出失败: ' + error.message)
    console.error('Export error:', error)
  }
}
</script>

<style scoped>
.overview-tab {
  padding: 16px;
}

.card-type-distribution {
  margin-top: 24px;
}

.card-type-distribution h4 {
  margin-bottom: 16px;
  font-weight: 500;
}

.type-card {
  text-align: center;
}

.analysis-progress {
  margin-top: 24px;
}

.analysis-progress h4 {
  margin-bottom: 16px;
  font-weight: 500;
}

.progress-details {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  font-size: 14px;
  color: #666;
}

.quality-assessment-section {
  margin-top: 24px;
}

.quality-assessment-section h4 {
  margin-bottom: 16px;
  font-weight: 500;
}
</style>
