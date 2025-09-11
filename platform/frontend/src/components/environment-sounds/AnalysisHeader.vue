<template>
  <div class="analysis-header">
    <div class="header-left">
      <h3 class="content-title">
        章节分析
        <a-tag
          v-if="selectedChapter"
          :color="getAnalysisStatusColor(selectedChapter)"
          size="small"
          style="margin-left: 8px;"
        >
          {{ getAnalysisStatusText(selectedChapter) }}
        </a-tag>
      </h3>
      <p class="content-subtitle" v-if="selectedChapter">
        第{{ selectedChapter.chapter_number }}章 {{ selectedChapter.chapter_title }}
        <span class="word-count">{{ formatNumber(selectedChapter.word_count || 0) }} 字</span>
      </p>
    </div>
    
    <div class="header-actions">
    
      
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
        
        <!-- 加载环境音数据 -->
        <a-button 
          v-if="hasAnalysis"
          type="default" 
          @click="$emit('reanalyze')"
          :loading="analysisLoading"
        >
          <ReloadOutlined />
          加载环境音
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
        
        <!-- 重新生成环境音 -->
        <a-button 
          v-if="hasAnalysis && hasTracks && hasGeneratedTracks"
          type="default" 
          @click="$emit('generate-all-sounds')"
          :loading="generationLoading"
        >
          <SoundOutlined />
          重新生成环境音
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
import { BulbOutlined, SoundOutlined, ReloadOutlined } from '@ant-design/icons-vue'

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

defineEmits([
  'start-analysis',
  'reanalyze',
  'generate-all-sounds',
  'mix-sounds',
  'play-mixing',
  'download-mixing'
])

// 状态显示函数
const getAnalysisStatusText = (chapter) => {
  const status = chapter.analysis_status || 'pending'
  const statusMap = {
    pending: '待分析',
    processing: '分析中',
    completed: '已完成',
    failed: '分析失败',
    ready: '准备就绪'
  }
  return statusMap[status] || '未知'
}

const getAnalysisStatusColor = (chapter) => {
  const status = chapter.analysis_status || 'pending'
  const colorMap = {
    pending: 'orange',
    processing: 'blue',
    completed: 'green',
    failed: 'red',
    ready: 'purple'
  }
  return colorMap[status] || 'default'
}

const formatNumber = (num) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + '万'
  }
  return num.toLocaleString()
}
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

.word-count {
  font-size: 12px;
  color: #666;
  margin-left: 8px;
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
