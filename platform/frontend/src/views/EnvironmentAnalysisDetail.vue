<template>
  <div class="environment-analysis-detail">
    <!-- 项目头部 -->
    <EnvironmentProjectHeader
      :project="projectInfo"
      :loading="projectLoading"
      :stats="projectStats"
      @back="handleBack"
      @edit="handleEditProject"
      @delete="handleDeleteProject"
    />

    <!-- 主要内容区域 - 左右分栏布局 -->
    <div class="main-content">
        <a-row :gutter="8">
        <!-- 左侧：章节选择器 -->
        <a-col :span="chapterListCollapsed ? 1 : 4" class="chapter-list-col">
          <div class="left-panel">
            <ChapterSelector
              :chapters="chapters"
              :selected-chapter-id="selectedChapter?.id"
              :collapsed="chapterListCollapsed"
              @select-chapter="handleChapterSelect"
              @toggle-collapse="toggleChapterList"
            />
          </div>
        </a-col>

        <!-- 右侧：分析内容 -->
        <a-col :span="chapterListCollapsed ? 23 : 20">
          <div class="right-panel">
        <!-- 分析头部 -->
        <AnalysisHeader
          :selected-chapter="selectedChapter"
          :has-analysis="hasAnalysis"
          :has-tracks="environmentTracks.length > 0"
          :has-generated-tracks="hasGeneratedTracks"
          :analysis-loading="analysisLoading"
          :generation-loading="generationLoading"
          :mixing-loading="mixingLoading"
          :has-mixing-file="hasMixingFile"
          @start-analysis="startAnalysis"
          @generate-all-sounds="handleGenerateAllSounds"
          @mix-sounds="handleMixSounds"
          @play-mixing="handlePlayMixing"
          @download-mixing="handleDownloadMixing"
        />
        
        <!-- 分析内容 -->
        <AnalysisContent
          :selected-chapter="selectedChapter"
          :has-analysis="hasAnalysis"
          :environment-tracks="environmentTracks"
          :generation-loading="generationLoading"
          @generate-track="handleGenerateTrack"
          @play-track="handlePlayTrack"
          @download-track="handleDownloadTrack"
          @regenerate-track="handleRegenerateTrack"
        />
          </div>
        </a-col>
      </a-row>
    </div>
    
    <!-- 调试信息 -->
    <div style="display: none;">
      <p>Debug: selectedChapter = {{ selectedChapter?.id }}</p>
      <p>Debug: hasAnalysis = {{ hasAnalysis }}</p>
      <p>Debug: environmentTracks.length = {{ environmentTracks.length }}</p>
      <p>Debug: currentChapterAnalysis = {{ selectedChapter?.id ? (analysisResults[selectedChapter.id] ? '有数据' : '无数据') : '无章节' }}</p>
      <p>Debug: projectInfo.id = {{ projectInfo?.id }}</p>
      <p>Debug: projectInfo.status = {{ projectInfo?.status }}</p>
      <p>Debug: analysisResults.keys = {{ Object.keys(analysisResults).join(', ') }}</p>
    </div>

    <!-- 环境音生成进度条 -->
    <EnvironmentProgressBar
      :visible="generationLoading && !!currentTaskId"
      :progress="generationProgress"
      :status="generationStatus"
      :completed-tracks="completedTracks"
      :total-tracks="totalTracks"
      :tracks-progress="tracksProgress"
      :error-message="generationErrorMessage"
      @close="handleProgressClose"
      @cancel="handleProgressCancel"
      @pause="handleProgressPause"
      @retry="handleProgressRetry"
      @refresh="handleProgressRefresh"
    />
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed, onUnmounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message, Modal } from 'ant-design-vue'
// 移除未使用的图标导入
import ChapterSelector from '@/components/environment-sounds/ChapterSelector.vue'
import AnalysisHeader from '@/components/environment-sounds/AnalysisHeader.vue'
import AnalysisContent from '@/components/environment-sounds/AnalysisContent.vue'
import EnvironmentProjectHeader from '@/components/environment-sounds/EnvironmentProjectHeader.vue'
import EnvironmentProgressBar from '@/components/environment-sounds/EnvironmentProgressBar.vue'
import { environmentGenerationAPI } from '@/api'
import { chaptersAPI } from '@/api'
import { booksAPI } from '@/api'
import { playEnvironmentTrack, playEnvironmentMixing } from '@/utils/audioService'
import { useWebSocket } from '@/composables/useWebSocketSimple'

// 路由参数
const route = useRoute()
const router = useRouter()

// 项目信息
const projectInfo = ref(null)
const projectLoading = ref(false)

// 章节相关
const chapters = ref([])
const selectedChapter = ref(null)
const chaptersLoading = ref(false)
const chapterListCollapsed = ref(false)

// 分析相关
const analysisResults = ref({})
const analysisLoading = ref(false)
const generationLoading = ref(false)

// WebSocket相关
const { connect, disconnect } = useWebSocket()
const currentTaskId = ref(null)
const mixingLoading = ref(false)
const hasMixingFile = ref(false)

// 进度相关
const generationProgress = ref(0)
const generationStatus = ref('processing')
const completedTracks = ref(0)
const totalTracks = ref(0)
const tracksProgress = ref([])
const generationErrorMessage = ref('')

// 环境音轨道
const environmentTracks = ref([])

// 计算属性
const hasAnalysis = computed(() => {
  if (!selectedChapter.value) {
    console.log('❌ hasAnalysis: 没有选中章节')
    return false
  }
  
  const chapterId = selectedChapter.value.id
  const chapterAnalysis = analysisResults.value[chapterId]
  
  const result = chapterAnalysis && Object.keys(chapterAnalysis).length > 0 && environmentTracks.value.length > 0
  
  console.log('🔍 hasAnalysis计算:', {
    chapterId,
    chapterAnalysis: chapterAnalysis ? '有数据' : '无数据',
    analysisResultsKeys: Object.keys(analysisResults.value),
    environmentTracksLength: environmentTracks.value.length,
    result
  })
  
  return result
})

// 计算属性：是否有已生成的环境音轨道
const hasGeneratedTracks = computed(() => {
  if (!environmentTracks.value || environmentTracks.value.length === 0) {
    return false
  }
  
  // 检查是否有至少一个轨道已经生成
  return environmentTracks.value.some(track => 
    track.generated_file_path && track.generated_file_path.length > 0
  )
})

// 项目统计数据
const projectStats = computed(() => {
  const totalChapters = chapters.value.length
  const analyzedChapters = Object.keys(analysisResults.value).length
  const totalTracks = environmentTracks.value.length
  const generatedTracks = environmentTracks.value.filter(track => track.generated_file_path).length
  
  return {
    totalChapters,
    analyzedChapters,
    totalTracks,
    generatedTracks
  }
})

// WebSocket消息处理
const handleWebSocketMessage = (event) => {
  try {
    const data = JSON.parse(event.detail)
    
    if (data.type === 'environment_generation_progress' && data.data.task_id === currentTaskId.value) {
      const progressData = data.data
      
      console.log('📊 环境音生成进度更新:', progressData)
      
      if (progressData.status === 'completed') {
        // 单个轨道完成
        if (progressData.track_index !== undefined) {
          console.log(`🎵 轨道 ${progressData.track_index} 生成完成`)
          completedTracks.value++
          
          // 查找对应的轨道进度数据
          const trackProgress = tracksProgress.value.find(track => track.originalIndex === progressData.track_index)
          if (trackProgress) {
            trackProgress.status = 'completed'
            trackProgress.progress = 100
            console.log(`✅ 更新轨道进度: 轨道${progressData.track_index} -> 状态:completed`)
          } else {
            console.warn(`⚠️ 未找到轨道进度数据: 轨道${progressData.track_index}`)
          }
          
          // 更新进度百分比
          if (totalTracks.value > 0) {
            generationProgress.value = Math.round((completedTracks.value / totalTracks.value) * 100)
          }
          
          console.log('📊 进度更新:', {
            completedTracks: completedTracks.value,
            totalTracks: totalTracks.value,
            progress: generationProgress.value
          })
        } else {
          // 整体生成完成
          generationStatus.value = 'completed'
          generationProgress.value = 100
          message.success('🎵 环境音生成完成！')
          
          // 延迟重置状态，让用户看到完成状态
          setTimeout(() => {
            generationLoading.value = false
            currentTaskId.value = null
            generationProgress.value = 0
            generationStatus.value = 'processing'
            completedTracks.value = 0
            totalTracks.value = 0
            tracksProgress.value = []
            generationErrorMessage.value = ''
          }, 2000)
          
          // 刷新项目信息和分析结果
          loadProjectInfo()
        }
      } else if (progressData.status === 'failed') {
        // 生成失败
        generationStatus.value = 'failed'
        generationErrorMessage.value = progressData.error || '未知错误'
        message.error(`环境音生成失败: ${generationErrorMessage.value}`)
        
        // 延迟重置状态
        setTimeout(() => {
          generationLoading.value = false
          currentTaskId.value = null
          generationProgress.value = 0
          generationStatus.value = 'processing'
          completedTracks.value = 0
          totalTracks.value = 0
          tracksProgress.value = []
          generationErrorMessage.value = ''
        }, 3000)
      }
    }
  } catch (error) {
    console.error('处理WebSocket消息失败:', error)
  }
}

// 返回上一页
const handleBack = () => {
  router.push('/environment-analysis')
}

// 编辑项目
const handleEditProject = () => {
  message.info('编辑项目功能开发中...')
}

// 删除项目
const handleDeleteProject = () => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个环境音分析项目吗？此操作不可恢复。',
    onOk: () => {
      message.info('删除项目功能开发中...')
    }
  })
}

// 进度条相关处理函数
const handleProgressClose = () => {
  // 进度条关闭时的处理
}

const handleProgressCancel = () => {
  message.info('取消生成功能开发中...')
}

const handleProgressPause = () => {
  message.info('暂停生成功能开发中...')
}

const handleProgressRetry = () => {
  // 重新生成环境音
  handleGenerateAllSounds()
}

const handleProgressRefresh = () => {
  // 刷新页面数据
  loadProjectInfo()
}

// 页面初始化
onMounted(async () => {
  await loadProjectInfo()
  
  // 连接WebSocket
  await connect()
  
  // 监听WebSocket消息
  window.addEventListener('websocket_message', handleWebSocketMessage)
})

onUnmounted(() => {
  // 清理WebSocket监听
  window.removeEventListener('websocket_message', handleWebSocketMessage)
  disconnect()
})

// 监听路由变化
watch(() => route.params.analysisId, async (newId) => {
  if (newId && newId !== 'new-analysis') {
    await loadProjectInfo()
  }
})

// 加载项目信息
const loadProjectInfo = async () => {
  const analysisId = route.params.analysisId
  
  if (analysisId === 'new-analysis') {
    router.push('/environment-sounds')
    return
  }
  
  try {
    projectLoading.value = true
    console.log('🔍 开始加载项目信息:', analysisId)
    
    const response = await environmentGenerationAPI.getProjectDetail(analysisId)
    
    if (response.data.success) {
      projectInfo.value = response.data.data.project
      console.log('📋 项目信息加载成功:', {
        projectId: projectInfo.value.id,
        analysisResult: response.data.data.analysis_result ? '有数据' : '无数据'
      })
      
      // 检查并加载分析结果
      if (response.data.data.analysis_result && Object.keys(response.data.data.analysis_result).length > 0) {
        console.log('🔍 检查分析结果:', {
          analysisResult: response.data.data.analysis_result,
          chapterIds: projectInfo.value.chapter_ids,
          analysisResultKeys: Object.keys(response.data.data.analysis_result)
        })
        
        // 如果是多章节分析结果格式（字典格式，key是章节ID）
        if (typeof response.data.data.analysis_result === 'object' && 
            !Array.isArray(response.data.data.analysis_result) &&
            response.data.data.analysis_result.environment_tracks === undefined) {
          
          // 多章节格式，直接加载到analysisResults
          analysisResults.value = response.data.data.analysis_result
          console.log('💾 加载多章节分析结果:', Object.keys(analysisResults.value))
        }
        // 否则保持原有逻辑，等章节加载完成后再处理
      } else {
        console.log('⚠️ 没有找到分析结果')
      }
      
      // 加载项目关联的章节
      if (projectInfo.value.chapter_ids?.length > 0) {
        await loadChaptersByIds(projectInfo.value.chapter_ids)
      } else if (projectInfo.value.book_name && projectInfo.value.book_name !== '未知书籍') {
        await loadChaptersByBookName(projectInfo.value.book_name)
      } else if (projectInfo.value.book_id) {
        // 如果有book_id，通过book_id加载章节
        await loadChaptersByBookId(projectInfo.value.book_id)
      }
      
      // 检查是否有混音文件
      hasMixingFile.value = projectInfo.value.matching_result?.mixed_file_path ? true : false
      
      // 设置当前选中章节的环境轨道
      if (selectedChapter.value) {
        // 如果是旧格式的分析结果，分配给当前选中的章节
        if (response.data.data.analysis_result && 
            Object.keys(response.data.data.analysis_result).length > 0 &&
            response.data.data.analysis_result.environment_tracks !== undefined) {
          analysisResults.value[selectedChapter.value.id] = response.data.data.analysis_result
          console.log('💾 旧格式分析结果已分配给当前章节:', selectedChapter.value.id)
        }
        
        const chapterAnalysis = analysisResults.value[selectedChapter.value.id]
        if (chapterAnalysis && Object.keys(chapterAnalysis).length > 0) {
          environmentTracks.value = chapterAnalysis.environment_tracks || []
          console.log('🎯 设置当前章节环境轨道:', {
            chapterId: selectedChapter.value.id,
            tracksCount: environmentTracks.value.length
          })
        }
      }
    }
  } catch (error) {
    console.error('❌ 加载项目信息失败:', error)
    message.error('加载项目信息失败')
  } finally {
    projectLoading.value = false
  }
}

// 通过章节ID列表加载章节
const loadChaptersByIds = async (chapterIds) => {
  try {
    chaptersLoading.value = true
    const response = await chaptersAPI.getChapters({ chapter_ids: chapterIds })
    if (response.data.success) {
      chapters.value = response.data.data || []
      if (chapterIds.length > 0) {
        selectedChapter.value = chapters.value.find(ch => ch.id === chapterIds[0])
        // 设置当前选中章节的环境轨道
        if (selectedChapter.value) {
          const chapterAnalysis = analysisResults.value[selectedChapter.value.id]
          if (chapterAnalysis && Object.keys(chapterAnalysis).length > 0) {
            environmentTracks.value = chapterAnalysis.environment_tracks || []
          }
        }
      }
    }
  } catch (error) {
    console.error('通过章节ID加载章节失败:', error)
    message.error('加载章节失败: ' + error.message)
  } finally {
    chaptersLoading.value = false
  }
}

// 通过书籍名称加载章节
const loadChaptersByBookName = async (bookName) => {
  try {
    chaptersLoading.value = true
    console.log('📚 开始通过书籍名称加载章节:', bookName)
    
    const booksResponse = await booksAPI.getBooks({ search: bookName })
    if (booksResponse.data.success && booksResponse.data.data.length > 0) {
      const book = booksResponse.data.data[0]
      console.log('📖 找到书籍:', book)
      
      const response = await chaptersAPI.getChapters({ book_id: book.id })
      if (response.data.success) {
        chapters.value = response.data.data || []
        console.log('📑 章节加载成功:', {
          chaptersCount: chapters.value.length,
          chapters: chapters.value.map(ch => ({ id: ch.id, title: ch.chapter_title }))
        })
        
        if (chapters.value.length > 0) {
          selectedChapter.value = chapters.value[0]
          console.log('🎯 设置选中章节:', selectedChapter.value)
          
          // 设置当前选中章节的环境轨道
          if (selectedChapter.value) {
            const chapterAnalysis = analysisResults.value[selectedChapter.value.id]
            console.log('🔍 查找章节分析结果:', {
              chapterId: selectedChapter.value.id,
              analysisResults: analysisResults.value,
              chapterAnalysis: chapterAnalysis
            })
            
            if (chapterAnalysis && Object.keys(chapterAnalysis).length > 0) {
              environmentTracks.value = chapterAnalysis.environment_tracks || []
              console.log('✅ 设置环境轨道:', {
                tracksCount: environmentTracks.value.length,
                tracks: environmentTracks.value
              })
            } else {
              console.log('❌ 章节没有分析结果')
            }
          }
        }
      }
    }
  } catch (error) {
    console.error('通过书籍名称加载章节失败:', error)
    message.error('加载章节失败: ' + error.message)
  } finally {
    chaptersLoading.value = false
  }
}

// 通过书籍ID加载章节
const loadChaptersByBookId = async (bookId) => {
  try {
    chaptersLoading.value = true
    console.log('📚 开始通过书籍ID加载章节:', bookId)
    
    const response = await chaptersAPI.getChapters({ book_id: bookId })
    if (response.data.success) {
      chapters.value = response.data.data || []
      console.log('📑 章节加载成功:', {
        chaptersCount: chapters.value.length,
        chapters: chapters.value.map(ch => ({ id: ch.id, title: ch.chapter_title }))
      })
      
      if (chapters.value.length > 0) {
        selectedChapter.value = chapters.value[0]
        console.log('🎯 设置选中章节:', selectedChapter.value)
        
        // 设置当前选中章节的环境轨道
        if (selectedChapter.value) {
          const chapterAnalysis = analysisResults.value[selectedChapter.value.id]
          console.log('🔍 查找章节分析结果:', {
            chapterId: selectedChapter.value.id,
            analysisResults: analysisResults.value,
            chapterAnalysis: chapterAnalysis
          })
          
          if (chapterAnalysis && Object.keys(chapterAnalysis).length > 0) {
            environmentTracks.value = chapterAnalysis.environment_tracks || []
            console.log('✅ 设置环境轨道:', {
              tracksCount: environmentTracks.value.length,
              tracks: environmentTracks.value
            })
          } else {
            console.log('❌ 章节没有分析结果')
          }
        }
      }
    }
  } catch (error) {
    console.error('通过书籍ID加载章节失败:', error)
    message.error('加载章节失败: ' + error.message)
  } finally {
    chaptersLoading.value = false
  }
}

// 选择章节
const handleChapterSelect = (chapterId) => {
  selectedChapter.value = chapters.value.find(ch => ch.id === chapterId)
  
  // 加载当前章节的分析结果
  const chapterAnalysis = analysisResults.value[chapterId]
  if (chapterAnalysis && Object.keys(chapterAnalysis).length > 0) {
    environmentTracks.value = chapterAnalysis.environment_tracks || []
  } else {
    // 清空环境轨道，因为该章节没有分析结果
    environmentTracks.value = []
  }
}

// 开始分析
const startAnalysis = async () => {
  if (!selectedChapter.value) {
    message.warning('请先选择要分析的章节')
    return
  }

  try {
    analysisLoading.value = true
    message.info('开始分析章节内容...')
    


    // 总是使用章节分析API，只分析当前选中的章节
    console.log('📑 分析当前选中章节:', selectedChapter.value.id)
    
    const response = await environmentGenerationAPI.analyzeChapters({
      chapter_ids: [selectedChapter.value.id],
      analysis_options: {
        mode: 'auto',
        environment_types: ['nature', 'urban', 'indoor', 'action'],
        precision: 'medium',
        create_project: false  // 详情页面分析不创建项目
      }
    })
    
    if (response.data.success) {
      // 将分析结果保存到当前章节
      analysisResults.value[selectedChapter.value.id] = response.data.analysis_result
      environmentTracks.value = response.data.analysis_result?.environment_tracks || []
      
      console.log('✅ 章节分析完成，设置环境轨道:', {
        chapterId: selectedChapter.value.id,
        tracksCount: environmentTracks.value.length
      })
      
      // 保存分析结果到项目
      if (projectInfo.value) {
        try {
          // 构建完整的分析结果（保持多章节格式）
          const fullAnalysisResult = { ...analysisResults.value }
          
          // 调用书籍分析API来保存结果（但不重新分析）
          const saveResponse = await environmentGenerationAPI.analyzeBook({
            book_id: projectInfo.value.book_id,
            project_id: projectInfo.value.id,
            analysis_options: {
              mode: 'auto',
              environment_types: ['nature', 'urban', 'indoor', 'action'],
              precision: 'medium',
              skip_analysis: true,  // 跳过分析，只保存结果
              analysis_result: fullAnalysisResult  // 传递已有的分析结果
            }
          })
          
          if (saveResponse.data.success) {
            console.log('✅ 分析结果已保存到项目:', projectInfo.value.id)
            message.success('章节环境音分析完成')
          } else {
            console.error('保存分析结果失败:', saveResponse.data)
            message.warning('分析完成，但保存结果失败')
          }
        } catch (saveError) {
          console.error('保存分析结果失败:', saveError)
          message.warning('分析完成，但保存结果失败')
        }
      } else {
        console.warn('⚠️ 没有项目信息，无法保存分析结果')
        message.success('章节环境音分析完成')
      }
    }
  } catch (error) {
    console.error('分析失败:', error)
    message.error('分析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    analysisLoading.value = false
  }
}

// 切换章节列表折叠状态
const toggleChapterList = () => {
  chapterListCollapsed.value = !chapterListCollapsed.value
}



// 生成所有环境音
const handleGenerateAllSounds = async () => {
  try {
    generationLoading.value = true
    generationProgress.value = 0
    generationStatus.value = 'processing'
    completedTracks.value = 0
    
    // 获取所有章节的环境音轨道总数
    let allTracks = []
    for (const chapterId in analysisResults.value) {
      const chapterAnalysis = analysisResults.value[chapterId]
      if (chapterAnalysis && chapterAnalysis.environment_tracks) {
        allTracks = allTracks.concat(chapterAnalysis.environment_tracks)
      }
    }
    totalTracks.value = allTracks.length
    
    // 初始化轨道进度数据
    tracksProgress.value = allTracks.map((track, index) => ({
      index,
      originalIndex: index, // 保存原始索引用于映射
      keyword: track.environment_keywords?.[0] || track.scene_description || '未命名',
      description: track.scene_description || '',
      status: 'pending',
      progress: 0
    }))
    
    console.log('🎵 初始化进度数据:', {
      totalTracks: totalTracks.value,
      tracksProgress: tracksProgress.value.length
    })
    
    const response = await environmentGenerationAPI.generateEnvironmentSounds(
      projectInfo.value.id
    )
    
    if (response.data.success) {
      // 保存任务ID用于WebSocket监听
      currentTaskId.value = response.data.data.task_id
      message.success('环境音生成任务已启动')
      console.log('🎵 环境音生成任务已启动，任务ID:', currentTaskId.value)
    }
  } catch (error) {
    console.error('生成所有环境音失败:', error)
    
    // 提供更具体的错误信息
    if (error.response?.status === 404) {
      if (error.response?.data?.detail?.includes('未找到环境音分析结果')) {
        message.error('请先进行环境音分析，然后再生成环境音')
      } else {
        message.error('项目不存在或未找到相关数据')
      }
    } else if (error.response?.status === 400) {
      message.error('请求参数错误: ' + (error.response?.data?.detail || '参数格式不正确'))
    } else if (error.response?.status === 500) {
      message.error('服务器内部错误，请稍后重试')
    } else {
      message.error('生成所有环境音失败: ' + (error.response?.data?.detail || error.message))
    }
    
    // 重置进度状态
    generationProgress.value = 0
    generationStatus.value = 'processing'
    completedTracks.value = 0
    totalTracks.value = 0
  } finally {
    // 只有在成功启动任务时才不重置loading状态
    if (!currentTaskId.value) {
      generationLoading.value = false
    }
  }
}

// 混音环境音
const handleMixSounds = async () => {
  try {
    mixingLoading.value = true
    
    const response = await environmentGenerationAPI.mixEnvironmentSounds(
      projectInfo.value.id
    )
    
    if (response.data.success) {
      message.success('环境音混音任务已启动')
      // 刷新状态
      await loadProjectInfo()
    }
  } catch (error) {
    console.error('混音环境音失败:', error)
    message.error('混音环境音失败')
  } finally {
    mixingLoading.value = false
  }
}

// 播放混音
const handlePlayMixing = async () => {
  try {
    const projectTitle = `环境音混音 - ${projectInfo.value.name || projectInfo.value.id}`
    await playEnvironmentMixing(projectInfo.value.id, projectTitle)
    message.success('正在播放混音')
  } catch (error) {
    console.error('播放混音失败:', error)
    message.error('播放混音失败')
  }
}

// 下载混音
const handleDownloadMixing = async () => {
  try {
    const response = await environmentGenerationAPI.downloadMixedEnvironmentSounds(
      projectInfo.value.id
    )
    
    const blob = new Blob([response.data], { type: 'audio/wav' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `mixed_environment_${projectInfo.value.id}.wav`
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    message.success('混音下载完成')
  } catch (error) {
    console.error('下载混音失败:', error)
    message.error('下载混音失败')
  }
}

// 生成单个轨道
const handleGenerateTrack = async (track, trackIndex) => {
  try {
    track.generating = true
    
    const response = await environmentGenerationAPI.generateEnvironmentSounds(
      projectInfo.value.id,
      [trackIndex]
    )
    
    if (response.data.success) {
      message.success('轨道生成任务已启动')
      // 刷新状态
      await loadProjectInfo()
    }
  } catch (error) {
    console.error('生成轨道失败:', error)
    
    // 提供更具体的错误信息
    if (error.response?.status === 404) {
      if (error.response?.data?.detail?.includes('未找到环境音分析结果')) {
        message.error('请先进行环境音分析，然后再生成环境音')
      } else {
        message.error('项目不存在或未找到相关数据')
      }
    } else if (error.response?.status === 400) {
      message.error('请求参数错误: ' + (error.response?.data?.detail || '参数格式不正确'))
    } else if (error.response?.status === 500) {
      message.error('服务器内部错误，请稍后重试')
    } else {
      message.error('生成轨道失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    track.generating = false
  }
}

// 播放轨道
const handlePlayTrack = async (track, trackIndex) => {
  try {
    // 检查轨道是否已生成
    if (!track.generated_file_path) {
      message.warning('该轨道尚未生成，请先生成环境音')
      return
    }
    
    track.playing = true
    
    // 构建轨道标题
    const keywords = track.environment_keywords?.[0] || track.scene_description || '未命名'
    const trackTitle = `环境音轨道 ${trackIndex}: ${keywords}`
    
    console.log('🎵 播放环境音轨道:', {
      项目ID: projectInfo.value.id,
      轨道索引: trackIndex,
      轨道标题: trackTitle,
      文件路径: track.generated_file_path
    })
    
    // 使用统一的音频播放服务
    await playEnvironmentTrack(projectInfo.value.id, trackIndex, trackTitle)
    message.success(`🎵 播放: ${trackTitle}`)
  } catch (error) {
    console.error('播放轨道失败:', error)
    message.error('播放轨道失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    track.playing = false
  }
}

// 下载轨道
const handleDownloadTrack = async (track, trackIndex) => {
  try {
    const response = await environmentGenerationAPI.downloadEnvironmentSound(
      projectInfo.value.id,
      trackIndex
    )
    
    const keywords = track.environment_keywords?.[0] || '环境音'
    const filename = `${keywords}_${projectInfo.value.id}_${trackIndex}.wav`
    
    const blob = new Blob([response.data], { type: 'audio/wav' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = filename
    document.body.appendChild(a)
    a.click()
    document.body.removeChild(a)
    window.URL.revokeObjectURL(url)
    
    message.success('环境音下载完成')
  } catch (error) {
    console.error('下载轨道失败:', error)
    message.error('下载轨道失败')
  }
}

// 重新生成轨道
const handleRegenerateTrack = async (track, trackIndex) => {
  try {
    track.regenerating = true
    
    const response = await environmentGenerationAPI.generateEnvironmentSounds(
      projectInfo.value.id,
      [trackIndex]
    )
    
    if (response.data.success) {
      message.success('轨道重新生成任务已启动')
      // 刷新状态
      await loadProjectInfo()
    }
  } catch (error) {
    console.error('重新生成轨道失败:', error)
    
    // 提供更具体的错误信息
    if (error.response?.status === 404) {
      if (error.response?.data?.detail?.includes('未找到环境音分析结果')) {
        message.error('请先进行环境音分析，然后再生成环境音')
      } else {
        message.error('项目不存在或未找到相关数据')
      }
    } else if (error.response?.status === 400) {
      message.error('请求参数错误: ' + (error.response?.data?.detail || '参数格式不正确'))
    } else if (error.response?.status === 500) {
      message.error('服务器内部错误，请稍后重试')
    } else {
      message.error('重新生成轨道失败: ' + (error.response?.data?.detail || error.message))
    }
  } finally {
    track.regenerating = false
  }
}
</script>

<style scoped>
.environment-analysis-detail {
  min-height: 100vh;
}



/* 移动端适配 */
@media (max-width: 768px) {
  .mini-progress-content {
    flex-direction: column;
    gap: 8px;
    padding: 12px 16px;
  }

  .mini-progress-text {
    font-size: 12px;
  }

  .mini-progress-tip {
    font-size: 11px;
  }
}

.page-header {
  margin-bottom: 24px;
  padding: 32px;
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(82, 196, 26, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title-section {
  flex: 1;
}

.title-with-back {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
}

.back-button {
  margin-right: 12px;
  color: rgba(255, 255, 255, 0.85);
}

.back-button:hover {
  color: white;
}

.page-title {
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: white;
  display: flex;
  align-items: center;
}

.title-icon {
  margin-right: 12px;
  color: #ffffff;
}

.page-description {
  margin: 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  line-height: 1.5;
}

.main-content {
  margin-top: 16px;
  min-height: calc(100vh - 200px);
}

/* 全局样式调整 */
.main-content .ant-row {
  height: calc(100vh - 200px);
}

.main-content .ant-col {
  background-color: var(--ant-color-bg-container);
}

/* 章节列表收起展开样式 */
.chapter-list-col {
  transition: all 0.3s ease;
}

.left-panel {
  height: 100%;
  border-radius: 8px;
  box-shadow: 0 2px 8px var(--ant-box-shadow);
  border: 1px solid var(--ant-color-border);
  display: flex;
  flex-direction: column;
}

.right-panel {
  height: 100%;
  background-color: var(--ant-color-bg-container);
  border-radius: 8px;
  padding: 16px;
  box-shadow: 0 2px 8px var(--ant-box-shadow);
  border: 1px solid var(--ant-color-border-secondary);
  overflow-y: auto;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .environment-analysis-detail {
    padding: 16px;
  }
  
  .page-header {
    padding: 16px;
  }
  
  .header-content {
    flex-direction: column;
    gap: 16px;
  }
  
  .page-title {
    font-size: 20px;
  }

  .main-content {
    padding: 16px;
  }

  .main-content .ant-row {
    height: auto;
  }

  .main-content .ant-col {
    height: auto;
    margin-bottom: 16px;
  }

  .left-panel {
    padding: 12px;
  }

  .right-panel {
    padding: 12px;
  }
}

/* 暗黑模式适配 */
[data-theme='dark'] .page-header {
  background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

[data-theme='dark'] .left-panel {
  background-color: #1a1a1a !important;
  border-color: #434343 !important;
}

[data-theme='dark'] .right-panel {
  background-color: #262626 !important;
  border-color: #434343 !important;
}
</style>
