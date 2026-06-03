import atexit
import os
import shutil
import subprocess
import sys
import threading
import time

import psutil
from flask import Flask, jsonify, render_template, request

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
            return False, 'snmpsim-command-responder was not found. Run: pip install -r requirements.txt', None
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
    return jsonify({
        'status': 'success',
        'data': devices,
        'summary': build_monitoring_summary(devices),
    })


@app.route('/api/monitoring/rules', methods=['GET'])
def api_monitoring_rules():
    return jsonify({'status': 'success', 'data': get_monitoring_rules()})


@app.route('/api/device/update', methods=['POST'])
def api_update_device():
    data = request.get_json(silent=True) or {}
    filename = data.get('filename')
    cpu = data.get('cpu')
    ram = data.get('ram')
    reset_normal = data.get('reset_normal', False)

    if not filename:
        return jsonify({'status': 'error', 'message': 'Filename is required'}), 400
    if os.path.basename(filename) != filename or not filename.endswith('.snmprec'):
        return jsonify({'status': 'error', 'message': 'Invalid SNMP record filename'}), 400

    try:
        success = update_device(filename, new_cpu=cpu, new_ram=ram, reset_normal=reset_normal)
    except Exception as exc:
        return jsonify({'status': 'error', 'message': f'Update failed: {exc}'}), 500

    if success:
        return jsonify({'status': 'success', 'message': f'Updated {filename}'})

    return jsonify({'status': 'error', 'message': 'Device file not found or cannot be updated'}), 404


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
