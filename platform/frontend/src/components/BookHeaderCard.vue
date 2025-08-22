<template>
  <div class="book-header-card">
    <a-card :bordered="false" class="header-card">
      <div class="header-content">
        <div class="book-meta">
          <h1 class="book-title">{{ book.title }}</h1>
          <div class="meta-info">
            <a-tag :color="getStatusColor(book.status)">
              {{ getStatusText(book.status) }}
            </a-tag>
            <span class="author">作者：{{ book.author || '未知' }}</span>
            <span class="word-count">字数：{{ (book.word_count || 0).toLocaleString() }}</span>
            <span class="chapter-count">章节：{{ chapterCount }}</span>
            <span class="update-time">更新：{{ formatDate(book.updated_at) }}</span>
          </div>
        </div>

        <div class="header-actions">
          <a-space>
           
            <a-button type="primary" @click="$emit('editBook')"> ✏️ 编辑 </a-button>
            <!-- <a-button @click="$emit('createProject')" :disabled="!book.content">
              🎯 创建项目
            </a-button> -->
            <a-button @click="$emit('openCharacterManagement')"> 🎭 管理角色配音 </a-button>
          </a-space>
        </div>
      </div>

      <!-- 可展开的详细信息 -->
      <a-collapse v-if="showDetails" v-model:activeKey="activeDetailKey" ghost>
        <a-collapse-panel key="details" header="📊 详细信息">
          <a-row :gutter="16">
            <a-col :span="12">
              <a-descriptions :column="1" bordered size="small">
                <a-descriptions-item label="状态">
                  <a-tag :color="getStatusColor(book.status)">
                    {{ getStatusText(book.status) }}
                  </a-tag>
                </a-descriptions-item>
                <a-descriptions-item label="字数">
                  {{ (book.word_count || 0).toLocaleString() }}
                </a-descriptions-item>
                <a-descriptions-item label="章节数">
                  {{ chapterCount }}
                </a-descriptions-item>
                <a-descriptions-item label="创建时间">
                  {{ formatDate(book.created_at) }}
                </a-descriptions-item>
                <a-descriptions-item label="更新时间">
                  {{ formatDate(book.updated_at) }}
                </a-descriptions-item>
              </a-descriptions>
            </a-col>
            <a-col :span="12">
              <div class="book-stats">
                <div class="stat-item">
                  <div class="stat-value">{{ (book.content || '').length.toLocaleString() }}</div>
                  <div class="stat-label">总字符数</div>
                </div>
                <div class="stat-item">
                  <div class="stat-value">{{ estimatedReadTime }}</div>
                  <div class="stat-label">预计阅读时长</div>
                </div>
              </div>
            </a-col>
          </a-row>

          <div v-if="book.description" class="book-description">
            <h4>描述</h4>
            <p>{{ book.description }}</p>
          </div>

          <div v-if="book.tags && book.tags.length > 0" class="book-tags">
            <h4>标签</h4>
            <a-space wrap>
              <a-tag v-for="tag in book.tags" :key="tag" color="blue">
                {{ tag }}
              </a-tag>
            </a-space>
          </div>
        </a-collapse-panel>
      </a-collapse>
    </a-card>
  </div>
</template>

<script setup>
  import { ref, computed } from 'vue'

  const props = defineProps({
    book: {
      type: Object,
      required: true
    },
    chapterCount: {
      type: Number,
      default: 0
    },
    showDetails: {
      type: Boolean,
      default: false
    }
  })

  const emit = defineEmits(['goBack', 'editBook', 'createProject', 'openCharacterManagement'])

  const activeDetailKey = ref([])

  const estimatedReadTime = computed(() => {
    if (!props.book?.word_count) return '0 分钟'
    const minutes = Math.ceil(props.book.word_count / 300)
    if (minutes < 60) return `${minutes} 分钟`
    const hours = Math.floor(minutes / 60)
    const remainingMinutes = minutes % 60
    return `${hours}小时${remainingMinutes}分钟`
  })

  const getStatusColor = (status) => {
    const colors = {
      draft: 'orange',
      published: 'green',
      archived: 'gray'
    }
    return colors[status] || 'default'
  }

  const getStatusText = (status) => {
    const texts = {
      draft: '草稿',
      published: '已发布',
      archived: '已归档'
    }
    return texts[status] || status
  }

  const formatDate = (dateString) => {
    if (!dateString) return '未知'
    const date = new Date(dateString)
    return date.toLocaleString('zh-CN')
  }
</script>

<style scoped>
  .book-header-card {
    margin-bottom: 16px;
  }

  .header-card {
    background: var(--ant-component-background);
    border-radius: 12px;
    box-shadow: 0 4px 12px var(--ant-shadow-color);
  }

  .header-content {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
  }

  .book-meta {
    flex: 1;
  }

  .book-title {
    font-size: 24px;
    font-weight: 600;
    margin: 0 0 8px 0;
    color: var(--ant-heading-color);
  }

  .meta-info {
    display: flex;
    gap: 16px;
    align-items: center;
    flex-wrap: wrap;
  }

  .meta-info > span {
    font-size: 14px;
    color: var(--ant-text-color-secondary);
  }

  .header-actions {
    flex-shrink: 0;
    margin-left: 16px;
  }

  .book-stats {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    margin-top: 16px;
  }

  .stat-item {
    text-align: center;
    padding: 12px;
    background: var(--ant-color-bg-container);
    border-radius: 8px;
  }

  .stat-value {
    font-size: 18px;
    font-weight: 600;
    color: var(--ant-heading-color);
  }

  .stat-label {
    font-size: 12px;
    color: var(--ant-text-color-secondary);
    margin-top: 4px;
  }

  .book-description {
    margin-top: 16px;
  }

  .book-description h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: var(--ant-heading-color);
  }

  .book-description p {
    margin: 0;
    color: var(--ant-text-color-secondary);
    line-height: 1.6;
  }

  .book-tags {
    margin-top: 16px;
  }

  .book-tags h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: var(--ant-heading-color);
  }
</style>
