import logging
from PySide6.QtWidgets import QTextEdit

class LogHandler(logging.Handler):
    """Custom logging handler to output logs to a QTextEdit widget as HTML."""
    def __init__(self, text_widget: QTextEdit):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)
        self.text_widget.append(msg)

def setup_logging(text_widget: QTextEdit):
    """Redirects Python logging to the console text widget using HTML formatting."""
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    # Ensure we don't add multiple handlers if initialized multiple times
    if not logger.handlers:
        handler = LogHandler(text_widget)
        formatter = logging.Formatter(
            '<span style="color:#89b4fa;">%(asctime)s</span> <span style="color:#f38ba8;">[%(levelname)s]</span> <span style="color:#a6e3a1;">%(message)s</span>', 
            datefmt='%H:%M:%S'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
