<template>
  <div class="empty-state">
    <a-empty
      class="empty-icon"
      :image="Empty.PRESENTED_IMAGE_SIMPLE"
      :description="description"
    />
    
    <div class="empty-actions">
      <a-button type="primary" size="large" @click="$emit('create')">
        <template #icon><PlusOutlined /></template>
        创建环境音项目
      </a-button>
    </div>
    
    <div class="empty-tips">
      <p><strong>使用提示：</strong></p>
      <ul>
        <li>点击"创建环境音项目"开始新的环境音制作</li>
        <li>可以通过书籍和章节关联，为特定场景生成环境音</li>
        <li>支持多种音效类型：自然环境、城市背景、室内氛围等</li>
        <li>每个项目可以包含多个音效轨道，组合成完整的环境音</li>
      </ul>
    </div>
  </div>
</template>

<script setup>
import { defineEmits } from 'vue'
import { Empty } from 'ant-design-vue'
import { PlusOutlined } from '@ant-design/icons-vue'

const props = defineProps({
  description: {
    type: String,
    default: '暂无环境音项目'
  }
})

const emit = defineEmits(['create'])
</script>

<style scoped>
.empty-state {
  text-align: center;
  padding: 60px 20px;
}

.empty-icon {
  margin-bottom: 16px;
}

.empty-actions {
  margin: 24px 0;
}

.empty-tips {
  text-align: left;
  max-width: 500px;
  margin: 0 auto;
  color: #666;
  font-size: 14px;
}

.empty-tips p {
  margin-bottom: 8px;
  font-weight: 500;
}

.empty-tips ul {
  margin: 0;
  padding-left: 20px;
}

.empty-tips li {
  margin-bottom: 4px;
  line-height: 1.5;
}

/* 暗黑模式适配 */
[data-theme='dark'] .empty-tips {
  color: #8c8c8c !important;
}
</style>