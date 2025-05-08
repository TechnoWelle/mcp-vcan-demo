#!/usr/bin/env python3
import threading
import time
import can
import cantools

DBC_PATH = "vehicle.dbc"

# 1. Load and verify the DBC file
try:
    db = cantools.database.load_file(DBC_PATH)
    print(f"Loaded DBC: {DBC_PATH} with {len(db.messages)} messages.")
except Exception as e:
    print(f"Failed to load DBC: {e}")
    exit(1)

# 2. Set up CAN bus (vcan0)
bus = can.ThreadSafeBus(interface="socketcan", channel="vcan0")

# 3. Example data and periods for each message
sim_defs = [
    # (message_name, period_seconds, example_signal_dict)
    ("ENGINE_STATUS", 0.05, {"ENGINE_SPEED": 1200, "ENGINE_TEMP": 85, "THROTTLE_POSITION": 20, "ENGINE_LOAD": 30, "FUEL_LEVEL": 50}),
    ("ABS_STATUS", 0.1, {"WHEEL_SPEED_FL": 50, "WHEEL_SPEED_FR": 50, "WHEEL_SPEED_RL": 48, "WHEEL_SPEED_RR": 48}),
    ("AIRBAG_STATUS", 0.2, {"CRASH_DETECTED": 0, "PASSENGER_AIRBAG_DISABLED": 0, "SEATBELT_DRIVER": 1, "SEATBELT_PASSENGER": 1, "SYSTEM_STATUS": 0}),
    ("BODY_STATUS", 0.5, {"DOOR_OPEN_FL": 0, "DOOR_OPEN_FR": 0, "DOOR_OPEN_RL": 0, "DOOR_OPEN_RR": 0, "HEADLIGHTS_ON": 1, "INTERIOR_TEMP": 22, "AMBIENT_LIGHT": 100, "VEHICLE_LOCKED": 1, "WIPER_STATUS": 1}),
]

class SimThread(threading.Thread):
    def __init__(self, msg_name, period, signals):
        super().__init__(daemon=True)
        self.msg = db.get_message_by_name(msg_name)
        self.period = period
        self.signals = signals

    def run(self):
        while True:
            try:
                data = self.msg.encode(self.signals)
                can_msg = can.Message(arbitration_id=self.msg.frame_id, data=data, is_extended_id=False)
                bus.send(can_msg)
            except Exception as e:
                print(f"Error sending {self.msg.name}: {e}")
            time.sleep(self.period)

# 4. Start simulation threads
threads = []
for msg_name, period, signals in sim_defs:
    t = SimThread(msg_name, period, signals)
    threads.append(t)
    t.start()

print("ECU simulation running. Press Ctrl-C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down simulation...")
    bus.shutdown()