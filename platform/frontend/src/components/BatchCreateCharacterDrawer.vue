<template>
  <div>
    <!-- 🔥 批量创建角色抽屉 - 第一步：选择角色 -->
    <a-drawer
      v-model:open="batchCreateModalVisible"
      title="🎭 批量添加角色到配音库 - 选择角色"
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
              @click="goToAudioConfig"
              :disabled="selectedCharactersForBatch.length === 0"
            >
              下一步：配置音频 ({{ selectedCharactersForBatch.length }}个角色)
            </a-button>
          </a-space>
        </div>

        <div
          class="batch-create-body"
          style="padding-bottom: 80px; max-height: calc(100vh - 120px); overflow-y: auto"
        >
          <div class="batch-description">
            <a-alert
              message="智能角色检测"
              :description="`AI已从章节中检测到 ${missingCharacters.length} 个尚未加入配音库的角色，您可以选择批量添加并配置语音。`"
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
          </div>

          <div v-if="selectedCharactersForBatch.length > 0" class="batch-summary">
            <a-divider />
            <div class="summary-info">
              <h4>📋 批量操作摘要</h4>
              <p>
                将创建 <strong>{{ selectedCharactersForBatch.length }}</strong> 个新角色到
                <strong>{{ chapter?.book_id ? '角色配音库' : '当前书籍' }}</strong>
              </p>
              <p class="summary-note">
                💡 创建完成后，这些角色将自动关联到合成计划中，您就可以立即开始语音合成了！
              </p>
            </div>
          </div>
        </div>
      </div>
    </a-drawer>

    <!-- 🔥 第二个抽屉 - 统一音频配置 -->
    <a-drawer
      :open="audioConfigModalVisible"
      title="🎧 统一配置音频文件"
      :width="700"
      placement="right"
      @close="cancelAudioConfig"
    >
      <div class="audio-config-content">
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
            <a-button @click="cancelAudioConfig">取消</a-button>
            <a-button @click="goBackToCharacterSelection">上一步</a-button>
            <a-button type="primary" @click="executeBatchCreate" :loading="batchCreating">
              创建 {{ selectedCharactersForBatch.length }} 个角色
            </a-button>
          </a-space>
        </div>

        <div
          class="audio-config-body"
          style="padding-bottom: 80px; max-height: calc(100vh - 120px); overflow-y: auto"
        >
          <!-- 选中角色摘要 -->
          <div class="selected-characters-summary">
            <a-alert
              message="即将创建的角色"
              :description="`已选择 ${selectedCharactersForBatch.length} 个角色：${selectedCharactersForBatch.join('、')}`"
              type="info"
              show-icon
              style="margin-bottom: 20px"
            />
          </div>

          <!-- 统一音频配置 -->
          <div class="unified-audio-config">
            <h3>🎧 统一音频配置</h3>
            <p class="config-description">
              为所有选中的角色设置相同的语音配置。如果某些角色需要个性化设置，您可以在创建后到角色配音库中单独修改。
            </p>

            <a-form layout="vertical" size="middle">
              <a-row :gutter="16">
                <a-col :span="12">
                  <a-form-item label="默认声音类型">
                    <a-select
                      v-model="unifiedVoiceType"
                      :options="voiceTypeOptions"
                      placeholder="选择默认声音类型"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="12">
                  <a-form-item label="默认描述">
                    <a-input
                      v-model="unifiedDescription"
                      placeholder="如：温柔女声、沉稳男声等"
                    />
                  </a-form-item>
                </a-col>
              </a-row>

              <!-- 音频文件上传 -->
              <a-form-item label="统一语音示例文件（可选，用于声音克隆）">
                <div class="unified-audio-upload">
                  <a-row :gutter="16">
                    <a-col :span="12">
                      <a-form-item label="WAV 音频文件">
                        <a-upload
                          v-model="unifiedWavFileList"
                          name="unified_wav_file"
                          accept=".wav"
                          :max-count="1"
                          :before-upload="() => false"
                          @change="handleUnifiedFileChange($event, 'wav')"
                        >
                          <a-button size="large" type="dashed" style="width: 100%; height: 80px">
                            <div style="text-align: center">
                              <div>📁</div>
                              <div>选择 WAV 文件</div>
                              <div style="font-size: 12px; color: #666">将应用到所有角色</div>
                            </div>
                          </a-button>
                        </a-upload>
                      </a-form-item>
                    </a-col>
                    <a-col :span="12">
                      <a-form-item label="NPY 特征文件">
                        <a-upload
                          v-model="unifiedNpyFileList"
                          name="unified_npy_file"
                          accept=".npy"
                          :max-count="1"
                          :before-upload="() => false"
                          @change="handleUnifiedFileChange($event, 'npy')"
                        >
                          <a-button size="large" type="dashed" style="width: 100%; height: 80px">
                            <div style="text-align: center">
                              <div>📊</div>
                              <div>选择 NPY 文件</div>
                              <div style="font-size: 12px; color: #666">将应用到所有角色</div>
                            </div>
                          </a-button>
                        </a-upload>
                      </a-form-item>
                    </a-col>
                  </a-row>

                  <div class="upload-tips">
                    <a-alert
                      message="💡 统一配置说明"
                      description="上传的音频文件将作为所有选中角色的默认语音示例。WAV格式要求：单声道, 16kHz-48kHz采样率。NPY文件为对应的音频特征文件。"
                      type="info"
                      show-icon
                    />
                  </div>
                </div>
              </a-form-item>
            </a-form>
          </div>
        </div>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { charactersAPI } from '@/api'

const props = defineProps({
  // 章节信息
  chapter: {
    type: Object,
    default: null
  },
  // 缺失的角色列表
  missingCharacters: {
    type: Array,
    default: () => []
  },
  // 是否显示批量创建抽屉
  visible: {
    type: Boolean,
    default: false
  },
  // 批量创建状态
  batchCreating: {
    type: Boolean,
    default: false
  }
})

const emit = defineEmits([
  'update:visible',
  'update:batchCreating', 
  'characters-created',
  'refresh-library',
  'close'
])

// 响应式状态
const batchCreateModalVisible = computed({
  get: () => {
    console.log('[BatchCreateCharacterDrawer] batchCreateModalVisible get:', props.visible)
    return props.visible
  },
  set: (value) => {
    console.log('[BatchCreateCharacterDrawer] batchCreateModalVisible set:', value)
    emit('update:visible', value)
  }
})

const selectedCharactersForBatch = ref([])
const audioConfigModalVisible = ref(false)
const unifiedVoiceType = ref('neutral')
const unifiedDescription = ref('')
const unifiedWavFileList = ref([])
const unifiedNpyFileList = ref([])
const unifiedWavFile = ref(null)
const unifiedNpyFile = ref(null)

// 🔥 语音类型选项
const voiceTypeOptions = [
  { label: '男声', value: 'male' },
  { label: '女声', value: 'female' },
  { label: '童声', value: 'child' },
  { label: '中性', value: 'neutral' },
  { label: '旁白', value: 'narrator' }
]

// 🔥 角色表格列配置
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
    width: 150
  },
  {
    title: '出现次数',
    key: 'count',
    width: 100,
    align: 'center'
  },
  {
    title: '角色描述',
    key: 'description',
    ellipsis: true
  }
]

// 🔥 表格行选择配置
const characterRowSelection = {
  selectedRowKeys: selectedCharactersForBatch,
  onChange: (selectedRowKeys) => {
    selectedCharactersForBatch.value = selectedRowKeys
    console.log('📋 选中角色:', selectedRowKeys)
  },
  onSelectAll: (selected, selectedRows) => {
    console.log(
      '📋 全选操作:',
      selected,
      selectedRows.map((r) => r.name)
    )
  }
}

// 方法定义
const showBatchCreateModal = () => {
  // 初始化缺失角色的配置
  props.missingCharacters.forEach((char) => {
    char.selected_voice_type = char.voice_type || 'neutral'
    char.description = char.description || ''
  })
  selectedCharactersForBatch.value = []
  batchCreateModalVisible.value = true
}

const cancelBatchCreate = () => {
  batchCreateModalVisible.value = false
  selectedCharactersForBatch.value = []
  emit('close')
}

// 🔥 进入音频配置步骤
const goToAudioConfig = () => {
  if (selectedCharactersForBatch.value.length === 0) {
    message.warning('请先选择要创建的角色')
    return
  }

  // 关闭第一个抽屉，打开第二个抽屉
  batchCreateModalVisible.value = false
  audioConfigModalVisible.value = true

  // 重置统一配置
  unifiedVoiceType.value = 'neutral'
  unifiedDescription.value = ''
  unifiedWavFileList.value = []
  unifiedNpyFileList.value = []
  unifiedWavFile.value = null
  unifiedNpyFile.value = null
}

// 🔥 取消音频配置
const cancelAudioConfig = () => {
  audioConfigModalVisible.value = false
  selectedCharactersForBatch.value = []
  // 重置配置
  unifiedVoiceType.value = 'neutral'
  unifiedDescription.value = ''
  unifiedWavFileList.value = []
  unifiedNpyFileList.value = []
  emit('close')
}

// 🔥 返回角色选择
const goBackToCharacterSelection = () => {
  audioConfigModalVisible.value = false
  batchCreateModalVisible.value = true
}

const selectAllMissingCharacters = () => {
  selectedCharactersForBatch.value = props.missingCharacters.map((char) => char.name)
}

const deselectAllMissingCharacters = () => {
  selectedCharactersForBatch.value = []
}

// 🔥 统一文件上传处理
const handleUnifiedFileChange = (info, fileType) => {
  console.log(`📁 统一文件变化 - 类型: ${fileType}`, info)

  if (fileType === 'wav') {
    unifiedWavFileList.value = info.fileList.slice(-1) // 保持最新的一个文件
    unifiedWavFile.value =
      unifiedWavFileList.value.length > 0 ? unifiedWavFileList.value[0].originFileObj : null
  } else if (fileType === 'npy') {
    unifiedNpyFileList.value = info.fileList.slice(-1) // 保持最新的一个文件
    unifiedNpyFile.value =
      unifiedNpyFileList.value.length > 0 ? unifiedNpyFileList.value[0].originFileObj : null
  }

  // 验证文件格式
  if (unifiedWavFile.value) {
    const fileName = unifiedWavFile.value.name.toLowerCase()
    if (!fileName.endsWith('.wav')) {
      message.warning('音频文件格式不正确，请选择 WAV 格式')
      unifiedWavFileList.value = []
      unifiedWavFile.value = null
      return
    }
  }

  if (unifiedNpyFile.value) {
    const fileName = unifiedNpyFile.value.name.toLowerCase()
    if (!fileName.endsWith('.npy')) {
      message.warning('特征文件格式不正确，请选择 NPY 格式')
      unifiedNpyFileList.value = []
      unifiedNpyFile.value = null
      return
    }
  }
}

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
    console.log('🎭 开始批量创建角色...')

    // 🔥 使用统一配置创建角色数据
    const charactersToCreate = selectedCharactersForBatch.value.map((characterName) => {
      const character = props.missingCharacters.find((char) => char.name === characterName)
      return {
        name: character.name,
        voice_type: unifiedVoiceType.value || character.voice_type || 'neutral',
        description:
          unifiedDescription.value ||
          character.description ||
          `从第${props.chapter.number}章智能识别的角色`,
        chapter_id: props.chapter.id,
        frequency: character.count || 1,
        is_main_character: character.count > 5, // 出现超过5次认为是主要角色
        // 保留智能分析的原始信息
        detection_source: 'ai_analysis',
        confidence: character.confidence || 0.8
      }
    })

    console.log('📝 准备创建的角色数据:', charactersToCreate)

    // 调用批量创建API
    const formData = new FormData()
    formData.append('characters_data', JSON.stringify(charactersToCreate))
    formData.append('book_id', props.chapter.book_id)
    if (props.chapter.id) {
      formData.append('chapter_id', props.chapter.id)
    }

    // 🔥 添加统一文件到FormData（为所有角色使用相同文件）
    if (unifiedWavFile.value || unifiedNpyFile.value) {
      selectedCharactersForBatch.value.forEach((characterName, index) => {
        // 为每个角色添加统一的WAV文件
        if (unifiedWavFile.value) {
          formData.append(
            `characters[${index}].wav_file`,
            unifiedWavFile.value,
            unifiedWavFile.value.name
          )
          console.log(`📁 添加统一WAV文件: ${characterName} -> ${unifiedWavFile.value.name}`)
        }

        // 为每个角色添加统一的NPY文件
        if (unifiedNpyFile.value) {
          formData.append(
            `characters[${index}].npy_file`,
            unifiedNpyFile.value,
            unifiedNpyFile.value.name
          )
          console.log(`📊 添加统一NPY文件: ${characterName} -> ${unifiedNpyFile.value.name}`)
        }
      })
    }

    const response = await charactersAPI.batchCreateCharacters(formData)

    console.log('✅ 批量创建角色响应:', response.data)

    if (response.data?.success) {
      const responseData = response.data.data || {}
      const createdCharacters = responseData.created || []
      const skippedCharacters = responseData.skipped || []

      console.log('📋 创建的角色:', createdCharacters)
      console.log('⏭️ 跳过的角色:', skippedCharacters)

      if (createdCharacters.length > 0) {
        message.success(
          `✅ 成功添加 ${createdCharacters.length} 个角色到配音库！${skippedCharacters.length > 0 ? ` (跳过 ${skippedCharacters.length} 个已存在的角色)` : ''}`
        )
        
        // 通知父组件角色已创建 - 传递完整的角色对象数组
        console.log('[BatchCreateCharacterDrawer] 传递给父组件的角色数据:', createdCharacters)
        emit('characters-created', createdCharacters)
      } else {
        message.warning('没有创建新角色，所选角色可能已存在')
      }

      // 关闭音频配置抽屉
      audioConfigModalVisible.value = false
      selectedCharactersForBatch.value = []
      emit('close')
    } else {
      throw new Error(response.data?.message || '批量创建角色失败')
    }
  } catch (error) {
    console.error('❌ 批量创建角色失败:', error)
    message.error(`批量创建角色失败: ${error.message || '未知错误'}`)
  } finally {
    emit('update:batchCreating', false)
  }
}

// 暴露方法给父组件
defineExpose({
  showBatchCreateModal
})
</script>

<style scoped>
.batch-create-content {
  height: 100%;
}

.batch-create-body {
  padding-bottom: 80px;
}

.batch-description {
  margin-bottom: 16px;
}

.characters-selection {
  margin-bottom: 20px;
}

.selection-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.selection-header h4 {
  margin: 0;
}

.characters-table {
  border: 1px solid var(--ant-border-color-split);
  border-radius: 6px;
}

.character-name-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.character-name-cell .name {
  font-weight: 500;
}

.character-name-cell .meta {
  display: flex;
  gap: 4px;
}

.description-cell {
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.batch-summary {
  margin-top: 20px;
}

.summary-info h4 {
  margin-bottom: 8px;
  color: var(--ant-primary-color);
}

.summary-info p {
  margin-bottom: 8px;
}

.summary-note {
  color: var(--ant-text-color-secondary);
  font-size: 14px;
}

.audio-config-content {
  height: 100%;
}

.audio-config-body {
  padding-bottom: 80px;
}

.selected-characters-summary {
  margin-bottom: 20px;
}

.unified-audio-config h3 {
  margin-bottom: 8px;
  color: var(--ant-primary-color);
}

.config-description {
  color: var(--ant-text-color-secondary);
  margin-bottom: 20px;
  line-height: 1.6;
}

.unified-audio-upload {
  margin-top: 16px;
}

.upload-tips {
  margin-top: 16px;
}

.drawer-footer {
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
  padding: 16px;
  border-top: 1px solid var(--ant-border-color-split);
  background: var(--ant-component-background);
  z-index: 1000;
}
</style>