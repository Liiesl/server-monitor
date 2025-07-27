# sidebar.py
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel, QPushButton
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import qtawesome as qta

# --- Custom widget for items in the project list ---
class ProjectListItemWidget(QWidget):
    """A custom widget for displaying a project in the QListWidget, including a settings button."""
    settings_requested = Signal(str) # Emits project name

    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.project_name = project_data.get('name', 'N/A')

        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(10)

        # --- MODIFIED: Store labels as instance attributes ---
        self.icon_label = QLabel()
        self.name_label = QLabel(self.project_name)

        layout.addWidget(self.icon_label)
        layout.addWidget(self.name_label)
        layout.addStretch()

        # Settings Button (unchanged)
        settings_button = QPushButton(qta.icon('fa5s.cog'), "")
        settings_button.setFlat(True)
        settings_button.setFixedSize(24, 24)
        settings_button.setIconSize(settings_button.size() * 0.75)
        settings_button.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_button.setToolTip(f"Configure '{self.project_name}'")
        settings_button.clicked.connect(self.emit_settings_request)
        layout.addWidget(settings_button)

        # Apply initial status and styles
        self.update_status(project_data)

    # --- NEW: The missing method that caused the crash ---
    def update_status(self, project_data):
        """Updates the icon and label color based on new project data."""
        status = project_data.get('pm2_env', {}).get('status', 'undeployed')

        # Update Status Icon
        if status == 'online':
            icon = QIcon.fromTheme("presence-online")
            self.name_label.setStyleSheet("color: #4CAF50;") # Green
        elif status in ['stopped', 'stopping']:
            icon = QIcon.fromTheme("presence-offline")
            self.name_label.setStyleSheet("color: #FFC107;") # Amber
        elif status == 'errored':
            icon = QIcon.fromTheme("presence-busy")
            self.name_label.setStyleSheet("color: #F44336;") # Red
        else: # Covers 'undeployed' or any other state
            icon = QIcon.fromTheme("presence-unknown")
            self.name_label.setStyleSheet("") # Reset to default theme color
        
        self.icon_label.setPixmap(icon.pixmap(16, 16))


    def emit_settings_request(self):
        self.settings_requested.emit(self.project_name)