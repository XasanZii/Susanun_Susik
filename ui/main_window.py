import os, vlc, json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QFrame, QProgressBar, QCheckBox, 
                             QFileDialog, QTextEdit, QSizePolicy)
from PyQt6.QtCore import Qt
from core.worker_threads import VideoDownloaderThread, VideoConverterThread
# Импортируем напрямую из файла
import ui.style_sheets as style_sheets

class VideoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal AI Player Pro")
        self.setMinimumWidth(700)
        
        # Путь к ffmpeg
        self.ffmpeg_path = os.path.join(os.getcwd(), "ffmpeg-master-latest-win64-gpl-shared", "bin", "ffmpeg.exe")
        self.config_file = "config.json"
        
        self.is_dark_theme = self.load_theme_settings()
        
        self.init_ui()
        self.apply_theme()
        self.init_vlc()

    def load_theme_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    return json.load(f).get("dark_theme", True)
            except: return True
        return True

    def save_theme_settings(self):
        try:
            with open(self.config_file, "w") as f:
                json.dump({"dark_theme": self.is_dark_theme}, f)
        except: pass

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)

        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumHeight(400)
        self.main_layout.addWidget(self.video_frame)

        info_box = QHBoxLayout()
        self.status_label = QLabel("Готов")
        self.eta_label = QLabel("")
        info_box.addWidget(self.status_label)
        info_box.addStretch()
        info_box.addWidget(self.eta_label)
        self.main_layout.addLayout(info_box)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.main_layout.addWidget(self.progress_bar)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Ссылка на видео...")
        self.main_layout.addWidget(self.url_input)

        btns_layout = QHBoxLayout()
        self.btn_load = QPushButton("СКАЧАТЬ")
        self.btn_file = QPushButton("ФАЙЛ")
        self.btn_theme = QPushButton("ТЕМА")
        self.btn_log = QPushButton("ЛОГИ")
        
        for b in [self.btn_load, self.btn_file, self.btn_theme, self.btn_log]:
            btns_layout.addWidget(b)
        self.main_layout.addLayout(btns_layout)

        opts_layout = QHBoxLayout()
        self.cb_show = QCheckBox("Показывать видео")
        self.cb_show.setChecked(True)
        self.cb_show.stateChanged.connect(self.toggle_video)
        self.cb_conv = QCheckBox("Конвертация")
        self.cb_conv.setChecked(True)
        opts_layout.addWidget(self.cb_show)
        opts_layout.addWidget(self.cb_conv)
        self.main_layout.addLayout(opts_layout)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.hide()
        self.main_layout.addWidget(self.log_box)

        player_layout = QHBoxLayout()
        for cmd in ["Play", "Pause", "Stop"]:
            btn = QPushButton(cmd)
            btn.clicked.connect(getattr(self, f"vlc_{cmd.lower()}"))
            player_layout.addWidget(btn)
        self.main_layout.addLayout(player_layout)

        self.btn_load.clicked.connect(self.start_download)
        self.btn_file.clicked.connect(self.open_local)
        self.btn_theme.clicked.connect(self.toggle_theme)
        self.btn_log.clicked.connect(self.toggle_logs)

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()
        self.save_theme_settings()

    def apply_theme(self):
        # Используем сохраненные строки из модуля
        style = style_sheets.DARK_STYLE if self.is_dark_theme else style_sheets.LIGHT_STYLE
        self.setStyleSheet(style)
        self.btn_theme.setText("🌙 ТЕМНАЯ" if self.is_dark_theme else "☀️ СВЕТЛАЯ")

    def toggle_video(self, state):
        self.video_frame.setVisible(bool(state))
        self.adjustSize()

    def toggle_logs(self):
        self.log_box.setVisible(not self.log_box.isVisible())
        self.adjustSize()

    def update_progress(self, data):
        if isinstance(data, dict):
            self.progress_bar.show()
            self.progress_bar.setValue(data.get('percent', 0))
            self.eta_label.setText(f"{data.get('speed', '')} ETA: {data.get('eta', '')}")
        else:
            self.log_box.append(str(data))

    def init_vlc(self):
        self.vlc_inst = vlc.Instance('--quiet')
        self.player = self.vlc_inst.media_player_new()
        self.player.set_hwnd(self.video_frame.winId())

    def start_download(self):
        url = self.url_input.text().strip()
        if not url: return
        self.log_box.clear()
        target = os.path.join(os.getcwd(), "video_temp.mp4")
        self.dl_thread = VideoDownloaderThread(url, target, self.ffmpeg_path)
        self.dl_thread.progress_signal.connect(self.update_progress)
        self.dl_thread.finished_signal.connect(self.handle_finish)
        self.dl_thread.start()

    def handle_finish(self, path):
        if not path:
            self.status_label.setText("Ошибка скачивания")
            return
        if self.cb_conv.isChecked():
            out = path.replace(".mp4", "_fixed.mp4")
            self.conv_thread = VideoConverterThread(path, out, self.ffmpeg_path)
            self.conv_thread.finished_signal.connect(self.play_final)
            self.conv_thread.start()
        else: self.play_final(path)

    def open_local(self):
        p, _ = QFileDialog.getOpenFileName(self, "Выбрать видео", "", "Video (*.mp4 *.mkv)")
        if p: self.play_final(p)

    def play_final(self, path):
        self.progress_bar.hide()
        self.player.set_media(self.vlc_inst.media_new(path))
        self.player.play()
        self.status_label.setText(f"Играет: {os.path.basename(path)}")

    def vlc_play(self): self.player.play()
    def vlc_pause(self): self.player.pause()
    def vlc_stop(self): self.player.stop()