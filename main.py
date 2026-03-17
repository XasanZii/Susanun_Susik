import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import DownloadWindow
from ui.player_window import PlayerWindow
from ui.logs_window import LogsWindow
from core.sheets_manager import SheetsManager

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Инициализируем менеджер Sheets
    sheets_manager = SheetsManager()
    
    # Создаём окна
    logs_window = LogsWindow(sheets_manager=sheets_manager)
    player_window = PlayerWindow(logs_window=logs_window, sheets_manager=sheets_manager)
    download_window = DownloadWindow(player_window=player_window, logs_window=logs_window, sheets_manager=sheets_manager)
    
    # Связываем окна между собой
    player_window.download_window = download_window
    
    # Показываем оба основных окна
    download_window.show()
    player_window.show()
    
    sys.exit(app.exec())