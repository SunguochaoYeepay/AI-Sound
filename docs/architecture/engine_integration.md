# AI-Sound TTS引擎整合方案

## 一、引擎整合概述

AI-Sound 系统整合了多种 TTS 引擎，通过统一的适配器层实现无缝协作。当前已整合的引擎包括 MegaTTS3 和 ESPnet，计划中将整合 Bert-VITS2。

### 1.1 整合架构

```
[API网关]
    │
    ├── [引擎选择器]
    │       │
    │       │ 
    ├───────┼───────┬───────────┐
    │       │       │           │
[MegaTTS3适配器] [ESPnet适配器] [Bert-VITS2适配器]
    │               │           │
    ▼               ▼           ▼
[MegaTTS3服务]   [ESPnet服务]  [Bert-VITS2服务]
```

### 1.2 服务职责

- **API Gateway**: 统一接口、服务发现、负载均衡
- **引擎选择器**: 根据文本特征选择最合适的引擎
- **适配器层**: 适配不同引擎的接口差异
- **TTS服务**: 独立部署的语音合成引擎

## 二、适配器设计

### 2.1 基础适配器接口

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

### 2.2 MegaTTS3适配器

MegaTTS3适配器负责与MegaTTS3服务通信，处理请求和响应转换。

```python
class MegaTTS3Adapter(BaseTTSAdapter):
    def __init__(self, service_url: str):
        self.service_url = service_url
        self.client = httpx.AsyncClient(base_url=service_url, timeout=30.0)
    
    async def synthesize(self, text: str, voice_id: str, **kwargs) -> bytes:
        emotion = kwargs.get("emotion", {"type": "neutral", "intensity": 0.5})
        style = kwargs.get("style", {"speed": 1.0, "pitch": 1.0})
        
        # 转换为MegaTTS3接口参数
        params = {
            "text": text,
            "voice_id": voice_id,
            "emotion_type": emotion["type"],
            "emotion_intensity": emotion["intensity"],
            "speed_scale": style["speed"],
            "pitch_scale": style["pitch"]
        }
        
        try:
            response = await self.client.post("/synthesize", json=params)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise TTSEngineError(f"MegaTTS3合成失败: {str(e)}")
    
    async def get_available_voices(self) -> List[dict]:
        try:
            response = await self.client.get("/voices")
            response.raise_for_status()
            return response.json()["voices"]
        except Exception as e:
            raise TTSEngineError(f"获取MegaTTS3音色失败: {str(e)}")
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get("/health")
            return response.status_code == 200
        except Exception:
            return False
```

### 2.3 ESPnet适配器

ESPnet适配器负责与ESPnet服务通信，处理请求和响应转换。

```python
class ESPnetAdapter(BaseTTSAdapter):
    def __init__(self, service_url: str):
        self.service_url = service_url
        self.client = httpx.AsyncClient(base_url=service_url, timeout=60.0)
    
    async def synthesize(self, text: str, voice_id: str, **kwargs) -> bytes:
        emotion = kwargs.get("emotion", {"type": "neutral", "intensity": 0.5})
        style = kwargs.get("style", {"speed": 1.0, "pitch": 1.0})
        
        # 转换为ESPnet接口参数
        params = {
            "text": text,
            "speaker_id": voice_id,  # ESPnet使用speaker_id而非voice_id
            "emotion": emotion["type"],
            "emotion_weight": emotion["intensity"],
            "speed_factor": style["speed"],
            "pitch_factor": style["pitch"]
        }
        
        try:
            response = await self.client.post("/api/tts", json=params)
            response.raise_for_status()
            return response.content
        except Exception as e:
            raise TTSEngineError(f"ESPnet合成失败: {str(e)}")
    
    async def get_available_voices(self) -> List[dict]:
        try:
            response = await self.client.get("/api/speakers")
            response.raise_for_status()
            
            # 转换ESPnet格式到统一格式
            speakers = response.json()["speakers"]
            return [
                {
                    "id": str(speaker["id"]),
                    "name": speaker["name"],
                    "gender": speaker.get("gender", "unknown"),
                    "language": speaker.get("language", "zh-CN")
                }
                for speaker in speakers
            ]
        except Exception as e:
            raise TTSEngineError(f"获取ESPnet音色失败: {str(e)}")
    
    async def health_check(self) -> bool:
        try:
            response = await self.client.get("/api/health")
            return response.status_code == 200
        except Exception:
            return False
```

## 三、引擎选择策略

### 3.1 策略接口

```python
class EngineSelector:
    def select_engine(
        self,
        text: str,
        requirements: dict
    ) -> str:
        """
        根据文本和需求选择合适的引擎
        返回: 引擎ID
        """
        pass
```

### 3.2 简化的引擎选择策略

```python
class SimpleEngineSelector(EngineSelector):
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

### 3.3 高级引擎选择策略

```python
class AdvancedEngineSelector(EngineSelector):
    def __init__(self, tts_router):
        self.tts_router = tts_router
        self.rules = [
            # 对话文本规则
            {
                "condition": lambda text, req: '"' in text or '"' in text or '「' in text,
                "engine": "megatts3"
            },
            # 情感需求规则
            {
                "condition": lambda text, req: req.get("emotion", {}).get("intensity", 0) > 0.7,
                "engine": "megatts3"
            },
            # 正式朗读规则
            {
                "condition": lambda text, req: len(text) > 500,
                "engine": "espnet"
            }
        ]
        self.default_engine = "megatts3"
    
    def select_engine(self, text: str, requirements: dict) -> str:
        # 用户指定引擎
        if requirements.get("engine_preference") and requirements["engine_preference"] != "auto":
            return requirements["engine_preference"]
        
        # 应用规则
        for rule in self.rules:
            if rule["condition"](text, requirements):
                engine = rule["engine"]
                # 检查引擎健康状态
                if self.tts_router.is_engine_healthy(engine):
                    return engine
        
        # 检查默认引擎健康状态
        if self.tts_router.is_engine_healthy(self.default_engine):
            return self.default_engine
        
        # 所有引擎不可用时，返回第一个健康的引擎
        for engine in self.tts_router.get_healthy_engines():
            return engine
        
        raise NoHealthyEngineError("没有可用的TTS引擎")
```

## 四、引擎路由器

### 4.1 路由器设计

引擎路由器负责管理所有已注册的TTS引擎，处理引擎选择和任务分发。

```python
class TTSEngineRouter:
    def __init__(self):
        self.engines = {}
        self.health_status = {}
        self.engine_selector = AdvancedEngineSelector(self)
    
    def register_engine(self, engine_type: str, engine: BaseTTSAdapter) -> None:
        """注册TTS引擎"""
        self.engines[engine_type] = engine
        self.health_status[engine_type] = {
            "status": "unknown",
            "last_check": time.time(),
            "check_count": 0,
            "success_count": 0
        }
    
    async def synthesize(self, text: str, voice_id: str, **kwargs) -> bytes:
        """合成语音"""
        # 确定使用的引擎
        engine_preference = kwargs.pop("engine_preference", "auto")
        requirements = {
            "engine_preference": engine_preference,
            **kwargs
        }
        
        if engine_preference != "auto" and engine_preference in self.engines:
            # 用户指定了引擎
            engine_type = engine_preference
        else:
            # 自动选择引擎
            engine_type = self.engine_selector.select_engine(text, requirements)
        
        # 检查引擎可用性
        if engine_type not in self.engines:
            raise UnknownEngineError(f"未知的引擎类型: {engine_type}")
        
        # 调用引擎合成
        engine = self.engines[engine_type]
        return await engine.synthesize(text, voice_id, **kwargs)
    
    async def get_available_voices(self, engine_type: str = None) -> Dict[str, List[dict]]:
        """获取可用音色"""
        if engine_type:
            if engine_type not in self.engines:
                raise UnknownEngineError(f"未知的引擎类型: {engine_type}")
            voices = await self.engines[engine_type].get_available_voices()
            return {engine_type: voices}
        
        # 获取所有引擎的音色
        result = {}
        for engine_type, engine in self.engines.items():
            try:
                voices = await engine.get_available_voices()
                result[engine_type] = voices
            except Exception as e:
                logger.error(f"获取引擎 {engine_type} 音色失败: {str(e)}")
                result[engine_type] = []
        
        return result
    
    async def check_health(self) -> Dict[str, Dict]:
        """检查所有引擎健康状态"""
        for engine_type, engine in self.engines.items():
            try:
                is_healthy = await engine.health_check()
                self.health_status[engine_type].update({
                    "status": "healthy" if is_healthy else "unhealthy",
                    "last_check": time.time(),
                    "check_count": self.health_status[engine_type]["check_count"] + 1,
                    "success_count": self.health_status[engine_type]["success_count"] + (1 if is_healthy else 0)
                })
            except Exception as e:
                logger.error(f"检查引擎 {engine_type} 健康状态失败: {str(e)}")
                self.health_status[engine_type].update({
                    "status": "unhealthy",
                    "last_check": time.time(),
                    "check_count": self.health_status[engine_type]["check_count"] + 1
                })
        
        return self.health_status
    
    def is_engine_healthy(self, engine_type: str) -> bool:
        """检查引擎是否健康"""
        if engine_type not in self.health_status:
            return False
        return self.health_status[engine_type]["status"] == "healthy"
    
    def get_healthy_engines(self) -> List[str]:
        """获取所有健康的引擎"""
        return [
            engine_type 
            for engine_type, status in self.health_status.items() 
            if status["status"] == "healthy"
        ]
```

## 五、服务监控

### 5.1 监控组件设计

```python
class ServiceMonitor:
    def __init__(self, tts_router: TTSEngineRouter, check_interval: int = 60):
        self.tts_router = tts_router
        self.check_interval = check_interval
        self.running = False
        self.task = None
        
    async def start(self):
        """启动监控任务"""
        if self.running:
            return
        
        self.running = True
        self.task = asyncio.create_task(self._monitor_task())
        logger.info(f"服务监控已启动，检查间隔: {self.check_interval}秒")
    
    async def stop(self):
        """停止监控任务"""
        if not self.running:
            return
        
        self.running = False
        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass
            self.task = None
        
        logger.info("服务监控已停止")
    
    async def _monitor_task(self):
        """监控任务主循环"""
        while self.running:
            try:
                # 检查引擎健康状态
                health_status = await self.tts_router.check_health()
                
                # 记录健康状态
                logger.info(f"引擎健康状态: {health_status}")
                
                # 更新监控指标
                for engine_type, status in health_status.items():
                    metrics.gauge(
                        f"engine_health_{engine_type}",
                        1 if status["status"] == "healthy" else 0
                    )
                    metrics.gauge(
                        f"engine_availability_{engine_type}",
                        status["success_count"] / status["check_count"] if status["check_count"] > 0 else 0
                    )
            except Exception as e:
                logger.error(f"服务监控任务出错: {str(e)}")
            
            # 等待下一次检查
            await asyncio.sleep(self.check_interval)
```

## 六、整合流程

### 6.1 整合流程图

```
初始化API网关
    │
    ▼
创建引擎适配器
    │
    ▼
注册引擎到路由器
    │
    ▼
启动服务监控
    │
    ▼
API服务准备就绪
```

### 6.2 初始化代码

```python
# 创建引擎路由器
tts_router = TTSEngineRouter()

# 创建引擎适配器
megatts3_adapter = MegaTTS3Adapter(os.getenv("MEGATTS3_URL", "http://megatts3:9931"))
espnet_adapter = ESPnetAdapter(os.getenv("ESPNET_URL", "http://espnet:9932"))

# 注册引擎
tts_router.register_engine("megatts3", megatts3_adapter)
tts_router.register_engine("espnet", espnet_adapter)

# 创建服务监控
service_monitor = ServiceMonitor(tts_router, check_interval=60)

# 启动监控
@app.on_event("startup")
async def startup_event():
    await service_monitor.start()

# 停止监控
@app.on_event("shutdown")
async def shutdown_event():
    await service_monitor.stop()
```

## 七、Docker配置

### 7.1 网络配置

```bash
# 创建共享网络
docker network create ai-sound-network
```

### 7.2 服务配置

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

## 八、未来规划

### 8.1 Bert-VITS2整合

规划在后续阶段整合Bert-VITS2引擎，实现步骤如下：

1. **Docker化Bert-VITS2**
   - 编写Dockerfile
   - 配置模型下载和加载
   - 添加健康检查接口

2. **实现Bert-VITS2适配器**
   - 创建BertVITS2Adapter类
   - 实现接口方法
   - 参数映射和转换

3. **扩展引擎选择策略**
   - 添加Bert-VITS2相关规则
   - 优化选择算法

4. **更新Web管理界面**
   - 添加Bert-VITS2引擎配置
   - 更新音色管理支持

### 8.2 商业引擎整合

计划整合商业TTS引擎作为备选方案：

1. **设计商业引擎适配器**
   - 创建通用商业引擎适配器接口
   - 实现各商业引擎的具体适配器
   - 计费和配额管理

2. **引擎优先级与故障转移**
   - 实现引擎优先级配置
   - 添加故障转移机制
   - 智能路由策略

3. **成本优化策略**
   - 实现基于成本的引擎选择
   - 缓存优化减少API调用
   - 用量统计和成本控制