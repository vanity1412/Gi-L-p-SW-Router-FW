let network = null;
let nodes = new vis.DataSet([]);
let edges = new vis.DataSet([]);
let currentDevices = [];
let currentRules = [];
let currentServices = {};
let currentIncidents = [];
let selectedNodeId = null;
let selectedIncidentId = null;

const ACTION_LABELS = {
    run_health_check: 'Run Health Check',
    restart_service: 'Restart Service',
    clear_cache: 'Clear Cache',
    clean_logs: 'Clean Logs',
    clear_sessions: 'Clear Sessions',
    bounce_interface: 'Bounce Interface',
    restart_agent: 'Restart Agent',
    reset_device: 'Reset Device'
};

const NODE_POSITIONS = {
    fortinet: { x: -230, y: 95 },
    switch: { x: 15, y: 95 },
    router: { x: -150, y: -85 },
    ubuntu: { x: 15, y: -170 }
};

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function formatNumber(value) {
    return Number(value || 0).toLocaleString();
}

function formatBytes(value) {
    const units = ['B', 'KB', 'MB', 'GB', 'TB'];
    let size = Number(value || 0);
    let unitIndex = 0;
    while (size >= 1024 && unitIndex < units.length - 1) {
        size /= 1024;
        unitIndex++;
    }
    return `${size.toFixed(size >= 10 || unitIndex === 0 ? 0 : 1)} ${units[unitIndex]}`;
}

function formatLoad(loadAvg) {
    if (!Array.isArray(loadAvg) || loadAvg.length === 0) return 'N/A';
    return loadAvg.map(value => Number(value).toFixed(1).replace('.0', '')).join(' / ');
}

function formatDate(value) {
    if (!value) return 'N/A';
    const date = new Date(value);
    if (Number.isNaN(date.getTime())) return value;
    return date.toLocaleString();
}

function numberOrNull(value) {
    const parsed = Number(value);
    return Number.isFinite(parsed) ? parsed : null;
}

function statusLabel(status) {
    if (status === 'critical') return 'Critical';
    if (status === 'warning') return 'Warning';
    return 'Good';
}

function severityClass(status) {
    if (status === 'critical') return 'danger';
    if (status === 'warning') return 'warning';
    return 'success';
}

function incidentBadgeClass(incident) {
    if (incident.status === 'resolved') return 'text-bg-success';
    if (incident.severity === 'critical') return 'text-bg-danger';
    if (incident.severity === 'warning') return 'text-bg-warning';
    return 'text-bg-secondary';
}

function serviceBadgeClass(status) {
    if (status === 'running') return 'text-bg-success';
    if (status === 'restarting') return 'text-bg-warning';
    if (status === 'failed' || status === 'stopped') return 'text-bg-danger';
    return 'text-bg-secondary';
}

function getNodeColor(dev) {
    if (dev.status === 'critical') return { background: '#ef4444', border: '#b91c1c' };
    if (dev.status === 'warning') return { background: '#f59e0b', border: '#b45309' };
    return { background: '#10b981', border: '#047857' };
}

function getStatusIndicator(dev) {
    const safeStatus = dev.status || 'good';
    return `<span class="status-indicator status-${safeStatus}"></span>${statusLabel(safeStatus)}`;
}

function progressCell(value) {
    const safeValue = Math.max(0, Math.min(100, Number(value || 0)));
    const color = safeValue >= 90 ? 'bg-danger' : (safeValue >= 70 ? 'bg-warning' : 'bg-success');
    return `
        <div class="metric-progress">
            <span>${safeValue}%</span>
            <div class="progress progress-dark flex-grow-1">
                <div class="progress-bar progress-bar-animated ${color}" style="width: ${safeValue}%"></div>
            </div>
        </div>
    `;
}

function toast(icon, title) {
    Swal.fire({
        toast: true,
        position: 'top-end',
        icon,
        title,
        showConfirmButton: false,
        timer: 1800,
        background: '#1e293b',
        color: '#fff'
    });
}

function initNetwork() {
    const container = document.getElementById('network-container');
    const data = { nodes: nodes, edges: edges };

    const options = {
        nodes: {
            shape: 'hexagon',
            size: 32,
            font: { color: '#ffffff', face: 'Inter' },
            borderWidth: 2,
            shadow: true
        },
        edges: {
            width: 3,
            color: { color: 'rgba(59, 130, 246, 0.6)', highlight: '#3b82f6' },
            smooth: { type: 'continuous' },
            shadow: true,
            dashes: [5, 5]
        },
        physics: false,
        interaction: { hover: true }
    };

    network = new vis.Network(container, data, options);

    edges.add([
        { from: 'fortinet', to: 'switch' },
        { from: 'switch', to: 'router' },
        { from: 'switch', to: 'ubuntu' }
    ]);

    network.on('click', function (params) {
        if (params.nodes.length > 0) {
            selectDevice(params.nodes[0]);
        } else {
            document.getElementById('device-placeholder').style.display = 'block';
            document.getElementById('device-editor').style.display = 'none';
            selectedNodeId = null;
        }
    });
}

function updateSummary(summary, devices) {
    const fallback = {
        device_count: devices.length,
        good_count: devices.filter(device => device.status === 'good').length,
        warning_count: devices.filter(device => device.status === 'warning').length,
        critical_count: devices.filter(device => device.status === 'critical').length,
        active_alert_count: devices.reduce((total, device) => total + (device.alert_count || 0), 0)
    };
    const data = summary || fallback;

    document.getElementById('summary-devices').innerText = data.device_count || 0;
    document.getElementById('summary-good').innerText = data.good_count || 0;
    document.getElementById('summary-warning').innerText = data.warning_count || 0;
    document.getElementById('summary-critical').innerText = data.critical_count || 0;
    document.getElementById('summary-alerts').innerText = `${data.active_alert_count || 0} active alerts`;
}

function updateNodes(devices) {
    devices.forEach(dev => {
        const serviceIssues = (currentServices[dev.id] || []).filter(service => service.status !== 'running').length;
        const title = [
            `CPU: ${dev.cpu}%`,
            `RAM: ${dev.ram_percent}%`,
            `Disk: ${dev.disk_percent || 0}%`,
            `Load: ${formatLoad(dev.load_avg)}`,
            `Alerts: ${dev.alert_count || 0}`,
            `Service issues: ${serviceIssues}`
        ].join(' | ');

        if (!nodes.get(dev.id)) {
            const position = NODE_POSITIONS[dev.id] || {};
            nodes.add({
                id: dev.id,
                label: dev.name,
                title,
                color: getNodeColor(dev),
                x: position.x,
                y: position.y,
                fixed: Boolean(position.x || position.y)
            });
        } else {
            nodes.update({
                id: dev.id,
                label: dev.name,
                title,
                color: getNodeColor(dev)
            });
        }
    });
}

function renderDeviceTable(devices) {
    const tbody = document.getElementById('device-table-body');
    let html = '';

    devices.forEach(dev => {
        const disk = dev.disk_percent > 0 ? progressCell(dev.disk_percent) : '<span class="text-muted small">N/A</span>';
        const sessions = dev.sessions > 0 ? formatNumber(dev.sessions) : '<span class="text-muted small">N/A</span>';
        const interfaces = dev.interface_count > 0
            ? `${dev.interfaces_up}/${dev.interface_count} up`
            : '<span class="text-muted small">N/A</span>';
        const traffic = dev.interface_count > 0
            ? `<div class="small">In ${formatBytes(dev.in_octets_total)}</div><div class="small">Out ${formatBytes(dev.out_octets_total)}</div>`
            : '<span class="text-muted small">N/A</span>';
        const safeId = escapeHtml(dev.id);

        html += `
            <tr>
                <td>${getStatusIndicator(dev)}</td>
                <td>
                    <div class="fw-bold">${escapeHtml(dev.name)}</div>
                    <div class="text-muted small">${escapeHtml(dev.filename)}</div>
                </td>
                <td>${progressCell(dev.cpu)}</td>
                <td>${progressCell(dev.ram_percent)}</td>
                <td>${disk}</td>
                <td>${sessions}</td>
                <td>${escapeHtml(formatLoad(dev.load_avg))}</td>
                <td>${interfaces}</td>
                <td>${traffic}</td>
                <td>
                    <button class="btn btn-sm btn-outline-primary" onclick="network.selectNodes(['${safeId}']); selectDevice('${safeId}')">
                        Inspect
                    </button>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function renderAlerts(devices) {
    const alertList = document.getElementById('alert-list');
    const alerts = [];

    devices.forEach(device => {
        (device.alerts || []).forEach(alert => {
            alerts.push({ device, alert });
        });
    });

    if (alerts.length === 0) {
        alertList.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-check2-circle"></i>
                <div>No active threshold alerts</div>
            </div>
        `;
        return;
    }

    alertList.innerHTML = alerts.map(({ device, alert }) => `
        <div class="alert-item alert-${escapeHtml(alert.severity)}">
            <div class="d-flex justify-content-between gap-2">
                <strong>${escapeHtml(device.name)}</strong>
                <span class="badge text-bg-${alert.severity === 'critical' ? 'danger' : 'warning'}">
                    ${escapeHtml(alert.severity)}
                </span>
            </div>
            <div class="small mt-1">${escapeHtml(alert.metric)}: ${escapeHtml(alert.value)}</div>
            <div class="text-muted small">${escapeHtml(alert.threshold)} - ${escapeHtml(alert.message)}</div>
        </div>
    `).join('');
}

function renderRules(rules) {
    const tbody = document.getElementById('rules-table-body');
    if (!rules || rules.length === 0) {
        tbody.innerHTML = '<tr><td colspan="3" class="text-muted">No monitoring rules loaded.</td></tr>';
        return;
    }

    tbody.innerHTML = rules.map(rule => `
        <tr>
            <td>
                <div class="fw-semibold">${escapeHtml(rule.metric)}</div>
                <code class="small">${escapeHtml(rule.oid)}</code>
            </td>
            <td><span class="badge bg-warning text-dark">${escapeHtml(rule.warning)}</span></td>
            <td><span class="badge bg-danger">${escapeHtml(rule.critical)}</span></td>
        </tr>
    `).join('');
}

function renderSelectedMetrics(dev) {
    const metricGrid = document.getElementById('selected-device-metrics');
    const interfaceText = dev.interface_count > 0
        ? `${dev.interfaces_up}/${dev.interface_count} up`
        : 'N/A';
    const swapText = dev.swap_total > 0 ? `${dev.swap_percent}%` : 'N/A';

    metricGrid.innerHTML = `
        <div class="metric-tile">
            <span>Disk</span>
            <strong>${dev.disk_percent || 0}%</strong>
        </div>
        <div class="metric-tile">
            <span>Swap</span>
            <strong>${escapeHtml(swapText)}</strong>
        </div>
        <div class="metric-tile">
            <span>Sessions</span>
            <strong>${dev.sessions > 0 ? formatNumber(dev.sessions) : 'N/A'}</strong>
        </div>
        <div class="metric-tile">
            <span>Load</span>
            <strong>${escapeHtml(formatLoad(dev.load_avg))}</strong>
        </div>
        <div class="metric-tile">
            <span>Interfaces</span>
            <strong>${escapeHtml(interfaceText)}</strong>
        </div>
        <div class="metric-tile">
            <span>Out Octets</span>
            <strong>${formatBytes(dev.out_octets_total)}</strong>
        </div>
    `;
}

function renderSelectedServices(deviceId) {
    const container = document.getElementById('selected-device-services');
    const services = currentServices[deviceId] || [];
    if (!services.length) {
        container.innerHTML = '<div class="text-muted small">No services configured for this device.</div>';
        return;
    }

    container.innerHTML = services.map(service => `
        <div class="service-mini-row">
            <div>
                <div class="fw-semibold">${escapeHtml(service.label || service.name)}</div>
                <div class="text-muted small">${escapeHtml(service.name)}${service.port ? ` :${escapeHtml(service.port)}` : ''}</div>
                <code class="service-oid">${escapeHtml(service.state_oid || '')}</code>
            </div>
            <div class="d-flex align-items-center gap-2">
                <span class="badge ${serviceBadgeClass(service.status)}">${escapeHtml(service.status)} = ${escapeHtml(service.state_value)}</span>
                <button type="button" class="btn btn-sm btn-outline-danger icon-action" title="Fail service" onclick="updateService('${escapeHtml(deviceId)}', '${escapeHtml(service.name)}', 'failed')">
                    <i class="bi bi-x-octagon"></i>
                </button>
                <button type="button" class="btn btn-sm btn-outline-success icon-action" title="Start service" onclick="updateService('${escapeHtml(deviceId)}', '${escapeHtml(service.name)}', 'running')">
                    <i class="bi bi-play-fill"></i>
                </button>
            </div>
        </div>
    `).join('');
}

function renderServiceList() {
    const container = document.getElementById('service-list');
    const rows = [];
    Object.entries(currentServices || {}).forEach(([deviceId, services]) => {
        const device = currentDevices.find(item => item.id === deviceId);
        (services || []).forEach(service => {
            rows.push({ deviceId, deviceName: device?.name || deviceId, service });
        });
    });

    if (!rows.length) {
        container.innerHTML = '<div class="empty-state"><i class="bi bi-server"></i><div>No services loaded</div></div>';
        return;
    }

    container.innerHTML = rows.map(({ deviceId, deviceName, service }) => `
        <div class="service-row">
                <div>
                    <div class="fw-semibold text-white">${escapeHtml(service.label || service.name)}</div>
                    <div class="text-muted small">${escapeHtml(deviceName)} / ${escapeHtml(service.name)}${service.port ? ` / port ${escapeHtml(service.port)}` : ''}</div>
                    <code class="service-oid">${escapeHtml(service.state_oid || '')}</code>
                </div>
                <div class="d-flex align-items-center gap-2">
                <span class="badge ${serviceBadgeClass(service.status)}">${escapeHtml(service.status)} = ${escapeHtml(service.state_value)}</span>
                <button class="btn btn-sm btn-outline-danger" onclick="updateService('${escapeHtml(deviceId)}', '${escapeHtml(service.name)}', 'failed')">
                    Fail
                </button>
                <button class="btn btn-sm btn-outline-success" onclick="updateService('${escapeHtml(deviceId)}', '${escapeHtml(service.name)}', 'running')">
                    Start
                </button>
            </div>
        </div>
    `).join('');
}

function updateDashboard(devices, summary) {
    currentDevices = devices || [];
    updateSummary(summary, currentDevices);
    updateNodes(currentDevices);
    renderDeviceTable(currentDevices);
    renderAlerts(currentDevices);
    renderServiceList();

    if (selectedNodeId) {
        const selectedDev = currentDevices.find(device => device.id === selectedNodeId);
        if (selectedDev) {
            renderSelectedMetrics(selectedDev);
            renderSelectedServices(selectedDev.id);
        }
    }
}

function selectDevice(id) {
    const dev = currentDevices.find(device => device.id === id);
    if (!dev) return;

    selectedNodeId = id;
    document.getElementById('device-placeholder').style.display = 'none';
    document.getElementById('device-editor').style.display = 'block';

    document.getElementById('edit-name').innerText = dev.name;
    document.getElementById('edit-id').innerText = dev.filename;
    document.getElementById('edit-filename').value = dev.filename;
    document.getElementById('edit-cpu').value = dev.cpu || 0;
    document.getElementById('edit-ram').value = dev.ram_percent || 0;
    document.getElementById('edit-disk').value = dev.disk_percent || 0;
    document.getElementById('edit-load').value = dev.load_avg_1m || 0;
    document.getElementById('edit-sessions').value = dev.sessions || 0;
    document.getElementById('ram-details').innerText = dev.ram_total > 0
        ? `Total: ${(dev.ram_total / 1024).toFixed(0)} MB`
        : 'Total: N/A';

    updateRangeLabel('cpu');
    updateRangeLabel('ram');
    updateRangeLabel('disk');
    renderSelectedMetrics(dev);
    renderSelectedServices(dev.id);
}

function updateRangeLabel(type) {
    const val = Number(document.getElementById(`edit-${type}`).value || 0);
    const label = document.getElementById(`${type}-val-display`);
    label.innerText = `${val}%`;

    if (val >= 90) label.className = 'text-danger fw-bold';
    else if (val >= 70) label.className = 'text-warning fw-bold';
    else label.className = 'text-success fw-bold';
}

function applyStatePayload(payload) {
    if (!payload || payload.status !== 'success') return;
    currentServices = payload.services || {};
    currentRules = payload.rules || currentRules || [];
    currentIncidents = payload.incidents || [];
    updateDashboard(payload.devices || payload.data || [], payload.summary);
    renderRules(currentRules);
    renderIncidents(currentIncidents);
    if (selectedIncidentId) {
        const incident = currentIncidents.find(item => item.id === selectedIncidentId);
        if (incident) renderIncidentDetail(incident);
    }
}

function saveDeviceConfig(resetNormal = false) {
    const filename = document.getElementById('edit-filename').value;
    const cpu = document.getElementById('edit-cpu').value;
    const ram = document.getElementById('edit-ram').value;
    const disk = document.getElementById('edit-disk').value;
    const load = document.getElementById('edit-load').value;
    const sessions = document.getElementById('edit-sessions').value;

    fetch('/api/device/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            filename,
            cpu: numberOrNull(cpu),
            ram: numberOrNull(ram),
            disk: numberOrNull(disk),
            load: numberOrNull(load),
            sessions: numberOrNull(sessions),
            reset_normal: resetNormal
        })
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                toast('success', resetNormal ? 'Device restored to normal state' : 'Metrics applied');
                applyStatePayload(data.state);
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire('Error', 'Unable to update the selected device.', 'error');
        });
}

function runScenario(scenario) {
    if (!selectedNodeId) {
        Swal.fire('Select a device', 'Choose a topology node before running a scenario.', 'info');
        return;
    }

    fetch('/api/scenario/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_id: selectedNodeId, scenario })
    })
        .then(async res => ({ ok: res.ok, data: await res.json() }))
        .then(({ ok, data }) => {
            if (ok && data.status === 'success') {
                toast('success', data.message || 'Scenario applied');
                applyStatePayload(data.state);
            } else {
                Swal.fire('Scenario blocked', data.message || 'Unable to run scenario.', 'warning');
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire('Error', 'Unable to run scenario.', 'error');
        });
}

function updateService(deviceId, serviceName, status) {
    fetch('/api/service/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ device_id: deviceId, service_name: serviceName, status })
    })
        .then(async res => ({ ok: res.ok, data: await res.json() }))
        .then(({ ok, data }) => {
            if (ok && data.status === 'success') {
                toast('success', data.message);
                applyStatePayload(data.state);
            } else {
                Swal.fire('Error', data.message || 'Unable to update service.', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire('Error', 'Unable to update service.', 'error');
        });
}

function fetchLabState() {
    document.getElementById('polling-indicator').style.display = 'block';
    fetch('/api/lab/state')
        .then(res => res.json())
        .then(data => {
            applyStatePayload(data);
            setTimeout(() => {
                document.getElementById('polling-indicator').style.display = 'none';
            }, 300);
        })
        .catch(err => {
            console.error(err);
            document.getElementById('polling-indicator').style.display = 'none';
        });
}

function renderIncidents(incidents) {
    const list = document.getElementById('incident-list');
    const openIncidents = incidents.filter(incident => incident.status !== 'resolved');
    document.getElementById('open-incident-count').innerText = openIncidents.length;
    document.getElementById('incident-total').innerText = `${incidents.length} total`;

    if (!incidents.length) {
        list.innerHTML = `
            <div class="empty-state">
                <i class="bi bi-check2-circle"></i>
                <div>No incidents yet</div>
            </div>
        `;
        return;
    }

    list.innerHTML = incidents.map(incident => {
        const active = incident.id === selectedIncidentId ? 'incident-card-active' : '';
        return `
            <button class="incident-card ${active}" onclick="selectIncident('${escapeHtml(incident.id)}')">
                <div class="d-flex justify-content-between gap-3">
                    <strong>${escapeHtml(incident.title)}</strong>
                    <span class="badge ${incidentBadgeClass(incident)}">${escapeHtml(incident.status)}</span>
                </div>
                <div class="small text-muted mt-1">${escapeHtml(incident.device_name)} / ${escapeHtml(incident.metric)}</div>
                <div class="d-flex justify-content-between mt-2">
                    <span class="badge text-bg-${incident.severity === 'critical' ? 'danger' : 'warning'}">${escapeHtml(incident.severity)}</span>
                    <span class="text-muted small">${formatDate(incident.created_at)}</span>
                </div>
            </button>
        `;
    }).join('');
}

function selectIncident(id) {
    const incident = currentIncidents.find(item => item.id === id);
    if (!incident) return;
    selectedIncidentId = id;
    renderIncidents(currentIncidents);
    renderIncidentDetail(incident);
}

function renderIncidentDetail(incident) {
    document.getElementById('incident-detail-placeholder').style.display = 'none';
    document.getElementById('incident-detail').style.display = 'block';
    document.getElementById('incident-title').innerText = incident.title || incident.id;
    document.getElementById('incident-meta').innerText = `${incident.id} / ${incident.device_name} / opened ${formatDate(incident.created_at)}`;

    const statusBadge = document.getElementById('incident-status-badge');
    statusBadge.className = `badge ${incidentBadgeClass(incident)}`;
    statusBadge.innerText = incident.status || 'open';

    document.getElementById('incident-severity').innerText = incident.severity || 'N/A';
    document.getElementById('incident-metric').innerText = incident.metric || 'N/A';
    document.getElementById('incident-value').innerText = incident.value ?? 'N/A';
    document.getElementById('incident-threshold').innerText = incident.threshold || 'N/A';

    const actions = document.getElementById('incident-actions');
    if (incident.status === 'resolved') {
        actions.innerHTML = '<span class="badge text-bg-success">Resolved</span>';
    } else {
        const actionButtons = (incident.suggested_actions || []).map(action => `
            <button class="btn btn-sm btn-outline-primary" onclick="runRemediation('${escapeHtml(incident.id)}', '${escapeHtml(action)}')">
                <i class="bi bi-play-circle"></i> ${escapeHtml(ACTION_LABELS[action] || action)}
            </button>
        `).join('');
        actions.innerHTML = `
            <button class="btn btn-sm btn-warning text-dark fw-semibold" onclick="ackIncident('${escapeHtml(incident.id)}')">
                <i class="bi bi-check2-square"></i> Acknowledge
            </button>
            ${actionButtons}
        `;
    }

    const log = document.getElementById('action-log');
    const actionLog = incident.action_log || [];
    log.innerHTML = actionLog.length
        ? actionLog.map(item => `<div><span>${formatDate(item.time)}</span> ${escapeHtml(item.message)}</div>`).join('')
        : '<div class="text-muted">No remediation action has run yet.</div>';

    const timeline = document.getElementById('incident-timeline');
    const events = incident.timeline || [];
    timeline.innerHTML = events.length
        ? events.map(item => `
            <div class="timeline-item">
                <div class="timeline-dot"></div>
                <div>
                    <div class="small text-muted">${formatDate(item.time)} / ${escapeHtml(item.type)}</div>
                    <div>${escapeHtml(item.message)}</div>
                </div>
            </div>
        `).join('')
        : '<div class="text-muted">No timeline events yet.</div>';
}

function ackIncident(incidentId) {
    fetch(`/api/incidents/${encodeURIComponent(incidentId)}/ack`, { method: 'POST' })
        .then(async res => ({ ok: res.ok, data: await res.json() }))
        .then(({ ok, data }) => {
            if (ok && data.status === 'success') {
                toast('success', data.message);
                applyStatePayload(data.state);
            } else {
                Swal.fire('Error', data.message || 'Unable to acknowledge incident.', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire('Error', 'Unable to acknowledge incident.', 'error');
        });
}

function runRemediation(incidentId, action) {
    fetch(`/api/incidents/${encodeURIComponent(incidentId)}/remediate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action })
    })
        .then(async res => ({ ok: res.ok, data: await res.json() }))
        .then(({ ok, data }) => {
            if (ok && data.status === 'success') {
                toast('success', data.message);
                applyStatePayload(data.state);
            } else {
                Swal.fire('Action failed', data.message || 'Unable to run remediation.', 'error');
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire('Error', 'Unable to run remediation.', 'error');
        });
}

function checkSimStatus() {
    fetch('/api/snmpsim/status')
        .then(res => res.json())
        .then(data => {
            const statusSpan = document.getElementById('sim-status');
            if (data.running) {
                statusSpan.innerHTML = `<span class="badge bg-success"><i class="bi bi-activity"></i> Running ${escapeHtml(data.endpoint)} (PID: ${data.pid})</span>`;
                document.getElementById('btn-start').disabled = true;
                document.getElementById('btn-stop').disabled = false;
            } else {
                statusSpan.innerHTML = `<span class="badge bg-danger"><i class="bi bi-stop-circle"></i> Stopped ${escapeHtml(data.endpoint || '')}</span>`;
                document.getElementById('btn-start').disabled = false;
                document.getElementById('btn-stop').disabled = true;
            }
        })
        .catch(err => console.error(err));
}

function startSim() {
    fetch('/api/snmpsim/start', { method: 'POST' })
        .then(async res => ({ ok: res.ok, data: await res.json() }))
        .then(({ ok, data }) => {
            if (ok && data.status === 'success') {
                Swal.fire('Started', 'SNMPSim is now running and serving SNMP OIDs.', 'success');
                checkSimStatus();
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire('Error', 'Unable to start SNMPSim.', 'error');
        });
}

function stopSim() {
    fetch('/api/snmpsim/stop', { method: 'POST' })
        .then(async res => ({ ok: res.ok, data: await res.json() }))
        .then(({ ok, data }) => {
            if (ok && data.status === 'success') {
                Swal.fire('Stopped', 'SNMPSim has been stopped.', 'info');
                checkSimStatus();
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire('Error', 'Unable to stop SNMPSim.', 'error');
        });
}

window.onload = function () {
    initNetwork();
    fetchLabState();
    checkSimStatus();

    setInterval(fetchLabState, 1000);
    setInterval(checkSimStatus, 5000);
};
