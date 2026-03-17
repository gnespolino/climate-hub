import QtQuick
import org.kde.plasma.plasmoid

PlasmoidItem {
    id: root

    // --- Properties ---
    property int activeDevicesCount: 0
    property string apiUrl: Plasmoid.configuration.apiUrl
    property int refreshInterval: Plasmoid.configuration.refreshInterval

    // --- Data Model ---
    ListModel {
        id: devicesModel
    }

    // --- Polling Timer ---
    Timer {
        id: refreshTimer
        interval: root.refreshInterval * 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: fetchDevices()
    }

    // --- Logic ---
    function fetchDevices() {
        var xhr = new XMLHttpRequest();
        var url = root.apiUrl + "/devices";
        
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    try {
                        var response = JSON.parse(xhr.responseText);
                        updateModel(response.devices);
                    } catch (e) {
                        console.error("JSON Parse error: " + e);
                    }
                } else {
                    console.error("API Error: " + xhr.status);
                }
            }
        }
        xhr.open("GET", url);
        xhr.send();
    }

    function updateModel(devices) {
        var active = 0;
        devicesModel.clear();

        for (var i = 0; i < devices.length; i++) {
            var dev = devices[i];
            var isOn = (dev.params && dev.params.pwr === 1);
            if (dev.isOnline && isOn) {
                active++;
            }

            devicesModel.append({
                endpointId: dev.endpointId,
                friendlyName: dev.friendlyName,
                isOnline: dev.isOnline,
                isOn: isOn,
                targetTemperature: dev.targetTemperature || "--",
                ambientTemperature: dev.ambientTemperature || "--",
                mode: dev.mode || "Unknown",
                fanSpeed: dev.fanSpeed || "Auto"
            });
        }
        root.activeDevicesCount = active;
    }

    // --- Control API Functions ---
    function sendCommand(endpoint, body, callback) {
        var xhr = new XMLHttpRequest();
        xhr.onreadystatechange = function() {
            if (xhr.readyState === XMLHttpRequest.DONE) {
                if (xhr.status === 200) {
                    if (callback) callback(true);
                    fetchDevices(); // Refresh after command
                } else {
                    console.error("Command failed: " + xhr.status);
                    if (callback) callback(false);
                }
            }
        }
        xhr.open("POST", endpoint);
        xhr.setRequestHeader("Content-Type", "application/json");
        xhr.send(JSON.stringify(body));
    }

    function setPower(deviceId, on) {
        var endpoint = root.apiUrl + "/devices/" + deviceId + "/power";
        sendCommand(endpoint, {"on": on});
    }

    function setTemperature(deviceId, temperature) {
        var endpoint = root.apiUrl + "/devices/" + deviceId + "/temperature";
        sendCommand(endpoint, {"temperature": temperature});
    }

    function setMode(deviceId, mode) {
        var endpoint = root.apiUrl + "/devices/" + deviceId + "/mode";
        sendCommand(endpoint, {"mode": mode});
    }

    function setFanSpeed(deviceId, speed) {
        var endpoint = root.apiUrl + "/devices/" + deviceId + "/fan";
        sendCommand(endpoint, {"speed": speed});
    }

    // --- UI Connections ---
    compactRepresentation: CompactRepresentation {
        activeCount: root.activeDevicesCount
        onClicked: root.expanded = !root.expanded
    }

    fullRepresentation: FullRepresentation {
        deviceModel: devicesModel
        onSetPower: (deviceId, on) => root.setPower(deviceId, on)
        onSetTemperature: (deviceId, temp) => root.setTemperature(deviceId, temp)
        onSetMode: (deviceId, mode) => root.setMode(deviceId, mode)
        onSetFanSpeed: (deviceId, speed) => root.setFanSpeed(deviceId, speed)
    }
    
    // Update timer if config changes
    onRefreshIntervalChanged: {
        refreshTimer.interval = refreshInterval * 1000;
        refreshTimer.restart();
    }
    
    onApiUrlChanged: {
        fetchDevices();
    }
}
