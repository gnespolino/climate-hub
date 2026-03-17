import QtQuick
import QtQuick.Layouts
import QtQuick.Controls as QQC2
import org.kde.plasma.components as PlasmaComponents
import org.kde.kirigami as Kirigami

Item {
    id: delegateRoot
    width: 180
    height: 190

    property var deviceData: model

    // Signals for control commands
    signal setPower(string deviceId, bool on)
    signal setTemperature(string deviceId, real temp)
    signal setMode(string deviceId, string mode)
    signal setFanSpeed(string deviceId, string speed)

    // Mode and fan speed options
    readonly property var modeOptions: ["cool", "heat", "dry", "fan", "auto"]
    readonly property var fanOptions: ["auto", "low", "medium", "high", "turbo", "mute"]

    Rectangle {
        anchors.fill: parent
        anchors.margins: 2
        radius: 8
        color: deviceData.isOnline
               ? (deviceData.isOn ? Qt.rgba(0.2, 0.8, 0.2, 0.1) : Qt.rgba(0.5, 0.5, 0.5, 0.1))
               : Qt.rgba(0.8, 0.2, 0.2, 0.1)
        border.color: deviceData.isOnline
                      ? (deviceData.isOn ? Kirigami.Theme.positiveTextColor : Kirigami.Theme.textColor)
                      : Kirigami.Theme.negativeTextColor
        border.width: 1

        ColumnLayout {
            anchors.fill: parent
            anchors.margins: 8
            spacing: 4

            // Header: Name + Power Toggle
            RowLayout {
                Layout.fillWidth: true
                spacing: 4

                Kirigami.Icon {
                    source: deviceData.isOnline ? "weather-clear" : "network-disconnect"
                    Layout.preferredWidth: 16
                    Layout.preferredHeight: 16
                }

                PlasmaComponents.Label {
                    text: deviceData.friendlyName
                    Layout.fillWidth: true
                    elide: Text.ElideRight
                    font.bold: true
                    font.pointSize: 9
                    opacity: deviceData.isOnline ? 1.0 : 0.6
                }

                PlasmaComponents.Switch {
                    id: powerSwitch
                    checked: deviceData.isOn
                    enabled: deviceData.isOnline
                    Layout.preferredWidth: 40
                    onToggled: {
                        delegateRoot.setPower(deviceData.endpointId, checked)
                    }
                }
            }

            // Offline message
            PlasmaComponents.Label {
                Layout.fillWidth: true
                Layout.alignment: Qt.AlignHCenter
                visible: !deviceData.isOnline
                text: "OFFLINE"
                font.bold: true
                opacity: 0.5
                horizontalAlignment: Text.AlignHCenter
            }

            // Controls (only visible when online)
            ColumnLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                spacing: 4
                visible: deviceData.isOnline

                // Temperature display and slider
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    visible: deviceData.isOn

                    RowLayout {
                        Layout.fillWidth: true
                        Layout.alignment: Qt.AlignHCenter

                        PlasmaComponents.Label {
                            text: tempSlider.value.toFixed(1) + "°C"
                            font.pointSize: 16
                            font.weight: Font.Light
                        }
                    }

                    PlasmaComponents.Label {
                        Layout.alignment: Qt.AlignHCenter
                        text: "Ambient: " + deviceData.ambientTemperature + "°C"
                        font.pointSize: 8
                        opacity: 0.7
                    }

                    QQC2.Slider {
                        id: tempSlider
                        Layout.fillWidth: true
                        from: 16
                        to: 30
                        stepSize: 0.5
                        value: typeof deviceData.targetTemperature === "number" ? deviceData.targetTemperature : 22
                        enabled: deviceData.isOn

                        onPressedChanged: {
                            if (!pressed) {
                                delegateRoot.setTemperature(deviceData.endpointId, value)
                            }
                        }
                    }
                }

                // Mode and Fan selectors (only when ON)
                RowLayout {
                    Layout.fillWidth: true
                    spacing: 4
                    visible: deviceData.isOn

                    QQC2.ComboBox {
                        id: modeCombo
                        Layout.fillWidth: true
                        model: delegateRoot.modeOptions
                        currentIndex: {
                            var m = deviceData.mode ? deviceData.mode.toLowerCase() : "auto";
                            var idx = delegateRoot.modeOptions.indexOf(m);
                            return idx >= 0 ? idx : 4;
                        }
                        font.pointSize: 8
                        onActivated: {
                            delegateRoot.setMode(deviceData.endpointId, currentText)
                        }
                    }

                    QQC2.ComboBox {
                        id: fanCombo
                        Layout.fillWidth: true
                        model: delegateRoot.fanOptions
                        currentIndex: {
                            var f = deviceData.fanSpeed ? deviceData.fanSpeed.toLowerCase() : "auto";
                            var idx = delegateRoot.fanOptions.indexOf(f);
                            return idx >= 0 ? idx : 0;
                        }
                        font.pointSize: 8
                        onActivated: {
                            delegateRoot.setFanSpeed(deviceData.endpointId, currentText)
                        }
                    }
                }

                // Mode icon row (when ON)
                RowLayout {
                    Layout.fillWidth: true
                    visible: deviceData.isOn
                    spacing: 4

                    Kirigami.Icon {
                        source: getModeIcon(deviceData.mode)
                        Layout.preferredWidth: 16
                        Layout.preferredHeight: 16
                    }

                    Item { Layout.fillWidth: true }

                    Kirigami.Icon {
                        source: "preferences-system-power"
                        Layout.preferredWidth: 14
                        Layout.preferredHeight: 14
                        opacity: 0.6
                    }

                    PlasmaComponents.Label {
                        text: deviceData.fanSpeed || "Auto"
                        font.pointSize: 8
                        opacity: 0.7
                    }
                }

                // OFF message
                PlasmaComponents.Label {
                    Layout.fillWidth: true
                    Layout.alignment: Qt.AlignHCenter
                    visible: !deviceData.isOn
                    text: "OFF"
                    font.bold: true
                    font.pointSize: 14
                    opacity: 0.5
                    horizontalAlignment: Text.AlignHCenter
                }

                Item { Layout.fillHeight: true }
            }
        }
    }

    function getModeIcon(mode) {
        if (!mode) return "question";
        mode = mode.toLowerCase();
        if (mode.includes("cool")) return "weather-snow";
        if (mode.includes("heat")) return "weather-clear";
        if (mode.includes("dry")) return "weather-showers";
        if (mode.includes("fan")) return "arrow-right";
        if (mode.includes("auto")) return "system-run";
        return "question";
    }
}
