# log_view.py

import re
from datetime import datetime
# MODIFIED: Changed imports from PyQt5 to PySide6
from PySide6.QtWidgets import QWidget, QVBoxLayout, QGroupBox, QPlainTextEdit
from PySide6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

# --- NEW: Log Viewer Widget ---
# This class encapsulates the log viewing functionality, making it reusable and customizable.
class LogViewerWidget(QWidget):
    """
    A dedicated widget for displaying log output. It provides a clean,
    two-column view by parsing each line to extract the original timestamp
    and aggressively cleaning the log message of any prefixes or redundant data.
    """
    def __init__(self, parent=None):
        print("[DEBUG] Initializing LogViewerWidget")
        super().__init__(parent)

        
        # --- Pre-compile regex patterns for performance ---
        print("[DEBUG] Compiling regex patterns for log cleaning")
        self._ansi_escape_pattern = re.compile(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])')
        
        # 2. Matches and removes the PM2 process prefix, e.g., "0|app  | "
        self._pm2_prefix_pattern = re.compile(r'^\d+\|\w+\s*\|\s*')
        
        # 3. Finds and captures the primary timestamp at the start of a log line
        self._log_timestamp_pattern = re.compile(
            # Capture Group 1: The timestamp itself
            r'^(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}(?:\s+[+-]\d{2}:\d{2})?)'
            # Match the following separator but don't capture it
            r'\s*:\s*'
        )
        
        # 4. Finds and removes the redundant inner UTC timestamp, e.g., "[... UTC] "
        self._utc_timestamp_pattern = re.compile(r'\[\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2}\s+UTC\]\s*')

        print("[DEBUG] Setting up text formats for log display")
        self.timestamp_format = QTextCharFormat()
        self.timestamp_format.setForeground(QColor("#757575")) # A muted grey

        self.error_format = QTextCharFormat()
        self.error_format.setForeground(QColor("#E53935")) # A clear red

        self.default_format = QTextCharFormat()

        self.init_ui()

    def init_ui(self):
        print("[DEBUG] Setting up LogViewerWidget UI")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        logs_group = QGroupBox("Logs")
        logs_layout = QVBoxLayout(logs_group)
        self.log_view = QPlainTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setFont(QFont("Monospace", 10))
        self.log_view.setMinimumHeight(150)
        logs_layout.addWidget(self.log_view)
        layout.addWidget(logs_group)
        print("[DEBUG] LogViewerWidget UI setup complete")

    def _parse_and_format_line(self, cursor, raw_line):
        """
        Processes a raw log line through multiple cleaning stages and inserts
        the formatted result into the text view.
        """
        # Stage 1: Basic cleaning of prefixes and colors.
        line = self._ansi_escape_pattern.sub('', raw_line)
        line = self._pm2_prefix_pattern.sub('', line).strip()

        # Stage 2: Determine the timestamp and the initial message.
        match = self._log_timestamp_pattern.match(line)
        if match:
            # A timestamp was found in the log itself. Use it.
            display_timestamp = match.group(1).strip()
            # The message is whatever comes after the full matched pattern.
            message = line[match.end():].strip()
        else:
            # Fallback: No timestamp found. Generate one and use the whole line as the message.
            display_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            message = line

        # Stage 3: Advanced cleaning of the message content.
        # Remove any inner UTC timestamps.
        message = self._utc_timestamp_pattern.sub('', message)
        # Remove any leftover colons or spaces from the start.
        message = message.lstrip(': ')

        # Stage 4: Determine message format (highlight errors)
        is_error = 'error' in message.lower() or 'exception' in message.lower()
        message_format = self.error_format if is_error else self.default_format

        # Stage 5: Insert the final, clean parts into the text edit.
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(f"{display_timestamp} ", self.timestamp_format)
        cursor.insertText(message + '\n', message_format)


    def update_logs(self, log_text):
        """
        Clears the view and appends new log text line-by-line, parsing each one.
        """
        self.log_view.setReadOnly(False)
        self.log_view.clear()
        
        cursor = self.log_view.textCursor()
        
        if not log_text.strip():
            cursor.insertText("No log output available for this process.", self.timestamp_format)
            self.log_view.setReadOnly(True)
            return
            
        lines = log_text.strip().split('\n')
        
        for line in lines:
            if line.strip(): # Process only non-empty lines
                self._parse_and_format_line(cursor, line)
        
        self.log_view.setReadOnly(True)
        self.log_view.verticalScrollBar().setValue(self.log_view.verticalScrollBar().maximum())

    def clear(self):
        """Clears all text from the log view."""
        self.log_view.clear()