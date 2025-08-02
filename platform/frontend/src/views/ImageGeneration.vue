<template>
  <div class="image-generation-container">
    <!-- 页面头部 -->
    <div class="header-section">
      <div class="page-title">
        <h1>🖼️ 图片生成</h1>
        <p>基于书籍智能准备结果生成配图</p>
      </div>
    </div>
    
    <!-- 主要内容标签页 -->
    <a-tabs v-model:activeKey="activeTab" class="main-tabs">
      <a-tab-pane key="generation" tab="图片生成">
        <!-- 章节选择 -->
    <a-card title="选择章节" class="section-card">
      <div class="chapter-selection">
        <a-row :gutter="16">
          <a-col :span="8">
            <a-select
              v-model:value="selectedBookId"
              placeholder="选择书籍"
              show-search
              :filter-option="false"
                             :loading="booksStore.loading"
              @search="searchBooks"
              @change="onBookChange"
              style="width: 100%"
            >
                             <a-select-option 
                 v-for="book in booksStore.books" 
                 :key="book.id" 
                 :value="book.id"
               >
                 {{ book.title }}
               </a-select-option>
            </a-select>
          </a-col>
          
          <a-col :span="8">
            <a-select
              v-model:value="selectedChapterId"
              placeholder="选择章节"
                             :disabled="!selectedBookId || booksStore.chaptersLoading"
               :loading="booksStore.chaptersLoading"
              @change="onChapterChange"
              style="width: 100%"
            >
                             <a-select-option 
                 v-for="chapter in booksStore.chapters" 
                 :key="chapter.id" 
                 :value="chapter.id"
               >
                 第{{ chapter.chapter_number }}章 {{ chapter.chapter_title }}
               </a-select-option>
            </a-select>
          </a-col>
          
          <a-col :span="8">
            <a-space>
              <a-button 
                type="primary" 
                :disabled="!selectedChapterId" 
                @click="createImageTasks"
                :loading="creatingTasks"
              >
                创建生成任务
              </a-button>
              
              <a-button 
                :disabled="!hasImageTasks" 
                @click="batchGenerate"
                :loading="batchGenerating"
              >
                批量生成
              </a-button>
              
              <a-button 
                icon="SettingOutlined"
                @click="showConfigDrawer"
              >
                配置
              </a-button>
            </a-space>
          </a-col>
        </a-row>
      </div>
    </a-card>
    
    <!-- 任务列表 -->
    <a-card 
      title="图片生成任务" 
      class="section-card" 
      v-if="selectedChapterId"
    >
      <template #extra>
        <a-space>
          <a-button 
            size="small" 
            @click="refreshTasks"
            :loading="loadingTasks"
          >
            刷新
          </a-button>
          
          <a-dropdown v-if="hasImageTasks">
            <a-button size="small">
              批量操作
              <DownOutlined />
            </a-button>
            <template #overlay>
              <a-menu @click="handleBatchAction">
                <a-menu-item key="delete">批量删除</a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </a-space>
      </template>
      
      <!-- 任务列表 -->
      <div v-if="!selectedChapterId" class="empty-state">
        <a-empty 
          description="请先选择书籍和章节"
          :image="'/static/images/empty-folder.svg'"
        >
          <template #description>
            <span style="color: #999;">
              请在上方选择要生成图片的书籍和章节
            </span>
          </template>
        </a-empty>
      </div>
      
      <ImageTaskList
        v-else
        :tasks="imageTasks"
        :loading="loadingTasks"
        @generate="generateSingleImage"
        @regenerate="regenerateImage"
        @rate="rateImage"
        @approve="approveImage"
        @delete="deleteImageTask"
        @view-details="viewTaskDetails"
      />
      
    </a-card>
    
    <!-- 生成统计 -->
    <a-card 
      title="生成统计" 
      class="section-card" 
      v-if="hasImageTasks"
    >
      <ImageGenerationStats :stats="generationStats" />
    </a-card>
    
    <!-- 统一抽屉 -->
    <a-drawer
      v-model:open="unifiedDrawerVisible"
      :title="drawerTitle"
      placement="right"
      width="600"
      @close="onDrawerClose"
    >
      <!-- 抽屉内容切换 -->
      <div class="drawer-tabs">
        <a-tabs v-model:activeKey="activeDrawerTab" @change="onDrawerTabChange">
          <a-tab-pane key="book-config" tab="书籍配置">
            <BookImageGenerationConfig
              :book-id="selectedBookId"
              v-model:config="bookGenerationConfig"
              :presets="presets"
              @preset-change="onPresetChange"
              @save="saveBookConfig"
            />
          </a-tab-pane>
          
          <a-tab-pane key="task-config" tab="任务配置">
            <TaskImageGenerationConfig
              :book-config="bookGenerationConfig"
              v-model:task-config="taskGenerationConfig"
              :available-characters="availableCharacters"
              :loading-characters="loadingCharacters"
              @character-select="onCharacterSelect"
              @search-characters="searchCharacters"
              @apply="applyTaskConfig"
            />
          </a-tab-pane>
          
          <a-tab-pane key="task-detail" tab="任务详情" v-if="selectedTask">
            <ImageTaskDetail
              :task="selectedTask"
              @update="refreshTasks"
              @close="closeTaskDetail"
            />
          </a-tab-pane>
        </a-tabs>
      </div>
    </a-drawer>
      </a-tab-pane>
      

    </a-tabs>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, onUnmounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { DownOutlined, SettingOutlined } from '@ant-design/icons-vue'

import BookImageGenerationConfig from '@/components/image-generation/BookImageGenerationConfig.vue'
import TaskImageGenerationConfig from '@/components/image-generation/TaskImageGenerationConfig.vue'
import CharacterConsistencyConfig from '@/components/image-generation/CharacterConsistencyConfig.vue'
import ImageTaskList from '@/components/image-generation/ImageTaskList.vue'
import ImageGenerationStats from '@/components/image-generation/ImageGenerationStats.vue'
import ImageTaskDetail from '@/components/image-generation/ImageTaskDetail.vue'


import { useImageGenerationStore } from '@/stores/imageGeneration'
import { useBookStore } from '@/stores/book'
import { bookAPI } from '@/api/v2.js'

// Stores
const imageStore = useImageGenerationStore()
const booksStore = useBookStore()

// 响应式数据
const activeTab = ref('generation') // 主标签页状态
const selectedBookId = ref(null)
const selectedChapterId = ref(null)
const creatingTasks = ref(false)
const batchGenerating = ref(false)
const loadingTasks = ref(false)
const unifiedDrawerVisible = ref(false) // 统一抽屉显示状态
const activeDrawerTab = ref('book-config') // 当前激活的抽屉标签页
const selectedTask = ref(null)

// 新增：图片任务和统计数据 - 直接使用store中的数据
// const imageTasks = ref([])  // 删除局部变量
// const generationStats = ref({})  // 删除局部变量

// 直接使用store中的响应式数据
const imageTasks = computed(() => {
  console.log('🔄 computed imageTasks 被触发，store.imageTasks:', imageStore.imageTasks)
  console.log('🔄 computed imageTasks length:', imageStore.imageTasks.length)
  return imageStore.imageTasks
})
const generationStats = computed(() => {
  console.log('📈 computed generationStats 被触发，store.generationStats:', imageStore.generationStats)
  return imageStore.generationStats
})

// 添加调试watch
watch(imageTasks, (newTasks, oldTasks) => {
  console.log('👀 imageTasks changed from:', oldTasks?.length, 'to:', newTasks?.length)
  console.log('👀 new imageTasks:', newTasks)
}, { immediate: true, deep: true })

// ComfyUI连接状态
const comfyuiConnected = ref(false)
const comfyuiAddress = ref('127.0.0.1:8188')

// 书籍级别配置
const bookGenerationConfig = reactive({
  style: 'cinematic', // 电影风格
  steps: 20,          // Flux推荐步数
  guidance: 2.5,      // Flux引导强度
  model: 'flux1-dev-kontext_fp8_scaled', // FluxKontext模型
  seed: null,         // 随机种子
  batchSize: 1        // 批次大小
})

// 任务级别配置
const taskGenerationConfig = reactive({
  characterConsistency: {
    enabled: false,
    selectedCharacterId: null,
    weight: 0.6,
    referenceImage: null
  },
  overrides: {} // 用于覆盖书籍配置的特定参数
})

// 预设配置
const presets = ref([
  {
    id: 1,
    name: 'FluxKontext 电影风格',
    description: '专业电影级画质，适合叙事场景',
    config: {
      style: 'cinematic',
      steps: 20,
      guidance: 2.5,
      model: 'flux1-dev-kontext_fp8_scaled'
    }
  },
  {
    id: 2,
    name: 'FluxKontext 古风写实',
    description: '古代历史场景，写实风格',
    config: {
      style: 'historical',
      steps: 25,
      guidance: 3.0,
      model: 'flux1-dev-kontext_fp8_scaled'
    }
  },
  {
    id: 3,
    name: 'FluxKontext 人物特写',
    description: '角色特写，情绪表达',
    config: {
      style: 'portrait',
      steps: 20,
      guidance: 2.0,
      model: 'flux1-dev-kontext_fp8_scaled'
    }
  }
])

const loadingCharacters = ref(false)
const availableCharacters = ref([])
const selectedCharacterInfo = ref(null)

// 计算属性
const hasImageTasks = computed(() => imageTasks.value.length > 0)

// 计算抽屉标题
const drawerTitle = computed(() => {
  if (activeDrawerTab.value === 'task-detail' && selectedTask.value) {
    return `任务详情 - 第${selectedTask.value.segment_index + 1}段`
  }
  if (activeDrawerTab.value === 'book-config') {
    return '书籍图片生成配置'
  }
  if (activeDrawerTab.value === 'task-config') {
    return '任务图片生成配置'
  }
  return '图片生成配置'
})

// 方法定义
const showConfigDrawer = () => {
  activeDrawerTab.value = 'book-config'
  unifiedDrawerVisible.value = true
}

const showTaskDetail = (task) => {
  selectedTask.value = task
  activeDrawerTab.value = 'task-detail'
  unifiedDrawerVisible.value = true
}

const closeTaskDetail = () => {
  selectedTask.value = null
  activeDrawerTab.value = 'book-config'
}

const onDrawerClose = () => {
  unifiedDrawerVisible.value = false
  if (activeDrawerTab.value === 'task-detail') {
    closeTaskDetail()
  }
}

const onDrawerTabChange = (key) => {
  activeDrawerTab.value = key
}

const onConfigDrawerClose = () => {
  unifiedDrawerVisible.value = false
}

// 保存书籍级别配置
const saveBookConfig = async () => {
  if (!selectedBookId.value) {
    message.error('请先选择书籍')
    return
  }
  
  try {
    await bookAPI.updateBookImageGenerationConfig(selectedBookId.value, bookGenerationConfig)
    message.success('书籍配置已保存')
  } catch (error) {
    console.error('保存书籍配置失败:', error)
    message.error('保存书籍配置失败: ' + error.message)
  }
}

// 应用任务配置
const applyTaskConfig = () => {
  message.success('任务配置已应用')
  activeDrawerTab.value = 'book-config'
}

const onPresetChange = (preset) => {
  if (preset && preset.config) {
    Object.assign(bookGenerationConfig, preset.config)
    message.success(`已应用预设: ${preset.name}`)
  }
}

// Methods
const searchBooks = async (searchText) => {
  if (!searchText) {
    await loadBooks()
    return
  }
  
  try {
    await booksStore.fetchBooks({ search: searchText })
  } catch (error) {
    message.error('搜索书籍失败: ' + error.message)
  }
}

const loadBooks = async () => {
  try {
    console.log('开始加载已发布的书籍列表...')
    // 只获取已发布状态的书籍
    const result = await booksStore.fetchBooks({ status: 'published' })
    console.log('fetchBooks 结果:', result)
    console.log('booksStore.books:', booksStore.books)
  } catch (error) {
    console.error('加载书籍失败:', error)
    message.error('加载书籍列表失败: ' + error.message)
  }
}

const onBookChange = async (bookId) => {
  selectedChapterId.value = null
  // imageTasks.value = [] // 删除局部变量赋值
  
  if (!bookId) {
    // 清空角色数据
    availableCharacters.value = []
    return
  }
  
  try {
    await booksStore.fetchChapters(bookId)
    // 加载书籍的图片生成配置
    await loadBookConfig(bookId)
    // 自动加载该书籍的角色数据
    await loadCharacters(bookId)
  } catch (error) {
    message.error('加载章节列表失败: ' + error.message)
  }
}

// 加载书籍级别配置
const loadBookConfig = async (bookId) => {
  try {
    const config = await bookAPI.getBookImageGenerationConfig(bookId)
    if (config) {
      Object.assign(bookGenerationConfig, config)
      console.log('已加载书籍配置:', config)
    }
  } catch (error) {
    console.error('加载书籍配置失败:', error)
    // 使用默认配置，不显示错误消息
  }
}

const onChapterChange = async (chapterId) => {
  if (!chapterId) return
  
  console.log('📂 章节切换到:', chapterId)
  clearStatusRefresh() // 清理之前的定时器
  await loadImageTasks(chapterId)  // 这一次调用就足够了，会同时更新tasks和stats
  // await loadGenerationStats(chapterId)  // 删除重复调用
  // 移除这里的startStatusRefresh，让loadImageTasks来决定是否启动
  
  // 重新加载角色数据（不按章节筛选，因为角色数据的chapter_id通常为null）
  if (selectedBookId.value) {
    await loadCharacters(selectedBookId.value) // 移除chapterId参数，加载该书籍的所有角色
  }
}

const loadImageTasks = async (chapterId) => {
  loadingTasks.value = true
  try {
    console.log('🔄 开始加载章节任务，章节ID:', chapterId)
    const response = await imageStore.getChapterImageStatus(chapterId)
    console.log('📡 API响应:', response)
    
    // 验证store中的数据状态
    console.log('📊 store.imageTasks:', imageStore.imageTasks)
    console.log('📊 store.imageTasks length:', imageStore.imageTasks.length)
    console.log('📊 computed imageTasks.value:', imageTasks.value)
    console.log('📊 computed imageTasks.value length:', imageTasks.value.length)
    
    console.log('📊 加载图片任务成功:', imageTasks.value.length, '个任务')
    console.log('📈 任务状态统计:', generationStats.value.status_breakdown)
    
    // 动态控制自动刷新：只有processing任务时才启用
    const hasProcessingTasks = imageTasks.value.some(task => task.status === 'processing')
    if (hasProcessingTasks) {
      startStatusRefresh(chapterId)
      console.log('🔄 检测到处理中任务，启动自动刷新')
    } else {
      clearStatusRefresh()
      console.log('✅ 无处理中任务，停止自动刷新')
    }
    
  } catch (error) {
    console.error('❌ 加载任务失败:', error)
    message.error('加载图片生成任务失败: ' + error.message)
  } finally {
    loadingTasks.value = false
  }
}

const loadGenerationStats = async (chapterId) => {
  // 不再需要单独调用API，因为loadImageTasks已经更新了store中的所有数据
  console.log('📈 统计数据已从store获取:', generationStats.value)
}

// 优化的状态自动刷新机制
let refreshTimer = null

const startStatusRefresh = (chapterId) => {
  clearStatusRefresh()
  refreshTimer = setInterval(async () => {
    if (selectedChapterId.value === chapterId) {
      try {
        console.log('🔄 执行自动刷新...')
        await imageStore.getChapterImageStatus(chapterId)  // store会自动更新数据
        
        // 检查是否还有processing任务
        const hasProcessingTasks = imageTasks.value.some(task => task.status === 'processing')
        if (!hasProcessingTasks) {
          clearStatusRefresh()
          console.log('✅ 所有任务已完成，停止自动刷新')
        }
        
        console.log('🔄 自动刷新完成，处理中任务:', hasProcessingTasks)
      } catch (error) {
        console.error('自动刷新失败:', error)
      }
    } else {
      clearStatusRefresh()
      console.log('📌 章节已切换，停止自动刷新')
    }
  }, 5000) // 改为5秒刷新一次，减少频率
}

const clearStatusRefresh = () => {
  if (refreshTimer) {
    clearInterval(refreshTimer)
    refreshTimer = null
    console.log('🛑 已停止自动刷新')
  }
}

const createImageTasks = async () => {
  if (!selectedChapterId.value) return
  
  creatingTasks.value = true
  try {
    // 合并书籍配置和任务配置
    const generationConfig = {
      ...bookGenerationConfig,
      character_consistency: taskGenerationConfig.characterConsistency,
      ...taskGenerationConfig.overrides
    }
    
    const response = await imageStore.createImageTasks({
      chapter_id: selectedChapterId.value,
      generation_config: generationConfig
    })
    
    message.success(`成功创建 ${response.data?.data?.total_tasks || 0} 个生成任务`)
    await loadImageTasks(selectedChapterId.value)
  } catch (error) {
    message.error('创建生成任务失败: ' + error.message)
  } finally {
    creatingTasks.value = false
  }
}

const batchGenerate = async () => {
  if (!selectedChapterId.value) return
  
  Modal.confirm({
    title: '确认批量生成',
    content: '这将开始为当前章节的所有待处理任务生成图片，可能需要较长时间，确认继续？',
    onOk: async () => {
      batchGenerating.value = true
      try {
        await imageStore.batchGenerateImages({
          chapter_id: selectedChapterId.value
        })
        
        message.success('批量生成已开始，请等待完成')
        
        // 定期刷新任务状态
        const refreshInterval = setInterval(async () => {
          await loadImageTasks(selectedChapterId.value)
          
          // 检查是否所有任务都已完成
          const pendingTasks = imageTasks.value.filter(t => t.status === 'pending' || t.status === 'processing')
          if (pendingTasks.length === 0) {
            clearInterval(refreshInterval)
            batchGenerating.value = false
            message.success('批量生成完成')
          }
        }, 5000)
        
        // 10分钟后停止刷新
        setTimeout(() => {
          clearInterval(refreshInterval)
          batchGenerating.value = false
        }, 600000)
        
      } catch (error) {
        message.error('启动批量生成失败: ' + error.message)
        batchGenerating.value = false
      }
    }
  })
}

const generateSingleImage = async (taskId) => {
  // 找到对应的任务
  const task = imageTasks.value.find(t => t.id === taskId)
  if (task) {
    // 打开详情抽屉
    viewTaskDetails(task)
  } else {
    message.error('未找到对应的任务')
  }
}

const regenerateImage = async (taskId) => {
  try {
    await imageStore.regenerateImage(taskId)
    message.success('重新生成请求已提交')
    await loadImageTasks(selectedChapterId.value)
  } catch (error) {
    message.error('重新生成失败: ' + error.message)
  }
}

const rateImage = async (taskId, rating) => {
  try {
    await imageStore.rateImageTask(taskId, rating)
    message.success('评分成功')
    await loadImageTasks(selectedChapterId.value)
  } catch (error) {
    message.error('评分失败: ' + error.message)
  }
}

const approveImage = async (taskId, approved) => {
  try {
    await imageStore.approveImageTask(taskId, approved)
    message.success(approved ? '审核通过' : '审核拒绝')
    await loadImageTasks(selectedChapterId.value)
  } catch (error) {
    message.error('审核失败: ' + error.message)
  }
}

const deleteImageTask = async (taskId) => {
  Modal.confirm({
    title: '确认删除',
    content: '确定要删除这个图片生成任务吗？此操作不可恢复。',
    onOk: async () => {
      try {
        await imageStore.deleteImageTask(taskId)
        message.success('删除成功')
        await loadImageTasks(selectedChapterId.value)
      } catch (error) {
        message.error('删除失败: ' + error.message)
      }
    }
  })
}

const viewTaskDetails = (task) => {
  showTaskDetail(task)
}

const refreshTasks = () => {
  if (selectedChapterId.value) {
    loadImageTasks(selectedChapterId.value)
  }
}

const handleBatchAction = async ({ key }) => {
  const selectedTasks = imageTasks.value.filter(t => t.selected)
  if (selectedTasks.length === 0) {
    message.warning('请先选择要操作的任务')
    return
  }
  
  const taskIds = selectedTasks.map(t => t.id)
  
  if (key === 'delete') {
    Modal.confirm({
      title: '确认批量删除',
      content: `确定要删除选中的 ${selectedTasks.length} 个任务吗？此操作不可恢复。`,
      onOk: async () => {
        try {
          // 逐个删除任务
          for (const taskId of taskIds) {
            await imageStore.deleteImageTask(taskId)
          }
          message.success(`成功删除 ${selectedTasks.length} 个任务`)
          await loadImageTasks(selectedChapterId.value)
        } catch (error) {
          message.error('批量删除失败: ' + error.message)
        }
      }
    })
  }
}

const testComfyuiConnection = async () => {
  try {
    const response = await imageStore.testComfyuiConnection()
    comfyuiConnected.value = response.data?.success || false
    
    if (comfyuiConnected.value) {
      message.success('ComfyUI连接成功')
    } else {
      message.warning('ComfyUI连接失败')
    }
  } catch (error) {
    message.error('测试连接失败: ' + error.message)
    comfyuiConnected.value = false
  }
}

// 角色一致性相关方法
// 加载角色数据
const loadCharacters = async (bookId, chapterId = null) => {
  if (!bookId) {
    availableCharacters.value = []
    return
  }
  
  loadingCharacters.value = true
  try {
    // 构建搜索参数
    const searchParams = { 
      book_id: bookId
    }
    
    // 如果指定了章节，则按章节筛选角色
    if (chapterId) {
      searchParams.chapter_id = chapterId
    }
    
    const response = await imageStore.searchCharacters(searchParams)
    availableCharacters.value = response.data?.data || []
    console.log('已加载角色数据:', availableCharacters.value.length, '个角色')
  } catch (error) {
    console.error('加载角色失败:', error)
    message.error('加载角色失败: ' + error.message)
    availableCharacters.value = []
  } finally {
    loadingCharacters.value = false
  }
}

const searchCharacters = async (searchText) => {
  if (!searchText) {
    // 如果没有搜索文本，重新加载所有角色
    if (selectedBookId.value) {
      await loadCharacters(selectedBookId.value, selectedChapterId.value)
    }
    return
  }
  
  // 检查是否选择了书籍
  if (!selectedBookId.value) {
    message.warning('请先选择书籍')
    return
  }
  
  loadingCharacters.value = true
  try {
    // 构建搜索参数
    const searchParams = { 
      search: searchText,
      book_id: selectedBookId.value
    }
    
    // 如果选择了章节，则按章节筛选角色
    if (selectedChapterId.value) {
      searchParams.chapter_id = selectedChapterId.value
    }
    
    const response = await imageStore.searchCharacters(searchParams)
    availableCharacters.value = response.data?.data || []
  } catch (error) {
    message.error('搜索角色失败: ' + error.message)
  } finally {
    loadingCharacters.value = false
  }
}

const onCharacterSelect = (characterId) => {
  const character = availableCharacters.value.find(c => c.id === characterId)
  if (character) {
    selectedCharacterInfo.value = character
    taskGenerationConfig.characterConsistency.selectedCharacterId = characterId
    taskGenerationConfig.characterConsistency.enabled = true
    
    // 如果有角色头像，设置为参考图片
    if (character.avatar_url) {
      taskGenerationConfig.characterConsistency.referenceImage = character.avatar_url
      console.log('设置参考图片:', character.avatar_url)
    }
  } else {
    selectedCharacterInfo.value = null
    taskGenerationConfig.characterConsistency.selectedCharacterId = null
    taskGenerationConfig.characterConsistency.enabled = false
    taskGenerationConfig.characterConsistency.referenceImage = null
  }
}

const onCharacterConsistencyToggle = (checked) => {
  taskGenerationConfig.characterConsistency.enabled = checked
  if (!checked) {
    selectedCharacterInfo.value = null
    taskGenerationConfig.characterConsistency.selectedCharacterId = null
    taskGenerationConfig.characterConsistency.referenceImage = null
  }
}

// Lifecycle
onMounted(async () => {
  console.log('🎬 图片生成页面已加载')
  await loadBooks()
  
  // 检查是否有默认选择
  if (selectedBookId.value) {
    console.log('📚 已选择书籍:', selectedBookId.value)
    await booksStore.fetchChapters(selectedBookId.value)
    await loadBookConfig(selectedBookId.value)
  }
  
  if (selectedChapterId.value) {
    console.log('📖 已选择章节:', selectedChapterId.value)
    await loadImageTasks(selectedChapterId.value)
  } else {
    console.log('⚠️ 请先选择书籍和章节')
  }
})

// Watch for chapter changes - 移除，避免与onChapterChange重复
// watch(selectedChapterId, (newValue) => {
//   if (newValue) {
//     loadImageTasks(newValue)
//   }
// })

// 组件卸载时清理定时器
onUnmounted(() => {
  clearStatusRefresh()
})
</script>

<style scoped>
.image-generation-container {
  background: #f8fafc;
  min-height: 100vh;
}

.header-section {
  margin-bottom: 24px;
  padding: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.page-title {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title h1 {
  margin: 0;
  font-size: 28px;
  color: white;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.page-title p {
  margin: 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  line-height: 1.5;
}

.connection-status {
  margin-top: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.section-card {
  margin-bottom: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
  border: none;
  transition: all 0.3s;
}

.section-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 10px 25px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05);
}

.section-card .ant-card-head {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 24px;
}

.section-card .ant-card-body {
  padding: 24px;
}

.chapter-selection {
  margin-bottom: 16px;
  padding: 16px;
  background: white;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.empty-state {
  padding: 40px 0;
  text-align: center;
}

.empty-state .ant-empty-description {
  color: #999;
  font-size: 16px;
}

.character-consistency-section .ant-form-item {
  margin-bottom: 24px;
}

.character-option {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px;
  border-radius: 4px;
  cursor: pointer;
  transition: background-color 0.2s ease;
  width: 100%;
}

.character-option:hover {
  background-color: #f0f0f0;
}

.character-option.selected {
  background-color: #e6f7ff;
  border: 1px solid #1890ff;
}

.character-avatar-mini {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  object-fit: cover;
}

.character-avatar-placeholder {
  width: 30px;
  height: 30px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 14px;
  font-weight: bold;
}

.character-name {
  font-size: 14px;
  font-weight: 500;
  color: #333;
  flex-grow: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.character-info-preview {
  margin-top: 10px;
  padding: 12px;
  background: #f5f5f5;
  border-radius: 6px;
  border: 1px solid #eee;
}

.character-info-item {
  display: flex;
  margin-bottom: 8px;
  align-items: flex-start;
  line-height: 1.5;
}

.character-info-item:last-child {
  margin-bottom: 0;
}

.info-label {
  font-weight: 600;
  color: #333;
  font-size: 13px;
  min-width: 80px;
  flex-shrink: 0;
}

.info-content {
  color: #555;
  font-size: 13px;
  flex: 1;
  word-break: break-word;
}

.form-hint {
  margin-top: 4px;
  font-size: 12px;
  color: #999;
}

@media (max-width: 768px) {
  .image-generation-container {
    padding: 10px;
  }
  
  .header-section {
    padding: 20px;
  }
  
  .chapter-selection .ant-col {
    margin-bottom: 12px;
  }
}

/* 统一抽屉样式 */
.drawer-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.drawer-tabs .ant-tabs {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.drawer-tabs .ant-tabs-content-holder {
  flex: 1;
  overflow-y: auto;
}

.drawer-tabs .ant-tabs-tabpane {
  height: 100%;
  padding: 0;
}

.drawer-tabs .ant-tabs-tab {
  padding: 12px 16px;
  font-weight: 500;
}

.drawer-tabs .ant-tabs-tab.ant-tabs-tab-active {
  background: #f0f7ff;
  border-radius: 6px 6px 0 0;
}

/* 暗黑模式适配 */
[data-theme='dark'] .image-generation-container {
  background: #141414 !important;
}

[data-theme='dark'] .header-section {
  background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

[data-theme='dark'] .connection-status,
[data-theme='dark'] .section-card,
[data-theme='dark'] .chapter-selection {
  background: #1f1f1f !important;
  border: 1px solid #434343 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

[data-theme='dark'] .drawer-tabs .ant-tabs-tab.ant-tabs-tab-active {
  background: #1f1f1f !important;
  color: #1890ff !important;
}

[data-theme='dark'] .character-info-preview {
  background: #262626 !important;
  border: 1px solid #434343 !important;
}

[data-theme='dark'] .info-label {
  color: #fff !important;
}

[data-theme='dark'] .info-content {
  color: #d9d9d9 !important;
}

[data-theme='dark'] .character-option:hover {
  background-color: #262626 !important;
}

[data-theme='dark'] .character-option.selected {
  background-color: #111b26 !important;
  border: 1px solid #1890ff !important;
}

[data-theme='dark'] .character-name {
  color: #fff !important;
}

/* 主标签页样式 */
.main-tabs {
  margin-top: 20px;
}

.main-tabs .ant-tabs-content-holder {
  padding: 20px 0;
}

.main-tabs .ant-tabs-tab {
  font-size: 16px;
  font-weight: 500;
}

.main-tabs .ant-tabs-tab-active {
  color: #1890ff;
}

/* 图片库标签页内容样式 */
.main-tabs .ant-tabs-tabpane[data-node-key="library"] {
  padding: 0;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .image-generation-container {
  }
  
  .header-section {
    padding: 24px;
  }
  
  .main-tabs .ant-tabs-tab {
    font-size: 14px;
    padding: 8px 16px;
  }
  
  .chapter-selection .ant-row {
    flex-direction: column;
  }
  
  .chapter-selection .ant-col {
    margin-bottom: 16px;
  }
}

/* 暗黑模式适配 */
[data-theme='dark'] .image-generation-container {
  background: #141414 !important;
}

[data-theme='dark'] .header-section {
  background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
}

[data-theme='dark'] .section-card,
[data-theme='dark'] .connection-status {
  background: #1f1f1f !important;
  border: 1px solid #434343 !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3) !important;
}

[data-theme='dark'] .section-card .ant-card-head {
  border-bottom: 1px solid #434343 !important;
  background: #1f1f1f !important;
}

[data-theme='dark'] .section-card .ant-card-body {
  background: #1f1f1f !important;
}

[data-theme='dark'] .chapter-selection {
  background: #1f1f1f !important;
}
</style>