#!/usr/bin/python

import wx
import DataViewModel as DB

TWEEN_MILLIS = 20
TWEEN_STEP = 20
TWEEN_END = 20
class PanelFileDropTarget(wx.FileDropTarget):
    def __init__(self,obj,log):
        wx.FileDropTarget.__init__(self)
        self.obj = obj
        self.log = log
    def OnDropFiles(self,x,y,filenames):
        if self.obj.getDest():
            self.log.write('[OnDropFiles] %s\n' % str(filenames))
            self.obj.setFiles(filenames)
            self.obj.parent.goto2()
        return True
    def OnDragOver(self,x,y,result):
        if self.obj.getDest():
            return result
        else:
            return 1

class ABEmain1(wx.SplitterWindow):
    def __init__(self,parent,log,size=wx.DefaultSize):
        wx.SplitterWindow.__init__(self,parent,size=size,style=wx.SP_LIVE_UPDATE)
        self.parent = parent
        self.log = log
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSashChanged)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.OnSashChanging)
        self.Bind(wx.EVT_SPLITTER_UNSPLIT, self.OnUnsplit)
        self.Bind(wx.EVT_SPLITTER_DOUBLECLICKED, self.OnDoubleClicked)
        self.Bind(wx.EVT_SIZE, self.OnSize)

        self.files = None
        self.fdt = PanelFileDropTarget(self,self.log)
        self.SetDropTarget(self.fdt)
        self.top = DB.createFilePanel(self,self,log,self.parent.getKey())
        self.down = wx.Panel(self)

        self.showHideButton = wx.CheckBox(self.down,label="Show All", size=(100,20),pos=(5,5))
        self.showHideButton.Bind(wx.EVT_CHECKBOX,self.OnShowHideChanged)
        self.saveToDesktopButton = wx.Button(self.down,label="Save to Desktop", size=(120,20),pos=(500,0))
        self.saveToDesktopButton.Bind(wx.EVT_BUTTON,self.OnSaveButtonClicked)
        self.deleteButton = wx.Button(self.down,label="Delete file",size=(120,20),pos=(280,0))
        self.deleteButton.Bind(wx.EVT_BUTTON,self.OnDeleteButtonClicked)
        self.addFileButton = wx.Button(self.down,label="Add file",size=(120,20),pos=(150,0))
        self.addFileButton.Bind(wx.EVT_BUTTON,self.onAddFileButtonClicked)
        self.deleteButton.Disable()
        self.saveToDesktopButton.Disable()
        self.SplitHorizontally(self.top, self.down)
        self.SetMinimumPaneSize(1)


    def OnSashChanged(self,ev):
        pass

    def OnSashChanging(self,ev):
        pass

    def OnUnsplit(self,ev):
        pass

    def OnDoubleClicked(self,ev):
        self.SetSashPosition(-40)

    def OnSize(self,ev):
        self.SetSashPosition(-40)

    def OnShowHideChanged(self,e):
        if self.showHideButton.GetValue():
            self.top.model.showAll = True
            self.top.model.Resort()
            self.top.model.syncDB()
            self.showHideButton.SetLabel("All shown")
        else:
            self.top.model.showAll = False
            self.top.model.Resort()
            self.top.model.syncDB()
            self.showHideButton.SetLabel("Show All")

    def onAddFileButtonClicked(self,e):
        addFileDialog = wx.FileDialog(self,"Add file","","","",wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_PREVIEW)
        if addFileDialog.ShowModal() == wx.ID_OK:
            self.fdt.obj.setFiles([addFileDialog.GetPath()])
            self.fdt.obj.parent.goto2()
        else:
            return

    def OnDeleteButtonClicked(self,e):
        self.top.OnDelete()

    def OnSaveButtonClicked(self,e):
        self.top.OnSave()

    def clrDest(self):
        self.top.clrDest()

    def getDest(self):
        return self.top.getDest()

    def slideTo(self):
        if self.GetSashPosition() > TWEEN_END:
            self.SetSashPosition(self.GetSashPosition() - TWEEN_STEP)
            wx.CallLater(TWEEN_MILLIS,self.slideTo)

    def setFiles(self,files):
        self.files = files

    def getFiles(self):
        return self.files

    def getParent(self):
        return self.parent

    def getLog(self):
        return self.down

    def setInfo(self,profile=None):
        self.parent.setInfo(profile)
