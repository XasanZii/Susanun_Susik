import os, json
from os import path
import re
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QLineEdit, QLabel, QProgressBar, QCheckBox, 
                             QFileDialog, QComboBox)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from core.worker_threads import VideoDownloaderThread
import ui.style_sheets as style_sheets

class DownloadWindow(QWidget):
    def __init__(self, player_window=None, logs_window=None, sheets_manager=None):
        super().__init__()
        self.setWindowTitle("Universal AI Player Pro (Susik Engine) - Загрузка и Конвертация")
        self.setFixedSize(750, 700)
        
        self.player_window = player_window
        self.logs_window = logs_window
        self.sheets_manager = sheets_manager
        
        self.config_file = "config.json"
        settings = self.load_settings()
        self.theme_index = settings.get("theme_index", 0)  # 0-6 for 7 themes
        self.themes = ["dark", "light", "alice", "miku", "lena", "ulyana", "slavi"]
        self.is_dark_theme = (self.theme_index == 0)
        self.download_dir = settings.get("download_path", os.getcwd())
        self.format_type = settings.get("format_type", "mp4")
        self.resolution_quality = settings.get("resolution_quality", "best")
        
        # Переменные для управления загрузкой
        self.dl_thread = None
        self.downloading_file = None
        
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
        data = {
            "dark_theme": self.is_dark_theme, 
            "download_path": self.download_dir, 
            "theme_index": self.theme_index,
            "format_type": self.format_type,
            "resolution_quality": self.resolution_quality
        }
        try:
            with open(self.config_file, "w", encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            self.add_log(f"Ошибка настроек: {e}", "ERROR")

    def init_ui(self):
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(15, 15, 15, 15)

        # Заголовок
        title_layout = QHBoxLayout()
        title_label = QLabel("Загрузка и Конвертация Видео")
        title_font = QFont("Segoe UI", 14, QFont.Weight.Bold)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        title_layout.addStretch()
        
        # Выпадающее меню для выбора темы
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["🌙 Темная", "☀️ Светлая", "🧡 Алиса (Рыжая)", "💙 Мику (Аквамарин)", "� Лена (Фиолетовая)", "❤️ Ульяна (Красная)", "🌾 Слави (Сена)"])
        self.theme_combo.setMaximumWidth(250)
        self.theme_combo.setMinimumHeight(35)
        self.theme_combo.setCurrentIndex(self.theme_index)
        self.theme_combo.currentIndexChanged.connect(self.on_theme_changed)
        title_layout.addWidget(self.theme_combo)
        
        # Кнопка логов
        self.btn_log = QPushButton("Логи")
        self.btn_log.setMaximumWidth(60)
        self.btn_log.setMaximumHeight(35)
        self.btn_log.setProperty("class", "info")
        self.btn_log.clicked.connect(self.show_logs)
        title_layout.addWidget(self.btn_log)
        
        self.main_layout.addLayout(title_layout)

        # Форма ввода
        form_layout = QVBoxLayout()
        form_layout.setSpacing(8)

        # URL ввод
        url_label = QLabel("Ссылка на видео:")
        url_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        form_layout.addWidget(url_label)
        
        self.url_input = QLineEdit()
        self.url_input.setPlaceholderText("YouTube, Vimeo, Facebook и другие источники...")
        self.url_input.setMinimumHeight(35)
        form_layout.addWidget(self.url_input)

        # Папка сохранения
        folder_label = QLabel("Папка сохранения:")
        folder_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        form_layout.addWidget(folder_label)
        
        path_layout = QHBoxLayout()
        self.path_display = QLineEdit(self.download_dir)
        self.path_display.setReadOnly(True)
        self.path_display.setMinimumHeight(35)
        self.btn_select_path = QPushButton("Выбрать")
        self.btn_select_path.setMaximumWidth(100)
        self.btn_select_path.setMinimumHeight(35)
        self.btn_select_path.setProperty("class", "info")
        self.btn_select_path.clicked.connect(self.choose_directory)
        path_layout.addWidget(self.path_display)
        path_layout.addWidget(self.btn_select_path)
        form_layout.addLayout(path_layout)

        # Cookies
        cookies_label = QLabel("Аутентификация для приватных видео:")
        cookies_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        form_layout.addWidget(cookies_label)
        
        cookies_layout = QHBoxLayout()
        
        # Выбор браузера для автоматического получения куков
        browser_label = QLabel("Браузер:")
        browser_label.setFont(QFont("Segoe UI", 10))
        cookies_layout.addWidget(browser_label)
        
        self.browser_combo = QComboBox()
        self.browser_combo.addItems(["Автоматически (все)", "Chrome", "Edge", "Firefox", "Opera", "Vivaldi", "Yandex", "Zen"])
        self.browser_combo.setMaximumWidth(140)
        self.browser_combo.setMinimumHeight(35)
        cookies_layout.addWidget(self.browser_combo)
        
        cookies_layout.addSpacing(15)
        
        # Или загрузить cookies.txt вручную
        or_label = QLabel("ИЛИ файл cookies:")
        or_label.setFont(QFont("Segoe UI", 10))
        cookies_layout.addWidget(or_label)
        
        self.cookies_input = QLineEdit()
        self.cookies_input.setPlaceholderText("Путь к cookies.txt (Netscape format)")
        self.cookies_input.setMinimumHeight(35)
        self.cookies_browse_btn = QPushButton("Обзор")
        self.cookies_browse_btn.setMaximumWidth(100)
        self.cookies_browse_btn.setMinimumHeight(35)
        self.cookies_browse_btn.setProperty("class", "info")
        self.cookies_browse_btn.clicked.connect(self.browse_cookies)
        cookies_layout.addWidget(self.cookies_input)
        cookies_layout.addWidget(self.cookies_browse_btn)
        cookies_layout.addStretch()
        
        form_layout.addLayout(cookies_layout)

        self.main_layout.addLayout(form_layout)

        # Опции конвертации
        options_label = QLabel("Настройки обработки:")
        options_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.main_layout.addWidget(options_label)
        
        options_layout = QHBoxLayout()
        
        self.cb_use_workers = QCheckBox("Конвертировать видео")
        self.cb_use_workers.setChecked(True)
        options_layout.addWidget(self.cb_use_workers)
        
        options_layout.addSpacing(20)
        
        output_label = QLabel("Формат вывода:")
        output_label.setFont(QFont("Segoe UI", 10))
        options_layout.addWidget(output_label)
        
        self.format_combo = QComboBox()
        self.format_combo.addItems(["MP4", "MP3", "WAV", "AAC", "OGG", "WebM", "MKV"])
        # Установить последний выбранный формат
        format_index = {"mp4": 0, "mp3": 1, "wav": 2, "aac": 3, "ogg": 4, "webm": 5, "mkv": 6}.get(self.format_type.lower(), 0)
        self.format_combo.setCurrentIndex(format_index)
        self.format_combo.setMaximumWidth(100)
        self.format_combo.setMinimumHeight(32)
        self.format_combo.currentTextChanged.connect(self.on_format_changed)
        options_layout.addWidget(self.format_combo)
        
        options_layout.addSpacing(20)
        
        resolution_label = QLabel("Разрешение:")
        resolution_label.setFont(QFont("Segoe UI", 10))
        options_layout.addWidget(resolution_label)
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["Лучшее", "1080p", "720p", "480p", "360p", "240p"])
        # Установить последнее выбранное разрешение
        resolution_index = {"best": 0, "1080": 1, "720": 2, "480": 3, "360": 4, "240": 5}.get(self.resolution_quality, 0)
        self.resolution_combo.setCurrentIndex(resolution_index)
        self.resolution_combo.setMaximumWidth(100)
        self.resolution_combo.setMinimumHeight(32)
        self.resolution_combo.currentTextChanged.connect(self.on_resolution_changed)
        options_layout.addWidget(self.resolution_combo)
        
        options_layout.addStretch()
        
        self.main_layout.addLayout(options_layout)

        # Статус и прогресс
        self.status_label = QLabel("Готово к загрузке")
        self.status_label.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.main_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.hide()
        self.progress_bar.setMinimumHeight(8)
        self.main_layout.addWidget(self.progress_bar)

        # ETA
        eta_layout = QHBoxLayout()
        eta_layout.addStretch()
        self.eta_label = QLabel("")
        self.eta_label.setFont(QFont("Segoe UI", 9))
        eta_layout.addWidget(self.eta_label)
        self.main_layout.addLayout(eta_layout)

        # Основные кнопки действия
        action_layout = QHBoxLayout()
        
        self.btn_load = QPushButton("Начать загрузку")
        self.btn_load.setMinimumHeight(45)
        self.btn_load.setProperty("class", "primary")
        self.btn_load.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_load.clicked.connect(self.start_download)
        action_layout.addWidget(self.btn_load)
        
        self.btn_stop = QPushButton("❌ Остановить")
        self.btn_stop.setMinimumHeight(45)
        self.btn_stop.setProperty("class", "danger")
        self.btn_stop.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_stop.clicked.connect(self.stop_download)
        self.btn_stop.hide()  # Скрыта по умолчанию
        action_layout.addWidget(self.btn_stop)
        
        self.btn_file = QPushButton("Открыть файл")
        self.btn_file.setMinimumHeight(45)
        self.btn_file.setProperty("class", "info")
        self.btn_file.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_file.clicked.connect(self.open_local)
        action_layout.addWidget(self.btn_file)
        
        self.btn_to_player = QPushButton("Плеер")
        self.btn_to_player.setMinimumHeight(45)
        self.btn_to_player.setProperty("class", "success")
        self.btn_to_player.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        self.btn_to_player.clicked.connect(self.show_player)
        action_layout.addWidget(self.btn_to_player)
        
        self.main_layout.addLayout(action_layout)

        # Низ окна - кнопка выхода слева
        bottom_layout = QHBoxLayout()
        
        self.btn_exit = QPushButton("ВЫХОД")
        self.btn_exit.setMaximumWidth(120)
        self.btn_exit.setMinimumHeight(40)
        self.btn_exit.setProperty("class", "danger")
        self.btn_exit.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))
        self.btn_exit.clicked.connect(self.exit_app)
        bottom_layout.addWidget(self.btn_exit)
        
        bottom_layout.addStretch()
        
        self.main_layout.addLayout(bottom_layout)

    def choose_directory(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Папка сохранения", self.download_dir)
        if dir_path:
            self.download_dir = dir_path
            self.path_display.setText(dir_path)
            self.save_settings()

    def toggle_theme(self):
        self.theme_index = (self.theme_index + 1) % len(self.themes)
        self.theme_combo.setCurrentIndex(self.theme_index)
        self.apply_theme()
        self.save_settings()

    def on_theme_changed(self, index):
        """Обработчик изменения темы из выпадающего меню"""
        self.theme_index = index
        self.apply_theme()
        self.save_settings()
        if self.player_window:
            self.player_window.theme_index = self.theme_index
            self.player_window.update_theme_combo()
            self.player_window.apply_theme()
            self.player_window.save_settings()
        if self.logs_window:
            self.logs_window.theme_index = self.theme_index
            self.logs_window.apply_theme()

    def apply_theme(self):
        theme_name = self.themes[self.theme_index]
        theme_map = {
            "dark": style_sheets.DARK_STYLE,
            "light": style_sheets.LIGHT_STYLE,
            "alice": style_sheets.ALICE_ORANGE_STYLE,
            "miku": style_sheets.MIKU_CYAN_STYLE,
            "lena": style_sheets.LENA_LIGHT_BLUE_STYLE,
            "ulyana": style_sheets.ULYANA_PINK_STYLE,
            "slavi": style_sheets.SLAVI_PURPLE_STYLE
        }
        self.is_dark_theme = (theme_name == "dark")
        style = theme_map.get(theme_name, style_sheets.DARK_STYLE)
        self.setStyleSheet(style)

    def on_format_changed(self, format_text):
        """Обработчик изменения формата"""
        self.format_type = format_text.lower()
    
    def on_resolution_changed(self, resolution_text):
        """Обработчик изменения разрешения"""
        if resolution_text == "Лучшее":
            self.resolution_quality = "best"
        else:
            self.resolution_quality = resolution_text.replace("p", "")

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
            self.hide()

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
                self.status_label.setText(f"Ошибка: {msg}")
                self.log_message(msg, "ERROR")
            
            elif status == 'downloading':
                percent = data.get('percent', 0)
                self.progress_bar.show()
                self.progress_bar.setValue(percent)
                self.status_label.setText(f"Загрузка: {percent}%")
                self.eta_label.setText(f"Скорость: {speed} • Осталось: {eta}")
                self.log_message(f"Загрузка: {percent}% ({speed})", "DOWNLOAD")

            elif status == 'processing':
                self.status_label.setText(f"Обработка: {msg}")
                self.progress_bar.setRange(0, 0)
                self.log_message(msg, "PROCESS")
            
            elif status == 'done':
                self.status_label.setText("Готово!")
                self.progress_bar.setValue(100)
        else:
            self.log_message(str(data))

    def start_download(self):
        url = self.url_input.text().strip()
        if not url:
            self.log_message("Пожалуйста введите URL", "ERROR")
            return
        
        # Получить выбранные формат и разрешение
        output_format = self.format_combo.currentText().lower()
        self.format_type = output_format
        
        resolution_text = self.resolution_combo.currentText()
        if resolution_text == "Лучшее":
            self.resolution_quality = "best"
        else:
            self.resolution_quality = resolution_text.replace("p", "")
        
        self.save_settings()  # Сохранить выбор
        
        self.log_message(f"Начало загрузки: {url} → {output_format} ({resolution_text})", "DOWNLOAD")
        
        # Сохраняем ссылку в Sheets
        if self.sheets_manager:
            self.sheets_manager.add_link(url, status="pending")
        
        # Получить браузер для куков
        browser_text = self.browser_combo.currentText()
        use_browser = None if browser_text == "Автоматически (все)" else browser_text.lower()
        
        # Получить путь к файлу с куками
        cookies = self.cookies_input.text().strip() or None
        
        self.dl_thread = VideoDownloaderThread(
            url,
            self.download_dir,
            use_conversion=self.cb_use_workers.isChecked(),
            cookies_path=cookies,
            output_format=output_format,
            resolution_quality=self.resolution_quality,
            use_browser=use_browser
        )
        self.dl_thread.progress_signal.connect(self.update_ui)
        self.dl_thread.finished_signal.connect(self.handle_finish)
        self.dl_thread.start()
        
        # Обновить UI - показать кнопку остановки
        self.btn_load.hide()
        self.btn_stop.show()
        self.btn_file.setEnabled(False)
        self.btn_to_player.setEnabled(False)

    def stop_download(self):
        """Остановить загрузку и удалить недокаченный файл"""
        if self.dl_thread and self.dl_thread.isRunning():
            self.log_message("Остановка загрузки...", "PROCESS")
            self.dl_thread.stop_download = True
            self.dl_thread.quit()
            self.dl_thread.wait()
            
            # Удалить недокаченный файл
            if self.downloading_file and os.path.exists(self.downloading_file):
                try:
                    os.remove(self.downloading_file)
                    self.log_message(f"Удален недокаченный файл: {os.path.basename(self.downloading_file)}", "PROCESS")
                except Exception as e:
                    self.log_message(f"Ошибка удаления файла: {e}", "ERROR")
            
            # Обновить UI - показать кнопку загрузки
            self.btn_stop.hide()
            self.btn_load.show()
            self.btn_file.setEnabled(True)
            self.btn_to_player.setEnabled(True)
            
            self.status_label.setText("Загрузка остановлена")
            self.progress_bar.hide()
            self.progress_bar.setRange(0, 100)
            self.eta_label.setText("")
        
        # Обновить UI - показать кнопку остановки
        self.btn_load.hide()
        self.btn_stop.show()
        self.btn_file.setEnabled(False)
        self.btn_to_player.setEnabled(False)

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
        output_format = self.format_combo.currentText().split()[0].lower()
        
        if path:
            self.log_message(f"Успешно: {os.path.basename(path)}", "SUCCESS")
            self.status_label.setText(f"Готово: {os.path.basename(path)}")
            
            # Сохраняем успех в Sheets
            if self.sheets_manager:
                title = os.path.splitext(os.path.basename(path))[0]
                self.sheets_manager.add_success_log(url, title, path)
            
            # Передаём файл в окно плеера если его выбрали
            if self.player_window:
                self.player_window.play_file(path)
                self.player_window.show()
                self.player_window.raise_()
        else:
            self.log_message(f"Ошибка загрузки {output_format}", "ERROR")
            self.status_label.setText("Ошибка загрузки")
            
            # Сохраняем ошибку в Sheets
            if self.sheets_manager:
                self.sheets_manager.add_error_log(url, f"Ошибка загрузки/конвертации в {output_format}")
        
        # Восстановить состояние UI
        self.progress_bar.hide()
        self.progress_bar.setRange(0, 100)
        self.eta_label.setText("")
        self.btn_stop.hide()
        self.btn_load.show()
        self.btn_file.setEnabled(True)
        self.btn_to_player.setEnabled(True)
        self.downloading_file = None

    def browse_cookies(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выберите cookies.txt (Netscape format)", "", "Cookies (*.txt);;All Files (*)")
        if file_path:
            self.cookies_input.setText(file_path)