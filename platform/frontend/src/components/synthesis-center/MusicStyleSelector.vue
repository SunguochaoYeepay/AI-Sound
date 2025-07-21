<template>
  <div class="music-style-selector">
    <div class="selector-header">
      <h4>音乐风格选择</h4>
      <p class="selector-description">选择适合当前章节的音乐风格</p>
    </div>

    <div class="style-grid">
      <div
        v-for="style in musicStyles"
        :key="style.id"
        class="style-card"
        :class="{ selected: selectedStyle === style.id }"
        @click="selectStyle(style)"
      >
        <div class="style-icon">{{ style.icon }}</div>
        <div class="style-info">
          <h5 class="style-name">{{ style.name }}</h5>
          <p class="style-description">{{ style.description }}</p>
          <div class="style-tags">
            <a-tag v-for="tag in style.tags" :key="tag" size="small" :color="style.color">
              {{ tag }}
            </a-tag>
          </div>
        </div>
        <div class="style-preview" v-if="style.preview">
          <a-button size="small" type="text" @click.stop="previewStyle(style)">
            <template #icon>
              <PlayCircleOutlined />
            </template>
          </a-button>
        </div>
      </div>
    </div>

    <div class="custom-style-section">
      <h5>自定义风格</h5>
      <a-input
        v-model:value="customStyleInput"
        placeholder="输入自定义音乐风格描述..."
        @pressEnter="addCustomStyle"
      >
        <template #suffix>
          <a-button type="text" size="small" @click="addCustomStyle">
            <template #icon>
              <PlusOutlined />
            </template>
          </a-button>
        </template>
      </a-input>
    </div>

    <div class="selector-actions">
      <a-space>
        <a-button @click="$emit('cancel')"> 取消 </a-button>
        <a-button type="primary" @click="confirmSelection" :disabled="!selectedStyle">
          确认选择
        </a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup>
  import { ref, onMounted } from 'vue'
  import { message } from 'ant-design-vue'
  import { PlayCircleOutlined, PlusOutlined } from '@ant-design/icons-vue'

  // Props
  const props = defineProps({
    defaultStyle: {
      type: String,
      default: null
    },
    sceneType: {
      type: String,
      default: null
    }
  })

  // Emits
  const emit = defineEmits(['styleSelected', 'cancel'])

  // 响应式数据
  const selectedStyle = ref(props.defaultStyle)
  const customStyleInput = ref('')

  // 预定义音乐风格
  const musicStyles = ref([
    {
      id: 'battle',
      name: '战斗',
      description: '激烈、紧张的战斗音乐',
      icon: '⚔️',
      color: 'red',
      tags: ['激烈', '紧张', '快节奏'],
      preview: true,
      bpm: 128,
      intensity: 0.8
    },
    {
      id: 'romance',
      name: '浪漫',
      description: '温柔、浪漫的爱情音乐',
      icon: '💕',
      color: 'pink',
      tags: ['温柔', '浪漫', '抒情'],
      preview: true,
      bpm: 78,
      intensity: 0.4
    },
    {
      id: 'mystery',
      name: '悬疑',
      description: '神秘、紧张的悬疑音乐',
      icon: '🔍',
      color: 'purple',
      tags: ['神秘', '悬疑', '阴暗'],
      preview: true,
      bpm: 89,
      intensity: 0.6
    },
    {
      id: 'peaceful',
      name: '平静',
      description: '宁静、祥和的背景音乐',
      icon: '🌸',
      color: 'green',
      tags: ['宁静', '祥和', '舒缓'],
      preview: true,
      bpm: 62,
      intensity: 0.2
    },
    {
      id: 'sad',
      name: '悲伤',
      description: '忧郁、感伤的音乐',
      icon: '😢',
      color: 'blue',
      tags: ['忧郁', '感伤', '缓慢'],
      preview: true,
      bpm: 55,
      intensity: 0.3
    },
    {
      id: 'epic',
      name: '史诗',
      description: '宏大、壮阔的史诗音乐',
      icon: '🏔️',
      color: 'gold',
      tags: ['宏大', '壮阔', '史诗'],
      preview: true,
      bpm: 95,
      intensity: 0.9
    }
  ])

  // 方法
  const selectStyle = (style) => {
    selectedStyle.value = style.id
    console.log('选择音乐风格:', style)
  }

  const previewStyle = (style) => {
    console.log('预览音乐风格:', style)
    message.info(`预览 ${style.name} 风格音乐`)
    // 这里可以添加实际的预览功能
  }

  const addCustomStyle = () => {
    if (!customStyleInput.value.trim()) {
      message.warning('请输入自定义风格描述')
      return
    }

    const customStyle = {
      id: `custom_${Date.now()}`,
      name: '自定义',
      description: customStyleInput.value,
      icon: '🎨',
      color: 'default',
      tags: ['自定义'],
      preview: false,
      bpm: 80,
      intensity: 0.5
    }

    musicStyles.value.push(customStyle)
    selectedStyle.value = customStyle.id
    customStyleInput.value = ''
    message.success('自定义风格已添加')
  }

  const confirmSelection = () => {
    const selected = musicStyles.value.find((style) => style.id === selectedStyle.value)
    if (selected) {
      emit('styleSelected', selected)
      message.success(`已选择 ${selected.name} 风格`)
    }
  }

  // 根据场景类型自动推荐
  const autoSelectByScene = () => {
    if (!props.sceneType) return

    const sceneMapping = {
      battle: 'battle',
      romance: 'romance',
      mystery: 'mystery',
      peaceful: 'peaceful',
      sad: 'sad',
      epic: 'epic'
    }

    const recommendedStyle = sceneMapping[props.sceneType]
    if (recommendedStyle) {
      selectedStyle.value = recommendedStyle
    }
  }

  // 生命周期
  onMounted(() => {
    autoSelectByScene()
  })
</script>

<style scoped>
  .music-style-selector {
    padding: 20px;
  }

  .selector-header {
    margin-bottom: 20px;
    text-align: center;
  }

  .selector-header h4 {
    margin: 0 0 8px 0;
    font-size: 18px;
    font-weight: 600;
    color: #1f2937;
  }

  .selector-description {
    margin: 0;
    font-size: 14px;
    color: #6b7280;
  }

  .style-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
    gap: 16px;
    margin-bottom: 24px;
  }

  .style-card {
    display: flex;
    align-items: center;
    padding: 16px;
    border: 2px solid #e5e7eb;
    border-radius: 8px;
    cursor: pointer;
    transition: all 0.2s ease;
    background: #ffffff;
  }

  .style-card:hover {
    border-color: #1890ff;
    box-shadow: 0 2px 8px rgba(24, 144, 255, 0.1);
    transform: translateY(-1px);
  }

  .style-card.selected {
    border-color: #1890ff;
    background: #f0f9ff;
    box-shadow: 0 4px 12px rgba(24, 144, 255, 0.15);
  }

  .style-icon {
    font-size: 32px;
    margin-right: 16px;
    flex-shrink: 0;
  }

  .style-info {
    flex: 1;
    min-width: 0;
  }

  .style-name {
    margin: 0 0 4px 0;
    font-size: 16px;
    font-weight: 600;
    color: #1f2937;
  }

  .style-description {
    margin: 0 0 8px 0;
    font-size: 13px;
    color: #6b7280;
    line-height: 1.4;
  }

  .style-tags {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
  }

  .style-preview {
    margin-left: 12px;
    flex-shrink: 0;
  }

  .custom-style-section {
    margin-bottom: 24px;
    padding: 16px;
    background: #f8fafc;
    border-radius: 6px;
    border: 1px solid #e5e7eb;
  }

  .custom-style-section h5 {
    margin: 0 0 12px 0;
    font-size: 14px;
    font-weight: 600;
    color: #374151;
  }

  .selector-actions {
    text-align: center;
    padding-top: 16px;
    border-top: 1px solid #e5e7eb;
  }

  /* 暗黑模式适配 */
  [data-theme='dark'] .music-style-selector {
    background: #1f1f1f;
  }

  [data-theme='dark'] .selector-header h4 {
    color: #ffffff;
  }

  [data-theme='dark'] .selector-description {
    color: #8c8c8c;
  }

  [data-theme='dark'] .style-card {
    background: #2a2a2a;
    border-color: #434343;
  }

  [data-theme='dark'] .style-card:hover {
    border-color: #1890ff;
    background: #2a2a2a;
  }

  [data-theme='dark'] .style-card.selected {
    background: #1a1a2e;
    border-color: #1890ff;
  }

  [data-theme='dark'] .style-name {
    color: #ffffff;
  }

  [data-theme='dark'] .style-description {
    color: #8c8c8c;
  }

  [data-theme='dark'] .custom-style-section {
    background: #2a2a2a;
    border-color: #434343;
  }

  [data-theme='dark'] .custom-style-section h5 {
    color: #ffffff;
  }

  [data-theme='dark'] .selector-actions {
    border-top-color: #434343;
  }
</style>
