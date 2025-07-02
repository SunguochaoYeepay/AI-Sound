<template>
  <div class="sound-editor-view" :class="{ 'fullscreen-mode': isAppFullscreen }">
    <!-- 页面头部 -->
    <div class="editor-header" v-show="!isAppFullscreen">
      <div class="header-content">
        <div class="header-left">
          <a-button type="text" @click="handleBack" class="back-button">
            <template #icon><ArrowLeftOutlined /></template>
          </a-button>
          <div class="header-title">
            <h2>{{ projectTitle }}</h2>
            <span class="header-subtitle">{{ projectSubtitle }}</span>
          </div>
        </div>
        
        <div class="header-right">
          <a-space>
            <a-tooltip title="帮助">
              <a-button type="text" shape="circle" @click="showHelp">
                <template #icon><QuestionCircleOutlined /></template>
              </a-button>
            </a-tooltip>
            <a-tooltip title="设置">
              <a-button type="text" shape="circle" @click="showSettings">
                <template #icon><SettingOutlined /></template>
              </a-button>
            </a-tooltip>
            <a-tooltip :title="isAppFullscreen ? '退出全屏' : '全屏'">
              <a-button type="text" shape="circle" @click="toggleFullscreen">
                <template #icon>
                  <FullscreenExitOutlined v-if="isAppFullscreen" />
                  <FullscreenOutlined v-else />
                </template>
              </a-button>
            </a-tooltip>
          </a-space>
        </div>
      </div>
    </div>

    <!-- 全屏模式下的浮动控制栏 -->
    <div class="fullscreen-controls" v-show="isAppFullscreen">
      <a-tooltip title="退出全屏">
        <a-button type="text" shape="circle" @click="toggleFullscreen" class="fullscreen-exit-btn">
          <template #icon><FullscreenExitOutlined /></template>
        </a-button>
      </a-tooltip>
      <a-tooltip title="设置">
        <a-button type="text" shape="circle" @click="showSettings">
          <template #icon><SettingOutlined /></template>
        </a-button>
      </a-tooltip>
      <a-tooltip title="帮助">
        <a-button type="text" shape="circle" @click="showHelp">
          <template #icon><QuestionCircleOutlined /></template>
        </a-button>
      </a-tooltip>
    </div>

    <!-- 主编辑器区域 -->
    <div class="editor-content" :class="{ 'fullscreen-content': isAppFullscreen }">
      <MultitrackEditor @project-change="handleProjectChange" />
    </div>

    <!-- 帮助对话框 -->
    <a-modal
      v-model:open="helpVisible"
      title="使用帮助"
      width="800px"
      :footer="null"
    >
      <div class="help-content">
        <a-typography>
          <a-typography-title :level="4">🎵 多轨音频编辑器</a-typography-title>
          <a-typography-paragraph>
            这是一个专业的多轨音频编辑工具，支持对话、环境音、背景音乐的分层编辑。
          </a-typography-paragraph>
          
          <a-typography-title :level="5">✨ 主要功能</a-typography-title>
          <ul>
            <li><strong>拖拽编辑</strong>：直接拖拽音频片段到时间轴上</li>
            <li><strong>多轨支持</strong>：对话、环境音、背景音乐三种音轨</li>
            <li><strong>精确控制</strong>：毫秒级音频定位和编辑</li>
            <li><strong>实时预览</strong>：即时播放和效果预览</li>
            <li><strong>项目管理</strong>：完整的项目保存和加载</li>
          </ul>

          <a-typography-title :level="5">⌨️ 快捷键</a-typography-title>
          <ul>
            <li><kbd>空格</kbd> - 播放/暂停</li>
            <li><kbd>Delete</kbd> - 删除选中片段</li>
            <li><kbd>Escape</kbd> - 清除选择</li>
            <li><kbd>Ctrl+S</kbd> - 保存项目</li>
            <li><kbd>Ctrl+E</kbd> - 导出音频</li>
          </ul>

          <a-typography-title :level="5">🎮 操作流程</a-typography-title>
          <ol>
            <li>创建新项目或打开现有项目</li>
            <li>上传音频文件到资源库</li>
            <li>拖拽音频片段到对应音轨</li>
            <li>调整时间位置和音量</li>
            <li>实时预览效果</li>
            <li>导出最终音频</li>
          </ol>
        </a-typography>
      </div>
    </a-modal>

    <!-- 设置对话框 -->
    <a-modal
      v-model:open="settingsVisible"
      title="编辑器设置"
      width="600px"
      @ok="saveSettings"
    >
      <a-form :model="settings" layout="vertical">
        <a-form-item label="默认采样率">
          <a-select v-model:value="settings.sampleRate">
            <a-select-option value="44100">44.1 kHz</a-select-option>
            <a-select-option value="48000">48 kHz</a-select-option>
            <a-select-option value="96000">96 kHz</a-select-option>
          </a-select>
        </a-form-item>
        
        <a-form-item label="默认导出格式">
          <a-select v-model:value="settings.exportFormat">
            <a-select-option value="wav">WAV</a-select-option>
            <a-select-option value="mp3">MP3</a-select-option>
            <a-select-option value="flac">FLAC</a-select-option>
          </a-select>
        </a-form-item>

        <a-form-item label="自动保存">
          <a-switch v-model:checked="settings.autoSave" />
          <span class="ant-form-text">每5分钟自动保存项目</span>
        </a-form-item>

        <a-form-item label="键盘快捷键">
          <a-switch v-model:checked="settings.enableShortcuts" />
          <span class="ant-form-text">启用键盘快捷键</span>
        </a-form-item>
      </a-form>
    </a-modal>
  </div>
</template>

<script setup>
import { ref, reactive, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { message } from 'ant-design-vue'
import { 
  QuestionCircleOutlined, 
  SettingOutlined, 
  ArrowLeftOutlined,
  FullscreenOutlined,
  FullscreenExitOutlined 
} from '@ant-design/icons-vue'

// 导入朋友的音频编辑器组件
import MultitrackEditor from '@/components/sound-editor/MultitrackEditor.vue'

const router = useRouter()

// 响应式数据
const helpVisible = ref(false)
const settingsVisible = ref(false)
const isAppFullscreen = ref(false)
const currentProject = ref(null)

// 计算属性
const projectTitle = computed(() => {
  return currentProject.value?.title || '多轨音频编辑器'
})

const projectSubtitle = computed(() => {
  if (currentProject.value?.title) {
    return `项目 · ${currentProject.value.author || 'AI-Sound'}`
  }
  return '专业级多轨音频编辑工具'
})

// 设置数据
const settings = reactive({
  sampleRate: '44100',
  exportFormat: 'wav',
  autoSave: true,
  enableShortcuts: true
})

// 方法定义
const handleBack = () => {
  router.push('/')
}

const showHelp = () => {
  helpVisible.value = true
}

const showSettings = () => {
  settingsVisible.value = true
}

const saveSettings = () => {
  // 保存设置到本地存储
  localStorage.setItem('soundEditorSettings', JSON.stringify(settings))
  message.success('设置已保存')
  settingsVisible.value = false
}

const toggleFullscreen = () => {
  // 切换应用内全屏模式
  isAppFullscreen.value = !isAppFullscreen.value
  
  // 通知父组件（App.vue）隐藏/显示导航栏
  if (isAppFullscreen.value) {
    document.body.classList.add('sound-editor-fullscreen')
  } else {
    document.body.classList.remove('sound-editor-fullscreen')
  }
}

// 组件卸载时清理样式
onUnmounted(() => {
  document.body.classList.remove('sound-editor-fullscreen')
})

const handleProjectChange = (project) => {
  currentProject.value = project
}

// 组件挂载时加载设置
onMounted(() => {
  const savedSettings = localStorage.getItem('soundEditorSettings')
  if (savedSettings) {
    Object.assign(settings, JSON.parse(savedSettings))
  }
})
</script>

<style scoped>
.sound-editor-view {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #0f0f0f;
}

.editor-header {
  background: #1a1a1a;
  border-bottom: 1px solid #333;
  flex-shrink: 0;
  height: 56px;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
  padding: 0 16px;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.back-button {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #999;
}

.back-button:hover {
  color: #fff;
}

.header-title h2 {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
  color: #fff;
  line-height: 1.2;
}

.header-subtitle {
  font-size: 12px;
  color: #888;
  display: block;
  margin-top: 2px;
}

.header-right {
  display: flex;
  align-items: center;
}

.editor-content {
  flex: 1;
  overflow: hidden;
}

.help-content {
  max-height: 600px;
  overflow-y: auto;
}

.help-content ul, .help-content ol {
  padding-left: 20px;
}

.help-content li {
  margin: 8px 0;
}

.help-content kbd {
  padding: 2px 6px;
  background: #f5f5f5;
  border: 1px solid #d9d9d9;
  border-radius: 3px;
  font-family: 'Courier New', monospace;
  font-size: 12px;
}

/* 全屏模式样式 */
.fullscreen-mode {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  right: 0 !important;
  bottom: 0 !important;
  width: 100vw !important;
  height: 100vh !important;
  z-index: 9999 !important;
  background: #0f0f0f !important;
}

.fullscreen-content {
  height: 100vh !important;
}

/* 全屏模式下的浮动控制栏 */
.fullscreen-controls {
  position: fixed;
  top: 16px;
  right: 16px;
  z-index: 10000;
  display: flex;
  gap: 8px;
  background: rgba(0, 0, 0, 0.7);
  backdrop-filter: blur(10px);
  border-radius: 8px;
  padding: 8px;
  border: 1px solid rgba(255, 255, 255, 0.1);
}

.fullscreen-controls .ant-btn {
  background: transparent;
  border: none;
  color: #fff;
}

.fullscreen-controls .ant-btn:hover {
  background: rgba(255, 255, 255, 0.1);
  color: #fff;
}

.fullscreen-exit-btn {
  color: #ff4d4f !important;
}

.fullscreen-exit-btn:hover {
  background: rgba(255, 77, 79, 0.1) !important;
  color: #ff4d4f !important;
}

:deep(.ant-page-header) {
  padding: 16px 24px;
}
</style> 