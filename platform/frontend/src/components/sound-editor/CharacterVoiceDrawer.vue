<template>
  <div class="character-voice-drawer">
    <div class="toolbar">
      <a-space>
        <a-button @click="handleSyncCharacters" :loading="isSyncing">
          <template #icon><reload-outlined /></template>
          同步角色
        </a-button>
        <a-button type="primary" @click="handleAutoMatch" :loading="isMatching">
          <template #icon><sync-outlined /></template>
          自动匹配
        </a-button>
        <!-- 其他按钮 -->
      </a-space>
    </div>
    
    <!-- 其他内容 -->
    
    <!-- 匹配结果弹窗 -->
    <CharacterMatchModal
      v-model:visible="matchModalVisible"
      :matchedCharacters="matchedCharacters"
      :unMatchedCharacters="unMatchedCharacters"
      @ok="handleMatchConfirm"
      @cancel="handleMatchCancel"
    />
  </div>
</template>

<script setup>
import { ref, defineEmits } from 'vue'
import { SyncOutlined, ReloadOutlined } from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'
import CharacterMatchModal from './CharacterMatchModal.vue'
import { useCharacterStore } from '@/stores/character'

const props = defineProps({
  bookId: {
    type: Number,
    required: true
  },
  chapterId: {
    type: Number,
    required: true
  }
})

const emit = defineEmits(['refresh'])

const characterStore = useCharacterStore()
const isSyncing = ref(false)
const isMatching = ref(false)
const matchModalVisible = ref(false)
const matchedCharacters = ref([])
const unMatchedCharacters = ref([])

const handleSyncCharacters = async () => {
  try {
    isSyncing.value = true
    
    // 同步角色记录
    const result = await characterStore.syncCharacters(props.bookId, props.chapterId)
    
    if (result.success) {
      message.success(result.message)
      emit('refresh')
    } else {
      message.error(result.message)
    }
  } catch (error) {
    message.error('同步失败：' + error.message)
  } finally {
    isSyncing.value = false
  }
}

const handleAutoMatch = async () => {
  try {
    isMatching.value = true
    
    // 调用后端API进行匹配
    const result = await characterStore.matchCharacters(props.bookId, props.chapterId)
    
    // 更新匹配结果
    matchedCharacters.value = result.matched_characters
    unMatchedCharacters.value = result.unmatched_characters
    
    // 显示匹配结果弹窗
    matchModalVisible.value = true
  } catch (error) {
    message.error('匹配失败：' + error.message)
  } finally {
    isMatching.value = false
  }
}

const handleMatchConfirm = async () => {
  try {
    // 应用匹配结果
    await characterStore.applyMatches(matchedCharacters.value)
    message.success('已应用匹配结果')
    matchModalVisible.value = false
    
    // 触发刷新
    emit('refresh')
  } catch (error) {
    message.error('应用匹配结果失败：' + error.message)
  }
}

const handleMatchCancel = () => {
  matchModalVisible.value = false
}
</script>

<style scoped>
.character-voice-drawer {
  padding: 16px;
}

.toolbar {
  margin-bottom: 16px;
}
</style> 