<template>
  <a-drawer
    :open="visible"
    :title="cardTitle"
    placement="right"
    width="600px"
    @close="handleClose"
  >
    <div v-if="card" class="card-detail">
      <!-- 卡片基本信息 -->
      <div class="card-header">
        <a-tag :color="getCardTypeColor(card.card_type)">
          {{ getCardTypeName(card.card_type) }}
        </a-tag>
        <a-tag :color="card.is_confirmed ? 'green' : 'orange'">
          {{ card.is_confirmed ? '已确认' : '待确认' }}
        </a-tag>
      </div>

      <!-- 卡片内容 -->
      <div class="card-content">
        <a-tabs v-model:activeKey="activeTab">
          <a-tab-pane key="content" tab="内容">
            <div class="content-section">
              <h4>卡片内容</h4>
              <a-textarea
                v-model:value="editedContent"
                :rows="10"
                placeholder="卡片内容..."
                :readonly="!isEditing"
              />
            </div>
          </a-tab-pane>
          
          <a-tab-pane key="relationships" tab="关系">
            <div class="relationships-section">
              <h4>关联关系</h4>
              <pre>{{ JSON.stringify(card.relationships, null, 2) }}</pre>
            </div>
          </a-tab-pane>
          
          <a-tab-pane key="metadata" tab="元数据">
            <div class="metadata-section">
              <h4>元数据</h4>
              <a-descriptions :column="1" bordered>
                <a-descriptions-item label="卡片ID">{{ card.id }}</a-descriptions-item>
                <a-descriptions-item label="会话ID">{{ card.session_id }}</a-descriptions-item>
                <a-descriptions-item label="章节ID">{{ card.chapter_id || '无' }}</a-descriptions-item>
                <a-descriptions-item label="置信度">{{ card.confidence_score }}</a-descriptions-item>
                <a-descriptions-item label="创建时间">{{ formatDate(card.created_at) }}</a-descriptions-item>
                <a-descriptions-item label="更新时间">{{ formatDate(card.updated_at) }}</a-descriptions-item>
              </a-descriptions>
            </div>
          </a-tab-pane>
        </a-tabs>
      </div>

      <!-- 操作按钮 -->
      <div class="card-actions">
        <a-space>
          <a-button
            v-if="!isEditing"
            type="primary"
            @click="startEdit"
          >
            编辑
          </a-button>
          <a-button
            v-if="isEditing"
            type="primary"
            @click="saveEdit"
            :loading="saving"
          >
            保存
          </a-button>
          <a-button
            v-if="isEditing"
            @click="cancelEdit"
          >
            取消
          </a-button>
          <a-button
            v-if="!card.is_confirmed"
            type="success"
            @click="confirmCard"
            :loading="confirming"
          >
            确认
          </a-button>
          <a-button
            @click="reanalyzeCard"
            :loading="reanalyzing"
          >
            重新分析
          </a-button>
        </a-space>
      </div>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { CARD_TYPE_CONFIG } from '@/api/storyboard'

const props = defineProps({
  visible: Boolean,
  card: Object
})

const emit = defineEmits(['update:visible', 'card-update', 'card-confirm', 'card-reanalyze'])

// 响应式数据
const activeTab = ref('content')
const isEditing = ref(false)
const editedContent = ref('')
const saving = ref(false)
const confirming = ref(false)
const reanalyzing = ref(false)

// 计算属性
const cardTitle = computed(() => {
  if (!props.card) return '卡片详情'
  return `${getCardTypeName(props.card.card_type)} - ${props.card.id}`
})

// 监听卡片变化
watch(() => props.card, (newCard) => {
  if (newCard) {
    editedContent.value = JSON.stringify(newCard.content, null, 2)
    isEditing.value = false
  }
}, { immediate: true })

// 方法
const getCardTypeColor = (type) => {
  return CARD_TYPE_CONFIG[type]?.color || '#d9d9d9'
}

const getCardTypeName = (type) => {
  return CARD_TYPE_CONFIG[type]?.name || '未知类型'
}

const formatDate = (dateString) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN')
}

const handleClose = () => {
  emit('update:visible', false)
  isEditing.value = false
}

const startEdit = () => {
  isEditing.value = true
}

const cancelEdit = () => {
  isEditing.value = false
  editedContent.value = JSON.stringify(props.card.content, null, 2)
}

const saveEdit = async () => {
  try {
    saving.value = true
    
    let newContent
    try {
      newContent = JSON.parse(editedContent.value)
    } catch (e) {
      message.error('JSON格式错误，请检查内容')
      return
    }
    
    emit('card-update', props.card.id, newContent)
    isEditing.value = false
    message.success('卡片已更新')
  } catch (error) {
    message.error('更新失败: ' + error.message)
  } finally {
    saving.value = false
  }
}

const confirmCard = async () => {
  try {
    confirming.value = true
    emit('card-confirm', props.card.id)
    message.success('卡片已确认')
  } catch (error) {
    message.error('确认失败: ' + error.message)
  } finally {
    confirming.value = false
  }
}

const reanalyzeCard = async () => {
  try {
    reanalyzing.value = true
    emit('card-reanalyze', props.card.id)
    message.success('重新分析已开始')
  } catch (error) {
    message.error('重新分析失败: ' + error.message)
  } finally {
    reanalyzing.value = false
  }
}
</script>

<style scoped>
.card-detail {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.card-header {
  margin-bottom: 16px;
  display: flex;
  gap: 8px;
}

.card-content {
  flex: 1;
  overflow-y: auto;
}

.content-section,
.relationships-section,
.metadata-section {
  margin-bottom: 16px;
}

.content-section h4,
.relationships-section h4,
.metadata-section h4 {
  margin-bottom: 8px;
  font-weight: 500;
}

.card-actions {
  margin-top: 16px;
  padding-top: 16px;
  border-top: 1px solid #f0f0f0;
  display: flex;
  justify-content: flex-end;
}

pre {
  background: #f5f5f5;
  padding: 12px;
  border-radius: 4px;
  font-size: 12px;
  overflow-x: auto;
}
</style>
