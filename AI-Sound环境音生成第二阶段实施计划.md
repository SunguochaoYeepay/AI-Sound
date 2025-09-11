# AI-Sound环境音生成第二阶段实施计划

## 1. 第二阶段目标

**核心任务**：修改 `TangoFluxEnvironmentGenerator` 适配器，支持从音频制作卡数据生成环境音

**具体目标**：
- 支持两种数据格式：环境音分析结果 + 音频制作卡
- 自动格式检测和数据转换
- AI生成英文提示词
- 音量到强度级别推导

## 2. 修改范围分析

### 2.1 核心文件
- **主要修改**：`platform/backend/app/services/tangoflux_environment_generator.py`
- **相关文件**：`platform/backend/app/api/v1/environment_generation/generation.py`

### 2.2 具体修改点

#### 2.2.1 新增方法
1. `_convert_track_to_generation_request()` - 数据格式转换
2. `_generate_english_prompt()` - AI英文提示词生成  
3. `_volume_to_intensity()` - 音量到强度推导
4. `_detect_track_format()` - 格式检测

#### 2.2.2 修改现有方法
1. `generate_project_environment_sounds()` - 主生成逻辑
2. `_process_tracks()` - 轨道处理逻辑

#### 2.2.3 删除/替换的原有逻辑

**需要删除的硬编码逻辑**（第722-740行）：
```python
# 删除这段硬编码的数据提取逻辑
for index, track in tracks_to_generate:
    # 从轨道数据中提取生成参数
    keyword = track.get('environment_keywords', [''])[0] if track.get('environment_keywords') else ''
    if not keyword and track.get('scene_description'):
        keyword = track.get('scene_description')
    
    # 提取英文提示词
    english_prompt = track.get('english_prompt', '')
    
    generation_request = {
        'keyword': keyword,
        'description': track.get('scene_description', ''),
        'duration': track.get('duration', 30.0),
        'intensity': track.get('intensity_level', 'medium'),
        'english_prompt': english_prompt  # 添加英文提示词
    }
    generation_requests.append(generation_request)
```

**替换为**：
```python
# 使用新的数据转换方法
for index, track in tracks_to_generate:
    generation_request = await self._convert_track_to_generation_request(track, scene_context)
    generation_requests.append(generation_request)
```

## 3. 详细实施步骤

### 3.1 步骤1：添加格式检测方法

```python
def _detect_track_format(self, track: Dict[str, Any]) -> str:
    """检测轨道数据格式类型"""
    if 'environment_keywords' in track:
        return 'environment_analysis'  # 环境音分析结果格式
    elif 'type' in track and track.get('type') == '环境音效':
        return 'audio_storyboard'      # 音频制作卡格式
    else:
        return 'unknown'               # 未知格式
```

### 3.2 步骤2：添加数据转换方法

```python
def _convert_track_to_generation_request(self, track: Dict[str, Any], scene_context: Dict[str, Any] = None) -> Dict[str, Any]:
    """转换轨道数据为生成请求 - 支持两种格式"""
    
    format_type = self._detect_track_format(track)
    
    if format_type == 'environment_analysis':
        # 环境音分析结果格式
        keyword = track.get('environment_keywords', [''])[0] if track.get('environment_keywords') else ''
        description = track.get('chinese_description', '')
        english_prompt = track.get('english_prompt', '')
        duration = track.get('duration', 30.0)
        intensity = track.get('intensity_level', 'medium')
        
    elif format_type == 'audio_storyboard':
        # 音频制作卡格式
        keyword = track.get('description', '')
        description = track.get('description', '')
        english_prompt = await self._generate_english_prompt(keyword, scene_context)
        duration = track.get('end_time', 30) - track.get('start_time', 0)
        intensity = self._volume_to_intensity(track.get('volume', 40))
        
    else:
        # 默认处理
        keyword = track.get('description', '')
        description = track.get('description', '')
        english_prompt = await self._generate_english_prompt(keyword)
        duration = track.get('duration', 30.0)
        intensity = 'medium'
    
    return {
        'keyword': keyword,
        'description': description,
        'duration': duration,
        'intensity': intensity,
        'english_prompt': english_prompt
    }
```

### 3.3 步骤3：添加AI英文提示词生成

```python
async def _generate_english_prompt(self, chinese_description: str, scene_context: Dict[str, Any] = None) -> str:
    """使用AI生成英文提示词 - 带场景上下文"""
    try:
        if scene_context:
            location = scene_context.get('location', '')
            time = scene_context.get('time', '')
            atmosphere = scene_context.get('atmosphere', '')
            
            prompt = f"""
            将以下中文环境音描述翻译为英文提示词，用于AI音频生成：
            
            环境音：{chinese_description}
            场景：{location}
            时间：{time}
            氛围：{atmosphere}
            
            请生成详细的英文提示词，包含场景、时间、氛围等上下文信息。
            """
        else:
            prompt = f"将以下中文环境音描述翻译为英文提示词，用于AI音频生成：{chinese_description}"
        
        # 调用LLM API（使用现有的LLM客户端）
        response = await self.llm_client.generate(prompt)
        
        # 提取生成的英文提示词
        english_prompt = response.strip()
        
        logger.info(f"[TANGOFLUX_GEN] 生成英文提示词: {chinese_description} -> {english_prompt}")
        return english_prompt
        
    except Exception as e:
        logger.error(f"[TANGOFLUX_GEN] 生成英文提示词失败: {e}")
        # 返回默认英文提示词
        return f"Ambient sound: {chinese_description}"
```

### 3.4 步骤4：添加音量到强度推导

```python
def _volume_to_intensity(self, volume: int) -> str:
    """从音量推导强度级别"""
    if volume <= 30:
        return 'low'
    elif volume <= 50:
        return 'medium'
    else:
        return 'high'
```

### 3.5 步骤5：修改主生成逻辑

**需要修改的方法签名**：
```python
# 原方法签名
async def generate_project_environment_sounds(self, project_id: int, tracks_to_generate: List[Tuple[int, Dict[str, Any]]], task_id: str = None, chapter_id: int = None) -> Dict[str, Any]:

# 新方法签名（添加scene_context参数）
async def generate_project_environment_sounds(self, project_id: int, tracks_to_generate: List[Tuple[int, Dict[str, Any]]], task_id: str = None, chapter_id: int = None, scene_context: Dict[str, Any] = None) -> Dict[str, Any]:
```

**需要替换的核心逻辑**（第722-740行）：
```python
# 删除原有的硬编码数据提取逻辑
# 转换轨道数据为生成请求
generation_requests = []
for index, track in tracks_to_generate:
    # 从轨道数据中提取生成参数
    keyword = track.get('environment_keywords', [''])[0] if track.get('environment_keywords') else ''
    if not keyword and track.get('scene_description'):
        keyword = track.get('scene_description')
    
    # 提取英文提示词
    english_prompt = track.get('english_prompt', '')
    
    generation_request = {
        'keyword': keyword,
        'description': track.get('scene_description', ''),
        'duration': track.get('duration', 30.0),
        'intensity': track.get('intensity_level', 'medium'),
        'english_prompt': english_prompt  # 添加英文提示词
    }
    generation_requests.append(generation_request)

# 替换为新的数据转换逻辑
generation_requests = []
for index, track in tracks_to_generate:
    try:
        request = await self._convert_track_to_generation_request(track, scene_context)
        generation_requests.append(request)
        logger.info(f"[TANGOFLUX_GEN] 转换轨道数据: {track.get('description', 'unknown')} -> {request['keyword']}")
    except Exception as e:
        logger.error(f"[TANGOFLUX_GEN] 转换轨道数据失败: {e}")
        continue
```

## 4. 测试计划

### 4.1 单元测试

#### 4.1.1 格式检测测试
```python
def test_detect_track_format():
    """测试格式检测功能"""
    
    # 环境音分析结果格式
    env_track = {
        'environment_keywords': ['马蹄声'],
        'chinese_description': '古代街道的马蹄声',
        'english_prompt': 'Horse hooves on ancient street'
    }
    assert generator._detect_track_format(env_track) == 'environment_analysis'
    
    # 音频制作卡格式
    storyboard_track = {
        'type': '环境音效',
        'description': '马蹄声',
        'start_time': 0,
        'end_time': 30,
        'volume': 40
    }
    assert generator._detect_track_format(storyboard_track) == 'audio_storyboard'
```

#### 4.1.2 数据转换测试
```python
async def test_convert_track_to_generation_request():
    """测试数据转换功能"""
    
    # 测试音频制作卡格式转换
    track = {
        'type': '环境音效',
        'description': '马蹄声',
        'start_time': 0,
        'end_time': 30,
        'volume': 40
    }
    
    scene_context = {
        'location': '古代街道',
        'time': '夜晚时分',
        'atmosphere': '宁静祥和'
    }
    
    result = await generator._convert_track_to_generation_request(track, scene_context)
    
    assert result['keyword'] == '马蹄声'
    assert result['description'] == '马蹄声'
    assert result['duration'] == 30.0
    assert result['intensity'] == 'medium'
    assert 'Horse' in result['english_prompt']  # AI生成的英文提示词
```

#### 4.1.3 音量推导测试
```python
def test_volume_to_intensity():
    """测试音量到强度推导"""
    
    assert generator._volume_to_intensity(20) == 'low'
    assert generator._volume_to_intensity(40) == 'medium'
    assert generator._volume_to_intensity(60) == 'high'
```

### 4.2 集成测试

#### 4.2.1 完整流程测试
```python
async def test_complete_generation_flow():
    """测试完整的环境音生成流程"""
    
    # 模拟音频制作卡数据
    tracks = [
        {
            'type': '环境音效',
            'description': '马蹄声',
            'start_time': 0,
            'end_time': 30,
            'volume': 40
        },
        {
            'type': '环境音效', 
            'description': '风声',
            'start_time': 0,
            'end_time': 25,
            'volume': 30
        }
    ]
    
    scene_context = {
        'location': '古代街道',
        'time': '夜晚时分',
        'atmosphere': '宁静祥和'
    }
    
    # 调用生成方法
    result = await generator.generate_project_environment_sounds(1, tracks, scene_context)
    
    # 验证结果
    assert result['success'] == True
    assert len(result['tracks']) == 2
```

## 5. 错误处理策略

### 5.1 格式检测失败
```python
# 在 _convert_track_to_generation_request 中
if format_type == 'unknown':
    logger.warning(f"[TANGOFLUX_GEN] 未知轨道格式，使用默认处理: {track}")
    # 使用默认处理逻辑
```

### 5.2 AI生成失败
```python
# 在 _generate_english_prompt 中
except Exception as e:
    logger.error(f"[TANGOFLUX_GEN] 生成英文提示词失败: {e}")
    return f"Ambient sound: {chinese_description}"  # 返回默认值
```

### 5.3 数据转换失败
```python
# 在主生成逻辑中
for track in tracks_to_generate:
    try:
        request = await self._convert_track_to_generation_request(track, scene_context)
        generation_requests.append(request)
    except Exception as e:
        logger.error(f"[TANGOFLUX_GEN] 转换轨道数据失败: {e}")
        continue  # 跳过失败的轨道，继续处理其他轨道
```

## 6. 性能优化

### 6.1 异步处理
- 所有AI生成操作使用异步处理
- 避免阻塞主线程

### 6.2 缓存机制
```python
# 可以考虑添加英文提示词缓存
_english_prompt_cache = {}

async def _generate_english_prompt(self, chinese_description: str, scene_context: Dict[str, Any] = None) -> str:
    """带缓存的英文提示词生成"""
    cache_key = f"{chinese_description}_{hash(str(scene_context))}"
    
    if cache_key in self._english_prompt_cache:
        return self._english_prompt_cache[cache_key]
    
    # 生成新的提示词
    english_prompt = await self._generate_english_prompt_impl(chinese_description, scene_context)
    self._english_prompt_cache[cache_key] = english_prompt
    
    return english_prompt
```

## 7. 日志记录

### 7.1 关键操作日志
```python
logger.info(f"[TANGOFLUX_GEN] 开始生成项目环境音，项目ID: {project_id}")
logger.info(f"[TANGOFLUX_GEN] 检测到轨道格式: {format_type}")
logger.info(f"[TANGOFLUX_GEN] 转换轨道数据: {track.get('description', 'unknown')} -> {request['keyword']}")
logger.info(f"[TANGOFLUX_GEN] 生成英文提示词: {chinese_description} -> {english_prompt}")
logger.info(f"[TANGOFLUX_GEN] 项目环境音生成完成，项目ID: {project_id}")
```

### 7.2 错误日志
```python
logger.error(f"[TANGOFLUX_GEN] 生成英文提示词失败: {e}")
logger.error(f"[TANGOFLUX_GEN] 转换轨道数据失败: {e}")
logger.error(f"[TANGOFLUX_GEN] 生成项目环境音失败: {e}")
```

## 8. 部署检查清单

### 8.1 代码检查
- [ ] 所有新增方法都有完整的类型提示
- [ ] 所有异常都有适当的错误处理
- [ ] 所有关键操作都有日志记录
- [ ] 单元测试覆盖率达到80%以上
- [ ] **删除了原有的硬编码逻辑**（第722-740行）
- [ ] **修改了方法签名**，添加了scene_context参数

### 8.2 功能检查
- [ ] 格式检测功能正常
- [ ] 数据转换功能正常
- [ ] AI英文提示词生成功能正常
- [ ] 音量到强度推导功能正常
- [ ] 完整流程测试通过
- [ ] **向后兼容性**：原有环境音分析结果格式仍然正常工作
- [ ] **新格式支持**：音频制作卡格式正常工作

### 8.3 性能检查
- [ ] 异步处理不影响响应速度
- [ ] 内存使用合理
- [ ] 无内存泄漏
- [ ] **AI生成不阻塞**：英文提示词生成使用异步处理

## 9. 回滚计划

### 9.1 代码回滚
- **保留原始方法作为备份**：在修改前备份原有的数据提取逻辑
- **使用特性开关控制新旧逻辑**：可以通过配置选择使用新逻辑还是旧逻辑
- **具体回滚步骤**：
  1. 恢复第722-740行的原有硬编码逻辑
  2. 移除新增的4个方法
  3. 恢复原方法签名（移除scene_context参数）

### 9.2 数据回滚
- **保持向后兼容性**：新逻辑完全兼容原有环境音分析结果格式
- **支持旧格式数据**：原有API调用方式无需修改
- **渐进式部署**：可以先部署到测试环境，验证无误后再部署到生产环境

## 10. 后续优化计划

### 10.1 第三阶段：前端集成
- 修改前端调用逻辑
- 传入音频制作卡数据
- 测试完整用户流程

### 10.2 第四阶段：性能优化
- 添加缓存机制
- 优化AI生成速度
- 增强错误处理

---

**文档创建时间**：2025年1月27日  
**基于文件**：`platform/backend/app/services/tangoflux_environment_generator.py`  
**实施优先级**：高  
**预计工期**：2-3天
