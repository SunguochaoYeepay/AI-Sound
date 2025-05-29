#!/usr/bin/env python3
"""
Admin前端与API后端接口对比分析
检查前后端接口是否匹配，找出漏接或错接的地方
"""

import json
import re
from typing import Dict, List, Set, Tuple
from pathlib import Path

class AdminAPIComparison:
    """Admin前端与API后端接口对比分析器"""
    
    def __init__(self):
        self.admin_endpoints = {}  # 前端调用的端点
        self.api_endpoints = {}    # 后端提供的端点
        self.mismatches = []       # 不匹配的端点
        self.missing_in_api = []   # 前端调用但API不存在
        self.missing_in_admin = [] # API存在但前端未调用
        self.exact_matches = []    # 完全匹配的端点
    
    def extract_admin_endpoints(self):
        """提取admin前端调用的端点"""
        print("🔍 分析Admin前端API调用...")
        
        # 从前端API文件中提取的端点
        admin_api_calls = {
            # EngineAPI类
            'engines': {
                'GET /api/engines': 'getEngines()',
                'GET /api/engines/{engineId}': 'getEngine(engineId)',
                'POST /api/engines': 'createEngine(engineData)',
                'PUT /api/engines/{engineId}': 'updateEngine(engineId, engineData)',
                'DELETE /api/engines/{engineId}': 'deleteEngine(engineId)',
                'GET /api/engines/{engineId}/health': 'checkHealth(engineId)',
                'GET /api/engines/{engineId}/config': 'getConfig(engineId)',
                'PUT /api/engines/{engineId}/config': 'updateConfig(engineId, config)',
                'POST /api/engines/{engineId}/restart': 'restartEngine(engineId)',
            },
            
            # VoiceAPI类
            'voices': {
                'GET /api/voices': 'getVoices(params)',
                'GET /api/voices/{voiceId}': 'getVoice(voiceId)',
                'POST /api/voices': 'createVoice(voiceData)',
                'PUT /api/voices/{voiceId}': 'updateVoice(voiceId, voiceData)',
                'DELETE /api/voices/{voiceId}': 'deleteVoice(voiceId)',
                'POST /api/voices/upload': 'uploadVoice(formData)',
                'POST /api/engines/megatts3/voices/{voiceId}/upload-reference': 'uploadMegaTTS3Voice(voiceId, audioFile, npyFile)',
                'POST /api/voices/extract-features': 'extractFeatures(audioFile, engine)',
                'POST /api/voices/{voiceId}/preview': 'previewVoice(voiceId, text)',
                'POST /api/voices/{voiceId}/analyze': 'analyzeVoice(voiceId)',
            },
            
            # CharacterAPI类
            'characters': {
                'GET /api/characters': 'getCharacters(params)',
                'GET /api/characters/{characterId}': 'getCharacter(characterId)',
                'POST /api/characters': 'createCharacter(characterData)',
                'PUT /api/characters/{characterId}': 'updateCharacter(characterId, characterData)',
                'DELETE /api/characters/{characterId}': 'deleteCharacter(characterId)',
                'POST /api/characters/{characterId}/voice-mapping': 'setVoiceMapping(characterId, voiceId)',
                'POST /api/characters/batch': 'batchOperation(operation, characterIds, data)',
            },
            
            # TTSAPI类
            'tts': {
                'POST /api/tts/synthesize': 'synthesize(data)',
                'POST /api/tts/batch-synthesize': 'batchSynthesize(data)',
                'GET /api/tts/tasks/{taskId}': 'getTaskStatus(taskId)',
                'GET /api/tts/tasks': 'getTasks(params)',
                'POST /api/tts/tasks/{taskId}/cancel': 'cancelTask(taskId)',
                'GET /api/tts/formats': 'getSupportedFormats()',
            },
            
            # SystemAPI类
            'system': {
                'GET /api/health': 'healthCheck()',
                'GET /api/system/info': 'getSystemInfo()',
                'GET /api/system/stats': 'getSystemStats()',
                'GET /api/system/logs': 'getLogs(params)',
                'GET /api/system/settings': 'getSettings()',
                'PUT /api/system/settings': 'updateSettings(data)',
                'GET /api/system/settings/export': 'exportSettings()',
                'POST /api/system/settings/import': 'importSettings(data)',
                'GET /api/system/logs/download': 'downloadLogs()',
                'DELETE /api/system/logs': 'clearLogs()',
            }
        }
        
        self.admin_endpoints = admin_api_calls
        total_admin = sum(len(category) for category in admin_api_calls.values())
        print(f"✅ 前端共调用 {total_admin} 个端点")
        return admin_api_calls
    
    def extract_api_endpoints(self):
        """提取API后端提供的端点"""
        print("🔍 分析API后端提供的端点...")
        
        # 从OpenAPI文档和代码分析得出的实际API端点
        api_endpoints = {
            # 系统端点
            'system': {
                'GET /health': '健康检查',
                'GET /info': '系统信息',
            },
            
            # 引擎管理端点
            'engines': {
                'GET /api/engines/': '获取引擎列表',
                'GET /api/engines/{engine_id}': '获取指定引擎详情',
                'POST /api/engines/': '创建引擎',
                'PUT /api/engines/{engine_id}': '更新引擎',
                'DELETE /api/engines/{engine_id}': '删除引擎',
                'POST /api/engines/{engine_id}/start': '启动引擎',
                'POST /api/engines/{engine_id}/stop': '停止引擎',
                'POST /api/engines/{engine_id}/restart': '重启引擎',
                'GET /api/engines/{engine_id}/health': '检查引擎健康状态',
                'GET /api/engines/{engine_id}/config': '获取引擎配置',
                'PUT /api/engines/{engine_id}/config': '更新引擎配置',
                'POST /api/engines/{engine_id}/test': '测试引擎',
                'GET /api/engines/{engine_id}/voices': '获取引擎声音列表',
                'GET /api/engines/{engine_id}/status': '获取引擎状态',
                'GET /api/engines/{engine_id}/metrics': '获取引擎指标',
                'POST /api/engines/discover': '发现引擎',
                'GET /api/engines/health': '检查所有引擎健康状态',
                'GET /api/engines/stats/summary': '获取引擎统计摘要',
            },
            
            # 声音管理端点
            'voices': {
                'GET /api/voices/': '获取声音列表',
                'GET /api/voices/{voice_id}': '获取指定声音',
                'POST /api/voices/': '创建声音',
                'PUT /api/voices/{voice_id}': '更新声音',
                'DELETE /api/voices/{voice_id}': '删除声音',
                'POST /api/voices/upload': '上传声音文件',
                'GET /api/voices/{voice_id}/preview': '预览声音',
                'GET /api/voices/{voice_id}/sample': '获取声音样本',
                'GET /api/voices/search/similar': '搜索相似声音',
                'GET /api/voices/stats/languages': '获取语言统计',
                'GET /api/voices/stats/engines': '获取引擎统计',
                'POST /api/voices/batch/import': '批量导入声音',
                'POST /api/voices/batch/export': '批量导出声音',
                'DELETE /api/voices/batch/delete': '批量删除声音',
            },
            
            # 角色管理端点
            'characters': {
                'GET /api/characters/': '获取角色列表',
                'GET /api/characters/{character_id}': '获取指定角色',
                'POST /api/characters/': '创建角色',
                'PUT /api/characters/{character_id}': '更新角色',
                'DELETE /api/characters/{character_id}': '删除角色',
                'POST /api/characters/{character_id}/voices/{voice_id}': '为角色添加声音',
                'DELETE /api/characters/{character_id}/voices/{voice_id}': '从角色移除声音',
                'POST /api/characters/{character_id}/test': '测试角色声音',
                'POST /api/characters/batch': '批量操作角色',
            },
            
            # TTS合成端点
            'tts': {
                'POST /api/tts/synthesize': '合成语音',
                'POST /api/tts/synthesize/async': '异步合成语音',
                'POST /api/tts/synthesize/batch': '批量合成语音',
                'GET /api/tts/tasks/{task_id}': '获取任务状态',
                'GET /api/tts/tasks/': '获取任务列表',
                'DELETE /api/tts/tasks/{task_id}': '取消任务',
                'GET /api/tts/engines': '获取可用引擎',
                'GET /api/tts/formats': '获取支持格式',
                'GET /api/tts/audio/{filename}': '下载音频文件',
            }
        }
        
        self.api_endpoints = api_endpoints
        total_api = sum(len(category) for category in api_endpoints.values())
        print(f"✅ 后端共提供 {total_api} 个端点")
        return api_endpoints
    
    def normalize_endpoint(self, endpoint: str) -> str:
        """标准化端点路径"""
        # 移除末尾的斜杠
        endpoint = endpoint.rstrip('/')
        # 统一参数格式 {id} 和 /{id}
        endpoint = re.sub(r'\{(\w+)Id\}', r'{$1_id}', endpoint)
        endpoint = re.sub(r'\{(\w+)_id\}', r'{$1_id}', endpoint)
        return endpoint
    
    def compare_endpoints(self):
        """比较前后端端点"""
        print("\n🔄 开始对比前后端接口...")
        
        # 展平所有端点用于比较
        admin_flat = {}
        for category, endpoints in self.admin_endpoints.items():
            for endpoint, method in endpoints.items():
                normalized = self.normalize_endpoint(endpoint)
                admin_flat[normalized] = {'category': category, 'method': method}
        
        api_flat = {}
        for category, endpoints in self.api_endpoints.items():
            for endpoint, desc in endpoints.items():
                normalized = self.normalize_endpoint(endpoint)
                api_flat[normalized] = {'category': category, 'desc': desc}
        
        # 找出匹配和不匹配的端点
        admin_set = set(admin_flat.keys())
        api_set = set(api_flat.keys())
        
        # 完全匹配的端点
        self.exact_matches = list(admin_set & api_set)
        
        # 前端有但API没有的
        self.missing_in_api = list(admin_set - api_set)
        
        # API有但前端没有的
        self.missing_in_admin = list(api_set - admin_set)
        
        # 检查近似匹配（路径相似但不完全相同）
        self.find_similar_endpoints(admin_flat, api_flat)
    
    def find_similar_endpoints(self, admin_flat: Dict, api_flat: Dict):
        """找出相似但不完全匹配的端点"""
        print("🔍 检查相似端点...")
        
        similar_pairs = []
        for admin_ep in self.missing_in_api:
            admin_base = self.get_base_path(admin_ep)
            for api_ep in self.missing_in_admin:
                api_base = self.get_base_path(api_ep)
                if admin_base == api_base:
                    similar_pairs.append((admin_ep, api_ep))
        
        # 从missing列表中移除相似的端点
        for admin_ep, api_ep in similar_pairs:
            if admin_ep in self.missing_in_api:
                self.missing_in_api.remove(admin_ep)
            if api_ep in self.missing_in_admin:
                self.missing_in_admin.remove(api_ep)
            
            self.mismatches.append({
                'admin': admin_ep,
                'api': api_ep,
                'type': 'path_difference',
                'issue': '路径格式不一致'
            })
    
    def get_base_path(self, endpoint: str) -> str:
        """获取端点的基础路径（去除参数）"""
        # 移除方法前缀
        if ' ' in endpoint:
            endpoint = endpoint.split(' ', 1)[1]
        
        # 移除路径参数
        endpoint = re.sub(r'/\{[^}]+\}', '/*', endpoint)
        return endpoint
    
    def analyze_critical_issues(self):
        """分析关键问题"""
        print("\n🚨 分析关键接口问题...")
        
        critical_issues = []
        
        # 检查核心业务功能是否缺失
        core_functions = [
            'POST /api/tts/synthesize',
            'GET /api/engines/',
            'GET /api/voices/',
            'GET /api/characters/',
            'GET /health'
        ]
        
        for func in core_functions:
            normalized = self.normalize_endpoint(func)
            if normalized in self.missing_in_api:
                critical_issues.append({
                    'type': 'missing_core_function',
                    'endpoint': func,
                    'severity': 'critical',
                    'message': f'核心功能缺失：{func}'
                })
        
        # 检查CRUD操作完整性
        crud_patterns = {
            'engines': ['GET', 'POST', 'PUT', 'DELETE'],
            'voices': ['GET', 'POST', 'PUT', 'DELETE'],
            'characters': ['GET', 'POST', 'PUT', 'DELETE']
        }
        
        for resource, methods in crud_patterns.items():
            for method in methods:
                pattern = f"{method} /api/{resource}/"
                if pattern in self.missing_in_api:
                    critical_issues.append({
                        'type': 'incomplete_crud',
                        'endpoint': pattern,
                        'severity': 'high',
                        'message': f'{resource}的{method}操作缺失'
                    })
        
        return critical_issues
    
    def print_comparison_report(self):
        """打印对比报告"""
        print("\n" + "="*80)
        print("📊 ADMIN前端与API后端接口对比报告")
        print("="*80)
        
        # 统计信息
        total_admin = sum(len(cat) for cat in self.admin_endpoints.values())
        total_api = sum(len(cat) for cat in self.api_endpoints.values())
        
        print(f"\n📈 基础统计:")
        print(f"   前端调用端点: {total_admin} 个")
        print(f"   后端提供端点: {total_api} 个")
        print(f"   完全匹配: {len(self.exact_matches)} 个")
        print(f"   路径不一致: {len(self.mismatches)} 个")
        print(f"   前端调用但API缺失: {len(self.missing_in_api)} 个")
        print(f"   API提供但前端未用: {len(self.missing_in_admin)} 个")
        
        # 匹配率
        match_rate = (len(self.exact_matches) / total_admin * 100) if total_admin > 0 else 0
        print(f"   接口匹配率: {match_rate:.1f}%")
        
        # 完全匹配的端点
        if self.exact_matches:
            print(f"\n✅ 完全匹配的端点 ({len(self.exact_matches)}个):")
            for endpoint in sorted(self.exact_matches):
                print(f"   ✓ {endpoint}")
        
        # 路径不一致的端点
        if self.mismatches:
            print(f"\n⚠️  路径不一致的端点 ({len(self.mismatches)}个):")
            for mismatch in self.mismatches:
                print(f"   🔄 前端: {mismatch['admin']}")
                print(f"      后端: {mismatch['api']}")
                print(f"      问题: {mismatch['issue']}")
                print()
        
        # 前端调用但API缺失
        if self.missing_in_api:
            print(f"\n❌ 前端调用但API缺失 ({len(self.missing_in_api)}个):")
            for endpoint in sorted(self.missing_in_api):
                print(f"   ❌ {endpoint}")
        
        # API提供但前端未使用
        if self.missing_in_admin:
            print(f"\n⭕ API提供但前端未调用 ({len(self.missing_in_admin)}个):")
            for endpoint in sorted(self.missing_in_admin):
                print(f"   ⭕ {endpoint}")
        
        # 关键问题分析
        critical_issues = self.analyze_critical_issues()
        if critical_issues:
            print(f"\n🚨 关键问题 ({len(critical_issues)}个):")
            for issue in critical_issues:
                severity_icon = "🔥" if issue['severity'] == 'critical' else "⚠️"
                print(f"   {severity_icon} {issue['message']}")
        
        # 建议
        print(f"\n💡 修复建议:")
        if self.missing_in_api:
            print(f"   1. 实现前端需要的 {len(self.missing_in_api)} 个缺失API端点")
        if self.mismatches:
            print(f"   2. 统一 {len(self.mismatches)} 个路径格式不一致的端点")
        if self.missing_in_admin:
            print(f"   3. 考虑在前端使用 {len(self.missing_in_admin)} 个未使用的API功能")
        
        print("\n" + "="*80)

def main():
    """主函数"""
    print("🔍 开始Admin前端与API后端接口对比分析...")
    
    analyzer = AdminAPIComparison()
    
    # 提取端点信息
    analyzer.extract_admin_endpoints()
    analyzer.extract_api_endpoints()
    
    # 进行对比分析
    analyzer.compare_endpoints()
    
    # 打印报告
    analyzer.print_comparison_report()

if __name__ == "__main__":
    main() 