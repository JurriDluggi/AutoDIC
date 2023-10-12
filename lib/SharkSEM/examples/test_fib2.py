#
# SharkSEM Script
# version 2.0.6
#
# This application requires:
#   
#   Python 2.5 (tested with 2.5.2)
#   PIL - Python Imaging Library
#
# Copyright (c) 2010 TESCAN, s.r.o.
# http://www.tescan.com
#

import time
import sys
sys.path.append("../remote")
import sem_fib
import Image

def main():
    m = sem_fib.SemFib()
    
    # you can change the 'localhost' string and provide another SEM addres
    res = m.Connect('localhost', 8300)    
    
    if res < 0:
        print("Error: unable to connect")
        return

    m.FibScStopScan()

    # start single frame acquisition at speed 3
    m.FibScSetSpeed(3)
    m.FibScScanXY(0, 512, 512, 0, 0, 511, 511, 1, 20)
    
    # fetch the image (blocking operation), string is returned
    img_str = m.FibFetchImage(0, 512 * 512)
    
    # we must stop the scanning even after single scan
    m.FibScStopScan()
    
    # save it in a file (only here the 'Image' library is required)
    img = Image.fromstring("L", (512, 512), img_str)
    img.save('python image.png')

    # finish
    m.Disconnect()

if __name__ == '__main__':
    main()
