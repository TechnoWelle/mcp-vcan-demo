#!/usr/bin/env python3
import threading
import time
import can
import cantools
import random

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
    ("ENGINE_STATUS", 0.05),
    ("ABS_STATUS", 0.1),
    ("AIRBAG_STATUS", 0.2),
    ("BODY_STATUS", 0.5),
]



class SimThread(threading.Thread):
    def __init__(self, msg_name, period):
        super().__init__(daemon=True)
        self.msg = db.get_message_by_name(msg_name)
        self.period = period

    def generate_random_signals(self):
        signals = {}
        for sig in self.msg.signals:
            if sig.choices:
                signals[sig.name] = random.choice(list(sig.choices.keys()))
            else:
                min_val = sig.minimum if sig.minimum is not None else 0
                max_val = sig.maximum if sig.maximum is not None else min_val + 100

                # Generate a value in range
                if sig.is_float:
                    value = round(random.uniform(min_val, max_val), 2)
                else:
                    value = random.uniform(min_val, max_val)
                    # Convert physical value to raw, then round/clamp
                    raw = (value - sig.offset) / sig.scale if sig.scale else value
                    raw = int(round(raw))
                    # Clamp based on bit length
                    max_raw = 2 ** sig.length - 1
                    raw = max(0, min(raw, max_raw))
                    # Convert back to physical
                    value = raw * sig.scale + sig.offset if sig.scale else raw

                signals[sig.name] = value
        return signals


    def run(self):
        while True:
            try:
                signals = self.generate_random_signals()
                data = self.msg.encode(signals)
                can_msg = can.Message(arbitration_id=self.msg.frame_id, data=data, is_extended_id=False)
                bus.send(can_msg)
                print(f"Sent {self.msg.name}: {signals}")
            except Exception as e:
                print(f"Error sending {self.msg.name}: {e}")
            time.sleep(self.period)


# 4. Start simulation threads
threads = []
for msg_name, period in sim_defs:
    t = SimThread(msg_name, period)
    threads.append(t)
    t.start()


print("ECU simulation running. Press Ctrl-C to exit.")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("Shutting down simulation...")
    bus.shutdown()