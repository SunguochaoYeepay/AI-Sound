# Stagewise工具栏配置指南

## 问题描述

在开发环境中，Stagewise工具栏会自动扫描多个端口（如5747、5749等）来寻找可用的代理服务，这导致了404错误请求。

## 解决方案

### 方案1：临时禁用工具栏（最简单）

在 `src/App.vue` 中注释掉Stagewise工具栏：

```vue
<!-- 临时禁用Stagewise工具栏 -->
<!-- <StagewiseToolbar v-if="isDev" :config="stagewiseConfig" /> -->
```

### 方案2：配置工具栏（当前实施的方案）

我们已经实施了以下配置：

1. **创建了配置文件** `stagewise.config.js`：
   - 禁用了实验性功能
   - 添加了网络配置选项（为未来版本准备）
   - 设置了调试选项

2. **修改了App.vue**：
   - 导入配置文件
   - 将配置传递给StagewiseToolbar组件

### 方案3：忽略404错误

这些404错误不会影响应用程序的正常功能，可以安全地忽略。

## 配置选项说明

### stagewise.config.js

```javascript
export default {
  // 插件配置
  plugins: [],
  
  // 实验性功能
  experimental: {
    enableStagewiseMCP: false,    // 禁用MCP服务器
    enableToolCalls: false        // 禁用工具调用
  },
  
  // 网络配置（未来版本可能支持）
  network: {
    scanPorts: [8001],            // 只扫描后端端口
    excludePorts: [5747, 5749],   // 排除特定端口
    timeout: 1000                 // 连接超时
  },
  
  // 调试配置
  debug: {
    verbose: false,               // 详细日志
    disableAutoScan: true         // 禁用自动扫描
  }
}
```

## 注意事项

1. **当前版本限制**：Stagewise工具栏的当前版本（0.6.1）可能不支持所有网络配置选项。

2. **实验性功能**：我们禁用了实验性功能以减少不必要的网络请求。

3. **开发环境专用**：工具栏只在开发环境中启用（`v-if="isDev"`）。

## 验证配置

重启开发服务器后，检查浏览器控制台：

1. 404错误应该减少或消失
2. Stagewise工具栏仍然可用
3. 不应该有到端口5747和5749的请求

## 故障排除

如果问题仍然存在：

1. **检查配置加载**：确保配置文件正确导入
2. **查看控制台**：检查是否有配置相关的错误
3. **临时禁用**：使用方案1临时禁用工具栏
4. **更新版本**：考虑更新到更新版本的Stagewise工具栏

## 相关文档

- [Stagewise官方文档](https://stagewise.io/docs)
- [GitHub仓库](https://github.com/stagewise-io/stagewise)
- [NPM包文档](https://www.npmjs.com/package/@stagewise/toolbar-vue)
