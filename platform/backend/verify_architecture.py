"""
验证新架构的数据一致性功能
"""

from app.database import get_db
from app.schemas.segment_data import ConsistencyChecker
from app.services.auto_recovery_service import AutoRecoveryService

def test_project_consistency(project_id=61):
    """测试项目数据一致性"""
    print(f"=== 验证新架构：项目{project_id}数据一致性检查 ===")
    
    db = next(get_db())
    
    try:
        # 第一步：检查当前状态
        result = ConsistencyChecker.check_chapter_segment_consistency(db, project_id)
        
        print(f"检查结果: {'通过' if result['success'] else '发现问题'}")
        print(f"统计信息: {result['statistics']}")
        
        if not result['success']:
            print(f"\n发现 {len(result['issues'])} 个问题:")
            for i, issue in enumerate(result['issues'], 1):
                print(f"  {i}. {issue}")
            
            return False, result['issues']
        else:
            print("✅ 数据一致性检查通过！")
            return True, []
            
    except Exception as e:
        print(f"❌ 检查失败: {str(e)}")
        return False, [str(e)]

async def test_auto_recovery(project_id=61):
    """测试自动恢复功能"""
    print(f"\n=== 测试自动恢复功能：项目{project_id} ===")
    
    db = next(get_db())
    
    try:
        recovery_service = AutoRecoveryService(db)
        result = await recovery_service.check_and_fix_project_consistency(project_id)
        
        print(f"修复结果: {'成功' if result['success'] else '部分成功'}")
        print(f"修复的问题数量: {len(result['issues_fixed'])}")
        print(f"无法修复的问题: {len(result['issues_unfixable'])}")
        
        if result['issues_fixed']:
            print("\n✅ 已修复的问题:")
            for issue in result['issues_fixed']:
                print(f"  - {issue}")
        
        if result['issues_unfixable']:
            print("\n⚠️ 需要手动处理的问题:")
            for issue in result['issues_unfixable']:
                print(f"  - {issue}")
        
        return result
        
    except Exception as e:
        print(f"❌ 自动恢复失败: {str(e)}")
        return None

def test_existing_data_validation():
    """测试现有数据的Schema验证"""
    print("\n=== 测试现有数据Schema验证 ===")
    
    db = next(get_db())
    
    try:
        from app.models import AnalysisResult
        from app.schemas.segment_data import DataIntegrityValidator
        
        # 获取最近的几个分析结果进行验证
        recent_analyses = db.query(AnalysisResult).filter(
            AnalysisResult.synthesis_plan.isnot(None)
        ).order_by(AnalysisResult.created_at.desc()).limit(3).all()
        
        for analysis in recent_analyses:
            print(f"\n检查章节 {analysis.chapter_id} 的分析结果...")
            
            try:
                validated_plan = DataIntegrityValidator.validate_synthesis_plan(
                    analysis.synthesis_plan
                )
                print(f"  ✅ Schema验证通过: {len(validated_plan.synthesis_plan)} 个segments")
                
                # 检查章节信息完整性
                missing_chapter_info = 0
                for segment in validated_plan.synthesis_plan:
                    if not segment.chapter_id or not segment.chapter_number:
                        missing_chapter_info += 1
                
                if missing_chapter_info == 0:
                    print(f"  ✅ 所有segments包含完整章节信息")
                else:
                    print(f"  ❌ {missing_chapter_info} 个segments缺少章节信息")
                    
            except Exception as e:
                print(f"  ❌ Schema验证失败: {str(e)}")
                print("  💡 建议：需要重新智能分析此章节")
        
    except Exception as e:
        print(f"❌ 现有数据验证失败: {str(e)}")

def main():
    """主验证流程"""
    print("🔍 开始验证新架构功能...")
    
    # 1. 检查数据一致性
    is_consistent, issues = test_project_consistency(61)
    
    # 2. 测试现有数据验证
    test_existing_data_validation()
    
    # 3. 如果有问题，测试自动修复
    if not is_consistent:
        print("\n💡 发现数据不一致问题，尝试自动修复...")
        import asyncio
        recovery_result = asyncio.run(test_auto_recovery(61))
        
        if recovery_result and recovery_result['success']:
            print("\n🎉 自动修复成功！重新检查一致性...")
            is_consistent_after_fix, _ = test_project_consistency(61)
            
            if is_consistent_after_fix:
                print("✅ 修复后数据一致性检查通过！")
            else:
                print("⚠️ 仍有问题需要手动处理")
        else:
            print("⚠️ 自动修复未完全成功，可能需要重新智能分析")
    
    print("\n📋 验证建议:")
    if is_consistent:
        print("✅ 现有数据状态良好，新架构工作正常")
        print("💡 可以继续使用现有数据，无需重新智能分析")
    else:
        print("⚠️ 建议对有问题的章节重新进行智能分析")
        print("💡 或者先尝试API修复：POST /api/v1/consistency/fix/61")

if __name__ == "__main__":
    main() 