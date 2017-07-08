import wx
from utils import *
from web import FMCWebView, NativeCodeScheme
from widgits import TransparentText
from wx.html2 import EVT_WEBVIEW_LOADED

__author__ = 'TheArchitect'


class VideoAdDialog ( wx.Dialog ):
    def __init__( self, parent, adsduration ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Ad window - FreeMyCall", pos = wx.DefaultPosition, size = wx.Size( 800,600 ), style = wx.CAPTION|wx.STAY_ON_TOP )
        self.adretcode = -1
        self.adsduration = adsduration
        self.moveable = False
        self.SetSizeHintsSz( wx.Size( 800,600 ), wx.Size( 800,600 ) )

        self.adtimer = wx.Timer(self, TIMER_ADVERT_ID)
        self.adtimer.timeelapsed = 0
        wx.EVT_TIMER(self, TIMER_ADVERT_ID, self.AdTimerTick)
        self.Bind(wx.EVT_MOVE_END, self.OnMove)

        self.paneltop = wx.Panel(self, size=(-1, 25))
        self.skipbutton = wx.Button( self.paneltop, wx.ID_ANY, u"Skip Ad", wx.DefaultPosition, wx.DefaultSize, 0 )
        self.skipbutton.Bind(wx.EVT_BUTTON, self.OnSkipButtonClick)
        self.skiptextstring = u"Time left"
        self.skiptext = TransparentText( self.paneltop, wx.ID_ANY, self.skiptextstring + " 30 ", wx.Point(700,5), wx.Size(-1,-1), 0 )
        self.skiptext.SetFont( wx.Font( 11, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial" ) )
        self.skiptext.SetForegroundColour( wx.Colour( 204, 0, 0 ) )

        self.paneltop.Bind(wx.EVT_PAINT, self.on_paint_top)
        paneltopsizer = wx.BoxSizer(wx.VERTICAL)
        paneltopsizer.Add(self.skipbutton, 0, wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM|wx.TOP|wx.RIGHT, 5)
        self.paneltop.SetSizer(paneltopsizer)


        self.webview = FMCWebView(parent=self,  size=(794,500))
        self.webview.browser.Bind(EVT_WEBVIEW_LOADED, self.PageLoaded)

        self.panelbottom = wx.Panel(self, size=(-1, 25))
        self.m_staticText = TransparentText( self.panelbottom, wx.ID_ANY, u"Clicking on the ad does not interrupt your call", wx.DefaultPosition, wx.Size(-1,-1), 0 )
        #self.m_staticText.Wrap( -1 )
        self.m_staticText.SetFont( wx.Font( 11, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_BOLD, False, "Arial" ) )
        self.m_staticText.SetForegroundColour( wx.Colour( 3, 106, 157 ) )
        self.panelbottom.Bind(wx.EVT_PAINT, self.on_paint_bottom)
        panelbottomsizer = wx.BoxSizer(wx.VERTICAL)
        panelbottomsizer.Add(self.m_staticText, 0, wx.ALIGN_CENTRE|wx.TOP,10 )
        self.panelbottom.SetSizer(panelbottomsizer)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.paneltop, 1, wx.EXPAND, 0)
        sizer.Add(self.webview, 1, wx.EXPAND, 0)
        sizer.Add(self.panelbottom, 1, wx.EXPAND, 0)

        self.SetSizer(sizer)
        self.SetSize((800, 600))
        self.Layout()

        self.scheme_callables = { "printarg" : self.PrintArg, "close" : self.CloseAdDialog, "onadclick": self.OnAdClick }
        scheme = NativeCodeScheme("app", self.scheme_callables)
        self.webview.RegisterHandler(scheme)

        self.Centre( wx.BOTH )
        self.skipbutton.Hide()

    def __del__( self ):
        pass

    def CloseAdDialog(self, retcode=-1):
        if type(retcode) != int:
            retcode = int(retcode)
        self.adretcode = retcode
        if self.IsModal():
            self.EndModal(retcode)
        self.SetReturnCode(retcode)
        self.Close()

    def OnAdClick(self):
        self.moveable = True

    def OnSkipButtonClick(self, event):
        self.CloseAdDialog(0)

    def PageLoaded(self, event):
        if not self.adtimer.IsRunning():
            self.adtimer.Start(1000)

    def AdTimerTick(self, event):
        self.adtimer.timeelapsed += 1000
        if self.adtimer.timeelapsed >= self.adsduration:
            self.skiptext.Hide()
            self.skipbutton.Show()
            self.adtimer.Stop()
        timeleft = self.adsduration - self.adtimer.timeelapsed
        timeleft = int(timeleft/1000)
        self.skiptext.UpdateLabel("%s %d" % (self.skiptextstring, timeleft))

    def OnMove(self, event):
        if not self.moveable:
            self.Center(wx.BOTH)
        event.Skip()

    def on_paint_top(self, event):
        # establish the painting canvas
        dc = wx.PaintDC(self.paneltop)
        x = 0
        y = 0
        w, h = self.paneltop.GetSize()
        dc.GradientFillLinear((x, y, w, h), '#cccccc', 'white', wx.DOWN)

    def on_paint_bottom(self, event):
        # establish the painting canvas
        dc = wx.PaintDC(self.panelbottom)
        x = 0
        y = 0
        w, h = self.panelbottom.GetSize()
        dc.GradientFillLinear((x, y, w, h), '#cccccc', 'white', wx.UP)

    def PrintArg(self, arg1="d", arg2="d"):
        print "Printargs called with ", arg1, arg2

if __name__=="__main__":
    app = wx.App()
    d = VideoAdDialog(None, 30000)
    d.webview.browser.LoadURL("app-storage:///dialer/ads.html")
    #d.webview.browser.LoadURL("https://www.youtube.com/watch?v=66TuSJo4dZM")
    ret = d.ShowModal()
    print "ret = ", d.adretcode, ret
    d.Destroy()

    app.MainLoop()
