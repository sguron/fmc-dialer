import wx
import wx.animate
from widgits import BackgroundPanel, ShapedButton, TransparentText
import time
from utils import *
import ctypes


__author__ = 'TheArchitect'



###########################################################################
## Class LoginFrame
###########################################################################

class LoginFrame(wx.Frame):
    def __del__(self):
        pass

    def DisableInputElements(self):
        self.btn_login.Disable()
        self.error_text.Hide()
        self.loadinganimation.Show()
        self.loadinganimation.Play()
        self.txtbx_username.Disable()
        self.txtbx_password.Disable()

    def EnableInputElements(self):
        self.txtbx_username.Enable()
        self.txtbx_password.Enable()
        self.btn_login.Enable()
        self.loadinganimation.Stop()
        self.loadinganimation.Hide()

    def OnLogin(self, event):
        if self.app.kill:
            self.DialerAlert()
            return
        self.DisableInputElements()

        #app = wx.GetApp()
        if self.app.bgstart:
            self.app.bgstart = False
        wx.CallAfter(self.app.login, self.txtbx_username.GetValue(), self.txtbx_password.GetValue())
        event.Skip()

    def LoginResult(self, event):
        self.EnableInputElements()
        if event.success:
            pass
            #print "Logged in"
        else:
            self.error_text.UpdateLabel(event.error_text)
            self.error_text.Show()
            #print "Login failed"
        #app = ex.GetApp()
        #app.dialerframe.Show()
        #self.Hide()
        event.Skip()

    def DialerAlert(self):
        error_text = "The application failed to initliaze due to missing files. Please reinstall the application and try again. Please contact support if error presists after reinstallation."
        dlg = wx.MessageDialog(self, error_text, "Application error", wx.OK | wx.ICON_ERROR)
        dlg.ShowModal()
        dlg.Destroy()

    def ClearPassword(self):
        self.txtbx_password.SetValue('')

    def OnSignup(self, event):
        try:
            wx.LaunchDefaultBrowser(FMC_SIGNUP_URL)
        except:
            pass

    def OnForgot(self, event):
        try:
            wx.LaunchDefaultBrowser(FMC_FORGOT_URL)
        except:
            pass

    def OnMin(self, event):
        self.Iconize()

    def OnClose(self, event):
        self.Hide()

    def OnShow(self, event):
        #event.Skip()
        if self.app.kill:
            self.DialerAlert()
        #print "Window shown"

    def OnMouseDown(self, event):
        pos = event.GetPosition()
        if pos.y < self.top_shadow + self.header_distance:
            self.dragenable = True
        #   print "Dragable"
        event.Skip()

    def OnMouseLeave(self,event):
        self.dragenable = False
        #print "Non dragable"

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
            #print time.time(), "_dragPos"
        else:
            pos = event.GetPosition()
            #print time.time(), pos
            if pos.y < self.top_shadow + self.header_distance:
                displacement = self._dragPos - pos
                self.SetPosition( self.GetPosition() - displacement )
        self.ReleaseMouse()
        self.Update()

    def DropShadow(self, drop=True):
        if wx.Platform != "__WXMSW__":
            # This works only on windows
            return

        hwnd = self.GetHandle()
        print "handle login=", hwnd

        CS_DROPSHADOW = 0x00020000
        GCL_STYLE= -26

        csstyle = ctypes.windll.user32.GetWindowLongA(hwnd, GCL_STYLE)
        if drop:
            if csstyle & CS_DROPSHADOW:
                return
            else:
                csstyle |= CS_DROPSHADOW
        else:
            csstyle &= ~CS_DROPSHADOW

        # Drop the shadow underneath the window

        cstyle= ctypes.windll.user32.GetClassLongA(hwnd, GCL_STYLE)
        if drop:
            if cstyle & CS_DROPSHADOW == 0:
                ctypes.windll.user32.SetClassLongA( hwnd, GCL_STYLE, cstyle | CS_DROPSHADOW)
        else:
            ctypes.windll.user32.SetClassLongA( hwnd, GCL_STYLE, cstyle &~ CS_DROPSHADOW)

    def __init__(self, parent=None):

        super(LoginFrame, self).__init__(parent, id=wx.ID_ANY, title=u"FreeMyCall", pos=wx.DefaultPosition,
                                         size=wx.Size(313, 545), style=wx.NO_BORDER | wx.FRAME_SHAPED)
        self.SetBackgroundColour(wx.Colour(255, 255, 255, 0))
        # self.SetExtraStyle(wx.WS)
        # self.SetTransparent( 254 )
        self.SetSizeHintsSz(wx.DefaultSize, wx.DefaultSize)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Connect(-1, -1, EVT_SIGNINRESULT_ID, self.LoginResult)

        image = wx.Image(u"images/loginframe/mask.png", wx.BITMAP_TYPE_PNG)
        image.SetMaskColour(255, 0, 0)
        image.SetMask(True)
        self.bmp = wx.BitmapFromImage(image)
        self.SetShape(wx.RegionFromBitmap(self.bmp))

        self.app = wx.GetApp()

        self.panel = BackgroundPanel(u"images/loginframe/background.png", self, wx.ID_ANY, wx.DefaultPosition,
                                     (313, 545), wx.TAB_TRAVERSAL | wx.NO_BORDER)
        self.panel.SetMinSize(wx.Size(313, 545))
        self.panel.Bind(wx.EVT_MOTION, self.OnMouse)
        self.panel.Bind(wx.EVT_LEFT_DOWN, self.OnMouseDown)
        self.panel.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeave)
        self.Bind(wx.EVT_SHOW, self.OnShow)

        self.btn_login = ShapedButton(u"images/loginframe/signin.png", self.panel, wx.ID_ANY, wx.DefaultPosition,
                                      wx.DefaultSize)
        self.btn_login.SetAdditionalImages(u"images/loginframe/signin-pressed.png",
                                           u"images/loginframe/signin-disabled.png")
        self.btn_login.Bind(wx.EVT_BUTTON, self.OnLogin)

        # self.btn_login.Disable()
        self.btn_forgot = ShapedButton(u"images/loginframe/forgotpass.png", self.panel, wx.ID_ANY, wx.DefaultPosition,
                                       wx.DefaultSize)
        self.btn_forgot.Bind(wx.EVT_BUTTON, self.OnForgot)
        self.btn_forgot.SetCursor(wx.StockCursor(wx.CURSOR_HAND))
        self.btn_signup = ShapedButton(u"images/loginframe/signup.png", self.panel, wx.ID_ANY, wx.DefaultPosition,
                                       wx.DefaultSize)
        self.btn_signup.Bind(wx.EVT_BUTTON, self.OnSignup)
        self.btn_signup.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

        self.btn_min = ShapedButton(u"images/loginframe/min.png", self.panel, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize)
        self.btn_min.SetAdditionalImages(u"images/loginframe/min-pressed.png")
        self.btn_min.Bind(wx.EVT_BUTTON, self.OnMin)

        self.btn_max = ShapedButton(u"images/loginframe/max.png", self.panel, wx.ID_ANY, wx.DefaultPosition,
                                    wx.DefaultSize)
        self.btn_max.SetAdditionalImages(u"images/loginframe/max-pressed.png")
        self.btn_max.Bind(wx.EVT_BUTTON, self.OnClose)

        self.error_text = TransparentText(self.panel, wx.ID_ANY, u"", wx.DefaultPosition, wx.Size(255, -1), 0)
        self.error_text.SetFont(wx.Font(10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial"))
        self.error_text.SetForegroundColour(wx.Colour(204, 51, 51))

        self.txtbx_username = wx.TextCtrl(self.panel, wx.ID_ANY, self.app.user.username, wx.DefaultPosition, (227, 22),
                                          wx.NO_BORDER)
        self.txtbx_username.SetFont(wx.Font(12, 74, 90, 90, False, "Arial"))
        self.txtbx_username.SetForegroundColour(wx.Colour(0, 70, 109))
        self.txtbx_username.SetBackgroundColour(wx.Colour(241, 241, 241))
        self.txtbx_password = wx.TextCtrl(self.panel, wx.ID_ANY, u"", wx.DefaultPosition, (227, 22),
                                          wx.TE_PASSWORD | wx.NO_BORDER | wx.TE_PROCESS_ENTER)
        self.txtbx_password.SetFont(wx.Font(12, 74, 90, 90, False, "Arial"))
        self.txtbx_password.SetForegroundColour(wx.Colour(0, 70, 109))
        self.txtbx_password.SetBackgroundColour(wx.Colour(241, 241, 241))
        self.txtbx_password.Bind(wx.EVT_TEXT_ENTER, self.OnLogin)

        self.top_shadow = 0  # 15
        self.left_shadow = 0  # 18
        self.header_distance = 80
        self.dragenable = False

        self.loadinganimation = wx.animate.GIFAnimationCtrl(self.panel, wx.ID_ANY, u"images/loginframe/ajax-loader.gif",
                                                            pos=(10, 10))  # 133,123
        self.loadinganimation.Hide()

        self.btn_min.SetPosition(wx.Point(self.left_shadow + 244, self.top_shadow + 5))
        self.btn_max.SetPosition(wx.Point(self.left_shadow + 276, self.top_shadow + 5))
        self.txtbx_username.SetPosition(wx.Point(self.left_shadow + 38, self.top_shadow + 227))
        self.txtbx_password.SetPosition(wx.Point(self.left_shadow + 38, self.top_shadow + 324))
        self.btn_login.SetPosition(wx.Point(self.left_shadow + 111, self.top_shadow + 384))
        self.btn_forgot.SetPosition(wx.Point(self.left_shadow + 22, self.top_shadow + 456))
        self.btn_signup.SetPosition(wx.Point(self.left_shadow + 167, self.top_shadow + 456))
        self.error_text.SetPosition(wx.Point(self.left_shadow + 27, self.top_shadow + 129))

        self.loadinganimation.SetPosition(wx.Point(self.left_shadow + 148, self.top_shadow + 123))

        self.Layout()

        self.Centre(wx.BOTH)

        # self.DropShadow()
        self.Hide()
