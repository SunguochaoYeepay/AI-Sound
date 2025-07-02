<template>
  <div class="import-json-form">
    <a-tabs v-model:active-key="activeTab" @change="handleTabChange">
      <!-- 对话JSON导入 -->
      <a-tab-pane key="dialogue" tab="对话JSON">
        <div class="import-section">
          <a-form layout="vertical">
            <a-form-item label="上传JSON文件">
              <a-upload
                :before-upload="handleFileUpload"
                accept=".json"
                :show-upload-list="false"
              >
                <a-button>
                  <template #icon><UploadOutlined /></template>
                  选择文件
                </a-button>
              </a-upload>
            </a-form-item>
            
            <a-form-item label="或直接粘贴JSON内容">
              <a-textarea
                v-model:value="dialogueJson"
                placeholder="粘贴对话JSON内容..."
                :rows="10"
                @change="validateDialogueJson"
              />
            </a-form-item>
            
            <a-form-item v-if="dialoguePreview" label="预览">
              <div class="json-preview">
                <div class="preview-header">
                  <h4>{{ dialoguePreview.title || '未命名项目' }}</h4>
                  <a-tag color="blue">{{ dialoguePreview.dialogues?.length || 0 }} 条对话</a-tag>
                </div>
                <div class="dialogue-list">
                  <div 
                    v-for="(dialogue, index) in dialoguePreview.dialogues?.slice(0, 3)" 
                    :key="index"
                    class="dialogue-item"
                  >
                    <a-tag color="green">{{ dialogue.character }}</a-tag>
                    <span>{{ dialogue.text }}</span>
                  </div>
                  <div v-if="dialoguePreview.dialogues?.length > 3" class="more-indicator">
                    还有 {{ dialoguePreview.dialogues.length - 3 }} 条对话...
                  </div>
                </div>
              </div>
            </a-form-item>
          </a-form>
        </div>
      </a-tab-pane>
      
      <!-- 示例说明 -->
      <a-tab-pane key="examples" tab="格式示例">
        <div class="examples-content">
          <h4>对话JSON示例：</h4>
          <pre class="example-code">{{ dialogueExample }}</pre>
        </div>
      </a-tab-pane>
    </a-tabs>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { UploadOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  modelValue: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:modelValue'])

const activeTab = ref('dialogue')
const dialogueJson = ref('')
const dialoguePreview = ref(null)

// 计算当前导入数据
const currentImportData = computed(() => {
  return {
    type: 'dialogue',
    data: dialoguePreview.value
  }
})

// 监听导入数据变化
watch(currentImportData, (newData) => {
  emit('update:modelValue', newData)
}, { deep: true })

// 标签页切换
function handleTabChange(key) {
  activeTab.value = key
}

// 文件上传处理
function handleFileUpload(file) {
  const reader = new FileReader()
  reader.onload = (e) => {
    dialogueJson.value = e.target.result
    validateDialogueJson()
  }
  reader.readAsText(file)
  return false // 阻止默认上传
}

// JSON验证和预览
function validateDialogueJson() {
  try {
    if (!dialogueJson.value.trim()) {
      dialoguePreview.value = null
      return
    }
    
    const parsed = JSON.parse(dialogueJson.value)
    
    // 验证对话JSON格式
    if (parsed.dialogues && Array.isArray(parsed.dialogues)) {
      dialoguePreview.value = parsed
    } else {
      throw new Error('无效的对话JSON格式')
    }
  } catch (error) {
    dialoguePreview.value = null
    message.error('JSON格式错误: ' + error.message)
  }
}

// JSON示例
const dialogueExample = `{
  "title": "示例小说",
  "description": "一个示例小说的对话",
  "dialogues": [
    {
      "character": "张三",
      "voice": "voice_001",
      "text": "你好，世界！",
      "emotion": "happy"
    },
    {
      "character": "李四",
      "voice": "voice_002", 
      "text": "今天天气真好啊。",
      "emotion": "neutral"
    }
  ]
}`
</script>

<style scoped>
.import-json-form {
  max-height: 600px;
}

.import-section {
  padding: 16px 0;
}

.json-preview {
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 16px;
  background: #fafafa;
}

.preview-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
  padding-bottom: 8px;
  border-bottom: 1px solid #e8e8e8;
}

.preview-header h4 {
  margin: 0;
  color: #333;
}

.dialogue-list {
  max-height: 200px;
  overflow-y: auto;
}

.dialogue-item {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 8px;
  padding: 8px;
  background: white;
  border-radius: 4px;
  border: 1px solid #e8e8e8;
}

.dialogue-item span {
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.more-indicator {
  text-align: center;
  color: #666;
  font-style: italic;
  margin-top: 8px;
}

.examples-content h4 {
  margin: 16px 0 8px 0;
  color: #333;
}

.example-code {
  background: #f6f8fa;
  border: 1px solid #e1e4e8;
  border-radius: 6px;
  padding: 16px;
  font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
  font-size: 12px;
  line-height: 1.4;
  color: #24292e;
  overflow-x: auto;
  white-space: pre-wrap;
}
</style>