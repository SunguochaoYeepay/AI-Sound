<template>
  <div class="chapters-tab">
    <a-card title="章节列表">
      <a-table 
        :columns="columns" 
        :data-source="chapters" 
        :loading="loading"
        row-key="chapter_id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'chapter_title'">
            <div class="chapter-info">
              <div class="chapter-title">{{ record.chapter_title }}</div>
              <div class="chapter-number">第{{ record.chapter_number }}章</div>
            </div>
          </template>
          
          <template v-else-if="column.key === 'word_count'">
            <span>{{ record.word_count }} 字</span>
          </template>
          
          <template v-else-if="column.key === 'analysis_status'">
            <a-tag :color="getStatusColor(record.analysis_status)">
              {{ getStatusText(record.analysis_status) }}
            </a-tag>
          </template>
          
          <template v-else-if="column.key === 'analysis_progress'">
            <a-progress 
              :percent="record.analysis_progress" 
              :status="getProgressStatus(record.analysis_status)"
              size="small"
            />
          </template>
          
          <template v-else-if="column.key === 'card_count'">
            <div class="card-count">
              <span class="count-number">{{ record.card_count }}</span>
              <span class="count-label">张卡片</span>
            </div>
          </template>
          
          <template v-else-if="column.key === 'card_types'">
            <div class="card-types">
              <a-tag 
                v-if="record.story_card" 
                size="small" 
                color="#fa8c16"
              >
                故事
              </a-tag>
              <a-tag 
                v-if="record.character_cards?.length" 
                size="small" 
                color="#1890ff"
              >
                角色({{ record.character_cards.length }})
              </a-tag>
              <a-tag 
                v-if="record.scene_cards?.length" 
                size="small" 
                color="#52c41a"
              >
                场景({{ record.scene_cards.length }})
              </a-tag>
              <a-tag 
                v-if="record.event_cards?.length" 
                size="small" 
                color="#722ed1"
              >
                事件({{ record.event_cards.length }})
              </a-tag>
              <a-tag 
                v-if="record.emotion_cards?.length" 
                size="small" 
                color="#eb2f96"
              >
                情绪({{ record.emotion_cards.length }})
              </a-tag>
              <a-tag 
                v-if="record.storyboard_card" 
                size="small" 
                color="#13c2c2"
              >
                分镜
              </a-tag>
            </div>
          </template>
          
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button 
                size="small" 
                @click="viewChapterCards(record)"
              >
                查看卡片
              </a-button>
              <a-button 
                v-if="record.analysis_status === 'pending'"
                size="small" 
                type="primary"
                @click="analyzeChapter(record.chapter_id)"
              >
                开始分析
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import { storyboardAPI } from '@/api/storyboard'

const props = defineProps({
  sessionId: String,
  loading: Boolean
})

const emit = defineEmits(['chapter-analyze'])

// 响应式数据
const chapters = ref([])
const chaptersLoading = ref(false)

// 表格列定义
const columns = [
  { 
    title: '章节', 
    key: 'chapter_title', 
    width: 200,
    fixed: 'left'
  },
  { 
    title: '字数', 
    key: 'word_count', 
    width: 100 
  },
  { 
    title: '分析状态', 
    key: 'analysis_status', 
    width: 120 
  },
  { 
    title: '进度', 
    key: 'analysis_progress', 
    width: 150 
  },
  { 
    title: '卡片数', 
    key: 'card_count', 
    width: 100 
  },
  { 
    title: '卡片类型', 
    key: 'card_types', 
    width: 300 
  },
  { 
    title: '操作', 
    key: 'action', 
    width: 150,
    fixed: 'right'
  }
]

// 方法
const loadChapters = async () => {
  if (!props.sessionId) return
  
  try {
    chaptersLoading.value = true
    const response = await storyboardAPI.getSessionChapters(props.sessionId)
    chapters.value = response.data.chapters || []
  } catch (error) {
    message.error('加载章节列表失败')
    console.error('Load chapters error:', error)
  } finally {
    chaptersLoading.value = false
  }
}

const getStatusColor = (status) => {
  const colors = {
    'pending': '#faad14',
    'analyzing': '#1890ff',
    'completed': '#52c41a',
    'failed': '#ff4d4f'
  }
  return colors[status] || '#d9d9d9'
}

const getStatusText = (status) => {
  const texts = {
    'pending': '待分析',
    'analyzing': '分析中',
    'completed': '已完成',
    'failed': '分析失败'
  }
  return texts[status] || '未知状态'
}

const getProgressStatus = (status) => {
  if (status === 'failed') return 'exception'
  if (status === 'completed') return 'success'
  if (status === 'analyzing') return 'active'
  return 'normal'
}

const viewChapterCards = (chapter) => {
  // TODO: 实现查看章节卡片功能
  message.info(`查看第${chapter.chapter_number}章卡片`)
}

const analyzeChapter = (chapterId) => {
  emit('chapter-analyze', chapterId)
}

// 生命周期
onMounted(() => {
  loadChapters()
})
</script>

<style scoped>
.chapters-tab {
  padding: 16px;
}

.chapter-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.chapter-title {
  font-weight: 500;
  color: #262626;
}

.chapter-number {
  font-size: 12px;
  color: #666;
}

.card-count {
  display: flex;
  align-items: center;
  gap: 4px;
}

.count-number {
  font-weight: 500;
  color: #1890ff;
}

.count-label {
  font-size: 12px;
  color: #666;
}

.card-types {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}
</style>
