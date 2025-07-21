# 虚拟章节列表组件使用指南

## 概述

`VirtualChapterList.vue` 是一个高性能的虚拟滚动组件，专门用于处理大量章节数据的渲染。当章节数量达到8000+时，传统渲染方式会导致严重的性能问题，而虚拟滚动技术只渲染可视区域内的项目，大幅提升性能。

## 特性

- ✅ **虚拟滚动**: 只渲染可视区域的章节，支持8000+数据
- ✅ **分页加载**: 支持按需加载更多数据
- ✅ **服务端搜索**: 支持关键词搜索和过滤
- ✅ **响应式设计**: 适配不同屏幕尺寸
- ✅ **平滑滚动**: 提供流畅的滚动体验
- ✅ **缓存优化**: 智能缓存搜索结果
- ✅ **性能监控**: 内置性能监控工具

## 快速开始

### 1. 基础使用

```vue
<template>
  <div class="chapter-list-container">
    <VirtualChapterList
      :chapters="chapters"
      :selected-chapter-id="selectedChapterId"
      :chapter-preparation-status="chapterPreparationStatus"
      :preparing-chapters="preparingChapters"
      :detecting-chapters="detectingChapters"
      :loading="loading"
      :total="totalChapters"
      :page-size="100"
      @select-chapter="handleSelectChapter"
      @load-more="handleLoadMore"
      @search="handleSearch"
      ref="virtualListRef"
    />
  </div>
</template>

<script setup>
  import VirtualChapterList from '@/components/VirtualChapterList.vue'

  // 组件状态
  const chapters = ref([])
  const selectedChapterId = ref(null)
  const chapterPreparationStatus = ref({})
  const preparingChapters = ref(new Set())
  const detectingChapters = ref(false)
  const loading = ref(false)
  const totalChapters = ref(0)

  // 事件处理
  const handleSelectChapter = (chapter) => {
    selectedChapterId.value = chapter.id
    console.log('选中章节:', chapter)
  }

  const handleLoadMore = async ({ page, keyword }) => {
    // 加载更多数据
    const newChapters = await fetchChapters(page, keyword)
    chapters.value.push(...newChapters)
  }

  const handleSearch = async ({ keyword }) => {
    // 执行搜索
    const result = await searchChapters(keyword)
    chapters.value = result.data
    totalChapters.value = result.total
  }
</script>
```

### 2. 高级配置

#### 自定义分页大小

```vue
<VirtualChapterList :page-size="200" :total="totalChapters" ... />
```

#### 性能优化配置

```javascript
// 在工具类中配置
import { VirtualScrollHelper } from '@/utils/virtualScrollHelper'

const helper = new VirtualScrollHelper({
  pageSize: 100,
  searchFields: ['title', 'content', 'tags'],
  sortField: 'chapter_number',
  sortOrder: 'asc'
})
```

## API 参考

### Props

| 属性名                     | 类型          | 默认值      | 说明               |
| -------------------------- | ------------- | ----------- | ------------------ |
| `chapters`                 | Array         | `[]`        | 章节数据数组       |
| `selectedChapterId`        | String/Number | `null`      | 当前选中的章节ID   |
| `chapterPreparationStatus` | Object        | `{}`        | 章节准备状态对象   |
| `preparingChapters`        | Set           | `new Set()` | 正在准备的章节集合 |
| `detectingChapters`        | Boolean       | `false`     | 是否正在检测章节   |
| `loading`                  | Boolean       | `false`     | 是否正在加载数据   |
| `total`                    | Number        | `0`         | 总章节数量         |
| `pageSize`                 | Number        | `100`       | 每页加载的章节数量 |

### Events

| 事件名            | 参数                                   | 说明                       |
| ----------------- | -------------------------------------- | -------------------------- |
| `select-chapter`  | `chapter` - 选中的章节对象             | 当用户点击章节时触发       |
| `load-more`       | `{ page, keyword }` - 页码和搜索关键词 | 需要加载更多数据时触发     |
| `search`          | `{ keyword }` - 搜索关键词             | 用户执行搜索时触发         |
| `detect-chapters` | -                                      | 用户点击重新检测按钮时触发 |

### 方法

通过 `ref` 可以调用组件方法：

```vue
<template>
  <VirtualChapterList ref="virtualListRef" ... />
  <button @click="scrollToChapter">跳转到第100章</button>
</template>

<script setup>
  const virtualListRef = ref(null)

  const scrollToChapter = () => {
    virtualListRef.value.scrollToChapter(100)
  }

  const resetScroll = () => {
    virtualListRef.value.resetScroll()
  }
</script>
```

| 方法名                       | 参数                       | 说明               |
| ---------------------------- | -------------------------- | ------------------ |
| `scrollToChapter(chapterId)` | `chapterId: string/number` | 滚动到指定章节     |
| `resetScroll()`              | -                          | 重置滚动位置到顶部 |

## 服务端集成

### 1. 分页加载

```javascript
// 服务端API示例
const handleLoadMore = async ({ page, keyword }) => {
  try {
    const response = await api.get('/api/chapters', {
      params: {
        page,
        limit: 100,
        keyword,
        sort: 'chapter_number',
        order: 'asc'
      }
    })

    if (page === 1) {
      chapters.value = response.data.items
    } else {
      chapters.value.push(...response.data.items)
    }

    totalChapters.value = response.data.total
  } catch (error) {
    console.error('加载章节失败:', error)
  }
}
```

### 2. 服务端搜索

```javascript
const handleSearch = async ({ keyword }) => {
  try {
    const response = await api.get('/api/chapters/search', {
      params: {
        keyword,
        limit: 100
      }
    })

    chapters.value = response.data.items
    totalChapters.value = response.data.total

    // 滚动到顶部
    if (virtualListRef.value) {
      virtualListRef.value.resetScroll()
    }
  } catch (error) {
    console.error('搜索失败:', error)
  }
}
```

## 性能优化建议

### 1. 数据预处理

在服务端处理数据排序和过滤，减少前端计算：

```javascript
// 服务端排序和过滤
const response = await api.get('/api/chapters', {
  params: {
    sort: 'chapter_number',
    order: 'asc',
    filter: { status: 'completed' }
  }
})
```

### 2. 缓存策略

使用工具类的缓存功能：

```javascript
import { VirtualScrollHelper } from '@/utils/virtualScrollHelper'

const helper = new VirtualScrollHelper({
  pageSize: 100,
  searchFields: ['title', 'content']
})

// 缓存搜索结果
const cachedResults = await helper.search('关键词')
```

### 3. 防抖和节流

```javascript
import { debounce, throttle } from '@/utils/virtualScrollHelper'

// 防抖搜索
const debouncedSearch = debounce(async (keyword) => {
  await handleSearch({ keyword })
}, 300)

// 节流滚动
const throttledScroll = throttle(() => {
  // 处理滚动事件
}, 16)
```

## 响应式设计

组件已经内置响应式设计，在不同屏幕尺寸下会自动适配：

- **桌面端**: 完整显示所有信息
- **平板端**: 适当缩小字体和间距
- **手机端**: 紧凑布局，优化触控体验

## 常见问题

### Q: 虚拟滚动不生效？

A: 检查以下几点：

1. 确保容器有固定高度
2. 检查 `total` 属性是否正确设置
3. 确认 `itemHeight` 与实际项目高度一致

### Q: 搜索后滚动位置不正确？

A: 搜索后调用 `resetScroll()` 方法：

```javascript
const handleSearch = async ({ keyword }) => {
  await performSearch(keyword)
  virtualListRef.value.resetScroll()
}
```

### Q: 如何处理大量数据的初始化？

A: 使用分页加载，避免一次性加载所有数据：

```javascript
onMounted(async () => {
  await fetchChapters(1) // 只加载第一页
})
```

## 最佳实践

1. **数据量建议**: 单页数据量保持在50-200条之间
2. **搜索优化**: 使用服务端搜索，避免前端过滤大量数据
3. **缓存使用**: 合理使用搜索结果缓存，提升用户体验
4. **错误处理**: 添加适当的错误处理和重试机制
5. **加载状态**: 显示清晰的加载状态，避免用户困惑

## 示例项目

参考 `ChapterListUsageExample.vue` 获取完整的使用示例，包括：

- 模拟数据加载
- 服务端搜索
- 分页加载
- 性能监控
- 错误处理

## 技术支持

如有问题，请检查浏览器控制台是否有错误信息，或参考组件源码中的注释。
