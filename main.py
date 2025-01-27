# -*- coding: utf8 -*-

import os
import sys
from alive_progress import alive_bar

#季数判断
def season_judge(path):
    file_exist = False
    dir_list = os.listdir(path)
    for dir in dir_list:
        if os.path.isfile(os.path.join(path, dir)):
            file_exist = True
    if file_exist == False:
        return True, dir_list
    else:
        return False, dir_list

#递归获取所有目录以及子目录下文件地址
def files_name_get(path):
    files_list = []
    for dirs,folders,files in os.walk(path):
        for file in files:
            files_list.append(os.path.join(dirs,file))

    return files_list

#文件分类
def files_extension_clas(path, files_list):
    formats = ['.mkv','.ass','.ssa','.srt','.ttf','.ttc','.otf','.fon']
    mkv = []
    subtitle = []
    font = []
    for format in formats:
        for files in files_list:
            file = os.path.split(files)[-1]
            if os.path.splitext(os.path.join(path, file))[-1].lower() == format:
                if format == '.mkv':
                    mkv.append(files)
                if format in ['.ass','.ssa','.srt']:
                    subtitle.append(files)
                if format in ['.ttf','.ttc','.otf','.fon']:
                    font.append(files)
    return mkv, subtitle, font

#执行混流(获取输出mkv的名称，判断单简体和简繁字幕，匹配视频及字幕文件，整合字体为命令，整合为命令)

#获取输出mkv的路径
def output_path_get(mkvs):
    output_mkv = []
    for i in mkvs:
        output_mkv.append("out\\" + os.path.split(i)[-1])
    return output_mkv

#判断单简体和简繁字幕
def subtitle_judge(mkvs, subtitles):
    num_mkv = len(mkvs)
    num_subtitle = len(subtitles)
    if num_subtitle == num_mkv:
        switch = 1
    elif num_subtitle == num_mkv*2:
        switch = 2
    else:
        print("字幕与mkv数量不匹配！请检查输入目录！")
        sys.exit(1)
    return switch

#匹配视频及字幕文件
def match_mkv_subtitle(switch, mkvs, subtitles):
    mkv_group = []
    #简繁字幕
    if switch == 2:
        index = 0
        for i in mkvs:
            index_sub1 = index * 2
            index_sub2 = index_sub1 + 1
            mkv_group.append([i, subtitles[index_sub1], subtitles[index_sub2]])
            index = index + 1
        
    #单简体字幕
    if switch == 1:
        index = 0
        for i in mkvs:
            mkv_group.append([i, subtitles[index]])
            index = index + 1
    return mkv_group

#整合字体为命令
def font_integration(fonts):
    fonts_command = ""
    for i in fonts:
        fonts_command = fonts_command + " " + "--attach-file " + "\"" + i + "\""
    return fonts_command

#整合为命令
def command_integration(mkv_group, output_path, fonts_command):
    command = []
    index = 0
    for i in mkv_group:
        command_tmp = ".\\mkvtoolnix\\mkvmerge.exe -o" + " " + "\"" + output_path[index] + "\""
        for files in i:
            command_tmp = command_tmp + " " + "\"" + files + "\""
        command_tmp = command_tmp + fonts_command
        command.append(command_tmp)
        index = index + 1
    return command
        
#执行命令
def execute_command(command):
    #创建alive_progress进度条
    with alive_bar(len(command)) as bar:
        
        #执行命令
        index = 1
        for i in command:
            print("正在混流第[" + str(index) + "]集" + "\n")
            result = os.system("\"" + i + "\"")
            print(result)
            print("\n")
            index = index + 1
            bar()

        

#path = input("请输入番剧目录")
path = "C:\\Users\\Fly__Panda\\Desktop\\[Nekomoe kissaten&VCB-Studio] Henjin no Salad Bowl [Ma10p_1080p]"
path = os.path.normpath(path)

multiple_season = season_judge(path)
if multiple_season[0]:
    season_dirs = multiple_season[1]
    multiple_season = multiple_season[0]
else:
    multiple_season = multiple_season[0]
    season_dirs = ""

#多季处理
if multiple_season:
    #文件地址获取
    files_list = []
    for dirs in season_dirs:
        files_list.append(files_name_get(os.path.join(path,dirs)))
    
    #文件分类
    classified_files = []
    for index, files in enumerate(files_list):
        classified_files.append(list(files_extension_clas(season_dirs[index], files)))
    
    #输出路径
    output_path = []
    for index, files in enumerate(classified_files):
        output = output_path_get(files[0])
        output_path_tmp = []
        for i in output:
            dir = os.path.split(i)[0]
            file = os.path.split(i)[1]
            output_path_tmp.append(os.path.join(dir, season_dirs[index], file))
        output_path.append(output_path_tmp)
    
    #字幕判断
    switch = []
    for files in classified_files:
        switch.append(subtitle_judge(files[0], files[1]))
    
    #视频字幕匹配
    mkv_group = []
    for index, files in enumerate(classified_files):
        mkv_group.append(match_mkv_subtitle(switch[index], files[0], files[1]))
    #字体命令整合
    font_command = []
    for files in classified_files:
        font_command.append(font_integration(files[2]))
    
    #命令整合
    command = []
    for index, files in enumerate(mkv_group):
        command = command + command_integration(files, output_path[index], font_command[index])
        
#单季处理
elif multiple_season == False:
    #文件地址获取
    files_list = files_name_get(path)
    #文件分类
    classified_files = files_extension_clas(path, files_list)
    #输出路径
    output_path = output_path_get(classified_files[0])
    #字幕判断
    switch = subtitle_judge(classified_files[0], classified_files[1])
    #视频字幕匹配
    mkv_group = match_mkv_subtitle(switch, classified_files[0], classified_files[1])
    #字体命令整合
    font_command = font_integration(classified_files[2])
    #命令整合
    command = command_integration(mkv_group, output_path, font_command)

execute_command(command)