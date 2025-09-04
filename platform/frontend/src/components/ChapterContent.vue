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
            <a-button size="small" @click="showStats = !showStats"> 📊 统计 </a-button>
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
            <div class="paragraph-header">
              <span class="paragraph-index">段落 {{ index + 1 }}</span>
              <a-button 
                size="small" 
                type="primary"
                @click="handleSixCardAnalysis(index)"
                :loading="analyzingSegments[index]"
              >
                <template #icon>
                  <AppstoreOutlined />
                </template>
                段落分析
              </a-button>
            </div>
            <div class="paragraph-text">{{ paragraph.text }}</div>
            <div v-if="paragraph.isSmartSegmented" class="smart-segment-badge">
              <a-tag color="blue" size="small">🤖 智能分段</a-tag>
            </div>
          </div>
        </div>
        <div v-else class="no-content">
          <a-empty description="该章节暂无内容" :image="false">
            <div class="empty-icon">📄</div>
            <p>点击编辑模式添加内容</p>
            <a-button type="primary" @click="mode = 'edit'"> ✏️ 开始编辑 </a-button>
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
              <a-button
                type="primary"
                size="small"
                @click="saveContent"
                :loading="saving"
                :disabled="!hasChanges"
              >
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
  import { AppstoreOutlined } from '@ant-design/icons-vue'
  import { storyboardAPI } from '@/api/storyboard'

  const props = defineProps({
    chapter: {
      type: Object,
      default: null
    }
  })

  const emit = defineEmits(['contentChanged', 'sixCardAnalysis'])

  const mode = ref('preview')
  const showStats = ref(false)
  const saving = ref(false)
  const editContent = ref('')
  const originalContent = ref('')
  const hasChanges = ref(false)
  const analyzingSegments = ref({})

  // 格式化内容为段落（只使用智能分段结果）
  const formattedContent = computed(() => {
    if (!props.chapter?.content) return []
    
    // 如果有智能分段数据，使用智能分段结果
    if (props.chapter.segmentation_data?.segments && props.chapter.segmentation_data.segments.length > 0) {
      return props.chapter.segmentation_data.segments.map((segment, index) => ({
        text: typeof segment === 'string' ? segment : segment.content || segment.text || '',
        index: index,
        isSmartSegmented: true
      }))
    }
    
    // 没有智能分段数据就返回空数组
    return []
  })

      // 段落分析方法
  const handleSixCardAnalysis = async (segmentIndex) => {
    if (analyzingSegments.value[segmentIndex]) return
    
    analyzingSegments.value[segmentIndex] = true
    try {
      console.log(`开始分析段落 ${segmentIndex + 1}...`)
      
      // 显示分析提示
      message.info({
        content: `正在分析段落 ${segmentIndex + 1}，请稍候...`,
        duration: 3,
        key: `segment-${segmentIndex}`
      })
      
      // 调用段落分析API
      const response = await storyboardAPI.sixCardAnalysis(props.chapter?.id, [segmentIndex])
      
      if (response.data?.success) {
        message.success({
          content: `✅ 段落 ${segmentIndex + 1} 段落分析完成！`,
          duration: 3,
          key: `segment-${segmentIndex}`
        })
        
        // 触发事件，让父组件显示分析结果
        emit('sixCardAnalysis', {
          segmentIndex,
          results: response.data.data.results
        })
        
        console.log('段落分析完成:', response.data)
      } else {
                  throw new Error(response.data?.message || '段落分析失败')
      }
      
    } catch (error) {
      console.error('段落分析失败:', error)
      message.error({
                  content: `❌ 段落 ${segmentIndex + 1} 段落分析失败`,
        duration: 3,
        key: `segment-${segmentIndex}`
      })
    } finally {
      analyzingSegments.value[segmentIndex] = false
    }
  }

  // 内容统计
  const contentStats = computed(() => {
    const content = props.chapter?.content || ''
    const wordCount = content.replace(/\s/g, '').length
    const charCount = content.length
    
    // 只使用智能分段数量，没有就显示0
    const paragraphCount = props.chapter?.segmentation_data?.segments?.length || 0
    
    const readTime = Math.ceil(wordCount / 300) // 假设每分钟300字

    return {
      wordCount,
      charCount,
      paragraphCount,
      readTime
    }
  })

  // 监听章节变化，重置编辑状态
  watch(
    () => props.chapter,
    (newChapter) => {
      if (newChapter) {
        editContent.value = newChapter.content || ''
        originalContent.value = newChapter.content || ''
        hasChanges.value = false
        mode.value = 'preview'
      }
    },
    { immediate: true }
  )

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
    background: var(--ant-color-bg-elevated);
    border-bottom: 1px solid var(--ant-color-split);
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
    margin-bottom: 20px;
    padding: 16px;
    border: 1px solid var(--border-color, #e8e8e8);
    border-radius: 8px;
    background: var(--card-bg, white);
    text-align: justify;
    color: var(--ant-color-text);
    font-size: 15px;
  }

  .paragraph-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid var(--border-color, #f0f0f0);
  }

  .paragraph-index {
    font-weight: 600;
    color: var(--text-color, #333);
    font-size: 14px;
  }

  .paragraph-text {
    margin-bottom: 8px;
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
    color: var(--ant-color-text-secondary);
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
    background: var(--ant-color-warning-bg);
    border-bottom: 1px solid var(--ant-color-warning);
  }

  .edit-info {
    display: flex;
    align-items: center;
  }

  .edit-tip {
    font-size: 12px;
    color: var(--ant-color-warning-text);
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
    border: 1px solid var(--ant-color-border);
    border-radius: 6px;
    resize: none;
    background-color: var(--ant-color-bg-container);
    color: var(--ant-color-text);
  }

  .content-editor:focus {
    border-color: var(--ant-color-primary);
    box-shadow: 0 0 0 3px var(--ant-color-primary-1);
  }

  /* 滚动条样式 */
  .preview-mode::-webkit-scrollbar {
    width: 8px;
  }

  .preview-mode::-webkit-scrollbar-track {
    background: var(--ant-color-bg-elevated);
    border-radius: 4px;
  }

  .preview-mode::-webkit-scrollbar-thumb {
    background: var(--ant-color-text-quaternary);
    border-radius: 4px;
  }

  .preview-mode::-webkit-scrollbar-thumb:hover {
    background: var(--ant-color-text-tertiary);
  }
</style>
