import { ref, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'

/**
 * WebWorker管理器
 * 负责Worker的创建、任务分发、结果处理和性能优化
 */
export function useWorkerManager(options = {}) {
  const {
    maxWorkers = navigator.hardwareConcurrency || 4,
    workerTimeout = 30000, // 30秒超时
    enablePooling = true, // 启用Worker池
    enableRetry = true, // 启用重试机制
    maxRetries = 3
  } = options
  
  // 状态管理
  const workers = ref([])
  const taskQueue = ref([])
  const activeTasks = ref(new Map())
  const workerStats = ref({
    totalTasks: 0,
    completedTasks: 0,
    failedTasks: 0,
    averageProcessTime: 0
  })
  
  // Worker池管理
  const availableWorkers = ref([])
  const busyWorkers = ref([])
  
  // 任务ID生成器
  let taskIdCounter = 0
  const generateTaskId = () => `task_${Date.now()}_${++taskIdCounter}`
  
  // 创建Worker
  const createWorker = () => {
    try {
      const worker = new Worker('/src/workers/audioProcessor.js', { type: 'module' })
      const workerId = `worker_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`
      
      const workerInstance = {
        id: workerId,
        worker,
        busy: false,
        currentTask: null,
        createdAt: Date.now(),
        completedTasks: 0,
        totalProcessTime: 0
      }
      
      // 监听Worker消息
      worker.onmessage = (event) => {
        handleWorkerMessage(workerInstance, event)
      }
      
      // 监听Worker错误
      worker.onerror = (error) => {
        console.error(`Worker ${workerId} error:`, error)
        handleWorkerError(workerInstance, error)
      }
      
      // 监听Worker终止
      worker.onmessageerror = (error) => {
        console.error(`Worker ${workerId} message error:`, error)
        handleWorkerError(workerInstance, error)
      }
      
      workers.value.push(workerInstance)
      availableWorkers.value.push(workerInstance)
      
      return workerInstance
    } catch (error) {
      console.error('创建Worker失败:', error)
      message.error('创建后台处理器失败')
      return null
    }
  }
  
  // 初始化Worker池
  const initWorkerPool = () => {
    if (!enablePooling) return
    
    for (let i = 0; i < Math.min(maxWorkers, 2); i++) {
      createWorker()
    }
  }
  
  // 获取可用Worker
  const getAvailableWorker = () => {
    if (availableWorkers.value.length > 0) {
      return availableWorkers.value.shift()
    }
    
    if (workers.value.length < maxWorkers) {
      return createWorker()
    }
    
    return null
  }
  
  // 释放Worker
  const releaseWorker = (workerInstance) => {
    workerInstance.busy = false
    workerInstance.currentTask = null
    
    // 从忙碌列表移除
    const busyIndex = busyWorkers.value.findIndex(w => w.id === workerInstance.id)
    if (busyIndex !== -1) {
      busyWorkers.value.splice(busyIndex, 1)
    }
    
    // 添加到可用列表
    if (!availableWorkers.value.find(w => w.id === workerInstance.id)) {
      availableWorkers.value.push(workerInstance)
    }
    
    // 处理队列中的下一个任务
    processQueue()
  }
  
  // 处理Worker消息
  const handleWorkerMessage = (workerInstance, event) => {
    const { type, result } = event.data
    const task = activeTasks.value.get(result.taskId)
    
    if (!task) {
      console.warn(`未找到任务 ${result.taskId}`)
      return
    }
    
    // 清除超时定时器
    if (task.timeoutId) {
      clearTimeout(task.timeoutId)
    }
    
    // 更新统计信息
    const processingTime = Date.now() - task.startTime
    workerInstance.completedTasks++
    workerInstance.totalProcessTime += processingTime
    
    workerStats.value.completedTasks++
    workerStats.value.averageProcessTime = 
      (workerStats.value.averageProcessTime * (workerStats.value.completedTasks - 1) + processingTime) / 
      workerStats.value.completedTasks
    
    // 处理结果
    if (result.success) {
      task.resolve(result.data)
    } else {
      if (enableRetry && task.retryCount < maxRetries) {
        // 重试任务
        task.retryCount++
        console.warn(`任务 ${result.taskId} 失败，正在重试 (${task.retryCount}/${maxRetries})`)
        
        setTimeout(() => {
          executeTask(task)
        }, 1000 * task.retryCount) // 指数退避
      } else {
        workerStats.value.failedTasks++
        task.reject(new Error(result.error || '任务执行失败'))
      }
    }
    
    // 清理任务
    activeTasks.value.delete(result.taskId)
    releaseWorker(workerInstance)
  }
  
  // 处理Worker错误
  const handleWorkerError = (workerInstance, error) => {
    console.error(`Worker ${workerInstance.id} 发生错误:`, error)
    
    // 处理当前任务
    if (workerInstance.currentTask) {
      const task = workerInstance.currentTask
      
      if (enableRetry && task.retryCount < maxRetries) {
        task.retryCount++
        taskQueue.value.unshift(task) // 重新加入队列头部
      } else {
        workerStats.value.failedTasks++
        task.reject(new Error('Worker执行错误'))
        activeTasks.value.delete(task.id)
      }
    }
    
    // 重启Worker
    restartWorker(workerInstance)
  }
  
  // 重启Worker
  const restartWorker = (workerInstance) => {
    try {
      // 终止旧Worker
      workerInstance.worker.terminate()
      
      // 从所有列表中移除
      const workerIndex = workers.value.findIndex(w => w.id === workerInstance.id)
      if (workerIndex !== -1) {
        workers.value.splice(workerIndex, 1)
      }
      
      const availableIndex = availableWorkers.value.findIndex(w => w.id === workerInstance.id)
      if (availableIndex !== -1) {
        availableWorkers.value.splice(availableIndex, 1)
      }
      
      const busyIndex = busyWorkers.value.findIndex(w => w.id === workerInstance.id)
      if (busyIndex !== -1) {
        busyWorkers.value.splice(busyIndex, 1)
      }
      
      // 创建新Worker
      if (enablePooling) {
        createWorker()
      }
    } catch (error) {
      console.error('重启Worker失败:', error)
    }
  }
  
  // 执行任务
  const executeTask = (task) => {
    const worker = getAvailableWorker()
    
    if (!worker) {
      // 没有可用Worker，加入队列
      taskQueue.value.push(task)
      return
    }
    
    // 标记Worker为忙碌
    worker.busy = true
    worker.currentTask = task
    busyWorkers.value.push(worker)
    
    // 设置超时
    task.timeoutId = setTimeout(() => {
      console.error(`任务 ${task.id} 超时`)
      workerStats.value.failedTasks++
      task.reject(new Error('任务执行超时'))
      activeTasks.value.delete(task.id)
      releaseWorker(worker)
    }, workerTimeout)
    
    // 发送任务到Worker
    task.startTime = Date.now()
    activeTasks.value.set(task.id, task)
    
    try {
      worker.worker.postMessage({
        type: task.type,
        data: task.data,
        taskId: task.id
      })
    } catch (error) {
      console.error('发送任务到Worker失败:', error)
      task.reject(error)
      activeTasks.value.delete(task.id)
      releaseWorker(worker)
    }
  }
  
  // 处理任务队列
  const processQueue = () => {
    while (taskQueue.value.length > 0 && availableWorkers.value.length > 0) {
      const task = taskQueue.value.shift()
      executeTask(task)
    }
  }
  
  // 提交任务
  const submitTask = (type, data, options = {}) => {
    return new Promise((resolve, reject) => {
      const task = {
        id: generateTaskId(),
        type,
        data,
        options,
        resolve,
        reject,
        retryCount: 0,
        createdAt: Date.now()
      }
      
      workerStats.value.totalTasks++
      executeTask(task)
    })
  }
  
  // 批量提交任务
  const submitBatchTasks = async (tasks) => {
    const promises = tasks.map(task => 
      submitTask(task.type, task.data, task.options)
    )
    
    try {
      const results = await Promise.all(promises)
      return { success: true, results }
    } catch (error) {
      return { success: false, error: error.message }
    }
  }
  
  // 取消任务
  const cancelTask = (taskId) => {
    const task = activeTasks.value.get(taskId)
    if (task) {
      if (task.timeoutId) {
        clearTimeout(task.timeoutId)
      }
      task.reject(new Error('任务已取消'))
      activeTasks.value.delete(taskId)
      
      // 释放Worker
      const worker = busyWorkers.value.find(w => w.currentTask?.id === taskId)
      if (worker) {
        releaseWorker(worker)
      }
    }
    
    // 从队列中移除
    const queueIndex = taskQueue.value.findIndex(t => t.id === taskId)
    if (queueIndex !== -1) {
      taskQueue.value.splice(queueIndex, 1)
    }
  }
  
  // 清空队列
  const clearQueue = () => {
    taskQueue.value.forEach(task => {
      task.reject(new Error('队列已清空'))
    })
    taskQueue.value = []
  }
  
  // 获取性能统计
  const getStats = () => {
    return {
      ...workerStats.value,
      activeWorkers: workers.value.length,
      availableWorkers: availableWorkers.value.length,
      busyWorkers: busyWorkers.value.length,
      queueLength: taskQueue.value.length,
      activeTasks: activeTasks.value.size,
      workerDetails: workers.value.map(w => ({
        id: w.id,
        busy: w.busy,
        completedTasks: w.completedTasks,
        averageTime: w.completedTasks > 0 ? w.totalProcessTime / w.completedTasks : 0,
        uptime: Date.now() - w.createdAt
      }))
    }
  }
  
  // 清理资源
  const cleanup = () => {
    // 取消所有活动任务
    activeTasks.value.forEach((task, taskId) => {
      cancelTask(taskId)
    })
    
    // 清空队列
    clearQueue()
    
    // 终止所有Worker
    workers.value.forEach(workerInstance => {
      try {
        workerInstance.worker.terminate()
      } catch (error) {
        console.error('终止Worker失败:', error)
      }
    })
    
    // 清空状态
    workers.value = []
    availableWorkers.value = []
    busyWorkers.value = []
    activeTasks.value.clear()
  }
  
  // 生命周期管理
  onUnmounted(() => {
    cleanup()
  })
  
  // 初始化
  initWorkerPool()
  
  // 导出的API方法
  return {
    // 任务提交
    submitTask,
    submitBatchTasks,
    
    // 任务管理
    cancelTask,
    clearQueue,
    
    // 统计信息
    getStats,
    workerStats,
    
    // 便捷方法
    decodeAudio: (arrayBuffer) => submitTask('decode_audio', { arrayBuffer }),
    generateWaveform: (channelData, options) => submitTask('generate_waveform', { channelData, options }),
    calculatePeaks: (channelData, options) => submitTask('calculate_peaks', { channelData, options }),
    normalizeAudio: (channelData, targetLevel) => submitTask('normalize_audio', { channelData, targetLevel }),
    applyFade: (channelData, options) => submitTask('apply_fade', { channelData, options }),
    mixTracks: (tracks, options) => submitTask('mix_tracks', { tracks, options }),
    
    // 资源管理
    cleanup
  }
} 