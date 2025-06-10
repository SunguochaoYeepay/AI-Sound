#!/usr/bin/env python3
"""
初始化AI-Sound平台示例数据
在后端环境中运行，使用SQLAlchemy模型
"""

import asyncio
import json
import sys
import os

# 添加app目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database import engine, get_db
from app.models import Base, Book, BookChapter, VoiceProfile, NovelProject
from datetime import datetime

def init_sample_data():
    """初始化示例数据"""
    
    try:
        # 创建数据库表
        Base.metadata.create_all(bind=engine)
        print("✅ 数据库表创建完成")
        
        # 获取数据库会话
        db = Session(bind=engine)
        
        # 示例书籍数据
        sample_books = [
            {
                'title': '西游记（节选）',
                'author': '吴承恩',
                'description': '中国古典四大名著之一，描述孙悟空等师徒四人西天取经的故事',
                'content': '''第一回 灵根育孕源流出 心性修持大道生

诗曰：
混沌未分天地乱，茫茫渺渺无人见。
自从盘古破鸿蒙，开辟从兹清浊辨。
覆载群生仰至仁，发明万物皆成善。
欲知造化会元功，须看西游释厄传。

盖闻天地之数，有十二万九千六百岁为一元。将一元分为十二会，乃子、丑、寅、卯、辰、巳、午、未、申、酉、戌、亥之十二支也。

第二回 悟彻菩提真妙理 断魔归本合元神

话说美猴王得了姓名，怡然踊跃，对菩提前作礼启谢。那祖师即命大众引悟空到二门之外，教他洒扫应对，进退周旋之节。众仙奉命而出。悟空到门外，又拜了大众师兄，就于廊庑之间，安排寝处。次早起来，与众师兄学言语礼貌、讲经论道、习字焚香、每日如此。闲时即扫地锄园、养花修树、寻柴燃火、挑水运浆。凡所用之物，无一不备。在洞中不觉倏忽六七年。

"悟空，你在这里学些什么道理？"祖师问道。

悟空道："弟子时常听讲，也颇知些。"

"既如此，你再上前来，我教你个长生之道如何？"

悟空闻言，叩头谢恩道："愿老爷传授。"''',
                'tags': ['古典小说', '神话', '冒险'],
                'status': 'published',
                'source_file_name': 'xiyouji_sample.txt'
            },
            {
                'title': '现代都市小说（示例）',
                'author': '网络作家',
                'description': '现代都市背景的恋爱小说示例',
                'content': '''第一章 初遇

秋日的午后，阳光透过法国梧桐的叶子洒在人行道上，形成斑驳的光影。

"对不起！"林晚匆忙地收拾着散落一地的文件。

"没关系。"一个温和的男声响起。

林晚抬起头，看到一张轮廓分明的脸庞，深邃的眼眸中带着关切。

"让我帮你吧。"陈默蹲下身，帮她捡起文件。

"谢谢。"林晚脸颊微红，"我叫林晚。"

"陈默。"他伸出手，"很高兴认识你。"

第二章 重逢

三天后，咖啡厅里。

"真的是你！"林晚惊喜地看着坐在角落的陈默。

陈默抬起头，眼中闪过一丝惊喜："这么巧？"

"是啊，我经常来这里。"林晚端着咖啡走向他的桌子，"可以坐下吗？"

"当然。"陈默起身为她拉开椅子。

"你也喜欢这里的环境吗？"林晚问道。

"是的，安静，适合思考。"陈默点点头，"你呢？工作很忙吗？"

"还好，就是偶尔会有些紧急的项目。"林晚笑了笑，"像那天一样。"

两人都笑了起来，气氛变得轻松愉快。''',
                'tags': ['都市', '爱情', '现代'],
                'status': 'published', 
                'source_file_name': 'modern_romance_sample.txt'
            }
        ]

        # 插入书籍数据
        book_objects = []
        for book_data in sample_books:
            # 计算字数
            word_count = len(book_data['content'].replace(' ', '').replace('\n', ''))
            
            book = Book()
            book.title = book_data['title']
            book.author = book_data['author']
            book.description = book_data['description']
            book.content = book_data['content']
            book.status = book_data['status']
            book.word_count = word_count
            book.source_file_name = book_data['source_file_name']
            book.created_at = datetime.now()
            book.updated_at = datetime.now()
            book.tags = json.dumps(book_data['tags'], ensure_ascii=False)
            
            db.add(book)
            book_objects.append(book)

        db.commit()
        
        # 刷新book对象以获取ID
        for book in book_objects:
            db.refresh(book)
        print(f"✅ 已插入 {len(sample_books)} 本示例书籍")
        
        # 为每本书创建章节数据
        for i, book in enumerate(book_objects):
            content = sample_books[i]['content']
            
            # 简单的章节分割逻辑
            chapters = []
            lines = content.split('\n')
            current_chapter = None
            chapter_content = []
            chapter_number = 0
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                    
                # 检测章节标题
                if line.startswith('第') and ('回' in line or '章' in line):
                    # 保存上一章节
                    if current_chapter and chapter_content:
                        chapter_text = '\n'.join(chapter_content)
                        chapter_obj = BookChapter(
                            book_id=book.id,
                            chapter_number=chapter_number,
                            title=current_chapter,
                            content=chapter_text,
                            word_count=len(chapter_text.replace(' ', '').replace('\n', '')),
                            character_count=len(chapter_text),
                            created_at=datetime.now(),
                            updated_at=datetime.now()
                        )
                        db.add(chapter_obj)
                        chapters.append({
                            'number': chapter_number,
                            'title': current_chapter,
                            'wordCount': len(chapter_text.replace(' ', '').replace('\n', ''))
                        })
                    
                    # 开始新章节
                    chapter_number += 1
                    current_chapter = line
                    chapter_content = []
                else:
                    chapter_content.append(line)
            
            # 保存最后一章
            if current_chapter and chapter_content:
                chapter_text = '\n'.join(chapter_content)
                chapter_obj = BookChapter(
                    book_id=book.id,
                    chapter_number=chapter_number,
                    title=current_chapter,
                    content=chapter_text,
                    word_count=len(chapter_text.replace(' ', '').replace('\n', '')),
                    character_count=len(chapter_text),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(chapter_obj)
                chapters.append({
                    'number': chapter_number,
                    'title': current_chapter,
                    'wordCount': len(chapter_text.replace(' ', '').replace('\n', ''))
                })
            
            # 更新书籍的章节信息
            book.set_chapters(chapters)
            book.chapter_count = len(chapters)
            
            print(f"  📖 《{book.title}》: {len(chapters)} 个章节")

        db.commit()

        # 创建示例声音配置
        sample_voices = [
            {
                'name': '温柔女声',
                'description': '温柔甜美的女性声音，适合女主角和旁白',
                'type': 'female',
                'color': '#ff69b4',
                'tags': ['温柔', '甜美', '女性'],
                'parameters': {"timeStep": 20, "pWeight": 1.0, "tWeight": 1.0}
            },
            {
                'name': '磁性男声',
                'description': '低沉磁性的男性声音，适合男主角',
                'type': 'male',
                'color': '#4169e1',
                'tags': ['磁性', '低沉', '男性'],
                'parameters': {"timeStep": 25, "pWeight": 1.2, "tWeight": 0.8}
            },
            {
                'name': '活泼少女',
                'description': '青春活泼的少女声音',
                'type': 'female',
                'color': '#ffa500',
                'tags': ['活泼', '青春', '少女'],
                'parameters': {"timeStep": 18, "pWeight": 0.9, "tWeight": 1.1}
            },
            {
                'name': '沉稳长者',
                'description': '沉稳威严的长者声音，适合师父等角色',
                'type': 'male',
                'color': '#8b4513',
                'tags': ['沉稳', '威严', '长者'],
                'parameters': {"timeStep": 30, "pWeight": 1.3, "tWeight": 0.7}
            }
        ]

        for voice_data in sample_voices:
            voice = VoiceProfile(
                name=voice_data['name'],
                description=voice_data['description'],
                type=voice_data['type'],
                color=voice_data['color'],
                created_at=datetime.now(),
                updated_at=datetime.now()
            )
            voice.set_tags(voice_data['tags'])
            voice.set_parameters(voice_data['parameters'])
            db.add(voice)

        db.commit()
        print(f"✅ 已创建 {len(sample_voices)} 个示例声音配置")

        # 创建示例项目
        for book in book_objects:
            project_name = f"《{book.title}》朗读项目"
            project = NovelProject(
                name=project_name,
                description=f"基于《{book.title}》的语音合成项目",
                book_id=book.id,
                status='pending',
                created_at=datetime.now()
            )
            db.add(project)
            
        db.commit()
        print(f"✅ 已创建 {len(book_objects)} 个示例项目")

        print("\n🎉 示例数据初始化完成！")
        
        # 显示数据统计
        book_count = db.query(Book).count()
        chapter_count = db.query(BookChapter).count()
        voice_count = db.query(VoiceProfile).count()
        project_count = db.query(NovelProject).count()
        
        print(f"""
📊 数据库统计:
   📚 书籍: {book_count} 本
   📄 章节: {chapter_count} 个  
   🎵 声音配置: {voice_count} 个
   🎬 项目: {project_count} 个
        """)
        
        return True
        
    except Exception as e:
        print(f"❌ 初始化数据时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        if 'db' in locals():
            db.rollback()
        return False
    finally:
        if 'db' in locals():
            db.close()

if __name__ == "__main__":
    success = init_sample_data()
    sys.exit(0 if success else 1) 