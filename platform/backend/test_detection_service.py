#!/usr/bin/env python3
"""
直接测试智能检测服务
"""
import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.intelligent_detection_service import IntelligentDetectionService

async def test_detection_service(chapter_id=339):
    """直接测试智能检测服务"""
    print(f"=== 直接测试智能检测服务 - 章节 {chapter_id} ===")
    
    try:
        # 创建检测服务实例
        detection_service = IntelligentDetectionService()
        
        # 执行检测
        print("🔍 开始执行智能检测...")
        detection_result = await detection_service.detect_chapter_issues(
            chapter_id=chapter_id,
            enable_ai_detection=True
        )
        
        print(f"📊 检测结果:")
        print(f"   章节ID: {detection_result.chapter_id}")
        print(f"   总问题数: {detection_result.total_issues}")
        print(f"   可修复问题数: {detection_result.fixable_issues}")
        print(f"   问题严重程度分布: {detection_result.issues_by_severity}")
        print(f"   检测时间: {detection_result.detection_time}")
        
        if detection_result.issues:
            print(f"\n🚨 发现的问题:")
            for i, issue in enumerate(detection_result.issues):
                print(f"   问题{i+1}: {issue.issue_type} (严重程度: {issue.severity})")
                print(f"     段落索引: {issue.segment_index}")
                print(f"     描述: {issue.description}")
                print(f"     建议: {issue.suggestion}")
                print(f"     可修复: {issue.fixable}")
                print()
        else:
            print(f"✅ 没有发现问题！")
            
    except Exception as e:
        print(f"❌ 检测过程中出错: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_detection_service()) 