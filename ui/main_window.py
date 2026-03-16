import os, vlc, json
import re
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QFrame, QProgressBar, QCheckBox, 
                             QFileDialog, QTextEdit)
from PyQt6.QtCore import Qt
from core.worker_threads import VideoDownloaderThread
import ui.style_sheets as style_sheets

class VideoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal AI Player Pro (Susik Engine)")
        self.setMinimumWidth(700)
        
        self.config_file = "config.json"
        settings = self.load_settings()
        self.is_dark_theme = settings.get("dark_theme", True)
        self.download_dir = settings.get("download_path", os.getcwd())
        
        self.init_ui()
        self.apply_theme()
        self.init_vlc()

    def load_settings(self):
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}

    def save_settings(self):
        data = {"dark_theme": self.is_dark_theme, "download_path": self.download_dir}
        try:
            with open(self.config_file, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.add_log(f"Ошибка настроек: {e}", "ERROR")

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)

        # Видео фрейм
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumHeight(400)
        self.main_layout.addWidget(self.video_frame)

        # Инфо панель
        info_box = QHBoxLayout()
        self.status_label = QLabel("Готов (SusikMedia Active)")
        self.eta_label = QLabel("")
        info_box.addWidget(self.status_label)
        info_box.addStretch()
        info_box.addWidget(self.eta_label)
        self.main_layout.addLayout(info_box)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.main_layout.addWidget(self.progress_bar)

        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Ссылка на видео (YouTube, и т.д.)...")
        self.main_layout.addWidget(self.url_input)

        path_layout = QHBoxLayout()
        self.path_display = QLineEdit(self.download_dir)
        self.path_display.setReadOnly(True) 
        self.btn_select_path = QPushButton("ПАПКА")
        self.btn_select_path.clicked.connect(self.choose_directory)
        path_layout.addWidget(self.path_display)
        path_layout.addWidget(self.btn_select_path)
        self.main_layout.addLayout(path_layout)

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
        self.cb_conv = QCheckBox("Конвертация (Susik)")
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

    def add_log(self, text, level="INFO"):
        """Красивый вывод лога с временем и цветом."""
        time_str = datetime.now().strftime("%H:%M:%S")
        colors = {"INFO": "#5dade2", "SUCCESS": "#58d68d", "ERROR": "#ec7063", "PROCESS": "#f4d03f"}
        color = colors.get(level, "#ffffff")
        log_html = f"<span style='color:#888;'>[{time_str}]</span> <b style='color:{color};'>{level: <7}</b> | {text}"
        self.log_box.append(log_html)
        self.log_box.ensureCursorVisible()

    def choose_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Папка сохранения", self.download_dir)
        if dir_path:
            self.download_dir = dir_path
            self.path_display.setText(dir_path)
            self.save_settings()

    def toggle_theme(self):
        self.is_dark_theme = not self.is_dark_theme
        self.apply_theme()
        self.save_settings()

    def apply_theme(self):
        style = style_sheets.DARK_STYLE if self.is_dark_theme else style_sheets.LIGHT_STYLE
        self.setStyleSheet(style)
        self.btn_theme.setText("🌙 ТЕМНАЯ" if self.is_dark_theme else "☀️ СВЕТЛАЯ")

    def toggle_video(self, state):
        self.video_frame.setVisible(bool(state))
        self.adjustSize()

    def toggle_logs(self):
        self.log_box.setVisible(not self.log_box.isVisible())
        self.adjustSize()

    def clean_ansi(self, text):
        """Удаляет ANSI-коды (цвета консоли) из строки."""
        ansi_escape = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        return ansi_escape.sub('', text)
    
    def update_ui(self, data):
        """Обработка данных от загрузчика."""
        if isinstance(data, dict):
            status = data.get('status')
            
            # Очищаем данные от мусора (как на скрине)
            speed = self.clean_ansi(data.get('speed', '---'))
            eta = self.clean_ansi(data.get('eta', '---'))
            msg = self.clean_ansi(data.get('msg', ''))

            if status == 'error':
                self.status_label.setText(f"Ошибка: {msg}") # Исправлено: self.label -> self.status_label
                self.add_log(msg, "ERROR")
            
            elif status == 'downloading':
                percent = data.get('percent', 0)
                self.progress_bar.show()
                self.progress_bar.setValue(percent)
                self.status_label.setText(f"Загрузка: {percent}% ({speed})")
                self.eta_label.setText(f"Осталось: {eta}")

            elif status == 'processing':
                self.status_label.setText(msg)
                self.progress_bar.setRange(0, 0)
        else:
            self.add_log(str(data))

    def init_vlc(self):
        self.vlc_inst = vlc.Instance('--quiet')
        self.player = self.vlc_inst.media_player_new()
        self.player.set_hwnd(self.video_frame.winId())

    def start_download(self):
        url = self.url_input.text().strip()
        if not url: return
        self.log_box.clear()
        
        self.dl_thread = VideoDownloaderThread(url, self.download_dir) 
        # ИСПРАВЛЕНО: подключаем к правильному методу update_ui
        self.dl_thread.progress_signal.connect(self.update_ui) 
        self.dl_thread.finished_signal.connect(self.handle_finish)
        self.dl_thread.start()

    def open_local(self):
        p, _ = QFileDialog.getOpenFileName(self, "Открыть видео", self.download_dir, "Video (*.mp4 *.mkv *.avi)")
        if p: self.play_final(p)

    def handle_finish(self, path: str):
        if path:
            self.add_log(f"Загрузка завершена: {path}", "SUCCESS")
        # проигрываем файл (play_final уже делает логику проверки/проигрывания)
            self.play_final(path)
        else:
            self.add_log("Загрузка завершилась без файла", "ERROR")
        # скрыть прогрессбар / восстановить состояние UI
            self.progress_bar.hide()
    
    def play_final(self, path):
        if not path:
            self.add_log("Завершено без файла", "ERROR")
            return
        self.progress_bar.hide()
        self.progress_bar.setRange(0, 100)
        self.eta_label.setText("")
        self.player.set_media(self.vlc_inst.media_new(path))
        self.player.play()
        self.status_label.setText(f"Воспроизведение: {os.path.basename(path)}")
        self.add_log(f"Файл готов: {path}", "SUCCESS")

    def vlc_play(self): self.player.play()
    def vlc_pause(self): self.player.pause()
    def vlc_stop(self): self.player.stop()