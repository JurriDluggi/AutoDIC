from PyQt5.QtCore import QFileInfo
from PyQt5.QtWidgets import QLabel, QWidget, QPushButton, QLineEdit, QVBoxLayout, QSpinBox, QFileDialog


class ProjectTab(QWidget):
    def __init__(self, fileInfo, parent=None):
        """
        Constructor.

        :param fileInfo: file information
        :param parent: parent
        """

        super(ProjectTab, self).__init__(parent)

        self.pathLabel = QLabel("XML Milling Template:")
        self.pathValueLabel = QLineEdit(fileInfo.absoluteFilePath())

        self.openFileNameLabel = QLabel()
        self.openFileNameButton = QPushButton("Open ...")

        self.repeatEdit = QSpinBox()

        self.mainLayout = QVBoxLayout()

        self.init_components()

    def init_components(self):
        """
        Initializes components, takes care of layout.
        """

        self.openFileNameButton.clicked.connect(self.setOpenFileName)

        repeatLabel = QLabel("Depth steps:")
        self.repeatEdit.setValue(25)
        self.repeatEdit.setMaximum(200)

        self.mainLayout.addWidget(self.pathLabel)
        self.mainLayout.addWidget(self.pathValueLabel)
        self.mainLayout.addWidget(self.openFileNameButton)
        self.mainLayout.addWidget(self.openFileNameLabel)
        self.mainLayout.addWidget(repeatLabel)
        self.mainLayout.addWidget(self.repeatEdit)
        self.mainLayout.addStretch(1)
        self.setLayout(self.mainLayout)

    def setOpenFileName(self):
        """
        Open XML file with milling template.
        """

        options = QFileDialog.Options()
        fileName, filtr = QFileDialog.getOpenFileName(self, "QFileDialog.getOpenFileName()",
                    self.openFileNameLabel.text(), "DrawBeam Layer XML (*.xml);;All Files (*)", "", options)

        if fileName:
            self.fileInfo = QFileInfo(fileName)
            self.pathValueLabel.setText(self.fileInfo.absoluteFilePath())
