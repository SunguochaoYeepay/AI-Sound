## 四、引擎集成流程

### 4.1 引擎注册机制

引擎注册机制允许动态添加和管理TTS引擎：

```python
class EngineRegistry:
    """引擎注册中心"""
    
    def __init__(self):
        self.engines = {}
        self.configs = {}
    
    def register_engine(self, engine_id: str, adapter_class, config: dict):
        """注册引擎"""
        self.engines[engine_id] = adapter_class
        self.configs[engine_id] = config
    
    async def create_adapter(self, engine_id: str) -> TTSEngineAdapter:
        """创建引擎适配器实例"""
        if engine_id not in self.engines:
            raise ValueError(f"引擎 {engine_id} 未注册")
        
        adapter_class = self.engines[engine_id]
        config = self.configs[engine_id]
        return adapter_class(**config)
    
    async def get_all_engines(self) -> list:
        """获取所有已注册引擎的基本信息"""
        result = []
        for engine_id, adapter_class in self.engines.items():
            config = self.configs[engine_id]
            adapter = await self.create_adapter(engine_id)
            capabilities = await adapter.get_capabilities()
            result.append({
                "id": engine_id,
                "name": capabilities["name"],
                "version": capabilities["version"],
                "status": "active"
            })
        return result
```

### 4.2 引擎自动发现

系统支持通过服务发现机制自动检测和注册引擎：

```python
class EngineDiscovery:
    """引擎发现服务"""
    
    def __init__(self, registry: EngineRegistry):
        self.registry = registry
        self.discovery_sources = []
    
    def add_discovery_source(self, source):
        """添加发现源"""
        self.discovery_sources.append(source)
    
    async def discover_engines(self):
        """发现并注册引擎"""
        for source in self.discovery_sources:
            engines = await source.get_engines()
            for engine in engines:
                self.registry.register_engine(
                    engine["id"],
                    get_adapter_class(engine["type"]),
                    engine["config"]
                )

# 实现基于Docker的发现源
class DockerDiscoverySource:
    """基于Docker的引擎发现"""
    
    async def get_engines(self):
        """从Docker环境中发现引擎"""
        client = docker.from_env()
        containers = client.containers.list(
            filters={"label": "ai-sound.engine=true"}
        )
        
        engines = []
        for container in containers:
            labels = container.labels
            if "ai-sound.engine.id" in labels:
                engines.append({
                    "id": labels["ai-sound.engine.id"],
                    "type": labels["ai-sound.engine.type"],
                    "config": {
                        "service_url": f"http://{container.name}:{labels.get('ai-sound.engine.port', '8000')}"
                    }
                })
        
        return engines
```

### 4.3 引擎选择策略

引擎选择策略决定对特定文本使用哪个引擎：

```python
class EngineSelector:
    """引擎选择器"""
    
    def __init__(self, registry: EngineRegistry):
        self.registry = registry
        self.strategies = []
    
    def add_strategy(self, strategy, priority=0):
        """添加选择策略"""
        self.strategies.append((strategy, priority))
        self.strategies.sort(key=lambda x: x[1], reverse=True)
    
    async def select_engine(self, text: str, requirements: dict = None) -> str:
        """选择合适的引擎"""
        if requirements is None:
            requirements = {}
        
        # 如果指定了引擎，直接使用
        if "engine_id" in requirements:
            return requirements["engine_id"]
        
        # 应用选择策略
        for strategy, _ in self.strategies:
            engine_id = await strategy.select(text, requirements, self.registry)
            if engine_id:
                return engine_id
        
        # 默认使用第一个可用引擎
        engines = await self.registry.get_all_engines()
        if engines:
            return engines[0]["id"]
        
        raise ValueError("没有可用的引擎")

# 基于文本长度的选择策略
class TextLengthStrategy:
    """基于文本长度的选择策略"""
    
    def __init__(self, length_thresholds: dict):
        self.length_thresholds = length_thresholds
    
    async def select(self, text: str, requirements: dict, registry: EngineRegistry) -> str:
        """根据文本长度选择引擎"""
        text_length = len(text)
        
        for engine_id, threshold in self.length_thresholds.items():
            if text_length <= threshold:
                return engine_id
        
        return None
```

## 五、声音管理设计

### 5.1 统一声音模型

声音模型统一了不同引擎的声音表示：

```python
class Voice:
    """统一声音模型"""
    
    def __init__(
        self,
        id: str,
        name: str,
        engine_id: str,
        gender: str = None,
        language: str = "zh-CN",
        description: str = "",
        attributes: dict = None,
        resources: dict = None
    ):
        self.id = id
        self.name = name
        self.engine_id = engine_id
        self.gender = gender
        self.language = language
        self.description = description
        self.attributes = attributes or {}
        self.resources = resources or {}
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "engine_id": self.engine_id,
            "gender": self.gender,
            "language": self.language,
            "description": self.description,
            "attributes": self.attributes
        }
```

### 5.2 声音库管理

声音库管理提供统一的声音管理功能：

```python
class VoiceLibrary:
    """声音库管理"""
    
    def __init__(self, registry: EngineRegistry):
        self.registry = registry
        self.custom_voices = {}  # 用户自定义声音
    
    async def get_all_voices(self) -> list:
        """获取所有可用声音"""
        all_voices = []
        
        # 获取引擎内置声音
        for engine_id in self.registry.engines:
            adapter = await self.registry.create_adapter(engine_id)
            engine_voices = await adapter.get_voices()
            for voice in engine_voices:
                voice["engine_id"] = engine_id
                all_voices.append(voice)
        
        # 添加用户自定义声音
        for voice_id, voice in self.custom_voices.items():
            all_voices.append(voice.to_dict())
        
        return all_voices
    
    async def get_voices_by_engine(self, engine_id: str) -> list:
        """获取指定引擎的声音"""
        voices = []
        
        # 获取引擎内置声音
        adapter = await self.registry.create_adapter(engine_id)
        engine_voices = await adapter.get_voices()
        for voice in engine_voices:
            voice["engine_id"] = engine_id
            voices.append(voice)
        
        # 添加该引擎的用户自定义声音
        for voice_id, voice in self.custom_voices.items():
            if voice.engine_id == engine_id:
                voices.append(voice.to_dict())
        
        return voices
    
    async def get_voice(self, voice_id: str) -> dict:
        """获取指定声音"""
        # 检查自定义声音
        if voice_id in self.custom_voices:
            return self.custom_voices[voice_id].to_dict()
        
        # 查找引擎内置声音
        for engine_id in self.registry.engines:
            adapter = await self.registry.create_adapter(engine_id)
            engine_voices = await adapter.get_voices()
            for voice in engine_voices:
                if voice["id"] == voice_id:
                    voice["engine_id"] = engine_id
                    return voice
        
        raise ValueError(f"声音 {voice_id} 不存在")
    
    async def add_custom_voice(self, voice: Voice) -> str:
        """添加自定义声音"""
        self.custom_voices[voice.id] = voice
        return voice.id
    
    async def update_custom_voice(self, voice_id: str, voice: Voice) -> bool:
        """更新自定义声音"""
        if voice_id not in self.custom_voices:
            return False
        self.custom_voices[voice_id] = voice
        return True
    
    async def delete_custom_voice(self, voice_id: str) -> bool:
        """删除自定义声音"""
        if voice_id not in self.custom_voices:
            return False
        del self.custom_voices[voice_id]
        return True
```

## 六、引擎配置管理

### 6.1 配置存储设计

引擎配置管理负责存储和应用引擎参数配置：

```python
class EngineConfigManager:
    """引擎配置管理"""
    
    def __init__(self, registry: EngineRegistry):
        self.registry = registry
        self.configs = {}  # 引擎配置
    
    async def get_default_config(self, engine_id: str) -> dict:
        """获取引擎默认配置"""
        adapter = await self.registry.create_adapter(engine_id)
        capabilities = await adapter.get_capabilities()
        
        default_config = {}
        for param in capabilities["params"]:
            default_config[param["name"]] = param["default"]
        
        return default_config
    
    async def get_engine_config(self, engine_id: str) -> dict:
        """获取引擎配置"""
        if engine_id not in self.configs:
            self.configs[engine_id] = await self.get_default_config(engine_id)
        
        return self.configs[engine_id]
    
    async def update_engine_config(self, engine_id: str, config: dict) -> bool:
        """更新引擎配置"""
        if engine_id not in self.registry.engines:
            return False
        
        current_config = await self.get_engine_config(engine_id)
        current_config.update(config)
        self.configs[engine_id] = current_config
        
        return True
    
    async def reset_engine_config(self, engine_id: str) -> bool:
        """重置引擎配置为默认值"""
        if engine_id not in self.registry.engines:
            return False
        
        self.configs[engine_id] = await self.get_default_config(engine_id)
        return True
```

### 6.2 配置应用机制

配置应用机制确保在合成请求中正确应用引擎配置：

```python
class TTSService:
    """TTS合成服务"""
    
    def __init__(
        self,
        registry: EngineRegistry,
        engine_selector: EngineSelector,
        config_manager: EngineConfigManager
    ):
        self.registry = registry
        self.engine_selector = engine_selector
        self.config_manager = config_manager
    
    async def synthesize(
        self,
        text: str,
        voice_id: str,
        params: dict = None,
        engine_id: str = None
    ) -> bytes:
        """合成语音"""
        if params is None:
            params = {}
        
        # 选择引擎
        if engine_id is None:
            requirements = {"voice_id": voice_id}
            requirements.update(params)
            engine_id = await self.engine_selector.select_engine(text, requirements)
        
        # 获取引擎配置
        config = await self.config_manager.get_engine_config(engine_id)
        
        # 合并参数
        merged_params = config.copy()
        merged_params.update(params)
        
        # 调用引擎合成
        adapter = await self.registry.create_adapter(engine_id)
        return await adapter.synthesize(text, voice_id, merged_params)
```

## 七、引擎Docker化设计

### 7.1 Docker容器结构

每个TTS引擎封装为独立的Docker容器：

```dockerfile
# MegaTTS3引擎Docker示例
FROM python:3.9-slim

LABEL ai-sound.engine=true
LABEL ai-sound.engine.id=megatts3
LABEL ai-sound.engine.type=megatts3
LABEL ai-sound.engine.port=8000

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "megatts3_service:app", "--host", "0.0.0.0", "--port", "8000"]
```

### 7.2 Docker Compose配置

使用Docker Compose组织多引擎部署：

```yaml
version: '3'

services:
  api:
    build: ./services/api
    ports:
      - "9930:9930"
    volumes:
      - ./data:/app/data
    depends_on:
      - megatts3
      - espnet
    networks:
      - ai-sound-net

  web-admin:
    build: ./services/web-admin
    ports:
      - "8080:80"
    depends_on:
      - api
    networks:
      - ai-sound-net

  megatts3:
    build: ./engines/megatts3
    volumes:
      - ./data/voices:/app/voices
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - ai-sound-net

  espnet:
    build: ./engines/espnet
    volumes:
      - ./data/models:/app/models
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    networks:
      - ai-sound-net

networks:
  ai-sound-net:
    driver: bridge
```

## 八、引擎监控设计

### 8.1 健康检查机制

定期检查引擎健康状态：

```python
class EngineMonitor:
    """引擎监控服务"""
    
    def __init__(self, registry: EngineRegistry, check_interval: int = 60):
        self.registry = registry
        self.check_interval = check_interval
        self.status = {}
        self.task = None
    
    async def start(self):
        """启动监控"""
        self.task = asyncio.create_task(self._monitor_loop())
    
    async def stop(self):
        """停止监控"""
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
    
    async def _monitor_loop(self):
        """监控循环"""
        while True:
            try:
                await self._check_all_engines()
            except Exception as e:
                logging.error(f"引擎监控错误: {str(e)}")
            
            await asyncio.sleep(self.check_interval)
    
    async def _check_all_engines(self):
        """检查所有引擎"""
        for engine_id in self.registry.engines:
            try:
                adapter = await self.registry.create_adapter(engine_id)
                health = await adapter.health_check()
                self.status[engine_id] = {
                    "status": "healthy" if health.get("status") == "ok" else "unhealthy",
                    "last_check": datetime.now().isoformat(),
                    "details": health
                }
            except Exception as e:
                self.status[engine_id] = {
                    "status": "unhealthy",
                    "last_check": datetime.now().isoformat(),
                    "error": str(e)
                }
    
    async def get_engine_status(self, engine_id: str = None) -> dict:
        """获取引擎状态"""
        if engine_id:
            return self.status.get(engine_id, {"status": "unknown"})
        return self.status
```

## 九、API接口设计

### 9.1 引擎API接口

```
# 获取所有引擎
GET /api/engines
响应:
{
  "engines": [
    {
      "id": "megatts3",
      "name": "MegaTTS3 引擎",
      "version": "1.0.0",
      "status": "healthy"
    },
    {
      "id": "espnet",
      "name": "ESPnet TTS",
      "version": "2.0.0",
      "status": "healthy"
    }
  ]
}

# 获取引擎详情
GET /api/engines/{engine_id}
响应:
{
  "id": "megatts3",
  "name": "MegaTTS3 引擎",
  "version": "1.0.0",
  "status": "healthy",
  "capabilities": { ... },
  "params": [ ... ]
}

# 获取引擎配置
GET /api/engines/{engine_id}/config
响应:
{
  "engine_id": "megatts3",
  "config": {
    "speed": 1.0,
    "pitch": 0.0,
    "volume": 1.0,
    "emotion": "neutral"
  }
}

# 更新引擎配置
POST /api/engines/{engine_id}/config
请求体:
{
  "speed": 1.2,
  "pitch": 2.0
}
响应:
{
  "success": true,
  "message": "配置更新成功"
}

# 测试引擎参数
POST /api/engines/{engine_id}/test
请求体:
{
  "text": "测试文本",
  "voice_id": "voice1",
  "params": {
    "speed": 1.2,
    "pitch": 2.0
  }
}
响应: 音频数据 (二进制)
```

### 9.2 声音API接口

```
# 获取所有声音
GET /api/voices?engine_id=megatts3
响应:
{
  "voices": [
    {
      "id": "voice1",
      "name": "女声1",
      "engine_id": "megatts3",
      "gender": "female",
      "language": "zh-CN",
      "description": "标准女声"
    },
    ...
  ]
}

# 获取声音详情
GET /api/voices/{voice_id}
响应:
{
  "id": "voice1",
  "name": "女声1",
  "engine_id": "megatts3",
  "gender": "female",
  "language": "zh-CN",
  "description": "标准女声",
  "attributes": { ... }
}

# 测试声音效果
POST /api/voices/{voice_id}/preview
请求体:
{
  "text": "这是一段测试文本",
  "params": {
    "speed": 1.0,
    "pitch": 0.0
  }
}
响应: 音频数据 (二进制)
```