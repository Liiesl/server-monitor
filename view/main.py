# main.py
# Application main window. Launched by entry.py.
import json, os
from enum import Enum
from PySide6.QtWidgets import ( QMainWindow, QToolBar, QMessageBox, QDialog, QStatusBar, QListWidget, QListWidgetItem,
                               QSplitter, QVBoxLayout, QFileDialog, QInputDialog, QStackedWidget, QWidget, QLabel) # NEW: Added QWidget and QLabel
from PySide6.QtGui import QAction
from PySide6.QtCore import QThread, Slot, QTimer, Qt
from PySide6.QtGui import QIcon, QFont
import qtawesome as qta
from .settings_dialog import ProjectSettingsDialog
from .project_detail import ProjectDetailWidget
from .dashboard import DashboardWidget
from .sidebar import ProjectListItemWidget

# NEW: An overlay widget for the pending state.
class LoadingOverlay(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        # Block mouse events from reaching widgets below
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.label = QLabel("Loading state...")
        font = QFont()
        font.setPointSize(24)
        font.setBold(True)
        self.label.setFont(font)

        layout.addWidget(self.label)
        self.setLayout(layout)

        self.setStyleSheet("""
            QWidget {
                background-color: rgba(0, 0, 0, 170); /* Dark semi-transparent background */
                color: white; /* Text color for the label */
            }
        """)

        self.hide()

    def set_text(self, text):
        self.label.setText(text)

# NEW: An enum to represent the daemon's state clearly.
class DaemonState(Enum):
    STOPPED = 0
    RUNNING = 1
    PENDING = 2 # A new state for when we are waiting for a status update.

# --- Main GUI Window ---
class PM2GUI(QMainWindow):
    # MODIFIED __init__ to accept pre-loaded objects
    def __init__(self, project_manager, worker_instance):
        super().__init__()
        print("[DEBUG] PM2GUI.__init__ starting (pre-loaded).")
        self.setWindowTitle("PM2 Project Manager")
        self.setGeometry(100, 100, 1000, 700)
        self.setWindowIcon(QIcon.fromTheme("utilities-terminal"))
        
        # Use the instances passed from the preloader
        self.project_manager = project_manager
        self.worker = worker_instance

        # MODIFIED: Replace boolean flag with a three-state enum.
        # Initialize to None; the true initial state is set in init_ui.
        self.daemon_state = None
        self.all_projects_data = []
        self.refresh_timer = QTimer(self)

        # init_ui is still called to build the widgets
        self.init_ui()

        # Worker thread is NOT started here
        self.status_bar.showMessage("Application loaded. Finalizing state...")
        print("[DEBUG] PM2GUI.__init__ finished.")

    # NEW method to be called from entry.py after __init__
    def post_init_setup(self, initial_json_data, initial_daemon_status):
        """
        Finalizes setup using pre-loaded data after the UI is constructed.
        This starts the worker thread and populates the UI for the first time.
        """
        print("[DEBUG] PM2GUI.post_init_setup starting.")
        self.setup_worker_thread() # Now we setup and start the thread

        # Set the true initial state *before* starting timers or periodic checks
        self.update_daemon_status(initial_daemon_status)
        self.update_ui(initial_json_data)

        # The refresh timer connection is moved here
        self.refresh_timer.timeout.connect(self.worker.get_process_list)

        # The timer will have been started inside update_daemon_status if needed.
        # The worker thread is now running in the background.
        print("[DEBUG] PM2GUI.post_init_setup finished.")

    # MODIFIED setup_worker_thread
    def setup_worker_thread(self):
        print("[DEBUG] Setting up worker thread...")
        self.thread = QThread()
        # self.worker was already instantiated and passed to __init__
        self.worker.moveToThread(self.thread)
        
        # --- Connect signals to slots ---
        self.worker.list_ready.connect(self.update_ui)
        # MODIFIED: Connect logs_ready to a new handler instead of a dialog
        self.worker.logs_ready.connect(self.on_logs_received)
        self.worker.action_finished.connect(self.show_action_result)
        self.worker.error.connect(self.show_error_message)
        self.worker.daemon_status_ready.connect(self.update_daemon_status)
        
        # We NO LONGER connect thread.started to an initial fetch,
        # as the preloader already did that.
        self.thread.start()
        print("[DEBUG] Worker thread started.")

    def init_ui(self):
        # ... (mostly unchanged widget setup)
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        # Daemon Actions
        self.start_daemon_action = QAction(qta.icon('fa5s.play-circle'), "Start PM2 Daemon", self)
        # MODIFIED: Connect to a handler method to set PENDING state first.
        self.start_daemon_action.triggered.connect(self.handle_start_daemon_request)
        toolbar.addAction(self.start_daemon_action)
        self.kill_daemon_action = QAction(qta.icon('fa5s.skull-crossbones'), "Kill PM2 Daemon", self)
        self.kill_daemon_action.triggered.connect(self.kill_daemon)
        toolbar.addAction(self.kill_daemon_action)
        toolbar.addSeparator()

        # Project Actions
        self.add_action = QAction(QIcon.fromTheme("list-add"), "Add Project...", self)
        self.add_action.triggered.connect(self.add_project_dialog)
        toolbar.addAction(self.add_action)
        self.remove_action = QAction(QIcon.fromTheme("list-remove"), "Remove Project", self)
        self.remove_action.triggered.connect(self.remove_project)
        toolbar.addAction(self.remove_action)
        toolbar.addSeparator()
        
        # Global Process Actions
        self.refresh_action = QAction(QIcon.fromTheme("view-refresh"), "Refresh All", self)
        self.refresh_action.triggered.connect(self.worker.get_process_list)
        toolbar.addAction(self.refresh_action)
        self.restart_all_action = QAction(QIcon.fromTheme("system-reboot"), "Restart All", self)
        self.restart_all_action.triggered.connect(self.worker.restart_all)
        toolbar.addAction(self.restart_all_action)
        self.stop_all_action = QAction(QIcon.fromTheme("process-stop"), "Stop All", self)
        self.stop_all_action.triggered.connect(self.worker.stop_all)
        toolbar.addAction(self.stop_all_action)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        self.project_list_widget = QListWidget()
        self.project_list_widget.setMaximumWidth(350) 
        self.project_list_widget.currentItemChanged.connect(self.on_item_selected)
        splitter.addWidget(self.project_list_widget)
        
        self.main_content_stack = QStackedWidget()
        self.dashboard_widget = DashboardWidget()
        self.dashboard_widget.start_daemon_requested.connect(self.handle_start_daemon_request)
        self.dashboard_widget.kill_daemon_requested.connect(self.kill_daemon)
        self.dashboard_widget.restart_all_requested.connect(self.worker.restart_all)
        self.dashboard_widget.stop_all_requested.connect(self.worker.stop_all)
        
        self.project_detail_widget = ProjectDetailWidget()
        self.project_detail_widget.start_requested.connect(self.worker.start_process)
        self.project_detail_widget.stop_requested.connect(self.worker.stop_process)
        self.project_detail_widget.restart_requested.connect(self.worker.restart_process)
        self.project_detail_widget.reload_requested.connect(self.worker.reload_process)
        self.project_detail_widget.delete_from_pm2_requested.connect(self.handle_delete_from_pm2)

        self.main_content_stack.addWidget(self.dashboard_widget)
        self.main_content_stack.addWidget(self.project_detail_widget)
        splitter.addWidget(self.main_content_stack)
        splitter.setSizes([280, 720])
        self.setCentralWidget(splitter)
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)

        # MODIFIED: Initialize loading overlay and set initial PENDING state.
        self.loading_overlay = LoadingOverlay(self)
        self.loading_overlay.set_text("loading state,,,")
        self.update_daemon_status(DaemonState.PENDING)

    # NEW: A handler to set the PENDING state before calling the worker.
    def handle_start_daemon_request(self):
        self.loading_overlay.set_text("Starting PM2 Daemon...")
        self.update_daemon_status(DaemonState.PENDING)
        self.worker.start_daemon()

    def kill_daemon(self):
        reply = QMessageBox.question(self, "Confirm Kill PM2",
                                     "Are you sure you want to kill the PM2 daemon?\n\n"
                                     "This will stop ALL managed processes immediately and they will not be revived.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # MODIFIED: Set pending state and overlay text for instant UI feedback.
            self.loading_overlay.set_text("Killing PM2 Daemon...")
            self.update_daemon_status(DaemonState.PENDING)
            self.worker.kill_daemon()

    # NEW: Override resizeEvent to keep the overlay positioned correctly.
    def resizeEvent(self, event):
        """Ensure the overlay is always sized to the main content area."""
        if hasattr(self, 'loading_overlay') and self.centralWidget():
            # Position the overlay over the central widget area.
            self.loading_overlay.setGeometry(self.centralWidget().geometry())
        super().resizeEvent(event)

    def handle_delete_from_pm2(self, project_name):
        reply = QMessageBox.question(self, "Confirm Deletion from PM2",
                                     f"Are you sure you want to delete '{project_name}' from PM2?\n\n"
                                     "This will stop the process and remove it from PM2's management list. "
                                     "The project configuration will remain in this application, and you can start it again later.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.worker.delete_process(project_name)

    # *** FIXED ***: The @Slot(object) decorator has been removed.
    def update_daemon_status(self, new_state_or_bool):
        """Updates the UI based on the daemon's state (STOPPED, RUNNING, or PENDING)."""
        # Convert boolean from worker/preloader signal to the corresponding enum.
        if isinstance(new_state_or_bool, bool):
            new_state = DaemonState.RUNNING if new_state_or_bool else DaemonState.STOPPED
        else:
            new_state = new_state_or_bool

        # Avoid redundant UI updates if the state hasn't changed.
        if new_state == self.daemon_state:
            return
        
        print(f"[DEBUG MAIN] State changing from {self.daemon_state} -> {new_state}")
        self.daemon_state = new_state

        if self.daemon_state == DaemonState.PENDING:
            self.status_bar.showMessage("Checking PM2 daemon status...")
            # Disable all major actions while we wait for confirmation.
            self.start_daemon_action.setEnabled(False)
            self.kill_daemon_action.setEnabled(False)
            for action in [self.add_action, self.remove_action, self.refresh_action, self.restart_all_action, self.stop_all_action]:
                action.setEnabled(False)
            self.dashboard_widget.set_daemon_status(False) # Treat pending as "down" for dashboard UI
            # Show the overlay
            if self.centralWidget():
                self.loading_overlay.setGeometry(self.centralWidget().geometry())
            self.loading_overlay.raise_()
            self.loading_overlay.show()

        elif self.daemon_state == DaemonState.RUNNING:
            self.status_bar.showMessage("PM2 Daemon is running. Fetching process list...", 3000)
            self.start_daemon_action.setEnabled(False)
            self.kill_daemon_action.setEnabled(True)
            for action in [self.add_action, self.remove_action, self.refresh_action, self.restart_all_action, self.stop_all_action]:
                action.setEnabled(True)
            self.dashboard_widget.set_daemon_status(True)
            self.loading_overlay.hide() # Hide the overlay
            if not self.refresh_timer.isActive():
                print("[DEBUG MAIN] Starting refresh timer.")
                self.refresh_timer.start(5000)

        elif self.daemon_state == DaemonState.STOPPED:
            self.status_bar.showMessage("PM2 Daemon is not running. Please use the 'Start Daemon' button.")
            self.start_daemon_action.setEnabled(True)
            self.kill_daemon_action.setEnabled(False)
            for action in [self.add_action, self.remove_action, self.refresh_action, self.restart_all_action, self.stop_all_action]:
                action.setEnabled(False)
            self.dashboard_widget.set_daemon_status(False)
            self.loading_overlay.hide() # Hide the overlay
            if self.refresh_timer.isActive():
                print("[DEBUG MAIN] Stopping refresh timer.")
                self.refresh_timer.stop()
            self.update_ui('[]') # Clear the process list

    # --- OPTIMIZED: This method now uses a diffing approach instead of rebuilding the list. ---
    @Slot(str)
    def update_ui(self, pm2_json_data):
        print(f"[DEBUG MAIN] SLOT: update_ui received data (len: {len(pm2_json_data)}).")
        
        is_first_load = not self.all_projects_data

        try:
            pm2_processes = json.loads(pm2_json_data)
        except json.JSONDecodeError:
            self.show_error_message("Failed to parse PM2 data.")
            pm2_processes = []

        known_projects = self.project_manager.get_projects()
        
        # --- 1. Merge known project configs with live PM2 data ---
        new_project_data_list = []
        for proj_config in known_projects:
            live_data = next((p for p in pm2_processes if p.get('name') == proj_config['name']), None)
            merged_data = {**proj_config, **(live_data or {})}
            new_project_data_list.append(merged_data)
        
        new_project_data_list.sort(key=lambda p: p['name'])
        self.all_projects_data = new_project_data_list # Update the main data store

        # --- 2. Update dashboard and detail widgets ---
        self.dashboard_widget.update_stats(self.all_projects_data)
        self.update_detail_view_if_selected()

        # --- 3. Efficiently update the project list widget ---
        self.project_list_widget.blockSignals(True)
        
        if is_first_load:
            # On first load, populate everything from scratch
            self.project_list_widget.clear()
            dashboard_item = QListWidgetItem(QIcon.fromTheme("view-dashboard"), "System Dashboard")
            dashboard_item.setData(Qt.ItemDataRole.UserRole, "dashboard")
            self.project_list_widget.addItem(dashboard_item)
            
            for proj in self.all_projects_data:
                self._add_project_list_item(proj)
            self.project_list_widget.setCurrentRow(0)
        else:
            # On subsequent updates, perform a diff
            existing_items_map = {}
            for i in range(self.project_list_widget.count()):
                item = self.project_list_widget.item(i)
                if item.data(Qt.ItemDataRole.UserRole) == "project":
                    name = item.data(Qt.ItemDataRole.UserRole + 1)
                    existing_items_map[name] = item

            new_data_map = {p['name']: p for p in self.all_projects_data}
            
            # REMOVE items that are no longer in the data
            for name, item in list(existing_items_map.items()):
                if name not in new_data_map:
                    row = self.project_list_widget.row(item)
                    self.project_list_widget.takeItem(row)

            # UPDATE existing items and ADD new ones
            for i, proj in enumerate(self.all_projects_data):
                name = proj['name']
                if name in existing_items_map:
                    # It exists, just update its widget
                    item = existing_items_map[name]
                    widget = self.project_list_widget.itemWidget(item)
                    if widget:
                        widget.update_status(proj) # Assumes ProjectListItemWidget has this method
                else:
                    # It's a new item, add it at the correct sorted position
                    # We insert at i+1 because dashboard is at index 0
                    self._add_project_list_item(proj, at_row=i + 1)

        self.project_list_widget.blockSignals(False)
        if is_first_load:
             self.on_item_selected(self.project_list_widget.currentItem(), None)

        status_msg = f"Updated. Managing {len(self.all_projects_data)} projects."
        if self.daemon_state == DaemonState.STOPPED:
             status_msg = "PM2 Daemon is not running."
        self.status_bar.showMessage(status_msg, 3000)
        print("[DEBUG MAIN] update_ui finished.")

    def _add_project_list_item(self, proj_data, at_row=None):
        """Helper to create and add a project item and its custom widget."""
        item = QListWidgetItem()
        item.setData(Qt.ItemDataRole.UserRole, "project")
        item.setData(Qt.ItemDataRole.UserRole + 1, proj_data['name'])
        custom_widget = ProjectListItemWidget(proj_data)
        custom_widget.settings_requested.connect(self.reconfigure_project_dialog)
        item.setSizeHint(custom_widget.sizeHint())

        if at_row is not None:
            self.project_list_widget.insertItem(at_row, item)
        else:
            self.project_list_widget.addItem(item)
            
        self.project_list_widget.setItemWidget(item, custom_widget)
        return item

    def update_detail_view_if_selected(self):
        """
        If a project is currently selected in the detail view,
        this method finds its updated data and refreshes the view.
        """
        current_item = self.project_list_widget.currentItem()
        if not current_item or current_item.data(Qt.ItemDataRole.UserRole) != "project":
            return
            
        selected_name = current_item.data(Qt.ItemDataRole.UserRole + 1)
        proj_data = next((p for p in self.all_projects_data if p.get('name') == selected_name), None)

        if proj_data:
            # We pass is_new_selection=False to prevent it from clearing logs on a refresh
            self.project_detail_widget.update_details(proj_data, is_new_selection=False)


    # MODIFIED: This now fetches logs only when a new project is selected.
    def on_item_selected(self, current_item, _previous_item):
        if not current_item:
            self.main_content_stack.setCurrentWidget(self.dashboard_widget)
            return
            
        item_type = current_item.data(Qt.ItemDataRole.UserRole)
        if item_type == "dashboard":
            self.main_content_stack.setCurrentWidget(self.dashboard_widget)
        elif item_type == "project":
            selected_name = current_item.data(Qt.ItemDataRole.UserRole + 1)
            proj_data = next((p for p in self.all_projects_data if p.get('name') == selected_name), None)

            if proj_data:
                is_new_selection = (self.project_detail_widget.current_project is None or 
                                    self.project_detail_widget.current_project.get('name') != selected_name)

                self.main_content_stack.setCurrentWidget(self.project_detail_widget)
                # Update the detail widget's UI. This is fast and provides immediate feedback.
                # If it's a new selection, update_details should clear old logs.
                self.project_detail_widget.update_details(proj_data, is_new_selection=is_new_selection)
                
                # If it's a new selection and the process is running, fetch its logs.
                is_in_pm2 = 'pm_id' in proj_data
                if is_new_selection and is_in_pm2:
                    self.worker.get_logs(selected_name)
            else:
                self.main_content_stack.setCurrentWidget(self.dashboard_widget)
    
    def add_project_dialog(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Entry Script", os.path.expanduser("~"), "Scripts (*.js *.py *.sh);;All files (*.*)"
        )
        if not file_path: return
        folder_path = os.path.dirname(file_path)
        script_name = os.path.basename(file_path)
        default_name = os.path.basename(folder_path)
        project_name, ok = QInputDialog.getText(self, "Project Name", "Enter a unique name for this project:", text=default_name)
        if not ok or not project_name: return
        
        if self.project_manager.add_project(project_name.strip(), folder_path, script_name):
            self.status_bar.showMessage(f"Project '{project_name}' added.", 4000)
            self.worker.get_process_list() # Trigger a refresh to show the new project
        else:
            QMessageBox.warning(self, "Add Failed", "A project with that name already exists.")
    
    @Slot(str)
    def reconfigure_project_dialog(self, project_name):
        original_project_data = self.project_manager.find_project(project_name)
        if not original_project_data: return

        dialog = ProjectSettingsDialog(original_project_data, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_data()
            if not new_data: return 

            config_changed = (original_project_data != new_data)
            old_name = original_project_data['name']
            
            live_process = next((p for p in self.all_projects_data if p.get('name') == old_name and 'pm_id' in p), None)

            # A process must be deleted to reconfigure it
            if live_process and config_changed:
                reply = QMessageBox.question(self, "Confirm Configuration Change",
                                     f"The running process '{old_name}' must be stopped and deleted from PM2 to apply these changes.\n\n"
                                     "This is required to change arguments, interpreter, environment variables, etc.\n\n"
                                     "Do you want to continue?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
                if reply == QMessageBox.StandardButton.No: return
                self.worker.delete_process(old_name)

            if not self.project_manager.update_project(old_name, **new_data):
                 QMessageBox.warning(self, "Update Failed", f"A project with the new name '{new_data['name']}' already exists.")
                 self.worker.get_process_list()
                 return
            
            self.status_bar.showMessage(f"Project '{old_name}' reconfigured. A refresh will occur shortly.", 4000)
            # No need to call get_process_list(), timer will handle it.

    def remove_project(self):
        current_item = self.project_list_widget.currentItem()
        if not current_item or current_item.data(Qt.ItemDataRole.UserRole) == "dashboard":
            QMessageBox.information(self, "Remove Project", "Please select a project to remove.")
            return
        project_name = current_item.data(Qt.ItemDataRole.UserRole + 1)
        reply = QMessageBox.question(self, "Confirm Removal",
                                     f"Are you sure you want to remove '{project_name}'?\n"
                                     "This will also stop and delete it from PM2 if it is running, and remove it from this application permanently.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No, QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            is_in_pm2 = any(p.get('name') == project_name and 'pm_id' in p for p in self.all_projects_data)
            if is_in_pm2:
                self.worker.delete_process(project_name)
            
            self.project_manager.remove_project(project_name)
            self.status_bar.showMessage(f"Project '{project_name}' removed.", 4000)
            # The next timed refresh will remove it from the UI.
            # For instant feedback, we can manually trigger one refresh.
            self.worker.get_process_list()

    @Slot(str, str)
    def on_logs_received(self, proc_name, logs):
        """
        Receives logs from the worker and passes them to the detail widget
        if it's the currently viewed project.
        """
        if self.main_content_stack.currentWidget() is not self.project_detail_widget:
            return

        if self.project_detail_widget.current_project and self.project_detail_widget.current_project.get('name') == proc_name:
            self.project_detail_widget.update_logs(logs)

    def show_action_result(self, title, message):
        self.status_bar.showMessage(title, 5000)

    def show_error_message(self, message):
        self.status_bar.showMessage("An error occurred.", 5000)
        QMessageBox.critical(self, "Error", message)

    def closeEvent(self, event):
        print("[DEBUG] closeEvent called. Stopping timer and quitting thread.")
        self.refresh_timer.stop()
        self.thread.quit()
        self.thread.wait()
        event.accept()