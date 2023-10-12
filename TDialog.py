import sys

from ImageT import *
from PositionT import *
from ProcessT import *
from ProjectT import *

from PyQt5.QtCore import QFileInfo, Qt
from PyQt5.QtGui import QImage, QPixmap
from PyQt5.QtWidgets import QLabel, QPushButton, QDialog, QTabWidget, QStatusBar, QLineEdit, QGroupBox, QHBoxLayout, \
    QVBoxLayout, QApplication

from lib.DIC_lib import *


class TabDialog(QDialog):
    def __init__(self, fileName, parent=None):
        """
        Constructor.

        :param fileName: name of file
        :param parent: parent
        """

        super(TabDialog, self).__init__(parent)

        self.fib_ip = "localhost"
        self.connection = None
        self.fileInfo = QFileInfo(fileName)

        self.tabWidget = QTabWidget()

        self.ProjectTab = ProjectTab(self.fileInfo, parent=self)
        self.ImageTab = ImageTab(parent=self)
        self.PositionsTab = PositionsTab(parent=self)
        self.ProcessTab = ProcessTab(self.fileInfo, parent=self)

        self.statusBar = QStatusBar()
        self.IP_Edit = QLineEdit()
        self.IP_TestBtn = QPushButton('Connect')

        self.connectionGroup = QGroupBox("SharkSEM Connection")

        self.init_components()

    def init_components(self):
        """
        Initializes components, takes care of layout.
        """

        self.tabWidget.addTab(self.ProjectTab, "Project")
        self.tabWidget.addTab(self.ImageTab, "Image")
        self.tabWidget.addTab(self.PositionsTab, "Positions")
        self.tabWidget.addTab(self.ProcessTab, "Process")

        self.statusBar.showMessage("Not connected.")

        logo = QImage("images\\banner.png")
        logoLabel = QLabel()
        logoLabel.setPixmap(QPixmap.fromImage(logo))
        logoLabel.setAlignment(Qt.AlignCenter)

        # connection
        IP_Label = QLabel("SEM IP Address:")
        self.IP_Edit.setText("localhost")
        self.IP_Edit.setToolTip('The IP address could be the IPv4 number (e.g. 127.0.0.1) or a computer name '
                                'detectable by DNS e.g. localhost.')
        IP_Port = QLabel(":8300")

        # action
        self.IP_TestBtn.clicked.connect(self.ConnectSem)

        connectionLayout = QHBoxLayout()
        connectionLayout.addWidget(IP_Label)
        connectionLayout.addWidget(self.IP_Edit)
        connectionLayout.addWidget(IP_Port)
        connectionLayout.addWidget(self.IP_TestBtn)
        self.connectionGroup.setLayout(connectionLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addStretch(1)
        mainLayout.addWidget(logoLabel)
        mainLayout.addWidget(self.connectionGroup)
        mainLayout.addWidget(self.tabWidget)
        mainLayout.addWidget(self.statusBar)
        self.setLayout(mainLayout)
        self.setWindowTitle("TESCAN AutoDIC")

    def ConnectSem(self):
        """
        Connection with microscope.
        """

        self.fib_ip = self.IP_Edit.text()
        if self.connection:
            self.connection = None
            self.IP_TestBtn.setText("""Connect""")
            self.statusBar.showMessage("Not connected.")
        else:
            self.statusBar.showMessage("Connecting %s...." % self.fib_ip)
            try:
                self.connection = myFibSem(self.fib_ip)
                self.ProcessTab.getPresetList()
                self.ImageTab.getPresetList()
                self.ImageTab.getDetectors()
            except FibError:
                self.statusBar.showMessage("Connection to %s failed!" % self.fib_ip)
                self.IP_TestBtn.setText("""Connect""")
                self.connection = None
            else:
                self.statusBar.showMessage("Connected to: %s" % self.fib_ip)
                self.IP_TestBtn.setText("""Disconnect""")

    def closeEvent(self, event):
        event.accept()


if __name__ == '__main__':

    app = QApplication(sys.argv)

    fileName = "./geometries/ringcore5um.xml"

    tabdialog = TabDialog(fileName)
    tabdialog.setGeometry(80, 80, 800, 514)
    sys.exit(tabdialog.exec_())
