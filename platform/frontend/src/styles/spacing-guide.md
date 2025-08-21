# 间距系统使用指南

## 概述

为了避免硬编码样式值，我们定义了一套统一的CSS变量系统来管理间距和布局。

## CSS变量定义

### 基础间距变量
```css
--spacing-xs: 4px;    /* 超小间距 */
--spacing-sm: 8px;    /* 小间距 */
--spacing-md: 12px;   /* 中等间距 */
--spacing-lg: 16px;   /* 大间距 */
--spacing-xl: 24px;   /* 超大间距 */
--spacing-xxl: 32px;  /* 特大间距 */
--spacing-xxxl: 48px; /* 最大间距 */
```

### 内容区域间距
```css
--content-padding: var(--spacing-xl);      /* 标准内容间距 (24px) */
--content-padding-sm: var(--spacing-lg);   /* 小内容间距 (16px) */
--content-padding-lg: var(--spacing-xxl);  /* 大内容间距 (32px) */
```

### 布局高度计算
```css
--header-height: 64px;
--sidebar-width: 180px;
--sidebar-width-collapsed: 80px;
--content-min-height: calc(100vh - var(--header-height));
```

## 使用方法

### 1. 直接使用CSS变量
```css
.my-component {
  padding: var(--content-padding);
  margin: var(--spacing-lg);
  min-height: var(--content-min-height);
}
```

### 2. 使用预定义的布局类
```html
<!-- 标准内容容器 -->
<div class="content-container">
  <!-- 内容 -->
</div>

<!-- 小间距内容容器 -->
<div class="content-container-sm">
  <!-- 内容 -->
</div>

<!-- 大间距内容容器 -->
<div class="content-container-lg">
  <!-- 内容 -->
</div>
```

### 3. 响应式设计
这些变量和类会自动适配不同屏幕尺寸：
- 桌面端：使用定义的间距值
- 平板端 (≤768px)：自动调整为 `--spacing-lg`
- 手机端 (≤480px)：自动调整为 `--spacing-md`

## 迁移指南

### 替换硬编码值

**之前：**
```css
.my-page {
  padding: 24px;
  min-height: calc(100vh - 60px);
}
```

**之后：**
```css
.my-page {
  padding: var(--content-padding);
  min-height: var(--content-min-height);
}
```

**或者使用布局类：**
```html
<div class="content-container">
  <!-- 页面内容 -->
</div>
```

### 常见替换对照表

| 硬编码值 | CSS变量 | 说明 |
|---------|---------|------|
| `24px` | `var(--content-padding)` | 标准内容间距 |
| `16px` | `var(--content-padding-sm)` | 小内容间距 |
| `32px` | `var(--content-padding-lg)` | 大内容间距 |
| `calc(100vh - 60px)` | `var(--content-min-height)` | 内容区域最小高度 |
| `8px` | `var(--spacing-sm)` | 小间距 |
| `12px` | `var(--spacing-md)` | 中等间距 |
| `16px` | `var(--spacing-lg)` | 大间距 |
| `48px` | `var(--spacing-xxxl)` | 最大间距 |

## 最佳实践

1. **优先使用布局类**：对于标准的内容容器，优先使用 `.content-container` 类
2. **使用语义化变量**：根据用途选择 `--content-padding` 而不是 `--spacing-xl`
3. **保持一致性**：在整个项目中使用相同的间距系统
4. **响应式考虑**：变量会自动适配不同屏幕尺寸，无需额外处理

## 示例

```vue
<template>
  <div class="page-container">
    <div class="content-container">
      <h1>页面标题</h1>
      <div class="card-grid">
        <div class="card" v-for="item in items" :key="item.id">
          {{ item.title }}
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.page-container {
  background: var(--ant-color-bg-container);
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
  gap: var(--spacing-lg);
  margin-top: var(--spacing-xl);
}

.card {
  padding: var(--spacing-lg);
  border-radius: 8px;
  background: var(--ant-color-bg-container);
  border: 1px solid var(--ant-border-color-base);
}
</style>
```
