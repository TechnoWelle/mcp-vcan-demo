from mcp.server.fastmcp import FastMCP, Context
from mcp.server.fastmcp.prompts.base import UserMessage, AssistantMessage, SystemMessage

import can
import time
import cantools


mcp = FastMCP("Vehicle CAN MCP")
can_bus = can.interface.Bus(channel="vcan0", interface="socketcan")

try:
    db = cantools.database.load_file('vehicle.dbc')
except FileNotFoundError:
    raise Exception("DBC file not found. Please ensure 'vehicle.dbc' is in the correct directory.")


@mcp.tool()
async def read_can_frames(duration_s: float = 1.0, ctx: Context = None) -> list[dict]:
    """
    Listen on CAN bus for duration_s seconds and return frames.

    Args:
        duration_s: Duration to listen for in seconds.
        ctx: Context for reporting progress.

    Returns:
        A list of dictionaries containing frame information.
    """
    frames = []
    end = time.time() + duration_s
    count = 0
    while time.time() < end:
        msg = can_bus.recv(timeout=0.1)
        if msg:
            frames.append({
                "timestamp": msg.timestamp,
                "arbitration_id": hex(msg.arbitration_id),
                "data": list(msg.data)
            })
            count += 1
            if ctx:
                await ctx.report_progress(count)
    return frames


@mcp.tool()
def decode_can_frame(arbitration_id: int, data: list[int]) -> dict:
    """
    Decode a CAN frame using the loaded DBC file.

    Args:
        arbitration_id: The CAN frame ID (integer).
        data: The CAN frame data as a list of bytes.

    Returns:
        Decoded signal values as a dictionary, or error info.
    """
    try:
        msg = db.get_message_by_frame_id(arbitration_id)
        decoded = msg.decode(bytes(data))
        return {"status": "success", "signals": decoded}
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

@mcp.tool()
async def filter_frames(
    arbitration_id: int = None,
    signal_name: str = None,
    duration_s: float = 1.0,
    ctx: Context = None
) -> list[dict]:
    """
    Filter CAN frames by arbitration ID or signal value.

    Args:
        arbitration_id: Optional CAN frame ID to filter.
        signal_name: Optional signal name to filter.
        duration_s: Duration to listen for in seconds.
        ctx: Context for reporting progress.

    Returns:
        List of matching frames or signal values.
    """
    end = time.time() + duration_s
    results = []
    count = 0
    while time.time() < end:
        msg = can_bus.recv(timeout=0.1)
        if msg:
            if arbitration_id is not None and msg.arbitration_id != arbitration_id:
                continue
            frame_info = {
                "timestamp": msg.timestamp,
                "arbitration_id": hex(msg.arbitration_id),
                "data": list(msg.data)
            }
            if signal_name:
                try:
                    message = db.get_message_by_frame_id(msg.arbitration_id)
                    decoded = message.decode(msg.data)
                    if signal_name in decoded:
                        frame_info["signal_value"] = decoded[signal_name]
                        results.append(frame_info)
                except Exception:
                    continue
            else:
                results.append(frame_info)
            count += 1
            if ctx:
                await ctx.report_progress(count)
    return results

@mcp.tool()
async def monitor_signal(
    signal_name: str,
    duration_s: float = 2.0,
    ctx: Context = None
) -> list[dict]:
    """
    Monitor a specific signal on the CAN bus for a duration.

    Args:
        signal_name: Name of the signal to monitor.
        duration_s: Duration to listen for in seconds.
        ctx: Context for reporting progress.

    Returns:
        List of timestamped signal values.
    """
    end = time.time() + duration_s
    results = []
    count = 0
    while time.time() < end:
        msg = can_bus.recv(timeout=0.1)
        if msg:
            try:
                message = db.get_message_by_frame_id(msg.arbitration_id)
                decoded = message.decode(msg.data)
                if signal_name in decoded:
                    results.append({
                        "timestamp": msg.timestamp,
                        "value": decoded[signal_name]
                    })
                    count += 1
                    if ctx:
                        await ctx.report_progress(count)
            except Exception:
                continue
    return results

@mcp.resource("file://vehicle.dbc")
def dbc_info() -> dict:
    """
    Loads the vehicle DBC file and extracts its most useful information.

    Returns:
        A dictionary containing structured information about the DBC file,
        or None if the file could not be loaded.
    """
    info = {}

    try:
        info['status'] = 'success'

        # 1. Basic Database Info
        info['version'] = db.version if db.version else 'N/A'

        # 3. Nodes
        info['nodes'] = [node.name for node in db.nodes]

        # 4. Messages and their Signals
        messages_info = []
        for msg in db.messages:
            message_details = {
                'name': msg.name,
                'id': msg.frame_id, # Use integer ID
                'id_hex': hex(msg.frame_id), # Also include hex representation
                'length': msg.length,
                'cycle_time_ms': msg.cycle_time,
                'senders': msg.senders,
                'signals': []
            }

            for sig in msg.signals:
                signal_details = {
                    'name': sig.name,
                    'start_bit': sig.start,
                    'length_bits': sig.length,
                    'scale': sig.scale,
                    'offset': sig.offset,
                    'minimum': sig.minimum,
                    'maximum': sig.maximum,
                    'unit': sig.unit,
                    'choices': sig.choices, # Dictionary of value descriptions
                    'is_signed': sig.is_signed,
                    'is_float': sig.is_float,
                    'byte_order': sig.byte_order,
                    'receivers': sig.receivers,
                }
                message_details['signals'].append(signal_details)

            messages_info.append(message_details)

        info['messages'] = messages_info

    except FileNotFoundError:
        info['status'] = 'error'
        info['message'] = f"DBC file not found"
    except Exception as e:
        info['status'] = 'error'
        info['message'] = f"An unexpected error occurred: {e}"

    return info


if __name__ == "__main__":
    mcp.settings.port = 6278
    mcp.run(transport="sse")

