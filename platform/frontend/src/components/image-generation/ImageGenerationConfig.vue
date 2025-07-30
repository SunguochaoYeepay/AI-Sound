<template>
  <div class="image-config-container">
    <a-form layout="vertical" :model="localConfig">
      <a-row :gutter="16">
        <!-- 预设选择 -->
        <a-col :span="8">
          <a-form-item label="生成预设">
            <a-select
              v-model:value="localConfig.preset_id"
              placeholder="选择预设模板"
              @change="onPresetChange"
              allow-clear
            >
              <a-select-option 
                v-for="preset in presets" 
                :key="preset.id" 
                :value="preset.id"
              >
                {{ preset.name }} - {{ preset.category }}
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        
        <!-- 图片尺寸 -->
        <a-col :span="8">
          <a-form-item label="图片尺寸">
            <a-select
              v-model:value="dimensionPreset"
              placeholder="选择尺寸"
              @change="onDimensionChange"
            >
              <a-select-option value="512x512">512×512 (1:1)</a-select-option>
              <a-select-option value="768x512">768×512 (3:2)</a-select-option>
              <a-select-option value="512x768">512×768 (2:3)</a-select-option>
              <a-select-option value="1024x1024">1024×1024 (1:1)</a-select-option>
              <a-select-option value="1024x768">1024×768 (4:3)</a-select-option>
              <a-select-option value="768x1024">768×1024 (3:4)</a-select-option>
              <a-select-option value="custom">自定义</a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
        
        <!-- 生成模型 -->
        <a-col :span="8">
          <a-form-item label="生成模型">
            <a-select
              v-model:value="localConfig.model"
              placeholder="选择模型"
              :loading="loadingModels"
            >
              <a-select-option 
                v-for="model in models" 
                :key="model.name" 
                :value="model.name"
              >
                {{ model.name }} ({{ model.type }})
              </a-select-option>
            </a-select>
          </a-form-item>
        </a-col>
      </a-row>
      
      <!-- 自定义尺寸 -->
      <a-row :gutter="16" v-if="dimensionPreset === 'custom'">
        <a-col :span="12">
          <a-form-item label="宽度">
            <a-input-number
              v-model:value="localConfig.width"
              :min="256"
              :max="2048"
              :step="64"
              style="width: 100%"
              addon-after="px"
            />
          </a-form-item>
        </a-col>
        
        <a-col :span="12">
          <a-form-item label="高度">
            <a-input-number
              v-model:value="localConfig.height"
              :min="256"
              :max="2048"
              :step="64"
              style="width: 100%"
              addon-after="px"
            />
          </a-form-item>
        </a-col>
      </a-row>
      
      <!-- 高级参数 -->
      <a-collapse ghost>
        <a-collapse-panel key="advanced" header="高级参数">
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="采样步数">
                <a-slider
                  v-model:value="localConfig.params.steps"
                  :min="1"
                  :max="100"
                  :marks="{ 1: '1', 20: '20', 50: '50', 100: '100' }"
                />
                <a-input-number
                  v-model:value="localConfig.params.steps"
                  :min="1"
                  :max="100"
                  size="small"
                  style="width: 80px; margin-top: 8px"
                />
              </a-form-item>
            </a-col>
            
            <a-col :span="8">
              <a-form-item label="引导强度 (CFG)">
                <a-slider
                  v-model:value="localConfig.params.cfg"
                  :min="1"
                  :max="30"
                  :step="0.5"
                  :marks="{ 1: '1', 7: '7', 15: '15', 30: '30' }"
                />
                <a-input-number
                  v-model:value="localConfig.params.cfg"
                  :min="1"
                  :max="30"
                  :step="0.5"
                  size="small"
                  style="width: 80px; margin-top: 8px"
                />
              </a-form-item>
            </a-col>
            
            <a-col :span="8">
              <a-form-item label="采样器">
                <a-select
                  v-model:value="localConfig.params.sampler_name"
                  placeholder="选择采样器"
                >
                  <a-select-option value="euler">Euler</a-select-option>
                  <a-select-option value="euler_ancestral">Euler Ancestral</a-select-option>
                  <a-select-option value="heun">Heun</a-select-option>
                  <a-select-option value="dpm_2">DPM 2</a-select-option>
                  <a-select-option value="dpm_2_ancestral">DPM 2 Ancestral</a-select-option>
                  <a-select-option value="lms">LMS</a-select-option>
                  <a-select-option value="dpm_fast">DPM Fast</a-select-option>
                  <a-select-option value="dpm_adaptive">DPM Adaptive</a-select-option>
                  <a-select-option value="dpmpp_2s_ancestral">DPM++ 2S Ancestral</a-select-option>
                  <a-select-option value="dpmpp_sde">DPM++ SDE</a-select-option>
                  <a-select-option value="dpmpp_2m">DPM++ 2M</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
          </a-row>
          
          <a-row :gutter="16">
            <a-col :span="8">
              <a-form-item label="调度器">
                <a-select
                  v-model:value="localConfig.params.scheduler"
                  placeholder="选择调度器"
                >
                  <a-select-option value="normal">Normal</a-select-option>
                  <a-select-option value="karras">Karras</a-select-option>
                  <a-select-option value="exponential">Exponential</a-select-option>
                  <a-select-option value="sgm_uniform">SGM Uniform</a-select-option>
                  <a-select-option value="simple">Simple</a-select-option>
                  <a-select-option value="ddim_uniform">DDIM Uniform</a-select-option>
                </a-select>
              </a-form-item>
            </a-col>
            
            <a-col :span="8">
              <a-form-item label="去噪强度">
                <a-slider
                  v-model:value="localConfig.params.denoise"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  :marks="{ 0: '0', 0.5: '0.5', 1: '1' }"
                />
                <a-input-number
                  v-model:value="localConfig.params.denoise"
                  :min="0"
                  :max="1"
                  :step="0.01"
                  size="small"
                  style="width: 80px; margin-top: 8px"
                />
              </a-form-item>
            </a-col>
            
            <a-col :span="8">
              <a-form-item label="随机种子">
                <a-input-number
                  v-model:value="localConfig.params.seed"
                  placeholder="留空自动生成"
                  style="width: 100%"
                />
                <a-button 
                  size="small" 
                  @click="generateRandomSeed"
                  style="margin-top: 8px"
                >
                  随机种子
                </a-button>
              </a-form-item>
            </a-col>
          </a-row>
        </a-collapse-panel>
      </a-collapse>
      
      <!-- 预设保存 -->
      <a-divider>预设管理</a-divider>
      <a-row :gutter="16">
        <a-col :span="16">
          <a-form-item>
            <a-input
              v-model:value="newPresetName"
              placeholder="输入预设名称以保存当前配置"
            />
          </a-form-item>
        </a-col>
        <a-col :span="8">
          <a-button 
            @click="saveAsPreset"
            :disabled="!newPresetName.trim()"
          >
            保存为预设
          </a-button>
        </a-col>
      </a-row>
    </a-form>
  </div>
</template>

<script setup>
import { ref, reactive, watch, computed } from 'vue'
import { message } from 'ant-design-vue'

// Props
const props = defineProps({
  config: {
    type: Object,
    required: true
  },
  presets: {
    type: Array,
    default: () => []
  },
  models: {
    type: Array,
    default: () => []
  },
  loadingModels: {
    type: Boolean,
    default: false
  }
})

// Emits
const emit = defineEmits(['update:config', 'preset-change', 'save-preset'])

// Reactive data
const localConfig = reactive({ ...props.config })
const dimensionPreset = ref('1024x1024')
const newPresetName = ref('')

// Methods
const onPresetChange = (presetId) => {
  emit('preset-change', presetId)
}

const onDimensionChange = (preset) => {
  if (preset !== 'custom') {
    const [width, height] = preset.split('x').map(Number)
    localConfig.width = width
    localConfig.height = height
  }
}

const generateRandomSeed = () => {
  localConfig.params.seed = Math.floor(Math.random() * 2147483647)
}

const saveAsPreset = () => {
  if (!newPresetName.value.trim()) {
    message.warning('请输入预设名称')
    return
  }
  
  const presetData = {
    name: newPresetName.value.trim(),
    category: 'general',
    default_params: { ...localConfig.params },
    style_keywords: [],
    description: '用户自定义预设'
  }
  
  emit('save-preset', presetData)
  newPresetName.value = ''
  message.success('预设保存成功')
}

// Watch for config changes
watch(localConfig, (newConfig) => {
  emit('update:config', newConfig)
}, { deep: true })

// Set initial dimension preset
watch(() => [localConfig.width, localConfig.height], ([width, height]) => {
  const preset = `${width}x${height}`
  const presetOptions = ['512x512', '768x512', '512x768', '1024x1024', '1024x768', '768x1024']
  
  if (presetOptions.includes(preset)) {
    dimensionPreset.value = preset
  } else {
    dimensionPreset.value = 'custom'
  }
}, { immediate: true })
</script>

<style scoped>
.image-config-container {
  padding: 20px;
  border-radius: 8px;
  border: 1px solid #e8e8e8;
}

.ant-slider {
  margin-bottom: 0;
}

.ant-form-item {
  margin-bottom: 16px;
}

.ant-collapse {
  margin-top: 16px;
}

.ant-divider {
  margin: 24px 0 16px 0;
}
</style> 