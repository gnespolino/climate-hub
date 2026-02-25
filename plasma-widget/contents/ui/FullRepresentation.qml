import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents
import org.kde.plasma.extras as PlasmaExtras

PlasmaExtras.Representation {
    id: fullRoot

    property var deviceModel

    signal setPower(string deviceId, bool on)
    signal setTemperature(string deviceId, real temp)
    signal setMode(string deviceId, string mode)
    signal setFanSpeed(string deviceId, string speed)

    header: PlasmaExtras.Heading {
        text: "Climate Control"
        level: 2
    }

    contentItem: Item {
        implicitWidth: 380
        implicitHeight: 400

        GridView {
            id: grid
            anchors.fill: parent
            model: fullRoot.deviceModel
            cellWidth: 185
            cellHeight: 195
            clip: true

            delegate: DeviceDelegate {
                onSetPower: (deviceId, on) => fullRoot.setPower(deviceId, on)
                onSetTemperature: (deviceId, temp) => fullRoot.setTemperature(deviceId, temp)
                onSetMode: (deviceId, mode) => fullRoot.setMode(deviceId, mode)
                onSetFanSpeed: (deviceId, speed) => fullRoot.setFanSpeed(deviceId, speed)
            }
        }

        PlasmaComponents.Label {
            anchors.centerIn: parent
            text: "Loading devices..."
            visible: fullRoot.deviceModel.count === 0
        }
    }
}