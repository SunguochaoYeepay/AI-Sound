<template>
  <a-drawer
    :visible="visible"
    :title="modalTitle"
    :width="1000"
    :closable="!processing"
    :mask-closable="!processing"
    @close="handleCancel"
  >
    <!-- 步骤指示器 -->
    <a-steps 
      :current="currentStep" 
      size="small" 
      class="mb-6"
      :status="stepStatus"
    >
      <a-step title="环境分析" description="分析旁白内容" />
      <a-step title="人工校对" description="校对环境配置" />
      <a-step title="生成完成" description="持久化配置" />
    </a-steps>

    <!-- 步骤1：环境分析 -->
    <div v-if="currentStep === 0" class="step-content">
      <div class="step-header">
        <h3>🔍 环境音需求分析</h3>
        <p class="text-gray-600">从章节内容中提取旁白环境描述，生成环境音配置建议</p>
      </div>

      <div v-if="!analysisResult" class="analysis-start">
        <a-alert
          message="准备开始环境音分析"
          description="系统将分析所选章节的synthesis_plan，提取旁白中的环境描述，生成TangoFlux配置建议。"
          type="info"
          show-icon
          class="mb-4"
        />
        
        <div class="analysis-actions">
          <a-button 
            type="primary" 
            size="large"
            :loading="processing"
            @click="startAnalysis"
          >
            <template #icon><SearchOutlined /></template>
            开始分析环境音需求
          </a-button>
        </div>
      </div>

      <div v-else class="analysis-result">
        <a-alert
          :message="`分析完成：检测到 ${analysisResult.analysis_stats?.total_tracks || 0} 个环境音轨道`"
          :description="`总时长 ${analysisResult.analysis_stats?.total_duration || 0}秒，平均时长 ${analysisResult.analysis_stats?.avg_duration || 0}秒`"
          type="success"
          show-icon
          class="mb-4"
        />

        <!-- 分析统计 -->
        <div class="analysis-stats mb-4">
          <a-row :gutter="16">
            <a-col :span="8">
              <a-statistic 
                title="环境轨道" 
                :value="analysisResult.analysis_stats?.total_tracks || 0" 
                suffix="个"
              />
            </a-col>
            <a-col :span="8">
              <a-statistic 
                title="总时长" 
                :value="analysisResult.analysis_stats?.total_duration || 0" 
                suffix="秒"
                :precision="1"
              />
            </a-col>
            <a-col :span="8">
              <a-statistic 
                title="置信度分布" 
                :value="getHighConfidenceCount()"
                suffix="个高置信度"
              />
            </a-col>
          </a-row>
        </div>

        <!-- 关键词分布 -->
        <div class="keyword-distribution mb-4">
          <h4>🏷️ 检测到的环境关键词</h4>
          <div class="keyword-tags">
            <a-tag 
              v-for="(count, keyword) in analysisResult.analysis_stats?.keyword_distribution || {}"
              :key="keyword"
              :color="getKeywordColor(count)"
              class="mb-2"
            >
              {{ keyword }} ({{ count }})
            </a-tag>
          </div>
        </div>

        <!-- 环境轨道预览 -->
        <div class="tracks-preview">
          <h4>🎵 环境音轨道预览</h4>
          <div class="tracks-list">
            <div 
              v-for="(track, index) in analysisResult.analysis_result?.environment_tracks || []"
              :key="track.segment_id"
              class="track-item"
            >
              <div class="track-header">
                <span class="track-id">轨道 {{ index + 1 }}</span>
                <span class="track-time">{{ track.start_time?.toFixed(1) }}s - {{ (track.start_time + track.duration)?.toFixed(1) }}s</span>
                <a-tag :color="getConfidenceColor(track.confidence)">
                  置信度 {{ (track.confidence * 100)?.toFixed(0) }}%
                </a-tag>
              </div>
              <div class="track-content">
                <div class="track-keywords">
                  <a-tag 
                    v-for="keyword in track.environment_keywords || []"
                    :key="keyword"
                    size="small"
                  >
                    {{ keyword }}
                  </a-tag>
                </div>
                <div class="track-description">{{ track.scene_description }}</div>
              </div>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <a-button @click="restartAnalysis" :disabled="processing">
            重新分析
          </a-button>
          <a-button 
            type="primary" 
            @click="proceedToValidation"
            :loading="processing"
          >
            进入校对阶段
          </a-button>
        </div>
      </div>
    </div>

    <!-- 步骤2：人工校对 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="step-header">
        <h3>🛠️ 人工校对与配置</h3>
        <p class="text-gray-600">校对环境音配置，支持场景继承和手动编辑</p>
      </div>

      <div v-if="validationData" class="validation-content">
        <!-- 校对总览 -->
        <div class="validation-summary mb-4">
          <a-alert
            :message="`校对进度：${getApprovedCount()}/${validationData.validation_tracks?.length || 0} 已校对`"
            :description="`场景继承：${validationData.validation_summary?.inheritance_applied_count || 0}个，手动编辑：${getManualEditCount()}个`"
            :type="isAllApproved() ? 'success' : 'info'"
            show-icon
          />
        </div>

        <!-- 校对轨道列表 -->
        <div class="validation-tracks">
          <div 
            v-for="(track, index) in validationData.validation_tracks || []"
            :key="track.segment_id"
            class="validation-track"
            :class="{ 'track-approved': track.validation_status === 'approved' }"
          >
            <div class="track-validation-header">
              <div class="track-info">
                <span class="track-title">轨道 {{ index + 1 }} (段落 {{ track.segment_id }})</span>
                <span class="track-time">{{ track.start_time?.toFixed(1) }}s - {{ (track.start_time + track.duration)?.toFixed(1) }}s</span>
                <a-tag 
                  :color="getValidationStatusColor(track.validation_status)"
                  class="validation-status"
                >
                  {{ getValidationStatusText(track.validation_status) }}
                </a-tag>
              </div>
              
              <div class="track-actions">
                <a-button 
                  size="small" 
                  @click="editTrack(index)"
                  :disabled="processing"
                >
                  编辑
                </a-button>
                <a-button 
                  size="small" 
                  type="primary"
                  @click="approveTrack(index)"
                  :disabled="track.validation_status === 'approved' || processing"
                >
                  通过
                </a-button>
              </div>
            </div>

            <div class="track-validation-content">
              <!-- 场景继承信息 -->
              <div v-if="track.inheritance_applied" class="inheritance-info">
                <a-tag color="blue" class="mb-2">
                  继承场景: {{ track.inherited_environment?.primary_keyword }}
                </a-tag>
              </div>

              <!-- 环境关键词 -->
              <div class="environment-keywords mb-2">
                <span class="label">环境关键词：</span>
                <a-tag 
                  v-for="keyword in getCurrentKeywords(track)"
                  :key="keyword"
                  size="small"
                  class="mr-1"
                >
                  {{ keyword }}
                </a-tag>
              </div>

              <!-- TangoFlux配置建议 -->
              <div class="tangoflux-suggestions">
                <span class="label">TangoFlux配置：</span>
                <div class="suggestions-list">
                  <div 
                    v-for="suggestion in track.matching_suggestions || []"
                    :key="suggestion.keyword"
                    class="suggestion-item"
                  >
                    <span class="suggestion-keyword">{{ suggestion.keyword }}:</span>
                    <span class="suggestion-prompt">{{ suggestion.suggested_tangoflux_config?.prompt }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div class="step-actions">
          <a-button @click="backToAnalysis" :disabled="processing">
            返回分析
          </a-button>
          <a-button 
            type="primary" 
            @click="proceedToFinalize"
            :disabled="!isAllApproved() || processing"
            :loading="processing"
          >
            完成校对
          </a-button>
        </div>
      </div>
    </div>

    <!-- 步骤3：生成完成 -->
    <div v-if="currentStep === 2" class="step-content">
      <div class="step-header">
        <h3>🎉 环境音生成完成</h3>
        <p class="text-gray-600">环境音配置已生成并持久化，可以进行音频混合</p>
      </div>

      <div v-if="finalResult" class="final-result">
        <a-result
          status="success"
          :title="`成功生成 ${finalResult.persistence_data?.persistence_summary?.approved_tracks_count || 0} 个环境音配置`"
          :sub-title="`总时长 ${finalResult.persistence_data?.persistence_summary?.total_duration || 0}秒，继承场景 ${finalResult.persistence_data?.persistence_summary?.inheritance_count || 0}个`"
        >
          <template #extra>
            <div class="final-stats">
              <a-descriptions :column="2" bordered size="small">
                <a-descriptions-item label="环境轨道数">
                  {{ finalResult.persistence_data?.persistence_summary?.approved_tracks_count || 0 }}
                </a-descriptions-item>
                <a-descriptions-item label="总时长">
                  {{ finalResult.persistence_data?.persistence_summary?.total_duration || 0 }}秒
                </a-descriptions-item>
                <a-descriptions-item label="场景继承">
                  {{ finalResult.persistence_data?.persistence_summary?.inheritance_count || 0 }}个
                </a-descriptions-item>
                <a-descriptions-item label="手动编辑">
                  {{ finalResult.persistence_data?.persistence_summary?.manual_edits_count || 0 }}个
                </a-descriptions-item>
              </a-descriptions>
            </div>
          </template>
        </a-result>

        <div class="next-steps">
          <a-alert
            message="下一步操作"
            description="环境音配置已保存，您现在可以在合成中心执行音频混合，将角色段落音与环境音合并生成最终音频文件。"
            type="info"
            show-icon
            class="mb-4"
          />
        </div>

        <div class="step-actions">
          <a-button @click="handleComplete">
            完成
          </a-button>
          <a-button type="primary" @click="handleStartAudioMixing">
            开始音频混合
          </a-button>
        </div>
      </div>
    </div>

    <!-- 轨道编辑抽屉 -->
    <a-drawer
      :visible="editDrawerVisible"
      title="编辑环境音配置"
      :width="600"
      @close="closeEditDrawer"
    >
      <div v-if="editingTrack" class="track-edit-form">
        <!-- 编辑表单内容 -->
        <a-form layout="vertical">
          <a-form-item label="环境关键词">
            <a-select
              v-model:value="editForm.keywords"
              mode="tags"
              placeholder="输入或选择环境关键词"
              :options="keywordOptions"
            />
          </a-form-item>
          
          <a-form-item label="场景描述">
            <a-textarea
              v-model:value="editForm.sceneDescription"
              placeholder="描述环境场景"
              :rows="3"
            />
          </a-form-item>
          
          <a-form-item label="TangoFlux提示词">
            <a-textarea
              v-model:value="editForm.tangofluxPrompt"
              placeholder="生成环境音的提示词"
              :rows="2"
            />
          </a-form-item>
          
          <a-form-item label="音量">
            <a-slider
              v-model:value="editForm.volume"
              :min="0"
              :max="1"
              :step="0.1"
              :marks="{ 0: '0%', 0.5: '50%', 1: '100%' }"
            />
          </a-form-item>
        </a-form>
        
        <div class="edit-actions">
          <a-button @click="closeEditDrawer">取消</a-button>
          <a-button type="primary" @click="saveTrackEdits" :loading="processing">
            保存修改
          </a-button>
        </div>
      </div>
    </a-drawer>
  </a-drawer>
</template>

<script setup>
import { ref, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { SearchOutlined } from '@ant-design/icons-vue'
import api from '@/api'

const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  projectId: {
    type: Number,
    required: true
  },
  synthesisData: {
    type: Object,
    default: () => ({})
  }
})

const emit = defineEmits(['update:visible', 'complete', 'start-audio-mixing'])

// 状态管理
const currentStep = ref(0)
const processing = ref(false)
const stepStatus = ref('process')

// 分析结果
const analysisResult = ref(null)
const validationData = ref(null)
const finalResult = ref(null)

// 编辑相关
const editDrawerVisible = ref(false)
const editingTrack = ref(null)
const editingTrackIndex = ref(-1)
const editForm = ref({
  keywords: [],
  sceneDescription: '',
  tangofluxPrompt: '',
  volume: 0.6
})

// 计算属性
const modalTitle = computed(() => {
  const titles = ['环境音需求分析', '人工校对配置', '生成完成']
  return titles[currentStep.value] || '环境音生成'
})

const keywordOptions = computed(() => {
  if (!analysisResult.value?.analysis_stats?.keyword_distribution) return []
  
  return Object.keys(analysisResult.value.analysis_stats.keyword_distribution).map(keyword => ({
    label: keyword,
    value: keyword
  }))
})

// 工具函数
const getHighConfidenceCount = () => {
  const distribution = analysisResult.value?.analysis_stats?.confidence_distribution || {}
  return distribution['高(>0.8)'] || 0
}

const getKeywordColor = (count) => {
  if (count >= 3) return 'red'
  if (count >= 2) return 'orange'
  return 'blue'
}

const getConfidenceColor = (confidence) => {
  if (confidence > 0.8) return 'green'
  if (confidence > 0.5) return 'orange'
  return 'red'
}

const getValidationStatusColor = (status) => {
  const colors = {
    'pending': 'default',
    'edited': 'blue',
    'approved': 'green',
    'rejected': 'red'
  }
  return colors[status] || 'default'
}

const getValidationStatusText = (status) => {
  const texts = {
    'pending': '待校对',
    'edited': '已编辑',
    'approved': '已通过',
    'rejected': '已拒绝'
  }
  return texts[status] || '未知'
}

const getCurrentKeywords = (track) => {
  if (track.inheritance_applied && track.inherited_environment) {
    return track.inherited_environment.all_keywords || []
  }
  return track.environment_keywords || []
}

const getApprovedCount = () => {
  if (!validationData.value?.validation_tracks) return 0
  return validationData.value.validation_tracks.filter(track => 
    track.validation_status === 'approved'
  ).length
}

const getManualEditCount = () => {
  if (!validationData.value?.validation_tracks) return 0
  return validationData.value.validation_tracks.filter(track => 
    track.manual_edits && Object.keys(track.manual_edits).length > 0
  ).length
}

const isAllApproved = () => {
  if (!validationData.value?.validation_tracks) return false
  return validationData.value.validation_tracks.every(track => 
    track.validation_status === 'approved'
  )
}

// 主要方法
const startAnalysis = async () => {
  try {
    processing.value = true
    
    const response = await api.analyzeEnvironment(props.projectId, props.synthesisData)
    
    if (response.data.success) {
      analysisResult.value = response.data
      message.success('环境音需求分析完成！')
    } else {
      message.error(response.data.message || '分析失败')
    }
  } catch (error) {
    console.error('环境音分析失败:', error)
    message.error('分析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    processing.value = false
  }
}

const restartAnalysis = () => {
  analysisResult.value = null
  validationData.value = null
  finalResult.value = null
  currentStep.value = 0
}

const proceedToValidation = async () => {
  try {
    processing.value = true
    
    const response = await api.prepareValidation(props.projectId)
    
    if (response.data.success) {
      validationData.value = response.data.validation_data
      currentStep.value = 1
      message.success('校对数据准备完成！')
    } else {
      message.error(response.data.message || '校对准备失败')
    }
  } catch (error) {
    console.error('校对准备失败:', error)
    message.error('校对准备失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    processing.value = false
  }
}

const editTrack = (trackIndex) => {
  const track = validationData.value.validation_tracks[trackIndex]
  editingTrack.value = track
  editingTrackIndex.value = trackIndex
  
  // 初始化编辑表单
  editForm.value = {
    keywords: getCurrentKeywords(track),
    sceneDescription: track.scene_description || track.inherited_environment?.scene_description || '',
    tangofluxPrompt: track.matching_suggestions?.[0]?.suggested_tangoflux_config?.prompt || '',
    volume: 0.6
  }
  
  editDrawerVisible.value = true
}

const closeEditDrawer = () => {
  editDrawerVisible.value = false
  editingTrack.value = null
  editingTrackIndex.value = -1
}

const saveTrackEdits = async () => {
  try {
    processing.value = true
    
    const manualEdits = {
      environment_keywords: editForm.value.keywords,
      scene_description: editForm.value.sceneDescription,
      selected_tangoflux_config: {
        prompt: editForm.value.tangofluxPrompt,
        volume: editForm.value.volume,
        duration: 30.0,
        fade_in: 3.0,
        fade_out: 2.0,
        loop: true
      }
    }
    
    const response = await api.editValidation(props.projectId, editingTrackIndex.value, manualEdits)
    
    if (response.data.success) {
      // 更新本地数据
      validationData.value.validation_tracks[editingTrackIndex.value] = response.data.updated_track
      message.success('轨道编辑保存成功！')
      closeEditDrawer()
    } else {
      message.error(response.data.message || '保存失败')
    }
  } catch (error) {
    console.error('保存轨道编辑失败:', error)
    message.error('保存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    processing.value = false
  }
}

const approveTrack = async (trackIndex) => {
  try {
    processing.value = true
    
    const response = await api.approveValidation(props.projectId, trackIndex, 'approved', '校对通过')
    
    if (response.data.success) {
      validationData.value.validation_tracks[trackIndex].validation_status = 'approved'
      validationData.value.validation_tracks[trackIndex].validation_timestamp = new Date().toISOString()
      message.success('轨道校对通过！')
    } else {
      message.error(response.data.message || '校对失败')
    }
  } catch (error) {
    console.error('轨道校对失败:', error)
    message.error('校对失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    processing.value = false
  }
}

const backToAnalysis = () => {
  currentStep.value = 0
}

const proceedToFinalize = async () => {
  try {
    processing.value = true
    
    const response = await api.finalizeGeneration(props.projectId)
    
    if (response.data.success) {
      finalResult.value = response.data
      currentStep.value = 2
      stepStatus.value = 'finish'
      message.success('环境音生成完成！')
    } else {
      message.error(response.data.message || '完成失败')
    }
  } catch (error) {
    console.error('完成环境音生成失败:', error)
    message.error('完成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    processing.value = false
  }
}

const handleComplete = () => {
  emit('update:visible', false)
  emit('complete', finalResult.value)
}

const handleStartAudioMixing = () => {
  emit('update:visible', false)
  emit('start-audio-mixing', finalResult.value)
}

const handleCancel = () => {
  if (processing.value) {
    message.warning('正在处理中，请稍候...')
    return
  }
  emit('update:visible', false)
}

// 监听visible变化，重置状态
watch(() => props.visible, (newVisible) => {
  if (newVisible) {
    // 重置状态
    currentStep.value = 0
    processing.value = false
    stepStatus.value = 'process'
    analysisResult.value = null
    validationData.value = null
    finalResult.value = null
  }
})
</script>

<style scoped>
.step-content {
  min-height: 400px;
}

.step-header {
  margin-bottom: 24px;
  text-align: center;
}

.step-header h3 {
  margin: 0 0 8px 0;
  font-size: 18px;
  font-weight: 600;
}

.analysis-start {
  text-align: center;
  padding: 40px 20px;
}

.analysis-actions {
  margin-top: 24px;
}

.analysis-stats {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
}

.keyword-distribution {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
}

.keyword-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.tracks-preview {
  background: #f8f9fa;
  padding: 16px;
  border-radius: 8px;
}

.tracks-list {
  max-height: 300px;
  overflow-y: auto;
}

.track-item {
  background: white;
  border: 1px solid #e8e8e8;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 8px;
}

.track-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.track-id {
  font-weight: 600;
}

.track-time {
  color: #666;
  font-size: 12px;
}

.track-content {
  font-size: 14px;
}

.track-keywords {
  margin-bottom: 4px;
}

.track-description {
  color: #666;
  font-size: 13px;
}

.validation-tracks {
  max-height: 400px;
  overflow-y: auto;
}

.validation-track {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  margin-bottom: 12px;
  transition: all 0.3s ease;
}

.validation-track:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
}

.track-approved {
  border-color: #52c41a;
  background-color: #f6ffed;
}

.track-validation-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.track-info {
  display: flex;
  align-items: center;
  gap: 12px;
}

.track-title {
  font-weight: 600;
}

.track-time {
  color: #666;
  font-size: 12px;
}

.track-actions {
  display: flex;
  gap: 8px;
}

.track-validation-content {
  font-size: 14px;
}

.inheritance-info {
  margin-bottom: 8px;
}

.environment-keywords {
  margin-bottom: 8px;
}

.label {
  font-weight: 500;
  margin-right: 8px;
}

.tangoflux-suggestions {
  background: #fafafa;
  padding: 8px;
  border-radius: 4px;
}

.suggestions-list {
  margin-top: 4px;
}

.suggestion-item {
  display: flex;
  margin-bottom: 4px;
  font-size: 13px;
}

.suggestion-keyword {
  font-weight: 500;
  margin-right: 8px;
  min-width: 80px;
}

.suggestion-prompt {
  color: #666;
}

.step-actions {
  display: flex;
  justify-content: space-between;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
}

.final-stats {
  margin-top: 16px;
}

.next-steps {
  margin-top: 24px;
}

.track-edit-form {
  padding: 16px 0;
}

.edit-actions {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  margin-top: 24px;
  padding-top: 16px;
  border-top: 1px solid #e8e8e8;
}
</style> 