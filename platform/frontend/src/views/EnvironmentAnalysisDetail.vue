<template>
  <div class="environment-analysis-detail">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <div class="title-with-back">
            <a-button type="link" @click="$router.go(-1)" class="back-button">
              <ArrowLeftOutlined />
              返回
            </a-button>
            <h1 class="page-title">
              <BulbOutlined class="title-icon" />
              环境音分析详情
            </h1>
          </div>
          
        </div>
      </div>
    </div>

    <!-- 主要内容区域 - 左右分栏布局 -->
    <div class="main-content">
      <!-- 左侧：章节选择器 -->
      <div class="left-panel">
        <ChapterSelector
          :chapters="chapters"
          :selected-chapter-id="selectedChapter?.id"
          @select-chapter="handleChapterSelect"
        />
      </div>

      <!-- 右侧：分析内容 -->
      <div class="right-panel">
        <!-- 分析头部 -->
        <AnalysisHeader
          :selected-chapter="selectedChapter"
          :has-analysis="hasAnalysis"
          :has-tracks="environmentTracks.length > 0"
          :analysis-loading="analysisLoading"
          :generation-loading="generationLoading"
          @start-analysis="startAnalysis"
          @generate-sounds="handleGenerateSounds"
        />
        
        <!-- 分析内容 -->
        <AnalysisContent
          :selected-chapter="selectedChapter"
          :has-analysis="hasAnalysis"
          :environment-tracks="environmentTracks"
        />
      </div>
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
  </div>
</template>

<script setup>
import { ref, onMounted, watch, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { ArrowLeftOutlined, BulbOutlined } from '@ant-design/icons-vue'
import ChapterSelector from '@/components/environment-sounds/ChapterSelector.vue'
import AnalysisHeader from '@/components/environment-sounds/AnalysisHeader.vue'
import AnalysisContent from '@/components/environment-sounds/AnalysisContent.vue'
import { environmentGenerationAPI } from '@/api'
import { chaptersAPI } from '@/api'
import { booksAPI } from '@/api'

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

// 分析结果 - 改为按章节ID存储
const analysisResults = ref({}) // { chapterId: analysisResult }
const environmentTracks = ref([])
const analysisLoading = ref(false)
const generationLoading = ref(false)

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

// 页面初始化
onMounted(async () => {
  await loadProjectInfo()
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
    message.warning('请先选择章节')
    return
  }
  
  try {
    analysisLoading.value = true
    message.info('开始分析章节内容...')
    
    const response = await environmentGenerationAPI.analyzeChaptersEnvironment(
      [selectedChapter.value.id],
      {
        mode: 'auto',
        environment_types: ['nature', 'urban', 'indoor', 'action'],
        precision: 'medium',
        create_project: false  // 详情页面分析不创建项目
      }
    )
    
    if (response.data.success) {
      analysisResults.value[selectedChapter.value.id] = response.data.analysis_result
      environmentTracks.value = response.data.analysis_result?.environment_tracks || []
      
      // 保存分析结果到项目 - 修复：只要有项目信息就保存，不依赖response.data.project_id
      if (projectInfo.value) {
        try {
          const updateResponse = await fetch(`/api/v1/environment-generation/projects/${projectInfo.value.id}/analysis`, {
            method: 'PUT',
            headers: {
              'Content-Type': 'application/json',
            },
            body: JSON.stringify({
              analysis_result: analysisResults.value[selectedChapter.value.id],
              status: 'analyzed',
              chapter_id: selectedChapter.value.id
            })
          })
          
          if (updateResponse.ok) {
            const updateData = await updateResponse.json()
            
            // 更新本地项目信息
            if (updateData.success) {
              projectInfo.value.analysis_result = analysisResults.value[selectedChapter.value.id]
              projectInfo.value.status = 'analyzed'
              console.log('✅ 分析结果已保存到项目:', projectInfo.value.id)
            }
          } else {
            const errorText = await updateResponse.text()
            console.error('保存分析结果失败:', updateResponse.status, errorText)
            message.warning('分析完成，但保存结果失败')
          }
        } catch (saveError) {
          console.error('保存分析结果失败:', saveError)
          message.warning('分析完成，但保存结果失败')
        }
      } else {
        console.warn('⚠️ 没有项目信息，无法保存分析结果')
      }
      
      message.success('分析完成')
    }
  } catch (error) {
    console.error('分析失败:', error)
    message.error('分析失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    analysisLoading.value = false
  }
}

// 生成环境音
const handleGenerateSounds = async () => {
  const needGenerationTracks = environmentTracks.value.filter(track => !track.has_match)
  
  if (needGenerationTracks.length === 0) {
    message.info('所有环境音都已匹配，无需生成')
    return
  }
  
  try {
    generationLoading.value = true
    message.info(`开始生成 ${needGenerationTracks.length} 个环境音...`)
    
    const response = await environmentGenerationAPI.batchGenerateEnvironmentSounds({
      tracks: needGenerationTracks,
      options: {
        mode: 'auto',
        environment_types: ['nature', 'urban', 'indoor', 'action'],
        precision: 'medium'
      }
    })
    
    if (response.data.success) {
      message.success(`批量生成任务已启动，共 ${needGenerationTracks.length} 个环境音`)
    } else {
      message.error(response.data.message || '批量生成失败')
    }
  } catch (error) {
    console.error('批量生成失败:', error)
    message.error('批量生成失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    generationLoading.value = false
  }
}
</script>

<style scoped>
.environment-analysis-detail {
  min-height: 100vh;
}

.page-header {
  border-radius: 8px;
  padding: 24px;
  margin-bottom: 24px;
  box-shadow: 0 2px 8px var(--ant-box-shadow);
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
  color: var(--ant-text-color-secondary);
}

.page-title {
  margin: 0;
  font-size: 24px;
  font-weight: 600;
  color: var(--ant-text-color);
  display: flex;
  align-items: center;
}

.title-icon {
  margin-right: 8px;
  color: var(--ant-primary-color);
}

.page-description {
  margin: 0;
  color: var(--ant-text-color-secondary);
  font-size: 14px;
  line-height: 1.5;
}

.main-content {
  display: flex;
  gap: 24px;
  padding: 24px;
  min-height: calc(100vh - 200px);
}

.left-panel {
  flex: 0 0 300px;
  background-color: var(--ant-component-background);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px var(--ant-box-shadow);
}

.right-panel {
  flex: 1;
  background-color: var(--ant-component-background);
  border-radius: 8px;
  padding: 24px;
  box-shadow: 0 2px 8px var(--ant-box-shadow);
  min-height: 400px;
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
    flex-direction: column;
    gap: 16px;
    padding: 16px;
  }

  .left-panel {
    flex: none;
    padding: 16px;
  }

  .right-panel {
    padding: 16px;
  }
}
</style>
