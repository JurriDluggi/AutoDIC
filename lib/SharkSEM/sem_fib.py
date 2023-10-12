#
# SharkSEM Script
# version 2.0.22
#
# Copyright (c) 2015 TESCAN Brno, s.r.o.
# http://www.tescan.com
#

import os.path
import sys
remote_dir = os.path.abspath("../remote")
sys.path.append(remote_dir)

import struct
from . import sem
from . import sem_conn

#
# FIB - Lyra
#
class SemFib(sem.Sem):

    def FibFetchImage(self, channel, size):
        return self.connection.FetchImage('FibScData', channel, size)

    def FibEnumOptPars(self):
        return self.connection.RecvString('FibEnumOptPars')

    def FibGetOptParam(self, index):
        return self.connection.Recv('FibGetOptParam', (sem_conn.ArgType.Float, sem_conn.ArgType.Float), self._CInt(index))

    def FibReadFCCurr(self):
        return self.connection.RecvFloat('FibReadFCCurr')

    def FibGetViewField(self):
        return self.connection.RecvFloat('FibGetViewField')

    def FibSetViewField(self, vf):
        self.connection.Send('FibSetViewField', self._CFloat(vf))
        
    def FibDtAutoSig(self, channel):
        self.connection.Send('FibDtAutoSig', self._CInt(channel))

    def FibDtGetGainBl(self, detector):
        return self.connection.Recv('FibDtGetGainBl', (sem_conn.ArgType.Float, sem_conn.ArgType.Float), self._CInt(detector))

    def FibDtSetGainBl(self, detector, gain, black):
        self.connection.Send('FibDtSetGainBl', self._CInt(detector), self._CFloat(gain), self._CFloat(black))

    def FibDtEnable(self, channel, enable, bpp = -1):
        if (bpp == -1):
            self.connection.Send('FibDtEnable', self._CInt(channel), self._CInt(enable))
        else:
            self.connection.Send('FibDtEnable', self._CInt(channel), self._CInt(enable), self._CInt(bpp))

    def FibDtGetChann(self):
        return self.connection.RecvInt('FibDtGetChann')
    
    def FibScEnumSpeeds(self):
        return self.connection.RecvString('FibScEnumSpeeds')
       
    def FibScGetSpeed(self):
        return self.connection.RecvInt('FibScGetSpeed')

    # frameid, width, height, left, top, right, bottom, single <, dwell>
    def FibScScanXY(self, *arg):
        if len(arg) == 8:
            return self.connection.RecvInt('FibScScanXY', self._CUnsigned(arg[0]), self._CUnsigned(arg[1]), self._CUnsigned(arg[2]), self._CUnsigned(arg[3]), self._CUnsigned(arg[4]), self._CUnsigned(arg[5]), self._CUnsigned(arg[6]), self._CInt(arg[7]))
        if len(arg) == 9:
            return self.connection.RecvInt('FibScScanXY', self._CUnsigned(arg[0]), self._CUnsigned(arg[1]), self._CUnsigned(arg[2]), self._CUnsigned(arg[3]), self._CUnsigned(arg[4]), self._CUnsigned(arg[5]), self._CUnsigned(arg[6]), self._CInt(arg[7]), self._CUnsigned(arg[8]))

    def FibScSetSpeed(self, speed):
        self.connection.Send('FibScSetSpeed', self._CInt(speed))

    def FibScStopScan(self):
        self.connection.Send('FibScStopScan')

    def FibHVGetVoltage(self):
        return self.connection.RecvFloat('FibHVGetVoltage')

    def FibHVGetFilTime(self):
        return self.connection.RecvFloat('FibHVGetFilTime')

    def FibHVGetBeam(self):
        return self.connection.RecvInt('FibHVGetBeam')

    def FibHVBeamOn(self):
        self.connection.Send('FibHVBeamOn')

    def FibHVBeamOff(self):
        self.connection.Send('FibHVBeamOff')

    def FibScGetExtern(self):
        return self.connection.RecvInt('FibScGetExtern')
    
    def FibScSetExtern(self, enable):
        self.connection.Send('FibScSetExtern', self._CInt(enable))

    def FibEnumPresets(self):
        return self.connection.RecvString('FibEnumPresets')
        
    def FibSetPreset(self, preset):
        self.connection.Send('FibSetPreset', self._CString(preset))

    def FibEnumGeom(self):
        return self.connection.RecvString('FibEnumGeom')

    def FibGetGeom(self, index):
        return self.connection.Recv('FibGetGeom', (sem_conn.ArgType.Float, sem_conn.ArgType.Float), self._CInt(index))

    def FibSetGeom(self, index, x, y):
        self.connection.Send('FibSetGeom', self._CInt(index), self._CFloat(x), self._CFloat(y))

    def FibEnumCent(self):
        return self.connection.RecvString('FibEnumCent')

    def FibGetCent(self, index):
        return self.connection.Recv('FibGetCent', (sem_conn.ArgType.Float, sem_conn.ArgType.Float), self._CInt(index))

    def FibSetCent(self, index, x, y):
        self.connection.Send('FibSetCent', self._CInt(index), self._CFloat(x), self._CFloat(y))
