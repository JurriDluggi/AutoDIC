#
# SEM EBL field navigation
#
# This application requires:
#   
#   Python 3.x (tested with 3.3)
#
# Copyright (c) 2014 TESCAN Brno, s.r.o.
# http://www.tescan.com
#

import tkinter
import tkinter.messagebox
import tkinter.filedialog
import sem

# max number of X (Y) fields
MAX_WIDTH_OR_HEIGHT = 20

# spacing limits (mm)
MIN_SPACING = 0.001
MAX_SPACING = 10.0

################################################################################################
#
# stage motion progress dialog
#

class DlgStgMove:

    def __init__(self, parent, scheme, sem):
        self.m_Sem = sem
        self.m_Parent = parent

        # label        
        ctl = tkinter.Label(parent, text="Stage in motion, please wait...", font=scheme['font'])
        ctl.grid(row=0, column=0, padx=100, pady=100)

        # timer
        parent.after(500, self.CheckStage)        
    
        # modal
        parent.grab_set()
        parent.wait_window(parent)
        
    def CheckStage(self):
        res = self.m_Sem.StgIsBusy()
        if res != 0:
            self.m_Parent.after(500, self.CheckStage)
        else:
            self.m_Parent.destroy()
        

################################################################################################
#
# XY field mesh generator
#

class DlgCreateXY:

    #
    # constructor - create the dialog
    #
    def __init__(self, parent, scheme, lst):
    
        # save args
        self.m_Parent = parent
        self.m_Coord = lst
        
        # result (0 - ignore result, 1 - accept result)
        self.result = 0
        
        # color scheme
        self.m_Scheme = scheme
        
        # Nx
        self.m_Nx = tkinter.IntVar()
        self.m_Nx.set(1)
        ctl = tkinter.Label(parent, text="Number of horizontal fields", font=self.m_Scheme['font'])
        ctl.grid(row=0, column=0, padx=5, pady=5, sticky=tkinter.E)
        ctl = tkinter.Entry(parent, textvariable=self.m_Nx, font=self.m_Scheme['font'], bg=self.m_Scheme['editvalcolor'])
        ctl.grid(row=0, column=1, padx=5, pady=5)
        first_edit = ctl

        # Ny
        self.m_Ny = tkinter.IntVar()
        self.m_Ny.set(1)
        ctl = tkinter.Label(parent, text="Number of vertical fields", font=self.m_Scheme['font'])
        ctl.grid(row=1, column=0, padx=5, pady=5, sticky=tkinter.E)
        ctl = tkinter.Entry(parent, textvariable=self.m_Ny, font=self.m_Scheme['font'], bg=self.m_Scheme['editvalcolor'])
        ctl.grid(row=1, column=1, padx=5, pady=5)

        # Dx
        self.m_Dx = tkinter.DoubleVar()
        self.m_Dx.set(0.5)
        ctl = tkinter.Label(parent, text="Delta X", font=self.m_Scheme['font'])
        ctl.grid(row=2, column=0, padx=5, pady=5, sticky=tkinter.E)
        ctl = tkinter.Entry(parent, textvariable=self.m_Dx, font=self.m_Scheme['font'], bg=self.m_Scheme['editvalcolor'])
        ctl.grid(row=2, column=1, padx=5, pady=5)
        ctl = tkinter.Label(parent, text="mm", font=self.m_Scheme['font'])
        ctl.grid(row=2, column=2, padx=5, pady=5, sticky=tkinter.W)

        # Dy
        self.m_Dy = tkinter.DoubleVar()
        self.m_Dy.set(0.5)
        ctl = tkinter.Label(parent, text="Delta Y", font=self.m_Scheme['font'])
        ctl.grid(row=3, column=0, padx=5, pady=5, sticky=tkinter.E)
        ctl = tkinter.Entry(parent, textvariable=self.m_Dy, font=self.m_Scheme['font'], bg=self.m_Scheme['editvalcolor'])
        ctl.grid(row=3, column=1, padx=5, pady=5)
        ctl = tkinter.Label(parent, text="mm", font=self.m_Scheme['font'])
        ctl.grid(row=3, column=2, padx=5, pady=5, sticky=tkinter.W)

        # origin
        self.m_SelOrigin = tkinter.StringVar()
        self.m_SelOrigin.set("tl")
        ctl = tkinter.Radiobutton(parent, variable=self.m_SelOrigin, value="tl", text="Start from the top left field", font=self.m_Scheme['font'])
        ctl.grid(row=4, column=0, columnspan=3, padx=5, pady=5, sticky=tkinter.W)
        ctl = tkinter.Radiobutton(parent, variable=self.m_SelOrigin, value="bl", text="Start from the bottom left field", font=self.m_Scheme['font'])
        ctl.grid(row=5, column=0, columnspan=3, padx=5, pady=5, sticky=tkinter.W)
        
        # OK button
        self.m_CtlGoPrev = tkinter.Button(parent, width=30, text="Done", font=self.m_Scheme['font'], command=self.onOK)
        self.m_CtlGoPrev.grid(row = 6, column = 0, columnspan=3, padx=5, pady=5)
        
        # modal
        first_edit.focus_set()
        first_edit.selection_range(0, tkinter.END)
        self.m_Parent.grab_set()
        self.m_Parent.wait_window(self.m_Parent)

    #
    # OK handler
    #
    def onOK(self):
    
        # sanity checks
        try:
            nx = self.m_Nx.get()
            if (nx < 1) or (nx > MAX_WIDTH_OR_HEIGHT):
                tkinter.messagebox.showwarning("Error", "X field count must be between 1 and %d" % (MAX_WIDTH_OR_HEIGHT), parent=self.m_Parent)
                return

            ny = self.m_Ny.get()
            if (ny < 1) or (ny > MAX_WIDTH_OR_HEIGHT):
                tkinter.messagebox.showwarning("Error", "Y field count must be between 1 and %d" % (MAX_WIDTH_OR_HEIGHT), parent=self.m_Parent)
                return
                
            dx = self.m_Dx.get()
            if (dx < MIN_SPACING) or (dx > MAX_SPACING):
                tkinter.messagebox.showwarning("Error", "X spacing must be between %g mm and %g mm" % (MIN_SPACING, MAX_SPACING), parent=self.m_Parent)
                return

            dy = self.m_Dy.get()
            if (dy < MIN_SPACING) or (dy > MAX_SPACING):
                tkinter.messagebox.showwarning("Error", "Y spacing must be between %g mm and %g mm" % (MIN_SPACING, MAX_SPACING), parent=self.m_Parent)
                return

        except:
            tkinter.messagebox.showwarning("Error", "Invalid numeric value", parent=self.m_Parent)
            return
        
        # fill-in the list
        self.m_Coord.clear()
        for row in range (0, nx):
            for col in range (0, ny):
                if self.m_SelOrigin.get() == "tl": 
                    self.m_Coord.append([0.0 - 1.0 * col * dx, row * dy])
                else:                
                    self.m_Coord.append([0.0 - 1.0 * col * dx, 0.0 - 1.0 * row * dy])
        
        # done
        self.result = 1
        self.m_Parent.destroy()


################################################################################################
#
# main dialog class
#

class MainDlg:

    #
    # constructor - create the dialog
    #
    def __init__(self, root, sem):
    
        # save args
        self.m_Root = root
        self.m_Sem = sem
        
        # list of coordinates
        self.m_Coord = []
        
        # current field index
        self.m_CurrentField = 0
        
        # reference positon
        self.m_RefStageX = 0.0
        self.m_RefStageY = 0.0
        
        # color scheme
        self.m_Scheme = {'font':"arial 12", 'editvalcolor':"#80FFC0"}

        # field list
        self.m_FFields = tkinter.LabelFrame(root, text="Field coordinates (relative)", font=self.m_Scheme['font'])
        self.m_FFields.grid(row = 0, column = 0, padx=5, pady=5, sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        
        self.m_FList = tkinter.Frame(self.m_FFields)
        self.m_FList.grid(row=0, column=0, padx=5, pady=5, sticky=tkinter.W+tkinter.N+tkinter.S+tkinter.E) 

        self.m_FButtons = tkinter.Frame(self.m_FFields)
        self.m_FButtons.grid(row=0, column=1, padx=5, pady=5, sticky=tkinter.N+tkinter.E+tkinter.S+tkinter.W)
        
        self.m_CtlVScroll = tkinter.Scrollbar(self.m_FList, orient=tkinter.VERTICAL)
        self.m_CtlVScroll.grid(row=0, column=1, pady=5, sticky=tkinter.N + tkinter.S)
        
        self.m_CtlList = tkinter.Listbox(self.m_FList, height=16, activestyle=tkinter.NONE, yscrollcommand=self.m_CtlVScroll.set, font=self.m_Scheme['font'])
        self.m_CtlList.grid(row = 0, column = 0, pady=5, sticky=tkinter.W+tkinter.N+tkinter.S+tkinter.E)
        
        self.m_CtlVScroll.config(command = self.m_CtlList.yview)
        
        self.m_CtlGenXY = tkinter.Button(self.m_FButtons, width=30, text="Create regular XY mesh", font=self.m_Scheme['font'], command=self.onGenerateXYMesh)
        self.m_CtlGenXY.grid(row = 0, column = 1, pady=5, sticky=tkinter.N+tkinter.E)

        self.m_CtlLoadCSV = tkinter.Button(self.m_FButtons, width=30, text="Load coordinates from CSV", font=self.m_Scheme['font'], command=self.onLoadCSV)
        self.m_CtlLoadCSV.grid(row = 1, column = 1, pady=5, sticky=tkinter.N+tkinter.E)

        self.m_CtlClearAll = tkinter.Button(self.m_FButtons, width=30, text="Clear all", font=self.m_Scheme['font'], command=self.onClearAll)
        self.m_CtlClearAll.grid(row = 2, column = 1, pady=5, sticky=tkinter.N+tkinter.E)

        # navigation
        self.m_FNavi = tkinter.LabelFrame(root, text="Navigation", font=self.m_Scheme['font'])
        self.m_FNavi.grid(row = 1, column = 0, padx=5, pady=5, sticky=tkinter.W+tkinter.E+tkinter.N+tkinter.S)
        
        self.m_CtlDefineFirst = tkinter.Button(self.m_FNavi, width=30, text="Set origin (first field position)", font=self.m_Scheme['font'], command=self.onDefineFirst)
        self.m_CtlDefineFirst.grid(row = 0, column = 1, padx=5, pady=5, sticky=tkinter.N+tkinter.E)

        self.m_CtlGoFirst = tkinter.Button(self.m_FNavi, width=30, text="Go to first field", font=self.m_Scheme['font'], command=self.onGoFirst)
        self.m_CtlGoFirst.grid(row = 1, column = 1, padx=5, pady=5, sticky=tkinter.N+tkinter.E)

        self.m_CtlGoNext = tkinter.Button(self.m_FNavi, width=30, text="Go to next field", font=self.m_Scheme['font'], command=self.onGoNext)
        self.m_CtlGoNext.grid(row = 2, column = 1, padx=5, pady=5, sticky=tkinter.N+tkinter.E)

        self.m_CtlGoPrev = tkinter.Button(self.m_FNavi, width=30, text="Go to previous field", font=self.m_Scheme['font'], command=self.onGoPrev)
        self.m_CtlGoPrev.grid(row = 3, column = 1, padx=5, pady=5, sticky=tkinter.N+tkinter.E)
        
        self.m_CtlStatus = tkinter.Label(self.m_FNavi, width=50, height=3, text="", justify=tkinter.LEFT, anchor=tkinter.NW, font=self.m_Scheme['font'])
        self.m_CtlStatus.grid(row=0, column=0, rowspan=4, padx=5, pady=5, sticky=tkinter.N+tkinter.W+tkinter.S+tkinter.E)
        
        # enable GUI
        self.EnableGui()

        # start status refresh
        self.RefreshStatus() 
        
    #
    # create mesh
    #
    def onGenerateXYMesh(self):
    
        # get
        dlg = tkinter.Toplevel(self.m_Root)
        dlg.title("Create XY Mesh")
        dlg.geometry("+%d+%d" % (self.m_Root.winfo_rootx()+50, self.m_Root.winfo_rooty()+50))
        dlg.resizable(width=tkinter.FALSE, height=tkinter.FALSE)
        dlg.wm_iconbitmap('ebl-navi.ico')
        res = DlgCreateXY(dlg, self.m_Scheme, self.m_Coord)
        if res:
            self.m_CurrentField = 0
            self.UpdateCoordListGui()
            self.UpdateCoordListGuiSelection()
            self.EnableGui()
        
    #
    # clear all fields
    #
    def onClearAll(self):
        if tkinter.messagebox.askyesno("", "The list of fields will be cleared.\n\nAre you sure?", parent=self.m_Root):
            self.m_Coord = []
            self.m_CurrentField = 0
            self.UpdateCoordListGui()
            self.UpdateCoordListGuiSelection()
            self.EnableGui()
        
    #
    # load coordinates from csv
    #
    def onLoadCSV(self):
        
        # get file name
        fname = tkinter.filedialog.askopenfilename(parent=self.m_Root, filetypes=(("CSV", "*.csv"), ("All Files", "*.*")))
        if fname == "":
            return
            
        # read file into list
        hf = open(fname, "rt")
        lines = hf.readlines()
        hf.close()
        
        # parse
        for l in lines:
            res = self.ParseSingleCsvLine(l)
            if res != None:
                self.m_Coord.append(res)
            
        # no matter what happens, re-load the list
        self.m_CurrentField = 0
        self.UpdateCoordListGui()
        self.UpdateCoordListGuiSelection()
        self.EnableGui()
        
    #
    # parse single CSV line, two float values are returned, None if unsuccessfull
    #
    def ParseSingleCsvLine(self, lin):
    
        res = None
    
        # split into tokens
        ltkn = lin.split(";")                   # try ';' separator
        if len(ltkn) != 2:
            ltkn = lin.split(",")               # try ',' separator
            if len(ltkn) != 2:
                return res
        
        # remove whitespace and possibly quotation marks and whitespaces again
        # replace all ',' with '.' (problem in eg. Czech)
        lparsed = []
        for tkn in ltkn:
            new_tkn = tkn.strip().strip("\"").strip()
            new_tkn = new_tkn.replace(",", ".")
            lparsed.append(new_tkn)
            
        # must not be empty strings
        for tkn in lparsed:
            if len(tkn) == 0:
                return res
                 
        # convert to float
        try:
            res = ((float(lparsed[0]), float(lparsed[1]))) 
        except:
            res = None
            
        return res
        
    #
    # define the first field position
    #
    def onDefineFirst(self):
        # check if stage is calibrated
        if not self.StgCheckIfCalibrated():
            return
        
        # read pos from SEM
        if self.m_CtlList.size() > 0:
            res = self.m_Sem.StgGetPosition()
            self.m_RefStageX = res[0]
            self.m_RefStageY = res[1]
            self.EnableGui()
        
    #
    # go to first field
    #
    def onGoFirst(self):
        # check if stage is calibrated
        if not self.StgCheckIfCalibrated():
            return
        
        # read pos from SEM
        if self.m_CtlList.size() > 0:
            self.m_CurrentField = 0
            self.StageGoTo()
            self.UpdateCoordListGuiSelection()
            self.EnableGui()

    #
    # go to next field
    #
    def onGoNext(self):
        # check if stage is calibrated
        if not self.StgCheckIfCalibrated():
            return

        # go        
        if self.m_CtlList.size() > 0:
            if self.m_CurrentField < self.m_CtlList.size() - 1:
                self.m_CurrentField = self.m_CurrentField + 1
            self.StageGoTo()
            self.UpdateCoordListGuiSelection()
            self.EnableGui()
        
    #
    # go to previous field
    #
    def onGoPrev(self):
        # check if stage is calibrated
        if not self.StgCheckIfCalibrated():
            return
            
        # go
        if self.m_CtlList.size() > 0:
            if self.m_CurrentField > 0:
                self.m_CurrentField = self.m_CurrentField - 1
            self.StageGoTo()
            self.UpdateCoordListGuiSelection()
            self.EnableGui()
            
    #
    # check if calibrated
    #
    def StgCheckIfCalibrated(self): 
        calib = self.m_Sem.StgIsCalibrated()
        if not calib:
            tkinter.messagebox.showwarning("Error", "Stage is not calibrated.", parent=self.m_Root)
        return calib 
        
    #
    # move stage to the current position
    #
    def StageGoTo(self):
        # go
        (stgx, stgy) = self.m_Coord[self.m_CurrentField]
        self.m_Sem.StgMoveTo(self.m_RefStageX + stgx, self.m_RefStageY + stgy)        
        
        # display progress
        dlg = tkinter.Toplevel(self.m_Root)
        dlg.title("Progress info")
        dlg.geometry("+%d+%d" % (self.m_Root.winfo_rootx()+50, self.m_Root.winfo_rooty()+50))
        dlg.resizable(width=tkinter.FALSE, height=tkinter.FALSE)
        dlg.wm_iconbitmap('ebl-navi.ico')
        res = DlgStgMove(dlg, self.m_Scheme, self.m_Sem)
        
    #
    # update list GUI 
    #
    def UpdateCoordListGui(self):
        self.m_CtlList.delete(0, self.m_CtlList.size() - 1)
        i = 0
        for v in self.m_Coord:
            lline = "%+.3f %+.3f" % (v[0], v[1])
            self.m_CtlList.insert(i, lline)
            i = i + 1         

    #
    # update list GUI selection 
    #
    def UpdateCoordListGuiSelection(self):
        n = self.m_CtlList.size()
        for i in range(0, n):
            if i == self.m_CurrentField:
                self.m_CtlList.itemconfig(i, background=self.m_Scheme['editvalcolor'])
                self.m_CtlList.see(i)
            else:
                self.m_CtlList.itemconfig(i, background="#FFFFFF")
                
    # 
    # update status
    #                 
    def UpdateStatusGui(self):
        res = self.m_Sem.StgGetPosition()
        sx = res[0]
        sy = res[1]
        msg = "Current field / total fields: %d / %d\nReference position: X = %.3f mm, Y = %.3f mm\nStage position: X = %.3f mm, Y = %.3f mm" % (self.m_CurrentField + 1, self.m_CtlList.size(), self.m_RefStageX, self.m_RefStageY, sx, sy)
        self.m_CtlStatus.config(text=msg)
        
    #
    # enable/disable GUI controls (depending on the status)
    def EnableGui(self):
        lst_empty = (len(self.m_Coord) == 0)
        lst_first = (self.m_CurrentField == 0)
        lst_last = (self.m_CurrentField == len(self.m_Coord) - 1) 
        
        if lst_empty:
            self.m_CtlGenXY.config(state=tkinter.NORMAL)
            self.m_CtlLoadCSV.config(state=tkinter.NORMAL)
            self.m_CtlClearAll.config(state=tkinter.DISABLED)
            self.m_CtlDefineFirst.config(state=tkinter.DISABLED)
            self.m_CtlGoFirst.config(state=tkinter.DISABLED)
            self.m_CtlGoNext.config(state=tkinter.DISABLED)
            self.m_CtlGoPrev.config(state=tkinter.DISABLED)
        else:
            self.m_CtlGenXY.config(state=tkinter.DISABLED)
            self.m_CtlLoadCSV.config(state=tkinter.DISABLED)
            self.m_CtlClearAll.config(state=tkinter.NORMAL)
            if lst_last:
                self.m_CtlGoNext.config(state=tkinter.DISABLED)
            else:
                self.m_CtlGoNext.config(state=tkinter.NORMAL)
            if lst_first:
                self.m_CtlDefineFirst.config(state=tkinter.NORMAL)
                self.m_CtlGoFirst.config(state=tkinter.DISABLED)
                self.m_CtlGoPrev.config(state=tkinter.DISABLED)
            else:
                self.m_CtlDefineFirst.config(state=tkinter.DISABLED)
                self.m_CtlGoFirst.config(state=tkinter.NORMAL)
                self.m_CtlGoPrev.config(state=tkinter.NORMAL)
                
    #
    # periodic refresh (timer)
    #
    def RefreshStatus(self):
        self.UpdateStatusGui()
        self.m_Root.after(1000, self.RefreshStatus)
                        

################################################################################################
#
# app main
#

# connection to SEM
m = sem.Sem()
res = m.Connect('localhost', 8300)    
if res < 0:
    print("Error: unable to connect")
    exit
    
# main dialog
root = tkinter.Tk()
root.title("EBL Multi-field Navigator")
root.resizable(width=tkinter.FALSE, height=tkinter.FALSE)
root.wm_iconbitmap('ebl-navi.ico')
maindlg = MainDlg(root, m)
root.mainloop()
