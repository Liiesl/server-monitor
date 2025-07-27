# --- Dark Mode Stylesheet ---
DARK_STYLE = """
QWidget {
    background-color: #2b2b2b;
    color: #f0f0f0;
    border: 0px;
    font-family: Segoe UI, sans-serif;
}

QToolBar {
    background-color: #3c3c3c;
    spacing: 5px;
    padding: 5px;
}
QToolBar::handle {
    image: none;
}
QToolBar QToolButton {
    background-color: #3c3c3c;
    border: 1px solid #3c3c3c;
    padding: 3px;
}
QToolBar QToolButton:hover {
    background-color: #555555;
    border: 1px solid #666666;
}
QToolBar QToolButton:pressed {
    background-color: #444444;
}

QStatusBar {
    background-color: #3c3c3c;
}
QStatusBar::item {
    border: none;
}

QMainWindow {
    background-color: #2b2b2b;
}

QGroupBox {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    border-radius: 5px;
    margin-top: 1ex;
    font-weight: bold;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top center;
    padding: 0 5px;
}

QLabel {
    background-color: transparent;
}

QListWidget {
    background-color: #3c3c3c;
    border: 1px solid #555555;
    padding: 5px;
}
QListWidget::item {
    padding: 5px;
}
QListWidget::item:selected {
    background-color: #0078d7;
    color: #ffffff;
}
QListWidget::item:hover:!selected {
    background-color: #4a4a4a;
}

QPushButton {
    background-color: #555555;
    border: 1px solid #666666;
    padding: 8px;
    border-radius: 4px;
}
QPushButton:hover {
    background-color: #666666;
    border: 1px solid #777777;
}
QPushButton:pressed {
    background-color: #444444;
}
QPushButton:disabled {
    color: #888888;
    background-color: #404040;
}

QPlainTextEdit, QTextEdit {
    background-color: #252525;
    border: 1px solid #555555;
    color: #f0f0f0;
    padding: 5px;
    border-radius: 4px;
}

QScrollBar:vertical {
    border: none;
    background: #3c3c3c;
    width: 12px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:vertical {
    background: #666666;
    min-height: 20px;
    border-radius: 6px;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    border: none;
    background: #3c3c3c;
    height: 12px;
    margin: 0px 0px 0px 0px;
}
QScrollBar::handle:horizontal {
    background: #666666;
    min-width: 20px;
    border-radius: 6px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0px;
}
QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

QSplitter::handle {
    background-color: #555555;
}
QSplitter::handle:horizontal {
    width: 1px;
}
QSplitter::handle:vertical {
    height: 1px;
}

QMessageBox {
    background-color: #3c3c3c;
}
QDialog {
     background-color: #3c3c3c;
}
"""