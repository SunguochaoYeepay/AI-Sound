#!/usr/bin/env python3
"""
环境音混合功能简化测试数据生成脚本
"""

import os
import sys
import json
from datetime import datetime, timedelta

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import get_db
from app.models import (
    NovelProject, Book, BookChapter, VoiceProfile, 
    AnalysisResult
)
from app.utils import log_system_event
from sqlalchemy.orm import Session

def create_test_voice_profiles(db: Session):
    """创建测试用声音档案"""
    
    voice_profiles = [
        {
            "name": "林雨",
            "gender": "female",
            "age_range": "young",
            "voice_style": "gentle",
            "voice_speed": 1.0,
            "description": "温柔清甜的女声，适合女主角",
            "sample_text": "这是林雨的声音测试",
            "provider": "MegaTTS3",
            "model_config": {
                "speaker_id": "liuyu",
                "emotion": "neutral",
                "speed": 1.0,
                "pitch": 0.0
            }
        },
        {
            "name": "陈剑",
            "gender": "male", 
            "age_range": "adult",
            "voice_style": "steady",
            "voice_speed": 1.0,
            "description": "沉稳磁性的男声，适合男主角",
            "sample_text": "这是陈剑的声音测试",
            "provider": "MegaTTS3",
            "model_config": {
                "speaker_id": "zhongxin",
                "emotion": "neutral",
                "speed": 1.0,
                "pitch": 0.0
            }
        },
        {
            "name": "老者",
            "gender": "male",
            "age_range": "senior", 
            "voice_style": "wise",
            "voice_speed": 0.9,
            "description": "苍老智慧的声音，适合长者角色",
            "sample_text": "这是老者的声音测试",
            "provider": "MegaTTS3",
            "model_config": {
                "speaker_id": "laorenjia",
                "emotion": "neutral",
                "speed": 0.9,
                "pitch": -0.1
            }
        },
        {
            "name": "小童",
            "gender": "neutral",
            "age_range": "child",
            "voice_style": "cute",
            "voice_speed": 1.1,
            "description": "天真可爱的童声",
            "sample_text": "这是小童的声音测试", 
            "provider": "MegaTTS3",
            "model_config": {
                "speaker_id": "xiaohai",
                "emotion": "happy",
                "speed": 1.1,
                "pitch": 0.2
            }
        }
    ]
    
    created_profiles = []
    for profile_data in voice_profiles:
        existing = db.query(VoiceProfile).filter(
            VoiceProfile.name == profile_data["name"]
        ).first()
        
        if existing:
            print(f"声音档案 '{profile_data['name']}' 已存在，跳过")
            created_profiles.append(existing)
            continue
            
        profile = VoiceProfile(**profile_data)
        db.add(profile)
        created_profiles.append(profile)
        print(f"✅ 创建声音档案: {profile_data['name']}")
    
    db.commit()
    return created_profiles

def create_test_book_and_chapters(db: Session):
    """创建测试用书籍和章节"""
    
    # 检查是否已存在
    existing_book = db.query(Book).filter(Book.title == "环境音测试小说").first()
    if existing_book:
        print(f"书籍 '环境音测试小说' 已存在，获取现有数据...")
        chapters = db.query(BookChapter).filter(BookChapter.book_id == existing_book.id).all()
        return existing_book, chapters
    
    # 创建测试书籍
    book = Book(
        title="环境音测试小说",
        author="AI-Sound测试团队",
        description="专为测试环境音混合功能设计的小说，包含多种场景",
        genre="fantasy",
        status="published",
        total_chapters=3,
        total_words=2500,
        language="zh-CN",
        tags=["测试", "环境音", "场景丰富", "幻想"]
    )
    db.add(book)
    db.flush()  # 获取book.id
    
    # 创建测试章节
    chapters_data = [
        {
            "chapter_number": 1,
            "title": "雨夜古宅",
            "content": """第一章 雨夜古宅

夜深人静，大雨如注。林雨推开古宅沉重的木门，门轴发出吱呀的声响。

"这里就是传说中的幽灵庄园吗？"她轻声自语，声音在空旷的大厅中回荡。

闪电划过天空，照亮了客厅里积满灰尘的家具。雷声轰鸣，让人心跳加速。

突然，楼上传来脚步声。林雨紧张地握紧手电筒，"谁在那里？"

一个苍老的声音从楼梯上方传来："孩子，你终于来了。我等你很久了。"

是一位白发苍苍的老人，慢慢走下楼梯。每一步都让木板嘎吱作响。

"老人家，您是？"林雨疑惑地问道。

"我是这座宅子的管家，守护着这里的秘密。"老者的声音中带着神秘色彩。

窗外雨声渐急，偶尔夹杂着猫头鹰的叫声，为这个诡异的夜晚增添了更多的悬疑气氛。""",
            "word_count": 280,
            "scene_tags": ["雨夜", "古宅", "悬疑", "室内"],
            "character_list": ["林雨", "老管家"],
            "reading_time": 120
        },
        {
            "chapter_number": 2, 
            "title": "森林追逐",
            "content": """第二章 森林追逐

清晨的阳光透过茂密的森林洒下斑驳的光影。鸟儿在枝头欢快地歌唱，溪水潺潺流淌。

陈剑骑着马在林间小径上疾驰，马蹄声在森林中回响。"驾！"他催促着胯下的战马。

身后传来野狼的嚎叫声，越来越近。风声呼啸，树叶簌簌作响。

"糟糕，狼群追上来了！"陈剑回头望去，只见数十只灰狼正在林间穿梭，眼中闪烁着凶光。

他拉紧缰绳，战马嘶鸣一声，跃过一道小溪。水花四溅，激起阵阵涟漪。

就在这时，前方出现了一个小女孩，正在采摘野花。"小心！"陈剑大声喊道。

小女孩抬起头，天真地笑着："大哥哥，你在和小动物们玩游戏吗？"

"快跑！"陈剑翻身下马，抱起小女孩就往林深处跑去。

风声、马蹄声、狼嚎声交织在一起，构成了一幅惊险刺激的森林追逐画面。""",
            "word_count": 310,
            "scene_tags": ["森林", "追逐", "白天", "户外"],
            "character_list": ["陈剑", "小女孩", "旁白"],
            "reading_time": 135
        },
        {
            "chapter_number": 3,
            "title": "海边重逢", 
            "content": """第三章 海边重逢

夕阳西下，海浪轻柔地拍打着沙滩。海鸥在空中盘旋，发出悠长的叫声。

林雨独自走在海边，海风轻抚着她的长发。远处传来渔船的汽笛声。

"真美啊..."她感叹道，看着远方波光粼粼的海面。

脚步声从身后传来，林雨回过头，看到了熟悉的身影。

"陈剑？你怎么会在这里？"她惊讶地问道。

陈剑微笑着走近："我一直在找你。听说你来了海边，我就赶来了。"

海浪声轻柔而有节奏，就像大自然的摇篮曲。两人并肩走在沙滩上，脚印留在湿润的沙子里。

一群海豚突然跃出水面，在夕阳的映照下显得格外美丽。

"看！海豚！"林雨兴奋地指着远方。

"真的很美。"陈剑温柔地看着她，"就像此刻的你一样。"

海风徐徐，夕阳渐落，这个浪漫的黄昏见证了两颗心的重新靠近。""",
            "word_count": 290,
            "scene_tags": ["海边", "黄昏", "浪漫", "户外"],
            "character_list": ["林雨", "陈剑"],
            "reading_time": 125
        }
    ]
    
    chapters = []
    for chapter_data in chapters_data:
        chapter = BookChapter(
            book_id=book.id,
            **chapter_data
        )
        db.add(chapter)
        chapters.append(chapter)
        print(f"✅ 创建章节: {chapter_data['title']}")
    
    db.commit()
    return book, chapters

def create_test_project(db: Session, book: Book):
    """创建测试项目"""
    
    # 检查是否已存在
    existing_project = db.query(NovelProject).filter(
        NovelProject.name == "环境音混合测试项目"
    ).first()
    if existing_project:
        print(f"项目 '环境音混合测试项目' 已存在，跳过创建")
        return existing_project
    
    project = NovelProject(
        name="环境音混合测试项目",
        book_id=book.id,
        description="测试环境音混合功能的项目，包含雨夜、森林、海边等多种场景",
        status="ready",
        total_chapters=3,
        total_segments=12,  # 预估段落数
        settings={
            "voice_settings": {
                "speed": 1.0,
                "pitch": 0.0,
                "volume": 0.8
            },
            "environment_settings": {
                "enable_environment": True,
                "environment_volume": 0.3,
                "auto_scene_detection": True
            },
            "output_format": "wav",
            "quality": "high"
        },
        created_by="test_user"
    )
    db.add(project)
    db.commit()
    return project

def create_test_analysis_result(db: Session, project: NovelProject, book: Book, chapters: list):
    """创建测试用的分析结果"""
    
    # 检查是否已存在
    existing_result = db.query(AnalysisResult).filter(
        AnalysisResult.project_id == project.id
    ).first()
    if existing_result:
        print(f"项目 {project.id} 的分析结果已存在，跳过创建")
        return existing_result
    
    # 准备合成计划
    synthesis_plan = {
        "segments": [
            # 第一章：雨夜古宅
            {
                "id": 1,
                "chapter_id": chapters[0].id,
                "text": "夜深人静，大雨如注。林雨推开古宅沉重的木门，门轴发出吱呀的声响。",
                "speaker": "旁白",
                "emotion": "neutral",
                "scene_info": {
                    "location": "古宅门口",
                    "weather": "大雨",
                    "time": "夜晚",
                    "atmosphere": "阴森"
                }
            },
            {
                "id": 2,
                "chapter_id": chapters[0].id,
                "text": "这里就是传说中的幽灵庄园吗？",
                "speaker": "林雨",
                "emotion": "curious",
                "scene_info": {
                    "location": "古宅大厅",
                    "weather": "大雨",
                    "time": "夜晚", 
                    "atmosphere": "紧张"
                }
            },
            {
                "id": 3,
                "chapter_id": chapters[0].id,
                "text": "闪电划过天空，照亮了客厅里积满灰尘的家具。雷声轰鸣，让人心跳加速。",
                "speaker": "旁白",
                "emotion": "dramatic",
                "scene_info": {
                    "location": "古宅客厅",
                    "weather": "雷雨",
                    "time": "夜晚",
                    "atmosphere": "惊悚"
                }
            },
            {
                "id": 4,
                "chapter_id": chapters[0].id,
                "text": "孩子，你终于来了。我等你很久了。",
                "speaker": "老管家",
                "emotion": "mysterious",
                "scene_info": {
                    "location": "古宅楼梯",
                    "weather": "雨",
                    "time": "夜晚",
                    "atmosphere": "神秘"
                }
            },
            
            # 第二章：森林追逐
            {
                "id": 5,
                "chapter_id": chapters[1].id,
                "text": "清晨的阳光透过茂密的森林洒下斑驳的光影。鸟儿在枝头欢快地歌唱，溪水潺潺流淌。",
                "speaker": "旁白",
                "emotion": "peaceful",
                "scene_info": {
                    "location": "森林",
                    "weather": "晴朗",
                    "time": "清晨",
                    "atmosphere": "宁静"
                }
            },
            {
                "id": 6,
                "chapter_id": chapters[1].id,
                "text": "驾！",
                "speaker": "陈剑",
                "emotion": "urgent",
                "scene_info": {
                    "location": "森林小径",
                    "weather": "晴朗", 
                    "time": "上午",
                    "atmosphere": "紧急"
                }
            },
            {
                "id": 7,
                "chapter_id": chapters[1].id,
                "text": "糟糕，狼群追上来了！",
                "speaker": "陈剑",
                "emotion": "worried",
                "scene_info": {
                    "location": "森林深处",
                    "weather": "晴朗",
                    "time": "上午",
                    "atmosphere": "危险"
                }
            },
            {
                "id": 8,
                "chapter_id": chapters[1].id,
                "text": "大哥哥，你在和小动物们玩游戏吗？",
                "speaker": "小女孩",
                "emotion": "innocent",
                "scene_info": {
                    "location": "森林空地",
                    "weather": "晴朗",
                    "time": "上午",
                    "atmosphere": "天真"
                }
            },
            
            # 第三章：海边重逢
            {
                "id": 9,
                "chapter_id": chapters[2].id,
                "text": "夕阳西下，海浪轻柔地拍打着沙滩。海鸥在空中盘旋，发出悠长的叫声。",
                "speaker": "旁白",
                "emotion": "romantic",
                "scene_info": {
                    "location": "海滩",
                    "weather": "晴朗",
                    "time": "黄昏",
                    "atmosphere": "浪漫"
                }
            },
            {
                "id": 10,
                "chapter_id": chapters[2].id,
                "text": "真美啊...",
                "speaker": "林雨",
                "emotion": "amazed",
                "scene_info": {
                    "location": "海边",
                    "weather": "晴朗",
                    "time": "黄昏",
                    "atmosphere": "感慨"
                }
            },
            {
                "id": 11,
                "chapter_id": chapters[2].id,
                "text": "我一直在找你。听说你来了海边，我就赶来了。",
                "speaker": "陈剑",
                "emotion": "gentle",
                "scene_info": {
                    "location": "海滩",
                    "weather": "晴朗",
                    "time": "黄昏",
                    "atmosphere": "温柔"
                }
            },
            {
                "id": 12,
                "chapter_id": chapters[2].id,
                "text": "看！海豚！",
                "speaker": "林雨",
                "emotion": "excited",
                "scene_info": {
                    "location": "海边",
                    "weather": "晴朗",
                    "time": "傍晚",
                    "atmosphere": "兴奋"
                }
            }
        ]
    }
    
    # 提取角色信息
    characters = [
        {
            "name": "林雨",
            "gender": "female",
            "age": "young",
            "personality": "温柔、好奇、勇敢",
            "voice_style": "gentle",
            "appearances": [1, 2, 9, 10, 12]
        },
        {
            "name": "陈剑", 
            "gender": "male",
            "age": "adult",
            "personality": "勇敢、稳重、温柔",
            "voice_style": "steady",
            "appearances": [5, 6, 7, 11]
        },
        {
            "name": "老管家",
            "gender": "male",
            "age": "senior",
            "personality": "神秘、智慧、苍老",
            "voice_style": "wise",
            "appearances": [4]
        },
        {
            "name": "小女孩",
            "gender": "female", 
            "age": "child",
            "personality": "天真、可爱、无邪",
            "voice_style": "cute",
            "appearances": [8]
        },
        {
            "name": "旁白",
            "gender": "neutral",
            "age": "adult",
            "personality": "客观、描述性",
            "voice_style": "narrative",
            "appearances": [1, 3, 5, 9]
        }
    ]
    
    analysis_result = AnalysisResult(
        project_id=project.id,
        book_id=book.id,
        analysis_type="intelligent_preparation",
        request_id=f"test_{project.id}_{int(datetime.now().timestamp())}",
        status="completed",
        result_data={
            "project_info": {
                "analysis_method": "test_data",
                "total_segments": len(synthesis_plan["segments"]),
                "total_characters": len(characters),
                "scene_count": 7,
                "estimated_duration": 380
            },
            "synthesis_plan": synthesis_plan,
            "characters": characters,
            "scenes": [
                {"location": "古宅", "weather": "雨夜", "atmosphere": "阴森神秘"},
                {"location": "森林", "weather": "晴朗", "atmosphere": "自然危险"},
                {"location": "海边", "weather": "黄昏", "atmosphere": "浪漫温馨"}
            ]
        },
        confidence_score=0.95,
        processing_time=120
    )
    db.add(analysis_result)
    db.commit()
    
    print(f"✅ 创建分析结果: {len(synthesis_plan['segments'])} 个段落")
    return analysis_result

async def main():
    """主函数"""
    print("🚀 开始创建环境音混合测试数据...")
    
    # 获取数据库连接
    db = next(get_db())
    
    try:
        # 1. 创建声音档案
        print("\n🎤 创建测试声音档案...")
        voice_profiles = create_test_voice_profiles(db)
        
        # 2. 创建书籍和章节
        print("\n📚 创建测试书籍和章节...")
        book, chapters = create_test_book_and_chapters(db)
        
        # 3. 创建项目
        print("\n🎬 创建测试项目...")
        project = create_test_project(db, book)
        
        # 4. 创建分析结果
        print("\n🧠 创建智能分析结果...")
        analysis_result = create_test_analysis_result(db, project, book, chapters)
        
        # 5. 记录系统日志
        await log_system_event(
            db=db,
            level="info",
            message="环境音混合测试数据创建完成",
            module="test_data",
            details={
                "project_id": project.id,
                "book_id": book.id,
                "chapters_count": len(chapters),
                "segments_count": 12,
                "characters_count": 5
            }
        )
        
        print("\n✅ 环境音混合测试数据创建完成！")
        print(f"📊 数据概览:")
        print(f"   - 项目ID: {project.id}")
        print(f"   - 书籍: {book.title}")
        print(f"   - 章节数: {len(chapters)} 个")
        print(f"   - 声音档案: {len(voice_profiles)} 个")
        print(f"   - 合成段落: 12 个")
        print(f"   - 测试场景: 雨夜古宅、森林追逐、海边重逢")
        
        print(f"\n🎯 测试说明:")
        print(f"   1. 访问前端合成中心: http://localhost:3000")
        print(f"   2. 选择项目 '环境音混合测试项目'")
        print(f"   3. 点击 '🌍 环境音混合' 按钮")
        print(f"   4. 配置环境音音量 (推荐 0.3)")
        print(f"   5. 开始测试智能合成")
        
        print(f"\n🎵 预期环境音效果:")
        print(f"   - 第1章: 雨声、雷声、古宅环境音")
        print(f"   - 第2章: 森林鸟叫、马蹄声、狼嚎声")
        print(f"   - 第3章: 海浪声、海鸥叫声、海风声")
        
    except Exception as e:
        print(f"❌ 创建测试数据失败: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main()) 