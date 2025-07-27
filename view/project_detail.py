# project_detail.py
import math, os, time
from PySide6.QtWidgets import ( QWidget, QPushButton, QVBoxLayout, QGridLayout, QLabel,
                             QGroupBox, QHBoxLayout, QFormLayout, QTabWidget, QScrollArea, QFrame,
                             QPlainTextEdit)
from PySide6.QtCore import Signal, Qt
from PySide6.QtGui import QIcon, QFont
import qtawesome as qta
from view.widgets import HalfCircleGauge, PerformanceGraphWidget, LogViewerWidget 

# --- Widget for showing details and actions for a single project (UPDATED) ---
class ProjectDetailWidget(QWidget):
    """
    A dashboard widget to display details, configuration, and actions for a selected PM2 project.
    All content is placed within a single scrollable area.
    """
    start_requested = Signal(dict) # Pass full project dict
    stop_requested = Signal(str)
    restart_requested = Signal(str)
    reload_requested = Signal(str)
    delete_from_pm2_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_project = None
        self.init_ui()
        self.clear_details()

    def init_ui(self):
        # The main layout will simply hold the scroll area
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Create a scrollable area for all content ---
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame) # Makes it seamless with the background

        # Create a container widget that will hold all the details and be placed inside the scroll area
        scroll_content_widget = QWidget()
        content_layout = QVBoxLayout(scroll_content_widget)
        content_layout.setContentsMargins(15, 15, 15, 15)
        content_layout.setSpacing(15)

        # --- Actions Group ---
        actions_group = QGroupBox("Actions")
        actions_layout = QHBoxLayout()
        self.start_button = QPushButton(QIcon.fromTheme("media-playback-start"), "Start")
        self.stop_button = QPushButton(QIcon.fromTheme("media-playback-stop"), "Stop")
        self.restart_button = QPushButton(QIcon.fromTheme("view-refresh"), "Restart")
        self.reload_button = QPushButton(QIcon.fromTheme("document-revert"), "Reload")
        self.delete_button = QPushButton(qta.icon('fa5s.trash-alt', color='#F44336'), "Delete")
        self.delete_button.setToolTip("Stops and deletes the process from PM2.\nThe project configuration remains in this app.")

        self.start_button.clicked.connect(lambda: self.current_project and self.start_requested.emit(self.current_project))
        self.stop_button.clicked.connect(lambda: self.current_project and self.stop_requested.emit(self.current_project['name']))
        self.restart_button.clicked.connect(lambda: self.current_project and self.restart_requested.emit(self.current_project['name']))
        self.reload_button.clicked.connect(lambda: self.current_project and self.reload_requested.emit(self.current_project['name']))
        self.delete_button.clicked.connect(lambda: self.current_project and self.delete_from_pm2_requested.emit(self.current_project['name']))

        actions_layout.addWidget(self.start_button)
        actions_layout.addWidget(self.stop_button)
        actions_layout.addWidget(self.restart_button)
        actions_layout.addWidget(self.reload_button)
        actions_layout.addWidget(self.delete_button)
        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        content_layout.addWidget(actions_group)

        # --- Details Grid ---
        details_grid = QGridLayout()
        details_grid.setSpacing(20)
        details_grid.setColumnStretch(0, 1)
        details_grid.setColumnStretch(1, 1)
        details_grid.setColumnStretch(2, 1)
        details_grid.setColumnStretch(3, 1)

        # Row 0: Name
        self.name_val = QLabel("Select a project")
        name_font = self.name_val.font()
        name_font.setPointSize(18)
        name_font.setBold(True)
        self.name_val.setFont(name_font)
        details_grid.addWidget(self.name_val, 0, 0, 1, 4)
        self.name_val.setAlignment(Qt.AlignmentFlag.AlignCenter)  # Center the name label
        # Row 1: Key Stats
        self.status_val = self._create_stat_box(details_grid, 1, 0, "STATUS")
        self.uptime_val = self._create_stat_box(details_grid, 1, 1, "UPTIME")
        self.restarts_val = self._create_stat_box(details_grid, 1, 2, "RESTARTS")
        self.id_val = self._create_stat_box(details_grid, 1, 3, "PM2 ID")

        # Row 2: Gauges
        self.cpu_gauge = HalfCircleGauge("CPU", "%")
        self.mem_gauge = HalfCircleGauge("MEMORY", " MB")
        details_grid.addWidget(self.cpu_gauge, 2, 0, 1, 2)
        details_grid.addWidget(self.mem_gauge, 2, 2, 1, 2)

        # Row 3: Performance Graphs
        self.performance_graphs = PerformanceGraphWidget()
        self.performance_graphs.setFixedHeight(250)
        details_grid.addWidget(self.performance_graphs, 3, 0, 1, 4)

        # Initialize all detail labels
        self.path_val = QLabel(); self.path_val.setWordWrap(True)
        self.interpreter_val = QLabel()
        self.node_args_val = QLabel(); self.node_args_val.setWordWrap(True)
        self.args_val = QLabel(); self.args_val.setWordWrap(True)
        self.watch_val = QLabel()
        self.max_mem_val = QLabel()
        self.exec_mode_val = QLabel()
        self.instances_val = QLabel()
        self.autorestart_val = QLabel()
        self.out_log_val = QLabel(); self.out_log_val.setWordWrap(True)
        self.error_log_val = QLabel(); self.error_log_val.setWordWrap(True)

        # Row 4: Two-column detailed info
        paths_group = QGroupBox("Paths & Arguments")
        paths_layout = QFormLayout(paths_group)
        paths_layout.setSpacing(10)
        paths_layout.addRow("<b>Script Path:</b>", self.path_val)
        paths_layout.addRow("<b>Script Args:</b>", self.args_val)
        paths_layout.addRow("<b>Interpreter Args:</b>", self.node_args_val)
        paths_layout.addRow("<b>Output Log:</b>", self.out_log_val)
        paths_layout.addRow("<b>Error Log:</b>", self.error_log_val)

        exec_group = QGroupBox("Execution & Monitoring")
        exec_layout = QFormLayout(exec_group)
        exec_layout.setSpacing(10)
        exec_layout.addRow("<b>Interpreter:</b>", self.interpreter_val)
        exec_layout.addRow("<b>Exec Mode:</b>", self.exec_mode_val)
        exec_layout.addRow("<b>Instances:</b>", self.instances_val)
        exec_layout.addRow("<b>Autorestart:</b>", self.autorestart_val)
        exec_layout.addRow("<b>Watch Mode:</b>", self.watch_val)
        exec_layout.addRow("<b>Max Memory Restart:</b>", self.max_mem_val)

        details_grid.addWidget(paths_group, 4, 0, 1, 2)
        details_grid.addWidget(exec_group, 4, 2, 1, 2)

        # UPDATED: Row 5 for logs, using the dedicated LogViewerWidget
        self.log_viewer = LogViewerWidget()
        details_grid.addWidget(self.log_viewer, 5, 0, 1, 4)

        content_layout.addLayout(details_grid)
        content_layout.addStretch(1) # Push all content up

        # Finalize the layout
        scroll_area.setWidget(scroll_content_widget)
        main_layout.addWidget(scroll_area)

    def _create_stat_box(self, grid, row, col, title):
        """Helper to create a small stat box with a title and value."""
        v_layout = QVBoxLayout()
        v_layout.setSpacing(0)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: #AAA; font-size: 9pt;")

        value_label = QLabel("N/A")
        font = value_label.font()
        font.setPointSize(14)
        font.setBold(True)
        value_label.setFont(font)

        v_layout.addWidget(title_label)
        v_layout.addWidget(value_label)
        v_layout.addStretch()

        grid.addLayout(v_layout, row, col)
        return value_label

    def update_logs(self, log_text):
        """Public method to set the content of the log view by delegating to the LogViewerWidget."""
        self.log_viewer.update_logs(log_text)

    # --- MODIFIED: Method signature now accepts the new argument ---
    def update_details(self, project_data, is_new_selection=False):
        # --- MODIFIED: Use the new argument to decide whether to clear data ---
        # If it's a new project selection, clear the performance graphs and logs to start fresh
        if is_new_selection:
            self.performance_graphs.clear()
            self.log_viewer.clear()

        self.current_project = project_data
        name = project_data.get('name', 'N/A')

        pm2_env = project_data.get('pm2_env', {})
        monit = project_data.get('monit', {})
        status = pm2_env.get('status', 'undeployed')
        is_in_pm2 = 'pm_id' in project_data
        is_online = (status == 'online')

        # --- Extract performance data ---
        cpu_val = monit.get('cpu', 0) if is_in_pm2 else 0
        mem_bytes = monit.get('memory', 0) if is_in_pm2 else 0
        mem_mb = math.ceil(mem_bytes / (1024 * 1024)) if mem_bytes > 0 else 0

        # --- Update performance graphs ---
        self.performance_graphs.update_data(cpu_val, mem_mb)

        # --- Update Displayed Values ---
        self.name_val.setText(name)
        self.path_val.setText(os.path.join(project_data.get('path', 'N/A'), project_data.get('script', '')))

        # Status box
        self.status_val.setText(f"{status.capitalize()}")
        if status == 'online': self.status_val.setStyleSheet("color: #4CAF50;") # Green
        elif status in ['stopped', 'stopping']: self.status_val.setStyleSheet("color: #FFC107;") # Amber
        elif status == 'errored': self.status_val.setStyleSheet("color: #F44336;") # Red
        else: self.status_val.setStyleSheet("")

        if is_in_pm2:
            self.id_val.setText(str(project_data.get('pm_id', 'N/A')))
            self.restarts_val.setText(str(pm2_env.get('restart_time', 0)))
            uptime_ms = pm2_env.get('pm_uptime', 0)
            uptime_secs = (time.time() * 1000 - uptime_ms) / 1000 if uptime_ms > 0 else 0
            self.uptime_val.setText(self.format_uptime(uptime_secs))

            # Update Gauges
            self.cpu_gauge.setValue(cpu_val)
            max_mem_str = project_data.get('max_memory_restart')
            max_mem_mb = self._parse_mem_str_to_mb(max_mem_str)
            if max_mem_mb:
                self.mem_gauge.setMaxValue(max_mem_mb)
                self.mem_gauge.setValue(mem_mb)
            else:
                self.mem_gauge.setMaxValue(1)
                self.mem_gauge.setValue(-1)
                self.mem_gauge.setText(f"{mem_mb} MB")

        else: # Not running in PM2
            for label in [self.id_val, self.restarts_val, self.uptime_val]:
                label.setText("N/A")
            self.cpu_gauge.setValue(-1)
            self.mem_gauge.setValue(-1)

        # Update config/exec details
        self.interpreter_val.setText(project_data.get('interpreter') or "Default (Node.js)")
        self.node_args_val.setText(str(project_data.get('node_args', 'None') or 'None'))
        self.args_val.setText(str(project_data.get('args', 'None') or 'None'))
        self.watch_val.setText("Enabled" if project_data.get('watch', False) else "Disabled")
        self.max_mem_val.setText(project_data.get('max_memory_restart') or "Not Set")

        exec_mode = project_data.get('exec_mode', 'fork')
        self.exec_mode_val.setText(exec_mode.capitalize())
        self.instances_val.setText(str(project_data.get('instances', 'N/A')) if exec_mode == 'cluster' else '1')
        self.autorestart_val.setText("Enabled" if project_data.get('autorestart', True) else "Disabled")
        self.out_log_val.setText(pm2_env.get('pm_out_log_path') or project_data.get('out_file') or "Default")
        self.error_log_val.setText(pm2_env.get('pm_err_log_path') or project_data.get('error_file') or "Default")

        # --- Update Button States ---
        self.start_button.setEnabled(not is_online)
        self.stop_button.setEnabled(is_online)
        self.restart_button.setEnabled(is_in_pm2)
        self.reload_button.setEnabled(is_online)
        self.delete_button.setEnabled(is_in_pm2)

    def _parse_mem_str_to_mb(self, mem_str):
        if not mem_str or not isinstance(mem_str, str): return None
        mem_str = mem_str.upper().strip()
        try:
            if mem_str.endswith('G'): return int(mem_str[:-1]) * 1024
            if mem_str.endswith('M'): return int(mem_str[:-1])
            if mem_str.endswith('K'): return int(mem_str[:-1]) / 1024
            return int(mem_str) / (1024*1024) # Assume bytes if no unit
        except (ValueError, TypeError):
            return None

    def clear_details(self):
        """Resets the view to a default blank state."""
        self.current_project = None
        self.name_val.setText("Select a project to see details")
        for label in [self.status_val, self.uptime_val, self.restarts_val, self.id_val,
                      self.path_val, self.interpreter_val, self.node_args_val,
                      self.args_val, self.watch_val, self.max_mem_val, self.exec_mode_val,
                      self.instances_val, self.autorestart_val, self.out_log_val,
                      self.error_log_val]:
            label.setText("N/A")
            label.setStyleSheet("")

        self.cpu_gauge.setValue(-1) # Set to N/A state
        self.mem_gauge.setValue(-1) # Set to N/A state

        if hasattr(self, 'performance_graphs'):
            self.performance_graphs.clear()
        if hasattr(self, 'log_viewer'):
            self.log_viewer.clear()

        for button in [self.start_button, self.stop_button, self.restart_button, self.reload_button, self.delete_button]:
            button.setEnabled(False)

    def format_uptime(self, seconds):
        if seconds <= 0: return "0s"
        days, rem = divmod(seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, secs = divmod(rem, 60)
        parts = []
        if days > 0: parts.append(f"{int(days)}d")
        if hours > 0: parts.append(f"{int(hours)}h")
        if minutes > 0: parts.append(f"{int(minutes)}m")
        if not parts and seconds > 0: parts.append(f"{int(secs)}s")
        return " ".join(parts) if parts else "0s"