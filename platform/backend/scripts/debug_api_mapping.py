#!/usr/bin/env python3
"""
调试API调用时的映射过程
"""

import sys
import os
import asyncio

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

async def debug_api_mapping():
    """调试API调用时的映射过程"""
    print("🔍 调试API调用时的映射过程")
    print("=" * 60)
    
    try:
        # 导入分析器
        from app.services.narration_environment_analyzer import NarrationEnvironmentAnalyzer
        from app.database import get_db
        from app.models.analysis_result import AnalysisResult
        
        # 获取数据库会话
        db = next(get_db())
        
        # 查询章节836的分析结果
        analysis_result = db.query(AnalysisResult).filter(
            AnalysisResult.chapter_id == 836
        ).first()
        
        if not analysis_result or not analysis_result.synthesis_plan:
            print("❌ 未找到章节836的synthesis_plan数据")
            return
        
        synthesis_plan = analysis_result.synthesis_plan.get('synthesis_plan', [])
        print(f"📊 获取到真实章节数据，共{len(synthesis_plan)}个段落")
        
        # 创建分析器实例
        analyzer = NarrationEnvironmentAnalyzer(db=db)
        
        # 直接调用分析器
        print("🎵 直接调用分析器...")
        result = await analyzer.extract_and_analyze_narration(synthesis_plan)
        
        print(f"✅ 分析完成")
        print(f"📊 识别轨道数: {len(result.get('environment_tracks', []))}")
        print()
        
        # 显示分析结果
        tracks = result.get('environment_tracks', [])
        for i, track in enumerate(tracks, 1):
            print(f"轨道 {i}:")
            print(f"  - 段落ID: {track.get('segment_id', 'N/A')}")
            print(f"  - 关键词: {track.get('environment_keywords', [])}")
            print(f"  - 时长: {track.get('duration', 0):.1f}秒")
            print(f"  - 开始时间: {track.get('start_time', 0):.1f}秒")
            print(f"  - 置信度: {track.get('confidence', 0):.2f}")
            print(f"  - 映射策略: {track.get('mapping_strategy', 'N/A')}")
            print(f"  - 旁白文本: {track.get('narration_text', '')[:100]}...")
            print()
        
        # 显示分析摘要
        summary = result.get('analysis_summary', {})
        print(f"📊 分析摘要:")
        print(f"  - 总时长: {summary.get('total_duration', 0):.1f}秒")
        print(f"  - 旁白段落数: {summary.get('narration_segments', 0)}")
        print(f"  - 环境音轨道数: {summary.get('environment_tracks_detected', 0)}")
        print(f"  - 分析模式: {summary.get('analysis_mode', 'N/A')}")
        print()
        
        # 对比API结果
        print("🔍 对比API结果:")
        print("  - API结果: ['马蹄声', '说话声']")
        print("  - 直接分析结果: 见上方轨道详情")
        print()
        
        # 检查是否有缓存问题
        print("🔍 检查缓存问题:")
        print("  - 可能的原因：")
        print("    1. API使用了缓存的分析结果")
        print("    2. 映射逻辑在API调用时出错")
        print("    3. synthesis_plan数据不一致")
        print()
        
        # 建议解决方案
        print("💡 建议解决方案:")
        print("  1. 强制重新分析（force_reanalyze=True）")
        print("  2. 检查API调用时的synthesis_plan数据")
        print("  3. 调试映射逻辑")
        
    except Exception as e:
        print(f"❌ 调试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_api_mapping())
