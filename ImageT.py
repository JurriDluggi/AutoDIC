from PyQt5.QtWidgets import QLabel, QWidget, QPushButton, QGroupBox, QVBoxLayout, QSpinBox, QFileDialog, QDoubleSpinBox, QComboBox, QGridLayout


class ImageTab(QWidget):
    def __init__(self, parent=None):
        """
        Constructor.

        :param parent: parent
        """

        super(ImageTab, self).__init__(parent)

        self.parent = parent
        self.settingsGroup = QGroupBox("Image Settings")

        self.widthEdit = QDoubleSpinBox()
        self.heightEdit = QDoubleSpinBox()
        self.pixelSize = QDoubleSpinBox()
        self.dwellEdit = QSpinBox()
        self.frames = QSpinBox()
        self.imagingPreset = QComboBox()
        self.detect = QComboBox()
        self.acc = QSpinBox()
        self.imgFormat = QComboBox()

        self.pathLabel = QLabel("Output folder:")
        self.outputDir = QLabel("./data")
        self.outputDirButton = QPushButton("Select ...")

        self.init_components()

    def init_components(self):
        """
        Initializes components, takes care of layout.
        """

        sizeLabel = QLabel("Width x Height:")
        unitLabel = QLabel("µm")
        pixelLabel = QLabel("PixelSize:")
        pixelUnit = QLabel("nm")
        dwellLabel = QLabel("Dwell time:")
        dwellUnit = QLabel("ns \t\t\t Accumulation:")
        frameLabel = QLabel("Frames:")
        presetLabel = QLabel("SEM Preset:")
        detectorchoices = []
        detecLabel = QLabel("Detector:")
        formatchoices = ["PNG", "TIF"]
        formatLabel = QLabel("Format:")

        ImgSettingsLayout = QGridLayout()
        mainLayout = QVBoxLayout()

        self.widthEdit.setValue(5)
        self.widthEdit.setMaximum(1000)

        self.heightEdit.setValue(5)
        self.heightEdit.setMaximum(1000)

        self.pixelSize.setMaximum(100000)
        self.pixelSize.setMinimum(1.0)
        self.pixelSize.setValue(5.0)

        self.dwellEdit.setMaximum(100000)
        self.dwellEdit.setValue(300)

        self.acc.setMaximum(100)
        self.acc.setValue(10)
        self.acc.setMinimum(1)

        self.frames.setMaximum(10)
        self.frames.setMinimum(0)
        self.frames.setValue(5)

        self.detect.addItems(detectorchoices)
        self.detect.setCurrentIndex(0)

        self.imgFormat.addItems(formatchoices)
        self.imgFormat.setCurrentIndex(1)

        self.outputDirButton.clicked.connect(self.setOutDir)

        ImgSettingsLayout.addWidget(sizeLabel, 0, 0)
        ImgSettingsLayout.addWidget(self.widthEdit, 0, 1)
        ImgSettingsLayout.addWidget(self.heightEdit, 0, 2)
        ImgSettingsLayout.addWidget(unitLabel, 0, 3)
        ImgSettingsLayout.addWidget(pixelLabel, 1, 0)
        ImgSettingsLayout.addWidget(self.pixelSize, 1, 1)
        ImgSettingsLayout.addWidget(pixelUnit, 1, 2)
        ImgSettingsLayout.addWidget(dwellLabel, 2, 0)
        ImgSettingsLayout.addWidget(self.dwellEdit, 2, 1)
        ImgSettingsLayout.addWidget(dwellUnit, 2, 2)
        ImgSettingsLayout.addWidget(self.acc, 2, 3)
        ImgSettingsLayout.addWidget(frameLabel, 3, 0)
        ImgSettingsLayout.addWidget(self.frames, 3, 1)
        ImgSettingsLayout.addWidget(presetLabel, 4, 0)
        ImgSettingsLayout.addWidget(self.imagingPreset, 4, 1)
        ImgSettingsLayout.addWidget(detecLabel, 5, 0)
        ImgSettingsLayout.addWidget(self.detect, 5, 1)
        ImgSettingsLayout.addWidget(formatLabel, 6, 0)
        ImgSettingsLayout.addWidget(self.imgFormat, 6, 1)
        ImgSettingsLayout.addWidget(self.pathLabel, 7, 0)
        ImgSettingsLayout.addWidget(self.outputDir, 7, 1)
        ImgSettingsLayout.addWidget(self.outputDirButton, 7, 2)

        self.settingsGroup.setLayout(ImgSettingsLayout)

        mainLayout.addWidget(self.settingsGroup)

        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    def setOutDir(self):
        """
        Select output directory, where data will be saved.
        """

        options = QFileDialog.DontResolveSymlinks | QFileDialog.ShowDirsOnly
        directory = QFileDialog.getExistingDirectory(self, "Select Output Directory",
                                                     self.outputDir.text(), options)
        if directory:
            self.outputDir.setText(directory)

    def getPresetList(self):
        """
        Get list of preset.
        """

        if self.parent.connection:
            presets = self.parent.connection.SemListPresets()
            self.parent.connection.logger.debug("Receiving SEM preset list")
            self.imagingPreset.insertItem(0, "None")
            for i in range(0, len(presets)):
                self.imagingPreset.removeItem(i + 1)
                self.imagingPreset.insertItem(i + 1, presets[i])

    def getDetectors(self):
        if self.parent.connection:
            detectors = self.parent.connection.DtEnumDetectors()
            self.parent.connection.logger.debug("Receiving detectors")
            index = 0
            i = 0
            while index < len(detectors):
                index = detectors.find('=', index)
                if index == -1:
                    break

                name = ""
                index = index + 1

                while detectors[index].isalpha() and (detectors[index] != "." and detectors[index] != "="):
                    name = name + detectors[index]
                    index += 1

                if name.isalpha():
                    self.detect.insertItem(i, name)
                    i += 1

