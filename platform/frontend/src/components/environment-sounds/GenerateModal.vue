<template>
  <a-modal
    v-model:visible="visible"
    title="生成环境音"
    width="800px"
    :confirm-loading="generating"
    @ok="handleGenerate"
    @cancel="handleCancel"
  >
    <div class="generate-modal">
      <!-- 预设选择 -->
      <div class="preset-section">
        <h4>选择预设模板</h4>
        <div class="preset-grid">
          <div
            v-for="preset in presets"
            :key="preset.id"
            class="preset-card"
            :class="{ 'selected': selectedPreset?.id === preset.id }"
            @click="selectPreset(preset)"
          >
            <div class="preset-name">{{ preset.name }}</div>
            <div class="preset-description">{{ preset.description }}</div>
            <div class="preset-params">
              {{ preset.default_duration }}s • {{ preset.default_steps }} steps • CFG {{ preset.default_cfg_scale }}
            </div>
          </div>
        </div>
      </div>

      <!-- 示例提示词 -->
      <div v-if="selectedPreset && selectedPreset.example_prompts?.length" class="examples-section">
        <h4>示例提示词</h4>
        <div class="examples-grid">
          <div
            v-for="(example, index) in selectedPreset.example_prompts"
            :key="index"
            class="example-item"
            @click="useExample(example)"
          >
            <QuestionCircleOutlined class="example-icon" />
            <span class="example-text">{{ example }}</span>
          </div>
        </div>
      </div>

      <!-- 生成表单 -->
      <a-form
        ref="formRef"
        :model="form"
        :rules="rules"
        layout="vertical"
        class="generate-form"
      >
        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="环境音名称" name="name">
              <a-input
                v-model:value="form.name"
                placeholder="为你的环境音起个名字"
                maxlength="200"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="环境音描述提示词" name="prompt">
              <a-textarea
                v-model:value="form.prompt"
                placeholder="详细描述你想要生成的环境音，例如：Heavy rain falling on leaves with distant thunder"
                :rows="4"
                maxlength="1000"
                show-count
              />
              <div class="prompt-tips">
                <a-alert
                  message="提示词建议"
                  description="使用英文描述效果更佳。可以包含声音类型、环境、强度、距离等细节。例如：'Birds chirping in a forest with gentle wind'、'Ocean waves crashing on rocks'等。"
                  type="info"
                  show-icon
                />
              </div>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="24">
            <a-form-item label="详细描述（可选）" name="description">
              <a-textarea
                v-model:value="form.description"
                placeholder="添加更多描述信息，帮助你更好地管理这个环境音"
                :rows="2"
                maxlength="500"
              />
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="8">
            <a-form-item label="音频时长（秒）" name="duration">
              <a-input-number
                v-model:value="form.duration"
                :min="1"
                :max="30"
                :step="0.5"
                style="width: 100%"
              />
              <div class="param-tip">建议5-15秒，时长越长生成时间越久</div>
            </a-form-item>
          </a-col>

          <a-col :span="8">
            <a-form-item label="推理步数" name="steps">
              <a-input-number
                v-model:value="form.steps"
                :min="10"
                :max="200"
                :step="10"
                style="width: 100%"
              />
              <div class="param-tip">步数越多质量越高，但生成时间更长</div>
            </a-form-item>
          </a-col>

          <a-col :span="8">
            <a-form-item label="CFG强度" name="cfg_scale">
              <a-input-number
                v-model:value="form.cfg_scale"
                :min="1"
                :max="10"
                :step="0.5"
                style="width: 100%"
              />
              <div class="param-tip">控制与提示词的相关性，建议3-5</div>
            </a-form-item>
          </a-col>
        </a-row>

        <a-row :gutter="16">
          <a-col :span="12">
            <a-form-item label="分类" name="category_id">
              <a-select
                v-model:value="form.category_id"
                placeholder="选择分类"
                allowClear
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
          </a-col>

          <a-col :span="12">
            <a-form-item label="标签" name="tag_ids">
              <a-select
                v-model:value="form.tag_ids"
                mode="multiple"
                placeholder="选择标签"
                allowClear
              >
                <a-select-option
                  v-for="tag in tags"
                  :key="tag.id"
                  :value="tag.id"
                >
                  <a-tag :color="tag.color" style="margin: 0;">
                    {{ tag.name }}
                  </a-tag>
                </a-select-option>
              </a-select>
            </a-form-item>
          </a-col>
        </a-row>

        <!-- 生成时间估算 -->
        <div class="generation-estimate">
          <a-alert
            :message="`预计生成时间：${estimatedTime}秒`"
            type="warning"
            show-icon
          />
        </div>
      </a-form>
    </div>

    <template #footer>
      <a-button @click="handleCancel">取消</a-button>
      <a-button
        type="primary"
        :loading="generating"
        @click="handleGenerate"
      >
        {{ generating ? '生成中...' : '开始生成' }}
      </a-button>
    </template>
  </a-modal>
</template>

<script setup>
import { ref, reactive, computed, watch } from 'vue'
import { message } from 'ant-design-vue'
import { QuestionCircleOutlined } from '@ant-design/icons-vue'
import api from '@/api'

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

// 响应式数据
const formRef = ref()
const generating = ref(false)
const selectedPreset = ref(null)

// 表单数据
const form = reactive({
  name: '',
  prompt: '',
  description: '',
  duration: 10,
  steps: 50,
  cfg_scale: 3.5,
  category_id: null,
  tag_ids: []
})

// 表单验证规则
const rules = {
  name: [
    { required: true, message: '请输入环境音名称', trigger: 'blur' },
    { max: 200, message: '名称不能超过200个字符', trigger: 'blur' }
  ],
  prompt: [
    { required: true, message: '请输入环境音描述提示词', trigger: 'blur' },
    { max: 1000, message: '提示词不能超过1000个字符', trigger: 'blur' }
  ],
  duration: [
    { required: true, message: '请输入音频时长', trigger: 'blur' },
    { type: 'number', min: 1, max: 30, message: '时长必须在1-30秒之间', trigger: 'blur' }
  ],
  steps: [
    { required: true, message: '请输入推理步数', trigger: 'blur' },
    { type: 'number', min: 10, max: 200, message: '步数必须在10-200之间', trigger: 'blur' }
  ],
  cfg_scale: [
    { required: true, message: '请输入CFG强度', trigger: 'blur' },
    { type: 'number', min: 1, max: 10, message: 'CFG强度必须在1-10之间', trigger: 'blur' }
  ]
}

// 计算属性
const visible = computed({
  get: () => props.visible,
  set: (value) => emit('update:visible', value)
})

const estimatedTime = computed(() => {
  // 基于时长和步数估算生成时间
  const baseTime = form.duration * 0.3
  const stepsMultiplier = form.steps / 50
  return Math.ceil(baseTime * stepsMultiplier)
})

// 监听器
watch(() => props.visible, (newVal) => {
  if (newVal) {
    resetForm()
  }
})

// 方法
const selectPreset = (preset) => {
  selectedPreset.value = preset
  
  // 应用预设参数
  form.duration = preset.default_duration
  form.steps = preset.default_steps
  form.cfg_scale = preset.default_cfg_scale
  form.category_id = preset.category_id
  
  // 如果有提示词模板，自动填充第一个
  if (preset.prompt_templates && preset.prompt_templates.length > 0) {
    form.prompt = preset.prompt_templates[0]
  }
  
  // 自动生成名称
  if (!form.name) {
    form.name = `${preset.name}_${Date.now().toString().slice(-6)}`
  }
}

const useExample = (example) => {
  form.prompt = example
  
  // 根据示例生成名称
  if (!form.name) {
    const words = example.split(' ').slice(0, 3).join(' ')
    form.name = words.charAt(0).toUpperCase() + words.slice(1)
  }
}

const handleGenerate = async () => {
  try {
    // 表单验证
    await formRef.value.validate()
    
    generating.value = true
    
    // 调用生成API
    const response = await api.post('/api/v1/environment-sounds/generate', form)
    const result = response.data
    
    if (result.success) {
      message.success('环境音生成任务已启动，请等待生成完成')
      emit('generated', result.sound_id)
      handleCancel()
    } else {
      message.error(result.message || '生成失败')
    }
    
  } catch (error) {
    console.error('生成环境音失败:', error)
    if (error.response?.data?.detail) {
      message.error(error.response.data.detail)
    } else {
      message.error('生成失败，请检查网络连接')
    }
  } finally {
    generating.value = false
  }
}

const handleCancel = () => {
  visible.value = false
  resetForm()
}

const resetForm = () => {
  selectedPreset.value = null
  Object.assign(form, {
    name: '',
    prompt: '',
    description: '',
    duration: 10,
    steps: 50,
    cfg_scale: 3.5,
    category_id: null,
    tag_ids: []
  })
  
  // 清除表单验证状态
  if (formRef.value) {
    formRef.value.clearValidate()
  }
}
</script>

<style scoped>
.generate-modal {
  max-height: 70vh;
  overflow-y: auto;
}

.preset-section {
  margin-bottom: 24px;
}

.preset-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.preset-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 12px;
  margin-bottom: 16px;
}

.preset-card {
  padding: 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.preset-card:hover {
  border-color: #1890ff;
  background: #f6f8ff;
}

.preset-card.selected {
  border-color: #1890ff;
  background: #e6f7ff;
}

.preset-name {
  font-weight: 600;
  color: #1a1a1a;
  margin-bottom: 4px;
}

.preset-description {
  font-size: 12px;
  color: #666;
  margin-bottom: 8px;
  line-height: 1.4;
}

.preset-params {
  font-size: 11px;
  color: #999;
}

.examples-section {
  margin-bottom: 24px;
}

.examples-section h4 {
  margin: 0 0 12px 0;
  font-size: 16px;
  font-weight: 600;
  color: #1a1a1a;
}

.examples-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.example-item {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 12px;
  border: 1px solid #f0f0f0;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.example-item:hover {
  border-color: #1890ff;
  background: #f6f8ff;
}

.example-icon {
  color: #1890ff;
  flex-shrink: 0;
}

.example-text {
  font-size: 14px;
  color: #666;
  line-height: 1.4;
}

.generate-form {
  border-top: 1px solid #f0f0f0;
  padding-top: 24px;
}

.param-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
  line-height: 1.3;
}

.prompt-tips {
  margin-top: 8px;
}

.generation-estimate {
  margin-top: 16px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .preset-grid {
    grid-template-columns: 1fr;
  }
  
  .generate-modal {
    max-height: 80vh;
  }
}
</style> 