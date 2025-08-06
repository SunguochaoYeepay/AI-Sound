import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'
import { booksAPI, chaptersAPI, charactersAPI } from '@/api'
import { bookAPI } from '@/api/v2.js'

export function useSmartDiscovery() {
  // 智能发现状态
  const discoveryStep = ref(0)
  const discoverySteps = ref([
    { title: '选择书籍', description: '选择要分析的书籍' },
    { title: '选择章节', description: '选择要分析的章节' },
    { title: '分析角色', description: 'AI分析章节中的角色' },
    { title: '配置角色', description: '配置发现的角色' },
    { title: '创建完成', description: '角色创建完成' }
  ])

  // 书籍和章节数据
  const booksData = ref([])
  const chaptersData = ref([])
  const chaptersLoading = ref(false)
  const selectedBook = ref(null)
  const availableChapters = ref([])
  const selectedChapters = ref([])
  const loadingChapters = ref(false)
  const chapterCheckAll = ref(false)
  const chapterIndeterminate = ref(false)

  // 分析状态
  const analysisStatus = ref('normal')
  const analysisText = ref('')

  // 角色数据
  const newCharacters = ref([])
  const selectedConfigs = ref([])
  const configCheckAll = ref(false)
  const configIndeterminate = ref(false)
  const creatingCharacters = ref(false)
  const createdCharacters = ref([])

  // 计算属性
  const mainCharactersCount = computed(() => {
    return newCharacters.value.filter(char => char.is_main_character).length
  })

  // 方法
  const loadBooks = async () => {
    try {
      const response = await booksAPI.getBooks()
      if (response.success) {
        booksData.value = response.data || []
      }
    } catch (error) {
      console.error('加载书籍失败:', error)
      message.error('加载书籍失败')
    }
  }

  const selectBook = async (book) => {
    selectedBook.value = book
    discoveryStep.value = 1
    await loadChapters(book.id)
  }

  const loadChapters = async (bookId) => {
    try {
      chaptersLoading.value = true
      const response = await chaptersAPI.getChapters({ book_id: bookId })
      if (response.success) {
        chaptersData.value = response.data || []
        availableChapters.value = chaptersData.value
      }
    } catch (error) {
      console.error('加载章节失败:', error)
      message.error('加载章节失败')
    } finally {
      chaptersLoading.value = false
    }
  }

  const analyzeCharacters = async () => {
    if (selectedChapters.value.length === 0) {
      message.warning('请至少选择一个章节进行分析')
      return
    }

    try {
      analysisStatus.value = 'analyzing'
      analysisText.value = '正在分析章节中的角色...'

      const chapterIds = selectedChapters.value.map(chapter => chapter.id)
      const response = await bookAPI.analyzeCharacters({
        book_id: selectedBook.value.id,
        chapter_ids: chapterIds
      })

      if (response.success) {
        await processAnalysisResult(response.data)
        discoveryStep.value = 3
      } else {
        throw new Error(response.message || '分析失败')
      }
    } catch (error) {
      console.error('角色分析失败:', error)
      message.error('角色分析失败，请重试')
      analysisStatus.value = 'error'
      analysisText.value = '分析失败，请重试'
    }
  }

  const processAnalysisResult = async (analysisData) => {
    try {
      // 检查角色是否已存在
      await checkCharacterExistence(analysisData.characters)
      
      // 准备角色配置
      prepareCharacterConfigs()
      
      analysisStatus.value = 'completed'
      analysisText.value = '角色分析完成！'
    } catch (error) {
      console.error('处理分析结果失败:', error)
      throw error
    }
  }

  const checkCharacterExistence = async (characters) => {
    try {
      // 获取现有角色列表来检查存在性
      const response = await charactersAPI.getCharacters({ page_size: 1000 })
      
      if (response.success) {
        const existingCharacters = response.data || []
        const existingNames = existingCharacters.map(char => char.name)
        
        newCharacters.value = characters.map(character => ({
          ...character,
          exists_in_library: existingNames.includes(character.name),
          existing_config: existingCharacters.find(char => char.name === character.name) || null,
          recommended_config: {
            name: character.name,
            description: character.description || `来自《${selectedBook.value.title}》的角色`,
            type: character.gender === 'male' ? 'male' : 'female',
            quality: 3.0,
            status: 'active',
            color: '#06b6d4'
          }
        }))
      }
    } catch (error) {
      console.error('检查角色存在性失败:', error)
      // 如果检查失败，假设所有角色都不存在
      newCharacters.value = characters.map(character => ({
        ...character,
        exists_in_library: false,
        existing_config: null,
        recommended_config: {
          name: character.name,
          description: character.description || `来自《${selectedBook.value.title}》的角色`,
          type: character.gender === 'male' ? 'male' : 'female',
          quality: 3.0,
          status: 'active',
          color: '#06b6d4'
        }
      }))
    }
  }

  const prepareCharacterConfigs = () => {
    selectedConfigs.value = newCharacters.value
      .filter(char => !char.exists_in_library)
      .map(char => char.name)
    
    updateConfigCheckState()
  }

  const updateConfigCheckState = () => {
    const charactersToCreate = newCharacters.value.filter(char => !char.exists_in_library)
    const checkedCount = selectedConfigs.value.length
    const totalCount = charactersToCreate.length

    configCheckAll.value = checkedCount === totalCount && totalCount > 0
    configIndeterminate.value = checkedCount > 0 && checkedCount < totalCount
  }

  const createCharacters = async () => {
    const charactersToCreate = newCharacters.value.filter(char => 
      selectedConfigs.value.includes(char.name) && !char.exists_in_library
    )

    if (charactersToCreate.length === 0) {
      message.warning('请选择要创建的角色')
      return
    }

    try {
      creatingCharacters.value = true

      const charactersData = charactersToCreate.map(character => ({
        name: character.name,
        description: character.recommended_config.description,
        type: character.recommended_config.type,
        quality: character.recommended_config.quality,
        status: character.recommended_config.status,
        color: character.recommended_config.color,
        book_id: selectedBook.value.id
      }))

      const response = await charactersAPI.batchCreateCharacters(charactersData)

      if (response.success) {
        createdCharacters.value = response.data || []
        discoveryStep.value = 4
        message.success(`成功创建 ${createdCharacters.value.length} 个角色`)
      } else {
        throw new Error(response.message || '创建角色失败')
      }
    } catch (error) {
      console.error('创建角色失败:', error)
      message.error('创建角色失败，请重试')
    } finally {
      creatingCharacters.value = false
    }
  }

  const startSmartDiscovery = async () => {
    discoveryStep.value = 0
    selectedBook.value = null
    selectedChapters.value = []
    newCharacters.value = []
    selectedConfigs.value = []
    analysisStatus.value = 'normal'
    analysisText.value = ''
    await loadBooks()
  }

  const nextStep = () => {
    if (discoveryStep.value < discoverySteps.value.length - 1) {
      discoveryStep.value++
    }
  }

  const prevStep = () => {
    if (discoveryStep.value > 0) {
      discoveryStep.value--
    }
  }

  const toggleChapterSelection = (chapter) => {
    const index = selectedChapters.value.findIndex(c => c.id === chapter.id)
    if (index > -1) {
      selectedChapters.value.splice(index, 1)
    } else {
      selectedChapters.value.push(chapter)
    }
    updateChapterCheckState()
  }

  const toggleAllChapters = () => {
    if (chapterCheckAll.value) {
      selectedChapters.value = []
    } else {
      selectedChapters.value = [...availableChapters.value]
    }
    updateChapterCheckState()
  }

  const updateChapterCheckState = () => {
    const checkedCount = selectedChapters.value.length
    const totalCount = availableChapters.value.length

    chapterCheckAll.value = checkedCount === totalCount && totalCount > 0
    chapterIndeterminate.value = checkedCount > 0 && checkedCount < totalCount
  }

  const onCheckAllConfigs = (e) => {
    const charactersToCreate = newCharacters.value.filter(char => !char.exists_in_library)
    
    if (e.target.checked) {
      selectedConfigs.value = charactersToCreate.map(char => char.name)
    } else {
      selectedConfigs.value = []
    }
    
    updateConfigCheckState()
  }

  const getCreationSummary = () => {
    const total = createdCharacters.value.length
    const active = createdCharacters.value.filter(c => c.status === 'active').length
    const withAudio = createdCharacters.value.filter(c => c.hasAudio).length
    const withLatent = createdCharacters.value.filter(c => c.hasLatent).length

    let summary = `已成功创建 ${total} 个角色。`
    if (active > 0) {
      summary += ` 其中 ${active} 个角色已激活可用。`
    }
    if (withAudio > 0) {
      summary += ` ${withAudio} 个角色已上传音频文件。`
    }
    if (withLatent > 0) {
      summary += ` ${withLatent} 个角色已上传Latent文件。`
    }
    if (total - active > 0) {
      summary += ` 剩余 ${total - active} 个角色需要上传音频文件才能使用。`
    }

    return summary
  }

  const resetDiscoveryState = () => {
    discoveryStep.value = 0
    selectedBook.value = null
    selectedChapters.value = []
    newCharacters.value = []
    selectedConfigs.value = []
    analysisStatus.value = 'normal'
    analysisText.value = ''
    createdCharacters.value = []
  }

  return {
    // 状态
    discoveryStep,
    discoverySteps,
    booksData,
    chaptersData,
    chaptersLoading,
    selectedBook,
    availableChapters,
    selectedChapters,
    loadingChapters,
    chapterCheckAll,
    chapterIndeterminate,
    analysisStatus,
    analysisText,
    newCharacters,
    selectedConfigs,
    configCheckAll,
    configIndeterminate,
    creatingCharacters,
    createdCharacters,
    mainCharactersCount,

    // 方法
    loadBooks,
    selectBook,
    loadChapters,
    analyzeCharacters,
    processAnalysisResult,
    checkCharacterExistence,
    prepareCharacterConfigs,
    updateConfigCheckState,
    createCharacters,
    startSmartDiscovery,
    nextStep,
    prevStep,
    toggleChapterSelection,
    toggleAllChapters,
    updateChapterCheckState,
    onCheckAllConfigs,
    getCreationSummary,
    resetDiscoveryState
  }
} 