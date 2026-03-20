import pandas as pd
import sys
from PySide6.QtWidgets import QApplication

from views.main_window import MainWindow

if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Intentar usar una fuente amigable/moderna globalmente
    font = app.font()
    font.setFamily("Helvetica Neue") # Común en macOS
    font.setPointSize(11)
    app.setFont(font)
    
    window = MainWindow()
    window.showMaximized()
    sys.exit(app.exec())
