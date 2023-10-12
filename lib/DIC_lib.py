#
# SharkSEM Script
# version 2.0.10
#
# # Related Documentation - SharkSEM Remote Control DrawBeam Extension
# Copyright (c) 2012 TESCAN, a.s
# http://www.tescan.com
#

import os, sys
from .SharkSEM import sem_fib, sem

from xml.dom.minidom import parseString, Document
import numpy, math, time
import logging
import cv2


# Set LOGGING
# create logger
class TescanImage():
    def __init__(self, img, hdr):
        """Creates an image object with header textfile"""
        self.img = img
        self.hdr = hdr

    def open(self, filename):
        pass

    def save(self, filename):
        pass


class myLogger(logging.Logger):
    def __init__(self, name, level="Debug"):
        # Filterer.__init__(self)
        self.name = name
        # self.level = _checkLevel(level)
        self.parent = None
        self.propagate = True
        self.handlers = []
        self.disabled = False

        self.setLevel(logging.DEBUG)
        # create console handler and set level to debug
        ch = logging.StreamHandler()
        ch.setLevel(logging.DEBUG)
        # create formatter
        formatter = logging.Formatter('%(asctime)s\t[%(levelname)s]\t %(name)s - %(message)s',
                                      datefmt='%Y-%m-%d %H:%M:%S')
        # add formatter to ch
        ch.setFormatter(formatter)
        # add ch to logger
        self.addHandler(ch)


class FibError(Exception):
    pass


class DrawBeamError(Exception):
    """A general exception for parsing DrawBeam Errors"""

    def __init__(self, value):
        self.value = value
        self.error = {}
        self.error[-1] = "INVALID_REQ"
        self.error[-2] = "GIS_NOT_READY"
        self.error[-3] = "MEMORY"
        self.error[-4] = "VISIBILITY"
        self.error[-5] = "LICENSE"
        self.error[-6] = "EMISSION"
        self.error[-7] = "VIEW_FIELD"
        self.error[-100] = "UNKNOWN"

    def __str__(self):
        return self.error[self.value]


class myFibSem(sem_fib.SemFib):
    def __init__(self, fib_ip="localhost", logger=None):
        """Initialization and direct connection to FIB"""
        # connect to FIB
        self.connection = sem.sem_conn.SemConnection()
        self.logger = logger
        if self.logger is None:
            self.startLogging("AutoDIC")

        self.logger.info("Connecting FIB at %s:8300 ..." % fib_ip)
        res = self.Connect(fib_ip, 8300)
        if res < 0:
            self.logger.error("Unable to connect SEM/FIB at %s:8300" % fib_ip)
            raise FibError("Unable to connect SEM/FIB at %s:8300" % fib_ip)
        else:
            self.logger.info("FIB connected at %s:8300" % fib_ip)

        self.FLAGS = {"SEM_scanning": 0x1, "SEM_stage": 0x2, "SEM_optics": 0x4, "SEM_automatics": 0x8,
                      "FIB_scanning": 0x10, "FIB_optics": 0x20, "FIB_automatics": 0x40, "A": 0x1, "B": 0x2, "C": 0x4,
                      "D": 0x8, "E": 0x10, "F": 0x20, "G": 0x40}
        # set wait flags to wait for all SEM+FIB
        self.logger.debug("Setting Flags to wait for all:0x1+0x2+0x4+0x8+0x20+0x40")
        self.GUISetScanning(0)
        # self.SetWaitFlags(0x1 + 0x2 + 0x4 + 0x8 + 0x20 + 0x40)

    def startLogging(self, name):
        self.logger = logging.getLogger(name)
        if not self.logger.hasHandlers():
            self.logger.setLevel(logging.DEBUG)
            fh = logging.FileHandler('./AutoDIC.log', mode='w')
            fh.setLevel(logging.DEBUG)
            # create console handler and set level to debug
            ch = logging.StreamHandler()
            ch.setLevel(logging.DEBUG)

            # create formatter
            formatter = logging.Formatter(fmt='%(asctime)s\t[%(levelname)s]\t %(name)s - %(message)s',
                                          datefmt='%Y-%m-%d %H:%M:%S')

            # add formatter 
            fh.setFormatter(formatter)
            ch.setFormatter(formatter)

            # add fh, ch to logger
            self.logger.addHandler(fh)
            self.logger.addHandler(ch)

        return

    def __exit__(self, type, value, traceback):
        """Destructor - automatically disconnects when object is deleted"""
        self.logger.info("Disconnecting %s ..." % self.fib_ip)
        self.connection.Disconnect()

    def checkFibCfg(self):
        """checks FIB settings and status"""

        if self.FibHVGetBeam():
            self.logger.info("Ion Beam is ON")
        else:
            raise FibError("Ion Beam is OFF")

        cfg = self.DrwGetConfig()
        if cfg == 0:
            self.logger.error("DrawBeam not installed")
            raise FibError("DrawBeam not installed")
        elif cfg == 1:
            self.logger.error("DrawBeam offline only")
            raise FibError("DrawBeam offline only")
        elif cfg == 2:
            self.logger.debug("DrawBeam Basic installed")
        elif cfg == 3:
            self.logger.debug("DrawBeam Advanced installed")
        elif cfg == 4:
            self.logger.error("DrawBeam installed, but license is not valid")
            # raise FibError("DrawBeam installed, but license is not valid")

        self.logger.info("I-beam scanning is busy : %i" % (self.IsBusy(12)))
        self.logger.info("I-beam optics is busy : %i" % (self.IsBusy(13)))
        self.logger.info("I-beam automated precedure is busy : %i" % (self.IsBusy(14)))

    def FibListPresets(self):
        return self.FibEnumPresets().split("\n")

    def SemListPresets(self):
        return self.PresetEnum().split("\n")

    def runFibLayer(self, filename, preset="2. Fine milling, polishing"):
        """Runs an DrawBeam external xml layer according to SharkSEM Remote Control
    DrawBeam Extension"""
        # open layer
        self.logger.info("Opening layer %s ..." % filename)
        prj = open(filename, "r")
        xml = prj.read()
        prj.close()
        layer = parseString(xml)
        # get settings from xml layer
        settings = layer.getElementsByTagName("Settings")[0]
        # set view field
        wf = float(settings.getAttribute("WriteFieldSize"))  # in meters
        self.logger.info("Setting write field to %.1f um" % (wf * 1e6))
        self.FibSetViewField(wf * 1e3)  # conversion to mm
        self.checkFibCfg()

        # check if preset exists
        presets = self.FibListPresets()
        if presets.count(preset) > 0:
            self.logger.info("changing preset to : %s" % preset)
            self.FibSetPreset(preset)
        else:
            raise FibError("The FIB preset: %s doesn't exist" % preset)

        FCC = self.FibReadFCCurr()  # in pA
        self.logger.info("Faraday cup current = %f pA" % FCC)

        # update beam current in xml project to actual value for time estimation correction
        if FCC <= 0:
            # in demo mode no current detected - 100pA set in such a case
            self.logger.info("Demo mode detected,FC current increased 100x to value = %e pA" % (
                    float(settings.getAttribute("BeamCurrent")) * 100 * 1e12))
            settings.setAttribute("BeamCurrent", "%e" % (float(settings.getAttribute("BeamCurrent")) * 100))
        else:
            logger.info("Beam current=0. Updating layer current current from %s A to %.2e A" % (
                settings.getAttribute("BeamCurrent"), FCC * 1e-12))
            settings.setAttribute("BeamCurrent", "%.2e" % (FCC * 1e-12))
        # generating updated xml
        xml = layer.toxml()
        print(xml)
        # print("DrawBeam Status:",self.DrwGetStatus())
        # logger.info("Unloading layer with status: %i" % self.DrwUnloadLayer(0))
        self.logger.info("Loading layer %s into DrawBeam with status:%i" % (filename[:-4], self.DrwLoadLayer(0, xml)))
        self.logger.debug("Any previous process is stopped ?? with status:%i" % (self.DrwStop()))
        self.logger.info("Layer started with status:%i" % (self.DrwStart(0)))
        status = self.DrwGetStatus()
        self.logger.info("Drawbeam Status:%i" % (status[0]))
        while status[0] == 2:
            try:
                self.logger.debug(
                    """Layer %s Running: Time: %.2f s / %.2f s ()""" % (filename[:-4], status[2], status[1]))
                time.sleep(1)
                status = self.DrwGetStatus()
                if status[0] == 1:
                    self.logger.debug("Layer %s Finished" % (filename[:-4]))
                else:
                    self.logger.debug("Drawbeam Status:%i" % (status[0]))
                    time.sleep(0.5)
            except KeyboardInterrupt:
                logger.error("Keyboard Interrupt")
                logger.info("Process stopped with status:%i" % (self.DrwStop()))
                logger.info("Unloading layer with status:", self.DrwUnloadLayer(0))

    def startFibLayer(self, filename, preset="2. Fine milling, polishing"):
        """Runs an DrawBeam external xml layer according to SharkSEM Remote Control
    DrawBeam Extension"""
        # open layer
        self.logger.info("Opening layer %s ..." % filename)
        prj = open(filename, "r")
        xml = prj.read()
        prj.close()
        layer = parseString(xml)
        # get settings from xml layer
        settings = layer.getElementsByTagName("Settings")[0]
        # set view field
        wf = float(settings.getAttribute("WriteFieldSize"))  # in meters
        self.logger.info("Setting write field to %.1f um" % (wf * 1e6))
        self.FibSetViewField(wf * 1e3)  # conversion to mm
        self.checkFibCfg()

        # check if preset exists
        presets = self.FibListPresets()
        if presets.count(preset) > 0:
            self.logger.info("changing preset to : %s" % preset)
            self.FibSetPreset(preset)
        else:
            raise FibError("The FIB preset: %s doesn't exist" % preset)

        FCC = self.FibReadFCCurr()  # in pA
        self.logger.info("Faraday cup current = %f pA" % FCC)

        # update beam current in xml project to actual value for time estimation correction
        if FCC <= 0:
            # in demo mode no current detected - 100pA set in such a case
            self.logger.info("Demo mode detected,FC current increased 100x to value = %e pA" % (
                    float(settings.getAttribute("BeamCurrent")) * 100 * 1e12))
            settings.setAttribute("BeamCurrent", "%e" % (float(settings.getAttribute("BeamCurrent")) * 100))
        else:
            logger.info("Beam current=0. Updating layer current current from %s A to %.2e A" % (
                settings.getAttribute("BeamCurrent"), FCC * 1e-12))
            settings.setAttribute("BeamCurrent", "%.2e" % (FCC * 1e-12))
        # generating updated xml
        xml = layer.toxml()
        # print(xml)
        # print("DrawBeam Status:",self.DrwGetStatus())
        # logger.info("Unloading layer with status: %i" % self.DrwUnloadLayer(0))
        self.logger.info("Loading layer %s into DrawBeam with status:%i" % (filename[:-4], self.DrwLoadLayer(0, xml)))
        self.logger.debug("Any previous process is stopped ?? with status:%i" % (self.DrwStop()))
        self.logger.info("Layer started with status:%i" % (self.DrwStart(0)))
        status = self.DrwGetStatus()
        self.logger.info("Drawbeam Status:%i" % (status[0]))

    def ProcessEstimateTime(self, filename, preset="2. Fine milling, polishing"):
        """Measures the beam current and returns a time estimation  of DrawBeam external xml layer"""
        # open layer
        self.logger.info("Opening layer %s ..." % filename)
        prj = open(filename, "r")
        xml = prj.read()
        prj.close()
        layer = parseString(xml)
        # get settings from xml layer
        settings = layer.getElementsByTagName("Settings")[0]
        # set view field
        self.checkFibCfg()
        # check if preset exists
        presets = self.FibListPresets()
        if presets.count(preset) > 0:
            self.logger.info("changing preset to : %s" % preset)
            self.FibSetPreset(preset)
        else:
            raise FibError("The FIB preset: %s doesn't exist" % preset)

        FCC = self.FibReadFCCurr()  # in pA
        self.logger.info("Faraday cup current = %f pA" % FCC)
        # update beam current in xml project to actual value for time estimation correction
        if FCC <= 0:
            # in demo mode no current detected - 100pA set in such a case
            self.logger.info("Demo mode detected,FC current increased 10x to value = %e pA" % (
                    float(settings.getAttribute("BeamCurrent")) * 10 * 1e12))
            settings.setAttribute("BeamCurrent", "%e" % (float(settings.getAttribute("BeamCurrent")) * 10))
        else:
            self.logger.info("Beam current=0. Updating layer current current from %s A to %.2e A" % (
                settings.getAttribute("BeamCurrent"), FCC * 1e-12))
            settings.setAttribute("BeamCurrent", "%.2e" % (FCC * 1e-12))
        # generating updated xml
        xml = layer.toxml()
        self.logger.info("Unloading any previous layer with status:%i" % self.DrwUnloadLayer(0))
        self.logger.info("Loading layer %s into DrawBeam with status:%i" % (filename[:-4], self.DrwLoadLayer(0, xml)))
        # returns estimate time in seconds
        esttime = self.DrwEstimateTime(0)
        print(esttime)
        self.logger.info("Unloading layer with status %i", self.DrwUnloadLayer(0))
        # self.logger.debug("Estimated time for one layer milling:%i s"%(esttime))
        return esttime[1]

    def processStatus(self):
        """Checks the status of the running process."""
        status = self.DrwGetStatus()
        self.logger.info("Drawbeam Status:%i" % (status[0]))
        if status[0] == 2:
            self.logger.debug("""Layer %s Running: Time: %.2f s / %.2f s ()""" % (filename[:-4], status[2], status[1]))
        elif status[0] == 1:
            self.logger.debug("Layer %s Finished" % (filename[:-4]))
        else:
            self.logger.debug("Drawbeam Status:%i" % (status[0]))
        return status

    def processStop(self):
        self.logger.debug("Any previous process is stopped ?? with status:%i" % (self.DrwStop()))
        status = self.DrwGetStatus()
        return status

    def processPause(self):
        self.logger.debug("Any previous process is stopped ?? with status:%i" % (self.DrwPause()))
        status = self.DrwGetStatus()
        return status

    def processResume(self):
        self.logger.debug("Any previous process is stopped ?? with status:%i" % (self.DrwResume()))
        status = self.DrwGetStatus()
        return status

    def AcquireImageExact(self, um_width, um_height, pixelsize=5e-9, detector=0, bits=16, dwell=200):
        """A simple function for SEM image acquisition.
        width, height - image dimensions in pixels
        detector - index of the detector same order as in SEM  detector list (starting with zero).
        bits -  bit depth of the image (channel) allowed 8 or 16
        dwell - dwell time of the beam in each pixel in nanoseconds"""

        # important: always stop the scanning before we start or before automatic procedures,
        # even before we configure the detectors
        self.ScStopScan()
        # select detector and enable channel
        self.DtSelect(0, detector)  # select detector #0 into channel #0
        self.DtEnable(0, 1, 16)
        # start single frame acquisition at speed 3
        singlescan = 1
        width = math.ceil(um_width / pixelsize)  # image width with correct pixelsize
        height = math.ceil(um_height / pixelsize)
        # set teh viewfield to correct value according the pixelsize
        if width >= height:
            viewfield = width * pixelsize
        else:
            viewfield = height * pixelsize
        self.logger.debug("setting the field of view to %.2e um" % viewfield)
        self.SetViewField(viewfield * 1e3)
        self.logger.info("""Starting acquisition: [%d x %d x %d],detector %d
        wait approx. %.2f s ...""" % (width, height, bits, detector, (width * height * dwell * 1e-9 + 1e-3 * height)))
        self.ScSetSpeed(4)
        self.ScScanXY(0, width, height, 0, 0, width - 1, height - 1, singlescan)
        # we must stop the scanning even after single scan
        self.ScStopScan()
        img_str = self.FetchImage(0, width * height)
        img = numpy.fromstring(img_str, dtype="uint16").reshape(height, width)
        # returns image as numpy array
        return img

    def AcquireFIBImageExact(self, viewfield, m_width, m_height, m_top, m_left, pixelsize=5e-9, detector=0, bits=8,
                             dwell=2e-9):
        """A simple function for FIB image acquisition.
        width, height - image dimensions in pixels
        detector - index of the detector same order as in SEM  detector list (starting with zero).
        bits -  bit depth of the image (channel) allowed 8 or 16
        dwell - dwell time of the beam in each pixel in nanoseconds"""

        # important: always stop the scanning before we start or before automatic procedures,
        # even before we configure the detectors
        self.FibScStopScan()
        self.ScStopScan()
        # select detector and enable channel
        self.FibDtEnable(0, 1, 8)  # enables channel 0 at 16 bits
        # start single frame acquisition at speed 3
        singlescan = 1
        width = math.ceil(m_width / pixelsize)  # image width with correct pixelsize
        height = math.ceil(m_height / pixelsize)
        top = math.ceil(m_top / pixelsize)
        left = math.ceil(m_left / pixelsize)
        pixelviewfield = math.ceil(viewfield / pixelsize)
        # set teh viewfield to correct value according the pixelsize
        self.FibSetViewField(viewfield * 1e3)
        self.logger.info("Setting the FIB field of view to %.2e um" % viewfield)
        self.logger.info("""Starting FIB image acquisition: [%d x %d x %d],detector %d wait approx. %.2f s ...""" % (
            width, height, bits, detector, (width * height * dwell * 1e-9 + 1e-3 * height)))
        self.FibScSetSpeed(3)
        self.logger.debug(
            """FibScScanXY(channel=%i,width=%i,height=%i,left=%i, top=%i, right=%i,bottom=%i, singlescan=%i)""" % (
                0, pixelviewfield, pixelviewfield, left, top, left + width - 1, top + height - 1, singlescan))
        self.FibScScanXY(0, pixelviewfield, pixelviewfield, left, top, left + width - 1, top + height - 1, singlescan,
                         dwell)
        # we must stop the scanning even after single scan
        num = height * width
        img_str = self.FibFetchImage(0, width * height)
        # self.FibScStopScan()
        img = numpy.fromstring(img_str, dtype="uint8").reshape(height, width)
        return img

    # drift correction functions
    def AcquireSEMImageExact(self, viewfield, m_width, m_height, m_top, m_left, pixelsize=5e-9, detector=0, bits=16,
                             dwell=2e-9):
        """A simple function for FIB image acquisition.
        width, height - image dimensions in pixels
        detector - index of the detector same order as in SEM  detector list (starting with zero).
        bits -  bit depth of the image (channel) allowed 8 or 16
        dwell - dwell time of the beam in each pixel in nanoseconds"""

        # important: always stop the scanning before we start or before automatic procedures,
        # even before we configure the detectors
        self.FibScStopScan()
        self.ScStopScan()
        
        # select detector and enable channel
        self.logger.debug("Enabling detector %i in %i bits" % (detector,bits))
        self.DtSelect(0, detector)
        self.DtEnable(0, 1, bits)  # enables channel 0 at 16 bits
        
        # start single frame acquisition at speed 3
        singlescan = 1
        width = math.ceil(m_width / pixelsize)  # image width with correct pixelsize
        height = math.ceil(m_height / pixelsize)
        top = math.ceil(m_top / pixelsize)
        left = math.ceil(m_left / pixelsize)
        pixelviewfield = math.ceil(viewfield / pixelsize)
        # set teh viewfield to correct value according the pixelsize
        self.logger.debug("Setting the field of view to %.2e um" % viewfield)
        self.SetViewField(viewfield * 1e3)
        self.logger.debug(
            """ScScanXY(channel=%i,width=%i,height=%i,left=%i, top=%i, right=%i,bottom=%i, singlescan=%i,dwelltime=%4f)""" % (
                0, pixelviewfield, pixelviewfield, left, top, left + width - 1, top + height - 1, singlescan,dwell))
        self.ScScanXY(0, pixelviewfield, pixelviewfield, left, top, left + width - 1, top + height - 1, singlescan,
                      dwell)
        # we must stop the scanning even after single scan
        self.logger.debug("Fetching image %ix%i"%(width ,height))
        img_str = self.FetchImageEx((0,), width * height)
        self.logger.debug("Image fetched")
        self.ScStopScan()
        num = height * width

        img = numpy.frombuffer(img_str[0], dtype="uint%i"%bits).reshape(height, width)
        #img = img / (2**bits) #converting to float image ??
        return img

    def find_image_shift_phasecorr(self, ref, img, pixelsize=1):
        """Calculates an image shift of the image relative to the reference image.
        Assuming that both images have the same pixel size...
        """

        ref_numpy = numpy.float32(ref)
        img_numpy = numpy.float32(img)

        p2d = cv2.phaseCorrelate(ref_numpy, img_numpy, None)

        x = p2d[0][0]
        y = p2d[0][1]
        self.logger.debug("""OpenCV phaseCorrelate: \n%s""" % (repr(p2d)))

        RX, RY = ref.shape
        IX, IY = img.shape
        shiftX = x + RX / 2 - IX / 2
        shiftY = y + RY / 2 - IY / 2
        pxlShiftX = x + RX / 2
        pxlShiftY = y + RY / 2
        self.logger.debug("""Image Shift Calculation:""")
        self.logger.debug("  template size =[%i,%i]" % ref.shape)
        self.logger.debug("  image size =[%i,%i]" % img.shape)
        self.logger.debug("  center = [%i,%i]" % (pxlShiftX, pxlShiftY))
        self.logger.debug("  pixel shift = [%.2e,%.2e]" % (shiftX, shiftY))
        self.logger.debug("  shift = [%.2e,%.2e]" % (shiftX * pixelsize, shiftY * pixelsize))
        return shiftX * pixelsize, shiftY * pixelsize, pxlShiftX, pxlShiftY

    def find_image_shift(self, ref, img, pixelsize=1):
        """Calculates an image shift of the image relative to the reference image.
        Assuming that both images have the same pixel size...
        """
        width, height = ref.shape

        ref = ref[int(width / 2.5):-int(width / 2.5), int(height / 2.5):-int(height / 2.5)]

        norm_cross_corr = cv2.matchTemplate(ref, img,
                                            cv2.TM_CCOEFF_NORMED)  # raplacing the Scikit-Image template matching

        # get subpixel resolution from cross correlation
        subpixel = True
        [xpeak, ypeak, stdx, stdy, corrcoef, info] = self.findpeak(norm_cross_corr, subpixel)
        self.logger.debug("Cross correlation using template matching:")
        self.logger.debug("Pixelshift [%.4f,%.4f]" % (xpeak, ypeak))
        self.logger.debug("ImageShift [%.4f,%.4f]" % (xpeak * pixelsize, ypeak * pixelsize))
        self.logger.debug("Std [%.4f,%.4f]" % (stdx, stdy))
        self.logger.debug("CorrCoef %.4f]" % (corrcoef))
        self.logger.debug("Info %s]" % (info))
        # plt.imshow(norm_cross_corr)
        # plt.plot(xpeak, ypeak, "r+")
        # plt.show()
        RX, RY = ref.shape
        IX, IY = img.shape
        shiftX = xpeak + RX / 2 - IX / 2
        shiftY = ypeak + RY / 2 - IY / 2
        # shiftX=norm_cross_corr.shape[0]
        pxlShiftX = xpeak + RX / 2
        pxlShiftY = xpeak + RY / 2
        self.logger.debug("""Image Shift Calculation:""")
        self.logger.debug("  template size =[%i,%i]" % ref.shape)
        self.logger.debug("  image size =[%i,%i]" % img.shape)
        self.logger.debug("  center = [%.4f,%.4f]" % (pxlShiftX, pxlShiftY))
        self.logger.debug("  pixel shift = [%.4f,%.4f]" % (shiftX, shiftY))
        self.logger.debug("  shift = [%.2e,%.2e]" % (shiftX * pixelsize, shiftY * pixelsize))
        return shiftX * pixelsize, shiftY * pixelsize, pxlShiftX, pxlShiftY

    def correlate(self, img1, img2):
        image_product = numpy.fft.fft2(img1) * numpy.fft.fft2(img2).conj()
        cc_image = numpy.fft.fftshift(numpy.fft.ifft2(image_product))

        cc_image_norm = numpy.zeros(cc_image.real.shape)
        cv2.normalize(cc_image.real, cc_image_norm, 0, 1, cv2.NORM_MINMAX)
        # cv2.imshow("a",cc_image_norm)
        # cv2.waitKey(0)
        r = cv2.minMaxLoc(cc_image_norm)

        center = (img2.shape[1] // 2, img2.shape[0] // 2)

        return (center[0] - r[3][0], center[1] - r[3][1])

    def find_image_shift_SEM(self, ref, img, pixelsize=1):
        """Calculates an image shift of the image relative to the reference image.
        Assuming that both images have the same pixel size...
        """
        width, height = ref.shape

        ref_converted = numpy.float32(ref)/256
        img_converted = numpy.float32(img)/256

        norm_cross_corr = cv2.matchTemplate(ref_converted, img_converted,
                                            cv2.TM_CCOEFF_NORMED)  # raplacing the Scikit-Image template matching

        # result = self.correlate(ref_converted, img_converted)

        # get subpixel resolution from cross correlation
        subpixel = True
        [xpeak, ypeak, stdx, stdy, corrcoef, info] = self.findpeak(norm_cross_corr, subpixel)
        self.logger.debug("Cross correlation using template matching:")
        self.logger.debug("Pixelshift [%.4f,%.4f]" % (xpeak, ypeak))
        self.logger.debug("ImageShift [%.4f,%.4f]" % (xpeak * pixelsize, ypeak * pixelsize))
        self.logger.debug("Std [%.4f,%.4f]" % (stdx, stdy))
        self.logger.debug("CorrCoef %.4f]" % (corrcoef))
        self.logger.debug("Info %s]" % (info))
        # plt.imshow(norm_cross_corr)
        # plt.plot(xpeak, ypeak, "r+")
        # plt.show()
        RX, RY = ref.shape
        IX, IY = img.shape
        shiftX = xpeak + RX / 2 - IX / 2
        shiftY = ypeak + RY / 2 - IY / 2
        # shiftX=norm_cross_corr.shape[0]
        pxlShiftX = xpeak + RX / 2
        pxlShiftY = xpeak + RY / 2
        self.logger.debug("""Image Shift Calculation:""")
        self.logger.debug("  template size =[%i,%i]" % ref.shape)
        self.logger.debug("  image size =[%i,%i]" % img.shape)
        self.logger.debug("  center = [%.4f,%.4f]" % (pxlShiftX, pxlShiftY))
        self.logger.debug("  pixel shift = [%.4f,%.4f]" % (shiftX, shiftY))
        self.logger.debug("  shift = [%.2e,%.2e]" % (shiftX * pixelsize, shiftY * pixelsize))
        return shiftX * pixelsize, shiftY * pixelsize, pxlShiftX, pxlShiftY

    def findpeak(self, f, subpixel):
        """Peak finding with sub pixel accuracy by 2D polynomial fit (quadratic)"""
        stdx = 1e-4
        stdy = 1e-4

        # Get absolute peak pixel

        max_f = numpy.amax(f)
        [xpeak, ypeak] = numpy.unravel_index(f.argmax(), f.shape)  # coordinates of the maximum value in f

        if subpixel == False or xpeak == 0 or xpeak == numpy.shape(f)[0] - 1 or ypeak == 0 or ypeak == numpy.shape(f)[
            1] - 1:  # on edge
            # print 'CpCorr : No Subpixel Adjustement.'
            return ypeak, xpeak, stdx, stdy, max_f, 0  # return absolute peak

        else:
            # fit a 2nd order polynomial to 9 points
            # using 9 pixels centered on irow,jcol
            u = f[xpeak - 1:xpeak + 2, ypeak - 1:ypeak + 2]
            u = numpy.reshape(numpy.transpose(u), (9, 1))
            x = numpy.array([-1, 0, 1, -1, 0, 1, -1, 0, 1])
            y = numpy.array([-1, -1, -1, 0, 0, 0, 1, 1, 1])
            x = numpy.reshape(x, (9, 1))
            y = numpy.reshape(y, (9, 1))

            # u(x,y) = A(0) + A(1)*x + A(2)*y + A(3)*x*y + A(4)*x^2 + A(5)*y^2
            X = numpy.hstack((numpy.ones((9, 1)), x, y, x * y, x ** 2, y ** 2))
            # u = X*A

            # A = numpy.linalg.lstsq(X,u, rcond=1e-1)
            A = numpy.linalg.lstsq(X, u, rcond=1e-20)

            e = A[1]  # residuals returned by Linalg Lstsq
            A = numpy.reshape(A[0], (6, 1))  # A[0] array of least square solution to the u = AX equation

            # get absolute maximum, where du/dx = du/dy = 0
            x_num = (-A[2] * A[3] + 2 * A[5] * A[1])
            y_num = (-A[3] * A[1] + 2 * A[4] * A[2])

            den = (A[3] ** 2 - 4 * A[4] * A[5])
            x_offset = x_num / den
            y_offset = y_num / den

            # print x_offset, y_offset
            if numpy.absolute(x_offset) > 1 or numpy.absolute(y_offset) > 1:
                # print 'CpCorr : Subpixel outside limit. No adjustement'
                # adjusted peak falls outside set of 9 points fit,
                return ypeak, xpeak, stdx, stdy, max_f, 1  # return absolute peak

            # x_offset = numpy.round(10000*x_offset)/10000
            # y_offset = numpy.round(10000*y_offset)/10000
            x_offset = numpy.around(x_offset, decimals=4)
            y_offset = numpy.around(y_offset, decimals=4)

            xpeak = xpeak + x_offset
            ypeak = ypeak + y_offset
            # print xpeak, ypeak

            # calculate residuals
            # e=u-numpy.dot(X,A)

            # calculate estimate of the noise variance
            n = 9  # number of data points
            p = 6  # number of fitted parameters
            var = numpy.sum(e ** 2) / (n - p)

            # calculate covariance matrix
            cov = numpy.linalg.inv(numpy.dot(numpy.transpose(X), X)) * var
            # produce vector of std deviations on each term
            s = numpy.sqrt([cov[0, 0], cov[1, 1], cov[2, 2], cov[3, 3], cov[4, 4], cov[5, 5]])
            # Calculate standard deviation of denominator, and numerators
            if A[1] == 0 or A[2] == 0 or A[3] == 0 or A[4] == 0 or A[
                5] == 0:  # avoid divide by zero error and invalid value
                # print 'CpCorr : Div. by 0 error escaped.'
                return ypeak, xpeak, stdx, stdy, max_f, 2  # return absolute peak
            else:
                x_num_std = numpy.sqrt(
                    4 * A[5] ** 2 * A[1] ** 2 * ((s[5] / A[5]) ** 2 + (s[1] / A[1]) ** 2) + A[2] ** 2 * A[3] ** 2 * (
                            (s[2] / A[2]) ** 2 + (s[3] / A[3]) ** 2))
                den_std = numpy.sqrt(
                    16 * A[4] ** 2 * A[5] ** 2 * ((s[4] / A[4]) ** 2 + (s[5] / A[5]) ** 2) + 2 * s[3] ** 2 * A[3] ** 2)
                y_num_std = numpy.sqrt(
                    4 * A[4] ** 2 * A[2] ** 2 * ((s[4] / A[4]) ** 2 + (s[2] / A[2]) ** 2) + A[3] ** 2 * A[1] ** 2 * (
                            (s[3] / A[3]) ** 2 + (s[1] / A[1]) ** 2))

            # Calculate standard deviation of x and y positions
            stdx = numpy.sqrt(x_offset ** 2 * ((x_num_std / x_num) ** 2 + (den_std / den) ** 2))
            stdy = numpy.sqrt(y_offset ** 2 * ((den_std / den) ** 2 + (y_num_std / y_num) ** 2))

            # Calculate extremum of fitted function
            max_f = numpy.dot([1, x_offset, y_offset, x_offset * y_offset, x_offset ** 2, y_offset ** 2], A)
            max_f = numpy.absolute(max_f)

        return ypeak, xpeak, stdx, stdy, max_f, 0

    def changeMillingRate(self, xml, value, dwell):
        layer = parseString(xml)

        objects = layer.getElementsByTagName("Settings")
        for dbobject in objects:
            dbobject.setAttribute("Rate", "%e" % value)
            dbobject.setAttribute("DwellTime", "%e" % dwell)

        xml2 = layer.toxml()
        return xml2

    def shiftLayer(self, xml, shift_x, shift_y):
        """Applies a pattern shift for drift correction"""
        self.logger.info("Shifting the patterns by [%e, %e]..." % (shift_x, shift_y))
        layer = parseString(xml)
        # self.logger.debug(xml)
        # shifting the common objects
        objects = layer.getElementsByTagName("Object")
        for dbobject in objects:
            C1X, C1Y = dbobject.getAttribute("Center").split()
            C2X = float(C1X) + shift_x
            C2Y = float(C1Y) + shift_y
            dbobject.setAttribute("Center", "%e %e" % (C2X, C2Y))

        polypoints = layer.getElementsByTagName("Vertex")
        for point in polypoints:
            C1X, C1Y = point.getAttribute("Position").split()
            C2X = float(C1X) + shift_x
            C2Y = float(C1Y) + shift_y
            point.setAttribute("Position", "%e %e" % (C2X, C2Y))

        xml2 = layer.toxml()
        # self.logger.debug(xml2)
        return xml2


if __name__ == '__main__':

    depth = 50  # nm
    myLyra = myFibSem()
    myLyra.GUISetScanning(1)
    img = myLyra.AcquireImageExact(um_width=10e-6, um_height=10e-6, pixelsize=10e-9, detector=0)
    imgMAG = myLyra.AcquireImageExact(um_width=5e-6, um_height=5e-6, pixelsize=5e-9, detector=0)
    myLyra.logger.info("Image acquisition finished")

    cv2.imwrite('Si10umA%04i.TIF' % 0, img)
    cv2.imwrite('Si5umA%04i.TIF' % 0, imgMAG)

    myLyra.logger.info('Saving SiA%04i' % (0))

    for i in range(1, 50):
        myLyra.GUISetScanning(1)
        myLyra.runFibLayer("ringcore2_5um\\milling.xml", "4. Deposition, imaging")
        img = myLyra.AcquireImageExact(um_width=10e-6, um_height=10e-6, pixelsize=10e-9, detector=0)
        imgMAG = myLyra.AcquireImageExact(um_width=5e-6, um_height=5e-6, pixelsize=5e-9, detector=0)

        cv2.imwrite('Si10umA%04i.TIF' % i, img)
        cv2.imwrite('Si5umA%04i.TIF' % i, imgMAG)

        logger.info('Saving SiA%04i' % i)
        # img.show()
