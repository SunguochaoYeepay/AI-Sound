import sys
import os
from pathlib import Path

def tail(file_path, n=20):
    """读取文件最后n行"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return lines[-n:]

def main():
    log_dir = Path(__file__).parent / 'data' / 'logs'
    log_files = {
        '1': 'ai_sound_main.log',
        '2': 'ai_sound_errors.log',
        '3': 'websocket.log',
        '4': 'api_requests.log',
        '5': 'intelligent_analysis.log',
        '6': 'music_generation.log',
        '7': 'audio_processing.log',
        '8': 'database.log',
        '9': 'tts_voice.log',
        '10': 'environment_sounds.log',
        '11': 'background_music.log'
    }
    
    print("可用的日志文件：")
    for key, name in log_files.items():
        print(f"{key}: {name}")
    
    choice = input("\n请选择要查看的日志文件编号（默认1）：").strip() or '1'
    lines = input("要查看最后几行（默认20）：").strip() or '20'
    
    if choice in log_files:
        file_path = log_dir / log_files[choice]
        if file_path.exists():
            print(f"\n查看 {log_files[choice]} 的最后 {lines} 行：\n")
            for line in tail(file_path, int(lines)):
                print(line.strip())
        else:
            print(f"错误：找不到文件 {file_path}")
    else:
        print("错误：无效的选择")

if __name__ == '__main__':
    main() 