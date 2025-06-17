import re

# 读取文件
with open('platform/backend/app/novel_reader.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 修复try语句内的缩进问题（在1779行左右）
lines = content.split('\n')
for i, line in enumerate(lines):
    if 'text = segment_data.get(' in line and line.startswith('                    '):
        # 从这一行开始到except之前，减少4个空格的缩进
        j = i
        while j < len(lines) and not (lines[j].strip().startswith('except Exception') and 'segment_index' in lines[j+1] if j+1 < len(lines) else False):
            if lines[j].startswith('                    '):  # 20个空格
                lines[j] = '                ' + lines[j][20:]  # 改为16个空格
            elif lines[j].startswith('                        '):  # 24个空格
                lines[j] = '                    ' + lines[j][24:]  # 改为20个空格
            elif lines[j].startswith('                            '):  # 28个空格或更多
                lines[j] = '                        ' + lines[j][28:]  # 改为24个空格
            j += 1
        break

# 写回文件
with open('platform/backend/app/novel_reader.py', 'w', encoding='utf-8') as f:
    f.write('\n'.join(lines))

print('缩进修复完成')