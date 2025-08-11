# AI-Sound 项目开发规则

## 项目概述

AI-Sound 是一个基于AI的智能音频生成平台，集成了语音合成、音频编辑、环境音混合、背景音乐生成等功能。本文档定义了项目的开发规则和最佳实践。

## 技术架构规范

### 后端技术栈
- **框架**: FastAPI (异步高性能)
- **数据库**: PostgreSQL (主数据库) + Redis (缓存)
- **AI服务**: MegaTTS3, TangoFlux, Ollama
- **容器化**: Docker + Docker Compose
- **Python版本**: 3.9+

### 前端技术栈
- **框架**: Vue 3 + Composition API
- **状态管理**: Pinia
- **UI组件**: Ant Design Vue
- **构建工具**: Vite
- **音频处理**: WaveSurfer.js
- **图形编辑**: Fabric.js
- **实时通信**: WebSocket

## 开发环境规范

### 目录结构
```
AI-Sound/
├── platform/
│   ├── backend/          # 后端服务
│   └── frontend/         # 前端应用
├── docker/               # Docker配置
├── scripts/              # 开发脚本
├── data/                 # 数据存储
├── docs/                 # 项目文档
└── storage/              # 文件存储
```

### 开发流程
1. **环境启动**: 使用 `scripts/dev-start.bat` 启动开发环境
2. **代码同步**: 使用 `scripts/check-code.bat` 检查代码同步状态
3. **强制重建**: 使用 `scripts/force-rebuild.bat` 解决缓存问题
4. **服务监控**: 通过健康检查端点监控服务状态

## 代码规范

### Python后端规范

#### 文件组织
- **路由模块**: `app/api/` 目录下按功能模块组织
- **服务层**: `app/services/` 目录下实现业务逻辑
- **数据模型**: `app/models/` 目录下定义数据结构
- **工具函数**: `app/utils/` 目录下放置通用工具

#### 编码规范
```python
# 1. 使用类型注解
from typing import List, Optional

async def get_books(user_id: int, limit: Optional[int] = 10) -> List[Book]:
    """获取用户书籍列表"""
    pass

# 2. 异步函数优先
async def process_audio(file_path: str) -> dict:
    """异步处理音频文件"""
    async with aiofiles.open(file_path, 'rb') as f:
        content = await f.read()
    return await ai_service.process(content)

# 3. 错误处理
try:
    result = await some_operation()
except SpecificException as e:
    logger.error(f"操作失败: {e}")
    raise HTTPException(status_code=400, detail="操作失败")
```

#### API设计规范
```python
# 1. 路由命名
@router.get("/books/{book_id}/chapters")
@router.post("/tts/synthesize")
@router.put("/projects/{project_id}/settings")

# 2. 响应格式
class APIResponse(BaseModel):
    success: bool
    data: Optional[Any] = None
    message: str = ""
    error_code: Optional[str] = None

# 3. 请求验证
class CreateBookRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    author: Optional[str] = Field(None, max_length=100)
    content: str = Field(..., min_length=1)
```

### Vue前端规范

#### 组件组织
- **页面组件**: `src/views/` 目录下按功能模块组织
- **通用组件**: `src/components/` 目录下放置可复用组件
- **组合式函数**: `src/composables/` 目录下放置逻辑复用
- **工具函数**: `src/utils/` 目录下放置通用工具

#### 编码规范
```vue
<!-- 1. 组件结构 -->
<template>
  <div class="audio-editor">
    <div class="editor-toolbar">
      <a-button @click="handlePlay">播放</a-button>
    </div>
    <div class="editor-canvas" ref="canvasRef"></div>
  </div>
</template>

<script setup>
// 2. 使用Composition API
import { ref, onMounted, computed } from 'vue'
import { useAudioStore } from '@/stores/audio'

// 3. 响应式数据
const canvasRef = ref(null)
const audioStore = useAudioStore()

// 4. 计算属性
const isPlaying = computed(() => audioStore.isPlaying)

// 5. 方法定义
const handlePlay = async () => {
  try {
    await audioStore.play()
  } catch (error) {
    console.error('播放失败:', error)
  }
}

// 6. 生命周期
onMounted(() => {
  initCanvas()
})
</script>

<style scoped>
/* 7. 样式规范 */
.audio-editor {
  display: flex;
  flex-direction: column;
  height: 100%;
}

.editor-toolbar {
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}
</style>
```

#### 状态管理规范
```javascript
// stores/audio.js
import { defineStore } from 'pinia'

export const useAudioStore = defineStore('audio', {
  state: () => ({
    currentTrack: null,
    isPlaying: false,
    volume: 1.0
  }),
  
  getters: {
    canPlay: (state) => state.currentTrack && !state.isPlaying
  },
  
  actions: {
    async play() {
      if (!this.currentTrack) return
      
      try {
        await this.currentTrack.play()
        this.isPlaying = true
      } catch (error) {
        console.error('播放失败:', error)
        throw error
      }
    }
  }
})
```

## 数据库规范

### 表设计原则
1. **命名规范**: 使用下划线命名法 (snake_case)
2. **主键**: 统一使用 `id` 作为主键，类型为 `SERIAL`
3. **时间戳**: 包含 `created_at` 和 `updated_at` 字段
4. **软删除**: 使用 `deleted_at` 字段实现软删除
5. **外键**: 明确定义外键关系和约束

### 迁移规范
```python
# 迁移文件命名: YYYY_MM_DD_HHMMSS_description.py
# 例如: 2024_01_15_143000_add_voice_profiles_table.py

def upgrade():
    op.create_table(
        'voice_profiles',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id']),
        sa.PrimaryKeyConstraint('id')
    )
```

## Docker规范

### 容器命名
- **后端**: `ai-sound-backend`
- **前端**: `ai-sound-frontend`
- **数据库**: `ai-sound-postgres`
- **缓存**: `ai-sound-redis`
- **AI服务**: `ai-sound-megatts3`, `ai-sound-tangoflux`

### 端口分配
- **后端API**: 8000
- **前端开发**: 4000
- **Nginx网关**: 4001
- **PostgreSQL**: 5432
- **Redis**: 6379
- **MegaTTS3**: 7929
- **TangoFlux**: 7930

### 数据卷管理
```yaml
volumes:
  postgres_data:     # 数据库数据
  redis_data:        # Redis数据
  audio_storage:     # 音频文件存储
  model_cache:       # AI模型缓存
```

## 测试规范

### 后端测试
```python
# tests/test_api.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_create_book():
    response = client.post("/api/books", json={
        "title": "测试书籍",
        "content": "测试内容"
    })
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### 前端测试
```javascript
// tests/components/AudioEditor.test.js
import { mount } from '@vue/test-utils'
import AudioEditor from '@/components/AudioEditor.vue'

describe('AudioEditor', () => {
  it('应该正确渲染', () => {
    const wrapper = mount(AudioEditor)
    expect(wrapper.find('.audio-editor').exists()).toBe(true)
  })
})
```

## 部署规范

### 环境配置
- **开发环境**: 使用 `docker-compose.yml`
- **生产环境**: 使用 `docker-compose.prod.yml`
- **环境变量**: 通过 `.env` 文件管理

### 健康检查
```python
# 后端健康检查
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "services": {
            "database": await check_database(),
            "redis": await check_redis(),
            "ai_services": await check_ai_services()
        }
    }
```

## 安全规范

### 认证授权
1. **JWT Token**: 使用JWT进行用户认证
2. **权限控制**: 基于角色的访问控制(RBAC)
3. **API限流**: 防止API滥用
4. **CORS配置**: 正确配置跨域访问

### 数据安全
1. **输入验证**: 前后端双重验证
2. **SQL注入防护**: 使用参数化查询
3. **文件上传安全**: 类型检查、大小限制
4. **敏感信息**: 不在日志中记录敏感信息

## 性能优化

### 后端优化
1. **数据库优化**: 合理使用索引、查询优化
2. **缓存策略**: Redis缓存热点数据
3. **异步处理**: 长时间任务使用异步队列
4. **连接池**: 数据库连接池管理

### 前端优化
1. **代码分割**: 路由级别的代码分割
2. **懒加载**: 图片和组件懒加载
3. **缓存策略**: 合理使用浏览器缓存
4. **打包优化**: Vite构建优化

## 监控与日志

### 日志规范
```python
# 后端日志
import logging

logger = logging.getLogger(__name__)

# 信息日志
logger.info(f"用户 {user_id} 创建了书籍 {book_id}")

# 错误日志
logger.error(f"TTS合成失败: {error}", exc_info=True)
```

### 监控指标
1. **系统指标**: CPU、内存、磁盘使用率
2. **应用指标**: 请求响应时间、错误率
3. **业务指标**: 用户活跃度、功能使用情况

## 文档规范

### API文档
- 使用FastAPI自动生成的Swagger文档
- 补充详细的接口说明和示例
- 定期更新文档内容

### 代码文档
```python
def synthesize_speech(text: str, voice_id: str, settings: dict) -> dict:
    """
    合成语音
    
    Args:
        text: 要合成的文本内容
        voice_id: 声音配置ID
        settings: 合成参数设置
        
    Returns:
        dict: 包含音频文件路径和元数据的字典
        
    Raises:
        TTSException: 合成失败时抛出
    """
    pass
```

## 团队协作

### Git工作流
1. **分支策略**: GitFlow工作流
2. **提交规范**: 使用约定式提交格式
3. **代码审查**: 所有代码必须经过审查
4. **版本管理**: 语义化版本控制

### 沟通协作
1. **需求澄清**: 开发前充分理解需求
2. **技术讨论**: 重要技术决策需要团队讨论
3. **问题反馈**: 及时反馈遇到的问题
4. **知识分享**: 定期分享技术经验

## 质量保证

### 代码质量
1. **代码审查**: 强制代码审查流程
2. **静态分析**: 使用ESLint、Pylint等工具
3. **测试覆盖**: 保持合理的测试覆盖率
4. **性能测试**: 定期进行性能测试

### 发布流程
1. **功能测试**: 完整的功能测试
2. **集成测试**: 服务间集成测试
3. **性能测试**: 负载和压力测试
4. **安全测试**: 安全漏洞扫描

---

## 附录

### 常用命令
```bash
# 启动开发环境
scripts\dev-start.bat

# 检查代码同步
scripts\check-code.bat

# 强制重建
scripts\force-rebuild.bat

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f ai-sound-backend
```

### 故障排除
1. **端口冲突**: 检查端口占用情况
2. **Docker问题**: 清理Docker缓存
3. **依赖问题**: 重新安装依赖
4. **权限问题**: 检查文件权限设置

### 参考资源
- [FastAPI官方文档](https://fastapi.tiangolo.com/)
- [Vue 3官方文档](https://vuejs.org/)
- [Docker官方文档](https://docs.docker.com/)
- [PostgreSQL官方文档](https://www.postgresql.org/docs/)

---

*本文档会根据项目发展持续更新，请定期查看最新版本。*