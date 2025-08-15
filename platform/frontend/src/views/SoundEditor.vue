<template>
  <div class="sound-editor-container" :class="{ 'fullscreen-mode': isAppFullscreen }">
    <!-- 标准页面头部 -->
    <div class="page-header" v-show="!isAppFullscreen">
      <div class="header-content">
        <div class="title-section">
          <div class="title-with-back">
       
            <h1 class="page-title">
              
              音频混合编辑器 {{ projectTitle || '专业的音频混合工具，支持对话、环境音、背景音乐智能混合' }}
            </h1>
            <!-- 新增：章节选择器 -->
            <div class="chapter-selector" v-if="projectBookId">
              <a-select 
                v-model:value="selectedChapterId" 
                @change="handleChapterChange"
                placeholder="选择章节"
                style="margin-left: 16px; width: 200px;"
              >
                <a-select-option v-for="chapter in chapters" :key="chapter.id" :value="chapter.id">
                  第{{ chapter.chapter_number }}章 - {{ chapter.chapter_title }}
                </a-select-option>
              </a-select>
            </div>
          </div>
        
        </div>
        <div class="action-section">
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
      <MultitrackEditor 
        :selected-chapter-id="selectedChapterId"
        @project-change="handleProjectChange"
        @chapter-change="handleChapterChange"
      />
    </div>

    <!-- 帮助对话框 -->
    <a-modal v-model:open="helpVisible" title="使用帮助" width="800px" :footer="null">
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
    <a-modal v-model:open="settingsVisible" title="编辑器设置" width="600px" @ok="saveSettings">
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
import { booksAPI } from '@/api'
import { createEmptyProject } from '@/api/sound-editor/multitrackProject'
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
  const currentProject = ref(createEmptyProject())

  // 章节相关数据
  const chapters = ref([])
  const selectedChapterId = ref(null)
  const projectBookId = ref(null)

  // 计算属性
  const projectTitle = computed(() => {
    return currentProject.value?.title || '音频混合编辑器'
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
    try {
      // 确保body类总是被移除，即使组件异常卸载
      if (document.body && document.body.classList) {
        document.body.classList.remove('sound-editor-fullscreen')
      }
    } catch (error) {
      console.error('Error during cleanup:', error)
    }
  })

  const handleProjectChange = (project) => {
    currentProject.value = project
    // 如果项目有关联书籍，加载章节信息
    if (project && project.bookId) {
      projectBookId.value = project.bookId
      loadChapters(project.bookId)
    }
  }

  // 加载章节列表
  const loadChapters = async (bookId) => {
    try {
      console.log('开始加载章节列表，bookId:', bookId)
      const response = await booksAPI.getBookChapters(bookId)
      console.log('章节API响应:', response)
      if (response.data && response.data.success) {
        chapters.value = response.data.data || []
        console.log('加载到的章节:', chapters.value)
      } else {
        console.error('章节API返回失败:', response)
      }
    } catch (error) {
      console.error('加载章节列表失败:', error)
    }
  }

  // 处理章节选择变化
  const handleChapterChange = (chapterId) => {
    console.log('选择章节:', chapterId)
    selectedChapterId.value = chapterId
    // 可以在这里添加章节选择后的逻辑
  }

  // 组件挂载时加载设置
  onMounted(() => {
    try {
      const savedSettings = localStorage.getItem('soundEditorSettings')
      if (savedSettings) {
        const parsed = JSON.parse(savedSettings)
        if (parsed && typeof parsed === 'object') {
          Object.assign(settings, parsed)
        }
      }
    } catch (error) {
      console.error('Failed to load settings:', error)
      localStorage.removeItem('soundEditorSettings')
    }
  })
</script>

<style scoped>
  .sound-editor-container {
    height: 100vh;
    display: flex;
    flex-direction: column;
    background: #f5f5f5;
  }

  /* 标准页面头部样式 */
  .page-header {
    background: white;
    border-bottom: 1px solid #e8e8e8;
    padding: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
    flex-shrink: 0;
  }

  .header-content {
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    width: 100%;
    margin: 0 auto;
  }

  .title-section {
    flex: 1;
  }

  .title-with-back {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .back-button {
    color: #666;
    border: none;
    padding: 4px;
    margin-right: 8px;
  }

  .back-button:hover {
    color: #1890ff;
    background: rgba(24, 144, 255, 0.1);
  }

  .page-title {
    margin: 0;
    font-size: 24px;
    font-weight: 600;
    color: #262626;
    line-height: 1.2;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  .title-icon {
    color: #1890ff;
  }

  .page-description {
    margin: 0;
    font-size: 14px;
    color: #666;
    line-height: 1.5;
  }

  .action-section {
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

  .help-content ul,
  .help-content ol {
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

  /* 响应式设计 */
  @media (max-width: 768px) {
    .page-header {
      padding: 16px;
    }

    .header-content {
      flex-direction: column;
      align-items: flex-start;
      gap: 16px;
    }

    .title-with-back {
      flex-direction: column;
      align-items: flex-start;
      gap: 8px;
    }

    .page-title {
      font-size: 20px;
    }

    .action-section {
      width: 100%;
      justify-content: flex-end;
    }
  }

  /* 暗黑模式支持 */
  [data-theme='dark'] .sound-editor-container {
    background: #141414;
  }

  [data-theme='dark'] .page-header {
    background: #1f1f1f;
    border-bottom-color: #303030;
  }

  [data-theme='dark'] .page-title {
    color: #fff;
  }

  [data-theme='dark'] .page-description {
    color: #a6a6a6;
  }

  [data-theme='dark'] .back-button {
    color: #a6a6a6;
  }

  [data-theme='dark'] .back-button:hover {
    color: #1890ff;
    background: rgba(24, 144, 255, 0.1);
  }

  [data-theme='dark'] .title-icon {
    color: #1890ff;
  }
</style>
