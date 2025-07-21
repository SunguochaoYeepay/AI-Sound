<template>
  <a-modal
    :open="open"
    title="备份系统配置"
    ok-text="保存配置"
    cancel-text="取消"
    :confirm-loading="loading"
    @ok="handleOk"
    @cancel="handleCancel"
    width="700px"
  >
    <a-form
      ref="formRef"
      :model="formData"
      :rules="rules"
      :label-col="{ span: 8 }"
      :wrapper-col="{ span: 16 }"
      layout="horizontal"
    >
      <!-- 常规设置 -->
      <a-divider orientation="left">常规设置</a-divider>

      <a-form-item label="默认备份类型" name="default_backup_type">
        <a-select v-model:value="formData.default_backup_type">
          <a-select-option value="full">全量备份</a-select-option>
          <a-select-option value="incremental">增量备份</a-select-option>
          <a-select-option value="manual">手动备份</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="默认保留天数" name="default_retention_days">
        <a-input-number
          v-model:value="formData.default_retention_days"
          :min="1"
          :max="365"
          placeholder="天数"
          style="width: 100%"
        />
      </a-form-item>

      <a-form-item label="并发备份数量" name="max_concurrent_backups">
        <a-input-number
          v-model:value="formData.max_concurrent_backups"
          :min="1"
          :max="10"
          placeholder="个数"
          style="width: 100%"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">同时进行的最大备份任务数量</div>
      </a-form-item>

      <!-- 存储设置 -->
      <a-divider orientation="left">存储设置</a-divider>

      <a-form-item label="默认存储位置" name="default_storage_location">
        <a-select v-model:value="formData.default_storage_location">
          <a-select-option value="local">本地存储</a-select-option>
          <a-select-option value="s3" disabled>Amazon S3（暂未开放）</a-select-option>
          <a-select-option value="oss" disabled>阿里云OSS（暂未开放）</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="本地存储路径" name="local_storage_path">
        <a-input
          v-model:value="formData.local_storage_path"
          placeholder="/path/to/backup/directory"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          备份文件在服务器上的存储路径
        </div>
      </a-form-item>

      <a-form-item label="磁盘空间阈值" name="disk_space_threshold">
        <a-input-number
          v-model:value="formData.disk_space_threshold"
          :min="1"
          :max="100"
          placeholder="百分比"
          style="width: 100%"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          当磁盘使用率超过此值时暂停备份操作（%）
        </div>
      </a-form-item>

      <!-- 安全设置 -->
      <a-divider orientation="left">安全设置</a-divider>

      <a-form-item label="默认启用加密" name="encryption_enabled">
        <a-switch
          v-model:checked="formData.encryption_enabled"
          checked-children="启用"
          un-checked-children="禁用"
        />
      </a-form-item>

      <a-form-item label="加密算法" name="encryption_algorithm">
        <a-select
          v-model:value="formData.encryption_algorithm"
          :disabled="!formData.encryption_enabled"
        >
          <a-select-option value="AES-256">AES-256</a-select-option>
          <a-select-option value="AES-128" disabled>AES-128（暂不支持）</a-select-option>
        </a-select>
      </a-form-item>

      <a-form-item label="启用完整性校验" name="integrity_check_enabled">
        <a-switch
          v-model:checked="formData.integrity_check_enabled"
          checked-children="启用"
          un-checked-children="禁用"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          生成MD5校验和以验证备份文件完整性
        </div>
      </a-form-item>

      <!-- 清理设置 -->
      <a-divider orientation="left">清理设置</a-divider>

      <a-form-item label="自动清理过期备份" name="auto_cleanup_enabled">
        <a-switch
          v-model:checked="formData.auto_cleanup_enabled"
          checked-children="启用"
          un-checked-children="禁用"
        />
      </a-form-item>

      <a-form-item label="清理执行时间" name="cleanup_schedule">
        <a-time-picker
          v-model:value="formData.cleanup_schedule"
          format="HH:mm"
          placeholder="选择时间"
          style="width: 100%"
          :disabled="!formData.auto_cleanup_enabled"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">每日自动清理的执行时间</div>
      </a-form-item>

      <a-form-item label="保留失败备份" name="keep_failed_backups">
        <a-switch
          v-model:checked="formData.keep_failed_backups"
          checked-children="保留"
          un-checked-children="删除"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">是否保留执行失败的备份文件</div>
      </a-form-item>

      <!-- 通知设置 -->
      <a-divider orientation="left">通知设置</a-divider>

      <a-form-item label="备份完成通知" name="notify_on_success">
        <a-switch
          v-model:checked="formData.notify_on_success"
          checked-children="启用"
          un-checked-children="禁用"
        />
      </a-form-item>

      <a-form-item label="备份失败通知" name="notify_on_failure">
        <a-switch
          v-model:checked="formData.notify_on_failure"
          checked-children="启用"
          un-checked-children="禁用"
        />
      </a-form-item>

      <a-form-item label="通知邮箱" name="notification_email">
        <a-input
          v-model:value="formData.notification_email"
          placeholder="admin@example.com"
          :disabled="!formData.notify_on_success && !formData.notify_on_failure"
        />
      </a-form-item>

      <!-- 性能设置 -->
      <a-divider orientation="left">性能设置</a-divider>

      <a-form-item label="压缩级别" name="compression_level">
        <a-slider
          v-model:value="formData.compression_level"
          :min="0"
          :max="9"
          :marks="compressionMarks"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          0=不压缩，9=最高压缩（速度最慢）
        </div>
      </a-form-item>

      <a-form-item label="备份超时时间" name="backup_timeout_minutes">
        <a-input-number
          v-model:value="formData.backup_timeout_minutes"
          :min="5"
          :max="1440"
          placeholder="分钟"
          style="width: 100%"
        />
        <div style="color: #999; font-size: 12px; margin-top: 4px">
          备份任务的最大执行时间，超时将自动取消
        </div>
      </a-form-item>
    </a-form>

    <!-- 配置预览 -->
    <a-alert type="info" show-icon style="margin-top: 16px">
      <template #message>
        <div>
          <strong>配置摘要</strong>
        </div>
        <ul style="margin: 8px 0 0 0; padding-left: 20px; font-size: 12px">
          <li>
            默认备份: {{ getBackupTypeText(formData.default_backup_type) }}，保留
            {{ formData.default_retention_days }} 天
          </li>
          <li>存储位置: {{ getStorageLocationText(formData.default_storage_location) }}</li>
          <li>
            安全设置: {{ formData.encryption_enabled ? '启用加密' : '不加密' }}，{{
              formData.integrity_check_enabled ? '启用校验' : '不校验'
            }}
          </li>
          <li>自动清理: {{ formData.auto_cleanup_enabled ? '启用' : '禁用' }}</li>
        </ul>
      </template>
    </a-alert>
  </a-modal>
</template>

<script setup lang="ts">
  import { ref, reactive, onMounted } from 'vue'
  import { message } from 'ant-design-vue'
  import type { FormInstance, Rule } from 'ant-design-vue/es/form'
  import type { Dayjs } from 'dayjs'
  import dayjs from 'dayjs'

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
    // 常规设置
    default_backup_type: 'full',
    default_retention_days: 30,
    max_concurrent_backups: 3,

    // 存储设置
    default_storage_location: 'local',
    local_storage_path: '/var/backups/ai-sound',
    disk_space_threshold: 85,

    // 安全设置
    encryption_enabled: true,
    encryption_algorithm: 'AES-256',
    integrity_check_enabled: true,

    // 清理设置
    auto_cleanup_enabled: true,
    cleanup_schedule: dayjs('02:00', 'HH:mm'),
    keep_failed_backups: true,

    // 通知设置
    notify_on_success: false,
    notify_on_failure: true,
    notification_email: '',

    // 性能设置
    compression_level: 6,
    backup_timeout_minutes: 120
  })

  // 压缩级别标记
  const compressionMarks = {
    0: '无',
    3: '快速',
    6: '平衡',
    9: '最高'
  }

  // 表单验证规则
  const rules: Record<string, Rule[]> = {
    default_retention_days: [
      { required: true, message: '请设置默认保留天数', trigger: 'blur' },
      { type: 'number', min: 1, max: 365, message: '保留天数范围为1-365天', trigger: 'blur' }
    ],
    max_concurrent_backups: [
      { required: true, message: '请设置并发备份数量', trigger: 'blur' },
      { type: 'number', min: 1, max: 10, message: '并发数量范围为1-10个', trigger: 'blur' }
    ],
    local_storage_path: [{ required: true, message: '请设置本地存储路径', trigger: 'blur' }],
    disk_space_threshold: [
      { required: true, message: '请设置磁盘空间阈值', trigger: 'blur' },
      { type: 'number', min: 1, max: 100, message: '阈值范围为1-100%', trigger: 'blur' }
    ],
    notification_email: [
      {
        validator: (rule: any, value: string) => {
          if ((formData.notify_on_success || formData.notify_on_failure) && !value) {
            return Promise.reject('启用通知时必须设置邮箱地址')
          }
          if (value && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
            return Promise.reject('请输入有效的邮箱地址')
          }
          return Promise.resolve()
        },
        trigger: 'blur'
      }
    ],
    backup_timeout_minutes: [
      { required: true, message: '请设置备份超时时间', trigger: 'blur' },
      { type: 'number', min: 5, max: 1440, message: '超时时间范围为5-1440分钟', trigger: 'blur' }
    ]
  }

  // 工具方法
  const getBackupTypeText = (type: string) => {
    const texts: Record<string, string> = {
      full: '全量备份',
      incremental: '增量备份',
      manual: '手动备份'
    }
    return texts[type] || type
  }

  const getStorageLocationText = (location: string) => {
    const texts: Record<string, string> = {
      local: '本地存储',
      s3: 'Amazon S3',
      oss: '阿里云OSS'
    }
    return texts[location] || location
  }

  // 加载现有配置
  const loadConfigs = async () => {
    try {
      // 这里调用API获取现有配置
      // const response = await getBackupConfigs()
      // Object.assign(formData, response.data)
      console.log('加载备份配置')
    } catch (error) {
      console.error('加载配置失败:', error)
      message.error('加载配置失败')
    }
  }

  // 重置表单
  const resetForm = () => {
    formRef.value?.resetFields()
  }

  // 确认保存
  const handleOk = async () => {
    try {
      await formRef.value?.validate()

      // 转换时间格式
      const configData = {
        ...formData,
        cleanup_schedule: formData.cleanup_schedule?.format('HH:mm') || '02:00'
      }

      emit('ok', configData)
    } catch (error) {
      message.error('请检查表单填写是否正确')
    }
  }

  // 取消保存
  const handleCancel = () => {
    emit('cancel')
  }

  // 组件挂载时加载配置
  onMounted(() => {
    loadConfigs()
  })
</script>

<style scoped>
  :deep(.ant-form-item-explain) {
    margin-top: 4px;
  }

  :deep(.ant-divider-horizontal.ant-divider-with-text-left) {
    margin: 16px 0;
  }

  :deep(.ant-divider-horizontal.ant-divider-with-text-left::before) {
    width: 8%;
  }

  :deep(.ant-divider-horizontal.ant-divider-with-text-left::after) {
    width: 92%;
  }

  :deep(.ant-slider-mark-text) {
    font-size: 12px;
  }
</style>
