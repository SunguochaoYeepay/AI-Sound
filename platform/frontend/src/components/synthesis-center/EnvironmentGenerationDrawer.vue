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
    <a-steps :current="currentStep" size="small" class="mb-6" :status="stepStatus">
      <a-step title="环境分析" description="分析旁白内容" />
      <a-step title="生成完成" description="结果展示与编辑" />
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
          <a-button type="primary" size="large" :loading="processing" @click="startAnalysis">
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
                <span class="track-time"
                  >{{ track.start_time?.toFixed(1) }}s -
                  {{ (track.start_time + track.duration)?.toFixed(1) }}s</span
                >
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
            <template #icon><ReloadOutlined /></template>
            重新分析
          </a-button>
        </div>
      </div>
    </div>

    <!-- 步骤2：生成完成 -->
    <div v-if="currentStep === 1" class="step-content">
      <div class="step-header">
        <h3>🎉 环境音配置生成完成</h3>
        <p class="text-gray-600">环境音配置已生成，可以查看和编辑配置</p>
      </div>

      <div v-if="finalResult" class="final-result">
        <!-- 配置总览 -->
        <div class="config-summary mb-4">
          <a-alert
            :message="`配置完成：生成 ${finalResult.config?.environment_tracks?.length || 0} 个环境音轨道`"
            :description="`总时长 ${finalResult.analysis_stats?.total_duration || 0}秒，平均时长 ${finalResult.analysis_stats?.avg_duration || 0}秒`"
            type="success"
            show-icon
          />
        </div>

        <!-- 环境音轨道列表 -->
        <div class="environment-tracks-list">
          <h4>🎵 环境音轨道配置</h4>
          <div
            v-for="(track, index) in finalResult.config?.environment_tracks || []"
            :key="track.segment_id"
            class="track-config-item"
          >
            <div class="track-header">
              <div class="track-info">
                <span class="track-title">轨道 {{ index + 1 }} (段落 {{ track.segment_id }})</span>
                <span class="track-time"
                  >{{ track.start_time?.toFixed(1) }}s -
                  {{ (track.start_time + track.duration)?.toFixed(1) }}s</span
                >
                <a-tag :color="getConfidenceColor(track.confidence)">
                  置信度 {{ (track.confidence * 100)?.toFixed(0) }}%
                </a-tag>
              </div>

              <div class="track-actions">
                <a-button size="small" @click="editTrack(index)" :disabled="processing">
                  编辑
                </a-button>
              </div>
            </div>

            <div class="track-content">
              <!-- 环境关键词 -->
              <div class="environment-keywords mb-2">
                <span class="label">环境关键词：</span>
                <a-tag
                  v-for="keyword in track.environment_keywords || []"
                  :key="keyword"
                  size="small"
                  class="mr-1"
                >
                  {{ keyword }}
                </a-tag>
              </div>

              <!-- 场景描述 -->
              <div class="scene-description mb-2">
                <span class="label">场景描述：</span>
                <span class="description-text">{{ track.scene_description }}</span>
              </div>

              <!-- TangoFlux配置 -->
              <div class="tangoflux-config">
                <span class="label">TangoFlux提示词：</span>
                <span class="config-text">{{ track.tangoflux_config?.prompt || '未配置' }}</span>
              </div>
            </div>
          </div>
        </div>

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
          <a-button @click="handleComplete"> 完成 </a-button>
          <a-button type="primary" @click="handleStartAudioMixing"> 开始音频混合 </a-button>
        </div>
      </div>
    </div>

    <!-- 轨道编辑抽屉 -->
    <a-drawer
      :visible="editDrawerVisible"
      title="编辑环境音配置"
      :width="800"
      @close="closeEditDrawer"
    >
      <div v-if="editingTrack" class="track-edit-form">
        <!-- 编辑表单内容 -->
        <a-form layout="vertical">
          <a-form-item label="环境关键词" required>
            <a-select
              v-model:value="editForm.keywords"
              mode="tags"
              placeholder="输入环境关键词，如：脚步声、雨声、风声等"
              :options="keywordOptions"
              style="width: 100%"
            />
            <div class="form-help">可以输入多个关键词，按回车添加</div>
          </a-form-item>

          <a-form-item label="场景描述">
            <a-textarea
              v-model:value="editForm.sceneDescription"
              placeholder="描述环境场景，如：教室里的安静氛围，雨夜的街道等"
              :rows="3"
            />
          </a-form-item>

          <!-- 环境音选择 -->
          <a-form-item label="环境音选择">
            <div class="environment-sound-selector">
              <a-tabs v-model:activeKey="soundSelectionMode" class="mb-4">
                <a-tab-pane key="library" tab="🎵 从环境音库选择">
                  <div class="sound-library-section">
                    <!-- 搜索和筛选 -->
                    <div class="library-filters mb-4">
                      <a-row :gutter="16">
                        <a-col :span="12">
                          <a-input-search
                            v-model:value="soundSearchQuery"
                            placeholder="搜索环境音..."
                            @search="searchEnvironmentSounds"
                            @change="debounceSearch"
                          />
                        </a-col>
                        <a-col :span="6">
                          <a-select
                            v-model:value="selectedSoundCategory"
                            placeholder="选择分类"
                            allowClear
                            @change="loadEnvironmentSounds"
                          >
                            <a-select-option
                              v-for="category in soundCategories"
                              :key="category.id"
                              :value="category.id"
                            >
                              {{ category.name }}
                            </a-select-option>
                          </a-select>
                        </a-col>
                        <a-col :span="6">
                          <a-select
                            v-model:value="selectedSoundStatus"
                            placeholder="状态筛选"
                            allowClear
                            @change="loadEnvironmentSounds"
                          >
                            <a-select-option value="completed">已完成</a-select-option>
                            <a-select-option value="processing">生成中</a-select-option>
                            <a-select-option value="failed">失败</a-select-option>
                          </a-select>
                        </a-col>
                      </a-row>
                    </div>

                    <!-- 环境音列表 -->
                    <div class="sound-list" v-if="environmentSounds.length > 0">
                      <div
                        v-for="sound in environmentSounds"
                        :key="sound.id"
                        class="sound-item"
                        :class="{
                          'sound-selected': editForm.selectedSoundId === sound.id,
                          'sound-disabled': sound.generation_status !== 'completed'
                        }"
                        @click="selectEnvironmentSound(sound)"
                      >
                        <div class="sound-info">
                          <div class="sound-header">
                            <span class="sound-name">{{ sound.name }}</span>
                            <div class="sound-badges">
                              <a-badge
                                :status="getSoundStatusType(sound.generation_status)"
                                :text="getSoundStatusText(sound.generation_status)"
                              />
                              <a-tag v-if="sound.is_featured" color="gold" size="small">精选</a-tag>
                            </div>
                          </div>
                          <div class="sound-meta">
                            <span class="sound-category">{{
                              sound.category?.name || '未分类'
                            }}</span>
                            <span class="sound-duration">{{ sound.duration }}s</span>
                            <span class="sound-stats">播放{{ sound.play_count }}次</span>
                          </div>
                          <div class="sound-prompt">{{ sound.prompt }}</div>
                          <div class="sound-tags" v-if="sound.tags && sound.tags.length > 0">
                            <a-tag v-for="tag in sound.tags" :key="tag.id" size="small">
                              {{ tag.name }}
                            </a-tag>
                          </div>
                        </div>
                        <div class="sound-actions" v-if="sound.generation_status === 'completed'">
                          <a-button
                            size="small"
                            @click.stop="previewSound(sound)"
                            :loading="previewingId === sound.id"
                          >
                            <template #icon><PlayCircleOutlined /></template>
                            试听
                          </a-button>
                        </div>
                      </div>
                    </div>

                    <!-- 空状态 -->
                    <div v-else-if="!loadingSounds" class="empty-state">
                      <a-empty description="暂无环境音" />
                    </div>

                    <!-- 加载状态 -->
                    <div v-if="loadingSounds" class="loading-state">
                      <a-spin size="large" />
                    </div>

                    <!-- 分页 -->
                    <div class="pagination-section" v-if="soundPagination.total > 0">
                      <a-pagination
                        v-model:current="soundPagination.current"
                        :total="soundPagination.total"
                        :page-size="soundPagination.pageSize"
                        :show-size-changer="false"
                        :show-quick-jumper="true"
                        @change="onSoundPageChange"
                      />
                    </div>
                  </div>
                </a-tab-pane>

                <a-tab-pane key="custom" tab="✏️ 自定义TangoFlux">
                  <div class="custom-prompt-section">
                    <a-form-item label="TangoFlux提示词" required>
                      <a-textarea
                        v-model:value="editForm.tangofluxPrompt"
                        placeholder="TangoFlux生成提示词，如：gentle footsteps on wooden floor, soft rain on window"
                        :rows="3"
                      />
                      <div class="form-help">建议使用英文描述，更准确地生成环境音效果</div>
                    </a-form-item>
                  </div>
                </a-tab-pane>
              </a-tabs>
            </div>
          </a-form-item>

          <a-form-item label="音量设置">
            <a-slider
              v-model:value="editForm.volume"
              :min="0"
              :max="1"
              :step="0.1"
              :marks="{ 0: '静音', 0.3: '轻柔', 0.6: '适中', 1: '响亮' }"
            />
            <div class="form-help">当前音量：{{ (editForm.volume * 100).toFixed(0) }}%</div>
          </a-form-item>

          <!-- 选中的环境音预览 -->
          <div v-if="editForm.selectedSoundId && selectedSoundInfo" class="selected-sound-preview">
            <a-alert
              :message="`已选择环境音: ${selectedSoundInfo.name}`"
              :description="`提示词: ${selectedSoundInfo.prompt}`"
              type="success"
              show-icon
            />
          </div>
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
  import { ref, computed, watch, onMounted } from 'vue'
  import { message } from 'ant-design-vue'
  import { SearchOutlined, ReloadOutlined, PlayCircleOutlined } from '@ant-design/icons-vue'
  import api from '@/api'
  import { environmentSoundsAPI } from '@/api'
  import { getAudioService } from '@/utils/audioService'

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

  const emit = defineEmits([
    'update:visible',
    'complete',
    'start-audio-mixing',
    'environment-data-updated'
  ])

  // 状态管理
  const currentStep = ref(0)
  const processing = ref(false)
  const stepStatus = ref('process')

  // 分析结果
  const analysisResult = ref(null)
  const finalResult = ref(null)

  // 编辑相关
  const editDrawerVisible = ref(false)
  const editingTrack = ref(null)
  const editingTrackIndex = ref(-1)
  const editForm = ref({
    keywords: [],
    sceneDescription: '',
    tangofluxPrompt: '',
    volume: 0.6,
    selectedSoundId: null
  })

  // 环境音库相关
  const soundSelectionMode = ref('library')
  const environmentSounds = ref([])
  const soundCategories = ref([])
  const loadingSounds = ref(false)
  const previewingId = ref(null)
  const soundSearchQuery = ref('')
  const selectedSoundCategory = ref(null)
  const selectedSoundStatus = ref('completed')
  const soundPagination = ref({
    current: 1,
    pageSize: 10,
    total: 0
  })

  // 搜索防抖
  let searchTimeout = null

  // 计算属性
  const modalTitle = computed(() => {
    const titles = ['环境音需求分析', '生成完成']
    return titles[currentStep.value] || '环境音生成'
  })

  const keywordOptions = computed(() => {
    if (!analysisResult.value?.analysis_stats?.keyword_distribution) return []

    return Object.keys(analysisResult.value.analysis_stats.keyword_distribution).map((keyword) => ({
      label: keyword,
      value: keyword
    }))
  })

  const selectedSoundInfo = computed(() => {
    if (!editForm.value.selectedSoundId) return null
    return environmentSounds.value.find((sound) => sound.id === editForm.value.selectedSoundId)
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

  // 主要方法
  const startAnalysis = async (forceReanalyze = false) => {
    try {
      processing.value = true

      // 显示预估时间提示
      const narrationCount =
        props.synthesisData?.synthesis_plan?.filter(
          (seg) => seg.speaker === '旁白' || seg.character === '旁白'
        ).length || 0

      if (forceReanalyze) {
        message.info('正在重新分析环境音需求，请稍候...', 3)
      } else if (narrationCount > 10) {
        message.info(
          `检测到${narrationCount}个旁白段落，预计需要${Math.ceil((narrationCount * 10) / 60)}分钟分析时间，请耐心等待...`,
          6
        )
      } else {
        message.info('正在分析环境音需求，请稍候...', 3)
      }

      const response = await api.analyzeEnvironment(props.projectId, {
        ...props.synthesisData,
        options: {
          ...props.synthesisData?.options,
          force_reanalyze: forceReanalyze
        }
      })

      if (response.data.success) {
        analysisResult.value = response.data

        // 直接进入最终结果展示，跳过校对步骤
        message.success({
          content: '环境音需求分析完成！正在准备结果展示...',
          duration: 3
        })

        // 直接完成流程
        await proceedToFinalize()
      } else {
        message.error(response.data.message || '分析失败')
      }
    } catch (error) {
      console.error('环境音分析失败:', error)
      if (error.code === 'ECONNABORTED' || error.message.includes('timeout')) {
        message.error('分析超时，可能是因为旁白内容较多。请稍后重试或联系管理员。')
      } else {
        message.error('分析失败: ' + (error.response?.data?.detail || error.message))
      }
    } finally {
      processing.value = false
    }
  }

  const restartAnalysis = async () => {
    // 重新分析：清空数据并强制重新分析
    analysisResult.value = null
    finalResult.value = null
    currentStep.value = 0

    // 立即开始重新分析
    await startAnalysis(true)
  }

  const editTrack = (trackIndex) => {
    const track = finalResult.value.config.environment_tracks[trackIndex]
    editingTrack.value = track
    editingTrackIndex.value = trackIndex

    // 初始化编辑表单
    editForm.value = {
      keywords: track.environment_keywords || [],
      sceneDescription: track.scene_description || '',
      tangofluxPrompt: track.tangoflux_config?.prompt || '',
      volume: track.tangoflux_config?.volume || 0.6,
      selectedSoundId: track.environment_sound_id || null
    }

    // 设置选择模式
    soundSelectionMode.value = track.environment_sound_id ? 'library' : 'custom'

    editDrawerVisible.value = true

    // 加载环境音库数据
    loadSoundCategories()
    loadEnvironmentSounds()
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
        environment_sound_id: editForm.value.selectedSoundId,
        tangoflux_config: {
          prompt: editForm.value.tangofluxPrompt,
          volume: editForm.value.volume,
          duration: 30.0,
          fade_in: 3.0,
          fade_out: 2.0,
          loop: true
        }
      }

      // 如果选择了环境音库中的音频，使用其提示词
      if (editForm.value.selectedSoundId && selectedSoundInfo.value) {
        manualEdits.tangoflux_config.prompt = selectedSoundInfo.value.prompt
        manualEdits.tangoflux_config.duration = selectedSoundInfo.value.duration
      }

      const response = await api.updateTrackConfig(
        props.projectId,
        editingTrackIndex.value,
        manualEdits
      )

      if (response.data.success) {
        // 更新本地数据
        finalResult.value.config.environment_tracks[editingTrackIndex.value] = {
          ...finalResult.value.config.environment_tracks[editingTrackIndex.value],
          ...manualEdits
        }
        message.success('轨道配置保存成功！')
        closeEditDrawer()

        // 🎯 重要：通知父组件刷新环境音数据
        emit('environment-data-updated')
      } else {
        message.error(response.data.message || '保存失败')
      }
    } catch (error) {
      console.error('保存轨道配置失败:', error)
      message.error('保存失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      processing.value = false
    }
  }

  const proceedToFinalize = async () => {
    try {
      processing.value = true

      const response = await api.finalizeGeneration(props.projectId)

      if (response.data.success) {
        finalResult.value = response.data
        currentStep.value = 1
        stepStatus.value = 'finish'
        message.success({
          content: '🎉 环境音配置生成完成！现在可以在段落列表中查看环境音标签',
          duration: 6,
          key: 'env-generation-complete'
        })
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
    emit('complete')
    emit('update:visible', false)
  }

  const handleStartAudioMixing = () => {
    emit('start-audio-mixing', finalResult.value)
    emit('update:visible', false)
  }

  const handleCancel = () => {
    if (!processing.value) {
      emit('update:visible', false)
    }
  }

  // 环境音库相关方法
  const loadSoundCategories = async () => {
    try {
      const response = await environmentSoundsAPI.getCategories({ active_only: true })
      soundCategories.value = response.data
    } catch (error) {
      console.error('加载环境音分类失败:', error)
    }
  }

  const loadEnvironmentSounds = async () => {
    try {
      loadingSounds.value = true

      const params = {
        page: soundPagination.value.current,
        page_size: soundPagination.value.pageSize,
        status: selectedSoundStatus.value,
        sort_by: 'created_at',
        sort_order: 'desc'
      }

      if (selectedSoundCategory.value) {
        params.category_id = selectedSoundCategory.value
      }

      if (soundSearchQuery.value.trim()) {
        params.search = soundSearchQuery.value.trim()
      }

      const response = await environmentSoundsAPI.getEnvironmentSounds(params)
      const data = response.data

      environmentSounds.value = data.sounds || []
      soundPagination.value.total = data.total || 0
      soundPagination.value.current = data.page || 1
      soundPagination.value.pageSize = data.page_size || 10
    } catch (error) {
      console.error('加载环境音列表失败:', error)
      message.error('加载环境音列表失败')
    } finally {
      loadingSounds.value = false
    }
  }

  const searchEnvironmentSounds = () => {
    soundPagination.value.current = 1
    loadEnvironmentSounds()
  }

  const debounceSearch = () => {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }
    searchTimeout = setTimeout(() => {
      searchEnvironmentSounds()
    }, 500)
  }

  const onSoundPageChange = (page) => {
    soundPagination.value.current = page
    loadEnvironmentSounds()
  }

  const selectEnvironmentSound = (sound) => {
    if (sound.generation_status !== 'completed') {
      message.warning('该环境音尚未生成完成，无法选择')
      return
    }

    editForm.value.selectedSoundId = sound.id
    // 自动填充提示词
    editForm.value.tangofluxPrompt = sound.prompt

    message.success(`已选择环境音: ${sound.name}`)
  }

  const previewSound = async (sound) => {
    try {
      previewingId.value = sound.id

      // 使用统一音频服务播放
      await getAudioService().playEnvironmentSound(sound)

      // 记录播放日志
      await environmentSoundsAPI.playEnvironmentSound(sound.id)
    } catch (error) {
      console.error('试听失败:', error)
      message.error('试听失败')
    } finally {
      previewingId.value = null
    }
  }

  const getSoundStatusType = (status) => {
    const statusMap = {
      completed: 'success',
      processing: 'processing',
      failed: 'error',
      pending: 'default'
    }
    return statusMap[status] || 'default'
  }

  const getSoundStatusText = (status) => {
    const statusMap = {
      completed: '已完成',
      processing: '生成中',
      failed: '失败',
      pending: '待生成'
    }
    return statusMap[status] || '未知'
  }

  // 监听visible变化，重置状态
  watch(
    () => props.visible,
    async (newVisible) => {
      if (newVisible) {
        // 重置状态
        currentStep.value = 0
        processing.value = false
        stepStatus.value = 'process'
        analysisResult.value = null

        // 🎯 检查是否已有环境音配置，如果有则直接跳到完成步骤
        try {
          const configResponse = await api.getEnvironmentConfig(props.projectId)
          if (configResponse.data.success && configResponse.data.config) {
            console.log('🎉 发现已有环境音配置，直接显示结果')
            finalResult.value = configResponse.data
            currentStep.value = 1
            stepStatus.value = 'finish'
            return
          }
        } catch (error) {
  
        }

        // 如果没有配置，重置finalResult并开始分析
        finalResult.value = null

        // 自动检查是否有已有分析结果，如果没有则自动启动分析
        await startAnalysis(false)
      }
    }
  )
</script>

<style scoped>
  .step-content {
    margin-top: 16px;
  }

  .step-header {
    margin-bottom: 24px;
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
    max-height: 200px;
    overflow-y: auto;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
    gap: 12px;
  }

  .track-item {
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    padding: 10px;
    height: fit-content;
    min-height: 100px;
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

  .track-config-item {
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 12px;
    background: #fafafa;
    transition: all 0.3s ease;
    height: fit-content;
  }

  .track-config-item:hover {
    border-color: #1890ff;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
  }

  .track-info {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .track-title {
    font-weight: 600;
  }

  .track-actions {
    display: flex;
    gap: 8px;
  }

  .environment-keywords {
    margin-bottom: 8px;
  }

  .label {
    font-weight: 500;
    margin-right: 8px;
  }

  .description-text,
  .config-text {
    color: #6b7280;
    font-size: 13px;
  }

  .step-actions {
    display: flex;
    justify-content: space-between;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #e8e8e8;
  }

  .config-summary {
    margin-bottom: 24px;
  }

  .environment-tracks-list h4 {
    margin-bottom: 16px;
    color: #1f2937;
  }

  .environment-tracks-list {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(400px, 1fr));
    gap: 16px;
  }

  .next-steps {
    margin-top: 24px;
  }

  .track-edit-form {
    padding: 16px 0;
  }

  .form-help {
    font-size: 12px;
    color: #666;
    margin-top: 4px;
    line-height: 1.4;
  }

  .edit-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #e8e8e8;
  }

  .environment-sound-selector {
    margin-bottom: 24px;
  }

  .sound-library-section {
    padding: 16px;
  }

  .library-filters {
    margin-bottom: 16px;
  }

  .sound-list {
    max-height: 200px;
    overflow-y: auto;
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 12px;
  }

  .sound-item {
    background: white;
    border: 1px solid #e8e8e8;
    border-radius: 6px;
    padding: 10px;
    cursor: pointer;
    transition: all 0.3s ease;
    height: fit-content;
    min-height: 120px;
  }

  .sound-item:hover {
    border-color: #1890ff;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
  }

  .sound-item.sound-selected {
    border-color: #1890ff;
    background: #f6ffed;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.2);
  }

  .sound-item.sound-disabled {
    opacity: 0.6;
    cursor: not-allowed;
    background: #f5f5f5;
  }

  .sound-info {
    display: flex;
    flex-direction: column;
  }

  .sound-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 8px;
  }

  .sound-name {
    font-weight: 600;
  }

  .sound-badges {
    display: flex;
    gap: 8px;
  }

  .sound-meta {
    color: #666;
    font-size: 12px;
    display: flex;
    gap: 16px;
    margin-bottom: 4px;
  }

  .sound-prompt {
    margin-top: 8px;
    color: #666;
    font-size: 13px;
  }

  .sound-tags {
    margin-top: 8px;
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
  }

  .sound-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }

  .selected-sound-preview {
    margin-top: 24px;
  }

  .empty-state,
  .loading-state {
    text-align: center;
    padding: 40px 20px;
  }

  .pagination-section {
    display: flex;
    justify-content: center;
    margin-top: 16px;
  }

  .custom-prompt-section {
    padding: 16px;
  }
</style>
