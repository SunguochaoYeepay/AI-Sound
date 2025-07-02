import { ref, computed } from 'vue'
import { message } from 'ant-design-vue'

/**
 * 撤销重做系统
 * 支持音频编辑器的完整操作历史管理
 */
export function useUndoRedo(options = {}) {
  const {
    maxHistorySize = 100,
    enableBatching = true,
    batchTimeout = 1000
  } = options
  
  // 历史记录栈
  const history = ref([])
  const currentIndex = ref(-1)
  const batchTimer = ref(null)
  const currentBatch = ref([])
  
  // 计算属性
  const canUndo = computed(() => currentIndex.value >= 0)
  const canRedo = computed(() => currentIndex.value < history.value.length - 1)
  
  // 操作类型定义
  const ActionTypes = {
    // 轨道操作
    ADD_TRACK: 'add_track',
    DELETE_TRACK: 'delete_track',
    RENAME_TRACK: 'rename_track',
    REORDER_TRACK: 'reorder_track',
    MUTE_TRACK: 'mute_track',
    SOLO_TRACK: 'solo_track',
    CHANGE_TRACK_VOLUME: 'change_track_volume',
    CHANGE_TRACK_PAN: 'change_track_pan',
    
    // 音频片段操作
    ADD_CLIP: 'add_clip',
    DELETE_CLIP: 'delete_clip',
    MOVE_CLIP: 'move_clip',
    RESIZE_CLIP: 'resize_clip',
    SPLIT_CLIP: 'split_clip',
    MERGE_CLIPS: 'merge_clips',
    CHANGE_CLIP_VOLUME: 'change_clip_volume',
    CHANGE_CLIP_FADE: 'change_clip_fade',
    
    // 效果操作
    ADD_EFFECT: 'add_effect',
    REMOVE_EFFECT: 'remove_effect',
    CHANGE_EFFECT_PARAMS: 'change_effect_params',
    REORDER_EFFECTS: 'reorder_effects',
    
    // 标记和区域
    ADD_MARKER: 'add_marker',
    DELETE_MARKER: 'delete_marker',
    MOVE_MARKER: 'move_marker',
    ADD_REGION: 'add_region',
    DELETE_REGION: 'delete_region',
    MODIFY_REGION: 'modify_region',
    
    // 项目设置
    CHANGE_PROJECT_SETTINGS: 'change_project_settings',
    CHANGE_TIMELINE_ZOOM: 'change_timeline_zoom',
    CHANGE_PLAYHEAD_POSITION: 'change_playhead_position',
    
    // 批量操作
    BATCH: 'batch'
  }
  
  // 创建操作记录
  const createAction = (type, data, undoFn, redoFn) => {
    return {
      id: Date.now() + Math.random(),
      type,
      data: JSON.parse(JSON.stringify(data)), // 深拷贝数据
      timestamp: new Date(),
      undoFn,
      redoFn
    }
  }
  
  // 添加操作到历史记录
  const addAction = (type, data, undoFn, redoFn) => {
    const action = createAction(type, data, undoFn, redoFn)
    
    if (enableBatching && shouldBatch(type)) {
      addToBatch(action)
      return
    }
    
    pushToHistory(action)
  }
  
  // 判断是否应该批量处理
  const shouldBatch = (type) => {
    const batchableTypes = [
      ActionTypes.CHANGE_TRACK_VOLUME,
      ActionTypes.CHANGE_TRACK_PAN,
      ActionTypes.CHANGE_CLIP_VOLUME,
      ActionTypes.CHANGE_CLIP_FADE,
      ActionTypes.CHANGE_EFFECT_PARAMS,
      ActionTypes.MOVE_CLIP,
      ActionTypes.RESIZE_CLIP,
      ActionTypes.CHANGE_TIMELINE_ZOOM,
      ActionTypes.CHANGE_PLAYHEAD_POSITION
    ]
    return batchableTypes.includes(type)
  }
  
  // 添加到批处理
  const addToBatch = (action) => {
    currentBatch.value.push(action)
    
    // 清除之前的定时器
    if (batchTimer.value) {
      clearTimeout(batchTimer.value)
    }
    
    // 设置新的定时器
    batchTimer.value = setTimeout(() => {
      flushBatch()
    }, batchTimeout)
  }
  
  // 提交批处理
  const flushBatch = () => {
    if (currentBatch.value.length === 0) return
    
    if (currentBatch.value.length === 1) {
      // 单个操作直接添加
      pushToHistory(currentBatch.value[0])
    } else {
      // 多个操作创建批处理记录
      const batchAction = createAction(
        ActionTypes.BATCH,
        { actions: [...currentBatch.value] },
        () => {
          // 批量撤销：逆序执行所有撤销操作
          for (let i = currentBatch.value.length - 1; i >= 0; i--) {
            const action = currentBatch.value[i]
            if (action.undoFn) action.undoFn()
          }
        },
        () => {
          // 批量重做：正序执行所有重做操作
          for (const action of currentBatch.value) {
            if (action.redoFn) action.redoFn()
          }
        }
      )
      
      pushToHistory(batchAction)
    }
    
    currentBatch.value = []
    batchTimer.value = null
  }
  
  // 推送到历史记录
  const pushToHistory = (action) => {
    // 如果当前不在历史记录末尾，删除后面的记录
    if (currentIndex.value < history.value.length - 1) {
      history.value = history.value.slice(0, currentIndex.value + 1)
    }
    
    // 添加新的操作
    history.value.push(action)
    currentIndex.value = history.value.length - 1
    
    // 限制历史记录大小
    if (history.value.length > maxHistorySize) {
      history.value.shift()
      currentIndex.value--
    }
  }
  
  // 撤销操作
  const undo = () => {
    if (!canUndo.value) {
      message.warning('没有可撤销的操作')
      return false
    }
    
    // 先提交当前批处理
    flushBatch()
    
    const action = history.value[currentIndex.value]
    
    try {
      if (action.undoFn) {
        action.undoFn()
      }
      currentIndex.value--
      message.success(`撤销: ${getActionName(action.type)}`)
      return true
    } catch (error) {
      console.error('撤销操作失败:', error)
      message.error('撤销操作失败')
      return false
    }
  }
  
  // 重做操作
  const redo = () => {
    if (!canRedo.value) {
      message.warning('没有可重做的操作')
      return false
    }
    
    currentIndex.value++
    const action = history.value[currentIndex.value]
    
    try {
      if (action.redoFn) {
        action.redoFn()
      }
      message.success(`重做: ${getActionName(action.type)}`)
      return true
    } catch (error) {
      console.error('重做操作失败:', error)
      message.error('重做操作失败')
      currentIndex.value--
      return false
    }
  }
  
  // 获取操作名称
  const getActionName = (type) => {
    const names = {
      [ActionTypes.ADD_TRACK]: '添加轨道',
      [ActionTypes.DELETE_TRACK]: '删除轨道',
      [ActionTypes.RENAME_TRACK]: '重命名轨道',
      [ActionTypes.REORDER_TRACK]: '调整轨道顺序',
      [ActionTypes.MUTE_TRACK]: '静音轨道',
      [ActionTypes.SOLO_TRACK]: '独奏轨道',
      [ActionTypes.CHANGE_TRACK_VOLUME]: '调整轨道音量',
      [ActionTypes.CHANGE_TRACK_PAN]: '调整轨道声像',
      [ActionTypes.ADD_CLIP]: '添加音频片段',
      [ActionTypes.DELETE_CLIP]: '删除音频片段',
      [ActionTypes.MOVE_CLIP]: '移动音频片段',
      [ActionTypes.RESIZE_CLIP]: '调整片段大小',
      [ActionTypes.SPLIT_CLIP]: '分割音频片段',
      [ActionTypes.MERGE_CLIPS]: '合并音频片段',
      [ActionTypes.CHANGE_CLIP_VOLUME]: '调整片段音量',
      [ActionTypes.CHANGE_CLIP_FADE]: '调整淡入淡出',
      [ActionTypes.ADD_EFFECT]: '添加效果',
      [ActionTypes.REMOVE_EFFECT]: '移除效果',
      [ActionTypes.CHANGE_EFFECT_PARAMS]: '调整效果参数',
      [ActionTypes.REORDER_EFFECTS]: '调整效果顺序',
      [ActionTypes.ADD_MARKER]: '添加标记',
      [ActionTypes.DELETE_MARKER]: '删除标记',
      [ActionTypes.MOVE_MARKER]: '移动标记',
      [ActionTypes.ADD_REGION]: '添加区域',
      [ActionTypes.DELETE_REGION]: '删除区域',
      [ActionTypes.MODIFY_REGION]: '修改区域',
      [ActionTypes.CHANGE_PROJECT_SETTINGS]: '修改项目设置',
      [ActionTypes.CHANGE_TIMELINE_ZOOM]: '调整时间轴缩放',
      [ActionTypes.CHANGE_PLAYHEAD_POSITION]: '移动播放头',
      [ActionTypes.BATCH]: '批量操作'
    }
    return names[type] || type
  }
  
  // 清除历史记录
  const clearHistory = () => {
    flushBatch()
    history.value = []
    currentIndex.value = -1
    message.info('操作历史已清除')
  }
  
  // 获取历史记录信息
  const getHistoryInfo = () => {
    return {
      total: history.value.length,
      current: currentIndex.value + 1,
      canUndo: canUndo.value,
      canRedo: canRedo.value,
      nextUndo: canUndo.value ? getActionName(history.value[currentIndex.value].type) : null,
      nextRedo: canRedo.value ? getActionName(history.value[currentIndex.value + 1].type) : null
    }
  }
  
  // 获取历史记录列表（用于调试）
  const getHistoryList = () => {
    return history.value.map((action, index) => ({
      index,
      type: action.type,
      name: getActionName(action.type),
      timestamp: action.timestamp,
      isCurrent: index === currentIndex.value,
      data: action.data
    }))
  }
  
  // 跳转到指定历史记录
  const jumpToHistory = (targetIndex) => {
    if (targetIndex < -1 || targetIndex >= history.value.length) {
      message.error('无效的历史记录索引')
      return false
    }
    
    flushBatch()
    
    try {
      if (targetIndex < currentIndex.value) {
        // 需要撤销
        while (currentIndex.value > targetIndex) {
          const action = history.value[currentIndex.value]
          if (action.undoFn) action.undoFn()
          currentIndex.value--
        }
      } else if (targetIndex > currentIndex.value) {
        // 需要重做
        while (currentIndex.value < targetIndex) {
          currentIndex.value++
          const action = history.value[currentIndex.value]
          if (action.redoFn) action.redoFn()
        }
      }
      
      message.success(`跳转到历史记录 ${targetIndex + 1}`)
      return true
    } catch (error) {
      console.error('跳转历史记录失败:', error)
      message.error('跳转历史记录失败')
      return false
    }
  }
  
  return {
    // 状态
    canUndo,
    canRedo,
    
    // 操作类型
    ActionTypes,
    
    // 核心方法
    addAction,
    undo,
    redo,
    
    // 批处理
    flushBatch,
    
    // 历史记录管理
    clearHistory,
    getHistoryInfo,
    getHistoryList,
    jumpToHistory,
    
    // 工具方法
    getActionName
  }
} 