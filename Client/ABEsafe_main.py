#!/usr/bin/python

import os
import re
import shutil, tempfile
import wx

import ABEsafe_main1 as M1
import ABEsafe_main2 as M2

from ABEsafe_process import CPABE
import DataViewModel as DB

import sqlite3
from ctypes import *

SCREEN_SIZE = (640, 480)
TWEEN_STEP = 32
TWEEN_MILLIS = 1
TOUT_INFO = 6000
PROFILE_SCALE = 80

USER_ID = None
USERNAME = ''
USERKEY = ''
USERDEPARTMENT = ''
USERPOSITION = ''
USERSECLV = -1

class ABEmain(wx.SplitterWindow):
    def __init__(self,parent,log):
        wx.SplitterWindow.__init__(self,parent)
        self.parent = parent
        self.log = log
        self.pj_enc = {}
        self.pj_dec = {}
    def setupWindow(self):
        self.setInfo()
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGED, self.OnSashChanged)
        self.Bind(wx.EVT_SPLITTER_SASH_POS_CHANGING, self.OnSashChanging)
        self.Bind(wx.EVT_SPLITTER_UNSPLIT, self.OnUnsplit)
        self.Bind(wx.EVT_SPLITTER_DOUBLECLICKED, self.OnDoubleClicked)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.left = M1.ABEmain1(self,self.log)
        self.right = M2.ABEmain2(self,self.log)
        self.SplitVertically(self.left, self.right)
        self.SetSashInvisible(True)
        self.page=1

    def setInfo(self,profile=None,staff_id=None,department=None,position=None,seclv=None):
        self.parent.p.setInfo(profile,staff_id,department,position,seclv)

    def getUser(self):
        return USERNAME

    def getKey(self):
        return USERKEY

    def getFiles(self):
        return self.left.getFiles()

    def encrypt(self):
        if self.pj_enc:
            self.log.write('encrypting\n')
            return
        self.pj_enc = {}
        self.r_encrypt()

    def r_encrypt(self,srcs=None,dest=None):
        srcs = self.left.getFiles() if not srcs else srcs
        dest = self.left.getDest() if not dest else dest
        srcs.sort()
        for src in srcs:
            output = os.path.join(dest,os.path.basename(src))
            if os.path.exists(output):
                self.onencerr('%s:%s:%s:%s'%('E','file exists',src,output))
                self.parent.showMessage("File already exists","orange")
                continue
            if os.path.isdir(src):
                #mkdir
                try:
                    if not os.path.exists(output):
                        os.mkdir(output)
                    #all inner files
                    nextsrcs = []
                    for tmp in os.listdir(src):
                        nextsrcs.append(os.path.join(src,tmp))
                    nextdest = output
                    self.r_encrypt(nextsrcs,nextdest)
                except OSError as oser:
                    self.onencerr('%s:%s'%('OSError E',oser))
                    continue
            else:
                real = src
                i = len(self.pj_enc)
                self.pj_enc[i] = real
                if not os.path.exists(CPABE.CONFIG_PATH):
                    wx.MessageBox("ABEsafe system is not connected.")
                    self.parent.Destroy()
                self.parent.p.SetLabel("Encrypting...")
                self.parent.p.SetForegroundColour("blue")
                CPABE.runcpabe(CPABE.ENC,i,self.onencrypt,output+'.cpabe',real,self.right.getPolicy())
        self.left.clrDest()
        self.goto1()

    def onencerr(self,err):
        self.log.write('[log] %s\n'%err)

    def onencrypt(self,DR,ftmp,copyTo):
        res = DR.get()
        jid = DR.getJobID()
        try:
            shutil.copyfile(ftmp.name, copyTo)
        except IOError as e:
            self.log.write("IOError: %s"%e)
            res = 1
        except Exception as e:
            self.log.write("cannot move: %s"%e)
            res = 1
        if res==0:
            self.log.write('[log] encryption succeeded:%s\n'%self.pj_enc[jid])
            self.parent.p.SetLabel("File has been encrypted")
            self.parent.p.SetForegroundColour("blue")
        else:
            self.log.write('[log] E:encryption failed:%s\n'%self.pj_enc[jid])
            self.parent.p.SetLabel("Encryption failed")
            self.parent.p.SetForegroundColour("red")
        del self.pj_enc[jid]

    def decrypt(self,path,save=False,savePath="~/Desktop"):
        if self.pj_dec:
            self.log.write('decrypting\n')
            return
        out_file = os.path.join(CPABE.TMP,os.path.basename(path)[0:-6])
        i = len(self.pj_enc)
        self.pj_dec[i] = out_file
        if not os.path.exists(CPABE.CONFIG_PATH):
            wx.MessageBox("ABEsafe system is not connected.")
            self.parent.Destroy()
        if save:
            CPABE.runcpabe(CPABE.DEC,i,self.onSave,out_file,USERKEY,path)
        else:
            CPABE.runcpabe(CPABE.DEC,i,self.ondecrypt,out_file,USERKEY,path)

    def ondecrypt(self,DR):
        res = DR.get()
        jid = DR.getJobID()
        ret = None
        out = self.pj_dec[jid]
        if res==0:
            status = os.system('open "%s"'%out)
            os.chmod(out,0o700)
            self.log.write('[decrypt] succeeded: %s\n'%out)
        else:
            self.log.write('[decrypt] failed: %s\n'%out)
        del self.pj_dec[jid]

    def onSave(self,DR):
        res = DR.get()
        jid = DR.getJobID()
        ret = None
        out = self.pj_dec[jid]
        if res==0:
            try:
                shutil.copyfile(os.path.join(os.path.expanduser("~/Desktop"),os.path.basename(out)),out)
                os.chmod(out,0o700)
                self.parent.showMessage("Save succeeded","blue")
                self.log.write('[save] succeeded: %s\n'%os.path.expanduser("~/Desktop"))
                ret = out
            except shutil.Error:
                res = 1
        if res!=0:
            self.parent.showMessage("Save failed","gray")
            self.log.write('[save] failed: %s\n'%os.path.expanduser("~/Desktop"))
            ret = None
        del self.pj_dec[jid]

    def goto2(self):
        self.SplitVertically(self.left, self.right, -1)
        self.right.createPolicyGUI()
        self.right.policyGUI_frame.Show()
        self.tweenltr()
        self.left.deleteButton.Disable()
        self.left.saveToDesktopButton.Disable()
        self.page=2
        self.right.p_policy.search.SetText("")
        self.right.timer.Restart(1000)

    def tweenltr(self):
        i = self.GetSashPosition()
        if i>TWEEN_STEP:
            self.SetSashPosition(i-TWEEN_STEP)
            wx.CallLater(TWEEN_MILLIS,self.tweenltr)
        else:
            self.Unsplit(self.left)
            self.right.focusOnEntry()

    def goto1(self):
        self.left.clrDest()
        self.right.focusOnExit()
        self.SplitVertically(self.left, self.right, 0)
        self.tweenrtl()
        self.setInfo()
        self.page=1

    def tweenrtl(self):
        i = self.GetSashPosition()
        if i<SCREEN_SIZE[0]-TWEEN_STEP:
            self.SetSashPosition(i+TWEEN_STEP)
            wx.CallLater(TWEEN_MILLIS,self.tweenrtl)
        else:
            self.Unsplit(self.right)

    def OnSashChanged(self,ev):
        pass

    def OnSashChanging(self,ev):
        pass

    def OnUnsplit(self,ev):
        pass

    def OnDoubleClicked(self,ev):
        pass

    def OnSize(self,ev):
        self.SetSashPosition(-1)

class ABEinfo(wx.Panel):
    def __init__(self,parent,log,size):
        wx.Panel.__init__(self,parent,size=size)
        self.log = log
        self.info = {}
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_PAINT,self.drawDC)
        self.setInfo()
        self.uploadPhotoButton = wx.Button(self,label="Upload Photo",size=(80,12),pos=(5,105))
        self.uploadPhotoButton.SetFont(wx.Font(10,wx.SWISS,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD,False))
        self.uploadPhotoButton.Bind(wx.EVT_BUTTON,self.OnUploadPhotoClicked)
        self.statusLabel = wx.StaticText(self,label="",pos=(270,100))
        self.statusLabel.SetFont(wx.Font(16,wx.SWISS,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD,False))
        
    def setInfo(self,profile=None,staff_id=None,department=None,position=None,seclv=None, attributes={}):
        global USERNAME, USER_ID, USERDEPARTMENT, USERPOSITION, USERSECLV
        self.info = {}
        self.info['name'] = profile if profile else USERNAME
        self.info['id']= staff_id if staff_id is not None else str(USER_ID) if USER_ID is not None else "Invalid Staff ID"
        self.info['dep']=department if department is not None else USERDEPARTMENT
        self.info['pos']=position if position is not None else USERPOSITION
        self.info['sec']=seclv if seclv is not None else str(USERSECLV) if USERSECLV>0 else "Not Specified"
        if isinstance(attributes, dict):
            for attribute in attributes:
                self.info[attribute] = attributes[attribute]
        self.Refresh()
        self.Update()

    def OnUploadPhotoClicked(self,e):
        fileSelect = wx.FileDialog(self,defaultDir=os.path.expanduser("~/Desktop"),message="Upload photo",wildcard="JPEG files(*.jpg)|*.jpg|JPEG files(*.jpeg)|*.jpeg",style=wx.FLP_OPEN|wx.FLP_FILE_MUST_EXIST)
        fname = None
        if fileSelect.ShowModal() == wx.ID_OK:
            fname = fileSelect.GetPath()
            shutil.copyfile(fname,os.path.join(CPABE.IMG_PATH,self.info['name']+"_"+str(self.info['id']+".jpg")))
            self.setInfo()

    def drawDC(self,ev):
        dc = wx.AutoBufferedPaintDC(self)
        dc.SetBackground(wx.WHITE_BRUSH)
        dc.Clear()
        dc.SetFont(wx.Font(20,wx.MODERN,wx.FONTSTYLE_SLANT,wx.FONTWEIGHT_BOLD,False))
        offset = 10
        img = wx.Image(os.path.join(CPABE.IMG_PATH,'%s.jpg'%(self.info['name']+"_"+str(self.info['id']))), wx.BITMAP_TYPE_JPEG).Rescale(PROFILE_SCALE,PROFILE_SCALE).ConvertToBitmap()
        
        dc.DrawBitmap(img,10,10+offset,True)
        dc.SetFont(wx.Font(16,wx.MODERN,wx.FONTSTYLE_SLANT,wx.FONTWEIGHT_BOLD,False))
        dc.SetTextForeground(DB.NAME_COLOR)
        dc.DrawText(self.info['name'].upper(),120,10+offset)
        dc.SetFont(wx.Font(12,wx.SWISS,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD,False)) 
        dc.SetTextForeground(DB.FUN3_COLOR)
        dc.DrawText('Staff ID',120,30+offset)
        dc.DrawText('Position',120,45+offset)
        dc.DrawText('Department',120,60+offset)

        dc.SetFont(wx.Font(12,wx.SWISS,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD,False)) 
        dc.SetTextForeground(DB.FUN2_COLOR)
        dc.DrawText(self.info['id'],210,30+offset)
        dc.DrawText(self.info['pos'],210,45+offset)
        dc.DrawText(self.info['dep'],210,60+offset)

        img = wx.Image(os.path.join(CPABE.LOCAL_PATH,'img/ASTRI.png'),wx.BITMAP_TYPE_PNG).Rescale(200,96).ConvertToBitmap()
        dc.DrawBitmap(img,430,10+offset,True)

class MainFrame(wx.Frame):
    def __init__(self,log,title,size):
        wx.Frame.__init__(self,None,title=title,size=size)
        self.log = log

    def setupPanel(self):      
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.p = ABEinfo(self,self.log,size=(SCREEN_SIZE[0],130))
        self.panel = ABEmain(self,self.log)
        self.sizer.Add(self.p,0,wx.EXPAND,0)
        self.sizer.Add(self.panel,1,wx.EXPAND,0)
        self.SetSizer(self.sizer)
        self.menubar = wx.MenuBar()
        menuhelp = wx.Menu()
        self.Bind(wx.EVT_MENU, self.OnHelp, menuhelp.Append(wx.ID_HELP,"CPABE Help"))
        self.menubar.Append(menuhelp,"&Help")
        self.SetMenuBar(self.menubar)
        self.panel.setupWindow()

    def OnHelp(self,ev):
        readme = open('README','r')
        dlg = wx.MessageDialog(self,''.join(readme.readlines()),"CPABE Help",wx.OK|wx.ICON_INFORMATION)
        dlg.ShowModal()
        dlg.Destroy()

    def showMessage(self,message,Colour):
        self.p.statusLabel.SetLabel(message)
        self.p.statusLabel.SetForegroundColour(Colour)
        wx.CallLater(1500,self.clearMessage)

    def clearMessage(self):
        self.p.statusLabel.SetLabel("")
        self.p.statusLabel.SetForegroundColour(DB.BLACK_COLOR)

class MainApp(wx.App):
    def __init__(self,log):
        wx.App.__init__(self)
        self.log = log
        LoginWindows(self, log)

    def OnInit(self):
        stdout = open(r'/dev/stdout','a',0)
        self.frame = None
        return True

    def BringWindowToFront(self):
        try:
            self.GetTopWindow().Raise()
        except:
            pass

    def OnActivate(self,ev):
        if ev.GetActive():
            self.BringWindowToFront()
        else:
            ev.Skip()

    def MacReopenApp(self):
        self.BringWindowToFront()

    def OnExit(self,e):
        self.OnExit()
        e.Skip()

    def OnExit(self):
        if os.path.exists(CPABE.TMP):
            try:
                shutil.rmtree(CPABE.TMP)
            except Exception as e:
                self.log.write("remove tmp dir error: %s"%e)
                return False
        return True

class LoginWindows(wx.Frame):
    def __init__(self,parent, log):
        self.parent = parent
        self.log = log
        self.userSelected = False
        self.nl = []
        wx.Frame.__init__(self,None,size=(400,300),title="ABEsafe Login",style=wx.DEFAULT_FRAME_STYLE)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.panel = wx.Panel(self,size=(400,300))
        login_font = wx.Font(16,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD,False)
        login_label = wx.StaticText(self.panel,label="Select your account to login",pos=(70,50))
        login_label.SetFont(login_font)
        login_label.SetForegroundColour(DB.BLACK_COLOR)
        login_font = wx.Font(14,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_SLANT,wx.FONTWEIGHT_NORMAL,False)
        self.sharedFolderLabel = wx.StaticText(self.panel,label="Shared Folder",pos=(20,100))
        self.sharedFolderLabel.SetFont(login_font)
        self.sharedFolderLabel.SetForegroundColour(DB.BLACK_COLOR)
        self.usernameLabel = wx.StaticText(self.panel,label="Username",pos=(20,150))
        self.usernameLabel.SetFont(login_font)
        self.usernameLabel.SetForegroundColour(DB.BLACK_COLOR)
        self.passphraseLabel = wx.StaticText(self.panel,label="Passphrase",pos=(20,200))
        self.passphraseLabel.SetFont(login_font)
        self.passphraseLabel.SetForegroundColour(DB.BLACK_COLOR)
        self.sharedFolderPathSelection = wx.DirPickerCtrl(self.panel,message="Select ABEsafe folder directory",pos=(145,100))

        self.sharedFolderPathSelection.Bind(wx.EVT_DIRPICKER_CHANGED,self.OnSharedFolderSelected)
        self.usernameComboBox = wx.ComboBox(self.panel,pos=(150,150),size=(130,25),choices=self.nl,style=wx.CB_READONLY)
        self.usernameComboBox.Bind(wx.EVT_COMBOBOX,self.OnSelectUser)
        self.passphraseBox = wx.TextCtrl(self.panel,pos=(150,200),size=(130,25))
        self.selectButton = wx.Button(self.panel,label="Select",pos=(150,240))
        self.selectButton.Bind(wx.EVT_BUTTON,self.OnSelectUserAccount)
        self.usernameLabel.Disable()
        self.usernameComboBox.Disable()
        self.Show(True)
        self.getDefaultSharedFolderPath()

    def OnSelectUser(self,e):
        self.userSelected = True
        USERNAME = self.namelist[self.usernameComboBox.GetStringSelection()]
        USER_ID = self.ndict[self.usernameComboBox.GetStringSelection()]
        USERKEY = USERNAME+"_"+str(USER_ID)+'_priv_key'
        self.log.write(os.path.join(CPABE.KEYS_PATH,USERKEY)+" ex:"+str(os.path.exists(os.path.join(CPABE.KEYS_PATH,USERKEY)))+"\n")
        if os.path.exists(os.path.join(CPABE.KEYS_PATH,USERKEY)):
            self.passphraseLabel.Disable()
            self.passphraseBox.Disable()
        else:
            self.passphraseLabel.Enable()
            self.passphraseBox.Enable()

    def OnSharedFolderSelected(self,e):
        if self.sharedFolderPathSelection.GetPath() and os.path.exists(self.sharedFolderPathSelection.GetPath()):
            CPABE.SHARED_FOLDER_PATH = self.sharedFolderPathSelection.GetPath()
        else:
            CPABE.SHARED_FOLDER_PATH = ""
        CPABE.ABEsafe_PATH = os.path.join(CPABE.SHARED_FOLDER_PATH,"ABEsafe")
        CPABE.CONFIG_PATH = os.path.join(CPABE.ABEsafe_PATH,".configs")
        CPABE.KEYS_PATH = os.path.join(os.path.join(CPABE.LOCAL_PATH,".keys"),os.path.relpath(CPABE.SHARED_FOLDER_PATH,"/"))
        CPABE.DATABASE = os.path.join(CPABE.CONFIG_PATH,CPABE.DATABASE_file)
        if not(os.path.exists(CPABE.ABEsafe_PATH) and os.path.exists(CPABE.CONFIG_PATH) and os.path.exists(CPABE.DATABASE)):
            self.nl=[]
            self.namelist = {}
            self.ndict = {}
            self.usernameComboBox.Clear()
            self.usernameLabel.Disable()
            self.usernameComboBox.Disable()
            self.userSelected = False
        else:
            connection = None
            try:
                connection = sqlite3.connect(CPABE.DATABASE)
                with connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT Staff_Id, Name FROM Users")
                    users = cursor.fetchall()
                    if len(users)==0:
                        self.nl = []
                        self.namelist = {}
                        self.ndict = {}
                    else:
                        self.nl = [user[1]+" (id: "+str(user[0])+")" for user in users]
                        self.namelist = {user[1]+" (id: "+str(user[0])+")":user[1] for user in users}
                        self.ndict = {user[1]+" (id: "+str(user[0])+")":user[0] for user in users}
                    self.usernameLabel.Enable()
                    self.usernameComboBox.Clear()
                    self.usernameComboBox.SetItems(self.nl)
                    self.usernameComboBox.Enable()
            except sqlite3.Error, e:
                if connection:
                    connection.rollback()
                self.log.write("Error %s"%e.args[0])
            except Exception as e:
                self.log.write("Error: %s"%e)
            finally:
                if connection:
                    connection.close()

    def OnSelectUserAccount(self,e):
        """
        Login window
        Need to check the username and password before access to the account
        """
        if self.sharedFolderPathSelection.GetPath():
            CPABE.SHARED_FOLDER_PATH = self.sharedFolderPathSelection.GetPath()
            folders = re.compile("/").split(CPABE.SHARED_FOLDER_PATH)
            if len(folders)>0:
                CPABE.SHARED_FOLDER_NAME = folders[-1]
                CPABE.HOME_PATH = CPABE.SHARED_FOLDER_PATH[:-len(CPABE.SHARED_FOLDER_NAME)] if CPABE.SHARED_FOLDER_PATH.endswith(CPABE.SHARED_FOLDER_NAME) else " "
                CPABE.HOME_PATH = CPABE.HOME_PATH if len(CPABE.HOME_PATH)<=1 else CPABE.HOME_PATH[:-1] 
            else:
                CPABE.SHARED_FOLDER_NAME = " "
        else:
            CPABE.SHARED_FOLDER_PATH = ""
        CPABE.ABEsafe_PATH = os.path.join(CPABE.SHARED_FOLDER_PATH,"ABEsafe")
        CPABE.KEYS_PATH = os.path.join(os.path.join(CPABE.LOCAL_PATH,".keys"),os.path.relpath(CPABE.SHARED_FOLDER_PATH,"/"))
        CPABE.CONFIG_PATH = os.path.join(CPABE.ABEsafe_PATH,".configs")
        CPABE.IMG_PATH = os.path.join(CPABE.ABEsafe_PATH,"userImages")
        CPABE.DATABASE = os.path.join(CPABE.CONFIG_PATH,CPABE.DATABASE_file)
        if not os.path.exists(CPABE.KEYS_PATH):
            os.makedirs(CPABE.KEYS_PATH)
        if not(os.path.exists(CPABE.ABEsafe_PATH) and os.path.exists(CPABE.CONFIG_PATH) and os.path.exists(CPABE.DATABASE)):
            wx.MessageBox("ABEsafe System is currently not built on this folder.","ABEsafe System not found",wx.OK)
            self.OnSharedFolderSelected(self.sharedFolderPathSelection)
            return
        elif self.userSelected == False:
            wx.MessageBox("Please select a user", "No user is selected",wx.OK)
            self.OnSharedFolderSelected(self.sharedFolderPathSelection)
            return
        else:
            global USER_ID, USERNAME, USERKEY,USERDEPARTMENT,USERPOSITION,USERSECLV
            try:
                USER_ID = self.ndict[self.usernameComboBox.GetStringSelection()]
                USERNAME = self.namelist[self.usernameComboBox.GetStringSelection()]
                USERKEY = USERNAME+"_"+str(USER_ID)+'_priv_key'
            except KeyError as ke:
                wx.MessageBox("User selected is invalid","Invalid user selected")
                return
            user = None
            connection = None
            try:
                connection = sqlite3.connect(CPABE.DATABASE)
                with connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT Department, Position, SecurityLevel FROM Users WHERE Staff_Id=%d AND Name='%s'"%(USER_ID,USERNAME))
                    user = cursor.fetchone()
                    if user is not None:
                        uservars = list(user)
                        cursor.execute("SELECT DepartmentName FROM department WHERE Department_Id=%d"%user[0])
                        uservars[0] = cursor.fetchone()[0]
                        cursor.execute("SELECT PositionName FROM position WHERE Position_Id=%d"%user[1])
                        uservars[1] = cursor.fetchone()[0]
                        user = tuple(uservars)
            except sqlite3.Error, e:
                if connection:
                    connection.rollback()
                self.log.write("Error: %s"%e.args[0])
            except Exception as e:
                self.log.write("Error: "%e)
            finally:
                if connection:
                    connection.close()
            passphrase = self.passphraseBox.GetValue()
            if self.passphraseBox.IsEnabled() and passphrase != "":
                decodedphrase = None
                try:
                    with open(os.path.join(CPABE.KEYS_PATH,USERKEY),mode='wb+') as f:
                        import base64
                        decodedphrase = passphrase.decode('base64')
                        f.write(decodedphrase)
                except:
                    wx.MessageBox("The passphrase is incorrect","incorrect passphrase")
                    os.remove(os.path.join(CPABE.KEYS_PATH,USERKEY))
                    return "decoding error"
                if not os.path.exists(os.path.join(CPABE.KEYS_PATH,USERKEY)):
                    self.log.write("Key does not exist right before decryption test")
                if not os.path.exists(os.path.join(CPABE.CONFIG_PATH,".%s_test"%(USERNAME+"_"+str(USER_ID)))):
                    self.log.write("Encrypted test file does not exist")

                status = CPABE.libc.abe_decrypt(str(os.path.join(CPABE.LOCAL_PATH,".tmpTest")), str(os.path.join(CPABE.CONFIG_PATH,".pub_key")), str(os.path.join(CPABE.KEYS_PATH,USERKEY)), str(os.path.join(CPABE.CONFIG_PATH,".%s_test"%(USERNAME+"_"+str(USER_ID)))))
                result = False
                if os.path.exists(os.path.join(CPABE.LOCAL_PATH,".tmpTest")):
                    readtext = None
                    with open(os.path.join(CPABE.LOCAL_PATH,".tmpTest"),'r') as f:
                        readtext = f.read()
                        if readtext=="OK":
                            wx.MessageBox("Login successful. Your account is saved.")
                            for (dirpath,dirnames,filenames) in os.walk(CPABE.KEYS_PATH):
                                for f in filenames:
                                    fname = os.path.join(dirpath,f)
                                    if fname != os.path.join(CPABE.KEYS_PATH,USERKEY):
                                        os.remove(fname)
                            result = True
                    os.remove(os.path.join(CPABE.LOCAL_PATH,".tmpTest"))
                    if readtext is not None:
                        self.log.write(readtext+"\n")
                else:
                    self.log.write(".tmpTest not exists error\n")
                if result == False:
                    os.remove(os.path.join(CPABE.KEYS_PATH,USERKEY))
                    wx.MessageBox("The passphrase is incorrect","incorrect passphrase")
                    self.log.write("incorrect passphrase\n")
                    self.OnSharedFolderSelected(self.sharedFolderPathSelection)
                    return
            elif self.passphraseBox.IsEnabled() and passphrase == "":
                wx.MessageBox("Please enter the secret passphrase","Secret Passphrase required")
                self.OnSharedFolderSelected(self.sharedFolderPathSelection)
                if os.path.exists(os.path.join(CPABE.KEYS_PATH,USERKEY)):
                    os.remove(os.path.join(CPABE.KEYS_PATH,USERKEY))
                return

            if user is None:
                if os.path.exists(os.path.join(CPABE.KEYS_PATH,USERKEY)):
                    try:
                        os.remove(os.path.join(CPABE.KEYS_PATH,USERKEY))
                    except:
                        pass
                    wx.MessageBox("User '%s' is not found in the system."%USERNAME,"User not found in this system",wx.OK)
                    self.OnSharedFolderSelected(self.sharedFolderPathSelection)
                    return
            else:
                USERDEPARTMENT = user[0]
                USERPOSITION = user[1]
                USERSECLV = user[2]
                CPABE.TMP = tempfile.mkdtemp(prefix='abesafe_')
                try:
                    os.makedirs(CPABE.TMP,0o700)
                except:
                    pass
                with open(os.path.join(CPABE.LOCAL_PATH,".path"),'w+') as f:
                    tpath = CPABE.SHARED_FOLDER_PATH[:-1] if CPABE.SHARED_FOLDER_PATH[-1]=="/" else CPABE.SHARED_FOLDER_PATH
                    f.write(tpath)

            self.parent.frame = MainFrame(stdout,"CPABE",SCREEN_SIZE)
            self.parent.frame.setupPanel()
            self.parent.SetTopWindow(self.parent.frame)
            self.parent.frame.Centre()
            self.parent.frame.Show(True)
            self.parent.frame.Raise()
            self.Destroy()

    def getDefaultSharedFolderPath(self):
        if os.path.exists(os.path.join(CPABE.LOCAL_PATH,".path")):
            tmp = None
            with open(os.path.join(CPABE.LOCAL_PATH,".path"),'r') as f:
                tmp = f.read()
            if os.path.exists(tmp):
                abesafep = os.path.join(tmp,"ABEsafe")
                cp = os.path.join(abesafep,".configs")
                d = os.path.join(cp,CPABE.DATABASE_file)
                if os.path.exists(abesafep) and os.path.exists(cp) and os.path.exists(d):
                    self.sharedFolderPathSelection.SetPath(tmp)
                    self.OnSharedFolderSelected(self.sharedFolderPathSelection)
        else:
            self.log.write(".path does not exist\n") 

    def OnClose(self,e):
        if self.userSelected == False:
            try:
                self.parent.frame.Close()
            except:
                pass
        else:
            if self.parent.frame:
                self.parent.frame.Show()
        self.Destroy()

if __name__=='__main__':
    os.putenv('PATH',os.getenv('PATH')+':.')
    stdout = open(os.path.join(CPABE.LOCAL_PATH,'.log'),'a+',0)
    tempdir = tempfile.gettempdir()
    dirs = os.listdir(tempdir)
    for a_dir in dirs:
        if re.match("abesafe_",a_dir):
            shutil.rmtree(os.path.join(tempdir,a_dir))
    MainApp(stdout).MainLoop()
