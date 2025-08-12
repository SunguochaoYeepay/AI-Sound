import { ref, reactive, nextTick } from 'vue'
import { message } from 'ant-design-vue'
import { charactersAPI } from '@/api'

export function useCharacters() {
  // 响应式数据
  const voiceLibrary = ref([])
  const loading = ref(false)
  const selectedVoice = ref(null)
  const selectedCharacterIds = ref([])

  // 分页配置
  const pagination = reactive({
    current: 1,
    pageSize: 20,
    total: 0,
    showSizeChanger: true,
    showQuickJumper: true,
    showTotal: (total, range) => `第 ${range[0]}-${range[1]} 条，共 ${total} 条`
  })

  // 筛选条件
  const searchQuery = ref('')
  const typeFilter = ref('')
  const statusFilter = ref('')
  const avatarFilter = ref('')
  const audioFilter = ref('')
  const selectedBookId = ref('')

  // 加载角色数据
  const loadVoiceLibrary = async () => {
    try {
      loading.value = true

      // 构建API参数
      const apiParams = {
        page: pagination.current,
        page_size: pagination.pageSize
      }

      // 添加筛选条件
      if (searchQuery.value) apiParams.search = searchQuery.value
      if (typeFilter.value) apiParams.voice_type = typeFilter.value
      if (statusFilter.value) apiParams.status = statusFilter.value
      if (selectedBookId.value) apiParams.book_id = selectedBookId.value
      if (avatarFilter.value) apiParams.avatar_filter = avatarFilter.value
      if (audioFilter.value) apiParams.audio_filter = audioFilter.value

      // 调试日志
      console.log('🔍 音频筛选调试:', {
        audioFilter: audioFilter.value,
        apiParams: apiParams
      })

      const response = await charactersAPI.getCharacters(apiParams)

      // axios响应的实际数据在response.data中
      const responseData = response.data

      // 🔧 调试：打印API响应数据结构
      console.log('🔍 API响应数据结构:', {
        hasSuccess: 'success' in responseData,
        success: responseData.success,
        hasData: 'data' in responseData,
        hasCharacters: 'characters' in responseData,
        dataKeys: Object.keys(responseData)
      })

      // 🔧 修复：支持多种API响应格式
      let data = null
      let total = 0

      if (responseData && responseData.success && responseData.data) {
        // 格式1: {success: true, data: [...], pagination: {...}}
        data = responseData.data
        total = responseData.pagination?.total || data.length
      } else if (responseData && responseData.characters) {
        // 格式2: {characters: [...], total: 63, page: 1, size: 20, has_next: true}
        data = responseData.characters
        total = responseData.total || data.length
      } else if (Array.isArray(responseData)) {
        // 格式3: 直接是数组
        data = responseData
        total = data.length
      }

      if (data && Array.isArray(data)) {
        // 🔧 调试：打印API响应数据
        console.log('🔍 API响应数据:', {
          dataLength: data.length,
          total: total,
          firstItem: data[0]
        })
        
        // 更新分页总数
        pagination.total = total

        // 统一处理角色数据
        voiceLibrary.value = data.map((character) => {
          // 🔧 调试：打印角色数据映射
          console.log(`🔍 角色数据映射 - ${character.name}:`, {
            id: character.id,
            status: character.status,
            is_voice_configured: character.is_voice_configured,
            reference_audio_path: character.reference_audio_path,
            latent_file_path: character.latent_file_path,
            avatar_path: character.avatar_path,
            referenceAudioUrl: character.referenceAudioUrl,
            latentFileUrl: character.latentFileUrl,
            avatarUrl: character.avatarUrl
          })
          
          return {
            id: character.id,
            name: character.name,
            description: character.description || '暂无描述',
            type: character.voice_type || 'custom',
            quality: character.quality_score || 0,
            status: character.status || 'unconfigured',
            color: character.color || '#8b5cf6',
            usageCount: character.usage_count || 0,
            // 🔧 修复：正确映射音频相关字段
            audioUrl: character.referenceAudioUrl || '',
            referenceAudioUrl: character.referenceAudioUrl || '',
            reference_audio_path: character.reference_audio_path || null, // 保留原始路径
            latentFileUrl: character.latentFileUrl || '',
            latent_file_path: character.latent_file_path || null, // 保留原始路径
            // 🔧 修复：正确映射头像相关字段，添加缓存破坏参数
            avatarUrl: character.avatarUrl ? `${character.avatarUrl}?t=${Date.now()}` : null,
            avatar_path: character.avatar_path || null, // 保留原始路径
            book: character.book,
            book_id: character.book_id,
            chapter_id: character.chapter_id,
            voice_parameters: character.voice_parameters || {
              time_step: 20,
              p_weight: 1.0,
              t_weight: 1.0
            },
            params: character.voice_parameters || {
              // 🔧 修复：添加params别名以兼容模板
              timeStep: character.voice_parameters?.time_step || 20,
              pWeight: character.voice_parameters?.p_weight || 1.0,
              tWeight: character.voice_parameters?.t_weight || 1.0
            },
            tags: character.tags || [],
            createdAt: character.created_at ? character.created_at.split('T')[0] : '',
            isCharacter: true,
            is_voice_configured: character.is_voice_configured || false
          }
        })
        
        // 🔧 调试：打印更新后的数据状态
        console.log('🔍 数据更新完成:', {
          voiceLibraryLength: voiceLibrary.value.length,
          firstCharacter: voiceLibrary.value[0]?.name,
          lastCharacter: voiceLibrary.value[voiceLibrary.value.length - 1]?.name
        })
        
        // 🔧 强制触发响应式更新
        await nextTick()
        console.log('🔍 响应式更新完成，当前列表长度:', voiceLibrary.value.length)
      } else {
        // 🔧 调试：打印错误情况
        console.error('🔍 数据处理失败:', {
          responseData: responseData,
          hasData: !!data,
          isArray: Array.isArray(data)
        })
        const errorMsg = responseData?.message || '数据格式错误'
        message.error('加载数据失败：' + errorMsg)
        voiceLibrary.value = []
      }
    } catch (error) {
      console.error('加载数据错误:', error)
      const errorMsg = error.response?.data?.message || error.message || '网络连接错误'
      message.error('加载数据失败：' + errorMsg)
      voiceLibrary.value = []
    } finally {
      loading.value = false
    }
  }

  // 选择角色
  const selectVoice = (voice) => {
    selectedVoice.value = voice
    // 注意：这里不设置 showDetailDrawer，由父组件处理
  }

  // 批量选择角色
  const handleCharacterSelection = (characterId, checked) => {
    if (checked) {
      selectedCharacterIds.value.push(characterId)
    } else {
      const index = selectedCharacterIds.value.indexOf(characterId)
      if (index > -1) {
        selectedCharacterIds.value.splice(index, 1)
      }
    }
  }

  // 全选角色
  const selectAllCharacters = () => {
    selectedCharacterIds.value = voiceLibrary.value.map(character => character.id)
  }

  // 清空选择
  const clearCharacterSelection = () => {
    selectedCharacterIds.value = []
  }

  // 重置筛选条件
  const resetFilters = () => {
    searchQuery.value = ''
    typeFilter.value = ''
    statusFilter.value = ''
    avatarFilter.value = ''
    audioFilter.value = ''
    selectedBookId.value = ''
    pagination.current = 1
  }

  // 分页变化处理
  const handlePaginationChange = (page, pageSize) => {
    pagination.current = page
    pagination.pageSize = pageSize
    loadVoiceLibrary()
  }

  return {
    // 数据
    voiceLibrary,
    loading,
    selectedVoice,
    selectedCharacterIds,
    pagination,
    
    // 筛选条件
    searchQuery,
    typeFilter,
    statusFilter,
    avatarFilter,
    audioFilter,
    selectedBookId,
    
    // 方法
    loadVoiceLibrary,
    selectVoice,
    handleCharacterSelection,
    selectAllCharacters,
    clearCharacterSelection,
    resetFilters,
    handlePaginationChange
  }
}