# AI-Sound 开发者指南

## 项目架构

AI-Sound 项目采用模块化微服务架构，主要组件包括：

1. **API 网关**：统一的 API 接口，负责路由和任务分发
2. **TTS 引擎服务**：独立的 TTS 引擎，包括 MegaTTS3、ESPnet 和 Bert-VITS2
3. **Web 管理界面**：用户友好的管理控制台
4. **适配器层**：连接 API 网关和不同 TTS 引擎的桥梁

## 技术栈

- **后端**：Python 3.10+, FastAPI, CUDA, PyTorch
- **前端**：Vue3, Element Plus
- **容器化**：Docker, Docker Compose
- **网络**：自定义 Docker 网络（ai-sound-network）
- **监控**：内置服务监控组件

## 开发环境设置

### 1. 克隆代码库

```bash
git clone https://github.com/your-org/ai-sound.git
cd ai-sound
```

### 2. 安装开发依赖

对于 API 服务开发：
```bash
cd services/api
pip install -r requirements.txt
```

对于 Web 管理界面开发：
```bash
cd services/web-admin
npm install
```

### 3. 启动模拟服务（用于开发）

```bash
cd services/mock_services
python megatts3_mock.py  # 在一个终端中运行
python espnet_mock.py    # 在另一个终端中运行
```

### 4. 在开发模式下启动 API 服务

```bash
cd services/api
python -m src.main --dev
```

### 5. 在开发模式下启动 Web 服务

```bash
cd services/web-admin
npm run dev
```

## 核心组件详解

### 1. TTSEngine 接口

TTSEngine 是所有 TTS 引擎适配器必须实现的接口，位于 `services/api/src/tts/engine.py`：

```python
class TTSEngine(Protocol):
    async def synthesize(self, text: str, voice_id: str, **kwargs) -> bytes:
        """将文本合成为音频"""
        ...
    
    async def get_available_voices(self) -> Dict[str, Dict]:
        """获取可用音色列表"""
        ...
    
    async def health_check(self) -> bool:
        """检查引擎健康状态"""
        ...
```

### 2. 适配器实现

每个 TTS 引擎都有一个对应的适配器，位于 `services/api/src/tts/adapters/` 目录下。例如：

```python
class MegaTTS3Adapter:
    def __init__(self, service_url: str):
        self.service_url = service_url
        self.client = httpx.AsyncClient(timeout=30.0)
        
    async def synthesize(self, text: str, voice_id: str, **kwargs) -> bytes:
        # 实现合成逻辑，调用 MegaTTS3 服务
        ...
```

### 3. 引擎路由器

TTSEngineRouter 负责管理所有已注册的 TTS 引擎，位于 `services/api/src/tts/engine.py`：

```python
class TTSEngineRouter:
    def __init__(self):
        self.engines: Dict[TTSEngineType, TTSEngine] = {}
        self.health_status: Dict[str, Dict] = {}
        
    def register_engine(self, engine_type: TTSEngineType, engine: TTSEngine) -> None:
        """注册 TTS 引擎"""
        ...
    
    async def synthesize(self, engine_type: TTSEngineType, text: str, voice_id: str, **kwargs) -> bytes:
        """使用指定引擎合成音频"""
        ...
```

### 4. 引擎选择器

EngineSelector 根据文本特征选择最合适的 TTS 引擎，位于 `services/api/src/tts/engine_selector.py`：

```python
class EngineSelector:
    def select_engine(self, text: str, requirements: Dict[str, Any] = None) -> TTSEngineType:
        """根据文本特征选择合适的引擎"""
        # 考虑文本长度、情感需求、文本类型等因素
        ...
```

### 5. 服务监控

ServiceMonitor 定期检查各个引擎的健康状态，位于 `services/api/src/monitor/service_monitor.py`：

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

## 添加新的 TTS 引擎

要添加新的 TTS 引擎，请按照以下步骤操作：

1. 在 `TTSEngineType` 枚举中添加新引擎类型
2. 创建一个新的适配器类，实现 `TTSEngine` 接口
3. 在 API 网关中注册新引擎
4. 扩展引擎选择策略支持新引擎
5. 更新 Web 管理界面支持新引擎的管理

示例：

```python
# 1. 添加新引擎类型
class TTSEngineType(str, Enum):
    MEGATTS3 = "megatts3"
    ESPNET = "espnet"
    NEW_ENGINE = "new_engine"  # 新增

# 2. 创建新适配器
class NewEngineAdapter:
    def __init__(self, service_url: str):
        self.service_url = service_url
        
    async def synthesize(self, text: str, voice_id: str, **kwargs) -> bytes:
        # 实现合成逻辑
        ...
    
    # 实现其他接口方法...

# 3. 在 API 网关中注册
new_engine_adapter = NewEngineAdapter("http://new-engine:9933")
tts_router.register_engine(TTSEngineType.NEW_ENGINE, new_engine_adapter)
```

## 代码风格指南

- 使用 PEP 8 代码风格
- 所有函数和类添加类型提示
- 关键函数添加详细注释
- 使用异步函数处理 I/O 操作
- 遵循依赖注入原则

## 测试指南

### 单元测试

```bash
cd services/api
pytest src/tests/unit
```

### 集成测试

```bash
cd services/api
pytest src/tests/integration
```

### 端到端测试

```bash
# 确保所有服务都在运行
pytest src/tests/e2e
```

## 调试技巧

1. 使用 Docker 日志查看服务状态：
   ```bash
   docker-compose logs -f api
   ```

2. 检查 API 健康状态：
   ```bash
   curl http://localhost:9930/health
   ```

3. 检查引擎连接状态：
   ```bash
   curl http://localhost:9930/health/engines
   ```

4. 监控 API 请求：
   ```bash
   docker-compose logs -f api | grep "INFO - 收到TTS请求"
   ```

## 常见问题

1. **问题**：Docker 容器无法连接到其他服务  
   **解决方案**：检查网络配置，确保所有服务连接到同一个 Docker 网络

2. **问题**：TTS 引擎健康检查失败  
   **解决方案**：检查引擎服务是否正常运行，检查 URL 配置是否正确

3. **问题**：音频合成请求超时  
   **解决方案**：增加超时时间，检查引擎负载状态

4. **问题**：API 服务启动失败  
   **解决方案**：检查依赖项是否安装完成，检查配置文件是否正确

## 贡献指南

1. Fork 项目
2. 创建特性分支：`git checkout -b feature/amazing-feature`
3. 提交更改：`git commit -m 'Add amazing feature'`
4. 推送到分支：`git push origin feature/amazing-feature`
5. 提交 Pull Request

## 联系方式

如有任何问题或建议，请联系项目维护者。