<template>
  <div class="image-file-list">
    <!-- 搜索和筛选工具栏 -->
    <div class="list-toolbar">
      <a-input
        v-model:value="localSearchKeyword"
        :placeholder="placeholder"
        allow-clear
        @input="handleSearch"
        style="width: 300px"
      >
        <template #prefix>
          <SearchOutlined />
        </template>
      </a-input>
      <a-space style="margin-left: 12px">
        <a-select
          v-model:value="localFilterBookId"
          placeholder="选择书籍"
          allow-clear
          @change="handleBookFilter"
          style="width: 150px"
        >
          <a-select-option
            v-for="book in books"
            :key="book.id"
            :value="book.id"
          >
            {{ book.title || `书籍 ${book.id}` }}
          </a-select-option>
        </a-select>
        <a-select
          v-model:value="localFilterChapterId"
          placeholder="选择章节"
          allow-clear
          @change="handleChapterFilter"
          style="width: 150px"
        >
          <a-select-option
            v-for="chapter in chapters"
            :key="chapter.id"
            :value="chapter.id"
          >
            {{ chapter.chapter_title || chapter.title || `章节 ${chapter.id}` }}
          </a-select-option>
        </a-select>
      </a-space>
    </div>

    <!-- 图片列表 -->
    <!-- 调试信息: loading={{ loading }}, images.length={{ images.length }} -->
    <div class="image-list" v-if="!loading && images.length > 0">
      <div
        v-for="image in images"
        :key="image.id"
        class="image-item"
        @click="$emit('detail', image)"
      >
        <div class="image-preview">
          <img
            :src="image.image_url"
            :alt="image.scene_description"
            class="image-thumbnail"
            @error="handleImageError"
          />
          <div class="image-overlay">
            <a-space>
              <a-button
                type="primary"
                size="small"
                @click.stop="$emit('preview', image)"
                title="预览图片"
              >
                <template #icon><EyeOutlined /></template>
              </a-button>
              <a-button
                type="primary"
                size="small"
                @click.stop="$emit('download', image)"
                style="background: #52c41a; border-color: #52c41a;"
                title="下载图片"
              >
                <template #icon><DownloadOutlined /></template>
              </a-button>
            </a-space>
          </div>
        </div>
        <div class="image-info">
          <div class="image-name">{{ image.scene_description }}</div>
          <div class="image-meta">
            <span class="image-size">{{ image.image_width }}×{{ image.image_height }}</span>
            <span class="image-model">{{ image.generation_model }}</span>
          </div>
          <div class="image-details">
            <span class="book-chapter">{{ image.book_title }} - {{ image.chapter_title }}</span>
            <span class="image-date">{{ formatDate(image.completed_at) }}</span>
          </div>
          <div class="image-rating" v-if="image.user_rating">
            <a-rate
              v-model:value="image.user_rating"
              disabled
              size="small"
            />
          </div>
        </div>
        <div class="image-actions">
          <a-dropdown>
            <a-button type="text" size="small">
              <template #icon><MoreOutlined /></template>
            </a-button>
            <template #overlay>
              <a-menu>
                <a-menu-item @click="$emit('preview', image)">
                  <EyeOutlined /> 预览
                </a-menu-item>
                <a-menu-item @click="$emit('download', image)">
                  <DownloadOutlined /> 下载
                </a-menu-item>
                <a-menu-item @click="$emit('detail', image)">
                  <InfoCircleOutlined /> 详情
                </a-menu-item>
              </a-menu>
            </template>
          </a-dropdown>
        </div>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="loading-container">
      <a-spin size="large" />
      <p>加载中...</p>
    </div>

    <!-- 空状态 -->
    <!-- 调试信息: 进入空状态 - loading={{ loading }}, images.length={{ images.length }} -->
    <div v-if="!loading && images.length === 0" class="empty-state">
      <div class="empty-icon">{{ emptyIcon }}</div>
      <h4>{{ emptyText }}</h4>
      <p>{{ emptyDesc }}</p>
      <div style="margin-top: 10px; font-size: 12px; color: #666;">
        调试: loading={{ loading }}, images={{ JSON.stringify(images) }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'
import {
  SearchOutlined,
  EyeOutlined,
  DownloadOutlined,
  MoreOutlined,
  InfoCircleOutlined
} from '@ant-design/icons-vue'

// Props
const props = defineProps({
  images: {
    type: Array,
    default: () => []
  },
  loading: {
    type: Boolean,
    default: false
  },
  searchKeyword: {
    type: String,
    default: ''
  },
  category: {
    type: String,
    default: 'all'
  },
  placeholder: {
    type: String,
    default: '搜索图片...'
  },
  emptyIcon: {
    type: String,
    default: '🖼️'
  },
  emptyText: {
    type: String,
    default: '暂无图片文件'
  },
  emptyDesc: {
    type: String,
    default: '前往图片生成页面创建图片'
  },
  books: {
    type: Array,
    default: () => []
  },
  chapters: {
    type: Array,
    default: () => []
  },
  filterBookId: {
    type: [String, Number],
    default: null
  },
  filterChapterId: {
    type: [String, Number],
    default: null
  }
})

// Emits
const emit = defineEmits([
  'search',
  'filter-book',
  'filter-chapter',
  'preview',
  'download',
  'detail'
])

// Reactive data
const localSearchKeyword = ref(props.searchKeyword)
const localFilterBookId = ref(props.filterBookId)
const localFilterChapterId = ref(props.filterChapterId)

// Watchers
watch(() => props.searchKeyword, (newVal) => {
  localSearchKeyword.value = newVal
})

watch(() => props.filterBookId, (newVal) => {
  localFilterBookId.value = newVal
})

watch(() => props.filterChapterId, (newVal) => {
  localFilterChapterId.value = newVal
})

// Methods
const handleSearch = () => {
  emit('search', localSearchKeyword.value)
}

const handleBookFilter = (value) => {
  localFilterBookId.value = value
  emit('filter-book', value)
}

const handleChapterFilter = (value) => {
  localFilterChapterId.value = value
  emit('filter-chapter', value)
}

const handleImageError = (event) => {
  event.target.src = '/placeholder-image.png'
}

const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.image-file-list {
  height: 100%;
  display: flex;
  flex-direction: column;
}

.list-toolbar {
  padding: 12px 0;
  border-bottom: 1px solid #f0f0f0;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.image-list {
  flex: 1;
  overflow-y: auto;
  padding: 8px 0;
}

.image-item {
  display: flex;
  align-items: center;
  padding: 12px;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s ease;
  border: 1px solid transparent;
  margin-bottom: 8px;
}

.image-item:hover {
  background-color: #f5f5f5;
  border-color: #d9d9d9;
}

.image-item:active {
  background-color: #e6f7ff;
  border-color: #1890ff;
}

.image-preview {
  position: relative;
  width: 80px;
  height: 60px;
  margin-right: 12px;
  border-radius: 4px;
  overflow: hidden;
  background-color: #f5f5f5;
}

.image-thumbnail {
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.2s ease;
}

.image-preview:hover .image-thumbnail {
  transform: scale(1.05);
}

.image-overlay {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.6);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.2s ease;
}

.image-preview:hover .image-overlay {
  opacity: 1;
}

.image-info {
  flex: 1;
  min-width: 0;
}

.image-name {
  font-size: 14px;
  font-weight: 500;
  color: #262626;
  margin-bottom: 4px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.image-meta {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.image-size {
  font-size: 12px;
  color: #8c8c8c;
  background: #f0f0f0;
  padding: 2px 6px;
  border-radius: 3px;
}

.image-model {
  font-size: 12px;
  color: #1890ff;
  background: #e6f7ff;
  padding: 2px 6px;
  border-radius: 3px;
}

.image-details {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 4px;
}

.book-chapter {
  font-size: 12px;
  color: #595959;
}

.image-date {
  font-size: 12px;
  color: #8c8c8c;
}

.image-rating {
  display: flex;
  align-items: center;
}

.image-actions {
  margin-left: 12px;
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #8c8c8c;
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 200px;
  color: #8c8c8c;
}

.empty-icon {
  font-size: 48px;
  margin-bottom: 16px;
}

.empty-state h4 {
  margin: 0 0 8px 0;
  color: #595959;
}

.empty-state p {
  margin: 0;
  font-size: 14px;
}
</style>