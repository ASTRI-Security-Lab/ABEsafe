import wx
import wx.dataview as dv

import sys,os
import re
import random
import difflib

from ABEsafe_process import CPABE


SYNC_FREQ = 2000
TOAST_FREQ = 1000
TOUT_INFO = 6000

NAME_COLOR = wx.Colour(48,25,255)
FUN1_COLOR = wx.Colour(178,70,0)
FUN2_COLOR = wx.Colour(232,63,197)
FUN3_COLOR = wx.Colour(82,85,255)
FUN4_COLOR = wx.Colour(63,232,213)
FUN5_COLOR = wx.Colour(0,172,178)
BLACK_COLOR = wx.Colour(40,40,20)

class PanelTreeListModel(wx.dataview.PyDataViewModel):
    def __init__(self, data, log):
        wx.dataview.PyDataViewModel.__init__(self)
        self.data = data
        self.log = log
        self.showAll = False
        self.UseWeakRefs(True)

        self.tree = self.walkDB()
        self.timer = wx.CallLater(SYNC_FREQ,self.syncDB)

    # Report how many columns this model provides data for.
    def GetColumnCount(self):
        return 3

    # Map the data column numbers to the data type
    def GetColumnType(self, col):
        mapper = { 0 : 'string',
                   1 : 'string',
                   2 : 'string'
                   }
        return mapper[col]
        
    def GetValue(self, item, col):
        node = self.ItemToObject(item)
        if not isinstance(node, DB_Entity):
            raise RuntimeError("[GetValue] unknown node type")
        mapper = { 0 : os.path.basename(node.getRname()),
                   1 : "*Unsecure*" if not node.getAbes() else "Locked" if node.getAbes()['perm']=="" else "Yes",
                   2 : (node.getAbes())['perm'] if node.getAbes() else ""
                   }
        return mapper[col]
    
    def GetChildren(self, parent, children):  
        if not parent:
            for n in self.data.values():
                children.append(self.ObjectToItem(n))
            return len(self.data)
        else:
            node = self.ItemToObject(parent)
            if not isinstance(node, DB_Entity):
                raise RuntimeError("[GetChildren] unknown node type")
            fname = os.path.join(CPABE.HOME_PATH,node.getRname())
            if not os.path.isdir(fname):
                return 0
            #create children if not exists
            if not node.getInners():
                files = os.listdir(fname)
                files.sort()
                for cfile in files:
                    tmp = os.path.join(node.getRname(),cfile)
                    file_node = DB_Entity(tmp,node)
                    fpath = os.path.join(CPABE.SHARED_FOLDER_PATH,cfile)
                    if not os.path.isdir(fpath) and not self.showAll and not file_node.isABE():
                        pass
                    else:
                        node.addInners(tmp,file_node)
            for n in node.getInners().values():
                children.append(self.ObjectToItem(n))
            return len(node)

    def IsContainer(self, item):
        # Return True if the item has children, False otherwise.
        # The hidden root is a container
        if not item:
            return True
        node = self.ItemToObject(item)
        if not isinstance(node, DB_Entity):
            raise RuntimeError("[IsContainer] unknown node type")
        return True if os.path.isdir(os.path.join(CPABE.HOME_PATH,node.getRname())) else False
    
    def GetParent(self, item):
        if not item:
            return wx.dataview.NullDataViewItem
        node = self.ItemToObject(item)        
        if not isinstance(node, DB_Entity):
            raise RuntimeError("[GetParent] unknown node type")
        tmp = node.getParent()
        if not tmp:
            return wx.dataview.NullDataViewItem
        else:
            return self.ObjectToItem(tmp)     

    def GetAttr(self, item, col, attr):
        global FUN1_COLOR,FUN5_COLOR
        node = self.ItemToObject(item)
        path = os.path.join(CPABE.HOME_PATH,node.getRname())
        if os.path.isdir(path):
            attr.SetColour(BLACK_COLOR)
            return False
        if node.getAbes():
            attr.SetBold(True)
            if node.getAbes()['perm'] == "Yes":
                attr.SetColour(FUN5_COLOR)
            else:
                attr.SetColour(FUN1_COLOR)
            return True
        else:
            attr.SetColour(wx.Colour(150,150,150))
        return False

    def getBase(self):
        return self.ObjectToItem(self.data[CPABE.SHARED_FOLDER_NAME])

    def walkDB(self,topdown=True):
        #topdown when itemadded
        #bottomup when itemdeleted
        #remove HOME
        t = []
        pattern = re.compile("\.")
        for p,ds,fs in os.walk(CPABE.SHARED_FOLDER_PATH,topdown):
            for f in fs:
                tmp = os.path.join(p,f)
                (path,cfile) = os.path.split(os.path.relpath(tmp,CPABE.HOME_PATH))
                node = DB_Entity(cfile,path)
                if not self.showAll and not node.isABE():
                    pass
                elif pattern.match(f) is None:
                    t.append(os.path.relpath(tmp,CPABE.HOME_PATH)+'\n')
            for d in ds:
                if pattern.match(d) is None:
                    tmp = os.path.join(p,d)
                    t.append(os.path.relpath(tmp,CPABE.HOME_PATH)+'\n')
        return t
    def syncDB(self):
        newtree = self.walkDB()
        diff = difflib.Differ()
        dt = list(diff.compare(self.tree,newtree))
        dt.sort()
        parent = self.data[CPABE.SHARED_FOLDER_NAME]
        ''' create:
            find parent from data inners layer by layer,
            then add node and item'''
        for d in dt:
            if d[0]=='+':
                keys = []
                x_path = re.search(r'\+\s+(.*)\n',d)
                path = x_path.group(1)
                (path,cfile) = os.path.split(path)
                while cfile and path:
                    keys.insert(0,path)
                    (path,cfile) = os.path.split(path)
                parent = self.data[CPABE.SHARED_FOLDER_NAME]
                try:
                    for k in keys[1:]:
                        parent = parent.getInners()[k]
                except KeyError as ke:
                    ""
                path = x_path.group(1)
                try:
                    node = DB_Entity(path,parent)
                    item = self.ObjectToItem(node)
                    parent.addInners(path,node)
                    self.ItemAdded(self.ObjectToItem(parent),item)
                except KeyError as ke:
                    self.log.write('+ error: %s'%ke)
        dt.reverse()
        for d in dt:
            if d[0]=='-':
                keys = []
                x_path = re.search(r'\-\s+(.*)\n',d)
                path = x_path.group(1)
                (path,cfile) = os.path.split(path)
                while cfile and path:
                    keys.insert(0,path)
                    (path,cfile) = os.path.split(path)
                parent = self.data[CPABE.SHARED_FOLDER_NAME]
                try:
                    for k in keys[1:]:
                        parent = parent.getInners()[k]
                except KeyError as ke:
                    pass
                path = x_path.group(1)
                try:
                    node = parent.getInners()[path]
                    item = self.ObjectToItem(node)
                    parent.delInners(path)
                    self.ItemDeleted(self.ObjectToItem(parent),item)
                except KeyError as ke:
                    self.log.write('- error: %s'%ke)
        self.tree = newtree
        self.timer.Restart(SYNC_FREQ)

class FilePanel(wx.Panel):
    def __init__(self, parent, log, data=None, model=None):
        self.parent = parent
        self.log = log
        wx.Panel.__init__(self, parent, -1)
        
        self.dest = CPABE.SHARED_FOLDER_NAME
        # Create a dataview control
        self.dvc = wx.dataview.DataViewCtrl(self, style=wx.BORDER_THEME | wx.dataview.DV_ROW_LINES | wx.dataview.DV_VERT_RULES)
        if model is None:
            self.model = PanelTreeListModel(data, log)
        else:
            self.model = model            

        # Tel the DVC to use the model
        self.dvc.AssociateModel(self.model)
        self.model.syncDB()

        c1 = self.dvc.AppendTextColumn("Name",    0, width=320, mode=wx.dataview.DATAVIEW_CELL_INERT)
        c2 = self.dvc.AppendTextColumn("Encrypted",   1, width=80, mode=wx.dataview.DATAVIEW_CELL_ACTIVATABLE,align=wx.ALIGN_CENTRE)
        c3 = self.dvc.AppendTextColumn('Allowed',   2, width=80, mode=wx.dataview.DATAVIEW_CELL_ACTIVATABLE,align=wx.ALIGN_CENTRE)
        
        # Set some additional attributes for all the columns
        for c in self.dvc.Columns:
            c.Sortable = True
            c.Reorderable = True

        self.dvc.Expand(self.model.getBase())

        self.Sizer = wx.BoxSizer(wx.VERTICAL)
        self.Sizer.Add(self.dvc, 1, wx.EXPAND)

        self.dvc.Bind(wx.dataview.EVT_DATAVIEW_ITEM_ACTIVATED, self.OnOpen)
        self.dvc.Bind(wx.dataview.EVT_DATAVIEW_SELECTION_CHANGED, self.OnSel)

        self.parent.setInfo()
        self.dvc.GetColumn(1).SetSortOrder(True)
        self.model.Resort()
        self.model.syncDB()

    def OnSel(self,ev):
        if not ev.GetItem():
            return
        try:
            rname = self.model.ItemToObject(ev.GetItem()).getRname()
            if rname:
                self.parent.deleteButton.Enable()
                self.parent.saveToDesktopButton.Enable()
            fname = os.path.join(CPABE.HOME_PATH,rname)
            if os.path.isdir(fname):
                self.dest = rname
            #unnecessary because link-to-dir is confused with real-dir
            elif os.path.islink(fname):
                tmp = fname
                self.log.write('[OnSel] ln_real: %s\n'%tmp)
                if os.path.isdir(tmp):
                    self.dest = os.path.relpath(tmp,CPABE.HOME_PATH)
                else:
                    self.dest = CPABE.SHARED_FOLDER_NAME
            else:
                self.dest = CPABE.SHARED_FOLDER_NAME
            self.log.write('[OnSel] dest:%s\n'%self.dest)
        except KeyError as ke:
            return

    def OnOpen(self,ev):
        obj = self.model.ItemToObject(ev.GetItem())
        openthis = os.path.join(CPABE.HOME_PATH,obj.getRname())
        if obj.getAbes():
            if (obj.getAbes())['perm']:
                self.parent.getParent().decrypt(openthis)
            else:
                self.parent.parent.parent.showMessage("File is encrypted",FUN1_COLOR)
        elif not os.path.isdir(openthis):
            status = os.system('open "%s"'%openthis)
            ret = status>>8
            if ret==0:
                self.log.write('[OnOpen] succeeded: %s\n'%openthis)
            else:
                self.log.write('[OnOpen] failed: %s\n'%openthis)

    def OnDelete(self):
        if not self.dvc.HasSelection():
            self.parent.parent.parent.showMessage("No file is selected",BLACK_COLOR)
            return
        obj = self.model.ItemToObject(self.dvc.GetSelection())
        dialog = wx.MessageDialog(self,"Are you sure to delete %s ?" % (obj.getRname()),"Deleting file",wx.YES_NO|wx.NO_DEFAULT|wx.ICON_INFORMATION)
        confirm_delete = dialog.ShowModal() == wx.ID_YES
        if not confirm_delete:
            self.parent.parent.parent.clearMessage()
            return
        deletethis = os.path.join(CPABE.HOME_PATH,obj.getRname())
        if os.path.isdir(deletethis):
            status = os.system('rm -r "%s"'%deletethis)
        else:
            status = os.system('rm "%s"'%deletethis)
        ret = status>>8
        if ret==0:
            self.parent.parent.parent.showMessage("File is deleted","orange")
            self.log.write('[OnDelete] succeeded: %s\n'%deletethis)
            self.clrDest()
            self.dvc.UnselectAll()
        else:
            self.parent.parent.parent.showMessage("File cannot be deleted",wx.Colour(100,100,0))
            self.log.write('[OnDelete] failed: %s\n'%deletethis)

    def OnSave(self):
        if not self.dvc.HasSelection():
            self.parent.parent.parent.showMessage("No file is selected",BLACK_COLOR)
            return
        obj = self.model.ItemToObject(self.dvc.GetSelection())
        savethis = os.path.join(CPABE.HOME_PATH,obj.getRname())
        if (obj.getAbes() and (obj.getAbes())['perm']=="Yes"):
            self.parent.getParent().decrypt(savethis,True)
        elif obj.getAbes():
            self.parent.parent.parent.showMessage("File is encrypted",FUN1_COLOR)
            self.log.write('[OnSave] encrypted: %s\n'%savethis)
        else:
            import shutil
            try:
                shutil.copyfile(savethis, os.path.join(os.path.expanduser("~/Desktop"),os.path.basename(savethis)))
                self.parent.parent.parent.showMessage("Save succeeded","gray")
                self.log.write('[OnSave] succeeded: %s\n'%savethis)
            except shutil.Error:
                self.parent.parent.parent.showMessage("Save failed",wx.Colour(100,100,0))
                self.log.write('[OnSave] failed: %s\n'%savethis)

    def getDest(self):
        return os.path.join(CPABE.HOME_PATH,self.dest)

    def clrDest(self):
        self.dest = CPABE.SHARED_FOLDER_NAME
        if self.dvc.HasSelection():
            self.dvc.Unselect(self.dvc.GetSelection())
        self.log.write('[clrDest] dest:%s\n' % self.dest)

def createFilePanel(frame, nb, log, userkey):
    data = {}
    global USERKEY
    USERKEY = userkey
    data[CPABE.SHARED_FOLDER_NAME] = DB_Entity(CPABE.SHARED_FOLDER_NAME,None)
    win = FilePanel(nb, log, data=data)
    return win
        
''' rname: path+file w/o HOME_DIR '''
class DB_Entity(object):
    def __init__(self, rname, dotdot=None):
        self.rname = rname
        self.dotdot = dotdot
        self.inners = {}
        self.abes = {}

        ''' .cpabes are binary data file '''
        if rname==None:
            return
        if os.path.isfile(os.path.join(CPABE.HOME_PATH,rname)) and self.isABE():
            self.abes['perm'] = self.isAllowed()
    def __repr__(self):
        return 'rname:'+str(self.rname)+' inners:'+str(self.inners)
    def __len__(self):
        return len(self.inners)

    def isABE(self):
        m_abe = re.search(r'\.cpabe$',self.rname)
        return True if m_abe else False

    def isAllowed(self):
        res = CPABE.runcpabe(CPABE.OPEN,None,None,USERKEY,os.path.join(CPABE.HOME_PATH,self.rname))
        return "Yes" if res==0 else ""

    def getRname(self):
        return self.rname
    def getParent(self):
        return self.dotdot
    def getInners(self):
        return self.inners
    def getAbes(self):
        return self.abes
    def addInners(self,key,node):
        self.inners[key] = node
    def delInners(self,key):
        del self.inners[key]
#----------------------------------------------------------------------

HOME_DIR=os.getenv('HOME')
USERKEY = ''

