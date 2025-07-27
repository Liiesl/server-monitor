# project_manager.py
import json, os, sys

class ProjectManager:
    """
    Handles loading, saving, and managing the list of projects
    from a JSON file in the user's AppData folder.
    """
    def __init__(self, filename='projects.json'):
        # --- NEW LOGIC FOR STORING DATA IN APPDATA ---
        # This is the correct, robust way for a Windows application.
        
        # Get the path to the user's Roaming AppData folder (e.g., C:\Users\YourUser\AppData\Roaming)
        app_data_path = os.getenv('APPDATA')
        
        # If APPDATA is not defined, fall back to a local folder (for non-Windows or edge cases)
        if not app_data_path:
            app_data_path = os.path.expanduser("~")

        # Define a specific folder for your application's data
        # Using CompanyName\AppName is standard practice.
        # CHANGE "LiieDev" and "Server Monitor" TO MATCH YOUR NSIS SCRIPT
        company_name = "LiieDev" 
        app_name = "Server Monitor"
        self.config_dir = os.path.join(app_data_path, company_name, app_name)

        # Ensure this directory exists. Create it if it doesn't.
        # The `exist_ok=True` prevents an error if the directory is already there.
        os.makedirs(self.config_dir, exist_ok=True)
        
        # The full path to the projects.json file is now inside this new directory.
        self.filename = os.path.join(self.config_dir, filename)
        
        print(f"[ProjectManager] Using configuration file: {self.filename}")
        # --- END OF NEW LOGIC ---
        
        self.projects = []
        self.load_projects()

    def load_projects(self):
        """Loads projects from the JSON file."""
        if not os.path.exists(self.filename):
            self.projects = []
            return

        try:
            with open(self.filename, 'r') as f:
                self.projects = json.load(f)
        except (json.JSONDecodeError, IOError):
            # In case of corrupt or empty file, start fresh
            self.projects = []

    def save_projects(self):
        """Saves the current list of projects to the JSON file."""
        try:
            with open(self.filename, 'w') as f:
                json.dump(self.projects, f, indent=4)
        except IOError as e:
            print(f"Error saving projects file: {e}")

    def get_projects(self):
        """Returns the list of all known projects."""
        return self.projects

    def add_project(self, name, path, script):
        """
        Adds a new project with minimal details, avoiding duplicates by name.
        More detailed configuration is added via update_project.
        """
        if any(p['name'] == name for p in self.projects):
            print(f"Project with name '{name}' already exists.")
            return False

        self.projects.append({
            'name': name,
            'path': path,
            'script': script,
            'autorestart': True, # Set a sensible default
            'watch': False
        })
        self.save_projects()
        return True

    def remove_project(self, project_name):
        """Removes a project by its name."""
        initial_count = len(self.projects)
        self.projects = [p for p in self.projects if p['name'] != project_name]
        if len(self.projects) < initial_count:
            self.save_projects()
            return True
        return False

    def find_project(self, project_name):
        """Finds a project by its name."""
        return next((p for p in self.projects if p['name'] == project_name), None)

    def update_project(self, old_name, **new_data):
        """
        Updates a project's details using a dictionary of new data.
        Identifies the project by its old name.
        """
        new_name = new_data.get('name')
        if not new_name:
            print("Update failed: new data must contain a 'name'.")
            return False

        # If the name is being changed, check if the new name is already taken
        # by a *different* project.
        if old_name != new_name:
            if any(p['name'] == new_name for p in self.projects):
                print(f"Update failed: project with new name '{new_name}' already exists.")
                return False
        
        project_to_update = self.find_project(old_name)
        if project_to_update:
            # Clear the old dictionary and update it with the new data.
            # This handles any added, removed, or changed fields from the settings dialog.
            project_to_update.clear()
            project_to_update.update(new_data)
            self.save_projects()
            return True
        
        print(f"Update failed: could not find project with name '{old_name}'.")
        return False