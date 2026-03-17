// ===== Climate Hub Dashboard - Dark Glassmorphism Edition =====

let ws = null;
let wsReconnectTimer = null;
let cachedDevices = [];
let temperatureDebounceTimers = {};
let deviceCooldowns = {};  // {deviceId: timestamp} - prevents WS updates after commands
const COOLDOWN_MS = 5000;

document.addEventListener('DOMContentLoaded', () => {
    refreshDevices();
    connectWebSocket();
    fetchWeather();
});

// ===== WebSocket =====

function connectWebSocket() {
    const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${location.host}/ws`;
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
        console.log('WS connected');
        setWsStatus(true);
        if (wsReconnectTimer) { clearInterval(wsReconnectTimer); wsReconnectTimer = null; }
    };

    ws.onmessage = (event) => {
        try {
            const msg = JSON.parse(event.data);
            if (msg.type === 'initial_state' && msg.devices) {
                cachedDevices = msg.devices;
                renderDevices(cachedDevices);
                hideLoading();
            } else if (msg.type === 'device_update' && msg.device) {
                // Skip update if device is in cooldown (prevents glitch after commands)
                if (isInCooldown(msg.device.endpointId)) {
                    console.log(`Skipping WS update for ${msg.device.friendlyName} (cooldown)`);
                    return;
                }
                updateCachedDevice(msg.device);
                updateSingleDeviceCard(msg.device);
            } else {
                refreshDevices();
            }
        } catch (e) {
            console.warn('WS parse error:', e);
            refreshDevices();
        }
    };

    ws.onclose = () => {
        console.log('WS disconnected');
        setWsStatus(false);
        ws = null;
        if (!wsReconnectTimer) wsReconnectTimer = setInterval(connectWebSocket, 5000);
    };

    ws.onerror = () => ws.close();
}

function setWsStatus(connected) {
    const el = document.getElementById('ws-status');
    if (el) el.classList.toggle('connected', connected);
}

// ===== Cooldown System =====

function startCooldown(deviceId) {
    deviceCooldowns[deviceId] = Date.now();
    // Add visual indicator
    const card = findCardElement(deviceId);
    if (card) {
        card.classList.remove('cooldown');
        void card.offsetWidth; // force reflow
        card.classList.add('cooldown');
        setTimeout(() => card.classList.remove('cooldown'), COOLDOWN_MS);
    }
}

function isInCooldown(deviceId) {
    const ts = deviceCooldowns[deviceId];
    if (!ts) return false;
    if (Date.now() - ts < COOLDOWN_MS) return true;
    delete deviceCooldowns[deviceId];
    return false;
}

// ===== Data Fetching =====

async function refreshDevices() {
    try {
        const r = await fetch('/devices');
        if (!r.ok) throw new Error('Failed to fetch devices');
        const data = await r.json();
        cachedDevices = data.devices;
        renderDevices(cachedDevices);
        hideLoading();
        hideError();
    } catch (e) {
        showError(e.message);
        hideLoading();
    }
}

function hideLoading() { document.getElementById('loading')?.classList.add('hidden'); }
function hideError() { document.getElementById('error-container')?.classList.add('hidden'); }

function updateCachedDevice(device) {
    const i = cachedDevices.findIndex(d => d.endpointId === device.endpointId);
    if (i !== -1) {
        const c = cachedDevices[i];
        cachedDevices[i] = {
            ...c, ...device,
            targetTemperature: device.targetTemperature ?? c.targetTemperature,
            ambientTemperature: device.ambientTemperature ?? c.ambientTemperature,
            mode: device.mode || c.mode,
            fanSpeed: device.fanSpeed || c.fanSpeed,
            verticalSwing: device.verticalSwing ?? c.verticalSwing,
            horizontalSwing: device.horizontalSwing ?? c.horizontalSwing,
            params: Object.keys(device.params || {}).length > 0 ? device.params : c.params
        };
    } else {
        cachedDevices.push(device);
    }
}

// ===== Rendering =====

function renderDevices(devices) {
    const el = document.getElementById('devices-container');
    el.innerHTML = devices.map(d => createDeviceCard(d)).join('');
    // Initialize all noUiSliders
    devices.forEach(d => initTempSlider(d));
}

function updateSingleDeviceCard(device) {
    const card = findCardElement(device.endpointId);
    if (card) {
        const wrapper = card.parentElement || card;
        const tmp = document.createElement('div');
        tmp.innerHTML = createDeviceCard(device);
        wrapper.replaceWith(tmp.firstElementChild);
        initTempSlider(device);
    } else {
        renderDevices(cachedDevices);
    }
}

function findCardElement(deviceId) {
    return document.querySelector(`.device-card[data-id="${deviceId}"]`);
}

// Normalize backend mode names (Cooling→cool, Heating→heat, etc.)
function normalizeMode(mode) {
    if (!mode) return 'auto';
    const map = { cooling: 'cool', heating: 'heat', dry: 'dry', fan: 'fan', auto: 'auto',
                  cool: 'cool', heat: 'heat' };
    return map[mode.toLowerCase()] || mode.toLowerCase();
}

function createDeviceCard(device) {
    const isOnline = device.isOnline;
    const isOn = device.params?.pwr === 1;
    const cached = cachedDevices.find(d => d.endpointId === device.endpointId);

    const targetTemp = device.targetTemperature ?? cached?.targetTemperature ?? '--';
    const ambientTemp = device.ambientTemperature ?? cached?.ambientTemperature ?? '--';
    const currentMode = normalizeMode(device.mode || cached?.mode);
    const currentFan = device.fanSpeed || cached?.fanSpeed || 'Auto';

    const statusClass = !isOnline ? 'status-offline' : (isOn ? 'status-on' : 'status-off');
    const statusText = !isOnline ? 'Offline' : (isOn ? 'On' : 'Off');
    const cardClass = !isOnline ? 'device-offline' : (!isOn ? 'device-off' : `mode-${currentMode}`);

    const disabled = !isOnline ? 'disabled' : '';

    return `
    <div class="device-card-wrap">
        <div class="device-card ${cardClass}" data-id="${device.endpointId}">
            <div class="card-head">
                <h3 title="${device.friendlyName}">${device.friendlyName}</h3>
                <span class="status-badge ${statusClass}">${statusText}</span>
            </div>

            <div class="temp-section">
                <div class="temp-target">
                    <span class="temp-value" id="tv-${device.endpointId}">${targetTemp}</span>
                    <span class="temp-unit">°C</span>
                </div>
                <div class="temp-ambient">
                    <div class="temp-ambient-label">Ambient</div>
                    <div class="temp-ambient-value">${ambientTemp !== '--' ? ambientTemp + '°C' : '--'}</div>
                </div>
            </div>

            <div class="temp-slider-wrap">
                <div id="slider-${device.endpointId}" class="temp-slider"></div>
                <div class="temp-range-labels"><span>16°</span><span>23°</span><span>30°</span></div>
            </div>

            <div class="controls">
                <div class="mode-row">
                    ${renderModeButtons(device.endpointId, currentMode, disabled)}
                </div>

                <div>
                    <div class="fan-row-label">Fan</div>
                    <div class="fan-row">
                        ${renderFanButtons(device.endpointId, currentFan, disabled)}
                    </div>
                </div>

                <div class="swing-row">
                    <button class="swing-btn ${device.verticalSwing ? 'active' : ''}"
                        onclick="toggleSwing('${device.endpointId}', 'vertical', ${!device.verticalSwing})" ${disabled}>
                        <i class="fa-solid fa-arrows-up-down"></i> Vertical
                    </button>
                    <button class="swing-btn ${device.horizontalSwing ? 'active' : ''}"
                        onclick="toggleSwing('${device.endpointId}', 'horizontal', ${!device.horizontalSwing})" ${disabled}>
                        <i class="fa-solid fa-arrows-left-right"></i> Horizontal
                    </button>
                </div>

                <div class="power-row">
                    <button class="power-btn ${isOn ? 'is-on' : 'is-off'}"
                        onclick="togglePower('${device.endpointId}', ${!isOn})" ${disabled}>
                        <i class="fa-solid fa-power-off"></i> ${isOn ? 'Turn Off' : 'Turn On'}
                    </button>
                </div>
            </div>

            <div class="card-foot">${device.lastUpdated || ''}</div>
        </div>
    </div>`;
}

function renderModeButtons(deviceId, currentMode, disabled) {
    const modes = [
        { val: 'cool', icon: 'snowflake', label: 'Cool' },
        { val: 'heat', icon: 'fire', label: 'Heat' },
        { val: 'dry',  icon: 'droplet', label: 'Dry' },
        { val: 'fan',  icon: 'fan', label: 'Fan' },
        { val: 'auto', icon: 'wand-magic-sparkles', label: 'Auto' },
    ];
    return modes.map(m => `
        <button class="mode-btn ${currentMode === m.val ? 'active' : ''}" data-mode="${m.val}"
            onclick="setMode('${deviceId}', '${m.val}')" ${disabled}>
            <i class="fa-solid fa-${m.icon}"></i>
            <span>${m.label}</span>
        </button>
    `).join('');
}

function renderFanButtons(deviceId, currentFan, disabled) {
    const fans = ['Auto', 'Low', 'Mid', 'High', 'Turbo', 'Mute'];
    const fanApiMap = { 'Auto': 'auto', 'Low': 'low', 'Mid': 'medium', 'High': 'high', 'Turbo': 'turbo', 'Mute': 'mute' };
    const currentNorm = currentFan === 'Medium' ? 'Mid' : currentFan;
    return fans.map(f => `
        <button class="fan-btn ${currentNorm === f ? 'active' : ''}"
            onclick="setFanSpeed('${deviceId}', '${fanApiMap[f]}')" ${disabled}>${f}</button>
    `).join('');
}

// ===== Temperature Slider =====

function initTempSlider(device) {
    const el = document.getElementById(`slider-${device.endpointId}`);
    if (!el || el.noUiSlider) return;

    const isOnline = device.isOnline;
    const isOn = device.params?.pwr === 1;
    const temp = device.targetTemperature ?? 24;

    noUiSlider.create(el, {
        start: [temp],
        connect: [true, false],
        range: { min: 16, max: 30 },
        step: 1,
        tooltips: false,
    });

    if (!isOnline || !isOn) el.setAttribute('disabled', true);

    // Live update display while sliding
    el.noUiSlider.on('slide', (values) => {
        const v = Math.round(values[0]);
        const tv = document.getElementById(`tv-${device.endpointId}`);
        if (tv) tv.textContent = v;
    });

    // Send command on release
    el.noUiSlider.on('change', (values) => {
        const newTemp = Math.round(values[0]);
        setTemperature(device.endpointId, newTemp);
    });
}

function setTemperature(id, newTemp) {
    // Update cache
    const device = cachedDevices.find(d => d.endpointId === id);
    if (device) device.targetTemperature = newTemp;

    // Display already updated by slider 'slide' event
    startCooldown(id);

    // Debounce API call
    if (temperatureDebounceTimers[id]) clearTimeout(temperatureDebounceTimers[id]);
    temperatureDebounceTimers[id] = setTimeout(async () => {
        delete temperatureDebounceTimers[id];
        await sendCommand(id, 'temperature', { temperature: newTemp }, false);
    }, 600);
}

// ===== Optimistic UI Helper =====

function optimisticUpdate(id, changes) {
    const device = cachedDevices.find(d => d.endpointId === id);
    if (!device) return;
    Object.assign(device, changes);
    if (changes.params) device.params = { ...device.params, ...changes.params };
    startCooldown(id);
    updateSingleDeviceCard(device);
}

// ===== Commands =====

async function togglePower(id, on) {
    const modeMap = { 'Cooling': 'cool', 'Heating': 'heat', 'Dry': 'dry', 'Fan': 'fan', 'Auto': 'auto' };
    const device = cachedDevices.find(d => d.endpointId === id);
    const mode = device ? (modeMap[device.mode] || device.mode?.toLowerCase() || 'auto') : 'auto';
    optimisticUpdate(id, { params: { pwr: on ? 1 : 0 }, mode: on ? device?.mode : device?.mode });
    await sendCommand(id, 'power', { on }, false);
}

async function setMode(id, mode) {
    optimisticUpdate(id, { mode: mode });
    await sendCommand(id, 'mode', { mode }, false);
}

async function setFanSpeed(id, speed) {
    const displayMap = { auto: 'Auto', low: 'Low', medium: 'Medium', high: 'High', turbo: 'Turbo', mute: 'Mute' };
    optimisticUpdate(id, { fanSpeed: displayMap[speed] || speed });
    await sendCommand(id, 'fan', { speed }, false);
}

async function toggleSwing(id, direction, on) {
    const changes = direction === 'vertical' ? { verticalSwing: on } : { horizontalSwing: on };
    optimisticUpdate(id, changes);
    await sendCommand(id, 'swing', { direction, on }, false);
}

async function sendCommand(id, endpoint, payload, shouldRefresh = true) {
    try {
        const r = await fetch(`/devices/${id}/${endpoint}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        if (!r.ok) {
            const err = await r.json();
            throw new Error(err.detail || 'Command failed');
        }
        showToast('Command sent');
        if (shouldRefresh) refreshDevices();
    } catch (e) {
        showToast(e.message, true);
        if (!shouldRefresh) refreshDevices();
    }
}

// ===== Toast =====

function showToast(msg, isError = false) {
    const c = document.getElementById('toast-container');
    const t = document.createElement('div');
    t.className = `toast-msg ${isError ? 'error' : ''}`;
    t.textContent = msg;
    c.appendChild(t);
    setTimeout(() => t.remove(), 3200);
}

// ===== Weather =====

async function fetchWeather() {
    try {
        const r = await fetch('https://api.open-meteo.com/v1/forecast?latitude=36.6271&longitude=-4.5403&current=temperature_2m,weather_code,wind_speed_10m&timezone=Europe/Madrid');
        const data = await r.json();
        const cur = data.current;
        const temp = Math.round(cur.temperature_2m);
        const icon = weatherIcon(cur.weather_code);
        const desc = weatherDesc(cur.weather_code);
        const el = document.getElementById('weather');
        if (el) el.innerHTML = `${icon} ${temp}°C ${desc}`;
    } catch (e) {
        console.warn('Weather fetch failed:', e);
    }
    // Refresh every 15 minutes
    setTimeout(fetchWeather, 15 * 60 * 1000);
}

function weatherIcon(code) {
    if (code === 0) return '<i class="fa-solid fa-sun" style="color:#fbbf24"></i>';
    if (code <= 3) return '<i class="fa-solid fa-cloud-sun" style="color:#94a3b8"></i>';
    if (code <= 48) return '<i class="fa-solid fa-smog" style="color:#94a3b8"></i>';
    if (code <= 67) return '<i class="fa-solid fa-cloud-rain" style="color:#38bdf8"></i>';
    if (code <= 77) return '<i class="fa-solid fa-snowflake" style="color:#a5b4fc"></i>';
    if (code <= 82) return '<i class="fa-solid fa-cloud-showers-heavy" style="color:#38bdf8"></i>';
    if (code <= 99) return '<i class="fa-solid fa-bolt" style="color:#fbbf24"></i>';
    return '<i class="fa-solid fa-cloud"></i>';
}

function weatherDesc(code) {
    if (code === 0) return 'Sereno';
    if (code <= 3) return 'Parz. nuvoloso';
    if (code <= 48) return 'Nebbia';
    if (code <= 55) return 'Pioggerella';
    if (code <= 67) return 'Pioggia';
    if (code <= 77) return 'Neve';
    if (code <= 82) return 'Acquazzoni';
    if (code <= 99) return 'Temporale';
    return '';
}

// ===== Error =====

function showError(msg) {
    const el = document.getElementById('error-container');
    document.getElementById('error-message').textContent = msg;
    el.classList.remove('hidden');
}
