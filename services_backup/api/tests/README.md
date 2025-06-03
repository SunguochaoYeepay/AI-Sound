# AI-Sound API 测试套件

这是AI-Sound TTS系统的完整测试套件，包含单元测试、集成测试和API测试。

## 📁 目录结构

```
tests/
├── api/                    # API接口测试
│   ├── test_engines.py     # 引擎管理API测试
│   ├── test_voices.py      # 声音管理API测试
│   ├── test_characters.py  # 角色管理API测试
│   ├── test_tts.py         # TTS合成API测试
│   └── test_health.py      # 健康检查API测试
├── unit/                   # 单元测试
│   ├── test_adapters.py    # 适配器单元测试
│   └── test_services.py    # 服务层单元测试
├── integration/            # 集成测试
│   ├── test_engine_integration.py  # 引擎集成测试
│   └── test_tts_workflow.py        # TTS工作流测试
├── conftest.py            # pytest配置和夹具
├── run_tests.py           # 测试运行脚本
├── quick_test.py          # 快速接口测试
└── README.md              # 本文件
```

## 🚀 快速开始

### 1. 安装测试依赖

```bash
# 安装测试依赖
pip install -r requirements-test.txt
```

### 2. 快速验证接口

在启动API服务后，运行快速测试来验证核心接口：

```bash
# 快速测试所有核心接口
python tests/quick_test.py

# 指定API服务地址
python tests/quick_test.py --url http://localhost:9930
```

### 3. 运行完整测试套件

```bash
# 运行所有测试
python tests/run_tests.py

# 运行特定类型的测试
python tests/run_tests.py --type unit        # 单元测试
python tests/run_tests.py --type integration # 集成测试
python tests/run_tests.py --type api         # API测试

# 详细输出和覆盖率报告
python tests/run_tests.py --verbose --coverage
```

### 4. 使用pytest直接运行

```bash
# 运行所有测试
pytest

# 运行特定测试文件
pytest tests/api/test_engines.py

# 运行特定测试类
pytest tests/api/test_engines.py::TestEnginesAPI

# 运行特定测试方法
pytest tests/api/test_engines.py::TestEnginesAPI::test_create_engine

# 运行带标记的测试
pytest -m integration  # 只运行集成测试
pytest -m "not slow"   # 排除慢速测试

# 并行运行测试
pytest -n auto

# 生成覆盖率报告
pytest --cov=src --cov-report=html
```

## 📋 测试类型说明

### 单元测试 (Unit Tests)
- **位置**: `tests/unit/`
- **目的**: 测试单个组件的功能
- **特点**: 快速、隔离、使用模拟对象
- **覆盖**: 适配器、服务层、工具函数

### 集成测试 (Integration Tests)
- **位置**: `tests/integration/`
- **目的**: 测试组件间的交互
- **特点**: 需要真实的数据库连接
- **覆盖**: 完整工作流、数据流转

### API测试 (API Tests)
- **位置**: `tests/api/`
- **目的**: 测试HTTP API接口
- **特点**: 端到端测试、真实HTTP请求
- **覆盖**: 所有REST API端点

## 🔧 测试配置

### 环境变量
测试会自动设置以下环境变量：
```bash
DB_HOST=localhost
DB_PORT=27017
DB_DATABASE=ai_sound_test
API_HOST=127.0.0.1
API_PORT=9930
LOG_LEVEL=DEBUG
```

### 测试数据库
- 使用独立的测试数据库 `ai_sound_test`
- 每次测试前后自动清理数据
- 支持MongoDB和模拟数据库

### 测试夹具 (Fixtures)
- `client`: 同步测试客户端
- `async_client`: 异步测试客户端
- `test_db`: 测试数据库连接
- `sample_*_data`: 示例测试数据

## 📊 覆盖率报告

运行带覆盖率的测试后，会生成以下报告：
- **终端报告**: 直接在命令行显示
- **HTML报告**: `htmlcov/index.html`
- **JSON报告**: 用于CI/CD集成

```bash
# 查看HTML覆盖率报告
open htmlcov/index.html  # macOS
start htmlcov/index.html # Windows
```

## 🐛 调试测试

### 详细输出
```bash
# 显示详细的测试输出
pytest -v -s

# 显示最慢的10个测试
pytest --durations=10

# 只运行失败的测试
pytest --lf

# 在第一个失败时停止
pytest -x
```

### 调试特定测试
```bash
# 使用pdb调试
pytest --pdb

# 在失败时进入调试器
pytest --pdb-trace
```

## 🔄 持续集成

### GitHub Actions
测试套件已配置为在以下情况下自动运行：
- 推送到主分支
- 创建Pull Request
- 定时运行（每日）

### 本地CI模拟
```bash
# 模拟CI环境运行测试
python tests/run_tests.py --type all --coverage --verbose
```

## 📝 编写新测试

### 测试命名规范
- 测试文件: `test_*.py`
- 测试类: `Test*`
- 测试方法: `test_*`

### 示例测试
```python
import pytest
from httpx import AsyncClient

class TestNewFeature:
    """新功能测试"""
    
    def test_sync_function(self, client):
        """同步测试示例"""
        response = client.get("/api/new-endpoint")
        assert response.status_code == 200
    
    @pytest.mark.asyncio
    async def test_async_function(self, async_client: AsyncClient):
        """异步测试示例"""
        response = await async_client.post("/api/async-endpoint")
        assert response.status_code == 201
```

### 测试标记
```python
@pytest.mark.slow          # 慢速测试
@pytest.mark.integration   # 集成测试
@pytest.mark.unit          # 单元测试
@pytest.mark.api           # API测试
```

## 🚨 常见问题

### 1. 数据库连接失败
确保MongoDB服务正在运行：
```bash
# 启动MongoDB
docker run -d -p 27017:27017 mongo:7
```

### 2. API服务未启动
确保API服务正在运行：
```bash
# 启动API服务
cd services/api
python main.py
```

### 3. 依赖包冲突
重新安装依赖：
```bash
pip install -r requirements.txt
pip install -r requirements-test.txt
```

### 4. 测试超时
增加超时时间：
```bash
pytest --timeout=60
```

## 📈 性能测试

### 基准测试
```bash
# 运行性能基准测试
pytest --benchmark-only

# 保存基准结果
pytest --benchmark-save=baseline

# 与基准比较
pytest --benchmark-compare=baseline
```

### 负载测试
```bash
# 并发测试
pytest tests/integration/ -n 4

# 压力测试
python tests/stress_test.py
```

## 🔒 安全测试

### API安全测试
- 输入验证测试
- 权限检查测试
- 注入攻击防护测试

### 数据安全测试
- 敏感数据脱敏测试
- 数据加密测试
- 访问控制测试

---

## 📞 支持

如果在运行测试时遇到问题，请：
1. 检查上述常见问题
2. 查看测试日志输出
3. 提交Issue并附上错误信息

Happy Testing! 🎉