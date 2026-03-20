MODERN_STYLE = """
* {
    font-family: 'Inter', 'Roboto', 'Segoe UI', sans-serif;
    border-radius: 0px;
}

/* Ventana Principal */
QMainWindow {
    background-color: #1a1a1a;
}

/* Divisores (Splitters) */
QSplitter::handle {
    background-color: #333333;
    width: 2px;
    height: 2px;
}

/* Sidebar Container */
#SidebarWidget {
    background-color: #121212;
}

/* Botones Principales Sidebar */
#SidebarWidget QPushButton {
    text-align: left;
    padding: 12px 25px;
    background-color: transparent;
    color: #e0e0e0;
    border: none;
    border-left: 4px solid transparent;
    font-size: 14px;
    outline: none;
}
#SidebarWidget QPushButton:hover {
    background-color: #2a2a2a;
}
#SidebarWidget QPushButton:checked {
    color: #ffffff;
    border-left: 4px solid #ffffff;
    background-color: #2a2a2a;
    font-weight: bold;
}

/* Sub-botones Sidebar */
#SidebarWidget QPushButton[is_sub="true"] {
    padding: 10px 10px 10px 40px;
    font-size: 13px;
    color: #d4d4d4;
}
#SidebarWidget QPushButton[is_sub="true"]:hover {
    color: #e0e0e0;
    background-color: #2a2a2a;
}

/* Dropdown Modelos button */
#SidebarWidget QPushButton[is_dropdown="true"] {
    text-align: left;
    padding: 12px 25px;
    background-color: transparent;
    color: #e0e0e0;
    border: none;
    font-size: 14px;
    font-weight: bold;
    outline: none;
}
#SidebarWidget QPushButton[is_dropdown="true"]:hover {
    background-color: #2a2a2a;
}

/* Lista dinámica de modelos */
#SidebarWidget QListWidget {
    background-color: transparent;
    color: #e0e0e0;
    border: none;
    outline: none;
    font-size: 13px;
    padding-left: 35px;
}
#SidebarWidget QListWidget::item {
    padding: 5px 0px;
}
#SidebarWidget QListWidget::item:hover {
    color: #ffffff;
}
#SidebarWidget QListWidget::item:selected {
    background-color: #333333;
    color: #ffffff;
    font-weight: bold;
}

/* Área de Trabajo */
QStackedWidget {
    background-color: #1a1a1a;
}

QLabel {
    color: #e0e0e0;
    font-size: 16px;
}

/* Consola */
QTextEdit {
    background-color: #0d0d0d;
    color: #cccccc;
    border: 1px solid #333333;
    padding: 15px;
    font-family: 'Courier New', monospace;
    font-size: 13px;
    selection-background-color: #404040;
}

/* Scrollbars Verticales */
QScrollBar:vertical {
    border: none;
    background: #121212;
    width: 12px;
    margin: 0px;
}
QScrollBar::handle:vertical {
    background: #404040;
    min-height: 25px;
}
QScrollBar::handle:vertical:hover {
    background: #606060;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    border: none;
    background: none;
}
"""
