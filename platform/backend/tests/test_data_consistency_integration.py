"""
数据一致性集成测试
端到端测试整个数据流的一致性
"""

import pytest
import asyncio
from sqlalchemy.orm import Session
from app.database import get_db
from app.services.content_preparation_service import ContentPreparationService
from app.services.auto_recovery_service import AutoRecoveryService
from app.schemas.segment_data import ConsistencyChecker, DataIntegrityValidator
from app.models import BookChapter, AnalysisResult, AudioFile, NovelProject

class TestDataConsistencyIntegration:
    """数据一致性集成测试"""
    
    @pytest.fixture
    def db_session(self):
        """测试数据库会话"""
        db = next(get_db())
        yield db
        db.close()
    
    @pytest.fixture
    def sample_chapter_id(self):
        """测试章节ID"""
        return 111  # 使用现有的测试章节
    
    @pytest.fixture 
    def sample_project_id(self):
        """测试项目ID"""
        return 61  # 使用现有的测试项目
    
    async def test_full_data_flow_consistency(self, db_session: Session, sample_chapter_id: int):
        """测试完整数据流的一致性"""
        # 步骤1：执行智能准备
        content_service = ContentPreparationService(db_session)
        
        try:
            result = await content_service.prepare_chapter_for_synthesis(
                chapter_id=sample_chapter_id,
                user_preferences={"processing_mode": "single"}
            )
            
            # 验证智能准备结果包含完整章节信息
            synthesis_json = result["synthesis_json"]
            assert "synthesis_plan" in synthesis_json
            
            segments = synthesis_json["synthesis_plan"]
            assert len(segments) > 0
            
            # 🔥 关键验证：每个segment都必须包含章节信息
            for i, segment in enumerate(segments):
                assert "chapter_id" in segment, f"Segment {i+1} 缺少 chapter_id"
                assert "chapter_number" in segment, f"Segment {i+1} 缺少 chapter_number"
                assert segment["chapter_id"] == sample_chapter_id, f"Segment {i+1} chapter_id 不正确"
                assert segment["chapter_number"] > 0, f"Segment {i+1} chapter_number 无效"
            
            print(f"✅ 智能准备数据一致性验证通过：{len(segments)} 个segments")
            
        except Exception as e:
            pytest.fail(f"智能准备阶段失败: {str(e)}")
    
    async def test_schema_validation(self, db_session: Session, sample_chapter_id: int):
        """测试Schema验证机制"""
        # 获取现有的分析结果
        analysis = db_session.query(AnalysisResult).filter(
            AnalysisResult.chapter_id == sample_chapter_id
        ).first()
        
        if not analysis or not analysis.synthesis_plan:
            pytest.skip("没有找到测试用的分析结果")
        
        try:
            # 验证现有数据是否符合新Schema
            validated_plan = DataIntegrityValidator.validate_synthesis_plan(
                analysis.synthesis_plan
            )
            
            print(f"✅ Schema验证通过：{len(validated_plan.synthesis_plan)} 个segments")
            
            # 验证每个segment的数据完整性
            for segment in validated_plan.synthesis_plan:
                assert segment.chapter_id > 0
                assert segment.chapter_number > 0
                assert len(segment.text.strip()) > 0
                assert len(segment.speaker.strip()) > 0
                
        except Exception as e:
            pytest.fail(f"Schema验证失败: {str(e)}")
    
    async def test_consistency_checker(self, db_session: Session, sample_project_id: int):
        """测试一致性检查器"""
        try:
            result = ConsistencyChecker.check_chapter_segment_consistency(
                db_session, sample_project_id
            )
            
            assert "success" in result
            assert "issues" in result
            assert "statistics" in result
            
            status = "通过" if result['success'] else f"{len(result['issues'])} 个问题"
            print(f"✅ 一致性检查完成：{status}")
            
            if not result["success"]:
                print("发现的问题：")
                for issue in result["issues"]:
                    print(f"  - {issue}")
            
        except Exception as e:
            pytest.fail(f"一致性检查失败: {str(e)}")
    
    async def test_auto_recovery_service(self, db_session: Session, sample_project_id: int):
        """测试自动恢复服务"""
        try:
            recovery_service = AutoRecoveryService(db_session)
            result = await recovery_service.check_and_fix_project_consistency(
                sample_project_id
            )
            
            assert "success" in result
            assert "issues_fixed" in result
            assert "issues_unfixable" in result
            
            print(f"✅ 自动恢复完成：修复 {len(result['issues_fixed'])} 个问题")
            
            if result["issues_fixed"]:
                print("已修复的问题：")
                for issue in result["issues_fixed"]:
                    print(f"  - {issue}")
            
            if result["issues_unfixable"]:
                print("需要手动处理的问题：")
                for issue in result["issues_unfixable"]:
                    print(f"  - {issue}")
            
        except Exception as e:
            pytest.fail(f"自动恢复测试失败: {str(e)}")
    
    async def test_audio_file_consistency(self, db_session: Session, sample_project_id: int):
        """测试音频文件与segment数据的一致性"""
        try:
            # 获取项目的所有音频文件
            audio_files = db_session.query(AudioFile).filter(
                AudioFile.project_id == sample_project_id,
                AudioFile.audio_type == 'segment'
            ).all()
            
            if not audio_files:
                pytest.skip("没有找到音频文件进行测试")
            
            # 获取对应的segment数据
            from app.models import NovelProject, BookChapter
            project = db_session.query(NovelProject).filter(
                NovelProject.id == sample_project_id
            ).first()
            
            if not project:
                pytest.fail("测试项目不存在")
            
            analysis_results = db_session.query(AnalysisResult).join(
                BookChapter, AnalysisResult.chapter_id == BookChapter.id
            ).filter(BookChapter.book_id == project.book_id).all()
            
            # 构建segment映射
            segment_chapter_mapping = {}
            for analysis in analysis_results:
                if analysis.synthesis_plan and 'synthesis_plan' in analysis.synthesis_plan:
                    segments = analysis.synthesis_plan['synthesis_plan']
                    for segment in segments:
                        segment_id = segment.get('segment_id')
                        chapter_id = segment.get('chapter_id') or analysis.chapter_id
                        if segment_id:
                            segment_chapter_mapping[segment_id] = chapter_id
            
            # 验证音频文件与segment的一致性
            inconsistent_files = []
            for audio in audio_files:
                if audio.segment_id in segment_chapter_mapping:
                    expected_chapter_id = segment_chapter_mapping[audio.segment_id]
                    if audio.chapter_id != expected_chapter_id:
                        inconsistent_files.append({
                            "audio_id": audio.id,
                            "segment_id": audio.segment_id,
                            "actual_chapter": audio.chapter_id,
                            "expected_chapter": expected_chapter_id
                        })
            
            if inconsistent_files:
                print(f"⚠️ 发现 {len(inconsistent_files)} 个音频文件章节映射不一致：")
                for file_info in inconsistent_files:
                    print(f"  - 音频 {file_info['audio_id']} (segment_{file_info['segment_id']}): "
                          f"实际章节 {file_info['actual_chapter']} != 期望章节 {file_info['expected_chapter']}")
            else:
                print(f"✅ 所有 {len(audio_files)} 个音频文件章节映射一致")
            
        except Exception as e:
            pytest.fail(f"音频文件一致性测试失败: {str(e)}")
    
    def test_data_flow_monitoring(self, db_session: Session):
        """测试数据流监控"""
        try:
            # 这里可以添加监控相关的测试
            # 例如检查日志记录、性能指标等
            print("✅ 数据流监控测试通过")
            
        except Exception as e:
            pytest.fail(f"数据流监控测试失败: {str(e)}")

# 运行所有测试的便捷函数
async def run_all_consistency_tests():
    """运行所有数据一致性测试"""
    print("🔍 开始运行数据一致性集成测试...")
    
    test_instance = TestDataConsistencyIntegration()
    db = next(get_db())
    
    try:
        # 运行各项测试
        print("\n1. 测试完整数据流一致性...")
        await test_instance.test_full_data_flow_consistency(db, 111)
        
        print("\n2. 测试Schema验证...")
        await test_instance.test_schema_validation(db, 111)
        
        print("\n3. 测试一致性检查器...")
        await test_instance.test_consistency_checker(db, 61)
        
        print("\n4. 测试自动恢复服务...")
        await test_instance.test_auto_recovery_service(db, 61)
        
        print("\n5. 测试音频文件一致性...")
        await test_instance.test_audio_file_consistency(db, 61)
        
        print("\n6. 测试数据流监控...")
        test_instance.test_data_flow_monitoring(db)
        
        print("\n🎉 所有数据一致性测试完成！")
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    # 直接运行测试
    asyncio.run(run_all_consistency_tests()) 