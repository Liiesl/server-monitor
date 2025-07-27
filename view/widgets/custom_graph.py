print('trying to import pyqtgraph')
import pyqtgraph as pg
print('succesfully import pyqtgraph')
from PySide6.QtWidgets import QWidget, QVBoxLayout, QTabWidget
from collections import deque
# Configure pyqtgraph for a dark theme to match the UI style
pg.setConfigOption('background', '#31363B')
pg.setConfigOption('foreground', 'w')

# --- NEW: Widget for Performance Graphs ---
class PerformanceGraphWidget(QWidget):
    """A widget with tabs for CPU, Memory, and Combined performance graphs."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.max_points = 60  # Show last 60 seconds of data

        # Data storage using deque for efficient fixed-length storage
        self.time_data = list(range(self.max_points))
        self.cpu_data = deque([0] * self.max_points, maxlen=self.max_points)
        self.mem_data = deque([0] * self.max_points, maxlen=self.max_points)

        self.init_ui()
        self.clear() # Initialize plots with empty/zeroed data

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 10, 0, 0) # Add some top margin
        main_layout.setSpacing(0)

        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create the plots for each tab
        self.cpu_plot_widget = self._create_cpu_plot()
        self.mem_plot_widget = self._create_mem_plot()
        self.combined_plot_widget = self._create_combined_plot()

        # Add plots as tabs
        self.tabs.addTab(self.cpu_plot_widget, "CPU")
        self.tabs.addTab(self.mem_plot_widget, "Memory")
        self.tabs.addTab(self.combined_plot_widget, "Combined")

    def _create_cpu_plot(self):
        plot = pg.PlotWidget(title="CPU Usage (%) over last 60s")
        plot.setLabel('left', 'CPU', units='%')
        plot.setLabel('bottom', 'Time (seconds ago)')
        plot.setYRange(0, 100, padding=0.1)
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.getAxis('bottom').setTicks([[(0, '60'), (30, '30'), (59, '0')]])
        # --- MODIFIED: Disable mouse interaction (zoom/pan) ---
        plot.setMouseEnabled(x=False, y=False)
        self.cpu_curve = plot.plot(self.time_data, list(self.cpu_data), pen=pg.mkPen('#0078D7', width=2)) # Blue
        return plot

    def _create_mem_plot(self):
        plot = pg.PlotWidget(title="Memory Usage (MB) over last 60s")
        plot.setLabel('left', 'Memory', units='MB')
        plot.setLabel('bottom', 'Time (seconds ago)')
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.getAxis('bottom').setTicks([[(0, '60'), (30, '30'), (59, '0')]])
        # --- MODIFIED: Disable mouse interaction (zoom/pan) ---
        plot.setMouseEnabled(x=False, y=False)
        self.mem_curve = plot.plot(self.time_data, list(self.mem_data), pen=pg.mkPen('#4CAF50', width=2)) # Green
        return plot

    def _create_combined_plot(self):
        plot = pg.PlotWidget(title="CPU & Memory Usage over last 60s")
        plot.setLabel('bottom', 'Time (seconds ago)')
        plot.addLegend(offset=(-10, 10))
        plot.showGrid(x=True, y=True, alpha=0.3)
        plot.getAxis('bottom').setTicks([[(0, '60'), (30, '30'), (59, '0')]])
        # --- MODIFIED: Disable mouse interaction (zoom/pan) on the main plot ---
        plot.setMouseEnabled(x=False, y=False)

        # Left Y-axis for CPU
        plot.setLabel('left', 'CPU', units='%', color='#0078D7')
        plot.getAxis('left').setPen(pg.mkPen('#0078D7', width=1.5))
        plot.setYRange(0, 100, padding=0)
        self.combined_cpu_curve = plot.plot(pen=pg.mkPen('#0078D7', width=2), name="CPU (%)")

        # Right Y-axis for Memory
        p2 = pg.ViewBox()
        # --- MODIFIED: Also disable interaction on the secondary Y-axis ViewBox ---
        p2.setMouseEnabled(x=False, y=False)
        plot.showAxis('right')
        plot.scene().addItem(p2)
        plot.getAxis('right').linkToView(p2)
        p2.setXLink(plot)
        plot.getAxis('right').setLabel('Memory', units='MB', color='#4CAF50')
        plot.getAxis('right').setPen(pg.mkPen('#4CAF50', width=1.5))

        self.combined_mem_curve = pg.PlotCurveItem(pen=pg.mkPen('#4CAF50', width=2), name="Memory (MB)")
        p2.addItem(self.combined_mem_curve)

        def update_view():
            p2.setGeometry(plot.getViewBox().sceneBoundingRect())
            p2.linkedViewChanged(plot.getViewBox(), p2.XAxis)
        plot.getViewBox().sigResized.connect(update_view)
        update_view()
        return plot

    def update_data(self, cpu_val, mem_val):
        """Appends new data points and updates the graphs."""
        self.cpu_data.append(cpu_val)
        self.mem_data.append(mem_val)

        self.cpu_curve.setData(self.time_data, list(self.cpu_data))
        self.mem_curve.setData(self.time_data, list(self.mem_data))
        self.combined_cpu_curve.setData(self.time_data, list(self.cpu_data))
        self.combined_mem_curve.setData(self.time_data, list(self.mem_data))

        # Auto-range memory axes as they can vary wildly
        self.mem_plot_widget.getPlotItem().enableAutoRange('y', True)
        mem_viewbox = self.combined_mem_curve.getViewBox()
        if mem_viewbox:
            mem_viewbox.enableAutoRange('y', True)

    def clear(self):
        """Resets graphs to an empty/zeroed state."""
        self.cpu_data.clear()
        self.mem_data.clear()
        self.cpu_data.extend([0] * self.max_points)
        self.mem_data.extend([0] * self.max_points)

        self.update_data(0, 0) # Update with zeros to clear visually

        # Reset memory autorange to a default state
        self.mem_plot_widget.getPlotItem().setYRange(0, 1, padding=0)
        mem_viewbox = self.combined_mem_curve.getViewBox()
        if mem_viewbox:
            mem_viewbox.setYRange(0, 1, padding=0)