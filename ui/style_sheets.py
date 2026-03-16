DARK_STYLE = """
QWidget { background-color: #0f0f0f; color: #d1d1d1; font-family: 'Segoe UI'; }
QLineEdit, QTextEdit { background-color: #1a1a1a; border: 1px solid #333; border-radius: 4px; padding: 6px; color: #fff; }
QPushButton { 
    background-color: #161616; 
    border: 1px solid #2a2a2a; 
    border-radius: 4px; 
    padding: 10px; 
    font-weight: bold; 
    color: #bbb;
}
QPushButton:hover { background-color: #222222; border-color: #3d5afe; color: #fff; }
QPushButton:pressed { background-color: #000; }
QProgressBar { border: 1px solid #222; height: 10px; text-align: center; border-radius: 5px; background: #1a1a1a; }
QProgressBar::chunk { background-color: #3d5afe; border-radius: 5px; }
QCheckBox { spacing: 8px; }
"""

LIGHT_STYLE = """
QWidget { background-color: #ffffff; color: #202124; font-family: 'Segoe UI'; }
QLineEdit, QTextEdit { background-color: #f1f3f4; border: 1px solid #dadce0; border-radius: 4px; padding: 6px; color: #000; }
QPushButton { 
    background-color: #e8eaed; 
    border: 1px solid #dadce0; 
    border-radius: 4px; 
    padding: 10px; 
    font-weight: bold; 
    color: #3c4043;
}
QPushButton:hover { background-color: #dee1e6; border-color: #bdc1c6; }
QPushButton:pressed { background-color: #d2d6dc; }
QProgressBar { border: 1px solid #dadce0; height: 10px; text-align: center; border-radius: 5px; background: #f1f3f4; }
QProgressBar::chunk { background-color: #1a73e8; border-radius: 5px; }
QCheckBox { spacing: 8px; }
"""