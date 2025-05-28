# AI-Sound 系统架构

## 一、整体架构图

```
┌─────────────────────────────────────────────────────────────────┐
│                       客户端应用层                              │
│  ┌─────────────────────────┐  ┌─────────────────────────────┐  │
│  │  Web管理后台           │  │  第三方应用集成            │  │
│  │  (Vue3 + Ant Design)   │  │  (DIFY/其他AI平台)         │  │
│  └──────────┬─────────────┘  └─────────────┬───────────────┘  │
└─────────────┼────────────────────────────────┼─────────────────┘
              │                                │
              ▼                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                          API网关层                              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │ FastAPI REST服务 (异步处理)                             │    │
│  │ ┌────────────────┐  ┌────────────────┐  ┌────────────┐  │    │
│  │ │ 管理API        │  │ HTTP集成API    │  │ 批处理API  │  │    │
│  │ └────────────────┘  └────────────────┘  └────────────┘  │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                         核心服务层                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ 小说内容   │  │ TTS引擎     │  │ 引擎选择器             │  │
│  │ 采集与解析 │  │ 适配器      │  │                        │  │
│  └──────┬──────┘  └──────┬──────┘  └─────────────┬───────────┘  │
│         │               │                        │              │
│         ▼               ▼                        ▼              │
│  ┌─────────────────────────────────────────────────────────┐    │
│  │              分布式任务队列 (Celery)                    │    │
│  └─────────────────────────────────────────────────────────┘    │
└───────────────────────────────┬─────────────────────────────────┘
                               │
                               ▼
┌─────────────────────────────────────────────────────────────────┐
│                        基础设施层                               │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │ GPU服务器   │  │ 音频存储    │  │ 监控与日志             │  │
│  │(CUDA/PyTorch)│  │(本地存储/S3)│  │(Prometheus/Grafana)     │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## 二、技术栈详解

### 2.1 编程语言与核心框架
- **主要语言**: Python 3.9+
- **AI框架**: PyTorch 2.0+ + CUDA 11.0+
- **Web后台**: Vue3 + Ant Design Vue 4.x
- **API服务**: FastAPI (异步Web框架)
- **任务调度**: Celery + Redis
- **容器化**: Docker + Docker Compose
- **API文档**: OpenAPI/Swagger

### 2.2 核心模块依赖

| 模块名称 | 版本 | 用途 |
|---------|------|------|
| MegaTTS3 | 1.0 | 核心语音合成引擎 |
| ESPnet | 2.0 | 自然度语音合成引擎 |
| httpx | 0.24.0 | 异步HTTP客户端 |
| pydantic | 2.0+ | API请求/响应模型验证 |
| librosa | 0.10.0 | 音频信号处理 |
| scipy | 1.10.0 | 数值计算与信号处理 |
| numpy | 1.24.0 | 数值计算基础库 |
| soundfile | 0.12.0 | 音频文件读写 |

## 三、子系统详解

### 3.1 API网关层

API网关是系统的统一入口，负责接收和处理所有外部请求。

#### 3.1.1 主要功能
- 请求路由与负载均衡
- 认证与授权
- 请求参数验证
- 响应格式化
- 跨域支持
- API文档生成

#### 3.1.2 核心组件
- **FastAPI服务**: 基于FastAPI实现的RESTful API服务
- **认证中间件**: 实现API Key和JWT认证
- **参数验证**: 使用Pydantic模型进行请求验证
- **异常处理**: 统一的异常捕获和处理
- **Swagger文档**: 自动生成的API文档

#### 3.1.3 扩展性设计
- 支持插件式API扩展
- 可配置的中间件链
- 动态路由规则

### 3.2 TTS引擎适配器层

适配器层是连接API网关和不同TTS引擎的桥梁，实现了统一的接口和功能适配。

#### 3.2.1 适配器设计
```python
class BaseTTSAdapter:
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        emotion: dict = None,
        style: dict = None
    ) -> bytes:
        """
        基础TTS合成接口
        返回: WAV格式音频数据
        """
        pass

    async def get_available_voices(self) -> List[dict]:
        """获取可用音色列表"""
        pass

    async def health_check(self) -> bool:
        """健康检查"""
        pass
```

#### 3.2.2 已实现适配器
- **MegaTTS3Adapter**: 适配MegaTTS3引擎，支持高表现力语音合成
- **ESPnetAdapter**: 适配ESPnet引擎，支持高自然度语音合成
- **BertVITS2Adapter**: (规划中) 适配Bert-VITS2引擎

#### 3.2.3 参数映射
为了统一接口，适配器层实现了不同引擎参数的映射和转换：
- 情感映射：统一情感类型和强度到引擎特定参数
- 风格映射：统一风格参数到引擎特定设置
- 音色映射：统一音色ID到引擎特定声音

### 3.3 引擎选择器

引擎选择器负责根据文本特征和需求自动选择最合适的TTS引擎。

#### 3.3.1 选择策略
```python
class SimpleEngineSelector:
    def select_engine(self, text: str, requirements: dict) -> str:
        # 长篇文本或正式场合使用ESPnet
        if len(text) > 300 or requirements.get("formal", False):
            return "espnet"
        # 对话、情感丰富的文本使用MegaTTS3
        elif '"' in text or requirements.get("emotion_intensity", 0) > 0.5:
            return "megatts3"
        # 默认使用MegaTTS3
        return "megatts3"
```

#### 3.3.2 选择规则
1. **对话文本** → MegaTTS3（适合情感丰富的对话）
2. **正式朗读** → ESPnet（适合长篇文本和正式场合）
3. **特殊风格** → Bert-VITS2（规划中，适合需要特定风格的场合）
4. **用户指定** → 直接使用用户指定的引擎

#### 3.3.3 优化机制
- 引擎负载考虑：在多个合适引擎间平衡负载
- 缓存优化：记录引擎对特定类型文本的性能表现
- 自适应学习：根据历史数据优化选择策略

### 3.4 服务监控系统

服务监控系统负责监控各个引擎和服务的健康状态。

#### 3.4.1 监控组件
```python
class ServiceMonitor:
    def __init__(self, tts_router: TTSEngineRouter, check_interval: int = 60):
        self.tts_router = tts_router
        self.check_interval = check_interval
        self.running = False
        self.task = None
        
    async def start(self):
        """启动监控任务"""
        ...
    
    async def _monitor_task(self):
        """监控任务主循环"""
        ...
```

#### 3.4.2 监控指标
- **引擎健康状态**：检查引擎是否可用
- **响应时间**：记录引擎响应时间
- **错误率**：统计引擎错误率
- **资源使用**：监控CPU、内存、GPU使用情况
- **任务队列**：监控任务队列长度和处理速度

#### 3.4.3 告警机制
- 引擎不可用时自动通知
- 响应时间超阈值告警
- 错误率超阈值告警
- 资源使用超阈值告警

### 3.5 文本处理流水线

文本处理流水线负责处理输入文本，准备合成任务。

#### 3.5.1 处理步骤
1. **文本清洗**：移除特殊字符，规范化标点
2. **分段处理**：将长文本分割为合适的段落
3. **角色识别**：识别对话文本中的角色
4. **情感分析**：分析文本情感倾向
5. **引擎分配**：为每个文本段选择合适的引擎

#### 3.5.2 实现示例
```python
class TextProcessor:
    def __init__(self, config: dict):
        self.config = config
        self.engine_selector = SimpleEngineSelector()
        
    async def process(self, text: str) -> List[dict]:
        # 文本清洗
        cleaned_text = self._clean_text(text)
        
        # 分段处理
        segments = self._split_text(cleaned_text)
        
        # 处理每个分段
        tasks = []
        for segment in segments:
            # 角色识别
            character = self._identify_character(segment)
            
            # 情感分析
            emotion = self._analyze_emotion(segment)
            
            # 引擎选择
            engine = self.engine_selector.select_engine(segment, {
                "character": character,
                "emotion": emotion
            })
            
            # 创建任务
            tasks.append({
                "text": segment,
                "engine": engine,
                "voice_id": self._map_character_to_voice(character),
                "emotion": emotion
            })
            
        return tasks
```

## 四、数据流向与处理

### 4.1 基础处理流程

```
文本输入 → API网关 → 参数验证 → 文本处理流水线 → 引擎选择 → 
引擎适配器 → TTS引擎处理 → 音频后处理 → 结果返回
```

### 4.2 批量处理流程

```
批量请求 → API网关 → 任务拆分 → 任务队列 → 并行处理 → 
结果汇总 → 状态跟踪 → 结果返回
```

### 4.3 异步处理机制

对于长文本或批量请求，系统使用异步处理机制：

1. 接收请求并创建任务
2. 返回任务ID和状态URL
3. 将任务加入Celery队列
4. 后台处理任务
5. 客户端通过状态URL查询进度
6. 任务完成后通过webhook通知客户端

### 4.4 缓存策略

系统实现了多级缓存策略：

1. **请求缓存**：相同文本和参数的请求直接返回缓存结果
2. **音频片段缓存**：常用音频片段缓存复用
3. **声纹特征缓存**：声纹特征加载后缓存在内存中
4. **模型缓存**：模型加载后保持在GPU内存中

## 五、安全与可扩展性

### 5.1 安全机制

#### 5.1.1 认证与授权
- API Key认证
- JWT令牌认证
- 用户权限控制

#### 5.1.2 数据安全
- HTTPS传输加密
- 敏感数据加密存储
- 临时文件安全清理

#### 5.1.3 资源限制
- API调用频率限制
- 并发请求限制
- 文本长度限制
- 任务队列优先级

### 5.2 扩展性设计

#### 5.2.1 引擎扩展
添加新的TTS引擎只需三步：
1. 创建新的适配器类实现BaseTTSAdapter接口
2. 在TTSEngineType枚举中添加新引擎类型
3. 在引擎选择器中添加新引擎的选择规则

```python
# 1. 添加新引擎类型
class TTSEngineType(str, Enum):
    MEGATTS3 = "megatts3"
    ESPNET = "espnet"
    NEW_ENGINE = "new_engine"  # 新增

# 2. 创建新适配器
class NewEngineAdapter(BaseTTSAdapter):
    def __init__(self, service_url: str):
        self.service_url = service_url
        
    async def synthesize(self, text: str, voice_id: str, **kwargs) -> bytes:
        # 实现合成逻辑
        ...
    
    # 实现其他接口方法...

# 3. 在API网关中注册
new_engine_adapter = NewEngineAdapter("http://new-engine:9933")
tts_router.register_engine(TTSEngineType.NEW_ENGINE, new_engine_adapter)
```

#### 5.2.2 功能扩展
系统支持通过插件机制扩展功能：
- 文本预处理插件
- 音频后处理插件
- 新API端点插件
- 监控指标插件

#### 5.2.3 部署扩展
系统支持多种部署方式：
- 单机部署：所有服务在一台服务器上
- 分布式部署：服务分布在多台服务器上
- 混合云部署：部分服务在本地，部分在云端
- Kubernetes部署：使用K8s管理容器集群

## 六、Docker与网络配置

### 6.1 Docker配置

系统使用Docker Compose管理容器，主要配置如下：

```yaml
# docker-compose.yml
services:
  api-gateway:
    build: ./services/api
    ports:
      - "9930:9930"
    environment:
      - MEGATTS3_URL=http://megatts3:9931
      - ESPNET_URL=http://espnet:9932
    depends_on:
      - megatts3
      - espnet
    networks:
      - ai-sound-network

  megatts3:
    image: megatts3-service:latest
    ports:
      - "9931:9931"
    networks:
      - ai-sound-network

  espnet:
    image: espnet-service:latest
    ports:
      - "9932:9932"
    networks:
      - ai-sound-network

  web-admin:
    build: ./services/web-admin
    ports:
      - "8080:80"
    depends_on:
      - api-gateway
    networks:
      - ai-sound-network

networks:
  ai-sound-network:
    external: true
```

### 6.2 网络配置

系统使用自定义Docker网络（ai-sound-network）连接各个服务：

1. **网络创建**：
```bash
docker network create ai-sound-network
```

2. **服务发现**：
- 服务间通过容器名互相访问
- API网关通过环境变量获取服务地址

3. **宿主机访问**：
- 通过端口映射暴露服务到宿主机
- API网关: 9930
- Web管理界面: 8080

4. **外部服务通信**：
- 在Docker容器中使用extra_hosts设置host.docker.internal
- 可以通过host.docker.internal访问宿主机服务

## 七、性能优化

### 7.1 GPU加速

系统利用GPU加速TTS引擎处理：

1. **模型优化**：
- FP16混合精度推理
- CUDA Graph优化
- TensorRT优化

2. **批处理优化**：
- 批量推理加速
- 动态批大小调整
- 梯度累积

### 7.2 并行处理

系统利用并行处理提高吞吐量：

1. **任务级并行**：
- 多任务并行处理
- 任务优先级队列

2. **段落级并行**：
- 长文本分段并行处理
- 结果顺序合并

3. **引擎级并行**：
- 多引擎并行处理
- 负载均衡

### 7.3 缓存优化

系统利用多级缓存减少重复计算：

1. **结果缓存**：
- 相同文本和参数的请求缓存
- LRU淘汰策略

2. **中间结果缓存**：
- 语音特征缓存
- 分段处理结果缓存

3. **模型缓存**：
- 模型预加载
- 模型常驻内存

## 八、未来扩展规划

### 8.1 引擎扩展

- **Bert-VITS2集成**：添加Bert-VITS2引擎支持
- **商业TTS引擎**：集成微软、讯飞等商业TTS引擎
- **定制模型支持**：支持用户上传和使用自定义TTS模型

### 8.2 功能扩展

- **实时流式处理**：支持长文本的实时流式合成
- **多语言支持**：扩展对更多语言的支持
- **语音克隆**：支持从短音频样本克隆声音
- **风格迁移**：支持音色间的风格迁移

### 8.3 系统扩展

- **分布式训练**：支持分布式模型训练
- **自动扩缩容**：根据负载自动扩缩服务实例
- **边缘部署**：支持边缘设备部署轻量级模型
- **联邦学习**：支持多机构间的联邦学习