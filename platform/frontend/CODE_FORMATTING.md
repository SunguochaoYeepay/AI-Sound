# 代码格式化指南

## 概述

项目现已配置了 ESLint 和 Prettier 来确保代码质量和一致的格式化风格。

## 可用命令

### 代码检查和自动修复
```bash
npm run lint
```
这个命令会：
- 检查所有 `.vue`, `.js`, `.ts` 等文件的代码质量
- 自动修复可以修复的问题
- 报告需要手动修复的问题

### 代码格式化
```bash
npm run format
```
这个命令会：
- 使用 Prettier 格式化 `src/` 目录下的所有文件
- 统一代码风格（缩进、引号、分号等）

## 配置文件

### ESLint 配置 (`.eslintrc.json`)
- 基于 Vue 3 + TypeScript 推荐配置
- 集成 Prettier 格式化规则
- 允许 console 和 debugger（开发阶段）
- 关闭 Vue 组件多词命名要求

### Prettier 配置 (`.prettierrc`)
- 不使用分号
- 使用单引号
- 2 空格缩进
- 行宽限制 100 字符
- Vue 文件中的 script 和 style 标签缩进

## IDE 集成

### VS Code
推荐安装以下扩展：
- ESLint
- Prettier - Code formatter
- Vetur 或 Volar (Vue 支持)

### 自动格式化设置
在 VS Code 的 `settings.json` 中添加：
```json
{
  "editor.formatOnSave": true,
  "editor.defaultFormatter": "esbenp.prettier-vscode",
  "[vue]": {
    "editor.defaultFormatter": "esbenp.prettier-vscode"
  }
}
```

## 解决格式错误

如果你在 IDE 中看到格式错误提示：

1. **运行格式化命令**：
   ```bash
   npm run format
   npm run lint
   ```

2. **检查 IDE 配置**：
   - 确保安装了 ESLint 和 Prettier 扩展
   - 检查是否启用了自动格式化

3. **重启 IDE**：
   - 有时需要重启 IDE 来加载新的配置

## 注意事项

- 在提交代码前，建议运行 `npm run lint` 和 `npm run format`
- 如果遇到无法自动修复的 ESLint 错误，需要手动修复
- 配置文件可以根据团队需求进行调整