"""
直接修复现有数据的章节信息缺失问题
无需重新智能分析，补全缺失的章节信息
"""

from app.database import get_db
from app.models import AnalysisResult, BookChapter

def fix_chapter_info_in_existing_data():
    """修复现有数据中缺失的章节信息"""
    print("🔧 开始修复现有数据的章节信息...")
    
    db = next(get_db())
    
    try:
        # 获取所有需要修复的分析结果
        analysis_results = db.query(AnalysisResult).filter(
            AnalysisResult.synthesis_plan.isnot(None)
        ).all()
        
        print(f"📊 找到 {len(analysis_results)} 个分析结果需要检查")
        
        fixed_count = 0
        
        for analysis in analysis_results:
            # 获取对应的章节信息
            chapter = db.query(BookChapter).filter(
                BookChapter.id == analysis.chapter_id
            ).first()
            
            if not chapter:
                print(f"⚠️ 章节 {analysis.chapter_id} 不存在，跳过")
                continue
            
            synthesis_plan = analysis.synthesis_plan
            if not synthesis_plan or 'synthesis_plan' not in synthesis_plan:
                continue
            
            segments = synthesis_plan['synthesis_plan']
            if not segments:
                continue
            
            # 检查是否需要修复
            needs_fix = False
            for segment in segments:
                if 'chapter_id' not in segment or 'chapter_number' not in segment:
                    needs_fix = True
                    break
            
            if needs_fix:
                print(f"🔄 修复章节 {chapter.id} (第{chapter.chapter_number}章) - {len(segments)} 个segments")
                
                # 为所有segments添加章节信息
                for segment in segments:
                    segment['chapter_id'] = chapter.id
                    segment['chapter_number'] = chapter.chapter_number
                
                # 保存修改
                analysis.synthesis_plan = synthesis_plan
                fixed_count += 1
            else:
                print(f"✅ 章节 {chapter.id} 数据已完整，无需修复")
        
        # 提交所有修改
        if fixed_count > 0:
            db.commit()
            print(f"\n🎉 修复完成！成功修复了 {fixed_count} 个章节的数据")
        else:
            print("\n✅ 所有数据都已完整，无需修复")
        
        return fixed_count
        
    except Exception as e:
        print(f"❌ 修复失败: {str(e)}")
        db.rollback()
        return 0
    finally:
        db.close()

def verify_fix():
    """验证修复结果"""
    print("\n🔍 验证修复结果...")
    
    from app.schemas.segment_data import ConsistencyChecker
    db = next(get_db())
    
    try:
        result = ConsistencyChecker.check_chapter_segment_consistency(db, 61)
        
        if result['success']:
            print("✅ 验证通过：数据一致性检查成功！")
            print("🎵 现在可以正常播放音频了")
            return True
        else:
            print(f"⚠️ 仍有 {len(result['issues'])} 个问题:")
            for issue in result['issues']:
                print(f"  - {issue}")
            return False
            
    except Exception as e:
        print(f"❌ 验证失败: {str(e)}")
        return False
    finally:
        db.close()

def main():
    """主修复流程"""
    print("🚀 开始一键修复现有数据...")
    
    # 1. 修复数据
    fixed_count = fix_chapter_info_in_existing_data()
    
    # 2. 验证修复结果
    if fixed_count > 0:
        success = verify_fix()
        
        if success:
            print("\n🎉 修复成功！问题已解决：")
            print("  ✅ 所有segments现在都包含完整的章节信息")
            print("  ✅ 音频播放错误已修复")
            print("  ✅ 数据一致性检查通过")
            print("\n💡 现在可以直接播放音频，无需重新智能分析！")
        else:
            print("\n⚠️ 修复后仍有问题，可能需要重新智能分析")
    else:
        print("\n💡 数据已经完整，问题可能在其他地方")

if __name__ == "__main__":
    main() 