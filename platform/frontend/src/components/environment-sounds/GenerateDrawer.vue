<template>
  <a-drawer
    :open="visible"
    title="🎵 生成环境音"
    placement="right"
    :width="600"
    @close="handleCancel"
    :closable="true"
    :maskClosable="false"
    :keyboard="false"
  >
    <template #extra>
      <a-space>
        <a-button @click="handleCancel">取消</a-button>
        <a-button 
          type="primary" 
          :loading="generating"
          @click="handleConfirm"
          :disabled="generating"
        >
          {{ buttonText }}
        </a-button>
      </a-space>
    </template>

    <div class="generate-form">
      <!-- 生成状态提示 -->
      <div v-if="generating && currentSoundId" class="generation-status">
        <a-alert
          :type="generationStatus === 'failed' ? 'error' : 'info'"
          :message="generationStatus === 'processing' ? '🎵 环境音正在生成中...' : '🚀 正在启动生成任务...'"
          :description="generationStatus === 'processing' ? '请耐心等待，生成完成后抽屉会自动关闭。' : '任务已提交，正在初始化生成环境...'"
          show-icon
          :closable="false"
          style="margin-bottom: 16px;"
        />
      </div>

      <a-form
        ref="formRef"
        :model="formState"
        :rules="rules"
        layout="vertical"
      >
        <!-- 基本信息 -->
        <div class="form-section">
          <h3>基本信息</h3>
          <a-form-item label="环境音名称" name="name">
            <a-input
              v-model:value="formState.name"
              placeholder="为这个环境音起个名字..."
              :maxLength="50"
              show-count
            />
          </a-form-item>

          <a-form-item label="提示词描述" name="prompt">
            <a-textarea
              v-model:value="formState.prompt"
              placeholder="描述你想要生成的环境音效，例如：'Heavy rain falling on leaves with distant thunder'..."
              :rows="4"
              :maxLength="1000"
              show-count
            />
          </a-form-item>

          <a-form-item label="分类" name="category_id">
            <a-select
              v-model:value="formState.category_id"
              placeholder="选择环境音分类"
              @change="handleCategoryChange"
            >
              <a-select-option
                v-for="category in categories"
                :key="category.id"
                :value="category.id"
              >
                {{ category.name }}
              </a-select-option>
            </a-select>
          </a-form-item>

          <a-form-item label="标签" name="tag_ids">
            <a-select
              v-model:value="formState.tag_ids"
              mode="multiple"
              placeholder="选择标签"
              :maxTagCount="5"
              :maxTagTextLength="10"
            >
              <a-select-option
                v-for="tag in tags"
                :key="tag.id"
                :value="tag.id"
              >
                <a-tag :color="tag.color">{{ tag.name }}</a-tag>
              </a-select-option>
            </a-select>
          </a-form-item>
        </div>

        <!-- 生成参数 -->
        <div class="form-section">
          <h3>生成参数</h3>
          <a-form-item label="时长 (秒)" name="duration">
            <a-input-number
              v-model:value="formState.duration"
              :min="5"
              :max="60"
              :step="5"
              style="width: 100%"
            />
            <div class="param-hint">建议时长：5-60秒</div>
          </a-form-item>

          <a-form-item label="生成步数" name="steps">
            <a-slider
              v-model:value="formState.steps"
              :min="20"
              :max="150"
              :step="5"
              :marks="{
                20: '20',
                50: '50',
                100: '100',
                150: '150'
              }"
            />
            <div class="param-hint">步数越多，生成质量越高，但耗时也越长</div>
          </a-form-item>

          <a-form-item label="CFG Scale" name="cfg_scale">
            <a-slider
              v-model:value="formState.cfg_scale"
              :min="1"
              :max="7"
              :step="0.5"
              :marks="{
                1: '1',
                3: '3',
                5: '5',
                7: '7'
              }"
            />
            <div class="param-hint">数值越高，生成结果越接近提示词描述</div>
          </a-form-item>
        </div>

        <!-- 预设模板 -->
        <div v-if="presets.length > 0" class="form-section">
          <h3>预设模板</h3>
          <div class="presets-grid">
            <div
              v-for="preset in presets"
              :key="preset.id"
              class="preset-card"
              :class="{ active: selectedPreset?.id === preset.id }"
              @click="applyPreset(preset)"
            >
              <div class="preset-content">
                <h4>{{ preset.name }}</h4>
                <p>{{ preset.description }}</p>
                <div class="preset-examples">
                  <a-tag v-for="(prompt, index) in preset.example_prompts.slice(0, 2)"
                    :key="index"
                    color="blue"
                  >
                    {{ prompt }}
                  </a-tag>
                </div>
              </div>
            </div>
          </div>
        </div>
      </a-form>
    </div>
  </a-drawer>
</template>

<script setup>
import { ref, reactive, watch, onUnmounted, computed } from 'vue'
import { message } from 'ant-design-vue'
import { environmentSoundsAPI } from '@/api'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  categories: {
    type: Array,
    default: () => []
  },
  tags: {
    type: Array,
    default: () => []
  },
  presets: {
    type: Array,
    default: () => []
  }
})

// Emits
const emit = defineEmits(['update:visible', 'generated'])

// 表单状态
const formRef = ref()
const generating = ref(false)
const selectedPreset = ref(null)
const currentSoundId = ref(null)
const generationStatus = ref('')
const generationProgress = ref(0)
const statusCheckInterval = ref(null)

const formState = reactive({
  name: '',
  prompt: '',
  description: '',
  category_id: undefined,
  tag_ids: [],
  duration: 15,
  steps: 50,
  cfg_scale: 3.5
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入环境音名称' },
    { max: 50, message: '名称最多50个字符' }
  ],
  prompt: [
    { required: true, message: '请输入提示词描述' },
    { max: 1000, message: '提示词最多1000个字符' }
  ],
  category_id: [
    { required: true, message: '请选择分类' }
  ]
}

// 计算属性
const buttonText = computed(() => {
  if (!generating.value) return '开始生成'
  if (generationStatus.value === 'processing') return '生成中...'
  return '启动生成中...'
})

// 方法
const handleCategoryChange = (categoryId) => {
  // 根据分类加载预设
  selectedPreset.value = null
}

const applyPreset = (preset) => {
  selectedPreset.value = preset
  formState.name = preset.name
  formState.prompt = preset.example_prompts[0]
  formState.duration = preset.default_duration
  formState.steps = preset.default_steps
  formState.cfg_scale = preset.default_cfg_scale
  formState.category_id = preset.category_id
}

const handleConfirm = async () => {
  try {
    await formRef.value.validate()
    generating.value = true
    
    const response = await environmentSoundsAPI.generateEnvironmentSound(formState)
    // 修复：检查正确的响应格式，后端返回的是 {sound_id, status, message, estimated_time}
    if (response.data && response.data.sound_id) {
      currentSoundId.value = response.data.sound_id
      generationStatus.value = response.data.status
      generationProgress.value = 0
      
      message.info(response.data.message || '环境音生成任务已启动')
      
      // 🔄 开始监听生成状态，不立即关闭抽屉
      startStatusMonitoring()
      
    } else {
      message.error('生成请求失败：响应格式错误')
      generating.value = false
    }
  } catch (error) {
    console.error('生成失败:', error)
    message.error(error.response?.data?.detail || '生成失败')
    generating.value = false
  }
}

// 🔄 状态监听逻辑
const startStatusMonitoring = () => {
  if (statusCheckInterval.value) {
    clearInterval(statusCheckInterval.value)
  }
  
  statusCheckInterval.value = setInterval(async () => {
    await checkGenerationStatus()
  }, 2000) // 每2秒检查一次
}

const checkGenerationStatus = async () => {
  if (!currentSoundId.value) return
  
  try {
    const response = await environmentSoundsAPI.getEnvironmentSound(currentSoundId.value)
    const sound = response.data
    
    generationStatus.value = sound.generation_status
    generationProgress.value = sound.generation_progress || 0
    
    if (sound.generation_status === 'completed') {
      // ✅ 生成成功 - 关闭抽屉并提示成功
      clearInterval(statusCheckInterval.value)
      statusCheckInterval.value = null
      
      message.success(`环境音"${sound.name}"生成完成！`)
      emit('generated', currentSoundId.value)
      
      // 重置状态并关闭
      resetState()
      emit('update:visible', false)
      
    } else if (sound.generation_status === 'failed') {
      // ❌ 生成失败 - 不关闭抽屉，提示失败
      clearInterval(statusCheckInterval.value)
      statusCheckInterval.value = null
      generating.value = false
      
      message.error(`环境音生成失败: ${sound.error_message || '未知错误'}`)
      // 保持抽屉打开，用户可以修改参数重试
    }
    
  } catch (error) {
    console.error('检查生成状态失败:', error)
    // 如果检查失败，继续尝试
  }
}

const resetState = () => {
  generating.value = false
  currentSoundId.value = null
  generationStatus.value = ''
  generationProgress.value = 0
  
  if (statusCheckInterval.value) {
    clearInterval(statusCheckInterval.value)
    statusCheckInterval.value = null
  }
}

const handleCancel = () => {
  resetState()
  formRef.value?.resetFields()
  selectedPreset.value = null
  emit('update:visible', false)
}

// 监听visible变化，重置表单
watch(() => props.visible, (val) => {
  if (!val) {
    resetState() // 确保清理状态监听
  }
})

// 组件卸载时清理
onUnmounted(() => {
  resetState()
})
</script>

<style scoped>
.generate-form {
  padding: 0 24px;
}

.form-section {
  margin-bottom: 32px;
}

.form-section h3 {
  margin-bottom: 16px;
  font-size: 16px;
  font-weight: 600;
  color: #1f1f1f;
}

.param-hint {
  margin-top: 4px;
  color: #666;
  font-size: 12px;
}

.presets-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 16px;
  margin-top: 16px;
}

.preset-card {
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 16px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.preset-card:hover {
  border-color: #1890ff;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.09);
}

.preset-card.active {
  border-color: #1890ff;
  background: #e6f7ff;
}

.preset-content h4 {
  margin: 0 0 8px 0;
  font-size: 14px;
  font-weight: 600;
}

.preset-content p {
  margin: 0 0 12px 0;
  font-size: 12px;
  color: #666;
}

.preset-examples {
  display: flex;
  flex-wrap: wrap;
  gap: 4px;
}

:deep(.ant-drawer-body) {
  padding: 0;
}

:deep(.ant-drawer-header) {
  padding: 16px 24px;
}

:deep(.ant-form-item) {
  margin-bottom: 24px;
}

/* 暗黑模式适配 */
[data-theme="dark"] .generate-form {
  background: transparent !important;
}

[data-theme="dark"] .form-section h3 {
  color: #fff !important;
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .param-hint {
  color: #8c8c8c !important;
}

[data-theme="dark"] .preset-card {
  background: #2d2d2d !important;
  border-color: #434343 !important;
  color: #434343 !important;
}

[data-theme="dark"] .preset-card:hover {
  border-color: #4a9eff !important;
  box-shadow: 0 2px 8px rgba(74, 158, 255, 0.2) !important;
}

[data-theme="dark"] .preset-card.active {
  border-color: #4a9eff !important;
  background: #1a2332 !important;
}

[data-theme="dark"] .preset-content h4 {
  color: #fff !important;
}

[data-theme="dark"] .preset-content p {
  color: #8c8c8c !important;
}
</style>