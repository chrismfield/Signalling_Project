import minimalmodbus
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from collections import deque

# Configure the minimalmodbus instrument.
instrument = minimalmodbus.Instrument('COM9', 3)
instrument.serial.baudrate = 19200  # Set baud rate to 19200
instrument.serial.timeout = 1  # Timeout in seconds

# Create deques to store the most recent 100 readings for each register.
maxlen = 100
data_reg20 = deque([0] * maxlen, maxlen=maxlen)
data_reg21 = deque([0] * maxlen, maxlen=maxlen)
data_reg22 = deque([0] * maxlen, maxlen=maxlen)

# Set up the live plot.
fig, ax = plt.subplots()
x_vals = list(range(maxlen))
line20, = ax.plot(x_vals, list(data_reg20), label='Register 20', color='blue')
line21, = ax.plot(x_vals, list(data_reg21), label='Register 21', color='red')
line22, = ax.plot(x_vals, list(data_reg22), label='Register 22', color='green')

ax.set_title("Rolling Live Plot of Registers 20, 21, 22")
ax.set_xlabel("Reading Number (most recent 100)")
ax.set_ylabel("Register Value")
ax.legend()
ax.grid(True)


def update(frame):
    try:
        # Read registers 20, 21, and 22.
        reg20 = instrument.read_register(20, 0)  # no decimals
        reg21 = instrument.read_register(21, 0)
        reg22 = instrument.read_register(22, 0)
    except Exception as e:
        print("Error reading registers:", e)
        return line20, line21, line22

    # Append new readings to the deques.
    data_reg20.append(reg20)
    data_reg21.append(reg21)
    data_reg22.append(reg22)

    # Update the plot lines with the new data.
    line20.set_ydata(list(data_reg20))
    line21.set_ydata(list(data_reg21))
    line22.set_ydata(list(data_reg22))

    # Recompute limits and autoscale the y-axis.
    ax.relim()  # Recalculate limits based on current data
    ax.autoscale_view()  # Update the view limits

    return line20, line21, line22


# Disable blitting so that the entire figure (including the y-axis) is updated.
ani = animation.FuncAnimation(fig, update, interval=1, blit=False)

try:
    plt.show()
except KeyboardInterrupt:
    pass
