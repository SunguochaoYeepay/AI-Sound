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
        
        <!-- 合并的图片描述 -->
        <template v-else-if="column.key === 'combined_description'">
          <div class="combined-description">
            <a-tooltip :title="getCombinedDescription(record)">
              <div class="description-content">
                {{ getCombinedDescriptionShort(record) }}
              </div>
            </a-tooltip>
            <a-button 
              size="small" 
              type="link" 
              @click="onEditDescription(record)"
              style="padding: 0; margin-left: 8px;"
            >
              编辑
            </a-button>
          </div>
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
                  <a-menu-item key="copy-description">
                    复制描述
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
          <a-descriptions-item label="提示词" :span="2">
            <div class="prompt-display">
              {{ previewTask.generated_prompt }}
            </div>
          </a-descriptions-item>
          <a-descriptions-item label="负面提示词" :span="2">
            <div class="prompt-display">
              {{ previewTask.negative_prompt || '无' }}
            </div>
          </a-descriptions-item>
        </a-descriptions>
      </div>
    </a-modal>
    
    <!-- 编辑描述弹窗 -->
    <a-modal
      v-model:open="editModalVisible"
      title="编辑图片描述"
      width="600px"
      @ok="onSaveDescription"
      @cancel="onCancelEdit"
    >
      <a-form :model="editForm" layout="vertical">
        <a-form-item label="场景描述">
          <a-textarea
            v-model:value="editForm.scene_description"
            placeholder="请描述图片的场景内容"
            :rows="3"
          />
        </a-form-item>
        <a-form-item label="情感色调">
          <a-input
            v-model:value="editForm.emotional_tone"
            placeholder="请描述图片的情感氛围"
          />
        </a-form-item>
        <a-form-item label="提示词">
          <a-textarea
            v-model:value="editForm.generated_prompt"
            placeholder="AI生成的英文提示词"
            :rows="4"
          />
        </a-form-item>
      </a-form>
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
const emit = defineEmits(['generate', 'rate', 'approve', 'delete', 'view-details'])

// Reactive data
const previewVisible = ref(false)
const previewTask = ref(null)
const editModalVisible = ref(false)
const editForm = ref({
  id: null,
  scene_description: '',
  emotional_tone: '',
  generated_prompt: ''
})
const currentEditRecord = ref(null)
const selectedRowKeys = ref([])

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
    title: '图片描述',
    key: 'combined_description',
    width: 300,
    ellipsis: true
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
  current: 1,
  pageSize: 10,
  total: props.tasks.length,
  showSizeChanger: true,
  showQuickJumper: true,
  showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
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
    case 'copy-description':
      copyToClipboard(getCombinedDescription(record))
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

// 合并描述相关方法
const getCombinedDescription = (record) => {
  const parts = []
  if (record.scene_description) parts.push(record.scene_description)
  if (record.emotional_tone) parts.push(record.emotional_tone)
  if (record.generated_prompt) parts.push(record.generated_prompt)
  return parts.join(' | ') || '暂无描述'
}

const getCombinedDescriptionShort = (record) => {
  const full = getCombinedDescription(record)
  return full.length > 100 ? full.substring(0, 100) + '...' : full
}

// 编辑描述相关方法
const onEditDescription = (record) => {
  currentEditRecord.value = record
  editForm.value = {
    id: record.id,
    scene_description: record.scene_description || '',
    emotional_tone: record.emotional_tone || '',
    generated_prompt: record.generated_prompt || ''
  }
  editModalVisible.value = true
}

const onSaveDescription = async () => {
  try {
    // 调用API保存描述
    const response = await fetch(`/api/v1/image-generation/tasks/${editForm.value.id}/description`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        scene_description: editForm.value.scene_description,
        emotional_tone: editForm.value.emotional_tone,
        generated_prompt: editForm.value.generated_prompt
      })
    })
    
    if (!response.ok) {
      throw new Error('保存失败')
    }
    
    const result = await response.json()
    
    // 更新本地数据
    if (currentEditRecord.value) {
      Object.assign(currentEditRecord.value, editForm.value)
    }
    
    message.success('描述更新成功')
    editModalVisible.value = false
  } catch (error) {
    message.error('保存失败: ' + error.message)
  }
}

const onCancelEdit = () => {
  editModalVisible.value = false
  editForm.value = {
    id: null,
    scene_description: '',
    emotional_tone: '',
    generated_prompt: ''
  }
  currentEditRecord.value = null
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

.combined-description {
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.description-content {
  flex: 1;
  color: #666;
  font-size: 13px;
  line-height: 1.4;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.description-content:hover {
  color: #1890ff;
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
</style>