import os, vlc, json
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QFrame, QProgressBar, QCheckBox, 
                             QFileDialog, QTextEdit, QSizePolicy)
from PyQt6.QtCore import Qt
from core.worker_threads import VideoDownloaderThread, VideoConverterThread
import ui.style_sheets as style_sheets

class VideoApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Universal AI Player Pro (Susik Engine)")
        self.setMinimumWidth(700)
        
        self.config_file = "config.json"
        
        # Загружаем настройки (тема и путь)
        settings = self.load_settings()
        self.is_dark_theme = settings.get("dark_theme", True)
        self.download_dir = settings.get("download_path", os.getcwd()) # По умолчанию текущая папка
        
        self.init_ui()
        self.apply_theme()
        self.init_vlc()

    def load_settings(self):
        """Загрузка всех настроек из JSON."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding='utf-8') as f:
                    return json.load(f)
            except: return {}
        return {}

    def save_settings(self):
        """Сохранение всех настроек в JSON."""
        data = {
            "dark_theme": self.is_dark_theme,
            "download_path": self.download_dir
        }
        try:
            with open(self.config_file, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")

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

        # Поле URL
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("Ссылка на видео...")
        self.main_layout.addWidget(self.url_input)

        # --- Панель выбора папки (НОВОЕ) ---
        path_layout = QHBoxLayout()
        self.path_display = QLineEdit(self.download_dir)
        self.path_display.setReadOnly(True) 
        self.path_display.setPlaceholderText("Папка для сохранения...")
        self.btn_select_path = QPushButton("ПАПКА")
        self.btn_select_path.clicked.connect(self.choose_directory)
        
        path_layout.addWidget(self.path_display)
        path_layout.addWidget(self.btn_select_path)
        self.main_layout.addLayout(path_layout)
        # -----------------------------------

        # Кнопки управления
        btns_layout = QHBoxLayout()
        self.btn_load = QPushButton("СКАЧАТЬ")
        self.btn_file = QPushButton("ФАЙЛ")
        self.btn_theme = QPushButton("ТЕМА")
        self.btn_log = QPushButton("ЛОГИ")
        
        for b in [self.btn_load, self.btn_file, self.btn_theme, self.btn_log]:
            btns_layout.addWidget(b)
        self.main_layout.addLayout(btns_layout)

        # Опции
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

        # Плеер
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

    def choose_directory(self):
        """Диалог выбора папки."""
        dir_path = QFileDialog.getExistingDirectory(self, "Выбрать папку для сохранения", self.download_dir)
        if dir_path:
            self.download_dir = dir_path
            self.path_display.setText(dir_path)
            self.save_settings() # Сразу сохраняем путь

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

    def update_ui(self, data):
    # Если пришел словарь
        if isinstance(data, dict):
            if data.get('status') == 'error':
                self.label.setText(f"Ошибка: {data['msg']}")
            else:
                self.progress_bar.setValue(data.get('percent', 0))
    # Если пришла просто строка (на случай старых ошибок)
        else:
            self.label.setText(str(data))

    def init_vlc(self):
        self.vlc_inst = vlc.Instance('--quiet')
        self.player = self.vlc_inst.media_player_new()
        self.player.set_hwnd(self.video_frame.winId())

    def start_download(self):
        url = self.url_input.text().strip()
        if not url: return
        self.log_box.clear()
        self.status_label.setText("Получение информации...")
        
        # Передаем только URL и ПАПКУ. Поток сам решит, как назвать файл.
        self.dl_thread = VideoDownloaderThread(url, self.download_dir) 
        self.dl_thread.progress_signal.connect(self.update_progress)
        self.dl_thread.finished_signal.connect(self.handle_finish)
        self.dl_thread.start()

    def handle_finish(self, path):
        if not path:
            self.status_label.setText("Ошибка скачивания")
            return
            
        if self.cb_conv.isChecked():
            self.status_label.setText("Оптимизация (SusikMedia)...")
            # Создаем имя для конвертированного файла (напр. "Title_fixed.mp4")
            base, ext = os.path.splitext(path)
            out = f"{base}_fixed{ext}"
            
            self.conv_thread = VideoConverterThread(path, out)
            self.conv_thread.finished_signal.connect(self.play_final)
            self.conv_thread.start()
        else: 
            self.play_final(path)

    def open_local(self):
        p, _ = QFileDialog.getOpenFileName(self, "Выбрать видео", self.download_dir, "Video (*.mp4 *.mkv *.avi)")
        if p: self.play_final(p)

    def play_final(self, path):
        self.progress_bar.hide()
        self.player.set_media(self.vlc_inst.media_new(path))
        self.player.play()
        self.status_label.setText(f"Играет: {os.path.basename(path)}")

    def vlc_play(self): self.player.play()
    def vlc_pause(self): self.player.pause()
    def vlc_stop(self): self.player.stop()