import wx
import wx.combo
from wx.lib.statbmp import GenStaticBitmap
from widgits import BackgroundPanel, ShapedButton, TransparentText, TransparentBitmap, TabbedBackgroundPanel
import FancyTabNotebook
from utils import *
from panels import LastdialedPanel, CaptureVolumeSlider, PlaybackVolumeSlider
from web import FMCWebView
from videodialog import VideoAdDialog

__author__ = 'TheArchitect'



ENTER_NUMBER = "Enter Number"

###########################################################################
#  Class DialerFrame
###########################################################################


class DialerFrame(wx.Frame):
    def __del__(self):
        pass

    def UpdateCallHistory(self):
        history = self.wxapp.dialed_history[:50]
        history.reverse()
        iterhistory = iter(history)
        startrow = 3
        startcol = 1
        row = 0
        col = 0

        windows = iter(list(self.recenthistory_panel.GetChildren()))
        #dont remove the transparent header.. just skip over it  #NEXT IT ;)
        next(windows)
        for window in windows:
            self.recenthistory_sizer.Detach(window)
            window.Destroy()
        self.recenthistory_sizer.Layout()

        #self.recenthistory_sizer.AddSpacer( ( 5, 1 ), wx.GBPosition( 0, startcol + col ), wx.GBSpan( 1, 1 ), wx.FIXED_MINSIZE, 0 )
        #self.recenthistory_sizer.AddSpacer( ( 5, 1 ), wx.GBPosition( 0, startcol + col + 2 ), wx.GBSpan( 1, 1 ), wx.FIXED_MINSIZE, 0 )
        #self.recenthistory_sizer.AddSpacer( ( 5, 1 ), wx.GBPosition( 0, startcol + col + 4 ), wx.GBSpan( 1, 1 ), wx.FIXED_MINSIZE, 0 )

        for row in range(5):
            try:
                for col in range(3):
                    call = next(iterhistory)
                    #print "Adding call to pane;", call
                    rc1 = LastdialedPanel(call[0], call[1], self.dialRecent, u"images/panel/recentcallbg.png",
                                          self.recenthistory_panel, wx.ID_ANY, )
                    self.recenthistory_sizer.Add(rc1, wx.GBPosition(startrow + row + 1, startcol + col),
                                                 wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)
                if row != 0:
                    try:
                        self.recenthistory_sizer.AddSpacer(( 2, 63 ), wx.GBPosition(startrow + row, 0), wx.GBSpan(1, 1),
                                                           wx.FIXED_MINSIZE, 0)
                    except:
                        pass
            except StopIteration:
                break

    def OnKeypadNumber(self, event):
        btn = event.GetEventObject()
        num = btn.number

        self.doCallChar(num)
        self.wxapp.sendDtmf(num)
        #self.wxapp.phonenum +=num
        #self.dialnumber.UpdateLabel( "+%s %s" % ( self.wxapp.phonecountry[3], self.wxapp.phonenum ) )

    def OnKeypadErase(self, event):
        self.wxapp.phonenum = self.wxapp.phonenum[:-1]
        if self.wxapp.phonenum == "":
            #self.wxapp.phonenum = ENTER_NUMBER
            self.dialnumber.UpdateLabel(ENTER_NUMBER)
            return

        self.dialnumber.UpdateLabel("+%s" % self.wxapp.phonenum)
        self.onPhoneNumberChange()

    def OnCountryboxSelect(self, event):
        obj = event.GetEventObject()
        country = obj.GetClientData(event.GetInt())
        self.wxapp.phonecountry = country
        self.wxapp.phonenum = "%s" % self.wxapp.phonecountry[3]
        self.dialnumber.UpdateLabel("+%s" % self.wxapp.phonenum)

    def OnConnectionStateChange(self, event):
        text = event.GetState()
        self.m_staticText4.UpdateLabel(text)

    def OnUsernameChange(self, event):
        text = event.GetUsername()
        self.m_staticText3.UpdateLabel(text)

    def OnCallTimeChange(self, event):
        time = event.GetTime()
        self.m_staticText5.UpdateLabel(time)

    def OnFrameClose(self, event):
        self.Hide()
        if event.CanVeto():
            event.Veto()

    def doCallChar(self, chr):
        if self.wxapp.phonenum == ENTER_NUMBER:
            self.wxapp.phonenum = ""

        self.wxapp.phonenum += chr
        self.onPhoneNumberChange()

    def onPhoneNumberChange(self):
        if self.just_coutry_selected:
            self.just_coutry_selected = False
            return

        if not self.wxapp.phonenum:
            return

        cIndex = findCountry(self.wxapp.phonenum[:6])

        if cIndex != -1:
            self.country_box.SetSelection(cIndex)
            self.wxapp.phonecountry = countries[cIndex]
            self.dialnumber.UpdateLabel("+%s" % self.wxapp.phonenum)
        else:
            self.country_box.SetSelection(wx.NOT_FOUND)
            self.wxapp.phonecountry = ('', 'null', '', '')
            self.dialnumber.UpdateLabel("%s" % self.wxapp.phonenum)

        return

    def callBtn_Click(self, event):
        if self.make_call:
            #self.makeCall()
            self.showPreCallAds()
            self.makeCall()
        else:
            self.endCall()

    def buildAudioDeviceDropdown(self):
        devices = self.wxapp.phone.getAudioDevices()
        i = 0
        for devname, selected in devices['playback']:
            self.spk_cb.Append(devname)
            if selected:
                self.spk_cb.SetSelection(i)
            i += 1

        i = 0
        for devname, selected in devices['capture']:
            self.mic_cb.Append(devname)
            if selected:
                self.mic_cb.SetSelection(i)
            i += 1

    def audioDevChange(self, event):
        cap = self.mic_cb.GetStringSelection()
        play = self.spk_cb.GetStringSelection()

        self.wxapp.changeAudioDevices(cap, play)


    def showPreCallAds(self):
        dlg = VideoAdDialog(self, self.wxapp.adsduration)
        dlg.webview.browser.LoadURL(self.wxapp.adsurl)
        #self.call_btn.Disable()
        dlg.ShowModal()
        dlg.Destroy()
        #self.call_btn.Enable()

    def makeCall(self):
        if self.wxapp.phonenum:
            wx.CallAfter(self.wxapp.pstnCall)
            self.make_call = False

            self.flag_bitmap.ChangeSource(u'images/flags/%s.png' % self.wxapp.phonecountry[1].lower())
            self.m_staticText5.UpdateLabel(u"00:00:00")
            codelen = len(self.wxapp.phonecountry[3])
            if self.wxapp.phonecountry[3]:
                self.m_staticText6.UpdateLabel(u"+%s %s" % ( self.wxapp.phonecountry[3], self.wxapp.phonenum[codelen:]))
            else:
                self.m_staticText6.UpdateLabel(self.wxapp.phonenum)

            #self.presencepanel.Refresh()

            self.call_btn.ChangeButtonImages(u"images/keypad/normal/end-call.png")

    def endCall(self, event=None):
        if not self.call_ending:
            self.call_ending = True
            wx.CallAfter(self.wxapp.hangup)

    def callStateChange(self, state):
        if state == DISCONNECTED:
            self.call_btn.ChangeButtonImages(u"images/keypad/normal/place-call.png",
                                             u"images/keypad/over/place-call.png")
            self.call_ending = False
            self.make_call = True
            self.m_staticText5.UpdateLabel(u"")
            self.m_staticText6.UpdateLabel(u"")

    def dialRecent(self, event):
        btn = event.GetEventObject()
        num = btn.GetParent().number
        country = btn.GetParent().country

        self.wxapp.phonenum = country[3] + num
        self.onPhoneNumberChange()

        self.fancynotebook.SetSelection(0)
        #self.makeCall()
        self.callBtn_Click(None)

        #self.wxapp.phonenum +=num
        #self.dialnumber.UpdateLabel( "+%s %s" % ( self.wxapp.phonecountry[3], self.wxapp.phonenum ) )

    def onCallDisconnect(self, event):
        self.make_call = True
        self.printCallStates()
        self.calltimer.Stop()
        self.call_btn.ChangeButtonImages(u"images/keypad/normal/place-call.png", u"images/keypad/over/place-call.png")
        self.call_ending = False
        self.UpdateCallHistory()

        #self.m_staticText5.UpdateLabel(u"")
        self.m_staticText6.UpdateLabel(u"Last call duration")

    def onCallConnect(self, event):
        self.calltimer.Start(1000)

    def onCallStatus(self, event):
        state = event.GetState()
        self.m_staticText4.UpdateLabel(state)

        if state in [OFFLINE, CONNECTING, NOTREADY]:
            self.m_bitmap5.ChangeSource(u"images/bar/offline.png")
        else:
            self.m_bitmap5.ChangeSource(u"images/bar/online.png")

    def onPlaybackVolumeChanged(self, volume):
        volume = float(volume)
        volume = volume * 0.1
        wx.CallAfter(self.wxapp.setPlaybackVolume, volume)

    def onCaptureVolumeChanged(self, volume):
        volume = float(volume)
        volume = volume * 0.1
        wx.CallAfter(self.wxapp.setCaptureVolume, volume)

    def showCaptureSlider(self, event):
        if self.playbackSlider.IsShown():
            self.playbackSlider.Hide()

        if self.captureSlider.IsShown():
            self.captureSlider.Hide()
            return
        else:
            self.captureSlider.Show()
            return

    def showPlaybackSlider(self, event):
        if self.captureSlider.IsShown():
            self.captureSlider.Hide()

        if self.playbackSlider.IsShown():
            self.playbackSlider.Hide()
            return
        else:
            self.playbackSlider.Show()
            return

    def callTimerTick(self, event):
        seconds = self.wxapp.callDuration()
        calltime = formatSecondsToCalltime(seconds)
        self.m_staticText5.UpdateLabel(calltime)

    def printCallStates(self):
        print "Make_call=", self.make_call, "call_ending=", self.call_ending, "state="

    def __init__(self, wxapp, parent):
        super(DialerFrame, self).__init__(parent, id=wx.ID_ANY, title="FreeMyCall Dialer", pos=wx.DefaultPosition,
                                          size=wx.Size(700, 670),
                                          style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.NO_BORDER | wx.TAB_TRAVERSAL)  # |wx.FRAME_SHAPED
        self.wxapp = wxapp
        self.captureSlider = None
        self.just_coutry_selected = False
        self.make_call = True
        self.call_ending = False

        self.SetSizeHintsSz(wx.Size(700, 670), wx.Size(700, 670))
        self.SetBackgroundColour(wx.Colour(255, 255, 255))

        OuterSizer = wx.BoxSizer(wx.VERTICAL)

        # self.m_bitmap1 = wx.StaticBitmap(self, wx.ID_ANY,
        #                                  wx.Bitmap(u"images/backgrounds/header.png", wx.BITMAP_TYPE_ANY),
        #                                  wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER)
        self.m_bitmap1 = TransparentBitmap(u"images/backgrounds/header.png", self, wx.ID_ANY, wx.DefaultPosition,
                                           wx.DefaultSize)
        OuterSizer.Add(self.m_bitmap1, 0, 0, 0)

        self.mainpanel = BackgroundPanel(u"images/backgrounds/background.png", self, wx.ID_ANY, wx.DefaultPosition,
                                         wx.Size(700, 550), wx.NO_BORDER | wx.TAB_TRAVERSAL)
        self.mainpanel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.mainpanel.SetMinSize(wx.Size(700, 550))

        presenceSizer = wx.BoxSizer(wx.VERTICAL)

        presenceSizer.AddSpacer((0, 5), 0, 0, 0)

        ###################################################################################
        #   <PresenceBox>
        ###################################################################################

        self.presencepanel = BackgroundPanel(u"images/bar/presence-bar.png", self.mainpanel, wx.ID_ANY,
                                             wx.DefaultPosition, wx.Size(-1, 67), wx.NO_BORDER | wx.TAB_TRAVERSAL)
        self.presencepanel.SetBackgroundColour(wx.Colour(255, 255, 255))
        self.presencepanel.SetMinSize(wx.Size(-1, 67))
        self.presencepanel.SetBackgroundPos(15, 0)

        pbar = wx.BoxSizer(wx.HORIZONTAL)

        pbar.SetMinSize(wx.Size(670, 78))

        ###################################################################################
        #                               First Box
        ###################################################################################

        pbar_box_1 = wx.GridBagSizer(0, 0)
        pbar_box_1.SetFlexibleDirection(wx.BOTH)
        pbar_box_1.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)
        pbar_box_1.AddSpacer((37, 1), wx.GBPosition(0, 0), wx.GBSpan(3, 1), wx.FIXED_MINSIZE, 0)
        pbar_box_1.AddSpacer((1, 20), wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        self.m_staticText3 = TransparentText(self.presencepanel, wx.ID_ANY, u"User Name", wx.DefaultPosition,
                                             wx.Size(140, -1), 0)
        # self.m_staticText3.Wrap( -1 )
        self.m_staticText3.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.m_staticText3.SetForegroundColour(wx.Colour(246, 246, 246))

        pbar_box_1.Add(self.m_staticText3, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        self.m_staticText4 = TransparentText(self.presencepanel, wx.ID_ANY, OFFLINE, wx.DefaultPosition,
                                             wx.Size(140, -1), 0)
        self.m_staticText4.Wrap(-1)
        self.m_staticText4.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.m_staticText4.SetForegroundColour(wx.Colour(62, 181, 208))
        pbar_box_1.Add(self.m_staticText4, wx.GBPosition(2, 1), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        self.m_bitmap5 = TransparentBitmap(u"images/bar/offline.png", self.presencepanel, wx.ID_ANY, wx.DefaultPosition,
                                           wx.DefaultSize)
        pbar_box_1.Add(self.m_bitmap5, wx.GBPosition(1, 2), wx.GBSpan(2, 1),
                       wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 5)

        pbar.Add(pbar_box_1, 1, wx.EXPAND, 0)

        ###################################################################################
        #                               Second Box
        ###################################################################################

        pbar_box_2 = wx.GridBagSizer(0, 0)
        pbar_box_2.SetFlexibleDirection(wx.BOTH)
        pbar_box_2.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        pbar_box_2.AddSpacer((20, 1), wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        pbar_box_2.AddSpacer((1, 14), wx.GBPosition(0, 2), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        self.flag_bitmap = TransparentBitmap(u'images/flags/%s.png' % self.wxapp.phonecountry[1].lower(),
                                             self.presencepanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
                                             0)  # wx.Bitmap(u'images/flags/%s.png' % country[1].lower()) , country)
        pbar_box_2.Add(self.flag_bitmap, wx.GBPosition(1, 1), wx.GBSpan(1, 1),
                       wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT, 10)

        self.m_staticText5 = TransparentText(self.presencepanel, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size(90, -1), 0)
        self.m_staticText5.Wrap(-1)
        self.m_staticText5.SetFont(wx.Font(13, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.m_staticText5.SetForegroundColour(wx.Colour(246, 246, 246))
        pbar_box_2.Add(self.m_staticText5, wx.GBPosition(1, 2), wx.GBSpan(1, 1), wx.ALIGN_LEFT | wx.ALL, 0)

        self.m_staticText6 = TransparentText(self.presencepanel, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size(150, -1),
                                             0)
        self.m_staticText6.Wrap(-1)
        self.m_staticText6.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        self.m_staticText6.SetForegroundColour(wx.Colour(246, 246, 246))
        pbar_box_2.Add(self.m_staticText6, wx.GBPosition(2, 1), wx.GBSpan(1, 2), wx.ALIGN_LEFT, 0)

        self.pbar_box_2 = pbar_box_2

        pbar.Add(pbar_box_2, 1, wx.EXPAND, 0)

        # pbar.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )

        ###################################################################################
        #                               Third Box
        ###################################################################################

        pbar_box_3 = wx.GridBagSizer(0, 0)
        pbar_box_3.SetFlexibleDirection(wx.BOTH)
        pbar_box_3.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        pbar_box_3.AddSpacer((21, 1), wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        pbar_box_3.AddSpacer((1, 10), wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        pbar_box_3.AddSpacer((10, 1), wx.GBPosition(0, 2), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        self.mic_button = ShapedButton(u"images/bar/mic-button.png", self.presencepanel, wx.ID_ANY, wx.DefaultPosition,
                                       wx.DefaultSize)
        self.mic_button.Bind(wx.EVT_BUTTON, self.showCaptureSlider)
        pbar_box_3.Add(self.mic_button, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        self.speaker_button = ShapedButton(u"images/bar/speaker-button.png", self.presencepanel, wx.ID_ANY,
                                           wx.DefaultPosition, wx.DefaultSize)
        self.speaker_button.Bind(wx.EVT_BUTTON, self.showPlaybackSlider)
        pbar_box_3.Add(self.speaker_button, wx.GBPosition(2, 1), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        self.bar_endcall_button = ShapedButton(u"images/bar/end-call.png", self.presencepanel, wx.ID_ANY,
                                               wx.DefaultPosition, wx.DefaultSize)
        self.bar_endcall_button.SetAdditionalImages(u"images/bar/end-call-pressed.png")
        self.bar_endcall_button.Bind(wx.EVT_BUTTON, self.endCall)
        pbar_box_3.Add(self.bar_endcall_button, wx.GBPosition(1, 3), wx.GBSpan(3, 1),
                       wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, 0)

        pbar.Add(pbar_box_3, 1, wx.EXPAND, 0)

        # pbar.AddSpacer( ( 0, 0), 1, wx.EXPAND, 5 )

        ###################################################################################
        #                               Fourth Box
        ###################################################################################

        pbar_box_4 = wx.GridBagSizer(0, 0)
        pbar_box_4.SetFlexibleDirection(wx.BOTH)
        pbar_box_4.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        pbar_box_4.AddSpacer((5, 1), wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        pbar_box_4.AddSpacer((0, 15), wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        pbar_box_4.AddSpacer((5, 0), wx.GBPosition(0, 2), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        self.m_staticText7 = TransparentText(self.presencepanel, wx.ID_ANY, u"Balance:\nPackage:\nUS Calling:",
                                             wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_staticText7.Wrap(-1)
        self.m_staticText7.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.m_staticText7.SetForegroundColour(wx.Colour(246, 246, 246))
        pbar_box_4.Add(self.m_staticText7, wx.GBPosition(1, 1), wx.GBSpan(3, 1), wx.ALIGN_LEFT, 0)

        self.txt_balance = TransparentText(self.presencepanel, wx.ID_ANY, u"0.0000", wx.DefaultPosition, wx.DefaultSize,
                                           0)
        self.txt_balance.Wrap(-1)
        self.txt_balance.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        self.txt_balance.SetForegroundColour(wx.Colour(246, 246, 246))
        pbar_box_4.Add(self.txt_balance, wx.GBPosition(1, 3), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        self.txt_package = TransparentText(self.presencepanel, wx.ID_ANY, u"None", wx.DefaultPosition, wx.DefaultSize,
                                           0)
        self.txt_package.Wrap(-1)
        self.txt_package.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        self.txt_package.SetForegroundColour(wx.Colour(246, 246, 246))
        pbar_box_4.Add(self.txt_package, wx.GBPosition(2, 3), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        self.txt_uscalling = TransparentText(self.presencepanel, wx.ID_ANY, u"Unlimited !", wx.DefaultPosition,
                                             wx.DefaultSize, 0)
        self.txt_uscalling.Wrap(-1)
        self.txt_uscalling.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        self.txt_uscalling.SetForegroundColour(wx.Colour(246, 246, 246))
        pbar_box_4.Add(self.txt_uscalling, wx.GBPosition(3, 3), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        pbar.Add(pbar_box_4, 1, wx.EXPAND, 0)

        self.presencepanel.SetSizer(pbar)
        self.presencepanel.Layout()
        presenceSizer.Add(self.presencepanel, 0, wx.EXPAND, 0)

        ###################################################################################
        #   </PresenceBox>
        #   <tabs-panel>
        ###################################################################################

        bSizer11 = wx.BoxSizer(wx.HORIZONTAL)

        self.fancynotebook = FancyTabNotebook.FancyTabNotebook(self.mainpanel, wx.ID_ANY,
                                                               agwStyle=FancyTabNotebook.INB_LEFT)
        # self.DisplayPanel = BackgroundPanel( u"images/panel/panel-bg-bar.png", self.fancynotebook, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        # self.DisplayPanel.SetSizeHints(501,450)

        ###################################################################################
        #   <call phones panel>
        ###################################################################################

        panel1 = TabbedBackgroundPanel(u"images/panel/panel-bg-bar.png", self.fancynotebook, wx.ID_ANY)
        panel1.setStuff(u"images/panel/tabsmoother.png", 0, 49)
        panel1.AddOverlayImage(u"images/panel/textbox.png", 155, 53)
        panel1.SetSizeHints(501, 450)

        panel1_sizer = wx.GridBagSizer(0, 0)
        panel1_sizer.SetFlexibleDirection(wx.BOTH)
        panel1_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        panel1_sizer.AddSpacer((11, 1), wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        panel1_sizer.AddSpacer((1, 20), wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        p1_staticText1 = TransparentText(panel1, wx.ID_ANY, u"Dial a Number", wx.DefaultPosition, wx.Size(140, -1), 0)
        p1_staticText1.Wrap(-1)
        p1_staticText1.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        p1_staticText1.SetForegroundColour(wx.Colour(3, 106, 157))
        panel1_sizer.Add(p1_staticText1, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        # Country box
        panel1_sizer.AddSpacer((1, 10), wx.GBPosition(2, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        self.country_box = wx.combo.BitmapComboBox(panel1, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size(125, 32), "",
                                                   wx.CB_READONLY | wx.TRANSPARENT_WINDOW)
        self.country_box.SetMinSize(wx.Size(125, 32))
        self.country_box.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        self.country_box.SetForegroundColour(wx.Colour(0, 70, 109))
        for country in countries:
            self.country_box.Append(country[0], wx.Bitmap(u'images/flags/%s.png' % country[1].lower()), country)
        self.country_box.Bind(wx.EVT_COMBOBOX, self.OnCountryboxSelect)
        panel1_sizer.Add(self.country_box, wx.GBPosition(3, 1), wx.GBSpan(1, 1), wx.ALIGN_LEFT | wx.EXPAND, 0)

        panel1_sizer.AddSpacer((5, 1), wx.GBPosition(3, 2), wx.GBSpan(9, 1), wx.FIXED_MINSIZE, 0)

        # number box
        self.dialnumber = TransparentText(panel1, wx.ID_ANY, u"Enter Number", wx.DefaultPosition, wx.Size(180, -1), 0)
        self.dialnumber.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.dialnumber.SetForegroundColour(wx.Colour(3, 106, 157))
        panel1_sizer.Add(self.dialnumber, wx.GBPosition(3, 3), wx.GBSpan(1, 5), wx.ALIGN_LEFT | wx.LEFT | wx.TOP, 8)

        panel1_sizer.AddSpacer((1, 10), wx.GBPosition(4, 3), wx.GBSpan(1, 5), wx.FIXED_MINSIZE, 0)

        # Number last erase button



        # The Dialpad follows
        dialpad_startrow = 5
        dialpad_startcol = 3
        btnrow = 0
        btncol = 0
        panel1_sizer.AddSpacer((1, 1), wx.GBPosition(dialpad_startrow, dialpad_startcol + 1), wx.GBSpan(1, 1),
                               wx.FIXED_MINSIZE, 0)
        panel1_sizer.AddSpacer((1, 1), wx.GBPosition(dialpad_startrow, dialpad_startcol + 3), wx.GBSpan(1, 1),
                               wx.FIXED_MINSIZE, 0)
        panel1_sizer.AddSpacer((5, 1), wx.GBPosition(3, dialpad_startcol + 5), wx.GBSpan(1, 1), wx.FIXED_MINSIZE,
                               0)  # This is for delete buttons

        delbtn = ShapedButton(u"images/keypad/normal/delete.png", panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize)
        delbtn.SetAdditionalImages(u"images/keypad/over/delete.png")
        delbtn.Bind(wx.EVT_BUTTON, self.OnKeypadErase)
        panel1_sizer.Add(delbtn, wx.GBPosition(3, dialpad_startcol + 6), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        for row in [('1', '2', '3'), ('4', '5', '6'), ('7', '8', '9'), ('*', '0', '#')]:
            btncol = 0
            for item in row:
                if item == '*':
                    filename = "star.png"
                elif item == '#':
                    filename = "hash.png"
                else:
                    filename = "%s.png" % item
                btn = ShapedButton(u"images/keypad/normal/" + filename, panel1, wx.ID_ANY, wx.DefaultPosition,
                                   wx.DefaultSize)
                btn.number = item
                btn.SetAdditionalImages(u"images/keypad/over/" + filename)
                btn.Bind(wx.EVT_BUTTON, self.OnKeypadNumber)
                panel1_sizer.Add(btn, wx.GBPosition(dialpad_startrow + btnrow, dialpad_startcol + btncol),
                                 wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)
                btncol += 2
            panel1_sizer.AddSpacer((1, 2), wx.GBPosition(dialpad_startrow + btnrow + 1, dialpad_startcol),
                                   wx.GBSpan(1, 5), wx.FIXED_MINSIZE, 0)
            btnrow += 2

        # Place call button / End call button
        self.call_btn = ShapedButton(u"images/keypad/normal/place-call.png", panel1, wx.ID_ANY, wx.DefaultPosition,
                                     wx.DefaultSize)
        self.call_btn.SetAdditionalImages(u"images/keypad/over/place-call.png")
        self.call_btn.Bind(wx.EVT_BUTTON, self.callBtn_Click)
        panel1_sizer.AddSpacer((1, 10), wx.GBPosition(dialpad_startrow + btnrow, dialpad_startcol - 1),
                               wx.GBSpan(1, 6), wx.FIXED_MINSIZE, 0)
        panel1_sizer.Add(self.call_btn, wx.GBPosition(dialpad_startrow + btnrow + 1, dialpad_startcol - 1),
                         wx.GBSpan(1, 6), wx.ALIGN_LEFT | wx.LEFT, 3)

        panel1.SetSizer(panel1_sizer)
        panel1.Layout()
        ###################################################################################
        #   </call phone panel>
        #   <recent calls panel>
        ###################################################################################

        panel2 = TabbedBackgroundPanel(u"images/panel/panel-bg-bar.png", self.fancynotebook, wx.ID_ANY)
        panel2.setStuff(u"images/panel/tabsmoother.png", 1, 49)
        panel2.SetSizeHints(501, 450)

        panel2_sizer = wx.GridBagSizer(0, 0)
        panel2_sizer.SetFlexibleDirection(wx.BOTH)
        panel2_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        panel2_sizer.AddSpacer((11, 1), wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        panel2_sizer.AddSpacer((1, 20), wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        p2_staticText1 = TransparentText(panel2, wx.ID_ANY, u"Recent calls", wx.DefaultPosition, wx.Size(140, -1), 0)
        p2_staticText1.Wrap(-1)
        p2_staticText1.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        p2_staticText1.SetForegroundColour(wx.Colour(3, 106, 157))
        panel2_sizer.Add(p2_staticText1, wx.GBPosition(1, 1), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        # rc1 = LastdialedPanel( u"23234234234234", countries[5], None, u"images/panel/recentcallbg.png", panel2, wx.ID_ANY )
        # panel2_sizer.Add( rc1, wx.GBPosition( 3,1 ), wx.GBSpan( 1, 1 ), wx.ALIGN_LEFT, 0 )


        self.recenthistory_panel = panel2
        self.recenthistory_sizer = panel2_sizer

        panel2.SetSizer(panel2_sizer)
        panel2.Layout()

        ###################################################################################
        #   </recentcalls-panel>
        #   <offers panel>
        ###################################################################################

        freecredits_panel = TabbedBackgroundPanel(u"images/panel/panel-bg-bar.png", self.fancynotebook, wx.ID_ANY)
        freecredits_panel.setStuff(u"images/panel/tabsmoother.png", 2, 49)
        freecredits_panel.SetSizeHints(501, 450)

        panel3_sizer = wx.GridBagSizer(0, 0)
        panel3_sizer.SetFlexibleDirection(wx.BOTH)
        panel3_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        panel3_sizer.AddSpacer((11, 1), wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        panel3_sizer.AddSpacer((1, 20), wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        self.p3_staticText1 = TransparentText(freecredits_panel, wx.ID_ANY, u"Complete offers for free credits",
                                              wx.DefaultPosition, wx.Size(-1, -1), 0)
        self.p3_staticText1.Wrap(-1)
        self.p3_staticText1.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.p3_staticText1.SetForegroundColour(wx.Colour(3, 106, 157))
        panel3_sizer.Add(self.p3_staticText1, wx.GBPosition(1, 1), wx.GBSpan(1, 9), wx.ALIGN_LEFT, 0)

        freecredits_panel.SetSizer(panel3_sizer)
        freecredits_panel.Layout()

        ###################################################################################
        #   </offers-panel>
        #   <purchase panel>
        ###################################################################################

        purchase_credits_panel = TabbedBackgroundPanel(u"images/panel/panel-bg-bar.png", self.fancynotebook, wx.ID_ANY)
        purchase_credits_panel.setStuff(u"images/panel/tabsmoother.png", 3, 49)
        purchase_credits_panel.SetSizeHints(501, 450)

        ###################################################################################
        #   </purchase_credits_panel>
        #   <settings_panel>
        ###################################################################################

        settings_panel = TabbedBackgroundPanel(u"images/panel/panel-bg-bar.png", self.fancynotebook, wx.ID_ANY)
        settings_panel.setStuff(u"images/panel/tabsmoother.png", 4, 49)
        settings_panel.SetSizeHints(501, 450)

        settings_sizer = wx.GridBagSizer(0, 0)
        settings_sizer.SetFlexibleDirection(wx.BOTH)
        settings_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        settings_sizer.AddSpacer((11, 1), wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        settings_sizer.AddSpacer((1, 20), wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        st_staticText1 = TransparentText(settings_panel, wx.ID_ANY, u"Audio Settings", wx.DefaultPosition,
                                         wx.Size(140, -1), 0)
        st_staticText1.Wrap(-1)
        st_staticText1.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        st_staticText1.SetForegroundColour(wx.Colour(3, 106, 157))

        # Audio device and speaker device
        audio_text = TransparentText(settings_panel, wx.ID_ANY, u"Speaker", wx.DefaultPosition, wx.Size(140, -1), 0)
        audio_text.Wrap(-1)
        audio_text.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        audio_text.SetForegroundColour(wx.Colour(3, 106, 157))

        mic_text = TransparentText(settings_panel, wx.ID_ANY, u"Microphone", wx.DefaultPosition, wx.Size(140, -1), 0)
        mic_text.Wrap(-1)
        mic_text.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        mic_text.SetForegroundColour(wx.Colour(3, 106, 157))

        mic_icon = TransparentBitmap(u'images/bar/mic-button.png', settings_panel, wx.ID_ANY, wx.DefaultPosition,
                                     wx.DefaultSize, 0)
        spk_icon = TransparentBitmap(u'images/bar/speaker-button.png', settings_panel, wx.ID_ANY, wx.DefaultPosition,
                                     wx.DefaultSize, 0)

        # Get the
        self.mic_cb = wx.ComboBox(settings_panel, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size(125, 32), "",
                                  wx.CB_READONLY | wx.TRANSPARENT_WINDOW)
        self.mic_cb.SetMinSize(wx.Size(190, 32))
        self.spk_cb = wx.ComboBox(settings_panel, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size(125, 32), "",
                                  wx.CB_READONLY | wx.TRANSPARENT_WINDOW)
        self.spk_cb.SetMinSize(wx.Size(190, 32))

        settings_apply_btn = wx.Button(settings_panel, wx.ID_ANY, u"Apply Changes")
        settings_apply_btn.Bind(wx.EVT_BUTTON, self.audioDevChange)

        settings_sizer.Add(st_staticText1, wx.GBPosition(1, 1), wx.GBSpan(1, 10), wx.ALIGN_LEFT, 0)
        settings_sizer.AddSpacer((1, 40), wx.GBPosition(2, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        settings_sizer.Add(spk_icon, wx.GBPosition(3, 1), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)
        settings_sizer.AddSpacer((10, 1), wx.GBPosition(3, 2), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        settings_sizer.Add(audio_text, wx.GBPosition(3, 3), wx.GBSpan(1, 1), wx.ALIGN_LEFT | wx.TOP, 5)
        settings_sizer.Add(self.spk_cb, wx.GBPosition(3, 5), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        settings_sizer.Add(mic_icon, wx.GBPosition(5, 1), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)
        settings_sizer.AddSpacer((10, 1), wx.GBPosition(5, 2), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        settings_sizer.Add(mic_text, wx.GBPosition(5, 3), wx.GBSpan(1, 1), wx.ALIGN_LEFT | wx.TOP, 5)
        settings_sizer.Add(self.mic_cb, wx.GBPosition(5, 5), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        settings_sizer.Add(settings_apply_btn, wx.GBPosition(7, 5), wx.GBSpan(1, 1), wx.ALIGN_LEFT, 0)

        # Country box
        settings_sizer.AddSpacer((1, 10), wx.GBPosition(2, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        settings_panel.SetSizer(settings_sizer)
        settings_panel.Layout()

        ###################################################################################
        #   </settings_panel>
        #   <help_panel>
        ###################################################################################

        help_panel = TabbedBackgroundPanel(u"images/panel/panel-bg-bar.png", self.fancynotebook, wx.ID_ANY)
        help_panel.setStuff(u"images/panel/tabsmoother.png", 5, 49)
        help_panel.SetSizeHints(501, 450)

        help_sizer = wx.GridBagSizer(0, 0)
        help_sizer.SetFlexibleDirection(wx.BOTH)
        help_sizer.SetNonFlexibleGrowMode(wx.FLEX_GROWMODE_SPECIFIED)

        help_sizer.AddSpacer((11, 1), wx.GBPosition(0, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        help_sizer.AddSpacer((1, 20), wx.GBPosition(0, 1), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)

        self.p6_staticText1 = TransparentText(help_panel, wx.ID_ANY, u"Help", wx.DefaultPosition, wx.Size(-1, -1), 0)
        self.p6_staticText1.Wrap(-1)
        self.p6_staticText1.SetFont(wx.Font(14, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.p6_staticText1.SetForegroundColour(wx.Colour(3, 106, 157))
        help_sizer.Add(self.p6_staticText1, wx.GBPosition(1, 1), wx.GBSpan(1, 9), wx.ALIGN_LEFT, 0)

        self.help_webview = FMCWebView(parent=help_panel, size=(475, 370))  # x,y
        self.help_webview.browser.LoadURL("app-storage:///dialer/faq.html")
        help_sizer.AddSpacer((1, 3), wx.GBPosition(2, 0), wx.GBSpan(1, 1), wx.FIXED_MINSIZE, 0)
        help_sizer.Add(self.help_webview, wx.GBPosition(3, 1), wx.GBSpan(1, 9), wx.ALIGN_LEFT, 0)

        help_panel.SetSizer(help_sizer)
        help_panel.Layout()

        ###################################################################################
        #   </help_panel>
        #   <>
        ###################################################################################

        self.fancynotebook.AssignImages(u"images/panel/tab-active.png", u"images/panel/tab-inactive.png")
        self.fancynotebook.AssignForeground(u"images/bar/bar-bottom-left.png")
        self.fancynotebook.AssignIllst(u"images/backgrounds/phone.png", (100, 270))
        self.fancynotebook.AssignFont(wx.Font(13, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"),
                                      wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        self.fancynotebook.AssignColor(wx.Colour(252, 132, 33), wx.Colour(0, 66, 102))

        self.fancynotebook.AddPage(panel1, "Call Phones", 1, 0)
        self.fancynotebook.AddPage(panel2, "Recent Calls", 0, 0)
        self.fancynotebook.AddPage(freecredits_panel, "Get Free Credits", 0, 0)
        self.fancynotebook.AddPage(purchase_credits_panel, "Purchase Credits", 0, 0)
        self.fancynotebook.AddPage(settings_panel, "Settings", 0, 0)
        self.fancynotebook.AddPage(help_panel, "Help", 0, 0)
        # self.fancynotebook.SetSelection(1)


        # tabs = [("tab1",panel1), ("tab2",panel2), ("tab3",panel3), ("tab4",panel4), ("tab5",panel5)]

        # self.TabsPanel = FancyTabsPanel( tabs, 10, self.mainpanel,  wx.ID_ANY, wx.DefaultPosition, wx.Size( 184,300 ), wx.TAB_TRAVERSAL|wx.TRANSPARENT_WINDOW|wx.NO_BORDER )
        # self.TabsPanel.SetMinSize( wx.Size( 184,300 ) )
        # self.TabsPanel.setBackgrounds( u"images/panel/tab-active.png", u"images/panel/tab-inactive.png", u"images/bar/bar-bottom-left.png" )

        # tabsBox = wx.BoxSizer( wx.VERTICAL )

        # self.m_button27 = wx.Button( self.TabsPanel, wx.ID_ANY, u"MyButton", wx.DefaultPosition, wx.DefaultSize, 0 )
        # tabsBox.Add( self.m_button27, 0, wx.ALL|wx.ALIGN_RIGHT, 5 )

        # self.TabsPanel.SetSizer( tabsBox )
        # self.TabsPanel.Layout()

        # self.m_bitmap22 = wx.StaticBitmap( self, wx.ID_ANY, wx.Bitmap( u"images/bar/bar-bottom-right.png", wx.BITMAP_TYPE_ANY ), wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER )
        bSizer11.AddSpacer((15, 15), 0, 0, 5)
        bSizer11.Add(self.fancynotebook, 0, 0, 0)

        # self.DisplayPanel = BackgroundPanel( u"images/panel/panel-bg-bar.png", self.mainpanel, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        # bSizer11.Add( self.DisplayPanel, 1, wx.EXPAND, 5 )


        presenceSizer.Add(bSizer11, 1, wx.EXPAND, 5)

        self.mainpanel.SetSizer(presenceSizer)
        self.mainpanel.Layout()
        OuterSizer.Add(self.mainpanel, 1, wx.EXPAND, 5)

        self.SetSizer(OuterSizer)
        self.Layout()
        # self.m_statusBar1 = self.CreateStatusBar(1, wx.ST_SIZEGRIP, wx.ID_ANY)
        # self.m_statusBar1.SetMinSize(wx.Size(700, 35))

        self.Centre(wx.BOTH)

        self.captureSlider = CaptureVolumeSlider(self.mic_button.GetPosition(), self.onCaptureVolumeChanged,
                                                 u"images/panel/micpopup.png", self.presencepanel, wx.ID_ANY,
                                                 wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER | wx.TAB_TRAVERSAL)
        self.playbackSlider = PlaybackVolumeSlider(self.speaker_button.GetPosition(), self.onPlaybackVolumeChanged,
                                                   u"images/panel/spkpopup.png", self.presencepanel, wx.ID_ANY,
                                                   wx.DefaultPosition, wx.DefaultSize, wx.NO_BORDER | wx.TAB_TRAVERSAL)
        # LastdialedPanel( call[0], call[1], self.dialRecent, u"images/panel/recentcallbg.png", self.recenthistory_panel, wx.ID_ANY, )
        self.captureSlider.Hide()
        self.playbackSlider.Hide()

        self.calltimer = wx.Timer(self, TIMER_CALLDURATION_ID)

        # Connect sgnals
        self.Connect(-1, -1, EVT_CONNECTED_ID, self.onCallConnect)
        self.Connect(-1, -1, EVT_DISCONNECTED_ID, self.onCallDisconnect)
        self.Connect(-1, -1, EVT_STATUS_ID, self.onCallStatus)
        self.Bind(wx.EVT_CLOSE, self.OnFrameClose)
        wx.EVT_TIMER(self, TIMER_CALLDURATION_ID, self.callTimerTick)