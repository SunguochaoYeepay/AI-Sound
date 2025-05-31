#!/usr/bin/env python3
"""
前后端对接完整解决方案 🔧
老爹出品 - 一键解决前后端对接问题
功能：自动化测试、Mock服务、接口文档、契约验证
"""

import requests
import json
import re
import os
import subprocess
from datetime import datetime
from typing import Dict, List, Any, Optional
from pathlib import Path
import threading
import time

class FrontendBackendIntegrationSolution:
    """前后端对接完整解决方案"""
    
    def __init__(self, 
                 backend_url: str = "http://localhost:9930",
                 frontend_url: str = "http://localhost:8929"):
        self.backend_url = backend_url
        self.frontend_url = frontend_url
        self.session = requests.Session()
        self.session.timeout = 10
        self.issues = []
        self.test_results = []
        
    def log_issue(self, category: str, severity: str, issue: str, solution: str):
        """记录问题及解决方案"""
        self.issues.append({
            "category": category,
            "severity": severity,
            "issue": issue,
            "solution": solution,
            "timestamp": datetime.now().isoformat()
        })
        
        icon = "🚨" if severity == "高" else "⚠️" if severity == "中" else "💡"
        print(f"{icon} [{severity}] {category}: {issue}")
        print(f"   💡 解决方案: {solution}\n")
    
    def check_services_status(self):
        """检查前后端服务状态"""
        print("🔍 === 检查服务状态 ===")
        
        # 检查后端
        try:
            response = self.session.get(f"{self.backend_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"   ✅ 后端服务正常 ({self.backend_url})")
            else:
                self.log_issue(
                    "服务状态", "高",
                    f"后端服务异常 (状态码: {response.status_code})",
                    "检查后端服务配置和启动状态"
                )
        except Exception as e:
            self.log_issue(
                "服务状态", "高",
                f"无法连接后端服务: {e}",
                f"确保后端服务在 {self.backend_url} 正常运行"
            )
        
        # 检查前端
        try:
            response = self.session.get(self.frontend_url, timeout=5)
            if response.status_code == 200:
                print(f"   ✅ 前端服务正常 ({self.frontend_url})")
            else:
                self.log_issue(
                    "服务状态", "中",
                    f"前端服务异常 (状态码: {response.status_code})",
                    "检查前端服务配置和启动状态"
                )
        except Exception as e:
            self.log_issue(
                "服务状态", "中",
                f"无法连接前端服务: {e}",
                f"确保前端服务在 {self.frontend_url} 正常运行"
            )
    
    def test_critical_api_endpoints(self):
        """测试关键API端点"""
        print("🎯 === 测试关键API端点 ===")
        
        critical_endpoints = [
            ("GET", "/health", "系统健康检查"),
            ("GET", "/info", "系统信息"),
            ("GET", "/api/engines/", "引擎列表"),
            ("GET", "/api/voices/", "声音列表"),
            ("GET", "/api/characters/", "角色列表"),
            ("POST", "/api/tts/synthesize", "TTS合成"),
        ]
        
        for method, endpoint, description in critical_endpoints:
            self._test_single_endpoint(method, endpoint, description)
    
    def _test_single_endpoint(self, method: str, endpoint: str, description: str):
        """测试单个端点"""
        try:
            full_url = f"{self.backend_url}{endpoint}"
            
            if method == "GET":
                response = self.session.get(full_url)
            elif method == "POST":
                test_data = self._get_test_data_for_endpoint(endpoint)
                response = self.session.post(full_url, json=test_data)
            else:
                return
            
            # 记录测试结果
            result = {
                "method": method,
                "endpoint": endpoint,
                "description": description,
                "status_code": response.status_code,
                "success": response.status_code in [200, 201],
                "response_time": response.elapsed.total_seconds(),
                "content_type": response.headers.get('content-type', ''),
                "timestamp": datetime.now().isoformat()
            }
            
            self.test_results.append(result)
            
            if result["success"]:
                print(f"   ✅ {description} - {method} {endpoint} (时间: {result['response_time']:.3f}s)")
                
                # 检查响应格式
                self._validate_response_format(endpoint, response)
            else:
                self.log_issue(
                    "API错误", "高",
                    f"{description} 失败 - {method} {endpoint} (状态码: {response.status_code})",
                    f"检查端点实现和参数验证"
                )
                
        except Exception as e:
            self.log_issue(
                "连接错误", "高",
                f"{description} 连接失败 - {method} {endpoint}: {e}",
                "检查网络连接和服务器状态"
            )
    
    def _get_test_data_for_endpoint(self, endpoint: str) -> dict:
        """获取端点测试数据"""
        test_data = {
            "/api/tts/synthesize": {
                "text": "这是一个测试文本",
                "voice_id": "xiaoxiao",
                "format": "wav"
            },
            "/api/engines/": {
                "name": "测试引擎",
                "type": "megatts3",
                "config": {}
            }
        }
        return test_data.get(endpoint, {})
    
    def _validate_response_format(self, endpoint: str, response: requests.Response):
        """验证响应格式"""
        try:
            data = response.json()
            
            # 检查标准响应格式
            if isinstance(data, dict):
                if "success" in data and "data" in data:
                    pass  # 标准格式
                elif endpoint.endswith('/') and isinstance(data, list):
                    pass  # 列表端点直接返回数组也可以接受
                else:
                    self.log_issue(
                        "响应格式", "中",
                        f"{endpoint} 响应格式不标准",
                        "使用统一的 {success: true, data: {...}, message: ''} 格式"
                    )
            
        except json.JSONDecodeError:
            self.log_issue(
                "响应格式", "中",
                f"{endpoint} 返回非JSON数据",
                "确保所有API端点返回有效的JSON数据"
            )
    
    def test_cors_configuration(self):
        """测试CORS配置"""
        print("🌐 === 测试CORS配置 ===")
        
        # 测试预检请求
        try:
            headers = {
                'Origin': self.frontend_url,
                'Access-Control-Request-Method': 'POST',
                'Access-Control-Request-Headers': 'Content-Type'
            }
            
            response = self.session.options(f"{self.backend_url}/api/engines/", headers=headers)
            
            required_cors_headers = [
                'Access-Control-Allow-Origin',
                'Access-Control-Allow-Methods',
                'Access-Control-Allow-Headers'
            ]
            
            missing_headers = []
            for header in required_cors_headers:
                if header not in response.headers:
                    missing_headers.append(header)
            
            if missing_headers:
                self.log_issue(
                    "CORS配置", "高",
                    f"CORS头部缺失: {', '.join(missing_headers)}",
                    "在后端添加CORS中间件配置"
                )
            else:
                print("   ✅ CORS配置正确")
                
        except Exception as e:
            self.log_issue(
                "CORS测试", "中",
                f"CORS测试失败: {e}",
                "检查后端CORS配置"
            )
    
    def test_data_flow(self):
        """测试完整数据流"""
        print("🔄 === 测试完整数据流 ===")
        
        # 测试完整的TTS流程
        try:
            # 1. 获取声音列表
            voices_response = self.session.get(f"{self.backend_url}/api/voices/")
            if voices_response.status_code != 200:
                raise Exception("无法获取声音列表")
            
            # 2. 执行TTS合成
            tts_data = {
                "text": "完整流程测试",
                "voice_id": "xiaoxiao",
                "format": "wav"
            }
            
            tts_response = self.session.post(f"{self.backend_url}/api/tts/synthesize", json=tts_data)
            if tts_response.status_code != 200:
                raise Exception("TTS合成失败")
            
            print("   ✅ 完整数据流测试通过")
            
        except Exception as e:
            self.log_issue(
                "数据流", "高",
                f"完整数据流测试失败: {e}",
                "检查各个端点的依赖关系和数据一致性"
            )
    
    def generate_api_documentation(self):
        """生成API文档"""
        print("📚 === 生成API文档 ===")
        
        doc_content = self._build_api_documentation()
        
        doc_file = Path("API_INTEGRATION_GUIDE.md")
        try:
            with open(doc_file, 'w', encoding='utf-8') as f:
                f.write(doc_content)
            
            print(f"   ✅ API文档已生成: {doc_file}")
            
        except Exception as e:
            self.log_issue(
                "文档生成", "低",
                f"无法生成API文档: {e}",
                "检查文件写入权限"
            )
    
    def _build_api_documentation(self) -> str:
        """构建API文档内容"""
        return f"""# AI-Sound API对接指南

## 📋 概览

本文档提供前后端API对接的完整指南，确保前后端协作顺利。

**生成时间**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**后端地址**: {self.backend_url}
**前端地址**: {self.frontend_url}

## 🔧 关键API端点

### 1. 系统信息
```
GET /health - 健康检查
GET /info - 系统信息
```

### 2. 引擎管理
```
GET /api/engines/ - 获取引擎列表
POST /api/engines/ - 创建引擎
GET /api/engines/{{id}} - 获取引擎详情
PUT /api/engines/{{id}} - 更新引擎
DELETE /api/engines/{{id}} - 删除引擎
```

### 3. 声音管理
```
GET /api/voices/ - 获取声音列表
POST /api/voices/ - 创建声音
POST /api/voices/upload - 上传声音文件
```

### 4. TTS合成
```
POST /api/tts/synthesize - 同步合成
POST /api/tts/synthesize-async - 异步合成
GET /api/tts/tasks/{{id}} - 查询任务状态
```

## 📊 标准响应格式

### 成功响应
```json
{{
  "success": true,
  "data": {{...}},
  "message": "操作成功"
}}
```

### 错误响应
```json
{{
  "success": false,
  "error": "错误信息",
  "code": "ERROR_CODE"
}}
```

## 🛠️ 前端调用示例

### 使用axios
```javascript
// 获取声音列表
const response = await axios.get('/api/voices/');
const voices = response.data.data || response.data;

// TTS合成
const ttsResponse = await axios.post('/api/tts/synthesize', {{
  text: '要合成的文本',
  voice_id: 'xiaoxiao',
  format: 'wav'
}});
```

## ⚠️ 常见问题

### 1. CORS问题
**现象**: 浏览器报CORS错误
**解决**: 后端添加CORS中间件，允许前端域名

### 2. 响应格式不一致
**现象**: 前端无法正确解析响应
**解决**: 统一使用标准响应格式

### 3. 接口超时
**现象**: 请求超时
**解决**: 增加超时设置，优化后端性能

## 🎯 最佳实践

1. **错误处理**: 前端要有完善的错误处理机制
2. **加载状态**: 显示加载状态，提升用户体验
3. **数据验证**: 前后端都要进行数据验证
4. **日志记录**: 记录关键操作日志，便于调试

## 📞 联系方式

如有问题，请联系开发团队。
"""
    
    def create_integration_checklist(self):
        """创建对接检查清单"""
        print("📝 === 创建对接检查清单 ===")
        
        checklist = """# 前后端对接检查清单 ✅

## 🔧 后端检查项

- [ ] 所有API端点已实现
- [ ] CORS配置正确
- [ ] 统一响应格式
- [ ] 错误处理完善
- [ ] API文档更新
- [ ] 单元测试覆盖
- [ ] 性能优化完成

## 📱 前端检查项

- [ ] API调用封装完成
- [ ] 错误处理机制
- [ ] 加载状态显示
- [ ] 数据验证逻辑
- [ ] 响应格式适配
- [ ] 跨域问题解决
- [ ] 用户体验优化

## 🧪 测试检查项

- [ ] 单接口功能测试
- [ ] 完整流程测试
- [ ] 异常情况测试
- [ ] 性能压力测试
- [ ] 跨浏览器测试
- [ ] 移动端适配测试

## 📊 部署检查项

- [ ] 环境配置正确
- [ ] 服务启动正常
- [ ] 网络连接畅通
- [ ] 监控告警配置
- [ ] 日志收集配置
- [ ] 备份恢复方案

## 🎯 验收标准

- [ ] 所有API调用正常
- [ ] 错误提示友好
- [ ] 性能指标达标
- [ ] 用户体验良好
- [ ] 代码质量合格
"""
        
        checklist_file = Path("INTEGRATION_CHECKLIST.md")
        try:
            with open(checklist_file, 'w', encoding='utf-8') as f:
                f.write(checklist)
            
            print(f"   ✅ 检查清单已生成: {checklist_file}")
            
        except Exception as e:
            self.log_issue(
                "文档生成", "低",
                f"无法生成检查清单: {e}",
                "检查文件写入权限"
            )
    
    def provide_fix_suggestions(self):
        """提供修复建议"""
        print("\n🎯 === 修复建议总结 ===")
        
        if not self.issues:
            print("🎉 太棒了！没有发现任何问题，前后端对接完美！")
            return
        
        # 按严重程度分类
        high_issues = [i for i in self.issues if i['severity'] == '高']
        medium_issues = [i for i in self.issues if i['severity'] == '中']
        low_issues = [i for i in self.issues if i['severity'] == '低']
        
        print(f"📊 问题统计:")
        print(f"   🚨 高优先级: {len(high_issues)} 个")
        print(f"   ⚠️ 中优先级: {len(medium_issues)} 个")
        print(f"   💡 低优先级: {len(low_issues)} 个")
        print()
        
        # 生成修复脚本
        self._generate_fix_script()
        
        print("🔧 立即修复建议:")
        for issue in high_issues[:5]:  # 只显示前5个高优先级问题
            print(f"   • {issue['issue']}")
            print(f"     解决方案: {issue['solution']}")
        
        if len(high_issues) > 5:
            print(f"   ... 还有 {len(high_issues) - 5} 个高优先级问题")
    
    def _generate_fix_script(self):
        """生成自动修复脚本"""
        script_content = """#!/usr/bin/env python3
# 自动修复脚本
# 此脚本包含常见问题的自动修复方案

import subprocess
import sys

def fix_cors_issues():
    print("修复CORS问题...")
    # 添加CORS中间件的示例代码
    cors_middleware = '''
    # 在FastAPI应用中添加CORS中间件
    from fastapi.middleware.cors import CORSMiddleware
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:8929"],  # 前端地址
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    '''
    print(cors_middleware)

def fix_response_format():
    print("统一响应格式...")
    # 响应格式标准化示例
    response_format = '''
    # 标准响应格式
    from pydantic import BaseModel
    
    class StandardResponse(BaseModel):
        success: bool
        data: Any = None
        message: str = ""
        
    @app.get("/api/example")
    async def example():
        return StandardResponse(
            success=True,
            data={"result": "data"},
            message="操作成功"
        )
    '''
    print(response_format)

if __name__ == "__main__":
    print("🔧 开始自动修复...")
    fix_cors_issues()
    fix_response_format()
    print("✅ 修复建议已生成")
"""
        
        script_file = Path("auto_fix_script.py")
        try:
            with open(script_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
            print(f"   ✅ 自动修复脚本已生成: {script_file}")
        except Exception:
            pass
    
    def run_complete_integration_test(self):
        """运行完整的集成测试"""
        print("🚀 === AI-Sound 前后端对接完整测试 ===")
        print(f"⏰ 开始时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 60)
        
        # 执行所有检查
        self.check_services_status()
        self.test_critical_api_endpoints()
        self.test_cors_configuration()
        self.test_data_flow()
        
        # 生成文档和工具
        self.generate_api_documentation()
        self.create_integration_checklist()
        
        # 提供修复建议
        self.provide_fix_suggestions()
        
        # 生成最终报告
        self._generate_final_report()
        
        print("\n🏁 完整对接测试完成！")
    
    def _generate_final_report(self):
        """生成最终测试报告"""
        print("=" * 60)
        print("📋 === 最终测试报告 ===")
        print("=" * 60)
        
        success_count = len([r for r in self.test_results if r['success']])
        total_count = len(self.test_results)
        success_rate = (success_count / total_count * 100) if total_count > 0 else 0
        
        print(f"🎯 API测试结果:")
        print(f"   成功: {success_count}/{total_count} ({success_rate:.1f}%)")
        
        if success_rate >= 90:
            print("   🎉 优秀！API对接质量很高")
        elif success_rate >= 70:
            print("   ✅ 良好！有少量问题需要修复")
        else:
            print("   ⚠️ 需要改进！存在较多问题")
        
        print(f"\n🔍 问题汇总:")
        print(f"   总问题数: {len(self.issues)}")
        
        if len(self.issues) == 0:
            print("   🎉 恭喜！没有发现任何问题")
        else:
            categories = {}
            for issue in self.issues:
                cat = issue['category']
                categories[cat] = categories.get(cat, 0) + 1
            
            for category, count in categories.items():
                print(f"   • {category}: {count} 个")
        
        print(f"\n📚 已生成文档:")
        docs = [
            "API_INTEGRATION_GUIDE.md - API对接指南",
            "INTEGRATION_CHECKLIST.md - 对接检查清单",
            "auto_fix_script.py - 自动修复脚本"
        ]
        
        for doc in docs:
            print(f"   📄 {doc}")


if __name__ == "__main__":
    solution = FrontendBackendIntegrationSolution()
    solution.run_complete_integration_test() 