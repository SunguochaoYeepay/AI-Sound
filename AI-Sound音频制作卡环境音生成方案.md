# AI-Sound音频制作卡环境音生成方案

## 1. 问题背景

用户询问：**我们识别的环境音可以用于环境音生成吗？**

经过深入分析，发现：
- ❌ **环境音分析结果**：LLM联想错误，准确性低
- ✅ **音频制作卡**：基于6卡分析，准确性高，可人工校对

**推荐方案：音频制作卡环境音生成**

## 2. 现状分析

### 2.1 环境音分析结果的问题

#### **LLM联想错误严重**：
```
错误场景 → 错误识别 → 正确做法
"御书房内" → "翻书声"、"写字声" ❌ → 不识别任何声音 ✅
"把玩钢笔" → "写字声" ❌ → 不识别任何声音 ✅  
"汗水浸湿" → "水声" ❌ → 不识别任何声音 ✅
"裙摆扫过" → "翻书声" ❌ → 不识别任何声音 ✅
```

#### **测试结果对比**：
- **第一章**：相对准确 ✅
- **第三章**：错误较多 ❌
  ```
  🎵 轨道 1: 翻书声、水声、写字声 ❌
  🎵 轨道 3: 翻书声 ❌  
  🎵 轨道 4: 翻书声、水声、写字声 ❌
  ```

### 2.2 音频制作卡的优势

#### **数据来源更可靠**：
- **环境音分析**：直接LLM分析旁白 → 容易联想错误
- **音频制作卡**：基于6卡分析 → 经过多轮验证

#### **数据结构完整**：
```json
{
  "sound_effects": [
    {
      "effect_id": "env_effect_001",
      "type": "环境音效",
      "description": "马蹄声",
      "start_time": 0,
      "end_time": 30,
      "volume": 40,
      "spatial": "环绕",
      "effects": ["空间化", "混响"]
    }
  ]
}
```

### 2.3 环境音生成服务输入格式

**TangoFluxEnvironmentGenerator 期望格式**：
```python
generation_request = {
    'keyword': keyword,           # 环境音关键词
    'description': description,   # 场景描述
    'duration': duration,        # 音频时长
    'intensity': intensity,       # 强度级别
    'english_prompt': english_prompt  # 英文提示词
}
```

### 2.4 数据匹配分析

| 字段 | 音频制作卡输出 | 环境音生成输入 | 匹配度 |
|------|---------------|---------------|--------|
| keyword | ✅ description | ✅ 需要 | ✅ 完全匹配 |
| description | ✅ description | ✅ 需要 | ✅ 完全匹配 |
| duration | ✅ end_time - start_time | ✅ 需要 | ✅ 完全匹配 |
| intensity | ❌ 缺失 | ✅ 需要 | ❌ 需要推导 |
| english_prompt | ❌ 缺失 | ✅ 需要 | ❌ 需要AI生成 |

## 3. 实施方案

### 3.1 整体架构

```
6卡分析 → scene_card.environment_sounds → AudioStoryboardCard.sound_effects → 修改现有适配器 → 环境音生成服务 → 音频文件输出
```

### 3.2 数据流转分析

#### 3.2.1 数据来源链条

1. **6卡分析** (`SixCardAnalyzer`) → 生成 `scene_card.environment_sounds`
2. **音频制作卡生成** (`AudioStoryboardGenerator._generate_sound_effects()`) → 从 `scene_card.environment_sounds` 提取生成 `sound_effects`
3. **环境音生成** (`TangoFluxEnvironmentGenerator`) → 需要适配 `sound_effects` 格式

#### 3.2.2 关键代码位置

**场景卡生成**：
```python
# platform/backend/app/services/six_card_analyzer.py
# 在 _build_analysis_prompt() 中定义 scene_card 结构
"scene_card": {
    "location": "具体地点",
    "time": "时间描述", 
    "atmosphere": "整体氛围",
    "environment_sounds": [
        {
            "keyword": "环境音效关键词",
            "description": "该环境音效的详细描述，包含场景上下文信息"
        }
    ],  # ← 这里是数据源，对象数组结构
    "visual_elements": ["视觉元素1", "视觉元素2"],
    "sensory_details": ["触觉/嗅觉等其他感官细节"]
}
```

**音频制作卡生成**：
```python
# platform/backend/app/services/audio_storyboard_generator.py
# 在 _generate_sound_effects() 中从 scene_card 提取环境音效
def _generate_sound_effects(self, scene_card: Dict[str, Any], event_card: Dict[str, Any], total_duration: float = 0):
    sound_effects = []
    
    # 从场景卡提取环境音效
    environment_sounds = scene_card.get("environment_sounds", [])  # ← 从这里提取对象数组
    for i, sound_obj in enumerate(environment_sounds):
        sound_effects.append({
            "effect_id": f"env_effect_{i+1:03d}",
            "type": "环境音效",
            "description": sound_obj.get("keyword", ""),  # ← 使用keyword字段
            "start_time": 0,
            "end_time": total_duration if total_duration > 0 else 30,
            "volume": 40,
            "spatial": "环绕",
            "effects": ["空间化", "混响"]
        })
    
    return sound_effects
```

### 3.3 核心组件

#### 3.3.1 修改现有适配器

**不需要新建适配器！** 只需要修改 `TangoFluxEnvironmentGenerator` 的现有适配逻辑。

**现有适配逻辑**：
```python
# 在 generate_project_environment_sounds() 中
generation_request = {
    'keyword': keyword,
    'description': track.get('scene_description', ''),
    'duration': track.get('duration', 30.0),
    'intensity': track.get('intensity_level', 'medium'),
    'english_prompt': english_prompt
}
```

**修改后的适配逻辑**：
```python
def _convert_track_to_generation_request(self, track):
    """转换轨道数据为生成请求 - 支持两种格式"""
    
    # 检查数据格式类型
    if 'environment_keywords' in track:
        # 环境音分析结果格式
        keyword = track.get('environment_keywords', [''])[0] if track.get('environment_keywords') else ''
        description = track.get('chinese_description', '')
        english_prompt = track.get('english_prompt', '')
        duration = track.get('duration', 30.0)
        intensity = track.get('intensity_level', 'medium')
    elif 'type' in track and track.get('type') == '环境音效':
        # 音频制作卡格式
        keyword = track.get('description', '')
        description = track.get('description', '')
        english_prompt = await self._generate_english_prompt(keyword, scene_context)  # AI生成，带场景上下文
        duration = track.get('end_time', 30) - track.get('start_time', 0)
        intensity = self._volume_to_intensity(track.get('volume', 40))  # 从volume推导
    else:
        # 默认处理
        keyword = track.get('description', '')
        description = track.get('description', '')
        english_prompt = await self._generate_english_prompt(keyword)  # AI生成
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

#### 3.2.2 添加AI英文提示词生成

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

#### 3.2.3 添加音量到强度推导

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

### 3.3 适配流程

#### 3.3.1 数据转换流程

```
1. 输入：AudioStoryboardCard.sound_effects 或 environment_tracks
2. 格式检测：判断数据来源类型
3. 字段提取：根据格式提取对应字段
4. 缺失补全：
   - intensity：从volume推导
   - english_prompt：AI生成
5. 输出：标准化的生成请求列表
```

#### 3.3.2 错误处理机制
- **格式检测失败**：使用默认处理逻辑
- **AI生成失败**：使用默认英文提示词
- **数据缺失**：提供合理默认值
- **异常捕获**：记录错误日志

## 4. 集成方案

### 4.1 API设计

**不需要新增API！** 现有的环境音生成API已经支持：

```
POST /api/v1/environment-generation/generate/{project_id}
```

**只需要前端传入音频制作卡数据即可！**

### 4.2 数据流设计

```
1. 前端调用6卡分析API
2. 获取AudioStoryboardCard数据
3. 提取sound_effects中的环境音效
4. 调用现有环境音生成API，传入sound_effects数据
5. 修改后的适配器自动识别格式并转换
6. 调用TangoFlux生成器
7. 返回生成任务状态
8. 前端轮询任务状态
9. 生成完成后获取音频文件
```

## 5. 实施步骤

### 5.1 第一阶段：修改6卡分析结构 ✅ **已完成**
1. ✅ 修改 `environment_sounds` 为对象数组结构，包含keyword和description字段
2. ✅ 修改 `background_music` 为对象数组结构，包含keyword和description字段
3. ✅ 删除重复的 `sound_effects` 字段，避免与环境音效重复
4. ✅ 删除冗余的 `scene_description` 字段，简化数据结构
5. ✅ 更新所有fallback数据结构，确保一致性
6. ✅ 更新分析提示词要求，增加结构化说明

### 5.2 第二阶段：修改现有适配器
1. 修改 `TangoFluxEnvironmentGenerator._convert_track_to_generation_request()`
2. 添加格式检测逻辑
3. 添加AI英文提示词生成
4. 添加音量到强度推导
5. 编写单元测试

### 5.3 第三阶段：前端集成
1. 修改前端调用逻辑，传入音频制作卡数据
2. 测试完整流程
3. 优化用户体验

### 5.4 第四阶段：优化完善
1. 性能优化
2. 错误处理完善
3. 日志记录增强

## 6. 重要说明：环境音识别准确性优化

### 6.1 如果要提升环境音识别准确性

**关键修改位置**：`platform/backend/app/services/six_card_analyzer.py`

**修改内容**：优化 `_build_analysis_prompt()` 中的场景分析提示词

**当前问题**：
- LLM在 `scene_card.environment_sounds` 中容易产生联想错误
- 如"御书房内" → "翻书声"、"写字声" ❌

**优化方案**：
```python
# 在 _build_analysis_prompt() 中强化环境音识别规则
【场景分析特别要求】
1. 【时代背景识别】：必须准确识别场景的时代背景（古代/现代/未来/架空等）
2. 【环境音效匹配】：environment_sounds必须与时代背景完全匹配
   - 古代场景：使用"马蹄声"、"叫卖声"、"钟声"、"风声"等古代音效
   - 现代场景：使用"车流声"、"交通声"、"建筑声"等现代音效
   - 严禁混用：古代场景不能出现现代音效，现代场景不能出现古代音效
3. 【场景一致性】：location、time、atmosphere、environment_sounds必须保持时代一致性
4. 【音效具体性】：环境音效要具体明确，避免模糊描述
5. 【【重要】】只识别明确描述的环境音，不要联想：
   - ✅ "远处传来马蹄声" → ["马蹄声"]
   - ❌ "御书房内" → 不要联想为["翻书声"、"写字声"]
   - ❌ "把玩钢笔" → 不要联想为["写字声"]
   - ❌ "汗水浸湿" → 不要联想为["水声"]
```

### 6.2 数据质量提升策略

1. **强化提示词**：在6卡分析中增加环境音识别准确性要求
2. **人工校对**：提供界面让用户修正错误的环境音识别
3. **规则引擎**：添加后处理规则，过滤明显错误的环境音
4. **反馈机制**：记录用户修正，用于优化LLM提示词

## 7. 技术优势

### 7.1 实施成本低
- **无需新建适配器**：修改现有代码即可
- **无需新增API**：复用现有接口
- **无需修改数据库**：使用现有数据结构

### 7.2 准确性提升
- 基于6卡分析，避免LLM联想错误
- 可人工校对，确保数据质量
- 结构化数据，减少解析错误

### 7.3 数据完整性
- 包含时间轴信息（start_time, end_time）
- 包含音量控制（volume）
- 包含空间化信息（spatial）
- 包含音效处理（effects）

### 7.4 可扩展性
- 支持新的环境音类型
- 可配置推导规则
- 易于维护和升级

## 8. 预期效果

### 8.1 用户体验提升
- 一键从音频制作卡生成环境音
- 减少手动配置工作
- 提高工作效率

### 8.2 系统集成度提升
- 音频制作卡与环境音生成完美配合
- 数据流转顺畅
- 减少重复工作

### 8.3 维护成本降低
- 统一的数据格式
- 标准化的处理流程
- 清晰的错误处理

## 9. 风险评估

### 9.1 技术风险
- **AI生成失败**：英文提示词生成可能失败
- **格式检测错误**：可能误判数据格式
- **性能影响**：AI生成可能影响响应速度

### 9.2 缓解措施
- 提供默认英文提示词
- 增强格式检测逻辑
- 异步处理AI生成

## 10. 总结

通过修改现有的 `TangoFluxEnvironmentGenerator` 适配器，可以实现音频制作卡与环境音生成服务的无缝对接。该方案具有以下特点：

1. **实施成本低**：无需新建组件，修改现有代码即可
2. **准确性高**：基于6卡分析，避免LLM联想错误
3. **数据完整**：包含时间轴、音量、空间化等完整信息
4. **易于实施**：基于现有架构，改动最小

该方案能够显著提升AI-Sound系统的整体集成度和用户体验，是一个实用且高效的解决方案。

---

## 附录：具体实现示例

### A.1 数据转换示例

**输入数据（音频制作卡）**：
```json
{
  "sound_effects": [
    {
      "effect_id": "env_effect_001",
      "type": "环境音效",
      "description": "马蹄声",
      "start_time": 0,
      "end_time": 30,
      "volume": 40,
      "spatial": "环绕",
      "effects": ["空间化", "混响"]
    }
  ]
}
```

**场景上下文数据**：
```json
{
  "location": "古代街道",
  "time": "夜晚时分",
  "atmosphere": "宁静祥和"
}
```

**输出数据（生成请求列表）**：
```json
[
  {
    "keyword": "马蹄声",
    "description": "马蹄声",
    "duration": 30.0,
    "intensity": "medium",
    "english_prompt": "Horse hooves on ancient cobblestone street at night, creating a peaceful and serene atmosphere"
  }
]
```

### A.2 修改后的适配器代码

```python
class TangoFluxEnvironmentGenerator:
    def _convert_track_to_generation_request(self, track):
        """转换轨道数据为生成请求 - 支持两种格式"""
        
        # 检查数据格式类型
        if 'environment_keywords' in track:
            # 环境音分析结果格式
            keyword = track.get('environment_keywords', [''])[0] if track.get('environment_keywords') else ''
            description = track.get('chinese_description', '')
            english_prompt = track.get('english_prompt', '')
            duration = track.get('duration', 30.0)
            intensity = track.get('intensity_level', 'medium')
        elif 'type' in track and track.get('type') == '环境音效':
            # 音频制作卡格式
            keyword = track.get('description', '')
            description = track.get('description', '')
            english_prompt = await self._generate_english_prompt(keyword)
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
    
    async def _generate_english_prompt(self, chinese_description: str) -> str:
        """使用AI生成英文提示词"""
        try:
            prompt = f"将以下中文环境音描述翻译为英文提示词，用于AI音频生成：{chinese_description}"
            response = await self.llm_client.generate(prompt)
            return response.strip()
        except Exception as e:
            logger.error(f"生成英文提示词失败: {e}")
            return f"Ambient sound: {chinese_description}"
    
    def _volume_to_intensity(self, volume: int) -> str:
        """从音量推导强度级别"""
        if volume <= 30:
            return 'low'
        elif volume <= 50:
            return 'medium'
        else:
            return 'high'
```

---

*文档生成时间：2025年1月27日*  
*基于代码分析：platform/backend/app/services/tangoflux_environment_generator.py*
