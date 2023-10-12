from PyQt5.QtCore import QThread, QMutex, QWaitCondition

from lib.DIC_lib import *


class FibProcessThread(QThread):
    def __init__(self, xml, preset="2. Fine milling, polishing", parent=None):
        """
        Constructor.

        :param xml: xml text
        :param preset: preset
        :param parent: parent
        """

        QThread.__init__(self, parent)

        self.preset = preset
        self.parent = parent
        self.xml = xml

    def __del__(self):
        self.wait()

    def run(self):
        """
        Runs an DrawBeam external xml layer in a new thread according to SharkSEM Remote Control DrawBeam Extension.
        """

        self.connection = self.parent.connection

        # parsing the xml text
        layer = parseString(self.xml)

        # get settings from xml layer
        self.settings = layer.getElementsByTagName("Settings")[0]

        # set view field
        wf = float(self.settings.getAttribute("WriteFieldSize"))  # in meters

        self.connection.logger.info("Setting write field to %.1f um" % (wf * 1e6))
        self.connection.FibSetViewField(wf * 1e3)  # conversion to mm

        while self.parent.ProcessTab.paused:
            time.sleep(0.1)

        # check if fib is ready
        self.connection.checkFibCfg()

        # check if preset exists
        presets = self.connection.FibListPresets()
        if presets.count(self.preset) > 0:
            self.connection.logger.info("changing preset to : %s" % self.preset)
            self.connection.FibSetPreset(self.preset)
        else:
            raise FibError("The FIB preset: %s doesn't exist" % self.preset)

        FCC = self.connection.FibReadFCCurr()  # in pA
        self.connection.logger.info("Faraday cup current = %f pA" % FCC)

        # update beam current in xml project to actual value for time estimation correction
        if FCC <= 0:
            # in demo mode no current detected - 100pA set in such a case
            self.connection.logger.info("Demo mode detected,FC current increased 100x to value = %e pA" % (
                    float(self.settings.getAttribute("BeamCurrent")) * 100 * 1e12))
            self.settings.setAttribute("BeamCurrent", "%e" % (float(self.settings.getAttribute("BeamCurrent")) * 100))
        else:
            self.connection.logger.info("Beam current=0. Updating layer current from %s A to %.2e A" % (
                    self.settings.getAttribute("BeamCurrent"), FCC * 1e-12))
            self.settings.setAttribute("BeamCurrent", "%.2e" % (FCC * 1e-12))

        while self.parent.ProcessTab.paused:
            time.sleep(0.1)

        

        # generating updated xml text
        xml = layer.toxml()
        self.connection.logger.debug(xml)
        self.connection.logger.info("Unloading layer with status: %i" % self.connection.DrwUnloadLayer(0))
        self.connection.logger.info("Loading layer into DrawBeam with status:%i" % (
                self.connection.DrwLoadLayer(0, xml)))
        self.connection.logger.debug("Any previous process is stopped ?? with status:%i" % (self.connection.DrwStop()))
        self.connection.logger.info("Layer started with status:%i" % (self.connection.DrwStart(0)))

        status = self.connection.DrwGetStatus()

        self.connection.logger.info("Drawbeam thread Status:%i" % (status[0]))

        while status[0] == 2 or status[0] == 3:  # means layer is running or paused
            while self.parent.ProcessTab.paused:
                time.sleep(0.1)

            try:
                self.connection.logger.debug("""Layer progress: Time: %.2f s / %.2f s ()""" % (status[2], status[1]))
                time.sleep(0.2)
                status = self.connection.DrwGetStatus()

                if status[0] == 1:  # layer finished
                    self.connection.logger.debug("Drawbeam Status: Layer Finished")
                    # self.terminate()

                if status[0] == 3:
                    self.connection.logger.debug("Drawbeam Status: Layer paused")
                    time.sleep(1)
                else:
                    self.connection.logger.debug("Drawbeam Status: running")
                    time.sleep(0.5)

            except KeyboardInterrupt:
                self.connection.logger.error("Keyboard Interrupt")
                self.connection.logger.info("Layer stopped with status:%i" % (self.connection.DrwStop()))
                self.connection.logger.info("Unloading layer with status:", self.connection.DrwUnloadLayer(0))
                self.terminate()
