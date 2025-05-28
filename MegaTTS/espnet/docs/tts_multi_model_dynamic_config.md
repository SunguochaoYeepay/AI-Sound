# ESPnet TTS 多模型参数动态适配设计文档

## 1. 设计目标
- 支持任意数量的 TTS 语音合成模型，每个模型参数可自定义。
- 前端页面根据所选模型动态渲染参数输入项。
- 后端接口灵活接收并分发不同模型参数。
- 参数配置集中管理，便于维护和扩展。

## 2. 参数配置结构
建议在后端集中维护模型参数配置，例如：

```python
MODEL_CONFIG = {
    "tts_train_raw_phn_pypinyin_g2p_phone": {
        "display_name": "普通话基础模型",
        "params": [
            {"name": "speed", "type": "float", "default": 1.0, "min": 0.5, "max": 2.0, "label": "语速"},
            {"name": "pitch", "type": "float", "default": 0.0, "min": -12, "max": 12, "label": "音调"},
            {"name": "volume", "type": "float", "default": 1.0, "min": 0.0, "max": 2.0, "label": "音量"}
        ]
    },
    "tts_train_raw_zh_emotion": {
        "display_name": "情感模型",
        "params": [
            {"name": "emotion", "type": "select", "options": ["happy", "sad", "angry"], "default": "happy", "label": "情感"},
            {"name": "speed", "type": "float", "default": 1.0, "min": 0.5, "max": 2.0, "label": "语速"}
        ]
    }
    # ...更多模型
}
```

## 3. 后端接口设计

### 3.1 获取所有模型及参数配置
```typescript
// GET /api/models
app.get('/api/models', (req, res) => {
    res.json(MODEL_CONFIG);
});
```

### 3.2 合成接口
```typescript
// POST /api/tts
app.post('/api/tts', async (req, res) => {
    const { model, text, ...params } = req.body;
    // 校验参数
    // 根据 model 选择推理逻辑，并传递 params
    // 返回音频/结果
});
```

## 4. 前端页面设计（Vue3 + Ant Design Vue）

### 4.1 页面结构
- 模型选择下拉框，选择后自动加载该模型的参数输入项
- 动态参数表单，根据模型配置渲染不同的输入控件（滑块、下拉、输入框等）
- 文本输入框、提交按钮、音频播放区

### 4.2 伪代码（核心逻辑）
```vue
<template>
  <a-form>
    <a-select v-model="selectedModel" @change="onModelChange">
      <a-select-option v-for="(cfg, key) in modelConfig" :key="key" :value="key">
        {{ cfg.display_name }}
      </a-select-option>
    </a-select>
    <div v-for="param in currentParams" :key="param.name">
      <component
        :is="getComponentType(param)"
        v-model="form[param.name]"
        v-bind="getComponentProps(param)"
      />
    </div>
    <a-input v-model="form.text" placeholder="请输入文本" />
    <a-button @click="submit">合成</a-button>
  </a-form>
</template>
```
- `getComponentType(param)` 根据参数类型返回合适的表单控件（如 slider、select、input）
- `getComponentProps(param)` 返回控件的属性（如 min/max/options）

## 5. 交互流程
1. 前端启动时请求 `/api/models`，获取所有模型及参数配置。
2. 用户选择模型，页面动态渲染该模型支持的参数输入项。
3. 用户填写文本和参数，点击“合成”。
4. 前端将 `model`、`text`、`params` 一起 POST 到 `/api/tts`。
5. 后端根据模型和参数调用对应推理逻辑，返回音频结果。

## 6. 扩展性
- 新增模型只需在 `MODEL_CONFIG` 里加一项，前后端自动适配，无需改动页面和接口。
- 参数类型支持 float、int、select、bool 等，易于扩展。

---
如需详细代码实现，可随时补充！