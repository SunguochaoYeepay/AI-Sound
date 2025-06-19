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
        >
          开始生成
        </a-button>
      </a-space>
    </template>

    <div class="generate-form">
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
import { ref, reactive, watch } from 'vue'
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
    if (response.data.success) {
      message.success('环境音生成任务已启动')
      emit('generated', response.data.sound_id)
      handleCancel()
    }
  } catch (error) {
    console.error('生成失败:', error)
    message.error(error.response?.data?.detail || '生成失败')
  } finally {
    generating.value = false
  }
}

const handleCancel = () => {
  formRef.value?.resetFields()
  selectedPreset.value = null
  emit('update:visible', false)
}

// 监听visible变化，重置表单
watch(() => props.visible, (val) => {
  if (!val) {
    handleCancel()
  }
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
</style>