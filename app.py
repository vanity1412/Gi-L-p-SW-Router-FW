import atexit
import os
import shutil
import subprocess
import sys
import threading
import time

import psutil
from flask import Flask, jsonify, render_template, request

from lab_state import (
    acknowledge_incident,
    append_action_log,
    finish_action,
    get_incident,
    get_services,
    reset_services,
    set_service_status,
    start_action,
    sync_incidents,
)
from snmp_parser import (
    DATA_DIR,
    build_monitoring_summary,
    get_all_devices,
    get_monitoring_rules,
    simulate_traffic,
    update_device,
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
SNMPSIM_ENDPOINT = os.getenv('SNMPSIM_ENDPOINT', '0.0.0.0:161')
SNMPSIM_AUTOSTART = os.getenv('SNMPSIM_AUTOSTART', '1').lower() not in ('0', 'false', 'no')
SIMULATION_ENABLED = os.getenv('SIMULATION_ENABLED', '1').lower() not in ('0', 'false', 'no')
SNMPSIM_LOG_PATH = os.path.join(BASE_DIR, 'snmpsim.log')

app = Flask(__name__)

snmpsim_process = None
snmpsim_lock = threading.RLock()


def env_int(name, default):
    try:
        return int(os.getenv(name, str(default)))
    except ValueError:
        return default


SIMULATION_INTERVAL = max(1, env_int('SIMULATION_INTERVAL', 1))
APP_HOST = os.getenv('FLASK_HOST', '0.0.0.0')
APP_PORT = env_int('FLASK_PORT', 5000)


def snmpsim_status_payload():
    payload = {
        'running': process_is_running(snmpsim_process),
        'endpoint': SNMPSIM_ENDPOINT,
    }
    if payload['running']:
        payload['pid'] = snmpsim_process.pid
    return payload


def build_lab_state():
    devices = get_all_devices()
    services = get_services(devices)
    incidents = sync_incidents(devices, services)
    return {
        'status': 'success',
        'devices': devices,
        'data': devices,
        'summary': build_monitoring_summary(devices),
        'rules': get_monitoring_rules(),
        'services': services,
        'incidents': incidents,
        'snmpsim': snmpsim_status_payload(),
    }


def find_device(device_id):
    for device in get_all_devices():
        if device.get('id') == device_id:
            return device
    return None


def first_interface(device, want_down=False):
    interfaces = [
        iface for iface in device.get('interfaces', [])
        if str(iface.get('name', '')).lower() != 'lo'
    ]
    if want_down:
        for iface in interfaces:
            if iface.get('oper_status') not in (None, 1):
                return iface
    else:
        for iface in interfaces:
            if iface.get('oper_status') == 1:
                return iface
    return interfaces[0] if interfaces else None


def primary_service(device_id, requested=None):
    if requested:
        return requested

    services = get_services()
    candidates = services.get(device_id, [])
    for service in candidates:
        if service.get('critical'):
            return service.get('name')
    if candidates:
        return candidates[0].get('name')
    return 'snmp-agent'


def monitoring_agent_service(device_id):
    services = get_services()
    names = {service.get('name') for service in services.get(device_id, [])}
    if 'snmpd' in names:
        return 'snmpd'
    if 'snmp-agent' in names:
        return 'snmp-agent'
    if 'zabbix-agent' in names:
        return 'zabbix-agent'
    return primary_service(device_id)


def reset_device_to_normal(device):
    update_device(device['filename'], reset_normal=True)
    fresh = find_device(device['id']) or device
    for iface in fresh.get('interfaces', []):
        if iface.get('oper_status') not in (None, 1):
            update_device(fresh['filename'], interface_index=iface.get('index'), interface_status=1)
    reset_services(device['id'])


def apply_scenario(device, scenario, service_name=None):
    filename = device['filename']
    device_id = device['id']

    if scenario == 'cpu_spike':
        update_device(filename, new_cpu=95, new_ram=max(device.get('ram_percent', 0), 65), new_load=12)
        return True, 'CPU spike applied.'

    if scenario == 'memory_leak':
        update_device(filename, new_cpu=max(device.get('cpu', 0), 58), new_ram=94, new_load=8)
        return True, 'Memory leak applied.'

    if scenario == 'disk_full':
        update_device(filename, new_disk=96, new_cpu=max(device.get('cpu', 0), 42), new_load=5)
        return True, 'Disk full condition applied.'

    if scenario == 'session_flood':
        if device_id != 'fortinet':
            return False, 'Session flood is only available for the Fortinet firewall.'
        update_device(filename, new_cpu=92, new_ram=82, new_disk=max(device.get('disk_percent', 0), 60), new_sessions=15000)
        return True, 'Firewall session flood applied.'

    if scenario == 'interface_down':
        iface = first_interface(device)
        if not iface:
            return False, 'No interface is available to bring down.'
        update_device(filename, interface_index=iface.get('index'), interface_status=2)
        return True, f"Interface {iface.get('name') or iface.get('index')} set to down."

    if scenario == 'link_congestion':
        update_device(filename, new_cpu=max(device.get('cpu', 0), 72), new_ram=max(device.get('ram_percent', 0), 62), new_load=6)
        return True, 'Link congestion profile applied.'

    if scenario == 'service_failed':
        service = primary_service(device_id, service_name)
        set_service_status(device_id, service, 'failed')
        return True, f'Service {service} marked as failed.'

    if scenario == 'snmp_agent_down':
        service = monitoring_agent_service(device_id)
        set_service_status(device_id, service, 'failed')
        return True, f'Monitoring agent {service} marked as failed.'

    if scenario == 'server_degraded':
        update_device(filename, new_cpu=82, new_ram=86, new_disk=88, new_load=9)
        if device_id == 'ubuntu':
            set_service_status(device_id, 'zabbix-agent', 'restarting')
        return True, 'Server degraded profile applied.'

    if scenario == 'reset_normal':
        reset_device_to_normal(device)
        return True, 'Device restored to normal.'

    return False, 'Unknown scenario.'


def add_action_steps(incident_id, steps):
    for step in steps:
        append_action_log(incident_id, step)


def apply_remediation(incident, action):
    device = find_device(incident.get('device_id'))
    if not device:
        return False, 'Device is no longer available.'

    device_id = device['id']
    filename = device['filename']
    metric = incident.get('metric')
    service_name = incident.get('service_name')

    start_action(incident['id'], action)

    if action == 'run_health_check':
        services = get_services().get(device_id, [])
        service_summary = ', '.join(f"{svc.get('name')}={svc.get('status')}" for svc in services) or 'no services'
        add_action_steps(incident['id'], [
            f"Polling {device.get('name')} health metrics.",
            f"CPU={device.get('cpu')}%, RAM={device.get('ram_percent')}%, Disk={device.get('disk_percent')}%, Load={device.get('load_avg_1m')}.",
            f"Services: {service_summary}.",
        ])
        finish_action(incident['id'], action, True, 'Health check completed. No state was changed.')
        return True, 'Health check completed.'

    if action == 'restart_service':
        service = primary_service(device_id, service_name)
        add_action_steps(incident['id'], [
            f"Connecting to {device.get('name')} remote service manager.",
            f"Restarting service {service}.",
        ])
        set_service_status(device_id, service, 'running')
        if metric in ('CPU', 'Load average', 'Service state'):
            update_device(filename, new_cpu=38, new_load=2)
        finish_action(incident['id'], action, True, f'Service {service} restarted successfully.')
        return True, f'Service {service} restarted.'

    if action == 'clear_cache':
        add_action_steps(incident['id'], [
            f"Connecting to {device.get('name')}.",
            'Dropping filesystem cache and reclaiming inactive memory.',
        ])
        update_device(filename, new_ram=42, new_load=2)
        finish_action(incident['id'], action, True, 'Memory cache cleared and RAM pressure reduced.')
        return True, 'Memory cache cleared.'

    if action == 'clean_logs':
        add_action_steps(incident['id'], [
            f"Connecting to {device.get('name')}.",
            'Compressing old logs and removing rotated temporary files.',
        ])
        update_device(filename, new_disk=45)
        finish_action(incident['id'], action, True, 'Disk cleanup completed.')
        return True, 'Disk cleanup completed.'

    if action == 'clear_sessions':
        target = device
        if device_id != 'fortinet':
            target = find_device('fortinet') or device
        add_action_steps(incident['id'], [
            f"Connecting to {target.get('name')} firewall control plane.",
            'Clearing stale and idle sessions.',
        ])
        update_device(target['filename'], new_sessions=1800, new_cpu=42, new_ram=48)
        finish_action(incident['id'], action, True, 'Firewall session table cleared.')
        return True, 'Firewall session table cleared.'

    if action == 'bounce_interface':
        iface = first_interface(device, want_down=True) or first_interface(device)
        if not iface:
            finish_action(incident['id'], action, False, 'No interface was available to bounce.')
            return False, 'No interface is available.'
        add_action_steps(incident['id'], [
            f"Shutting interface {iface.get('name') or iface.get('index')} on {device.get('name')}.",
            f"Enabling interface {iface.get('name') or iface.get('index')} and verifying link status.",
        ])
        update_device(filename, interface_index=iface.get('index'), interface_status=1)
        finish_action(incident['id'], action, True, f"Interface {iface.get('name') or iface.get('index')} is back up.")
        return True, 'Interface bounced.'

    if action == 'restart_agent':
        service = service_name or monitoring_agent_service(device_id)
        add_action_steps(incident['id'], [
            f"Restarting monitoring agent {service}.",
            'Waiting for agent heartbeat.',
        ])
        set_service_status(device_id, service, 'running')
        if device_id == 'ubuntu':
            set_service_status(device_id, 'zabbix-agent', 'running')
        finish_action(incident['id'], action, True, f'Monitoring agent {service} is running.')
        return True, 'Monitoring agent restarted.'

    if action == 'reset_device':
        add_action_steps(incident['id'], [
            f"Restoring {device.get('name')} to baseline lab values.",
            'Resetting metrics, interfaces, and services.',
        ])
        reset_device_to_normal(device)
        finish_action(incident['id'], action, True, 'Device restored to normal baseline.')
        return True, 'Device reset to normal.'

    finish_action(incident['id'], action, False, 'Unknown remediation action.')
    return False, 'Unknown remediation action.'


def simulation_loop():
    while True:
        try:
            simulate_traffic()
        except Exception as exc:
            print(f'Simulation error: {exc}')
        time.sleep(SIMULATION_INTERVAL)


def process_is_running(process):
    return process is not None and process.poll() is None


def find_snmpsim_executable():
    python_dir = os.path.dirname(sys.executable)
    if os.path.basename(python_dir).lower() == 'scripts':
        local_candidate = os.path.join(python_dir, 'snmpsim-command-responder.exe')
    else:
        local_candidate = os.path.join(python_dir, 'Scripts', 'snmpsim-command-responder.exe')

    candidates = [
        local_candidate,
        os.path.join(BASE_DIR, 'venv', 'Scripts', 'snmpsim-command-responder.exe'),
        os.path.join(BASE_DIR, '.venv', 'Scripts', 'snmpsim-command-responder.exe'),
        os.path.join(BASE_DIR, 'venv', 'bin', 'snmpsim-command-responder'),
        os.path.join(BASE_DIR, '.venv', 'bin', 'snmpsim-command-responder'),
        shutil.which('snmpsim-command-responder'),
        'snmpsim-command-responder',
    ]

    for candidate in candidates:
        if not candidate:
            continue
        if os.path.isabs(candidate) and os.path.exists(candidate):
            return candidate
        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    return 'snmpsim-command-responder'


def snmpsim_command():
    return [
        find_snmpsim_executable(),
        f'--data-dir={DATA_DIR}',
        f'--agent-udpv4-endpoint={SNMPSIM_ENDPOINT}',
    ]


def read_log_tail(max_bytes=4096):
    if not os.path.exists(SNMPSIM_LOG_PATH):
        return ''

    with open(SNMPSIM_LOG_PATH, 'rb') as file:
        file.seek(0, os.SEEK_END)
        size = file.tell()
        file.seek(max(0, size - max_bytes))
        return file.read().decode('utf-8', errors='ignore').strip()


def start_snmpsim_process():
    global snmpsim_process

    with snmpsim_lock:
        if process_is_running(snmpsim_process):
            return True, 'SNMPSim is already running', snmpsim_process.pid

        os.makedirs(DATA_DIR, exist_ok=True)
        command = snmpsim_command()
        creationflags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0

        try:
            with open(SNMPSIM_LOG_PATH, 'ab') as log_file:
                snmpsim_process = subprocess.Popen(
                    command,
                    cwd=BASE_DIR,
                    stdout=log_file,
                    stderr=log_file,
                    creationflags=creationflags,
                )
        except FileNotFoundError:
            snmpsim_process = None
            return False, (
                'snmpsim-command-responder was not found. '
                'Run: venv\\Scripts\\python.exe -m pip install -r requirements.txt'
            ), None
        except Exception as exc:
            snmpsim_process = None
            return False, str(exc), None

        time.sleep(1)
        if snmpsim_process.poll() is not None:
            exit_code = snmpsim_process.poll()
            snmpsim_process = None
            detail = read_log_tail()
            message = f'SNMPSim exited immediately with code {exit_code}.'
            if detail:
                message = f'{message} Log: {detail}'
            return False, message, None

        return True, 'SNMPSim started', snmpsim_process.pid


def stop_snmpsim_process():
    global snmpsim_process

    with snmpsim_lock:
        if not process_is_running(snmpsim_process):
            snmpsim_process = None
            return False, 'SNMPSim is not running'

        try:
            parent = psutil.Process(snmpsim_process.pid)
            processes = parent.children(recursive=True) + [parent]

            for process in processes:
                process.terminate()

            gone, alive = psutil.wait_procs(processes, timeout=5)
            for process in alive:
                process.kill()
            psutil.wait_procs(alive, timeout=3)

            snmpsim_process = None
            return True, 'SNMPSim stopped'
        except psutil.NoSuchProcess:
            snmpsim_process = None
            return True, 'SNMPSim process was already stopped'
        except Exception as exc:
            return False, str(exc)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/devices', methods=['GET'])
def api_get_devices():
    devices = get_all_devices()
    services = get_services(devices)
    sync_incidents(devices, services)
    return jsonify({
        'status': 'success',
        'data': devices,
        'summary': build_monitoring_summary(devices),
    })


@app.route('/api/lab/state', methods=['GET'])
def api_lab_state():
    return jsonify(build_lab_state())


@app.route('/api/monitoring/rules', methods=['GET'])
def api_monitoring_rules():
    return jsonify({'status': 'success', 'data': get_monitoring_rules()})


@app.route('/api/device/update', methods=['POST'])
def api_update_device():
    data = request.get_json(silent=True) or {}
    filename = data.get('filename')
    cpu = data.get('cpu')
    ram = data.get('ram')
    disk = data.get('disk')
    sessions = data.get('sessions')
    load = data.get('load')
    interface_index = data.get('interface_index')
    interface_status = data.get('interface_status')
    reset_normal = data.get('reset_normal', False)

    if not filename:
        return jsonify({'status': 'error', 'message': 'Filename is required'}), 400
    if os.path.basename(filename) != filename or not filename.endswith('.snmprec'):
        return jsonify({'status': 'error', 'message': 'Invalid SNMP record filename'}), 400

    try:
        success = update_device(
            filename,
            new_cpu=cpu,
            new_ram=ram,
            new_disk=disk,
            new_sessions=sessions,
            new_load=load,
            interface_index=interface_index,
            interface_status=interface_status,
            reset_normal=reset_normal,
        )
    except Exception as exc:
        return jsonify({'status': 'error', 'message': f'Update failed: {exc}'}), 500

    if reset_normal:
        device_id = filename.replace('.snmprec', '')
        reset_services(device_id)

    if success:
        return jsonify({'status': 'success', 'message': f'Updated {filename}', 'state': build_lab_state()})

    return jsonify({'status': 'error', 'message': 'Device file not found or cannot be updated'}), 404


@app.route('/api/scenario/run', methods=['POST'])
def api_run_scenario():
    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id')
    scenario = data.get('scenario')
    service_name = data.get('service_name')

    if not device_id:
        return jsonify({'status': 'error', 'message': 'Device is required'}), 400
    if not scenario:
        return jsonify({'status': 'error', 'message': 'Scenario is required'}), 400

    device = find_device(device_id)
    if not device:
        return jsonify({'status': 'error', 'message': 'Device not found'}), 404

    try:
        success, message = apply_scenario(device, scenario, service_name)
    except Exception as exc:
        return jsonify({'status': 'error', 'message': f'Scenario failed: {exc}'}), 500

    status_code = 200 if success else 400
    return jsonify({
        'status': 'success' if success else 'error',
        'message': message,
        'state': build_lab_state(),
    }), status_code


@app.route('/api/service/update', methods=['POST'])
def api_update_service():
    data = request.get_json(silent=True) or {}
    device_id = data.get('device_id')
    service_name = data.get('service_name')
    status = data.get('status')

    if not device_id or not service_name or not status:
        return jsonify({'status': 'error', 'message': 'device_id, service_name, and status are required'}), 400

    try:
        set_service_status(device_id, service_name, status)
    except ValueError as exc:
        return jsonify({'status': 'error', 'message': str(exc)}), 400
    except Exception as exc:
        return jsonify({'status': 'error', 'message': f'Service update failed: {exc}'}), 500

    return jsonify({'status': 'success', 'message': f'{service_name} set to {status}', 'state': build_lab_state()})


@app.route('/api/incidents/<incident_id>/ack', methods=['POST'])
def api_ack_incident(incident_id):
    incident = acknowledge_incident(incident_id)
    if not incident:
        return jsonify({'status': 'error', 'message': 'Incident not found'}), 404
    return jsonify({'status': 'success', 'message': f'{incident_id} acknowledged', 'state': build_lab_state()})


@app.route('/api/incidents/<incident_id>/remediate', methods=['POST'])
def api_remediate_incident(incident_id):
    data = request.get_json(silent=True) or {}
    action = data.get('action')
    if not action:
        return jsonify({'status': 'error', 'message': 'Action is required'}), 400

    incident = get_incident(incident_id)
    if not incident:
        return jsonify({'status': 'error', 'message': 'Incident not found'}), 404

    try:
        success, message = apply_remediation(incident, action)
    except Exception as exc:
        return jsonify({'status': 'error', 'message': f'Remediation failed: {exc}'}), 500

    status_code = 200 if success else 400
    return jsonify({
        'status': 'success' if success else 'error',
        'message': message,
        'state': build_lab_state(),
    }), status_code


@app.route('/api/snmpsim/start', methods=['POST'])
def api_start_snmpsim():
    success, message, pid = start_snmpsim_process()
    status_code = 200 if success else 500
    return jsonify({'status': 'success' if success else 'error', 'message': message, 'pid': pid}), status_code


@app.route('/api/snmpsim/stop', methods=['POST'])
def api_stop_snmpsim():
    success, message = stop_snmpsim_process()
    status_code = 200 if success else 400
    return jsonify({'status': 'success' if success else 'error', 'message': message}), status_code


@app.route('/api/snmpsim/status', methods=['GET'])
def api_snmpsim_status():
    if process_is_running(snmpsim_process):
        return jsonify({
            'status': 'success',
            'running': True,
            'pid': snmpsim_process.pid,
            'endpoint': SNMPSIM_ENDPOINT,
        })

    return jsonify({
        'status': 'success',
        'running': False,
        'endpoint': SNMPSIM_ENDPOINT,
    })


@atexit.register
def cleanup_snmpsim_process():
    if process_is_running(snmpsim_process):
        stop_snmpsim_process()


if __name__ == '__main__':
    os.makedirs(DATA_DIR, exist_ok=True)

    if SIMULATION_ENABLED:
        sim_thread = threading.Thread(target=simulation_loop, daemon=True)
        sim_thread.start()
        print(f'Metric simulation enabled, interval={SIMULATION_INTERVAL}s.')

    if SNMPSIM_AUTOSTART:
        print('Auto-starting SNMPSim...')
        success, message, pid = start_snmpsim_process()
        if success:
            print(f'{message}. PID={pid}, endpoint={SNMPSIM_ENDPOINT}')
        else:
            print(f'Unable to auto-start SNMPSim: {message}')
    else:
        print('SNMPSim auto-start disabled by SNMPSIM_AUTOSTART=0.')

    app.run(host=APP_HOST, port=APP_PORT, debug=False)
