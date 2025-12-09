import asyncio
import jsons
import logging
from pymodbus.datastore import ModbusSequentialDataBlock, ModbusSlaveContext, ModbusServerContext
from pymodbus.server.async_io import StartAsyncSerialServer

port="COM7"

# Enable logging (makes it easier to debug if something goes wrong)
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.WARN)

with open("default_good_copy.json") as layout_file:
    jsoninfradata = jsons.loads(layout_file.read())

def setup_slaves():

    signals = {}
    points = {}
    axlecounters = {}
    plungers = {}

    # Define the Modbus registers
    coils = ModbusSequentialDataBlock(0, [False] * 2000)
    discrete_inputs = ModbusSequentialDataBlock(0, [False] * 2000)
    holding_registers = ModbusSequentialDataBlock(0, [0] * 100)
    input_registers = ModbusSequentialDataBlock(0, [0] * 100)

    single_slave = ModbusSlaveContext(
        di=discrete_inputs,
        co=coils,
        hr=holding_registers,
        ir=input_registers
    )

    for signal_key, signal_val in jsoninfradata["Signals"].items():
        signals[signal_val["address"]] = single_slave

    for point in jsoninfradata["Points"].values():
        points[point["address"]] = single_slave

    for ac in jsoninfradata["AxleCounters"].values():
        axlecounters[ac["address"]] = single_slave

#    for plunger in jsoninfradata["Plungers"].values():
#        plungers[plunger["address"]] = single_slave

    slave_context = signals|points|axlecounters|plungers
    # Define the Modbus server context
    server_context = ModbusServerContext(slaves=slave_context, single=False)
    return server_context, points

server_context, points = setup_slaves()

async def update_input_registers(server_context):
    """
    Periodically updates the input registers with values corresponding to coil registers.
    """
    while True:
        try:
            for point in jsoninfradata["Points"].values():
                # Get the coil values from the data store
                slave_id = point["address"]
                address = 0  # Start address
                count = 2000  # Number of registers to read
                coils = server_context[slave_id].getValues(1, address, count)  # Function code 1: Coils
                # Update input registers with the same values
                server_context[slave_id].setValues(2, address, coils)  # Function code 4: Input Registers
                logging.info(f"Updated input registers with coil values: {coils}")

        except Exception as e:
            logging.error(f"Error updating input registers: {e}")

        await asyncio.sleep(1)  # Update every 1 second

async def main(port):
    # Start the Modbus Serial server
    server_task = StartAsyncSerialServer(context=server_context, ignore_missing_slaves=True, port=port)

    # Start the input register update loop
    update_task = asyncio.create_task(update_input_registers(server_context))

    # Run both tasks concurrently
    await asyncio.gather(server_task, update_task)


if __name__ == "__main__":
    asyncio.run(main(port))