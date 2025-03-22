import serial
import matplotlib.pyplot as plt
import time

# --- Serial Setup ---
# Adjust port name and baud rate as needed.
ser = serial.Serial('COM8', 115200, timeout=1)

# Duration of the burst in seconds (set to 10 or 5 as required)
duration = 5  #  5-second burst

# --- Data Storage ---
# We'll store timestamps (relative to the start) and three value streams.
timestamps = []
values1 = []
values2 = []
values3 = []

# Record the start time.
start_time = time.time()

print("Starting data collection for {} seconds...".format(duration))

# --- Data Collection Loop ---
while time.time() - start_time < duration:
    try:
        # Read one line from the serial port.
        line = ser.readline().decode('utf-8').strip()
        if not line:
            continue  # Skip if no data is received.

        # Expect data in the format: "val1,val2,val3"
        parts = line.split(',')
        if len(parts) != 3:
            print("Unexpected data format:", line)
            continue

        # Convert string parts to float.
        val1 = int(parts[0])
        val2 = int(parts[1])
        val3 = int(parts[2])

        # Save the values along with the relative timestamp.
        current_time = time.time() - start_time
        timestamps.append(current_time)
        values1.append(val1)
        values2.append(val2)
        values3.append(val3)

    except Exception as e:
        print("Error reading or parsing data:", e)
        continue

ser.close()
print("Data collection finished. {} data points captured.".format(len(timestamps)))

# --- Plotting the Data ---
fig, ax = plt.subplots()
ax.plot(timestamps, values1, label='Value 1', color='blue')
ax.plot(timestamps, values2, label='Value 2', color='red')
ax.plot(timestamps, values3, label='Value 3', color='green')

ax.set_title("Serial Data Burst ({} seconds)".format(duration))
ax.set_xlabel("Time (s)")
ax.set_ylabel("Value")
ax.legend()
ax.grid(True)

# The interactive matplotlib window will allow zooming/panning.
plt.show()
