<template>
  <div>
    <!-- 🔥 批量创建角色抽屉 - 简化版：只创建角色信息 -->
    <a-drawer
      v-model:open="batchCreateModalVisible"
      title="🎭 批量添加角色到配音库"
      :width="800"
      placement="right"
      @close="cancelBatchCreate"
    >
      <div class="batch-create-content">
        <div
          class="drawer-footer"
          style="
            position: absolute;
            bottom: 0;
            left: 0;
            right: 0;
            padding: 16px;
            border-top: 1px solid var(--ant-border-color-split);
            background: var(--ant-component-background);
            z-index: 1000;
          "
        >
          <a-space style="float: right">
            <a-button @click="cancelBatchCreate">取消</a-button>
            <a-button
              type="primary"
              @click="executeBatchCreate"
              :disabled="selectedCharactersForBatch.length === 0 || batchCreating"
              :loading="batchCreating"
            >
              创建角色 ({{ selectedCharactersForBatch.length }}个)
            </a-button>
          </a-space>
        </div>

        <div
          class="batch-create-body"
          style="padding-bottom: var(--spacing-xxxl); max-height: calc(100vh - var(--spacing-xxxl) - var(--spacing-xxxl)); overflow-y: auto"
        >
          <div class="batch-description">
            <a-alert
              message="智能角色检测"
              :description="`AI已从章节中检测到 ${missingCharacters.length} 个尚未加入配音库的角色，您可以选择批量添加。音频和头像配置请在角色配音库中单独设置。`"
              type="info"
              show-icon
              style="margin-bottom: 16px"
            />
          </div>

          <div class="characters-selection">
            <div class="selection-header">
              <h4>选择要添加的角色</h4>
              <a-space>
                <a-button size="small" @click="selectAllMissingCharacters">全选</a-button>
                <a-button size="small" @click="deselectAllMissingCharacters">取消全选</a-button>
              </a-space>
            </div>

            <!-- 🔥 重构：使用表格显示角色列表 -->
            <div class="characters-table">
              <a-table
                :data-source="missingCharacters"
                :columns="characterTableColumns"
                :row-selection="characterRowSelection"
                :pagination="false"
                size="small"
                :scroll="{ y: 400 }"
                row-key="name"
              >
                <template #bodyCell="{ column, record }">
                  <template v-if="column.key === 'avatar'">
                    <a-avatar
                      :size="32"
                      :style="{ backgroundColor: '#8b5cf6' }"
                    >
                      {{ record.name?.charAt(0) || '?' }}
                    </a-avatar>
                  </template>

                  <template v-if="column.key === 'name'">
                    <div class="character-name-cell">
                      <div class="name">{{ record.name }}</div>
                      <div class="meta">
                        <a-tag size="small" :color="record.voice_type === 'male' ? 'blue' : record.voice_type === 'female' ? 'pink' : record.voice_type === 'narrator' ? 'orange' : 'default'">
                          {{ record.voice_type === 'male' ? '男性' : record.voice_type === 'female' ? '女性' : record.voice_type === 'narrator' ? '旁白' : '中性' }}
                        </a-tag>
                      </div>
                    </div>
                  </template>

                  <template v-if="column.key === 'count'">
                    <a-tag color="blue" size="small">{{ record.count }}次</a-tag>
                  </template>

                  <template v-if="column.key === 'description'">
                    <div class="description-cell">
                      {{ record.description || '暂无描述' }}
                    </div>
                  </template>
                </template>
              </a-table>
            </div>

            <!-- 🔥 简化：移除音频配置部分，只保留统一描述 -->
            <div class="unified-config" style="margin-top: 16px; padding: 16px; background: #f5f5f5; border-radius: 6px;">
              <h4>统一配置</h4>
              <a-form layout="vertical">
                <a-form-item label="统一描述（可选）">
                  <a-textarea
                    v-model:value="unifiedDescription"
                    placeholder="为所有选中的角色设置统一描述，留空则使用默认描述"
                    :rows="3"
                  />
                </a-form-item>
              </a-form>
            </div>
          </div>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { charactersAPI } from '@/api'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  missingCharacters: {
    type: Array,
    default: () => []
  },
  chapter: {
    type: Object,
    default: null
  },
  batchCreating: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits([
  'update:visible',
  'update:batchCreating',
  'characters-created',
  'close'
])

// 响应式数据
const batchCreateModalVisible = ref(false)
const selectedCharactersForBatch = ref([])
const unifiedDescription = ref('')

// 监听visible变化
watch(
  () => props.visible,
  (newVal) => {
    batchCreateModalVisible.value = newVal
    if (newVal) {
      // 重置状态
      selectedCharactersForBatch.value = []
      unifiedDescription.value = ''
    }
  }
)

// 监听抽屉状态变化
watch(batchCreateModalVisible, (newVal) => {
  emit('update:visible', newVal)
  if (!newVal) {
    emit('close')
  }
})

// 表格列配置
const characterTableColumns = [
  {
    title: '头像',
    key: 'avatar',
    width: 60,
    align: 'center'
  },
  {
    title: '角色名称',
    key: 'name',
    width: 200
  },
  {
    title: '出现次数',
    key: 'count',
    width: 100,
    align: 'center'
  },
  {
    title: '描述',
    key: 'description',
    ellipsis: true
  }
]

// 表格行选择配置
const characterRowSelection = computed(() => ({
  selectedRowKeys: selectedCharactersForBatch.value,
  onChange: (selectedRowKeys, selectedRows) => {
    selectedCharactersForBatch.value = selectedRowKeys
  }
}))

// 取消批量创建
const cancelBatchCreate = () => {
  batchCreateModalVisible.value = false
  selectedCharactersForBatch.value = []
  unifiedDescription.value = ''
  emit('close')
}

// 全选/取消全选
const selectAllMissingCharacters = () => {
  selectedCharactersForBatch.value = props.missingCharacters.map((char) => char.name)
}

const deselectAllMissingCharacters = () => {
  selectedCharactersForBatch.value = []
}

// 🔥 简化：直接执行批量创建，不包含音频配置
const executeBatchCreate = async () => {
  if (selectedCharactersForBatch.value.length === 0) {
    message.warning('请选择要添加的角色')
    return
  }

  if (!props.chapter?.book_id) {
    message.error('缺少书籍ID，无法创建角色')
    return
  }

  emit('update:batchCreating', true)
  try {


    // 🔥 简化：只创建角色基本信息，不包含音频文件
    const charactersToCreate = selectedCharactersForBatch.value.map((characterName) => {
      const character = props.missingCharacters.find((char) => char.name === characterName)
      return {
        name: character.name,
        description:
          unifiedDescription.value ||
          character.description ||
          `从第${props.chapter.number}章智能识别的角色`
      }
    })

    console.log('📝 准备创建的角色数据:', charactersToCreate)

    // 调用批量创建API（不包含文件）
    const formData = new FormData()
    formData.append('characters_data', JSON.stringify(charactersToCreate))
    formData.append('book_id', props.chapter.book_id)
    if (props.chapter.id) {
      formData.append('chapter_id', props.chapter.id)
    }

    const response = await charactersAPI.batchCreateCharacters(formData)

    console.log('✅ 批量创建角色响应:', response.data)

    if (response.data?.success) {
      const responseData = response.data.data || {}
      const createdCharacters = responseData.created_characters || []
      const failedCharacters = responseData.failed_characters || []

      console.log('📋 创建的角色:', createdCharacters)
      console.log('❌ 失败的角色:', failedCharacters)

      if (createdCharacters.length > 0) {
        message.success(
          `✅ 成功添加 ${createdCharacters.length} 个角色到配音库！${failedCharacters.length > 0 ? ` (失败 ${failedCharacters.length} 个角色)` : ''}`
        )
        
        // 提示用户去角色配音库配置音频
        message.info('💡 请在角色配音库中为这些角色配置音频和头像')
        
        // 通知父组件角色已创建
        console.log('[BatchCreateCharacterDrawer] 传递给父组件的角色数据:', createdCharacters)
        emit('characters-created', createdCharacters)
      } else {
        if (failedCharacters.length > 0) {
          const failedNames = failedCharacters.map(char => char.name).join('、')
          message.warning(`没有创建新角色，以下角色已存在：${failedNames}`)
        } else {
          message.warning('没有创建新角色，所选角色可能已存在')
        }
      }

      // 关闭抽屉
      batchCreateModalVisible.value = false
      selectedCharactersForBatch.value = []
      emit('close')
    } else {
      throw new Error(response.data?.message || '批量创建角色失败')
    }
  } catch (error) {
    console.error('❌ 批量创建角色失败:', error)
    let errorMessage = '未知错误'
    if (error.response?.data?.detail) {
      errorMessage = error.response.data.detail
    } else if (error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.response?.data?.error === 'http_error' && error.response?.data?.message) {
      errorMessage = error.response.data.message
    } else if (error.message) {
      errorMessage = error.message
    }
    message.error(`批量创建角色失败: ${errorMessage}`)
  } finally {
    emit('update:batchCreating', false)
  }
}
</script>

<style scoped>
.batch-create-content {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.batch-create-body {
  flex: 1;
  overflow-y: auto;
}

.batch-description {
  margin-bottom: 16px;
}

.characters-selection {
  flex: 1;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.selection-header h4 {
  margin: 0;
  color: var(--ant-text-color);
}

.characters-table {
  margin-bottom: 16px;
}

.character-name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.character-name-cell .name {
  font-weight: 500;
  color: var(--ant-text-color);
}

.character-name-cell .meta {
  display: flex;
  gap: 4px;
}

.description-cell {
  color: var(--ant-text-color-secondary);
  font-size: 12px;
}

.unified-config {
  border: 1px solid var(--ant-border-color-split);
}

.unified-config h4 {
  margin: 0 0 12px 0;
  color: var(--ant-text-color);
}
</style>