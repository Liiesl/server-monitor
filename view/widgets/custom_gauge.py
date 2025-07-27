import math
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import (QPainter, QColor, QPen, QFont, QConicalGradient,
                         QBrush)
from PySide6.QtCore import QRectF, Qt, QPointF

class HalfCircleGauge(QWidget):
    """
    A half-circle gauge widget that functions like a speedometer.
    It displays a static gradient arc (green-yellow-red) and a moving
    rectangular indicator to show the current value.
    """
    def __init__(self, title="Metric", unit="%", parent=None):
        super().__init__(parent)
        self._title = title
        self._unit = unit
        self._value = 0
        self._max_value = 100
        self._text = "N/A"
        self.setMinimumHeight(150)

    def setValue(self, value):
        """Sets the current value of the gauge."""
        self._value = max(0, min(value, self._max_value)) # Clamp value
        
        if value < 0:
            self._text = "N/A"
        else:
            self._text = f"{int(self._value)}{self._unit}"
        
        self.update() # Trigger repaint

    def setMaxValue(self, max_value):
        """Sets the maximum value of the gauge."""
        self._max_value = max_value if max_value > 0 else 100
        self.setValue(self._value) # Re-clamp and update
        self.update()

    def setText(self, text):
        """Manually set the center text, bypassing value/unit formatting."""
        self._text = text
        self.update()

    def setTitle(self, title):
        """Sets the title displayed below the gauge."""
        self._title = title
        self.update()

    def paintEvent(self, event):
        """
        --- Fixed painting logic for Speedometer Style ---
        - Draws a proper conical gradient arc (green -> yellow -> red).
        - Draws a small rectangular indicator that moves along the arc.
        - Keeps text and layout optimized for dark themes.
        """
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # --- 1. Define Layout & Font Metrics ---
        title_font = QFont("Segoe UI", 10)
        painter.setFont(title_font)
        fm_title = painter.fontMetrics()
        title_height = fm_title.height() + 5

        # Reserve space at the bottom for the title
        gauge_area = self.rect().adjusted(0, 0, 0, -title_height)

        # --- 2. Calculate Gauge Geometry ---
        padding = 15
        pen_width = 12
        diameter = min(gauge_area.width() - 2 * padding, (gauge_area.height() - padding) * 2)

        arc_rect_x = (self.width() - diameter) / 2
        arc_rect_y = gauge_area.bottom() - (diameter / 2)
        arc_rect = QRectF(arc_rect_x, arc_rect_y, diameter, diameter)

        # --- NEW: Calculate Color for Text based on Value ---
        text_color = QColor(220, 220, 220) # Default for "N/A"
        if self._value >= 0:
            # Define the gradient's key colors
            color_green = QColor("#4CAF50")
            color_yellow = QColor("#FFC107")
            color_red = QColor("#F44336")

            # Normalize value to a proportion p (0.0 to 1.0)
            p = self._value / self._max_value

            if p <= 0.5:
                # Interpolate between Green (at p=0.0) and Yellow (at p=0.5)
                # t is the local proportion between the two colors (0.0 to 1.0)
                t = p * 2.0
                r = color_green.redF() * (1 - t) + color_yellow.redF() * t
                g = color_green.greenF() * (1 - t) + color_yellow.greenF() * t
                b = color_green.blueF() * (1 - t) + color_yellow.blueF() * t
            else:
                # Interpolate between Yellow (at p=0.5) and Red (at p=1.0)
                # t is the local proportion between the two colors (0.0 to 1.0)
                t = (p - 0.5) * 2.0
                r = color_yellow.redF() * (1 - t) + color_red.redF() * t
                g = color_yellow.greenF() * (1 - t) + color_red.greenF() * t
                b = color_yellow.blueF() * (1 - t) + color_red.blueF() * t
            
            text_color = QColor.fromRgbF(r, g, b)


        # --- 3. Draw the Gradient Arc (Fixed Single Gradient) ---
        painter.setPen(Qt.PenStyle.NoPen)

        # Create a single conical gradient that spans the entire semicircle
        gradient = QConicalGradient(arc_rect.center(), 0)  # Start at 0 degrees (3 o'clock)
        
        # Map the colors to the correct positions for a semicircle from 180° to 0°
        # 180° (9 o'clock) = Green, 90° (12 o'clock) = Yellow, 0° (3 o'clock) = Red
        gradient.setColorAt(0.0, QColor("#F44336"))   # Red at 0°
        gradient.setColorAt(0.25, QColor("#FFC107"))  # Yellow at 90°
        gradient.setColorAt(0.5, QColor("#4CAF50"))   # Green at 180°
        gradient.setColorAt(0.75, QColor("#FFC107"))  # Yellow at 270° (not used in semicircle)
        gradient.setColorAt(1.0, QColor("#F44336"))   # Red at 360° (same as 0°)

        painter.setBrush(gradient)
        
        # Draw the semicircle from 180° to 0° (clockwise)
        painter.drawPie(arc_rect, 0 * 16, 180 * 16)

        # --- 4. "Punch out" the center by drawing a circle in the background color ---
        hole_rect = arc_rect.adjusted(pen_width, pen_width, -pen_width, -pen_width)
        bg_color = self.palette().window().color()
        painter.setBrush(bg_color)
        painter.drawEllipse(hole_rect)

        # --- 5. Cover the bottom part to make it a semicircle ---
        cover_rect = QRectF(arc_rect.left(), arc_rect.center().y(), arc_rect.width(), arc_rect.height() / 2 + 2)
        painter.drawRect(cover_rect)

        # --- 6. Draw the Moving Indicator Rectangle ---
        if self._value >= 0:
            angle = 180 - (self._value / self._max_value) * 180
            angle_rad = math.radians(angle)

            # Position indicator in the middle of the arc's width
            radius = (diameter / 2) - (pen_width / 2)
            center = arc_rect.center()
            indicator_x = center.x() + radius * math.cos(angle_rad)
            indicator_y = center.y() - radius * math.sin(angle_rad)

            painter.save()
            painter.translate(indicator_x, indicator_y)
            painter.rotate(90 - angle)

            indicator_height = pen_width + 6
            indicator_width = 3
            indicator_rect = QRectF(-indicator_width / 2, -indicator_height / 2,
                                    indicator_width, indicator_height)

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QColor(240, 240, 240))
            painter.drawRoundedRect(indicator_rect, 1, 1)
            painter.restore()

        # --- 7. Draw Center Text (Value) ---
        text_rect = arc_rect.adjusted(pen_width, pen_width, -pen_width, 0)
        text_rect.setHeight(text_rect.height() / 2 + pen_width)

        value_font = QFont("Segoe UI", 18, QFont.Weight.Bold)
        painter.setFont(value_font)
        # Use the dynamically calculated color for the text pen
        painter.setPen(text_color)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignHCenter | Qt.AlignmentFlag.AlignBottom, self._text)

        # --- 8. Draw Title Text (Indicator below gauge) ---
        painter.setFont(title_font)
        painter.setPen(QColor(180, 180, 180))
        title_draw_rect = QRectF(0, gauge_area.bottom() + 5, self.width(), title_height)
        painter.drawText(title_draw_rect, Qt.AlignmentFlag.AlignCenter, self._title)