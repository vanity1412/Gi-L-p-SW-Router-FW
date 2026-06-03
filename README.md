# Network-Recon-Risk-Profiler

SNMPSim Monitoring Lab for simulating Server, Switch, Router, and Firewall SNMP metrics.

## Features

- Flask web dashboard for SNMP simulation control.
- Real-time topology view.
- Simulated CPU, RAM, disk, sessions, load average, and interface counters.
- Device high-load forcing and reset-to-normal controls.
- SNMPSim start/stop controls.
- Monitoring rules for warning and critical states.

## Run

```powershell
pip install -r requirements.txt
python app.py
```

Open:

```text
http://localhost:5000
```

For Windows SNMP port 161, run as Administrator if SNMPSim cannot bind the port.
