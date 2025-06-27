<template>
  <div class="composition-info">
    <!-- 信息头部 -->
    <div class="info-header">
      <h3>项目信息</h3>
      <a-button type="text" size="small" @click="refreshInfo">
        <ReloadOutlined />
      </a-button>
    </div>

    <!-- 项目基本信息 -->
    <div class="info-section">
      <div class="section-title">基本信息</div>
      <div class="info-item">
        <label>项目名称：</label>
        <a-input 
          v-model:value="projectInfo.name" 
          size="small" 
          @blur="updateProjectInfo"
          placeholder="未命名项目"
        />
      </div>
      <div class="info-item">
        <label>创建时间：</label>
        <span>{{ formatDate(projectInfo.createTime) }}</span>
      </div>
      <div class="info-item">
        <label>总时长：</label>
        <span>{{ formatDuration(projectInfo.duration) }}</span>
      </div>
      <div class="info-item">
        <label>轨道数：</label>
        <span>{{ projectInfo.trackCount }} 个</span>
      </div>
    </div>

    <!-- 当前选中轨道信息 -->
    <div class="info-section" v-if="selectedTrack">
      <div class="section-title">当前轨道</div>
      <div class="info-item">
        <label>轨道名称：</label>
        <a-input 
          v-model:value="selectedTrack.name" 
          size="small"
          @blur="updateTrackInfo"
        />
      </div>
      <div class="info-item">
        <label>轨道类型：</label>
        <a-tag :color="getTrackTypeColor(selectedTrack.type)">
          {{ getTrackTypeName(selectedTrack.type) }}
        </a-tag>
      </div>
      <div class="info-item">
        <label>音量：</label>
        <a-slider
          v-model:value="selectedTrack.volume"
          :min="0"
          :max="100"
          :tooltip-formatter="value => `${value}%`"
          @change="updateTrackVolume"
        />
      </div>
      <div class="info-item">
        <label>静音：</label>
        <a-switch 
          v-model:checked="selectedTrack.muted" 
          size="small"
          @change="updateTrackMute"
        />
      </div>
      <div class="info-item">
        <label>独奏：</label>
        <a-switch 
          v-model:checked="selectedTrack.solo" 
          size="small"
          @change="updateTrackSolo"
        />
      </div>
    </div>

    <!-- 音频效果 -->
    <div class="info-section">
      <div class="section-title">
        音频效果
        <a-button type="text" size="small" @click="addEffect">
          <PlusOutlined />
        </a-button>
      </div>
      <div class="effects-list">
        <div 
          v-for="effect in audioEffects" 
          :key="effect.id"
          class="effect-item"
        >
          <div class="effect-header">
            <span class="effect-name">{{ effect.name }}</span>
            <a-switch 
              v-model:checked="effect.enabled" 
              size="small"
              @change="toggleEffect(effect)"
            />
          </div>
          <div class="effect-controls" v-if="effect.enabled">
            <div 
              v-for="param in effect.parameters" 
              :key="param.name"
              class="effect-param"
            >
              <label>{{ param.label }}：</label>
              <a-slider
                v-model:value="param.value"
                :min="param.min"
                :max="param.max"
                :step="param.step"
                :tooltip-formatter="value => `${value}${param.unit || ''}`"
                @change="updateEffectParam(effect, param)"
              />
            </div>
          </div>
        </div>
        
        <div v-if="audioEffects.length === 0" class="effects-empty">
          <a-empty description="暂无音频效果" size="small">
            <a-button type="primary" size="small" @click="addEffect">
              添加效果
            </a-button>
          </a-empty>
        </div>
      </div>
    </div>

    <!-- 导出设置 -->
    <div class="info-section">
      <div class="section-title">导出设置</div>
      <div class="info-item">
        <label>格式：</label>
        <a-select 
          v-model:value="exportSettings.format" 
          size="small"
          style="width: 100px;"
        >
          <a-select-option value="mp3">MP3</a-select-option>
          <a-select-option value="wav">WAV</a-select-option>
          <a-select-option value="flac">FLAC</a-select-option>
        </a-select>
      </div>
      <div class="info-item">
        <label>质量：</label>
        <a-select 
          v-model:value="exportSettings.quality" 
          size="small"
          style="width: 100px;"
        >
          <a-select-option value="high">高质量</a-select-option>
          <a-select-option value="medium">中等</a-select-option>
          <a-select-option value="low">低质量</a-select-option>
        </a-select>
      </div>
      <div class="info-item">
        <label>采样率：</label>
        <a-select 
          v-model:value="exportSettings.sampleRate" 
          size="small"
          style="width: 100px;"
        >
          <a-select-option value="44100">44.1kHz</a-select-option>
          <a-select-option value="48000">48kHz</a-select-option>
          <a-select-option value="96000">96kHz</a-select-option>
        </a-select>
      </div>
      <a-button type="primary" block @click="exportProject" :loading="exporting">
        <ExportOutlined /> 导出项目
      </a-button>
    </div>

    <!-- 效果选择模态框 -->
    <a-modal
      v-model:open="showEffectModal"
      title="添加音频效果"
      @ok="handleAddEffect"
      @cancel="showEffectModal = false"
    >
      <a-list :data-source="availableEffects" size="small">
        <template #renderItem="{ item }">
          <a-list-item>
            <a-list-item-meta
              :title="item.name"
              :description="item.description"
            />
            <a-button 
              type="link" 
              @click="selectEffect(item)"
              :disabled="audioEffects.some(e => e.type === item.type)"
            >
              添加
            </a-button>
          </a-list-item>
        </template>
      </a-list>
    </a-modal>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { 
  ReloadOutlined, PlusOutlined, ExportOutlined 
} from '@ant-design/icons-vue'
import { message } from 'ant-design-vue'

export default {
  name: 'CompositionInfo',
  components: {
    ReloadOutlined, PlusOutlined, ExportOutlined
  },
  props: {
    project: {
      type: Object,
      default: () => ({})
    },
    selectedTrack: {
      type: Object,
      default: null
    },
    tracks: {
      type: Array,
      default: () => []
    }
  },
  emits: ['updateProject', 'updateTrack', 'exportProject'],
  setup(props, { emit }) {
    // 响应式数据
    const projectInfo = ref({
      name: '',
      createTime: new Date(),
      duration: 0,
      trackCount: 0
    })

    const audioEffects = ref([])
    const exportSettings = ref({
      format: 'mp3',
      quality: 'high',
      sampleRate: '44100'
    })
    
    const showEffectModal = ref(false)
    const exporting = ref(false)

    // 可用的音频效果
    const availableEffects = ref([
      {
        type: 'reverb',
        name: '混响',
        description: '模拟房间或空间的回声效果',
        parameters: [
          { name: 'wet', label: '湿度', min: 0, max: 100, step: 1, value: 30, unit: '%' },
          { name: 'room', label: '房间大小', min: 0, max: 100, step: 1, value: 50, unit: '%' },
          { name: 'damp', label: '阻尼', min: 0, max: 100, step: 1, value: 40, unit: '%' }
        ]
      },
      {
        type: 'eq',
        name: '均衡器',
        description: '调整音频的频率响应',
        parameters: [
          { name: 'low', label: '低频', min: -20, max: 20, step: 0.1, value: 0, unit: 'dB' },
          { name: 'mid', label: '中频', min: -20, max: 20, step: 0.1, value: 0, unit: 'dB' },
          { name: 'high', label: '高频', min: -20, max: 20, step: 0.1, value: 0, unit: 'dB' }
        ]
      },
      {
        type: 'compressor',
        name: '压缩器',
        description: '动态范围压缩，平衡音量差异',
        parameters: [
          { name: 'threshold', label: '阈值', min: -60, max: 0, step: 1, value: -20, unit: 'dB' },
          { name: 'ratio', label: '比率', min: 1, max: 20, step: 0.1, value: 4, unit: ':1' },
          { name: 'attack', label: '起音', min: 0, max: 100, step: 1, value: 10, unit: 'ms' }
        ]
      },
      {
        type: 'delay',
        name: '延迟',
        description: '添加回声延迟效果',
        parameters: [
          { name: 'time', label: '延迟时间', min: 0, max: 2000, step: 10, value: 250, unit: 'ms' },
          { name: 'feedback', label: '反馈', min: 0, max: 95, step: 1, value: 30, unit: '%' },
          { name: 'mix', label: '混合', min: 0, max: 100, step: 1, value: 25, unit: '%' }
        ]
      }
    ])

    // 计算属性
    const computedProjectInfo = computed(() => ({
      ...projectInfo.value,
      duration: props.tracks.reduce((total, track) => Math.max(total, track.duration || 0), 0),
      trackCount: props.tracks.length
    }))

    // 方法
    const refreshInfo = () => {
      // 刷新项目信息
      updateProjectInfoFromProps()
    }

    const updateProjectInfoFromProps = () => {
      if (props.project) {
        projectInfo.value = {
          name: props.project.name || '未命名项目',
          createTime: props.project.createTime || new Date(),
          duration: computedProjectInfo.value.duration,
          trackCount: computedProjectInfo.value.trackCount
        }
      }
    }

    const updateProjectInfo = () => {
      emit('updateProject', projectInfo.value)
    }

    const updateTrackInfo = () => {
      if (props.selectedTrack) {
        emit('updateTrack', props.selectedTrack)
      }
    }

    const updateTrackVolume = (value) => {
      if (props.selectedTrack) {
        props.selectedTrack.volume = value
        emit('updateTrack', props.selectedTrack)
      }
    }

    const updateTrackMute = (checked) => {
      if (props.selectedTrack) {
        props.selectedTrack.muted = checked
        emit('updateTrack', props.selectedTrack)
      }
    }

    const updateTrackSolo = (checked) => {
      if (props.selectedTrack) {
        props.selectedTrack.solo = checked
        emit('updateTrack', props.selectedTrack)
      }
    }

    const getTrackTypeColor = (type) => {
      const colors = {
        audio: 'blue',
        voice: 'green',
        music: 'purple',
        environment: 'orange',
        effect: 'red'
      }
      return colors[type] || 'default'
    }

    const getTrackTypeName = (type) => {
      const names = {
        audio: '音频',
        voice: '角色音',
        music: '背景音乐',
        environment: '环境音',
        effect: '音效'
      }
      return names[type] || '未知'
    }

    const addEffect = () => {
      showEffectModal.value = true
    }

    const selectEffect = (effect) => {
      const newEffect = {
        id: Date.now(),
        type: effect.type,
        name: effect.name,
        enabled: true,
        parameters: effect.parameters.map(p => ({ ...p }))
      }
      audioEffects.value.push(newEffect)
      showEffectModal.value = false
      message.success(`已添加${effect.name}效果`)
    }

    const handleAddEffect = () => {
      showEffectModal.value = false
    }

    const toggleEffect = (effect) => {
      // 切换效果启用状态
      message.info(`${effect.name}已${effect.enabled ? '启用' : '禁用'}`)
    }

    const updateEffectParam = (effect, param) => {
      // 更新效果参数
    }

    const exportProject = () => {
      exporting.value = true
      emit('exportProject', exportSettings.value)
      
      // 模拟导出过程
      setTimeout(() => {
        exporting.value = false
        message.success('项目导出成功')
      }, 3000)
    }

    const formatDate = (date) => {
      if (!date) return '未知'
      return new Intl.DateTimeFormat('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }).format(new Date(date))
    }

    const formatDuration = (seconds) => {
      if (!seconds || isNaN(seconds)) return '00:00'
      const mins = Math.floor(seconds / 60)
      const secs = Math.floor(seconds % 60)
      return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`
    }

    // 监听器
    watch(() => props.project, updateProjectInfoFromProps, { immediate: true })
    watch(() => props.tracks, () => {
      projectInfo.value.trackCount = props.tracks.length
    }, { deep: true })

    // 生命周期
    onMounted(() => {
      updateProjectInfoFromProps()
    })

    return {
      projectInfo: computedProjectInfo,
      audioEffects,
      exportSettings,
      showEffectModal,
      exporting,
      availableEffects,
      refreshInfo,
      updateProjectInfo,
      updateTrackInfo,
      updateTrackVolume,
      updateTrackMute,
      updateTrackSolo,
      getTrackTypeColor,
      getTrackTypeName,
      addEffect,
      selectEffect,
      handleAddEffect,
      toggleEffect,
      updateEffectParam,
      exportProject,
      formatDate,
      formatDuration
    }
  }
}
</script>

<style scoped>
.composition-info {
  height: 100%;
  display: flex;
  flex-direction: column;
  background: var(--bg-color-container);
  border-left: 1px solid var(--border-color);
}

.info-header {
  padding: 12px 16px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-header h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

.info-section {
  padding: 16px;
  border-bottom: 1px solid var(--border-color);
}

.section-title {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 12px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.info-item {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.info-item label {
  min-width: 70px;
  color: var(--text-color-secondary);
  margin-right: 8px;
}

.info-item span {
  color: var(--text-color);
}

.effects-list {
  max-height: 300px;
  overflow-y: auto;
}

.effect-item {
  padding: 8px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  margin-bottom: 8px;
  background: var(--bg-color-elevated);
}

.effect-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.effect-name {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-color);
}

.effect-controls {
  padding-left: 8px;
}

.effect-param {
  display: flex;
  align-items: center;
  margin-bottom: 8px;
  font-size: 12px;
}

.effect-param label {
  min-width: 60px;
  color: var(--text-color-secondary);
  margin-right: 8px;
}

.effects-empty {
  text-align: center;
  padding: 20px;
}

/* 暗黑主题适配 */
[data-theme="dark"] .composition-info {
  background: #1f1f1f !important;
  border-left-color: #434343 !important;
}

[data-theme="dark"] .info-header {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .info-header h3 {
  color: #fff !important;
}

[data-theme="dark"] .info-section {
  border-bottom-color: #434343 !important;
}

[data-theme="dark"] .section-title {
  color: #fff !important;
}

[data-theme="dark"] .info-item label {
  color: #8c8c8c !important;
}

[data-theme="dark"] .info-item span {
  color: #fff !important;
}

[data-theme="dark"] .effect-item {
  border-color: #434343 !important;
  background: #2d2d2d !important;
}

[data-theme="dark"] .effect-name {
  color: #fff !important;
}

[data-theme="dark"] .effect-param label {
  color: #8c8c8c !important;
}

[data-theme="dark"] .effects-empty {
  color: #8c8c8c !important;
}
</style>