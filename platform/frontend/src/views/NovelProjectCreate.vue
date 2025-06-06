<template>
  <div class="novel-project-create-container">
    <!-- 页面头部 -->
    <div class="page-header">
      <div class="header-content">
        <h1>{{ isEditing ? '编辑项目' : '创建新项目' }}</h1>
        <p>{{ isEditing ? '修改项目配置和设置' : '配置您的多角色朗读项目基本信息和生成设置' }}</p>
      </div>
      <div class="header-actions">
        <a-button @click="goBack">
          ← 返回
        </a-button>
      </div>
    </div>

    <!-- 创建步骤指示器 -->
    <div class="steps-section">
      <a-steps :current="currentStep" size="small">
        <a-step title="基本信息" description="项目名称和设置" />
        <a-step title="文本上传" description="上传或输入小说文本" />
        <a-step title="确认创建" description="确认项目信息" />
      </a-steps>
    </div>

    <div class="create-content">
      <!-- 步骤1：基本信息 -->
      <div v-show="currentStep === 0" class="step-content">
        <a-card title="项目基本信息" :bordered="false" class="config-card">
          <a-form :model="projectForm" :rules="projectRules" ref="projectFormRef" layout="vertical">
            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item label="项目名称" name="name" required>
                  <a-input 
                    v-model:value="projectForm.name"
                    placeholder="请输入项目名称，如：西游记朗读版"
                    size="large"
                  />
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="项目类型" name="type">
                  <a-select 
                    v-model:value="projectForm.type"
                    placeholder="选择项目类型"
                    size="large"
                  >
                    <a-select-option value="novel">小说朗读</a-select-option>
                    <a-select-option value="story">故事朗读</a-select-option>
                    <a-select-option value="dialogue">对话朗读</a-select-option>
                    <a-select-option value="custom">自定义</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>

            <a-form-item label="项目描述" name="description">
              <a-textarea 
                v-model:value="projectForm.description"
                placeholder="简要描述这个项目的内容和目标（可选）"
                :rows="4"
                :maxlength="500"
                show-count
              />
            </a-form-item>

            <a-form-item label="标签" name="tags">
              <a-select
                v-model:value="projectForm.tags"
                mode="tags"
                placeholder="添加标签以便管理（按回车确认）"
                style="width: 100%"
              >
                <a-select-option value="武侠">武侠</a-select-option>
                <a-select-option value="言情">言情</a-select-option>
                <a-select-option value="玄幻">玄幻</a-select-option>
                <a-select-option value="科幻">科幻</a-select-option>
              </a-select>
            </a-form-item>
          </a-form>
        </a-card>

        <a-card title="朗读设置预配置" :bordered="false" class="config-card">
          <a-form layout="vertical">
            <a-row :gutter="24">
              <a-col :span="8">
                <a-form-item label="分段方式">
                  <a-radio-group v-model:value="projectSettings.segmentMode" size="large">
                    <a-radio-button value="paragraph">按段落</a-radio-button>
                    <a-radio-button value="sentence">按句子</a-radio-button>
                    <a-radio-button value="chapter">按章节</a-radio-button>
                  </a-radio-group>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="朗读速度">
                  <a-slider 
                    v-model:value="projectSettings.readingSpeed" 
                    :min="0.5" 
                    :max="2.0" 
                    :step="0.1"
                  />
                  <div class="setting-value">{{ projectSettings.readingSpeed }}x</div>
                </a-form-item>
              </a-col>
              <a-col :span="8">
                <a-form-item label="音质设置">
                  <a-select v-model:value="projectSettings.audioQuality" size="large">
                    <a-select-option value="standard">标准音质</a-select-option>
                    <a-select-option value="high">高音质</a-select-option>
                    <a-select-option value="premium">专业音质</a-select-option>
                  </a-select>
                </a-form-item>
              </a-col>
            </a-row>

            <a-row :gutter="24">
              <a-col :span="12">
                <a-form-item label="背景音乐">
                  <a-switch 
                    v-model:checked="projectSettings.enableBgMusic"
                    checked-children="开启"
                    un-checked-children="关闭"
                  />
                  <span style="margin-left: 12px; color: #666;">为朗读添加轻柔的背景音乐</span>
                </a-form-item>
              </a-col>
              <a-col :span="12">
                <a-form-item label="智能识别">
                  <a-switch 
                    v-model:checked="projectSettings.enableSmartDetection"
                    checked-children="开启"
                    un-checked-children="关闭"
                  />
                  <span style="margin-left: 12px; color: #666;">自动识别角色对话和情感</span>
                </a-form-item>
              </a-col>
            </a-row>
          </a-form>
        </a-card>
      </div>

      <!-- 步骤2：文本上传 -->
      <div v-show="currentStep === 1" class="step-content">
        <a-card title="上传小说文本" :bordered="false" class="config-card">
          <div class="upload-section">
            <a-tabs v-model:activeKey="uploadMode" size="large">
              <a-tab-pane key="file" tab="文件上传">
                <a-upload-dragger
                  v-model:fileList="novelFiles"
                  :multiple="false"
                  :before-upload="beforeNovelUpload"
                  @change="handleNovelChange"
                  accept=".txt,.doc,.docx"
                  class="novel-upload"
                >
                  <div class="upload-content">
                    <div class="upload-icon">📖</div>
                    <h3>点击或拖拽小说文件到此区域</h3>
                    <p>支持 TXT, DOC, DOCX 格式，文件大小不超过 10MB</p>
                  </div>
                </a-upload-dragger>
              </a-tab-pane>

              <a-tab-pane key="text" tab="直接输入">
                <a-textarea
                  v-model:value="directText"
                  placeholder="直接粘贴或输入小说文本内容..."
                  :rows="12"
                  :maxlength="100000"
                  show-count
                  class="direct-input"
                />
                <div class="input-tips">
                  <div class="tip-item">
                    💡 建议：请确保文本中角色对话使用引号「」或""标记
                  </div>
                  <div class="tip-item">
                    💡 提示：段落之间使用空行分隔可以获得更好的识别效果
                  </div>
                </div>
              </a-tab-pane>
            </a-tabs>
          </div>
        </a-card>

        <!-- 文本预览 -->
        <a-card v-if="textPreview" title="文本预览" :bordered="false" class="config-card">
          <div class="text-preview">
            <div class="preview-stats">
              <div class="stat-item">
                <span class="stat-label">总字数:</span>
                <span class="stat-value">{{ textStats.totalChars }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">预计段落:</span>
                <span class="stat-value">{{ textStats.estimatedSegments }}</span>
              </div>
              <div class="stat-item">
                <span class="stat-label">预计时长:</span>
                <span class="stat-value">{{ textStats.estimatedDuration }}</span>
              </div>
            </div>
            <div class="preview-content">
              {{ textPreview.substring(0, 500) }}{{ textPreview.length > 500 ? '...' : '' }}
            </div>
          </div>
        </a-card>
      </div>

      <!-- 步骤3：确认创建 -->
      <div v-show="currentStep === 2" class="step-content">
        <a-card title="确认项目信息" :bordered="false" class="config-card">
          <a-descriptions :column="2" bordered>
            <a-descriptions-item label="项目名称">
              {{ projectForm.name }}
            </a-descriptions-item>
            <a-descriptions-item label="项目类型">
              {{ getTypeText(projectForm.type) }}
            </a-descriptions-item>
            <a-descriptions-item label="项目描述" :span="2">
              {{ projectForm.description || '暂无描述' }}
            </a-descriptions-item>
            <a-descriptions-item label="分段方式">
              {{ getSegmentModeText(projectSettings.segmentMode) }}
            </a-descriptions-item>
            <a-descriptions-item label="朗读速度">
              {{ projectSettings.readingSpeed }}x
            </a-descriptions-item>
            <a-descriptions-item label="音质设置">
              {{ getAudioQualityText(projectSettings.audioQuality) }}
            </a-descriptions-item>
            <a-descriptions-item label="背景音乐">
              {{ projectSettings.enableBgMusic ? '开启' : '关闭' }}
            </a-descriptions-item>
            <a-descriptions-item label="文本来源">
              {{ uploadMode === 'file' ? '文件上传' : '直接输入' }}
            </a-descriptions-item>
            <a-descriptions-item label="文本字数">
              {{ textStats.totalChars }} 字符
            </a-descriptions-item>
          </a-descriptions>

          <div class="confirm-text-preview">
            <h4>文本内容预览:</h4>
            <div class="preview-box">
              {{ textPreview?.substring(0, 800) }}{{ textPreview?.length > 800 ? '...' : '' }}
            </div>
          </div>
        </a-card>
      </div>

      <!-- 操作按钮 -->
      <div class="action-buttons">
        <a-space size="large">
          <a-button v-if="currentStep > 0" size="large" @click="prevStep">
            上一步
          </a-button>
          <a-button v-if="currentStep < 2" type="primary" size="large" @click="nextStep" :disabled="!canProceed">
            下一步
          </a-button>
          <a-button v-if="currentStep === 2" type="primary" size="large" @click="createProject" :loading="creating">
            ✓ {{ isEditing ? '保存修改' : '创建项目' }}
          </a-button>
        </a-space>
      </div>
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
const textStats = computed(() => {
  const text = textPreview.value || ''
  const totalChars = text.length
  const estimatedSegments = Math.ceil(totalChars / 200) // 假设每段200字
  const estimatedMinutes = Math.ceil(totalChars / 300) // 假设每分钟300字
  
  return {
    totalChars,
    estimatedSegments,
    estimatedDuration: `约 ${estimatedMinutes} 分钟`
  }
})

const canProceed = computed(() => {
  if (currentStep.value === 0) {
    return projectForm.name.trim().length >= 2
  }
  if (currentStep.value === 1) {
    return textPreview.value && textPreview.value.length > 10
  }
  return true
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
  if (!textPreview.value) {
    message.error('请先上传文本内容')
    return
  }
  
  creating.value = true
  try {
    const projectData = {
      name: projectForm.name,
      type: projectForm.type,
      description: projectForm.description,
      tags: projectForm.tags,
      text_content: textPreview.value,
      settings: projectSettings,
      character_mapping: {}
    }
    
    let response
    if (isEditing.value) {
      response = await readerAPI.updateProject(route.params.id, projectData)
    } else {
      response = await readerAPI.createProject(projectData)
    }
    
    if (response.data.success) {
      message.success(isEditing.value ? '项目更新成功' : '项目创建成功')
      router.push(`/novel-reader/detail/${response.data.data.id}`)
    } else {
      message.error((isEditing.value ? '更新' : '创建') + '失败: ' + response.data.message)
    }
  } catch (error) {
    message.error((isEditing.value ? '更新' : '创建') + '失败')
  } finally {
    creating.value = false
  }
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

const getSegmentModeText = (mode) => {
  const modes = {
    'paragraph': '按段落',
    'sentence': '按句子',
    'chapter': '按章节'
  }
  return modes[mode] || '未知'
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
</style> 