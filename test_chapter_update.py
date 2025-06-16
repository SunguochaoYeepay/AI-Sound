#!/usr/bin/env python3
"""
测试章节标题更新功能
"""

import requests
import json

BASE_URL = "http://localhost:8000/api/v1"

def test_chapter_title_update():
    """测试章节标题更新"""
    print("=== 测试章节标题更新功能 ===")
    
    # 1. 获取一个书籍的章节
    try:
        books_response = requests.get(f"{BASE_URL}/books")
        if books_response.status_code != 200:
            print("无法获取书籍列表")
            return
        
        books_data = books_response.json()
        if not books_data.get('success') or not books_data.get('data'):
            print("没有可用的书籍")
            return
        
        book_id = books_data['data'][0]['id']
        print(f"使用书籍ID: {book_id}")
        
        # 2. 获取章节列表
        chapters_response = requests.get(f"{BASE_URL}/chapters?book_id={book_id}")
        if chapters_response.status_code != 200:
            print("无法获取章节列表")
            return
        
        chapters_data = chapters_response.json()
        if not chapters_data.get('success') or not chapters_data.get('data'):
            print("没有可用的章节")
            return
        
        chapter = chapters_data['data'][0]
        chapter_id = chapter['id']
        original_title = chapter['chapter_title']
        print(f"测试章节ID: {chapter_id}")
        print(f"原始标题: {original_title}")
        
        # 3. 更新章节标题
        new_title = f"更新测试标题_{chapter_id}"
        update_data = {
            'title': new_title
        }
        
        update_response = requests.patch(f"{BASE_URL}/chapters/{chapter_id}", data=update_data)
        print(f"更新API状态: {update_response.status_code}")
        
        if update_response.status_code == 200:
            update_result = update_response.json()
            if update_result.get('success'):
                updated_chapter = update_result.get('data', {})
                updated_title = updated_chapter.get('chapter_title')
                print(f"✓ 更新成功！新标题: {updated_title}")
                
                # 4. 验证更新结果
                if updated_title == new_title:
                    print("✓ 标题更新验证通过")
                else:
                    print(f"✗ 标题更新验证失败: 期望 '{new_title}', 实际 '{updated_title}'")
                
                # 5. 再次获取章节详情确认
                detail_response = requests.get(f"{BASE_URL}/chapters/{chapter_id}")
                if detail_response.status_code == 200:
                    detail_data = detail_response.json()
                    if detail_data.get('success'):
                        detail_chapter = detail_data.get('data', {})
                        final_title = detail_chapter.get('chapter_title')
                        print(f"最终确认标题: {final_title}")
                        
                        if final_title == new_title:
                            print("✓ 章节标题更新功能正常")
                        else:
                            print(f"✗ 最终验证失败: 期望 '{new_title}', 实际 '{final_title}'")
                    else:
                        print("获取章节详情失败")
                else:
                    print(f"获取章节详情API失败: {detail_response.status_code}")
                
            else:
                print(f"更新失败: {update_result}")
        else:
            print(f"更新API请求失败: {update_response.status_code}")
            print(f"响应内容: {update_response.text}")
            
    except Exception as e:
        print(f"测试过程出错: {str(e)}")

if __name__ == "__main__":
    test_chapter_title_update() 