#!/usr/bin/env python3
import asyncio
import pyplumio
import logging

import server_async

from pymodbus.constants import Endian
from pymodbus.datastore import (
    ModbusSequentialDataBlock,
    ModbusServerContext,
    ModbusSlaveContext,
)
from pymodbus.payload import BinaryPayloadBuilder

_logger = logging.getLogger(__name__)


async def updating_task(context):
    #   Update values in server.
    #
    #   It should be noted that getValues and setValues are not safe
    #   against concurrent use.

    async with pyplumio.open_serial_connection("/dev/ttyUSB0", baudrate=115200) as conn:
        fc_as_hex = 3
        slave_id = 0x00
        address = 0x00

        # update loop
        try:
            while True:
                values = await read_data(conn)
                context[slave_id].setValues(fc_as_hex, address, values)

                txt = f"updating_task: read values: {values!s} at address {address!s}"
                print(txt)
                _logger.debug(txt)
                await asyncio.sleep(10)

        except asyncio.CancelledError:
            pass  # Ignore CancelledError when the task is canceled
        await conn.close()

async def read_data(conn):
    ecomax = await conn.get("ecomax")
    heating_temp            = await ecomax.get( "heating_temp"           )
    feeder_temp             = await ecomax.get( "feeder_temp"            )
    #   water_heater_temp       = await ecomax.get( "water_heater_temp"      )
    #   outside_temp            = await ecomax.get( "outside_temp"           )
    return_temp             = await ecomax.get( "return_temp"            )
    exhaust_temp            = await ecomax.get( "exhaust_temp"           )
    #   optical_temp            = await ecomax.get( "optical_temp"           )
    upper_buffer_temp       = await ecomax.get( "upper_buffer_temp"      )
    lower_buffer_temp       = await ecomax.get( "lower_buffer_temp"      )
    #   upper_solar_temp        = await ecomax.get( "upper_solar_temp"       )
    #   lower_solar_temp        = await ecomax.get( "lower_solar_temp"       )
    #   fireplace_temp          = await ecomax.get( "fireplace_temp"         )
    #   total_gain              = await ecomax.get( "total_gain"             )
    #   hydraulic_coupler_temp  = await ecomax.get( "hydraulic_coupler_temp" )
    #   exchanger_temp          = await ecomax.get( "exchanger_temp"         )
    #   air_in_temp             = await ecomax.get( "air_in_temp"            )
    #   air_out_temp            = await ecomax.get( "air_out_temp"           )
    heating_target          = await ecomax.get( "heating_target"         )
    heating_status          = await ecomax.get( "heating_status"         )
    fuel_level              = await ecomax.get( "fuel_level"             )
    #   fuel_consumption        = await ecomax.get( "fuel_consumption"       )
    fan_power               = await ecomax.get( "fan_power"              )

    retval = [
        int(heating_temp * 100),
        int(feeder_temp * 100),
    #       int(water_heater_temp * 100),
    #       int(outside_temp * 100),
        int(return_temp * 100),
        int(exhaust_temp * 100),
    #       int(optical_temp * 100),
        int(upper_buffer_temp * 100),
        int(lower_buffer_temp * 100),
    #       int(upper_solar_temp * 100),
    #       int(lower_solar_temp * 100),
    #       int(fireplace_temp * 100),
    #       int(total_gain * 100),
    #       int(hydraulic_coupler_temp * 100),
    #       int(exchanger_temp * 100),
    #       int(air_in_temp * 100),
    #       int(air_out_temp * 100)
        int(heating_target * 100),
        int(heating_status),
        int(fuel_level),
    #       int(fuel_consumption * 100)
        int(fan_power)
    ]
    return retval
        


def setup_payload_server(cmdline=None):
    """Define payload for server and do setup."""

    block = ModbusSequentialDataBlock(1, [0] * 20)
    store = ModbusSlaveContext(hr=block, ir=block,slave=1)
    context = ModbusServerContext(slaves=store, single=True)
    return server_async.setup_server(
        description="Run payload server.", cmdline=cmdline, context=context
    )

async def run_updating_server(args):
    """Start updating_task concurrently with the current task."""
    task = asyncio.create_task(updating_task(args.context))
    task.set_name("example updating task")
    await server_async.run_async_server(args)  # start the server
    task.cancel()


async def main(cmdline=None):
    """Combine setup and run."""
    run_args = setup_payload_server(cmdline=cmdline)
    await run_updating_server(run_args)

if __name__ == "__main__":
    asyncio.run(main(), debug=False)  # pragma: no cover
