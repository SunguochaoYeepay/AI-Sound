<template>
  <div class="image-generation-stats">
    <a-row :gutter="16">
      <!-- 总体统计卡片 -->
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="总任务数"
            :value="stats.total_tasks || 0"
            :value-style="{ color: '#1890ff' }"
          >
            <template #prefix>
              <FileImageOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="已完成"
            :value="completedCount"
            :value-style="{ color: '#52c41a' }"
          >
            <template #prefix>
              <CheckCircleOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="处理中"
            :value="processingCount"
            :value-style="{ color: '#faad14' }"
          >
            <template #prefix>
              <LoadingOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
      
      <a-col :span="6">
        <a-card>
          <a-statistic
            title="失败"
            :value="failedCount"
            :value-style="{ color: '#ff4d4f' }"
          >
            <template #prefix>
              <ExclamationCircleOutlined />
            </template>
          </a-statistic>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 进度条和详细信息 -->
    <a-row :gutter="16" style="margin-top: 16px">
      <a-col :span="12">
        <a-card title="完成进度" size="small">
          <a-progress
            :percent="completionPercent"
            :stroke-color="{
              '0%': '#108ee9',
              '100%': '#87d068'
            }"
            :show-info="true"
          />
          <div style="margin-top: 8px">
            <a-tag color="green">已完成: {{ completedCount }}</a-tag>
            <a-tag color="blue">处理中: {{ processingCount }}</a-tag>
            <a-tag color="default">等待中: {{ pendingCount }}</a-tag>
            <a-tag color="red">失败: {{ failedCount }}</a-tag>
          </div>
        </a-card>
      </a-col>
      
      <a-col :span="12">
        <a-card title="质量统计" size="small">
          <div class="quality-stats">
            <div class="stat-item">
              <span class="label">平均评分:</span>
              <a-rate 
                :value="averageRating" 
                :disabled="true"
                :allow-half="true"
                style="font-size: 14px"
              />
              <span class="value">{{ averageRating.toFixed(1) }}</span>
            </div>
            
            <div class="stat-item">
              <span class="label">通过率:</span>
              <span class="value">{{ approvalRate.toFixed(1) }}%</span>
              <a-progress 
                :percent="approvalRate" 
                size="small" 
                :show-info="false"
                stroke-color="#52c41a"
              />
            </div>
            
            <div class="stat-item">
              <span class="label">平均生成时间:</span>
              <span class="value">{{ averageGenerationTime.toFixed(1) }}秒</span>
            </div>
          </div>
        </a-card>
      </a-col>
    </a-row>
    
    <!-- 状态分布饼图 -->
    <a-row style="margin-top: 16px">
      <a-col :span="24">
        <a-card title="状态分布" size="small">
          <div class="status-chart">
            <canvas ref="chartCanvas" width="400" height="200"></canvas>
          </div>
        </a-card>
      </a-col>
    </a-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { 
  FileImageOutlined, 
  CheckCircleOutlined, 
  LoadingOutlined, 
  ExclamationCircleOutlined 
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  stats: {
    type: Object,
    default: () => ({})
  }
})

// Reactive data
const chartCanvas = ref(null)

// Computed properties
const totalTasks = computed(() => props.stats.total_tasks || 0)
const statusBreakdown = computed(() => props.stats.status_breakdown || {})

const completedCount = computed(() => statusBreakdown.value.completed || 0)
const processingCount = computed(() => statusBreakdown.value.processing || 0)
const pendingCount = computed(() => statusBreakdown.value.pending || 0)
const failedCount = computed(() => statusBreakdown.value.failed || 0)

const completionPercent = computed(() => {
  if (totalTasks.value === 0) return 0
  return Math.round((completedCount.value / totalTasks.value) * 100)
})

const averageRating = computed(() => {
  const tasks = props.stats.tasks || []
  const ratedTasks = tasks.filter(task => task.user_rating && task.user_rating > 0)
  
  if (ratedTasks.length === 0) return 0
  
  const totalRating = ratedTasks.reduce((sum, task) => sum + task.user_rating, 0)
  return totalRating / ratedTasks.length
})

const approvalRate = computed(() => {
  const tasks = props.stats.tasks || []
  const completedTasks = tasks.filter(task => task.status === 'completed')
  
  if (completedTasks.length === 0) return 0
  
  const approvedTasks = completedTasks.filter(task => task.is_approved === true)
  return (approvedTasks.length / completedTasks.length) * 100
})

const averageGenerationTime = computed(() => {
  const tasks = props.stats.tasks || []
  const completedTasks = tasks.filter(task => 
    task.status === 'completed' && task.generation_time
  )
  
  if (completedTasks.length === 0) return 0
  
  const totalTime = completedTasks.reduce((sum, task) => sum + task.generation_time, 0)
  return totalTime / completedTasks.length
})

// Methods
const drawStatusChart = () => {
  if (!chartCanvas.value) return
  
  const canvas = chartCanvas.value
  const ctx = canvas.getContext('2d')
  
  // 清空画布
  ctx.clearRect(0, 0, canvas.width, canvas.height)
  
  // 数据
  const data = [
    { label: '已完成', value: completedCount.value, color: '#52c41a' },
    { label: '处理中', value: processingCount.value, color: '#faad14' },
    { label: '等待中', value: pendingCount.value, color: '#d9d9d9' },
    { label: '失败', value: failedCount.value, color: '#ff4d4f' }
  ]
  
  const total = data.reduce((sum, item) => sum + item.value, 0)
  
  if (total === 0) {
    // 绘制空状态
    ctx.fillStyle = '#f0f0f0'
    ctx.font = '16px Arial'
    ctx.textAlign = 'center'
    ctx.fillText('暂无数据', canvas.width / 2, canvas.height / 2)
    return
  }
  
  // 绘制饼图
  const centerX = canvas.width / 2
  const centerY = canvas.height / 2
  const radius = Math.min(centerX, centerY) - 40
  
  let startAngle = 0
  
  data.forEach((item, index) => {
    if (item.value === 0) return
    
    const sliceAngle = (item.value / total) * 2 * Math.PI
    
    // 绘制扇形
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.arc(centerX, centerY, radius, startAngle, startAngle + sliceAngle)
    ctx.closePath()
    ctx.fillStyle = item.color
    ctx.fill()
    
    // 绘制标签
    const labelAngle = startAngle + sliceAngle / 2
    const labelX = centerX + Math.cos(labelAngle) * (radius + 20)
    const labelY = centerY + Math.sin(labelAngle) * (radius + 20)
    
    ctx.fillStyle = '#333'
    ctx.font = '12px Arial'
    ctx.textAlign = 'center'
    ctx.fillText(`${item.label}: ${item.value}`, labelX, labelY)
    
    startAngle += sliceAngle
  })
}

// Lifecycle
onMounted(() => {
  drawStatusChart()
})

// Watch for stats changes
watch(() => props.stats, () => {
  setTimeout(() => {
    drawStatusChart()
  }, 100)
}, { deep: true })
</script>

<style scoped>
.image-generation-stats {
  .quality-stats {
    .stat-item {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
      
      .label {
        min-width: 80px;
        font-weight: 500;
      }
      
      .value {
        margin-left: 8px;
        font-weight: 600;
        color: #1890ff;
      }
      
      .ant-progress {
        flex: 1;
        margin: 0 8px;
      }
    }
  }
  
  .status-chart {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 200px;
  }
}

:deep(.ant-card-head) {
  padding: 0 12px;
}

:deep(.ant-card-body) {
  padding: 12px;
}

:deep(.ant-statistic-title) {
  font-size: 12px;
  margin-bottom: 4px;
}

:deep(.ant-statistic-content) {
  font-size: 18px;
}
</style> 