"""
This is a heavily modified version of ImageNotebook example from wxPython.
It now supports transparency and various fixes to make this work with the dialer


License And Version
===================

:class:`LabelBook` and :class:`FlatImageBook` are distributed under the wxPython license.

Latest Revision: Andrea Gavana @ 22 Jan 2013, 21.00 GMT

Version 0.6.

"""

__docformat__ = "epytext"
__version__ = "0.6"


#----------------------------------------------------------------------
# Beginning Of IMAGENOTEBOOK wxPython Code
#----------------------------------------------------------------------

import wx

from wx.lib.agw.artmanager import ArtManager, DCSaver
from wx.lib.agw.fmresources import *

# Check for the new method in 2.7 (not present in 2.6.3.3)
if wx.VERSION_STRING < "2.7":
    wx.Rect.Contains = lambda self, point: wx.Rect.Inside(self, point)

# FlatImageBook and LabelBook styles
INB_BOTTOM = 1
""" Place labels below the page area. Available only for :class:`FlatImageBook`."""
INB_LEFT = 2
""" Place labels on the left side. Available only for :class:`FlatImageBook`."""
INB_RIGHT = 4
""" Place labels on the right side. """
INB_TOP = 8
""" Place labels above the page area. """
INB_BORDER = 16
""" Draws a border around :class:`LabelBook` or :class:`FlatImageBook`. """
INB_SHOW_ONLY_TEXT = 32
""" Shows only text labels and no images. Available only for :class:`LabelBook`."""
INB_SHOW_ONLY_IMAGES = 64
""" Shows only tab images and no label texts. Available only for :class:`LabelBook`."""
INB_FIT_BUTTON = 128
""" Displays a pin button to show/hide the book control. """
INB_DRAW_SHADOW = 256
""" Draw shadows below the book tabs. Available only for :class:`LabelBook`."""
INB_USE_PIN_BUTTON = 512
""" Displays a pin button to show/hide the book control. """
INB_GRADIENT_BACKGROUND = 1024
""" Draws a gradient shading on the tabs background. Available only for :class:`LabelBook`."""
INB_WEB_HILITE = 2048
""" On mouse hovering, tabs behave like html hyperlinks. Available only for :class:`LabelBook`."""
INB_NO_RESIZE = 4096
""" Don't allow resizing of the tab area. """
INB_FIT_LABELTEXT = 8192
""" Will fit the tab area to the longest text (or text+image if you have images) in all the tabs. """
INB_BOLD_TAB_SELECTION = 16384
""" Show the selected tab text using a bold font. """

wxEVT_IMAGENOTEBOOK_PAGE_CHANGED = wx.wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGED
wxEVT_IMAGENOTEBOOK_PAGE_CHANGING = wx.wxEVT_COMMAND_NOTEBOOK_PAGE_CHANGING
wxEVT_IMAGENOTEBOOK_PAGE_CLOSING = wx.NewEventType()
wxEVT_IMAGENOTEBOOK_PAGE_CLOSED = wx.NewEventType()

#-----------------------------------#
#        ImageNotebookEvent
#-----------------------------------#

EVT_IMAGENOTEBOOK_PAGE_CHANGED = wx.EVT_NOTEBOOK_PAGE_CHANGED
""" Notify client objects when the active page in :class:`FlatImageBook` or :class:`LabelBook` has changed. """
EVT_IMAGENOTEBOOK_PAGE_CHANGING = wx.EVT_NOTEBOOK_PAGE_CHANGING
""" Notify client objects when the active page in :class:`FlatImageBook` or :class:`LabelBook` is about to change. """
EVT_IMAGENOTEBOOK_PAGE_CLOSING = wx.PyEventBinder(wxEVT_IMAGENOTEBOOK_PAGE_CLOSING, 1)
""" Notify client objects when a page in :class:`FlatImageBook` or :class:`LabelBook` is closing. """
EVT_IMAGENOTEBOOK_PAGE_CLOSED = wx.PyEventBinder(wxEVT_IMAGENOTEBOOK_PAGE_CLOSED, 1)
""" Notify client objects when a page in :class:`FlatImageBook` or :class:`LabelBook` has been closed. """


# ---------------------------------------------------------------------------- #
# Class ImageNotebookEvent
# ---------------------------------------------------------------------------- #

class ImageNotebookEvent(wx.PyCommandEvent):
    """
    This events will be sent when a ``EVT_IMAGENOTEBOOK_PAGE_CHANGED``,
    ``EVT_IMAGENOTEBOOK_PAGE_CHANGING``, ``EVT_IMAGENOTEBOOK_PAGE_CLOSING``,
    ``EVT_IMAGENOTEBOOK_PAGE_CLOSED`` is mapped in the parent.
    """

    def __init__(self, eventType, eventId=1, sel=-1, oldsel=-1):
        """
        Default class constructor.

        :param `eventType`: the event type;
        :param `eventId`: the event identifier;
        :param `sel`: the current selection;
        :param `oldsel`: the old selection.
        """

        wx.PyCommandEvent.__init__(self, eventType, eventId)
        self._eventType = eventType
        self._sel = sel
        self._oldsel = oldsel
        self._allowed = True


    def SetSelection(self, s):
        """
        Sets the event selection.

        :param `s`: an integer specifying the new selection.
        """

        self._sel = s


    def SetOldSelection(self, s):
        """
        Sets the event old selection.

        :param `s`: an integer specifying the old selection.
        """

        self._oldsel = s


    def GetSelection(self):
        """ Returns the event selection. """

        return self._sel


    def GetOldSelection(self):
        """ Returns the old event selection. """

        return self._oldsel


    def Veto(self):
        """
        Prevents the change announced by this event from happening.

        :note: It is in general a good idea to notify the user about the reasons
         for vetoing the change because otherwise the applications behaviour (which
         just refuses to do what the user wants) might be quite surprising.
        """

        self._allowed = False


    def Allow(self):
        """
        This is the opposite of :meth:`~ImageNotebookEvent.Veto`: it explicitly allows the event to be processed.
        For most events it is not necessary to call this method as the events are
        allowed anyhow but some are forbidden by default (this will be mentioned
        in the corresponding event description).
        """

        self._allowed = True


    def IsAllowed(self):
        """
        Returns ``True`` if the change is allowed (:meth:`~ImageNotebookEvent.Veto` hasn't been called) or
        ``False`` otherwise (if it was).
        """

        return self._allowed


# ---------------------------------------------------------------------------- #
# Class ImageInfo
# ---------------------------------------------------------------------------- #

class ImageInfo(object):
    """
    This class holds all the information (caption, image, etc...) belonging to a
    single tab in :class:`LabelBook`.
    """
    def __init__(self, strCaption="", imageIndex=-1, enabled=True):
        """
        Default class constructor.

        :param `strCaption`: the tab caption;
        :param `imageIndex`: the tab image index based on the assigned (set)
         :class:`ImageList` (if any);
        :param `enabled`: sets the tab as enabled or disabled.
        """

        self._pos = wx.Point()
        self._size = wx.Size()
        self._strCaption = strCaption
        self._ImageIndex = imageIndex
        self._captionRect = wx.Rect()
        self._bEnabled = enabled


    def SetCaption(self, value):
        """
        Sets the tab caption.

        :param `value`: the new tab caption.
        """

        self._strCaption = value


    def GetCaption(self):
        """ Returns the tab caption. """

        return self._strCaption


    def SetPosition(self, value):
        """
        Sets the tab position.

        :param `value`: the new tab position, an instance of :class:`Point`.
        """

        self._pos = value


    def GetPosition(self):
        """ Returns the tab position. """

        return self._pos


    def SetSize(self, value):
        """
        Sets the tab size.

        :param `value`:  the new tab size, an instance of :class:`Size`.
        """

        self._size = value


    def GetSize(self):
        """ Returns the tab size. """

        return self._size


    def SetImageIndex(self, value):
        """
        Sets the tab image index.

        :param `value`: an index into the image list..
        """

        self._ImageIndex = value


    def GetImageIndex(self):
        """ Returns the tab image index. """

        return self._ImageIndex


    def SetTextRect(self, rect):
        """
        Sets the client rectangle available for the tab text.

        :param `rect`: the tab text client rectangle, an instance of :class:`Rect`.
        """

        self._captionRect = rect


    def GetTextRect(self):
        """ Returns the client rectangle available for the tab text. """

        return self._captionRect


    def GetEnabled(self):
        """ Returns whether the tab is enabled or not. """

        return self._bEnabled


    def EnableTab(self, enabled):
        """
        Sets the tab enabled or disabled.

        :param `enabled`: ``True`` to enable a tab, ``False`` to disable it.
        """

        self._bEnabled = enabled


# ---------------------------------------------------------------------------- #
# Class ImageContainerBase
# ---------------------------------------------------------------------------- #

class ImageContainerBase(wx.Panel):
    """
    Base class for :class:`FlatImageBook` image container.
    """
    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0, agwStyle=0, name="ImageContainerBase"):
        """
        Default class constructor.

        :param `parent`: parent window. Must not be ``None``;
        :param `id`: window identifier. A value of -1 indicates a default value;
        :param `pos`: the control position. A value of (-1, -1) indicates a default position,
         chosen by either the windowing system or wxPython, depending on platform;
        :param `size`: the control size. A value of (-1, -1) indicates a default size,
         chosen by either the windowing system or wxPython, depending on platform;
        :param `style`: the underlying :class:`Panel` window style;
        :param `agwStyle`: the AGW-specific window style. This can be a combination of the
         following bits:

         =========================== =========== ==================================================
         Window Styles               Hex Value   Description
         =========================== =========== ==================================================
         ``INB_BOTTOM``                      0x1 Place labels below the page area. Available only for :class:`FlatImageBook`.
         ``INB_LEFT``                        0x2 Place labels on the left side. Available only for :class:`FlatImageBook`.
         ``INB_RIGHT``                       0x4 Place labels on the right side.
         ``INB_TOP``                         0x8 Place labels above the page area.
         ``INB_BORDER``                     0x10 Draws a border around :class:`LabelBook` or :class:`FlatImageBook`.
         ``INB_SHOW_ONLY_TEXT``             0x20 Shows only text labels and no images. Available only for :class:`LabelBook`.
         ``INB_SHOW_ONLY_IMAGES``           0x40 Shows only tab images and no label texts. Available only for :class:`LabelBook`.
         ``INB_FIT_BUTTON``                 0x80 Displays a pin button to show/hide the book control.
         ``INB_DRAW_SHADOW``               0x100 Draw shadows below the book tabs. Available only for :class:`LabelBook`.
         ``INB_USE_PIN_BUTTON``            0x200 Displays a pin button to show/hide the book control.
         ``INB_GRADIENT_BACKGROUND``       0x400 Draws a gradient shading on the tabs background. Available only for :class:`LabelBook`.
         ``INB_WEB_HILITE``                0x800 On mouse hovering, tabs behave like html hyperlinks. Available only for :class:`LabelBook`.
         ``INB_NO_RESIZE``                0x1000 Don't allow resizing of the tab area.
         ``INB_FIT_LABELTEXT``            0x2000 Will fit the tab area to the longest text (or text+image if you have images) in all the tabs.
         ``INB_BOLD_TAB_SELECTION``       0x4000 Show the selected tab text using a bold font.
         =========================== =========== ==================================================

        :param `name`: the window name.
        """

        self._nIndex = -1
        self._nImgSize = 16
        self._ImageList = None
        self._nHoveredImgIdx = -1
        self._nLastHoveredImgIdx = -1
        self._bCollapsed = False
        self._tabAreaSize = (-1, -1)
        self._nPinButtonStatus = INB_PIN_NONE
        self._pagesInfoVec = []
        self._pinBtnRect = wx.Rect()

        self.active_font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)
        self.inactive_font = wx.SystemSettings_GetFont(wx.SYS_DEFAULT_GUI_FONT)

        self.active_tab_bitmap = wx.NullBitmap
        self.inactive_tab_bitmap = wx.NullBitmap
        self.foreground = None
        self.illst = []


        self.inactive_color = wx.Colour(0,255,0)
        self.active_color = wx.Colour(255,0,0)
        self.hand_cursor_active = False

        self.overlap = 10

        wx.Panel.__init__(self, parent, id, pos, size, style | wx.NO_BORDER |wx.TRANSPARENT_WINDOW, name)


    def HasAGWFlag(self, flag):
        """
        Tests for existance of flag in the style.

        :param `flag`: a window style. This can be a combination of the following bits:

         =========================== =========== ==================================================
         Window Styles               Hex Value   Description
         =========================== =========== ==================================================
         ``INB_BOTTOM``                      0x1 Place labels below the page area. Available only for :class:`FlatImageBook`.
         ``INB_LEFT``                        0x2 Place labels on the left side. Available only for :class:`FlatImageBook`.
         ``INB_RIGHT``                       0x4 Place labels on the right side.
         ``INB_TOP``                         0x8 Place labels above the page area.
         ``INB_BORDER``                     0x10 Draws a border around :class:`LabelBook` or :class:`FlatImageBook`.
         ``INB_SHOW_ONLY_TEXT``             0x20 Shows only text labels and no images. Available only for :class:`LabelBook`.
         ``INB_SHOW_ONLY_IMAGES``           0x40 Shows only tab images and no label texts. Available only for :class:`LabelBook`.
         ``INB_FIT_BUTTON``                 0x80 Displays a pin button to show/hide the book control.
         ``INB_DRAW_SHADOW``               0x100 Draw shadows below the book tabs. Available only for :class:`LabelBook`.
         ``INB_USE_PIN_BUTTON``            0x200 Displays a pin button to show/hide the book control.
         ``INB_GRADIENT_BACKGROUND``       0x400 Draws a gradient shading on the tabs background. Available only for :class:`LabelBook`.
         ``INB_WEB_HILITE``                0x800 On mouse hovering, tabs behave like html hyperlinks. Available only for :class:`LabelBook`.
         ``INB_NO_RESIZE``                0x1000 Don't allow resizing of the tab area.
         ``INB_FIT_LABELTEXT``            0x2000 Will fit the tab area to the longest text (or text+image if you have images) in all the tabs.
         ``INB_BOLD_TAB_SELECTION``       0x4000 Show the selected tab text using a bold font.
         =========================== =========== ==================================================
        """

        style = self.GetParent().GetAGWWindowStyleFlag()
        res = (style & flag and [True] or [False])[0]
        return res


    def ClearFlag(self, flag):
        """
        Removes flag from the style.

        :param `flag`: a window style flag.

        :see: :meth:`~ImageContainerBase.HasAGWFlag` for a list of possible window style flags.
        """

        parent = self.GetParent()
        agwStyle = parent.GetAGWWindowStyleFlag()
        agwStyle &= ~(flag)
        parent.SetAGWWindowStyleFlag(agwStyle)

    def AssignImages(self, active, inactive):
        self.active_tab_bitmap = wx.Bitmap(active)
        self.inactive_tab_bitmap = wx.Bitmap(inactive)

        self._nImgSize = max(self.active_tab_bitmap.GetHeight(), self.inactive_tab_bitmap.GetHeight() )

    def GetActiveSize(self):
        return self.active_tab_bitmap.GetSize()

    def GetInactiveSize(self):
        return self.inactive_tab_bitmap.GetSize()

    def AssignFont(self, active, inactive):
        self.active_font = active
        self.inactive_font = inactive

    def AssignColor(self, active, inactive):
        self.active_color = active
        self.inactive_color = inactive

    def AssignForeground(self, fg):
        self.foreground = wx.Bitmap(fg)

    def AssignIllst(self, image, pos):
        self.illst.append( (wx.Bitmap(image), pos) )

    def GetImageSize(self):
        """ Returns the image size inside the :class:`ImageContainerBase` image list. """

        return self._nImgSize


    def FixTextSize(self, dc, text, maxWidth):
        """
        Fixes the text, to fit `maxWidth` value. If the text length exceeds
        `maxWidth` value this function truncates it and appends two dots at
        the end. ("Long Long Long Text" might become "Long Long...").

        :param `dc`: an instance of :class:`DC`;
        :param `text`: the text to fix/truncate;
        :param `maxWidth`: the maximum allowed width for the text, in pixels.
        """

        return ArtManager.Get().TruncateText(dc, text, maxWidth)


    def CanDoBottomStyle(self):
        """
        Allows the parent to examine the children type. Some implementation
        (such as :class:`LabelBook`), does not support top/bottom images, only left/right.
        """

        return False


    def AddPage(self, caption, selected=False, imgIdx=-1):
        """
        Adds a page to the container.

        :param `caption`: specifies the text for the new tab;
        :param `selected`: specifies whether the page should be selected;
        :param `imgIdx`: specifies the optional image index for the new tab.
        """

        self._pagesInfoVec.append(ImageInfo(caption, imgIdx))
        if selected or len(self._pagesInfoVec) == 1:
            self._nIndex = len(self._pagesInfoVec)-1

        self.Refresh()


    def InsertPage(self, page_idx, caption, selected=False, imgIdx=-1):
        """
        Inserts a page into the container at the specified position.

        :param `page_idx`: specifies the position for the new tab;
        :param `caption`: specifies the text for the new tab;
        :param `selected`: specifies whether the page should be selected;
        :param `imgIdx`: specifies the optional image index for the new tab.
        """

        self._pagesInfoVec.insert(page_idx, ImageInfo(caption, imgIdx))
        if selected or len(self._pagesInfoVec) == 1:
            self._nIndex = len(self._pagesInfoVec)-1

        self.Refresh()


    def SetPageText(self, page, text):
        """
        Sets the tab caption for the given page.

        :param `page`: the index of the tab;
        :param `text`: the new tab caption.
        """

        imgInfo = self._pagesInfoVec[page]
        imgInfo.SetCaption(text)


    def GetPageImage(self, page):
        """
        Returns the image index for the given page.

        :param `page`: the index of the tab.
        """

        imgInfo = self._pagesInfoVec[page]
        return imgInfo.GetImageIndex()


    def GetPageText(self, page):
        """
        Returns the tab caption for the given page.

        :param `page`: the index of the tab.
        """

        imgInfo = self._pagesInfoVec[page]
        return imgInfo.GetCaption()


    def GetEnabled(self, page):
        """
        Returns whether a tab is enabled or not.

        :param `page`: an integer specifying the page index.
        """

        if page >= len(self._pagesInfoVec):
            return True # Adding a page - enabled by default

        imgInfo = self._pagesInfoVec[page]
        return imgInfo.GetEnabled()


    def EnableTab(self, page, enabled=True):
        """
        Enables or disables a tab.

        :param `page`: an integer specifying the page index;
        :param `enabled`: ``True`` to enable a tab, ``False`` to disable it.
        """

        if page >= len(self._pagesInfoVec):
            return

        imgInfo = self._pagesInfoVec[page]
        imgInfo.EnableTab(enabled)


    def ClearAll(self):
        """ Deletes all the pages in the container. """

        self._pagesInfoVec = []
        self._nIndex = wx.NOT_FOUND


    def DoDeletePage(self, page):
        """
        Does the actual page deletion.

        :param `page`: the index of the tab.
        """

        # Remove the page from the vector
        book = self.GetParent()
        self._pagesInfoVec.pop(page)

        if self._nIndex >= page:
            self._nIndex = self._nIndex - 1

        # The delete page was the last first on the array,
        # but the book still has more pages, so we set the
        # active page to be the first one (0)
        if self._nIndex < 0 and len(self._pagesInfoVec) > 0:
            self._nIndex = 0

        # Refresh the tabs
        if self._nIndex >= 0:

            book._bForceSelection = True
            book.SetSelection(self._nIndex)
            book._bForceSelection = False

        if not self._pagesInfoVec:
            # Erase the page container drawings
            dc = wx.ClientDC(self)
            dc.Clear()


    def OnSize(self, event):
        """
        Handles the ``wx.EVT_SIZE`` event for :class:`ImageContainerBase`.

        :param `event`: a :class:`SizeEvent` event to be processed.
        """

        self.Refresh() # Call on paint
        event.Skip()


    def OnEraseBackground(self, event):
        """
        Handles the ``wx.EVT_ERASE_BACKGROUND`` event for :class:`ImageContainerBase`.

        :param `event`: a :class:`EraseEvent` event to be processed.

        :note: This method is intentionally empty to reduce flicker.
        """

        pass


    def HitTest(self, pt):
        """
        Returns the index of the tab at the specified position or ``wx.NOT_FOUND``
        if ``None``, plus the flag style of :meth:`~ImageContainerBase.HitTest`.

        :param `pt`: an instance of :class:`Point`, to test for hits.

        :return: The index of the tab at the specified position plus the hit test
         flag, which can be one of the following bits:

         ====================== ======= ================================
         HitTest Flags           Value  Description
         ====================== ======= ================================
         ``IMG_OVER_IMG``             0 The mouse is over the tab icon
         ``IMG_OVER_PIN``             1 The mouse is over the pin button
         ``IMG_OVER_EW_BORDER``       2 The mouse is over the east-west book border
         ``IMG_NONE``                 3 Nowhere
         ====================== ======= ================================

        """

        style = self.GetParent().GetAGWWindowStyleFlag()

        for i in reversed( xrange(len(self._pagesInfoVec)) ) :

            if self._pagesInfoVec[i].GetPosition() == wx.Point(-1, -1):
                break

            # For Web Hover style, we test the TextRect
            if not self.HasAGWFlag(INB_WEB_HILITE):
                buttonRect = wx.RectPS(self._pagesInfoVec[i].GetPosition(), self._pagesInfoVec[i].GetSize())
            else:
                buttonRect = self._pagesInfoVec[i].GetTextRect()

            if buttonRect.Contains(pt):
                return i, IMG_OVER_IMG

        return -1, IMG_NONE

    def OnMouseLeftDown(self, event):
        """
        Handles the ``wx.EVT_LEFT_DOWN`` event for :class:`ImageContainerBase`.

        :param `event`: a :class:`MouseEvent` event to be processed.
        """

        newSelection = -1
        event.Skip()

        # Support for collapse/expand
        style = self.GetParent().GetAGWWindowStyleFlag()

        tabIdx, where = self.HitTest(event.GetPosition())

        if where == IMG_OVER_IMG:
            self._nHoveredImgIdx = -1

        if tabIdx == -1:
            return

        self.GetParent().SetSelection(tabIdx)


    def OnMouseLeaveWindow(self, event):
        """
        Handles the ``wx.EVT_LEAVE_WINDOW`` event for :class:`ImageContainerBase`.

        :param `event`: a :class:`MouseEvent` event to be processed.
        """

        bRepaint = self._nHoveredImgIdx != -1
        self._nHoveredImgIdx = -1

        # Make sure the pin button status is NONE
        # incase we were in pin button style
        style = self.GetParent().GetAGWWindowStyleFlag()

        # Restore cursor
        wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))

        #if bRepaint:
        #    self.Refresh()


    def OnMouseLeftUp(self, event):
        """
        Handles the ``wx.EVT_LEFT_UP`` event for :class:`ImageContainerBase`.

        :param `event`: a :class:`MouseEvent` event to be processed.
        """

        style = self.GetParent().GetAGWWindowStyleFlag()

        if style & INB_USE_PIN_BUTTON:

            bIsLabelContainer = not self.CanDoBottomStyle()

            if self._pinBtnRect.Contains(event.GetPosition()):

                self._nPinButtonStatus = INB_PIN_NONE
                self._bCollapsed = not self._bCollapsed

                if self._bCollapsed:

                    # Save the current tab area width
                    self._tabAreaSize = self.GetSize()

                    if bIsLabelContainer:

                        self.SetSizeHints(20, self._tabAreaSize.y)

                    else:

                        if style & INB_BOTTOM or style & INB_TOP:
                            self.SetSizeHints(self._tabAreaSize.x, 20)
                        else:
                            self.SetSizeHints(20, self._tabAreaSize.y)

                else:

                    if bIsLabelContainer:

                        self.SetSizeHints(self._tabAreaSize.x, -1)

                    else:

                        # Restore the tab area size
                        if style & INB_BOTTOM or style & INB_TOP:
                            self.SetSizeHints(-1, self._tabAreaSize.y)
                        else:
                            self.SetSizeHints(self._tabAreaSize.x, -1)

                self.GetParent().GetSizer().Layout()
                self.Refresh()
                return


    def OnMouseMove(self, event):
        """
        Handles the ``wx.EVT_MOTION`` event for :class:`ImageContainerBase`.

        :param `event`: a :class:`MouseEvent` event to be processed.
        """

        style = self.GetParent().GetAGWWindowStyleFlag()
        #print "Mouse move at", event.GetPosition().Get()
        imgIdx, where = self.HitTest(event.GetPosition())
        #print "imgIdx=", imgIdx, "where=", where


        # Allow hovering unless over current tab or tab is disabled
        self._nHoveredImgIdx = -1

        if imgIdx < len(self._pagesInfoVec) and self.GetEnabled(imgIdx) and imgIdx != self._nIndex:
            self._nHoveredImgIdx = imgIdx

        if self._nHoveredImgIdx >= 0 and self.HasAGWFlag(INB_WEB_HILITE):

            # Change the cursor to be Hand if we have the Web hover style set
            wx.SetCursor(wx.StockCursor(wx.CURSOR_HAND))

        #elif not self.PointOnSash(event.GetPosition()):
        #    # Restore the cursor if we are not currently hovering the sash
        #    wx.SetCursor(wx.StockCursor(wx.CURSOR_ARROW))



        #self.Refresh()



# ---------------------------------------------------------------------------- #
# Class ImageContainer
# ---------------------------------------------------------------------------- #

class ImageContainer(ImageContainerBase):
    """
    Base class for :class:`FlatImageBook` image container.
    """

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0, agwStyle=0, name="ImageContainer"):
        """
        Default class constructor.

        :param `parent`: parent window. Must not be ``None``;
        :param `id`: window identifier. A value of -1 indicates a default value;
        :param `pos`: the control position. A value of (-1, -1) indicates a default position,
         chosen by either the windowing system or wxPython, depending on platform;
        :param `size`: the control size. A value of (-1, -1) indicates a default size,
         chosen by either the windowing system or wxPython, depending on platform;
        :param `style`: the underlying :class:`Panel` window style;
        :param `agwStyle`: the AGW-specific window style. This can be a combination of the
         following bits:

         =========================== =========== ==================================================
         Window Styles               Hex Value   Description
         =========================== =========== ==================================================
         ``INB_BOTTOM``                      0x1 Place labels below the page area. Available only for :class:`FlatImageBook`.
         ``INB_LEFT``                        0x2 Place labels on the left side. Available only for :class:`FlatImageBook`.
         ``INB_RIGHT``                       0x4 Place labels on the right side.
         ``INB_TOP``                         0x8 Place labels above the page area.
         ``INB_BORDER``                     0x10 Draws a border around :class:`LabelBook` or :class:`FlatImageBook`.
         ``INB_SHOW_ONLY_TEXT``             0x20 Shows only text labels and no images. Available only for :class:`LabelBook`.
         ``INB_SHOW_ONLY_IMAGES``           0x40 Shows only tab images and no label texts. Available only for :class:`LabelBook`.
         ``INB_FIT_BUTTON``                 0x80 Displays a pin button to show/hide the book control.
         ``INB_DRAW_SHADOW``               0x100 Draw shadows below the book tabs. Available only for :class:`LabelBook`.
         ``INB_USE_PIN_BUTTON``            0x200 Displays a pin button to show/hide the book control.
         ``INB_GRADIENT_BACKGROUND``       0x400 Draws a gradient shading on the tabs background. Available only for :class:`LabelBook`.
         ``INB_WEB_HILITE``                0x800 On mouse hovering, tabs behave like html hyperlinks. Available only for :class:`LabelBook`.
         ``INB_NO_RESIZE``                0x1000 Don't allow resizing of the tab area.
         ``INB_FIT_LABELTEXT``            0x2000 Will fit the tab area to the longest text (or text+image if you have images) in all the tabs.
         ``INB_BOLD_TAB_SELECTION``       0x4000 Show the selected tab text using a bold font.
         =========================== =========== ==================================================

        :param `name`: the window name.
        """

        ImageContainerBase.__init__(self, parent, id, pos, size, style, agwStyle, name)

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_SIZE, self.OnSize)
        self.Bind(wx.EVT_LEFT_DOWN, self.OnMouseLeftDown)
        self.Bind(wx.EVT_LEFT_UP, self.OnMouseLeftUp)
        self.Bind(wx.EVT_ERASE_BACKGROUND, self.OnEraseBackground)
        self.Bind(wx.EVT_MOTION, self.OnMouseMove)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.OnMouseLeaveWindow)


    def OnSize(self, event):
        """
        Handles the ``wx.EVT_SIZE`` event for :class:`ImageContainer`.

        :param `event`: a :class:`SizeEvent` event to be processed.
        """

        ImageContainerBase.OnSize(self, event)
        event.Skip()


    def OnMouseLeftDown(self, event):
        """
        Handles the ``wx.EVT_LEFT_DOWN`` event for :class:`ImageContainer`.

        :param `event`: a :class:`MouseEvent` event to be processed.
        """

        ImageContainerBase.OnMouseLeftDown(self, event)
        event.Skip()


    def OnMouseLeftUp(self, event):
        """
        Handles the ``wx.EVT_LEFT_UP`` event for :class:`ImageContainer`.

        :param `event`: a :class:`MouseEvent` event to be processed.
        """

        ImageContainerBase.OnMouseLeftUp(self, event)
        event.Skip()


    def OnEraseBackground(self, event):
        """
        Handles the ``wx.EVT_ERASE_BACKGROUND`` event for :class:`ImageContainer`.

        :param `event`: a :class:`EraseEvent` event to be processed.
        """

        ImageContainerBase.OnEraseBackground(self, event)


    def OnMouseMove(self, event):
        """
        Handles the ``wx.EVT_MOTION`` event for :class:`ImageContainer`.

        :param `event`: a :class:`MouseEvent` event to be processed.
        """

        ImageContainerBase.OnMouseMove(self, event)
        event.Skip()


    def OnMouseLeaveWindow(self, event):
        """
        Handles the ``wx.EVT_LEAVE_WINDOW`` event for :class:`ImageContainer`.

        :param `event`: a :class:`MouseEvent` event to be processed.
        """

        ImageContainerBase.OnMouseLeaveWindow(self, event)
        event.Skip()


    def CanDoBottomStyle(self):
        """
        Allows the parent to examine the children type. Some implementation
        (such as :class:`LabelBook`), does not support top/bottom images, only left/right.
        """

        return True


    def OnPaint(self, event):
        """
        Handles the ``wx.EVT_PAINT`` event for :class:`ImageContainer`.

        :param `event`: a :class:`PaintEvent` event to be processed.
        """
        bdc = wx.PaintDC(self)
        dc = wx.GCDC(bdc)
        dc.SetBackgroundMode(wx.TRANSPARENT)
        dc.SetBackground(wx.TRANSPARENT_BRUSH)
        dc.Clear()
        #self.GetParent().RefreshRect(self.GetRect())
        style = self.GetParent().GetAGWWindowStyleFlag()

        size = self.GetSize()

        pos = 0

        nPadding = 17
        nTextPaddingLeft = 20

        count = 0

        #Draw buttons one by one

        for i in reversed(xrange(len(self._pagesInfoVec))):

            tab_img_size = self.GetInactiveSize()
            overlap = self.overlap

            if self._nIndex == i:
                active = True
                continue

            count = count + 1


            textWidth, textHeight = dc.GetTextExtent(self._pagesInfoVec[i].GetCaption())

            # Default values for the surronounding rectangle
            # around a button

            rectWidth = tab_img_size.GetWidth()  # To avoid the recangle to 'touch' the borders
            rectHeight = tab_img_size.GetHeight()

            xpos = self.GetSize().GetWidth() - rectWidth
            ypos = ( rectHeight - self.overlap ) * i

            # Calculate the button rectangle
            modRectWidth = rectWidth
            modRectHeight = rectHeight - self.overlap

            buttonRect = wx.Rect(xpos, ypos+self.overlap, modRectWidth, modRectHeight)

            if False: #self._nHoveredImgIdx == i:   #TODO: Will handle this at last

                # Set the colours
                penColour = wx.SystemSettings_GetColour(wx.SYS_COLOUR_ACTIVECAPTION)
                brushColour = ArtManager.Get().LightColour(wx.SystemSettings_GetColour(wx.SYS_COLOUR_ACTIVECAPTION), 90)

                dc.SetPen(wx.Pen(penColour))
                dc.SetBrush(wx.Brush(brushColour))

                # Fix the surrounding of the rect if border is set
                if style & INB_BORDER:

                    if style & INB_TOP or style & INB_BOTTOM:
                        buttonRect = wx.Rect(buttonRect.x + 1, buttonRect.y, buttonRect.width - 1, buttonRect.height)
                    else:
                        buttonRect = wx.Rect(buttonRect.x, buttonRect.y + 1, buttonRect.width, buttonRect.height - 1)

                dc.DrawRectangleRect(buttonRect)


            # Draw the caption and text

            dc.DrawBitmap(self.inactive_tab_bitmap, xpos , ypos)

            dc.SetFont(self.inactive_font)
            dc.SetTextForeground(self.inactive_color)
            dc.DrawText(self._pagesInfoVec[i].GetCaption(), xpos + nTextPaddingLeft, ypos+nPadding)

            # Update the page info
            self._pagesInfoVec[i].SetPosition(buttonRect.GetPosition())
            self._pagesInfoVec[i].SetSize(buttonRect.GetSize())


        #Now to draw the active button:
        inactivepos = ( self.inactive_tab_bitmap.GetHeight() - self.overlap ) * self._nIndex
        activepos = inactivepos - 9


        textWidth, textHeight = dc.GetTextExtent(self._pagesInfoVec[self._nIndex].GetCaption())

        # Default values for the surronounding rectangle
        # around a button

        rectWidth = self.active_tab_bitmap.GetWidth()  # To avoid the recangle to 'touch' the borders
        rectHeight = self.active_tab_bitmap.GetHeight()

        modRectWidth = rectWidth
        modRectHeight = rectHeight - 16

        buttonRect = wx.Rect(0, activepos+8, modRectWidth, modRectHeight)

        dc.DrawBitmap(self.active_tab_bitmap, 0 , activepos)

        dc.SetFont(self.active_font)
        dc.SetTextForeground(self.active_color)
        dc.DrawText(self._pagesInfoVec[self._nIndex].GetCaption(), nTextPaddingLeft-2, inactivepos+nPadding-3)

        for i in self.illst:
            dc.DrawBitmap(i[0], *i[1])

        #Draw the foreground at top
        if self.foreground is not None:
            dc.DrawBitmap(self.foreground, 0, 0)

        self._pagesInfoVec[self._nIndex].SetPosition(buttonRect.GetPosition())
        self._pagesInfoVec[self._nIndex].SetSize(buttonRect.GetSize())

        # Update all buttons that can not fit into the screen as non-visible
        #for ii in xrange(count, len(self._pagesInfoVec)):
        #    self._pagesInfoVec[ii].SetPosition(wx.Point(-1, -1))



# ---------------------------------------------------------------------------- #
# Class FlatBookBase
# ---------------------------------------------------------------------------- #

class FlatBookBase(wx.Panel):
    """ Base class for the containing window for :class:`LabelBook` and :class:`FlatImageBook`. """

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0, agwStyle=0, name="FlatBookBase"):
        """
        Default class constructor.

        :param `parent`: parent window. Must not be ``None``;
        :param `id`: window identifier. A value of -1 indicates a default value;
        :param `pos`: the control position. A value of (-1, -1) indicates a default position,
         chosen by either the windowing system or wxPython, depending on platform;
        :param `size`: the control size. A value of (-1, -1) indicates a default size,
         chosen by either the windowing system or wxPython, depending on platform;
        :param `style`: the underlying :class:`Panel` window style;
        :param `agwStyle`: the AGW-specific window style. This can be a combination of the
         following bits:

         =========================== =========== ==================================================
         Window Styles               Hex Value   Description
         =========================== =========== ==================================================
         ``INB_BOTTOM``                      0x1 Place labels below the page area. Available only for :class:`FlatImageBook`.
         ``INB_LEFT``                        0x2 Place labels on the left side. Available only for :class:`FlatImageBook`.
         ``INB_RIGHT``                       0x4 Place labels on the right side.
         ``INB_TOP``                         0x8 Place labels above the page area.
         ``INB_BORDER``                     0x10 Draws a border around :class:`LabelBook` or :class:`FlatImageBook`.
         ``INB_SHOW_ONLY_TEXT``             0x20 Shows only text labels and no images. Available only for :class:`LabelBook`.
         ``INB_SHOW_ONLY_IMAGES``           0x40 Shows only tab images and no label texts. Available only for :class:`LabelBook`.
         ``INB_FIT_BUTTON``                 0x80 Displays a pin button to show/hide the book control.
         ``INB_DRAW_SHADOW``               0x100 Draw shadows below the book tabs. Available only for :class:`LabelBook`.
         ``INB_USE_PIN_BUTTON``            0x200 Displays a pin button to show/hide the book control.
         ``INB_GRADIENT_BACKGROUND``       0x400 Draws a gradient shading on the tabs background. Available only for :class:`LabelBook`.
         ``INB_WEB_HILITE``                0x800 On mouse hovering, tabs behave like html hyperlinks. Available only for :class:`LabelBook`.
         ``INB_NO_RESIZE``                0x1000 Don't allow resizing of the tab area.
         ``INB_FIT_LABELTEXT``            0x2000 Will fit the tab area to the longest text (or text+image if you have images) in all the tabs.
         ``INB_BOLD_TAB_SELECTION``       0x4000 Show the selected tab text using a bold font.
         =========================== =========== ==================================================

        :param `name`: the window name.
        """

        self._pages = None
        self._bInitializing = True
        self._pages = None
        self._bForceSelection = False
        self._windows = []
        self._fontSizeMultiple = 1.0

        self._agwStyle = agwStyle

        wx.Panel.__init__(self, parent, id, pos, size, style, name)
        self.SetWindowStyle(self.GetWindowStyle()|wx.TRANSPARENT_WINDOW|wx.NO_BORDER)
        self._bInitializing = False

        self.Bind(wx.EVT_NAVIGATION_KEY, self.OnNavigationKey)
        self.Bind(wx.EVT_MOUSE_CAPTURE_LOST, lambda evt: True)

    def SetPagesPanel(self):
        self._mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self._mainSizer)

        # Add the tab container and the separator
        self._mainSizer.Add(self._pages, 0, wx.EXPAND)

        self._pages.SetSizeHints(self._pages._nImgSize , -1)

    def SetAGWWindowStyleFlag(self, agwStyle):
        print "Called", "SetAGWWindowStyleFlag"
        """
        Sets the window style.

        :param `agwStyle`: can be a combination of the following bits:

         =========================== =========== ==================================================
         Window Styles               Hex Value   Description
         =========================== =========== ==================================================
         ``INB_BOTTOM``                      0x1 Place labels below the page area. Available only for :class:`FlatImageBook`.
         ``INB_LEFT``                        0x2 Place labels on the left side. Available only for :class:`FlatImageBook`.
         ``INB_RIGHT``                       0x4 Place labels on the right side.
         ``INB_TOP``                         0x8 Place labels above the page area.
         ``INB_BORDER``                     0x10 Draws a border around :class:`LabelBook` or :class:`FlatImageBook`.
         ``INB_SHOW_ONLY_TEXT``             0x20 Shows only text labels and no images. Available only for :class:`LabelBook`.
         ``INB_SHOW_ONLY_IMAGES``           0x40 Shows only tab images and no label texts. Available only for :class:`LabelBook`.
         ``INB_FIT_BUTTON``                 0x80 Displays a pin button to show/hide the book control.
         ``INB_DRAW_SHADOW``               0x100 Draw shadows below the book tabs. Available only for :class:`LabelBook`.
         ``INB_USE_PIN_BUTTON``            0x200 Displays a pin button to show/hide the book control.
         ``INB_GRADIENT_BACKGROUND``       0x400 Draws a gradient shading on the tabs background. Available only for :class:`LabelBook`.
         ``INB_WEB_HILITE``                0x800 On mouse hovering, tabs behave like html hyperlinks. Available only for :class:`LabelBook`.
         ``INB_NO_RESIZE``                0x1000 Don't allow resizing of the tab area.
         ``INB_FIT_LABELTEXT``            0x2000 Will fit the tab area to the longest text (or text+image if you have images) in all the tabs.
         ``INB_BOLD_TAB_SELECTION``       0x4000 Show the selected tab text using a bold font.
         =========================== =========== ==================================================

        """

        self._agwStyle = agwStyle

        # Check that we are not in initialization process
        if self._bInitializing:
            return

        if not self._pages:
            return

        # Detach the windows attached to the sizer
        if self.GetSelection() >= 0:
            self._mainSizer.Detach(self._windows[self.GetSelection()])

        self._mainSizer.Detach(self._pages)

        if isinstance(self, LabelBook):
            self._mainSizer = wx.BoxSizer(wx.HORIZONTAL)
        else:
            if agwStyle & INB_LEFT or agwStyle & INB_RIGHT:
                self._mainSizer = wx.BoxSizer(wx.HORIZONTAL)
            else:
                self._mainSizer = wx.BoxSizer(wx.VERTICAL)

        self.SetSizer(self._mainSizer)

        # Add the tab container and the separator
        self._mainSizer.Add(self._pages, 0, wx.EXPAND)

        if isinstance(self, FlatImageBook):
            if agwStyle & INB_LEFT or agwStyle & INB_RIGHT:
                self._pages.SetSizeHints(self._pages._nImgSize * 2, -1)
            else:
                self._pages.SetSizeHints(-1, self._pages._nImgSize * 2)

        # Attach the windows back to the sizer to the sizer
        if self.GetSelection() >= 0:
            self.DoSetSelection(self._windows[self.GetSelection()])

        #if agwStyle & INB_FIT_LABELTEXT:
        #    self.ResizeTabArea()

        self._mainSizer.Layout()
        #dummy = wx.SizeEvent()
        #wx.PostEvent(self, dummy)
        self._pages.Refresh()


    def GetAGWWindowStyleFlag(self):
        """
        Returns the :class:`FlatBookBase` window style.

        :see: :meth:`~FlatBookBase.SetAGWWindowStyleFlag` for a list of possible window style flags.
        """

        return self._agwStyle


    def HasAGWFlag(self, flag):
        """
        Returns whether a flag is present in the :class:`FlatBookBase` style.

        :param `flag`: one of the possible :class:`FlatBookBase` window styles.

        :see: :meth:`~FlatBookBase.SetAGWWindowStyleFlag` for a list of possible window style flags.
        """

        agwStyle = self.GetAGWWindowStyleFlag()
        res = (agwStyle & flag and [True] or [False])[0]
        return res


    def AddPage(self, page, text, select=False, imageId=-1):
        """
        Adds a page to the book.

        :param `page`: specifies the new page;
        :param `text`: specifies the text for the new page;
        :param `select`: specifies whether the page should be selected;
        :param `imageId`: specifies the optional image index for the new page.

        :note: The call to this function generates the page changing events.
        """

        if not page:
            return

        page.Reparent(self)

        self._windows.append(page)

        if select or len(self._windows) == 1:
            self.SetSelection(len(self._windows)-1)
        else:
            page.Hide()

        self._pages.AddPage(text, select, imageId)
        #self.ResizeTabArea()
        self.Refresh()


    def InsertPage(self, page_idx, page, text, select=False, imageId=-1):
        """
        Inserts a page into the book at the specified position.

        :param `page_idx`: specifies the position for the new page;
        :param `page`: specifies the new page;
        :param `text`: specifies the text for the new page;
        :param `select`: specifies whether the page should be selected;
        :param `imageId`: specifies the optional image index for the new page.

        :note: The call to this function generates the page changing events.
        """

        if not page:
            return

        page.Reparent(self)

        self._windows.insert(page_idx, page)

        if select or len(self._windows) == 1:
            self.SetSelection(page_idx)
        else:
            page.Hide()

        self._pages.InsertPage(page_idx, text, select, imageId)
        #self.ResizeTabArea()
        self.Refresh()


    def DeletePage(self, page):
        """
        Deletes the specified page, and the associated window.

        :param `page`: an integer specifying the page to be deleted.

        :note: The call to this function generates the page changing events.
        """

        if page >= len(self._windows) or page < 0:
            return

        # Fire a closing event
        event = ImageNotebookEvent(wxEVT_IMAGENOTEBOOK_PAGE_CLOSING, self.GetId())
        event.SetSelection(page)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

        # The event handler allows it?
        if not event.IsAllowed():
            return False

        self.Freeze()

        # Delete the requested page
        pageRemoved = self._windows[page]

        # If the page is the current window, remove it from the sizer
        # as well
        if page == self.GetSelection():
            self._mainSizer.Detach(pageRemoved)


        # Remove it from the array as well
        self._windows.pop(page)

        # Now we can destroy it in wxWidgets use Destroy instead of delete
        pageRemoved.Destroy()
        self._mainSizer.Layout()

        self._pages.DoDeletePage(page)
        #self.ResizeTabArea()
        self.Thaw()

        # Fire a closed event
        closedEvent = ImageNotebookEvent(wxEVT_IMAGENOTEBOOK_PAGE_CLOSED, self.GetId())
        closedEvent.SetSelection(page)
        closedEvent.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(closedEvent)


    def RemovePage(self, page):
        """
        Deletes the specified page, without deleting the associated window.

        :param `page`: an integer specifying the page to be removed.

        :note: The call to this function generates the page changing events.
        """

        if page >= len(self._windows):
            return False

        # Fire a closing event
        event = ImageNotebookEvent(wxEVT_IMAGENOTEBOOK_PAGE_CLOSING, self.GetId())
        event.SetSelection(page)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

        # The event handler allows it?
        if not event.IsAllowed():
            return False

        self.Freeze()

        # Remove the requested page
        pageRemoved = self._windows[page]

        # If the page is the current window, remove it from the sizer
        # as well
        if page == self.GetSelection():
            self._mainSizer.Detach(pageRemoved)

        # Remove it from the array as well
        self._windows.pop(page)
        self._mainSizer.Layout()
        #self.ResizeTabArea()
        self.Thaw()

        self._pages.DoDeletePage(page)

        # Fire a closed event
        closedEvent = ImageNotebookEvent(wxEVT_IMAGENOTEBOOK_PAGE_CLOSED, self.GetId())
        closedEvent.SetSelection(page)
        closedEvent.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(closedEvent)

        return True


    def DeleteAllPages(self):
        """ Deletes all the pages in the book. """

        if not self._windows:
            return

        self.Freeze()

        for win in self._windows:
            win.Destroy()

        self._windows = []
        self.Thaw()

        # remove old selection
        self._pages.ClearAll()
        self._pages.Refresh()


    def SetSelection(self, page):
        """
        Changes the selection from currently visible/selected page to the page
        given by page.

        :param `page`: an integer specifying the page to be selected.

        :note: The call to this function generates the page changing events.
        """

        if page >= len(self._windows):
            return

        if not self.GetEnabled(page):
            return

        if page == self.GetSelection() and not self._bForceSelection:
            return

        oldSelection = self.GetSelection()

        # Generate an event that indicates that an image is about to be selected
        event = ImageNotebookEvent(wxEVT_IMAGENOTEBOOK_PAGE_CHANGING, self.GetId())
        event.SetSelection(page)
        event.SetOldSelection(oldSelection)
        event.SetEventObject(self)
        self.GetEventHandler().ProcessEvent(event)

        # The event handler allows it?
        if not event.IsAllowed() and not self._bForceSelection:
            return

        self.DoSetSelection(self._windows[page])
        # Now we can update the new selection
        self._pages._nIndex = page

        # Refresh calls the OnPaint of this class
        self._pages.Refresh()

        # Generate an event that indicates that an image was selected
        eventChanged = ImageNotebookEvent(wxEVT_IMAGENOTEBOOK_PAGE_CHANGED, self.GetId())
        eventChanged.SetEventObject(self)
        eventChanged.SetOldSelection(oldSelection)
        eventChanged.SetSelection(page)
        self.GetEventHandler().ProcessEvent(eventChanged)


    def AssignImages(self, active, inactive):
        self._pages.AssignImages(active, inactive)

    def AssignFont(self, active, inactive):
        self._pages.AssignFont(active, inactive)

    def AssignColor(self, active, inactive):
        self._pages.AssignColor(active, inactive)

    def AssignForeground(self, fg):
        self._pages.AssignForeground(fg)

    def AssignIllst(self, image, pos):
        self._pages.AssignIllst(image, pos)

    def GetSelection(self):
        """ Returns the current selection. """

        if self._pages:
            return self._pages._nIndex
        else:
            return -1


    def DoSetSelection(self, window):
        """
        Select the window by the provided pointer.

        :param `window`: an instance of :class:`Window`.
        """

        curSel = self.GetSelection()
        agwStyle = self.GetAGWWindowStyleFlag()


        # Replace the window in the sizer
        self.Freeze()

        # Check if a new selection was made
        bInsertFirst = (agwStyle & INB_BOTTOM or agwStyle & INB_RIGHT)

        if curSel >= 0:

            # Remove the window from the main sizer
            self._mainSizer.Detach(self._windows[curSel])
            self._windows[curSel].Hide()

        if bInsertFirst:
            self._mainSizer.Insert(0, window, 1, wx.EXPAND)
        else:
            self._mainSizer.Add(window, 1, wx.EXPAND)

        window.Show()
        self._mainSizer.Layout()
        self.Thaw()

    def GetPageCount(self):
        """ Returns the number of pages in the book. """

        return len(self._windows)


    def SetPageText(self, page, text):
        """
        Sets the text for the given page.

        :param `page`: an integer specifying the page index;
        :param `text`: the new tab label.
        """

        self._pages.SetPageText(page, text)
        self._pages.Refresh()


    def GetPageText(self, page):
        """
        Returns the text for the given page.

        :param `page`: an integer specifying the page index.
        """

        return self._pages.GetPageText(page)


    def GetPageImage(self, page):
        """
        Returns the image index for the given page.

        :param `page`: an integer specifying the page index.
        """

        return self._pages.GetPageImage(page)


    def GetEnabled(self, page):
        """
        Returns whether a tab is enabled or not.

        :param `page`: an integer specifying the page index.
        """

        return self._pages.GetEnabled(page)


    def EnableTab(self, page, enabled=True):
        """
        Enables or disables a tab.

        :param `page`: an integer specifying the page index;
        :param `enabled`: ``True`` to enable a tab, ``False`` to disable it.
        """

        if page >= len(self._windows):
            return

        self._windows[page].Enable(enabled)
        self._pages.EnableTab(page, enabled)


    def GetPage(self, page):
        """
        Returns the window at the given page position.

        :param `page`: an integer specifying the page to be returned.
        """

        if page >= len(self._windows):
            return

        return self._windows[page]


    def GetCurrentPage(self):
        """ Returns the currently selected notebook page or ``None``. """

        if self.GetSelection() < 0:
            return

        return self.GetPage(self.GetSelection())


    def OnNavigationKey(self, event):
        """
        Handles the ``wx.EVT_NAVIGATION_KEY`` event for :class:`FlatBookBase`.

        :param `event`: a :class:`NavigationKeyEvent` event to be processed.
        """

        if event.IsWindowChange():
            if self.GetPageCount() == 0:
                return

            # change pages
            self.AdvanceSelection(event.GetDirection())

        else:
            event.Skip()


    def AdvanceSelection(self, forward=True):
        """
        Cycles through the tabs.

        :param `forward`: if ``True``, the selection is advanced in ascending order
         (to the right), otherwise the selection is advanced in descending order.

        :note: The call to this function generates the page changing events.
        """

        nSel = self.GetSelection()

        if nSel < 0:
            return

        nMax = self.GetPageCount() - 1

        if forward:
            newSelection = (nSel == nMax and [0] or [nSel + 1])[0]
        else:
            newSelection = (nSel == 0 and [nMax] or [nSel - 1])[0]

        self.SetSelection(newSelection)


    def ChangeSelection(self, page):
        """
        Changes the selection for the given page, returning the previous selection.

        :param `page`: an integer specifying the page to be selected.

        :note: The call to this function does not generate the page changing events.
        """

        if page < 0 or page >= self.GetPageCount():
            return

        oldPage = self.GetSelection()
        self.DoSetSelection(page)

        return oldPage

    CurrentPage = property(GetCurrentPage, doc="See `GetCurrentPage`")
    Page = property(GetPage, doc="See `GetPage`")
    PageCount = property(GetPageCount, doc="See `GetPageCount`")
    PageText = property(GetPageText, SetPageText, doc="See `GetPageText, SetPageText`")
    Selection = property(GetSelection, SetSelection, doc="See `GetSelection, SetSelection`")


# ---------------------------------------------------------------------------- #
# Class FlatImageBook
# ---------------------------------------------------------------------------- #

class FancyTabNotebook(FlatBookBase):
    """
    Default implementation of the image book, it is like a :class:`Notebook`, except that
    images are used to control the different pages. This container is usually used
    for configuration dialogs etc.

    :note: Currently, this control works properly for images of size 32x32 and bigger.
    """

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=0, agwStyle=0, name="FlatImageBook"):
        """
        Default class constructor.

        :param `parent`: parent window. Must not be ``None``;
        :param `id`: window identifier. A value of -1 indicates a default value;
        :param `pos`: the control position. A value of (-1, -1) indicates a default position,
         chosen by either the windowing system or wxPython, depending on platform;
        :param `size`: the control size. A value of (-1, -1) indicates a default size,
         chosen by either the windowing system or wxPython, depending on platform;
        :param `style`: the underlying :class:`Panel` window style;
        :param `agwStyle`: the AGW-specific window style. This can be a combination of the
         following bits:

         =========================== =========== ==================================================
         Window Styles               Hex Value   Description
         =========================== =========== ==================================================
         ``INB_BOTTOM``                      0x1 Place labels below the page area. Available only for :class:`FlatImageBook`.
         ``INB_LEFT``                        0x2 Place labels on the left side. Available only for :class:`FlatImageBook`.
         ``INB_RIGHT``                       0x4 Place labels on the right side.
         ``INB_TOP``                         0x8 Place labels above the page area.
         ``INB_BORDER``                     0x10 Draws a border around :class:`LabelBook` or :class:`FlatImageBook`.
         ``INB_SHOW_ONLY_TEXT``             0x20 Shows only text labels and no images. Available only for :class:`LabelBook`.
         ``INB_SHOW_ONLY_IMAGES``           0x40 Shows only tab images and no label texts. Available only for :class:`LabelBook`.
         ``INB_FIT_BUTTON``                 0x80 Displays a pin button to show/hide the book control.
         ``INB_DRAW_SHADOW``               0x100 Draw shadows below the book tabs. Available only for :class:`LabelBook`.
         ``INB_USE_PIN_BUTTON``            0x200 Displays a pin button to show/hide the book control.
         ``INB_GRADIENT_BACKGROUND``       0x400 Draws a gradient shading on the tabs background. Available only for :class:`LabelBook`.
         ``INB_WEB_HILITE``                0x800 On mouse hovering, tabs behave like html hyperlinks. Available only for :class:`LabelBook`.
         ``INB_NO_RESIZE``                0x1000 Don't allow resizing of the tab area.
         ``INB_FIT_LABELTEXT``            0x2000 Will fit the tab area to the longest text (or text+image if you have images) in all the tabs.
         ``INB_BOLD_TAB_SELECTION``       0x4000 Show the selected tab text using a bold font.
         =========================== =========== ==================================================

        :param `name`: the window name.
        """

        FlatBookBase.__init__(self, parent, id, pos, size, style, agwStyle, name)

        self._pages = self.CreateImageContainer()
        #self._pages.SetDoubleBuffered(True)


        self._mainSizer = wx.BoxSizer(wx.HORIZONTAL)

        self.SetSizer(self._mainSizer)

        # Add the tab container to the sizer
        self._mainSizer.Add(self._pages, 0, wx.EXPAND)

        self._pages.SetSizeHints(169, 300)

        self._mainSizer.Layout()


    def CreateImageContainer(self):
        """ Creates the image container class for :class:`FlatImageBook`. """

        return ImageContainer(self, wx.ID_ANY, agwStyle=self.GetAGWWindowStyleFlag())
