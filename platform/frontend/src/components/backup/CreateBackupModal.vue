<template>
  <a-modal
    :open="open"
    :title="'创建数据库备份'"
    ok-text="创建备份"
    cancel-text="取消"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
    width="600px"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      :label-col="{ span: 6 }"
      :wrapper-col="{ span: 18 }"
      layout="horizontal"
    >
      <!-- 基本信息 -->
      <a-divider orientation="left">基本信息</a-divider>

      <a-form-item label="任务名称" name="task_name">
        <a-input
          v-model:value="formData.task_name"
          placeholder="请输入备份任务名称"
          :maxlength="100"
          show-count
        />
      </a-form-item>

      <a-form-item label="备份类型" name="backup_type">
        <a-select
          v-model:value="formData.backup_type"
          placeholder="请选择备份类型"
          @change="handleBackupTypeChange"
        >
          <a-select-option value="full">
            <div>
              <strong>全量备份</strong>
              <div style="color: #999; font-size: 12px">完整备份所有数据，耗时较长</div>
            </div>
          </a-select-option>
          <a-select-option value="incremental">
            <div>
              <strong>增量备份</strong>
              <div style="color: #999; font-size: 12px">仅备份变更数据，速度较快</div>
            </div>
          </a-select-option>
          <a-select-option value="manual">
            <div>
              <strong>手动备份</strong>
              <div style="color: #999; font-size: 12px">一次性手动备份操作</div>
            </div>
          </a-select-option>
        </a-select>
      </a-form-item>

      <!-- 备份选项 -->
      <a-divider orientation="left">备份选项</a-divider>

      <a-form-item label="包含音频文件" name="include_audio">
        <a-switch
          v-model:checked="formData.include_audio"
          checked-children="是"
          un-checked-children="否"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          是否同时备份音频文件（会显著增加备份大小和时间）
        </div>
      </a-form-item>

      <a-form-item label="启用加密" name="encryption_enabled">
        <a-switch
          v-model:checked="formData.encryption_enabled"
          checked-children="是"
          un-checked-children="否"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          使用AES-256加密备份文件（推荐）
        </div>
      </a-form-item>

      <!-- 存储配置 -->
      <a-divider orientation="left">存储配置</a-divider>

      <a-form-item label="存储位置" name="storage_location">
        <a-select v-model:value="formData.storage_location" placeholder="请选择存储位置">
          <a-select-option value="local">
            <div>
              <strong>本地存储</strong>
              <div style="color: #999; font-size: 12px">存储在服务器本地磁盘</div>
            </div>
          </a-select-option>
          <a-select-option value="s3" disabled>
            <div>
              <strong>Amazon S3</strong>
              <div style="color: #999; font-size: 12px">存储到AWS S3（暂未开放）</div>
            </div>
          </a-select-option>
          <a-select-option value="oss" disabled>
            <div>
              <strong>阿里云OSS</strong>
              <div style="color: #999; font-size: 12px">存储到阿里云对象存储（暂未开放）</div>
            </div>
          </a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="保留天数" name="retention_days">
        <a-input-number
          v-model:value="formData.retention_days"
          :min="1"
          :max="365"
          placeholder="天数"
          style="width: 100%"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          备份文件自动清理时间，超过该天数的备份将被删除
        </div>
      </a-form-item>
    </a-form>

    <!-- 备份预估信息 -->
    <a-alert v-if="showEstimate" type="info" show-icon style="margin-top: 16px">
      <template #message>
        <div>
          <strong>备份预估</strong>
        </div>
        <ul style="margin: 8px 0 0 0; padding-left: 20px">
          <li>预计时间: {{ estimatedTime }}</li>
          <li>预计大小: {{ estimatedSize }}</li>
          <li v-if="formData.include_audio">包含音频文件会大幅增加备份时间和大小</li>
        </ul>
      </template>
    </a-alert>

    <!-- 重要提示 -->
    <a-alert type="warning" show-icon style="margin-top: 16px">
      <template #message>
        <div>
          <strong>重要提示</strong>
        </div>
        <ul style="margin: 8px 0 0 0; padding-left: 20px">
          <li>备份过程中请勿关闭系统，以免造成备份文件损坏</li>
          <li>大型备份可能需要较长时间，请耐心等待</li>
          <li>建议在系统负载较低时进行备份操作</li>
        </ul>
      </template>
    </a-alert>
  </a-modal>
</template>

<script setup lang="ts">
  import { ref, reactive, computed, watch } from 'vue'
  import { message } from 'ant-design-vue'
  import type { FormInstance, Rule } from 'ant-design-vue/es/form'

  // Props
  interface Props {
    open: boolean
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
    backup_type: 'full',
    include_audio: false,
    encryption_enabled: true,
    storage_location: 'local',
    retention_days: 30
  })

  // 表单验证规则
  const rules: Record<string, Rule[]> = {
    task_name: [
      { required: true, message: '请输入任务名称', trigger: 'blur' },
      { min: 2, max: 100, message: '任务名称长度为2-100个字符', trigger: 'blur' }
    ],
    backup_type: [{ required: true, message: '请选择备份类型', trigger: 'change' }],
    storage_location: [{ required: true, message: '请选择存储位置', trigger: 'change' }],
    retention_days: [
      { required: true, message: '请设置保留天数', trigger: 'blur' },
      { type: 'number', min: 1, max: 365, message: '保留天数范围为1-365天', trigger: 'blur' }
    ]
  }

  // 是否显示预估信息
  const showEstimate = computed(() => {
    return formData.backup_type && formData.backup_type !== ''
  })

  // 预估时间
  const estimatedTime = computed(() => {
    const baseTime = {
      full: 15,
      incremental: 5,
      manual: 10
    }

    let time = baseTime[formData.backup_type as keyof typeof baseTime] || 10

    if (formData.include_audio) {
      time = time * 3 // 音频文件增加3倍时间
    }

    return `${time}-${time * 2} 分钟`
  })

  // 预估大小
  const estimatedSize = computed(() => {
    const baseSize = {
      full: 500,
      incremental: 100,
      manual: 300
    }

    let size = baseSize[formData.backup_type as keyof typeof baseSize] || 200

    if (formData.include_audio) {
      size = size + 2000 // 音频文件增加约2GB
    }

    if (size < 1024) {
      return `${size} MB`
    } else {
      return `${(size / 1024).toFixed(1)} GB`
    }
  })

  // 生成默认任务名称
  const generateTaskName = () => {
    const now = new Date()
    const timestamp = now.toISOString().slice(0, 19).replace(/[-:]/g, '').replace('T', '_')
    const typeMap = {
      full: '全量',
      incremental: '增量',
      manual: '手动'
    }
    const typeName = typeMap[formData.backup_type as keyof typeof typeMap] || '备份'
    return `${typeName}备份_${timestamp}`
  }

  // 监听备份类型变化
  const handleBackupTypeChange = (value: string) => {
    if (!formData.task_name || formData.task_name.match(/^(全量|增量|手动)备份_\d{8}_\d{6}$/)) {
      formData.task_name = generateTaskName()
    }
  }

  // 重置表单
  const resetForm = () => {
    formRef.value?.resetFields()
    Object.assign(formData, {
      task_name: '',
      backup_type: 'full',
      include_audio: false,
      encryption_enabled: true,
      storage_location: 'local',
      retention_days: 30
    })
  }

  // 确认创建
  const handleOk = async () => {
    try {
      await formRef.value?.validate()
      emit('ok', { ...formData })
    } catch (error) {
      message.error('请检查表单填写是否正确')
    }
  }

  // 取消创建
  const handleCancel = () => {
    emit('cancel')
  }

  // 监听弹窗打开状态
  watch(
    () => props.open,
    (newVal) => {
      if (newVal) {
        // 弹窗打开时生成默认任务名称
        if (!formData.task_name) {
          formData.task_name = generateTaskName()
        }
      } else {
        // 弹窗关闭时重置表单
        setTimeout(() => {
          resetForm()
        }, 300)
      }
    }
  )
</script>

<style scoped>
  :deep(.ant-form-item-explain) {
    margin-top: 4px;
  }

  :deep(.ant-select-selection-item) {
    padding: 8px 0;
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
