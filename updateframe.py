# -*- coding: utf-8 -*-
import wx
#from utils import
import requests
from threading import Thread
from utils import TEMP_UPDATE_FILE, TEMP_UPDATE_INFO, API_UPDATE_URL, ThreadedRequests
from hashlib import md5
import os
import string, random

__author__ = 'TheArchitect'


class ThreadedDownloader(Thread):
    def __init__(self, url, download_location, progress_callback, filehash=False, skipdownload=False, *args, **kwargs):
        super(ThreadedDownloader, self).__init__(*args, **kwargs)
        self.url = url
        self.download_location = download_location
        self.progress_callback = progress_callback
        self.filehash = filehash
        self.skipdownload = skipdownload

    def run(self):
        try:
            #all is go
            if not self.skipdownload:
                self.savefile = open(self.download_location, 'w+b')
                reply = requests.get(self.url, stream=True)
                reply.raise_for_status()
                filesize = float(reply.headers['content-length'])
                downloaded = 0.0
                for chunk in reply.iter_content(chunk_size=10 * 1024):
                    if chunk:
                        downloaded += len(chunk)
                        self.savefile.write(chunk)
                        self.savefile.flush()
                        self.update_progress(downloaded/filesize)
                self.update_progress(1)
            #The download finishe
            else:
                self.savefile = open(self.download_location, 'rb')
            if self.filehash:
                result = self.verify_hash()
                if result:
                    self.progress_callback("done")
                else:
                    self.progress_callback("verifyfail")
                return
            self.progress_callback("done")
        except requests.RequestException:
            self.progress_callback("download-fail")
            return
        except IOError:
            self.progress_callback("save-fail")
            return
        except:
            self.progress_callback("fail")
            return
        else:
            self.savefile.close()



    def verify_hash(self):
        self.progress_callback("verify")
        self.savefile.seek(0, 2)  # Added to solve dev by 0 error when skipping download
        total = float(self.savefile.tell())
        current = 0.0
        self.savefile.seek(0)
        hash = md5()
        block_size = 128 * hash.block_size
        while True:
            data = self.savefile.read(block_size)
            if not data:
                break
            current += block_size
            self.update_progress(current/total)
            hash.update(data)
        sig = hash.hexdigest()
        self.savefile.close()
        if self.filehash != sig:
            return False
        return True

    def update_progress(self, percentage):
        percentage = int(percentage * 100)
        if percentage > 100: percentage = 100
        self.progress_callback(percentage)


###########################################################################
## Class UpdateFrame
###########################################################################

class UpdateFrame(wx.Frame):
    def __init__(self, parent=None):
        wx.Frame.__init__(self, parent, id=wx.ID_ANY, title=u"Software Updater", pos=wx.DefaultPosition,
                          size=wx.Size(500, 230),
                          style=wx.CAPTION | wx.CLOSE_BOX | wx.MINIMIZE_BOX | wx.SYSTEM_MENU | wx.TAB_TRAVERSAL)

        self.SetSizeHintsSz(wx.Size(500, 230), wx.Size(500, 230))
        self.app = wx.GetApp()
        self.download_location = TEMP_UPDATE_FILE
        self.updateinfo = None
        self.td = None
        self.background = False

        bSizer1 = wx.BoxSizer(wx.VERTICAL)

        self.m_panel1 = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        bSizer2 = wx.BoxSizer(wx.VERTICAL)

        bSizer3 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_bitmap1 = wx.StaticBitmap(self.m_panel1, wx.ID_ANY,
                                         wx.Bitmap(u"images/panel/update.png", wx.BITMAP_TYPE_ANY),
                                         wx.DefaultPosition, wx.DefaultSize, 0)
        bSizer3.Add(self.m_bitmap1, 0, wx.ALL, 5)

        self.updatetext = wx.StaticText(self.m_panel1, wx.ID_ANY, u"Checking for updates", wx.DefaultPosition, wx.DefaultSize,
                                        0)
        self.updatetext.Wrap(-1)
        bSizer3.Add(self.updatetext, 0, wx.ALIGN_CENTER_VERTICAL | wx.LEFT, 15)

        bSizer2.Add(bSizer3, 1, wx.ALL | wx.EXPAND, 15)

        bSizer5 = wx.BoxSizer(wx.VERTICAL)

        self.progress_bar = wx.Gauge(self.m_panel1, wx.ID_ANY, 100, wx.DefaultPosition, wx.Size(455, -1),
                                     wx.GA_HORIZONTAL)
        self.progress_bar.SetValue(45)
        bSizer5.Add(self.progress_bar, 0, wx.ALL, 5)

        bSizer2.Add(bSizer5, 0, wx.ALIGN_CENTER | wx.LEFT | wx.RIGHT, 15)

        bSizer6 = wx.BoxSizer(wx.VERTICAL)

        bSizer7 = wx.BoxSizer(wx.HORIZONTAL)

        self.m_button1 = wx.Button(self.m_panel1, wx.ID_ANY, u"Download in background", wx.DefaultPosition,
                                   wx.DefaultSize, 0)
        bSizer7.Add(self.m_button1, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        self.m_button2 = wx.Button(self.m_panel1, wx.ID_ANY, u"Check for update", wx.DefaultPosition, wx.DefaultSize, 0)
        self.m_button1.Bind(wx.EVT_BUTTON, self.OnButtonBackground)
        self.m_button2.Bind(wx.EVT_BUTTON, self.OnButtonUpdate)
        self.m_button2.Disable()
        self.Bind(wx.EVT_CLOSE, self.OnClose)
        bSizer7.Add(self.m_button2, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        bSizer6.Add(bSizer7, 0, wx.ALIGN_RIGHT, 5)

        bSizer2.Add(bSizer6, 1, wx.ALIGN_RIGHT | wx.EXPAND | wx.ALL, 15)

        self.m_panel1.SetSizer(bSizer2)
        self.m_panel1.Layout()
        bSizer2.Fit(self.m_panel1)
        bSizer1.Add(self.m_panel1, 1, wx.EXPAND)

        self.SetSizer(bSizer1)
        self.Layout()

        self.Centre(wx.BOTH)

    def check_update(self):
        self.progress_bar.SetValue(0)
        self.updatetext.SetLabel(u"Checking for updates")
        threquest = ThreadedRequests(self.update_callback)
        threquest.get(API_UPDATE_URL)

    def __update_failed(self, text=u"Failed to update"):
        self.updatetext.SetLabel(text)
        self.m_button2.Enable()
        self.progress_bar.SetValue(0)

    def update_callback(self, response):
        self.m_button2.Disable()
        if response.error:
            self.__update_failed(u"Failed to connect to update server")
        else:
            try:
                data = response.result.json()
                # if data.has_key(u"update_version") and data.has_key(u"update") and data.has_key():
                #     pass
                ver = int(data['update_version'])
                url = str(data['update_url'])
                filehash = str(data['update_hash'])

                f = open(TEMP_UPDATE_INFO, "wb")
                f.write(response.result.text)
                f.flush()
                f.close()

                self.updateinfo = (ver, url, filehash)

                #if file already exists
                #then skip download and jump to verification
                #if verification fails. delete file and start afreash

                if self.app.appversion < ver:
                    if os.path.isfile(TEMP_UPDATE_FILE % ver):
                        self.td = ThreadedDownloader(url, TEMP_UPDATE_FILE % ver, self.OnDownloadProgress, filehash, skipdownload=True)
                        self.td.start()
                    else:
                        self.updatetext.SetLabel(u"Downloading update...")
                        self.td = ThreadedDownloader(url, TEMP_UPDATE_FILE % 100, self.OnDownloadProgress, filehash)
                        self.td.start()
                else:
                    self.updatetext.SetLabel(u"Software is already updated.")
            except Exception, e:
                #raise
                self.__update_failed(u"Error while trying to update")

    def run_background(self, val = True):
            self.background = val

    def OnDownloadProgress(self, obj):
        if type(obj) == int:
            self.progress_bar.SetValue(obj)
            return
        #print obj
        if obj == "verify":
            self.updatetext.SetLabel(u"Verifying download")
        if obj == "verifyfail":
            self.__update_failed(u"Verification failed")
            #humm if we skipped downloading then we just try downloading again
            try:
                os.remove(self.td.download_location)
            except Exception, e:
                try:
                    newname = ''.join(random.choice(string.ascii_lowercase) for _ in range(8)) + ".tmp"
                    os.rename(self.td.download_location, newname)
                except Exception, e:
                    pass
                self.forceredownload = True
            if self.td.skipdownload:
                wx.CallAfter(self.check_update)
        if obj == "download-fail":
            self.__update_failed(u"Failed to download update")
        if obj == "save-fail":
            self.__update_failed(u"Unable to save file to disk")
        if obj == "fail":
            self.__update_failed(u"Update failed")
        if obj == "done":
            if not self.background:
                #delete tempfile
                if self.td.download_location != TEMP_UPDATE_FILE % self.updateinfo[0]:
                    os.rename(self.td.download_location, TEMP_UPDATE_FILE % self.updateinfo[0])
                self.app.run_update(TEMP_UPDATE_FILE % self.updateinfo[0])
                self.m_button2.Enable()

    def OnButtonBackground(self, event):
        self.Hide()

    def OnButtonUpdate(self, event):
        self.check_update()

    def OnClose(self, event):
        self.Hide()

    def __del__(self):
        pass

# def nullfn(*arg):
#     print "run_updte called"
#
# if __name__ == '__main__':
#     app = wx.App()
#     app.appversion = 201
#     app.run_update = nullfn
#     wizard = UpdateFrame(None)
#     wizard.Show()
#     import time
#     #time.sleep(1)
#     wizard.check_update()
#     app.MainLoop()
