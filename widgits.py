import wx
from wx.lib.stattext import GenStaticText
import array

__author__ = 'TheArchitect'


class BackgroundPanel(wx.Panel):
    def __init__(self, bg, *args, **kw_args):
        super(BackgroundPanel, self).__init__(*args, **kw_args)
        self.SetWindowStyle(self.GetWindowStyle() | wx.TRANSPARENT_WINDOW)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.bg = bg
        if self.bg == '' or self.bg is None:
            self.bitmap = None
        else:
            self.bitmap = wx.Bitmap(bg)
        self.bg_x = 0
        self.bg_y = 0

        #self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def SetBackgroundPos(self, bg_x=0, bg_y=0):
        self.bg_x = bg_x
        self.bg_y = bg_y

    def on_paint(self, evt):
        if self.bitmap is None:
            evt.Skip()
            return
        bdc = wx.PaintDC(self)
        dc = wx.GCDC(bdc)
        rect = self.GetUpdateRegion().GetBox()
        dc.SetClippingRect(rect)
        dc.Clear()
        dc.DrawBitmap(self.bitmap, self.bg_x, self.bg_y, True)


class TabbedBackgroundPanel(wx.Panel):
    def __init__(self, bg,  *args, **kw_args):
        super(TabbedBackgroundPanel, self).__init__(*args, **kw_args)
        self.SetWindowStyle(self.GetWindowStyle() | wx.TRANSPARENT_WINDOW)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.bitmap = wx.Bitmap(bg)
        self.bg_x = 0
        self.bg_y = 0

        self.active_tab_height = 0
        self.overlap = 0
        self.inacvtive_tab_height = 0
        self.tab_index = 0
        self.tabsmoother = wx.NullBitmap

        self.overlay_images = []
        self.Bind(wx.EVT_PAINT, self.onn_paint)

    def SetBackgroundPos(self, bg_x=0, bg_y=0):
        self.bg_x = bg_x
        self.bg_y = bg_y

    def AddOverlayImage(self, bitmap, x, y):
        item = (wx.Bitmap(bitmap), x, y)
        self.overlay_images.append(item)

    def onn_paint(self, evt):
        #print "BGPanel:Paint Start"
        pdc = wx.PaintDC(self)

        dc = wx.GCDC(pdc)

        rect = self.GetUpdateRegion().GetBox()
        dc.SetClippingRect(rect)
        dc.Clear()


        #Draw the background
        dc.DrawBitmap(self.bitmap, self.bg_x, self.bg_y, True)


        #Draw the tabs smoother
        inactivepos = (self.inacvtive_tab_height - self.overlap) * self.tab_index
        activepos = inactivepos - 9
        if self.tab_index == 0:
            rect = wx.Rect(0, 10, self.tabsmoother.GetWidth(), self.tabsmoother.GetHeight() - 10)
            subbitmap = self.tabsmoother.GetSubBitmap(rect)
            dc.DrawBitmap(subbitmap, 0, 10, True)
        else:
            dc.DrawBitmap(self.tabsmoother, 0, activepos, True)

        #Draw overlay images:
        for overlay in self.overlay_images:
            dc.DrawBitmap(overlay[0], overlay[1], overlay[2])
        #print "BGPanel:Paint Stop"



    def setStuff(self, tabsmoother, tab_index, inactivetabheight, overlap=10):
        self.tabsmoother = wx.Bitmap(tabsmoother)
        self.tab_index = tab_index
        self.inacvtive_tab_height = inactivetabheight
        self.overlap = overlap



class TransparentBitmap(wx.PyControl):
    def __init__(self, normal, *args, **kw_args):
        super(TransparentBitmap, self).__init__(*args, **kw_args)
        self.SetWindowStyle(self.GetWindowStyle() | wx.NO_BORDER | wx.TRANSPARENT_WINDOW)
        self.bitmap = wx.Bitmap(normal)
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.SetSize(self.bitmap.GetSize())

    def DoGetBestSize(self):
        return self.bitmap.GetSize()

    def on_size(self, event):
        event.Skip()
        self.Refresh()

    def on_paint(self, event):
        bdc = wx.PaintDC(self)

        dc = wx.GCDC(bdc)
        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetBackground(wx.TRANSPARENT_BRUSH)
        dc.Clear()
        dc.DrawBitmap(self.bitmap, 0, 0, True)

        event.Skip()

    def ChangeSource(self, source):
        self.bitmap = wx.Bitmap(source)
        self.GetParent().Refresh(False, self.GetRect())


class ShapedButton(wx.PyControl):
    def __init__(self, normal, *args, **kw_args):
        super(ShapedButton, self).__init__(*args, **kw_args)
        self.SetWindowStyle(self.GetWindowStyle() | wx.NO_BORDER | wx.TRANSPARENT_WINDOW)
        self.normal = wx.Bitmap(normal)
        self.pressed = None
        self.disabled = None
        self.region = wx.RegionFromBitmapColour(self.normal, wx.Colour(0, 0, 0, 0))
        self._clicked = False
        self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
        self.SetSize(self.DoGetBestSize())
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_left_down)
        self.Bind(wx.EVT_LEFT_DCLICK, self.on_left_dclick)
        self.Bind(wx.EVT_LEFT_UP, self.on_left_up)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.on_leave_window)

    def AcceptsFocus(self):
        return True

    def SetAdditionalImages(self, pressed, disabled=None):
        self.pressed = wx.Bitmap(pressed)
        if disabled:
            self.disabled = wx.Bitmap(disabled)


    def ChangeButtonImages(self, normal=None, pressed=None, disabled=None):
        if normal:
            self.normal = wx.Bitmap(normal)
        if pressed:
            self.pressed = wx.Bitmap(pressed)
        else:
            self.pressed = None
        if disabled:
            self.disabled = wx.Bitmap(disabled)
        else:
            self.disabled = None
        #self.SetSize(self.DoGetBestSize())
        self.GetParent().Refresh(False, self.GetRect())

    def DoGetBestSize(self):
        return self.normal.GetSize()

    def Enable(self, *args, **kwargs):
        super(ShapedButton, self).Enable(*args, **kwargs)
        self.Refresh()

    def Disable(self, *args, **kwargs):
        super(ShapedButton, self).Disable(*args, **kwargs)
        self.Refresh()

    def post_event(self):
        event = wx.CommandEvent()
        event.SetEventObject(self)
        event.SetEventType(wx.EVT_BUTTON.typeId)
        wx.PostEvent(self, event)

    def on_size(self, event):
        event.Skip()
        self.Refresh()
        #self.PaintNow()

    def on_paint(self, event):
        #print "Painting button"

        bdc = wx.PaintDC(self)
        #event.Skip()
        dc = wx.GCDC(bdc)
        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetBackground(wx.TRANSPARENT_BRUSH)
        dc.Clear()
        bitmap = self.normal
        if self.clicked:
            bitmap = self.pressed or bitmap
        if not self.IsEnabled():
            bitmap = self.disabled or bitmap
        dc.DrawBitmap(bitmap, 0, 0, True)

        #event.Skip()

    def set_clicked(self, clicked):
        if clicked != self._clicked:
            self._clicked = clicked
            if self.pressed is not None:  #Dont redraw if there is no onPressed images
                self.SetFocus()
                self.Refresh()#
                #self.GetParent().Refresh(False, self.GetRect())

    def get_clicked(self):
        return self._clicked

    clicked = property(get_clicked, set_clicked)

    def on_left_down(self, event):
        x, y = event.GetPosition()
        if self.region.Contains(x, y):
            self.clicked = True

    def on_left_dclick(self, event):
        self.on_left_down(event)

    def on_left_up(self, event):
        if self.clicked:
            x, y = event.GetPosition()
            if self.region.Contains(x, y):
                self.post_event()
        self.clicked = False

    def on_motion(self, event):
        if self.clicked:
            x, y = event.GetPosition()
            if not self.region.Contains(x, y):
                self.clicked = False

    def on_leave_window(self, event):
        self.clicked = False


class TransparentText(GenStaticText):
  def __init__(self, *args, **kwargs):
    super(TransparentText,self).__init__(*args,**kwargs)
    self.SetWindowStyle(self.GetWindowStyle()|wx.TRANSPARENT_WINDOW|wx.NO_BORDER)
    self.SetBackgroundStyle(wx.BG_STYLE_PAINT)
    self.Bind(wx.EVT_PAINT, self.on_paint)
    self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)
    self.Bind(wx.EVT_SIZE, self.on_size)

  def Wrap(self, code):
    pass

  def on_paint(self, event):
    bdc = wx.PaintDC(self)
    #print "painting", self.GetLabel()
    dc = wx.GCDC(bdc)
    _gc = dc.GetGraphicsContext()
    dc.SetBackgroundMode(wx.TRANSPARENT)
    dc.SetBackground(wx.TRANSPARENT_BRUSH)
    _gc.SetAntialiasMode(wx.ANTIALIAS_DEFAULT)


    rect = self.GetUpdateRegion().GetBox()
    dc.SetClippingRect(rect)
    dc.Clear()
    #self.DoEraseBackground(dc)

    font_face = self.GetFont()
    font_color = self.GetForegroundColour()

    dc.SetFont(font_face)
    dc.SetTextForeground(font_color)

    dc.DrawText(self.GetLabel(), 0, 0)
    #event.Skip()


  def on_size(self, event):
    self.Refresh()
    event.Skip()

  def UpdateLabel(self, txt=None):
    self.SetLabelText(txt)
    self.GetParent().Refresh(False, self.GetRect())
    #self.InvalidateBestSize()
    #self.Refresh()


class FancyTabsPanel(wx.Panel):
    def __init__(self, tab_items, underlap=10, *args, **kwargs):
        super(FancyTabsPanel, self).__init__(*args, **kwargs)
        self.SetWindowStyle(self.GetWindowStyle() | wx.TRANSPARENT_WINDOW | wx.NO_BORDER)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda event: None)
        self.Bind(wx.EVT_SIZE, self.on_size)

        self.tab_items = []
        self.tab_item_objects = []
        self.tab_panels = []
        self.tab_selected = 3
        self.underlap_length = underlap

        self.tabtop = None
        self.inactive_img = None
        self.inactive_height = 0
        self.active_img = None
        self.active_height = 0

        for item in tab_items:
            self.addTab(item[0], item[1])

    def addTab(self, item_name, panel):
        self.tab_items.append(item_name)
        self.tab_panels.append(panel)

    def __getOverlap(self, index):
        return self.underlap_length * index

    def __getButtonPos(self, index):
        return self.inactive_height * index

    def __paintImages(self,dc, selected):
        for index in reversed(range(len(self.tab_items))):
            if index == selected: continue
            pos = self.__getButtonPos(index)
            dc.DrawBitmap(self.inactive_img, 16, pos)  # 15

    def setBackgrounds(self, active, inactive, tabtop):
        self.active_img = wx.Bitmap(active)
        self.active_height = self.active_img.GetHeight()
        self.inactive_img = wx.Bitmap(inactive)
        self.inactive_height = self.inactive_img.GetHeight() - self.underlap_length
        self.tabtop = wx.Bitmap(tabtop)

    def selectIndex(self, index):
        old_item = self.tab_panels[self.tab_selected]
        old_item.Hide()
        self.tab_selected=index
        new_item = self.tabs_panel[index]
        new_item.Hide()
        self.Refresh() #MAYBE SELF.LAYOUT() ?

    def on_size(self, event):
        self.Refresh()
        event.Skip()

    def on_paint(self, event):
        #print "paining fancytabs"
        bdc = wx.PaintDC(self)
        dc = wx.GCDC(bdc)

        #Paint inactive buttons
        self.__paintImages(dc, self.tab_selected)

        #Paint the highlighted button
        dc.DrawBitmap(self.active_img, 14,self.__getButtonPos(self.tab_selected) - 9)  #13

        #Then draw at the top the bottom of the presence bar
        dc.DrawBitmap(self.tabtop, 15,0)
