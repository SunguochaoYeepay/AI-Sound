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
        <!-- 第一步：环境音分析 -->
        <a-button 
          v-if="!hasAnalysis"
          type="primary" 
          @click="$emit('start-analysis')"
          :loading="analysisLoading"
        >
          <BulbOutlined />
          环境音分析
        </a-button>
        
       
        
        <!-- 第二步：生成环境音（合并两个生成按钮） -->
        <a-button 
          v-if="hasAnalysis && hasTracks"
          type="primary" 
          @click="$emit('generate-all-sounds')"
          :loading="generationLoading"
        >
          <SoundOutlined />
          生成所有环境音
        </a-button>
        
        <!-- 第三步：混音操作（只有在有生成文件时才显示） -->
        <a-button 
          v-if="hasAnalysis && hasTracks && hasGeneratedTracks"
          size="small"
          :loading="mixingLoading"
          @click="$emit('mix-sounds')"
        >
          🔊 混音环境音
        </a-button>
        
        <!-- 第四步：播放和下载混音（只有在有混音文件时才显示） -->
        <a-button 
          v-if="hasAnalysis && hasTracks && hasMixingFile"
          size="small"
          @click="$emit('play-mixing')"
        >
          🎵 播放混音
        </a-button>
        
        <a-button 
          v-if="hasAnalysis && hasTracks && hasMixingFile"
          size="small"
          @click="$emit('download-mixing')"
        >
          ⬇️ 下载混音
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
  hasGeneratedTracks: {
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
  },
  mixingLoading: {
    type: Boolean,
    default: false
  },
  hasMixingFile: {
    type: Boolean,
    default: false
  }
})

defineEmits(['start-analysis', 'generate-all-sounds', 'mix-sounds', 'play-mixing', 'download-mixing'])
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

/* 暗色主题适配 */
[data-theme='dark'] .analysis-header {
  border-bottom-color: var(--ant-border-color-split);
}

[data-theme='dark'] .content-title {
  color: var(--ant-color-text);
}

[data-theme='dark'] .content-subtitle {
  color: var(--ant-color-text-secondary);
}
</style>
