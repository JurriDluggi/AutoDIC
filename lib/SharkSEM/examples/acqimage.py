#!c:/python33/python

#
# Acquire 16-bit SEM image and save it to TIFF file.
#
# Usage:
#   acqimage.py <filename> <scanning speed>
#
# Example
#   acqimage.py sample01.tiff 3
#
# Process retrun code 0 - failed, 1 - success.
#
# Scanning speed table - G2 SEM manufactured till 2009.
#   1   0.2 us
#   2   0.6 us
#   3   1.8 us
#   4   5.4 us
#   ...      
#
# This application requires:
#   
#   Python 3.3
#   Pillow (imaging)
#
# Copyright (c) 2015 TESCAN Brno, s.r.o.
# http://www.tescan.com
#

import sys
from PIL import Image
import sem

# defines
SEM_ADDR = 'localhost'      # local PC
DETECTOR = 0                # index 0, usually SE 
PXL_W = 768                 # image dimensions
PXL_H = 768

# main
def main():
    m = sem.Sem()
    
    # check command line
    if len(sys.argv) != 3:
        print("acqimage.py <filename> <scanning speed>")
        return 0
        
    filename = sys.argv[1]
    scan_speed = int(sys.argv[2])
    
    # you can change the 'localhost' string and provide another SEM addres
    res = m.Connect(SEM_ADDR, 8300)    
    if res < 0:
        print("Error: unable to connect")
        return 0

    # stop the scanning before we go ahead
    m.ScStopScan()

    # select detector, enable 16-bit acquisition
    m.DtSelect(0, 0)
    m.DtEnable(0, 1, 16)
    
    # start single frame acquisition
    m.ScSetSpeed(scan_speed)    
    m.ScScanXY(0, PXL_W, PXL_H, 0, 0, PXL_W - 1, PXL_H - 1, 1)
    
    # fetch the image (blocking operation), list of strings containing the pixel data is returned
    img_str = m.FetchImageEx((0, ), PXL_W * PXL_H)
    
    # we must stop the scanning even after single scan
    m.ScStopScan()
    
    # create and save the images (only here the 'Image' library is required)
    img = Image.frombuffer("I;16", (PXL_W, PXL_H), img_str[0], "raw", "I;16", 0, 1)     # 16-bit grayscale
    img.save(filename)

    # finish
    m.Disconnect()

    return 1

if __name__ == '__main__':
    res = main()
    sys.exit(res)
