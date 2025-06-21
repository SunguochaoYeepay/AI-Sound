<template>
  <a-modal
    :open="open"
    :title="'恢复数据库备份'"
    ok-text="开始恢复"
    cancel-text="取消"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
    width="700px"
  >
    <!-- 备份信息展示 -->
    <div v-if="backupTask" class="backup-info">
      <a-descriptions title="备份信息" bordered size="small">
        <a-descriptions-item label="备份名称">
          {{ backupTask.task_name }}
        </a-descriptions-item>
        <a-descriptions-item label="备份类型">
          <a-tag :color="getTypeColor(backupTask.task_type)">
            {{ getTypeText(backupTask.task_type) }}
          </a-tag>
        </a-descriptions-item>
        <a-descriptions-item label="文件大小">
          {{ formatFileSize(backupTask.file_size) }}
        </a-descriptions-item>
        <a-descriptions-item label="创建时间">
          {{ formatDateTime(backupTask.created_at) }}
        </a-descriptions-item>
        <a-descriptions-item label="包含音频" :span="2">
          <a-tag :color="backupTask.include_audio ? 'green' : 'gray'">
            {{ backupTask.include_audio ? '是' : '否' }}
          </a-tag>
        </a-descriptions-item>
      </a-descriptions>
    </div>

    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      layout="horizontal"
      style="margin-top: 20px"
    >
      <!-- 恢复配置 -->
      <a-divider orientation="left">恢复配置</a-divider>

      <a-form-item label="恢复任务名称" name="task_name">
        <a-input
          v-model:value="formData.task_name"
          placeholder="请输入恢复任务名称"
          :maxlength="100"
          show-count
        />
      </a-form-item>

      <a-form-item label="恢复类型" name="restore_type">
        <a-select
          v-model:value="formData.restore_type"
          placeholder="请选择恢复类型"
          @change="handleRestoreTypeChange"
        >
          <a-select-option value="full">
            <div>
              <strong>完整恢复</strong>
              <div style="color: #999; font-size: 12px">恢复整个数据库到备份时状态</div>
            </div>
          </a-select-option>
          <a-select-option value="partial">
            <div>
              <strong>部分恢复</strong>
              <div style="color: #999; font-size: 12px">仅恢复指定的表或数据</div>
            </div>
          </a-select-option>
          <a-select-option value="point_in_time" disabled>
            <div>
              <strong>时间点恢复</strong>
              <div style="color: #999; font-size: 12px">恢复到指定时间点（暂不支持）</div>
            </div>
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="目标数据库" name="target_database">
        <a-input
          v-model:value="formData.target_database"
          placeholder="数据库名称（留空使用原数据库）"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          可指定不同的数据库名称，留空则使用原数据库
        </div>
      </a-form-item>

      <!-- 恢复选项 -->
      <a-divider orientation="left">恢复选项</a-divider>

      <a-form-item label="恢复音频文件" name="include_audio">
        <a-switch
          v-model:checked="formData.include_audio"
          :disabled="!backupTask?.include_audio"
          checked-children="是"
          un-checked-children="否"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          <span v-if="backupTask?.include_audio">
            是否同时恢复音频文件
          </span>
          <span v-else style="color: #ff4d4f">
            当前备份不包含音频文件
          </span>
        </div>
      </a-form-item>

      <a-form-item label="覆盖现有数据" name="overwrite_existing">
        <a-switch
          v-model:checked="formData.overwrite_existing"
          checked-children="是"
          un-checked-children="否"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          是否覆盖目标数据库中的现有数据
        </div>
      </a-form-item>

      <!-- 部分恢复选项 -->
      <template v-if="formData.restore_type === 'partial'">
        <a-divider orientation="left">选择恢复表</a-divider>
        
        <a-form-item label="恢复表" name="selected_tables">
          <a-select
            v-model:value="formData.selected_tables"
            mode="multiple"
            placeholder="选择要恢复的表"
            :options="availableTables"
            :loading="loadingTables"
          />
          <div style="color: #999; font-size: 12px; margin-top: 4px">
            选择需要恢复的数据表，不选择则恢复所有表
          </div>
        </a-form-item>
      </template>
    </a-form>

    <!-- 风险提示 -->
    <a-alert
      type="error"
      show-icon
      style="margin-top: 16px"
    >
      <template #message>
        <div>
          <strong>重要警告</strong>
        </div>
        <ul style="margin: 8px 0 0 0; padding-left: 20px">
          <li v-if="formData.overwrite_existing">
            <strong>覆盖模式将永久删除目标数据库中的现有数据！</strong>
          </li>
          <li>恢复操作不可撤销，请确保已做好数据备份</li>
          <li>恢复过程中系统可能暂时不可用</li>
          <li>建议在维护时间窗口内进行恢复操作</li>
        </ul>
      </template>
    </a-alert>

    <!-- 恢复预估 -->
    <a-alert
      v-if="showEstimate"
      type="info"
      show-icon
      style="margin-top: 16px"
    >
      <template #message>
        <div>
          <strong>恢复预估</strong>
        </div>
        <ul style="margin: 8px 0 0 0; padding-left: 20px">
          <li>预计时间: {{ estimatedTime }}</li>
          <li>影响范围: {{ affectedScope }}</li>
          <li v-if="formData.include_audio">包含音频文件恢复会显著增加时间</li>
        </ul>
      </template>
    </a-alert>
  </a-modal>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch, onMounted } from 'vue'
import { message } from 'ant-design-vue'
import type { FormInstance, Rule } from 'ant-design-vue/es/form'

// Props
interface Props {
  open: boolean
  backupTask: any
  loading?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  loading: false
})

// Emits
const emit = defineEmits<{
  ok: [data: any]
  cancel: []
}>()

// 表单引用
const formRef = ref<FormInstance>()

// 表单数据
const formData = reactive({
  task_name: '',
  restore_type: 'full',
  target_database: '',
  include_audio: true,
  overwrite_existing: false,
  selected_tables: [] as string[]
})

// 可用表列表
const availableTables = ref([
  { label: 'users (用户表)', value: 'users' },
  { label: 'tts_requests (TTS请求表)', value: 'tts_requests' },
  { label: 'audio_files (音频文件表)', value: 'audio_files' },
  { label: 'system_logs (系统日志表)', value: 'system_logs' },
  { label: 'backup_tasks (备份任务表)', value: 'backup_tasks' },
  { label: 'backup_configs (备份配置表)', value: 'backup_configs' }
])

const loadingTables = ref(false)

// 表单验证规则
const rules: Record<string, Rule[]> = {
  task_name: [
    { required: true, message: '请输入恢复任务名称', trigger: 'blur' },
    { min: 2, max: 100, message: '任务名称长度为2-100个字符', trigger: 'blur' }
  ],
  restore_type: [
    { required: true, message: '请选择恢复类型', trigger: 'change' }
  ]
}

// 工具方法
const getTypeColor = (type: string) => {
  const colors: Record<string, string> = {
    full: 'purple',
    incremental: 'cyan',
    manual: 'lime'
  }
  return colors[type] || 'default'
}

const getTypeText = (type: string) => {
  const texts: Record<string, string> = {
    full: '全量备份',
    incremental: '增量备份',
    manual: '手动备份'
  }
  return texts[type] || type
}

const formatFileSize = (bytes: number) => {
  if (!bytes) return '-'
  if (bytes === 0) return '0 B'
  const k = 1024
  const sizes = ['B', 'KB', 'MB', 'GB', 'TB']
  const i = Math.floor(Math.log(bytes) / Math.log(k))
  return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i]
}

const formatDateTime = (dateString: string) => {
  if (!dateString) return '-'
  return new Date(dateString).toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 计算属性
const showEstimate = computed(() => {
  return formData.restore_type && formData.restore_type !== ''
})

const estimatedTime = computed(() => {
  if (!props.backupTask) return '-'
  
  let baseTime = 10 // 基础恢复时间（分钟）
  
  // 根据文件大小调整时间
  if (props.backupTask.file_size) {
    const sizeGB = props.backupTask.file_size / (1024 * 1024 * 1024)
    baseTime = Math.max(10, Math.ceil(sizeGB * 5))
  }
  
  // 音频文件增加时间
  if (formData.include_audio && props.backupTask.include_audio) {
    baseTime = baseTime * 2
  }
  
  // 部分恢复减少时间
  if (formData.restore_type === 'partial' && formData.selected_tables.length > 0) {
    const ratio = formData.selected_tables.length / 6 // 假设总共6个表
    baseTime = Math.ceil(baseTime * ratio)
  }
  
  return `约 ${baseTime} 分钟`
})

const affectedScope = computed(() => {
  if (formData.restore_type === 'full') {
    return '整个数据库'
  } else if (formData.restore_type === 'partial') {
    if (formData.selected_tables.length === 0) {
      return '所有数据表'
    } else {
      return `${formData.selected_tables.length} 个选定的数据表`
    }
  } else {
    return '指定范围'
  }
})

// 生成默认任务名称
const generateTaskName = () => {
  if (!props.backupTask) return ''
  
  const now = new Date()
  const timestamp = now.toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '_')
  const backupName = props.backupTask.task_name.replace(/备份/g, '').slice(0, 20)
  return `恢复${backupName}_${timestamp}`
}

// 恢复类型改变处理
const handleRestoreTypeChange = (value: string) => {
  if (value !== 'partial') {
    formData.selected_tables = []
  }
}

// 重置表单
const resetForm = () => {
  formRef.value?.resetFields()
  Object.assign(formData, {
    task_name: '',
    restore_type: 'full',
    target_database: '',
    include_audio: true,
    overwrite_existing: false,
    selected_tables: []
  })
}

// 确认恢复
const handleOk = async () => {
  try {
    await formRef.value?.validate()
    
    const restoreData = {
      backup_id: props.backupTask?.id,
      ...formData
    }
    
    emit('ok', restoreData)
  } catch (error) {
    message.error('请检查表单填写是否正确')
  }
}

// 取消恢复
const handleCancel = () => {
  emit('cancel')
}

// 监听弹窗打开状态
watch(() => props.open, (newVal) => {
  if (newVal && props.backupTask) {
    // 弹窗打开时生成默认任务名称和设置默认值
    formData.task_name = generateTaskName()
    formData.include_audio = props.backupTask.include_audio || false
  } else if (!newVal) {
    // 弹窗关闭时重置表单
    setTimeout(() => {
      resetForm()
    }, 300)
  }
})
</script>

<style scoped>
.backup-info {
  margin-bottom: 16px;
}

:deep(.ant-descriptions-item-label) {
  background-color: #fafafa;
  font-weight: 500;
}

:deep(.ant-form-item-explain) {
  margin-top: 4px;
}

:deep(.ant-divider-horizontal.ant-divider-with-text-left) {
  margin: 16px 0;
}

:deep(.ant-divider-horizontal.ant-divider-with-text-left::before) {
  width: 5%;
}

:deep(.ant-divider-horizontal.ant-divider-with-text-left::after) {
  width: 95%;
}
</style>