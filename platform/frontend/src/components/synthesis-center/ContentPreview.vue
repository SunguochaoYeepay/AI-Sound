<template>
  <div class="content-preview">
    <!-- 智能准备结果 -->
    <div
      v-if="preparationResults && preparationResults.data && preparationResults.data.length > 0"
      class="preparation-preview"
    >
      <div class="dialogue-preview">
        <div class="dialogue-list">
          <div v-for="(chapterResult, chapterIndex) in preparationResults.data" :key="chapterIndex">
            <!-- 章节标题 -->
            <div class="chapter-divider">
              <div class="chapter-title-section">
                <span class="chapter-title">
                  第{{ chapterResult.chapter_number }}章 {{ chapterResult.chapter_title }}
                </span>
                <div class="chapter-stats">
                  <a-space>
                    <a-tag color="blue"
                      >📋
                      {{ chapterResult.synthesis_json?.synthesis_plan?.length || 0 }} 个段落</a-tag
                    >
                    <a-tag color="green"
                      >🎭 {{ getChapterCharacterCount(chapterResult) }} 个角色</a-tag
                    >
                    <a-tag :color="getChapterStatusColor(chapterResult.chapter_id)"
                      >状态: {{ getChapterStatusText(chapterResult.chapter_id) }}</a-tag
                    >
                  </a-space>
                </div>
              </div>
              <div class="chapter-actions">
                <!-- 刷新按钮 -->
                <a-button
                  v-if="preparationResults && selectedChapter"
                  @click="handleRefreshPreparation"
                  :loading="contentLoading"
                  size="small"
                  type="text"
                >
                  🔄 刷新
                </a-button>

                <!-- 合成控制按钮 -->
                <a-space size="small">
                  <!-- 待处理状态：显示对话语音生成按钮 -->
                  <template
                    v-if="
                      selectedChapterStatus === 'pending' ||
                      selectedChapterStatus === 'ready' ||
                      !selectedChapterStatus
                    "
                  >
                    <a-button
                      type="primary"
                      size="small"
                      :disabled="!canStart || synthesisStarting"
                      :loading="synthesisStarting"
                      @click="$emit('start-synthesis')"
                    >
                      🎤 对话语音生成
                    </a-button>
                  </template>

                  <!-- 完成状态：显示播放、下载和重新合成按钮 -->
                  <template v-else-if="selectedChapterStatus === 'completed'">
                    <a-button
                      type="primary"
                      size="small"
                      @click="$emit('play-chapter', selectedChapter)"
                      :loading="playingChapterAudio === selectedChapter"
                    >
                      🎵 播放
                    </a-button>
                    <a-button size="small" @click="$emit('download-chapter', selectedChapter)">
                      ⬇️ 下载
                    </a-button>
                    <a-button size="small" @click="$emit('restart-synthesis')">
                      🔄 重新合成
                    </a-button>
                  </template>

                  <!-- 处理中状态：显示暂停和取消按钮 -->
                  <template v-else-if="selectedChapterStatus === 'processing'">
                    <a-button size="small" @click="$emit('pause-synthesis')"> 暂停 </a-button>
                    <a-button size="small" @click="$emit('cancel-synthesis')"> 取消 </a-button>
                  </template>

                  <!-- 部分完成状态：显示继续合成和重新合成按钮 -->
                  <template v-else-if="selectedChapterStatus === 'partial'">
                    <a-button
                      type="primary"
                      size="small"
                      @click="$emit('resume-synthesis')"
                      :disabled="synthesisStarting"
                      :loading="synthesisStarting"
                    >
                      ⚡ 继续合成
                    </a-button>
                    <a-button
                      size="small"
                      @click="$emit('restart-synthesis')"
                      :disabled="synthesisStarting"
                    >
                      🔄 重新合成
                    </a-button>
                  </template>

                  <!-- 失败状态：显示重试和重新合成按钮 -->
                  <template v-else-if="selectedChapterStatus === 'failed'">
                    <a-button
                      type="primary"
                      size="small"
                      @click="$emit('retry-synthesis')"
                      :disabled="synthesisStarting"
                      :loading="synthesisStarting"
                    >
                      🔄 重试
                    </a-button>
                    <a-button
                      size="small"
                      @click="$emit('restart-synthesis')"
                      :disabled="synthesisStarting"
                    >
                      🔄 重新合成
                    </a-button>
                  </template>
                </a-space>
              </div>
            </div>

            <!-- 段落剧本展示 -->
            <div class="dialogue-bubbles">
              <div
                v-for="(segment, segmentIndex) in chapterResult.synthesis_json?.synthesis_plan || []"
                :key="segmentIndex"
                class="dialogue-segment"
              >
                <DialogueBubble
                  :segment="segment"
                  :segment-index="segmentIndex"
                  :chapter-result="chapterResult"
                  @play-segment="$emit('play-segment', segment, segmentIndex)"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="empty-preview">
      <a-empty description="未找到智能准备结果" :image="Empty.PRESENTED_IMAGE_SIMPLE">
        <div class="empty-hint">
          <p v-if="!selectedChapter">{{ getStartHint() }}</p>
          <div v-else class="no-preparation-content">
            <p>当前章节尚未进行智能准备</p>
            <p class="chapter-info">
              选中章节: 第{{ getSelectedChapterInfo()?.chapter_number }}章
              {{ getSelectedChapterInfo()?.chapter_title || getSelectedChapterInfo()?.title }}
            </p>
            <a-space direction="vertical" style="margin-top: 16px">
              <a-button type="primary" @click="handleTriggerPreparation" :loading="contentLoading">
                🎭 开始智能准备
              </a-button>
              <a-button type="dashed" @click="handleRefreshPreparation" :loading="contentLoading">
                🔄 重新加载
              </a-button>
            </a-space>
            <p class="help-text">
              智能准备将自动分析章节内容，识别角色对话，生成语音合成配置。<br />
              这是使用AI技术的一键式准备功能，通常需要1-3分钟完成。
            </p>
          </div>
        </div>
      </a-empty>
    </div>
  </div>
</template>

<script setup>
  import { ref, computed, h, watch, onMounted } from 'vue'
  import { Empty, Modal, message } from 'ant-design-vue'
  import { DownOutlined } from '@ant-design/icons-vue'
  import { useRouter } from 'vue-router'
  import { getWebSocketUrl } from '@/config/services'
  import DialogueBubble from './DialogueBubble.vue'
  import apiClient, { llmAnalysisClient } from '@/api/config.js'
  import { getSegmentsStatus } from '@/api/synthesis.js'
  import { charactersAPI } from '@/api/index.js'

  const router = useRouter()

  const props = defineProps({
    project: Object,
    selectedChapter: [String, Number],
    chapterContent: String,
    contentLoading: Boolean,
    segments: Array,
    preparationResults: Object,
    availableChapters: Array,
    synthesisStarting: Boolean,
    synthesisRunning: Boolean,
    selectedChapterStatus: String,
    progressData: Object,
    chapterProgress: Object,
    canStart: Boolean
  })

  const emit = defineEmits([
    'play-segment',
    'refresh-preparation',
    'trigger-preparation',
    'trigger-preparation-loading',
    'start-chapter-synthesis',
    'play-chapter',
    'download-chapter',
    'start-synthesis',
    'pause-synthesis',
    'cancel-synthesis',
    'retry-synthesis',
    'play-audio',
    'download-audio',
    'restart-synthesis',
    'resume-synthesis',
    'reset-project-status'
  ])

  // 响应式数据
  const playingChapterAudio = ref(null)

  // 计算属性
  const getStartHint = () => {
    if (!props.project) {
      return '请先选择一个项目'
    }
    if (!props.selectedChapter) {
      return '请选择要处理的章节'
    }
    return '当前章节尚未进行智能准备'
  }

  // 🔥 修复：始终基于项目级别的音频文件数据判断章节状态
  const getChapterStatusText = (chapterId) => {
    if (!chapterId) return '未知'

    // 🔥 核心修复：始终基于项目级别的音频文件数据判断状态
    // 不再根据项目是否已开始来决定逻辑分支

    // 如果是当前选中的章节，使用已有的进度数据
    if (chapterId === props.selectedChapter && props.chapterProgress) {
      const chapterProgress = props.chapterProgress
      if (chapterProgress.total > 0 && chapterProgress.completed === chapterProgress.total) {
        return '已完成'
      } else if (chapterProgress.completed > 0) {
        return '部分完成'
      } else {
        return '待处理'
      }
    }

    // 对于其他章节，使用项目状态数据
    if (props.progressData && props.progressData.chapter_status) {
      const chapterStatus = props.progressData.chapter_status[chapterId]
      if (chapterStatus) {
        switch (chapterStatus.status) {
          case 'completed':
            return '已完成'
          case 'processing':
            return '处理中'
          case 'failed':
            return '失败'
          case 'pending':
            return '待处理'
          default:
            return '未知'
        }
      }
    }

    return '待处理'
  }

  const getChapterStatusColor = (chapterId) => {
    const statusText = getChapterStatusText(chapterId)
    switch (statusText) {
      case '已完成':
        return 'success'
      case '处理中':
        return 'processing'
      case '失败':
        return 'error'
      case '部分完成':
        return 'warning'
      default:
        return 'default'
    }
  }

  const getChapterCharacterCount = (chapterResult) => {
    if (!chapterResult?.synthesis_json?.synthesis_plan) return 0
    
    const characters = new Set()
    chapterResult.synthesis_json.synthesis_plan.forEach(segment => {
      if (segment.character && segment.character !== '旁白') {
        characters.add(segment.character)
      }
    })
    return characters.size
  }

  // 监听selectedChapter变化，自动刷新准备结果
  watch(
    () => props.selectedChapter,
    async (newChapterId, oldChapterId) => {
      if (newChapterId && newChapterId !== oldChapterId) {
        console.log('📋 章节切换，自动刷新准备结果:', newChapterId)
        // 这里可以触发父组件刷新准备结果
        emit('refresh-preparation')
      }
    },
    { immediate: true }
  )

  const handleTriggerPreparation = async () => {
    if (!props.selectedChapter) {
      message.warning('请先选择要智能准备的章节')
      return
    }

    // 显示确认对话框
    console.log('📋 显示智能准备确认对话框...')

    // 显示确认对话框
    console.log('📋 显示智能准备确认对话框...')
    Modal.confirm({
      title: '智能准备章节',
      content: h('div', [
        h('p', '即将开始智能准备以下章节：'),
        h(
          'p',
          { style: 'font-weight: 600; color: #1890ff; margin: 8px 0;' },
          `第${getSelectedChapterInfo()?.chapter_number}章 ${getSelectedChapterInfo()?.chapter_title || getSelectedChapterInfo()?.title}`
        ),
        h('br'),
        h('p', '智能准备将：'),
        h('ul', { style: 'margin: 8px 0; padding-left: 20px;' }, [
          h('li', '🎭 智能识别章节中的角色和对话'),
          h('li', '📝 自动分段并生成语音合成配置'),
          h('li', '🎨 为角色自动分配声音'),
          h('li', '📋 生成完整的合成计划')
        ]),
        h('br'),
        h('p', { style: 'color: #666; font-size: 13px;' }, '此操作可能需要1-3分钟，请耐心等待。'),
        h(
          'p',
          { style: 'color: #52c41a; font-size: 12px; margin-top: 8px;' },
          '🚀 使用快速模式，大幅减少处理时间'
        )
      ]),
      width: 500,
      okText: '开始智能准备',
      cancelText: '取消',
      onOk: async () => {
        console.log('✅ 用户确认开始智能准备')
        await executePreparation()
      },
      onCancel: () => {
        console.log('❌ 用户取消智能准备')
      }
    })
  }

  const executePreparation = async () => {
    try {
      console.log('🚀 开始加载书籍分析结果...')

      // 显示loading状态
      emit('trigger-preparation-loading', true)
      const hideLoading = message.loading('正在加载书籍分析结果...', 0)

      try {
        // 检查书籍分析结果是否存在
        const bookAnalysisResponse = await apiClient.get(
          `/books/${props.project.book_id}/analysis-results?chapter_ids=${props.selectedChapter}`
        )

        if (bookAnalysisResponse.data.success && bookAnalysisResponse.data.data?.length > 0) {
          // 书籍分析结果存在，直接加载
          hideLoading()
          
          Modal.success({
            title: '🎉 智能准备完成！',
            content: h('div', { style: 'text-align: left;' }, [
              h(
                'p',
                { style: 'font-weight: 600;' },
                `第${getSelectedChapterInfo()?.chapter_number}章 ${getSelectedChapterInfo()?.chapter_title || getSelectedChapterInfo()?.title}`
              ),
              h('br'),
              h(
                'div',
                { style: 'background: #f6f8fa; padding: 12px; border-radius: 6px; margin: 8px 0;' },
                [
                  h('p', { style: 'font-weight: 600; margin-bottom: 8px;' }, '📊 数据来源：'),
                  h('p', { style: 'margin: 4px 0; color: #52c41a;' }, '✅ 已从书籍分析结果加载'),
                  h('p', { style: 'margin: 4px 0; color: #666;' }, '📋 包含完整的角色对话和段落分析'),
                  h('p', { style: 'margin: 4px 0; color: #666;' }, '🎭 无需重新分析，直接使用已有结果')
                ]
              ),
              h('br'),
              h('p', { style: 'color: #52c41a; font-weight: 600;' }, '✅ 现在可以开始对话语音合成了！')
            ]),
            width: 500,
            okText: '开始合成',
            cancelText: '稍后合成',
            onOk: () => {
              console.log('✅ 用户选择立即开始合成')
            },
            onCancel: () => {
              console.log('📋 用户选择稍后合成')
              message.info('数据已加载，您现在可以开始合成了')
            }
          })

          message.success('智能准备完成，已加载书籍分析结果')
          
          // 通知父组件刷新数据
          emit('refresh-preparation')
        } else {
          // 书籍分析结果不存在，引导用户进行书籍分析
          hideLoading()
          
          Modal.warning({
            title: '⚠️ 需要先进行书籍分析',
            content: h('div', { style: 'text-align: left;' }, [
              h('p', { style: 'margin-bottom: 12px;' }, '当前章节尚未进行书籍分析，无法进行智能准备。'),
              h('p', { style: 'margin-bottom: 12px;' }, '请先进行书籍分析，然后才能进行智能准备。'),
              h('p', { style: 'color: #1890ff; font-weight: 600;' }, '书籍分析 → 智能准备 → 对话音合成')
            ]),
            width: 400,
            okText: '去书籍分析',
            cancelText: '取消',
            onOk: () => {
              // 跳转到书籍分析页面
              router.push(`/content-management/book-analysis/${props.project.book_id}`)
            }
          })
        }
      } catch (error) {
        hideLoading()
        console.error('❌ 加载书籍分析结果失败:', error)
        
        Modal.error({
          title: '❌ 加载失败',
          content: h('div', [
            h('p', { style: 'margin-bottom: 12px;' }, '加载书籍分析结果失败，请稍后重试。'),
            h('p', { style: 'color: #666; font-size: 13px;' }, '如果问题持续存在，请联系技术支持。')
          ]),
          width: 400,
          okText: '我知道了'
        })
        
        message.error('加载书籍分析结果失败')
      }
    } finally {
      emit('trigger-preparation-loading', false)
    }
  }

  const handleRefreshPreparation = () => {
    message.info('刷新智能准备结果')
    // 🔧 只刷新当前章节的准备结果，不影响其他章节
    if (props.selectedChapter) {
      emit('refresh-preparation')
    }
  }

  const getSelectedChapterInfo = () => {
    if (!props.selectedChapter || !props.availableChapters) return null
    return props.availableChapters.find(chapter => chapter.id === props.selectedChapter)
  }

  // 页面初始化
  onMounted(() => {
    console.log('📋 ContentPreview组件已挂载')
  })
</script>

<style scoped>
.content-preview {
  padding: 16px;
  background: #fff;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.preparation-preview {
  margin-bottom: 16px;
}

.dialogue-preview {
  background: #fafafa;
  border-radius: 8px;
  padding: 16px;
}

.dialogue-list {
  max-height: 600px;
  overflow-y: auto;
}

.chapter-divider {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding-bottom: 12px;
  border-bottom: 2px solid #e8e8e8;
}

.chapter-title-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.chapter-title {
  font-size: 18px;
  font-weight: 600;
  color: #1890ff;
}

.chapter-stats {
  display: flex;
  gap: 8px;
}

.chapter-actions {
  display: flex;
  gap: 8px;
  align-items: center;
}

.dialogue-bubbles {
  background: #fff;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.dialogue-segment {
  margin-bottom: 12px;
}

.dialogue-segment:last-child {
  margin-bottom: 0;
}

.empty-preview {
  text-align: center;
  padding: 40px 20px;
  background: #fafafa;
  border-radius: 8px;
}

.empty-hint {
  margin-top: 16px;
}

.chapter-info {
  color: #1890ff;
  font-weight: 600;
  margin: 8px 0;
}

.help-text {
  color: #666;
  font-size: 13px;
  margin-top: 16px;
  line-height: 1.5;
}

.no-preparation-content {
  text-align: center;
}

.no-preparation-content p {
  margin: 8px 0;
  color: #666;
}

/* 暗色主题支持 */
[data-theme='dark'] .content-preview {
  background: #1f1f1f;
  border-color: #2d2d2d;
}

[data-theme='dark'] .dialogue-preview {
  background: #2d2d2d;
}

[data-theme='dark'] .dialogue-bubbles {
  background: #1f1f1f;
}

[data-theme='dark'] .chapter-divider {
  border-bottom-color: #2d2d2d;
}

[data-theme='dark'] .chapter-title {
  color: #1890ff;
}

[data-theme='dark'] .empty-preview {
  background: #1f1f1f;
}

[data-theme='dark'] .chapter-info {
  color: #1890ff;
}

[data-theme='dark'] .help-text {
  color: #8c8c8c;
}

[data-theme='dark'] .no-preparation-content {
  color: #434343;
}

[data-theme='dark'] .no-preparation-content p {
  color: #434343;
}

[data-theme='dark'] .dialogue-list {
  background: #1f1f1f;
}

[data-theme='dark'] .dialogue-bubbles {
  background: transparent;
}

/* 移动端响应式设计 */
@media (max-width: 768px) {
  .content-preview {
    padding: 0 16px 16px 16px;
  }

  .chapter-divider {
    flex-direction: column;
    align-items: stretch;
    gap: 12px;
    margin: 0px 0 12px 0;
  }

  .chapter-title-section {
    align-items: center;
    text-align: center;
  }

  .chapter-actions {
    justify-content: center;
    flex-wrap: wrap;
  }

  .chapter-actions .ant-btn {
    font-size: 12px;
    padding: 4px 8px;
    height: 32px;
  }

  .dialogue-list {
    padding: 12px;
  }
}
</style>