import QtQuick
import QtQuick.Layouts
import org.kde.plasma.components as PlasmaComponents
import org.kde.kirigami as Kirigami

Item {
    id: compactRoot
    property int activeCount: 0

    signal clicked()

    MouseArea {
        anchors.fill: parent
        onClicked: compactRoot.clicked()
    }

    RowLayout {
        anchors.fill: parent
        spacing: 2

        Kirigami.Icon {
            source: "weather-clear"
            Layout.fillHeight: true
            Layout.preferredWidth: height
        }

        PlasmaComponents.Label {
            text: compactRoot.activeCount > 0 ? compactRoot.activeCount : ""
            visible: compactRoot.activeCount > 0
            Layout.fillWidth: true
            font.bold: true
        }
    }
}
