<template>
  <div class="chapter-content">
    <!-- 工具栏 -->
    <div class="content-toolbar">
      <div class="toolbar-left">
        <a-radio-group v-model:value="mode" button-style="solid" size="small">
          <a-radio-button value="preview">👁️ 预览</a-radio-button>
          <a-radio-button value="edit">✏️ 编辑</a-radio-button>
        </a-radio-group>
      </div>
      
      <div class="toolbar-right">
        <a-space>
          <a-tooltip title="复制内容">
            <a-button size="small" @click="copyContent" :disabled="!chapter?.content">
              📋 复制
            </a-button>
          </a-tooltip>
          <a-tooltip title="导出为TXT文件">
            <a-button size="small" @click="downloadTxt" :disabled="!chapter?.content">
              💾 导出
            </a-button>
          </a-tooltip>
          <a-tooltip title="统计信息">
            <a-button size="small" @click="showStats = !showStats">
              📊 统计
            </a-button>
          </a-tooltip>
        </a-space>
      </div>
    </div>

    <!-- 统计信息 -->
    <div v-if="showStats" class="content-stats">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic title="总字数" :value="contentStats.wordCount" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="字符数" :value="contentStats.charCount" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="段落数" :value="contentStats.paragraphCount" />
        </a-col>
        <a-col :span="6">
          <a-statistic title="预计阅读" :value="contentStats.readTime" suffix="分钟" />
        </a-col>
      </a-row>
    </div>

    <!-- 内容区域 -->
    <div class="content-area">
      <!-- 预览模式 -->
      <div v-if="mode === 'preview'" class="preview-mode">
        <div v-if="chapter?.content" class="content-display">
          <div v-for="(paragraph, index) in formattedContent" :key="index" class="paragraph">
            {{ paragraph }}
          </div>
        </div>
        <div v-else class="no-content">
          <a-empty description="该章节暂无内容" :image="false">
            <div class="empty-icon">📄</div>
            <p>点击编辑模式添加内容</p>
            <a-button type="primary" @click="mode = 'edit'">
              ✏️ 开始编辑
            </a-button>
          </a-empty>
        </div>
      </div>

      <!-- 编辑模式 -->
      <div v-else class="edit-mode">
        <div class="edit-header">
          <div class="edit-info">
            <span class="edit-tip">💡 编辑模式：直接编辑章节原文内容</span>
          </div>
          <div class="edit-actions">
            <a-space>
              <a-button size="small" @click="resetContent" :disabled="!hasChanges">
                🔄 撤销
              </a-button>
              <a-button type="primary" size="small" @click="saveContent" :loading="saving" :disabled="!hasChanges">
                💾 保存
              </a-button>
            </a-space>
          </div>
        </div>
        
        <div class="editor-container">
          <a-textarea
            v-model:value="editContent"
            :rows="20"
            placeholder="在此输入章节内容..."
            class="content-editor"
            @change="handleContentChange"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'

const props = defineProps({
  chapter: {
    type: Object,
    default: null
  }
})

const emit = defineEmits(['contentChanged'])

const mode = ref('preview')
const showStats = ref(false)
const saving = ref(false)
const editContent = ref('')
const originalContent = ref('')
const hasChanges = ref(false)

// 格式化内容为段落
const formattedContent = computed(() => {
  if (!props.chapter?.content) return []
  return props.chapter.content.split('\n').filter(line => line.trim())
})

// 内容统计
const contentStats = computed(() => {
  const content = props.chapter?.content || ''
  const wordCount = content.replace(/\s/g, '').length
  const charCount = content.length
  const paragraphCount = content.split('\n').filter(line => line.trim()).length
  const readTime = Math.ceil(wordCount / 300) // 假设每分钟300字
  
  return {
    wordCount,
    charCount,
    paragraphCount,
    readTime
  }
})

// 监听章节变化，重置编辑状态
watch(() => props.chapter, (newChapter) => {
  if (newChapter) {
    editContent.value = newChapter.content || ''
    originalContent.value = newChapter.content || ''
    hasChanges.value = false
    mode.value = 'preview'
  }
}, { immediate: true })

const handleContentChange = () => {
  hasChanges.value = editContent.value !== originalContent.value
}

const copyContent = async () => {
  if (!props.chapter?.content) {
    message.warning('暂无内容可复制')
    return
  }

  try {
    await navigator.clipboard.writeText(props.chapter.content)
    message.success('内容已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    message.error('复制失败')
  }
}

const downloadTxt = () => {
  if (!props.chapter?.content) {
    message.warning('暂无内容可下载')
    return
  }

  const blob = new Blob([props.chapter.content], { type: 'text/plain;charset=utf-8' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `第${props.chapter.number}章_${props.chapter.title}.txt`
  document.body.appendChild(link)
  link.click()
  document.body.removeChild(link)
  URL.revokeObjectURL(url)
  message.success('下载成功')
}

const resetContent = () => {
  editContent.value = originalContent.value
  hasChanges.value = false
  message.info('已撤销修改')
}

const saveContent = async () => {
  if (!hasChanges.value) return
  
  saving.value = true
  try {
    // 触发保存事件
    emit('contentChanged', editContent.value)
    
    // 更新本地状态
    originalContent.value = editContent.value
    hasChanges.value = false
    
    message.success('内容保存成功')
    mode.value = 'preview'
  } catch (error) {
    console.error('保存失败:', error)
    message.error('保存失败')
  } finally {
    saving.value = false
  }
}
</script>

<style scoped>
.chapter-content {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.content-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-radius: 8px 8px 0 0;
}

.toolbar-left {
  display: flex;
  align-items: center;
}

.toolbar-right {
  display: flex;
  align-items: center;
}

.content-stats {
  padding: 16px;
  background: #f1f5f9;
  border-bottom: 1px solid #e5e7eb;
}

.content-area {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.preview-mode {
  flex: 1;
  overflow-y: auto;
  padding: 16px;
}

.content-display {
  margin: 0 auto;
  line-height: 1.8;
}

.paragraph {
  margin-bottom: 16px;
  text-align: justify;
  color: #374151;
  font-size: 15px;
  text-indent: 2em;
}

.no-content {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 100%;
  text-align: center;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
  opacity: 0.5;
}

.no-content p {
  color: #6b7280;
  margin: 8px 0 16px 0;
}

.edit-mode {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.edit-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  background: #fef3cd;
  border-bottom: 1px solid #f59e0b;
}

.edit-info {
  display: flex;
  align-items: center;
}

.edit-tip {
  font-size: 12px;
  color: #92400e;
}

.edit-actions {
  display: flex;
  align-items: center;
}

.editor-container {
  flex: 1;
  padding: 16px;
  overflow: hidden;
}

.content-editor {
  width: 100%;
  height: 100%;
  font-family: 'Courier New', monospace;
  font-size: 14px;
  line-height: 1.6;
  border: 1px solid #d1d5db;
  border-radius: 6px;
  resize: none;
}

.content-editor:focus {
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

/* 滚动条样式 */
.preview-mode::-webkit-scrollbar {
  width: 8px;
}

.preview-mode::-webkit-scrollbar-track {
  background: #f1f5f9;
  border-radius: 4px;
}

.preview-mode::-webkit-scrollbar-thumb {
  background: #cbd5e1;
  border-radius: 4px;
}

.preview-mode::-webkit-scrollbar-thumb:hover {
  background: #94a3b8;
}
</style> 