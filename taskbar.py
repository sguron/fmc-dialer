import wx

TRAY_TOOLTIP = 'FreeMyCall Dialer'

__author__ = 'TheArchitect'


def create_menu_item(menu, label, func):
    item = wx.MenuItem(menu, -1, label)
    menu.Bind(wx.EVT_MENU, func, id=item.GetId())
    menu.AppendItem(item)
    return item


class TaskBarIcon(wx.TaskBarIcon):
    def __init__(self, wxapp):
        super(TaskBarIcon, self).__init__()
        self.wxapp = wxapp
        self.set_icon("images/icons/16x16wn.png")
        self.Bind(wx.EVT_TASKBAR_LEFT_DCLICK, self.on_left_down)

    def CreatePopupMenu(self):
        menu = wx.Menu()
        create_menu_item(menu, u'Open', self.on_open)
        if self.wxapp.user.loggedin:
            menu.AppendSeparator()
            create_menu_item(menu, u'Call phone', self.on_callphone)
            create_menu_item(menu, u'Recent calls', self.on_recentcalls)
            create_menu_item(menu, u'Settings', self.on_settings)
            create_menu_item(menu, u'Logout', self.on_logout)
        menu.AppendSeparator()
        if self.wxapp.any_window_shown():
            create_menu_item(menu, u'Hide', self.on_hide)
        create_menu_item(menu, u'Check update', self.on_check_update)
        create_menu_item(menu, u'Exit', self.on_exit)
        return menu

    def set_icon(self, path):
        icon = wx.IconFromBitmap(wx.Bitmap(path))
        self.SetIcon(icon, TRAY_TOOLTIP)

    def on_left_down(self, event):
        self.on_open(event)

    def on_open(self, event):
        self.wxapp.TaskbarOpen()

    def on_callphone(self, event):
        self.wxapp.TaskbarCallphone()

    def on_recentcalls(self, event):
        self.wxapp.TaskbarRecentcalls()

    def on_settings(self, event):
        self.wxapp.TaskbarSettings()

    def on_logout(self, event):
        self.wxapp.TaskbarLogout()

    def on_hide(self, event):
        self.wxapp.TaskbarHideapp()

    def on_check_update(self, event):
        self.wxapp.TaskbarCheckupdate()

    def on_exit(self, event):
        self.wxapp.ExitApp()
        #wx.CallAfter(self.Destroy)
