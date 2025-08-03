# Server Monitor for PM2

**Server Monitor** is a user-friendly desktop application for Windows designed to monitor and manage your [PM2](https://pm2.keymetrics.io/) processes. Built with Python and PySide6, it provides a rich graphical user interface to visualize process status, resource usage, and logs in real-time, offering a powerful alternative to the command line.

Whether you are developing Node.js applications or managing multiple scripts, Server Monitor simplifies your workflow by bringing all essential PM2 functionalities into one intuitive dashboard.

![Server Monitor Dashboard](https://i.imgur.com/YOUR_DASHBOARD_SCREENSHOT.png)  <!-- Replace with an actual screenshot URL -->

---

## Features

- **System Dashboard**: Get a high-level overview of your PM2 ecosystem. Instantly see the status of the PM2 daemon, the number of online, stopped, or errored processes, and aggregated resource consumption.
- **Real-Time Process Monitoring**: The application automatically refreshes to provide live updates on process status (online, stopped, errored), CPU usage, and memory footprint.
- **Detailed Process View**: Dive deep into individual processes. View detailed configuration, paths, arguments, and performance metrics with historical graphs for CPU and memory usage over the last 60 seconds.
- **Integrated Log Viewer**: No more `pm2 logs` in a separate terminal. View formatted and color-coded logs directly within the app for any selected process. The viewer intelligently parses timestamps and cleans up log prefixes for better readability.
- **Full Process Control**:
    - **Global Actions**: Start or kill the PM2 daemon, and restart or stop all processes with a single click.
    - **Individual Actions**: Start, stop, restart, reload, or delete any process directly from the UI.
- **Project Management**:
    - **Add & Remove Projects**: Easily add new scripts to be managed by PM2 or remove them entirely from the application and PM2's process list.
    - **Persistent Configuration**: Your list of projects is saved locally in your user profile, so you don't have to reconfigure them every time.
- **Advanced Process Configuration**: A comprehensive settings dialog allows you to configure every detail of your process, mapping directly to `ecosystem.json` options. This includes:
    - Execution mode (fork vs. cluster) and instances.
    - Custom interpreters (e.g., `python`) and arguments.
    - Watch & Restart strategies, including memory limits and cron-based restarts.
    - Custom log file paths and environment variables.
- **Smooth & Responsive UI**:
    - **Fast Startup**: A splash screen and asynchronous pre-loader ensure the application launches quickly without freezing.
    - **Non-Blocking Operations**: All PM2 commands run in a background thread, keeping the UI responsive at all times.
    - **Modern Dark Theme**: A sleek, modern dark theme provides a comfortable viewing experience.

---

## Installation

Server Monitor is distributed as a simple installer for Windows.

1.  Download the latest `Server-Monitor-Installer.exe` from the [Releases page](https://github.com/YOUR_USERNAME/YOUR_REPO/releases).
2.  Run the installer and follow the on-screen instructions. The application will be installed, and a shortcut will be created on your Desktop and in the Start Menu.
3.  Launch the application. It will automatically detect if the PM2 daemon is running and display your processes.

**Prerequisites**:
*   **Windows Operating System**.
*   **Node.js and PM2 must be installed** and accessible from your system's PATH. You can install PM2 globally by running:
    ```bash
    npm install pm2 -g
    ```

---

## How to Use

### The Main Interface

The application is divided into three main areas:
1.  **Toolbar (Top)**: Provides quick access to global actions like starting/killing the PM2 daemon, refreshing the process list, and adding new projects.
2.  **Project Sidebar (Left)**: Lists all your configured projects, including a link to the main System Dashboard. The color of the icon next to each project indicates its current status.
3.  **Main Content Area (Right)**: Displays either the System Dashboard or the detailed view for a selected project.

### System Dashboard

The dashboard is the default view. It gives you a birds-eye view of your system.

![System Dashboard](https://i.imgur.com/YOUR_DASHBOARD_DETAIL_SCREENSHOT.png) <!-- Replace with an actual screenshot URL -->

- **Process Overview**: Shows the count of your projects in different states.
- **Resource Usage**: Displays the total CPU and Memory being consumed by all *online* processes via intuitive gauges.
- **Global Actions**: Buttons to control the PM2 daemon and all processes.

### Managing a Project

Click on any project in the sidebar to open its detail view.

![Project Detail View](https://i.imgur.com/YOUR_PROJECT_DETAIL_SCREENSHOT.png) <!-- Replace with an actual screenshot URL -->

- **Actions**: The buttons at the top allow you to `Start`, `Stop`, `Restart`, `Reload`, or `Delete` the selected process.
- **Key Stats**: View the process status, uptime, restart count, and PM2 ID.
- **Performance**: Monitor real-time CPU and Memory usage with gauges and historical performance graphs.
- **Configuration Details**: See all the configured settings for the process, such as its script path, arguments, and logging setup.
- **Logs**: The log viewer at the bottom displays the latest log output for the process.

### Adding a New Project

1.  Click the **"Add Project"** button ( <img src="https://i.imgur.com/YOUR_PLUS_ICON.png" width="16" /> ) in the toolbar.
2.  A file dialog will open. Navigate to and select the entry script for your application (e.g., `app.js`, `server.py`).
3.  You will be prompted to enter a unique name for the project. A default name based on the parent folder is suggested.
4.  Click **OK**. The project is now added to your list and will appear in the sidebar. You can start it from its detail view.

### Configuring a Project

1.  In the project sidebar, click the **cogwheel icon** ( <img src="https://i.imgur.com/YOUR_COG_ICON.png" width="16" /> ) next to the project you want to configure.
2.  The Project Settings dialog will open, allowing you to modify all PM2-related options.
3.  After making your changes, click **OK**. If the process is currently running, you will be prompted to stop and delete it from PM2 before the new configuration can be applied. This is necessary for changes to take effect.

---

## Technical Overview

- **Framework**: The application is built using **Python 3** and the **PySide6** library (the official Python bindings for Qt).
- **Backend Communication**: It interacts with your local PM2 installation by executing PM2 commands in a background thread using Python's `subprocess` module. This ensures the GUI remains fluid and responsive.
- **Data Management**: Project configurations are stored in a `projects.json` file located in your user's `AppData/Roaming` directory, ensuring your setup is preserved across application restarts.
- **Asynchronous Loading**: To provide a smooth startup experience, a preloader on a separate thread fetches the initial PM2 state while a splash screen is displayed.

---

## Contributing

Contributions are welcome! If you have ideas for new features, bug fixes, or improvements, please feel free to open an issue or submit a pull request.

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
