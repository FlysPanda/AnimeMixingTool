# -*- coding: utf-8 -*-
"""预处理模块"""

import time
import subprocess
import json
from pathlib import Path
from alive_progress import alive_bar

def mkv_check(mkvs: list[Path]):
    """检查输入mkv中是否含有字幕文件"""
    results = []
    subs_id = []
    mkvmerge = Path("mkvtoolnix/mkvmerge.exe")
    cmds = (str(mkvmerge) + " -F json -i " + "\"" + str(mkv) + "\"" for mkv in mkvs)
    for cmd in cmds:
        complete = subprocess.run(
            cmd, 
            stdout=subprocess.PIPE, 
            text=True, 
            shell=False, 
            encoding="utf-8"
        )
        results.append(complete.stdout)
    
    for result in results:
        sub_id = []
        js = json.loads(result)
        tracks = js["tracks"]
        for track in tracks:
            if track["type"] == "subtitles":
                sub_id.append(js["file_name"])
                sub_id.append(track["id"])
        if sub_id != []:
            subs_id.append(sub_id)
    return subs_id

def processing(subs_id: list[str]):
    """将输入mkv中的字幕文件改为非默认轨道"""
    mkvs = []
    with alive_bar(len(subs_id)) as bar:
        for sub_id in subs_id:
            mkv = sub_id[0]
            mkvs.append(mkv)
            sub_id.remove(mkv)
            mkv = Path(mkv)
            cmd = ["./mkvtoolnix/mkvmerge.exe", "-o", str(Path(mkv.parent, "Processed", mkv.name))]
            for id in sub_id:
                cmd.append("--default-track-flag")
                tmp = str(id) + ":no"
                cmd.append(tmp)
            cmd.append(mkv)
            subprocess.run(
                cmd,
                text= True,
                shell= False, 
                encoding="utf-8"
            )
            bar()
    # 将处理好的文件从Processed文件夹移到原文件夹
    for mkv in mkvs:
        mkv = Path(mkv)
        completed_mkv = Path(mkv.parent, "Processed", mkv.name)
        completed_mkv.replace(mkv)
        try:
            completed_mkv.parent.rmdir()
        except WindowsError:
            pass
    
    

if __name__ == "__main__":
    import mixing
    input_path = Path(input("请输入番剧目录：").strip())
    mkvs = mixing.classify_files(mixing.get_all_files(input_path))[0]
    processing(mkv_check(mkvs))