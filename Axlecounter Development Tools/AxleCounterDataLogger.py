import serial.tools.list_ports
import serial
from datetime import datetime
import json
import keyboard

comportlist = [comport.device for comport in serial.tools.list_ports.comports()]
if comportlist:
    port = comportlist[-1]
else:
    print("No valid com port")
    exit()

# Configure the serial port
ser = serial.Serial(port, 19200)

# Create an empty list to store the data
data = []

# Read data from the serial port
recording = False
stopandsave = False
while not stopandsave:
    if keyboard.is_pressed('t'):
        recording = True
        print("Recording has started")
    elif keyboard.is_pressed('p'):
        recording = False
        stopandsave = True
        print("Recording ended")

    if recording:
        line = ser.readline().decode().strip()
        if line:
            # Parse the data into a dictionary
            values = line.split(',')
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S.%f')
            try:
                record = {
                    'timestamp': timestamp,
                    'value1': int(values[0]),
                    'value2': int(values[1]),
                    'value3': int(values[2])
                }
                data.append(record)
            except:
                pass
    # Check if the user has pressed Ctrl+C to stop the program
    if keyboard.is_pressed('ctrl+c'):
        break

# Generate the filename using the current date and time
now = datetime.now()
filename = 'data_{}.json'.format(now.strftime('%Y-%m-%d_%H-%M-%S'))

# Save the data to a JSON file
with open(filename, 'w') as f:
    json.dump(data, f)


