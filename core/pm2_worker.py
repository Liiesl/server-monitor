# pm2_worker.py
import subprocess, os, json, tempfile
from PySide6.QtCore import QObject, Slot, Signal

class Pm2Worker(QObject):
    """
    Runs PM2 commands in a non-blocking way and emits signals with the results.
    """
    list_ready = Signal(str)
    logs_ready = Signal(str, str) # proc_name, logs
    action_finished = Signal(str, str) # title, message
    error = Signal(str)
    daemon_status_ready = Signal(bool)

    # --- MODIFIED: Replaced 'pm2 ping' with a non-intrusive OS-level process check ---
    def _is_daemon_running(self):
        """
        Checks for the PM2 daemon process without using any pm2 commands,
        preventing the daemon from being accidentally started. This is a non-intrusive check.
        """
        print("[DEBUG WORKER] Performing non-intrusive daemon check...")
        try:
            startupinfo = None
            is_running = False
            if os.name == 'nt': # Windows
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                # WMIC is reliable for checking command line arguments of a running node.exe process.
                command = 'wmic process where "name=\'node.exe\' and commandline like \'%PM2%Daemon.js%\'" get ProcessId'
                output = subprocess.check_output(
                    command, shell=True, text=True, startupinfo=startupinfo, 
                    stderr=subprocess.DEVNULL, timeout=10
                )
                # Successful output has a header ("ProcessId") and at least one PID line.
                if "ProcessId" in output and len(output.strip().splitlines()) > 1:
                    is_running = True
            else: # Linux, macOS, etc.
                # Use ps and grep. The '[P]M2' is a common trick to prevent grep from matching its own process.
                # This checks the full command line for the "God Daemon" signature.
                command = "ps -ef | grep '[P]M2 v.*: God Daemon'"
                subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL, timeout=10)
                is_running = True
        except subprocess.CalledProcessError:
            # This is the expected outcome if the process is not found (grep returns non-zero).
            is_running = False
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            # Handle cases where system commands (ps, wmic) aren't found or time out.
            print(f"[ERROR WORKER] System process listing command failed: {e}")
            is_running = False
        
        print(f"[DEBUG WORKER] Non-intrusive check result: is_running = {is_running}")
        return is_running

    def get_initial_state(self):
        """
        Synchronous method to get initial state. Called only by the preloader thread.
        It first checks daemon status with the non-intrusive method, then gets the process list.
        """
        print("[WORKER_SYNC] Getting initial state...")
        is_running = self._is_daemon_running()

        if not is_running:
            print("[WORKER_SYNC] PM2 daemon is not running. Reporting as stopped.")
            return '[]', False

        print("[WORKER_SYNC] PM2 daemon is running. Fetching process list.")
        process_list_json = self._run_command("pm2 jlist", can_fail=True)
        
        if process_list_json is None:
            return '[]', True
        try:
            json.loads(process_list_json)
        except (json.JSONDecodeError, TypeError):
            print("[WORKER_SYNC] Got invalid JSON from jlist despite daemon running. Reporting empty list.")
            return '[]', True

        return process_list_json, True

    def _run_command(self, command, cwd=None, can_fail=False):
        """Helper to run a command and handle common errors."""
        print(f"[DEBUG WORKER] Preparing to run command: {command}")
        try:
            startupinfo = None
            if os.name == 'nt':
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

            result = subprocess.check_output(
                command,
                shell=True,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8',
                errors='replace',
                cwd=cwd,
                startupinfo=startupinfo,
                timeout=15
            )
            print(f"[DEBUG WORKER] Command successful. Output length: {len(result)}")
            return result
        except FileNotFoundError:
            print("[ERROR WORKER] 'pm2' command not found!")
            self.error.emit("Error: 'pm2' command not found. Is PM2 installed and in your system's PATH?")
            return None
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"[ERROR WORKER] Command failed: {command}")
            output = e.output if hasattr(e, 'output') else "Command timed out."
            print(f"[ERROR WORKER] Output:\n{output}")
            if not can_fail:
                self.error.emit(f"Command failed: {command}\n\nOutput:\n{output}")
            return output

    @Slot()
    def start_daemon(self):
        print("[DEBUG WORKER] SLOT: start_daemon")
        self._run_command("pm2 resurrect", can_fail=True)
        self.action_finished.emit("PM2 Daemon", "Attempting to start/resurrect PM2 Daemon...")
        self.get_process_list()

    @Slot()
    def kill_daemon(self):
        print("[DEBUG WORKER] SLOT: kill_daemon")
        output = self._run_command("pm2 kill")
        if output is not None:
            self.action_finished.emit("PM2 Daemon Killed", "The PM2 daemon has been stopped.")
        self.get_process_list()

    @Slot()
    def get_process_list(self):
        """
        The primary method for checking daemon status and getting process data,
        now using the non-intrusive OS-level check.
        """
        print("[DEBUG WORKER] SLOT: get_process_list (using non-intrusive check)")
        
        is_running = self._is_daemon_running()
        self.daemon_status_ready.emit(is_running)

        if is_running:
            process_list_json = self._run_command("pm2 jlist", can_fail=True)
            if process_list_json is None:
                self.list_ready.emit("[]")
                return
            try:
                json.loads(process_list_json)
                self.list_ready.emit(process_list_json)
            except (json.JSONDecodeError, TypeError):
                self.list_ready.emit("[]")
        else:
            self.list_ready.emit("[]")
    
    @Slot(str)
    def get_logs(self, proc_id_or_name):
        print(f"[DEBUG WORKER] SLOT: get_logs for {proc_id_or_name}")
        output = self._run_command(f"pm2 logs {proc_id_or_name} --lines 200 --nostream")
        if output:
            self.logs_ready.emit(proc_id_or_name, output)

    @Slot(dict)
    def start_process(self, project_data):
        print(f"[DEBUG WORKER] SLOT: start_process for {project_data.get('name')}")
        pm2_keys = [
            'name', 'script', 'args', 'interpreter', 'node_args', 'watch', 'max_memory_restart',
            'env', 'exec_mode', 'instances', 'autorestart', 'cron_restart', 'merge_logs',
            'log_date_format', 'out_file', 'error_file'
        ]
        app_config = {}
        for key in pm2_keys:
            if key in project_data and project_data[key] not in (None, ''):
                app_config[key] = project_data[key]
        if 'path' in project_data:
            app_config['cwd'] = project_data['path']
        ecosystem = {"apps": [app_config]}
        temp_eco_file = None
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, encoding='utf-8') as fp:
                temp_eco_file = fp.name
                json.dump(ecosystem, fp, indent=2)
            command = f'pm2 start "{temp_eco_file}"'
            output = self._run_command(command)
            if output:
                self.action_finished.emit("Process Started", f"Attempted to start '{app_config['name']}'.\n{output}")
        finally:
            if temp_eco_file and os.path.exists(temp_eco_file):
                os.remove(temp_eco_file)
            self.get_process_list()

    @Slot(str)
    def stop_process(self, proc_id_or_name):
        print(f"[DEBUG WORKER] SLOT: stop_process for {proc_id_or_name}")
        output = self._run_command(f"pm2 stop {proc_id_or_name}")
        if output:
            self.action_finished.emit("Process Stopped", f"Stopped '{proc_id_or_name}'.\n{output}")
        self.get_process_list()

    @Slot(str)
    def restart_process(self, proc_id_or_name):
        print(f"[DEBUG WORKER] SLOT: restart_process for {proc_id_or_name}")
        output = self._run_command(f"pm2 restart {proc_id_or_name}")
        if output:
            self.action_finished.emit("Process Restarted", f"Restarted '{proc_id_or_name}'.\n{output}")
        self.get_process_list()
        
    @Slot(str)
    def delete_process(self, proc_id_or_name):
        print(f"[DEBUG WORKER] SLOT: delete_process for {proc_id_or_name}")
        output = self._run_command(f"pm2 delete {proc_id_or_name}")
        if output:
             self.action_finished.emit("Process Deleted", f"Deleted '{proc_id_or_name}' from PM2.\n{output}")
        self.get_process_list()

    @Slot(str)
    def reload_process(self, proc_id_or_name):
        print(f"[DEBUG WORKER] SLOT: reload_process for {proc_id_or_name}")
        output = self._run_command(f"pm2 reload {proc_id_or_name}")
        if output:
            self.action_finished.emit("Process Reloaded", f"Reloaded '{proc_id_or_name}'.\n{output}")
        self.get_process_list()

    @Slot()
    def stop_all(self):
        print("[DEBUG WORKER] SLOT: stop_all")
        output = self._run_command("pm2 stop all")
        if output:
            self.action_finished.emit("All Processes Stopped", output)
        self.get_process_list()

    @Slot()
    def restart_all(self):
        print("[DEBUG WORKER] SLOT: restart_all")
        output = self._run_command("pm2 restart all")
        if output:
            self.action_finished.emit("All Processes Restarted", output)
        self.get_process_list()