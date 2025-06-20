<template>
  <div class="audio-enhancement">
    <a-card title="🎵 音频增强设置" size="small">
      <!-- 启用音效增强 -->
      <a-form-item label="启用音效增强">
        <a-switch 
          v-model:checked="enhancementEnabled"
          @change="onEnhancementToggle"
        />
        <span class="help-text">自动为小说朗读添加背景音效</span>
      </a-form-item>

      <!-- 音效设置 -->
      <div v-if="enhancementEnabled" class="enhancement-settings">
        <a-form-item label="语音音量">
          <a-slider 
            v-model:value="voiceVolume" 
            :min="0" 
            :max="100" 
            :tip-formatter="value => `${value}%`"
          />
        </a-form-item>

        <a-form-item label="背景音量">
          <a-slider 
            v-model:value="backgroundVolume" 
            :min="0" 
            :max="100" 
            :tip-formatter="value => `${value}%`"
          />
        </a-form-item>

        <a-form-item label="音效类型">
          <a-select v-model:value="effectType" placeholder="选择音效风格">
            <a-select-option value="auto">🤖 自动检测</a-select-option>
            <a-select-option value="ambient">🌅 环境音</a-select-option>
            <a-select-option value="dramatic">🎭 戏剧化</a-select-option>
            <a-select-option value="minimal">🔇 轻微背景</a-select-option>
          </a-select>
        </a-form-item>

        <!-- TangoFlux 配置 -->
        <a-divider>TangoFlux 配置</a-divider>
        
        <a-form-item label="HuggingFace Token">
          <a-input-password 
            v-model:value="hfToken"
            placeholder="输入您的 HuggingFace API Token"
            @change="onTokenChange"
          />
          <div class="help-text">
            <a href="https://huggingface.co/settings/tokens" target="_blank">
              🔗 获取 HuggingFace Token
            </a>
          </div>
        </a-form-item>

        <a-form-item label="音效质量">
          <a-radio-group v-model:value="qualitySettings">
            <a-radio value="fast">⚡ 快速 (25步)</a-radio>
            <a-radio value="balanced">⚖️ 平衡 (50步)</a-radio>
            <a-radio value="high">🎨 高质量 (100步)</a-radio>
          </a-radio-group>
        </a-form-item>

        <!-- 预览功能 -->
        <a-form-item>
          <a-space>
            <a-button 
              type="primary" 
              @click="testAudioGeneration"
              :loading="testing"
            >
              🎧 测试音效生成
            </a-button>
            <a-button @click="resetSettings">
              🔄 重置设置
            </a-button>
          </a-space>
        </a-form-item>

        <!-- 预设场景 -->
        <a-divider>快速预设</a-divider>
        <div class="preset-scenes">
          <a-tag 
            v-for="preset in presetScenes" 
            :key="preset.name"
            @click="applyPreset(preset)"
            class="preset-tag"
          >
            {{ preset.name }}
          </a-tag>
        </div>
      </div>
    </a-card>

    <!-- 音频预览 -->
    <div v-if="previewAudio" class="audio-preview">
      <a-card title="🎵 音效预览" size="small">
        <audio controls :src="previewAudio" style="width: 100%;">
          您的浏览器不支持音频播放
        </audio>
      </a-card>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import { message } from 'ant-design-vue'

// 响应式数据
const enhancementEnabled = ref(false)
const voiceVolume = ref(80)
const backgroundVolume = ref(30)
const effectType = ref('auto')
const hfToken = ref('')
const qualitySettings = ref('balanced')
const testing = ref(false)
const previewAudio = ref(null)

// 预设场景
const presetScenes = ref([
  { name: '🌧️ 雨夜', prompt: 'heavy rain and thunder storm', volumes: { voice: 85, bg: 25 } },
  { name: '🏰 古堡', prompt: 'medieval castle ambience with wind', volumes: { voice: 80, bg: 35 } },
  { name: '🌊 海边', prompt: 'ocean waves and seagulls', volumes: { voice: 75, bg: 40 } },
  { name: '🌲 森林', prompt: 'peaceful forest with birds', volumes: { voice: 80, bg: 30 } },
  { name: '🏙️ 都市', prompt: 'busy city street ambience', volumes: { voice: 85, bg: 20 } },
  { name: '🔥 战斗', prompt: 'epic battle sounds with swords', volumes: { voice: 90, bg: 45 } }
])

// 方法
const onEnhancementToggle = (enabled) => {
  if (enabled) {
    message.info('音频增强已启用，将自动为合成的语音添加背景音效')
  } else {
    message.info('音频增强已关闭')
  }
}

const onTokenChange = () => {
  if (hfToken.value) {
    localStorage.setItem('hf_token', hfToken.value)
    message.success('HuggingFace Token 已保存')
  }
}

const testAudioGeneration = async () => {
  if (!hfToken.value) {
    message.error('请先设置 HuggingFace Token')
    return
  }

  testing.value = true
  try {
    // 测试音效生成
    const testPrompt = "gentle rain and thunder in the distance"
    const response = await fetch('/api/v1/audio-enhancement/test-generation', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        prompt: testPrompt,
        token: hfToken.value,
        quality: qualitySettings.value
      })
    })

    if (response.ok) {
      const audioBlob = await response.blob()
      previewAudio.value = URL.createObjectURL(audioBlob)
      message.success('音效生成成功！请试听预览')
    } else {
      throw new Error('生成失败')
    }
  } catch (error) {
    message.error('音效生成测试失败，请检查网络和 Token 设置')
  } finally {
    testing.value = false
  }
}

const applyPreset = (preset) => {
  voiceVolume.value = preset.volumes.voice
  backgroundVolume.value = preset.volumes.bg
  message.info(`已应用预设: ${preset.name}`)
}

const resetSettings = () => {
  voiceVolume.value = 80
  backgroundVolume.value = 30
  effectType.value = 'auto'
  qualitySettings.value = 'balanced'
  message.info('设置已重置为默认值')
}

// 生命周期
onMounted(() => {
  // 加载保存的设置
  const savedToken = localStorage.getItem('hf_token')
  if (savedToken) {
    hfToken.value = savedToken
  }
})

// 暴露给父组件的方法
defineExpose({
  getSettings: () => ({
    enabled: enhancementEnabled.value,
    voiceVolume: voiceVolume.value / 100,
    backgroundVolume: backgroundVolume.value / 100,
    effectType: effectType.value,
    quality: qualitySettings.value,
    hfToken: hfToken.value
  })
})
</script>

<style scoped>
.audio-enhancement {
  margin-bottom: 16px;
}

.enhancement-settings {
  margin-top: 16px;
}

.help-text {
  color: #666;
  font-size: 12px;
  margin-left: 8px;
}

.preset-scenes {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.preset-tag {
  cursor: pointer;
  transition: all 0.3s;
}

.preset-tag:hover {
  background-color: #1890ff;
  transform: scale(1.05);
}

.audio-preview {
  margin-top: 16px;
}
</style> 