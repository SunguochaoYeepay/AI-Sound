<template>
  <a-drawer
    v-model:open="visible"
    title="协作与导出"
    width="480"
    placement="right"
    @close="$emit('close')"
  >
    <a-tabs v-model:activeKey="activeTab" size="small">
      <!-- 导出任务 -->
      <a-tab-pane key="export" tab="导出">
        <div class="export-section">
          <a-button
            type="primary"
            block
            @click="showExportModal = true"
            style="margin-bottom: 16px"
          >
            <template #icon><ExportOutlined /></template>
            新建导出任务
          </a-button>

          <a-list :data-source="exportTasks" :loading="exportLoading" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <template #actions>
                  <a-button
                    v-if="item.status === 'completed'"
                    size="small"
                    @click="downloadFile(item)"
                  >
                    下载
                  </a-button>
                </template>

                <a-list-item-meta>
                  <template #title>
                    {{ item.export_format.toUpperCase() }} 导出
                    <a-tag :color="getStatusColor(item.status)" size="small">
                      {{ getStatusLabel(item.status) }}
                    </a-tag>
                  </template>
                  <template #description>
                    <a-progress
                      :percent="item.progress"
                      size="small"
                      :status="item.status === 'failed' ? 'exception' : 'normal'"
                    />
                    <div style="font-size: 12px; color: #999; margin-top: 4px">
                      {{ formatTime(item.created_at) }}
                    </div>
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </a-tab-pane>

      <!-- 项目分享 -->
      <a-tab-pane key="share" tab="分享">
        <div class="share-section">
          <a-button type="primary" block @click="showShareModal = true" style="margin-bottom: 16px">
            <template #icon><ShareAltOutlined /></template>
            创建分享链接
          </a-button>

          <a-list :data-source="shareLinks" size="small">
            <template #renderItem="{ item }">
              <a-list-item>
                <template #actions>
                  <a @click="copyShareLink(item.share_token)">复制</a>
                </template>

                <a-list-item-meta>
                  <template #title>
                    {{ getShareTypeLabel(item.share_type) }}分享
                    <a-tag v-if="item.password" color="orange" size="small">密码</a-tag>
                  </template>
                  <template #description>
                    访问: {{ item.access_count }}次 ·
                    {{ formatTime(item.created_at) }}
                  </template>
                </a-list-item-meta>
              </a-list-item>
            </template>
          </a-list>
        </div>
      </a-tab-pane>

      <!-- 版本历史 -->
      <a-tab-pane key="history" tab="历史">
        <div class="history-section">
          <a-button
            size="small"
            block
            @click="loadEditHistory"
            :loading="historyLoading"
            style="margin-bottom: 16px"
          >
            <template #icon><ReloadOutlined /></template>
            刷新历史
          </a-button>

          <a-timeline size="small">
            <a-timeline-item
              v-for="history in editHistory"
              :key="history.id"
              :color="getOperationColor(history.operation_type)"
            >
              <div class="history-item">
                <div style="font-weight: 500; margin-bottom: 4px">
                  v{{ history.version_number }} - {{ getOperationLabel(history.operation_type) }}
                </div>
                <div style="font-size: 12px; color: #999; margin-bottom: 8px">
                  {{ formatTime(history.created_at) }}
                </div>
                <a-button
                  size="small"
                  @click="revertToVersion(history.version_number)"
                  :disabled="history.version_number === currentVersion"
                >
                  回滚
                </a-button>
              </div>
            </a-timeline-item>
          </a-timeline>
        </div>
      </a-tab-pane>

      <!-- 云端同步 -->
      <a-tab-pane key="sync" tab="同步">
        <div class="sync-section">
          <a-card size="small" style="margin-bottom: 16px">
            <div v-if="syncStatus">
              <a-descriptions size="small" :column="1">
                <a-descriptions-item label="本地版本">
                  v{{ syncStatus.local_version }}
                </a-descriptions-item>
                <a-descriptions-item label="云端版本">
                  v{{ syncStatus.cloud_version }}
                </a-descriptions-item>
                <a-descriptions-item label="状态">
                  <a-tag :color="getSyncStatusColor(syncStatus.sync_status)" size="small">
                    {{ getSyncStatusLabel(syncStatus.sync_status) }}
                  </a-tag>
                </a-descriptions-item>
              </a-descriptions>
            </div>
          </a-card>

          <a-space direction="vertical" style="width: 100%">
            <a-button
              type="primary"
              block
              @click="syncToCloud"
              :loading="syncLoading"
              :disabled="syncStatus?.sync_status === 'syncing'"
            >
              <template #icon><CloudUploadOutlined /></template>
              同步到云端
            </a-button>
            <a-button
              block
              @click="syncFromCloud"
              :loading="syncLoading"
              :disabled="syncStatus?.sync_status === 'syncing'"
            >
              <template #icon><CloudDownloadOutlined /></template>
              从云端同步
            </a-button>
          </a-space>
        </div>
      </a-tab-pane>
    </a-tabs>

    <!-- 导出对话框 -->
    <a-modal
      v-model:open="showExportModal"
      title="导出设置"
      @ok="createExportTask"
      :confirm-loading="createExportLoading"
    >
      <a-form :model="exportForm" layout="vertical" size="small">
        <a-form-item label="导出格式" required>
          <a-select v-model:value="exportForm.export_format">
            <a-select-option value="mp3">MP3 - 通用格式</a-select-option>
            <a-select-option value="wav">WAV - 无损格式</a-select-option>
            <a-select-option value="flac">FLAC - 无损压缩</a-select-option>
            <a-select-option value="aac">AAC - 高效编码</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="音质设置">
          <a-row :gutter="8">
            <a-col :span="12">
              <label style="font-size: 12px">比特率 (kbps)</label>
              <a-input-number
                v-model:value="exportForm.export_settings.bitrate"
                :min="64"
                :max="320"
                size="small"
                style="width: 100%"
              />
            </a-col>
            <a-col :span="12">
              <label style="font-size: 12px">采样率 (Hz)</label>
              <a-select v-model:value="exportForm.export_settings.sample_rate" size="small">
                <a-select-option :value="22050">22050</a-select-option>
                <a-select-option :value="44100">44100</a-select-option>
                <a-select-option :value="48000">48000</a-select-option>
              </a-select>
            </a-col>
          </a-row>
        </a-form-item>

        <a-form-item>
          <a-checkbox v-model:checked="exportForm.export_settings.normalize">
            音量标准化
          </a-checkbox>
        </a-form-item>
      </a-form>
    </a-modal>

    <!-- 分享对话框 -->
    <a-modal
      v-model:open="showShareModal"
      title="分享设置"
      @ok="createShare"
      :confirm-loading="createShareLoading"
    >
      <a-form :model="shareForm" layout="vertical" size="small">
        <a-form-item label="分享类型" required>
          <a-radio-group v-model:value="shareForm.share_type">
            <a-radio value="view">仅查看</a-radio>
            <a-radio value="edit">可编辑</a-radio>
            <a-radio value="download">可下载</a-radio>
          </a-radio-group>
        </a-form-item>

        <a-form-item label="访问密码">
          <a-input
            v-model:value="shareForm.password"
            placeholder="留空表示无需密码"
            type="password"
          />
        </a-form-item>

        <a-form-item label="过期时间">
          <a-date-picker
            v-model:value="shareForm.expires_at"
            show-time
            placeholder="留空表示永不过期"
            size="small"
            style="width: 100%"
          />
        </a-form-item>
      </a-form>
    </a-modal>
  </a-drawer>
</template>

<script>
  import { defineComponent, ref, reactive, watch } from 'vue'
  import { message } from 'ant-design-vue'
  import {
    ExportOutlined,
    ShareAltOutlined,
    ReloadOutlined,
    CloudUploadOutlined,
    CloudDownloadOutlined
  } from '@ant-design/icons-vue'
  import {
    getEditHistory,
    revertToVersion as revertToVersionApi,
    getExportTasks,
    createExportTask as createExportTaskApi,
    createProjectShare,
    getSyncStatus,
    syncToCloud as syncToCloudApi,
    syncFromCloud as syncFromCloudApi
  } from '@/api/collaboration'

  export default defineComponent({
    name: 'CollaborationDrawer',
    components: {
      ExportOutlined,
      ShareAltOutlined,
      ReloadOutlined,
      CloudUploadOutlined,
      CloudDownloadOutlined
    },
    props: {
      visible: {
        type: Boolean,
        default: false
      },
      projectId: {
        type: Number,
        required: true
      }
    },
    emits: ['close'],
    setup(props) {
      const activeTab = ref('export')

      // 导出相关
      const exportTasks = ref([])
      const exportLoading = ref(false)
      const showExportModal = ref(false)
      const createExportLoading = ref(false)
      const exportForm = reactive({
        project_id: props.projectId,
        export_format: 'mp3',
        export_settings: {
          bitrate: 128,
          sample_rate: 44100,
          channels: 2,
          quality: 'high',
          normalize: true
        }
      })

      // 分享相关
      const shareLinks = ref([])
      const showShareModal = ref(false)
      const createShareLoading = ref(false)
      const shareForm = reactive({
        project_id: props.projectId,
        share_type: 'view',
        password: '',
        expires_at: null
      })

      // 历史相关
      const editHistory = ref([])
      const historyLoading = ref(false)
      const currentVersion = ref(1)

      // 同步相关
      const syncStatus = ref(null)
      const syncLoading = ref(false)

      // 工具函数
      const formatTime = (time) => {
        return new Date(time).toLocaleString()
      }

      const getStatusColor = (status) => {
        const colors = {
          pending: 'default',
          processing: 'blue',
          completed: 'green',
          failed: 'red'
        }
        return colors[status] || 'default'
      }

      const getStatusLabel = (status) => {
        const labels = {
          pending: '等待中',
          processing: '处理中',
          completed: '已完成',
          failed: '失败'
        }
        return labels[status] || status
      }

      const getShareTypeLabel = (type) => {
        const labels = {
          view: '查看',
          edit: '编辑',
          download: '下载'
        }
        return labels[type] || type
      }

      const getOperationColor = (type) => {
        const colors = {
          create: 'green',
          edit: 'blue',
          delete: 'red',
          revert: 'orange'
        }
        return colors[type] || 'default'
      }

      const getOperationLabel = (type) => {
        const labels = {
          create: '创建',
          edit: '编辑',
          delete: '删除',
          revert: '回滚'
        }
        return labels[type] || type
      }

      const getSyncStatusColor = (status) => {
        const colors = {
          local: 'default',
          syncing: 'blue',
          synced: 'green',
          conflict: 'orange',
          error: 'red'
        }
        return colors[status] || 'default'
      }

      const getSyncStatusLabel = (status) => {
        const labels = {
          local: '仅本地',
          syncing: '同步中',
          synced: '已同步',
          conflict: '有冲突',
          error: '同步错误'
        }
        return labels[status] || status
      }

      // API方法
      const loadExportTasks = async () => {
        try {
          exportLoading.value = true
          const response = await getExportTasks({ project_id: props.projectId })
          exportTasks.value = response.data || []
        } catch (error) {
          message.error('加载导出任务失败')
        } finally {
          exportLoading.value = false
        }
      }

      const createExportTask = async () => {
        try {
          createExportLoading.value = true
          await createExportTaskApi(exportForm)
          message.success('导出任务创建成功')
          showExportModal.value = false
          loadExportTasks()
        } catch (error) {
          message.error('创建导出任务失败')
        } finally {
          createExportLoading.value = false
        }
      }

      const downloadFile = (record) => {
        const link = document.createElement('a')
        link.href = `/api/v1/collaboration/export/download/${record.id}`
        link.download = `project_${record.project_id}.${record.export_format}`
        link.click()
      }

      const createShare = async () => {
        try {
          createShareLoading.value = true
          const response = await createProjectShare(shareForm)
          message.success('分享链接创建成功')
          showShareModal.value = false
          shareLinks.value.push(response.data)
        } catch (error) {
          message.error('创建分享链接失败')
        } finally {
          createShareLoading.value = false
        }
      }

      const copyShareLink = async (shareToken) => {
        const url = `${window.location.origin}/share/${shareToken}`
        try {
          await navigator.clipboard.writeText(url)
          message.success('链接已复制到剪贴板')
        } catch (error) {
          message.error('复制失败')
        }
      }

      const loadEditHistory = async () => {
        try {
          historyLoading.value = true
          const response = await getEditHistory(props.projectId)
          editHistory.value = response.data || []
        } catch (error) {
          message.error('加载编辑历史失败')
        } finally {
          historyLoading.value = false
        }
      }

      const revertToVersion = async (versionNumber) => {
        try {
          await revertToVersionApi(props.projectId, versionNumber)
          message.success(`已回滚到版本 ${versionNumber}`)
          loadEditHistory()
        } catch (error) {
          message.error('版本回滚失败')
        }
      }

      const loadSyncStatus = async () => {
        try {
          const response = await getSyncStatus(props.projectId)
          syncStatus.value = response.data
        } catch (error) {
          message.error('加载同步状态失败')
        }
      }

      const syncToCloud = async () => {
        try {
          syncLoading.value = true
          await syncToCloudApi(props.projectId)
          message.success('开始同步到云端')
          setTimeout(loadSyncStatus, 2000)
        } catch (error) {
          message.error('同步失败')
        } finally {
          syncLoading.value = false
        }
      }

      const syncFromCloud = async () => {
        try {
          syncLoading.value = true
          await syncFromCloudApi(props.projectId)
          message.success('从云端同步完成')
          loadSyncStatus()
        } catch (error) {
          message.error('同步失败')
        } finally {
          syncLoading.value = false
        }
      }

      // 监听抽屉打开状态，加载数据
      watch(
        () => props.visible,
        (visible) => {
          if (visible) {
            loadExportTasks()
            loadSyncStatus()
          }
        }
      )

      return {
        activeTab,

        // 导出
        exportTasks,
        exportLoading,
        showExportModal,
        createExportLoading,
        exportForm,
        loadExportTasks,
        createExportTask,
        downloadFile,

        // 分享
        shareLinks,
        showShareModal,
        createShareLoading,
        shareForm,
        createShare,
        copyShareLink,

        // 历史
        editHistory,
        historyLoading,
        currentVersion,
        loadEditHistory,
        revertToVersion,

        // 同步
        syncStatus,
        syncLoading,
        syncToCloud,
        syncFromCloud,

        // 工具函数
        formatTime,
        getStatusColor,
        getStatusLabel,
        getShareTypeLabel,
        getOperationColor,
        getOperationLabel,
        getSyncStatusColor,
        getSyncStatusLabel
      }
    }
  })
</script>

<style scoped>
  .export-section,
  .share-section,
  .history-section,
  .sync-section {
    padding: 8px 0;
  }

  .history-item {
    font-size: 13px;
  }

  :deep(.ant-timeline-item-content) {
    margin-left: 8px;
  }

  :deep(.ant-descriptions-item-label) {
    font-size: 12px;
  }

  :deep(.ant-descriptions-item-content) {
    font-size: 12px;
  }
</style>
