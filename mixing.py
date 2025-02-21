# -*- coding: utf-8 -*-
"""混流模块"""

import os
import sys
from pathlib import Path
from enum import Enum
from typing import List, Tuple, Optional
from alive_progress import alive_bar

class SubtitleMode(Enum):
    SINGLE = 1
    DOUBLE = 2

def check_multiple_seasons(path: Path) -> Tuple[bool, List[Path]]:
    """
    检查目录结构是否包含多季内容
    Returns: (是否多季, 子目录列表)
    """
    if not path.exists():
        raise FileNotFoundError(f"目录不存在: {path}")

    has_files = any(child.is_file() for child in path.iterdir())
    dirs = [child for child in path.iterdir() if child.is_dir()]
    return (not has_files and len(dirs) > 0, dirs)

def get_all_files(path: Path) -> List[Path]:
    """递归获取目录下所有文件"""
    return [p for p in path.rglob('*') if p.is_file() and p.suffix]

def classify_files(files: List[Path]) -> Tuple[List[Path], List[Path], List[Path]]:
    """分类文件类型"""
    video_ext = {'.mkv'}
    sub_ext = {'.ass', '.ssa', '.srt'}
    font_ext = {'.ttf', '.ttc', '.otf', '.fon'}

    videos, subs, fonts = [], [], []
    for f in files:
        ext = f.suffix.lower()
        if ext in video_ext:
            videos.append(f)
        elif ext in sub_ext:
            subs.append(f)
        elif ext in font_ext:
            fonts.append(f)
    return videos, subs, fonts

def validate_subtitles(video_count: int, sub_count: int) -> SubtitleMode:
    """验证字幕数量有效性"""
    if sub_count == video_count:
        return SubtitleMode.SINGLE
    if sub_count == video_count * 2:
        return SubtitleMode.DOUBLE
    raise ValueError(f"字幕数量{sub_count}与视频数量{video_count}不匹配")

def generate_output_paths(videos: List[Path], base_path: Path, output_root: Path) -> List[Path]:
    """生成输出路径"""
    return [output_root / v.relative_to(base_path.parent) for v in videos]

def build_command(mkv: Path, subs: List[Path], fonts: List[Path], output: Path) -> str:
    """构建命令行字符串（带自动转义处理）"""
    def escape_path(p: Path) -> str:
        # 处理Windows路径空格和特殊符号
        return f'"{str(p.resolve())}"'

    cmd_parts = [
        'mkvtoolnix\mkvmerge.exe',
        '-o', escape_path(output),
        escape_path(mkv)
    ]
    
    # 添加字幕文件
    simple = {".sc", ".chs"}
    for s in subs:
        tmp = Path(s.stem)
        lang = tmp.suffix.lower()
        if lang in simple:
            cmd =[
                "--language 0:zh-Hans", 
                "--track-name \"0:简体中文\"", 
                "\"(\"",
                escape_path(s),
                "\")\""
            ]
        else:
            cmd =[
                "--language 0:zh-Hant", 
                "--track-name \"0:繁體中文\"", 
                "\"(\"",
                escape_path(s),
                "\")\""
            ]
        cmd_parts.extend(cmd)
    
    # 添加字体文件参数
    for font in fonts:
        cmd_parts.append('--attach-file')
        cmd_parts.append(escape_path(font))
    
    output.parent.mkdir(parents=True, exist_ok=True)
    return ' '.join(cmd_parts)

def process_season(season_path: Path, base_path: Path, output_root: Path) -> List[str]:
    """处理单个季"""
    files = get_all_files(season_path)
    videos, subs, fonts = classify_files(files)
    
    if not videos:
        raise ValueError(f"未找到视频文件: {season_path}")

    try:
        sub_mode = validate_subtitles(len(videos), len(subs))
    except ValueError as e:
        print(f"错误: {e}")
        sys.exit(1)

    sub_groups = []
    for i, video in enumerate(videos):
        if sub_mode == SubtitleMode.DOUBLE:
            sub_groups.append(subs[i*2:i*2+2])
        else:
            sub_groups.append([subs[i]])

    output_paths = generate_output_paths(videos, base_path, output_root)
    return [build_command(v, s, fonts, o) for v, s, o in zip(videos, sub_groups, output_paths)]

def main():
    input_path = Path(input("请输入番剧目录：").strip())
    output_root = Path("out")
    mkvmerge = Path("mkvtoolnix/mkvmerge.exe")

    if not mkvmerge.exists():
        print(f"错误: 找不到mkvmerge工具: {mkvmerge}")
        sys.exit(1)

    try:
        is_multi, seasons = check_multiple_seasons(input_path)
    except FileNotFoundError as e:
        print(e)
        sys.exit(1)

    all_commands = []
    try:
        if is_multi:
            for season in seasons:
                all_commands += process_season(season, input_path, output_root)
        else:
            all_commands = process_season(input_path, input_path, output_root)
    except Exception as e:
        print(f"处理出错: {e}")
        sys.exit(1)

    print(f"\n即将处理 {len(all_commands)} 个视频")
    with alive_bar(len(all_commands)) as bar:
        for idx, cmd in enumerate(all_commands, 1):
            print(f"正在处理第 {idx} 个视频...")
            os.system(cmd)
            bar()
    print("\n所有处理已完成！")

if __name__ == "__main__":
    main()