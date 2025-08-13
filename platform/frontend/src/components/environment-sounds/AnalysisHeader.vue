<template>
  <div class="analysis-header">
    <div class="header-left">
      <h2 class="content-title">章节内容分析</h2>
      <p class="content-subtitle" v-if="selectedChapter">
        第{{ selectedChapter.chapter_number }}章 {{ selectedChapter.chapter_title }}
      </p>
    </div>
    
    <div class="header-actions">
      <a-space>
        <a-button 
          v-if="!hasAnalysis"
          type="primary" 
          @click="$emit('start-analysis')"
          :loading="analysisLoading"
        >
          <BulbOutlined />
          环境音分析
        </a-button>
        
        <a-button 
          v-if="hasAnalysis && hasTracks"
          type="primary" 
          @click="$emit('generate-sounds')"
          :loading="generationLoading"
        >
          <SoundOutlined />
          生成环境音
        </a-button>
      </a-space>
    </div>
  </div>
</template>

<script setup>
import { BulbOutlined, SoundOutlined } from '@ant-design/icons-vue'

defineProps({
  selectedChapter: {
    type: Object,
    default: null
  },
  hasAnalysis: {
    type: Boolean,
    default: false
  },
  hasTracks: {
    type: Boolean,
    default: false
  },
  analysisLoading: {
    type: Boolean,
    default: false
  },
  generationLoading: {
    type: Boolean,
    default: false
  }
})

defineEmits(['start-analysis', 'generate-sounds'])
</script>

<style scoped>
.analysis-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 24px;
  padding-bottom: 16px;
  border-bottom: 1px solid var(--ant-border-color-split);
}

.header-left {
  flex: 1;
}

.content-title {
  margin: 0 0 4px 0;
  font-size: 20px;
  font-weight: 600;
  color: var(--ant-text-color);
}

.content-subtitle {
  margin: 0;
  font-size: 14px;
  color: var(--ant-text-color-secondary);
}

.header-actions {
  flex-shrink: 0;
}
</style>
