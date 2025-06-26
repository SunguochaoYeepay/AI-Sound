# 调试AnalysisResult模型的数据结构
from app.database import get_db
from app.models import NovelProject, BookChapter, AnalysisResult
import json

def debug_analysis_result():
    db = next(get_db())
    
    print("=== 调试AnalysisResult数据结构 ===")
    
    # 1. 获取项目34关联的AnalysisResult
    project = db.query(NovelProject).filter(NovelProject.id == 34).first()
    if not project:
        print("❌ 项目34不存在")
        return
    
    print(f"📋 项目: {project.name} (书籍ID: {project.book_id})")
    
    # 2. 获取章节和分析结果
    chapters = db.query(BookChapter).filter(BookChapter.book_id == project.book_id).all()
    
    for chapter in chapters:
        print(f"\n📖 章节: {chapter.chapter_title} (ID: {chapter.id})")
        
        if hasattr(chapter, 'analysis_results') and chapter.analysis_results:
            print(f"  分析结果数量: {len(chapter.analysis_results)}")
            
            for i, analysis in enumerate(chapter.analysis_results):
                print(f"\n  分析结果 {i+1} (ID: {analysis.id}):")
                print(f"    类型: {type(analysis)}")
                
                # 检查AnalysisResult的所有属性
                print(f"    属性列表:")
                for attr in dir(analysis):
                    if not attr.startswith('_') and not callable(getattr(analysis, attr)):
                        try:
                            value = getattr(analysis, attr)
                            if value is not None:
                                if isinstance(value, str) and len(value) > 100:
                                    print(f"      {attr}: [字符串，长度{len(value)}] {value[:50]}...")
                                else:
                                    print(f"      {attr}: {value}")
                        except Exception as e:
                            print(f"      {attr}: [获取失败: {e}]")
                
                # 特别检查可能的JSON字段
                for json_field in ['result', 'data', 'content', 'analysis_data', 'result_data']:
                    if hasattr(analysis, json_field):
                        field_value = getattr(analysis, json_field)
                        if field_value:
                            print(f"\n    🔍 检查JSON字段 '{json_field}':")
                            print(f"      类型: {type(field_value)}")
                            
                            if isinstance(field_value, str):
                                try:
                                    parsed = json.loads(field_value)
                                    print(f"      ✅ JSON解析成功，类型: {type(parsed)}")
                                    
                                    if isinstance(parsed, dict):
                                        print(f"      键: {list(parsed.keys())}")
                                        
                                        # 检查角色和段落数据
                                        if 'characters' in parsed:
                                            chars = parsed['characters']
                                            print(f"      🎭 角色数量: {len(chars) if hasattr(chars, '__len__') else '无法获取'}")
                                            if isinstance(chars, list) and chars:
                                                char = chars[0]
                                                print(f"      🎭 第一个角色: name={char.get('name')}, voice_id={char.get('voice_id')}")
                                        
                                        if 'segments' in parsed:
                                            segments = parsed['segments']
                                            print(f"      📝 段落数量: {len(segments) if hasattr(segments, '__len__') else '无法获取'}")
                                            if isinstance(segments, list) and segments:
                                                seg = segments[0]
                                                print(f"      📝 第一个段落: speaker={seg.get('speaker')}, voice_id={seg.get('voice_id')}")
                                                
                                except json.JSONDecodeError as e:
                                    print(f"      ❌ JSON解析失败: {e}")
                                except Exception as e:
                                    print(f"      ❌ 处理失败: {e}")
        else:
            print("  ❌ 无分析结果")

if __name__ == "__main__":
    debug_analysis_result()