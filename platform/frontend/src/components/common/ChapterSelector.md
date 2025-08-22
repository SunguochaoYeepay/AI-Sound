# 统一章节选择器组件 (ChapterSelector)

## 概述

这是一个统一的章节选择器组件，整合了环境音合成、合成中心、书籍详情三个页面的所有章节选择功能。

## 功能特性

- ✅ 章节选择
- ✅ 收起/展开
- ✅ 搜索功能
- ✅ 章节状态显示
- ✅ 刷新功能
- ✅ 重置/检测功能
- ✅ 翻页功能
- ✅ 加载更多功能
- ✅ 暗黑模式支持

## Props

### 数据 Props

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| chapters | Array | [] | 章节列表数据 |
| selectedChapter | Number/String | null | 当前选中的章节ID |
| loading | Boolean | false | 加载状态 |
| loadingMore | Boolean | false | 加载更多状态 |
| detectingChapters | Boolean | false | 章节检测状态 |

### 功能开关 Props

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| showCollapse | Boolean | true | 是否显示收起/展开功能 |
| showSearch | Boolean | false | 是否显示搜索功能 |
| showStatus | Boolean | false | 是否显示章节状态 |
| showRefresh | Boolean | false | 是否显示刷新按钮 |
| showReset | Boolean | false | 是否显示重置/检测按钮 |
| showChapterCount | Boolean | false | 是否显示章节总数 |

### 配置 Props

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| title | String | '选择章节' | 组件标题 |
| pageSize | Number | 10 | 每页显示的章节数量 |
| paginationType | String | 'page' | 分页类型：'page' \| 'load-more' |
| collapsed | Boolean | false | 是否收起状态 |

## Events

| 事件名 | 参数 | 说明 |
|--------|------|------|
| select | chapterId | 选择章节时触发 |
| refresh | - | 点击刷新按钮时触发 |
| reset | - | 点击重置/检测按钮时触发 |
| search | keyword | 搜索时触发 |
| load-more | - | 点击加载更多时触发 |
| toggle-collapse | - | 收起/展开时触发 |

## 使用示例

### 1. 环境音合成详情页面

```vue
<ChapterSelector
  :chapters="chapters"
  :selected-chapter="selectedChapter?.id"
  :collapsed="chapterListCollapsed"
  :show-collapse="true"
  :show-search="false"
  :show-status="false"
  :show-refresh="false"
  :show-reset="false"
  :pagination-type="'page'"
  :page-size="10"
  title="选择章节"
  @select="handleChapterSelect"
  @toggle-collapse="toggleChapterList"
/>
```

### 2. 合成中心页面

```vue
<ChapterSelector
  :chapters="chapters"
  :selected-chapter="selectedChapter"
  :loading="chaptersLoading"
  :show-collapse="false"
  :show-search="false"
  :show-status="true"
  :show-refresh="true"
  :show-reset="false"
  :pagination-type="'page'"
  :page-size="10"
  title="选择章节"
  @select="handleChapterSelect"
  @refresh="loadChapters"
/>
```

### 3. 书籍详情页面

```vue
<ChapterSelector
  :chapters="chapters"
  :selected-chapter="selectedChapterId"
  :loading="false"
  :detecting-chapters="detectingChapters"
  :show-collapse="true"
  :show-search="true"
  :show-status="false"
  :show-refresh="false"
  :show-reset="true"
  :show-chapter-count="true"
  :pagination-type="'load-more'"
  :page-size="100"
  title="章节列表"
  @select="selectChapter"
  @reset="detectChapters"
  @load-more="loadMoreChapters"
  @toggle-collapse="handleChapterListToggle"
/>
```

## 章节数据结构

```javascript
{
  id: Number,           // 章节ID
  chapter_number: Number, // 章节号
  chapter_title: String,  // 章节标题
  word_count: Number,     // 字数
  analysis_status: String // 分析状态：'pending' | 'processing' | 'completed' | 'failed' | 'ready'
}
```

## 样式定制

组件使用 Ant Design Vue 的设计规范，支持暗黑模式。主要样式类：

- `.chapter-selector` - 主容器
- `.section-header` - 头部区域
- `.chapter-menu` - 章节菜单
- `.chapter-menu-item` - 章节项
- `.pagination-controls` - 翻页控制
- `.load-more-section` - 加载更多区域

## 注意事项

1. 确保传入的 `chapters` 数组包含必要的字段
2. 根据页面需求合理配置功能开关
3. 翻页类型选择：
   - `page`: 适合章节数量较多的情况
   - `load-more`: 适合需要虚拟滚动的情况
4. 搜索功能会自动过滤章节标题和章节号

