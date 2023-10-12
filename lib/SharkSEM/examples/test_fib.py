#
# SharkSEM Script
# version 2.0.6
#
# Dertived from test.py, this is FIB test suite
#
# Copyright (c) 2010 TESCAN, s.r.o.
# http://www.tescan.com
#

import time
import sem_fib
from PIL import Image

def main():
    m = sem_fib.SemFib()
    
    # you can change the 'localhost' string and provide another SEM addres
    res = m.Connect('localhost', 8300)    
    if res < 0:
        print("Error: unable to connect")
        return
   
    # vief field
    vf = m.FibGetViewField()
    print("view field=%f" % vf)
    m.FibSetViewField(vf / 2)
    vf = m.FibGetViewField()
    print("view field=%f" % vf)
    
    # speed
    print(m.FibScEnumSpeeds())
    spd = m.FibScGetSpeed()
    print("speed=%d" % spd)
    m.FibScSetSpeed(spd + 1)
    spd = m.FibScGetSpeed()
    print("speed=%d" % spd)
    
    # get channels
    print("no channels=%d" % m.FibDtGetChann())
    
    # optical parameters
    print(m.FibEnumOptPars())
    print("optical parameter 0")
    print(m.FibGetOptParam(0))
    print("optical parameter 1")
    print(m.FibGetOptParam(1))
    print("optical parameter 2")
    print(m.FibGetOptParam(2))
    
    # faraday cup current
    print("faraday cup current = %f pA" % m.FibReadFCCurr())
    
    # scanning
    m.FibDtEnable(0, 1, 8)
    m.FibScSetSpeed(3)
    m.FibScScanXY(0, 512, 512, 0, 0, 511, 511, 1)
    
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
