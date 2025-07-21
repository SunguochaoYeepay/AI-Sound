/**
 * 音频合成状态管理
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { synthesisAPI } from '../api/v2.js'

export const useSynthesisStore = defineStore('synthesis', () => {
  // 合成任务
  const tasks = ref([])
  const currentTask = ref(null)
  const tasksLoading = ref(false)

  // 合成进度
  const synthesisProgress = ref({})

  // 音频文件
  const audioFiles = ref({}) // 按taskId分组

  // 计算属性
  const activeTasks = computed(() => tasks.value.filter((t) => t.status === 'running'))

  const completedTasks = computed(() => tasks.value.filter((t) => t.status === 'completed'))

  const hasActiveTasks = computed(() => activeTasks.value.length > 0)

  const taskCount = computed(() => tasks.value.length)

  // 获取合成任务列表
  const fetchTasks = async (params = {}) => {
    tasksLoading.value = true
    try {
      const result = await synthesisAPI.getTasks(params)
      if (result.success) {
        tasks.value = result.data.items || result.data || []
      }
      return result
    } finally {
      tasksLoading.value = false
    }
  }

  // 获取合成任务详情
  const fetchTask = async (taskId) => {
    const result = await synthesisAPI.getTask(taskId)
    if (result.success) {
      currentTask.value = result.data

      // 更新本地任务列表中的对应项
      const index = tasks.value.findIndex((t) => t.id === taskId)
      if (index > -1) {
        tasks.value[index] = result.data
      }
    }
    return result
  }

  // 创建合成任务
  const createTask = async (taskData) => {
    const result = await synthesisAPI.createTask(taskData)
    if (result.success) {
      tasks.value.unshift(result.data)
      currentTask.value = result.data
    }
    return result
  }

  // 开始合成
  const startSynthesis = async (taskId) => {
    const result = await synthesisAPI.startSynthesis(taskId)
    if (result.success) {
      // 更新任务状态
      updateTaskStatus(taskId, 'running')

      // 初始化进度
      synthesisProgress.value[taskId] = {
        totalChapters: 0,
        completedChapters: 0,
        currentChapter: null,
        progress: 0,
        message: '正在初始化合成...'
      }
    }
    return result
  }

  // 停止合成
  const stopSynthesis = async (taskId) => {
    const result = await synthesisAPI.stopSynthesis(taskId)
    if (result.success) {
      updateTaskStatus(taskId, 'stopped')
      delete synthesisProgress.value[taskId]
    }
    return result
  }

  // 获取音频文件
  const fetchAudioFiles = async (taskId) => {
    const result = await synthesisAPI.getAudioFiles(taskId)
    if (result.success) {
      audioFiles.value[taskId] = result.data || []
    }
    return result
  }

  // 下载音频文件
  const downloadAudio = async (taskId, fileId) => {
    const result = await synthesisAPI.downloadAudio(taskId, fileId)
    if (result.success) {
      // 创建下载链接
      const blob = new Blob([result.data])
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.download = `audio_${fileId}.mp3`
      document.body.appendChild(link)
      link.click()
      document.body.removeChild(link)
      window.URL.revokeObjectURL(url)
    }
    return result
  }

  // 更新任务状态
  const updateTaskStatus = (taskId, status) => {
    const task = tasks.value.find((t) => t.id === taskId)
    if (task) {
      task.status = status
      task.updated_at = new Date().toISOString()
    }

    if (currentTask.value?.id === taskId) {
      currentTask.value.status = status
      currentTask.value.updated_at = new Date().toISOString()
    }
  }

  // 更新合成进度
  const updateProgress = (taskId, progress) => {
    synthesisProgress.value[taskId] = {
      ...synthesisProgress.value[taskId],
      ...progress
    }

    // 同时更新任务的进度字段
    const task = tasks.value.find((t) => t.id === taskId)
    if (task) {
      task.progress = progress.progress || 0
    }

    if (currentTask.value?.id === taskId) {
      currentTask.value.progress = progress.progress || 0
    }
  }

  // 删除合成任务
  const removeTask = (taskId) => {
    const index = tasks.value.findIndex((t) => t.id === taskId)
    if (index > -1) {
      tasks.value.splice(index, 1)
    }

    if (currentTask.value?.id === taskId) {
      currentTask.value = null
    }

    // 清理相关数据
    delete synthesisProgress.value[taskId]
    delete audioFiles.value[taskId]
  }

  // 获取任务进度
  const getTaskProgress = (taskId) => {
    return (
      synthesisProgress.value[taskId] || {
        totalChapters: 0,
        completedChapters: 0,
        progress: 0,
        message: '等待开始...'
      }
    )
  }

  // 获取任务音频文件
  const getTaskAudioFiles = (taskId) => {
    return audioFiles.value[taskId] || []
  }

  return {
    // 状态
    tasks,
    currentTask,
    tasksLoading,
    synthesisProgress,
    audioFiles,

    // 计算属性
    activeTasks,
    completedTasks,
    hasActiveTasks,
    taskCount,

    // 方法
    fetchTasks,
    fetchTask,
    createTask,
    startSynthesis,
    stopSynthesis,
    fetchAudioFiles,
    downloadAudio,
    updateTaskStatus,
    updateProgress,
    removeTask,
    getTaskProgress,
    getTaskAudioFiles
  }
})
