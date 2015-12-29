#!/usr/bin/python

import wx
import wx.stc
import re

token = {}
token['id'] = {'type':'range', 'value':[1,16]}
token['position'] = {'type':'string', 'value':['1','2','3','4']}
token['department'] = {'type':'string', 'value':['1','2','3']}
token['seclv'] = {'type':'range', 'value':[1,4]}

class PolicyPanel(wx.Panel):
    def __init__(self, parent, log):
        self.log = log
        wx.Panel.__init__(self, parent)
        bgcolor = wx.Colour(255,0,0,127)
        self.SetBackgroundColour(wx.RED)
        self.SetMaxSize((-1,40))
        self.menu = self.MakeMenu()

        self.search = wx.stc.StyledTextCtrl(self)

        self.autosizer = wx.BoxSizer(wx.VERTICAL)
        self.searchsizer = wx.BoxSizer(wx.HORIZONTAL) 
        self.searchsizer.Add(self.search, 1, wx.TOP, 0)
        self.autosizer.Add(self.searchsizer, 0, wx.EXPAND|wx.LEFT|wx.RIGHT, 0)
        self.SetSizer(self.autosizer)

    def GetText(self):
        return self.search.GetText().lower()

    def OnSTC_Charadded(self, ev):
        polstr = self.search.GetText()
        res = []
        self.GetCompletions(polstr.encode('ascii','ignore'),res)
        if res:
            self.search.AutoCompShow(0,' '.join(res))

    def OnSTC_AutoCompleted(self,ev):
        self.log.write("[OnSTC_AutoCompleted] %s\n" % str(ev))

    def OnSTC_AutoCompCancel(self):
        self.search.AutoCompCancel()

    def OnKeyUp(self,ev):
        pass    

    def OnMenuItemSelected(self,ev):
        self.log.write("[OnMenuItemSelected] %d\n"%ev.GetSelection())

    def getPolicy(self):
        p = self.search.GetText()
        p = re.sub(r'((?:<|>|=)\s*\d+)',r'\1',p)
        return p
            

    def GetCompletions(self, prefix, res):
        '''dots:
            in: 2 or more dots
            out: empty'''
        m_dots = re.search(r'_{2,}',prefix)
        if m_dots:
            return
        m_dotspace = re.search(r'_\s+',prefix)
        if m_dotspace:
            return
        x_nonspace = re.search(r'(.*)\s+$',prefix)
        if x_nonspace:
            pref = x_nonspace.group(1)
        else:
            pref = prefix
        '''beginning:
            in: ('^', '(', '&', '|')
            out: all cats, op('(','k of')'''
        m_beg = re.search(r'^$|\($|&$|\|$',pref)
        if m_beg:
            for cat in token.keys():
                res.append(cat)
            return
        '''ending:
            in: (')', str)
            out: op('&','|',')')'''
        m_end_pts = re.search(r'\)$',pref)
        if m_end_pts:
            res.append('&')
            res.append('|')
            return
        '''rational
            in: ('<', '>', '=')
            out: (attri_range, '=')'''
        m_rat = re.search(r'([a-z0-9]+)(_[a-z0-9]*)*\s*(<|>|<=|>=|=)\s*(\d+)*$',pref)
        if m_rat:
            m_ne = re.search(r'(?:<|>)\s*$',pref)
            if m_ne:
                res.append('=')
            cat_attri = m_rat.groups()
            try:
                t = token[cat_attri[0]]
            except KeyError:
                return
            if t['type']=='range':
                lower = int(t['value'][0])
                upper = int(t['value'][1])
                x_digit = re.search(r'(\d+)$',pref)
                if x_digit:
                    digit = int(x_digit.group(1))
                    for i in range(lower,upper+1):
                        regex = re.compile('^'+x_digit.group(1))
                        m_msb = regex.search(str(i))
                        if m_msb and digit!=i:
                            res.append(str(i))
                    if lower<=digit and digit<=upper:
                        res.append('&')
                        res.append('|')
                    else:
                        pass
                else:
                    for i in range(lower,upper+1):
                        res.append(str(i))
            return
        '''cating or attring
            in: part (cat, attri)
            out: full (cat, attri)'''
        '''TODO: recursive sub-categories'''
        m_str = re.search(r'([a-z0-9]+)(_[a-z0-9]*)*$',pref)
        if m_str:
            cat_attri = m_str.groups()
            if cat_attri[1] is None:
                try:
                    t = token[cat_attri[0]]
                    if t['type']=='range':
                        res.append("<")
                        res.append(">")
                        res.append("<=")
                        res.append("<=")
                        res.append("=")
                    elif t['type']=='string':
                        res.append("_")
                    else:
                        self.log.write("[GetCompletions] m_str: unexpected\n")
                except KeyError:
                    for cat in token.keys():
                        regex = re.compile('^'+cat_attri[0])
                        m_cat = regex.search(cat)
                        if m_cat:
                            res.append(cat)
            else:
                try:
                    t = token[cat_attri[0]]
                except KeyError:
                    return
                if t['type']=='string':
                    if cat_attri[1]=='_':
                        for attri in t['value']:
                            res.append(attri)
                    else:
                        for attri in t['value']:
                            if attri==cat_attri[1][1:]:
                                res.append('&')
                                res.append('|')
                                return
                        for attri in t['value']:
                            regex = re.compile('^'+cat_attri[1][1:])
                            m_attri = regex.search(attri)
                            if m_attri:
                                res.append(attri)
            return
                
    def OnSearch(self, evt):
        self.log.write("OnSearch\n")

    def OnCancel(self, evt):
        self.log.write("OnCancel\n")

    def OnDoSearch(self, evt):
        self.log.write("[OnDoSearch] ")
        self.log.write(" %s\n" % self.search.GetValue())

    def MakeMenu(self):
        menu = wx.Menu()
        item = menu.Append(-1, "Recent Searches")
        item.Enable(False)
        for txt in [ "You can maintain",
                     "a list of old",
                     "search strings here",
                     "and bind EVT_MENU to",
                     "catch their selections" ]:
            menu.Append(-1, txt)
        return menu
