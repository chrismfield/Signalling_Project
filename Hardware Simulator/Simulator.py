import asyncio
import jsons
import logging

from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusSlaveContext,
    ModbusServerContext,
)
from pymodbus.server import StartAsyncSerialServer

port = "COM6"

# Enable logging
logging.basicConfig()
log = logging.getLogger()
log.setLevel(logging.WARN)

with open("default.json") as layout_file:
    jsoninfradata = jsons.loads(layout_file.read())


def setup_slaves():
    signals = {}
    points = {}
    axlecounters = {}
    plungers = {}

    # Define registers
    coils = ModbusSequentialDataBlock(0, [False] * 2000)
    discrete_inputs = ModbusSequentialDataBlock(0, [False] * 2000)
    holding_registers = ModbusSequentialDataBlock(0, [0] * 100)
    input_registers = ModbusSequentialDataBlock(0, [0] * 100)

    # NEW: ModbusDeviceContext replaces ModbusSlaveContext
    def create_slave():
        return ModbusSlaveContext(
            di=ModbusSequentialDataBlock(0, [False] * 2000),
            co=ModbusSequentialDataBlock(0, [False] * 2000),
            hr=ModbusSequentialDataBlock(0, [0] * 100),
            ir=ModbusSequentialDataBlock(0, [0] * 100),
        )

    # Build slave map
    for signal_val in jsoninfradata["Signals"].values():
        signals[signal_val["address"]] = create_slave()

    for point in jsoninfradata["Points"].values():
        points[point["address"]] = create_slave()

    for ac in jsoninfradata["AxleCounters"].values():
        axlecounters[ac["address"]] = create_slave()

    for plunger in jsoninfradata["Plungers"].values():
        plungers[plunger["address"]] = create_slave()

    # Combine all slaves
    slave_context = signals | points | axlecounters | plungers

    # Server context
    server_context = ModbusServerContext(slaves=slave_context, single=False)

    return server_context, points


server_context, points = setup_slaves()


async def update_input_registers(server_context):
    while True:
        try:
            for point in jsoninfradata["Points"].values():
                slave_id = point["address"]

                address = 1
                count = 2000

                # Read coils (function code 1)
                coils = server_context[slave_id].getValues(1, address, count)

                # Write to input registers (function code 4 → use 4, not 2)
                server_context[slave_id].setValues(2, address, coils)

        except Exception as e:
            logging.error(f"Error updating input registers: {e}")

        await asyncio.sleep(1)


async def main(port):
    # IMPORTANT: must be awaited in new pymodbus
    server_task = asyncio.create_task(
        StartAsyncSerialServer(
            context=server_context,
            port=port,
            baudrate=19200,
        )
    )

    update_task = asyncio.create_task(
        update_input_registers(server_context)
    )

    await asyncio.gather(server_task, update_task)


if __name__ == "__main__":
    asyncio.run(main(port))