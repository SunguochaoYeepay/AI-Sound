import { ref, computed, onMounted, onUnmounted } from 'vue'
import { message } from 'ant-design-vue'

/**
 * 高性能拖拽系统
 * 支持音频片段拖拽、磁吸对齐、实时预览、多选拖拽和碰撞检测
 */
export function useDragAndDrop(options = {}) {
  const {
    snapThreshold = 10, // 磁吸阈值(像素)
    enableSnapping = true, // 启用磁吸
    enableMultiSelect = true, // 启用多选
    enableCollisionDetection = true, // 启用碰撞检测
    enablePreview = true, // 启用拖拽预览
    ghostOpacity = 0.5, // 拖拽幽灵透明度
    animationDuration = 200 // 动画持续时间
  } = options
  
  // 状态管理
  const isDragging = ref(false)
  const dragData = ref(null)
  const selectedItems = ref(new Set())
  const snapPoints = ref([])
  const dragPreview = ref(null)
  const dropZones = ref([])
  
  // 拖拽相关状态
  const dragState = ref({
    startX: 0,
    startY: 0,
    currentX: 0,
    currentY: 0,
    deltaX: 0,
    deltaY: 0,
    targetElement: null,
    sourceContainer: null,
    targetContainer: null,
    dragItems: [],
    snapToX: null,
    snapToY: null
  })
  
  // 性能优化
  let rafId = null
  let lastUpdateTime = 0
  const updateThrottle = 16 // 60fps
  
  // 计算属性
  const dragOffset = computed(() => ({
    x: dragState.value.deltaX,
    y: dragState.value.deltaY
  }))
  
  const snapPosition = computed(() => ({
    x: dragState.value.snapToX ?? dragState.value.currentX,
    y: dragState.value.snapToY ?? dragState.value.currentY
  }))
  
  // 创建拖拽幽灵元素
  const createDragGhost = (element, items) => {
    const ghost = element.cloneNode(true)
    ghost.style.position = 'fixed'
    ghost.style.pointerEvents = 'none'
    ghost.style.zIndex = '9999'
    ghost.style.opacity = ghostOpacity
    ghost.style.transform = 'rotate(5deg)'
    ghost.style.transition = 'none'
    
    // 多选时显示数量标识
    if (items.length > 1) {
      const badge = document.createElement('div')
      badge.style.position = 'absolute'
      badge.style.top = '-8px'
      badge.style.right = '-8px'
      badge.style.background = '#1890ff'
      badge.style.color = 'white'
      badge.style.borderRadius = '50%'
      badge.style.width = '20px'
      badge.style.height = '20px'
      badge.style.fontSize = '12px'
      badge.style.display = 'flex'
      badge.style.alignItems = 'center'
      badge.style.justifyContent = 'center'
      badge.textContent = items.length
      ghost.appendChild(badge)
    }
    
    document.body.appendChild(ghost)
    return ghost
  }
  
  // 更新拖拽幽灵位置
  const updateDragGhost = (ghost, x, y) => {
    if (!ghost) return
    
    ghost.style.left = `${x + 10}px`
    ghost.style.top = `${y + 10}px`
  }
  
  // 移除拖拽幽灵
  const removeDragGhost = (ghost) => {
    if (ghost && ghost.parentNode) {
      ghost.parentNode.removeChild(ghost)
    }
  }
  
  // 计算磁吸点
  const calculateSnapPoints = (container) => {
    const points = []
    
    if (!enableSnapping) return points
    
    // 获取容器内所有可磁吸的元素
    const snapElements = container.querySelectorAll('[data-snap="true"]')
    
    snapElements.forEach(element => {
      const rect = element.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      
      // 添加元素的左边、中心、右边作为磁吸点
      points.push({
        x: rect.left - containerRect.left,
        type: 'element-start',
        element
      })
      points.push({
        x: rect.left + rect.width / 2 - containerRect.left,
        type: 'element-center',
        element
      })
      points.push({
        x: rect.right - containerRect.left,
        type: 'element-end',
        element
      })
    })
    
    // 添加时间轴刻度作为磁吸点
    const timeMarkers = container.querySelectorAll('[data-time-marker]')
    timeMarkers.forEach(marker => {
      const rect = marker.getBoundingClientRect()
      const containerRect = container.getBoundingClientRect()
      
      points.push({
        x: rect.left - containerRect.left,
        type: 'time-marker',
        time: parseFloat(marker.dataset.timeMarker),
        element: marker
      })
    })
    
    return points
  }
  
  // 查找最近的磁吸点
  const findNearestSnapPoint = (x, y, points) => {
    if (!enableSnapping || points.length === 0) return null
    
    let nearest = null
    let minDistance = snapThreshold
    
    points.forEach(point => {
      const distance = Math.abs(point.x - x)
      if (distance < minDistance) {
        minDistance = distance
        nearest = point
      }
    })
    
    return nearest
  }
  
  // 碰撞检测
  const checkCollisions = (dragRect, container) => {
    if (!enableCollisionDetection) return []
    
    const collisions = []
    const elements = container.querySelectorAll('[data-collision="true"]')
    
    elements.forEach(element => {
      if (dragState.value.dragItems.some(item => item.element === element)) {
        return // 跳过自身
      }
      
      const rect = element.getBoundingClientRect()
      
      // 简单的矩形碰撞检测
      if (dragRect.left < rect.right &&
          dragRect.right > rect.left &&
          dragRect.top < rect.bottom &&
          dragRect.bottom > rect.top) {
        collisions.push({
          element,
          rect,
          type: 'overlap'
        })
      }
    })
    
    return collisions
  }
  
  // 更新拖拽状态
  const updateDragState = (e) => {
    const now = Date.now()
    if (now - lastUpdateTime < updateThrottle) return
    
    lastUpdateTime = now
    
    const currentX = e.clientX
    const currentY = e.clientY
    
    dragState.value.currentX = currentX
    dragState.value.currentY = currentY
    dragState.value.deltaX = currentX - dragState.value.startX
    dragState.value.deltaY = currentY - dragState.value.startY
    
    // 计算磁吸
    if (enableSnapping && dragState.value.sourceContainer) {
      const containerRect = dragState.value.sourceContainer.getBoundingClientRect()
      const relativeX = currentX - containerRect.left
      
      const nearestSnap = findNearestSnapPoint(relativeX, 0, snapPoints.value)
      if (nearestSnap) {
        dragState.value.snapToX = nearestSnap.x + containerRect.left
        
        // 显示磁吸指示器
        showSnapIndicator(nearestSnap)
      } else {
        dragState.value.snapToX = null
        hideSnapIndicator()
      }
    }
    
    // 更新拖拽预览
    if (dragPreview.value) {
      const x = snapPosition.value.x
      const y = snapPosition.value.y
      updateDragGhost(dragPreview.value, x, y)
    }
    
    // 碰撞检测
    if (enableCollisionDetection && dragState.value.targetElement) {
      const rect = dragState.value.targetElement.getBoundingClientRect()
      const dragRect = {
        left: rect.left + dragState.value.deltaX,
        right: rect.right + dragState.value.deltaX,
        top: rect.top + dragState.value.deltaY,
        bottom: rect.bottom + dragState.value.deltaY
      }
      
      const collisions = checkCollisions(dragRect, dragState.value.sourceContainer)
      updateCollisionIndicators(collisions)
    }
  }
  
  // 显示磁吸指示器
  const showSnapIndicator = (snapPoint) => {
    let indicator = document.getElementById('snap-indicator')
    
    if (!indicator) {
      indicator = document.createElement('div')
      indicator.id = 'snap-indicator'
      indicator.style.position = 'fixed'
      indicator.style.width = '2px'
      indicator.style.height = '100px'
      indicator.style.background = '#1890ff'
      indicator.style.pointerEvents = 'none'
      indicator.style.zIndex = '9998'
      indicator.style.opacity = '0.8'
      document.body.appendChild(indicator)
    }
    
    indicator.style.left = `${snapPoint.x}px`
    indicator.style.top = `${dragState.value.currentY - 50}px`
    indicator.style.display = 'block'
  }
  
  // 隐藏磁吸指示器
  const hideSnapIndicator = () => {
    const indicator = document.getElementById('snap-indicator')
    if (indicator) {
      indicator.style.display = 'none'
    }
  }
  
  // 更新碰撞指示器
  const updateCollisionIndicators = (collisions) => {
    // 清除之前的指示器
    document.querySelectorAll('.collision-indicator').forEach(el => {
      el.classList.remove('collision-indicator')
    })
    
    // 添加新的指示器
    collisions.forEach(collision => {
      collision.element.classList.add('collision-indicator')
    })
  }
  
  // 开始拖拽
  const startDrag = (e, element, data) => {
    e.preventDefault()
    
    isDragging.value = true
    dragData.value = data
    
    const rect = element.getBoundingClientRect()
    
    dragState.value = {
      startX: e.clientX,
      startY: e.clientY,
      currentX: e.clientX,
      currentY: e.clientY,
      deltaX: 0,
      deltaY: 0,
      targetElement: element,
      sourceContainer: element.closest('[data-drop-zone]'),
      targetContainer: null,
      dragItems: selectedItems.value.has(data.id) 
        ? Array.from(selectedItems.value).map(id => ({ id, element: document.querySelector(`[data-item-id="${id}"]`) }))
        : [{ id: data.id, element }],
      snapToX: null,
      snapToY: null
    }
    
    // 计算磁吸点
    if (dragState.value.sourceContainer) {
      snapPoints.value = calculateSnapPoints(dragState.value.sourceContainer)
    }
    
    // 创建拖拽预览
    if (enablePreview) {
      dragPreview.value = createDragGhost(element, dragState.value.dragItems)
    }
    
    // 添加拖拽样式
    element.classList.add('dragging')
    dragState.value.dragItems.forEach(item => {
      if (item.element) {
        item.element.classList.add('drag-selected')
      }
    })
    
    // 绑定事件
    document.addEventListener('mousemove', handleMouseMove)
    document.addEventListener('mouseup', handleMouseUp)
    
    // 触发拖拽开始事件
    emitEvent('dragStart', {
      data: dragData.value,
      items: dragState.value.dragItems,
      position: { x: e.clientX, y: e.clientY }
    })
  }
  
  // 处理鼠标移动
  const handleMouseMove = (e) => {
    if (!isDragging.value) return
    
    if (rafId) {
      cancelAnimationFrame(rafId)
    }
    
    rafId = requestAnimationFrame(() => {
      updateDragState(e)
      
      // 检查拖拽目标
      const elementBelow = document.elementFromPoint(e.clientX, e.clientY)
      const dropZone = elementBelow?.closest('[data-drop-zone]')
      
      if (dropZone !== dragState.value.targetContainer) {
        // 离开之前的拖放区域
        if (dragState.value.targetContainer) {
          dragState.value.targetContainer.classList.remove('drag-over')
          emitEvent('dragLeave', {
            container: dragState.value.targetContainer,
            data: dragData.value
          })
        }
        
        // 进入新的拖放区域
        if (dropZone) {
          dropZone.classList.add('drag-over')
          emitEvent('dragEnter', {
            container: dropZone,
            data: dragData.value
          })
        }
        
        dragState.value.targetContainer = dropZone
      }
      
      // 触发拖拽移动事件
      emitEvent('dragMove', {
        data: dragData.value,
        position: snapPosition.value,
        delta: dragOffset.value
      })
    })
  }
  
  // 处理鼠标释放
  const handleMouseUp = (e) => {
    if (!isDragging.value) return
    
    isDragging.value = false
    
    // 清理事件监听
    document.removeEventListener('mousemove', handleMouseMove)
    document.removeEventListener('mouseup', handleMouseUp)
    
    if (rafId) {
      cancelAnimationFrame(rafId)
      rafId = null
    }
    
    // 清理样式
    dragState.value.targetElement?.classList.remove('dragging')
    dragState.value.dragItems.forEach(item => {
      if (item.element) {
        item.element.classList.remove('drag-selected')
      }
    })
    
    // 清理指示器
    hideSnapIndicator()
    document.querySelectorAll('.collision-indicator').forEach(el => {
      el.classList.remove('collision-indicator')
    })
    
    if (dragState.value.targetContainer) {
      dragState.value.targetContainer.classList.remove('drag-over')
    }
    
    // 移除拖拽预览
    if (dragPreview.value) {
      removeDragGhost(dragPreview.value)
      dragPreview.value = null
    }
    
    // 处理拖放结果
    const dropResult = {
      data: dragData.value,
      items: dragState.value.dragItems,
      sourceContainer: dragState.value.sourceContainer,
      targetContainer: dragState.value.targetContainer,
      position: snapPosition.value,
      delta: dragOffset.value,
      snapPoint: dragState.value.snapToX ? {
        x: dragState.value.snapToX,
        y: dragState.value.snapToY
      } : null
    }
    
    if (dragState.value.targetContainer && dragState.value.targetContainer !== dragState.value.sourceContainer) {
      // 跨容器拖放
      emitEvent('drop', dropResult)
    } else if (Math.abs(dragState.value.deltaX) > 5 || Math.abs(dragState.value.deltaY) > 5) {
      // 同容器内移动
      emitEvent('move', dropResult)
    } else {
      // 点击事件
      emitEvent('click', dropResult)
    }
    
    // 清理状态
    dragData.value = null
    dragState.value = {
      startX: 0,
      startY: 0,
      currentX: 0,
      currentY: 0,
      deltaX: 0,
      deltaY: 0,
      targetElement: null,
      sourceContainer: null,
      targetContainer: null,
      dragItems: [],
      snapToX: null,
      snapToY: null
    }
  }
  
  // 多选管理
  const toggleSelection = (itemId, ctrlKey = false) => {
    if (!enableMultiSelect) {
      selectedItems.value.clear()
      selectedItems.value.add(itemId)
      return
    }
    
    if (ctrlKey) {
      if (selectedItems.value.has(itemId)) {
        selectedItems.value.delete(itemId)
      } else {
        selectedItems.value.add(itemId)
      }
    } else {
      selectedItems.value.clear()
      selectedItems.value.add(itemId)
    }
    
    // 更新选中样式
    updateSelectionStyles()
  }
  
  // 更新选中样式
  const updateSelectionStyles = () => {
    document.querySelectorAll('[data-item-id]').forEach(element => {
      const itemId = element.dataset.itemId
      if (selectedItems.value.has(itemId)) {
        element.classList.add('selected')
      } else {
        element.classList.remove('selected')
      }
    })
  }
  
  // 清空选择
  const clearSelection = () => {
    selectedItems.value.clear()
    updateSelectionStyles()
  }
  
  // 事件系统
  const eventHandlers = ref({})
  
  const on = (event, handler) => {
    if (!eventHandlers.value[event]) {
      eventHandlers.value[event] = []
    }
    eventHandlers.value[event].push(handler)
  }
  
  const off = (event, handler) => {
    if (eventHandlers.value[event]) {
      const index = eventHandlers.value[event].indexOf(handler)
      if (index > -1) {
        eventHandlers.value[event].splice(index, 1)
      }
    }
  }
  
  const emitEvent = (event, data) => {
    if (eventHandlers.value[event]) {
      eventHandlers.value[event].forEach(handler => {
        try {
          handler(data)
        } catch (error) {
          console.error(`拖拽事件处理错误 (${event}):`, error)
        }
      })
    }
  }
  
  // 键盘事件处理
  const handleKeyDown = (e) => {
    if (e.key === 'Escape' && isDragging.value) {
      // 取消拖拽
      handleMouseUp(e)
    }
    
    if (e.key === 'Delete' && selectedItems.value.size > 0) {
      // 删除选中项
      emitEvent('deleteSelected', {
        items: Array.from(selectedItems.value)
      })
      clearSelection()
    }
  }
  
  // 生命周期
  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
    
    // 添加CSS样式
    const style = document.createElement('style')
    style.textContent = `
      .dragging {
        opacity: 0.5;
        transform: scale(0.95);
        transition: transform 0.1s ease;
      }
      
      .drag-selected {
        outline: 2px solid #1890ff;
        outline-offset: 2px;
      }
      
      .selected {
        background-color: rgba(24, 144, 255, 0.1);
        border: 2px solid #1890ff;
      }
      
      .drag-over {
        background-color: rgba(24, 144, 255, 0.05);
        border: 2px dashed #1890ff;
      }
      
      .collision-indicator {
        background-color: rgba(255, 77, 79, 0.2);
        border: 2px solid #ff4d4f;
      }
    `
    document.head.appendChild(style)
  })
  
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
    
    // 清理拖拽状态
    if (isDragging.value) {
      handleMouseUp({ clientX: 0, clientY: 0 })
    }
    
    // 清理指示器
    hideSnapIndicator()
    const indicator = document.getElementById('snap-indicator')
    if (indicator) {
      indicator.remove()
    }
  })
  
  return {
    // 状态
    isDragging,
    selectedItems,
    dragOffset,
    snapPosition,
    
    // 核心方法
    startDrag,
    toggleSelection,
    clearSelection,
    
    // 事件系统
    on,
    off,
    
    // 配置
    enableSnapping: ref(enableSnapping),
    enableMultiSelect: ref(enableMultiSelect),
    enableCollisionDetection: ref(enableCollisionDetection),
    snapThreshold: ref(snapThreshold)
  }
} 