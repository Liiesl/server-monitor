from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel, QGroupBox, QHBoxLayout, QPushButton, QGridLayout
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon
import qtawesome as qta
import math

# --- Import the custom gauge widget ---
from view.widgets import HalfCircleGauge

# --- Widget for the main dashboard ---
class DashboardWidget(QWidget):
    """
    A widget that shows a high-level summary of all PM2 processes,
    now featuring resource gauges.
    """
    restart_all_requested = Signal()
    stop_all_requested = Signal()
    start_daemon_requested = Signal()
    kill_daemon_requested = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # --- Title ---
        title_label = QLabel("System Dashboard")
        title_font = title_label.font()
        title_font.setPointSize(20)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        main_layout.addWidget(title_label)

        # --- Daemon Status Label ---
        self.daemon_status_label = QLabel()
        self.daemon_status_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        font = self.daemon_status_label.font()
        font.setBold(True)
        self.daemon_status_label.setFont(font)
        main_layout.addWidget(self.daemon_status_label)

        # Grid for stat boxes
        grid_layout = QGridLayout()
        grid_layout.setSpacing(20)

        # --- Overview Group ---
        overview_group = QGroupBox("Process Overview")
        overview_layout = QVBoxLayout()
        self.total_val = self._create_stat_label("Total Projects: 0")
        self.online_val = self._create_stat_label("Online: 0", "#4CAF50")
        self.stopped_val = self._create_stat_label("Stopped: 0", "#FFC107")
        self.errored_val = self._create_stat_label("Errored: 0", "#F44336")
        self.undeployed_val = self._create_stat_label("Undeployed: 0")
        overview_layout.addWidget(self.total_val)
        overview_layout.addWidget(self.online_val)
        overview_layout.addWidget(self.stopped_val)
        overview_layout.addWidget(self.errored_val)
        overview_layout.addWidget(self.undeployed_val)
        overview_group.setLayout(overview_layout)
        grid_layout.addWidget(overview_group, 0, 0)

        # --- MODIFICATION: Resource Group with Gauges ---
        resource_group = QGroupBox("Resource Usage (Online Processes)")
        # Use QHBoxLayout to place gauges side-by-side
        resource_layout = QHBoxLayout()
        
        # Create gauge instances instead of labels
        self.cpu_gauge = HalfCircleGauge(title="Total CPU", unit="%")
        self.mem_gauge = HalfCircleGauge(title="Total Memory", unit=" MB")
        
        resource_layout.addWidget(self.cpu_gauge)
        resource_layout.addWidget(self.mem_gauge)
        
        resource_group.setLayout(resource_layout)
        grid_layout.addWidget(resource_group, 0, 1)

        # --- Global Actions Group ---
        actions_group = QGroupBox("Global Actions")
        actions_layout = QHBoxLayout()

        self.start_daemon_button = QPushButton(qta.icon('fa5s.play-circle', color='#4CAF50'), "Start PM2 Daemon")
        self.kill_daemon_button = QPushButton(qta.icon('fa5s.skull-crossbones', color='#F44336'), "Kill PM2 Daemon")
        self.restart_all_button = QPushButton(QIcon.fromTheme("system-reboot"), "Restart All")
        self.stop_all_button = QPushButton(QIcon.fromTheme("process-stop"), "Stop All")

        self.start_daemon_button.clicked.connect(self.start_daemon_requested)
        self.kill_daemon_button.clicked.connect(self.kill_daemon_requested)
        self.restart_all_button.clicked.connect(self.restart_all_requested)
        self.stop_all_button.clicked.connect(self.stop_all_requested)

        actions_layout.addStretch()
        actions_layout.addWidget(self.start_daemon_button)
        actions_layout.addWidget(self.kill_daemon_button)
        actions_layout.addSpacing(30)
        actions_layout.addWidget(self.restart_all_button)
        actions_layout.addWidget(self.stop_all_button)
        actions_layout.addStretch()
        actions_group.setLayout(actions_layout)
        grid_layout.addWidget(actions_group, 1, 0, 1, 2) # Span across 2 columns

        grid_layout.setRowStretch(2, 1)
        grid_layout.setColumnStretch(0, 1)
        grid_layout.setColumnStretch(1, 1)
        main_layout.addLayout(grid_layout)

    def _create_stat_label(self, text, color=None):
        label = QLabel(text)
        font = label.font()
        font.setPointSize(14)
        label.setFont(font)
        if color:
            label.setStyleSheet(f"color: {color}; font-weight: bold;")
        return label
    
    def set_daemon_status(self, is_running):
        self.start_daemon_button.setEnabled(not is_running)
        self.kill_daemon_button.setEnabled(is_running)

        if is_running:
            self.daemon_status_label.setText("<p style='color: #4CAF50;'>PM2 Daemon is Running</p>")
        else:
            self.daemon_status_label.setText("<p style='color: #F44336;'>PM2 Daemon is Stopped. Start it to manage processes.</p>")
            self.update_stats([]) # Clear stats if daemon is down
            # --- MODIFICATION: Set gauges to N/A when daemon is down ---
            self.cpu_gauge.setValue(-1)
            self.mem_gauge.setValue(-1)

    def update_stats(self, all_processes_data):
        total_count = len(all_processes_data)
        online_count = 0
        stopped_count = 0
        errored_count = 0
        undeployed_count = 0
        total_cpu = 0
        total_mem_bytes = 0

        for proc in all_processes_data:
            status = proc.get('pm2_env', {}).get('status', 'undeployed')
            if status == 'online':
                online_count += 1
                total_cpu += proc.get('monit', {}).get('cpu', 0)
                total_mem_bytes += proc.get('monit', {}).get('memory', 0)
            elif status in ['stopped', 'stopping']:
                stopped_count += 1
            elif status == 'errored':
                errored_count += 1
            else: # undeployed
                undeployed_count += 1

        total_mem_mb = math.ceil(total_mem_bytes / (1024 * 1024)) if total_mem_bytes > 0 else 0

        self.total_val.setText(f"Total Projects: {total_count}")
        self.online_val.setText(f"Online: {online_count}")
        self.stopped_val.setText(f"Stopped: {stopped_count}")
        self.errored_val.setText(f"Errored: {errored_count}")
        self.undeployed_val.setText(f"Undeployed: {undeployed_count}")
        
        # --- MODIFICATION: Update gauges instead of labels ---

        # Update CPU Gauge, dynamically adjusting the max value
        # Clamp at a minimum of 100% for the max value, but allow it to grow
        # for multi-core systems (e.g., 150% usage sets max to 200%).
        cpu_max = max(100, math.ceil(total_cpu / 100) * 100 if total_cpu > 0 else 100)
        self.cpu_gauge.setMaxValue(cpu_max)
        self.cpu_gauge.setValue(total_cpu)

        # Update Memory Gauge, dynamically adjusting the max value to the next
        # sensible tier (e.g., 600MB usage sets max to 1024MB).
        mem_tiers_mb = [256, 512, 1024, 2048, 4096, 8192, 16384, 32768]
        mem_max = mem_tiers_mb[2]  # Default to 1024MB
        for tier in mem_tiers_mb:
            if total_mem_mb < tier:
                mem_max = tier
                break
        else:  # If memory usage is higher than all defined tiers
            mem_max = math.ceil(total_mem_mb * 1.2) # Set max to 20% more than current

        self.mem_gauge.setMaxValue(mem_max)
        self.mem_gauge.setValue(total_mem_mb)
        
        # --- End of Gauge Modification ---

        can_act = online_count > 0 or stopped_count > 0 or errored_count > 0
        self.restart_all_button.setEnabled(can_act)
        self.stop_all_button.setEnabled(online_count > 0)