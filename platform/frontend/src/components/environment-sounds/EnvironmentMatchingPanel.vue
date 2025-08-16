<template>
  <div class="environment-matching-panel">
    <div class="panel-header">
      <h3>🎵 环境音智能匹配</h3>
      <div class="header-actions">
        <a-button type="primary" @click="startMatching" :loading="matching" size="small">
          <template #icon><SyncOutlined /></template>
          开始匹配
        </a-button>
        <a-button @click="clearResults" :disabled="!hasResults" size="small"> 清除结果 </a-button>
      </div>
    </div>

    <!-- 匹配统计信息 -->
    <div v-if="matchingSummary" class="matching-summary">
      <a-row :gutter="16">
        <a-col :span="6">
          <a-statistic title="总轨道数" :value="matchingSummary.total_tracks" />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="已匹配"
            :value="matchingSummary.matched_tracks"
            :value-style="{ color: '#52c41a' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="需生成"
            :value="matchingSummary.need_generation_tracks"
            :value-style="{ color: '#fa8c16' }"
          />
        </a-col>
        <a-col :span="6">
          <a-statistic
            title="匹配率"
            :value="matchingSummary.match_rate"
            suffix="%"
            :value-style="getMatchRateStyle()"
          />
        </a-col>
      </a-row>
    </div>

    <!-- 匹配结果展示 -->
    <div v-if="hasResults" class="matching-results">
      <!-- 已匹配的环境音 -->
      <div class="matched-section">
        <h4>✅ 已匹配环境音</h4>
        <a-list :data-source="matchedSounds" size="small" :pagination="false">
          <template #renderItem="{ item }">
            <a-list-item>
              <a-list-item-meta>
                <template #title>
                  <span class="sound-name">{{ item.sound_name }}</span>
                  <a-tag color="green" size="small"
                    >匹配度: {{ (item.confidence * 100).toFixed(0) }}%</a-tag
                  >
                </template>
                <template #description>
                  <span>关键词: {{ item.keywords.join(', ') }}</span>
                  <span class="match-type">{{ getMatchTypeLabel(item.match_type) }}</span>
                </template>
              </a-list-item-meta>
              <template #actions>
                <a-button type="link" size="small" @click="previewSound(item.sound_id)">
                  预览
                </a-button>
                <a-button type="link" size="small" @click="confirmMatch(item)"> 确认 </a-button>
              </template>
            </a-list-item>
          </template>
        </a-list>
      </div>

      <!-- 需要生成的环境音 -->
      <div class="generation-section">
        <h4>🔧 需要生成环境音</h4>
        <div class="generation-actions">
          <a-button type="primary" @click="batchGenerate" :loading="generating" size="small">
            <template #icon><ThunderboltOutlined /></template>
            批量生成 ({{ needGenerationSounds.length }}个)
          </a-button>
          <a-button @click="selectAll" size="small">全选</a-button>
          <a-button @click="selectNone" size="small">取消全选</a-button>
        </div>

        <a-list :data-source="needGenerationSounds" size="small" :pagination="false">
          <template #renderItem="{ item }">
            <a-list-item>
              <template #actions>
                <a-checkbox v-model:checked="item.selected" @change="updateSelection" />
                <a-button type="link" size="small" @click="generateSingle(item)">
                  单独生成
                </a-button>
              </template>
              <a-list-item-meta>
                <template #title>
                  <span class="keyword-name">{{ item.keyword }}</span>
                  <a-tag color="orange" size="small">使用{{ item.track_count }}次</a-tag>
                  <a-tag :color="getIntensityColor(item.intensity_level)" size="small">
                    {{ getIntensityLabel(item.intensity_level) }}
                  </a-tag>
                </template>
                <template #description>
                  <div>
                    <span>场景: {{ item.example_scene }}</span>
                    <span class="duration">建议时长: {{ item.suggested_duration }}秒</span>
                  </div>
                </template>
              </a-list-item-meta>
            </a-list-item>
          </template>
        </a-list>
      </div>

      <!-- 操作按钮 -->
      <div class="panel-actions">
        <a-button type="primary" size="large" @click="proceedToGeneration" :disabled="!canProceed">
          继续到环境音生成
        </a-button>
        <a-button @click="exportResults" size="large"> 导出配置 </a-button>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-state">
      <a-empty description="暂无匹配结果">
        <template #image>
          <SoundOutlined style="font-size: 48px; color: #ccc" />
        </template>
        <a-button type="primary" @click="startMatching">开始匹配环境音</a-button>
      </a-empty>
    </div>
  </div>
</template>

<script>
  import { ref, computed, watch } from 'vue'
  import { message } from 'ant-design-vue'
  import { SyncOutlined, ThunderboltOutlined, SoundOutlined } from '@ant-design/icons-vue'
  import api from '@/api'

  export default {
    name: 'EnvironmentMatchingPanel',
    components: {
      SyncOutlined,
      ThunderboltOutlined,
      SoundOutlined
    },
    props: {
      analysisResult: {
        type: Object,
        default: () => ({})
      },
      matchingResult: {
        type: Object,
        default: () => null
      }
    },
    emits: ['matched', 'generation-plan', 'proceed'],
    setup(props, { emit }) {
      // 响应式数据
      const matching = ref(false)
      const generating = ref(false)
      const matchingResults = ref(null)
      const selectedSounds = ref([])

      // 计算属性
      const hasResults = computed(() => {
        // 优先使用外部传入的匹配结果
        const results = props.matchingResult || matchingResults.value
        const hasEnhanced = results && results.enhanced_analysis_result



        return hasEnhanced
      })

      const matchingSummary = computed(() => {
        const results = props.matchingResult || matchingResults.value
        const summary = results?.matching_summary || null



        return summary
      })

      const matchedSounds = computed(() => {
        const results = props.matchingResult || matchingResults.value
        if (!results?.enhanced_analysis_result) return []

        const tracks = results.enhanced_analysis_result.environment_tracks || []
        return tracks
          .filter((track) => track.has_match && track.best_match)
          .map((track) => ({
            ...track.best_match,
            keywords: track.environment_keywords || [],
            track_id: track.segment_id
          }))
      })

      const needGenerationSounds = computed(() => {
        const results = props.matchingResult || matchingResults.value
        if (!results?.generation_plan) return []

        return results.generation_plan.need_generation.map((item) => ({
          ...item,
          selected: true // 默认全选
        }))
      })

      const canProceed = computed(() => {
        return (
          hasResults.value &&
          (matchedSounds.value.length > 0 || needGenerationSounds.value.length > 0)
        )
      })

      // 方法
      const getMatchRateStyle = () => {
        const rate = matchingSummary.value?.match_rate || 0
        if (rate >= 80) return { color: '#52c41a' }
        if (rate >= 50) return { color: '#fa8c16' }
        return { color: '#ff4d4f' }
      }

      const getMatchTypeLabel = (type) => {
        const labels = {
          exact: '精确匹配',
          semantic: '语义匹配',
          tag: '标签匹配',
          fuzzy: '模糊匹配'
        }
        return labels[type] || type
      }

      const getIntensityColor = (level) => {
        const colors = {
          high: 'red',
          medium: 'orange',
          low: 'green'
        }
        return colors[level] || 'default'
      }

      const getIntensityLabel = (level) => {
        const labels = {
          high: '高强度',
          medium: '中强度',
          low: '低强度'
        }
        return labels[level] || level
      }

      const startMatching = async () => {
        // 检查分析结果的多种格式
        let hasEnvironmentTracks = false

        if (props.analysisResult) {
          // 直接包含environment_tracks
          if (
            props.analysisResult.environment_tracks &&
            props.analysisResult.environment_tracks.length > 0
          ) {
            hasEnvironmentTracks = true
          }
          // 或者包含chapters格式
          else if (props.analysisResult.chapters && props.analysisResult.chapters.length > 0) {
            const hasChapterTracks = props.analysisResult.chapters.some(
              (chapter) =>
                chapter.analysis_result &&
                chapter.analysis_result.environment_tracks &&
                chapter.analysis_result.environment_tracks.length > 0
            )
            hasEnvironmentTracks = hasChapterTracks
          }
        }

        if (!hasEnvironmentTracks) {
          message.warning('请先完成环境音分析，没有找到可匹配的环境轨道')
          return
        }

        matching.value = true
        try {
          const response = await api.environmentGenerationAPI.matchEnvironmentSounds(
            props.analysisResult
          )

          if (response.data.success) {
            matchingResults.value = response.data
            emit('matched', response.data)
            message.success(`匹配完成！找到${matchingSummary.value.matched_tracks}个匹配项`)
          } else {
            message.error('匹配失败')
          }
        } catch (error) {
          console.error('环境音匹配失败:', error)
          message.error('匹配失败: ' + (error.response?.data?.detail || error.message))
        } finally {
          matching.value = false
        }
      }

      const clearResults = () => {
        matchingResults.value = null
        selectedSounds.value = []
      }

      const previewSound = async (soundId) => {
        try {
          message.info('正在准备预览...')
          // 这里调用环境音预览API
          // await api.environmentSoundsAPI.playEnvironmentSound(soundId)
        } catch (error) {
          message.error('预览失败')
        }
      }

      const confirmMatch = (matchItem) => {
        message.success(`已确认匹配: ${matchItem.sound_name}`)
        // 这里可以添加确认逻辑
      }

      const selectAll = () => {
        needGenerationSounds.value.forEach((item) => {
          item.selected = true
        })
        updateSelection()
      }

      const selectNone = () => {
        needGenerationSounds.value.forEach((item) => {
          item.selected = false
        })
        updateSelection()
      }

      const updateSelection = () => {
        selectedSounds.value = needGenerationSounds.value.filter((item) => item.selected)
      }

      const batchGenerate = async () => {
        const selected = needGenerationSounds.value.filter((item) => item.selected)
        if (selected.length === 0) {
          message.warning('请选择要生成的环境音')
          return
        }

        generating.value = true
        try {
          // 这里调用批量生成API
          message.success(`开始批量生成${selected.length}个环境音`)
          emit('generation-plan', selected)
        } catch (error) {
          message.error('批量生成失败')
        } finally {
          generating.value = false
        }
      }

      const generateSingle = async (item) => {
        try {
          message.success(`开始生成: ${item.keyword}`)
          // 这里调用单个生成API
        } catch (error) {
          message.error('生成失败')
        }
      }

      const proceedToGeneration = () => {
        emit('proceed', {
          matchingResults: matchingResults.value,
          selectedSounds: selectedSounds.value
        })
      }

      const exportResults = () => {
        if (!hasResults.value) return

        const data = {
          matching_summary: matchingSummary.value,
          matched_sounds: matchedSounds.value,
          generation_plan: needGenerationSounds.value.filter((item) => item.selected)
        }

        const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
        const url = URL.createObjectURL(blob)
        const a = document.createElement('a')
        a.href = url
        a.download = `environment_matching_${Date.now()}.json`
        a.click()
        URL.revokeObjectURL(url)

        message.success('配置已导出')
      }

      // 监听分析结果变化
      watch(
        () => props.analysisResult,
        () => {
          if (hasResults.value) {
            clearResults()
          }
        },
        { deep: true }
      )

      return {
        // 响应式数据
        matching,
        generating,
        matchingResults,
        selectedSounds,

        // 计算属性
        hasResults,
        matchingSummary,
        matchedSounds,
        needGenerationSounds,
        canProceed,

        // 方法
        getMatchRateStyle,
        getMatchTypeLabel,
        getIntensityColor,
        getIntensityLabel,
        startMatching,
        clearResults,
        previewSound,
        confirmMatch,
        selectAll,
        selectNone,
        updateSelection,
        batchGenerate,
        generateSingle,
        proceedToGeneration,
        exportResults
      }
    }
  }
</script>

<style scoped>
  .environment-matching-panel {
    padding: 16px;
    background: #fafafa;
    border-radius: 8px;
  }

  .panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding-bottom: 12px;
    border-bottom: 1px solid #e8e8e8;
  }

  .panel-header h3 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
  }

  .header-actions {
    display: flex;
    gap: 8px;
  }

  .matching-summary {
    margin-bottom: 24px;
    padding: 16px;
    background: white;
    border-radius: 6px;
    border: 1px solid #e8e8e8;
  }

  .matching-results {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .matched-section,
  .generation-section {
    background: white;
    border-radius: 6px;
    border: 1px solid #e8e8e8;
    overflow: hidden;
  }

  .matched-section h4,
  .generation-section h4 {
    margin: 0;
    padding: 12px 16px;
    background: #f5f5f5;
    border-bottom: 1px solid #e8e8e8;
    font-size: 14px;
    font-weight: 600;
  }

  .generation-actions {
    padding: 12px 16px;
    background: #f9f9f9;
    border-bottom: 1px solid #e8e8e8;
    display: flex;
    gap: 8px;
    align-items: center;
  }

  .sound-name {
    font-weight: 500;
    margin-right: 8px;
  }

  .keyword-name {
    font-weight: 500;
    margin-right: 8px;
  }

  .match-type {
    margin-left: 8px;
    color: #666;
    font-size: 12px;
  }

  .duration {
    margin-left: 12px;
    color: #666;
    font-size: 12px;
  }

  .panel-actions {
    margin-top: 24px;
    text-align: center;
    display: flex;
    gap: 16px;
    justify-content: center;
  }

  .empty-state {
    padding: 48px 24px;
    text-align: center;
  }

  @media (max-width: 768px) {
    .panel-header {
      flex-direction: column;
      gap: 12px;
      align-items: stretch;
    }

    .header-actions {
      justify-content: center;
    }

    .generation-actions {
      flex-direction: column;
      gap: 8px;
      align-items: stretch;
    }

    .panel-actions {
      flex-direction: column;
    }
  }
</style>
