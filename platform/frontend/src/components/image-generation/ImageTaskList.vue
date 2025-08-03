<template>
  <div class="image-task-list">
    <a-table
      :columns="columns"
      :data-source="tasks"
      :loading="loading"
      :pagination="pagination"
      :scroll="{ x: 1200 }"
      row-key="id"
      :row-selection="rowSelection"
    >
      <!-- 段落内容 -->
      <template #bodyCell="{ column, record }">
        <template v-if="column.key === 'segment_text'">
          <a-tooltip :title="record.segment_text">
            <span class="segment-text">
              {{ record.segment_text.length > 50 ? 
                 record.segment_text.substring(0, 50) + '...' : 
                 record.segment_text }}
            </span>
          </a-tooltip>
        </template>
        
        <!-- 生成的图片 -->
        <template v-else-if="column.key === 'generated_image'">
          <div class="image-preview">
            <a-image
              v-if="record.generated_image_url"
              :width="80"
              :height="80"
              :src="record.generated_image_url"
              :preview="true"
              class="generated-image"
            />
            <div v-else class="no-image">
              <PictureOutlined style="font-size: 24px; color: #ccc" />
              <div>暂无图片</div>
            </div>
          </div>
        </template>
        
        <!-- 状态 -->
        <template v-else-if="column.key === 'status'">
          <a-tag :color="getStatusColor(record.status)">
            {{ getStatusText(record.status) }}
          </a-tag>
          <a-progress
            v-if="record.status === 'processing'"
            :percent="record.progress || 0"
            :size="'small'"
            style="margin-top: 4px; width: 80px"
          />
        </template>
        

        
        <!-- 操作 -->
        <template v-else-if="column.key === 'actions'">
          <a-space>
            <!-- 生成按钮 -->
            <a-button
              v-if="record.status === 'pending'"
              type="primary"
              size="small"
              @click="onGenerate(record.id)"
            >
              生成
            </a-button>
            
            <!-- 重新生成按钮 -->
            <a-button
              v-if="record.status === 'failed'"
              type="primary"
              size="small"
              @click="onGenerate(record.id)"
            >
              重试
            </a-button>
            
            <!-- 为已完成的任务添加重新生成按钮 -->
            <a-button
              v-if="record.status === 'completed'"
              type="default"
              size="small"
              @click="onRegenerate(record.id)"
            >
              重新生成
            </a-button>
            
            <!-- 预览按钮 -->
            <a-button
              v-if="record.generated_image_url"
              size="small"
              @click="onPreview(record)"
            >
              预览
            </a-button>
            
            <!-- 详情按钮 -->
            <a-button
              size="small"
              @click="onViewDetails(record)"
            >
              详情
            </a-button>
            
            <!-- 更多操作 -->
            <a-dropdown>
              <a-button size="small">
                更多
                <DownOutlined />
              </a-button>
              <template #overlay>
                <a-menu @click="(e) => handleMenuClick(e, record)">
                  <a-menu-item key="download" v-if="record.generated_image_url">
                    下载图片
                  </a-menu-item>

                  <a-menu-divider />
                  <a-menu-item key="delete" danger>
                    删除任务
                  </a-menu-item>
                </a-menu>
              </template>
            </a-dropdown>
          </a-space>
        </template>
      </template>
    </a-table>
    
    <!-- 图片预览弹窗 -->
    <a-modal
      v-model:open="previewVisible"
      title="图片预览"
      :footer="null"
      width="800px"
      centered
    >
      <div v-if="previewTask" class="preview-content">
        <a-image
          :src="previewTask.generated_image_url"
          :width="'100%'"
          style="max-height: 500px; object-fit: contain"
        />
        
        <a-divider />
        
        <a-descriptions title="生成信息" :column="2" size="small">
          <a-descriptions-item label="段落索引">
            {{ previewTask.segment_index }}
          </a-descriptions-item>
          <a-descriptions-item label="生成时间">
            {{ previewTask.generation_time }}秒
          </a-descriptions-item>
          <a-descriptions-item label="图片尺寸">
            {{ previewTask.image_width }}×{{ previewTask.image_height }}
          </a-descriptions-item>
          <a-descriptions-item label="生成种子">
            {{ previewTask.generation_seed }}
          </a-descriptions-item>
          <a-descriptions-item label="中文提示词" :span="2" v-if="previewTask.generated_prompt_chinese">
            <div class="prompt-display chinese-prompt">
              {{ previewTask.generated_prompt_chinese }}
            </div>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
    

  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { message } from 'ant-design-vue'
import { PictureOutlined, DownOutlined } from '@ant-design/icons-vue'

// Props
const props = defineProps({
  tasks: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  }
})

// 添加调试watch
watch(() => props.tasks, (newTasks) => {
  console.log('📋 ImageTaskList 接收到 tasks:', newTasks)
  console.log('📋 ImageTaskList tasks length:', newTasks?.length)
  console.log('📋 ImageTaskList tasks 第一个任务:', newTasks?.[0])
}, { immediate: true })

// Emits
const emit = defineEmits(['generate', 'regenerate', 'rate', 'approve', 'delete', 'view-details'])

// Reactive data
const previewVisible = ref(false)
const previewTask = ref(null)
const selectedRowKeys = ref([])
const currentPage = ref(1)
const pageSize = ref(10)

// Row selection configuration
const rowSelection = {
  selectedRowKeys: selectedRowKeys,
  onChange: (selectedKeys) => {
    selectedRowKeys.value = selectedKeys
    // 更新任务的选择状态
    props.tasks.forEach(task => {
      task.selected = selectedKeys.includes(task.id)
    })
  },
  onSelectAll: (selected, selectedRows, changeRows) => {
    props.tasks.forEach(task => {
      task.selected = selected
    })
  }
}

// Table configuration
const columns = [
  {
    title: '段落',
    key: 'segment_text',
    width: 200,
    ellipsis: true
  },
  {
    title: '图片',
    key: 'generated_image',
    width: 120,
    align: 'center'
  },
  {
    title: '状态',
    key: 'status',
    width: 120,
    align: 'center'
  },
  {
    title: '中文提示词',
    key: 'generated_prompt_chinese',
    width: 250,
    ellipsis: true,
    customRender: ({ record }) => record.generated_prompt_chinese || '无'
  },

  {
    title: '创建时间',
    dataIndex: 'created_at',
    width: 150,
    customRender: ({ text }) => text ? new Date(text).toLocaleDateString() : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 200,
    fixed: 'right'
  }
]

const pagination = computed(() => ({
  current: currentPage.value,
  pageSize: pageSize.value,
  total: props.tasks.length,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`,
  onChange: (page, size) => {
    currentPage.value = page
    pageSize.value = size
  },
  onShowSizeChange: (current, size) => {
    currentPage.value = 1
    pageSize.value = size
  }
}))

// Methods
const getStatusColor = (status) => {
  const colors = {
    pending: 'default',
    processing: 'blue',
    completed: 'green',
    failed: 'red'
  }
  return colors[status] || 'default'
}

const getStatusText = (status) => {
  const texts = {
    pending: '等待中',
    processing: '生成中',
    completed: '已完成',
    failed: '失败'
  }
  return texts[status] || status
}

const onGenerate = (taskId) => {
  emit('generate', taskId)
}

const onRegenerate = (taskId) => {
  emit('regenerate', taskId)
}

// 移除了评分功能

const onPreview = (task) => {
  previewTask.value = task
  previewVisible.value = true
}

const onViewDetails = (task) => {
  emit('view-details', task)
}

const handleMenuClick = async ({ key }, record) => {
  switch (key) {
    case 'download':
      downloadImage(record.generated_image_url, `image_${record.id}`)
      break

    case 'delete':
      emit('delete', record.id)
      break
  }
}

const downloadImage = (url, filename) => {
  try {
    const link = document.createElement('a')
    link.href = url
    link.download = filename
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    message.success('图片下载开始')
  } catch (error) {
    message.error('下载失败: ' + error.message)
  }
}

const copyToClipboard = async (text) => {
  try {
    await navigator.clipboard.writeText(text)
    message.success('提示词已复制到剪贴板')
  } catch (error) {
    message.error('复制失败: ' + error.message)
  }
}


</script>

<style scoped>
.image-task-list {
  .segment-text {
    font-size: 12px;
    line-height: 1.4;
  }
  
  .image-preview {
    display: flex;
    flex-direction: column;
    align-items: center;
    
    .generated-image {
      border-radius: 4px;
      object-fit: cover;
    }
    
    .no-image {
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 10px;
      background: #f5f5f5;
      border-radius: 4px;
      font-size: 12px;
      color: #999;
    }
  }
  
  .prompt-text {
    font-size: 12px;
    line-height: 1.4;
  }
  
  .text-gray {
    color: #999;
  }
}



.preview-content {
  .prompt-display {
    background: #f5f5f5;
    padding: 8px;
    border-radius: 4px;
    font-size: 12px;
    line-height: 1.4;
    max-height: 100px;
    overflow-y: auto;
  }
  
  .chinese-prompt {
    background: #f6ffed;
    border-color: #b7eb8f;
    font-family: 'Microsoft YaHei', 'PingFang SC', sans-serif;
  }
}

:deep(.ant-table-cell) {
  padding: 8px !important;
}

:deep(.ant-table-tbody > tr > td) {
  border-bottom: 1px solid #f0f0f0;
}

:deep(.ant-rate) {
  font-size: 14px;
}

/* 暗黑模式适配 */
[data-theme='dark'] .image-task-list {
  .no-image {
    background: #1f1f1f;
    color: #8c8c8c;
  }
  

}

[data-theme='dark'] .preview-content .prompt-display {
  background: #1f1f1f;
  color: #d9d9d9;
  border: 1px solid #434343;
}

[data-theme='dark'] :deep(.ant-table-tbody > tr > td) {
  border-bottom-color: #303030;
}

[data-theme='dark'] :deep(.ant-table-tbody > tr:hover > td) {
  background: #1f1f1f;
}
</style>