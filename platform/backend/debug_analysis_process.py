#!/usr/bin/env python3
"""
详细调试分析过程
"""

import asyncio
from app.database import get_db
from app.services.storyboard_analysis_service import StoryboardAnalysisService
from app.models import Book, BookChapter, StoryboardAnalysisSession

async def debug_analysis_process():
    """调试分析过程"""
    db = next(get_db())
    
    try:
        print("开始调试分析过程...")
        
        # 获取会话
        service = StoryboardAnalysisService(db)
        session = service.get_session(6)  # 使用会话ID 6
        if not session:
            print("❌ 会话不存在")
            return
        
        print(f"✅ 会话找到，ID: {session.id}")
        print(f"✅ 状态: {session.status}")
        print(f"✅ 当前步骤: {session.current_step}")
        print(f"✅ 已分析章节: {session.analyzed_chapters}")
        print(f"✅ 失败章节: {session.failed_chapters}")
        
        # 获取书籍
        book = db.query(Book).filter(Book.id == session.book_id).first()
        if not book:
            print("❌ 书籍不存在")
            return
        
        print(f"✅ 书籍找到: {book.title}")
        print(f"✅ 章节数: {len(book.chapters)}")
        
        # 手动执行章节分析
        chapter = book.chapters[0]  # 第一个章节
        print(f"\n开始分析章节: {chapter.chapter_title}")
        
        try:
            # 手动调用分析方法
            print("1. 分析场景...")
            scene_cards = await service._analyze_scenes(session, chapter)
            print(f"   生成场景卡: {len(scene_cards)} 个")
            
            print("2. 分析事件...")
            event_cards = await service._analyze_events(session, chapter)
            print(f"   生成事件卡: {len(event_cards)} 个")
            
            print("3. 分析情绪...")
            emotion_cards = await service._analyze_emotions(session, chapter)
            print(f"   生成情绪卡: {len(emotion_cards)} 个")
            
            print("4. 生成音频分镜卡...")
            storyboard_cards = await service._generate_audio_storyboard(
                session, chapter, scene_cards, event_cards, emotion_cards
            )
            print(f"   生成音频分镜卡: {len(storyboard_cards)} 个")
            
            # 保存所有卡片
            print("5. 保存卡片...")
            all_cards = scene_cards + event_cards + emotion_cards + storyboard_cards
            for card in all_cards:
                db.add(card)
            
            db.commit()
            print(f"   ✅ 成功保存 {len(all_cards)} 个卡片")
            
            # 验证卡片是否保存成功
            print("6. 验证保存结果...")
            saved_cards = service.get_session_cards(session_id=session.id, chapter_id=chapter.id)
            print(f"   数据库中的卡片数: {len(saved_cards)}")
            
            for i, card in enumerate(saved_cards):
                print(f"   卡片 {i+1}: {type(card).__name__}")
            
        except Exception as e:
            print(f"❌ 分析过程失败: {str(e)}")
            import traceback
            traceback.print_exc()
        
        print("\n调试完成！")
        
    except Exception as e:
        print(f"❌ 调试失败: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_analysis_process())
