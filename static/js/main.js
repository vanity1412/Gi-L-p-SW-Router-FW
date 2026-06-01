let network = null;
let nodes = new vis.DataSet([]);
let edges = new vis.DataSet([]);
let currentDevices = [];
let currentRules = [];
let selectedNodeId = null;
let pollingInterval = null;

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
        physics: {
            stabilization: false,
            barnesHut: {
                gravitationalConstant: -2200,
                springConstant: 0.04,
                springLength: 160
            }
        },
        interaction: { hover: true }
    };

    network = new vis.Network(container, data, options);

    edges.add([
        { from: 'fortinet', to: 'switch' },
        { from: 'switch', to: 'router' },
        { from: 'switch', to: 'ubuntu' }
    ]);

    setInterval(() => {
        network.setOptions({ edges: { dashes: [5, 5] } });
    }, 400);

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
        const title = [
            `CPU: ${dev.cpu}%`,
            `RAM: ${dev.ram_percent}%`,
            `Disk: ${dev.disk_percent || 0}%`,
            `Load: ${formatLoad(dev.load_avg)}`,
            `Alerts: ${dev.alert_count || 0}`
        ].join(' | ');

        if (!nodes.get(dev.id)) {
            nodes.add({
                id: dev.id,
                label: dev.name,
                title,
                color: getNodeColor(dev)
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
                        Edit
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
        tbody.innerHTML = '<tr><td colspan="5" class="text-muted">No monitoring rules loaded.</td></tr>';
        return;
    }

    tbody.innerHTML = rules.map(rule => `
        <tr>
            <td class="fw-semibold">${escapeHtml(rule.metric)}</td>
            <td><code>${escapeHtml(rule.oid)}</code></td>
            <td><span class="badge bg-warning text-dark">${escapeHtml(rule.warning)}</span></td>
            <td><span class="badge bg-danger">${escapeHtml(rule.critical)}</span></td>
            <td class="text-muted">${escapeHtml(rule.meaning)}</td>
        </tr>
    `).join('');
}

function updateDashboard(devices, summary) {
    currentDevices = devices;
    updateSummary(summary, devices);
    updateNodes(devices);
    renderDeviceTable(devices);
    renderAlerts(devices);

    if (selectedNodeId) {
        const selectedDev = devices.find(device => device.id === selectedNodeId);
        if (selectedDev) renderSelectedMetrics(selectedDev);
    }
}

function renderSelectedMetrics(dev) {
    const metricGrid = document.getElementById('selected-device-metrics');
    const interfaceText = dev.interface_count > 0
        ? `${dev.interfaces_up}/${dev.interface_count} up`
        : 'N/A';

    metricGrid.innerHTML = `
        <div class="metric-tile">
            <span>Disk</span>
            <strong>${dev.disk_percent || 0}%</strong>
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
        <div class="metric-tile metric-tile-wide">
            <span>In Octets</span>
            <strong>${formatBytes(dev.in_octets_total)}</strong>
        </div>
        <div class="metric-tile metric-tile-wide">
            <span>Out Octets</span>
            <strong>${formatBytes(dev.out_octets_total)}</strong>
        </div>
    `;
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
    document.getElementById('edit-cpu').value = dev.cpu;
    document.getElementById('edit-ram').value = dev.ram_percent;
    document.getElementById('ram-details').innerText = dev.ram_total > 0
        ? `Total: ${(dev.ram_total / 1024).toFixed(0)} MB`
        : 'Total: N/A';

    updateRangeLabel('cpu');
    updateRangeLabel('ram');
    renderSelectedMetrics(dev);
}

function updateRangeLabel(type) {
    const val = document.getElementById(`edit-${type}`).value;
    const label = document.getElementById(`${type}-val-display`);
    label.innerText = `${val}%`;

    if (val >= 90) label.className = 'text-danger fw-bold';
    else if (val >= 70) label.className = 'text-warning fw-bold';
    else label.className = 'text-success fw-bold';
}

function saveDeviceConfig(resetNormal = false) {
    const filename = document.getElementById('edit-filename').value;
    const cpu = document.getElementById('edit-cpu').value;
    const ram = document.getElementById('edit-ram').value;

    fetch('/api/device/update', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, cpu: parseInt(cpu, 10), ram: parseInt(ram, 10), reset_normal: resetNormal })
    })
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                Swal.fire({
                    toast: true,
                    position: 'top-end',
                    icon: 'success',
                    title: resetNormal ? 'Device restored to normal state' : 'High load values applied',
                    showConfirmButton: false,
                    timer: 1500,
                    background: '#1e293b',
                    color: '#fff'
                });
                fetchDevices();
            } else {
                Swal.fire('Error', data.message, 'error');
            }
        })
        .catch(err => {
            console.error(err);
            Swal.fire('Error', 'Unable to update the selected device.', 'error');
        });
}

function fetchDevices() {
    document.getElementById('polling-indicator').style.display = 'block';
    fetch('/api/devices')
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                updateDashboard(data.data, data.summary);
            }
            setTimeout(() => {
                document.getElementById('polling-indicator').style.display = 'none';
            }, 400);
        })
        .catch(err => {
            console.error(err);
            document.getElementById('polling-indicator').style.display = 'none';
        });
}

function fetchRules() {
    fetch('/api/monitoring/rules')
        .then(res => res.json())
        .then(data => {
            if (data.status === 'success') {
                currentRules = data.data;
                renderRules(currentRules);
            }
        })
        .catch(err => console.error(err));
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
    fetchRules();
    fetchDevices();
    checkSimStatus();

    pollingInterval = setInterval(fetchDevices, 1000);
    setInterval(checkSimStatus, 5000);
};
