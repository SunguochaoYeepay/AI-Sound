# 调试智能准备结果的数据结构
from app.database import get_db
from app.models import NovelProject, BookChapter
import json

def debug_preparation_data():
    db = next(get_db())
    
    print("=== 调试项目34的智能准备结果数据结构 ===")
    
    # 1. 获取项目
    project = db.query(NovelProject).filter(NovelProject.id == 34).first()
    if not project:
        print("❌ 项目34不存在")
        return
    
    print(f"📋 项目信息:")
    print(f"  名称: {project.name}")
    print(f"  关联书籍: {project.book_id}")
    
    if not project.book_id:
        print("❌ 项目未关联书籍")
        return
    
    # 2. 检查章节的智能准备结果
    chapters = db.query(BookChapter).filter(BookChapter.book_id == project.book_id).all()
    print(f"\n📚 书籍章节信息:")
    print(f"  总章节数: {len(chapters)}")
    
    for i, chapter in enumerate(chapters):
        print(f"\n  章节 {i+1} (ID: {chapter.id}):")
        print(f"    标题: {chapter.chapter_title}")
        print(f"    analysis_results类型: {type(chapter.analysis_results)}")
        
        if chapter.analysis_results:
            # 检查数据类型
            if isinstance(chapter.analysis_results, str):
                print(f"    ✅ analysis_results是字符串，长度: {len(chapter.analysis_results)}")
                try:
                    data = json.loads(chapter.analysis_results)
                    print(f"    ✅ JSON解析成功，类型: {type(data)}")
                    
                    if isinstance(data, dict):
                        print(f"    📊 数据结构键: {list(data.keys())}")
                        
                        # 检查characters字段
                        if 'characters' in data:
                            characters = data['characters']
                            print(f"    🎭 角色数据类型: {type(characters)}")
                            print(f"    🎭 角色数量: {len(characters) if hasattr(characters, '__len__') else '无法获取长度'}")
                            
                            if isinstance(characters, list) and characters:
                                print(f"    🎭 第一个角色结构:")
                                first_char = characters[0]
                                print(f"      类型: {type(first_char)}")
                                if isinstance(first_char, dict):
                                    print(f"      键: {list(first_char.keys())}")
                                    print(f"      角色名: {first_char.get('name', '未知')}")
                                    print(f"      voice_id: {first_char.get('voice_id', '无')}")
                        
                        # 检查segments字段
                        if 'segments' in data:
                            segments = data['segments']
                            print(f"    📝 段落数据类型: {type(segments)}")
                            print(f"    📝 段落数量: {len(segments) if hasattr(segments, '__len__') else '无法获取长度'}")
                            
                            if isinstance(segments, list) and segments:
                                print(f"    📝 第一个段落结构:")
                                first_seg = segments[0]
                                print(f"      类型: {type(first_seg)}")
                                if isinstance(first_seg, dict):
                                    print(f"      键: {list(first_seg.keys())}")
                                    print(f"      speaker: {first_seg.get('speaker', '未知')}")
                                    print(f"      content: {first_seg.get('content', '')[:50]}...")
                                    print(f"      voice_id: {first_seg.get('voice_id', '无')}")
                    
                except json.JSONDecodeError as e:
                    print(f"    ❌ JSON解析失败: {e}")
                except Exception as e:
                    print(f"    ❌ 处理失败: {e}")
                    
            elif isinstance(chapter.analysis_results, list):
                print(f"    ⚠️ analysis_results是列表，长度: {len(chapter.analysis_results)}")
                if chapter.analysis_results:
                    print(f"    第一个元素类型: {type(chapter.analysis_results[0])}")
                    
            else:
                print(f"    ❌ analysis_results类型异常: {type(chapter.analysis_results)}")
        else:
            print(f"    ❌ 无analysis_results数据")

if __name__ == "__main__":
    debug_preparation_data()