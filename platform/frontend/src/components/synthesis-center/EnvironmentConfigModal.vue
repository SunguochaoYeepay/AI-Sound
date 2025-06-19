<template>
  <a-modal
    v-model:open="visible"
    title="🌍 环境音混合配置"
    :width="500"
    @ok="handleConfirm"
    @cancel="handleCancel"
    :ok-text="'开始环境音混合合成'"
    :cancel-text="'取消'"
    :ok-button-props="{ loading: loading }"
  >
    <div class="environment-config-content">
      <div class="config-section">
        <h4>🎵 环境音效配置</h4>
        <p class="config-description">
          系统将自动分析文本内容，生成适合的环境音效并与语音进行智能混合。
        </p>
        
        <div class="config-item">
          <label class="config-label">环境音音量：</label>
          <a-slider
            v-model:value="environmentVolume"
            :min="0"
            :max="1"
            :step="0.1"
            :marks="{
              0: '0%',
              0.3: '30%',
              0.5: '50%',
              0.7: '70%',
              1: '100%'
            }"
            style="margin: 8px 0;"
          />
          <div class="volume-hint">
            当前音量：{{ Math.round(environmentVolume * 100) }}%
          </div>
        </div>
      </div>
      
      <div class="config-section">
        <h4>🎬 会生成的环境音效</h4>
        <div class="environment-examples">
          <a-tag color="blue">🌆 日出日落</a-tag>
          <a-tag color="green">🌳 森林鸟叫</a-tag>
          <a-tag color="cyan">🌊 海浪声</a-tag>
          <a-tag color="orange">🏙️ 城市噪音</a-tag>
          <a-tag color="purple">⛈️ 雷雨声</a-tag>
          <a-tag color="gold">🎵 背景音乐</a-tag>
        </div>
        <p class="examples-note">
          基于文本内容自动选择适合的环境音效
        </p>
      </div>
      
      <div class="config-section">
        <h4>⚠️ 注意事项</h4>
        <ul class="warning-list">
          <li>环境音生成需要额外时间，合成时间会显著增加</li>
          <li>需要足够的GPU资源来处理TTS和环境音生成</li>
          <li>最终文件大小会比普通TTS大一些</li>
        </ul>
      </div>
    </div>
  </a-modal>
</template>

<script setup>
import { ref, watch } from 'vue'

// Props
const props = defineProps({
  visible: {
    type: Boolean,
    default: false
  },
  loading: {
    type: Boolean,
    default: false
  },
  initialVolume: {
    type: Number,
    default: 0.3
  }
})

// Emits
const emit = defineEmits(['update:visible', 'confirm', 'cancel'])

// 环境音音量
const environmentVolume = ref(props.initialVolume)

// 监听初始音量变化
watch(() => props.initialVolume, (newValue) => {
  environmentVolume.value = newValue
})

// 处理确认
const handleConfirm = () => {
  emit('confirm', {
    environmentVolume: environmentVolume.value
  })
}

// 处理取消
const handleCancel = () => {
  emit('cancel')
  emit('update:visible', false)
}
</script>

<style scoped>
/* 环境音配置弹窗样式 */
.environment-config-content {
  .config-section {
    margin-bottom: 24px;
    
    h4 {
      margin: 0 0 12px 0;
      color: #1f2937;
      font-weight: 600;
    }
    
    .config-description {
      color: #6b7280;
      margin-bottom: 16px;
      line-height: 1.5;
    }
    
    .config-item {
      margin-bottom: 16px;
      
      .config-label {
        display: block;
        margin-bottom: 8px;
        font-weight: 500;
        color: #374151;
      }
      
      .volume-hint {
        color: #6b7280;
        font-size: 12px;
        text-align: center;
        font-weight: 600;
        margin-top: 8px;
      }
    }
    
    .environment-examples {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
      margin-bottom: 12px;
      
      :deep(.ant-tag) {
        font-size: 12px;
        padding: 4px 8px;
        border-radius: 4px;
      }
    }
    
    .examples-note {
      color: #6b7280;
      font-size: 12px;
      margin: 0;
    }
    
    .warning-list {
      margin: 0;
      padding-left: 20px;
      
      li {
        color: #6b7280;
        margin-bottom: 4px;
        font-size: 12px;
      }
    }
  }
}

@media (max-width: 768px) {
  .environment-config-content {
    .environment-examples {
      gap: 4px;
      
      :deep(.ant-tag) {
        font-size: 11px;
        padding: 2px 6px;
      }
    }
  }
}
</style>