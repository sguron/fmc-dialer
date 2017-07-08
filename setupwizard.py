import wx
import ctypes
from utils import *
from widgits import BackgroundPanel, ShapedButton, TransparentText, TransparentBitmap

__author__ = 'TheArchitect'


class SetupWizard(wx.Frame):
    def SetupAudio(self):
        #self.Hide()
        self.app.WizardClose()

    def OnShowReview(self, event):
        #self.testtext.SetLabel(txt)
        if event.IsShown():
            self.spktext.UpdateLabel(self.spk_cb.GetStringSelection())
            self.mictext.UpdateLabel(self.mic_cb.GetStringSelection())

    def buildAudioDeviceDropdown(self):
        devices = self.app.phone.getAudioDevices()
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

        self.app.changeAudioDevices(cap, play)

    def playTestTone(self, event):
        if self.playenable:
            self.playenable = False
            self.button_playtone.Disable()
            self.app.phone.playTestTone()
            self.text_playtone.SetLabel(u"Playing Tone")
            self.tone_timer.Start(DURATION_TESTTONE, wx.TIMER_ONE_SHOT)

    def timerTick(self, event):
        self.text_playtone.SetLabel(u"Stopped")
        self.playenable = True
        self.button_playtone.Enable()

    def ShowPrevious(self):
        if self.m_index > 0:
            current = self.m_pages[self.m_index]
            prev = self.m_pages[self.m_index - 1]
            current.Hide()
            prev.Show()
            self.m_index -= 1
        if self.m_index == 0:
            self.prev_button.Disable()
        if self.m_index == len(self.m_pages) - 2:
            self.next_button.SetLabel(u"Next")

    def ShowNext(self):
        if self.m_index < len(self.m_pages) - 1:
            current = self.m_pages[self.m_index]
            next = self.m_pages[self.m_index + 1]
            current.Hide()
            next.Show()
            self.m_index += 1
        if self.m_index == len(self.m_pages) - 1:
            self.next_button.SetLabel(u"Finish")
        else:
            self.next_button.SetLabel(u"Next")
        if not self.prev_button.IsEnabled():
                self.prev_button.Enable()

    def OnClickNext(self, event):
        if self.next_button.GetLabel() == u"Finish":
            self.SetupAudio()
        else:
            self.ShowNext()

    def OnClickPrev(self, event):
        self.ShowPrevious()

    def OnMouseDown(self, event):
        pos = event.GetPosition()
        if pos.y < self.header_distance:  # Only if y is inside header
            self.dragenable = True
        event.Skip()

    def OnMouseLeave(self, event):
        self.dragenable = False

    def OnMouse(self, event):
        """implement dragging"""
        if not event.Dragging():
            self._dragPos = None
            return

        if not self.dragenable:
            return

        self.CaptureMouse()
        if not self._dragPos:
            self._dragPos = event.GetPosition()
        else:
            pos = event.GetPosition()
            if pos.y < self.header_distance:
                displacement = self._dragPos - pos
                self.SetPosition(self.GetPosition() - displacement)
        self.ReleaseMouse()
        self.Update()

    def DropShadow(self, drop=True):
        if wx.Platform != "__WXMSW__":
            # This works only on windows
            return

        hwnd = self.GetHandle()
        print "handle wizard=", hwnd
        CS_DROPSHADOW = 0x00020000
        GCL_STYLE = -26

        csstyle = ctypes.windll.user32.GetWindowLongA(hwnd, GCL_STYLE)
        if drop:
            if csstyle & CS_DROPSHADOW:
                return
            else:
                csstyle |= CS_DROPSHADOW     #Nothing to be done
        else:
            csstyle &= ~CS_DROPSHADOW

        cstyle= ctypes.windll.user32.GetClassLongA(hwnd, GCL_STYLE)
        if drop:
            if cstyle & CS_DROPSHADOW == 0:
                ctypes.windll.user32.SetClassLongA(hwnd, GCL_STYLE, cstyle | CS_DROPSHADOW)
        else:
            ctypes.windll.user32.SetClassLongA(hwnd, GCL_STYLE, cstyle & ~CS_DROPSHADOW)

    def __init__(self, parent=None):
        super(SetupWizard, self).__init__(parent, id=wx.ID_ANY, title=u"FreeMyCall Setup Wizard",
                                          pos=wx.DefaultPosition,
                                          size=wx.Size(596, 385), style=wx.NO_BORDER | wx.FRAME_SHAPED)
        self.SetBackgroundColour(wx.Colour(255, 255, 255, 0))
        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)

        image = wx.Image(u"images/wizard/mask.png", wx.BITMAP_TYPE_PNG)
        image.SetMaskColour(255, 0, 0)
        image.SetMask(True)
        self.bmp = wx.BitmapFromImage(image)
        self.SetShape(wx.RegionFromBitmap(self.bmp))

        self.bgpanel = BackgroundPanel(u"images/wizard/background.png", self, wx.ID_ANY, wx.DefaultPosition,
                                       size=(596, 385), style=wx.TAB_TRAVERSAL | wx.NO_BORDER)
        self.bgpanel.SetMinSize(wx.Size(596, 385))
        self.bgpanel.Bind(wx.EVT_MOTION, self.OnMouse)
        self.bgpanel.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.bgpanel.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)

        self.next_button = wx.Button(self.bgpanel, wx.ID_ANY, u"Next", wx.Point(491, 340), wx.DefaultSize, 0)
        self.next_button.Bind(wx.EVT_BUTTON, self.OnClickNext)
        self.prev_button = wx.Button(self.bgpanel, wx.ID_ANY, u"Previous", wx.Point(386, 340), wx.DefaultSize, 0)
        self.prev_button.Bind(wx.EVT_BUTTON, self.OnClickPrev)
        self.prev_button.Disable()

        ####################################################
        #
        #              Describing the panels here
        #
        ####################################################
        self.panel1 = BackgroundPanel(u"", self.bgpanel, wx.ID_ANY, wx.Point(2, 88), wx.Size(591, 230),
                                      wx.TAB_TRAVERSAL | wx.NO_BORDER)
        # self.panel1.SetMinSize(wx.Size(591, 230))
        text_panel1_s1 = TransparentText(self.panel1, wx.ID_ANY, u"Step 1:                   Audio output device",
                                         wx.DefaultPosition,
                                         wx.Size(200, 20), 0)
        text_panel1_s1.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        text_panel1_s1.SetForegroundColour(wx.Colour(3, 106, 157))

        # self.text_playtone = TransparentText(self.panel1, wx.ID_ANY, u"Not playing", wx.DefaultPosition,
        #                                     wx.Size(100, 20), 0)
        self.text_playtone = wx.StaticText(self.panel1, label=u"Not playing")
        self.text_playtone.SetFont(wx.Font(9, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.text_playtone.SetForegroundColour(wx.Colour(102, 102, 102))
        self.text_playtone.SetBackgroundColour(wx.WHITE)

        htext = u"Select the speaker or headphone that you would\n" \
                u"like to use as the audio output device.\n" \
                u"Headphones are recommended over speakers."
        helptext = TransparentText(self.panel1, wx.ID_ANY, htext, wx.DefaultPosition,
                                   wx.Size(200, 20), 0)
        helptext.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        helptext.SetForegroundColour(wx.Colour(3, 106, 157))

        spk_icon = TransparentBitmap(u'images/bar/speaker-button.png', self.panel1, wx.ID_ANY, wx.DefaultPosition,
                                     wx.DefaultSize, 0)
        # Get the
        self.spk_cb = wx.ComboBox(self.panel1, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size(190, 32), "",
                                  wx.CB_READONLY | wx.TRANSPARENT_WINDOW)
        self.spk_cb.SetMinSize(wx.Size(190, 32))
        self.button_playtone = wx.Button(self.panel1, wx.ID_ANY, u"Play test tone", wx.DefaultPosition, wx.DefaultSize,
                                         0)
        self.button_playtone.Bind(wx.EVT_BUTTON, self.playTestTone)

        text_panel1_s1.SetPosition(wx.Point(60, 20))
        spk_icon.SetPosition(wx.Point(75, 55))
        spk_icon.SetSize(spk_icon.DoGetBestSize())
        self.spk_cb.SetPosition(wx.Point(185, 60))
        self.button_playtone.SetPosition(wx.Point(405, 58))
        self.text_playtone.SetPosition(wx.Point(410, 100))
        helptext.SetPosition(wx.Point(185, 160))
        self.panel1.Show()

        ###########################################################
        #
        #       Panel 2 (mic) starts
        #
        ############################################################

        self.panel2 = BackgroundPanel(u"", self.bgpanel, wx.ID_ANY, wx.Point(2, 88), wx.Size(591, 230),
                                      wx.TAB_TRAVERSAL | wx.NO_BORDER)
        self.panel2.SetMinSize(wx.Size(591, 230))
        self.mic_cb = wx.ComboBox(self.panel2, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size(190, 32), "",
                                  wx.CB_READONLY | wx.TRANSPARENT_WINDOW)
        self.mic_cb.SetMinSize(wx.Size(190, 32))
        mic_icon = TransparentBitmap(u'images/bar/mic-button.png', self.panel2, wx.ID_ANY, wx.DefaultPosition,
                                     wx.DefaultSize, 0)
        text_panel2_s1 = TransparentText(self.panel2, wx.ID_ANY, u"Step 2:                   Audio input device",
                                         wx.DefaultPosition,
                                         wx.Size(200, 20), 0)
        text_panel2_s1.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        text_panel2_s1.SetForegroundColour(wx.Colour(3, 106, 157))

        # htext2 = u"Select the speaker or headphone that you would\n" \
        #        u"like to use as the audio output device.\n" \
        #        u"Headphones are recommended over speakers."
        # helptext2 = TransparentText(self.panel2, wx.ID_ANY, htext2, wx.DefaultPosition,
        #                                     wx.Size(200, 20), 0)
        # helptext2.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        # helptext2.SetForegroundColour(wx.Colour(3, 106, 157))

        text_panel2_s1.SetPosition(wx.Point(60, 20))
        mic_icon.SetPosition(wx.Point(75, 55))
        mic_icon.SetSize(spk_icon.DoGetBestSize())
        self.mic_cb.SetPosition(wx.Point(185, 60))
        # helptext2.SetPosition(wx.Point(185, 160))
        self.panel2.Hide()

        ###########################################################
        #
        #       Panel 3 (review) starts
        #
        ############################################################

        self.panel3 = BackgroundPanel(u"", self.bgpanel, wx.ID_ANY, wx.Point(2, 88), wx.Size(591, 230),
                                      wx.TAB_TRAVERSAL | wx.NO_BORDER)
        self.panel3.SetMinSize(wx.Size(591, 230))

        text_panel3_s1 = TransparentText(self.panel3, wx.ID_ANY, u"Step 3:                   Review Settings",
                                         wx.DefaultPosition,
                                         wx.Size(200, 20), 0)
        text_panel3_s1.SetFont(wx.Font(11, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        text_panel3_s1.SetForegroundColour(wx.Colour(3, 106, 157))

        self.mictext = TransparentText(self.panel3, wx.ID_ANY, u"mic name", (50, 50),
                                       wx.Size(200, 20), 0)
        self.spktext = TransparentText(self.panel3, wx.ID_ANY, u"spk name", (50, 50),
                                       wx.Size(200, 20), 0)
        self.spktext.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        self.spktext.SetForegroundColour(wx.Colour(3, 106, 157))
        self.mictext.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        self.mictext.SetForegroundColour(wx.Colour(3, 106, 157))

        p3_mic_icon = TransparentBitmap(u'images/bar/mic-button.png', self.panel3, wx.ID_ANY, wx.DefaultPosition,
                                        wx.DefaultSize, 0)
        p3_spk_icon = TransparentBitmap(u'images/bar/speaker-button.png', self.panel3, wx.ID_ANY, wx.DefaultPosition,
                                        wx.DefaultSize, 0)

        htext3 = u"Click finish to save settings and open dialer."
        helptext3 = TransparentText(self.panel3, wx.ID_ANY, htext3, wx.DefaultPosition,
                                    wx.Size(200, 20), 0)
        helptext3.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial"))
        helptext3.SetForegroundColour(wx.Colour(3, 106, 157))
        text_panel3_s1.SetPosition(wx.Point(60, 20))
        p3_spk_icon.SetPosition(wx.Point(75, 55))
        p3_mic_icon.SetPosition(wx.Point(75, 95))
        self.spktext.SetPosition(wx.Point(185, 60))
        self.mictext.SetPosition(wx.Point(185, 100))
        helptext3.SetPosition(wx.Point(185, 190))
        self.panel3.Hide()
        self.panel3.Bind(wx.EVT_SHOW, self.OnShowReview)
        self.spk_cb.Bind(wx.EVT_COMBOBOX, self.audioDevChange)
        self.mic_cb.Bind(wx.EVT_COMBOBOX, self.audioDevChange)

        ##################################################################################
        ##################################################################################

        self.m_pages = [self.panel1, self.panel2, self.panel3]
        self.m_index = 0
        self.app = wx.GetApp()
        self.tone_timer = wx.Timer(self, TIMER_TESTTONE_ID)
        wx.EVT_TIMER(self, TIMER_TESTTONE_ID, self.timerTick)
        self.header_distance = 73
        self.dragenable = False
        self.playenable = True

        self.Centre(wx.BOTH)
        # self.buildAudioDeviceDropdown()
        # self.DropShadow()

    def __del__(self):
        pass


if __name__ == '__main__':
    from softphone import Softphone
    app = wx.App()
    app.phone = Softphone()
    app.phone.runSoftphone()
    wizard = SetupWizard(None)

    wizard.Show()
    #print "Dialog destroyed"
    #wizard.Destroy()

    app.MainLoop()

