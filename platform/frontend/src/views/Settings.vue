<template>
  <div class="settings-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <div class="title-section">
          <h1 class="page-title">
            <SettingOutlined class="title-icon" />
            系统设置
          </h1>
          <p class="page-description">
            管理站点基本信息和系统核心配置
          </p>
        </div>
        <div class="action-section">
          <a-button type="primary" size="large" @click="saveAllSettings" :loading="saving" ghost>
            <template #icon>
              <SaveOutlined />
            </template>
            保存设置
          </a-button>
        </div>
      </div>
    </div>

    <!-- 主要内容区域 -->
    <div class="main-content">
      <a-row :gutter="24">
        <!-- 左侧：站点基本设置 -->
        <a-col :span="16">
          <div class="settings-section">
            <!-- 站点基本信息 -->
            <a-card title="站点基本信息" :bordered="false" class="setting-card">
              <template #extra>
                <a-button type="link" size="small" @click="resetSiteSettings">
                  <ReloadOutlined />
                  重置
                </a-button>
              </template>

              <a-form :model="siteSettings" layout="vertical">
                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="站点名称" name="siteName">
                      <a-input 
                        v-model:value="siteSettings.siteName" 
                        placeholder="AI-Sound 智能语音平台"
                        size="large"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="站点副标题" name="siteSubtitle">
                      <a-input 
                        v-model:value="siteSettings.siteSubtitle" 
                        placeholder="专业的AI语音合成解决方案"
                        size="large"
                      />
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-form-item label="站点描述" name="siteDescription">
                  <a-textarea 
                    v-model:value="siteSettings.siteDescription" 
                    placeholder="详细描述您的AI语音平台..."
                    :rows="3"
                    size="large"
                  />
                </a-form-item>

                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="管理员邮箱" name="adminEmail">
                      <a-input 
                        v-model:value="siteSettings.adminEmail" 
                        placeholder="admin@example.com"
                        size="large"
                        type="email"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="技术支持联系方式" name="supportContact">
                      <a-input 
                        v-model:value="siteSettings.supportContact" 
                        placeholder="技术支持联系方式"
                        size="large"
                      />
                    </a-form-item>
                  </a-col>
                </a-row>
              </a-form>
            </a-card>

            <!-- LOGO设置 -->
            <a-card title="品牌标识设置" :bordered="false" class="setting-card">
              <a-form layout="vertical">
                <a-row :gutter="24">
                  <a-col :span="12">
                    <a-form-item label="站点LOGO">
                      <div class="logo-upload-container">
                        <div class="logo-preview">
                          <img 
                            v-if="siteSettings.logo" 
                            :src="siteSettings.logo" 
                            alt="站点LOGO" 
                            class="logo-image"
                          />
                          <div v-else class="logo-placeholder">
                            <PictureOutlined style="font-size: 32px; color: #bfbfbf;" />
                            <p style="color: #bfbfbf; margin: 8px 0 0 0;">暂无LOGO</p>
                          </div>
                        </div>
                        <div class="logo-actions">
                          <a-upload
                            :show-upload-list="false"
                            accept="image/*"
                            :before-upload="handleLogoUpload"
                            :custom-request="uploadLogo"
                          >
                            <a-button type="primary" ghost>
                              <UploadOutlined />
                              上传LOGO
                            </a-button>
                          </a-upload>
                          <a-button v-if="siteSettings.logo" @click="removeLogo" danger>
                            <DeleteOutlined />
                            移除
                          </a-button>
                        </div>
                      </div>
                      <div class="upload-tips">
                        <p>• 建议尺寸：200×200px 或 400×400px</p>
                        <p>• 支持格式：PNG、JPG、SVG</p>
                        <p>• 文件大小：不超过2MB</p>
                      </div>
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="收藏夹图标 (Favicon)">
                      <div class="favicon-upload-container">
                        <div class="favicon-preview">
                          <img 
                            v-if="siteSettings.favicon" 
                            :src="siteSettings.favicon" 
                            alt="Favicon" 
                            class="favicon-image"
                          />
                          <div v-else class="favicon-placeholder">
                            <GlobalOutlined style="font-size: 24px; color: #bfbfbf;" />
                          </div>
                        </div>
                        <div class="favicon-actions">
                          <a-upload
                            :show-upload-list="false"
                            accept="image/*"
                            :before-upload="handleFaviconUpload"
                            :custom-request="uploadFavicon"
                          >
                            <a-button type="primary" ghost size="small">
                              <UploadOutlined />
                              上传Favicon
                            </a-button>
                          </a-upload>
                        </div>
                      </div>
                      <div class="upload-tips">
                        <p>• 建议尺寸：32×32px 或 64×64px</p>
                        <p>• 支持格式：PNG、ICO</p>
                      </div>
                    </a-form-item>
                  </a-col>
                </a-row>
              </a-form>
            </a-card>

            <!-- 主题设置 -->
            <a-card title="主题设置" :bordered="false" class="setting-card">
              <template #extra>
                <a-button type="link" size="small" @click="resetThemeSettings">
                  <ReloadOutlined />
                  重置
                </a-button>
              </template>

              <a-form :model="themeSettings" layout="vertical">
                <a-row :gutter="16">
                  <a-col :span="8">
                    <a-form-item label="主题模式">
                      <a-radio-group 
                        v-model:value="themeSettings.mode" 
                        @change="previewTheme"
                        button-style="solid"
                        size="large"
                      >
                        <a-radio-button value="system">跟随系统</a-radio-button>
                        <a-radio-button value="light">浅色模式</a-radio-button>
                        <a-radio-button value="dark">深色模式</a-radio-button>
                      </a-radio-group>
                    </a-form-item>
                  </a-col>
                  <a-col :span="8">
                    <a-form-item label="布局密度">
                      <a-select 
                        v-model:value="themeSettings.layout" 
                        @change="previewTheme"
                        size="large"
                      >
                        <a-select-option value="compact">紧凑</a-select-option>
                        <a-select-option value="comfortable">舒适</a-select-option>
                        <a-select-option value="spacious">宽松</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                  <a-col :span="8">
                    <a-form-item label="侧边栏样式">
                      <a-select 
                        v-model:value="themeSettings.sidebarStyle" 
                        @change="previewTheme"
                        size="large"
                      >
                        <a-select-option value="gradient">渐变</a-select-option>
                        <a-select-option value="solid">纯色</a-select-option>
                        <a-select-option value="glass">玻璃</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                </a-row>
                
                <a-form-item label="主色调方案">
                  <div class="color-scheme-selector">
                    <div 
                      v-for="(scheme, key) in colorSchemes" 
                      :key="key"
                      class="color-scheme-item"
                      :class="{ active: themeSettings.colorScheme === key }"
                      @click="selectColorScheme(key)"
                    >
                      <div class="color-preview" :style="{ background: scheme.gradient }"></div>
                      <span class="color-name">{{ getColorSchemeName(key) }}</span>
                    </div>
                  </div>
                </a-form-item>
                
                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="卡片样式">
                      <a-radio-group 
                        v-model:value="themeSettings.cardStyle" 
                        @change="previewTheme"
                        size="large"
                      >
                        <a-radio-button value="rounded">圆角</a-radio-button>
                        <a-radio-button value="square">直角</a-radio-button>
                      </a-radio-group>
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="动效设置">
                      <a-switch 
                        v-model:checked="themeSettings.enableAnimations"
                        @change="previewTheme"
                        checked-children="开启"
                        un-checked-children="关闭"
                        size="default"
                      />
                      <span style="margin-left: 12px;">动画效果</span>
                    </a-form-item>
                  </a-col>
                </a-row>
                
                <a-form-item label="紧凑模式">
                  <a-switch 
                    v-model:checked="themeSettings.compactMode"
                    @change="previewTheme"
                    checked-children="开启"
                    un-checked-children="关闭"
                    size="default"
                  />
                  <span style="margin-left: 12px;">启用紧凑界面布局</span>
                </a-form-item>
              </a-form>
            </a-card>

            <!-- AI服务配置 -->
            <a-card title="AI服务配置" :bordered="false" class="setting-card">
              <a-form :model="aiSettings" layout="vertical">
                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="TTS服务地址" name="ttsServiceUrl">
                      <a-input 
                        v-model:value="aiSettings.ttsServiceUrl" 
                        placeholder="http://localhost:7929"
                        size="large"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="并发处理限制" name="concurrentLimit">
                      <a-input-number 
                        v-model:value="aiSettings.concurrentLimit" 
                        :min="1" 
                        :max="10"
                        size="large"
                        style="width: 100%"
                      />
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-row :gutter="16">
                  <a-col :span="12">
                    <a-form-item label="Ollama服务地址" name="ollamaServiceUrl">
                      <a-input 
                        v-model:value="aiSettings.ollamaServiceUrl" 
                        placeholder="http://localhost:11434"
                        size="large"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="12">
                    <a-form-item label="默认LLM模型" name="defaultLlmModel">
                      <a-select 
                        v-model:value="aiSettings.defaultLlmModel" 
                        placeholder="选择默认模型"
                        size="large"
                      >
                        <a-select-option value="qwen:latest">Qwen Latest</a-select-option>
                        <a-select-option value="llama3.2:latest">Llama 3.2</a-select-option>
                        <a-select-option value="gemma2:latest">Gemma 2</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                </a-row>


              </a-form>
            </a-card>

            <!-- 存储与文件设置 -->
            <a-card title="存储与文件设置" :bordered="false" class="setting-card">
              <a-form :model="storageSettings" layout="vertical">
                <a-row :gutter="16">
                  <a-col :span="8">
                    <a-form-item label="音频文件保存天数" name="audioRetentionDays">
                      <a-input-number 
                        v-model:value="storageSettings.audioRetentionDays" 
                        :min="1" 
                        :max="365"
                        size="large"
                        style="width: 100%"
                        addon-after="天"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="8">
                    <a-form-item label="最大文件大小" name="maxFileSize">
                      <a-input-number 
                        v-model:value="storageSettings.maxFileSize" 
                        :min="1" 
                        :max="1000"
                        size="large"
                        style="width: 100%"
                        addon-after="MB"
                      />
                    </a-form-item>
                  </a-col>
                  <a-col :span="8">
                    <a-form-item label="自动清理周期" name="cleanupInterval">
                      <a-select 
                        v-model:value="storageSettings.cleanupInterval" 
                        size="large"
                      >
                        <a-select-option value="daily">每日</a-select-option>
                        <a-select-option value="weekly">每周</a-select-option>
                        <a-select-option value="monthly">每月</a-select-option>
                      </a-select>
                    </a-form-item>
                  </a-col>
                </a-row>

                <a-form-item>
                  <a-checkbox v-model:checked="storageSettings.enableAutoBackup">
                    启用自动备份
                  </a-checkbox>
                  <span style="margin-left: 8px; color: #666;">定期备份重要数据和配置</span>
                </a-form-item>
              </a-form>
            </a-card>
          </div>
        </a-col>

        <!-- 右侧：系统状态和快速操作 -->
        <a-col :span="8">
          <div class="status-section">
            <!-- 系统状态概览 -->
            <a-card title="系统状态" :bordered="false" class="status-card">
              <template #extra>
                <a-button type="text" size="small" @click="refreshSystemStatus" :loading="statusLoading">
                  <ReloadOutlined />
                  刷新
                </a-button>
              </template>

              <div class="status-items">
                <div class="status-item">
                  <div class="status-icon" :class="getStatusClass(systemStatus.database)">
                    <DatabaseOutlined />
                  </div>
                  <div class="status-content">
                    <div class="status-label">数据库</div>
                    <div class="status-value">{{ getStatusText(systemStatus.database) }}</div>
                  </div>
                </div>

                <div class="status-item">
                  <div class="status-icon" :class="getStatusClass(systemStatus.tts_service)">
                    <SoundOutlined />
                  </div>
                  <div class="status-content">
                    <div class="status-label">TTS服务</div>
                    <div class="status-value">{{ getStatusText(systemStatus.tts_service) }}</div>
                  </div>
                </div>

                <div class="status-item">
                  <div class="status-icon" :class="getStatusClass(systemStatus.ollama_service || 'unknown')">
                    <RobotOutlined />
                  </div>
                  <div class="status-content">
                    <div class="status-label">Ollama服务</div>
                    <div class="status-value">{{ getStatusText(systemStatus.ollama_service || 'unknown') }}</div>
                  </div>
                </div>
              </div>
            </a-card>

            <!-- 快速操作 -->
            <a-card title="快速操作" :bordered="false" class="action-card">
              <div class="quick-actions">
                <a-button type="primary" block @click="testTTSService" :loading="testing.tts">
                  <SoundOutlined />
                  测试TTS服务
                </a-button>
                
                <a-button block @click="testOllamaService" :loading="testing.ollama">
                  <RobotOutlined />
                  测试Ollama服务
                </a-button>
                
                <a-button block @click="clearCache" :loading="clearing">
                  <ClearOutlined />
                  清理系统缓存
                </a-button>
                
                <a-button block @click="exportSettings">
                  <ExportOutlined />
                  导出设置
                </a-button>
                
                <a-upload
                  :show-upload-list="false"
                  accept=".json"
                  :before-upload="importSettings"
                  style="width: 100%"
                >
                  <a-button block>
                    <ImportOutlined />
                    导入设置
                  </a-button>
                </a-upload>
              </div>
            </a-card>

            <!-- 版本信息 -->
            <a-card title="版本信息" :bordered="false" class="version-card">
              <div class="version-info">
                <div class="version-item">
                  <span class="version-label">系统版本:</span>
                  <span class="version-value">{{ appVersion }}</span>
                </div>
                <div class="version-item">
                  <span class="version-label">构建时间:</span>
                  <span class="version-value">{{ buildTime }}</span>
                </div>
                <div class="version-item">
                  <span class="version-label">运行时长:</span>
                  <span class="version-value">{{ systemUptime }}</span>
                </div>
              </div>
            </a-card>
          </div>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { useAppStore } from '@/stores/app'
import apiClient from '@/api/config'
import {
  SaveOutlined, ReloadOutlined, PictureOutlined, UploadOutlined, 
  DeleteOutlined, GlobalOutlined, InfoCircleOutlined, DatabaseOutlined,
  SoundOutlined, RobotOutlined, ClearOutlined, ExportOutlined, ImportOutlined
} from '@ant-design/icons-vue'

// Store
const appStore = useAppStore()

// 响应式数据
const saving = ref(false)
const statusLoading = ref(false)
const clearing = ref(false)

// 测试状态
const testing = reactive({
  tts: false,
  ollama: false
})

// 站点设置
const siteSettings = reactive({
  siteName: 'AI-Sound 智能语音平台',
  siteSubtitle: '专业的AI语音合成解决方案',
  siteDescription: '基于最新AI技术的语音合成平台，支持多种语音模型、情感表达和个性化定制，为您提供专业的语音解决方案。',
  adminEmail: 'admin@ai-sound.com',
  supportContact: 'support@ai-sound.com',
  logo: '',
  favicon: ''
})

// 主题设置
const themeSettings = reactive({
  mode: 'system',
  colorScheme: 'blue',
  layout: 'comfortable',
  sidebarStyle: 'gradient',
  cardStyle: 'rounded',
  enableAnimations: true,
  compactMode: false
})

// 颜色方案配置
const colorSchemes = {
  blue: {
    primary: '#1890ff',
    secondary: '#06b6d4',
    gradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)',
    sidebarGradient: 'linear-gradient(135deg, #06b6d4 0%, #0891b2 100%)'
  },
  green: {
    primary: '#52c41a',
    secondary: '#10b981',
    gradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)',
    sidebarGradient: 'linear-gradient(135deg, #10b981 0%, #059669 100%)'
  },
  purple: {
    primary: '#722ed1',
    secondary: '#8b5cf6',
    gradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)',
    sidebarGradient: 'linear-gradient(135deg, #8b5cf6 0%, #7c3aed 100%)'
  },
  red: {
    primary: '#f5222d',
    secondary: '#ef4444',
    gradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)',
    sidebarGradient: 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)'
  },
  orange: {
    primary: '#fa8c16',
    secondary: '#f97316',
    gradient: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)',
    sidebarGradient: 'linear-gradient(135deg, #f97316 0%, #ea580c 100%)'
  }
}

// AI服务设置
const aiSettings = reactive({
  ttsServiceUrl: 'http://localhost:7929',
  concurrentLimit: 3,
  ollamaServiceUrl: 'http://localhost:11434',
  defaultLlmModel: 'qwen:latest',
  
})

// 存储设置
const storageSettings = reactive({
  audioRetentionDays: 30,
  maxFileSize: 100,
  cleanupInterval: 'weekly',
  enableAutoBackup: true
})

// 系统状态
const systemStatus = computed(() => appStore.systemStatus)

// 版本信息
const appVersion = ref('2.0.0')
const buildTime = ref('2024-01-23 15:30:00')
const systemUptime = ref('3天 14小时 25分钟')

// 颜色方案名称映射
const getColorSchemeName = (key) => {
  const names = {
    blue: '海洋蓝',
    green: '森林绿', 
    purple: '优雅紫',
    red: '活力红',
    orange: '阳光橙'
  }
  return names[key] || key
}

// 主题相关方法
const previewTheme = () => {
  // 实时预览主题更改
  appStore.updateThemeSettings(themeSettings)
}

const selectColorScheme = (scheme) => {
  themeSettings.colorScheme = scheme
  previewTheme()
}

const resetThemeSettings = () => {
  Object.assign(themeSettings, {
    mode: 'system',
    colorScheme: 'blue',
    layout: 'comfortable',
    sidebarStyle: 'gradient',
    cardStyle: 'rounded',
    enableAnimations: true,
    compactMode: false
  })
  previewTheme()
  message.success('主题设置已重置')
}

const resetSiteSettings = () => {
  Object.assign(siteSettings, {
    siteName: 'AI-Sound 智能语音平台',
    siteSubtitle: '专业的AI语音合成解决方案',
    siteDescription: '基于最新AI技术的语音合成平台，支持多种语音模型、情感表达和个性化定制，为您提供专业的语音解决方案。',
    adminEmail: 'admin@ai-sound.com',
    supportContact: 'support@ai-sound.com',
    logo: '',
    favicon: ''
  })
  // 更新应用store中的站点设置
  appStore.updateSiteSettings(siteSettings)
  message.success('站点设置已重置')
}

// 方法
const saveAllSettings = async () => {
  saving.value = true
  try {
    const settingsData = {
      site: siteSettings,
      theme: themeSettings,
      ai: aiSettings,
      storage: storageSettings
    }

    // 调用后端API保存设置
    await apiClient.put('/system/settings', settingsData)
    
    // 更新应用store中的设置
    appStore.updateSiteSettings(siteSettings)
    appStore.updateThemeSettings(themeSettings)
    
    message.success('设置保存成功！')
  } catch (error) {
    console.error('保存设置失败:', error)
    message.error('保存设置失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    saving.value = false
  }
}

const refreshSystemStatus = async () => {
  statusLoading.value = true
  try {
    const response = await apiClient.get('/monitor/system-status')
    appStore.updateSystemStatus(response.data.data)
    message.success('状态刷新成功')
  } catch (error) {
    console.error('刷新状态失败:', error)
    message.error('刷新状态失败')
  } finally {
    statusLoading.value = false
  }
}

const getStatusClass = (status) => {
  switch (status) {
    case 'healthy': return 'status-healthy'
    case 'unhealthy': return 'status-unhealthy'
    case 'degraded': return 'status-degraded'
    default: return 'status-unknown'
  }
}

const getStatusText = (status) => {
  switch (status) {
    case 'healthy': return '正常'
    case 'unhealthy': return '异常'
    case 'degraded': return '降级'
    default: return '未知'
  }
}

const testTTSService = async () => {
  testing.tts = true
  try {
    // 调用TTS测试接口
    await apiClient.post('/system/test-tts')
    message.success('TTS服务测试通过！')
  } catch (error) {
    message.error('TTS服务测试失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    testing.tts = false
  }
}

const testOllamaService = async () => {
  testing.ollama = true
  try {
    // 调用Ollama测试接口
    await apiClient.post('/system/test-ollama')
    message.success('Ollama服务测试通过！')
  } catch (error) {
    message.error('Ollama服务测试失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    testing.ollama = false
  }
}

const clearCache = async () => {
  clearing.value = true
  try {
    await apiClient.post('/system/clear-cache')
    message.success('系统缓存清理完成！')
  } catch (error) {
    message.error('清理缓存失败: ' + (error.response?.data?.detail || error.message))
  } finally {
    clearing.value = false
  }
}

const exportSettings = () => {
  const settings = {
    site: siteSettings,
    ai: aiSettings,
    storage: storageSettings,
    exportTime: new Date().toISOString()
  }
  
  const dataStr = JSON.stringify(settings, null, 2)
  const dataBlob = new Blob([dataStr], { type: 'application/json' })
  const url = URL.createObjectURL(dataBlob)
  
  const link = document.createElement('a')
  link.href = url
  link.download = `ai-sound-settings-${new Date().toISOString().split('T')[0]}.json`
  link.click()
  
  URL.revokeObjectURL(url)
  message.success('设置导出成功！')
}

const importSettings = (file) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    try {
      const settings = JSON.parse(e.target.result)
      
      if (settings.site) Object.assign(siteSettings, settings.site)
      if (settings.ai) Object.assign(aiSettings, settings.ai)
      if (settings.storage) Object.assign(storageSettings, settings.storage)
      
      message.success('设置导入成功！请记得保存设置。')
    } catch (error) {
      message.error('导入文件格式错误！')
    }
  }
  reader.readAsText(file)
  return false // 阻止默认上传行为
}

const handleLogoUpload = (file) => {
  // 验证文件类型和大小
  const isImage = file.type.startsWith('image/')
  const isLt2M = file.size / 1024 / 1024 < 2

  if (!isImage) {
    message.error('只能上传图片文件！')
    return false
  }
  if (!isLt2M) {
    message.error('图片大小不能超过2MB！')
    return false
  }
  return true
}

const uploadLogo = ({ file }) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    siteSettings.logo = e.target.result
    // 实时更新到store，让LOGO立即生效
    appStore.updateSiteSettings(siteSettings)
    message.success('LOGO上传成功！')
  }
  reader.readAsDataURL(file)
}

const removeLogo = () => {
  siteSettings.logo = ''
  // 实时更新到store
  appStore.updateSiteSettings(siteSettings)
  message.success('LOGO已移除')
}

const handleFaviconUpload = (file) => {
  const isImage = file.type.startsWith('image/')
  const isLt1M = file.size / 1024 / 1024 < 1

  if (!isImage) {
    message.error('只能上传图片文件！')
    return false
  }
  if (!isLt1M) {
    message.error('图片大小不能超过1MB！')
    return false
  }
  return true
}

const uploadFavicon = ({ file }) => {
  const reader = new FileReader()
  reader.onload = (e) => {
    siteSettings.favicon = e.target.result
    // 实时更新到store，让Favicon立即生效
    appStore.updateSiteSettings(siteSettings)
    message.success('Favicon上传成功！')
  }
  reader.readAsDataURL(file)
}

const loadSettings = async () => {
  try {
    const response = await apiClient.get('/system/settings')
    const settings = response.data.data
    
    if (settings.site) Object.assign(siteSettings, settings.site)
    if (settings.theme) Object.assign(themeSettings, settings.theme)
    if (settings.ai) Object.assign(aiSettings, settings.ai)
    if (settings.storage) Object.assign(storageSettings, settings.storage)
    
    // 同步到store
    appStore.updateSiteSettings(siteSettings)
    appStore.updateThemeSettings(themeSettings)
  } catch (error) {
    console.error('加载设置失败:', error)
    // 使用store中的默认设置
    Object.assign(siteSettings, appStore.siteSettings)
    Object.assign(themeSettings, appStore.themeSettings)
  }
}

// 生命周期
onMounted(() => {
  // 初始化应用store（这会从localStorage恢复设置）
  appStore.initApp()
  
  // 从store获取恢复的设置
  Object.assign(siteSettings, appStore.siteSettings)
  Object.assign(themeSettings, appStore.themeSettings)
  
  // 加载后端设置
  loadSettings()
  refreshSystemStatus()
})
</script>

<style scoped>
.settings-container {
  margin: 0 auto;
}

.page-header {
  margin-bottom: 24px;
  padding: 32px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 12px;
  box-shadow: 0 8px 32px rgba(102, 126, 234, 0.3);
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
}

.title-section {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.page-title {
  display: flex;
  align-items: center;
  margin: 0;
  font-size: 28px;
  font-weight: 600;
  color: white;
}

.title-icon {
  margin-right: 12px;
  color: #ffffff;
}

.page-description {
  margin: 0;
  color: rgba(255, 255, 255, 0.85);
  font-size: 14px;
  line-height: 1.5;
}

.action-section {
  display: flex;
  gap: 16px;
}

.main-content {
  min-height: calc(100vh - 200px);
}

.settings-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.status-section {
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.setting-card, .status-card, .action-card, .version-card {
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.06);
  border: 1px solid #f0f0f0;
}

.setting-card :deep(.ant-card-head) {
  border-bottom: 1px solid #f0f0f0;
  padding: 16px 24px;
}

.setting-card :deep(.ant-card-body) {
  padding: 24px;
}

/* LOGO上传样式 */
.logo-upload-container {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

.logo-preview {
  width: 100px;
  height: 100px;
  border: 2px dashed #d9d9d9;
  border-radius: 8px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fafafa;
}

.logo-image {
  width: 96px;
  height: 96px;
  object-fit: contain;
  border-radius: 6px;
}

.logo-placeholder {
  text-align: center;
}

.logo-actions {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

/* 主题设置样式 */
.color-scheme-selector {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin: 16px 0;
}

.color-scheme-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 12px;
  border-radius: 8px;
  border: 2px solid transparent;
  transition: all 0.3s ease;
  background: #fafafa;
}

.color-scheme-item:hover {
  background: #f0f0f0;
  transform: translateY(-2px);
}

.color-scheme-item.active {
  border-color: var(--primary-color);
  background: rgba(var(--primary-color-rgb), 0.06);
  box-shadow: 0 4px 12px rgba(var(--primary-color-rgb), 0.2);
}

.color-preview {
  width: 50px;
  height: 30px;
  border-radius: 6px;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.color-name {
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

/* Favicon上传样式 */
.favicon-upload-container {
  display: flex;
  gap: 12px;
  align-items: center;
}

.favicon-preview {
  width: 40px;
  height: 40px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: #fafafa;
}

.favicon-image {
  width: 36px;
  height: 36px;
  object-fit: contain;
}

.upload-tips {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
}

.upload-tips p {
  margin: 2px 0;
}

.form-tip {
  margin-top: 8px;
  font-size: 12px;
  color: #666;
  display: flex;
  align-items: center;
}

/* 系统状态样式 */
.status-items {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.status-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px;
  background: #fafafa;
  border-radius: 8px;
}

.status-icon {
  width: 36px;
  height: 36px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: white;
  font-size: 16px;
}

.status-icon.status-healthy {
  background: linear-gradient(135deg, #52c41a 0%, #389e0d 100%);
}

.status-icon.status-unhealthy {
  background: linear-gradient(135deg, #ff4d4f 0%, #cf1322 100%);
}

.status-icon.status-degraded {
  background: linear-gradient(135deg, #fa8c16 0%, #d46b08 100%);
}

.status-icon.status-unknown {
  background: linear-gradient(135deg, #d9d9d9 0%, #bfbfbf 100%);
}

.status-content {
  flex: 1;
}

.status-label {
  font-size: 12px;
  color: #666;
  margin-bottom: 2px;
}

.status-value {
  font-size: 14px;
  font-weight: 600;
  color: #333;
}

/* 快速操作样式 */
.quick-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.quick-actions .ant-btn {
  height: 40px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
}

/* 版本信息样式 */
.version-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.version-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 8px 0;
  border-bottom: 1px solid #f0f0f0;
}

.version-item:last-child {
  border-bottom: none;
}

.version-label {
  font-size: 12px;
  color: #666;
}

.version-value {
  font-size: 12px;
  font-weight: 600;
  color: #333;
}

/* 暗黑模式适配 */
[data-theme="dark"] .page-header {
  background: linear-gradient(135deg, #1f1f1f 0%, #2d2d2d 100%) !important;
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3) !important;
}

[data-theme="dark"] .page-title {
  color: #fff !important;
}

[data-theme="dark"] .page-description {
  color: #d1d5db !important;
}

[data-theme="dark"] .setting-card,
[data-theme="dark"] .status-card,
[data-theme="dark"] .action-card,
[data-theme="dark"] .version-card {
  background-color: #1f1f1f !important;
  border-color: #434343 !important;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3) !important;
}

[data-theme="dark"] .setting-card :deep(.ant-card-head) {
  background-color: #1f1f1f !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .setting-card :deep(.ant-card-head-title) {
  color: #fff !important;
}

[data-theme="dark"] .color-scheme-item {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .color-scheme-item:hover {
  background-color: #3a3a3a !important;
}

[data-theme="dark"] .color-scheme-item.active {
  background-color: rgba(var(--primary-color-rgb), 0.15) !important;
  border-color: var(--primary-color) !important;
  box-shadow: 0 4px 12px rgba(var(--primary-color-rgb), 0.3) !important;
}

[data-theme="dark"] .color-name {
  color: #d1d5db !important;
}

[data-theme="dark"] .favicon-preview {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
}

[data-theme="dark"] .upload-tips {
  color: #d1d5db !important;
}

[data-theme="dark"] .form-tip {
  color: #d1d5db !important;
}

[data-theme="dark"] .status-item {
  background-color: #2d2d2d !important;
}

[data-theme="dark"] .status-label {
  color: #d1d5db !important;
}

[data-theme="dark"] .status-value {
  color: #fff !important;
}

[data-theme="dark"] .version-item {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .version-label {
  color: #d1d5db !important;
}

[data-theme="dark"] .version-value {
  color: #fff !important;
}

/* Ant Design 表单组件暗黑模式适配 */
[data-theme="dark"] :deep(.ant-input) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-input:hover) {
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-input:focus) {
  border-color: var(--primary-color) !important;
  box-shadow: 0 0 0 2px rgba(var(--primary-color-rgb), 0.2) !important;
}

[data-theme="dark"] :deep(.ant-input::placeholder) {
  color: #8c8c8c !important;
}

[data-theme="dark"] :deep(.ant-select) {
  background-color: #2d2d2d !important;
}

[data-theme="dark"] :deep(.ant-select-selector) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-select-selection-item) {
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-radio-button-wrapper) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-radio-button-wrapper:hover) {
  border-color: var(--primary-color) !important;
  color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-radio-button-wrapper-checked) {
  background-color: var(--primary-color) !important;
  border-color: var(--primary-color) !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-form-item-label > label) {
  color: #fff !important;
}

/* 开关组件暗黑模式适配 */
[data-theme="dark"] :deep(.ant-switch) {
  background-color: #434343 !important;
}

[data-theme="dark"] :deep(.ant-switch-checked) {
  background-color: var(--primary-color) !important;
}

/* 滑块组件暗黑模式适配 */
[data-theme="dark"] :deep(.ant-slider-track) {
  background-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-slider-handle) {
  border-color: var(--primary-color) !important;
}

[data-theme="dark"] :deep(.ant-slider-rail) {
  background-color: #434343 !important;
}

/* 按钮组件暗黑模式适配 */
[data-theme="dark"] :deep(.ant-btn-default) {
  background-color: #2d2d2d !important;
  border-color: #434343 !important;
  color: #fff !important;
}

[data-theme="dark"] :deep(.ant-btn-default:hover) {
  background-color: #3a3a3a !important;
  border-color: var(--primary-color) !important;
  color: var(--primary-color) !important;
}

/* 版本信息和所有普通文本适配 */
[data-theme="dark"] .version-info,
[data-theme="dark"] .status-items,
[data-theme="dark"] .quick-actions {
  color: #fff !important;
}

[data-theme="dark"] .version-info p,
[data-theme="dark"] .status-items p,
[data-theme="dark"] span,
[data-theme="dark"] .ant-typography {
  color: #d1d5db !important;
}

/* 通用文本颜色适配 - 确保所有文本在暗黑模式下可见 */
[data-theme="dark"] {
  color: #d1d5db !important;
}

[data-theme="dark"] h1,
[data-theme="dark"] h2,
[data-theme="dark"] h3,
[data-theme="dark"] h4,
[data-theme="dark"] h5,
[data-theme="dark"] h6 {
  color: #fff !important;
}

[data-theme="dark"] p {
  color: #d1d5db !important;
}

/* 强制所有表单标签为白色 */
[data-theme="dark"] :deep(.ant-form-item-label),
[data-theme="dark"] :deep(.ant-form-item-label *) {
  color: #fff !important;
}

@media (max-width: 1200px) {
  .main-content .ant-row {
    flex-direction: column;
  }
  
  .main-content .ant-col {
    width: 100% !important;
    max-width: 100% !important;
  }
}
</style>