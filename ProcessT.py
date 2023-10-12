import sys
import threading

from ImageT import *
from PositionT import *
from TDialog import *
from ProjectT import *
from SemImage import *
from FibProcess import *

import numpy as np

from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QLabel, QWidget, QPushButton, QGroupBox, QHBoxLayout, QVBoxLayout, \
    QApplication, QGridLayout, QProgressBar, QDoubleSpinBox, QComboBox


class ProcessTab(QWidget):
    def __init__(self, fileInfo, parent=None):
        """
        Constructor.

        :param fileInfo: file information
        :param parent: parent
        """

        super(ProcessTab, self).__init__(parent)

        self.parent = parent
        self.currentValue = 0
        self.currentValueAll = 0
        self.currentStatus = 0
        self.end = False
        self.esttime = 0.0
        self.reset = False

        self.paused = False
        self.stoped = False
        self.resume = False

        self.images = 0

        self.timer = QTimer()
        self.timer.timeout.connect(self.timeFunction)

        # status locks
        self.FibRunning = False
        self.imageAcquisition = False
        self.stageBusy = False

        # FIB settings group
        self.settingsGroup = QGroupBox("FIB Settings")
        self.rateEdit = QDoubleSpinBox()
        self.dwellEdit = QDoubleSpinBox()

        self.millingPreset = QComboBox()

        self.checkPushButton = QPushButton("Check")
        self.runPushButton = QPushButton("Run")
        self.pausePushButton = QPushButton("Pause")
        self.stopPushButton = QPushButton("Stop")

        # Process control group
        self.processGroup = QGroupBox("Process Control")

        self.progressBarLayerLabel = QLabel("Layer Progress:")
        self.progressBarLayer = QProgressBar()

        self.progressBarLabel = QLabel("Overall Progress:")
        self.progressBar = QProgressBar()

        self.init_components()

    def init_components(self):
        """
        Initializes components, takes care of layout.
        """

        millingLabel = QLabel("FIB milling:")

        rateLabel = QLabel("Milling rate:")
        self.rateEdit.setValue(0.204)
        self.rateEdit.setDecimals(3)
        self.rateEdit.setMaximum(20)
        rateUnit = QLabel("µm<sup>3</sup>/nA/s")

        dwellLabel = QLabel("Dwell time:")
        self.dwellEdit.setValue(1.0)
        self.dwellEdit.setMaximum(10000)
        dwellUnit = QLabel("µs")

        FibSettingsLayout = QGridLayout()
        FibSettingsLayout.addWidget(millingLabel, 0, 0)
        FibSettingsLayout.addWidget(self.millingPreset, 0, 1)
        FibSettingsLayout.addWidget(rateLabel, 1, 0)
        FibSettingsLayout.addWidget(self.rateEdit, 1, 1)
        FibSettingsLayout.addWidget(rateUnit, 1, 2)
        FibSettingsLayout.addWidget(dwellLabel, 2, 0)
        FibSettingsLayout.addWidget(self.dwellEdit, 2, 1)
        FibSettingsLayout.addWidget(dwellUnit, 2, 2)
        self.settingsGroup.setLayout(FibSettingsLayout)

        self.checkPushButton.setDefault(True)

        self.runPushButton.setCheckable(True)
        self.runPushButton.setChecked(False)

        self.pausePushButton.setCheckable(True)
        self.pausePushButton.setChecked(False)

        self.stopPushButton.setDefault(True)

        self.progressBarLayer.setRange(0, 100)
        self.progressBarLayer.setValue(0)

        self.progressBar.setRange(0, 100)
        self.progressBar.setValue(0)

        ProcessControlLayout = QHBoxLayout()
        ProcessControlLayout.addWidget(self.checkPushButton)
        ProcessControlLayout.addWidget(self.runPushButton)
        ProcessControlLayout.addWidget(self.pausePushButton)
        ProcessControlLayout.addWidget(self.stopPushButton)

        self.runPushButton.clicked.connect(self.runIt)
        self.checkPushButton.clicked.connect(self.measureCurrent)
        self.pausePushButton.clicked.connect(self.pauseIt)
        self.stopPushButton.clicked.connect(self.stopIt)

        ProgressLayout = QVBoxLayout()
        ProgressLayout.addLayout(ProcessControlLayout)
        ProgressLayout.addWidget(self.progressBarLayerLabel)
        ProgressLayout.addWidget(self.progressBarLayer)
        ProgressLayout.addWidget(self.progressBarLabel)
        ProgressLayout.addWidget(self.progressBar)

        self.processGroup.setLayout(ProgressLayout)

        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.settingsGroup)
        mainLayout.addWidget(self.processGroup)

        mainLayout.addStretch(1)
        self.setLayout(mainLayout)

    def pauseIt(self):
        """
        This function is executed after user clicked on 'Pause' button.
        """

        if self.paused:
            self.end = False
            self.paused = False
            self.resume = True
        else:
            self.end = True
            self.paused = True
            self.resume = False

    def stopIt(self):
        """
        This function is executed after user clicked on 'Stop' button.
        """

        self.stoped = True
        self.end = True

    def getPresetList(self):
        """
        Gets the milling preset list.
        """

        if self.parent.connection:
            presets = self.parent.connection.FibListPresets()
            self.parent.connection.logger.debug("Receiving preset list")
            for i in range(0, len(presets)):
                self.millingPreset.removeItem(i)
                self.millingPreset.insertItem(i, presets[i])

    def measureCurrent(self):
        """
        Measures the current and estimates the time of the milling process.
        """

        if self.parent.connection:
            positions = self.parent.PositionsTab.listPositions()
            n = len(positions)

            if n < 1:
                return

            layer = self.parent.ProjectTab.pathValueLabel.text()
            # self.esttime = self.parent.connection.ProcessEstimateTime(layer, self.millingPreset.currentText()) * 6

            self.progressBarLayerLabel.setText("Layer Progress")

            images = int(self.parent.ImageTab.frames.text())
            # dwell = int(self.parent.ImageTab.dwellEdit.text())
            depth = int(self.parent.ProjectTab.repeatEdit.text())

            # print("Images: %s " % int(self.parent.ImageTab.frames.text()))
            # print("Dwell: %s " % float(self.parent.ImageTab.dwellEdit.text()))
            # print("Ref: %s " % (images * (dwell * 0.00475)))
            # print("Depth: %s " % int(self.parent.ProjectTab.repeatEdit.text()))

            # constante = 0.01425 / ((dwell / 100) * (100 % dwell))
            # print("Constante: %s " % constante)

            # total = n * (7 + (images * (dwell * constante)) + (depth * (17 + (images * (dwell * constante)))))
            total = n * (7 + (images * 3) + (depth * (18 + (images * 2.5))))
            self.progressBar.setMaximum(int(total))
            self.progressBarLabel.setText("Overall progress: %.2f s" % total)

    def timeFunction(self):
        """
        Each second increments variables currentValue and currentValueAll. If variable reset is active,
        variable currentValue is changed to 0.
        """

        if self.paused:
            self.pausePushButton.setText("Continue")
            self.stopPushButton.setEnabled(False)
        else:
            self.pausePushButton.setText("Pause")
            self.stopPushButton.setEnabled(True)

        if self.stoped:
            self.afterStop()
            return

        if self.end:
            if self.stoped:
                self.pausePushButton.setEnabled(False)
            self.progressBarLayer.setValue(self.progressBarLayer.maximum())
            self.progressBar.setValue(self.progressBar.maximum())
            return

        images = int(self.parent.ImageTab.frames.text())
        # dwell = int(self.parent.ImageTab.dwellEdit.text())
        # depth = int(self.parent.ProjectTab.repeatEdit.text())

        # constante = 0.01425 / ((dwell / 100) * (100 % dwell))

        if self.currentStatus == 0:
            self.progressBarLayerLabel.setText("SEM image reference for drift correction")
            self.progressBarLayer.setMaximum(7)

        if self.currentStatus == 1:
            self.progressBarLayerLabel.setText("SEM images for DIC reference")
            # self.progressBarLayer.setMaximum(images * (dwell * constante))
            self.progressBarLayer.setMaximum(images * 3)

        if self.currentStatus == 2:
            self.progressBarLayerLabel.setText("FIB milling")
            self.progressBarLayer.setMaximum(5)

        if self.currentStatus == 3:
            self.progressBarLayerLabel.setText("FIB Drift correction")
            self.progressBarLayer.setMaximum(12)

        if self.currentStatus == 4:
            self.progressBarLayerLabel.setText("Images for accumulation")
            self.progressBarLayer.setMaximum(images * 3)

        if not self.reset:
            self.currentValue += 1
        else:
            self.currentValue = 0

        self.currentValueAll += 1

        self.progressBarLayer.setValue(self.currentValue)
        self.progressBar.setValue(self.currentValueAll)

    def openFibLayer(self):
        """
        Runs a FIB xml layer as a separate thread.

        :return: xml
        """

        # Create new thread object.
        filename = self.parent.ProjectTab.pathValueLabel.text()
        self.parent.connection.logger.info("Opening layer %s ..." % filename)
        prj = open(self.parent.ProjectTab.pathValueLabel.text(), "r")
        xml = prj.read()
        prj.close()
        return xml

    def runFibLayer(self, xml):
        """
        Runs a FIB xml layer as a separate thread.

        :param xml: xml file with milling preset
        """

        # Create new thread object.
        selected_preset = self.millingPreset.currentText()

        self.fib_process = FibProcessThread(xml, preset=selected_preset, parent=self.parent)

        # Start new thread.
        self.fib_process.start()

    def AcquireImage(self, filename, SemPreset="None", Note="", Sign=""):
        """
        Acquires an Image as a separate thread.

        :param filename: name of file
        :param SemPreset:
        :param Note:
        :param Sign:
        """

        # Create new thread object.
        width = self.parent.ImageTab.widthEdit.value()
        height = self.parent.ImageTab.heightEdit.value()
        dwell = self.parent.ImageTab.dwellEdit.value()
        pixelsize = self.parent.ImageTab.pixelSize.value()

        SemPreset = self.parent.ImageTab.imagingPreset.currentText()
        if SemPreset != "None":
            self.parent.connection.PresetSet(SemPreset)
            time.sleep(2)

        detector = self.parent.connection.DtGetSelected(0)

        self.img_acquisition = SemImageThread(m_width=width * 1e-6, m_height=height * 1e-6, pixelsize=pixelsize * 1e-9,
                                              detector=detector, bits=16, dwell=dwell, filename=filename,
                                              parent=self.parent, Note=Note, Sign=Sign)

        # Start new thread.
        self.img_acquisition.start()
    def SaveImgHeader(self, pixelsize, filename):
        """
        Saves image *.hdr file compatible with TESCAN software.

        :param pixelsize: pixel size
        :param filename: name of file
        """

        self.connection = self.parent.connection

        MAIN = self.connection.GetDeviceParams(0)
        SEM = self.connection.GetDeviceParams(1)
        hdrfilename = "%s-%s.hdr" % (filename[:-4], filename[-3:])
        hdr = open(hdrfilename, "w")
        hdr.write("[MAIN]\r\n")
        hdr.write(MAIN)
        hdr.write("""PixelSizeX=%.2e\r\nPixelSizeY=%.2e\r\n""" % (pixelsize, pixelsize))
        hdr.write("Note = %s\r\n" % self.Note)
        hdr.write("Sign = %s\r\n" % self.Sign)
        hdr.write("AccDCFA = %i\r\n" % self.AccDCFA)
        hdr.write("AccFrames = %i\r\n" % self.AccDCFA)
        hdr.write("AccType = DCFA\r\n" )
        
        hdr.write("\r\n[SEM]\r\n")
        hdr.write(SEM)
        hdr.close()
        return

    def dcfa_multiframe(self, pixel_dwell=100, N=100, frames=1, detector=0, skip=0,
                        prefix="Image"):
        m_width = self.parent.ImageTab.widthEdit.value()*1e-6 #convert from um to meters
        m_height = self.parent.ImageTab.heightEdit.value()*1e-6 #convert from um to meters
        dwell = self.parent.ImageTab.dwellEdit.value() #dwelltime in nm
        pixelsize = self.parent.ImageTab.pixelSize.value()*1e-9 #convert from nm to meters

        width = math.ceil(m_width / pixelsize)  # image width with correct pixelsize (rounded to whole pixels)
        height = math.ceil(m_height / pixelsize)
        #self.images =0 
        #self.image_no = 0 
        top = 0
        left = 0
        if width >= height:
            viewfield = width * pixelsize
        else:
            viewfield = height * pixelsize

        self.AccDCFA=N
            
        pixelviewfield = math.ceil(viewfield / pixelsize)
        # set teh viewfield to correct value according the pixelsize
        self.parent.connection.logger.debug("Setting the field of view to %.2e um" % viewfield)
        # set teh viewfield to correct value according the pixelsize
        
        self.parent.connection.SetViewField(viewfield * 1e3)# this is in mm =:-o
        
        # start series of image acquisition, acquisition at 100 ns/pxl
        self.parent.connection.ScStopScan()
        self.parent.connection.DtSelect(0, detector)  # select detector #0 into channel #0
        self.parent.connection.DtEnable(0, 1, 16)
        # self.parent.connection.SetWaitFlags(0x2 + 0x4 + 0x8 + 0x20 + 0x40)

        outdir = self.parent.ImageTab.outputDir.text() + "/"
        logfile = open("%s_DCFAlog.csv" % prefix[:-5], "a")
        init_time = time.time()
        self.parent.connection.ScScanXY(0, width, height, 0, 0, width - 1, height - 1, 0, pixel_dwell)
        # skip first x images
        for skim in range(skip):
            # fetch image -i.e. they are scanned but not used
            img_str = self.parent.connection.FetchImageEx((0,), width * height)
            deltime = time.time() - init_time
            logfile.write("%.4fs skipping %i\n" % (deltime, skim))
            self.parent.connection.logger.debug("Stabilizing image %.4fs \n" % (deltime))
            
        #acquiring reference frame for DCFA (same for all images)
        img_str = self.parent.connection.FetchImageEx((0,), width * height)
        deltime = time.time() - init_time
        logfile.write("%s_0000.tif; %.4f; 0; 0; 1; ref\n" % (prefix, deltime))
        self.parent.connection.logger.debug("%s_0000.tif; %.4f; 0; 0; 1; ref\n" % (prefix, deltime))

        img = numpy.fromstring(img_str[0], dtype="uint16").reshape(height, width)

        # img = numpy.fromstring(img_str[0], dtype="uint16").reshape(pxl_w, pxl_h)

        # img = np.frombuffer("I;16", (pxl_w, pxl_h), img_str[0], "raw", "I;16", 0, 1)
        # img.save("%s0000_%04i.tif" % (prefix, 0))

        #cv2.imwrite(outdir + "%s0000_%04i.tif" % (prefix, 0), img)

        # prefix = str(self.images).zfill(4)
        # print("prefix: %s" % prefix)

        # convert image to numpy ndarray and convert to float with values between 0.0 .. 1.0
        first_img_for_acc = np.copy(img) / 65535.0
        #acc_img = np.array(img) / 65535.0

        # print("first_img: %s" % first_img_for_acc)
        # print("acc_img: %s" % acc_img)
        
        
        

        # repeat the averaging for
        for frame in range(frames):
            # fetch the first (reference) image, list of strings containing the pixel data is returned
            # prefix = str(self.images)
            #self.parent.connection.logger.debug("prefix: %s" % prefix)
            #new accumulation
            self.parent.connection.logger.debug("New accumulation")
            acc_img = np.copy(first_img_for_acc) #new copy of first image 
            #cv2.imwrite(outdir + "%s-ACC-REF-%04i_ref.tif" % (prefix, frame), np.uint16(acc_img * 65535.0))
            # number of Images that will be used for accumulation
            noOfAccumulatedImages = 1
            # response statistics
            AvgResponse = 0.0
            self.Note="Depth step%i, frame %i"%(self.depth_step,frame)
            # acquire images
            dx = 0
            dy = 0
            if N==1:   #skip accumulation
               # fetch next image
                img_str = self.parent.connection.FetchImageEx((0,), width * height)
                deltime = time.time() - init_time

                img = np.frombuffer(img_str[0], dtype="uint16").reshape(height, width)
                self.parent.connection.logger.debug("Writing %s_img%04i.%s" % (prefix, self.image_no,self.parent.ImageTab.imgFormat.currentText() ))
                cv2.imwrite(outdir + "%s_img%04i.%s" % (prefix, self.image_no,self.parent.ImageTab.imgFormat.currentText() ), img)
                self.SaveImgHeader(pixelsize, outdir + "%s_img%04i.%s" % (prefix, self.image_no,self.parent.ImageTab.imgFormat.currentText() ))
                self.images += 1
                self.image_no += 1 
            else:
                        
                for i in range(1, N):
                    
                    # fetch next image
                    img_str = self.parent.connection.FetchImageEx((0,), width * height)
                    deltime = time.time() - init_time
    
                    img = np.frombuffer(img_str[0], dtype="uint16").reshape(height, width)
                    
                    #cv2.imwrite(outdir + "%s-ACC-%04i_%04i.tif" % (prefix, frame, i), img)
                    
    
                    imgCV = np.array(img) / 65535.0
    
                    # calculate correlation relative to the reference image
                    p2d = cv2.phaseCorrelate(first_img_for_acc, imgCV, None)
    
                    # last value p2d[1] is so called "response". This variable says how good is phaseCorrelation.
                    # Images with value less than 0.2 are not used.
                    AvgResponse += p2d[1]
    
                    if p2d[1] < 0.1:
                        # print("skipping %i"%i)
                        logfile.write("%s%04i_%04i.tif; %.4f; %.4e; %.4e; %.6f;skipped\n" % (
                            prefix, frame, i, deltime, p2d[0][0], p2d[0][1], p2d[1]))
                        self.parent.connection.logger.debug("%s %04i_%04i.tif; %.4f; %.4e; %.4e; %.6f;skipped" % (
                            prefix, frame, i, deltime, p2d[0][0], p2d[0][1], p2d[1]))
                        continue
    
                    logfile.write("%s%04i_%04i.tif; %.4f; %.4e; %.4e; %.6f;OK\n" % (
                        prefix, frame, i, deltime, p2d[0][0], p2d[0][1], p2d[1]))
                    self.parent.connection.logger.debug("Accumulating %s %04i_%04i; %.4f; %.4e; %.4e; %.6f;OK\n" % (
                        prefix, frame, i, deltime, p2d[0][0], p2d[0][1], p2d[1]))
    
                    # increment image count
    
                    noOfAccumulatedImages += 1
    
                    # displacement
                    dx = p2d[0][0]
                    dy = p2d[0][1]
                    
                    # absolute value of the shift in pixels
                    top = abs(int(round(dy)))
                    bottom = top
                    left = abs(int(round(dx)))
                    right = left
    
                    # DJ idea try subpixel translation instead of cropping
                    # -------------------
                    translation_matrix = np.float32([[1, 0, -dx], [0, 1, -dy]])
                    img_translation = cv2.warpAffine(imgCV, translation_matrix, (width, height))
                    #cv2.imwrite(outdir + "%s-ACC-transl-%04i_%04i.tif" % (prefix, frame, i), np.uint16(img_translation * 65535.0) )
                    cv2.accumulate(img_translation, acc_img)
                #end off accumulation    
                self.parent.connection.logger.debug("Accframes: %i"%noOfAccumulatedImages)
                acc_img = acc_img / noOfAccumulatedImages
    
                # print average response and number of images used for accumulation
                #self.parent.connection.logger.debug("DCFA-Average response: %f s, number of images used for accumulation"%(AvgResponse / (N - 1),noOfAccumulatedImages))                
    
                # im_pil = Image.fromarray(np.uint16(acc_img * 65535.0))
                # im_pil.save("%s_dcfa_%04i.tif" % (prefix, frame))
                img=np.uint16(acc_img * 65535.0)
                self.parent.connection.logger.debug("Writing %s_img%04i.%s" % (prefix, self.image_no,self.parent.ImageTab.imgFormat.currentText() ))
                cv2.imwrite(outdir + "%s_img%04i.%s" % (prefix, self.image_no,self.parent.ImageTab.imgFormat.currentText() ), img)
                self.SaveImgHeader(pixelsize, outdir + "%s_img%04i.%s" % (prefix, self.image_no,self.parent.ImageTab.imgFormat.currentText() ))
                self.images += 1
                self.image_no += 1

        # acquisition completed, stop scanning
        self.parent.connection.ScStopScan()
        # self.parent.connection.SetWaitFlags(0x1 + 0x2 + 0x4 + 0x8 + 0x20 + 0x40)

        # finish
        logfile.close()

    def afterStop(self):
        self.timer.stop()

        # TODO - Unload layer (4)
        self.parent.connection.DrwUnloadLayer(0)

        self.progressBar.setValue(0)
        self.progressBarLayer.setValue(0)
        self.pausePushButton.setEnabled(True)
        self.stopPushButton.setEnabled(True)
        self.runPushButton.setEnabled(True)
        self.checkPushButton.setEnabled(True)

        self.currentValue = 0
        self.currentValueAll = 0

        self.run_thread.join()
        self.stoped = False
        self.end = False

    def resetTime(self):
        self.reset = True
        time.sleep(1)
        self.reset = False

    def runProject(self):
        """
        Runs process. For each position scans images and removes layers.
        """

        # perform a pattern shift correction
        xml1 = self.openFibLayer()

        val = self.rateEdit.value()
        val2 = val * 1.0e-9

        dw = self.dwellEdit.value()
        dw2 = dw * 1.0e-6

        xml2 = self.parent.connection.changeMillingRate(xml1, val2, dw2)
        prj = open(self.parent.ProjectTab.pathValueLabel.text(), "w")
        prj.write(xml2)
        prj.close()

        if self.parent.connection:
            # TODO - STOP pred Run process (3)
            self.parent.connection.GUISetScanning(0)

            # get a list of positions
            positions = self.parent.PositionsTab.listPositions()

            # run a layer for each position
            layer = self.parent.ProjectTab.pathValueLabel.text()
            outdir = self.parent.ImageTab.outputDir.text() + "/"

            for position in positions:
                # 1. Move to the position
                name = position[0]
                x = position[1]
                y = position[2]
                z = position[3]
                rot = position[4]
                tilt = position[5]
                wd = position[6]

                while self.paused:
                    time.sleep(0.1)

                if self.stoped:
                    return

                self.parent.connection.logger.info("""========= %s ============""" % name)
                self.parent.connection.logger.debug(
                    "Moving to %s: %.3e,%.3e,%.3e,%.3e,%.3e; WD= %.3e mm" % (name, x, y, z, rot, tilt, wd))

                self.parent.connection.StgMoveTo(x, y, z, rot, tilt)

                while self.paused:
                    time.sleep(0.1)

                if self.stoped:
                    return

                while self.parent.connection.StgIsBusy():
                    self.parent.statusBar.showMessage("Moving the stage...")
                    QApplication.processEvents()
                    time.sleep(0.5)  # 500 milliseconds sleep

                if not (self.parent.connection.StgIsCalibrated()):
                    self.parent.connection.logger.error("Stage collision!!!")
                    self.parent.statusBar.showMessage("Stage movement crashed, calibration required!!!")
                    QApplication.processEvents()
                else:
                    self.parent.statusBar.showMessage("OK")
                    QApplication.processEvents()

                self.parent.connection.SetWD(wd)

                while self.paused:
                    time.sleep(0.1)

                if self.stoped:
                    return

                # 2. Acquire an image before the milling starts
                self.currentStatus = 0
                self.resetTime()

                # define image list for matlab
                filelist = []

                # TODO - Volat preset (2)
                SemPreset = self.parent.ImageTab.imagingPreset.currentText()
                if SemPreset != "None":
                    self.parent.connection.logger.debug("Changing SEM preset to %s" % (SemPreset))
                    self.parent.connection.PresetSet(SemPreset)
                    time.sleep(2)

                # SEM image reference for drift correction
                self.sem_ref = self.parent.connection.AcquireSEMImageExact(30.0e-6, 10.0e-6, 10.0e-6, 0, 0,
                                                                           pixelsize=10e-9,
                                                                           detector=self.parent.ImageTab.detect.currentIndex(),
                                                                           bits=8, dwell=1000)
                # cv2.imshow("1", self.sem_ref)
                # cv2.waitKey(0)

                while self.paused:
                    time.sleep(0.1)

                if self.stoped:
                    return

                cv2.imwrite(outdir + '%s_SEM_REF.%s' % (name, self.parent.ImageTab.imgFormat.currentText()),
                            self.sem_ref)

                while self.paused:
                    time.sleep(0.1)

                if self.stoped:
                    self.afterStop()
                    return

                # getting initial sem image shift for drift correction
                sem_shiftx, sem_shifty = self.parent.connection.GetImageShift()  # in mm!
                self.parent.connection.logger.debug("Init SEM image shift %.2e , %.2e um" % (sem_shiftx*1e3, sem_shifty*1e3))

                # acquiring SEM images first n frames for DIC reference
                self.image_no = 0  # resetting image counter

                while self.paused:
                    time.sleep(0.1)

                if self.stoped:
                    return

                self.currentStatus = 1
                self.resetTime()

                skipping = 0
                if self.parent.ImageTab.dwellEdit.value() > 1000: 
                    skipping = 0
                else:
                    skipping = round(3000000000.0 / (self.parent.ImageTab.dwellEdit.value() * 1024 * 1024))

                #print("Preskakujem %s obrazkov" % skipping)
                #print("Dwell time je:  %s" % self.parent.ImageTab.dwellEdit.value())
                #print("Pocet obrazkov na acc: %s " % self.parent.ImageTab.acc.value())
                #print("Pocet frames: %s " % self.parent.ImageTab.frames.value())
                #print("Detector: %s " % self.parent.ImageTab.detect.currentIndex())
                self.Sign=name
                self.depth_step=0
                self.dcfa_multiframe(pixel_dwell=self.parent.ImageTab.dwellEdit.value(),
                                     N=self.parent.ImageTab.acc.value(), frames=self.parent.ImageTab.frames.value(),
                                     detector=self.parent.ImageTab.detect.currentIndex(), skip=skipping, prefix=name)

                self.fib_ref = cv2.imread('lib\FIBref10.png', 0)

                # 3. now repeats milling and image acquisition
                for i in range(0, int(self.parent.ProjectTab.repeatEdit.text())):
                    self.depth_step=i+1
                    while self.paused:
                        time.sleep(0.1)

                    if self.stoped:
                        return

                    self.currentStatus = 2
                    self.resetTime()

                    QApplication.processEvents()

                    while self.paused:
                        time.sleep(0.1)

                    if self.stoped:
                        return

                    # 3.1 - acquire a new FIB image for drift correction
                    self.fib_img_tmp = self.parent.connection.AcquireFIBImageExact(26e-6, 6e-6, 6e-6, 0, 0,
                                                                                   pixelsize=10e-9,
                                                                                   detector=0, bits=8, dwell=1000)

                    while self.paused:
                        time.sleep(0.1)

                    if self.stoped:
                        return

                    cv2.imwrite(
                        outdir + '%s_FIB_step%04i.%s' % (name, i + 1, self.parent.ImageTab.imgFormat.currentText()),
                        self.fib_img_tmp)

                    while self.paused:
                        time.sleep(0.1)

                    if self.stoped:
                        self.afterStop()
                        return

                    # 3.1.1 - calculating FIB image shifts
                    # comparing with a reference image of a cross
                    shiftX, shiftY, pxlShiftX, pxlShiftY = self.parent.connection.find_image_shift(self.fib_ref,
                                                                                                   self.fib_img_tmp,
                                                                                                   pixelsize=10e-9)

                    # perform a pattern shift correction
                    xml1 = self.openFibLayer()
                    xml2 = self.parent.connection.shiftLayer(xml1, shiftX, -shiftY)

                    self.runFibLayer(xml2)
                    self.parent.connection.logger.info("===== Milling Layer, step %i======" % (i + 1))

                    while not self.fib_process.isFinished():
                        QApplication.processEvents()
                        time.sleep(0.1)

                    if self.fib_process.isFinished():
                        self.parent.connection.logger.debug("FIB process finished.")

                    self.currentStatus = 3
                    self.resetTime()

                    

                    # TODO - Volat preset (2)
                    SemPreset = self.parent.ImageTab.imagingPreset.currentText()
                    if SemPreset != "None":
                        self.parent.connection.logger.debug("Changing SEM preset to %s" % (SemPreset))
                        self.parent.connection.PresetSet(SemPreset)
                        time.sleep(2)
                        
                    # SEM drift correction before image acquisition    
                    self.parent.connection.logger.info("SEM Drift correction")
                    
                    # return to initial image shift
                    self.parent.connection.SetImageShift(sem_shiftx, sem_shifty)
                    # acquire new image for drift correction
                    self.sem_img = self.parent.connection.AcquireSEMImageExact(30.0e-6, 10.0e-6, 10.0e-6, 0, 0,
                                                                           pixelsize=10e-9,
                                                                           detector=self.parent.ImageTab.detect.currentIndex(),
                                                                           bits=8, dwell=1000)
                    # cv2.imshow("2", self.sem_img)
                    # cv2.waitKey(0)

                    while self.paused:
                        time.sleep(0.1)

                    if self.stoped:
                        return

                    cv2.imwrite(
                        outdir + '%s_SEM_A%04i.%s' % (name, i + 1, self.parent.ImageTab.imgFormat.currentText()),
                        self.sem_img)

                    # calculating image shift
                    new_shiftX, new_shiftY, new_pxlShiftX, new_pxlShiftY = self.parent.connection.find_image_shift(
                        self.sem_ref, self.sem_img, pixelsize=10e-9)  # in m!??

                    while self.paused:
                        time.sleep(0.1)

                    if self.stoped:
                        return

                    # applying image shift 
                    self.parent.connection.logger.debug("Setting SEM image shift %.2e , %.2e um -> %.2e , %.2e um"%(sem_shiftx*1e3,sem_shifty*1e3,(sem_shiftx-new_shiftX*1e3)*1e3,(sem_shifty+new_shiftY*1e3*math.cos(math.radians(55)))*1e3))     
                    self.parent.connection.SetImageShift(sem_shiftx-new_shiftX*1e3,sem_shifty+new_shiftY*math.cos(math.radians(55))*1e3)

                    newshx, newshy = self.parent.connection.GetImageShift()

                    self.parent.connection.logger.debug("New SEM image shift %.2e , %.2e um" % (newshx*1e3, newshy*1e3))

                    # SEM image after drift correction - for debugging purposes only
                    self.sem_img2 = self.parent.connection.AcquireSEMImageExact(30.0e-6, 10.0e-6, 10.0e-6, 0, 0,
                                                                           pixelsize=10e-9,
                                                                           detector=self.parent.ImageTab.detect.currentIndex(),
                                                                           bits=8, dwell=1000)
                    time.sleep(0.1)

                    while self.paused:
                        time.sleep(0.1)

                    if self.stoped:
                        return

                    cv2.imwrite(outdir + '%s_SEM-driftcorrected_A%04i.%s' % (
                    name, i + 1, self.parent.ImageTab.imgFormat.currentText()), self.sem_img2)

                    self.currentStatus = 4
                    self.resetTime()

                    skipping = int(3.0 / self.parent.ImageTab.dwellEdit.value())
                    #print("Preskakujem %s obrazkov" % skipping)
                    #print("Dwell time je:  %s" % self.parent.ImageTab.dwellEdit.value())
                    #print("Pocet obrazkov na acc: %s " % self.parent.ImageTab.acc.value())
                    #print("Pocet frames: %s " % self.parent.ImageTab.frames.value())
                    #print("Detector: %s " % self.parent.ImageTab.detect.currentIndex())
                    self.dcfa_multiframe(pixel_dwell=self.parent.ImageTab.dwellEdit.value(),
                                         N=self.parent.ImageTab.acc.value(), frames=self.parent.ImageTab.frames.value(),
                                         detector=self.parent.ImageTab.detect.currentIndex(), skip=skipping, prefix=name)

                self.parent.connection.logger.info(
                    '''Position %s finished.\n --------------------------------''' % position)

            self.end = True
            self.afterStop()  
            self.parent.connection.logger.info('''Project finished!\n ==================================''' % position)

    def runIt(self):
        """
        Runs thread for computing and timer.
        """

        self.checkPushButton.setEnabled(False)
        self.runPushButton.setEnabled(False)

        self.run_thread = threading.Thread(target=self.runProject)
        self.run_thread.daemon = True
        self.run_thread.start()

        self.timer.start(1000)
