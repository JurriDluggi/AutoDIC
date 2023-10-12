from TDialog import *
from PyQt5.QtWidgets import QWidget, QPushButton, QCheckBox, QHBoxLayout, QVBoxLayout, QTableWidgetItem, QTableWidget


class PositionsTab(QWidget):
    def __init__(self, parent=None):
        """
        Constructor.

        :param parent: parent
        """

        super(PositionsTab, self).__init__(parent)

        self.parent = parent
        self.header_lbls = ['Position', 'X [mm]', 'Y [mm]', 'Z [mm]', 'Rot [deg]', 'Tilt [deg]', 'WD [mm]']
        self.PositionsTable = QTableWidget(0, 7)

        self.init_components()

    def init_components(self):
        """
        Initializes components, takes care of layout.
        """

        self.PositionsTable.setHorizontalHeaderLabels(self.header_lbls)

        addPushButton = QPushButton("Add Current")
        removePushButton = QPushButton("Remove")
        movetoPushButton = QPushButton("Move To")
        PositionsLayout = QHBoxLayout()
        PositionsLayout.addWidget(addPushButton)
        PositionsLayout.addWidget(removePushButton)
        PositionsLayout.addWidget(movetoPushButton)

        addPushButton.clicked.connect(self.addCurrentPosition)
        removePushButton.clicked.connect(self.removeSelectedPosition)
        movetoPushButton.clicked.connect(self.moveToPosition)

        sameposCheckBox = QCheckBox("Milling and imaging position is same")
        sameposCheckBox.setChecked(True)
        sameposCheckBox.setDisabled(True)

        layout = QVBoxLayout()
        layout.addWidget(self.PositionsTable)
        layout.addLayout(PositionsLayout)
        layout.addWidget(sameposCheckBox)
        self.setLayout(layout)

    def addCurrentPosition(self):
        """
        Add new position to the table. Position is taken from stage position.
        """

        if self.parent.connection:
            # TODO - STOP scanning pred nacitanim pozicie (3)
            self.parent.connection.GUISetScanning(0)

            x, y, z, rot, tilt = self.parent.connection.StgGetPosition()
            self.parent.connection.logger.debug("Position: %.3e,%.3e,%.3e,%.3e,%3e" % (x, y, z, rot, tilt))
            wd = self.parent.connection.GetWD()
            self.parent.connection.logger.debug("WD: %3e" % wd)

            # add position
            count = self.PositionsTable.rowCount()
            self.PositionsTable.setRowCount(count + 1)
            self.PositionsTable.setItem(count, 0, QTableWidgetItem("Position_%i" % (count + 1)))
            self.PositionsTable.setItem(count, 1, QTableWidgetItem(str(x)))
            self.PositionsTable.setItem(count, 2, QTableWidgetItem(str(y)))
            self.PositionsTable.setItem(count, 3, QTableWidgetItem(str(z)))
            self.PositionsTable.setItem(count, 4, QTableWidgetItem(str(rot)))
            self.PositionsTable.setItem(count, 5, QTableWidgetItem(str(tilt)))
            self.PositionsTable.setItem(count, 6, QTableWidgetItem(str(wd)))

    def removeSelectedPosition(self):
        """
        Remove position from the table.
        """

        # list selected positions
        selectitems = self.PositionsTable.selectedIndexes()

        # go through the selection
        rows = []
        for itemindexes in selectitems:
            if rows.count(itemindexes.row()) < 1:
                print("Selected rows: %i" % (itemindexes.row()))
                rows.append(itemindexes.row())

        print(rows)

        # deleting from last to the first
        rows.reverse()
        for row in rows:
            self.parent.connection.logger.debug("Removing row %i" % row)
            self.PositionsTable.removeRow(row)

    def moveToPosition(self):
        """
        Move the stage to the specific position.
        """

        # list selected positions
        selectitems = self.PositionsTable.selectedIndexes()

        # go through the selection
        row = selectitems[0].row()

        name = self.PositionsTable.item(row, 0).text()
        print(name)

        x = float(self.PositionsTable.item(row, 1).text())
        y = float(self.PositionsTable.item(row, 2).text())
        z = float(self.PositionsTable.item(row, 3).text())
        rot = float(self.PositionsTable.item(row, 4).text())
        tilt = float(self.PositionsTable.item(row, 5).text())
        wd = float(self.PositionsTable.item(row, 6).text())

        self.parent.connection.logger.debug("Moving to %s: %.3e,%.3e,%.3e,%.3e,%.3e; WD= %.3e mm" % (name, x, y, z, rot, tilt, wd))
        self.parent.connection.StgMoveTo(x, y, z, rot, tilt)

        while self.parent.connection.StgIsBusy():
            self.parent.statusBar.showMessage("Moving the stage...")
            time.sleep(0.5)  # 500 milliseconds sleep

        if not self.parent.connection.StgIsCalibrated():
            self.parent.connection.logger.error("Stage collision!!!")
            self.parent.statusBar.showMessage("Stage movement crashed, calibration required!!!")
        else:
            self.parent.statusBar.showMessage("OK")

        self.parent.connection.SetWD(wd)

    def listPositions(self):
        """
        Return all positions in the table.

        :return: array of positions
        """

        rowcnt = self.PositionsTable.rowCount()
        positions = []

        for row in range(0, rowcnt):
            name = self.PositionsTable.item(row, 0).text()
            x = float(self.PositionsTable.item(row, 1).text())
            y = float(self.PositionsTable.item(row, 2).text())
            z = float(self.PositionsTable.item(row, 3).text())
            rot = float(self.PositionsTable.item(row, 4).text())
            tilt = float(self.PositionsTable.item(row, 5).text())
            wd = float(self.PositionsTable.item(row, 6).text())
            positions.append([name, x, y, z, rot, tilt, wd])

        return positions
