from PySide6.QtWidgets import QWidget, QPushButton, QVBoxLayout, QFrame
from PySide6.QtCore import Qt
from core.styles import apply_stylesheet

class CollapsibleBox(QWidget):
    def __init__(self, title="", parent=None):
        super().__init__(parent)
        self.setObjectName("CollapsibleBox")

        self.container = QFrame()
        self.container.setObjectName("CollapsibleContainer")

        self.toggle_button = QPushButton(f"▼  {title}")
        self.toggle_button.setObjectName("CollapsibleToggleButton")
        self.toggle_button.setCursor(Qt.PointingHandCursor)
        self.toggle_button.setSizePolicy(
            self.toggle_button.sizePolicy().Policy.Expanding,
            self.toggle_button.sizePolicy().Policy.Fixed
        )
        self.toggle_button.pressed.connect(self.on_pressed)

        self.content_area = QFrame()
        self.content_area.setObjectName("CollapsibleContentArea")
        
        self.content_layout = QVBoxLayout(self.content_area)
        self.content_layout.setContentsMargins(18, 16, 18, 18)
        self.content_layout.setSpacing(16)

        container_layout = QVBoxLayout(self.container)
        container_layout.setSpacing(0)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.toggle_button)
        container_layout.addWidget(self.content_area)

        main_layout = QVBoxLayout(self)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.addWidget(self.container)

        apply_stylesheet(self, "collapsible_box.qss")

        self.is_expanded = True
        self.content_area.setVisible(True)

    def add_widget(self, widget):
        self.content_layout.addWidget(widget)

    def add_layout(self, layout):
        self.content_layout.addLayout(layout)

    def on_pressed(self):
        self.is_expanded = not self.is_expanded
        if self.is_expanded:
            self.toggle_button.setText(self.toggle_button.text().replace("►", "▼"))
            self.content_area.setVisible(True)
        else:
            self.toggle_button.setText(self.toggle_button.text().replace("▼", "►"))
            self.content_area.setVisible(False)

    def collapse(self):
        if self.is_expanded:
            self.on_pressed()
            
    def expand(self):
        if not self.is_expanded:
            self.on_pressed()
