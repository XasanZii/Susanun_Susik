import json
from datetime import datetime
from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
                             QTextEdit, QLabel, QScrollArea, QFrame)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QTextCursor, QFont
import ui.style_sheets as style_sheets


class LogLevel:
    """Класс для уровней логирования"""
    INFO = {"name": "INFO", "color": "#5dade2", "icon": "ℹ"}
    SUCCESS = {"name": "SUCCESS", "color": "#58d68d", "icon": "✓"}
    ERROR = {"name": "ERROR", "color": "#ec7063", "icon": "✕"}
    PROCESS = {"name": "PROCESS", "color": "#f4d03f", "icon": "⚙"}
    DOWNLOAD = {"name": "DOWNLOAD", "color": "#3498db", "icon": "⬇"}
    CONVERT = {"name": "CONVERT", "color": "#9b59b6", "icon": "◆"}


class LogsWindow(QWidget):
    """
    Визуализатор логов приложения с сохранением в Google Sheets.
    """
    logs_updated = pyqtSignal(dict)
    
    def __init__(self, sheets_manager=None):
        super().__init__()
        self.setWindowTitle("Universal AI Player Pro - Логи")
        self.setMinimumSize(900, 600)
        
        self.sheets_manager = sheets_manager
        self.logs_history = []
        
        self.is_dark_theme = True
        self.theme_index = 0
        self.themes = ["dark", "light", "alice", "miku"]
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        """Инициализация интерфейса"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(10, 10, 10, 10)
        main_layout.setSpacing(10)

        # Заголовок с статистикой
        header_layout = QHBoxLayout()
        self.title_label = QLabel("ЛОГ ПРИЛОЖЕНИЯ")
        self.title_label.setFont(QFont("Segoe UI", 12, QFont.Weight.Bold))
        
        self.stats_label = QLabel("Логов: 0 | Ошибок: 0 | Успехов: 0")
        self.stats_label.setFont(QFont("Segoe UI", 10))
        self.stats_label.setStyleSheet("color: #888;")
        
        header_layout.addWidget(self.title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.stats_label)
        main_layout.addLayout(header_layout)

        # Основное окно логов
        self.logs_text = QTextEdit()
        self.logs_text.setReadOnly(True)
        self.logs_text.setFont(QFont("Courier New", 9))
        self.logs_text.setMaximumHeight(500)
        main_layout.addWidget(self.logs_text)

        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.btn_copy = QPushButton("Копировать")
        self.btn_copy.clicked.connect(self.copy_logs)
        self.btn_copy.setProperty("class", "info")
        buttons_layout.addWidget(self.btn_copy)
        
        self.btn_save = QPushButton("Сохранить")
        self.btn_save.clicked.connect(self.save_logs)
        self.btn_save.setProperty("class", "success")
        buttons_layout.addWidget(self.btn_save)
        
        self.btn_clear = QPushButton("Очистить")
        self.btn_clear.clicked.connect(self.clear_logs)
        self.btn_clear.setProperty("class", "info")
        buttons_layout.addWidget(self.btn_clear)
        
        buttons_layout.addStretch()
        
        self.btn_close = QPushButton("Закрыть")
        self.btn_close.clicked.connect(self.close)
        self.btn_close.setProperty("class", "danger")
        buttons_layout.addWidget(self.btn_close)
        
        main_layout.addLayout(buttons_layout)

    def add_log(self, text: str, level: str = "INFO"):
        """Добавление лога с форматированием"""
        time_str = datetime.now().strftime("%H:%M:%S")
        
        # Выбираем уровень логирования
        levels = {
            "INFO": LogLevel.INFO,
            "SUCCESS": LogLevel.SUCCESS,
            "ERROR": LogLevel.ERROR,
            "PROCESS": LogLevel.PROCESS,
            "DOWNLOAD": LogLevel.DOWNLOAD,
            "CONVERT": LogLevel.CONVERT,
        }
        
        log_level = levels.get(level.upper(), LogLevel.INFO)
        
        # Форматированная строка лога
        log_entry = {
            "timestamp": time_str,
            "level": log_level["name"],
            "message": text,
            "color": log_level["color"],
            "icon": log_level["icon"]
        }
        
        self.logs_history.append(log_entry)
        
        # Добавляем в текстовое поле
        formatted_log = f"[{time_str}] {log_level['icon']} {log_level['name']:<8} | {text}"
        
        self.logs_text.moveCursor(QTextCursor.MoveOperation.End)
        self.logs_text.setTextColor(QColor(log_level["color"]))
        self.logs_text.insertPlainText(formatted_log + "\n")
        self.logs_text.setTextColor(QColor("#d1d1d1"))
        
        # Обновляем статистику
        self.update_stats()
        
        # Сохраняем в Google Sheets если доступно
        if self.sheets_manager:
            self.logs_updated.emit(log_entry)

    def update_stats(self):
        """Обновление статистики логов"""
        total = len(self.logs_history)
        errors = sum(1 for log in self.logs_history if log["level"] == "ERROR")
        successes = sum(1 for log in self.logs_history if log["level"] == "SUCCESS")
        
        self.stats_label.setText(f"Логов: {total} | ❌ Ошибок: {errors} | ✓ Успехов: {successes}")

    def copy_logs(self):
        """Копирование всех логов"""
        self.logs_text.selectAll()
        self.logs_text.copy()
        self.add_log("Логи скопированы в буфер обмена", "SUCCESS")

    def save_logs(self):
        """Сохранение логов в файл"""
        try:
            filename = f"logs_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.logs_history, f, ensure_ascii=False, indent=2)
            self.add_log(f"Логи сохранены в {filename}", "SUCCESS")
        except Exception as e:
            self.add_log(f"Ошибка сохранения: {str(e)}", "ERROR")

    def clear_logs(self):
        """Очистка логов"""
        self.logs_text.clear()
        self.logs_history.clear()
        self.update_stats()
        self.add_log("Логирование перезагружено", "PROCESS")

    def apply_theme(self, is_dark=True):
        """Применение темы"""
        # Если передан параметр is_dark (старый способ), используем его
        # Иначе используем theme_index для новых тем
        if isinstance(is_dark, bool):
            self.is_dark_theme = is_dark
            theme_name = "dark" if is_dark else "light"
            self.theme_index = 0 if is_dark else 1
        else:
            theme_name = self.themes[self.theme_index] if hasattr(self, 'theme_index') else "dark"
            self.is_dark_theme = (theme_name == "dark")
        
        theme_map = {
            "dark": style_sheets.DARK_STYLE,
            "light": style_sheets.LIGHT_STYLE,
            "alice": style_sheets.ALICE_ORANGE_STYLE,
            "miku": style_sheets.MIKU_CYAN_STYLE
        }
        
        style = theme_map.get(theme_name if isinstance(is_dark, bool) else self.themes[getattr(self, 'theme_index', 0)], style_sheets.DARK_STYLE)
        self.setStyleSheet(style)

    def get_logs_json(self):
        """Получение логов в JSON формате"""
        return json.dumps(self.logs_history, ensure_ascii=False, indent=2)
