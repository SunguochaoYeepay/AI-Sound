# 📁 AI-Sound 项目结构

## 🏗️ 清洁的根目录结构

```
AI-Sound/                           # 🎵 项目根目录
├── 📚 核心文档
│   ├── README.md                   # 主要文档
│   ├── QUICKSTART.md              # 快速开始指南
│   ├── CHANGELOG.md               # 更新日志
│   └── MIGRATION_COMPLETE.md      # 迁移完成报告
│
├── 🚀 微服务架构
│   ├── services/                  # 微服务目录
│   │   ├── tts-services/         # TTS服务集群
│   │   │   └── megatts3/         # MegaTTS3服务 ✅
│   │   ├── gateway/              # API网关
│   │   └── tools/                # 工具和脚本
│   │
│   └── docker-compose.microservices.yml # 主编排文件
│
├── 🔧 原始代码库
│   └── MegaTTS/                   # 原始MegaTTS3代码
│
├── 📖 详细文档
│   └── docs/                      # 文档目录
│
├── 🛠️ 配置文件
│   ├── .gitignore                # Git忽略配置
│   └── .dockerignore             # Docker忽略配置
│
└── 📦 其他目录 (待整理)
    ├── boss/                     # 🚧 独立Vue项目
    ├── config/                   # 🚧 旧配置
    ├── scripts/                  # 🚧 旧脚本
    ├── monitoring/               # 🚧 监控配置
    ├── data/                     # 🚧 数据目录
    ├── static/                   # 🚧 静态文件
    ├── src/                      # 🚧 旧源码
    ├── docker/                   # 🚧 旧Docker
    ├── nginx/                    # 🚧 重复nginx
    ├── test_output/              # 🗑️ 空目录
    ├── templates/                # 🗑️ 空目录
    └── output/                   # 🗑️ 空目录
```

## ✅ 已清理的内容

### 🗑️ 删除的文件 (25+个)
- 所有临时测试脚本 (.py)
- 旧的Docker配置文件
- 重复的迁移文档
- 无用的部署脚本

### 📋 整合的文档
- 合并重复的README文件
- 统一微服务文档
- 创建快速开始指南
- 添加更新日志

## 🎯 推荐的最终结构

### 🔥 应该保留
```
AI-Sound/
├── README.md                      # ✅ 主文档
├── QUICKSTART.md                  # ✅ 快速开始
├── CHANGELOG.md                   # ✅ 更新日志
├── services/                      # ✅ 微服务核心
├── MegaTTS/                       # ✅ 原始代码
├── docs/                          # ✅ 详细文档
├── docker-compose.microservices.yml # ✅ 主编排
├── .gitignore                     # ✅ Git配置
└── .dockerignore                  # ✅ Docker配置
```

### 🚧 需要决策的目录
- **boss/**: 独立Vue项目，可移到单独仓库
- **monitoring/**: 监控配置，未来可用
- **data/**: 数据目录，可能有用
- **config/**: 旧配置，可以整理

### 🗑️ 可以删除的目录
- **test_output/**, **templates/**, **output/**: 空目录
- **nginx/**: 已有services/gateway/
- **scripts/**: 已有tools/
- **static/**, **src/**: 旧结构
- **docker/**: 旧Docker配置

## 🧹 清理建议

1. **立即删除空目录**:
   ```bash
   rmdir test_output templates output
   ```

2. **移动有用内容**:
   ```bash
   # 移动monitoring到services/
   move monitoring services/monitoring
   ```

3. **备份后删除重复目录**:
   ```bash
   # 备份有用配置后删除
   rmdir nginx scripts static src docker
   ```

---

**🎯 目标**: 保持根目录简洁，核心文件一目了然！ 