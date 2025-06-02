# 🎵 AI-Sound 系统设计文档

## 🎯 设计原则

**专注实用，避免过度设计，架构独立干净**

- ❌ **不做**：多TTS引擎扩展、复杂用户管理、过度监控
- ✅ **专注**：文字转语音、角色配音、多角色小说朗读
- 🎯 **架构**：完全独立的platform平台，避免与现有services冲突

## 🏗️ 系统架构

### 🔄 **新架构设计：干净独立**

```
AI-Sound/
├── MegaTTS/MegaTTS3/          # ✅ 现有稳定TTS服务 (保持不变)
├── platform/                  # 🆕 新的统一平台 (完全独立)
│   ├── backend/               # FastAPI后端
│   ├── frontend/              # Vue3前端
│   ├── data/                  # 数据和数据库
│   └── docker/                # Docker配置
├── services/                  # ❌ 现有混乱目录 (暂时保留，不动)
└── archive/                   # ✅ 已清理的历史文件
```

### 🏗️ **platform/ 详细结构**

```
platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py            # FastAPI应用入口
│   │   ├── models.py          # 数据模型
│   │   ├── database.py        # 数据库连接
│   │   ├── voice_manager.py   # 角色语音管理
│   │   ├── novel_reader.py    # 小说朗读功能
│   │   └── tts_client.py      # MegaTTS3客户端封装
│   ├── requirements.txt
│   ├── Dockerfile
│   └── start.py
│
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── BasicTTS.vue     # 基础TTS
│   │   │   ├── Characters.vue   # 角色管理
│   │   │   └── NovelReader.vue  # 小说朗读
│   │   ├── components/
│   │   │   ├── AudioPlayer.vue  # 音频播放器
│   │   │   ├── VoiceSelector.vue# 语音选择
│   │   │   └── TextUploader.vue # 文本上传
│   │   ├── api/
│   │   │   └── client.js        # API客户端
│   │   ├── router/
│   │   │   └── index.js
│   │   ├── App.vue
│   │   └── main.js
│   ├── package.json
│   ├── vite.config.js
│   ├── Dockerfile
│   └── nginx.conf
│
├── data/
│   ├── database.db            # SQLite数据库
│   ├── audio/                 # 生成的音频文件
│   └── uploads/               # 上传的文本文件
│
├── docker/
│   ├── docker-compose.yml     # 平台服务编排
│   └── .env                   # 环境变量
│
├── scripts/
│   ├── setup.py              # 初始化脚本
│   ├── start_platform.py     # 平台启动脚本
│   └── init_db.py            # 数据库初始化
│
└── README.md                  # 平台使用说明
```

## 🔧 **服务端口分配**

```
MegaTTS3 Core:     7929  # ✅ 现有TTS服务
Platform API:      8000  # 🆕 新后端API
Platform Web:      3000  # 🆕 新前端界面
Platform Demo:     8888  # ✅ 现有文档服务 (可选保留)
```

## 🎪 核心功能设计

### 🖥️ Platform Web 管理界面

#### 📝 基础TTS功能
- **文本输入框** - 支持长文本输入
- **语音角色选择** - 下拉选择可用语音
- **语速/音调调节** - 滑块控制语音参数
- **在线试听/下载** - 音频播放器 + 下载按钮

#### 🎭 角色管理功能
- **创建角色** - 角色名称 + 绑定语音ID
- **角色语音预览** - 测试文本试听角色声音
- **角色库管理** - 增删改查角色配置
- **角色语音测试** - 快速验证角色声音效果

#### 📚 小说朗读功能
- **文本上传** - 支持txt/docx文件上传
- **自动角色识别** - 智能解析对话中的角色
- **角色语音分配** - 手动或自动分配角色声音
- **批量生成音频** - 按章节生成音频文件
- **章节音频管理** - 音频文件列表和播放

## 🔧 技术架构

### 后端技术栈
- **FastAPI** - 轻量级API服务框架
- **SQLite** - 角色配置和项目数据存储
- **MegaTTS3 Client** - 封装对现有TTS服务的调用
- **Python 3.8+** - 主要开发语言

### 前端技术栈
- **Vue3** - 现代前端框架
- **Ant Design Vue** - UI组件库
- **Vite** - 构建工具
- **音频播放器组件** - 支持在线试听
- **文件上传组件** - 处理文本文件上传

## 💻 核心模块设计

### 🎭 Voice Manager (角色语音管理)

```python
class VoiceManager:
    def create_character(name: str, voice_id: str, voice_settings: dict):
        """创建角色配置"""
        # 保存角色名称、语音ID、语音参数到数据库
    
    def get_character_list():
        """获取角色列表"""
        # 从数据库读取所有角色配置
    
    def assign_voice_to_text(text: str, character_id: str):
        """为文本分配角色语音"""
        # 根据角色ID获取语音配置，调用MegaTTS3生成音频
    
    def test_character_voice(character_id: str, test_text: str):
        """测试角色语音"""
        # 使用测试文本生成音频样本
```

### 📚 Novel Reader (小说朗读)

```python
class NovelReader:
    def parse_text_file(file_path: str):
        """解析上传的文本文件"""
        # 读取txt/docx文件，分章节处理
    
    def extract_dialogues(text: str):
        """提取对话内容"""
        # 使用正则表达式识别对话标记（引号、破折号等）
    
    def auto_identify_characters(dialogues: list):
        """自动识别对话角色"""
        # 分析对话上下文，自动提取角色名称
    
    def assign_characters_to_voices(characters: list, voice_mapping: dict):
        """分配角色语音"""
        # 将识别的角色与语音角色进行映射
    
    def generate_chapter_audio(chapter_text: str, character_voices: dict):
        """生成章节音频"""
        # 按角色分段生成音频，合并成完整章节
```

### 🔗 TTS Client (MegaTTS3客户端封装)

```python
class TTSClient:
    def __init__(self, base_url="http://localhost:7929"):
        self.base_url = base_url
    
    def health_check():
        """检查MegaTTS3服务状态"""
        # GET /health
    
    def synthesize(text: str, voice_settings: dict):
        """调用TTS合成"""
        # POST /synthesize
    
    def get_available_voices():
        """获取可用语音列表"""
        # 从MegaTTS3获取支持的语音
```

### 🗄️ Database Schema

```sql
-- 角色配置表
CREATE TABLE characters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    voice_id TEXT NOT NULL,
    voice_settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 项目表
CREATE TABLE projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    type TEXT NOT NULL, -- 'basic_tts' | 'novel'
    content TEXT,
    settings JSON,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 音频文件表
CREATE TABLE audio_files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER,
    filename TEXT NOT NULL,
    file_path TEXT NOT NULL,
    character_id INTEGER,
    text_content TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (project_id) REFERENCES projects(id),
    FOREIGN KEY (character_id) REFERENCES characters(id)
);
```

## 🚀 启动方式

### 现有MegaTTS3服务
```bash
# 启动现有TTS核心服务 (保持不变)
cd MegaTTS/MegaTTS3
python start_api_demo.py
```

### 新Platform平台
```bash
# 启动新Platform平台
cd platform
python scripts/start_platform.py

# 或使用Docker
cd platform/docker
docker-compose up -d
```

## 🎯 实施计划

### Phase 1: 平台基础搭建 (2天)
**目标**: 搭建独立的platform平台基础框架

- [ ] 创建platform目录结构
- [ ] 搭建FastAPI后端框架
- [ ] 创建Vue3前端项目
- [ ] 实现TTS Client封装
- [ ] 基础的前后端通信

**验收标准**: Platform平台可以成功调用MegaTTS3服务生成音频

### Phase 2: 基础TTS界面 (2天)
**目标**: 实现基础文字转语音Web界面

- [ ] 开发BasicTTS.vue页面
- [ ] 实现文字转语音API
- [ ] 开发音频播放组件
- [ ] 集成下载功能
- [ ] 语音参数调节

**验收标准**: 用户可以通过Web界面输入文字，选择语音，生成并下载音频

### Phase 3: 角色语音管理 (3天)
**目标**: 实现角色创建和管理功能

- [ ] 设计数据库表结构
- [ ] 实现角色CRUD API
- [ ] 开发Characters.vue页面
- [ ] 实现角色语音预览功能
- [ ] 角色配置持久化存储

**验收标准**: 用户可以创建、编辑、删除角色，并为每个角色分配特定语音

### Phase 4: 多角色小说朗读 (5天)
**目标**: 实现文本解析和批量音频生成

- [ ] 实现文本文件上传解析
- [ ] 开发对话角色识别算法
- [ ] 实现角色语音自动分配
- [ ] 开发批量音频生成功能
- [ ] NovelReader.vue页面开发
- [ ] 章节音频管理界面

**验收标准**: 用户可以上传小说文本，系统自动识别角色，生成多角色朗读音频

## 🎯 **迁移策略**

### **阶段1：建立新平台**
- 创建platform目录结构
- 开发核心功能
- 验证可用性

### **阶段2：功能验证**
- 与MegaTTS3集成测试
- 用户界面完善
- 功能完整性验证

### **阶段3：平滑切换**
- 新平台稳定后
- 可选择性清理services目录
- 或者两套系统并存

## 🎨 用户界面设计

### 导航结构
```
AI-Sound Platform 管理后台
├── 📝 基础TTS        # 简单文字转语音
├── 🎭 角色管理       # 创建和管理语音角色
└── 📚 小说朗读       # 多角色文本朗读
```

### 页面布局
- **统一Header**: Logo + 导航菜单
- **侧边栏**: 功能导航
- **主内容区**: 各功能页面
- **Footer**: 系统信息

## 🔗 API接口设计

### 基础TTS接口
```
POST /api/tts/synthesize
{
    "text": "要转换的文字",
    "voice_id": "语音ID",
    "speed": 1.0,
    "pitch": 1.0
}
```

### 角色管理接口
```
GET    /api/characters          # 获取角色列表
POST   /api/characters          # 创建角色
PUT    /api/characters/{id}     # 更新角色
DELETE /api/characters/{id}     # 删除角色
```

### 小说朗读接口
```
POST /api/novel/upload          # 上传文本文件
POST /api/novel/parse           # 解析角色对话
POST /api/novel/generate        # 生成音频
GET  /api/novel/projects        # 获取项目列表
```

## 📊 成功指标

### 用户体验指标
- ✅ **操作简单**: 3步完成基础TTS（输入→选择→生成）
- ✅ **响应快速**: 单句语音生成<5秒
- ✅ **界面友好**: 零学习成本，直观易用

### 功能完成度
- ✅ **基础TTS**: 100%可用
- ✅ **角色管理**: 支持无限角色创建
- ✅ **小说朗读**: 自动识别准确率>80%

### 技术性能
- ✅ **系统稳定**: 99%可用性
- ✅ **音质保证**: 与MegaTTS3直接调用效果一致
- ✅ **扩展性**: 代码结构支持后续功能扩展

## 🎯 **架构优势**

### ✅ **完全独立**
- 不与现有services目录产生任何冲突
- 可以并行开发，不影响现有系统
- 清晰的职责分工

### ✅ **简洁高效**
- 单一platform目录，结构清晰
- 标准的前后端分离架构
- 容器化部署，一键启动

### ✅ **易于管理**
- 独立的数据库和文件存储
- 统一的配置和脚本
- 清晰的文档和说明

---

**设计理念**: 简单实用，专注核心功能，架构独立干净，为用户提供最佳的语音合成体验。