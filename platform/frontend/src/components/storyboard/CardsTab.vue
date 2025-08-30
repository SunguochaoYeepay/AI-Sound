<template>
  <div class="cards-tab">
    <a-card title="卡片管理">
      <a-table 
        :columns="columns" 
        :data-source="cards" 
        :loading="loading"
        row-key="id"
      >
        <template #bodyCell="{ column, record }">
          <template v-if="column.key === 'card_type'">
            <a-tag :color="getCardTypeColor(record.card_type)">
              {{ getCardTypeName(record.card_type) }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'status'">
            <a-tag :color="record.is_confirmed ? 'green' : 'orange'">
              {{ record.is_confirmed ? '已确认' : '待确认' }}
            </a-tag>
          </template>
          <template v-else-if="column.key === 'action'">
            <a-space>
              <a-button size="small" @click="viewCard(record)">查看</a-button>
              <a-button 
                v-if="!record.is_confirmed"
                size="small" 
                type="primary"
                @click="confirmCard(record.id)"
              >
                确认
              </a-button>
              <a-button 
                size="small"
                @click="reanalyzeCard(record.id)"
              >
                重新分析
              </a-button>
            </a-space>
          </template>
        </template>
      </a-table>
    </a-card>

    <!-- 卡片详情抽屉 -->
    <CardDetailDrawer
      v-model:visible="cardDetailVisible"
      :card="selectedCard"
      @card-update="handleCardUpdate"
      @card-confirm="handleCardConfirm"
      @card-reanalyze="handleCardReanalyze"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { CARD_TYPE_CONFIG } from '@/api/storyboard'
import CardDetailDrawer from './CardDetailDrawer.vue'

defineProps({
  session: Object,
  cards: Array,
  loading: Boolean
})

const emit = defineEmits(['card-update', 'card-confirm', 'card-reanalyze'])

// 响应式数据
const cardDetailVisible = ref(false)
const selectedCard = ref(null)

const columns = [
  { title: 'ID', dataIndex: 'id', key: 'id', width: 80 },
  { title: '卡片类型', key: 'card_type', width: 120 },
  { title: '标题', dataIndex: 'title', key: 'title' },
  { title: '状态', key: 'status', width: 100 },
  { title: '操作', key: 'action', width: 200, fixed: 'right' }
]

const getCardTypeColor = (type) => {
  return CARD_TYPE_CONFIG[type]?.color || '#d9d9d9'
}

const getCardTypeName = (type) => {
  return CARD_TYPE_CONFIG[type]?.name || '未知类型'
}

const viewCard = (card) => {
  selectedCard.value = card
  cardDetailVisible.value = true
}

const confirmCard = (cardId) => {
  emit('card-confirm', cardId)
}

const reanalyzeCard = (cardId) => {
  emit('card-reanalyze', cardId)
}

const handleCardUpdate = (cardId, content) => {
  emit('card-update', cardId, content)
}

const handleCardConfirm = (cardId) => {
  emit('card-confirm', cardId)
}

const handleCardReanalyze = (cardId) => {
  emit('card-reanalyze', cardId)
}
</script>

<style scoped>
.cards-tab {
  padding: 16px;
}
</style>
