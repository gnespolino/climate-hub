document.addEventListener('DOMContentLoaded', () => {
    // Initial load via HTTP (fallback if WebSocket is slow)
    // WebSocket will send initial_state and replace this
    refreshDevices();

    // Connect WebSocket for real-time updates
    connectWebSocket();
});

let ws = null;
let wsReconnectTimer = null;
let cachedDevices = [];  // In-memory cache of device states
let temperatureDebounceTimers = {};  // Debounce for temperature changes

function connectWebSocket() {
    // Determine protocol (ws or wss)
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;

    console.log(`Connecting to WebSocket: ${wsUrl}`);
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WebSocket connected');
        if (wsReconnectTimer) {
            clearInterval(wsReconnectTimer);
            wsReconnectTimer = null;
        }
    };

    ws.onmessage = (event) => {
        console.log('WS Message:', event.data);

        try {
            const msg = JSON.parse(event.data);

            if (msg.type === 'initial_state' && msg.devices) {
                // Initial state: render all devices
                console.log(`Received initial state: ${msg.devices.length} devices`);
                cachedDevices = msg.devices;
                renderDevices(cachedDevices);
                document.getElementById('loading').classList.add('d-none');
            } else if (msg.type === 'device_update' && msg.device) {
                // Single device update with full data - NO fetch needed!
                console.log(`Device update: ${msg.device.friendlyName}`);
                updateCachedDevice(msg.device);
                updateSingleDeviceCard(msg.device);
            } else {
                // Fallback: Refresh all devices for other/unknown message types
                console.log('Unknown message type, doing full refresh:', msg.type || msg.msgtype);
                refreshDevices();
            }
        } catch (e) {
            // If parsing fails, fallback to full refresh
            console.warn('Failed to parse WS message, doing full refresh:', e);
            refreshDevices();
        }
    };

    ws.onclose = () => {
        console.log('WebSocket disconnected. Reconnecting in 5s...');
        ws = null;
        if (!wsReconnectTimer) {
            wsReconnectTimer = setInterval(connectWebSocket, 5000);
        }
    };

    ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        ws.close();
    };
}

async function refreshDevices() {
    try {
        const response = await fetch('/devices');
        if (!response.ok) throw new Error('Failed to fetch devices');

        const data = await response.json();
        cachedDevices = data.devices;  // Update in-memory cache
        renderDevices(cachedDevices);
        document.getElementById('loading').classList.add('d-none');
        document.getElementById('error-container').classList.add('d-none');
    } catch (error) {
        showError(error.message);
        document.getElementById('loading').classList.add('d-none');
    }
}

function updateCachedDevice(device) {
    // Update device in cache with smart merging
    const index = cachedDevices.findIndex(d => d.endpointId === device.endpointId);
    if (index !== -1) {
        const cached = cachedDevices[index];
        // Merge: preserve existing values if new values are null/undefined/empty
        cachedDevices[index] = {
            ...cached,
            ...device,
            // Keep cached values if new ones are missing
            targetTemperature: device.targetTemperature ?? cached.targetTemperature,
            ambientTemperature: device.ambientTemperature ?? cached.ambientTemperature,
            mode: device.mode || cached.mode,
            fanSpeed: device.fanSpeed || cached.fanSpeed,
            params: Object.keys(device.params || {}).length > 0 ? device.params : cached.params
        };
    } else {
        // New device, add to cache
        cachedDevices.push(device);
    }
}

function updateSingleDeviceCard(device) {
    // Find the device card in the DOM by searching for the endpoint ID in buttons
    const container = document.getElementById('devices-container');
    const cards = container.querySelectorAll('.device-card');

    for (const card of cards) {
        // Check if this card contains a button with this device ID
        const button = card.querySelector(`button[onclick*="${device.endpointId}"]`);
        if (button) {
            // Found the card - replace it with updated HTML
            const col = card.closest('.col-md-6');
            if (col) {
                col.outerHTML = createDeviceCard(device);
                console.log(`DOM updated for device: ${device.friendlyName}`);
                return;
            }
        }
    }

    // Device not found in DOM - do full refresh
    console.warn(`Device ${device.endpointId} not found in DOM, doing full refresh`);
    refreshDevices();
}

function renderDevices(devices) {
    const container = document.getElementById('devices-container');
    container.innerHTML = devices.map(device => createDeviceCard(device)).join('');
}

function createDeviceCard(device) {
    const isOnline = device.isOnline;
    const isOn = device.params?.pwr === 1;
    const statusColor = isOnline ? (isOn ? 'success' : 'secondary') : 'danger';
    const statusText = isOnline ? (isOn ? 'ON' : 'OFF') : 'OFFLINE';

    // Safety checks for values - NEVER show '--' for online devices
    // Use cached values if current values are null/undefined
    const cached = cachedDevices.find(d => d.endpointId === device.endpointId);

    const targetTemp = device.targetTemperature ?? cached?.targetTemperature ?? (isOnline ? '?' : '--');
    const ambientTemp = device.ambientTemperature ?? cached?.ambientTemperature ?? (isOnline ? '?' : '--');
    const currentMode = device.mode || cached?.mode || 'Unknown';
    const currentFan = device.fanSpeed || cached?.fanSpeed || 'Auto';

    // Disable controls if offline
    const disabled = !isOnline ? 'disabled' : '';

    return `
        <div class="col-md-6 col-lg-4">
            <div class="card device-card ${!isOnline ? 'device-offline' : ''}">
                <div class="card-header bg-transparent border-0 d-flex justify-content-between align-items-center pt-3">
                    <h5 class="mb-0 text-truncate" title="${device.friendlyName}">${device.friendlyName}</h5>
                    <span class="badge bg-${statusColor} rounded-pill">${statusText}</span>
                </div>
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center mb-4">
                        <div class="text-center">
                            <span class="text-muted small">Target</span>
                            <div class="d-flex justify-content-center">
                                <span class="temp-display">${targetTemp}</span>
                                <span class="temp-unit">°C</span>
                            </div>
                        </div>
                        <div class="text-center">
                            <span class="text-muted small">Ambient</span>
                            <div class="h4 mb-0 text-secondary">${ambientTemp}°C</div>
                        </div>
                    </div>

                    <div class="control-group mb-3">
                        <label class="small text-muted mb-2">Power</label>
                        <div class="d-grid">
                            <button class="btn btn-${isOn ? 'danger' : 'success'}"
                                onclick="togglePower('${device.endpointId}', ${!isOn})" ${disabled}>
                                <i class="fa-solid fa-power-off me-2"></i> Turn ${isOn ? 'OFF' : 'ON'}
                            </button>
                        </div>
                    </div>

                    <div class="control-group mb-3">
                        <label class="small text-muted mb-2">Mode</label>
                        <div class="d-flex justify-content-between gap-2">
                            ${renderModeButtons(device.endpointId, currentMode, disabled)}
                        </div>
                    </div>

                    <div class="control-group mb-3">
                        <label class="small text-muted mb-2">Fan Speed: <strong>${currentFan}</strong></label>
                        <input type="range" class="form-range" min="0" max="5" step="1"
                            value="${getFanValue(currentFan)}"
                            onchange="setFanSpeed('${device.endpointId}', this.value)" ${disabled}>
                        <div class="d-flex justify-content-between small text-muted">
                            <span>Auto</span><span>Low</span><span>Mid</span><span>High</span><span>Turbo</span><span>Mute</span>
                        </div>
                    </div>

                    <div class="control-group">
                        <label class="small text-muted mb-2">Temperature Control</label>
                        <div class="input-group">
                            <button class="btn btn-outline-secondary" onclick="adjustTemp('${device.endpointId}', -1, ${targetTemp})" ${disabled}>
                                <i class="fa-solid fa-minus"></i>
                            </button>
                            <input type="text" class="form-control text-center" value="${targetTemp}°C" readonly disabled>
                            <button class="btn btn-outline-secondary" onclick="adjustTemp('${device.endpointId}', 1, ${targetTemp})" ${disabled}>
                                <i class="fa-solid fa-plus"></i>
                            </button>
                        </div>
                    </div>
                </div>
                <div class="card-footer bg-transparent border-0 text-muted small text-end">
                    Last updated: ${device.lastUpdated || 'Never'}
                </div>
            </div>
        </div>
    `;
}

function renderModeButtons(deviceId, currentMode, disabled) {
    const modes = [
        { name: 'Cooling', icon: 'snowflake', val: 'cool' },
        { name: 'Heating', icon: 'fire', val: 'heat' },
        { name: 'Dry', icon: 'droplet', val: 'dry' },
        { name: 'Fan', icon: 'fan', val: 'fan' },
        { name: 'Auto', icon: 'robot', val: 'auto' }
    ];

    return modes.map(mode => `
        <button class="btn btn-outline-primary flex-grow-1 p-2 ${currentMode === mode.name ? 'active' : ''}"
            onclick="setMode('${deviceId}', '${mode.val}')"
            title="${mode.name}" ${disabled}>
            <i class="fa-solid fa-${mode.icon}"></i>
        </button>
    `).join('');
}

function getFanValue(name) {
    const map = { 'Auto': 0, 'Low': 1, 'Medium': 2, 'High': 3, 'Turbo': 4, 'Mute': 5 };
    return map[name] || 0;
}

function getFanName(val) {
    const map = ['auto', 'low', 'medium', 'high', 'turbo', 'mute'];
    return map[val] || 'auto';
}

// API Actions
async function togglePower(id, on) {
    await sendCommand(id, 'power', { on });
}

async function setMode(id, mode) {
    await sendCommand(id, 'mode', { mode });
}

async function setFanSpeed(id, val) {
    const speed = getFanName(val);
    await sendCommand(id, 'fan', { speed });
}

async function adjustTemp(id, delta, current) {
    if (current === '--') return;
    const newTemp = current + delta;
    if (newTemp < 16 || newTemp > 30) return;

    // Optimistic UI update: immediately show new temperature
    updateTemperatureDisplay(id, newTemp);

    // Update cache optimistically
    const device = cachedDevices.find(d => d.endpointId === id);
    if (device) {
        device.targetTemperature = newTemp;
    }

    // Debounced API call: wait 800ms of silence before sending
    if (temperatureDebounceTimers[id]) {
        clearTimeout(temperatureDebounceTimers[id]);
    }

    temperatureDebounceTimers[id] = setTimeout(async () => {
        delete temperatureDebounceTimers[id];
        await sendCommand(id, 'temperature', { temperature: newTemp }, false); // Don't refresh after command
    }, 800);
}

function updateTemperatureDisplay(deviceId, newTemp) {
    // Find the device card and update the temperature display immediately
    const container = document.getElementById('devices-container');
    const cards = container.querySelectorAll('.device-card');

    for (const card of cards) {
        const button = card.querySelector(`button[onclick*="${deviceId}"]`);
        if (button) {
            // Update both the display and the button onclick attributes
            const tempDisplay = card.querySelector('.temp-display');
            if (tempDisplay) {
                tempDisplay.textContent = newTemp;
            }

            // Update the - and + buttons with new current value
            const minusBtn = card.querySelector(`button[onclick*="adjustTemp('${deviceId}', -1"]`);
            const plusBtn = card.querySelector(`button[onclick*="adjustTemp('${deviceId}', 1"]`);
            if (minusBtn) minusBtn.setAttribute('onclick', `adjustTemp('${deviceId}', -1, ${newTemp})`);
            if (plusBtn) plusBtn.setAttribute('onclick', `adjustTemp('${deviceId}', 1, ${newTemp})`);

            // Update readonly input
            const tempInput = card.querySelector('input[readonly]');
            if (tempInput) {
                tempInput.value = `${newTemp}°C`;
            }

            console.log(`Optimistic update: ${deviceId} temperature -> ${newTemp}°C`);
            return;
        }
    }
}

async function sendCommand(id, endpoint, payload, shouldRefresh = true) {
    try {
        const response = await fetch(`/devices/${id}/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Command failed');
        }

        showToast('Success', 'Command sent successfully');

        // Only refresh if requested (temperature uses optimistic updates)
        if (shouldRefresh) {
            refreshDevices();
        }
    } catch (error) {
        showToast('Error', error.message, 'danger');
        // On error, refresh to restore correct state
        if (!shouldRefresh) {
            refreshDevices();
        }
    }
}

function showError(msg) {
    const el = document.getElementById('error-container');
    document.getElementById('error-message').innerText = msg;
    el.classList.remove('d-none');
}

function showToast(title, msg, type = 'success') {
    const toastEl = document.getElementById('liveToast');
    document.getElementById('toast-title').innerText = title;
    document.getElementById('toast-body').innerText = msg;
    document.getElementById('toast-body').className = `toast-body text-${type}`;
    const toast = new bootstrap.Toast(toastEl);
    toast.show();
}
