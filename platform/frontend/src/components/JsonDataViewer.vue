<template>
  <div class="json-view">
    <div class="json-header">
      <a-space>
        <a-button
          size="small"
          @click="toggleJsonEditMode"
          :type="jsonEditMode ? 'primary' : 'default'"
        >
          {{ jsonEditMode ? '📖 预览模式' : '✏️ 编辑模式' }}
        </a-button>
        <a-button size="small" @click="copyJson"> 📋 复制JSON </a-button>
        <a-button size="small" @click="formatJson"> 🎨 格式化 </a-button>
        <a-button size="small" @click="downloadJson"> 💾 下载JSON </a-button>
        <a-button
          v-if="jsonEditMode"
          size="small"
          @click="saveJsonChanges"
          type="primary"
          :disabled="!hasJsonChanges"
        >
          💾 保存JSON
        </a-button>
      </a-space>
    </div>

    <div class="json-editor">
      <!-- 编辑模式 -->
      <a-textarea
        v-if="jsonEditMode"
        v-model="editableJsonText"
        :rows="25"
        class="json-display editable"
        placeholder="编辑JSON数据..."
        @change="markJsonChanged"
      />
      <!-- 预览模式 -->
      <a-textarea
        v-else
        :value="getJsonPreview()"
        :rows="25"
        readonly
        class="json-display"
      />
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'

// Props
const props = defineProps({
  analysisData: {
    type: Object,
    default: () => ({})
  },
  editableCharacters: {
    type: Array,
    default: () => []
  },
  editableSegments: {
    type: Array,
    default: () => []
  },
  chapter: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits(['json-changed', 'data-updated'])

// JSON编辑相关状态
const jsonEditMode = ref(false)
const editableJsonText = ref('')
const hasJsonChanges = ref(false)

// 切换JSON编辑模式
const toggleJsonEditMode = () => {
  if (!jsonEditMode.value) {
    // 进入编辑模式，初始化编辑文本
    editableJsonText.value = getJsonPreview()
    hasJsonChanges.value = false
  }
  jsonEditMode.value = !jsonEditMode.value
}

// 标记JSON已修改
const markJsonChanged = () => {
  hasJsonChanges.value = true
  emit('json-changed', true)
}

// 获取JSON预览
const getJsonPreview = () => {
  const previewData = {
    chapter_id: props.chapter?.id,
    chapter_number: props.chapter?.number,
    chapter_title: props.chapter?.title,
    book_id: props.chapter?.book_id,
    total_segments: props.editableSegments.length,
    total_characters: props.editableCharacters.length,
    characters: props.editableCharacters,
    synthesis_plan: props.editableSegments,
    analysis_metadata: {
      created_at: props.analysisData?.created_at || new Date().toISOString(),
      updated_at: new Date().toISOString(),
      version: '1.0'
    }
  }
  return JSON.stringify(previewData, null, 2)
}

// 复制JSON
const copyJson = async () => {
  try {
    await navigator.clipboard.writeText(getJsonPreview())
    message.success('JSON已复制到剪贴板')
  } catch (error) {
    message.error('复制失败')
  }
}

// 格式化JSON
const formatJson = () => {
  message.info('JSON已格式化显示')
}

// 下载JSON
const downloadJson = () => {
  const jsonContent = getJsonPreview()
  const blob = new Blob([jsonContent], { type: 'application/json' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `第${props.chapter?.number}章_智能分析结果.json`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  message.success('JSON文件下载成功')
}

// 保存JSON修改
const saveJsonChanges = () => {
  try {
    const parsedJson = JSON.parse(editableJsonText.value)
    
    // 验证JSON结构
    if (!parsedJson.characters || !Array.isArray(parsedJson.characters)) {
      throw new Error('JSON格式错误：缺少characters数组')
    }
    if (!parsedJson.synthesis_plan || !Array.isArray(parsedJson.synthesis_plan)) {
      throw new Error('JSON格式错误：缺少synthesis_plan数组')
    }

    // 发送更新事件
    emit('data-updated', {
      characters: parsedJson.characters,
      segments: parsedJson.synthesis_plan
    })

    hasJsonChanges.value = false
    message.success('JSON数据已应用到编辑器')
  } catch (error) {
    console.error('JSON解析失败:', error)
    message.error(`JSON格式错误: ${error.message}`)
  }
}
</script>

<style scoped>
.json-view {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.json-header {
  margin-bottom: 16px;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.json-editor {
  flex: 1;
  overflow: hidden;
}

.json-display {
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.5;
  background-color: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 4px;
  resize: none;
}

.json-display.editable {
  background-color: #fff;
  border-color: #d9d9d9;
}

.json-display.editable:focus {
  border-color: #40a9ff;
  box-shadow: 0 0 0 2px rgba(24, 144, 255, 0.2);
}
</style>