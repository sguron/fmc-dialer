import wx
from widgits import TransparentText, TransparentBitmap, BackgroundPanel, ShapedButton
from utils import TIMER_CALLDURATION_ID

__author__ = 'TheArchitect'


class LastdialedPanel(BackgroundPanel):  #target - > 153 X 70 pixels
    def __init__(self, number, country, dialfn, *args, **kw_args):
        super(LastdialedPanel, self).__init__(*args, **kw_args)
        self.country = country
        self.flag = self.country[1]
        self.number = number
        self.dial_function = dialfn
        parent = self

        sizer = wx.BoxSizer()
        sizer = wx.GridBagSizer(0,0)
        sizer.SetFlexibleDirection( wx.BOTH )
        sizer.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        sizer.AddSpacer( ( 1, 9 ), wx.GBPosition( 0, 1 ), wx.GBSpan( 1, 1 ), wx.FIXED_MINSIZE, 0 )
        sizer.AddSpacer( ( 10, 1 ), wx.GBPosition( 0, 0 ), wx.GBSpan( 1, 1 ), wx.FIXED_MINSIZE, 0 )

        flag = TransparentBitmap( u'images/flags/%s.png' % country[1].lower(), parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize )
        sizer.Add( flag, wx.GBPosition( 1, 1 ), wx.GBSpan( 2, 1 ), wx.ALIGN_LEFT, 0 )

        sizer.AddSpacer( ( 9, 1 ), wx.GBPosition( 0, 2 ), wx.GBSpan( 1, 1 ), wx.FIXED_MINSIZE, 0 )

        if self.country[3]:
            txt = u"+" + self.country[3] + self.number
        else:
            txt = u"" + self.number
        numbertxt =  TransparentText( parent, wx.ID_ANY, txt, wx.DefaultPosition, wx.Size(100,-1), 0 )
        numbertxt.SetFont( wx.Font( 10, wx.FONTFAMILY_SWISS, 90, wx.FONTWEIGHT_NORMAL, False, "Arial" ) )
        numbertxt.SetForegroundColour( wx.Colour( 3, 106, 157 ) )
        sizer.Add( numbertxt, wx.GBPosition( 1, 3 ), wx.GBSpan( 1, 4 ), wx.ALIGN_LEFT, 0 )

        sizer.AddSpacer( ( 55, 1 ), wx.GBPosition( 2, 3 ), wx.GBSpan( 1, 1 ), wx.FIXED_MINSIZE, 0 )

        callbtn = ShapedButton(u"images/keypad/normal/recent-call.png", parent, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize )
        callbtn.SetAdditionalImages(u"images/keypad/over/recent-call.png")
        callbtn.Bind(wx.EVT_BUTTON, self.dial_function)
        sizer.Add( callbtn, wx.GBPosition( 2, 5 ), wx.GBSpan( 1, 1 ), wx.ALIGN_LEFT, 0 )

        self.SetMaxSize(wx.Size(160, 73))
        self.SetSizer(sizer)
        self.Layout()

    def GetBestSize(self):
        wx.Size(160, 70)


class AbstractVolumeSlider(BackgroundPanel):
    def __init__(self, *args, **kw_args):
        super(AbstractVolumeSlider, self).__init__(*args, **kw_args)
        self.timer_duration = 3 * 1000  # 3 seconds
        self.mouseinside = False
        self.needsclosing = False
        self.timer = wx.Timer(self, TIMER_CALLDURATION_ID)
        self.slider = wx.Slider( self, wx.ID_ANY, 60, 0, 100, (5,0), (-1,self.height), wx.SL_VERTICAL|wx.NO_BORDER|wx.TRANSPARENT_WINDOW|wx.SL_INVERSE )
        wx.EVT_TIMER(self, TIMER_CALLDURATION_ID, self.timer_tick)
        self.Bind(wx.EVT_SHOW, self.on_window_show)
        self.slider.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window)
        self.slider.Bind(wx.EVT_ENTER_WINDOW, self.on_enter_window)
        self.app = wx.GetApp()

    def on_leave_window(self, event):
        self.needsclosing = True
        self.timer.Start(self.timer_duration)

    def on_enter_window(self, event):
        self.needsclosing = False
        self.timer.Stop()

    def timer_tick(self, event):
        if self.needsclosing:
            self.Hide()
            return

    def on_window_show(self, event):
        if event.GetShow():
            self.needsclosing = True
            self.timer.Start(self.timer_duration)
            #print "Timer (re)Started"

    def GetBestSize(self):
        wx.Size(self.width, self.height)

    def sliderChange(self, event):
        value =  event.GetPosition()
        self.updateFn(value)


class CaptureVolumeSlider(AbstractVolumeSlider):
    def __init__(self, pos, updatefunction, *args, **kw_args):
        self.width = 53
        self.height = 67
        super(CaptureVolumeSlider, self).__init__(*args, **kw_args)
        self.slidervalue = float(self.app.config_get("audio",'%svolume' % 'capture', 0)) * 10

        self.updateFn = updatefunction

        self.slider.SetBackgroundColour( wx.Colour( 217, 217, 217 ) )
        micicon = TransparentBitmap( u'images/bar/mic-button.png', self, wx.ID_ANY, (28,8), (23,28), )
        self.slider.SetSize(wx.Size(25,67))
        self.SetSize((self.width,self.height))
        pos.x -= 30
        pos.y = 0
        self.SetPosition(pos)
        self.slider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.sliderChange)

        self.slider.SetValue(self.slidervalue)


class PlaybackVolumeSlider(AbstractVolumeSlider):
    def __init__(self, pos, updatefunction, *args, **kw_args):
        self.width = 53
        self.height = 67
        super(PlaybackVolumeSlider, self).__init__(*args, **kw_args)
        self.slidervalue = float(self.app.config_get('audio','%svolume' % 'playback', 10)) * 10
        #print "PlaybackVolumeSlider", self.slidervalue

        self.updateFn = updatefunction
        self.slider.SetBackgroundColour( wx.Colour( 217, 217, 217 ) )
        spkicon = TransparentBitmap( u'images/bar/speaker-button.png', self, wx.ID_ANY, (28,34), (23,28), )
        self.slider.SetSize(wx.Size(25,67))
        self.SetSize((self.width,self.height))
        pos.x -= 30
        pos.y = 0
        self.SetPosition(pos)
        self.slider.Bind(wx.EVT_SCROLL_THUMBTRACK, self.sliderChange)
        self.slider.SetValue(self.slidervalue)
        self.updateFn(self.slidervalue)

