import json
import os
import threading
from datetime import datetime

from snmp_parser import (
    DATA_DIR,
    LAB_SERVICE_COUNT_OID,
    LAB_SERVICE_CRITICAL_PREFIX,
    LAB_SERVICE_LABEL_PREFIX,
    LAB_SERVICE_NAME_PREFIX,
    LAB_SERVICE_PORT_PREFIX,
    LAB_SERVICE_STATE_PREFIX,
    upsert_snmprec_values,
)

_LOCK = threading.RLock()

SERVICES_PATH = os.path.join(DATA_DIR, 'services.json')
INCIDENTS_PATH = os.path.join(DATA_DIR, 'incidents.json')

SERVICE_STATUS_VALUES = {
    'unknown': 0,
    'running': 1,
    'stopped': 2,
    'failed': 3,
    'restarting': 4,
}

SERVICE_STATUS_TEXT = '0=unknown, 1=running, 2=stopped, 3=failed, 4=restarting'

DEFAULT_SERVICES = {
    'ubuntu': [
        {'name': 'nginx', 'label': 'Nginx Web', 'status': 'running', 'port': 80, 'critical': True},
        {'name': 'postgresql', 'label': 'PostgreSQL DB', 'status': 'running', 'port': 5432, 'critical': True},
        {'name': 'ssh', 'label': 'SSH Remote Access', 'status': 'running', 'port': 22, 'critical': True},
        {'name': 'snmpd', 'label': 'SNMP Agent', 'status': 'running', 'port': 161, 'critical': True},
        {'name': 'zabbix-agent', 'label': 'Zabbix Agent', 'status': 'running', 'port': 10050, 'critical': True},
        {'name': 'docker', 'label': 'Docker Engine', 'status': 'running', 'port': 2375, 'critical': False},
    ],
    'fortinet': [
        {'name': 'snmp-agent', 'label': 'SNMP Agent', 'status': 'running', 'port': 161, 'critical': True},
        {'name': 'ipsec-vpn', 'label': 'IPsec VPN', 'status': 'running', 'port': 500, 'critical': True},
        {'name': 'syslog-forwarder', 'label': 'Syslog Forwarder', 'status': 'running', 'port': 514, 'critical': False},
    ],
    'router': [
        {'name': 'snmp-agent', 'label': 'SNMP Agent', 'status': 'running', 'port': 161, 'critical': True},
        {'name': 'routing-engine', 'label': 'Routing Engine', 'status': 'running', 'port': None, 'critical': True},
        {'name': 'ssh', 'label': 'SSH Remote Access', 'status': 'running', 'port': 22, 'critical': True},
    ],
    'switch': [
        {'name': 'snmp-agent', 'label': 'SNMP Agent', 'status': 'running', 'port': 161, 'critical': True},
        {'name': 'lldp', 'label': 'LLDP Neighbor Discovery', 'status': 'running', 'port': None, 'critical': False},
        {'name': 'ssh', 'label': 'SSH Remote Access', 'status': 'running', 'port': 22, 'critical': True},
    ],
}


def _now():
    return datetime.now().replace(microsecond=0).isoformat()


def _read_json(path, default):
    if not os.path.exists(path):
        return default
    try:
        with open(path, 'r', encoding='utf-8') as file:
            return json.load(file)
    except (OSError, json.JSONDecodeError):
        return default


def _write_json(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    tmp_path = f'{path}.tmp'
    with open(tmp_path, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=2)
    os.replace(tmp_path, path)


def _default_service(device_id):
    return {
        'name': 'snmp-agent',
        'label': 'SNMP Agent',
        'status': 'running',
        'port': 161,
        'critical': True,
    }


def _service_key(service):
    return service.get('name')


def _service_status_value(status):
    return SERVICE_STATUS_VALUES.get(status, SERVICE_STATUS_VALUES['unknown'])


def _service_state_oid(index):
    return f'{LAB_SERVICE_STATE_PREFIX}.{index}.0'


def _service_name_oid(index):
    return f'{LAB_SERVICE_NAME_PREFIX}.{index}.0'


def _service_label_oid(index):
    return f'{LAB_SERVICE_LABEL_PREFIX}.{index}.0'


def _service_port_oid(index):
    return f'{LAB_SERVICE_PORT_PREFIX}.{index}.0'


def _service_critical_oid(index):
    return f'{LAB_SERVICE_CRITICAL_PREFIX}.{index}.0'


def _decorate_service_oids(services):
    for index, service in enumerate(services, start=1):
        service['index'] = index
        service['state_value'] = _service_status_value(service.get('status'))
        service['state_oid'] = _service_state_oid(index)
        service['name_oid'] = _service_name_oid(index)
        service['label_oid'] = _service_label_oid(index)
        service['port_oid'] = _service_port_oid(index)
        service['critical_oid'] = _service_critical_oid(index)
        service['state_value_map'] = SERVICE_STATUS_TEXT
    return services


def _merge_services(existing, devices=None):
    merged = {}

    for device_id, defaults in DEFAULT_SERVICES.items():
        merged[device_id] = [dict(service) for service in defaults]

    for device_id, services in (existing or {}).items():
        current = {service.get('name'): dict(service) for service in merged.get(device_id, [])}
        for service in services:
            name = service.get('name')
            if not name:
                continue
            base = current.get(name, {})
            base.update(service)
            current[name] = base
        merged[device_id] = list(current.values())

    for device in devices or []:
        device_id = device.get('id')
        if device_id and device_id not in merged:
            merged[device_id] = [_default_service(device_id)]

    for device_id, services in merged.items():
        merged[device_id] = _decorate_service_oids(services)

    return merged


def _service_snmp_values(services):
    values = [{'oid': LAB_SERVICE_COUNT_OID, 'type': 2, 'value': len(services)}]

    for service in services:
        index = service.get('index')
        name = service.get('name') or f'service-{index}'
        port = service.get('port') or 0
        values.extend([
            {'oid': service['state_oid'], 'type': 2, 'value': _service_status_value(service.get('status'))},
            {'oid': service['name_oid'], 'type': 4, 'value': name},
            {'oid': service['label_oid'], 'type': 4, 'value': service.get('label') or name},
            {'oid': service['port_oid'], 'type': 2, 'value': port},
            {'oid': service['critical_oid'], 'type': 2, 'value': 1 if service.get('critical') else 0},
        ])

    return values


def sync_services_to_snmprec(services_by_device):
    for device_id, services in (services_by_device or {}).items():
        filename = f'{device_id}.snmprec'
        upsert_snmprec_values(
            filename,
            _service_snmp_values(services),
            marker_comment='Lab service-state OIDs for Zabbix. State: 0 unknown, 1 running, 2 stopped, 3 failed, 4 restarting',
        )


def get_services(devices=None):
    with _LOCK:
        services = _merge_services(_read_json(SERVICES_PATH, {}), devices)
        _write_json(SERVICES_PATH, services)
        return services


def set_service_status(device_id, service_name, status):
    if status not in ('running', 'stopped', 'failed', 'restarting', 'unknown'):
        raise ValueError('Invalid service status')

    with _LOCK:
        services = get_services()
        if device_id not in services:
            services[device_id] = [_default_service(device_id)]

        for service in services[device_id]:
            if service.get('name') == service_name:
                service['status'] = status
                service['updated_at'] = _now()
                services[device_id] = _decorate_service_oids(services[device_id])
                _write_json(SERVICES_PATH, services)
                sync_services_to_snmprec({device_id: services[device_id]})
                return True

        services[device_id].append({
            'name': service_name,
            'label': service_name,
            'status': status,
            'port': None,
            'critical': True,
            'updated_at': _now(),
        })
        services[device_id] = _decorate_service_oids(services[device_id])
        _write_json(SERVICES_PATH, services)
        sync_services_to_snmprec({device_id: services[device_id]})
        return True


def reset_services(device_id=None):
    with _LOCK:
        services = get_services()
        device_ids = [device_id] if device_id else list(services.keys())
        for current_device_id in device_ids:
            for service in services.get(current_device_id, []):
                service['status'] = 'running'
                service['updated_at'] = _now()
            services[current_device_id] = _decorate_service_oids(services.get(current_device_id, []))
        _write_json(SERVICES_PATH, services)
        sync_services_to_snmprec({current_device_id: services.get(current_device_id, []) for current_device_id in device_ids})
        return services


def load_incidents():
    with _LOCK:
        return _read_json(INCIDENTS_PATH, [])


def save_incidents(incidents):
    with _LOCK:
        _write_json(INCIDENTS_PATH, incidents)


def _next_incident_id(incidents):
    today = datetime.now().strftime('%Y%m%d')
    count = sum(1 for incident in incidents if str(incident.get('id', '')).startswith(f'INC-{today}'))
    return f'INC-{today}-{count + 1:03d}'


def _timeline(message, event_type='system'):
    return {'time': _now(), 'type': event_type, 'message': message}


def _action_label(action):
    labels = {
        'run_health_check': 'Run Health Check',
        'restart_service': 'Restart Service',
        'clear_cache': 'Clear Memory Cache',
        'clean_logs': 'Clean Disk Logs',
        'clear_sessions': 'Clear Firewall Sessions',
        'bounce_interface': 'Bounce Interface',
        'restart_agent': 'Restart Monitoring Agent',
        'reset_device': 'Reset Device to Normal',
    }
    return labels.get(action, action.replace('_', ' ').title())


def suggested_actions_for(metric, source='metric'):
    if source == 'service':
        return ['restart_service', 'run_health_check', 'restart_agent']
    if metric == 'CPU':
        return ['run_health_check', 'restart_service', 'reset_device']
    if metric == 'RAM':
        return ['clear_cache', 'restart_service', 'reset_device']
    if metric == 'Disk':
        return ['clean_logs', 'reset_device']
    if metric == 'Sessions':
        return ['clear_sessions', 'run_health_check']
    if metric == 'Interface status':
        return ['bounce_interface', 'run_health_check']
    if metric == 'Load average':
        return ['run_health_check', 'restart_service', 'reset_device']
    return ['run_health_check', 'reset_device']


def _alert_to_event(device, alert):
    metric = alert.get('metric', 'Metric')
    return {
        'key': f"metric:{device.get('id')}:{metric}",
        'device_id': device.get('id'),
        'device_name': device.get('name') or device.get('id'),
        'source': 'metric',
        'metric': metric,
        'severity': alert.get('severity', 'warning'),
        'title': f"{metric} alert on {device.get('name') or device.get('id')}",
        'value': alert.get('value'),
        'threshold': alert.get('threshold'),
        'message': alert.get('message'),
        'suggested_actions': suggested_actions_for(metric),
    }


def _service_to_event(device_by_id, device_id, service):
    status = service.get('status', 'unknown')
    severity = 'warning' if status == 'restarting' else 'critical'
    label = service.get('label') or service.get('name')
    device = device_by_id.get(device_id, {})
    return {
        'key': f"service:{device_id}:{service.get('name')}",
        'device_id': device_id,
        'device_name': device.get('name') or device_id,
        'source': 'service',
        'service_name': service.get('name'),
        'metric': 'Service state',
        'severity': severity,
        'title': f"{label} is {status}",
        'value': status,
        'threshold': 'running',
        'message': f"{label} service is not running.",
        'suggested_actions': suggested_actions_for('Service state', 'service'),
    }


def build_active_events(devices, services):
    device_by_id = {device.get('id'): device for device in devices}
    events = []

    for device in devices:
        for alert in device.get('alerts', []):
            events.append(_alert_to_event(device, alert))

    for device_id, device_services in (services or {}).items():
        for service in device_services:
            if service.get('status') != 'running':
                events.append(_service_to_event(device_by_id, device_id, service))

    return events


def sync_incidents(devices, services):
    with _LOCK:
        incidents = load_incidents()
        active_events = {event['key']: event for event in build_active_events(devices, services)}
        open_by_key = {
            incident.get('key'): incident
            for incident in incidents
            if incident.get('status') != 'resolved'
        }

        for key, event in active_events.items():
            incident = open_by_key.get(key)
            if not incident:
                incident = {
                    'id': _next_incident_id(incidents),
                    'key': key,
                    'status': 'open',
                    'created_at': _now(),
                    'updated_at': _now(),
                    'resolved_at': None,
                    'timeline': [_timeline(f"Incident opened: {event.get('message')}", 'alert')],
                    'action_log': [],
                }
                incidents.append(incident)
            else:
                incident['updated_at'] = _now()

            previous_severity = incident.get('severity')
            incident.update(event)
            if previous_severity and previous_severity != event.get('severity'):
                incident.setdefault('timeline', []).append(
                    _timeline(f"Severity changed from {previous_severity} to {event.get('severity')}.", 'alert')
                )

        for incident in incidents:
            if incident.get('status') == 'resolved':
                continue
            if incident.get('key') not in active_events:
                incident['status'] = 'resolved'
                incident['resolved_at'] = _now()
                incident['updated_at'] = _now()
                incident.setdefault('timeline', []).append(
                    _timeline('Incident resolved after metrics returned to normal.', 'recovery')
                )

        save_incidents(incidents)
        return sorted(incidents, key=lambda item: item.get('created_at', ''), reverse=True)


def get_incident(incident_id):
    for incident in load_incidents():
        if incident.get('id') == incident_id:
            return incident
    return None


def update_incident(incident_id, updater):
    with _LOCK:
        incidents = load_incidents()
        for incident in incidents:
            if incident.get('id') == incident_id:
                updater(incident)
                incident['updated_at'] = _now()
                save_incidents(incidents)
                return incident
    return None


def acknowledge_incident(incident_id):
    def updater(incident):
        if incident.get('status') != 'resolved':
            incident['status'] = 'acknowledged'
            incident.setdefault('timeline', []).append(_timeline('Incident acknowledged by operator.', 'ack'))

    return update_incident(incident_id, updater)


def append_action_log(incident_id, message):
    def updater(incident):
        incident.setdefault('action_log', []).append({'time': _now(), 'message': message})

    return update_incident(incident_id, updater)


def start_action(incident_id, action):
    label = _action_label(action)

    def updater(incident):
        if incident.get('status') != 'resolved':
            incident['status'] = 'remediating'
        incident.setdefault('timeline', []).append(_timeline(f"Started remediation: {label}.", 'action'))
        incident.setdefault('action_log', []).append({'time': _now(), 'message': f"Starting {label}."})

    return update_incident(incident_id, updater)


def finish_action(incident_id, action, success=True, detail=None):
    label = _action_label(action)

    def updater(incident):
        if incident.get('status') != 'resolved':
            incident['status'] = 'acknowledged' if success else 'open'
        message = detail or (f"{label} completed." if success else f"{label} failed.")
        incident.setdefault('timeline', []).append(_timeline(message, 'action' if success else 'error'))
        incident.setdefault('action_log', []).append({'time': _now(), 'message': message})

    return update_incident(incident_id, updater)
