# settings_dialog.py
import os
from PySide6.QtWidgets import ( QDialog, QFormLayout, QLineEdit, QHBoxLayout, QPushButton,
                              QDialogButtonBox, QFileDialog, QCheckBox, QGroupBox, 
                              QVBoxLayout, QPlainTextEdit, QMessageBox, QComboBox )
from PySide6.QtCore import Qt

class ProjectSettingsDialog(QDialog):
    """A dialog for configuring all project settings, mapping to PM2 ecosystem options."""
    def __init__(self, project_data, parent=None):
        super().__init__(parent)
        self.setWindowTitle(f"Settings for '{project_data.get('name')}'")
        self.setMinimumWidth(550)
        
        self.original_data = project_data

        main_layout = QVBoxLayout(self)
        
        # --- Core Settings Group ---
        core_group = QGroupBox("Core Configuration")
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        self.script_path_edit = QLineEdit()
        browse_button = QPushButton("Browse...")
        browse_button.clicked.connect(self.browse_for_script)
        script_layout = QHBoxLayout()
        script_layout.addWidget(self.script_path_edit)
        script_layout.addWidget(browse_button)
        form_layout.addRow("Project Name:", self.name_edit)
        form_layout.addRow("Script Path:", script_layout)
        core_group.setLayout(form_layout)
        main_layout.addWidget(core_group)

        # --- Execution Settings Group ---
        exec_group = QGroupBox("Execution Settings")
        exec_layout = QFormLayout()
        self.exec_mode_combo = QComboBox()
        self.exec_mode_combo.addItems(["fork", "cluster"])
        self.instances_edit = QLineEdit()
        self.instances_edit.setPlaceholderText("e.g., 4, 'max'")
        self.exec_mode_combo.currentTextChanged.connect(lambda mode: self.instances_edit.setEnabled(mode == 'cluster'))
        self.interpreter_edit = QLineEdit()
        self.interpreter_edit.setPlaceholderText("e.g., python, /usr/bin/node (leave empty for default)")
        self.node_args_edit = QLineEdit()
        self.node_args_edit.setPlaceholderText("e.g., --harmony --max-old-space-size=4096")
        self.node_args_edit.setToolTip("Arguments passed to the Node.js interpreter itself.")
        self.args_edit = QLineEdit()
        self.args_edit.setPlaceholderText("e.g., --port 3000 --verbose")
        exec_layout.addRow("Execution Mode:", self.exec_mode_combo)
        exec_layout.addRow("Instances:", self.instances_edit)
        exec_layout.addRow("Interpreter:", self.interpreter_edit)
        exec_layout.addRow("Interpreter Args:", self.node_args_edit)
        exec_layout.addRow("Script Arguments:", self.args_edit)
        exec_group.setLayout(exec_layout)
        main_layout.addWidget(exec_group)
        
        # --- Restart & Watch Group ---
        restart_group = QGroupBox("Restart & Watch Strategy")
        restart_layout = QFormLayout()
        self.watch_checkbox = QCheckBox("Enable Watch & Restart on file change")
        self.autorestart_checkbox = QCheckBox("Enable auto-restart on crash/stop")
        self.max_mem_edit = QLineEdit()
        self.max_mem_edit.setPlaceholderText("e.g., 150M, 1G (leave empty for no limit)")
        self.cron_restart_edit = QLineEdit()
        self.cron_restart_edit.setPlaceholderText("Cron pattern, e.g., '0 0 * * *'")
        restart_layout.addRow(self.watch_checkbox)
        restart_layout.addRow(self.autorestart_checkbox)
        restart_layout.addRow("Max Memory Restart:", self.max_mem_edit)
        restart_layout.addRow("Cron Restart Pattern:", self.cron_restart_edit)
        restart_group.setLayout(restart_layout)
        main_layout.addWidget(restart_group)

        # --- Logging Group ---
        log_group = QGroupBox("Logging")
        log_layout = QFormLayout()
        self.merge_logs_checkbox = QCheckBox("Merge all instance logs into one file (in cluster mode)")
        self.log_date_format_edit = QLineEdit()
        self.log_date_format_edit.setPlaceholderText("e.g., YYYY-MM-DD HH:mm Z")
        self.out_file_edit = QLineEdit()
        self.out_file_edit.setPlaceholderText("./logs/out.log (relative to project path)")
        self.error_file_edit = QLineEdit()
        self.error_file_edit.setPlaceholderText("./logs/error.log (relative to project path)")
        log_layout.addRow(self.merge_logs_checkbox)
        log_layout.addRow("Log Date Format:", self.log_date_format_edit)
        log_layout.addRow("Output Log File:", self.out_file_edit)
        log_layout.addRow("Error Log File:", self.error_file_edit)
        log_group.setLayout(log_layout)
        main_layout.addWidget(log_group)
        
        # --- Environment Variables Group ---
        env_group = QGroupBox("Environment Variables (KEY=VALUE format, one per line)")
        env_layout = QVBoxLayout()
        self.env_vars_edit = QPlainTextEdit()
        self.env_vars_edit.setPlaceholderText("DB_HOST=localhost\nDB_USER=myuser\nAPI_KEY=12345")
        env_layout.addWidget(self.env_vars_edit)
        env_group.setLayout(env_layout)
        main_layout.addWidget(env_group)

        # --- Dialog Buttons ---
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

        self._populate_fields()

    def _populate_fields(self):
        """Fills the dialog's fields with the existing project data."""
        self.name_edit.setText(self.original_data.get('name', ''))
        script_path = os.path.join(self.original_data.get('path', ''), self.original_data.get('script', ''))
        self.script_path_edit.setText(script_path)
        
        exec_mode = self.original_data.get('exec_mode', 'fork')
        self.exec_mode_combo.setCurrentText(exec_mode)
        self.instances_edit.setText(str(self.original_data.get('instances', '1')))
        self.instances_edit.setEnabled(exec_mode == 'cluster')
        
        self.interpreter_edit.setText(self.original_data.get('interpreter', ''))
        self.node_args_edit.setText(self.original_data.get('node_args', ''))
        self.args_edit.setText(self.original_data.get('args', ''))
        
        self.watch_checkbox.setChecked(self.original_data.get('watch', False))
        # PM2 defaults autorestart to True. If key is missing, we assume True.
        self.autorestart_checkbox.setChecked(self.original_data.get('autorestart', True))
        self.max_mem_edit.setText(self.original_data.get('max_memory_restart', ''))
        self.cron_restart_edit.setText(self.original_data.get('cron_restart', ''))
        
        self.merge_logs_checkbox.setChecked(self.original_data.get('merge_logs', False))
        self.log_date_format_edit.setText(self.original_data.get('log_date_format', ''))
        self.out_file_edit.setText(self.original_data.get('out_file', ''))
        self.error_file_edit.setText(self.original_data.get('error_file', ''))
        
        env_dict = self.original_data.get('env', {})
        env_text = "\n".join([f"{k}={v}" for k, v in env_dict.items()])
        self.env_vars_edit.setPlainText(env_text)

    def browse_for_script(self):
        current_dir = os.path.dirname(self.script_path_edit.text()) or os.path.expanduser("~")
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Entry Script", current_dir, "Scripts (*.js *.py *.sh);;All files (*.*)"
        )
        if file_path:
            self.script_path_edit.setText(file_path)

    def get_data(self):
        """Parses the dialog fields and returns a project data dictionary."""
        full_path = self.script_path_edit.text().strip()
        name = self.name_edit.text().strip()
        if not full_path or not os.path.exists(full_path) or not name:
            QMessageBox.warning(self, "Invalid Input", "Project Name and a valid Script Path are required.")
            return None

        # Parse environment variables
        env_dict = {}
        try:
            for line in self.env_vars_edit.toPlainText().splitlines():
                line = line.strip()
                if line and '=' in line:
                    key, value = line.split('=', 1)
                    env_dict[key.strip()] = value.strip()
        except Exception as e:
            QMessageBox.warning(self, "Invalid Environment Variables", f"Could not parse variables.\nPlease use KEY=VALUE format.\n\nError: {e}")
            return None
            
        data = {
            "name": name,
            "path": os.path.dirname(full_path),
            "script": os.path.basename(full_path),
            "env": env_dict,
            # Booleans are always included
            "watch": self.watch_checkbox.isChecked(),
            "autorestart": self.autorestart_checkbox.isChecked(),
            "merge_logs": self.merge_logs_checkbox.isChecked(),
            # Strings are included if not empty
            "interpreter": self.interpreter_edit.text().strip(),
            "node_args": self.node_args_edit.text().strip(),
            "args": self.args_edit.text().strip(),
            "max_memory_restart": self.max_mem_edit.text().strip(),
            "cron_restart": self.cron_restart_edit.text().strip(),
            "log_date_format": self.log_date_format_edit.text().strip(),
            "out_file": self.out_file_edit.text().strip(),
            "error_file": self.error_file_edit.text().strip(),
            # Special handling
            "exec_mode": self.exec_mode_combo.currentText(),
            "instances": self.instances_edit.text().strip(),
        }

        # Create final dict, filtering out keys with empty string values.
        # Booleans and dicts are always kept.
        final_data = {k: v for k, v in data.items() if v != '' or isinstance(v, (bool, dict))}

        # If mode is fork, `instances` is irrelevant, so don't include it.
        if final_data.get('exec_mode') == 'fork' and 'instances' in final_data:
            del final_data['instances']
            
        return final_data