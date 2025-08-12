<template>
  <div class="voice-library-container">
    <!-- 🔧 使用新组件：页面头部 -->
    <CharacterHeader
      :selected-count="selectedCharacterIds.length"
      @add-character="addNewCharacter"
      @batch-config="openBatchConfigModal"
    />

    <!-- 🔧 使用新组件：统计卡片 -->
    <CharacterStats
      :total-count="voiceLibrary.length"
      :configured-count="configuredCount"
      :today-usage="todayUsage"
      :average-quality="averageQuality"
    />

    <!-- 🔧 使用新组件：筛选和搜索 -->
    <CharacterFilters
      :search-query="searchQuery"
      :selected-book-id="selectedBookId"
      :type-filter="typeFilter"
      :status-filter="statusFilter"
      :avatar-filter="avatarFilter"
      :audio-filter="audioFilter"
      :view-mode="viewMode"
      :available-books="availableBooks"
      :books-loading="booksLoading"
      :total-count="voiceLibrary.length"
      :selected-count="selectedCharacterIds.length"
      @search="handleSearch"
      @update:search-query="searchQuery = $event"
      @update:selected-book-id="selectedBookId = $event"
      @update:type-filter="typeFilter = $event"
      @update:status-filter="statusFilter = $event"
      @update:avatar-filter="avatarFilter = $event"
      @update:audio-filter="audioFilter = $event"
      @update:view-mode="viewMode = $event"
      @book-change="handleBookChange"
      @filter-change="handleFilterChange"
      @view-change="handleViewChange"
      @select-all="selectAllCharacters"
      @clear-selection="clearCharacterSelection"
    />

    <!-- 声音库列表 -->
    <div class="voice-library-content">
      <!-- 🔧 使用新组件：网格视图 -->
      <div v-if="viewMode === 'grid'" class="grid-view">
        <div class="character-cards-container">
          <CharacterCard
            v-for="voice in voiceLibrary"
            :key="voice.id"
            :character="voice"
            :selected-character-id="selectedVoice?.id"
            :selected-character-ids="selectedCharacterIds"
            :management-type="managementType"
            @select="handleSelectVoice"
            @play="playVoice"
            @edit="editVoice"
            @duplicate="duplicateVoice"
            @export="exportVoice"
            @delete="confirmDeleteCharacter"
            @batch-select="handleCharacterSelection"
          />
        </div>
        
        <!-- 🔧 使用新组件：卡片模式分页组件 -->
        <CharacterPagination
          v-if="viewMode === 'grid'"
          :current="pagination.current"
          :page-size="pagination.pageSize"
          :total="pagination.total"
          :show-size-changer="pagination.showSizeChanger"
          :show-quick-jumper="pagination.showQuickJumper"
          @change="handleGridPaginationChange"
          @show-size-change="handleGridPaginationChange"
        />
      </div>

      <!-- 🔧 使用新组件：列表视图 -->
      <CharacterListView
        v-else
        :characters="voiceLibrary"
        :pagination="pagination"
        @select="handleSelectVoice"
        @play="playVoice"
        @edit="editVoice"
        @delete="confirmDeleteCharacter"
        @table-change="handleTableChange"
      />
    </div>

    <!-- 🔧 使用新组件：声音详情面板 -->
    <CharacterDetail
      :visible="showDetailDrawer"
      :character="selectedVoice"
      @close="showDetailDrawer = false"
      @use="useVoiceForTTS"
      @edit="editVoice"
      @duplicate="duplicateVoice"
      @delete="confirmDeleteCharacter"
    />

    <!-- 🔧 使用新组件：新增/编辑角色抽屉 -->
    <CharacterEdit
      ref="characterEditRef"
      :visible="showEditModal"
      :character="editingVoice"
      :available-books="availableBooks"
      :books-loading="booksLoading"
      :avatar-generating="avatarGenerating"
      :saving="saving"
      :edit-rules="editRules"
      :color-options="colorOptions"
      @close="cancelEdit"
      @save="saveVoice"
      @generate-avatar="openGenerateAvatarDrawer"
      @remove-avatar="removeAvatar"
      @book-search="handleBookSearch"
      @load-books="loadBooksForEdit"
      @play-audio="playCurrentAudio"
    />



    <!-- 🔧 使用新组件：AI生成头像抽屉 -->
    <AvatarGenerationDrawer
      :visible="showGenerateAvatarDrawer"
      :generating="avatarGenerating"
      :character-name="editingVoice.name"
      :character-description="editingVoice.description"
      :voice-type="editingVoice.type"
      :config="avatarGenConfig"
      @generate="generateAvatar"
      @cancel="cancelGenerateAvatar"
      @update:config="avatarGenConfig = $event"
    />

    <!-- 🔧 使用新组件：批量配置模态框 -->
    <BatchConfigModal
      :visible="showBatchConfigModal"
      :current-step="batchConfigStep"
      :selected-count="selectedCharacterIds.length"
      :selected-characters="voiceLibrary.filter(v => selectedCharacterIds.includes(v.id))"
      :config-data="batchConfigData"
      :loading="batchConfigLoading"
      @close="closeBatchConfigModal"
      @next-step="goToBatchConfigStep(2)"
      @prev-step="goToBatchConfigStep(1)"
      @execute="() => executeBatchConfig(selectedCharacterIds, voiceLibrary)"
      @audio-change="handleBatchAudioChange"
      @npy-change="handleBatchNpyChange"
      @avatar-change="handleBatchAvatarChange"
      @update:config-data="batchConfigData = $event"
    />
  </div>
</template>

<script setup>
  import { ref, computed, reactive, onMounted, h } from 'vue'
  import { useRoute } from 'vue-router'
  import { message, Modal } from 'ant-design-vue'
  import { charactersAPI, booksAPI } from '@/api'
  import { bookAPI } from '../api/v2.js'
  import { playCustomAudio } from '@/utils/audioService'

  // 🔧 引入新的 composables
  import { useBatchConfig } from '@/composables/useBatchConfig'
  
  
  // 🔧 引入新组件
  import CharacterCard from './Characters/components/CharacterCard.vue'
import CharacterFilters from './Characters/components/CharacterFilters.vue'
import CharacterPagination from './Characters/components/CharacterPagination.vue'
import CharacterListView from './Characters/components/CharacterListView.vue'
import CharacterDetail from './Characters/components/CharacterDetail.vue'
import CharacterEdit from './Characters/components/CharacterEdit.vue'

import CharacterHeader from './Characters/components/CharacterHeader.vue'
import CharacterStats from './Characters/components/CharacterStats.vue'
import AvatarGenerationDrawer from './Characters/components/AvatarGenerationDrawer.vue'
import BatchConfigModal from './Characters/components/BatchConfigModal.vue'
  
  // 🔧 引入composable
  import { useCharacters } from '@/composables/useCharacters'

  // 路由
  const route = useRoute()

  // 🔧 使用composable管理角色数据
  const {
    voiceLibrary,
    selectedVoice,
    selectedCharacterIds,
    pagination,
    searchQuery,
    typeFilter,
    statusFilter,
    avatarFilter,
    audioFilter,
    selectedBookId,
    loadVoiceLibrary,
    selectVoice,
    handleCharacterSelection,
    selectAllCharacters,
    clearCharacterSelection
  } = useCharacters()



  // 🔧 使用批量配置 composable
  const {
    showBatchConfigModal,
    batchConfigStep,
    batchConfigData,
    batchConfigLoading,
    openBatchConfigModal,
    closeBatchConfigModal,
    goToBatchConfigStep,
    handleBatchAudioChange,
    handleBatchNpyChange,
    handleBatchAvatarChange,
    executeBatchConfig
  } = useBatchConfig()

  // 其他状态
  const viewMode = ref('grid')
  const showDetailDrawer = ref(false)
  const showEditModal = ref(false)

  // 🔧 自定义选择角色方法，处理详情显示
  const handleSelectVoice = (voice) => {
    selectVoice(voice)
    showDetailDrawer.value = true
  }

  const showUploadModal = ref(false)
  const managementType = ref('character') // 管理类型：'voice' 或 'character'

  // 书籍筛选
  const availableBooks = ref([])
  const booksLoading = ref(false)

  // 编辑状态
  const editingVoice = ref({})

  const characterEditRef = ref(null)
  const saving = ref(false)

  // 表单验证规则
  const editRules = {
    name: [
      { required: true, message: '请输入声音名称', trigger: 'blur' },
      { min: 2, max: 20, message: '名称长度应在 2-20 字符之间', trigger: 'blur' }
    ],
    type: [{ required: true, message: '请选择声音类型', trigger: 'change' }]
  }

  // 颜色选项
  const colorOptions = [
    '#06b6d4',
    '#f472b6',
    '#10b981',
    '#f59e0b',
    '#ef4444',
    '#8b5cf6',
    '#06d6a0',
    '#fbbf24',
    '#3b82f6',
    '#6b7280',
    '#f97316',
    '#84cc16'
  ]



  // 页面初始化时加载书籍列表
  onMounted(async () => {
    await loadAvailableBooks()

    // 🔥 新增：检查URL参数，如果有书籍ID就自动设置过滤条件

    if (route.query.bookId) {
      const bookId = parseInt(route.query.bookId)
      if (!isNaN(bookId)) {
        selectedBookId.value = bookId

        // 如果有书籍标题，显示提示信息
        if (route.query.bookTitle) {
          message.info(`已自动筛选书籍：${route.query.bookTitle}`)
        }
      }
    }

    await loadVoiceLibrary()
  })

  // 加载可用书籍列表
  const loadAvailableBooks = async () => {
    if (availableBooks.value.length > 0) return // 已加载过，直接返回

    try {
      booksLoading.value = true
      const response = await bookAPI.getBooks({
        page: 1,
        page_size: 100
      })

      if (response.success) {
        let books = []
        if (response.data) {
          if (Array.isArray(response.data)) {
            books = response.data
          } else if (response.data.items) {
            books = response.data.items
          } else if (response.data.data) {
            books = response.data.data
          }
        }

        availableBooks.value = books.map((book) => ({
          id: book.id,
          title: book.title,
          author: book.author || '',
          character_count: 0 // 初始值，会在加载角色数据时更新
        }))
      } else {
        message.error('加载书籍列表失败: ' + (response.message || '未知错误'))
      }
    } catch (error) {
      console.error('加载书籍列表失败:', error)
      message.error('加载书籍列表失败: ' + (error.message || '网络错误'))
    } finally {
      booksLoading.value = false
    }
  }



  // 书籍选择变化处理
  const handleBookChange = async (bookId) => {
    selectedBookId.value = bookId
    await loadVoiceLibrary()
  }

  // 搜索处理（兼容新的管理模式）
  // 搜索防抖
  let searchTimeout = null
  const handleSearch = async () => {
    if (searchTimeout) {
      clearTimeout(searchTimeout)
    }
    searchTimeout = setTimeout(async () => {
      pagination.current = 1 // 重置到第一页
      await loadVoiceLibrary()
    }, 300)
  }

  // 筛选变化处理（兼容新的管理模式）
  const handleFilterChange = async () => {
    console.log('🎯 筛选器变化:', {
      audioFilter: audioFilter.value,
      avatarFilter: avatarFilter.value,
      typeFilter: typeFilter.value,
      statusFilter: statusFilter.value
    })
    pagination.current = 1 // 重置到第一页
    await loadVoiceLibrary()
  }

  // 视图模式变化处理
  const handleViewChange = (mode) => {
    viewMode.value = mode
  }
  
  // 表格分页变化处理
  const handleTableChange = (paginationInfo) => {
    pagination.current = paginationInfo.current
    pagination.pageSize = paginationInfo.pageSize
    loadVoiceLibrary()
  }

  // 卡片模式分页变化处理
  const handleGridPaginationChange = (page, pageSize) => {
    pagination.current = page
    pagination.pageSize = pageSize
    loadVoiceLibrary()
  }

  // 保存声音到后端
  const saveVoiceToBackend = async (voiceData) => {
    try {
      // 调试：打印voiceData内容
      console.log('[DEBUG] 保存声音数据:', voiceData)

      // 构建FormData格式数据（后端期望Form格式）
      const formData = new FormData()
      formData.append('name', voiceData.name)
      formData.append('description', voiceData.description || '')
      formData.append('voice_type', voiceData.type) // 注意：后端期望voice_type字段
      formData.append('color', voiceData.color || '#06b6d4')
      formData.append('parameters', JSON.stringify(voiceData.params || {}))
      formData.append('tags', '') // 暂时为空，后续可添加标签功能

      // 添加书籍关联
      if (voiceData.book_id) {
        formData.append('book_id', voiceData.book_id)
      }

      // 添加头像文件（如果有新上传的）
      if (voiceData.avatarFile) {
        formData.append('avatar', voiceData.avatarFile)
      }
      
      // 处理移除头像的情况
      if (voiceData.removeAvatar) {
        formData.append('remove_avatar', 'true')
      }

      // 调试：打印FormData内容
      console.log('[DEBUG] FormData内容:')
      for (let [key, value] of formData.entries()) {
        console.log(`  ${key}: ${value}`)
      }

      // 添加音频文件（如果有新上传的）
      if (voiceData.audioFileList && voiceData.audioFileList.length > 0) {
        const audioFile = voiceData.audioFileList[0].originFileObj
        if (audioFile) {
          formData.append('reference_audio', audioFile)
        }
      }

      // 添加latent文件（如果有新上传的）
      if (voiceData.latentFileList && voiceData.latentFileList.length > 0) {
        const latentFile = voiceData.latentFileList[0].originFileObj
        if (latentFile) {
          formData.append('latent_file', latentFile)
        }
      }

      let response
      if (voiceData.id) {
        // 更新现有声音
        response = await charactersAPI.updateCharacter(voiceData.id, formData)
      } else {
        // 创建新声音
        response = await charactersAPI.createCharacter(formData)
      }

      // axios响应处理
      const responseData = response.data
      if (responseData && responseData.success) {
        await loadVoiceLibrary() // 重新加载数据
        return true
      } else {
        const errorMsg = responseData?.message || '未知错误'
        message.error('保存失败：' + errorMsg)
        return false
      }
    } catch (error) {
      console.error('保存声音错误:', error)
      const errorMsg =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        '网络连接错误'
      message.error('保存失败：' + errorMsg)
      return false
    }
  }

  // 删除角色
  const deleteVoiceFromBackend = async (voiceId, force = false) => {
    try {
      const response = await charactersAPI.deleteCharacter(voiceId, force)
      // 修正：axios响应的实际数据在response.data中
      const responseData = response.data
      if (responseData && responseData.success) {
        await loadVoiceLibrary() // 重新加载数据
        message.success('删除成功')
        return true
      } else {
        const errorMsg = responseData?.message || '未知错误'
        message.error('删除失败：' + errorMsg)
        return false
      }
    } catch (error) {
      console.error('删除角色错误:', error)
      const errorMsg =
        error.response?.data?.detail ||
        error.response?.data?.message ||
        error.message ||
        '网络连接错误'
      message.error('删除失败：' + errorMsg)
      return false
    }
  }

  // 计算属性

  const configuredCount = computed(
    () => voiceLibrary.value.filter((character) => character.status === 'configured').length
  )

  const todayUsage = computed(() =>
    voiceLibrary.value.reduce(
      (sum, v) => sum + (typeof v.usageCount === 'number' ? v.usageCount : 0),
      0
    )
  )

  const averageQuality = computed(() => {
    if (voiceLibrary.value.length === 0) return 0
    const total = voiceLibrary.value.reduce(
      (sum, v) => sum + (typeof v.quality === 'number' ? v.quality : 0),
      0
    )
    const average = total / voiceLibrary.value.length
    return average || 0
  })





  // 播放音频的安全处理
  const playVoice = async (voice) => {
    if (!voice || (!voice.audioUrl && !voice.sampleAudioUrl && !voice.referenceAudioUrl)) {
      message.warning('该声音暂无可播放的音频样本')
      return
    }

    try {
      const audioUrl = voice.sampleAudioUrl || voice.audioUrl || voice.referenceAudioUrl

      // 使用统一播放组件播放
      await playCustomAudio(audioUrl, `${voice.name} - 声音试听`, {
        voiceId: voice.id,
        voiceName: voice.name,
        description: voice.description,
        quality: voice.quality,
        type: voice.type,
        onEnded: () => {
          console.log(`角色 ${voice.name} 试听完成`)
        }
      })

      message.success(`正在播放：${voice.name}`)
    } catch (error) {
      console.error('播放音频失败:', error)
      message.error('播放音频失败，请检查音频文件是否存在')
    }
  }

  const editVoice = (voice) => {
    editingVoice.value = {
      id: voice.id,
      name: voice.name,
      description: voice.description,
      type: voice.type,
      book_id: voice.book_id || '',
      quality: voice.quality,
      status: voice.status,
      color: voice.color,
      avatarUrl: voice.avatarUrl ? `${voice.avatarUrl}?t=${Date.now()}` : null,
      avatarPreview: null,
      avatarFile: null,
      avatarFileList: [],
      referenceAudioUrl: voice.audioUrl || voice.referenceAudioUrl,
      latentFileUrl: voice.latentFileUrl,
      audioFileList: [],
      latentFileList: [],
      audioFileInfo: null,
      latentFileInfo: null,
      params: { ...voice.params }
    }
    showEditModal.value = true
  }

  const addNewCharacter = () => {
    editingVoice.value = {
      id: null,
      name: '',
      description: '',
      type: '',
      book_id: '',
      quality: 3.0,
      status: 'active',
      color: '#06b6d4',
      avatarUrl: null,
      avatarPreview: null,
      avatarFile: null,
      avatarFileList: [],
      audioFileList: [],
      latentFileList: [],
      audioFileInfo: null,
      latentFileInfo: null,
      params: {
        timeStep: 20,
        pWeight: 1.0,
        tWeight: 1.0
      }
    }
    showEditModal.value = true
    showUploadModal.value = false
  }

  const saveVoice = async () => {
    try {
      saving.value = true
      
      // 检查组件引用是否存在
      if (!characterEditRef.value || !characterEditRef.value.editForm) {
        console.error('表单引用不存在')
        message.error('表单未正确初始化，请重新打开编辑窗口')
        return
      }
      
      await characterEditRef.value.editForm.validate()

      // 调用后端API保存
      const success = await saveVoiceToBackend(editingVoice.value)

      if (success) {
        showEditModal.value = false
        message.success(editingVoice.value.id ? '角色更新成功' : '角色创建成功')
        // 数据已在saveVoiceToBackend中重新加载
      }
    } catch (error) {
      console.error('保存声音失败:', error)
      message.error('保存失败，请重试')
    } finally {
      saving.value = false
    }
  }

  const cancelEdit = () => {
    showEditModal.value = false
    characterEditRef.value?.editForm?.resetFields()
  }





  const removeAvatar = () => {
    editingVoice.value.avatarPreview = null
    editingVoice.value.avatarFile = null
    editingVoice.value.avatarFileList = []
    editingVoice.value.avatarUrl = null // 清除现有头像URL
    editingVoice.value.removeAvatar = true // 标记需要删除头像
  }

  // 🔥 新增：AI头像生成相关方法
  const generateAvatar = async () => {
    if (!editingVoice.value.name) {
      message.error('请先输入角色名称')
      return
    }

    try {
      avatarGenerating.value = true
      
      // 构建请求数据
      const requestData = {
        character_name: editingVoice.value.name || '',
        description: avatarGenConfig.customPrompt || editingVoice.value.description || '',
        style: avatarGenConfig.style || 'realistic'
      }

      // 如果是编辑已存在的角色，直接调用API
      if (editingVoice.value.id) {
        const response = await fetch(`/api/v1/characters/ai/generate-avatar/${editingVoice.value.id}`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(requestData)
        })

        const result = await response.json()
        
        if (result.success) {
          // 更新头像预览
          editingVoice.value.avatarUrl = result.avatar_url
          editingVoice.value.avatarPreview = result.avatar_url
          
          // 🔧 修复：刷新角色列表以显示新头像
          await loadVoiceLibrary()
          
          message.success('头像生成成功！')
          showGenerateAvatarDrawer.value = false
        } else {
          message.error(`头像生成失败: ${result.message}`)
        }
      } else {
        // 新角色，先临时保存角色信息
        message.info('新角色需要先保存才能生成头像，请先保存角色信息')
      }

    } catch (error) {
      console.error('生成头像失败:', error)
      message.error('头像生成失败，请检查网络连接')
    } finally {
      avatarGenerating.value = false
    }
  }

  const openGenerateAvatarDrawer = () => {
    // 重置所有头像生成配置参数
    avatarGenConfig.style = 'realistic'
    avatarGenConfig.size = '512x512'
    avatarGenConfig.customPrompt = ''
    avatarGenConfig.referenceImageList = []
    avatarGenConfig.referenceImageFile = null
    showGenerateAvatarDrawer.value = true
  }

  const cancelGenerateAvatar = () => {
    showGenerateAvatarDrawer.value = false
    // 重置所有头像生成配置参数
    avatarGenConfig.style = 'realistic'
  }



  // 为编辑界面加载书籍列表
  const loadBooksForEdit = async () => {
    if (availableBooks.value.length > 0) return // 已加载过

    booksLoading.value = true
    try {
      const response = await booksAPI.getBooks({
        page: 1,
        page_size: 100
      })

      // 处理响应数据
      const responseData = response.data
      if (responseData && responseData.success) {
        let books = []
        if (responseData.data) {
          if (Array.isArray(responseData.data)) {
            books = responseData.data
          } else if (responseData.data.items) {
            books = responseData.data.items
          } else if (responseData.data.data) {
            books = responseData.data.data
          }
        }

        availableBooks.value = books
      }
    } catch (error) {
      console.error('加载书籍列表失败:', error)
    } finally {
      booksLoading.value = false
    }
  }

  // 书籍搜索
  const handleBookSearch = (searchValue) => {
    // 可以在这里实现实时搜索功能
    console.log('搜索书籍:', searchValue)
  }









  const duplicateVoice = (voice) => {
    message.success(`已复制声音：${voice.name}`)
  }

  const exportVoice = (voice) => {
    message.success(`导出声音：${voice.name}`)
  }

  // 确认删除角色
  const confirmDeleteCharacter = (character) => {
    // 创建一个响应式的状态来管理强制删除选项
    let forceDelete = false

    Modal.confirm({
      title: '删除角色',
      content: h('div', [
        h('p', `确定要删除角色"${character.name}"吗？此操作不可恢复。`),
        h('div', { style: 'margin: 16px 0 8px 0;' }, [
          h('p', { style: 'margin: 0 0 8px 0; color: #fa8c16; font-weight: 500;' }, '⚠️ 删除提示'),
          h(
            'p',
            { style: 'margin: 0; font-size: 13px; color: #8c8c8c;' },
            '如果角色已被项目使用或包含声音文件，可能需要强制删除'
          )
        ]),
        h('div', { style: 'margin: 12px 0;' }, [
          h('label', { style: 'display: flex; align-items: center; gap: 8px; cursor: pointer;' }, [
            h('input', {
              type: 'checkbox',
              onChange: (e) => {
                forceDelete = e.target.checked
              }
            }),
            h(
              'span',
              { style: 'color: #ff4d4f; font-weight: 500;' },
              '强制删除（包括关联的声音文件和项目引用）'
            )
          ])
        ])
      ]),
      okText: '删除',
      okType: 'danger',
      cancelText: '取消',
      onOk: () => deleteCharacter(character, forceDelete)
    })
  }

  // 删除角色
  const deleteCharacter = async (character, force = false) => {
    try {
      console.log('删除角色:', character.id, '强制删除:', force)
      const success = await deleteVoiceFromBackend(character.id, force)
      if (success) {
        message.success('角色删除成功')
        loadVoiceLibrary()
        if (selectedVoice.value?.id === character.id) {
          showDetailDrawer.value = false
          selectedVoice.value = null
        }
      }
    } catch (error) {
      console.error('删除角色失败:', error)

      // 如果是需要强制删除的错误，给出友好提示
      if (error.response?.data?.message?.includes('请使用强制删除')) {
        Modal.warning({
          title: '删除失败',
          content: '角色包含关联数据，请勾选"强制删除"选项后重试',
          okText: '知道了'
        })
      } else {
        const errorMsg = error.response?.data?.message || error.message || '删除失败'
        message.error('删除失败: ' + errorMsg)
      }
    }
  }

  const useVoiceForTTS = () => {
    message.success(`已选择声音用于TTS生成`)
    showDetailDrawer.value = false
  }

  // getStatusColor 和 getStatusText 函数已移动到文件前面，避免重复定义

  // 添加播放当前音频的功能
  const playCurrentAudio = async () => {
    if (editingVoice.value.referenceAudioUrl) {
      try {
        // 使用统一播放组件播放
        await playCustomAudio(
          editingVoice.value.referenceAudioUrl,
          `${editingVoice.value.name || '预览'} - 音频试听`,
          {
            voiceId: editingVoice.value.id,
            voiceName: editingVoice.value.name,
            description: editingVoice.value.description,
            onEnded: () => {
              console.log(`编辑音频 ${editingVoice.value.name} 试听完成`)
            }
          }
        )
        message.success('开始播放音频')
      } catch (error) {
        console.error('播放音频失败:', error)
        message.error('播放音频失败')
      }
    } else {
      message.warning('没有可播放的音频文件')
    }
  }



  // 组件挂载时加载数据
  onMounted(async () => {
    try {
      await loadVoiceLibrary()
    } catch (error) {
      console.error('初始化加载失败:', error)
      message.error('加载数据失败，请刷新页面重试')
    }
  })







  // 🔥 新增：AI头像生成相关状态
  const showGenerateAvatarDrawer = ref(false)
  const avatarGenerating = ref(false)
  const avatarGenConfig = reactive({
    style: 'realistic',
    size: '512x512',
    customPrompt: '',
    referenceImageList: [],
    referenceImageFile: null
  })
</script>

<style scoped>
  .voice-library-container {
    background: #f8fafc;
    min-height: 100vh;
  }

  .page-header {
    margin-bottom: 24px;
    padding: 32px;
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    border-radius: 12px;
    box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .title-section {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .page-title {
    display: flex;
    align-items: center;
    margin: 0;
    font-size: 28px;
    font-weight: 600;
    color: white;
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

  .action-section {
    display: flex;
    gap: 16px;
  }

  .filter-controls {
    display: flex;
    gap: 16px;
    align-items: center;
  }

  .voice-library-content {
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    padding: 24px;
  }

  .grid-view {
    display: flex;
    flex-direction: column;
    gap: 24px;
  }

  .character-cards-container {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
    gap: 16px;
    align-items: stretch;
  }

  .voice-card {
    border: 2px solid #d1d5db;
    border-radius: 12px;
    padding: 20px;
    cursor: pointer;
    transition: all 0.3s;
    position: relative;
  }

  .voice-card:hover {
    border-color: #06b6d4;
    transform: translateY(-4px);
    box-shadow: 0 8px 24px rgba(6, 182, 212, 0.15);
  }

  .voice-card.selected {
    border-color: #06b6d4;
    background: #f0f9ff;
  }

  .voice-avatar {
    position: relative;
    margin-bottom: 16px;
  }

  .avatar-icon {
    width: 64px;
    height: 64px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 24px;
    font-weight: 600;
    overflow: hidden;
  }

  .avatar-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
    border-radius: inherit;
  }

  .voice-status {
    position: absolute;
    bottom: -4px;
    right: -4px;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .status-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }

  .voice-status.active .status-dot {
    background: #10b981;
  }
  .voice-status.training .status-dot {
    background: #f59e0b;
  }
  .voice-status.inactive .status-dot {
    background: #6b7280;
  }

  .voice-info {
    margin-bottom: 16px;
  }

  .voice-name {
    margin: 0 0 8px 0;
    font-size: 18px;
    font-weight: 600;
    color: #2c3e50;
  }

  .voice-desc {
    margin: 0 0 12px 0;
    color: #6b7280;
    font-size: 14px;
    line-height: 1.5;
  }

  .voice-meta {
    display: flex;
    gap: 16px;
  }

  .meta-item {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    color: #6b7280;
  }

  .voice-actions {
    display: flex;
    justify-content: flex-end;
    gap: 8px;
  }

  .table-avatar {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 16px;
    overflow: hidden;
  }

  .voice-detail {
    height: 100%;
    display: flex;
    flex-direction: column;
  }

  .detail-header {
    display: flex;
    gap: 16px;
    align-items: flex-start;
  }

  .detail-avatar {
    width: 80px;
    height: 80px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 32px;
    font-weight: 600;
    overflow: hidden;
  }

  .detail-info {
    flex: 1;
  }

  .detail-info h2 {
    margin: 0 0 8px 0;
    color: #2c3e50;
  }

  .detail-info p {
    margin: 0 0 12px 0;
    color: #6b7280;
  }

  .detail-section {
    margin-bottom: 24px;
  }

  .detail-section h3 {
    margin: 0 0 16px 0;
    color: #374151;
    font-size: 16px;
    font-weight: 600;
  }

  .params-list,
  .stats-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .param-row,
  .stat-row {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 8px 0;
    border-bottom: 1px solid #f3f4f6;
  }

  .param-label,
  .stat-label {
    color: #6b7280;
    font-size: 14px;
  }

  /* 头像上传样式 */
  .avatar-upload-section {
    display: flex;
    align-items: center;
    gap: 16px;
  }

  .current-avatar-preview {
    flex-shrink: 0;
  }

  .avatar-preview {
    width: 80px;
    height: 80px;
    border-radius: 12px;
    overflow: hidden;
    border: 2px solid #e5e7eb;
  }

  .avatar-preview .avatar-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .avatar-placeholder {
    width: 80px;
    height: 80px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px dashed #d1d5db;
  }

  .upload-tips {
    font-size: 12px;
    color: #6b7280;
    margin-top: 8px;
  }

  .param-value,
  .stat-value {
    color: #374151;
    font-weight: 500;
    font-size: 14px;
  }

  .detail-actions {
    margin-top: auto;
    padding-top: 24px;
  }

  .voice-edit-form {
    padding-bottom: 80px;
  }

  .voice-edit-form .ant-form-item {
    margin-bottom: 20px;
  }

  .edit-upload {
    border-radius: 8px !important;
    border-color: #d1d5db !important;
    background: #f9fafb !important;
  }

  .edit-upload .upload-content {
    padding: 24px;
    text-align: center;
  }

  .param-display {
    text-align: center;
    color: #6b7280;
    font-size: 12px;
    margin-top: 4px;
  }

  .color-picker {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }

  .color-option {
    width: 32px;
    height: 32px;
    border-radius: 6px;
    cursor: pointer;
    border: 2px solid transparent;
    transition: all 0.3s;
  }

  .color-option:hover,
  .color-option.selected {
    border-color: #374151;
    transform: scale(1.1);
  }

  .file-item {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 8px;
    background: #f0f9ff;
    border-radius: 6px;
    border: 1px solid #e0f2fe;
  }

  .file-details {
    flex: 1;
  }

  .file-name {
    font-size: 14px;
    color: #374151;
    font-weight: 500;
  }

  .file-meta {
    font-size: 12px;
    color: #6b7280;
  }

  .import-upload {
    border-radius: 12px !important;
    border-color: #d1d5db !important;
    background: #f9fafb !important;
  }

  .import-upload .upload-content {
    padding: 32px;
    text-align: center;
  }

  .import-tips {
    background: #f8fafc;
    padding: 16px;
    border-radius: 8px;
    border: 1px solid #e2e8f0;
  }

  .import-tips ul {
    margin: 0;
    padding-left: 16px;
  }

  /* 当前文件显示样式 */
  .current-files-section {
    margin-bottom: 24px;
  }

  .current-file-item {
    margin-bottom: 12px;
    padding: 12px;
    background: #f8f9fa;
    border-radius: 8px;
    border: 1px solid #e9ecef;
  }

  .file-info {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .file-header {
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .file-label {
    font-size: 14px;
    color: #374151;
    font-weight: 500;
  }

  .file-actions {
    display: flex;
    gap: 8px;
  }

  /* 音频样本样式 */
  .audio-sample {
    background: #f8fafc;
    border: 1px solid #e2e8f0;
    border-radius: 8px;
    padding: 16px;
  }

  .audio-sample audio {
    border-radius: 4px;
  }

  .no-audio-message {
    background: #f9fafb;
    border: 2px dashed #d1d5db;
    border-radius: 8px;
  }

  /* 统计卡片样式 */
  .stats-grid {
    display: grid;
    grid-template-columns: repeat(4, 1fr);
    gap: 24px;
    margin-bottom: 32px;
  }

  .stat-card {
    border-radius: 16px;
    padding: 24px;
    display: flex;
    align-items: center;
    gap: 16px;
    box-shadow:
      0 4px 6px -1px rgba(0, 0, 0, 0.1),
      0 2px 4px -1px rgba(0, 0, 0, 0.06);
    transition: all 0.3s;
    border: 1px solid rgba(255, 255, 255, 0.2);
  }

  .stat-card:hover {
    transform: translateY(-2px);
    box-shadow:
      0 10px 25px -3px rgba(0, 0, 0, 0.1),
      0 4px 6px -2px rgba(0, 0, 0, 0.05);
  }

  .stat-icon {
    width: 56px;
    height: 56px;
    border-radius: 12px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  .stat-content {
    flex: 1;
  }

  .stat-value {
    font-size: 28px;
    font-weight: 700;
    color: #1f2937;
    line-height: 1;
    margin-bottom: 4px;
  }

  .stat-label {
    font-size: 14px;
    color: #6b7280;
    font-weight: 500;
  }

  /* 筛选区域样式 */
  .filter-section {
    border-radius: 12px;
    padding: 20px;
    margin-bottom: 24px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .view-controls {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  /* 响应式设计 */
  @media (max-width: 1200px) {
    .stats-grid {
      grid-template-columns: repeat(2, 1fr);
    }
  }

  @media (max-width: 768px) {
    .stats-grid {
      grid-template-columns: 1fr;
      gap: 16px;
    }

    .stat-card {
      padding: 20px;
    }

    .stat-icon {
      width: 48px;
      height: 48px;
    }

    .stat-value {
      font-size: 24px;
    }

    .filter-section {
      flex-direction: column;
      gap: 16px;
      align-items: stretch;
    }

    .filter-controls {
      flex-wrap: wrap;
    }

    .grid-view {
      grid-template-columns: 1fr;
    }

    .ant-layout-sider {
      position: fixed !important;
      left: 0;
      top: 0;
      bottom: 0;
      z-index: 1000;
    }

    .ant-layout-content {
      margin-left: 0 !important;
    }

    .logo-text h3 {
      font-size: 14px !important;
    }
  }



  .book-card.selected {
    border-color: var(--primary-color);
    background: rgba(var(--primary-color-rgb), 0.06);
  }

  .book-icon {
    color: var(--primary-color);
    flex-shrink: 0;
  }

  .book-info {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .book-info h4 {
    margin: 0;
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
    line-height: 1.4;
  }

  .book-info p {
    margin: 0;
    color: #6b7280;
    font-size: 14px;
  }

  .book-stats {
    display: flex;
    gap: 12px;
    margin: 8px 0;
    font-size: 12px;
    color: #9ca3af;
  }

  .book-meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-top: auto;
  }

  .book-status {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 12px;
    background: #10b981;
    color: white;
  }

  .book-id {
    font-size: 11px;
    color: #9ca3af;
  }

  /* 章节选择样式 */
  .chapter-selection {
    margin-bottom: 32px;
  }

  .selection-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: #f9fafb;
    border-radius: 8px;
  }

  .selection-info {
    color: #6b7280;
    font-size: 14px;
  }

  .chapters-list {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #d1d5db;
    border-radius: 8px;
  }

  .chapters-grid {
    display: block;
  }

  .chapter-item {
    border-bottom: 1px solid #d1d5db;
    padding: 12px 16px;
  }

  .chapter-item:last-child {
    border-bottom: none;
  }

  .chapter-content {
    margin-left: 8px;
  }

  /* 已存在角色样式 */
  .existing-character {
    opacity: 0.7;
  }

  .existing-character .config-card {
    background: #f8f9fa !important;
    border: 1px dashed #d1d5db !important;
  }

  .existing-character-info {
    padding: 16px;
    background: #f8f9fa;
    border-radius: 8px;
  }

  .existing-config-display {
    margin-top: 12px;
  }

  .chapter-title {
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 4px;
  }

  .chapter-meta {
    font-size: 12px;
    color: #6b7280;
  }

  /* 分析进度样式 */
  .analysis-progress {
    margin-bottom: 32px;
    text-align: center;
  }

  .progress-text {
    margin-top: 16px;
    color: #6b7280;
    font-size: 14px;
  }

  .analysis-results {
    margin-top: 32px;
  }

  .results-summary {
    margin-bottom: 24px;
    padding: 20px;
    background: #f9fafb;
    border-radius: 8px;
  }

  .characters-preview h4 {
    margin-bottom: 16px;
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
  }

  .characters-list {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .character-preview-item,
  .created-character-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px;
    border: 1px solid #d1d5db;
    border-radius: 8px;
  }

  .character-avatar {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: 600;
    font-size: 16px;
    flex-shrink: 0;
  }

  .character-info {
    flex: 1;
  }

  .character-name {
    font-weight: 500;
    color: #1f2937;
    margin-bottom: 4px;
  }

  .character-meta {
    font-size: 12px;
    color: #6b7280;
  }

  .character-status,
  .character-actions {
    display: flex;
    gap: 8px;
    align-items: center;
  }

  /* 批量配置样式 */
  .batch-config {
    margin-bottom: 32px;
  }

  .config-controls {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 16px;
    padding: 12px 16px;
    background: #f9fafb;
    border-radius: 8px;
  }

  .config-list {
    max-height: 400px;
    overflow-y: auto;
  }

  .config-grid {
    display: block;
  }

  .config-item {
    margin-bottom: 16px;
  }

  .config-card {
    border: 1px solid #d1d5db;
    border-radius: 8px;
    padding: 16px;
  }

  .config-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 16px;
  }

  .character-basic h4 {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
  }

  .character-basic p {
    margin: 0;
    color: #6b7280;
    font-size: 14px;
  }

  .config-details {
    border-top: 1px solid #d1d5db;
    padding-top: 16px;
  }

  /* 创建结果样式 */
  .creation-results {
    margin-top: 24px;
  }

  .results-summary {
    margin-bottom: 24px;
  }

  .created-characters h4 {
    margin-bottom: 16px;
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
  }

  /* 文件信息小样式 */
  .file-info-mini {
    margin-top: 4px;
    font-size: 11px;
    color: #6b7280;
  }

  .file-name-mini {
    display: block;
    font-weight: 500;
    color: #374151;
  }

  .file-size-mini {
    color: #9ca3af;
  }

  .character-files {
    margin-top: 8px;
    display: flex;
    gap: 4px;
    flex-wrap: wrap;
  }

  .back-btn-header {
    font-size: 18px;
    padding: 8px 12px;
    display: flex;
    align-items: center;
    color: rgba(255, 255, 255, 0.9);
    transition: all 0.2s;
    border: 1px solid rgba(255, 255, 255, 0.3);
    margin-right: 16px;
  }

  .back-btn-header:hover {
    color: white;
    background: rgba(255, 255, 255, 0.1);
    border-color: rgba(255, 255, 255, 0.5);
  }

  /* 暗黑模式适配 */
  [data-theme='dark'] .characters-container {
    background: #141414 !important;
    min-height: 100vh !important;
  }

  [data-theme='dark'] .character-card,
  [data-theme='dark'] .character-preview-item,
  [data-theme='dark'] .created-character-item,
  [data-theme='dark'] .config-card {
    background: #434343 !important;
    border-color: #434343 !important;
    color: #fff !important;
  }

  [data-theme='dark'] .character-name {
    color: #fff !important;
  }

  [data-theme='dark'] .character-meta,
  [data-theme='dark'] .character-basic p,
  [data-theme='dark'] .file-info-mini,
  [data-theme='dark'] .file-size-mini {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .file-name-mini {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .progress-text {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .results-summary,
  [data-theme='dark'] .config-controls {
    background: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .characters-preview h4,
  [data-theme='dark'] .created-characters h4,
  [data-theme='dark'] .character-basic h4 {
    color: #fff !important;
  }

  [data-theme='dark'] .config-details {
    border-top-color: #434343 !important;
  }

  [data-theme='dark'] .voice-card {
    background: #1f1f1f !important;
    border-color: #434343 !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
  }

  [data-theme='dark'] .voice-card:hover {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
  }

  [data-theme='dark'] .voice-card.selected {
    border-color: #4a9eff !important;
    box-shadow: 0 0 0 2px rgba(74, 158, 255, 0.2) !important;
  }

  [data-theme='dark'] .voice-name {
    color: #fff !important;
  }

  [data-theme='dark'] .voice-desc {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .meta-item span {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .voice-library-content {
    background: transparent !important;
  }

  [data-theme='dark'] .grid-view,
  [data-theme='dark'] .list-view {
    background: transparent !important;
  }

  [data-theme='dark'] .voice-library-container {
    background: #141414 !important;
  }

  [data-theme='dark'] .stats-grid {
    background: transparent !important;
  }

  [data-theme='dark'] .stat-card {
    background: #1f1f1f !important;
    border-color: #434343 !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
  }

  [data-theme='dark'] .stat-card:hover {
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.4) !important;
  }

  [data-theme='dark'] .stat-value {
    color: #fff !important;
  }

  [data-theme='dark'] .stat-label {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .filter-section {
    background: #1f1f1f !important;
    border-color: #434343 !important;
    box-shadow: 0 4px 16px rgba(0, 0, 0, 0.3) !important;
  }

  [data-theme='dark'] .voice-library-content {
    background: transparent !important;
    box-shadow: none !important;
  }

  [data-theme='dark'] .page-header {
    background: linear-gradient(135deg, #2d2d2d 0%, #1f1f1f 100%) !important;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.5) !important;
  }

  [data-theme='dark'] .voice-info {
    color: #d1d5db !important;
  }

  [data-theme='dark'] .voice-avatar {
    background: transparent !important;
  }

  [data-theme='dark'] .voice-status {
    background: #2d2d2d !important;
    border: 1px solid #434343 !important;
  }



  [data-theme='dark'] .character-meta {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .existing-character-info {
    background: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .existing-character .config-card {
    background: #2d2d2d !important;
    border-color: #434343 !important;
  }

  [data-theme='dark'] .empty-state p {
    color: #8c8c8c !important;
  }

  [data-theme='dark'] .empty-state svg {
    fill: #434343 !important;
  }

  /* 书籍信息样式 */
  .book-info {
    margin: 8px 0;
  }

  .book-badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 2px 8px;
    background: #f3f4f6;
    border: 1px solid #d1d5db;
    border-radius: 12px;
    font-size: 11px;
    color: #6b7280;
    max-width: 100%;
    overflow: hidden;
  }

  .book-badge svg {
    flex-shrink: 0;
    fill: #9ca3af;
  }

  .book-badge span {
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
  }

  /* 角色管理模式的卡片样式调整 */
  .voice-card[data-character='true'] {
    border-left: 4px solid #8b5cf6;
  }

  .voice-card[data-character='true'] .voice-avatar .avatar-icon {
    background: #8b5cf6 !important;
  }

  /* 管理类型选择器样式 */
  .filter-controls .ant-select:first-child {
    border: 2px solid #06b6d4;
    border-radius: 8px;
  }

  .filter-controls .ant-select:first-child .ant-select-selector {
    border: none;
    font-weight: 500;
    color: #06b6d4;
  }

  /* 角色配置状态样式 */
  .meta-item span[data-status='configured'] {
    color: #10b981;
  }

  .meta-item span[data-status='unconfigured'] {
    color: #f59e0b;
  }

  /* 书籍选择器样式 */
  .filter-controls .ant-select[data-book-selector] .ant-select-selector {
    border-color: #8b5cf6;
  }

  /* 暗黑模式适配 */
  [data-theme='dark'] .book-badge {
    background: #374151 !important;
    border-color: #6b7280 !important;
    color: #d1d5db !important;
  }

  [data-theme='dark'] .book-badge svg {
    fill: #9ca3af !important;
  }

  [data-theme='dark'] .voice-card[data-character='true'] {
    border-left-color: #a855f7 !important;
  }

  [data-theme='dark'] .voice-card[data-character='true'] .voice-avatar .avatar-icon {
    background: #a855f7 !important;
  }

  /* 批量配置相关样式 */
  .batch-controls {
    display: flex;
    gap: 8px;
    margin-right: 16px;
  }

  .batch-select-checkbox {
    position: absolute;
    top: 8px;
    left: 8px;
    z-index: 10;
    background: rgba(255, 255, 255, 0.9);
    border-radius: 4px;
    padding: 2px;
  }

  .voice-card.batch-selected {
    border: 2px solid #1890ff;
    box-shadow: 0 0 8px rgba(24, 144, 255, 0.3);
  }

  .batch-config-content {
    padding: 16px 0;
  }

  .batch-steps {
    margin-bottom: 24px;
  }

  .batch-step-content {
    min-height: 300px;
  }

  .selected-characters-info h3 {
    margin-bottom: 16px;
    color: #1890ff;
  }

  .character-list {
    max-height: 300px;
    overflow-y: auto;
    border: 1px solid #d9d9d9;
    border-radius: 6px;
    padding: 8px;
  }

  .character-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 8px;
    border-radius: 4px;
    margin-bottom: 8px;
    background: #fafafa;
  }

  .character-item:last-child {
    margin-bottom: 0;
  }

  .character-item .character-avatar {
    flex-shrink: 0;
  }

  .character-item .avatar-icon {
    width: 32px;
    height: 32px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-weight: bold;
    font-size: 14px;
  }

  .character-item .avatar-image {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
  }

  .character-item .character-info {
    flex: 1;
    min-width: 0;
  }

  .character-item .character-name {
    font-weight: 500;
    margin-bottom: 4px;
  }

  .character-item .character-desc {
    font-size: 12px;
    color: #666;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  .file-upload-section {
    margin-top: 12px;
    padding: 12px;
    background: #f9f9f9;
    border-radius: 6px;
  }

  .upload-tips {
    margin-top: 8px;
    color: #666;
  }

  .step-actions {
    display: flex;
    justify-content: flex-end;
    gap: 12px;
    margin-top: 24px;
    padding-top: 16px;
    border-top: 1px solid #f0f0f0;
  }

  /* 暗黑模式适配 */
  [data-theme='dark'] .batch-select-checkbox {
    background: rgba(0, 0, 0, 0.8);
  }

  [data-theme='dark'] .character-list {
    border-color: #434343;
    background: #1f1f1f;
  }

  [data-theme='dark'] .character-item {
    background: #2d2d2d;
  }

  [data-theme='dark'] .character-item .character-name {
    color: #fff;
  }

  [data-theme='dark'] .character-item .character-desc {
    color: #8c8c8c;
  }

  [data-theme='dark'] .file-upload-section {
    background: #2d2d2d;
  }

  [data-theme='dark'] .step-actions {
    border-top-color: #434343;
  }

  [data-theme='dark'] .upload-tips {
    color: #8c8c8c;
  }

  /* 卡片模式分页组件样式 */
  .grid-pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    margin-top: 32px;
    padding: 24px 0;
    border-top: 1px solid #f0f0f0;
    background: #fff;
    width: 100%;
    min-width: 100%;
    box-sizing: border-box;
  }

  /* 分页组件内部样式 */
  .grid-pagination .ant-pagination {
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  /* 确保分页组件占满容器宽度 */
  .grid-pagination .ant-pagination-total {
    flex: 1;
    text-align: left;
  }

  .grid-pagination .ant-pagination-options {
    flex: 1;
    text-align: right;
  }

  .grid-pagination .ant-pagination-prev,
  .grid-pagination .ant-pagination-next,
  .grid-pagination .ant-pagination-item {
    margin: 0 4px;
  }

  /* 暗黑模式下的分页组件样式 */
  [data-theme='dark'] .grid-pagination {
    border-top-color: #434343;
    background: #1f1f1f;
    width: 100%;
    min-width: 100%;
  }
</style>
