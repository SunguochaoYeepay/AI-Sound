import sys
sys.path.append('platform/backend')

from app.database import SessionLocal
from app.services.chapter_analysis_service import ChapterAnalysisService

def debug_aggregation():
    db = SessionLocal()
    try:
        service = ChapterAnalysisService(db)
        
        print('=== 测试项目聚合逻辑 ===')
        
        # 直接测试聚合逻辑
        aggregated = service.aggregate_chapter_results(9)  # 项目ID 9
        
        print(f'✅ 聚合成功！')
        print(f'📊 聚合角色数: {len(aggregated["characters"])}')
        print('🎭 聚合的角色:')
        for char in aggregated['characters']:
            print(f'  - {char["name"]} (频次: {char["frequency"]}, 性别: {char.get("gender", "未知")})')
        
        print(f'\n📝 聚合片段数: {len(aggregated["synthesis_plan"])}')
        print('🗣️ 前5个片段的说话人:')
        for i, segment in enumerate(aggregated['synthesis_plan'][:5]):
            print(f'  {i+1}. [{segment["speaker"]}]: {segment["text"][:30]}...')
        
        # 测试转换为合成格式
        print('\n=== 测试转换为合成格式 ===')
        synthesis_format = service.convert_to_synthesis_format(aggregated)
        
        print(f'🎵 合成格式角色数: {len(synthesis_format["characters"])}')
        print('🎤 分配声音的角色:')
        for char in synthesis_format['characters']:
            print(f'  - {char["name"]} -> {char.get("voice_name", "未分配声音")} (ID: {char.get("voice_id", "无")})')
        
    except Exception as e:
        print(f'❌ 错误: {e}')
        import traceback
        traceback.print_exc()
    finally:
        db.close()

if __name__ == "__main__":
    debug_aggregation() 