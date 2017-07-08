import wx
from wx.html2 import WebView, PyWebViewHandler, WebViewArchiveHandler
from StringIO import StringIO
from utils import *
from base64 import b64encode, b64decode
import webassets
import webpages
import json

__author__ = 'TheArchitect'


class PageFactory(object):
    def __init__(self, pagemodule = webpages.Pages, assetsmodule = webassets.Assets, assets_prefix = "ASSET_" ):
        self.pagemodule = pagemodule

        self.assetmodule = assetsmodule
        self.asset_prefix = assets_prefix

        self.assets = {}
        self.pages = {}

        self.initAssets()
        self.initWebpages()

    def initAssets(self):
        items = dir(self.assetmodule)
        for item in items:
            if item.find(self.asset_prefix) == 0:  #ie it starts with the prefix:
                itemid = item.split(self.asset_prefix)[1]
                self.assets[itemid] = getattr(self.assetmodule, item)

    def renderWithAssets(self, page):  #This function can be pretty slow
        for key, item in self.assets.items():
            page = page.replace("{% " + key + " %}", item)
        return page

    def initWebpages(self):
        self.pages = self.pagemodule.pages

    def getPage(self, uri):
        if self.pages.has_key(uri):
            return self.renderWithAssets(self.pages[uri])
        elif self.pages.has_key("404.html"):
            return self.renderWithAssets(self.pages["404.html"])
        else: return None


html = "<html><head><title>Test Title</title></head><body><h1>HandlerTest</h1><a href=dialer:///jstests.html>JSTESTS</a></body></html>"
FMC_API_SERVER = "http://www.google.com/"
class FileNotFound(Exception):
    pass


class ScriptRun(object):
    def __init__(self, script):
        self.script = script


class DummyScheme(object):
    def __init__(self, scheme, extension):
        self.scheme = scheme
        self.extension = extension
        self.files = {}

    def GetFile(self, uri):
        scheme, name = uri.split("://")
        if self.files.has_key(name):
            return self.files[name]
        if self.files.has_key('404.%s'% self.extension):
            return self.files['404.%s'% self.extension]
        return "<html>File not found: dialer://%s</html>" % name

    def AddFile(self, uri, data):
        self.files[uri] = data

    def GetExtension(self):
        return self.extension

    def GetScheme(self):
        return self.scheme


class DialerScheme(PageFactory):
    def __init__(self, scheme):
        super(DialerScheme, self).__init__()
        self.scheme = scheme
        self.extension = "html"

    def GetFile(self, uri):
        scheme, name = uri.split("://")
        file = self.getPage(name)
        if file is not None:
            return file
        else: return "<html>File not found: dialer://%s</html>" % name

    def AddFile(self, uri, data):
        self.pages[uri] = data

    def GetExtension(self):
        return self.extension

    def GetScheme(self):
        return self.scheme


class CallbackScheme(object):
    def __init__(self, scheme, extension, browser=None):
        self.scheme = scheme
        self.extension = extension
        self.browser = browser
        self.files = {}
        self.reqs = []

    def GetFile(self, uri):
        scheme, uri, postdata, callbackfn, errorback = uri.split("//")
        req = ThreadedRequests(self.ResponseCallback)
        req.jscallback = callbackfn
        req.jserrorback = errorback
        if postdata:
            data = b64decode(postdata)
            postdata = json.loads(data)
            #maybe get cookies from wx.App
            req.post(FMC_API_SERVER+uri, postdata=postdata, verify=True)
        else:
            req.get(FMC_API_SERVER+uri , verify=True)
        self.reqs.append(req)
        #print "Running script", '%s("started");' % callbackfn
        return ScriptRun('%s("started");' % callbackfn)


    def ResponseCallback(self, response):
        resp = response.result
        #print resp
        if response.error:
            callback = response.request.jserrorback
            #self.browser.RunScript("%s();" % callback)
            wx.CallAfter(self.browser.RunScript, "%s('fail');" % callback )
        else:
            callback = response.request.jscallback
            wx.CallAfter(self.browser.RunScript, '%s("success", %d, "%s");' % (callback, resp.status_code, b64encode( resp.content) ) )
            #self.browser.RunScript("%s('success','%s');" % (callback, resp.content) )
        self.reqs.remove(response.request)


    def GetExtension(self):
        return self.extension

    def GetScheme(self):
        return self.scheme


class NativeCodeScheme(object):
    def __init__(self, scheme, funcdict):  #acheme = app
        self.scheme = scheme
        self.extension = ""
        self.functions = funcdict

    def GetFile(self, uri):
        scheme, uri = uri.split("://")
        if uri.find('?') > 0:
            name, args = uri.split("?")
            args = args.split(",")
        else:
            name = uri
            args = None

        if name[-1] == "/": #because somehow the uri always suffixes with a "/" on MSX
            name = name[:-1]

        if self.functions.has_key(name):
            if args is not None:
                self.functions[name](*args)
            else:
                return self.functions[name]()
        else:
            return None

    def AddFile(self, uri, data):
        self.files[uri] = data

    def GetExtension(self):
        return self.extension

    def GetScheme(self):
        return self.scheme


class FMCWebView(wx.Panel):
    def __init__(self, *args, **kwds):
        wx.Panel.__init__(self, *args, **kwds)
        size = self.GetSize()
        self.handlers = {}

        self.browser = wx.html2.WebView.New(self,size=size, style=wx.NO_BORDER)
        self.browser.Bind(wx.html2.EVT_WEBVIEW_NAVIGATING, self.PreNavigation)

        self.initHandlers()

    def PreNavigation(self, event):
        uri = event.GetURL()
        #print "FMCWEBVIEW.PreNavigation", uri
        scheme = uri.split('://')[0]

        if self.handlers.has_key(scheme):
            event.Veto()
            resource = self.handlers[scheme].GetFile(uri)
            if type(resource) in [str, unicode]:
                wx.CallAfter(self.browser.SetPage, resource, "")
            elif type(resource) == ScriptRun:
                wx.CallAfter(self.browser.RunScript, resource.script )
            elif resource is None:
                #print "None resource recvd. Doing nothing"
                return
        #print "Skipping event"
        event.Skip()

    def RegisterHandler(self, handler):
        scheme = handler.GetScheme()
        self.handlers[scheme] = handler

    def UnregisterHandler(self, handler):
        if self.handlers.has_key(handler):
            del self.handlers[handler]
            return True
        else:
            return False

    def initHandlers(self):
        dialerhandler = DialerScheme('app-storage')
        #dialerhandler.AddFile('index.html',html)
        #dialerhandler.AddFile('jstests.html', open("C:/work/projects/fmcv2/dialer/html/jstests.htm",'rb').read())
        self.RegisterHandler(dialerhandler)

        callbackhandler = CallbackScheme('fmcapi', None, self.browser)
        self.RegisterHandler(callbackhandler)


# if __name__ == '__main__':
#     print __file__
#     class MyBrowser(wx.Frame):
#         def __init__(self, *args, **kwds):
#             wx.Frame.__init__(self, *args, **kwds)
#             sizer = wx.BoxSizer(wx.VERTICAL)
#
#             self.webaddress = wx.TextCtrl( self, wx.ID_ANY, u"http://", wx.DefaultPosition)
#             self.webaddress.Bind(wx.EVT_TEXT_ENTER, self.NavigateTo)
#             sizer.Add(self.webaddress, 1, wx.EXPAND, 10)
#
#             self.webview = FMCWebView(parent=self,  size=(700,700))
#             #self.webview.browser.Bind(wx.html2.EVT_WEBVIEW_TITLE_CHANGED, self.printtitle)
#             self.webview.browser.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.runscript)
#             #self.browser.EnableContextMenu(False)
#             sizer.Add(self.webview, 2, wx.EXPAND, 10)
#
#             self.SetSizer(sizer)
#             self.SetSize((700, 700))
#
#             #wx.CallLater(5000,self.webview.browser.RunScript, 'document.title = "RunScript was successfulls";')
#
#         def NavigateTo(self, event):
#             print "Navigating to", self.webaddress.GetValue()
#             self.webview.browser.LoadURL(self.webaddress.GetValue())
#
#         def printtitle(self, event):
#             print "Title:", event.GetString()
#
#         def runscript(self, event):
#             print "Page loaded"
#             #self.webview.browser.RunScript('document.title = "RunScript was successfulls";')
#
#     app = wx.App()
#     dialog = MyBrowser(None, -1)
#
#     dialog.webview.browser.LoadURL("app-storage:///dialer/faq.html")
#     dialog.Show()
#
#     app.MainLoop()
