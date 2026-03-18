DARK_STYLE = """
QWidget { 
    background-color: #0f0f0f; 
    color: #d1d1d1; 
    font-family: 'Segoe UI'; 
}

QLineEdit, QTextEdit { 
    background-color: #1a1a1a; 
    border: 2px solid #333; 
    border-radius: 6px; 
    padding: 8px; 
    color: #fff;
    selection-background-color: #2c4cc4;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #2c4cc4;
}

QPushButton { 
    background-color: #161616; 
    border: 2px solid #2a2a2a; 
    border-radius: 6px; 
    padding: 10px 15px; 
    font-weight: bold; 
    color: #bbb;
    font-size: 11px;
    font-family: 'Segoe UI';
}

QPushButton:hover { 
    background-color: #222222; 
    border-color: #3d5afe; 
    color: #fff; 
}

QPushButton:pressed { 
    background-color: #000; 
    border-color: #3d5afe;
}

/* Primary Button Style */
QPushButton[class="primary"] {
    background-color: #2c4cc4;
    border: 2px solid #2c4cc4;
    color: #fff;
}

QPushButton[class="primary"]:hover {
    background-color: #3d5afe;
    border-color: #3d5afe;
}

/* Success Button Style */
QPushButton[class="success"] {
    background-color: #1e8449;
    border: 2px solid #1e8449;
    color: #fff;
}

QPushButton[class="success"]:hover {
    background-color: #27ae60;
    border-color: #27ae60;
}

/* Danger Button Style */
QPushButton[class="danger"] {
    background-color: #c0392b;
    border: 2px solid #c0392b;
    color: #fff;
}

QPushButton[class="danger"]:hover {
    background-color: #e74c3c;
    border-color: #e74c3c;
}

/* Info Button Style */
QPushButton[class="info"] {
    background-color: #2980b9;
    border: 2px solid #2980b9;
    color: #fff;
}

QPushButton[class="info"]:hover {
    background-color: #3498db;
    border-color: #3498db;
}

QProgressBar { 
    border: 2px solid #333; 
    height: 12px; 
    text-align: center; 
    border-radius: 6px; 
    background: #1a1a1a; 
}

QProgressBar::chunk { 
    background-color: #2c4cc4; 
    border-radius: 4px; 
}

QSlider::groove:horizontal {
    background: #333;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #3d5afe;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
    border: 2px solid #3d5afe;
}

QSlider::handle:horizontal:hover {
    background: #5b7fff;
    border: 2px solid #5b7fff;
}

QCheckBox { 
    spacing: 10px;
    color: #d1d1d1;
    font-weight: bold;
    font-size: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #444;
    background-color: #1a1a1a;
}

QCheckBox::indicator:hover {
    border: 2px solid #2c4cc4;
    background-color: #222;
}

QCheckBox::indicator:checked {
    background-color: #1e8449;
    border: 2px solid #1e8449;
}

QLabel {
    color: #d1d1d1;
}

QScrollBar:vertical {
    border: none;
    background-color: #1a1a1a;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #333;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #3d5afe;
}
"""

LIGHT_STYLE = """
QWidget { 
    background-color: #ffffff; 
    color: #202124; 
    font-family: 'Segoe UI'; 
}

QLineEdit, QTextEdit { 
    background-color: #f1f3f4; 
    border: 2px solid #dadce0; 
    border-radius: 6px; 
    padding: 8px; 
    color: #000;
    selection-background-color: #2563eb;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #2563eb;
}

QPushButton { 
    background-color: #e8eaed; 
    border: 2px solid #dadce0; 
    border-radius: 6px; 
    padding: 10px 15px; 
    font-weight: bold; 
    color: #3c4043;
    font-size: 11px;
    font-family: 'Segoe UI';
}

QPushButton:hover { 
    background-color: #dee1e6; 
    border-color: #2563eb; 
    color: #000;
}

QPushButton:pressed { 
    background-color: #d2d6dc; 
    border-color: #2563eb;
}

/* Primary Button Style */
QPushButton[class="primary"] {
    background-color: #2563eb;
    border: 2px solid #2563eb;
    color: #fff;
}

QPushButton[class="primary"]:hover {
    background-color: #3b82f6;
    border-color: #3b82f6;
}

/* Success Button Style */
QPushButton[class="success"] {
    background-color: #16a34a;
    border: 2px solid #16a34a;
    color: #fff;
}

QPushButton[class="success"]:hover {
    background-color: #22c55e;
    border-color: #22c55e;
}

/* Danger Button Style */
QPushButton[class="danger"] {
    background-color: #dc2626;
    border: 2px solid #dc2626;
    color: #fff;
}

QPushButton[class="danger"]:hover {
    background-color: #ef4444;
    border-color: #ef4444;
}

/* Info Button Style */
QPushButton[class="info"] {
    background-color: #2563eb;
    border: 2px solid #2563eb;
    color: #fff;
}

QPushButton[class="info"]:hover {
    background-color: #3b82f6;
    border-color: #3b82f6;
}

QProgressBar { 
    border: 2px solid #dadce0; 
    height: 12px; 
    text-align: center; 
    border-radius: 6px; 
    background: #f1f3f4; 
}

QProgressBar::chunk { 
    background-color: #2563eb; 
    border-radius: 4px; 
}

QSlider::groove:horizontal {
    background: #dadce0;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #2563eb;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
    border: 2px solid #2563eb;
}

QSlider::handle:horizontal:hover {
    background: #3b82f6;
    border: 2px solid #3b82f6;
}

QCheckBox { 
    spacing: 10px;
    color: #202124;
    font-weight: bold;
    font-size: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #dadce0;
    background-color: #f1f3f4;
}

QCheckBox::indicator:hover {
    border: 2px solid #2563eb;
    background-color: #e8eaed;
}

QCheckBox::indicator:checked {
    background-color: #16a34a;
    border: 2px solid #16a34a;
}

QLabel {
    color: #202124;
}

QScrollBar:vertical {
    border: none;
    background-color: #f1f3f4;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #dadce0;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #2563eb;
}
"""

# Рыжая тема (Алиса из "Бесконечного лета")
ALICE_ORANGE_STYLE = """
QWidget { 
    background-color: #2b1810; 
    color: #ffd8b8; 
    font-family: 'Segoe UI'; 
}

QLineEdit, QTextEdit { 
    background-color: #1a0f08; 
    border: 2px solid #8b4513; 
    border-radius: 6px; 
    padding: 8px; 
    color: #fff;
    selection-background-color: #d97706;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #d97706;
}

QPushButton { 
    background-color: #3d240f; 
    border: 2px solid #8b4513; 
    border-radius: 6px; 
    padding: 10px 15px; 
    font-weight: bold; 
    color: #ffc99a;
    font-size: 11px;
    font-family: 'Segoe UI';
}

QPushButton:hover { 
    background-color: #5a340f; 
    border-color: #d97706; 
    color: #fff; 
}

QPushButton:pressed { 
    background-color: #2b1810; 
    border-color: #d97706;
}

/* Primary Button Style */
QPushButton[class="primary"] {
    background-color: #d97706;
    border: 2px solid #d97706;
    color: #fff;
}

QPushButton[class="primary"]:hover {
    background-color: #ea580c;
    border-color: #ea580c;
}

/* Success Button Style */
QPushButton[class="success"] {
    background-color: #b45309;
    border: 2px solid #b45309;
    color: #fff;
}

QPushButton[class="success"]:hover {
    background-color: #d97706;
    border-color: #d97706;
}

/* Danger Button Style */
QPushButton[class="danger"] {
    background-color: #7c2d12;
    border: 2px solid #7c2d12;
    color: #fff;
}

QPushButton[class="danger"]:hover {
    background-color: #9a3412;
    border-color: #9a3412;
}

/* Info Button Style */
QPushButton[class="info"] {
    background-color: #c26922;
    border: 2px solid #c26922;
    color: #fff;
}

QPushButton[class="info"]:hover {
    background-color: #d97706;
    border-color: #d97706;
}

QProgressBar { 
    border: 2px solid #8b4513; 
    height: 12px; 
    text-align: center; 
    border-radius: 6px; 
    background: #1a0f08; 
}

QProgressBar::chunk { 
    background-color: #d97706; 
    border-radius: 4px; 
}

QSlider::groove:horizontal {
    background: #8b4513;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #d97706;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
    border: 2px solid #d97706;
}

QSlider::handle:horizontal:hover {
    background: #ea580c;
    border: 2px solid #ea580c;
}

QCheckBox { 
    spacing: 10px;
    color: #ffd8b8;
    font-weight: bold;
    font-size: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #8b4513;
    background-color: #1a0f08;
}

QCheckBox::indicator:hover {
    border: 2px solid #d97706;
    background-color: #3d240f;
}

QCheckBox::indicator:checked {
    background-color: #b45309;
    border: 2px solid #b45309;
}

QLabel {
    color: #ffd8b8;
}

QScrollBar:vertical {
    border: none;
    background-color: #1a0f08;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #8b4513;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #d97706;
}
"""

# Аквамариновая тема (Хатсуне Мику)
MIKU_CYAN_STYLE = """
QWidget { 
    background-color: #0a2a2a; 
    color: #a8f0f5; 
    font-family: 'Segoe UI'; 
}

QLineEdit, QTextEdit { 
    background-color: #051515; 
    border: 2px solid #0d7377; 
    border-radius: 6px; 
    padding: 8px; 
    color: #fff;
    selection-background-color: #06b6d4;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #06b6d4;
}

QPushButton { 
    background-color: #0f3e3e; 
    border: 2px solid #0d7377; 
    border-radius: 6px; 
    padding: 10px 15px; 
    font-weight: bold; 
    color: #88f3f8;
    font-size: 11px;
    font-family: 'Segoe UI';
}

QPushButton:hover { 
    background-color: #155560; 
    border-color: #06b6d4; 
    color: #fff; 
}

QPushButton:pressed { 
    background-color: #0a2a2a; 
    border-color: #06b6d4;
}

/* Primary Button Style */
QPushButton[class="primary"] {
    background-color: #06b6d4;
    border: 2px solid #06b6d4;
    color: #1a1a1a;
}

QPushButton[class="primary"]:hover {
    background-color: #22d3ee;
    border-color: #22d3ee;
}

/* Success Button Style */
QPushButton[class="success"] {
    background-color: #06a77d;
    border: 2px solid #06a77d;
    color: #fff;
}

QPushButton[class="success"]:hover {
    background-color: #14b8a6;
    border-color: #14b8a6;
}

/* Danger Button Style */
QPushButton[class="danger"] {
    background-color: #b82c4c;
    border: 2px solid #b82c4c;
    color: #fff;
}

QPushButton[class="danger"]:hover {
    background-color: #d63384;
    border-color: #d63384;
}

/* Info Button Style */
QPushButton[class="info"] {
    background-color: #0891b2;
    border: 2px solid #0891b2;
    color: #fff;
}

QPushButton[class="info"]:hover {
    background-color: #06b6d4;
    border-color: #06b6d4;
}

QProgressBar { 
    border: 2px solid #0d7377; 
    height: 12px; 
    text-align: center; 
    border-radius: 6px; 
    background: #051515; 
}

QProgressBar::chunk { 
    background-color: #06b6d4; 
    border-radius: 4px; 
}

QSlider::groove:horizontal {
    background: #0d7377;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #06b6d4;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
    border: 2px solid #06b6d4;
}

QSlider::handle:horizontal:hover {
    background: #22d3ee;
    border: 2px solid #22d3ee;
}

QCheckBox { 
    spacing: 10px;
    color: #a8f0f5;
    font-weight: bold;
    font-size: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #0d7377;
    background-color: #051515;
}

QCheckBox::indicator:hover {
    border: 2px solid #06b6d4;
    background-color: #0f3e3e;
}

QCheckBox::indicator:checked {
    background-color: #06a77d;
    border: 2px solid #06a77d;
}

QLabel {
    color: #a8f0f5;
}

QScrollBar:vertical {
    border: none;
    background-color: #051515;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #0d7377;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #06b6d4;
}
"""

# Фиолетовая тема (Лена Ейтова)
LENA_LIGHT_BLUE_STYLE = """
QWidget { 
    background-color: #1a0a2e; 
    color: #d4a5ff; 
    font-family: 'Segoe UI'; 
}

QLineEdit, QTextEdit { 
    background-color: #0f0620; 
    border: 2px solid #8b5fbf; 
    border-radius: 6px; 
    padding: 8px; 
    color: #fff;
    selection-background-color: #8b5fbf;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #6a0dad;
}

QPushButton { 
    background-color: #1a0a2e; 
    border: 2px solid #3d1f52; 
    border-radius: 6px; 
    padding: 10px 15px; 
    font-weight: bold; 
    color: #d4a5ff;
    font-size: 11px;
    font-family: 'Segoe UI';
}

QPushButton:hover { 
    background-color: #281a42; 
    border-color: #8b5fbf; 
    color: #fff; 
}

QPushButton:pressed { 
    background-color: #0f0620; 
    border-color: #8b5fbf;
}

/* Primary Button Style */
QPushButton[class="primary"] {
    background-color: #8b5fbf;
    border: 2px solid #8b5fbf;
    color: #fff;
}

QPushButton[class="primary"]:hover {
    background-color: #6a0dad;
    border-color: #6a0dad;
}

/* Success Button Style */
QPushButton[class="success"] {
    background-color: #1e8449;
    border: 2px solid #1e8449;
    color: #fff;
}

QPushButton[class="success"]:hover {
    background-color: #27ae60;
    border-color: #27ae60;
}

/* Danger Button Style */
QPushButton[class="danger"] {
    background-color: #c0392b;
    border: 2px solid #c0392b;
    color: #fff;
}

QPushButton[class="danger"]:hover {
    background-color: #e74c3c;
    border-color: #e74c3c;
}

/* Info Button Style */
QPushButton[class="info"] {
    background-color: #7c3aed;
    border: 2px solid #7c3aed;
    color: #fff;
}

QPushButton[class="info"]:hover {
    background-color: #6d28d9;
    border-color: #6d28d9;
}

QProgressBar { 
    border: 2px solid #3d1f52; 
    height: 12px; 
    text-align: center; 
    border-radius: 6px; 
    background: #0f0620; 
}

QProgressBar::chunk { 
    background-color: #8b5fbf; 
    border-radius: 4px; 
}

QSlider::groove:horizontal {
    background: #3d1f52;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #8b5fbf;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
    border: 2px solid #8b5fbf;
}

QSlider::handle:horizontal:hover {
    background: #6a0dad;
    border: 2px solid #6a0dad;
}

QCheckBox { 
    spacing: 10px;
    color: #d4a5ff;
    font-weight: bold;
    font-size: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #3d1f52;
    background-color: #0f0620;
}

QCheckBox::indicator:hover {
    border: 2px solid #8b5fbf;
    background-color: #1a0a2e;
}

QCheckBox::indicator:checked {
    background-color: #8b5fbf;
    border: 2px solid #8b5fbf;
}

QLabel {
    color: #d4a5ff;
}

QScrollBar:vertical {
    border: none;
    background-color: #0f0620;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #3d1f52;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #8b5fbf;
}
"""

# Красная тема (Ульяна Долорес)
ULYANA_PINK_STYLE = """
QWidget { 
    background-color: #2a0a0a; 
    color: #ffb3ba; 
    font-family: 'Segoe UI'; 
}

QLineEdit, QTextEdit { 
    background-color: #1a0505; 
    border: 2px solid #dc143c; 
    border-radius: 6px; 
    padding: 8px; 
    color: #fff;
    selection-background-color: #dc143c;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #b21830;
}

QPushButton { 
    background-color: #2a0a0a; 
    border: 2px solid #4a1a1a; 
    border-radius: 6px; 
    padding: 10px 15px; 
    font-weight: bold; 
    color: #ffb3ba;
    font-size: 11px;
    font-family: 'Segoe UI';
}

QPushButton:hover { 
    background-color: #3d1515; 
    border-color: #dc143c; 
    color: #fff; 
}

QPushButton:pressed { 
    background-color: #200808; 
    border-color: #dc143c;
}

/* Primary Button Style */
QPushButton[class="primary"] {
    background-color: #dc143c;
    border: 2px solid #dc143c;
    color: #fff;
}

QPushButton[class="primary"]:hover {
    background-color: #b21830;
    border-color: #b21830;
}

/* Success Button Style */
QPushButton[class="success"] {
    background-color: #1e8449;
    border: 2px solid #1e8449;
    color: #fff;
}

QPushButton[class="success"]:hover {
    background-color: #27ae60;
    border-color: #27ae60;
}

/* Danger Button Style */
QPushButton[class="danger"] {
    background-color: #c0392b;
    border: 2px solid #c0392b;
    color: #fff;
}

QPushButton[class="danger"]:hover {
    background-color: #e74c3c;
    border-color: #e74c3c;
}

/* Info Button Style */
QPushButton[class="info"] {
    background-color: #ff5252;
    border: 2px solid #ff5252;
    color: #fff;
}

QPushButton[class="info"]:hover {
    background-color: #ff1744;
    border-color: #ff1744;
}

QProgressBar { 
    border: 2px solid #4a1a1a; 
    height: 12px; 
    text-align: center; 
    border-radius: 6px; 
    background: #1a0505; 
}

QProgressBar::chunk { 
    background-color: #dc143c; 
    border-radius: 4px; 
}

QSlider::groove:horizontal {
    background: #4a1a1a;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #dc143c;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
    border: 2px solid #dc143c;
}

QSlider::handle:horizontal:hover {
    background: #b21830;
    border: 2px solid #b21830;
}

QCheckBox { 
    spacing: 10px;
    color: #ffb3ba;
    font-weight: bold;
    font-size: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #4a1a1a;
    background-color: #1a0505;
}

QCheckBox::indicator:hover {
    border: 2px solid #dc143c;
    background-color: #2a0a0a;
}

QCheckBox::indicator:checked {
    background-color: #dc143c;
    border: 2px solid #dc143c;
}

QLabel {
    color: #ffb3ba;
}

QScrollBar:vertical {
    border: none;
    background-color: #1a0505;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #4a1a1a;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #dc143c;
}
"""

# Золотая тема (Слави - цвет сена)
SLAVI_PURPLE_STYLE = """
QWidget { 
    background-color: #1a1410; 
    color: #f4d8a0; 
    font-family: 'Segoe UI'; 
}

QLineEdit, QTextEdit { 
    background-color: #0f0a07; 
    border: 2px solid #d4af37; 
    border-radius: 6px; 
    padding: 8px; 
    color: #fff;
    selection-background-color: #d4af37;
}

QLineEdit:focus, QTextEdit:focus {
    border: 2px solid #c9a227;
}

QPushButton { 
    background-color: #1a1410; 
    border: 2px solid #3d3220; 
    border-radius: 6px; 
    padding: 10px 15px; 
    font-weight: bold; 
    color: #f4d8a0;
    font-size: 11px;
    font-family: 'Segoe UI';
}

QPushButton:hover { 
    background-color: #2a1f15; 
    border-color: #d4af37; 
    color: #fff; 
}

QPushButton:pressed { 
    background-color: #0f0a07; 
    border-color: #d4af37;
}

/* Primary Button Style */
QPushButton[class="primary"] {
    background-color: #d4af37;
    border: 2px solid #d4af37;
    color: #000;
}

QPushButton[class="primary"]:hover {
    background-color: #ffc107;
    border-color: #ffc107;
    color: #000;
}

/* Success Button Style */
QPushButton[class="success"] {
    background-color: #1e8449;
    border: 2px solid #1e8449;
    color: #fff;
}

QPushButton[class="success"]:hover {
    background-color: #27ae60;
    border-color: #27ae60;
}

/* Danger Button Style */
QPushButton[class="danger"] {
    background-color: #c0392b;
    border: 2px solid #c0392b;
    color: #fff;
}

QPushButton[class="danger"]:hover {
    background-color: #e74c3c;
    border-color: #e74c3c;
}

/* Info Button Style */
QPushButton[class="info"] {
    background-color: #daa520;
    border: 2px solid #daa520;
    color: #000;
}

QPushButton[class="info"]:hover {
    background-color: #ffc107;
    border-color: #ffc107;
    color: #000;
}

QProgressBar { 
    border: 2px solid #3d3220; 
    height: 12px; 
    text-align: center; 
    border-radius: 6px; 
    background: #0f0a07; 
}

QProgressBar::chunk { 
    background-color: #d4af37; 
    border-radius: 4px; 
}

QSlider::groove:horizontal {
    background: #3d3220;
    height: 8px;
    border-radius: 4px;
}

QSlider::handle:horizontal {
    background: #d4af37;
    width: 18px;
    margin: -5px 0;
    border-radius: 9px;
    border: 2px solid #d4af37;
}

QSlider::handle:horizontal:hover {
    background: #ffc107;
    border: 2px solid #ffc107;
}

QCheckBox { 
    spacing: 10px;
    color: #f4d8a0;
    font-weight: bold;
    font-size: 10px;
}

QCheckBox::indicator {
    width: 20px;
    height: 20px;
    border-radius: 4px;
    border: 2px solid #3d3220;
    background-color: #0f0a07;
}

QCheckBox::indicator:hover {
    border: 2px solid #d4af37;
    background-color: #1a1410;
}

QCheckBox::indicator:checked {
    background-color: #d4af37;
    border: 2px solid #d4af37;
}

QLabel {
    color: #f4d8a0;
}

QScrollBar:vertical {
    border: none;
    background-color: #0f0a07;
    width: 12px;
    border-radius: 6px;
}

QScrollBar::handle:vertical {
    background-color: #3d3220;
    border-radius: 6px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background-color: #d4af37;
}
"""