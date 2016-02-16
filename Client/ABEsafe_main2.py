#!/usr/bin/python

import wx
import os
import re
import sys

import sqlite3
from wx.lib.mixins.listctrl import ColumnSorterMixin
import searchbar as SB
import wx.lib.agw.ultimatelistctrl as ULC
from ABEsafe_process import CPABE

IDCON_SIZE = 100
TOUT_INFO = 2000

class CipherSpecPanel(wx.Panel):
    def __init__(self,parent,size):
        wx.Panel.__init__(self,parent,wx.ID_ANY,size=size)
        self.SetBackgroundColour(wx.RED)

class ABEmain2(wx.Panel):
    def __init__(self, parent, log, pos=wx.DefaultPosition, size=wx.DefaultSize):
        wx.Panel.__init__(self, parent, wx.ID_ANY, pos=pos, size=size)
        self.parent = parent
        self.log = log
        self.enabled = True
        self.policy = {}
        self.pj_mkey = {}
        self.attributeList = []
        self.policyGUI_frame = PolicyGUI_frame(self)
        
        #SEARCH BOX
        self.p_policy = SB.PolicyPanel(self,self.log)
        self.p_policy.SetBackgroundColour("white")
        
        #ELIGIBLE WALL
        self.il = ULC.PyImageList(IDCON_SIZE, IDCON_SIZE, True)
        nl = []
        files = sorted(os.listdir(CPABE.IMG_PATH))
        for f in files:
            m_idcon = re.search(r'^(([A-z]|[0-9])+)_[0-9]+\.jpg$',f)
            if m_idcon:
                bmp = wx.Image(os.path.join(CPABE.IMG_PATH,f),wx.BITMAP_TYPE_JPEG).Rescale(IDCON_SIZE,IDCON_SIZE).ConvertToBitmap()
                self.il.Add(bmp)
                nl.append(m_idcon.group(1))
        self.ulc_eliwall = ULC.UltimateListCtrl(self, -1, agwStyle=wx.LC_ICON | wx.LC_AUTOARRANGE )
        self.ulc_eliwall.AssignImageList(self.il, wx.IMAGE_LIST_NORMAL)
        self.ndict = {}
        attrDictList = []
        connection = None
        try:
            connection = sqlite3.connect(CPABE.DATABASE)
            with connection:
                cursor = connection.cursor()

                #fetch all attributes from the database
                cursor.execute("SELECT * FROM sqlite_master where type='table'")
                data = cursor.fetchall()
                attriList = filter(lambda x:x!="Users" and x!="sqlite_sequence",map(lambda x:x[1],data))
                self.attributeList = attriList

                for attri in attriList:
                    cursor.execute("SELECT * FROM %s"%attri)
                    data = cursor.fetchall()
                    attriDict = {a_data[0]:a_data[1] for a_data in data}
                    attrDictList += [attriDict]
                
                for name in nl:
                    userinfoquery = "SELECT Staff_Id, %s FROM Users WHERE Name = '%s'"%(', '.join(attriList),name)
                    cursor.execute(userinfoquery)
                    record = cursor.fetchone()
                    if record is not None and len(record)==1+len(attriList):
                        self.ndict[name] = set([str(record[0])]+list(map(lambda x:attrDictList[x][record[x+1]],range(len(record)-1))))
        except sqlite3.Error, e:
            if connection:
                connection.rollback()
            self.log.write("Error: %s"%e.args[0])
        except Exception as e:
            self.log.write("Error: %s"%e)
        finally:
            if connection:
                connection.close()
        for i in range(0,len(nl)):
            self.ulc_eliwall.InsertImageStringItem(i, nl[i], i)
        self.ulc_eliwall.Bind(wx.EVT_LIST_ITEM_SELECTED,self.onEli)

        #DOCK
        self.dock = wx.Panel(self)
        cancelImage = wx.Image(os.path.join(CPABE.LOCAL_PATH,'img/ic_action_back_b.png'))
        cancelImage.Rescale(40,40)
        self.cancelButton = wx.BitmapButton(self.dock,bitmap=wx.Bitmap(cancelImage),pos=(10,240))
        self.cancelButton.Bind(wx.EVT_BUTTON,self.onCancelButtonClicked)
        self.cancelLabel = wx.StaticText(self.dock,label="Cancel",pos=(10,225),style=wx.ALIGN_CENTRE)
        self.cancelLabel.SetFont(wx.Font(12,wx.DEFAULT,wx.NORMAL,weight=wx.BOLD))
        encryptImage = wx.Image(os.path.join(CPABE.LOCAL_PATH,'img/ic_action_secure_b.png'))
        encryptImage.Rescale(40,40)
        encryptDisabledImage = wx.Image(os.path.join(CPABE.LOCAL_PATH,'img/ic_action_secure_w.png'))
        encryptDisabledImage.Rescale(40,40)
        self.encryptButton = wx.BitmapButton(self.dock,bitmap=wx.Bitmap(encryptImage),pos=(560,240))
        self.encryptButton.SetBitmapDisabled(wx.Bitmap(encryptDisabledImage))
        self.encryptButton.Bind(wx.EVT_BUTTON,self.callEncrypt)
        self.encryptButton.Disable()
        self.encryptLabel = wx.StaticText(self.dock,label="Encrypt",pos=(555,225),style=wx.ALIGN_CENTRE)
        self.encryptLabel.SetFont(wx.Font(12,wx.DEFAULT,wx.NORMAL,weight=wx.BOLD))
        self.encryptLabel.Disable()

        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.policy_plaintextLabel = wx.StaticText(self,label="Policy in plain text")
        self.policy_plaintextLabel.SetFont(wx.Font(14,wx.SWISS,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD,False))
        self.policy_plaintextLabel.SetBackgroundColour("white")
        self.mainSizer.Add(self.policy_plaintextLabel,0,wx.EXPAND)
        self.mainSizer.Add(self.p_policy, 0, wx.EXPAND, wx.ALL)
        self.userlistLabel = wx.StaticText(self,label="List of all other users")
        self.userlistLabel.SetFont(wx.Font(14,wx.SWISS,wx.FONTSTYLE_NORMAL,wx.FONTWEIGHT_BOLD,False))
        self.userlistLabel.SetBackgroundColour("white")
        self.mainSizer.Add(self.userlistLabel,0, wx.EXPAND)
        self.mainSizer.Add(self.ulc_eliwall, 1, wx.EXPAND, 0)
        self.mainSizer.Add(self.dock)
        self.SetSizer(self.mainSizer)
        self.timer = wx.CallLater(1500,self.validatePolicy)

    def onCancelButtonClicked(self,e):
        self.parent.goto1()

    def hideHintBox(self):
        self.p_policy.OnSTC_AutoCompCancel()

    def onEli(self,ev):
        name = ev.GetLabel()
        info = list(self.ndict[name])
        self.parent.setInfo(name,info[0],info[1],info[2],info[3])

    def unsetToaster(self):
        self.hasToaster = False

    def focusOnEntry(self):
        self.p_policy.search.SetFocus()

    def focusOnExit(self):
        if(self.policyGUI_frame):
            self.policyGUI_frame.Close()
        self.parent.SetFocus()

    def getPolicy(self):
        return self.p_policy.getPolicy()

    def eligibles(self):
        '''balance () check: push/pop stack'''
        '''bsw result check'''
        eligibles = []
        if self.validate():
            self.p_policy.SetBackgroundColour(wx.WHITE)
        else:
            self.p_policy.SetBackgroundColour(wx.RED)
            return eligibles
        pol = self.getPolicy()
        files = sorted(os.listdir(CPABE.IMG_PATH))
        for f in files:
            m_priv = re.search(r'(\w+)_priv_key_meta$',f)
            if m_priv:
                i = len(self.pj_mkey)
                CPABE.runcpabe(CPABE.MKEY,i,self.oneligibles,pol,f)
                self.pj_mkey[i] = m_priv.group(1)

    def validate(self):
        pol = self.p_policy.getPolicy()
        if not os.path.exists(CPABE.CONFIG_PATH):
            wx.MessageBox("ABEsafe system is not connected.")
            self.parent.parent.Destroy()
        return True if CPABE.runcpabe(CPABE.POK,None,None,pol)==0 else False

    def validatePolicy(self):
        if self.validate():
            self.encryptButton.Enable()
            self.encryptLabel.Enable()
        else:
            self.encryptButton.Disable()
            self.encryptLabel.Disable()
        if self.parent.page==2:
            self.timer.Restart(2000)

    def callEncrypt(self,e):
        self.parent.parent.showMessage("Start encrypting...","blue")
        self.callEncryptTimer = wx.CallLater(100,self.parent.encrypt)

    def SearchDir(self):
        self.ulc_eliwall.ClearAll()
        self.il = ULC.PyImageList(IDCON_SIZE, IDCON_SIZE, True)
        self.nl = []
        self.pj_mkey = {}
        self.eligibles()

    def oneligibles(self,DR):
        res = DR.get()
        jid = DR.getJobID()
        if res==2:
            self.log.write('[oneligibles] il:%s\n'%self.il.GetImageCount())
            bmp = wx.Image(os.path.join(CPABE.IMG_PATH,'%s_priv_key.png'%self.pj_mkey[jid]),wx.BITMAP_TYPE_PNG).Scale(IDCON_SIZE,IDCON_SIZE).ConvertToBitmap()
            self.il.Add(bmp)
            self.nl.append(self.pj_mkey[jid])
            self.ulc_eliwall.ClearAll()
            self.ulc_eliwall.AssignImageList(self.il, wx.IMAGE_LIST_NORMAL)
            for i in range(0,len(self.nl)):
                self.ulc_eliwall.InsertImageStringItem(i, self.nl[i], i)
        del self.pj_mkey[jid]

    def OnZoomFactor(self, event):
        value = event.GetInt()
        event.Skip()

    def OnZoomColour(self, event):
        colour = event.GetValue()

    def OnCenterZoom(self, event):
        wx.CallAfter(self.ReLayout)

    def OnShowLabels(self, event):
        wx.CallAfter(self.ReLayout)

    def OnEnable(self, event):
        self.enabled = not self.enabled
        obj = event.GetEventObject()
        obj.Refresh()

    def OnButtonSize(self, event):
        value = event.GetValue()
        event.Skip()
        if value < 32 or value > 72:
            return
        wx.CallAfter(self.ReLayout)

    def createPolicyGUI(self):
        self.policyGUI_frame = PolicyGUI_frame(self)

    def ReLayout(self):
        self.Layout()
        self.Refresh()
        self.Update()

class PolicyGUI_frame(wx.Frame):
    def __init__(self,parent):
        wx.Frame.__init__(self,parent,title="Policy Selection",size=(700,500))
        self.policyGUI_panel = wx.Panel(self)
        self.attributeList = parent.attributeList
        self.mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.wrapSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.groupSizer = wx.BoxSizer(wx.VERTICAL)
        self.userSizer = wx.BoxSizer(wx.VERTICAL)
        self.attributeSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.parent = parent
        self.titleLabel = wx.StaticText(self.policyGUI_panel,label="Select the group of users you want to share to")
        self.titleLabel.SetFont(wx.Font(14,wx.DEFAULT,wx.NORMAL,wx.BOLD))
        self.rule = self.Rule_box(self.policyGUI_panel,self,(0,30))
        self.resetButton = wx.Button(self.policyGUI_panel,label="Reset Group")
        self.resetButton.Bind(wx.EVT_BUTTON, self.OnReset)
        self.addGroupButton = wx.Button(self.policyGUI_panel,label="Add Group")
        self.addGroupButton.Bind(wx.EVT_BUTTON, self.OnAddGroup)
        self.groupConfirmButton = wx.Button(self.policyGUI_panel,label="Confirm groups")
        self.groupConfirmButton.Bind(wx.EVT_BUTTON, self.OnConfirmGroup)
        self.confirmButton = wx.Button(self.policyGUI_panel, label='Confirm users')
        self.confirmButton.Bind(wx.EVT_BUTTON, self.OnConfirmRule)
        self.buttonSizer.Add(self.resetButton,0,wx.ALL|wx.ALIGN_RIGHT,5)
        self.buttonSizer.Add(self.addGroupButton,0,wx.ALL|wx.ALIGN_RIGHT,5)
        self.buttonSizer.Add(self.groupConfirmButton,0,wx.ALL|wx.ALIGN_RIGHT,5)
        self.buttonSizer.Add(150,10)
        self.buttonSizer.Add(self.confirmButton,0,wx.ALL|wx.ALIGN_RIGHT,5)
        self.buttonSizer.Add(20,10)
        self.groupSizer.Add(self.titleLabel,0,wx.ALL,5)
        self.groupSizer.Add(self.attributeSizer,0,wx.ALL,5)

        self.wrapSizer.Add(self.groupSizer,1,wx.ALL,5)
        self.wrapSizer.Add(50,10)
        self.wrapSizer.Add(self.userSizer,1,wx.ALL,5)
        self.mainSizer.Add(self.wrapSizer,0,wx.ALL,0)
        self.mainSizer.Add(self.buttonSizer,0,wx.ALIGN_RIGHT)

        self.rule.userTitleLabel.Disable()
        self.rule.userBox.Disable()
        self.rule.userSelectedLabel.Disable()
        
        #Disable the listctrl
        self.rule.userSelectedListCtrl.SetEvtHandlerEnabled(False)
        self.rule.userSelectedListCtrl.SetBackgroundColour(wx.Colour(220,220,220))
        self.rule.userAvailableListCtrl.SetEvtHandlerEnabled(False)
        self.rule.userAvailableListCtrl.SetBackgroundColour(wx.Colour(220,220,220))
        self.rule.userDeselectButton.Disable()
        self.rule.userSelectButton.Disable()

        self.confirmButton.Disable()
        self.policyGUI_panel.SetSizer(self.mainSizer)
        self.error_message = ""
        self.policy = ""
        self.empty_rule_restriction = False
        self.attri_string = []


    def OnReset(self,e):
        for i in range(len(self.rule.attriAvailableList)):
            self.rule.attriAvailableList[i] += self.rule.attriSelectedList[i]
            self.rule.attriSelectedList[i] = []
            self.rule.refreshList(self.rule.attriSelectedListCtrl[i],self.rule.attriSelectedList[i])
            self.rule.refreshList(self.rule.attriAvailableListCtrl[i],self.rule.attriAvailableList[i])
            self.rule.attri_radioButton_Any[i].SetValue(True)
        self.rule.userAvailableList += self.rule.userSelectedList
        self.rule.userSelectedList = []
        self.rule.refreshList(self.rule.userSelectedListCtrl,self.rule.userSelectedList,True)
        self.rule.refreshList(self.rule.userAvailableListCtrl,self.rule.userAvailableList,True)
            
    def OnAddGroup(self,e):
        rule_string = self.parsePolicyStringFromOptions()
        if(rule_string != ""):
            if(self.parent.p_policy.search.GetText().strip() != ""):
                self.parent.p_policy.search.AppendText(" | ")
            self.parent.p_policy.search.AppendText(rule_string.strip())
            wx.MessageBox("Selected group is added.","Group added")
            self.OnReset(e)
            self.parent.validatePolicy()

    def OnConfirmGroup(self,e):
        rule_string = self.parsePolicyStringFromOptions(False)
        if(rule_string != ""):
            selectConfirm = wx.MessageDialog(self,"You have selected some options for current group, do you want to add this group?","Add a new group",wx.YES_NO|wx.YES_DEFAULT)
            if selectConfirm.ShowModal() == wx.ID_YES:
                if(self.parent.p_policy.search.GetText().strip() != ""):
                    self.parent.p_policy.search.AppendText(" | ")
                self.parent.p_policy.search.AppendText(rule_string.strip())
                self.OnReset(e)
                self.parent.validatePolicy()
        self.resetButton.Disable()
        self.addGroupButton.Disable()
        self.groupConfirmButton.Disable()
        self.titleLabel.Disable()

        #Disable listctrl
        for index in range(len(self.rule.attributeList)):
            self.rule.attriSelectedListCtrl[index].SetEvtHandlerEnabled(False)
            self.rule.attriSelectedListCtrl[index].SetBackgroundColour(wx.Colour(220,220,220))
            self.rule.attriAvailableListCtrl[index].SetEvtHandlerEnabled(False)
            self.rule.attriAvailableListCtrl[index].SetBackgroundColour(wx.Colour(220,220,220))
            self.rule.attriDeselectButton[index].Disable()
            self.rule.attriSelectButton[index].Disable()
            self.rule.attri_box[index].Disable()

        self.rule.userTitleLabel.Enable()
        self.rule.userBox.Enable()
        self.rule.userSelectedLabel.Enable()
        self.rule.userSelectedListCtrl.SetEvtHandlerEnabled(True)
        self.rule.userSelectedListCtrl.SetBackgroundColour(wx.Colour(255,255,255))
        self.rule.userAvailableListCtrl.SetEvtHandlerEnabled(True)
        self.rule.userAvailableListCtrl.SetBackgroundColour(wx.Colour(255,255,255))
        self.rule.userDeselectButton.Enable()
        self.rule.userSelectButton.Enable()
        self.confirmButton.Enable()

    def OnConfirmRule(self,e):
        if len(self.rule.userSelectedList)>0:
            for user in self.rule.userSelectedList:
                if(self.parent.p_policy.search.GetText().strip() != ""):
                    self.parent.p_policy.search.AppendText(" | (staffId = %s)"%user[1])
                else:
                    self.parent.p_policy.search.AppendText("(staffId = %s)"%user[1])
        elif self.parent.p_policy.search.GetText().strip() == "":
            wx.MessageBox("You must select some users you want to share to, since you have not specify any group.","Please select some users for sharing")
            return
        self.parent.parent.parent.Raise()
        self.parent.focusOnEntry()
        self.parent.validatePolicy()

    def parsePolicyStringFromOptions(self,promptWarning=True):
        self.policy = ""
        for i in range(len(self.attributeList)):
            self.attri_string += [self.getAttributeString(i)]

        for index in range(len(self.rule.attributeList)):
            if ((not self.rule.attri_radioButton_Any[index].GetValue()) and self.attri_string[index] == ""):
                if promptWarning:
                    self.pop_error_when_parsing()
                return ""

        for index in range(len(self.rule.attributeList)):
            if (not self.rule.attri_radioButton_Any[index].GetValue()):
                if self.policy != "":
                    self.policy += " & "
                self.policy += self.attri_string[index]
        if self.policy == "":
            if promptWarning:
                self.pop_empty_rule_restriction()
            return ""
        return "("+self.policy+")"
        
    def getAttributeString(self,attri_index):
        attribute_string = ""
        if(not self.rule.attri_radioButton_Any[attri_index].GetValue()):
            anyChecked = False
            if len(self.rule.attriSelectedList[attri_index])<=0:
                self.error_message += "- No item is selection for %s options.\n"%self.attributeList[attri_index]
                return ""
            else:
                attribute_string = "("
                for x in self.rule.attriSelectedList[attri_index]:
                    attribute_string += "%s_%s | "%(self.attributeList[attri_index],str(self.rule.attriDictionary[attri_index][x]))
                attribute_string = attribute_string[:-3]+")"
        return attribute_string

    def pop_error_when_parsing(self):
        dialog = wx.MessageDialog(self,self.error_message,"Error when submitting", wx.OK|wx.ICON_INFORMATION)
        self.error_message = ""
        dialog.ShowModal()

    def pop_empty_rule_restriction(self):
        dialog = wx.MessageDialog(self,"No restriction on the group to access the encrypted file.\n","No restriction",wx.OK|wx.ICON_EXCLAMATION)
        dialog.ShowModal()

    def confirmed_empty_rule_restriction(self,e):
        self.empty_rule_restriction = True

    class Rule_box(wx.Panel):
        def __init__(self,parent,p_frame,offset=(0,0)):
            wx.Panel.__init__(self,parent)
            self.parent = parent
            self.attributeList = []

            self.userAvailableList = []
            self.attriDictionary = []
            self.attriAvailableList = []
            connection = None
            try:
                connection = sqlite3.connect(CPABE.DATABASE)
                with connection:
                    cursor = connection.cursor()
                    cursor.execute("SELECT * FROM sqlite_master WHERE type='table'") 
                    data = cursor.fetchall()
                    self.attributeList = filter(lambda x:x!="Users" and x!="sqlite_sequence",map(lambda x:x[1],data))

                    for attri in self.attributeList:
                        cursor.execute("SELECT * FROM %s"%attri)
                        data = cursor.fetchall()
                        if len(data)>0:
                            self.attriDictionary += [{x[1]:x[0] for x in data}]
                            self.attriAvailableList += [[x[1] for x in data]]

                    cursor.execute("SELECT Staff_Id, Name FROM Users")
                    users = cursor.fetchall()
                    if len(users)>0:
                        self.userAvailableList = [(user[1],str(user[0])) for user in users]
            except sqlite3.Error, e:
                if connection:
                    connection.rollback()
                self.log.write("Error %s"%e.args[0])
            except Exception as e:
                self.log.write("Error: ", e)
            finally:
                if connection:
                    connection.close()

            self.attri_box = []
            self.attri_radioButton_Any = []
            self.attri_radioButton_Select = []
            self.attriSelectedList = []
            self.attriSelectLabel = []
            self.attriSelectedListCtrl = []
            self.attriAvailableLabel = []
            self.attriAvailableListCtrl = []
            self.attriDeselectButton = []
            self.attriSelectButton = []
            for index in range(len(self.attributeList)):
                self.attri_box += [wx.StaticBox(self.parent,label=self.attributeList[index],pos=(0,0))]
                self.attri_radioButton_Any += [wx.RadioButton(self.attri_box[-1],label="Any",pos=(0,35),style=wx.RB_GROUP)]
                self.attri_radioButton_Select += [wx.RadioButton(self.attri_box[-1],label="Select Multiple",pos=(0,70))]
                self.attriSelectedList += [[]]
                self.attriSelectLabel += [wx.StaticText(self.attri_box[-1],label="Selected %s(s)"%attri,pos=(5,90))]
                self.attriSelectedListCtrl += [self.SortedListCtrl(self.attri_box[-1],cols=1,pos=(5,110),size=(120,100),data=self.attriSelectedList[-1])]
                self.attriSelectedListCtrl[-1].InsertColumn(0,attri)
                self.attriAvailableLabel += [wx.StaticText(self.attri_box[-1],label="Unselected %s(s)"%attri,pos=(5,220))]
                self.attriAvailableListCtrl += [self.SortedListCtrl(self.attri_box[-1],cols=1,pos=(5,240),size=(120,150),data=self.attriAvailableList[index])]
                self.attriAvailableListCtrl[-1].InsertColumn(0,attri)
                self.attriDeselectButton += [wx.Button(self.attri_box[-1],label="-",pos=(130,120),size=(30,30),style=wx.ALIGN_CENTRE)]
                self.attriSelectButton += [wx.Button(self.attri_box[-1],label="+",pos=(130,240),size=(30,30),style=wx.ALIGN_CENTRE)]
                self.attriSelectedListCtrl[-1].Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.onListNeedModify)
                self.attriAvailableListCtrl[-1].Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.onListNeedModify)
                self.attriDeselectButton[-1].Bind(wx.EVT_BUTTON,self.onListNeedModify)
                self.attriSelectButton[-1].Bind(wx.EVT_BUTTON,self.onListNeedModify)
                self.attriDeselectButton[-1].Disable()
                self.attriSelectButton[-1].Disable()
                self.refreshList(self.attriSelectedListCtrl[-1],self.attriSelectedList[-1])
                self.refreshList(self.attriAvailableListCtrl[-1],self.attriAvailableList[index])
                self.attriSelectedListCtrl[-1].Bind(wx.EVT_LIST_ITEM_SELECTED,self.onListItemSelected)
                self.attriAvailableListCtrl[-1].Bind(wx.EVT_LIST_ITEM_SELECTED,self.onListItemSelected)
                self.attri_radioButton_Any[-1].SetValue(True)

            for box in self.attri_box:
                p_frame.attributeSizer.Add(box,1,wx.ALL,5)

            self.userTitleLabel = wx.StaticText(self.parent,label="Then select specific user(s)")
            self.userTitleLabel.SetFont(wx.Font(14,wx.DEFAULT,wx.NORMAL,wx.BOLD))
            self.userBox = wx.StaticBox(self.parent,label="Specific user(s)",pos=(0,0))
            self.userSelectedList = []
            self.userSelectedLabel = wx.StaticText(self.userBox,label="Selected User(s)",pos=(20,50))
            self.userSelectedListCtrl = self.SortedListCtrl(self.userBox,cols=2,pos=(20,70),size=(120,100),data=self.userSelectedList)
            self.userSelectedListCtrl.InsertColumn(0,"User")
            self.userSelectedListCtrl.InsertColumn(1,"Staff ID")
            self.userAvailableLabel = wx.StaticText(self.userBox,label="Unselected User(s)",pos=(20,190))
            self.userAvailableListCtrl = self.SortedListCtrl(self.userBox,cols=2,pos=(20,210),size=(120,195),data=self.userAvailableList)
            self.userAvailableListCtrl.InsertColumn(0,"User")
            self.userAvailableListCtrl.InsertColumn(1,"Staff ID")
            self.userDeselectButton = wx.Button(self.userBox,label="-",pos=(145,90),size=(30,30),style=wx.ALIGN_CENTRE)
            self.userSelectButton = wx.Button(self.userBox,label="+",pos=(145,230),size=(30,30),style=wx.ALIGN_CENTRE)
            self.userSelectedListCtrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.onListNeedModify)
            self.userAvailableListCtrl.Bind(wx.EVT_LIST_ITEM_ACTIVATED,self.onListNeedModify)
            self.userDeselectButton.Bind(wx.EVT_BUTTON,self.onListNeedModify)
            self.userSelectButton.Bind(wx.EVT_BUTTON,self.onListNeedModify)
            self.userDeselectButton.Disable()
            self.userSelectButton.Disable()
            self.refreshList(self.userSelectedListCtrl,self.userSelectedList,True)
            self.refreshList(self.userAvailableListCtrl,self.userAvailableList,True)
            self.userSelectedListCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED,self.onListItemSelected)
            self.userAvailableListCtrl.Bind(wx.EVT_LIST_ITEM_SELECTED,self.onListItemSelected)

            p_frame.userSizer.Add(self.userTitleLabel,0,wx.ALL,5)
            p_frame.userSizer.Add(self.userBox,0,wx.ALL,10)

        class SortedListCtrl(wx.ListCtrl,ColumnSorterMixin):
            def __init__(self,parent,data,pos=wx.DefaultPosition,size=wx.DefaultSize,cols=None):
                wx.ListCtrl.__init__(self,parent,pos=pos,size=size,style=wx.LC_REPORT|wx.LC_AUTOARRANGE|wx.LC_SORT_ASCENDING)
                ColumnSorterMixin.__init__(self,len(data) if cols is None else cols)
                self.Bind(wx.EVT_LIST_COL_CLICK,self.OnColumn)
                self.itemDataMap = data

            def OnColumn(self,e):
                self.Refresh()
                e.Skip()

            def GetListCtrl(self):
                return self

        def refreshList(self,listCtrl,datalist,data2=False):
            listCtrl.DeleteAllItems()
            listCtrl.itemDataMap = datalist
            dict_index = range(len(datalist))
            zipped = zip(dict_index,datalist)
            userDictionary = dict(zipped)
            items = userDictionary.items()
            index = None
            for key,data in items:
                if data2:
                    index = listCtrl.InsertItem(sys.maxint,str(data[0]))
                    listCtrl.SetItem(index,1,str(data[1]))
                else:
                    index = listCtrl.InsertItem(sys.maxint,str(data))
                listCtrl.SetItemData(index,key)
                
        def onListNeedModify(self,e):
            evtObj = e.GetEventObject()
            if evtObj is self.userDeselectButton or evtObj is self.userSelectedListCtrl:
                selected_index = self.userSelectedListCtrl.GetNextSelected(-1)
                if selected_index < 0:
                    self.userDeselectButton.Disable()
                    return
                else:
                    selected_item = self.userSelectedList.pop(selected_index)
                    self.userAvailableList += [selected_item]
                    self.refreshList(self.userSelectedListCtrl,self.userSelectedList,True)
                    self.refreshList(self.userAvailableListCtrl,self.userAvailableList,True)
                    self.userDeselectButton.Disable()
                    return
            elif evtObj is self.userSelectButton or evtObj is self.userAvailableListCtrl:
                selected_index = self.userAvailableListCtrl.GetNextSelected(-1)
                if selected_index < 0:
                    self.userSelectButton.Disable()
                    return
                else:
                    selected_item = self.userAvailableList.pop(selected_index)
                    self.userSelectedList += [selected_item]
                    self.refreshList(self.userSelectedListCtrl,self.userSelectedList,True)
                    self.refreshList(self.userAvailableListCtrl,self.userAvailableList,True)
                    self.userSelectButton.Disable()
                    return
            for index in range(len(self.attriDeselectButton)):
                if evtObj is self.attriDeselectButton[index] or evtObj is self.attriSelectedListCtrl[index]:
                    selected_index = self.attriSelectedListCtrl[index].GetNextSelected(-1)
                    if selected_index < 0:
                        self.attriDeselectButton[index].Disable()
                        return
                    else:
                        selected_item = self.attriSelectedList[index].pop(selected_index)
                        self.attriAvailableList[index] += [selected_item]
                        self.refreshList(self.attriSelectedListCtrl[index],self.attriSelectedList[index])
                        self.refreshList(self.attriAvailableListCtrl[index],self.attriAvailableList[index])
                        self.attriDeselectButton[index].Disable()
                        return
                elif evtObj is self.attriSelectButton[index] or evtObj is self.attriAvailableListCtrl[index]:
                    selected_index = self.attriAvailableListCtrl[index].GetNextSelected(-1)
                    if selected_index < 0:
                        self.attriSelectButton[index].Disable()
                        return
                    else:
                        selected_item = self.attriAvailableList[index].pop(selected_index)
                        self.attriSelectedList[index] += [selected_item]
                        self.refreshList(self.attriSelectedListCtrl[index],self.attriSelectedList[index])
                        self.refreshList(self.attriAvailableListCtrl[index],self.attriAvailableList[index])
                        self.attriSelectButton[index].Disable()
                        return

        def onListItemSelected(self,e):
            evtObj = e.GetEventObject()
            if evtObj is self.userSelectedListCtrl:
                self.userDeselectButton.Enable()
                return
            elif evtObj is self.userAvailableListCtrl:
                self.userSelectButton.Enable()
                return
            for index in range(len(self.attriDeselectButton)):
                if evtObj is self.attriSelectedListCtrl[index]:
                    self.attriDeselectButton[index].Enable()
                    self.attri_radioButton_Select[index].SetValue(True)
                    return
                elif evtObj is self.attriAvailableListCtrl[index]:
                    self.attriSelectButton[index].Enable()
                    self.attri_radioButton_Select[index].SetValue(True)
                    return

