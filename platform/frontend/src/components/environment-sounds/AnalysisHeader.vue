<template>
  <div class="analysis-header">
    <div class="header-left">
      <h3 class="content-title">章节分析</h3>
      <p class="content-subtitle" v-if="selectedChapter">
        {{ selectedChapter.chapter_title }}
      </p>
    </div>
    
    <div class="header-actions">
      <!-- 调试信息 -->
      <div style="background: #fff3cd; padding: 5px; margin-bottom: 10px; border: 1px solid #ffeaa7; border-radius: 4px; font-size: 12px;">
        🔍 按钮状态: hasAnalysis={{ hasAnalysis }}, hasTracks={{ hasTracks }}, hasGeneratedTracks={{ hasGeneratedTracks }}
      </div>
      
      <a-space>
        <!-- 环境音分析 -->
        <a-button 
          v-if="!hasAnalysis"
          type="default" 
          @click="$emit('start-analysis')"
          :loading="analysisLoading"
        >
          <BulbOutlined />
          分析环境音
        </a-button>
        
        <!-- 生成当前章节环境音 -->
        <a-button 
          v-if="hasAnalysis && hasTracks && !hasGeneratedTracks"
          type="default" 
          @click="$emit('generate-all-sounds')"
          :loading="generationLoading"
        >
          <SoundOutlined />
          生成当前章节环境音
        </a-button>
        
        <!-- 混音操作 -->
        <a-button 
          v-if="hasAnalysis && hasTracks && hasGeneratedTracks"
          size="small"
          type="default"
          :loading="mixingLoading"
          @click="$emit('mix-sounds')"
        >
          混音
        </a-button>
        
        <!-- 播放和下载 -->
        <a-button 
          v-if="hasAnalysis && hasTracks && hasMixingFile"
          size="small"
          type="default"
          @click="$emit('play-mixing')"
        >
          播放
        </a-button>
        
        <a-button 
          v-if="hasAnalysis && hasTracks && hasMixingFile"
          size="small"
          type="default"
          @click="$emit('download-mixing')"
        >
          下载
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
  align-items: center;
  margin-bottom: 20px;
  padding: 16px 0;
  border-bottom: 1px solid #f0f0f0;
  background: #fafafa;
  border-radius: 6px;
  padding-left: 16px;
  padding-right: 16px;
}

.header-left {
  flex: 1;
}

.content-title {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 500;
  color: #262626;
}

.content-subtitle {
  margin: 0;
  font-size: 13px;
  color: #8c8c8c;
}

.header-actions {
  flex-shrink: 0;
}

/* 暗色主题适配 */
[data-theme='dark'] .analysis-header {
  background: #1f1f1f;
  border-bottom-color: #303030;
}

[data-theme='dark'] .content-title {
  color: #ffffff;
}

[data-theme='dark'] .content-subtitle {
  color: #a6a6a6;
}
</style>
