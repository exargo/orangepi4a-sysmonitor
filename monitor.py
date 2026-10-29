import json
import os
import time
from collections import deque
from datetime import datetime

import psutil

from INA219 import INA219

USABLE_CAPACITY_MAH = 3100
DISCHARGED = 9.0
FULL_BATT = 12.50
SENS = 150

DISCHARGE_CURVE = [
    (12.47, 100.0),
    (12.2, 90.0),
    (11.9, 80.0),
    (11.6, 70.0),
    (11.3, 60.0),
    (11.0, 50.0),
    (10.8, 40.0),
    (10.6, 30.0),
    (10.3, 20.0),
    (9.9, 10.0),
    (9.5, 5.0),
    (9.0, 0.0),
]

voltage_history = deque(maxlen=15)
current_history = deque(maxlen=60)

ina = INA219(addr=0x41)


def get_battery_percentage(voltage):
    """linear interpolation of battery percentage"""
    if voltage >= DISCHARGE_CURVE[0][0]:
        return 100.0
    if voltage <= DISCHARGE_CURVE[-1][0]:
        return 0.0

    for i in range(len(DISCHARGE_CURVE) - 1):
        v_high, p_high = DISCHARGE_CURVE[i]
        v_low, p_low = DISCHARGE_CURVE[i + 1]

        if v_low <= voltage <= v_high:
            ratio = (voltage - v_low) / (v_high - v_low)
            return p_low + (p_high - p_low) * ratio

    return 0.0


is_discharging = False


def get_stats():
    global is_discharging

    bus_voltage = ina.getBusVoltage_V()
    raw_current = ina.getCurrent_mA()
    power = ina.getPower_W()

    voltage_history.append(bus_voltage)
    current_history.append(raw_current)

    bus_voltage = sum(voltage_history) / len(voltage_history)  # ignore spikes
    current = sum(current_history) / len(current_history)
    percent = get_battery_percentage(bus_voltage)

    # remaining_mah = (percent / 100) * USABLE_CAPACITY_MAH
    if raw_current < -SENS:
        if not is_discharging:
            current_history.clear()
            is_discharging = True

        current_history.append(raw_current)
        avg_current = sum(current_history) / len(current_history)
        remaining_mah = (percent / 100) * USABLE_CAPACITY_MAH
        total_minutes = int((remaining_mah / abs(avg_current)) * 60)
        h, m = divmod(total_minutes, 60)
        time_left_str = f"{h}h {m}m left"
    else:
        is_discharging = False
        time_left_str = "Charging" if raw_current > SENS else "Full/AC"
    memory = psutil.virtual_memory()
    ram_used_gb = memory.used / (1024**3)
    uptime_sec = time.time() - psutil.boot_time()
    d = int(uptime_sec // 86400)
    h = int((uptime_sec % 86400) // 3600)
    m = int((uptime_sec % 3600) // 60)
    uptime_str = f"{d}d {h}h {m}m" if d > 0 else f"{h}h {m}m"

    if bus_voltage <= DISCHARGED:
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        with open("shutdown.log", "w") as file:
            file.write(current_time)
        os.system("sudo shutdown -h now")

    return {
        "voltage": round(bus_voltage, 2),
        "ups_percent": round(percent, 1),
        "current": round(raw_current, 0),
        "watt": round(power, 2),
        "cpu_percent": psutil.cpu_percent(),
        "cpu_temp": int(open("/sys/class/thermal/thermal_zone0/temp").read()) / 1000,
        "ram": memory.percent,
        "ram_used": round(ram_used_gb, 3),
        "time": time.strftime("%H:%M:%S"),
        "uptime": uptime_str,
        "power_state": time_left_str,
    }


while True:
    data = get_stats()
    with open("/dev/shm/new_data.json", "w") as f:
        json.dump(data, f, indent=4)
    os.replace("/dev/shm/new_data.json", "/dev/shm/data.json")
    time.sleep(1)
