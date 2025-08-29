# 🎵 AI-Sound 产品设计文档

## 🎯 产品定位

**基于MegaTTS3技术的智能语音克隆与多角色朗读平台**

核心价值：通过上传少量音频样本，快速克隆任意人声，实现个性化语音合成和多角色文本朗读。

## 🔬 技术原理深度分析

### MegaTTS3 工作机制
根据API分析，MegaTTS3的真实工作流程：

```
输入: 参考音频文件(.wav) + 文本 + [可选latent文件(.npy)]
参数: time_step(推理步数) + p_w(智能度权重) + t_w(相似度权重)
输出: 克隆的语音音频(.wav)
```

**关键理解**：
- **不是**传统的选择预设声音
- **而是**基于上传的音频样本进行声音克隆
- latent文件可以提升克隆质量和速度

## 🏗️ 重新设计的产品架构

### 1. 📝 语音克隆测试台（原基础TTS）

**功能定位**：MegaTTS3技术验证和单次语音生成

#### 核心交互流程：
```
1. 上传参考音频 (.wav) ← 必需
2. 上传latent文件 (.npy) ← 可选，提升效果
3. 输入要合成的文本
4. 调节合成参数
   - 推理步数 (time_step: 16-64)
   - 智能度权重 (p_w: 0.5-2.0) 
   - 相似度权重 (t_w: 1.0-5.0)
5. 生成并试听结果
6. 下载或保存为声音库
```

#### 界面设计：
```
┌─ 语音克隆测试台 ─────────────────────┐
│ ┌─ 音频上传区 ─────┐ ┌─ 参数调节区 ─┐ │
│ │ 📁 参考音频      │ │ 推理步数 32   │ │
│ │ 📁 Latent文件    │ │ 智能度 1.4    │ │ 
│ │ (可选，提升效果)  │ │ 相似度 3.0    │ │
│ └──────────────────┘ └──────────────┘ │
│ ┌─ 文本输入区 ─────────────────────── │
│ │ 请输入要克隆的文本内容...           │ │
│ └──────────────────────────────────── │
│ ┌─ 生成结果 ──────────────────────── │
│ │ 🎵 [播放] [下载] [保存为角色]      │ │
│ └──────────────────────────────────── │
└────────────────────────────────────────┘
```

### 2. 🎭 声音库管理（原角色管理）

**功能定位**：管理已克隆的声音样本，建立声音资产库

#### 声音库结构：
```javascript
VoiceProfile {
  id: "voice_001",
  name: "张三的声音",
  description: "温和的男性声音",
  referenceAudio: "zhang_san_sample.wav", // 原始参考音频
  latentFile: "zhang_san.npy",           // 提取的特征文件
  parameters: {                          // 最优参数
    time_step: 32,
    p_w: 1.4,
    t_w: 3.0
  },
  testText: "你好，这是我的声音测试。",
  createdAt: "2024-01-15",
  quality: "高质量", // 根据测试结果评级
  tags: ["男性", "中年", "磁性"]
}
```

#### 核心功能：
1. **声音入库**：测试台生成的满意效果可保存为声音库
2. **质量评估**：每个声音库包含质量评级和最优参数
3. **标签管理**：按性别、年龄、风格等分类
4. **批量测试**：一键测试所有声音库效果
5. **参数优化**：为每个声音库找到最佳合成参数

### 3. 📚 智能多角色朗读

**功能定位**：长文本的多角色语音合成，支持中断恢复

#### 复杂业务流程设计：

```
阶段1: 文本预处理
├── 上传文本文件
├── 智能分段(按段落/章节)
├── 对话识别与角色提取
└── 生成处理任务队列

阶段2: 角色声音分配  
├── 自动匹配声音库
├── 手动调整角色绑定
├── 批量预览角色效果
└── 确认角色映射关系

阶段3: 分段批量生成
├── 按段落队列化处理
├── 实时进度跟踪
├── 失败重试机制
├── 断点续传能力
└── 质量检查与人工干预

阶段4: 音频后处理
├── 段落音频合并
├── 音量标准化
├── 静音间隔插入
└── 最终音频输出
```

#### 中断恢复机制：
```javascript
ProjectStatus {
  id: "novel_001",
  name: "修仙传奇第一章",
  totalSegments: 150,        // 总段落数
  processedSegments: 87,     // 已处理段落
  failedSegments: [23, 45],  // 失败段落
  currentStatus: "processing", // processing/paused/completed/failed
  characterMapping: {...},    // 角色映射关系
  audioSegments: [           // 音频段落状态
    {segmentId: 1, status: "completed", audioPath: "seg_001.wav"},
    {segmentId: 2, status: "failed", error: "网络超时"},
    {segmentId: 3, status: "pending"}
  ],
  resumePoint: 88,          // 恢复处理点
  lastError: "GPU内存不足",
  createdAt: "2024-01-15",
  estimatedCompletion: "2024-01-15 18:30"
}
```

## 🎨 界面设计重构

### 布局改为左右结构：

```
┌─ 侧边导航 ─┐ ┌─ 主内容区 ──────────────────────┐
│ 🔬 克隆测试台 │ │                              │
│ 🎭 声音库    │ │                              │  
│ 📚 多角色朗读 │ │        当前页面内容            │
│ ⚙️ 系统设置  │ │                              │
│            │ │                              │
│ ───────── │ │                              │
│ 📊 使用统计  │ │                              │
│ 🔧 高级设置  │ │                              │
└────────────┘ └────────────────────────────────┘
```

## 🔧 技术实现细节

### 后端架构调整：

```python
# 声音库管理
class VoiceProfileManager:
    def create_profile(audio_file, latent_file, name, description):
        """从测试结果创建声音库"""
    
    def optimize_parameters(profile_id, test_texts):
        """为声音库找到最佳参数"""
    
    def batch_test(profile_ids, test_text):
        """批量测试声音库效果"""

# 多角色项目管理  
class NovelProjectManager:
    def create_project(text_file, project_name):
        """创建朗读项目"""
    
    def parse_segments(project_id):
        """分析文本，提取段落和角色"""
    
    def process_segments(project_id, start_segment=None):
        """分段处理，支持断点续传"""
    
    def merge_audio_segments(project_id):
        """合并音频段落"""

# 任务队列管理
class TaskQueueManager:
    def add_synthesis_task(segment_id, voice_profile, text, priority):
        """添加合成任务到队列"""
    
    def process_queue():
        """处理任务队列"""
    
    def handle_failure(task_id, error):
        """处理失败任务"""
    
    def resume_project(project_id):
        """恢复中断的项目"""
```

### 前端状态管理：

```javascript
// 实时状态更新
const useProjectStatus = (projectId) => {
  const [status, setStatus] = useState(null)
  
  useEffect(() => {
    // WebSocket连接实时更新
    const ws = new WebSocket(`ws://api/projects/${projectId}/status`)
    ws.onmessage = (event) => {
      setStatus(JSON.parse(event.data))
    }
  }, [])
  
  return status
}

// 断点续传控制
const resumeProject = async (projectId) => {
  const response = await api.post(`/projects/${projectId}/resume`)
  return response.data
}
```

## 🎯 用户使用场景

### 场景1: 个人声音克隆
```
用户：自媒体创作者
需求：用自己的声音制作视频配音
流程：
1. 录制10-30秒清晰发音样本
2. 上传到克隆测试台
3. 调试参数直到满意
4. 保存为个人声音库
5. 后续直接输入文稿生成配音
```

### 场景2: 多角色有声书制作
```
用户：有声书制作工作室  
需求：为小说配置多个角色声音
流程：
1. 收集不同风格的声音样本(男女老少)
2. 批量导入建立声音库
3. 上传小说文本，自动识别角色对话
4. 分配角色与声音的映射关系
5. 启动批量生成，支持分段处理
6. 最终合成完整有声书
```

### 场景3: 企业级应用
```
用户：企业培训部门
需求：用领导声音录制培训材料
流程：
1. 获得领导声音样本授权
2. 建立企业专用声音库
3. 批量生成各类培训音频
4. 定期更新和优化声音库
```

## 🚫 核心问题解决方案

### 问题1: 中断恢复机制
**解决方案**：
- 分段队列化处理
- 每段完成后立即保存状态
- 失败段落自动重试3次
- 用户可手动跳过问题段落
- 支持从任意段落恢复处理

### 问题2: 声音质量一致性
**解决方案**：
- 参数自动优化算法
- 质量评分系统
- A/B测试对比
- 人工质检流程

### 问题3: 长文本处理效率
**解决方案**：
- GPU队列调度
- 并行处理优化
- 内存管理策略
- 进度可视化

### 问题4: 角色识别准确性
**解决方案**：
- 多种对话格式支持
- 人工修正界面
- 学习用户习惯
- 模板化处理

## 📊 成功指标

### 技术指标
- 声音克隆相似度 > 85%
- 单段文本处理时间 < 10秒
- 系统可用率 > 99%
- 中断恢复成功率 > 95%

### 用户体验指标  
- 新用户完成首次克隆 < 5分钟
- 多角色项目设置 < 15分钟
- 用户满意度 > 4.5/5.0
- 功能使用率 > 80%

---

**核心设计理念**：深度理解技术本质，设计符合真实业务场景的产品功能，提供企业级的稳定性和易用性。