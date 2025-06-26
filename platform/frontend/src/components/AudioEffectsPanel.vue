<template>
  <div class="audio-effects-panel">
    <div class="panel-header">
      <h3>音频效果</h3>
      <a-button size="small" @click="resetAllEffects">
        <template #icon><ReloadOutlined /></template>
        重置
      </a-button>
    </div>
    
    <div class="effects-content">
      <!-- 基础音频调节 -->
      <div class="effect-section">
        <h4>基础调节</h4>
        
        <div class="effect-item">
          <label>音量</label>
          <div class="control-group">
            <a-slider
              v-model:value="effects.volume"
              :min="0"
              :max="2"
              :step="0.01"
              @change="onVolumeChange"
            />
            <span class="value-display">{{ Math.round(effects.volume * 100) }}%</span>
          </div>
        </div>
        
        <div class="effect-item">
          <label>平衡</label>
          <div class="control-group">
            <a-slider
              v-model:value="effects.balance"
              :min="-1"
              :max="1"
              :step="0.01"
              @change="onBalanceChange"
            />
            <span class="value-display">{{ effects.balance > 0 ? 'R' : 'L' }}{{ Math.abs(Math.round(effects.balance * 100)) }}</span>
          </div>
        </div>
      </div>
      
      <!-- 均衡器 -->
      <div class="effect-section">
        <h4>
          均衡器
          <a-switch
            v-model:checked="effects.equalizer.enabled"
            size="small"
            @change="onEqualizerToggle"
          />
        </h4>
        
        <div v-if="effects.equalizer.enabled" class="equalizer-controls">
          <div class="eq-bands">
            <div
              v-for="(band, index) in effects.equalizer.bands"
              :key="index"
              class="eq-band"
            >
              <div class="band-slider">
                <a-slider
                  v-model:value="band.gain"
                  :min="-12"
                  :max="12"
                  :step="0.1"
                  vertical
                  @change="() => onEqualizerChange(index)"
                />
              </div>
              <div class="band-label">{{ band.frequency }}Hz</div>
              <div class="band-value">{{ band.gain > 0 ? '+' : '' }}{{ band.gain.toFixed(1) }}dB</div>
            </div>
          </div>
          
          <div class="eq-presets">
            <a-select
              v-model:value="selectedEqPreset"
              placeholder="选择预设"
              style="width: 100%"
              @change="applyEqualizerPreset"
            >
              <a-select-option value="flat">平坦</a-select-option>
              <a-select-option value="rock">摇滚</a-select-option>
              <a-select-option value="pop">流行</a-select-option>
              <a-select-option value="jazz">爵士</a-select-option>
              <a-select-option value="classical">古典</a-select-option>
              <a-select-option value="vocal">人声增强</a-select-option>
            </a-select>
          </div>
        </div>
      </div>
      
      <!-- 动态处理 -->
      <div class="effect-section">
        <h4>
          压缩器
          <a-switch
            v-model:checked="effects.compressor.enabled"
            size="small"
            @change="onCompressorToggle"
          />
        </h4>
        
        <div v-if="effects.compressor.enabled" class="compressor-controls">
          <div class="effect-item">
            <label>阈值</label>
            <div class="control-group">
              <a-slider
                v-model:value="effects.compressor.threshold"
                :min="-60"
                :max="0"
                :step="1"
                @change="onCompressorChange"
              />
              <span class="value-display">{{ effects.compressor.threshold }}dB</span>
            </div>
          </div>
          
          <div class="effect-item">
            <label>比例</label>
            <div class="control-group">
              <a-slider
                v-model:value="effects.compressor.ratio"
                :min="1"
                :max="20"
                :step="0.1"
                @change="onCompressorChange"
              />
              <span class="value-display">{{ effects.compressor.ratio.toFixed(1) }}:1</span>
            </div>
          </div>
          
          <div class="effect-item">
            <label>启动时间</label>
            <div class="control-group">
              <a-slider
                v-model:value="effects.compressor.attack"
                :min="0"
                :max="100"
                :step="1"
                @change="onCompressorChange"
              />
              <span class="value-display">{{ effects.compressor.attack }}ms</span>
            </div>
          </div>
          
          <div class="effect-item">
            <label>释放时间</label>
            <div class="control-group">
              <a-slider
                v-model:value="effects.compressor.release"
                :min="10"
                :max="1000"
                :step="10"
                @change="onCompressorChange"
              />
              <span class="value-display">{{ effects.compressor.release }}ms</span>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 混响效果 -->
      <div class="effect-section">
        <h4>
          混响
          <a-switch
            v-model:checked="effects.reverb.enabled"
            size="small"
            @change="onReverbToggle"
          />
        </h4>
        
        <div v-if="effects.reverb.enabled" class="reverb-controls">
          <div class="effect-item">
            <label>房间大小</label>
            <div class="control-group">
              <a-slider
                v-model:value="effects.reverb.roomSize"
                :min="0"
                :max="1"
                :step="0.01"
                @change="onReverbChange"
              />
              <span class="value-display">{{ Math.round(effects.reverb.roomSize * 100) }}%</span>
            </div>
          </div>
          
          <div class="effect-item">
            <label>湿度</label>
            <div class="control-group">
              <a-slider
                v-model:value="effects.reverb.wetness"
                :min="0"
                :max="1"
                :step="0.01"
                @change="onReverbChange"
              />
              <span class="value-display">{{ Math.round(effects.reverb.wetness * 100) }}%</span>
            </div>
          </div>
          
          <div class="effect-item">
            <label>衰减</label>
            <div class="control-group">
              <a-slider
                v-model:value="effects.reverb.decay"
                :min="0.1"
                :max="10"
                :step="0.1"
                @change="onReverbChange"
              />
              <span class="value-display">{{ effects.reverb.decay.toFixed(1) }}s</span>
            </div>
          </div>
          
          <div class="reverb-presets">
            <a-select
              v-model:value="selectedReverbPreset"
              placeholder="选择混响类型"
              style="width: 100%"
              @change="applyReverbPreset"
            >
              <a-select-option value="room">房间</a-select-option>
              <a-select-option value="hall">大厅</a-select-option>
              <a-select-option value="cathedral">教堂</a-select-option>
              <a-select-option value="studio">录音室</a-select-option>
              <a-select-option value="bathroom">浴室</a-select-option>
            </a-select>
          </div>
        </div>
      </div>
      
      <!-- 降噪处理 -->
      <div class="effect-section">
        <h4>
          降噪
          <a-switch
            v-model:checked="effects.noiseReduction.enabled"
            size="small"
            @change="onNoiseReductionToggle"
          />
        </h4>
        
        <div v-if="effects.noiseReduction.enabled" class="noise-reduction-controls">
          <div class="effect-item">
            <label>降噪强度</label>
            <div class="control-group">
              <a-slider
                v-model:value="effects.noiseReduction.strength"
                :min="0"
                :max="1"
                :step="0.01"
                @change="onNoiseReductionChange"
              />
              <span class="value-display">{{ Math.round(effects.noiseReduction.strength * 100) }}%</span>
            </div>
          </div>
          
          <div class="effect-item">
            <label>频率阈值</label>
            <div class="control-group">
              <a-slider
                v-model:value="effects.noiseReduction.threshold"
                :min="0"
                :max="1"
                :step="0.01"
                @change="onNoiseReductionChange"
              />
              <span class="value-display">{{ Math.round(effects.noiseReduction.threshold * 100) }}%</span>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <!-- 效果链控制 -->
    <div class="effects-footer">
      <div class="effect-chain-controls">
        <a-button @click="previewEffects" :loading="previewing">
          <template #icon><PlayCircleOutlined /></template>
          预览效果
        </a-button>
        <a-button type="primary" @click="applyEffects" :loading="applying">
          <template #icon><CheckOutlined /></template>
          应用效果
        </a-button>
      </div>
      
      <div class="preset-controls">
        <a-button @click="savePreset">
          <template #icon><SaveOutlined /></template>
          保存预设
        </a-button>
        <a-button @click="loadPreset">
          <template #icon><FolderOpenOutlined /></template>
          加载预设
        </a-button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, watch } from 'vue'
import { message } from 'ant-design-vue'
import {
  ReloadOutlined,
  PlayCircleOutlined,
  CheckOutlined,
  SaveOutlined,
  FolderOpenOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  audioUrl: {
    type: String,
    default: ''
  },
  initialEffects: {
    type: Object,
    default: () => ({})
  }
})

// Emits
const emit = defineEmits([
  'effects-changed',
  'preview-effects',
  'apply-effects'
])

// 状态
const previewing = ref(false)
const applying = ref(false)
const selectedEqPreset = ref('')
const selectedReverbPreset = ref('')

// 音频效果配置
const effects = reactive({
  volume: 1,
  balance: 0,
  equalizer: {
    enabled: false,
    bands: [
      { frequency: 60, gain: 0 },
      { frequency: 170, gain: 0 },
      { frequency: 310, gain: 0 },
      { frequency: 600, gain: 0 },
      { frequency: 1000, gain: 0 },
      { frequency: 3000, gain: 0 },
      { frequency: 6000, gain: 0 },
      { frequency: 12000, gain: 0 },
      { frequency: 14000, gain: 0 },
      { frequency: 16000, gain: 0 }
    ]
  },
  compressor: {
    enabled: false,
    threshold: -12,
    ratio: 3,
    attack: 3,
    release: 100
  },
  reverb: {
    enabled: false,
    roomSize: 0.5,
    wetness: 0.3,
    decay: 2.0
  },
  noiseReduction: {
    enabled: false,
    strength: 0.5,
    threshold: 0.1
  }
})

// 均衡器预设
const equalizerPresets = {
  flat: [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
  rock: [3, 2, -1, -2, -1, 1, 2, 3, 3, 3],
  pop: [-1, 1, 2, 2, 0, -1, -1, 1, 2, 3],
  jazz: [2, 1, 0, 1, -1, -1, 0, 1, 2, 2],
  classical: [3, 2, -1, -2, -1, 0, 1, 2, 3, 4],
  vocal: [-2, -1, 1, 3, 3, 2, 1, 0, -1, -2]
}

// 混响预设
const reverbPresets = {
  room: { roomSize: 0.3, wetness: 0.2, decay: 1.0 },
  hall: { roomSize: 0.7, wetness: 0.4, decay: 3.0 },
  cathedral: { roomSize: 0.9, wetness: 0.6, decay: 5.0 },
  studio: { roomSize: 0.2, wetness: 0.1, decay: 0.5 },
  bathroom: { roomSize: 0.4, wetness: 0.8, decay: 1.5 }
}

// 方法
const onVolumeChange = () => {
  emitEffectsChange()
}

const onBalanceChange = () => {
  emitEffectsChange()
}

const onEqualizerToggle = () => {
  emitEffectsChange()
}

const onEqualizerChange = (bandIndex) => {
  emitEffectsChange()
}

const applyEqualizerPreset = (presetName) => {
  if (equalizerPresets[presetName]) {
    const gains = equalizerPresets[presetName]
    effects.equalizer.bands.forEach((band, index) => {
      if (gains[index] !== undefined) {
        band.gain = gains[index]
      }
    })
    emitEffectsChange()
  }
}

const onCompressorToggle = () => {
  emitEffectsChange()
}

const onCompressorChange = () => {
  emitEffectsChange()
}

const onReverbToggle = () => {
  emitEffectsChange()
}

const onReverbChange = () => {
  emitEffectsChange()
}

const applyReverbPreset = (presetName) => {
  if (reverbPresets[presetName]) {
    const preset = reverbPresets[presetName]
    Object.assign(effects.reverb, preset)
    emitEffectsChange()
  }
}

const onNoiseReductionToggle = () => {
  emitEffectsChange()
}

const onNoiseReductionChange = () => {
  emitEffectsChange()
}

const resetAllEffects = () => {
  effects.volume = 1
  effects.balance = 0
  effects.equalizer.enabled = false
  effects.equalizer.bands.forEach(band => {
    band.gain = 0
  })
  effects.compressor.enabled = false
  effects.reverb.enabled = false
  effects.noiseReduction.enabled = false
  selectedEqPreset.value = ''
  selectedReverbPreset.value = ''
  emitEffectsChange()
  message.success('已重置所有效果')
}

const previewEffects = async () => {
  previewing.value = true
  try {
    emit('preview-effects', effects)
    message.success('开始预览效果')
  } catch (error) {
    console.error('预览效果失败:', error)
    message.error('预览效果失败')
  } finally {
    setTimeout(() => {
      previewing.value = false
    }, 1000)
  }
}

const applyEffects = async () => {
  applying.value = true
  try {
    emit('apply-effects', effects)
    message.success('效果应用成功')
  } catch (error) {
    console.error('应用效果失败:', error)
    message.error('应用效果失败')
  } finally {
    applying.value = false
  }
}

const savePreset = () => {
  // 保存预设逻辑
  message.info('保存预设功能开发中...')
}

const loadPreset = () => {
  // 加载预设逻辑
  message.info('加载预设功能开发中...')
}

const emitEffectsChange = () => {
  emit('effects-changed', effects)
}

// 监听初始效果变化
watch(() => props.initialEffects, (newEffects) => {
  if (newEffects) {
    Object.assign(effects, newEffects)
  }
}, { immediate: true, deep: true })
</script>

<style scoped>
.audio-effects-panel {
  background: #fff;
  border: 1px solid #d9d9d9;
  border-radius: 6px;
  overflow: hidden;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px;
  background: #fafafa;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h3 {
  margin: 0;
  font-size: 16px;
  font-weight: 500;
}

.effects-content {
  max-height: 600px;
  overflow-y: auto;
  padding: 16px;
}

.effect-section {
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.effect-section:last-child {
  border-bottom: none;
  margin-bottom: 0;
}

.effect-section h4 {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin: 0 0 16px 0;
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.effect-item {
  margin-bottom: 16px;
}

.effect-item label {
  display: block;
  margin-bottom: 8px;
  font-size: 12px;
  color: #666;
  font-weight: 500;
}

.control-group {
  display: flex;
  align-items: center;
  gap: 12px;
}

.control-group .ant-slider {
  flex: 1;
}

.value-display {
  min-width: 60px;
  text-align: right;
  font-size: 12px;
  color: #666;
  font-family: monospace;
}

/* 均衡器样式 */
.equalizer-controls {
  margin-top: 16px;
}

.eq-bands {
  display: flex;
  justify-content: space-between;
  align-items: end;
  margin-bottom: 16px;
  padding: 16px;
  background: #f9f9f9;
  border-radius: 4px;
}

.eq-band {
  display: flex;
  flex-direction: column;
  align-items: center;
  width: 32px;
}

.band-slider {
  height: 120px;
  margin-bottom: 8px;
}

.band-label {
  font-size: 10px;
  color: #666;
  margin-bottom: 4px;
}

.band-value {
  font-size: 10px;
  color: #333;
  font-family: monospace;
  font-weight: 500;
}

.eq-presets {
  margin-top: 12px;
}

/* 压缩器样式 */
.compressor-controls {
  margin-top: 16px;
}

/* 混响样式 */
.reverb-controls {
  margin-top: 16px;
}

.reverb-presets {
  margin-top: 12px;
}

/* 降噪样式 */
.noise-reduction-controls {
  margin-top: 16px;
}

/* 底部控制 */
.effects-footer {
  padding: 16px;
  background: #fafafa;
  border-top: 1px solid #f0f0f0;
}

.effect-chain-controls {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.preset-controls {
  display: flex;
  gap: 12px;
}

/* 响应式设计 */
@media (max-width: 768px) {
  .eq-bands {
    overflow-x: auto;
    padding: 12px;
  }
  
  .eq-band {
    min-width: 28px;
  }
  
  .band-slider {
    height: 80px;
  }
  
  .effect-chain-controls,
  .preset-controls {
    flex-direction: column;
  }
}
</style> 