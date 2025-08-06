import { ref } from 'vue'
import { message } from 'ant-design-vue'
import { charactersAPI } from '@/api'

export function useBatchConfig() {
  // 批量配置状态
  const showBatchConfigModal = ref(false)
  const batchConfigStep = ref(1) // 1: 选择角色, 2: 配置文件
  const batchConfigData = ref({
    audioFile: null,
    audioFileList: [],
    npyFile: null,
    npyFileList: [],
    avatarFile: null,
    avatarFileList: [],
    applyToAll: {
      audio: false,
      npy: false,
      avatar: false
    }
  })
  const batchConfigLoading = ref(false)

  // 方法
  const openBatchConfigModal = () => {
    showBatchConfigModal.value = true
    batchConfigStep.value = 1
    resetBatchConfigData()
  }

  const closeBatchConfigModal = () => {
    showBatchConfigModal.value = false
    batchConfigStep.value = 1
    resetBatchConfigData()
  }

  const goToBatchConfigStep = (step) => {
    batchConfigStep.value = step
  }

  const resetBatchConfigData = () => {
    batchConfigData.value = {
      audioFile: null,
      audioFileList: [],
      npyFile: null,
      npyFileList: [],
      avatarFile: null,
      avatarFileList: [],
      applyToAll: {
        audio: false,
        npy: false,
        avatar: false
      }
    }
  }

  const handleBatchAudioChange = (info) => {
    if (info.fileList.length > 0) {
      const file = info.fileList[0].originFileObj
      batchConfigData.value.audioFile = file
      batchConfigData.value.audioFileList = info.fileList
    } else {
      batchConfigData.value.audioFile = null
      batchConfigData.value.audioFileList = []
    }
  }

  const handleBatchNpyChange = (info) => {
    if (info.fileList.length > 0) {
      const file = info.fileList[0].originFileObj
      batchConfigData.value.npyFile = file
      batchConfigData.value.npyFileList = info.fileList
    } else {
      batchConfigData.value.npyFile = null
      batchConfigData.value.npyFileList = []
    }
  }

  const handleBatchAvatarChange = (info) => {
    if (info.fileList.length > 0) {
      const file = info.fileList[0].originFileObj
      batchConfigData.value.avatarFile = file
      batchConfigData.value.avatarFileList = info.fileList
    } else {
      batchConfigData.value.avatarFile = null
      batchConfigData.value.avatarFileList = []
    }
  }

  const executeBatchConfig = async (selectedCharacterIds, voiceLibrary) => {
    if (!voiceLibrary || !Array.isArray(voiceLibrary)) {
      message.error('角色库数据无效')
      return false
    }
    
    if (!selectedCharacterIds || !Array.isArray(selectedCharacterIds)) {
      message.warning('请选择要配置的角色')
      return false
    }
    
    const selectedCharacters = voiceLibrary.filter(v => selectedCharacterIds.includes(v.id))
    
    if (selectedCharacters.length === 0) {
      message.warning('请选择要配置的角色')
      return
    }

    const hasConfig = batchConfigData.value.applyToAll.audio || 
                     batchConfigData.value.applyToAll.npy || 
                     batchConfigData.value.applyToAll.avatar

    if (!hasConfig) {
      message.warning('请至少选择一种配置类型')
      return
    }

    try {
      batchConfigLoading.value = true

      for (const character of selectedCharacters) {
        const formData = new FormData()

        // 更新音频文件
        if (batchConfigData.value.applyToAll.audio && batchConfigData.value.audioFile) {
          formData.append('reference_audio', batchConfigData.value.audioFile)
        }

        // 更新NPY文件
        if (batchConfigData.value.applyToAll.npy && batchConfigData.value.npyFile) {
          formData.append('latent_file', batchConfigData.value.npyFile)
        }

        // 更新头像文件
        if (batchConfigData.value.applyToAll.avatar && batchConfigData.value.avatarFile) {
          formData.append('avatar', batchConfigData.value.avatarFile)
        }

        await charactersAPI.updateCharacter(character.id, formData)
      }

      message.success(`成功配置 ${selectedCharacters.length} 个角色`)
      closeBatchConfigModal()
      
      // 重新加载数据
      return true
    } catch (error) {
      console.error('批量配置失败:', error)
      message.error('批量配置失败，请重试')
      return false
    } finally {
      batchConfigLoading.value = false
    }
  }

  return {
    // 状态
    showBatchConfigModal,
    batchConfigStep,
    batchConfigData,
    batchConfigLoading,

    // 方法
    openBatchConfigModal,
    closeBatchConfigModal,
    goToBatchConfigStep,
    resetBatchConfigData,
    handleBatchAudioChange,
    handleBatchNpyChange,
    handleBatchAvatarChange,
    executeBatchConfig
  }
} 