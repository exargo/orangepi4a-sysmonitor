# System Monitor & UPS Controller

A Python-based system monitor and Waveshare S3 UPS (Uninterruptible Power Supply) management script designed for single-board computers (like Raspberry Pi) equipped with an INA219 current/voltage sensor.

## Features

- **Real-time Monitoring**: Tracks bus voltage, current, and power consumption via the INA219 sensor.
- **System Stats**: Monitors CPU usage, CPU temperature, RAM usage, and system uptime.
- **Battery Management**:
    - Calculates battery percentage using a non-linear discharge curve.
    - Estimates remaining time when discharging.
    - Detects "Charging", "Full/AC", and "Discharging" states.
- **Auto-Shutdown**: Automatically triggers a system shutdown when the battery voltage drops below a safe threshold (9.0V) to prevent deep discharge.
- **Data Export**: Writes all stats to `/dev/shm/data.json` every second for use by other applications (e.g., a web dashboard or status display).

## Hardware Requirements

- Raspberry Pi or similar SBC.
- **INA219** High-Side DC Current Sensor (Default I2C address: `0x41`).
- Battery pack (configured for ~9.0V to 12.5V range).

## Installation

This project uses `uv` for dependency management.

1.  **Clone the repository**:

    ```bash
    git clone <repository-url>
    cd sysmonitor
    ```

2.  **Install dependencies**:
    ```bash
    uv sync
    ```

## Usage

Run the monitor script:

```bash
uv run monitor.py
```

### Data Output

The script continuously updates `/dev/shm/data.json` with the following structure:

```json
{
    "voltage": 12.45,
    "ups_percent": 98.5,
    "current": -250.0,
    "watt": 3.11,
    "cpu_percent": 15.2,
    "cpu_temp": 45.5,
    "ram": 22.1,
    "ram_used": 0.854,
    "time": "14:30:05",
    "uptime": "2d 4h 15m",
    "power_state": "5h 12m left"
}
```

## Configuration

You can adjust the constants in `monitor.py`:

- `USABLE_CAPACITY_MAH`: Your battery capacity (default: 3100mAh).
- `DISCHARGED`: Shutdown voltage threshold (default: 9.0V).
- `FULL_BATT`: Voltage representing 100% charge (default: 12.5V).
- `SENS`: Current sensitivity threshold in mA for state detection (default: 150mA).
- `DISCHARGE_CURVE`: The voltage-to-percentage mapping table.

## Logging

When an automatic shutdown is triggered, the script writes the timestamp to `shutdown.log` before executing the shutdown command.
