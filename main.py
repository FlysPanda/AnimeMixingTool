# -*- coding: utf-8 -*-

import os
import sys
import time
from pathlib import Path
from alive_progress import alive_bar
import mixing
import preprocessing


input_path = Path(input("请输入番剧目录：").strip())
output_root = Path("out")
mkvmerge = Path("mkvtoolnix/mkvmerge.exe")

if not mkvmerge.exists():
    print(f"错误: 找不到mkvmerge工具: {mkvmerge}")
    sys.exit(1)

# 预处理
mkvs = mixing.classify_files(mixing.get_all_files(input_path))[0]
subs_id = preprocessing.mkv_check(mkvs)
if subs_id == []:
    print(f"\n未在输入的mkv文件中发现字幕文件,即将开始混流...\n")
else:
    print(f"\n在输入的mkv文件中发现字幕文件,即将开始预处理...\n")
    time.sleep(2)
    try:
        preprocessing.processing(subs_id)
    except Exception as e:
        print(f"处理出错: {e}")
        sys.exit(1)
    
    print("\n预处理已完成,即将开始混流...\n")
    
time.sleep(2)

# 混流处理
try:
    is_multi, seasons = mixing.check_multiple_seasons(input_path)
except FileNotFoundError as e:
    print(e)
    sys.exit(1)

all_commands = []
try:
    if is_multi:
        for season in seasons:
            all_commands += mixing.process_season(season, input_path, output_root)
    else:
        all_commands = mixing.process_season(input_path, input_path, output_root)
except Exception as e:
    print(f"处理出错: {e}")
    sys.exit(1)

print(f"即将处理 {len(all_commands)} 个视频")
with alive_bar(len(all_commands)) as bar:
    for idx, cmd in enumerate(all_commands, 1):
        print(f"\n正在处理第 {idx} 个视频...")
        print("执行命令:", cmd)
        os.system(cmd)
        bar()
print("\n所有处理已完成！")