from PyQt5.QtCore import QThread

from lib.DIC_lib import *


class SemImageThread(QThread):
    def __init__(self, m_width, m_height, pixelsize=5e-9, detector=0, bits=16, dwell=200, filename=None, parent=None,
                 Note="", Sign=""):
        """
        Constructor.

        :param m_width: image width in meters
        :param m_height: image height in meters
        :param pixelsize: pixel size in meters
        :param detector: index of the detector same order as in SEM detector list (starting with zero)
        :param bits: bit depth of the image (channel) allowed 8 or 16
        :param dwell: dwell time of the beam in each pixel in nanoseconds
        :param filename: name of file
        :param parent: parent !!!
        :param Note: some note !!!
        :param Sign: some sign !!!
        """

        QThread.__init__(self, parent)

        self.parent = parent
        self.m_width = m_width
        self.m_height = m_height
        self.pixelsize = pixelsize
        self.detector = detector
        self.bits = bits
        self.dwell = dwell
        self.filename = filename
        self.Note = Note
        self.Sign = Sign

    def __del__(self):
        self.wait()

    def AcquireImageExact(self, m_width, m_height, pixelsize=5e-9, detector=0, bits=16, dwell=200):
        """
        A simple function for SEM image acquisition.

        :param m_width: image dimension in meters
        :param m_height: image dimension in meters
        :param pixelsize: pixel size in meters
        :param detector: index of the detector same order as in SEM detector list (starting with zero).
        :param bits: bit depth of the image (channel) allowed 8 or 16
        :param dwell: dwell time of the beam in each pixel in nanoseconds
        :return: image as numpy array
        """

        self.connection = self.parent.connection

        # important: always stop the scanning before we start or before automatic procedures,
        # even before we configure the detectors
        self.connection.ScStopScan()

        # select detector and enable channel
        self.connection.DtSelect(0, detector)  # select detector #0 into channel #0
        self.connection.DtEnable(0, 1, 16)

        singlescan = 1
        width = numpy.math.ceil(m_width / pixelsize)  # image width in pixels with correct pixelsize
        height = numpy.math.ceil(m_height / pixelsize)

        # set the viewfield to correct value according the pixelsize
        if width >= height:
            viewfield = width * pixelsize
        else:
            viewfield = height * pixelsize

        self.connection.logger.debug("setting the field of view to %.4e m" % viewfield)
        self.SetViewField(viewfield * 1e3)
        self.connection.logger.info(
            """Starting acquisition: [%d x %d x %d],detector %d ... wait approx. %.2f s ...""" % (
                width, height, bits, detector, (width * height * dwell * 1e-9 + 1e-3 * height)))

        # TODO - change singlescan to 0 (predposledne)
        self.ScScanXY(0, width, height, 0, 0, width - 1, height - 1, singlescan, dwell)

        # TODO - nepouzijeme StopScan
        # we must stop the scanning even after single scan
        self.ScStopScan()

        self.img_str = self.connection.FetchImageEx([0], width * height)

        if bits == 8:
            self.img_tmp = numpy.fromstring(self.img_str[0], dtype="uint8").reshape(height, width)
        elif bits == 16:
            self.img_tmp = numpy.fromstring(self.img_str[0], dtype="uint16").reshape(height, width)

        # returns image as numpy array
        return self.img_tmp

    def GetImgHeader(self, pixelsize):
        """
        Returns image header as a string.

        :param pixelsize: pixel size
        :return: header
        """

        self.connection = self.parent.connection

        MAIN = self.connection.GetDeviceParams(0)
        SEM = self.connection.GetDeviceParams(1)
        hdr = ""
        hdr = hdr + "[MAIN]\r\n"
        hdr = hdr + MAIN
        hdr = hdr + """PixelSizeX=%.2e\r\nPixelSizeY=%.2e\r\n""" % (pixelsize, pixelsize)
        hdr = hdr + "Note = %s\r\n" % self.Note
        hdr = hdr + "Sign = %s\r\n" % self.Sign
        hdr = hdr + "\r\n[SEM]\r\n"
        hdr = hdr + SEM
        return hdr

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
        hdr.write("\r\n[SEM]\r\n")
        hdr.write(SEM)
        hdr.close()
        return

    def SaveImageExact(self, m_width, m_height, pixelsize=5e-9, detector=0, bits=16, dwell=200, filename="myImage.png"):
        """
        A simple function for SEM image acquisition.

        :param m_width: image dimension in meters
        :param m_height: image dimension in meters
        :param pixelsize: pixel size in meters
        :param detector: index of the detector same order as in SEM  detector list (starting with zero).
        :param bits: bit depth of the image (channel) allowed 8 or 16
        :param dwell: dwell time of the beam in each pixel in nanoseconds
        :param filename: name of file
        """

        self.connection = self.parent.connection
        self.connection.SetWaitFlags(0x09)

        # important: always stop the scanning before we start or before automatic procedures,
        # even before we configure the detectors
        self.connection.ScStopScan()

        # select detector and enable channel
        self.connection.DtSelect(0, detector)  # select detector #0 into channel #0
        self.connection.DtEnable(0, 1, bits)

        # calculate image width with respect to pixelsize
        singlescan = 1
        width = numpy.math.ceil(m_width / pixelsize)  # image width with correct pixelsize
        height = numpy.math.ceil(m_height / pixelsize)

        # set the viewfield to correct value according the pixelsize, in order to reach exact pixelsize
        if width >= height:
            viewfield = width * pixelsize
            pixelfield = width
            self.connection.logger.debug("Setting the viewfield = %.4e m" % viewfield)
        else:
            viewfield = height * pixelsize
            pixelfield = height
            self.connection.logger.info("Setting the field of view to %.4e m" % viewfield)

        self.connection.SetWaitFlags(0x09)
        self.connection.SetViewField(viewfield * 1e3)  # in fact the SharkSEM works with mm !!! - what a mess!
        self.connection.logger.info(
            """Starting acquisition: [%d x %d x %d],detector %d, please ... wait approx. %.2f s""" % (
                width, height, bits, detector, (width * height * dwell * 1e-9 + 1e-3 * height)))
        self.connection.logger.debug("""ScScanXY(%d, %d, %d, %d, %d, %d, %d,%d,%d)""" % (
            0, pixelfield, pixelfield, int(pixelfield / 2 - width / 2), int(pixelfield / 2 - height / 2),
            int(pixelfield / 2 + width / 2 - 1), int(pixelfield / 2 + height / 2 - 1), singlescan, dwell))

        self.connection.ScScanXY(0, pixelfield, pixelfield, int(pixelfield / 2 - width / 2),
                                 int(pixelfield / 2 - height / 2), int(pixelfield / 2 + width / 2 - 1),
                                 int(pixelfield / 2 + height / 2 - 1), singlescan, dwell)

        time.sleep(0.1)
        # we must stop the scanning even after single scan
        self.connection.ScStopScan()

        self.img_str = self.connection.FetchImageEx([0], width * height)

        if bits == 8:
            self.img_tmp = numpy.fromstring(self.img_str[0], dtype="uint8").reshape(height, width)
        elif bits == 16:
            self.img_tmp = numpy.fromstring(self.img_str[0], dtype="uint16").reshape(height, width)

        cv2.imwrite(filename, self.img_tmp)

        self.connection.logger.info('Saving image as %s' % filename)
        self.SaveImgHeader(pixelsize, filename)

        return

    def run(self):
        """
        Runs an image acquisition.
        """

        try:
            if self.filename is None:
                img = self.AcquireImageExact(self.m_width, self.m_height, self.pixelsize, self.detector, self.bits,
                                             self.dwell)
                hdr = self.GetImgHeader(self.pixelsize)
                return img, hdr
            else:
                self.SaveImageExact(self.m_width, self.m_height, self.pixelsize, self.detector, self.bits, self.dwell,
                                    self.filename)
                return

        except KeyboardInterrupt:
            self.connection.logger.error("Keyboard Interrupt")
            self.connection.logger.info("Stopping image acquisition :%i" % (self.connection.ScStopScan()))
            self.terminate()
