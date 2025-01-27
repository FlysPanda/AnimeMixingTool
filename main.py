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
def files_name_get(path, multiple_season, season_dirs):
    files_list = []
    #多季文件地址获取
    if multiple_season == True:
        for season_dir in season_dirs:
            season_files_list = []
            for dirs,folders,files in os.walk(os.path.join(path, season_dir)):   
                for file in files:
                    season_files_list.append(os.path.join(dirs,file))
            files_list.append(season_files_list)
    
    #单季文件地址获取
    elif multiple_season == False:
        for dirs,folders,files in os.walk(path):
            for file in files:
                files_list.append(os.path.join(dirs,file))

    return files_list

#文件分类
def files_extension_clas(path, files_list, multiple_season):
    formats = ['.mkv','.ass','.ssa','.srt','.ttf','.ttc','.otf','.fon']
    mkv = []
    subtitle = []
    font = []
    if multiple_season:
        for season_files in files_list:
            season_mkv = []
            season_subtitle = []
            season_font = []
            for format in formats:
                for files in season_files:
                    file = os.path.split(files)[-1]
                    if os.path.splitext(files)[-1].lower() == format:
                        if format == '.mkv':
                            season_mkv.append(files)
                        if format in ['.ass','.ssa','.srt']:
                            season_subtitle.append(files)
                        if format in ['.ttf','.ttc','.otf','.fon']:
                            season_font.append(files)
            mkv.append(season_mkv)
            subtitle.append(season_subtitle)
            font.append(season_font)
    else:
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
def mkv_mix(mkvs, subtitles, fonts, multiple_season, season_dirs):
    output_mkv_name = []
    mkv_group = []
    command = []
    
    #多季输出路径
    if multiple_season:
        index = 0
        for mkv in mkvs:
            output_mkv_name_tmp = []
            for i in mkv:
                output_mkv_name_tmp.append("out\\"+ season_dirs[index] + "\\" + os.path.split(i)[-1])
            index = index + 1
            output_mkv_name.append(output_mkv_name_tmp)
            
        #判断每季单简体和简繁字幕
        switch = []
        for i in range(len(mkvs)):
            num_mkv = len(mkvs[i])
            num_subtitle = len(subtitles[i])
            if num_subtitle == num_mkv:
                switch_tmp = 1
            elif num_subtitle == num_mkv*2:
                switch_tmp = 2
            else:
                print("字幕与mkv数量不匹配！请检查输入目录！")
                sys.exit(1)
            switch.append(switch_tmp)
        
        #整合字体为命令
        fonts_command = []
        for font in fonts:
            fonts_command_tmp = ""
            for i in font:
                fonts_command_tmp = fonts_command_tmp + " " + "--attach-file " + "\"" + i + "\""
            fonts_command.append(fonts_command_tmp)
        
        #匹配视频及字幕文件
        index_switch = 0
        for i in switch:
            mkv_group_tmp = []
            #匹配视频及字幕文件(简繁字幕)
            if i == 2:
                index = 0
                for n in range(len(mkvs[index_switch])):
                    index_sub1 = index * 2
                    index_sub2 = index_sub1 + 1
                    mkv_group_tmp.append([mkvs[index_switch][n], subtitles[index_switch][index_sub1], subtitles[index_switch][index_sub2]])
                    index = index + 1
                index_switch = index_switch + 1
            #匹配视频及字幕文件(单简体字幕)
            if i == 1:
                index = 0
                for n in range(len(mkvs[index_switch])):
                    mkv_group_tmp.append([mkvs[index_switch][n], subtitles[index_switch][index]])
                    index = index + 1
                index_switch = index_switch + 1
            mkv_group.append(mkv_group_tmp)
        #整合为命令(未完成)
        season_index = 0
        for mkv in mkv_group:
            index = 0
            for i in mkv:
                command_tmp = ".\\mkvtoolnix\\mkvmerge.exe -o" + " " + "\"" + output_mkv_name[season_index][index] + "\""
                for file in i:
                    command_tmp = command_tmp + " " + "\"" + file + "\""
                command_tmp = command_tmp + fonts_command[season_index]
                command.append(command_tmp)
                index = index + 1
            season_index =season_index + 1
            
    else: 
        #获取输出mkv的路径
        for i in mkvs:
            output_mkv_name.append("out\\" + os.path.split(i)[-1])
        
        #判断单简体和简繁字幕
        num_mkv = len(mkvs)
        num_subtitle = len(subtitles)
        if num_subtitle == num_mkv:
            switch = 1
        elif num_subtitle == num_mkv*2:
            switch = 2
        else:
            print("字幕与mkv数量不匹配！请检查输入目录！")
            sys.exit(1)
    
        #整合字体为命令
        fonts_command = ""
        for i in fonts:
            fonts_command = fonts_command + " " + "--attach-file " + "\"" + i + "\""
            
        #整合为命令
        index = 0
        for i in mkv_group:
            command_tmp = ".\\mkvtoolnix\\mkvmerge.exe -o" + " " + "\"" + output_mkv_name[index] + "\""
            for files in i:
                file = files
                command_tmp = command_tmp + " " + "\"" + file + "\""
            command_tmp = command_tmp + fonts_command
            command.append(command_tmp)
            index = index + 1
        
        #匹配视频及字幕文件(简繁字幕)
        if switch == 2:
            index = 0
            for i in mkvs:
                index_sub1 = index * 2
                index_sub2 = index_sub1 + 1
                mkv_group.append([i, subtitles[index_sub1], subtitles[index_sub2]])
                index = index + 1
            
        #匹配视频及字幕文件(单简体字幕)
        if switch == 1:
            index = 0
            for i in mkvs:
                mkv_group.append([i, subtitles[index]])
                index = index + 1
        
        #整合字体为命令
        fonts_command = ""
        for i in fonts:
            fonts_command = fonts_command + " " + "--attach-file " + "\"" + i + "\""
    
        #整合为命令
        index = 0
        for i in mkv_group:
            command_tmp = ".\\mkvtoolnix\\mkvmerge.exe -o" + " " + "\"" + output_mkv_name[index] + "\""
            for files in i:
                file = files
                command_tmp = command_tmp + " " + "\"" + file + "\""
            command_tmp = command_tmp + fonts_command
            command.append(command_tmp)
            index = index + 1
    #创建alive_progress进度条
    with alive_bar(len(command)) as bar:
        
        #执行命令
        index = 1
        for i in command:
            print("正在混流第[" + str(index) + "]个")
            result = os.system("\"" + i + "\"")
            print(result)
            print("\n")
            index = index + 1
            bar()
        

path = input("请输入番剧目录")
path = os.path.normpath(path)
multiple_season = season_judge(path)
if multiple_season[0]:
    season_dirs = multiple_season[1]
    multiple_season = multiple_season[0]
else:
    multiple_season = multiple_season[0]
    season_dirs = ""

files_list = files_name_get(path, multiple_season,season_dirs)
files = files_extension_clas(path, files_list, multiple_season)

mkv_mix(files[0], files[1], files[2], multiple_season, season_dirs)

