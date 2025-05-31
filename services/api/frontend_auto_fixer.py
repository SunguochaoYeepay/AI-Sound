#!/usr/bin/env python3
"""
前端自动修复脚本
自动修复前端代码中的常见问题
"""

import re
import json
from pathlib import Path
import shutil
from datetime import datetime

class FrontendAutoFixer:
    def __init__(self):
        self.frontend_path = Path("../web-admin/src")
        self.fixes_applied = []
        self.backup_dir = Path("frontend_backups") / datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # 检查前端路径是否存在
        if not self.frontend_path.exists():
            print(f"❌ 前端路径不存在: {self.frontend_path.absolute()}")
            print("请确保在正确的目录中运行此脚本")
            exit(1)
        
    def backup_file(self, file_path):
        """备份文件"""
        if not self.backup_dir.exists():
            self.backup_dir.mkdir(parents=True)
        
        backup_path = self.backup_dir / file_path.relative_to(self.frontend_path)
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(file_path, backup_path)
        print(f"📁 已备份: {file_path}")
        
    def fix_api_data_access(self, file_path):
        """修复API数据访问问题"""
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        fixes = []
        
        # 修复 response.data.voices 为 response.voices
        pattern1 = r'response\.data\?\.voices'
        if re.search(pattern1, content):
            content = re.sub(pattern1, 'response.voices', content)
            fixes.append("修复: response.data?.voices -> response.voices")
        
        # 修复 response.data?.engines 为 response.engines  
        pattern2 = r'response\.data\?\.engines'
        if re.search(pattern2, content):
            content = re.sub(pattern2, 'response.engines', content)
            fixes.append("修复: response.data?.engines -> response.engines")
            
        # 修复 response.data.data 为 response.data
        pattern3 = r'response\.data\.data'
        if re.search(pattern3, content):
            content = re.sub(pattern3, 'response.data', content)
            fixes.append("修复: response.data.data -> response.data")
            
        # 修复不安全的数据访问
        pattern4 = r'response\.(\w+)\['
        matches = re.findall(pattern4, content)
        for match in matches:
            old_pattern = f'response.{match}['
            new_pattern = f'response.{match}?.[' if match != 'status' else old_pattern
            if old_pattern in content and new_pattern != old_pattern:
                content = content.replace(old_pattern, new_pattern)
                fixes.append(f"修复: 添加安全访问符 response.{match}?.[")
        
        if content != original_content:
            self.backup_file(file_path)
            file_path.write_text(content, encoding='utf-8')
            self.fixes_applied.extend([f"{file_path.name}: {fix}" for fix in fixes])
            return True
        return False
        
    def fix_error_handling(self, file_path):
        """添加错误处理"""
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        fixes = []
        
        # 查找没有错误处理的 async 函数
        async_pattern = r'const\s+(\w+)\s*=\s*async\s*\([^)]*\)\s*=>\s*\{'
        matches = re.finditer(async_pattern, content)
        
        for match in matches:
            func_name = match.group(1)
            start_pos = match.end()
            
            # 查找函数结束位置
            brace_count = 1
            pos = start_pos
            while pos < len(content) and brace_count > 0:
                if content[pos] == '{':
                    brace_count += 1
                elif content[pos] == '}':
                    brace_count -= 1
                pos += 1
            
            if pos < len(content):
                func_body = content[start_pos-1:pos]
                
                # 检查是否包含 await 但没有 try-catch
                if 'await' in func_body and 'try {' not in func_body and 'try{' not in func_body:
                    # 添加 try-catch 包装
                    indented_body = '    ' + func_body[1:-1].replace('\n', '\n    ')
                    new_body = f'''{{
    try {{
{indented_body}
    }} catch (error) {{
      console.error('{func_name}失败:', error);
      message.error('{func_name}失败: ' + (error.response?.data?.message || error.message));
    }}
  }}'''
                    content = content[:start_pos-1] + new_body + content[pos:]
                    fixes.append(f"为函数 {func_name} 添加错误处理")
        
        if content != original_content:
            self.backup_file(file_path)
            file_path.write_text(content, encoding='utf-8')
            self.fixes_applied.extend([f"{file_path.name}: {fix}" for fix in fixes])
            return True
        return False
        
    def fix_import_issues(self, file_path):
        """修复导入问题"""
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        fixes = []
        
        # 检查是否缺少必要的导入
        if 'message.' in content and 'import { message' not in content:
            # 查找现有的 ant-design-vue 导入
            antd_import_pattern = r"import\s*\{([^}]+)\}\s*from\s*['\"]ant-design-vue['\"]"
            match = re.search(antd_import_pattern, content)
            
            if match:
                imports = match.group(1).strip()
                if 'message' not in imports:
                    new_imports = imports + ', message'
                    content = re.sub(antd_import_pattern, f"import {{ {new_imports} }} from 'ant-design-vue'", content)
                    fixes.append("添加 message 导入")
            else:
                # 添加新的导入
                script_match = re.search(r'<script[^>]*>', content)
                if script_match:
                    insert_pos = script_match.end()
                    import_line = "\nimport { message } from 'ant-design-vue';"
                    content = content[:insert_pos] + import_line + content[insert_pos:]
                    fixes.append("添加 ant-design-vue message 导入")
        
        if content != original_content:
            self.backup_file(file_path)
            file_path.write_text(content, encoding='utf-8')
            self.fixes_applied.extend([f"{file_path.name}: {fix}" for fix in fixes])
            return True
        return False
        
    def fix_vue_composition_api_issues(self, file_path):
        """修复Vue Composition API问题"""
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        fixes = []
        
        # 检查是否使用了过时的 @vue/composition-api
        if '@vue/composition-api' in content:
            content = content.replace("from '@vue/composition-api'", "from 'vue'")
            fixes.append("移除过时的 @vue/composition-api 导入")
        
        # 检查 reactive 和 ref 的正确使用
        if 'reactive(' in content or 'ref(' in content:
            vue_import_pattern = r"import\s*\{([^}]+)\}\s*from\s*['\"]vue['\"]"
            match = re.search(vue_import_pattern, content)
            
            if match:
                imports = match.group(1).strip()
                needed_imports = []
                
                if 'reactive(' in content and 'reactive' not in imports:
                    needed_imports.append('reactive')
                if 'ref(' in content and 'ref' not in imports:
                    needed_imports.append('ref')
                if 'computed(' in content and 'computed' not in imports:
                    needed_imports.append('computed')
                if 'onMounted(' in content and 'onMounted' not in imports:
                    needed_imports.append('onMounted')
                if 'onUnmounted(' in content and 'onUnmounted' not in imports:
                    needed_imports.append('onUnmounted')
                if 'nextTick(' in content and 'nextTick' not in imports:
                    needed_imports.append('nextTick')
                    
                if needed_imports:
                    new_imports = imports + ', ' + ', '.join(needed_imports)
                    content = re.sub(vue_import_pattern, f"import {{ {new_imports} }} from 'vue'", content)
                    fixes.append(f"添加Vue导入: {', '.join(needed_imports)}")
        
        if content != original_content:
            self.backup_file(file_path)
            file_path.write_text(content, encoding='utf-8')
            self.fixes_applied.extend([f"{file_path.name}: {fix}" for fix in fixes])
            return True
        return False
        
    def fix_typescript_issues(self, file_path):
        """修复TypeScript类型问题"""
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        fixes = []
        
        # 添加基本的类型安全检查
        patterns = [
            (r'(\w+)\.length(?!\s*>)', r'\1?.length'),  # 安全访问数组长度
            (r'(\w+)\.map\(', r'\1?.map('),              # 安全访问数组方法
            (r'(\w+)\.filter\(', r'\1?.filter('),        # 安全访问数组方法
            (r'(\w+)\.find\(', r'\1?.find('),            # 安全访问数组方法
        ]
        
        for pattern, replacement in patterns:
            if re.search(pattern, content):
                content = re.sub(pattern, replacement, content)
                fixes.append(f"添加类型安全: {pattern} -> {replacement}")
        
        if content != original_content:
            self.backup_file(file_path)
            file_path.write_text(content, encoding='utf-8')
            self.fixes_applied.extend([f"{file_path.name}: {fix}" for fix in fixes])
            return True
        return False
        
    def fix_performance_issues(self, file_path):
        """修复性能问题"""
        content = file_path.read_text(encoding='utf-8')
        original_content = content
        fixes = []
        
        # 检查是否需要添加防抖
        if 'onSearch' in content and 'debounce' not in content:
            # 简单的防抖建议（不自动修复，只记录）
            fixes.append("建议: 为搜索功能添加防抖")
        
        # 检查是否有大量的DOM操作可以优化
        if content.count('document.querySelector') > 3:
            fixes.append("建议: 使用Vue ref替代直接DOM查询")
        
        if fixes:
            self.fixes_applied.extend([f"{file_path.name}: {fix}" for fix in fixes])
            return True
        return False
        
    def run_fixes(self):
        """运行所有修复"""
        print("🚀 开始自动修复前端代码...")
        print("=" * 50)
        
        vue_files = list(self.frontend_path.glob("**/*.vue"))
        js_files = list(self.frontend_path.glob("**/*.js"))
        
        total_files = len(vue_files) + len(js_files)
        fixed_files = 0
        
        for file_path in vue_files + js_files:
            print(f"\n📝 检查文件: {file_path.relative_to(self.frontend_path)}")
            
            try:
                file_fixed = False
                
                # 应用各种修复
                if self.fix_api_data_access(file_path):
                    file_fixed = True
                    
                if self.fix_import_issues(file_path):
                    file_fixed = True
                    
                if self.fix_vue_composition_api_issues(file_path):
                    file_fixed = True
                    
                # if self.fix_error_handling(file_path):
                #     file_fixed = True
                    
                if self.fix_typescript_issues(file_path):
                    file_fixed = True
                    
                if self.fix_performance_issues(file_path):
                    file_fixed = True
                    
                if file_fixed:
                    fixed_files += 1
                    print(f"✅ 已修复")
                else:
                    print(f"✅ 无需修复")
                    
            except Exception as e:
                print(f"❌ 修复失败: {str(e)}")
        
        # 生成修复报告
        self.generate_report(total_files, fixed_files)
        
    def generate_report(self, total_files, fixed_files):
        """生成修复报告"""
        print("\n" + "=" * 50)
        print("📋 自动修复报告")
        print("=" * 50)
        
        print(f"📊 文件统计:")
        print(f"   总文件数: {total_files}")
        print(f"   修复文件数: {fixed_files}")
        if total_files > 0:
            print(f"   修复率: {fixed_files/total_files*100:.1f}%")
        else:
            print("   修复率: 0%（未找到文件）")
        
        print(f"\n🔧 修复详情:")
        if not self.fixes_applied:
            print("   无需要修复的问题")
        else:
            for i, fix in enumerate(self.fixes_applied, 1):
                print(f"   {i}. {fix}")
        
        # 保存详细报告
        report = {
            "fix_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "total_files": total_files,
            "fixed_files": fixed_files,
            "fixes_applied": self.fixes_applied,
            "backup_directory": str(self.backup_dir)
        }
        
        with open("frontend_auto_fix_report.json", "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 详细报告已保存到: frontend_auto_fix_report.json")
        if self.backup_dir.exists():
            print(f"📁 备份文件保存在: {self.backup_dir}")

def main():
    fixer = FrontendAutoFixer()
    fixer.run_fixes()

if __name__ == "__main__":
    main() 