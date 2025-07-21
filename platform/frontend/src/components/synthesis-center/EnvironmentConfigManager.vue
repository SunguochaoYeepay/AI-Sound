<template>
  <div class="environment-config-manager">
    <!-- 头部信息 -->
    <div class="config-header">
      <div class="header-left">
        <h3>🎵 环境音配置管理</h3>
        <p class="text-gray-600">查看和编辑项目的环境音轨道配置</p>
      </div>
      <div class="header-right">
        <a-button @click="refreshConfig" :loading="loading">
          <template #icon><ReloadOutlined /></template>
          刷新
        </a-button>
        <a-button type="primary" @click="openBatchEdit" :disabled="!hasConfig">
          <template #icon><EditOutlined /></template>
          批量编辑
        </a-button>
      </div>
    </div>

    <!-- 配置统计 -->
    <div v-if="config && config.analysis_stats" class="config-stats mb-4">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic
            title="环境轨道"
            :value="config.config?.environment_tracks?.length || 0"
            suffix="个"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="总时长"
            :value="config.analysis_stats?.total_duration || 0"
            suffix="秒"
            :precision="1"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic title="已确认" :value="getConfirmedCount()" suffix="个" />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="会话状态"
            :value="config.session_stage"
            :value-style="{ color: getSessionStatusColor() }"
          />
        </a-col>
      </a-row>
    </div>

    <!-- 环境音轨道列表 -->
    <div v-if="hasConfig" class="tracks-container">
      <a-table
        :dataSource="config.config.environment_tracks"
        :columns="trackColumns"
        :pagination="false"
        :scroll="{ x: 1200 }"
        row-key="track_index"
        size="middle"
      >
        <!-- 轨道基本信息 -->
        <template #bodyCell="{ column, record, index }">
          <template v-if="column.dataIndex === 'track_info'">
            <div class="track-info">
              <div class="track-title">
                <span class="track-index">轨道 {{ index + 1 }}</span>
                <a-tag :color="getConfidenceColor(record.confidence)">
                  {{ (record.confidence * 100).toFixed(0) }}%
                </a-tag>
              </div>
              <div class="track-time">
                {{ record.start_time?.toFixed(1) }}s -
                {{ (record.start_time + record.duration)?.toFixed(1) }}s
              </div>
              <div class="track-segment">段落ID: {{ record.segment_id }}</div>
            </div>
          </template>

          <!-- 环境音ID配置 -->
          <template v-else-if="column.dataIndex === 'environment_id'">
            <div class="environment-id-config">
              <div class="id-display">
                <a-input
                  v-model:value="record.environment_id"
                  :placeholder="record.auto_generated_id ? '自动生成' : '自定义ID'"
                  size="small"
                  @blur="
                    updateTrackConfig(index, {
                      environment_id: record.environment_id,
                      auto_generated_id: false
                    })
                  "
                />
              </div>
              <div class="id-status">
                <a-tag :color="record.auto_generated_id ? 'orange' : 'green'" size="small">
                  {{ record.auto_generated_id ? '自动' : '手动' }}
                </a-tag>
              </div>
            </div>
          </template>

          <!-- 环境关键词 -->
          <template v-else-if="column.dataIndex === 'environment_keywords'">
            <div class="keywords-display">
              <a-tag
                v-for="keyword in record.environment_keywords || []"
                :key="keyword"
                size="small"
                closable
                @close="removeKeyword(index, keyword)"
              >
                {{ keyword }}
              </a-tag>
              <a-button
                type="dashed"
                size="small"
                @click="addKeyword(index)"
                style="margin-top: 4px"
              >
                + 添加
              </a-button>
            </div>
          </template>

          <!-- 场景描述 -->
          <template v-else-if="column.dataIndex === 'scene_description'">
            <a-textarea
              v-model:value="record.scene_description"
              :rows="2"
              placeholder="环境场景描述"
              @blur="updateTrackConfig(index, { scene_description: record.scene_description })"
            />
          </template>

          <!-- TangoFlux配置 -->
          <template v-else-if="column.dataIndex === 'tango_config'">
            <div class="tango-config">
              <a-input
                v-model:value="record.tango_prompt"
                placeholder="TangoFlux提示词"
                size="small"
                @blur="updateTrackConfig(index, { tango_prompt: record.tango_prompt })"
              />
              <div class="config-controls">
                <span>音量:</span>
                <a-slider
                  v-model:value="record.volume"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  style="width: 80px; margin: 0 8px"
                  @change="updateTrackConfig(index, { volume: record.volume })"
                />
                <span>{{ (record.volume * 100).toFixed(0) }}%</span>
              </div>
            </div>
          </template>

          <!-- 状态操作 -->
          <template v-else-if="column.dataIndex === 'actions'">
            <div class="track-actions">
              <a-button-group size="small">
                <a-button
                  type="primary"
                  :disabled="record.validation_status === 'approved'"
                  @click="confirmTrack(index)"
                >
                  {{ record.user_confirmed ? '已确认' : '确认' }}
                </a-button>
                <a-button @click="editTrack(index)"> 编辑 </a-button>
                <a-button danger @click="removeTrack(index)"> 删除 </a-button>
              </a-button-group>
            </div>
          </template>
        </template>
      </a-table>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <a-empty description="暂无环境音配置" :image="Empty.PRESENTED_IMAGE_SIMPLE">
        <a-button type="primary" @click="$emit('start-analysis')"> 开始环境音分析 </a-button>
      </a-empty>
    </div>

    <!-- 添加关键词模态框 -->
    <a-modal
      v-model:open="keywordModalVisible"
      title="添加环境关键词"
      @ok="handleAddKeyword"
      @cancel="keywordModalVisible = false"
    >
      <a-select
        v-model:value="newKeyword"
        placeholder="选择或输入关键词"
        style="width: 100%"
        :options="keywordOptions"
        allow-clear
        show-search
        @search="handleKeywordSearch"
      />
    </a-modal>

    <!-- 轨道编辑抽屉 -->
    <a-drawer
      v-model:open="editDrawerVisible"
      title="编辑环境音轨道"
      :width="600"
      @close="editDrawerVisible = false"
    >
      <div v-if="editingTrack" class="track-edit-form">
        <a-form layout="vertical">
          <a-form-item label="环境音ID">
            <a-input v-model:value="editingTrack.environment_id" placeholder="输入自定义环境音ID" />
            <div class="form-help">留空将自动生成ID，格式：env_段落ID_轨道序号</div>
          </a-form-item>

          <a-form-item label="环境关键词">
            <a-select
              v-model:value="editingTrack.environment_keywords"
              mode="tags"
              placeholder="选择或输入关键词"
              :options="keywordOptions"
              style="width: 100%"
            />
          </a-form-item>

          <a-form-item label="场景描述">
            <a-textarea
              v-model:value="editingTrack.scene_description"
              :rows="3"
              placeholder="描述环境场景"
            />
          </a-form-item>

          <a-form-item label="TangoFlux提示词">
            <a-textarea
              v-model:value="editingTrack.tango_prompt"
              :rows="4"
              placeholder="生成环境音的提示词"
            />
          </a-form-item>

          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="音量">
                <a-slider
                  v-model:value="editingTrack.volume"
                  :min="0"
                  :max="1"
                  :step="0.1"
                  :tip-formatter="(value) => `${(value * 100).toFixed(0)}%`"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="淡入时间(秒)">
                <a-input-number
                  v-model:value="editingTrack.fade_in"
                  :min="0"
                  :max="10"
                  :step="0.5"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
            <a-col :span="8">
              <a-form-item label="淡出时间(秒)">
                <a-input-number
                  v-model:value="editingTrack.fade_out"
                  :min="0"
                  :max="10"
                  :step="0.5"
                  style="width: 100%"
                />
              </a-form-item>
            </a-col>
          </a-row>

          <a-form-item>
            <a-checkbox v-model:checked="editingTrack.loop_enabled"> 启用循环播放 </a-checkbox>
          </a-form-item>

          <div class="form-actions">
            <a-button @click="editDrawerVisible = false"> 取消 </a-button>
            <a-button type="primary" @click="saveTrackEdit" :loading="saving"> 保存配置 </a-button>
          </div>
        </a-form>
      </div>
    </a-drawer>
  </div>
</template>

<script setup>
  import { ref, computed, onMounted, watch } from 'vue'
  import { message, Empty } from 'ant-design-vue'
  import { ReloadOutlined, EditOutlined } from '@ant-design/icons-vue'
  import api from '@/api'

  const props = defineProps({
    projectId: {
      type: Number,
      required: true
    },
    visible: {
      type: Boolean,
      default: false
    }
  })

  const emit = defineEmits(['start-analysis'])

  // 状态管理
  const loading = ref(false)
  const saving = ref(false)
  const config = ref(null)

  // 编辑相关
  const editDrawerVisible = ref(false)
  const editingTrack = ref(null)
  const editingTrackIndex = ref(-1)

  // 关键词管理
  const keywordModalVisible = ref(false)
  const newKeyword = ref('')
  const editingKeywordIndex = ref(-1)

  // 表格列定义
  const trackColumns = [
    {
      title: '轨道信息',
      dataIndex: 'track_info',
      width: 200,
      fixed: 'left'
    },
    {
      title: '环境音ID',
      dataIndex: 'environment_id',
      width: 180
    },
    {
      title: '环境关键词',
      dataIndex: 'environment_keywords',
      width: 200
    },
    {
      title: '场景描述',
      dataIndex: 'scene_description',
      width: 250
    },
    {
      title: 'TangoFlux配置',
      dataIndex: 'tango_config',
      width: 300
    },
    {
      title: '操作',
      dataIndex: 'actions',
      width: 150,
      fixed: 'right'
    }
  ]

  // 计算属性
  const hasConfig = computed(() => {
    return (
      config.value && config.value.success && config.value.config?.environment_tracks?.length > 0
    )
  })

  const keywordOptions = computed(() => {
    const commonKeywords = [
      '脚步声',
      '翻书声',
      '雷声',
      '雨声',
      '风声',
      '虫鸣',
      '鸟叫',
      '水声',
      '汽车声',
      '钟声',
      '门声',
      '窗声',
      '电话声',
      '键盘声',
      '音乐声'
    ]

    return commonKeywords.map((keyword) => ({
      label: keyword,
      value: keyword
    }))
  })

  // 工具函数
  const getConfirmedCount = () => {
    if (!hasConfig.value) return 0
    return config.value.config.environment_tracks.filter((track) => track.user_confirmed).length
  }

  const getSessionStatusColor = () => {
    const stage = config.value?.session_stage
    switch (stage) {
      case 'analyzed':
        return '#52c41a'
      case 'validation_prepared':
        return '#1890ff'
      case 'completed':
        return '#722ed1'
      default:
        return '#8c8c8c'
    }
  }

  const getConfidenceColor = (confidence) => {
    if (confidence > 0.8) return 'green'
    if (confidence > 0.5) return 'orange'
    return 'red'
  }

  // 数据加载
  const loadConfig = async () => {
    if (!props.projectId) return

    try {
      loading.value = true
      const response = await api.environmentGenerationAPI.getEnvironmentConfig(props.projectId)
      config.value = response.data

      if (!response.data.success) {
        message.info(response.data.message || '暂无环境音配置')
      }
    } catch (error) {
      console.error('加载环境音配置失败:', error)
      message.error('加载配置失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      loading.value = false
    }
  }

  const refreshConfig = () => {
    loadConfig()
  }

  // 轨道配置更新
  const updateTrackConfig = async (trackIndex, configUpdate) => {
    try {
      const response = await api.environmentGenerationAPI.updateTrackConfig(
        props.projectId,
        trackIndex,
        configUpdate
      )

      if (response.data.success) {
        // 更新本地配置
        const track = config.value.config.environment_tracks[trackIndex]
        Object.assign(track, configUpdate)

        message.success('配置更新成功')
      }
    } catch (error) {
      console.error('更新轨道配置失败:', error)
      message.error('更新失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 关键词管理
  const addKeyword = (trackIndex) => {
    editingKeywordIndex.value = trackIndex
    keywordModalVisible.value = true
    newKeyword.value = ''
  }

  const removeKeyword = async (trackIndex, keyword) => {
    const track = config.value.config.environment_tracks[trackIndex]
    const newKeywords = track.environment_keywords.filter((k) => k !== keyword)

    await updateTrackConfig(trackIndex, { environment_keywords: newKeywords })
  }

  const handleAddKeyword = async () => {
    if (!newKeyword.value.trim()) {
      message.error('请输入关键词')
      return
    }

    const trackIndex = editingKeywordIndex.value
    const track = config.value.config.environment_tracks[trackIndex]
    const newKeywords = [...(track.environment_keywords || []), newKeyword.value.trim()]

    await updateTrackConfig(trackIndex, { environment_keywords: newKeywords })

    keywordModalVisible.value = false
    newKeyword.value = ''
  }

  const handleKeywordSearch = (value) => {
    // 搜索功能可以后续扩展
  }

  // 轨道操作
  const confirmTrack = async (trackIndex) => {
    await updateTrackConfig(trackIndex, { user_confirmed: true, validation_status: 'approved' })
  }

  const editTrack = (trackIndex) => {
    editingTrackIndex.value = trackIndex
    editingTrack.value = { ...config.value.config.environment_tracks[trackIndex] }
    editDrawerVisible.value = true
  }

  const saveTrackEdit = async () => {
    try {
      saving.value = true

      await updateTrackConfig(editingTrackIndex.value, editingTrack.value)

      editDrawerVisible.value = false
      message.success('轨道配置保存成功')
    } catch (error) {
      message.error('保存失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      saving.value = false
    }
  }

  const removeTrack = async (trackIndex) => {
    // TODO: 实现删除轨道功能
    message.info('删除功能待实现')
  }

  const openBatchEdit = () => {
    // TODO: 实现批量编辑功能
    message.info('批量编辑功能待实现')
  }

  // 生命周期
  onMounted(() => {
    if (props.visible && props.projectId) {
      loadConfig()
    }
  })

  watch(
    () => props.visible,
    (newVisible) => {
      if (newVisible && props.projectId) {
        loadConfig()
      }
    }
  )

  watch(
    () => props.projectId,
    (newProjectId) => {
      if (newProjectId && props.visible) {
        loadConfig()
      }
    }
  )
</script>

<style scoped>
  .environment-config-manager {
    padding: 16px;
  }

  .config-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
  }

  .config-header h3 {
    margin: 0 0 8px 0;
    font-size: 18px;
    font-weight: 600;
  }

  .config-stats {
    background: #f8f9fa;
    padding: 16px;
    border-radius: 8px;
  }

  .tracks-container {
    background: white;
    border-radius: 8px;
    overflow: hidden;
  }

  .track-info {
    padding: 8px 0;
  }

  .track-title {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-bottom: 4px;
  }

  .track-index {
    font-weight: 600;
    color: #1890ff;
  }

  .track-time {
    font-size: 12px;
    color: #666;
    margin-bottom: 2px;
  }

  .track-segment {
    font-size: 12px;
    color: #999;
  }

  .environment-id-config {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .keywords-display {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .tango-config {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .config-controls {
    display: flex;
    align-items: center;
    font-size: 12px;
    color: #666;
  }

  .track-actions {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .empty-state {
    text-align: center;
    padding: 60px 20px;
  }

  .track-edit-form {
    padding: 16px 0;
  }

  .form-help {
    font-size: 12px;
    color: #999;
    margin-top: 4px;
  }

  .form-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }
</style>
