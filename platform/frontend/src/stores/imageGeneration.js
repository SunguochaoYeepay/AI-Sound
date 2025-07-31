import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { imageGenerationAPI } from '../api/v2.js'

export const useImageGenerationStore = defineStore('imageGeneration', () => {
  // State
  const imageTasks = ref([])
  const imagePresets = ref([])
  const generationStats = ref({})
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const totalTasks = computed(() => imageTasks.value.length)
  const completedTasks = computed(() => 
    imageTasks.value.filter(task => task.status === 'completed').length
  )
  const pendingTasks = computed(() => 
    imageTasks.value.filter(task => task.status === 'pending').length
  )
  const processingTasks = computed(() => 
    imageTasks.value.filter(task => task.status === 'processing').length
  )
  const failedTasks = computed(() => 
    imageTasks.value.filter(task => task.status === 'failed').length
  )

  // Actions
  const createImageTasks = async (data) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.createImageTasks(data)
      
      if (response.success) {
        return response
      } else {
        throw new Error(response.message || '创建图片生成任务失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const generateSingleImage = async (taskId) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.generateSingleImage(taskId)
      
      if (response.success) {
        // 更新本地任务状态
        const taskIndex = imageTasks.value.findIndex(task => task.id === taskId)
        if (taskIndex !== -1) {
          imageTasks.value[taskIndex].status = 'processing'
        }
        return response
      } else {
        throw new Error(response.message || '启动图片生成失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const batchGenerateImages = async (data) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.batchGenerateImages(data)
      
      if (response.success) {
        return response
      } else {
        throw new Error(response.message || '批量生成失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getChapterImageStatus = async (chapterId) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.getChapterImageStatus(chapterId)
      
      // 详细调试API响应结构
      console.log('🏪 Store收到API响应:', response)
      console.log('🏪 response.success:', response.success)
      console.log('🏪 response.data:', response.data)
      console.log('🏪 response.data?.tasks:', response.data?.tasks)
      console.log('🏪 response.data?.tasks length:', response.data?.tasks?.length)
      
      if (response.success) {
        // 修复：API响应结构是 response.data.data，实际任务数据在 response.data.data.tasks
        const actualData = response.data?.data || response.data || {}
        const tasks = actualData?.tasks || []
        const stats = actualData || {}
        
        console.log('🏪 准备设置 imageTasks:', tasks)
        console.log('🏪 准备设置 generationStats:', stats)
        
        imageTasks.value = tasks
        generationStats.value = stats
        
        console.log('🏪 设置后 imageTasks.value:', imageTasks.value)
        console.log('🏪 设置后 imageTasks.value length:', imageTasks.value.length)
        console.log('🏪 设置后 generationStats.value:', generationStats.value)
        
        return response
      } else {
        throw new Error(response.message || '获取章节图片状态失败')
      }
    } catch (err) {
      console.error('🏪 Store错误:', err)
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getImageTask = async (taskId) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.getImageTask(taskId)
      
      if (response.success) {
        return response
      } else {
        throw new Error(response.message || '获取任务详情失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const rateImageTask = async (taskId, rating) => {
    try {
      loading.value = true
      error.value = null
      
              const response = await imageGenerationAPI.rateImageTask(taskId, rating)
      
      if (response.success) {
        // 更新本地任务数据
        const taskIndex = imageTasks.value.findIndex(task => task.id === taskId)
        if (taskIndex !== -1) {
          imageTasks.value[taskIndex].user_rating = rating
        }
        return response
      } else {
        throw new Error(response.message || '评分失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const approveImageTask = async (taskId, approved) => {
    try {
      loading.value = true
      error.value = null
      
              const response = await imageGenerationAPI.approveImageTask(taskId, approved)
      
      if (response.success) {
        // 更新本地任务数据
        const taskIndex = imageTasks.value.findIndex(task => task.id === taskId)
        if (taskIndex !== -1) {
          imageTasks.value[taskIndex].is_approved = approved
        }
        return response
      } else {
        throw new Error(response.message || '审核失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const updateTaskPrompt = async (taskId, promptData) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.updateTaskPrompt(taskId, promptData)
      
      if (response.success) {
        // 更新本地任务数据
        const taskIndex = imageTasks.value.findIndex(task => task.id === taskId)
        if (taskIndex !== -1) {
          if (promptData.original_prompt !== undefined) {
            imageTasks.value[taskIndex].original_prompt = promptData.original_prompt
          }
          if (promptData.generated_prompt !== undefined) {
            imageTasks.value[taskIndex].generated_prompt = promptData.generated_prompt
          }
        }
        return response
      } else {
        throw new Error(response.message || '更新提示词失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const deleteImageTask = async (taskId) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.deleteImageTask(taskId)
      
      if (response.success) {
        // 从本地列表中移除
        imageTasks.value = imageTasks.value.filter(task => task.id !== taskId)
        return response
      } else {
        throw new Error(response.message || '删除任务失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getImagePresets = async (category = null) => {
    try {
      loading.value = true
      error.value = null
      
      const params = category ? { category } : {}
      const response = await imageGenerationAPI.getImagePresets(params)
      
      if (response.success) {
        imagePresets.value = response.data?.presets || []
        return response
      } else {
        throw new Error(response.message || '获取预设列表失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const createImagePreset = async (data) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.createImagePreset(data)
      
      if (response.success) {
        // 添加到本地列表
        imagePresets.value.push(response.data)
        return response
      } else {
        throw new Error(response.message || '创建预设失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const testComfyuiConnection = async () => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.testComfyuiConnection()
      
      return response
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const getComfyuiModels = async () => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.getComfyuiModels()
      
      if (response.success) {
        return response
      } else {
        throw new Error(response.message || '获取模型列表失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  const clearError = () => {
    error.value = null
  }

  const resetState = () => {
    imageTasks.value = []
    imagePresets.value = []
    generationStats.value = {}
    error.value = null
  }

  // 🔥 新增：角色搜索功能
  const searchCharacters = async (params) => {
    try {
      loading.value = true
      error.value = null
      
      const response = await imageGenerationAPI.searchCharacters(params)
      
      if (response.success) {
        return response
      } else {
        throw new Error(response.message || '搜索角色失败')
      }
    } catch (err) {
      error.value = err.message
      throw err
    } finally {
      loading.value = false
    }
  }

  return {
    // State
    imageTasks,
    imagePresets,
    generationStats,
    loading,
    error,
    
    // Getters
    totalTasks,
    completedTasks,
    pendingTasks,
    processingTasks,
    failedTasks,
    
    // Actions
    createImageTasks,
    generateSingleImage,
    batchGenerateImages,
    getChapterImageStatus,
    getImageTask,
    rateImageTask,
    approveImageTask,
    updateTaskPrompt,
    deleteImageTask,
    getImagePresets,
    createImagePreset,
    testComfyuiConnection,
    getComfyuiModels,
    searchCharacters, // 🔥 新增
    clearError,
    resetState
  }
})