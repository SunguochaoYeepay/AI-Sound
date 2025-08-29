# 前端架构重新设计

## 🎯 **新的页面结构**

### 1. 书籍结构化页面 (`/books/{bookId}/structure`)
```
📖 书籍结构管理
├── 📊 书籍概览
│   ├── 基本信息 (标题、作者、字数)
│   ├── 结构化状态 (原始/已分章/已分析)
│   └── 章节统计
├── 🔧 章节分割工具
│   ├── 自动检测 (智能分章)
│   ├── 手动分割 (正则表达式)
│   └── 预览和调整
└── 📋 章节列表
    ├── 章节标题编辑
    ├── 内容预览
    ├── 分析状态标记
    └── 批量选择操作
```

### 2. 智能分析管理页面 (`/projects/{projectId}/analysis`)
```
🤖 智能分析中心  
├── 📝 分析配置
│   ├── 大模型选择 (Dify工作流)
│   ├── 分析范围选择 (全书/章节/段落)
│   ├── 批处理设置
│   └── 预设配置管理
├── 🚀 分析任务
│   ├── 创建新分析会话
│   ├── 任务队列管理
│   ├── 实时进度显示
│   └── 错误处理和重试
├── 📊 分析结果
│   ├── 按章节展示结果
│   ├── 角色统计和分布
│   ├── 声音推荐查看
│   └── 结果对比和版本管理
└── 💾 配置管理
    ├── 保存当前配置
    ├── 加载历史配置
    ├── 导出/导入设置
    └── 预设模板管理
```

### 3. 合成任务管理页面 (`/projects/{projectId}/synthesis`)
```
🎵 合成任务中心
├── 📋 任务规划
│   ├── 选择分析结果
│   ├── 批次规划 (按章节/段落)
│   ├── 合成参数设置
│   └── 输出格式配置
├── ⚡ 执行监控
│   ├── 任务队列状态
│   ├── 实时进度追踪
│   ├── 资源使用监控
│   └── 错误日志查看
└── 📁 结果管理
    ├── 音频文件列表
    ├── 章节合并工具
    ├── 质量检查报告
    └── 最终作品导出
```

## 🧩 **核心组件设计**

### 1. BookStructureManager.vue
```javascript
// 书籍结构化管理组件
export default {
  name: 'BookStructureManager',
  data() {
    return {
      book: null,
      chapters: [],
      structureMode: 'auto', // 'auto' | 'manual' | 'regex'
      detectionRules: {
        chapterPattern: /^第[一二三四五六七八九十\d]+[章节]/,
        minChapterLength: 500,
        maxChapterLength: 50000
      },
      processing: false
    }
  },
  
  methods: {
    // 自动章节检测
    async autoDetectChapters() {
      const response = await bookAPI.detectChapters(this.book.id, {
        method: 'auto',
        rules: this.detectionRules
      })
      this.chapters = response.data.chapters
    },
    
    // 手动章节分割
    async manualSplitChapter(chapterId, splitPoint) {
      await bookAPI.splitChapter(chapterId, splitPoint)
      await this.loadChapters()
    },
    
    // 合并章节
    async mergeChapters(chapterIds) {
      await bookAPI.mergeChapters(chapterIds)
      await this.loadChapters()
    },
    
    // 保存章节结构
    async saveStructure() {
      await bookAPI.saveChapterStructure(this.book.id, this.chapters)
      this.$message.success('章节结构已保存')
    }
  }
}
```

### 2. AnalysisSessionManager.vue
```javascript
// 智能分析会话管理
export default {
  name: 'AnalysisSessionManager',
  data() {
    return {
      sessions: [],
      currentSession: null,
      analysisConfig: {
        llmProvider: 'dify',
        workflowId: '',
        targetType: 'chapters',
        selectedTargets: [],
        batchSize: 5,
        maxRetries: 3
      },
      progress: {
        total: 0,
        completed: 0,
        failed: 0,
        current: ''
      }
    }
  },
  
  methods: {
    // 创建分析会话
    async createAnalysisSession() {
      const response = await analysisAPI.createSession(this.projectId, {
        ...this.analysisConfig,
        targetIds: this.analysisConfig.selectedTargets
      })
      
      this.currentSession = response.data.session
      await this.startAnalysis()
    },
    
    // 开始分析
    async startAnalysis() {
      if (!this.currentSession) return
      
      // 启动WebSocket连接监听进度
      this.connectProgressSocket()
      
      const response = await analysisAPI.startSession(this.currentSession.id)
      if (response.data.success) {
        this.$message.success('分析任务已启动')
      }
    },
    
    // 实时进度监听
    connectProgressSocket() {
      const ws = new WebSocket(`ws://localhost:3001/ws/analysis/${this.currentSession.id}`)
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data)
        
        if (data.type === 'progress') {
          this.progress = data.progress
        } else if (data.type === 'result') {
          this.handleAnalysisResult(data.result)
        } else if (data.type === 'error') {
          this.handleAnalysisError(data.error)
        }
      }
    },
    
    // 保存用户配置
    async saveUserConfig(configName) {
      const config = {
        analysisConfig: this.analysisConfig,
        voiceMappings: this.voiceMappings,
        synthesisParams: this.synthesisParams
      }
      
      await presetsAPI.savePreset({
        name: configName,
        configType: 'analysis_complete',
        configData: config,
        scope: 'project',
        scopeId: this.projectId
      })
      
      this.$message.success('配置已保存')
    }
  }
}
```

### 3. ConfigurationManager.vue
```javascript
// 配置管理组件
export default {
  name: 'ConfigurationManager',
  data() {
    return {
      presets: [],
      currentConfig: {},
      saveDialogVisible: false,
      loadDialogVisible: false,
      configName: '',
      configDescription: ''
    }
  },
  
  methods: {
    // 加载预设列表
    async loadPresets() {
      const response = await presetsAPI.getPresets({
        scope: 'project',
        scopeId: this.projectId,
        configType: 'analysis_complete'
      })
      this.presets = response.data.presets
    },
    
    // 保存当前配置
    async saveCurrentConfig() {
      const config = this.collectCurrentConfig()
      
      await presetsAPI.savePreset({
        name: this.configName,
        description: this.configDescription,
        configType: 'analysis_complete',
        configData: config,
        scope: 'project',
        scopeId: this.projectId
      })
      
      this.$message.success('配置保存成功')
      await this.loadPresets()
    },
    
    // 应用预设配置
    async applyPreset(presetId) {
      const response = await presetsAPI.getPreset(presetId)
      const config = response.data.preset.configData
      
      this.applyConfiguration(config)
      this.$message.success('配置已应用')
    },
    
    // 导出配置
    exportConfig() {
      const config = this.collectCurrentConfig()
      const blob = new Blob([JSON.stringify(config, null, 2)], {
        type: 'application/json'
      })
      
      const url = URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = `ai-sound-config-${Date.now()}.json`
      a.click()
    }
  }
}
```

## 🔄 **工作流程设计**

### 分析流程
```javascript
// 完整的智能分析流程
const analysisWorkflow = {
  // 1. 书籍结构化
  async structureBook(bookId) {
    return await bookAPI.detectChapters(bookId)
  },
  
  // 2. 创建分析会话
  async createSession(projectId, config) {
    return await analysisAPI.createSession(projectId, config)
  },
  
  // 3. 分批执行分析
  async executeAnalysis(sessionId) {
    // 启动后台任务，通过WebSocket返回进度
    return await analysisAPI.startSession(sessionId)
  },
  
  // 4. 处理结果
  async processResults(sessionId) {
    const results = await analysisAPI.getSessionResults(sessionId)
    return this.mergeAnalysisResults(results)
  },
  
  // 5. 用户确认和修改
  async applyUserConfig(resultId, userConfig) {
    return await analysisAPI.updateResultConfig(resultId, userConfig)
  },
  
  // 6. 保存最终配置
  async saveFinalConfig(projectId, config) {
    return await analysisAPI.saveFinalConfig(projectId, config)
  }
}
```

### 合成流程
```javascript
// 分批合成流程
const synthesisWorkflow = {
  // 1. 创建合成任务
  async createSynthesisTask(projectId, config) {
    return await synthesisAPI.createTask(projectId, config)
  },
  
  // 2. 分批执行合成
  async executeSynthesis(taskId) {
    return await synthesisAPI.startTask(taskId)
  },
  
  // 3. 监控进度
  monitorProgress(taskId, callback) {
    const ws = new WebSocket(`ws://localhost:3001/ws/synthesis/${taskId}`)
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      callback(data)
    }
  },
  
  // 4. 合并结果
  async mergeResults(taskId) {
    return await synthesisAPI.mergeAudioFiles(taskId)
  }
}
```

## 🎨 **UI/UX 设计要点**

### 进度显示
- **实时进度条** - WebSocket更新
- **任务队列可视化** - 显示等待/处理中/已完成
- **错误处理界面** - 重试按钮、错误详情
- **预估时间** - 基于历史数据计算

### 配置管理
- **一键保存** - 保存当前所有配置
- **快速应用** - 预设配置快速切换
- **配置对比** - 显示配置差异
- **导入导出** - 支持配置文件

### 批处理控制
- **暂停/恢复** - 任务控制
- **优先级调整** - 章节处理顺序
- **资源限制** - 并发数控制
- **失败重试** - 自动重试机制 