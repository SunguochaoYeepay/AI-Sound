import { onMounted, onUnmounted, ref } from 'vue'
import { message } from 'ant-design-vue'

/**
 * 键盘快捷键管理组合函数
 * 支持专业音视频编辑器的所有常用快捷键
 */
export function useKeyboardShortcuts(callbacks = {}) {
  const isEnabled = ref(true)
  const pressedKeys = ref(new Set())
  
  // 快捷键映射表
  const shortcuts = {
    // 播放控制
    'Space': 'togglePlayback',
    'Enter': 'play',
    'Escape': 'stop',
    
    // 编辑操作
    'Ctrl+Z': 'undo',
    'Ctrl+Y': 'redo',
    'Ctrl+Shift+Z': 'redo',
    'Ctrl+C': 'copy',
    'Ctrl+V': 'paste',
    'Ctrl+X': 'cut',
    'Ctrl+A': 'selectAll',
    'Delete': 'delete',
    'Backspace': 'delete',
    
    // 文件操作
    'Ctrl+S': 'save',
    'Ctrl+O': 'open',
    'Ctrl+N': 'new',
    'Ctrl+E': 'export',
    'Ctrl+I': 'import',
    
    // 视图控制
    'Ctrl+Plus': 'zoomIn',
    'Ctrl+=': 'zoomIn',
    'Ctrl+Minus': 'zoomOut',
    'Ctrl+-': 'zoomOut',
    'Ctrl+0': 'zoomReset',
    'Ctrl+1': 'zoomFit',
    
    // 导航
    'Home': 'goToStart',
    'End': 'goToEnd',
    'ArrowLeft': 'previousFrame',
    'ArrowRight': 'nextFrame',
    'Shift+ArrowLeft': 'previousSecond',
    'Shift+ArrowRight': 'nextSecond',
    'Ctrl+ArrowLeft': 'previousMarker',
    'Ctrl+ArrowRight': 'nextMarker',
    
    // 轨道操作
    'Digit1': 'selectTrack1',
    'Digit2': 'selectTrack2',
    'Digit3': 'selectTrack3',
    'Digit4': 'selectTrack4',
    'Digit5': 'selectTrack5',
    'Digit6': 'selectTrack6',
    'Digit7': 'selectTrack7',
    'Digit8': 'selectTrack8',
    'Digit9': 'selectTrack9',
    
    // 轨道控制
    'M': 'muteTrack',
    'S': 'soloTrack',
    'R': 'recordTrack',
    
    // 标记和区域
    'Ctrl+M': 'addMarker',
    'Ctrl+R': 'addRegion',
    'Ctrl+L': 'loop',
    
    // 效果和工具
    'F': 'fadeIn',
    'Shift+F': 'fadeOut',
    'G': 'gain',
    'N': 'normalize',
    'T': 'trim',
    
    // 面板切换
    'F1': 'toggleHelp',
    'F2': 'toggleProperties',
    'F3': 'toggleEffects',
    'F4': 'toggleMixer',
    'F5': 'refresh',
    
    // 全屏和界面
    'F11': 'toggleFullscreen',
    'Tab': 'nextPanel',
    'Shift+Tab': 'previousPanel'
  }
  
  // 获取按键组合字符串
  const getKeyCombo = (event) => {
    const keys = []
    
    if (event.ctrlKey) keys.push('Ctrl')
    if (event.shiftKey) keys.push('Shift')
    if (event.altKey) keys.push('Alt')
    if (event.metaKey) keys.push('Meta')
    
    // 处理特殊键
    let key = event.key
    if (key === ' ') key = 'Space'
    if (key === '+') key = 'Plus'
    if (key === '-') key = 'Minus'
    if (key === '=') key = '='
    
    // 处理数字键
    if (event.code && event.code.startsWith('Digit')) {
      key = event.code
    }
    
    keys.push(key)
    return keys.join('+')
  }
  
  // 键盘事件处理
  const handleKeyDown = (event) => {
    if (!isEnabled.value) return
    
    // 忽略在输入框中的按键
    const target = event.target
    if (target.tagName === 'INPUT' || 
        target.tagName === 'TEXTAREA' || 
        target.contentEditable === 'true') {
      return
    }
    
    const combo = getKeyCombo(event)
    pressedKeys.value.add(combo)
    
    const action = shortcuts[combo]
    if (action && callbacks[action]) {
      event.preventDefault()
      event.stopPropagation()
      
      try {
        callbacks[action](event)
      } catch (error) {
        console.error(`快捷键执行失败 (${combo} -> ${action}):`, error)
        message.error(`快捷键执行失败: ${action}`)
      }
    }
  }
  
  const handleKeyUp = (event) => {
    const combo = getKeyCombo(event)
    pressedKeys.value.delete(combo)
  }
  
  // 启用/禁用快捷键
  const enable = () => {
    isEnabled.value = true
  }
  
  const disable = () => {
    isEnabled.value = false
    pressedKeys.value.clear()
  }
  
  // 检查按键是否被按下
  const isKeyPressed = (combo) => {
    return pressedKeys.value.has(combo)
  }
  
  // 获取所有快捷键列表
  const getShortcutsList = () => {
    const categories = {
      '播放控制': [
        { key: 'Space', action: '播放/暂停' },
        { key: 'Enter', action: '播放' },
        { key: 'Escape', action: '停止' }
      ],
      '编辑操作': [
        { key: 'Ctrl+Z', action: '撤销' },
        { key: 'Ctrl+Y', action: '重做' },
        { key: 'Ctrl+C', action: '复制' },
        { key: 'Ctrl+V', action: '粘贴' },
        { key: 'Ctrl+X', action: '剪切' },
        { key: 'Ctrl+A', action: '全选' },
        { key: 'Delete', action: '删除' }
      ],
      '文件操作': [
        { key: 'Ctrl+S', action: '保存' },
        { key: 'Ctrl+O', action: '打开' },
        { key: 'Ctrl+N', action: '新建' },
        { key: 'Ctrl+E', action: '导出' },
        { key: 'Ctrl+I', action: '导入' }
      ],
      '视图控制': [
        { key: 'Ctrl++', action: '放大' },
        { key: 'Ctrl+-', action: '缩小' },
        { key: 'Ctrl+0', action: '重置缩放' },
        { key: 'Ctrl+1', action: '适合窗口' }
      ],
      '导航': [
        { key: 'Home', action: '跳到开始' },
        { key: 'End', action: '跳到结束' },
        { key: '←/→', action: '逐帧移动' },
        { key: 'Shift+←/→', action: '逐秒移动' }
      ],
      '轨道操作': [
        { key: '1-9', action: '选择轨道' },
        { key: 'M', action: '静音轨道' },
        { key: 'S', action: '独奏轨道' },
        { key: 'R', action: '录制轨道' }
      ]
    }
    
    return categories
  }
  
  // 显示快捷键帮助
  const showHelp = () => {
    const shortcuts = getShortcutsList()
    let helpText = '键盘快捷键:\n\n'
    
    Object.entries(shortcuts).forEach(([category, keys]) => {
      helpText += `${category}:\n`
      keys.forEach(({ key, action }) => {
        helpText += `  ${key} - ${action}\n`
      })
      helpText += '\n'
    })
    
    console.log(helpText)
    message.info('快捷键帮助已输出到控制台')
  }
  
  // 生命周期管理
  onMounted(() => {
    document.addEventListener('keydown', handleKeyDown)
    document.addEventListener('keyup', handleKeyUp)
  })
  
  onUnmounted(() => {
    document.removeEventListener('keydown', handleKeyDown)
    document.removeEventListener('keyup', handleKeyUp)
  })
  
  return {
    isEnabled,
    pressedKeys,
    enable,
    disable,
    isKeyPressed,
    getShortcutsList,
    showHelp
  }
} 