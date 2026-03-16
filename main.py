import sys
from PyQt6.QtWidgets import QApplication
from ui.main_window import VideoApp

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VideoApp()
    window.show()
    
    sys.exit(app.exec())