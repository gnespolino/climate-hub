import QtQuick
import QtQuick.Controls as QQC2
import QtQuick.Layouts
import org.kde.kirigami as Kirigami

Kirigami.FormLayout {
    property alias cfg_apiUrl: apiUrlField.text
    property alias cfg_refreshInterval: intervalField.value

    QQC2.TextField {
        id: apiUrlField
        Kirigami.FormData.label: "API URL:"
        placeholderText: "http://localhost:8090"
    }

    QQC2.SpinBox {
        id: intervalField
        Kirigami.FormData.label: "Refresh Interval (sec):"
        from: 1
        to: 600
        stepSize: 1
    }
}