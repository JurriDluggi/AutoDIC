#
# SharkSEM Script - test application
# version 2.0.19
#
# This application requires:
#   
#   Python 3.x (tested with 3.3)
#   Pillow (imaging)
#
# Copyright (c) 2014 TESCAN Brno, s.r.o.
# http://www.tescan.com
#

import time
import sem
from PIL import Image

def main():
    m = sem.Sem()
    
    # you can change the 'localhost' string and provide another SEM addres
    res = m.Connect('localhost', 8300)    
    
    if res < 0:
        print("Error: unable to connect")
        return

    # we can read some parameter
    print('wd: ', m.GetWD())
    
    # tuple is returned if the function has more output arguments
    print('stage position: ', m.StgGetPosition())
    
    # let us take a look at the detector configuration
    print(m.DtEnumDetectors())
    
    # set the Probe Current - this is equivalent to BI in SEM Generation 3
    m.SetPCIndex(10)
    
    # important: stop the scanning before we start scanning or before automatic procedures,
    # even before we configure the detectors
    m.ScStopScan()

    # select detector and enable channel
    # example scenario: use channel 0 (det 0, 8-bit) and channel 2 (det 1, 16-bit)
    # note that FetchImageEx() and Image.frombuffer() must be called in the corresponding way    
    m.DtSelect(0, 0)
    m.DtEnable(0, 1, 8)
    m.DtSelect(2, 1)
    m.DtEnable(2, 1, 16)
    
    # now tell the engine to wait for scanning inactivity and auto procedure finish,
    # see the docs for details
    m.SetWaitFlags(0x09)
    
    # adjust brigtness and contrast of cahnnel 0, read back the result
    m.DtAutoSignal(0)
    print('gain/black: ', m.DtGetGainBlack(0))
    
    # start single frame acquisition at 1000 ns/pxl
    pxl_w = 512
    pxl_h = 512
    m.ScScanXY(0, pxl_w, pxl_h, 0, 0, pxl_w - 1, pxl_h - 1, 1, 1000)
    
    # fetch the image (blocking operation), list of strings containing the pixel data is returned
    img_str = m.FetchImageEx((0, 2, ), pxl_w * pxl_h)
    
    # we must stop the scanning even after single scan
    m.ScStopScan()
    
    # create and save the images (only here the 'Image' library is required)
    img = Image.frombuffer("L", (pxl_w, pxl_h), img_str[0], "raw", "L", 0, 1)           # 8-bit grayscale
    img.save('img-ch-0.png')
    img = Image.frombuffer("I;16", (pxl_w, pxl_h), img_str[1], "raw", "I;16", 0, 1)     # 16-bit grayscale
    img.save('img-ch-1.tiff')

    # finish
    m.Disconnect()

if __name__ == '__main__':
    main()
