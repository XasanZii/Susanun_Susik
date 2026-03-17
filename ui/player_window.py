import os, vlc
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLabel, QFrame, QFileDialog, QSlider)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont


class PlayerWindow(QWidget):
    """
    Окно для воспроизведения видео.
    """
    def __init__(self, logs_window=None, sheets_manager=None):
        super().__init__()
        self.setWindowTitle("Universal AI Player Pro (Susik Engine) - Плеер")
        self.setFixedSize(900, 700)
        
        self.logs_window = logs_window
        self.sheets_manager = sheets_manager
        self.download_window = None  # Будет установлено в main.py
        
        self.current_file = None
        self.is_dark_theme = True
        
        self.init_vlc()
        self.init_ui()
        self.setup_timer()

    def init_vlc(self):
        """Инициализация VLC."""
        self.vlc_inst = vlc.Instance('--quiet')
        self.player = self.vlc_inst.media_player_new()

    def init_ui(self):
        """Создание интерфейса игрока."""
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Верхняя панель управления
        top_layout = QHBoxLayout()
        
        self.status_label = QLabel("Готов к воспроизведению")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        top_layout.addWidget(self.status_label)
        
        top_layout.addStretch()
        
        # Кнопка переключения на загрузку
        self.btn_to_download = QPushButton("⬇️ ЗАГРУЗКА")
        self.btn_to_download.setMaximumWidth(110)
        self.btn_to_download.clicked.connect(self.show_download)
        top_layout.addWidget(self.btn_to_download)
        
        # Кнопка темы (маленькая)
        self.btn_theme = QPushButton("🌙")
        self.btn_theme.setMaximumWidth(40)
        self.btn_theme.setMaximumHeight(35)
        self.btn_theme.clicked.connect(self.toggle_theme)
        top_layout.addWidget(self.btn_theme)
        
        # Кнопка логов
        self.btn_log = QPushButton("📋")
        self.btn_log.setMaximumWidth(40)
        self.btn_log.setMaximumHeight(35)
        self.btn_log.clicked.connect(self.show_logs)
        top_layout.addWidget(self.btn_log)
        
        # Кнопка выхода
        self.btn_exit = QPushButton("❌")
        self.btn_exit.setMaximumWidth(40)
        self.btn_exit.setMaximumHeight(35)
        self.btn_exit.clicked.connect(self.exit_app)
        top_layout.addWidget(self.btn_exit)
        
        self.main_layout.addLayout(top_layout)

        # Видео фрейм
        self.video_frame = QFrame()
        self.video_frame.setStyleSheet("background-color: black;")
        self.video_frame.setMinimumHeight(500)
        self.main_layout.addWidget(self.video_frame)
        self.player.set_hwnd(self.video_frame.winId())

        # Инфо панель
        info_box = QHBoxLayout()
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setFont(QFont("Courier New", 9))
        info_box.addStretch()
        info_box.addWidget(self.time_label)
        self.main_layout.addLayout(info_box)

        # Слайдер прогресса
        self.progress_slider = QSlider(Qt.Orientation.Horizontal)
        self.progress_slider.setSliderPosition(0)
        self.progress_slider.sliderMoved.connect(self.seek_video)
        self.main_layout.addWidget(self.progress_slider)

        # Контрольные кнопки
        controls_layout = QHBoxLayout()
        
        self.btn_open = QPushButton("📂 ОТКРЫТЬ")
        self.btn_open.clicked.connect(self.open_file)
        controls_layout.addWidget(self.btn_open)
        
        self.btn_play = QPushButton("▶️ ВОСПРОИЗВЕДЕНИЕ")
        self.btn_play.clicked.connect(self.vlc_play)
        controls_layout.addWidget(self.btn_play)
        
        self.btn_pause = QPushButton("⏸️ ПАУЗА")
        self.btn_pause.clicked.connect(self.vlc_pause)
        controls_layout.addWidget(self.btn_pause)
        
        self.btn_stop = QPushButton("⏹️ СТОП")
        self.btn_stop.clicked.connect(self.vlc_stop)
        controls_layout.addWidget(self.btn_stop)
        
        self.main_layout.addLayout(controls_layout)

    def setup_timer(self):
        """Таймер для обновления времени."""
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_time)
        self.timer.start(500)

    def update_time(self):
        """Обновление текущего времени и прогресса."""
        if self.player.is_playing() or self.player.get_state() == vlc.State.Playing:
            try:
                duration = self.player.get_length()
                current = self.player.get_time()
                
                if duration > 0:
                    self.progress_slider.blockSignals(True)
                    self.progress_slider.setValue(int(current / duration * 100) if duration > 0 else 0)
                    self.progress_slider.blockSignals(False)
                    
                    current_str = self.format_time(current // 1000)
                    duration_str = self.format_time(duration // 1000)
                    self.time_label.setText(f"{current_str} / {duration_str}")
            except Exception:
                pass

    def format_time(self, seconds: int) -> str:
        """Форматирование времени в MM:SS."""
        minutes = seconds // 60
        secs = seconds % 60
        return f"{minutes:02d}:{secs:02d}"

    def play_file(self, file_path: str):
        """Воспроизведение файла."""
        if not file_path or not os.path.exists(file_path):
            self.status_label.setText(f"❌ Ошибка: файл не найден")
            if self.logs_window:
                self.logs_window.add_log(f"Файл не найден: {file_path}", "ERROR")
            return
        
        self.current_file = file_path
        self.player.set_media(self.vlc_inst.media_new(file_path))
        self.player.play()
        self.status_label.setText(f"▶️ Воспроизведение: {os.path.basename(file_path)}")
        
        if self.logs_window:
            self.logs_window.add_log(f"▶️ Начало воспроизведения: {os.path.basename(file_path)}", "SUCCESS")

    def open_file(self):
        """Открыть файл через диалог."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Открыть видео", 
            "", 
            "Видео (*.mp4 *.mkv *.avi *.mov *.webm);;Все файлы (*)"
        )
        if file_path:
            self.play_file(file_path)

    def seek_video(self, position: int):
        """Перемотка видео по слайдеру."""
        if self.player.get_length() > 0:
            duration = self.player.get_length()
            seek_time = int(position / 100 * duration)
            self.player.set_time(seek_time)

    def vlc_play(self):
        """Воспроизведение."""
        self.player.play()

    def vlc_pause(self):
        """Пауза."""
        self.player.pause()

    def vlc_stop(self):
        """Остановка."""
        self.player.stop()
        self.progress_slider.setValue(0)
        self.time_label.setText("00:00 / 00:00")
        self.status_label.setText("Готов к воспроизведению")

    def show_download(self):
        """Показать окно загрузки"""
        if self.download_window:
            self.download_window.show()
            self.download_window.raise_()

    def show_logs(self):
        """Показать окно логов"""
        if self.logs_window:
            self.logs_window.show()
            self.logs_window.raise_()

    def toggle_theme(self):
        """Переключить тему"""
        self.is_dark_theme = not self.is_dark_theme
        self.btn_theme.setText("☀️" if self.is_dark_theme else "🌙")

    def exit_app(self):
        """Выход из приложения"""
        import sys
        sys.exit(0)

    def closeEvent(self, event):
        """Закрытие окна."""
        self.timer.stop()
        self.player.stop()
        event.accept()
