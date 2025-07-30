<template>
  <div class="image-generation-container">
    <!-- 页面头部 -->
    <div class="header-section">
      <div class="page-title">
        <h1>🖼️ 图片生成</h1>
        <p>基于书籍智能准备结果生成配图</p>
      </div>
      
    </div>
    
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
        @rate="rateImage"
        @approve="approveImage"
        @delete="deleteImageTask"
        @view-details="viewTaskDetails"
      />
      
      <!-- 调试信息显示 -->
      <div v-if="imageTasks.length === 0 && !loadingTasks" style="padding: 20px; border: 1px dashed #ccc; margin: 10px 0;">
        <h4>🔍 调试信息：</h4>
        <p><strong>selectedChapterId:</strong> {{ selectedChapterId }}</p>
        <p><strong>imageTasks.length:</strong> {{ imageTasks.length }}</p>
        <p><strong>loadingTasks:</strong> {{ loadingTasks }}</p>
        <p><strong>store.imageTasks.length:</strong> {{ imageStore.imageTasks.length }}</p>
        <p><strong>generationStats:</strong> {{ JSON.stringify(generationStats, null, 2) }}</p>
        <button @click="loadImageTasks(selectedChapterId)" :disabled="!selectedChapterId">
          🔄 手动重新加载
        </button>
      </div>
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
          <a-tab-pane key="config" tab="生成配置">
            <!-- 🔥 新增：角色一致性配置 -->
            <div class="character-consistency-section" style="margin-bottom: 24px;">
              <a-divider orientation="left">角色一致性设置</a-divider>
              
              <a-form layout="vertical">
                <a-form-item label="启用角色一致性">
                  <a-switch 
                    v-model:checked="characterConsistency.enabled"
                    checkedChildren="开"
                    unCheckedChildren="关"
                    @change="onCharacterConsistencyToggle"
                  />
                  <div class="form-hint">
                    <small>开启后，生成的图片将保持角色外貌一致性</small>
                  </div>
                </a-form-item>
                
                <template v-if="characterConsistency.enabled">
                  <a-form-item label="选择角色">
                    <a-select
                      v-model:value="characterConsistency.selectedCharacterId"
                      placeholder="选择要保持一致性的角色"
                      style="width: 100%"
                      :loading="loadingCharacters"
                      show-search
                      :filter-option="false"
                      @search="searchCharacters"
                      @change="onCharacterSelect"
              >
                <a-select-option 
                  v-for="character in availableCharacters" 
                  :key="character.id" 
                  :value="character.id"
                >
                  <div class="character-option">
                    <img 
                      v-if="character.avatar_url" 
                      :src="character.avatar_url" 
                      class="character-avatar-mini"
                      alt="头像"
                    />
                    <div 
                      v-else 
                      class="character-avatar-placeholder"
                      :style="{ background: character.color }"
                    >
                      {{ character.name[0] }}
                    </div>
                    <span class="character-name">{{ character.name }}</span>
                    <a-tag v-if="character.consistency_tag" size="small" color="blue">
                      {{ character.consistency_tag }}
                    </a-tag>
                  </div>
                </a-select-option>
              </a-select>
            </a-form-item>
            
            <a-form-item label="一致性权重" v-if="characterConsistency.selectedCharacterId">
              <a-slider
                v-model:value="characterConsistency.weight"
                :min="0.3"
                :max="1.0"
                :step="0.1"
                :marks="{ 0.3: '弱', 0.6: '中', 0.9: '强' }"
              />
              <div class="form-hint">
                <small>权重越高，角色特征越明显</small>
              </div>
            </a-form-item>
            
            <a-form-item label="角色提示词预览" v-if="selectedCharacterInfo">
              <a-textarea 
                :value="selectedCharacterInfo.avatar_prompt"
                :rows="3"
                disabled
                style="background: #f5f5f5;"
              />
              <div class="character-info-preview">
                <p><strong>外貌描述：</strong>{{ selectedCharacterInfo.appearance_description || '暂无' }}</p>
                <p><strong>特殊特征：</strong>{{ selectedCharacterInfo.distinctive_features || '暂无' }}</p>
              </div>
            </a-form-item>
          </template>
        </a-form>
      </div>
            
            <FluxKontextConfig
              v-model:config="generationConfig"
              :presets="presets"
              :character-consistency="characterConsistency"
              @preset-change="onPresetChange"
              @save="saveConfig"
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
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch, onUnmounted } from 'vue'
import { message, Modal } from 'ant-design-vue'
import { DownOutlined, SettingOutlined } from '@ant-design/icons-vue'

import FluxKontextConfig from '@/components/image-generation/FluxKontextConfig.vue'
import ImageTaskList from '@/components/image-generation/ImageTaskList.vue'
import ImageGenerationStats from '@/components/image-generation/ImageGenerationStats.vue'
import ImageTaskDetail from '@/components/image-generation/ImageTaskDetail.vue'

import { useImageGenerationStore } from '@/stores/imageGeneration'
import { useBookStore } from '@/stores/book'

// Stores
const imageStore = useImageGenerationStore()
const booksStore = useBookStore()

// 响应式数据
const selectedBookId = ref(null)
const selectedChapterId = ref(null)
const creatingTasks = ref(false)
const batchGenerating = ref(false)
const loadingTasks = ref(false)
const unifiedDrawerVisible = ref(false) // 统一抽屉显示状态
const activeDrawerTab = ref('config') // 当前激活的抽屉标签页
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

// 生成配置 - 适配FluxKontext
const generationConfig = reactive({
  style: 'cinematic', // 电影风格
  steps: 20,          // Flux推荐步数
  guidance: 2.5,      // Flux引导强度
  model: 'flux1-dev-kontext_fp8_scaled', // FluxKontext模型
  enableCharacterConsistency: false,     // 角色一致性
  referenceImage: null                   // 参考图像
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

// 角色一致性配置
const characterConsistency = reactive({
  enabled: false,
  selectedCharacterId: null,
  weight: 0.6,
  characters: [] // 用于存储所有可用的角色
})

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
  return 'FluxKontext 生成配置'
})

// 方法定义
const showConfigDrawer = () => {
  activeDrawerTab.value = 'config'
  unifiedDrawerVisible.value = true
}

const showTaskDetail = (task) => {
  selectedTask.value = task
  activeDrawerTab.value = 'task-detail'
  unifiedDrawerVisible.value = true
}

const closeTaskDetail = () => {
  selectedTask.value = null
  activeDrawerTab.value = 'config'
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

const saveConfig = () => {
  message.success('配置已保存')
  unifiedDrawerVisible.value = false
}

const onPresetChange = (preset) => {
  if (preset && preset.config) {
    Object.assign(generationConfig, preset.config)
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
  
  if (!bookId) return
  
  try {
    await booksStore.fetchChapters(bookId)
  } catch (error) {
    message.error('加载章节列表失败: ' + error.message)
  }
}

const onChapterChange = async (chapterId) => {
  if (!chapterId) return
  
  console.log('📂 章节切换到:', chapterId)
  clearStatusRefresh() // 清理之前的定时器
  await loadImageTasks(chapterId)  // 这一次调用就足够了，会同时更新tasks和stats
  // await loadGenerationStats(chapterId)  // 删除重复调用
  // 移除这里的startStatusRefresh，让loadImageTasks来决定是否启动
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
  try {
    await imageStore.generateSingleImage(taskId)
    message.success('图片生成已开始')
    
    // 5秒后刷新任务状态
    setTimeout(() => {
      loadImageTasks(selectedChapterId.value)
    }, 5000)
  } catch (error) {
    message.error('启动图片生成失败: ' + error.message)
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
const searchCharacters = async (searchText) => {
  if (!searchText) {
    characterConsistency.characters = []
    return
  }
  
  loadingCharacters.value = true
  try {
    const response = await imageStore.searchCharacters({ search: searchText })
    characterConsistency.characters = response.data?.data || []
  } catch (error) {
    message.error('搜索角色失败: ' + error.message)
  } finally {
    loadingCharacters.value = false
  }
}

const onCharacterSelect = (characterId) => {
  const character = characterConsistency.characters.find(c => c.id === characterId)
  if (character) {
    selectedCharacterInfo.value = character
    generationConfig.enableCharacterConsistency = true
    generationConfig.referenceImage = null // 清空参考图像
  } else {
    selectedCharacterInfo.value = null
    generationConfig.enableCharacterConsistency = false
    generationConfig.referenceImage = null
  }
}

const onCharacterConsistencyToggle = (checked) => {
  generationConfig.enableCharacterConsistency = checked
  selectedCharacterInfo.value = null
  generationConfig.referenceImage = null
}

// Lifecycle
onMounted(async () => {
  console.log('🎬 图片生成页面已加载')
  await loadBooks()
  
  // 检查是否有默认选择
  if (selectedBookId.value) {
    console.log('📚 已选择书籍:', selectedBookId.value)
    await booksStore.fetchChapters(selectedBookId.value)
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
  background: #f5f5f5;
  min-height: 100vh;
  padding: 20px;
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
  align-items: center;
  margin: 0 0 8px 0;
  font-size: 28px;
  font-weight: 600;
  color: white;
}

.page-title h1 {
  margin: 0;
  font-size: 28px;
  color: white;
  font-weight: 600;
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
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
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
  gap: 10px;
  padding: 8px 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: background-color 0.2s ease;
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
  padding: 10px;
  background: #f5f5f5;
  border-radius: 6px;
  border: 1px solid #eee;
}

.character-info-preview p {
  margin-bottom: 5px;
  font-size: 13px;
  color: #555;
}

.character-info-preview strong {
  color: #333;
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
</style>