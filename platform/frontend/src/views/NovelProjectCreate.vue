<template>
  <div class="novel-project-create-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>{{ isEditing ? '编辑项目' : '创建新项目' }}</h1>
        <p>{{ isEditing ? '修改项目配置和设置' : '一次性配置您的多角色朗读项目，无需繁琐步骤' }}</p>
      </div>
      <div class="header-actions">
        <a-button @click="goBack">
          ← 返回
        </a-button>
      </div>
    </div>

    <div class="create-content-simplified">
      <a-row :gutter="24">
        <!-- 左侧：基本信息和文本上传 -->
        <a-col :span="14">
          <!-- 基本信息 -->
          <a-card title="📝 项目基本信息" :bordered="false" class="config-card">
            <a-form :model="projectForm" :rules="projectRules" ref="projectFormRef" layout="vertical">
              <a-row :gutter="16">
                <a-col :span="16">
                  <a-form-item label="项目名称" name="name" required>
                    <a-input 
                      v-model:value="projectForm.name"
                      placeholder="如：西游记朗读版"
                      size="large"
                    />
                  </a-form-item>
                </a-col>
                <a-col :span="8">
                  <a-form-item label="项目类型" name="type">
                    <a-select 
                      v-model:value="projectForm.type"
                      placeholder="类型"
                      size="large"
                    >
                      <a-select-option value="novel">小说</a-select-option>
                      <a-select-option value="story">故事</a-select-option>
                      <a-select-option value="dialogue">对话</a-select-option>
                    </a-select>
                  </a-form-item>
                </a-col>
              </a-row>

              <a-form-item label="项目描述（可选）" name="description">
                <a-textarea 
                  v-model:value="projectForm.description"
                  placeholder="简要描述项目内容..."
                  :rows="3"
                  :maxlength="200"
                  show-count
                />
              </a-form-item>
            </a-form>
          </a-card>

          <!-- 文本上传 -->
          <a-card title="📚 小说文本" :bordered="false" class="config-card">
            <a-tabs v-model:activeKey="uploadMode" size="large">
              <a-tab-pane key="file" tab="📁 文件上传">
                <a-upload-dragger
                  v-model:fileList="novelFiles"
                  :multiple="false"
                  :before-upload="beforeNovelUpload"
                  @change="handleNovelChange"
                  accept=".txt,.doc,.docx"
                  class="novel-upload-simplified"
                >
                  <div class="upload-content-simplified">
                    <div class="upload-icon">📖</div>
                    <p><strong>拖拽或点击上传文本文件</strong></p>
                    <p style="color: #666; font-size: 12px;">支持 TXT, DOC, DOCX，最大10MB</p>
                  </div>
                </a-upload-dragger>
              </a-tab-pane>

              <a-tab-pane key="text" tab="✏️ 直接输入">
                <a-textarea
                  v-model:value="directText"
                  placeholder="直接粘贴小说文本内容..."
                  :rows="8"
                  :maxlength="50000"
                  show-count
                  class="direct-input"
                />
              </a-tab-pane>
            </a-tabs>

            <!-- 文本预览统计 -->
            <div v-if="textPreview" class="text-stats-simple">
              <a-space>
                <span>📊 字数: <strong>{{ textStats.totalChars }}</strong></span>
                <span>📝 段落: <strong>{{ textStats.estimatedSegments }}</strong></span>
                <span>⏱️ 预计: <strong>{{ textStats.estimatedDuration }}</strong></span>
              </a-space>
            </div>
          </a-card>
        </a-col>

        <!-- 右侧：配置和操作 -->
        <a-col :span="10">
          <!-- 朗读设置 -->
          <a-card title="🎯 朗读设置" :bordered="false" class="config-card">
            <a-form layout="vertical">
              <a-form-item label="分段方式">
                <a-radio-group v-model:value="projectSettings.segmentMode" size="small">
                  <a-radio-button value="paragraph">段落</a-radio-button>
                  <a-radio-button value="sentence">句子</a-radio-button>
                </a-radio-group>
              </a-form-item>

              <a-form-item label="音质设置">
                <a-select v-model:value="projectSettings.audioQuality" size="large">
                  <a-select-option value="high">高音质 (推荐)</a-select-option>
                  <a-select-option value="standard">标准音质</a-select-option>
                </a-select>
              </a-form-item>

              <a-form-item label="智能功能">
                <div style="display: flex; flex-direction: column; gap: 8px;">
                  <a-checkbox v-model:checked="projectSettings.enableSmartDetection">
                    🤖 智能角色识别
                  </a-checkbox>
                  <a-checkbox v-model:checked="projectSettings.enableBgMusic">
                    🎵 背景音乐
                  </a-checkbox>
                </div>
              </a-form-item>
            </a-form>
          </a-card>

          <!-- 快速操作 -->
          <a-card title="🚀 快速创建" :bordered="false" class="config-card">
            <div class="quick-actions">
              <a-space direction="vertical" style="width: 100%;">
                <a-button 
                  type="primary" 
                  size="large" 
                  block 
                  @click="createProject" 
                  :loading="creating"
                  :disabled="!canCreate"
                >
                  {{ isEditing ? '💾 保存修改' : '✨ 创建项目' }}
                </a-button>
                
                <a-button 
                  size="large" 
                  block 
                  @click="createAndStart" 
                  :loading="creating"
                  :disabled="!canCreate"
                  style="background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%); border: none; color: white;"
                >
                  🎙️ 创建并立即开始合成
                </a-button>
              </a-space>
            </div>

            <!-- 创建提示 -->
            <a-alert 
              v-if="!canCreate" 
              message="请填写项目名称和上传文本" 
              type="warning" 
              show-icon 
              style="margin-top: 16px;"
            />

            <div v-if="canCreate" class="create-preview">
              <a-divider style="margin: 16px 0;" />
              <h4 style="margin-bottom: 8px;">📋 创建预览</h4>
              <div class="preview-item">
                <span class="preview-label">项目名称:</span>
                <span class="preview-value">{{ projectForm.name }}</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">文本长度:</span>
                <span class="preview-value">{{ textStats.totalChars }} 字</span>
              </div>
              <div class="preview-item">
                <span class="preview-label">分段方式:</span>
                <span class="preview-value">{{ getSegmentModeText(projectSettings.segmentMode) }}</span>
              </div>
            </div>
          </a-card>
        </a-col>
      </a-row>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, reactive, onMounted, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { message } from 'ant-design-vue'
import { readerAPI } from '@/api'

const router = useRouter()
const route = useRoute()

// 判断是否编辑模式
const isEditing = computed(() => !!route.params.id)

// 响应式数据
const currentStep = ref(0)
const creating = ref(false)
const uploadMode = ref('file')
const novelFiles = ref([])
const directText = ref('')
const textPreview = ref('')
const projectFormRef = ref()

// 表单数据
const projectForm = reactive({
  name: '',
  type: 'novel',
  description: '',
  tags: []
})

const projectSettings = reactive({
  segmentMode: 'paragraph',
  readingSpeed: 1.0,
  audioQuality: 'high',
  enableBgMusic: false,
  enableSmartDetection: true
})

// 表单规则
const projectRules = {
  name: [
    { required: true, message: '请输入项目名称', trigger: 'blur' },
    { min: 2, max: 50, message: '项目名称长度应为2-50个字符', trigger: 'blur' }
  ]
}

// 计算属性
const canProceed = computed(() => {
  if (currentStep.value === 0) {
    return projectForm.name && projectForm.name.trim()
  } else if (currentStep.value === 1) {
    return textPreview.value && textPreview.value.trim()
  }
  return false
})

const canCreate = computed(() => {
  return projectForm.name && 
         projectForm.name.trim() && 
         textPreview.value && 
         textPreview.value.trim()
})

const textStats = computed(() => {
  const text = textPreview.value || ''
  const totalChars = text.length
  const estimatedSegments = Math.max(1, Math.ceil(totalChars / 200))
  const estimatedMinutes = Math.ceil(totalChars / 300) // 假设每分钟300字
  const estimatedDuration = `${estimatedMinutes} 分钟`
  
  return {
    totalChars,
    estimatedSegments,
    estimatedDuration
  }
})

// 方法
const goBack = () => {
  router.push('/novel-reader')
}

const nextStep = async () => {
  if (currentStep.value === 0) {
    // 验证基本信息表单
    try {
      await projectFormRef.value.validate()
      currentStep.value++
    } catch (error) {
      message.error('请完善项目基本信息')
    }
  } else if (currentStep.value === 1) {
    if (!textPreview.value) {
      message.error('请先上传文本或输入内容')
      return
    }
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 0) {
    currentStep.value--
  }
}

const beforeNovelUpload = () => {
  return false // 阻止自动上传，手动处理
}

const handleNovelChange = async (info) => {
  if (info.fileList.length > 0) {
    const file = info.fileList[0].originFileObj
    await readFileContent(file)
  } else {
    textPreview.value = ''
  }
}

const readFileContent = async (file) => {
  if (file.size > 10 * 1024 * 1024) {
    message.error('文件大小不能超过10MB')
    return
  }
  
  try {
    const text = await readFileAsText(file)
    textPreview.value = text
    message.success('文件读取成功')
  } catch (error) {
    message.error('文件读取失败：' + error.message)
  }
}

const readFileAsText = (file) => {
  return new Promise((resolve, reject) => {
    const reader = new FileReader()
    reader.onload = e => resolve(e.target.result)
    reader.onerror = e => reject(new Error('文件读取失败'))
    reader.readAsText(file, 'UTF-8')
  })
}

const createProject = async () => {
  creating.value = true
  try {
    await projectFormRef.value.validate()
    
    const projectData = {
      name: projectForm.name.trim(),
      description: projectForm.description?.trim() || '',
      type: projectForm.type,
      text_content: textPreview.value,
      character_mapping: {}
    }
    
    console.log('[创建项目] 提交数据:', projectData)
    
    const response = await readerAPI.createProject(projectData)
    
    if (response.data.success) {
      message.success('项目创建成功')
      router.push(`/novel-reader/detail/${response.data.data.id}`)
    } else {
      message.error(response.data.message || '创建失败')
    }
  } catch (error) {
    console.error('创建项目失败:', error)
    message.error('创建项目失败')
  } finally {
    creating.value = false
  }
}

// 创建并立即开始合成
const createAndStart = async () => {
  creating.value = true
  try {
    await projectFormRef.value.validate()
    
    const projectData = {
      name: projectForm.name.trim(),
      description: projectForm.description?.trim() || '',
      type: projectForm.type,
      text_content: textPreview.value,
      character_mapping: {}
    }
    
    console.log('[创建并开始] 提交数据:', projectData)
    
    // 1. 创建项目
    const createResponse = await readerAPI.createProject(projectData)
    
    if (createResponse.data.success) {
      const projectId = createResponse.data.data.id
      message.success('项目创建成功，正在启动合成...')
      
      // 2. 立即开始合成
      try {
        const startResponse = await readerAPI.startGeneration(projectId)
        if (startResponse.data.success) {
          message.success('合成已开始！')
          router.push(`/novel-reader/detail/${projectId}`)
        } else {
          message.warning('项目创建成功，但启动合成失败，请手动开始')
          router.push(`/novel-reader/detail/${projectId}`)
        }
      } catch (startError) {
        console.error('启动合成失败:', startError)
        message.warning('项目创建成功，但启动合成失败，请手动开始')
        router.push(`/novel-reader/detail/${projectId}`)
      }
    } else {
      message.error(createResponse.data.message || '创建失败')
    }
  } catch (error) {
    console.error('创建项目失败:', error)
    message.error('创建项目失败')
  } finally {
    creating.value = false
  }
}

// 获取分段方式文本
const getSegmentModeText = (mode) => {
  const modeMap = {
    'paragraph': '按段落',
    'sentence': '按句子',
    'chapter': '按章节'
  }
  return modeMap[mode] || mode
}

// 辅助函数
const getTypeText = (type) => {
  const types = {
    'novel': '小说朗读',
    'story': '故事朗读', 
    'dialogue': '对话朗读',
    'custom': '自定义'
  }
  return types[type] || '未知'
}

const getAudioQualityText = (quality) => {
  const qualities = {
    'standard': '标准音质',
    'high': '高音质',
    'premium': '专业音质'
  }
  return qualities[quality] || '未知'
}

// 加载编辑数据（如果是编辑模式）
const loadEditData = async () => {
  if (isEditing.value) {
    try {
      const response = await readerAPI.getProjectDetail(route.params.id)
      if (response.data.success) {
        const project = response.data.data
        Object.assign(projectForm, {
          name: project.name,
          type: project.type || 'novel',
          description: project.description || '',
          tags: project.tags || []
        })
        
        if (project.settings) {
          Object.assign(projectSettings, project.settings)
        }
        
        if (project.original_text) {
          textPreview.value = project.original_text
          directText.value = project.original_text
        }
      }
    } catch (error) {
      message.error('加载项目数据失败')
      goBack()
    }
  }
}

// 监听直接输入文本变化
watch(directText, (newText) => {
  if (uploadMode.value === 'text') {
    textPreview.value = newText
  }
})

// 生命周期
onMounted(() => {
  loadEditData()
})
</script>

<style scoped>
.novel-project-create-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 32px;
  padding: 32px;
  background: linear-gradient(135deg, #06b6d4 0%, #0891b2 100%);
  border-radius: 16px;
  color: white;
}

.header-content h1 {
  margin: 0;
  font-size: 28px;
  font-weight: 700;
}

.header-content p {
  margin: 8px 0 0 0;
  font-size: 16px;
  opacity: 0.9;
}

.steps-section {
  margin-bottom: 32px;
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

.create-content {
  margin-bottom: 32px;
}

.step-content {
  min-height: 400px;
}

.config-card {
  margin-bottom: 24px;
  border-radius: 12px !important;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1) !important;
  border: none !important;
}

.setting-value {
  text-align: center;
  font-weight: 600;
  color: #06b6d4;
  font-size: 14px;
  margin-top: 8px;
}

.upload-section {
  margin-bottom: 24px;
}

.novel-upload {
  border-radius: 12px !important;
  border-color: #d1d5db !important;
  background: #f9fafb !important;
}

.upload-content {
  padding: 48px;
  text-align: center;
}

.upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.upload-content h3 {
  margin: 0 0 8px 0;
  color: #374151;
}

.upload-content p {
  margin: 0;
  color: #9ca3af;
}

.direct-input {
  border-radius: 8px !important;
  border-color: #d1d5db !important;
  font-family: 'Consolas', 'Monaco', monospace;
}

.input-tips {
  margin-top: 16px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.tip-item {
  color: #6b7280;
  font-size: 14px;
}

.text-preview {
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  overflow: hidden;
}

.preview-stats {
  display: flex;
  gap: 24px;
  padding: 16px;
  background: #f9fafb;
  border-bottom: 1px solid #e5e7eb;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
}

.stat-label {
  color: #6b7280;
}

.stat-value {
  font-weight: 600;
  color: #374151;
}

.preview-content {
  padding: 16px;
  background: white;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #374151;
  max-height: 200px;
  overflow-y: auto;
}

.confirm-text-preview {
  margin-top: 24px;
}

.confirm-text-preview h4 {
  margin-bottom: 12px;
  color: #374151;
}

.preview-box {
  padding: 16px;
  background: #f9fafb;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-family: 'Consolas', 'Monaco', monospace;
  font-size: 14px;
  line-height: 1.6;
  color: #6b7280;
  max-height: 150px;
  overflow-y: auto;
}

.action-buttons {
  display: flex;
  justify-content: center;
  padding: 24px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .novel-project-create-container {
    padding: 16px;
  }
  
  .page-header {
    flex-direction: column;
    gap: 16px;
    align-items: stretch;
  }
  
  .preview-stats {
    flex-direction: column;
    gap: 12px;
  }
}

/* 简化版样式 */
.create-content-simplified {
  padding: 24px 0;
}

.config-card {
  margin-bottom: 24px;
  border-radius: 12px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
}

.config-card .ant-card-head-title {
  font-weight: 600;
  font-size: 16px;
}

.novel-upload-simplified {
  border: 2px dashed #d1d5db;
  border-radius: 8px;
  transition: all 0.3s ease;
}

.novel-upload-simplified:hover {
  border-color: #06b6d4;
  background-color: #f0f9ff;
}

.upload-content-simplified {
  padding: 32px 16px;
  text-align: center;
}

.upload-content-simplified .upload-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.text-stats-simple {
  margin-top: 16px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 6px;
  border-left: 4px solid #06b6d4;
}

.quick-actions .ant-btn {
  height: 48px;
  font-weight: 600;
}

.create-preview {
  background: #f8fafc;
  padding: 16px;
  border-radius: 8px;
  margin-top: 16px;
}

.preview-item {
  display: flex;
  justify-content: space-between;
  margin-bottom: 8px;
}

.preview-label {
  color: #6b7280;
  font-size: 14px;
}

.preview-value {
  font-weight: 600;
  color: #1f2937;
  font-size: 14px;
}
</style> 