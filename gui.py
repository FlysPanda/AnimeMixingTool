import wx
import time
import threading
import shutil 
import subprocess
from pathlib import Path
import mixing
import preprocessing

class MediaMixerApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame()
        self.frame.Show()
        return True

class MainFrame(wx.Frame):
    path = ""
    def __init__(self):
        wx.Frame.__init__(self, None, title="番剧混流工具", size=(1000, 750))
        self.SetMinSize((800, 600))  # 设置最小窗口尺寸
        
        # 初始化界面
        self.init_ui()
        self.setup_icon()
        
        # 状态变量
        self.is_processing = False
        self.current_progress = 0

    def init_ui(self):
        # 主面板
        panel = wx.Panel(self)
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 目录选择区域
        dir_sizer = self.create_dir_selector(panel)
        main_sizer.Add(dir_sizer, 0, wx.EXPAND|wx.ALL, 15)

        # 控制按钮区域
        btn_sizer = self.create_control_buttons(panel)
        main_sizer.Add(btn_sizer, 0, wx.CENTER|wx.BOTTOM, 15)

        # 进度条区域
        progress_sizer = self.create_progress_bar(panel)
        main_sizer.Add(progress_sizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 15)

        # 日志输出区域
        log_sizer = self.create_log_panel(panel)
        main_sizer.Add(log_sizer, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.BOTTOM, 15)

        panel.SetSizer(main_sizer)
        self.Centre()

    def setup_icon(self):
        """设置应用程序图标"""
        try:
            # 优先尝试加载外部图标文件
            self.SetIcon(wx.Icon("res/favicon.ico", wx.BITMAP_TYPE_PNG))
        except Exception as e:
            print("图标加载失败:", str(e))

    def create_dir_selector(self, panel):
        """创建目录选择组件"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # 标签
        lbl = wx.StaticText(panel, label="番剧目录：")
        sizer.Add(lbl, 0, wx.ALIGN_CENTER_VERTICAL|wx.RIGHT, 10)

        # 路径显示框
        self.txt_dir = wx.TextCtrl(panel)
        sizer.Add(self.txt_dir, 1, wx.EXPAND|wx.RIGHT, 10)

        # 选择按钮
        btn_choose = wx.Button(panel, label="选择目录...", size=(120, 30))
        btn_choose.Bind(wx.EVT_BUTTON, self.on_choose_dir)
        sizer.Add(btn_choose, 0)

        return sizer

    def create_control_buttons(self, panel):
        """创建控制按钮"""
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.btn_start = wx.Button(panel, label="开始混流", size=(150, 40))
        self.btn_start.Bind(wx.EVT_BUTTON, self.on_start)
        sizer.Add(self.btn_start, 0, wx.RIGHT, 10)

        self.btn_cancel = wx.Button(panel, label="取消操作", size=(150, 40))
        self.btn_cancel.Bind(wx.EVT_BUTTON, self.on_cancel)
        self.btn_cancel.Disable()
        sizer.Add(self.btn_cancel, 0)

        return sizer

    def create_progress_bar(self, panel):
        """创建进度条组件"""
        sizer = wx.BoxSizer(wx.VERTICAL)
        
        # 进度文本
        self.lbl_status = wx.StaticText(panel, label="准备就绪")
        sizer.Add(self.lbl_status, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.BOTTOM, 5)

        # 进度条
        self.gauge = wx.Gauge(panel, range=100, style=wx.GA_HORIZONTAL|wx.GA_SMOOTH)
        self.gauge.SetMinSize((-1, 25))
        sizer.Add(self.gauge, 0, wx.EXPAND)

        # 百分比显示
        self.lbl_percent = wx.StaticText(panel, label="0%")
        sizer.Add(self.lbl_percent, 0, wx.ALIGN_CENTER|wx.TOP, 5)

        return sizer

    def create_log_panel(self, panel):
        """创建日志面板"""
        box = wx.StaticBox(panel, label="操作日志")
        sizer = wx.StaticBoxSizer(box, wx.VERTICAL)
        
        self.log_text = wx.TextCtrl(
            panel, 
            style=wx.TE_MULTILINE|wx.TE_READONLY|wx.HSCROLL|wx.TE_RICH
        )
        # 设置等宽字体
        font = wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL)
        self.log_text.SetFont(font)
        
        sizer.Add(self.log_text, 1, wx.EXPAND|wx.ALL, 5)
        return sizer

    def on_choose_dir(self, event):
        """目录选择事件处理"""
        dlg = wx.DirDialog(
            self,
            "选择番剧目录",
            style=wx.DD_DEFAULT_STYLE|wx.DD_DIR_MUST_EXIST
        )
        
        if dlg.ShowModal() == wx.ID_OK:
            path = dlg.GetPath()
            self.path = Path(path)
            self.txt_dir.SetValue(path)
            self.log(f"已选择目录：{path}")
        
        dlg.Destroy()

    def on_start(self, event):
        """开始处理事件"""
        if self.is_processing:
            wx.MessageBox("当前已有任务正在运行！", "提示", wx.OK|wx.ICON_INFORMATION)
            return
            
        if not self.txt_dir.GetValue():
            wx.MessageBox("请先选择番剧目录！", "错误", wx.OK|wx.ICON_ERROR)
            return
            
        self.start_processing()

    def on_cancel(self, event):
        """取消操作事件"""
        self.is_processing = False
        self.log("操作已被用户取消")
        self.update_ui_state(False)

    def start_processing(self):
        """启动处理流程"""
        self.is_processing = True
        self.current_progress = 0
        self.gauge.SetValue(0)
        self.lbl_percent.SetLabel(f"{0}%")
        self.update_ui_state(True)
        
        # 启动后台线程
        worker = threading.Thread(target=self.process_files)
        worker.start()


    def processing(self ,subs_id: list[str]):
        """将输入mkv中的字幕文件改为非默认轨道"""
        mkvs = []
        total = len(subs_id)
        for idx, sub_id in enumerate(subs_id, 1):
            # 更新进度
            progress = int((idx-1) / total * 100)
            status = f"正在预处理第 {idx}/{total} 项"
            wx.CallAfter(self.update_progress, progress, status)
            
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
                stdout=subprocess.PIPE,
                text= True,
                shell= False, 
                encoding="utf-8"
            )
            if self.is_processing == False:
                shutil.rmtree(str(Path(mkv.parent, "Processed")))
                self.current_progress = 0
                self.gauge.SetValue(0)
                self.lbl_percent.SetLabel(f"{0}%")
                raise KeyboardInterrupt("操作已被用户取消") 
            
            self.current_progress = 100
            self.gauge.SetValue(100)
            self.lbl_percent.SetLabel(f"{100}%")

        # 将处理好的文件从Processed文件夹移到原文件夹
        for mkv in mkvs:
            mkv = Path(mkv)
            completed_mkv = Path(mkv.parent, "Processed", mkv.name)
            completed_mkv.replace(mkv)
            try:
                completed_mkv.parent.rmdir()
            except WindowsError:
                pass

    def process_files(self):
        """文件处理"""
        mkvmerge = Path("mkvtoolnix/mkvmerge.exe")
        output_root = Path("out")
        if not mkvmerge.exists():
            raise Exception(f"错误: 找不到mkvmerge工具: {mkvmerge}")
        
        # 预处理
        mkvs = mixing.classify_files(mixing.get_all_files(self.path))[0]
        subs_id = preprocessing.mkv_check(mkvs)
        if subs_id == []:
            self.log(f"未在输入的mkv文件中发现字幕文件,即将开始混流...")
        else:
            self.log(f"在输入的mkv文件中发现字幕文件,即将开始预处理...")
            time.sleep(2)
            try:
                self.processing(subs_id)
            except Exception as e:
                raise Exception(f"处理出错: {e}")
            self.log(f"预处理已完成,即将开始混流...")
            self.lbl_status.SetLabel("预处理完成")
        time.sleep(2)

        # 混流处理
        try:
            is_multi, seasons = mixing.check_multiple_seasons(self.path)
        except FileNotFoundError as e:
            raise Exception(e)

        all_commands = []
        try:
            if is_multi:
                for season in seasons:
                    all_commands += mixing.process_season(season, self.path, output_root)
            else:
                all_commands = mixing.process_season(self.path, self.path, output_root)
        except Exception as e:
            raise Exception(f"处理出错: {e}")
        
        total = len(all_commands)
        try:
            for idx, cmd in enumerate(all_commands, 1):
                # 更新进度
                progress = int((idx-1) / total * 100)
                status = f"正在处理第 {idx}/{total} 项"
                wx.CallAfter(self.update_progress, progress, status)
                complete = subprocess.run(
                    cmd, 
                    stdout=subprocess.PIPE, 
                    text=True, 
                    shell=False, 
                    encoding="utf-8"
                )
                if self.is_processing == False:
                    self.current_progress = 0
                    self.gauge.SetValue(0)
                    self.lbl_percent.SetLabel(f"{0}%")
                    raise KeyboardInterrupt("操作已被用户取消")
                    
            wx.CallAfter(self.on_process_complete)
              
        except Exception as e:
            wx.CallAfter(self.log, f"发生错误：{str(e)}")
            wx.CallAfter(self.update_ui_state, False)

    def update_progress(self, value, status):
        """更新进度显示"""
        self.current_progress = value
        self.gauge.SetValue(value)
        self.lbl_percent.SetLabel(f"{value}%")
        self.lbl_status.SetLabel(status)
        self.log(status)

    def on_process_complete(self):
        """处理完成回调"""
        self.log("混流处理完成！")
        self.current_progress = 100
        self.gauge.SetValue(100)
        self.lbl_percent.SetLabel(f"{100}%")
        self.update_ui_state(False)
        wx.MessageBox("处理完成！", "提示", wx.OK|wx.ICON_INFORMATION)

    def update_ui_state(self, processing):
        """更新界面状态"""
        self.is_processing = processing
        self.btn_start.Enable(not processing)
        self.btn_cancel.Enable(processing)
        if not processing:
            self.lbl_status.SetLabel("准备就绪")

    def log(self, message):
        """记录日志"""
        timestamp = wx.DateTime.Now().FormatTime()
        self.log_text.AppendText(f"[{timestamp}] {message}\n")
        self.log_text.ShowPosition(self.log_text.GetLastPosition())

if __name__ == "__main__":
    app = MediaMixerApp()
    app.MainLoop()