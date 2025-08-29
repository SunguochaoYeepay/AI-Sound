#!/usr/bin/env python3
"""
显示最终6种卡片分析结果
"""

from app.database import get_db
from app.models import StoryboardAnalysisSession, BaseStoryboardCard

def show_final_results():
    """显示最终6种卡片分析结果"""
    db = next(get_db())
    
    print("🎉 6种卡片分析系统 - 最终结果展示")
    print("=" * 50)
    
    # 获取所有会话
    all_sessions = db.query(StoryboardAnalysisSession).order_by(StoryboardAnalysisSession.id.desc()).limit(5).all()
    
    print(f"\n📊 最近 {len(all_sessions)} 个分析会话:")
    
    for session in all_sessions:
        print(f"\n🔍 会话 {session.id}: {session.session_name}")
        print(f"   状态: {session.status}")
        print(f"   进度: {session.progress}%")
        print(f"   总章节: {session.total_chapters}")
        print(f"   已分析: {session.analyzed_chapters}")
        print(f"   失败: {session.failed_chapters}")
        
        # 获取卡片
        cards = db.query(BaseStoryboardCard).filter(BaseStoryboardCard.session_id == session.id).all()
        
        if cards:
            # 按类型统计
            cards_by_type = {}
            for card in cards:
                card_type = card.card_type
                if card_type not in cards_by_type:
                    cards_by_type[card_type] = []
                cards_by_type[card_type].append(card)
            
            print(f"   📈 卡片统计:")
            for card_type, type_cards in cards_by_type.items():
                print(f"      {card_type.upper()}: {len(type_cards)} 个")
            
            print(f"   📊 总计: {len(cards)} 个卡片")
        else:
            print(f"   ❌ 无卡片生成")
    
    # 显示最新的完整会话详情
    latest_complete = None
    for session in all_sessions:
        if session.status == 'ready_for_review':
            latest_complete = session
            break
    
    if latest_complete:
        print(f"\n🎯 最新完整分析会话详情 (会话 {latest_complete.id}):")
        print("=" * 50)
        
        cards = db.query(BaseStoryboardCard).filter(BaseStoryboardCard.session_id == latest_complete.id).all()
        
        # 按类型分组显示
        cards_by_type = {}
        for card in cards:
            card_type = card.card_type
            if card_type not in cards_by_type:
                cards_by_type[card_type] = []
            cards_by_type[card_type].append(card)
        
        for card_type, type_cards in cards_by_type.items():
            print(f"\n📋 {card_type.upper()} 卡片 ({len(type_cards)} 个):")
            for i, card in enumerate(type_cards, 1):
                if hasattr(card, 'content') and card.content:
                    if card.card_type == 'scene':
                        scene_name = card.content.get('scene_name', '未知')
                        print(f"   {i}. 场景: {scene_name}")
                    elif card.card_type == 'event':
                        event_name = card.content.get('event_name', '未知')
                        print(f"   {i}. 事件: {event_name}")
                    elif card.card_type == 'emotion':
                        emotion_type = card.content.get('emotion_type', '未知')
                        print(f"   {i}. 情绪: {emotion_type}")
                    elif card.card_type == 'storyboard':
                        print(f"   {i}. 音频分镜卡")
                    elif card.card_type == 'story':
                        story_summary = card.content.get('story_summary', '未知')
                        print(f"   {i}. 故事概要: {story_summary[:50]}...")
                    elif card.card_type == 'character':
                        character_name = card.content.get('character_name', '未知')
                        print(f"   {i}. 角色: {character_name}")
        
        print(f"\n🎉 6种卡片分析系统运行成功！")
        print(f"📊 总结:")
        print(f"   - 章节级卡片: SCENE({len(cards_by_type.get('scene', []))}) + EVENT({len(cards_by_type.get('event', []))}) + EMOTION({len(cards_by_type.get('emotion', []))}) + STORYBOARD({len(cards_by_type.get('storyboard', []))})")
        print(f"   - 书籍级卡片: STORY({len(cards_by_type.get('story', []))}) + CHARACTER({len(cards_by_type.get('character', []))})")
        print(f"   - 总计: {len(cards)} 个卡片")

if __name__ == "__main__":
    show_final_results()
