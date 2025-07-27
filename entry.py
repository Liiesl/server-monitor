# entry.py
# New application entry point with a splash screen for smooth startup.
# Refactored to prioritize showing the UI by deferring heavy imports.

# --- 1. Bare minimum imports for initial launch ---
import sys
import time
# We need these PyQt classes to create the app and splash screen
from PySide6.QtWidgets import QApplication, QSplashScreen
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QPixmap, QPainter, QFont, QColor, QIcon

# Note: Heavy imports like PM2GUI, ProjectManager, and Pm2Worker are now
# imported inside the functions/threads that use them, not at the top level.


class Preloader(QThread):
    """
    Performs initial, blocking tasks in a separate thread to avoid freezing the GUI.
    It prepares all necessary data and objects before the main window is shown.
    """
    # MODIFIED: Signal signature no longer passes the worker object.
    # (project_manager_obj, initial_json_data_str, initial_daemon_status_bool)
    finished = Signal(object, str, bool)
    progress_update = Signal(str)

    def run(self):
        """The entry point for the thread."""
        # --- 2. Defer these imports until the thread is actually running ---
        from core import ProjectManager
        from core import Pm2Worker

        self.progress_update.emit("Loading project configurations...")
        project_manager = ProjectManager()
        time.sleep(0.4)  # Small delay for visual effect

        self.progress_update.emit("Initializing PM2 interface...")
        # MODIFIED: Create a TEMPORARY worker just for the initial check.
        # This instance lives and dies within this thread and is never passed out.
        temp_worker = Pm2Worker()
        time.sleep(0.4)

        self.progress_update.emit("Connecting to PM2 daemon...")
        # This is the potentially slow, blocking call we want off the main thread.
        initial_json_data, is_running = temp_worker.get_initial_state()
        time.sleep(0.8) # Let the user see the final message

        self.progress_update.emit("Launching application...")
        # MODIFIED: Emit the project_manager and the DATA, not the worker object.
        self.finished.emit(project_manager, initial_json_data, is_running)

class CustomSplashScreen(QSplashScreen):
    # ... (no changes needed in this class)
    # --- snip ---
    def __init__(self, pixmap):
        super().__init__(pixmap)
        self.message = "Initializing..."
        self.setStyleSheet("QSplashScreen { border: 1px solid #555; }")

    def drawContents(self, painter):
        super().drawContents(painter)
        text_rect = self.rect().adjusted(10, 0, -10, -10)
        painter.setPen(QColor(220, 220, 220)) # Light gray text
        painter.drawText(text_rect, Qt.AlignBottom | Qt.AlignLeft, self.message)

    def showMessage(self, message, alignment=Qt.AlignLeft, color=Qt.white):
        self.message = message
        super().showMessage(message, alignment, color)
        self.repaint()
        QApplication.processEvents()


# --- Global variables to hold instances ---
main_window = None
splash = None

# MODIFIED: The function signature is changed to reflect the new signal from Preloader.
def on_preload_finished(project_manager, initial_json_data, is_running):
    """
    This function is a slot that runs on the main thread once the Preloader is done.
    It creates the main window, passes the pre-loaded data to it, shows it,
    and closes the splash screen.
    """
    global main_window, splash
    print("[ENTRY] Preloading finished. Creating main window.")

    # --- 3. Defer the import of the main window until it's actually needed ---
    from view import PM2GUI
    # MODIFIED: Import Pm2Worker here as well.
    from core import Pm2Worker

    # MODIFIED: Create the persistent Pm2Worker instance IN THE MAIN THREAD.
    # This object has the correct thread affinity for being moved later.
    persistent_worker = Pm2Worker()

    # MODIFIED: Create the main window, passing the project manager and the NEW persistent_worker.
    main_window = PM2GUI(project_manager, persistent_worker)

    # 2. Populate the UI with pre-loaded data before showing it.
    main_window.post_init_setup(initial_json_data, is_running)

    # 3. Show the fully prepared main window.
    main_window.show()

    # 4. Close the splash screen.
    splash.finish(main_window)
    print("[ENTRY] Main window shown, splash screen closed.")


if __name__ == '__main__':
    # ... (the rest of the file is unchanged)
    # --- snip ---
    app = QApplication(sys.argv)
    from view import DARK_STYLE
    app.setStyleSheet(DARK_STYLE)
    QIcon.setThemeName("breeze-dark")
    pixmap = QPixmap(500, 250)
    pixmap.fill(QColor(45, 45, 45))
    painter = QPainter(pixmap)
    painter.setPen(QColor(220, 220, 220))
    font = QFont("Segoe UI", 24, QFont.Bold)
    painter.setFont(font)
    painter.drawText(pixmap.rect().adjusted(0, -30, 0, -30), Qt.AlignCenter, "PM2 Project Manager")
    try:
        icon_font = QFont("FontAwesome", 30)
        painter.setFont(icon_font)
        painter.drawText(pixmap.rect().adjusted(0, 40, 0, 40), Qt.AlignCenter, "\uf121") # fa.code icon
    except Exception as e:
        print(f"Warning: Could not load 'FontAwesome' for splash screen icon. {e}")
    painter.end()
    splash = CustomSplashScreen(pixmap)
    splash.show()
    preloader = Preloader()
    preloader.progress_update.connect(splash.showMessage)
    preloader.finished.connect(on_preload_finished)
    preloader.start()
    sys.exit(app.exec())