import sys
import serial
import threading
import time
from collections import deque

from PyQt5 import QtWidgets, QtCore
import pyqtgraph as pg

# --- Config ---
PORT = 'COM9'
BAUD = 115200
ROLLING_SECONDS = 10
MAX_SAMPLES = 5000  # Enough to hold 10s of data at 500Hz

# --- Buffers ---
timestamps = deque(maxlen=MAX_SAMPLES)
values1 = deque(maxlen=MAX_SAMPLES)
values2 = deque(maxlen=MAX_SAMPLES)
values3 = deque(maxlen=MAX_SAMPLES)

# --- Serial Reading Thread ---
def serial_reader():
    ser = serial.Serial(PORT, BAUD, timeout=0.01)
    start_time = time.time()
    while True:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
            parts = line.split(',')
            if len(parts) != 3:
                continue

            v1 = int(parts[0])
            v2 = int(parts[1])
            v3 = int(parts[2])
            t = time.time() - start_time

            timestamps.append(t)
            values1.append(v1)
            values2.append(v2)
            values3.append(v3)

        except Exception as e:
            print("Serial read error:", e)

# --- PyQtGraph App ---
class SerialPlotApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Real-Time Serial Plot (pyqtgraph)")
        self.resize(800, 400)

        self.plot_widget = pg.PlotWidget()
        self.setCentralWidget(self.plot_widget)

        self.plot_widget.addLegend()
        self.plot_widget.setLabel('bottom', 'Time', 's')
        self.plot_widget.setLabel('left', 'Value')

        self.curve1 = self.plot_widget.plot(pen='b', name='Value 1')
        self.curve2 = self.plot_widget.plot(pen='r', name='Value 2')
        self.curve3 = self.plot_widget.plot(pen='g', name='Value 3')

        self.paused = False

        # Add pause toggle
        self.pause_text = pg.TextItem("[SPACE] to pause", anchor=(1,1), color='y')
        self.plot_widget.addItem(self.pause_text)
        self.pause_text.setPos(0, 0)

        # Timer for refreshing plot
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_plot)
        self.timer.start(33)  # ~30 FPS

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Space:
            self.paused = not self.paused
            print("Paused" if self.paused else "Resumed")
            self.pause_text.setText("[PAUSED]" if self.paused else "[SPACE] to pause")

    def update_plot(self):
        if self.paused or not timestamps:
            return

        # Only plot the last N seconds of data
        t0 = timestamps[-1] - ROLLING_SECONDS
        idx = next((i for i, t in enumerate(timestamps) if t >= t0), 0)

        x = list(timestamps)[idx:]
        y1 = list(values1)[idx:]
        y2 = list(values2)[idx:]
        y3 = list(values3)[idx:]

        self.curve1.setData(x, y1)
        self.curve2.setData(x, y2)
        self.curve3.setData(x, y3)

        self.plot_widget.setXRange(x[0], x[-1], padding=0)

# --- Launch everything ---
if __name__ == '__main__':
    threading.Thread(target=serial_reader, daemon=True).start()

    app = QtWidgets.QApplication(sys.argv)
    window = SerialPlotApp()
    window.show()
    sys.exit(app.exec_())
