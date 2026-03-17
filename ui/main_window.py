import os, json
from os import path
import re
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QProgressBar, QCheckBox, 
                             QFileDialog, QTextEdit)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.worker_threads import VideoDownloaderThread
import ui.style_sheets as style_sheets

class DownloadWindow(QWidget):
    def __init__(self, player_window=None, logs_window=None, sheets_manager=None):
        super().__init__()
        self.setWindowTitle("Universal AI Player Pro (Susik Engine) - Загрузка")
        self.setFixedSize(700, 650)
        
        self.player_window = player_window
        self.logs_window = logs_window
        self.sheets_manager = sheets_manager
        
        self.config_file = "config.json"
        settings = self.load_settings()
        self.is_dark_theme = settings.get("dark_theme", True)
        self.download_dir = settings.get("download_path", os.getcwd())
        
        self.init_ui()
        self.apply_theme()

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
        self.main_layout.setSpacing(8)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Инфо панель с кнопками управления окнами в верхнем углу
        top_layout = QHBoxLayout()
        
        self.status_label = QLabel("Готов (SusikMedia Active)")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        top_layout.addWidget(self.status_label)
        
        top_layout.addStretch()
        
        # Кнопка переключения на плеер
        self.btn_to_player = QPushButton("▶️ ПЛЕЕР")
        self.btn_to_player.setMaximumWidth(80)
        self.btn_to_player.clicked.connect(self.show_player)
        top_layout.addWidget(self.btn_to_player)
        
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

        # Статус с ETA
        info_box = QHBoxLayout()
        self.eta_label = QLabel("")
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
        self.btn_load.setMinimumHeight(40)
        self.btn_file = QPushButton("ФАЙЛ")
        self.btn_file.setMinimumHeight(40)
        for b in [self.btn_load, self.btn_file]:
            btns_layout.addWidget(b)
        self.main_layout.addLayout(btns_layout)

        opts_layout = QHBoxLayout()
        self.cb_use_workers = QCheckBox("Использовать Susik-конвертер")
        self.cb_use_workers.setChecked(True)
        opts_layout.addWidget(self.cb_use_workers)
        self.main_layout.addLayout(opts_layout)

        cookies_layout = QHBoxLayout()
        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText("Путь к cookies.txt (опционально)")
        self.cookies_browse_btn = QPushButton("Обзор")
        self.cookies_browse_btn.clicked.connect(self.browse_cookies)
        cookies_layout.addWidget(self.cookies_input)
        cookies_layout.addWidget(self.cookies_browse_btn)
        self.main_layout.addLayout(cookies_layout)
        
        self.main_layout.addStretch()

        self.btn_load.clicked.connect(self.start_download)
        self.btn_file.clicked.connect(self.open_local)

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
        self.btn_theme.setText("☀️" if self.is_dark_theme else "🌙")

    def toggle_logs(self):
        """Показать логи"""
        if self.logs_window:
            self.logs_window.show()
            self.logs_window.raise_()

    def show_logs(self):
        """Показать окно логов"""
        if self.logs_window:
            self.logs_window.show()
            self.logs_window.raise_()

    def show_player(self):
        """Показать окно плеера и скрыть текущее"""
        if self.player_window:
            self.player_window.show()
            self.player_window.raise_()

    def exit_app(self):
        """Выход из приложения"""
        import sys
        sys.exit(0)

    def log_message(self, text: str, level: str = "INFO"):
        """Отправить сообщение в логи"""
        if self.logs_window:
            self.logs_window.add_log(text, level)

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
                self.status_label.setText(f"❌ Ошибка: {msg}")
                self.log_message(msg, "ERROR")
            
            elif status == 'downloading':
                percent = data.get('percent', 0)
                self.progress_bar.show()
                self.progress_bar.setValue(percent)
                self.status_label.setText(f"⬇️ Загрузка: {percent}% ({speed})")
                self.eta_label.setText(f"⏱ {eta}")
                self.log_message(f"Загрузка: {percent}% ({speed})", "DOWNLOAD")

            elif status == 'processing':
                self.status_label.setText(f"⚙️ {msg}")
                self.progress_bar.setRange(0, 0)
                self.log_message(msg, "PROCESS")
        else:
            self.log_message(str(data))

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.log_message("Пожалуйста введите URL", "ERROR")
            return
        
        self.log_message(f"🔗 Начало скачивания: {url}", "DOWNLOAD")
        
        # Сохраняем ссылку в Sheets
        if self.sheets_manager:
            self.sheets_manager.add_link(url, status="pending")
        
        cookies = self.cookies_input.text().strip() or None
        self.dl_thread = VideoDownloaderThread(
            url,
            self.download_dir,
            use_conversion=self.cb_use_workers.isChecked(),
            cookies_path=cookies
        )
        self.dl_thread.progress_signal.connect(self.update_ui)
        self.dl_thread.finished_signal.connect(self.handle_finish)
        self.dl_thread.start()

    def open_local(self):
        """Открыть локальный файл в плеере."""
        file_path, _ = QFileDialog.getOpenFileName(
            self, 
            "Открыть видео", 
            self.download_dir, 
            "Видео (*.mp4 *.mkv *.avi *.mov *.webm);;Все файлы (*)"
        )
        if file_path and self.player_window:
            self.log_message(f"📂 Открыт файл: {os.path.basename(file_path)}", "INFO")
            self.player_window.play_file(file_path)
            self.player_window.show()
            self.player_window.raise_()

    def handle_finish(self, path: str):
        url = self.url_input.text().strip()
        
        if path:
            self.log_message(f"✓ Загрузка завершена: {path}", "SUCCESS")
            self.status_label.setText(f"✓ Готово: {os.path.basename(path)}")
            
            # Сохраняем успех в Sheets
            if self.sheets_manager:
                title = os.path.splitext(os.path.basename(path))[0]
                self.sheets_manager.add_success_log(url, title, path)
            
            # Передаём файл в окно плеера и автоматически открываем его
            if self.player_window:
                self.player_window.play_file(path)
                self.player_window.show()
                self.player_window.raise_()
        else:
            self.log_message("❌ Загрузка завершилась без файла", "ERROR")
            self.status_label.setText("❌ Ошибка загрузки")
            
            # Сохраняем ошибку в Sheets
            if self.sheets_manager:
                self.sheets_manager.add_error_log(url, "Загрузка завершилась без файла")
        
        # скрыть прогрессбар / восстановить состояние UI
        self.progress_bar.hide()
        self.eta_label.setText("")

    def browse_cookies(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите cookies.txt (Netscape format)", "", "Cookies (*.txt);;All Files (*)")
        if file_path:
            self.cookies_input.setText(file_path)