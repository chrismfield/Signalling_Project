import json
from datetime import datetime
import matplotlib.pyplot as plt
from tkinter import filedialog
import tkinter as tk

# Show file dialog to choose the JSON file to load
root = tk.Tk()
root.withdraw()
file_path = filedialog.askopenfilename()

# Load the data from the selected JSON file
with open(file_path, 'r') as f:
    data = json.load(f)

# Extract the timestamps and data values
timestamps = [datetime.strptime(record['timestamp'], '%Y-%m-%d %H:%M:%S.%f') for record in data]
values1 = [record['value1'] for record in data]
values2 = [record['value2'] for record in data]
values3 = [record['value3'] for record in data]

# Create a line graph of the data
plt.plot(timestamps, values1, label='Value 1')
plt.plot(timestamps, values2, label='Value 2')
plt.plot(timestamps, values3, label='Value 3')
plt.xlabel('Time')
plt.ylabel('Value')
plt.title('Data')
plt.legend()
plt.show()
