#
# Tescan air lock test (type 2 - motorized)
#
# This application requires:
#   
#   Python 3.x (tested with 3.3)
#
# Copyright (c) 2014 TESCAN Brno, s.r.o.
# http://www.tescan.com
#

import sem
import tkinter
import tkinter.messagebox


#
# global definitions
#

SERVER_IP = "127.0.0.1"         # TESCAN SEM

#
# table of states
#
arl_s_txt = {}
arl_s_txt[-2] = "RALS2_NOT_INSTALLED"
arl_s_txt[-1] = "RALS2_ERROR"
arl_s_txt[0] = "RALS2_POS_OUTSIDE"
arl_s_txt[1] = "RALS2_POS_INSIDE"
arl_s_txt[2] = "RALS2_POS_STOPPED"
arl_s_txt[10] = "RALS2_PROC_PUMPING"
arl_s_txt[11] = "RALS2_PROC_LOADING"
arl_s_txt[12] = "RALS2_PROC_UNLOADING"
arl_s_txt[13] = "RALS2_PROC_VENTING"
arl_s_txt[14] = "RALS2_POS_RECOVERY"

#
# main dialog
#
class MainDlg:

    #
    # constructor - create the dialog
    #
    def __init__(self, root, arg_sem):

        # SEM
        self.mSem = arg_sem
        
        # form
        self.mRoot = root
        self.mNoBtn = 0
        
        # burn-in
        self.mBurn = 0
        self.mBurnPhase = 0

        # arrange widgets by grid manager
        self.mFrame = tkinter.Frame(root)
        self.mFrame.grid()

        # status
        self.mStatus1 = tkinter.Label(self.mFrame)
        self.mStatus1.grid(row=self.mNoBtn, column=0)
        self.mNoBtn = self.mNoBtn + 1

        self.mStatus2 = tkinter.Label(self.mFrame)
        self.mStatus2.grid(row=self.mNoBtn, column=0)
        self.mNoBtn = self.mNoBtn + 1
        self.mStatus2Bg = self.mStatus2.cget("bg")

        # add buttons
        self.BtnAdd("Stop Movement", self.CmdMoveStop)
        self.mBtnPump = self.BtnAdd("Pump", self.CmdPump)
        self.BtnAdd("Vent", self.CmdVent)
        self.BtnAdd("Load", self.CmdLoad)
        self.BtnAdd("Unload", self.CmdUnload)
        self.BtnAdd("Calibrate", self.CmdCalibrate)
        self.BtnAdd("Recovery", self.CmdRecovery)
        self.mBtnBurn = self.BtnAdd("Start Burn-in", self.CmdBurnIn)
        
        # update status, schedule timer
        self.UpdateStatus()
        
        # burn-in timer
        self.mRoot.after(1000, self.BurnTimer)

        # initial focus
        self.mBtnPump.focus_force()
        
    #
    # add button into list
    #
    def BtnAdd(self, label, fn):
        btn = tkinter.Button(self.mFrame)
        btn.configure(text=label, width=32)
        btn.bind("<ButtonRelease-1>", fn)
        btn.bind("<space>", fn)
        btn.grid(row=self.mNoBtn, column=0, padx=20, pady=6)
        self.mNoBtn = self.mNoBtn + 1
        return btn 

    #
    # handlers
    #
    def CmdBurnIn(self, event):
        if not self.mBurn:
            res = tkinter.messagebox.askyesno("Air Lock Burn-in", "Please make sure that:\n - chamber is evacuated\n - stage is calibrated\n - there is no sample inside\n - load lock vented\n\nDo you want to start the burn-in procedure?", default=tkinter.messagebox.NO)
            if res:
                self.mBtnBurn.configure(text = "Stop Burn-in")
                self.mBurn = 1
        else:
            self.mBtnBurn.configure(text = "Start Burn-in")
            self.mBurn = 0

    def CmdMoveStop(self, event):
        self.mSem.Arl2MoveStop()

    def CmdRecovery(self, event):
        self.mSem.Arl2Recovery()

    def CmdCalibrate(self, event):
        self.mSem.Arl2Calibrate()

    def CmdLoad(self, event):
        self.mSem.Arl2Load()

    def CmdUnload(self, event):
        self.mSem.Arl2Unload()

    def CmdPump(self, event):
        self.mSem.Arl2Pump()

    def CmdVent(self, event):
        self.mSem.Arl2Vent()

    #
    # update and show status (called periadically)
    #
    def UpdateStatus(self):

        # update status
        (status_arl, status_arl_detailed) = self.mSem.Arl2GetStatus()
        status_ups = self.mSem.GetUPSStatus()
        msg = "Status: %s (%d)\nDetailed Status: %d\nUPS Status: %d\n" % (arl_s_txt[status_arl], status_arl, status_arl_detailed, status_ups)
        self.mStatus1.configure(text=msg)
        msg = "      Burn-in: %d      " % (self.mBurn)
        self.mStatus2.configure(text=msg)
        if self.mBurn:
            self.mStatus2.configure(bg="#FF8080")
        else:
            self.mStatus2.configure(bg=self.mStatus2Bg)
            

        # schedule next invocation
        self.mRoot.after(500, self.UpdateStatus)

    #
    # burn-in
    #
    def BurnTimer(self):
    
        # only if burn is ON
        if self.mBurn:

            # current status    
            (status_arl, status_arl_detailed) = self.mSem.Arl2GetStatus()
    
            # state change
            if (status_arl == 0):
                self.mSem.Arl2Pump()
            elif (status_arl == 1) and (self.mBurnPhase == 0):
                self.mSem.Arl2Load()
                self.mBurnPhase = 1
            elif (status_arl == 1) and (self.mBurnPhase == 1):
                self.mSem.Arl2Unload()
                self.mBurnPhase = 2
            elif (status_arl == 1) and (self.mBurnPhase == 2):
                self.mSem.Arl2Vent()
                self.mBurnPhase = 0
            
        # schedule next invocation
        self.mRoot.after(1000, self.BurnTimer)

#
# app main
#

# connect
m = sem.Sem()
res = m.Connect(SERVER_IP, 8300)
if res < 0:
    tkinter.messagebox.showerror("SEM Connect", "Error: SEM does not respond.")
    sys.exit()

# main dialog
root = tkinter.Tk()
root.title("Air Lock Test")
MainDlg(root, m)
root.mainloop()

# TCP/IP communication sync
m.TcpGetVersion()
