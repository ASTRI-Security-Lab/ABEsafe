import os
import sys
import re
import math
import shutil
import base64
import wx
import sqlite3

import logging, logging.handlers

from wx.lib.mixins.listctrl import ColumnSorterMixin
import wx.lib.delayedresult as DR
from ABEsafe_gen import ABEsafe_generator as GEN

TITLE_COLOR = wx.Colour(19, 57, 204)
LABEL_COLOR = wx.Colour(104, 94, 255)
USUAL_COLOR = wx.Colour(103, 195, 7)
LESS_COLOR = wx.Colour(255, 242, 35)
IGNORE_COLOR = wx.Colour(84, 88, 80)
FUN1_COLOR = wx.Colour(178, 77, 0)
FUN2_COLOR = wx.Colour(255, 181, 125)
FUN3_COLOR = wx.Colour(255, 154, 77)
FUN4_COLOR = wx.Colour(18, 160, 178)
FUN5_COLOR = wx.Colour(180, 246, 255)
FUN6_COLOR = wx.Colour(0, 200, 50)
BLACK_COLOR = wx.Colour(40, 40, 20)

SCREEN_SIZE = (640, 480)

departmentList = []
positionList = []
class AdminApp(wx.App):
    def __init__(self,log):
        wx.App.__init__(self)
        self.log = log
        LoginWindows(self,log)
    def OnInit(self):
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

class MainFrame(wx.Frame):
    def __init__(self,log,titlename,framesize):
        wx.Frame.__init__(self,None,title=titlename,size=framesize)
        self.log = log
        self.staffId = ""
        self.username = ""
        self.department = ""
        self.position = ""
        

    def setupPanel(self):
        global departmentList, positionList
        self.panel = wx.Panel(self)
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.createUserSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.staffIdSizer = wx.BoxSizer(wx.VERTICAL)
        self.usernameSizer = wx.BoxSizer(wx.VERTICAL)
        self.departmentSizer = wx.BoxSizer(wx.VERTICAL)
        self.positionSizer = wx.BoxSizer(wx.VERTICAL)
        self.lastColumnSizer = wx.BoxSizer(wx.VERTICAL)
        self.userListButtonSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.createUserStaffIdLabel = wx.StaticText(self.panel,label="Staff ID")
        self.createStaffIdTextBox = wx.TextCtrl(self.panel,size=(70,22),style=wx.TE_NOHIDESEL)
        self.staffIdSizer.Add(self.createUserStaffIdLabel,0,wx.ALL,5)
        self.staffIdSizer.Add(self.createStaffIdTextBox,1,wx.ALL,5)

        self.createUsernameLabel = wx.StaticText(self.panel,label="User name")
        self.createUsernameTextBox = wx.TextCtrl(self.panel,style=wx.TE_NOHIDESEL)
        self.usernameSizer.Add(self.createUsernameLabel,0,wx.ALL,5)
        self.usernameSizer.Add(self.createUsernameTextBox,1,wx.ALL,5)
                       
        self.loadDepartmentList()
        self.createDepartmentLabel = wx.StaticText(self.panel,label="Department")
        self.createUserDepartmentCombobox = wx.ComboBox(self.panel,size=(120,25),choices=departmentList)
        self.addDepartmentButton = wx.Button(self.panel,label="Add Department")
        self.addDepartmentButton.Bind(wx.EVT_BUTTON,self.onAddDepartmentClicked)
        self.addDepartmentButton.Disable()
        self.departmentSizer.Add(self.createDepartmentLabel,0,wx.ALL,5)
        self.departmentSizer.Add(self.createUserDepartmentCombobox,1,wx.ALL,5)
        self.departmentSizer.Add(self.addDepartmentButton,0,wx.ALL,5)
        
        self.loadPositionList()
        self.createPositionLabel = wx.StaticText(self.panel,label="Position")
        self.createUserPositionCombobox = wx.ComboBox(self.panel,size=(120,25),choices=positionList)
        self.addPositionButton = wx.Button(self.panel,label="Add Position")
        self.addPositionButton.Bind(wx.EVT_BUTTON,self.onAddPositionClicked)
        self.addPositionButton.Disable()
        self.positionSizer.Add(self.createPositionLabel,0,wx.ALL,5)
        self.positionSizer.Add(self.createUserPositionCombobox,1,wx.ALL,5)
        self.positionSizer.Add(self.addPositionButton,0,wx.ALL,5)
        
        self.createUserButton = wx.Button(self.panel,label="Create user")
        self.createUserButton.Bind(wx.EVT_BUTTON,self.onCreateNewUserClicked)
        self.createUserButton.Disable()
        self.lastColumnSizer.Add(self.createUserButton,0,wx.ALL,5)
        self.createUserSizer.Add(self.staffIdSizer,0,wx.ALL,5)
        self.createUserSizer.Add(self.usernameSizer,0,wx.ALL,5)
        self.createUserSizer.Add(self.departmentSizer,0,wx.ALL,5)
        self.createUserSizer.Add(self.positionSizer,0,wx.ALL,5)
        self.createUserSizer.Add(self.lastColumnSizer,0,wx.ALL|wx.EXPAND,5)
        self.mainSizer.Add(self.createUserSizer,0,wx.ALL,10)

        panel_pos = self.panel.GetPosition()
        panel_size = self.panel.GetSize()
        self.userdata = self.getUserList()
        self.userList = self.SortedListCtrl(self.panel,data=self.userdata)
        self.userList.InsertColumn(0,"Staff ID",width=80)
        self.userList.InsertColumn(1,"User name",width=220)
        self.userList.InsertColumn(2,"Department",width=150)
        self.userList.InsertColumn(3,"Position",width=150)
        dict_index = range(len(self.userdata))
        zipped = zip(dict_index,self.userdata)
        userDictionary = dict(zipped)
        items = userDictionary.items()
        for key,data in items:
            index = self.userList.InsertItem(sys.maxint,str(data[0]))
            self.userList.SetItem(index,1,str(data[1]))
            self.userList.SetItem(index,2,str(data[2]))
            self.userList.SetItem(index,3,str(data[3]))
            self.userList.SetItemData(index,key)
        self.userList.Bind(wx.EVT_LIST_ITEM_SELECTED,self.onUserListItemSelected)

        self.refreshUserListButton = wx.Button(self.panel,label="Refresh List")
        self.refreshUserListButton.Bind(wx.EVT_BUTTON,self.onRefreshButtonClicked)
        self.removeUserButton = wx.Button(self.panel,label="Remove User")
        self.removeUserButton.Bind(wx.EVT_BUTTON,self.onRemoveUserClicked)
        self.removeUserButton.Disable()
        self.passphraseUserButton = wx.Button(self.panel,label="Passphrase")
        self.passphraseUserButton.Bind(wx.EVT_BUTTON,self.showPassphrase)
        self.passphraseUserButton.Disable()
        self.userListButtonSizer.Add(self.refreshUserListButton,0,wx.ALL,5)
        self.userListButtonSizer.Add(self.removeUserButton,0,wx.ALL,5)
        self.userListButtonSizer.Add(self.passphraseUserButton,0,wx.ALL,5)
        self.mainSizer.Add(self.userListButtonSizer,0,wx.ALL,5)
        self.mainSizer.Add(self.userList,1,wx.ALL|wx.EXPAND,10)
        self.panel.SetSizer(self.mainSizer)

        self.checkNewGroupTimer = wx.CallLater(500,self.checkNewGroup)

    def updateUserList(self):
        self.userdata = self.getUserList()
        self.userList.DeleteAllItems()
        self.userList.itemDataMap = self.userdata
        dict_index = range(len(self.userdata))
        zipped = zip(dict_index,self.userdata)
        userDictionary = dict(zipped)
        items = userDictionary.items()
        for key,data in items:
            index = self.userList.InsertItem(sys.maxint,str(data[0]))
            self.userList.SetItem(index,1,data[1])
            self.userList.SetItem(index,2,data[2])
            self.userList.SetItem(index,3,data[3])
            self.userList.SetItemData(index,key)
    def onRefreshButtonClicked(self,e):
        self.updateUserList()

    class SortedListCtrl(wx.ListCtrl,ColumnSorterMixin):
        def __init__(self,parent,data):
            wx.ListCtrl.__init__(self,parent,style=wx.LC_REPORT|wx.LC_AUTOARRANGE|wx.LC_SORT_ASCENDING)
            ColumnSorterMixin.__init__(self,len(data))
            self.itemDataMap = data
        def GetListCtrl(self):
            return self

    def getUserList(self,no_id=True):
        connection = None
        users = None
        mappedUsers = []
        depart = None
        pos = None
        try:
            connection = sqlite3.connect(GEN.DATABASE)
            with connection:
                cursor = connection.cursor()
                cursor.execute("SELECT * FROM Users")
                users = cursor.fetchall()
                for (a_id,a_staff_id,a_name,a_departmentId,a_positionId,sec) in users:
                    try:
                        cursor.execute('SELECT DepartmentName FROM department WHERE Department_Id="%d"'%a_departmentId)
                        data = cursor.fetchall()
                        if data:
                            depart = data[0][0]
                        else:
                            self.log.warning("Invalid department name, " + str((a_id,a_staff_id,a_name,a_departmentId,a_positionId,sec)) + " is not added")
                            continue
                    except Exception, e:
                        logging.error(e)
                    try:
                        cursor.execute('SELECT PositionName FROM position WHERE Position_Id="%d"'%a_positionId)
                        data = cursor.fetchall()
                        if data:
                            pos = data[0][0]
                        else:
                            self.log.warning("Invalid position name, " + str((a_id,a_staff_id,a_name,a_departmentId,a_positionId,sec)) + " is not added")
                            continue
                    except Exception, e:
                        self.log.error(e)
                    if no_id:
                        mappedUsers += [(a_staff_id,a_name,depart,pos,sec)]
                    else:
                        mappedUsers += [(a_id,a_staff_id,a_name,depart,pos,sec)]
        except sqlite3.Error, e:
            if connection:
                connection.rollback()
                self.log.error(e.args[0])
        finally:
            if connection:
                connection.close()
        return mappedUsers
        

    def loadDepartmentList(self):
        global departmentList
        connection = None
        try:
            connection = sqlite3.connect(GEN.DATABASE)
            with connection:
                cursor = connection.cursor()
                cursor.execute("SELECT DepartmentName FROM department")
                data = cursor.fetchall()
                departmentList = []
                if data:
                    departmentList = [a_data[0] for a_data in data]
        except sqlite3.Error, e:
            if connection:
                connection.rollback()
                self.log.error(e.args[0])
        finally:
            if connection:
                connection.close()
    def loadPositionList(self):
        global positionList
        connection = None
        try:
            connection = sqlite3.connect(GEN.DATABASE)
            with connection:
                cursor = connection.cursor()
                cursor.execute("SELECT PositionName FROM position")
                data = cursor.fetchall()
                positionList = []
                if data:
                    positionList = [a_data[0] for a_data in data]
        except sqlite3.Error, e:
            if connection:
                connection.rollback()
                self.log.error(e.args[0])
            if connection:
                self.log.warning("Still have connection")
        finally:
            if connection:
                connection.close()
    def departmentValidation(self):
        departmentValidation = self.department.replace("_","")
        if not departmentValidation.isalnum():
            wx.MessageBox("Department contains special characters or spaces","Create New User failed",wx.OK)
            return False
        return True
    def positionValidation(self):
        positionValidation = self.position.replace("_","")
        if not positionValidation.isalnum():
            wx.MessageBox("Position contains special characters or spaces","Create New User failed",wx.OK)
            return False
        return True

    def onAddDepartmentClicked(self,e):
        if self.departmentValidation():
            confirm = wx.MessageDialog(self,'Are you sure to add new department "%s" ?'%self.department,"Confirm to add new department",wx.YES_NO|wx.NO_DEFAULT|wx.ICON_NONE)
            if confirm.ShowModal() != wx.ID_YES:
                return
            connection = None
            try:
                connection = sqlite3.connect(GEN.DATABASE)
                with connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT DepartmentName FROM department")
                    data = cursor.fetchall()
                    if data:
                        data = set([a_data[0] for a_data in data])
                        if self.department in data:
                            return "department already existed"
                        else:
                            cursor.execute("INSERT INTO department VALUES(NULL,'%s')"%self.department)
                            wx.MessageBox("Department '%s' has been successfully created"%self.department)
                    else:
                        cursor.execute("INSERT INTO department VALUES(NULL,'%s')"%self.department)
                        wx.MessageBox("Department '%s' has been successfully created"%self.department)
            except sqlite3.Error, e:
                if connection:
                    connection.rollback()
                self.log.error(e.args[0])
            finally:
                if connection:
                    connection.close()
            self.loadDepartmentList()
            self.createUserDepartmentCombobox.Clear()
            for a_department in departmentList:
                self.createUserDepartmentCombobox.Append(a_department)
        
    def onAddPositionClicked(self,e):
        if self.positionValidation():
            confirm = wx.MessageDialog(self,'Are you sure to add new position "%s" ?'%self.position,"Confirm to add new position",wx.YES_NO|wx.NO_DEFAULT|wx.ICON_NONE)
            if confirm.ShowModal() != wx.ID_YES:
                return
            connection = None
            try:
                connection = sqlite3.connect(GEN.DATABASE)
                with connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT PositionName FROM position")
                    data = cursor.fetchall()
                    if data:
                        data = {a_data[0] for a_data in data}
                        if self.position in data:
                            return "position already existed"
                        else:
                            cursor.execute("INSERT INTO position VALUES(NULL,'%s')"%self.position)
                            wx.MessageBox("Position '%s' has been successfully created"%self.position)
                    else:
                        cursor.execute("INSERT INTO position VALUES(NULL,'%s')"%self.position)
                        wx.MessageBox("Position '%s' has been successfully created"%self.position)
            except sqlite3.Error, e:
                if connection:
                    connection.rollback()
                self.log.error(e.args[0])
            finally:
                if connection:
                    connection.close()
            self.loadPositionList()
            self.createUserDepartmentCombobox.Clear()
            for a_department in departmentList:
                self.createUserDepartmentCombobox.Append(a_department)
        
    def onCreateNewUserClicked(self,e):
        try:
            staffId = int(self.createStaffIdTextBox.GetValue())
            self.updateUserList()
            existing_staffId = set([user[0] for user in self.userdata])
            if staffId in existing_staffId:
                wx.MessageBox("Staff ID already existed.","Create New User failed",wx.OK)
                return
            if staffId<=0:
                wx.MessageBox("Staff ID should be a positive integer","Create New User failed",wx.OK)
                return
        except ValueError:
            wx.MessageBox("Staff ID should be a positive integer","Create New User failed",wx.OK)
            return
        except Exception as e:
            self.log.error(e)
        usernameValidation = self.username.replace("_","")#''.join(self.username.split())
        if not usernameValidation.isalnum():
            wx.MessageBox("Username contains special characters or spaces","Create New User failed",wx.OK)
            return
        if not (self.departmentValidation() and self.positionValidation()):
            return
        connection = None
        try:
            connection = sqlite3.connect(GEN.DATABASE)
            with connection:
                cursor = connection.cursor()
                cursor.execute("SELECT Department_Id FROM department WHERE DepartmentName='%s'"%self.department)
                data = cursor.fetchall()
                depart_id = data[0][0]
                cursor.execute("SELECT Position_Id FROM position WHERE PositionName='%s'"%self.position)
                data = cursor.fetchall()
                pos_id = data[0][0]
                cursor.execute("SELECT * FROM Users WHERE Staff_Id='%d' AND Name='%s' AND department='%d' AND position='%d'"%(staffId,self.username,depart_id,pos_id))
                data = cursor.fetchall()
                if data:
                    wx.MessageBox("This user already has already been created before.")
                    return False
                cursor.execute("INSERT INTO Users VALUES(NULL,%d, '%s', '%d', '%d', NULL)"%(staffId,self.username,depart_id,pos_id))
                if GEN.generateKey(staffId,self.username,depart_id,pos_id,None):
                    if not os.path.exists(os.path.join(GEN.LOCAL_PATH,"userImages/default.jpg")):
                        print "default image " + os.path.join(GEN.LOCAL_PATH,"userImages/default.jpg") + " not found"
                    shutil.copyfile(os.path.join(GEN.LOCAL_PATH,"userImages/default.jpg"),os.path.join(GEN.IMG_PATH,self.username+"_"+str(staffId)+".jpg"))
                    f = None
                    code = None
                    with open(GEN.PRIV_NAME,mode='rb') as f:
                        src = f.read()
                        code = src.encode('base64')
                    oncreated = wx.Frame(self,title="User created",style=wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP,size=(300,220))
                    boxsizer = wx.BoxSizer(wx.VERTICAL)
                    createdlabel = wx.StaticText(oncreated,label="User '%s' has been successfully created."%self.username)
                    passphraselabel = wx.StaticText(oncreated,label="The secret passphrase for '%s' is:\n"%self.username)
                    passphrase = wx.TextCtrl(oncreated,value=code,size=(250,25),style=wx.HSCROLL)
                    copyButton = wx.Button(oncreated,label="Copy Passphrase")
                    self.Bind(wx.EVT_BUTTON,lambda event: self.onCopyPassphrase(event,passphrase.GetValue()),copyButton)
                    boxsizer.Add(createdlabel,0,wx.ALL|wx.ALIGN_CENTER,10)
                    boxsizer.Add(passphraselabel,0,wx.ALL|wx.ALIGN_CENTER,10)
                    boxsizer.Add(passphrase,0,wx.ALIGN_CENTER)
                    boxsizer.Add(copyButton,0,wx.ALL|wx.ALIGN_CENTER,10)
                    oncreated.SetSizer(boxsizer)
                    oncreated.Show(True)
                else:
                    cursor.execute("SELECT Id FROM Users WHERE Name='%s'"%self.username)
                    data = cursor.fetchall()
                    cursor.execute("DELETE FROM Users WHERE Id='%s'"%data[-1][0])
                GEN.PRIV_NAME = ""
        except sqlite3.Error, e:
            if connection:
                connection.rollback()
            self.log.error(e.args[0])
        finally:
            if connection:
                connection.close()
        GEN.PRIV_NAME = ""
        wx.CallLater(1000,self.updateUserList)

    def onRemoveUserClicked(self,e):
        selected_index = self.userList.GetNextSelected(-1)
        selected_item = self.userdata[selected_index]
        confirm = wx.MessageDialog(self,"Are you sure you want to delete user '%s'"%selected_item[1],"Deleting User",wx.YES_NO|wx.NO_DEFAULT|wx.ICON_NONE)
        if confirm.ShowModal() != wx.ID_YES:
            return False
        connection = None
        try:
            connection = sqlite3.connect(GEN.DATABASE)
            with connection:
                cursor = connection.cursor()
                cursor.execute("SELECT Department_Id FROM department WHERE DepartmentName='%s'"%selected_item[2])
                depart = cursor.fetchall()[0][0]
                cursor.execute("SELECT Position_Id FROM position WHERE PositionName='%s'"%selected_item[3])
                pos = cursor.fetchall()[0][0]
                cursor.execute("DELETE FROM Users WHERE Staff_Id='%d' AND Name='%s' AND Department='%d' AND Position='%d'"%(int(selected_item[0]),selected_item[1],depart,pos))
                try:
                    os.remove(os.path.join(GEN.KEYS_PATH,"%s_priv_key"%(selected_item[1]+"_"+str(selected_item[0]))))
                except:
                    pass
                try:
                    os.remove(os.path.join(GEN.KEYS_PATH,"%s_priv_key_meta"%(selected_item[1]+"_"+str(selected_item[0]))))
                except:
                    pass
                wx.MessageBox("User '%s' has been successfully deleted"%selected_item[1])
                
        except sqlite3.Error, e:
            if connection:
                connection.rollback()
            wx.MessageBox("User '%s' deletion failed due to data inconsistency"%selected_item[1])
            self.log(e.args[0])
        except ValueError as e:
            wx.MessageBox("The selected user account contains some poor values.")
        finally:
            if connection:
                connection.close()
        wx.CallLater(1000,self.updateUserList)
        self.removeUserButton.Disable()
        self.passphraseUserButton.Disable()
    def onUserListItemSelected(self,e):
        self.removeUserButton.Enable()
        self.passphraseUserButton.Enable()

    def checkNewGroup(self):
        self.department = self.createUserDepartmentCombobox.GetValue()
        self.position = self.createUserPositionCombobox.GetValue()
        if self.department and not self.department in departmentList:
            self.addDepartmentButton.Enable()
        else:
            self.addDepartmentButton.Disable()
        if self.position and not self.position in positionList:
            self.addPositionButton.Enable()
        else:
            self.addPositionButton.Disable()
        self.checkCreateUser()
        self.checkNewGroupTimer.Restart(500)

    def checkCreateUser(self):
        self.staffId = self.createStaffIdTextBox.GetValue()
        self.username = self.createUsernameTextBox.GetValue()
        if self.staffId and self.username and self.department and self.position and not self.addDepartmentButton.IsEnabled() and not self.addPositionButton.IsEnabled():
            self.createUserButton.Enable()
        else:
            self.createUserButton.Disable()

    def showPassphrase(self,e):
        f = None
        code = None
        selected_index = self.userList.GetNextSelected(-1)
        selected_item = self.userdata[selected_index]
        user_id = selected_item[0]
        user_name = selected_item[1]
        department = selected_item[2]
        position = selected_item[3]
        privkey_filename = user_name + "_" +str(user_id)
        GEN.PRIV_NAME = os.path.join(GEN.KEYS_PATH,"%s_priv_key"%(privkey_filename))
        try:
            with open(GEN.PRIV_NAME,mode='rb') as f:
                import base64
                src = f.read()
                code = src.encode('base64')
            if code is None:
                self.log.warning("Key cannot be encoded")
        except:
            wx.MessageBox("Key for '%s' does not exist"%user_name,"Key does not exist")
            return
        oncreated = wx.Frame(self,title="User passphrase",style=wx.DEFAULT_FRAME_STYLE|wx.STAY_ON_TOP,size=(300,170))
        boxsizer = wx.BoxSizer(wx.VERTICAL)
        passphraselabel = wx.StaticText(oncreated,label="The secret passphrase for '%s' is:\n"%user_name)
        passphrase = wx.TextCtrl(oncreated,value=code,size=(250,25))
        copyButton = wx.Button(oncreated,label="Copy Passphrase")
        self.Bind(wx.EVT_BUTTON,lambda event: self.onCopyPassphrase(event,passphrase.GetValue()),copyButton)
        boxsizer.Add(passphraselabel,0,wx.ALL|wx.ALIGN_CENTER,10)
        boxsizer.Add(passphrase,0,wx.ALIGN_CENTER)
        boxsizer.Add(copyButton,0,wx.ALL|wx.ALIGN_CENTER,10)
        oncreated.SetSizer(boxsizer)
        oncreated.Show(True)
    def onCopyPassphrase(self,e,code):
        clipdata = wx.TextDataObject()
        clipdata.SetText(code)
        wx.TheClipboard.Open()
        wx.TheClipboard.SetData(clipdata)
        wx.TheClipboard.Close()

class LoginWindows(wx.Frame):
    def __init__(self,parent,log):
        self.parent = parent
        self.log = log
        self.userSelected = False
        self.nl = []
        self.ndict = {}
        wx.Frame.__init__(self,None,size=(400,200),title="ABEsafe Admin Tool",style=wx.DEFAULT_FRAME_STYLE)
        self.Bind(wx.EVT_CLOSE,self.OnClose)
        self.panel = wx.Panel(self,size=(400,200))
        login_font = wx.Font(16,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD,False)
        login_label = wx.StaticText(self,label="Select your admin account",pos=(100,50))
        login_label.SetFont(login_font)
        login_label.SetForegroundColour(wx.BLUE)
        login_font = wx.Font(14,wx.FONTFAMILY_DEFAULT,wx.FONTSTYLE_SLANT,wx.FONTWEIGHT_NORMAL,False)
        self.sharedFolderLabel = wx.StaticText(self,label="Shared Folder",pos=(20,100))
        self.sharedFolderLabel.SetFont(login_font)
        self.sharedFolderLabel.SetForegroundColour(wx.BLUE)
        self.sharedFolderPathSelection = wx.DirPickerCtrl(self.panel,message="Select ABEsafe folder directory",pos=(145,100))
        self.sharedFolderPathSelection.Bind(wx.EVT_DIRPICKER_CHANGED,self.OnSharedFolderSelected)
        self.selectButton = wx.Button(self.panel,label="Select",pos=(150,140))
        self.selectButton.Bind(wx.EVT_BUTTON,self.OnSelectUserAccount)
        self.Show(True)
        self.getDefaultSharedFolderPath()
        self.selectButton.SetLabel("Select" if self.checkSystemExist() else "Create")

    def checkSystemExist(self):
        if self.sharedFolderPathSelection.GetPath():
            GEN.SHARED_FOLDER_PATH = self.sharedFolderPathSelection.GetPath()
        else:
            GEN.SHARED_FOLDER_PATH = ""

        GEN.ABEsafe_PATH = os.path.join(GEN.SHARED_FOLDER_PATH,"ABEsafe")
        GEN.KEYS_PATH = os.path.join(".keys",GEN.SHARED_FOLDER_PATH)
        GEN.CONFIG_PATH = os.path.join(GEN.ABEsafe_PATH,".configs")
        GEN.IMG_PATH = os.path.join(GEN.ABEsafe_PATH,"userImages")
        GEN.DATABASE = os.path.join(GEN.CONFIG_PATH,GEN.DATABASE_file)
        
        if not os.path.exists(GEN.KEYS_PATH):
            os.makedirs(GEN.KEYS_PATH)
        if not(os.path.exists(GEN.ABEsafe_PATH) and os.path.exists(GEN.CONFIG_PATH) and os.path.exists(GEN.IMG_PATH) and os.path.exists(GEN.DATABASE)):
            return False
        else:
            return True

    def OnSharedFolderSelected(self,e):
        if not self.checkSystemExist():
            self.nl=[]
            self.ndict = {}
        else:
            connection = None
            try:
                connection = sqlite3.connect(GEN.DATABASE)
                with connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT Staff_Id, Name FROM Users")
                    users = cursor.fetchall()
                    self.nl = [user[1]+" (id: "+str(user[0])+")" for user in users]
                    self.ndict = {user[1]+" (id: "+str(user[0])+")":user[0] for user in users}
            except sqlite3.Error, e:
                if connection:
                    connection.rollback()
                self.log.error(e.args[0])
            except Exception as e:
                self.log.error(e)
            finally:
                if connection:
                    connection.close()
        self.selectButton.SetLabel("Select" if self.checkSystemExist() else "Create")

    def saveSelectedPath(self):
        pathexist = True if os.path.exists(os.path.join(GEN.LOCAL_PATH,".path")) else False
        f = None
        tmp = None
        tpath = None
        if pathexist:
            with open(os.path.join(GEN.LOCAL_PATH,".path"),'r') as f:
                tmp = f.read()
                tpath = "" if len(GEN.SHARED_FOLDER_PATH)==0 else GEN.SHARED_FOLDER_PATH[:-1] if GEN.SHARED_FOLDER_PATH[-1]=="/" else GEN.SHARED_FOLDER_PATH
        else:
            tpath = ""
        if tmp != tpath or pathexist==False:
            with open(os.path.join(GEN.LOCAL_PATH,".path"),'w+') as f:
                f.write(tpath)

    def OnSelectUserAccount(self,e):
        """
        Login window
        Need to check the username and password before access to the account
        """
        if not self.checkSystemExist():
            createdABEsafeConfirm = wx.MessageDialog(self,"ABEsafe System is currently not built on this folder,\nDo you want to build ABEsafe System on this folder?","Build a new ABEsafe System",wx.YES_NO|wx.YES_DEFAULT|wx.ICON_NONE)
            if createdABEsafeConfirm.ShowModal() == wx.ID_YES:
                sampleUserSetCofirm = wx.MessageDialog(self,"Do you want to add sample users, department and position?","Sample dataset",wx.YES_NO|wx.YES_DEFAULT|wx.ICON_NONE)
                if sampleUserSetCofirm.ShowModal() == wx.ID_YES:
                    GEN.ABEsafe_gensystem(self.log,GEN.SHARED_FOLDER_PATH,True)
                else:
                    GEN.ABEsafe_gensystem(self.log,GEN.SHARED_FOLDER_PATH,False)
                wx.MessageBox("ABEsafe has been successfully deployed.")
                with open(os.path.join(GEN.LOCAL_PATH,".path"),'w+') as f:
                    tpath = GEN.SHARED_FOLDER_PATH[:-1] if GEN.SHARED_FOLDER_PATH[-1]=="/" else GEN.SHARED_FOLDER_PATH
                    f.write(tpath)
                self.getDefaultSharedFolderPath()

        self.parent.frame = MainFrame(self.log,"ABEsafe admin tools",SCREEN_SIZE)
        self.parent.frame.setupPanel()
        self.parent.SetTopWindow(self.parent.frame)
        self.parent.frame.Centre()
        self.parent.frame.Show(True)
        self.parent.frame.Raise()
        self.Destroy()

    def getDefaultSharedFolderPath(self):
        if os.path.exists(os.path.join(GEN.LOCAL_PATH,".path")):
            f = open(os.path.join(GEN.LOCAL_PATH,".path"),'r')
            tmp = f.readline()
            f.close()
            if os.path.exists(tmp):
                abesafep = os.path.join(tmp,"ABEsafe")
                cp = os.path.join(abesafep,".configs")
                d = os.path.join(cp,GEN.DATABASE_file)
                if os.path.exists(abesafep) and os.path.exists(cp) and os.path.exists(d):
                    self.sharedFolderPathSelection.SetPath(tmp)
                    self.OnSharedFolderSelected(self.sharedFolderPathSelection)
        else:
            self.log.info(".path does not exist")

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
    logger = logging.getLogger('history')
    logger.setLevel(logging.INFO)
    handler = logging.handlers.RotatingFileHandler('history.log', maxBytes=1<<12, backupCount=5)
    handler.setFormatter(logging.Formatter('%(asctime)s %(levelname)-8s %(funcName)s %(message)s'))
    logger.addHandler(handler)
    AdminApp(logger).MainLoop()
