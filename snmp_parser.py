import glob
import os
import random
import threading
import time

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, 'data')

_LOCK = threading.RLock()

OIDS = {
    'sysName': '1.3.6.1.2.1.1.5.0',
    'fortinet_cpu': '1.3.6.1.4.1.12356.101.4.1.3.0',
    'fortinet_ram': '1.3.6.1.4.1.12356.101.4.1.4.0',
    'fortinet_disk': '1.3.6.1.4.1.12356.101.4.1.6.0',
    'fortinet_sessions': '1.3.6.1.4.1.12356.101.4.1.8.0',
    'cisco_cpu': '1.3.6.1.4.1.9.9.109.1.1.1.1.5.1',
    'ucd_cpu': '1.3.6.1.4.1.2021.11.9.0',
    'ucd_ram_total': '1.3.6.1.4.1.2021.4.5.0',
    'ucd_ram_avail': '1.3.6.1.4.1.2021.4.6.0',
}

IF_NAME_PREFIX = '1.3.6.1.2.1.2.2.1.1.'
IF_ADMIN_STATUS_PREFIX = '1.3.6.1.2.1.2.3.1.1.'
IF_OPER_STATUS_PREFIX = '1.3.6.1.2.1.2.3.1.2.'
IF_IN_OCTETS_PREFIX = '1.3.6.1.2.1.31.1.1.1.6.'
IF_OUT_OCTETS_PREFIX = '1.3.6.1.2.1.31.1.1.1.10.'
LOAD_AVG_PREFIX = '1.3.6.1.4.1.2021.10.1.3.'

MONITORING_RULES = [
    {
        'metric': 'CPU usage',
        'oid': 'Fortinet/Cisco/UCD CPU OIDs',
        'warning': '>= 70%',
        'critical': '>= 90%',
        'meaning': 'Device is under high processing load.',
    },
    {
        'metric': 'RAM usage',
        'oid': 'Fortinet RAM or UCD RAM total/available',
        'warning': '>= 70%',
        'critical': '>= 90%',
        'meaning': 'Device memory pressure is high.',
    },
    {
        'metric': 'Disk usage',
        'oid': OIDS['fortinet_disk'],
        'warning': '>= 80%',
        'critical': '>= 90%',
        'meaning': 'Firewall disk usage is high.',
    },
    {
        'metric': 'Firewall sessions',
        'oid': OIDS['fortinet_sessions'],
        'warning': '>= 5,000',
        'critical': '>= 10,000',
        'meaning': 'Firewall session table is growing.',
    },
    {
        'metric': 'Load average',
        'oid': f'{LOAD_AVG_PREFIX}1/2/3',
        'warning': '>= 5',
        'critical': '>= 10',
        'meaning': 'Server-like load average is high.',
    },
    {
        'metric': 'Interface status',
        'oid': f'{IF_OPER_STATUS_PREFIX}<index>',
        'warning': 'down',
        'critical': 'n/a',
        'meaning': 'Network interface is not operational.',
    },
    {
        'metric': 'Interface counters',
        'oid': f'{IF_IN_OCTETS_PREFIX}<index>, {IF_OUT_OCTETS_PREFIX}<index>',
        'warning': 'rate is calculated by external monitoring tools',
        'critical': 'rate is calculated by external monitoring tools',
        'meaning': 'Counters are exposed for Cacti/Nagios/Zabbix/PRTG polling.',
    },
]


def _parse_int(value, default=0):
    try:
        return int(float(str(value).strip()))
    except (TypeError, ValueError):
        return default


def _parse_float(value, default=0.0):
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return default


def _clamp_percent(value):
    return max(0, min(100, _parse_int(value)))


def _read_snmprec_lines(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        return file.readlines()


def _write_snmprec_lines(filepath, lines):
    tmp_path = f'{filepath}.tmp'
    last_error = None

    for _ in range(8):
        try:
            with open(tmp_path, 'w', encoding='utf-8', newline='') as file:
                file.writelines(lines)
            os.replace(tmp_path, filepath)
            return
        except PermissionError as exc:
            last_error = exc
            time.sleep(0.15)

    # Windows can reject os.replace() while SNMPSim/PRTG is reading the
    # record. Direct overwrite is less atomic but keeps the lab UI usable.
    try:
        with open(filepath, 'w', encoding='utf-8', newline='') as file:
            file.writelines(lines)
    finally:
        try:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
        except OSError:
            pass

    if last_error and not os.path.exists(filepath):
        raise last_error


def _resolve_device_path(filename):
    if not filename or os.path.basename(filename) != filename:
        return None
    if not filename.endswith('.snmprec'):
        return None

    data_dir = os.path.abspath(DATA_DIR)
    filepath = os.path.abspath(os.path.join(data_dir, filename))
    if os.path.commonpath([data_dir, filepath]) != data_dir:
        return None
    return filepath


def _interface(index, interfaces):
    if index not in interfaces:
        interfaces[index] = {
            'index': index,
            'name': f'if-{index}',
            'admin_status': None,
            'oper_status': None,
            'in_octets': 0,
            'out_octets': 0,
        }
    return interfaces[index]


def _extract_index(oid, prefix):
    if not oid.startswith(prefix):
        return None
    return oid[len(prefix):]


def _add_threshold_alert(alerts, severity, metric, value, threshold, message):
    alerts.append({
        'severity': severity,
        'metric': metric,
        'value': value,
        'threshold': threshold,
        'message': message,
    })


def evaluate_device_alerts(device):
    alerts = []

    cpu = device.get('cpu', 0)
    if cpu >= 90:
        _add_threshold_alert(alerts, 'critical', 'CPU', f'{cpu}%', '>= 90%', 'CPU usage is critical.')
    elif cpu >= 70:
        _add_threshold_alert(alerts, 'warning', 'CPU', f'{cpu}%', '>= 70%', 'CPU usage is high.')

    ram = device.get('ram_percent', 0)
    if ram >= 90:
        _add_threshold_alert(alerts, 'critical', 'RAM', f'{ram}%', '>= 90%', 'RAM usage is critical.')
    elif ram >= 70:
        _add_threshold_alert(alerts, 'warning', 'RAM', f'{ram}%', '>= 70%', 'RAM usage is high.')

    disk = device.get('disk_percent', 0)
    if disk >= 90:
        _add_threshold_alert(alerts, 'critical', 'Disk', f'{disk}%', '>= 90%', 'Disk usage is critical.')
    elif disk >= 80:
        _add_threshold_alert(alerts, 'warning', 'Disk', f'{disk}%', '>= 80%', 'Disk usage is high.')

    sessions = device.get('sessions', 0)
    if sessions >= 10000:
        _add_threshold_alert(
            alerts, 'critical', 'Sessions', sessions, '>= 10000', 'Firewall session count is critical.'
        )
    elif sessions >= 5000:
        _add_threshold_alert(
            alerts, 'warning', 'Sessions', sessions, '>= 5000', 'Firewall session count is high.'
        )

    load_avg_1m = device.get('load_avg_1m', 0)
    if load_avg_1m >= 10:
        _add_threshold_alert(
            alerts, 'critical', 'Load average', load_avg_1m, '>= 10', 'Load average is critical.'
        )
    elif load_avg_1m >= 5:
        _add_threshold_alert(
            alerts, 'warning', 'Load average', load_avg_1m, '>= 5', 'Load average is high.'
        )

    down_interfaces = [
        iface for iface in device.get('interfaces', [])
        if iface.get('oper_status') not in (None, 1)
    ]
    if down_interfaces:
        names = ', '.join(iface.get('name') or f"if-{iface.get('index')}" for iface in down_interfaces)
        _add_threshold_alert(
            alerts,
            'warning',
            'Interface status',
            names,
            'oper_status != 1',
            'One or more interfaces are down.',
        )

    return alerts


def _apply_status(device):
    alerts = evaluate_device_alerts(device)
    device['alerts'] = alerts
    device['alert_count'] = len(alerts)

    if any(alert['severity'] == 'critical' for alert in alerts):
        device['status'] = 'critical'
    elif alerts:
        device['status'] = 'warning'
    else:
        device['status'] = 'good'

    device['forced_high'] = device['cpu'] > 60 or device['ram_percent'] > 60
    return device


def parse_device_file(filepath):
    filename = os.path.basename(filepath)
    device_id = filename.replace('.snmprec', '')
    interfaces = {}
    load_avg = {}

    data = {
        'id': device_id,
        'filename': filename,
        'name': device_id.capitalize(),
        'cpu': 0,
        'ram_total': 0,
        'ram_avail': 0,
        'ram_percent': 0,
        'disk_percent': 0,
        'sessions': 0,
        'load_avg': [],
        'load_avg_1m': 0,
        'interface_count': 0,
        'interfaces_up': 0,
        'interfaces_down': 0,
        'in_octets_total': 0,
        'out_octets_total': 0,
        'interfaces': [],
        'forced_high': False,
        'status': 'good',
        'alerts': [],
        'alert_count': 0,
    }

    cpu_candidates = {}
    ram_percent_candidate = None

    for line in _read_snmprec_lines(filepath):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue

        parts = stripped.split('|')
        if len(parts) < 3:
            continue

        oid = parts[0]
        value = parts[2]

        if oid == OIDS['sysName']:
            data['name'] = value
        elif oid == OIDS['fortinet_cpu']:
            cpu_candidates['vendor'] = _parse_int(value)
        elif oid == OIDS['cisco_cpu']:
            cpu_candidates['vendor'] = _parse_int(value)
        elif oid == OIDS['ucd_cpu']:
            cpu_candidates['ucd'] = _parse_int(value)
        elif oid == OIDS['fortinet_ram']:
            ram_percent_candidate = _parse_int(value)
        elif oid == OIDS['fortinet_disk']:
            data['disk_percent'] = _parse_int(value)
        elif oid == OIDS['fortinet_sessions']:
            data['sessions'] = _parse_int(value)
        elif oid == OIDS['ucd_ram_total']:
            data['ram_total'] = _parse_int(value)
        elif oid == OIDS['ucd_ram_avail']:
            data['ram_avail'] = _parse_int(value)

        index = _extract_index(oid, IF_NAME_PREFIX)
        if index is not None and not value.isdigit():
            _interface(index, interfaces)['name'] = value

        index = _extract_index(oid, IF_ADMIN_STATUS_PREFIX)
        if index is not None:
            _interface(index, interfaces)['admin_status'] = _parse_int(value)

        index = _extract_index(oid, IF_OPER_STATUS_PREFIX)
        if index is not None:
            _interface(index, interfaces)['oper_status'] = _parse_int(value)

        index = _extract_index(oid, IF_IN_OCTETS_PREFIX)
        if index is not None:
            _interface(index, interfaces)['in_octets'] = _parse_int(value)

        index = _extract_index(oid, IF_OUT_OCTETS_PREFIX)
        if index is not None:
            _interface(index, interfaces)['out_octets'] = _parse_int(value)

        index = _extract_index(oid, LOAD_AVG_PREFIX)
        if index is not None:
            load_avg[index] = _parse_float(value)

    data['cpu'] = cpu_candidates.get('vendor', cpu_candidates.get('ucd', 0))

    if ram_percent_candidate is not None:
        data['ram_percent'] = ram_percent_candidate
    elif data['ram_total'] > 0:
        used = max(0, data['ram_total'] - data['ram_avail'])
        data['ram_percent'] = int((used / data['ram_total']) * 100)

    data['interfaces'] = sorted(
        interfaces.values(),
        key=lambda iface: _parse_int(iface.get('index')),
    )
    data['interface_count'] = len(data['interfaces'])
    data['interfaces_up'] = sum(1 for iface in data['interfaces'] if iface.get('oper_status') == 1)
    data['interfaces_down'] = sum(
        1 for iface in data['interfaces'] if iface.get('oper_status') not in (None, 1)
    )
    data['in_octets_total'] = sum(iface.get('in_octets', 0) for iface in data['interfaces'])
    data['out_octets_total'] = sum(iface.get('out_octets', 0) for iface in data['interfaces'])
    data['load_avg'] = [load_avg[key] for key in sorted(load_avg, key=_parse_int)]
    data['load_avg_1m'] = data['load_avg'][0] if data['load_avg'] else 0

    return _apply_status(data)


def get_all_devices():
    if not os.path.exists(DATA_DIR):
        return []

    with _LOCK:
        devices = []
        for filepath in sorted(glob.glob(os.path.join(DATA_DIR, '*.snmprec'))):
            try:
                devices.append(parse_device_file(filepath))
            except OSError:
                continue
        return devices


def get_monitoring_rules():
    return MONITORING_RULES


def build_monitoring_summary(devices):
    active_alerts = [alert for device in devices for alert in device.get('alerts', [])]
    return {
        'device_count': len(devices),
        'good_count': sum(1 for device in devices if device.get('status') == 'good'),
        'warning_count': sum(1 for device in devices if device.get('status') == 'warning'),
        'critical_count': sum(1 for device in devices if device.get('status') == 'critical'),
        'active_alert_count': len(active_alerts),
    }


def update_device(filename, new_cpu=None, new_ram=None, reset_normal=False):
    filepath = _resolve_device_path(filename)
    if not filepath or not os.path.exists(filepath):
        return False

    if reset_normal:
        new_cpu = random.randint(10, 30)
        new_ram = random.randint(20, 40)
    else:
        if new_cpu is not None:
            new_cpu = _clamp_percent(new_cpu)
        if new_ram is not None:
            new_ram = _clamp_percent(new_ram)

    with _LOCK:
        lines = _read_snmprec_lines(filepath)

        ram_total = 0
        for line in lines:
            if line.startswith(OIDS['ucd_ram_total']):
                parts = line.strip().split('|')
                if len(parts) >= 3:
                    ram_total = _parse_int(parts[2])

        for index, line in enumerate(lines):
            stripped = line.strip()
            if not stripped or stripped.startswith('#'):
                continue

            parts = stripped.split('|')
            if len(parts) < 3:
                continue

            oid = parts[0]

            if new_cpu is not None and oid in (OIDS['fortinet_cpu'], OIDS['cisco_cpu'], OIDS['ucd_cpu']):
                parts[2] = str(new_cpu)
                lines[index] = '|'.join(parts) + '\n'

            if new_ram is not None:
                if oid == OIDS['fortinet_ram']:
                    parts[2] = str(new_ram)
                    lines[index] = '|'.join(parts) + '\n'
                elif oid == OIDS['ucd_ram_avail'] and ram_total > 0:
                    avail = int(ram_total - (ram_total * new_ram / 100))
                    parts[2] = str(max(0, avail))
                    lines[index] = '|'.join(parts) + '\n'

        _write_snmprec_lines(filepath, lines)

    return True


def get_fluctuated_value(current_val):
    current_val = _clamp_percent(current_val)
    if current_val > 60:
        new_val = current_val + random.randint(-2, 2)
        return max(60, min(100, new_val))

    drift = random.randint(-5, 5)
    new_val = current_val + drift
    return max(10, min(50, new_val))


def simulate_traffic():
    if not os.path.exists(DATA_DIR):
        return

    with _LOCK:
        for filepath in sorted(glob.glob(os.path.join(DATA_DIR, '*.snmprec'))):
            try:
                lines = _read_snmprec_lines(filepath)
            except OSError:
                continue

            ram_total = 0
            for line in lines:
                if line.startswith(OIDS['ucd_ram_total']):
                    parts = line.strip().split('|')
                    if len(parts) >= 3:
                        ram_total = _parse_int(parts[2])

            is_cpu_high = False

            for index, line in enumerate(lines):
                stripped = line.strip()
                if not stripped or stripped.startswith('#'):
                    continue

                parts = stripped.split('|')
                if len(parts) < 3:
                    continue

                oid = parts[0]
                value = parts[2]

                if oid in (OIDS['fortinet_cpu'], OIDS['cisco_cpu'], OIDS['ucd_cpu']):
                    new_cpu = get_fluctuated_value(value)
                    is_cpu_high = is_cpu_high or new_cpu > 60
                    parts[2] = str(new_cpu)
                    lines[index] = '|'.join(parts) + '\n'

                elif oid == OIDS['fortinet_ram']:
                    parts[2] = str(get_fluctuated_value(value))
                    lines[index] = '|'.join(parts) + '\n'

                elif oid == OIDS['fortinet_disk']:
                    parts[2] = str(get_fluctuated_value(value))
                    lines[index] = '|'.join(parts) + '\n'

                elif oid == OIDS['fortinet_sessions']:
                    current_sessions = _parse_int(value)
                    drift = random.randint(100, 500) if is_cpu_high else random.randint(-50, 50)
                    parts[2] = str(max(0, current_sessions + drift))
                    lines[index] = '|'.join(parts) + '\n'

                elif oid == OIDS['ucd_ram_avail'] and ram_total > 0:
                    avail = _parse_int(value)
                    used = max(0, ram_total - avail)
                    percent = int((used / ram_total) * 100)
                    new_percent = get_fluctuated_value(percent)
                    new_avail = int(ram_total - (ram_total * new_percent / 100))
                    parts[2] = str(max(0, new_avail))
                    lines[index] = '|'.join(parts) + '\n'

                elif oid.startswith(IF_IN_OCTETS_PREFIX) or oid.startswith(IF_OUT_OCTETS_PREFIX):
                    increment = random.randint(10000, 5000000)
                    parts[2] = str(_parse_int(value) + increment)
                    lines[index] = '|'.join(parts) + '\n'

                elif oid.startswith(LOAD_AVG_PREFIX):
                    parts[2] = str(random.randint(5, 15) if is_cpu_high else random.randint(1, 4))
                    lines[index] = '|'.join(parts) + '\n'

            try:
                _write_snmprec_lines(filepath, lines)
            except OSError:
                continue
