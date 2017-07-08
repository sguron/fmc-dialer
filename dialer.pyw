import wx
from widgits import *
from DialerFrame import DialerFrame
from taskbar import TaskBarIcon
from loginframe import LoginFrame
from softphone import Softphone
from setupwizard import SetupWizard
from updateframe import UpdateFrame
from ConfigParser import ConfigParser
import os.path as path
from utils import *
from utils import _
import requests
import time
import sys
import _winreg as winreg
import hashlib
import socket
import subprocess
import json
import win32com.shell.shell as shell

__author__ = 'TheArchitect'


class CallConnectedEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_CONNECTED_ID)


class CallDisconnectedEvent(wx.PyEvent):
    def __init__(self):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_DISCONNECTED_ID)


class CallStatusEvent(wx.PyEvent):
    def __init__(self, state):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_STATUS_ID)
        self.state = state

    def GetState(self):
        return self.state


class SigninResultEvent(wx.PyEvent):
    def __init__(self, success=False, error_text=_([194, 219, 208, 220, 219, 209, 214, 225, 214, 220, 219, 206, 217, 141, 217, 220, 212, 214, 219, 141, 209, 210, 219, 214, 210, 209])):  # "Unconditional login denied"):
        wx.PyEvent.__init__(self)
        self.SetEventType(EVT_SIGNINRESULT_ID)
        self.success = success
        self.error_text = error_text

    def GetState(self):
        return self.success


class User(object):
    def __init__(self, username, password):
        self.loggedin = False
        self.username = username
        self.password = password
        self.macid = ''
        self.first_name = ''
        self.last_name = ''
        self.balance = 0.0000
        self.usacalling = False
        self.useremail = ''
        self.useraccount = ''
        self.package = None

    def readUserInfo(self, accountdata):
        self.first_name = accountdata.get(_([211, 214, 223, 224, 225, 204, 219, 206, 218, 210]), '')  # first_name
        self.last_name = accountdata.get(_([217, 206, 224, 225, 204, 219, 206, 218, 210]), '')  # 'last_name'
        self.balance = float(accountdata.get(_([207, 206, 217, 206, 219, 208, 210]), _([157, 155, 157, 157, 157])))  # balance, 0.000
        self.usacalling = accountdata.get(_([226, 224, 206, 208, 206, 217, 217, 214, 219, 212]), False)  # usa calling
        self.useremail = accountdata.get(_([226, 224, 210, 223, 210, 218, 206, 214, 217]), '')  # useremail
        self.useraccount = accountdata.get(_([226, 224, 210, 223, 206, 208, 208, 220, 226, 219, 225]), '')  # useraccount


class DialerApp(wx.App):
    def __init__(self, configfile, uid, kill, bgstart, *args, **kwargs):
        self.configfile = configfile
        f = open(configfile, 'rb')
        self.config = ConfigParser()
        self.config.readfp(f)
        f.close()

        self.uid = uid
        self.kill = kill

        self.adsurl = FMC_ADS_URL
        self.adsduration = DURATION_AD_TIMER
        self.updateran = False

        self.apisession = requests.session()
        self.bgstart = bgstart
        self.appversion = 201
        self.id2 = ''

        self.lastcall_duration = 0
        self.dialed_history = []

        self.user = User(*self.getUser())
        self.user.loggedin = False

        self.phonenum = ""
        self.phonecountry = ['', 'null', '', '']
        self.phone = Softphone()

        self.phone.setGuiCallbacks(self.callConnected, self.callDisconnected, self.callStatus)
        self.loadRecentCalls()
        super(DialerApp, self).__init__(*args, **kwargs)

    def OnInit(self):
        self.dialerframe = DialerFrame(self, None)
        #self.SetTopWindow(self.dialerframe)
        #self.dialerframe.Show()
        self.dialerframe.UpdateCallHistory()
        self.icon = wx.IconBundleFromFile(u"images/icons/icon.png")

        self.tray = TaskBarIcon(self)

        self.loginframe = LoginFrame()
        self.wizardframe = SetupWizard()
        self.updateframe = UpdateFrame()
        #self.SetTopWindow(self.loginframe)
        self.phone.runSoftphone()
        if not self.bgstart:
            self.loginframe.Show()

        self.setAudioDevices()
        self.wizardframe.buildAudioDeviceDropdown()
        self.dialerframe.buildAudioDeviceDropdown()

        if self.bgstart and self.user.username and self.user.password and not self.kill:
            wx.CallAfter(self.login, self.user.username, self.user.password)

        if not self.bgstart:
            self.check_downloaded_updates()

        self.Bind(wx.EVT_END_SESSION, self.ExitApp)

        return True

    def softphoneInitCallback(self):
        pass

    def loadRecentCalls(self):
        if not self.config.has_section(_([223, 210, 208, 210, 219, 225, 208, 206, 217, 217, 224])):  # recentcalls
            calls = []
        else:
            calls = []
            options = self.config.items(_([223, 210, 208, 210, 219, 225, 208, 206, 217, 217, 224]))  # recentcalls
            for time, cdr in options:
                try:
                    call = cdr.split(';')
                    calls.append(((str(call[1])), getCountry(call[0]), int(call[2]), int(time)))
                except:
                    continue
        self.dialed_history = calls

    def setAudioDevices(self):
        cap = self.config_get(_([206, 226, 209, 214, 220]), _([208, 206, 221, 225, 226, 223, 210, 209, 210, 227, 214, 208, 210]))  # 'audio', 'capturedevice')
        play = self.config_get(_([206, 226, 209, 214, 220]), _([221, 217, 206, 230, 207, 206, 208, 216, 209, 210, 227, 214, 208, 210]))  # 'audio', 'playbackdevice'

        self.phone.setCaptureDeviceByName(cap)
        self.phone.setPlaybackDeviceByName(play)

    def login(self, username, password):
        threquests = ThreadedRequests(self.login_callback, self.apisession)
        self.user.username = username
        self.user.password = password
        data = {'username': username, 'password': password, 'ver': self.appversion, 'id1': self.uid, 'id2': self.id2}
        threquests.post(API_LOGIN_URL, data=data, verify=True)  # TODO: Change verification to True

    def logout(self):
        self.user.loggedin = False
        self.apisession.cookies.clear()
        self.user = User(*self.getUser())

        self.phonenum = ""
        self.phonecountry = ['', 'null', '', '']
        self.bgstart = False

    def login_callback(self, response):
        login = False
        if response.error:
            wx.PostEvent(self.loginframe, SigninResultEvent(False, "Error: Unable to connect with server."))
            return
        else:
            try:
                data = response.result.json()
                if data['success']:
                    wx.PostEvent(self.loginframe, SigninResultEvent(True, "Logged in!"))
                    login = True
                else:
                    error_name = data['error'].get('error', "unamed")
                    error_text = data['error'].get('error_text', "Invalid username / password")
                    wx.PostEvent(self.loginframe, SigninResultEvent(False, error_text))
                    if error_name == "updateclient":
                        self.updateran = False
                        wx.CallLater(5 * 1000, self.check_downloaded_updates)

            except:
                wx.PostEvent(self.loginframe, SigninResultEvent(False, "Error while logging in."))
        if login:
            self.saveUser()
            self.loginframe.EnableInputElements()
            self.loginframe.ClearPassword()
            self.SetTopWindow(self.dialerframe)
            #self.loginframe.DropShadow(drop=False)
            self.loginframe.Hide()

            accountdata = response.result.json()['result']
            self.user.readUserInfo(accountdata)
            self.user.loggedin = True
            #before showing the dialer lets set some labels first
            self.dialerframe.m_staticText3.SetLabel(self.user.useremail)
            self.dialerframe.txt_balance.SetLabel(u"$%0.4f" % self.user.balance)
            self.dialerframe.txt_package.SetLabel(unicode(self.user.package))

            if "background-download" in accountdata:
                self.updateframe.run_background()
                wx.CallLater(5 * 60 * 1000, self.updateframe.check_update)

            uscall = self.user.usacalling
            if uscall == True:      # I know
                txt = "Unlimited !"
            elif uscall == False:   # I know
                txt = "N/A"
            else:       # This is why
                txt = uscall
            self.dialerframe.txt_uscalling.SetLabel(txt)
            wiz = self.wizardrequired()
            if not self.bgstart and not wiz:
                self.SetTopWindow(self.dialerframe)
                wx.CallAfter(self.dialerframe.Show)

            if not self.bgstart and wiz:
                self.SetTopWindow(self.wizardframe)
                wx.CallAfter(self.wizardframe.Show)

            if accountdata.has_key("dialer"):
                dialerdata = accountdata['dialer']
                self.adsurl = dialerdata.get('adurl', FMC_ADS_URL)
                self.adsduration = dialerdata.get('adduration', DURATION_AD_TIMER)
            wx.CallAfter(self.phone.retreveAccounts, self.apisession)

    def pstnCall(self):
        #This must be called in a non GUI thread
        codelen = len(self.phonecountry[3])
        self.phone.makePSTNCall(self.phonecountry[3], self.phonenum[codelen:])


    def hangup(self):
        self.phone.hangup()

    def sendDtmf(self, num):
        self.phone.sendDtmf(num)

    def setCaptureVolume(self, volume):
        self.phone.captureVolumeChange(volume)
        self.saveVolume('capture', volume)

    def setPlaybackVolume(self, volume):
        self.phone.playbackVolumeChange(volume)
        self.saveVolume('playback', volume)

    def changeAudioDevices(self, cap, play):
        self.phone.setCaptureDeviceByName(cap)  #TODO:change this to be more abstract
        self.phone.setPlaybackDeviceByName(play)

        self.saveDevice('capture', cap)
        self.saveDevice('playback', play)

    def callConnected(self):
        self.lastcall_duration = 0
        wx.PostEvent(self.dialerframe, CallConnectedEvent())

    def callDisconnected(self):
        codelen = len(self.phonecountry[3])
        t = str(int(time.time()))
        self.dialed_history.append(( self.phonenum[codelen:], self.phonecountry, self.lastcall_duration, int(t) ))
        self.saveRecentCall(self.phonecountry[3], self.phonenum[codelen:], self.lastcall_duration, t)
        wx.PostEvent(self.dialerframe, CallDisconnectedEvent())

    def callStatus(self, state, override=False):
        #print "New phone state:", state
        wx.PostEvent(self.dialerframe, CallStatusEvent(state))

    def callDuration(self):
        self.lastcall_duration = self.phone.getCallDuration()
        return self.lastcall_duration

    #
    #
    #       Configuration (.ini) related stuff is put there
    #
    #

    def wizardrequired(self):
        runwizard = self.config_get('system', 'runwizard')
        if runwizard == "1":
            runwizard = True
        else:
            runwizard = False
        return runwizard

    def WizardClose(self):
        self.wizardframe.Hide()
        self.SetTopWindow(self.dialerframe)
        self.dialerframe.Show()
        self.config_save("system", "runwizard", "0")

    def saveRecentCall(self, cc, number, duration, t):

        self.config_save("recentcalls", t, '%s;%s;%s' % ( cc, number, duration ))


    def saveVolume(self, audio, volume):
        self.config_save("audio", '%svolume' % audio, str(volume))

    def saveDevice(self, device, name):
        self.config_save("audio", '%sdevice' % device, name)

    def saveUser(self):
        self.config_save("user", "username", self.user.username)
        self.config_save("user", "password", self.user.password)

    def getUser(self):
        return self.config_get('user', 'username', ''), self.config_get('user', 'password', '')

    def config_save(self, section, key, value):
        if not self.config.has_section(section):
            self.config.add_section(section)
        self.config.set(section, key, value)
        f = open(self.configfile, 'wb')
        self.config.write(f)
        f.close()

    def config_get(self, section, key, default=''):
        if not self.config.has_section(section) or not self.config.has_option(section, key):
            return default
        else:
            return self.config.get(section, key)

    def check_downloaded_updates(self):
        #Check for existing update downloads
        if self.updateran:
            return
        try:
            if not path.isfile(TEMP_UPDATE_INFO):
                return
            f = open(TEMP_UPDATE_INFO, "rb")
            updateinfo = f.read()
            f.close()
            updateinfo = json.loads(updateinfo)
            if updateinfo['update_version'] > self.appversion:
                if path.isfile(TEMP_UPDATE_FILE % int(updateinfo['update_version'])):
                    self.updateran = True
                    self.run_update(TEMP_UPDATE_FILE % int(updateinfo['update_version']))
            else:
                return
        except:
            pass

    def run_update(self, exe):
            #subprocess.call(exe)
            #params = ' '.join([exe] + ["asadmin"])
            try:
                shell.ShellExecuteEx(lpVerb='runas', lpFile=exe, lpParameters="asadmin")
            except:  # eg user clicked cancel on elevation prompt
                pass
    #
    #
    #       Functions called from the taskbar icon are placed here
    #
    #

    def any_window_shown(self):
        if self.dialerframe.IsShown() or self.loginframe.IsShown():
            return True
        else:
            return False

    def TaskbarOpen(self):
        if self.user.loggedin:
            if self.wizardrequired():
                self.wizardframe.Show()
            elif not self.dialerframe.IsShown():
                self.dialerframe.Show()
            #if self.dialerframe.IsIconized():
            self.dialerframe.Raise()
            self.dialerframe.Iconize(False)
            self.check_downloaded_updates()
        else:
            if not self.loginframe.IsShown():
                self.loginframe.Show()
            self.loginframe.Iconize(False)
            self.loginframe.Raise()

    def TaskbarHideapp(self):
        if self.user.loggedin:
            if self.dialerframe.IsShown():
                self.dialerframe.Hide()
        else:
            if self.loginframe.IsShown():
                self.loginframe.Hide()

    def TaskbarCheckupdate(self):
        self.updateframe.Show()
        self.updateframe.check_update()

    def TaskbarCallphone(self):
        if self.user.loggedin:
            self.dialerframe.fancynotebook.SetSelection(INDEX_CALLPHONES)
            if not self.dialerframe.IsShown():
                self.dialerframe.Show()
            self.dialerframe.Raise()
            self.dialerframe.Iconize(False)
            self.check_downloaded_updates()

    def TaskbarRecentcalls(self):
        if self.user.loggedin:
            self.dialerframe.fancynotebook.SetSelection(INDEX_RECENTCALLS)
            if not self.dialerframe.IsShown():
                self.dialerframe.Show()
            self.dialerframe.Raise()
            self.dialerframe.Iconize(False)
            self.check_downloaded_updates()

    def TaskbarSettings(self):
        if self.user.loggedin:
            self.dialerframe.fancynotebook.SetSelection(INDEX_SETTINGS)
            if not self.dialerframe.IsShown():
                self.dialerframe.Show()
            self.dialerframe.Raise()
            self.dialerframe.Iconize(False)
            self.check_downloaded_updates()

    def TaskbarLogout(self):
        if self.user.loggedin:
            self.user.loggedin = False
            if self.dialerframe.IsShown():
                self.dialerframe.Hide()
            self.logout()
            self.callStatus(OFFLINE)
            self.phone.lib.hangup_all()
            self.loginframe.Show()

    def ExitApp(self):
        self.loginframe.Destroy()
        self.dialerframe.Destroy()
        self.wizardframe.Destroy()
        self.updateframe.Destroy()
        self.phone.destroy()
        self.tray.Destroy()

    #def __del__(self):
    #    pass
    #    #self.phone.destroy()

#
#
#  FOLLOWING CODE PROTECTS AGAINST CHEATING AND ABUSE
#
#
class Proc:
    def __init__(self, key, base=winreg.HKEY_LOCAL_MACHINE):  #port key -> query uid -> verify -> store and use forever
        self.k = key
        self.base = base
        # Get identifier
        self.pcid = _([228, 218, 214, 208, 141, 208, 221, 226, 141, 212, 210, 225, 141, 221, 223, 220, 208, 210, 224, 224, 220, 223, 214, 209])  # wimic command
        # Get serial number of harddisk
        self.diskid = _([228, 218, 214, 208, 141, 209, 214, 224, 216, 209, 223, 214, 227, 210, 141, 212, 210, 225, 141, 224, 210, 223, 214, 206, 217, 219, 226, 218, 207, 210, 223])  # wimic command
        self.yv = _([158, 159, 164, 155, 157, 155, 157, 155, 158])  # 127.0.0.1
        self.startupinfo = None
        self.startupinfo = subprocess.STARTUPINFO()
        self.startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

    def getTokens(self):
        buf = subprocess.check_output(self.diskid, startupinfo=self.startupinfo)
        diskserial = buf.split("\r\n")[1].strip()

        buf = subprocess.check_output(self.pcid, startupinfo=self.startupinfo)
        cpuid = buf.split("\r\n")[1].strip()

        #hasher = hashlib.md5(diskserial + cpuid + "\x12\xa1\xf2")
        #tokenhash = hasher.hexdigest()

        self.token = "-/-%s-/-%s-/-" % (diskserial, cpuid)

    def ts5(self):  #get port
        hkey = winreg.CreateKeyEx(self.base, self.k, 0, winreg.KEY_WOW64_64KEY | winreg.KEY_READ)
        rt = winreg.QueryValueEx(hkey, _([180, 214, 209]))[0]
        rt = int(rt) + 18532
        self.rt = rt

    def getuid(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(1)
        try:
            # CONNECT TO PERSISTANT HIDDEN SERVICE TO VERIFY INSTALLATION
            sock.connect((self.yv, self.rt))
            buf = ""
            buf = sock.recv(3)
            if buf != "\xDE\xAF\x04":
                raise Exception
            #if the socket doesnt connect raise error
            buf = ""

            sock.send("\x0F\x6D\x0C\x8A")
            time.sleep(0.5)
            while buf[-3:] != "\x5D\x5B\x5D":
                rcv = sock.recv(10)
                buf += rcv
                if rcv == "":
                    break
        except:
            raise
        self.gu = buf[3:35]

    def retToken(self):
        return self.token + self.gu

    def nike(self):
        # JUST DO USER VERIFICATION
        # MAKES SURE A BANNED USER ISNT RUNNING USING A NEW USERNAME
        self.ts5()
        self.getuid()
        self.getTokens()
        return self.retToken()


def main():
    if hasattr(sys, "frozen") and sys.frozen in ("windows_exe", "console_exe"):
        script_path = unicode(sys.executable, sys.getfilesystemencoding())
    else:
        script_path = path.abspath(__file__)

    script_location = path.dirname(script_path)

    args = sys.argv
    background_start = False
    kill_start = False

    if _([154, 154, 207, 206, 208, 216, 212, 223, 220, 226, 219, 209, 154, 224, 225, 206, 223, 225]) in args:  # --background-start
        background_start = True

    #generate tokens for abuse verification
    j = Proc(_([192, 188, 179, 193, 196, 174, 191, 178, 201, 201, 186, 214, 208, 223, 220, 224, 220, 211, 225, 201, 201, 177, 214, 223, 210, 208, 225, 197]))  # SOFTWARE\\Microsoft\\DirectX
    try:
        softid = j.nike()
    except:
        kill_start = True
        softid = ''

    #generate self hash
    sbuf = open(script_path, 'rb').read()
    sha = hashlib.md5()
    sha.update(sbuf)

    if hasattr(sys, "frozen") and sys.frozen in ("windows_exe", "console_exe"):
        sbuf = open(script_location + "\\"+ _([214, 221, 221, 223, 154, 165, 155, 159, 155, 209, 217, 217]), 'rb').read()  # u"ippr-8.2.dll"
        sha.update(sbuf)

    shash = sha.hexdigest()
    shash = "123"  #TODO: Remove this before release
    softid = shash + softid


    # All good create an instance of the dialer and launch it
    app = DialerApp(script_location + '\\config.ini', softid, kill_start, background_start, useBestVisual=True ) # ,redirect=True, filename=None )
    app.MainLoop()


if __name__ == '__main__':
    main()


#Done: recent calls dialer does not trigger ads
#Done: Hide doesnt work in taskbar
#Done: Add configuration wizard on first run and options in settings panel
#Done: Get adurl and timerduration from login json
#Done: DialerFrame.showPreCallAds has a hard coded ads url

#Done as needed (only imp strs): Encrypt Strings using some method
#Done: Integrate a update mechanism
#Done: close on dialerframe destroys the window. change this to iconize

#DONE: Disable all logging
#Done: Disable hashing of token in Proc (dialer.pyw)



#Low proprity V2 fixes
#fix shadow drop artifact bug on aleast win8



#CantFix :/ : Fix dragging in login window
#Willnot do: Requests session times out then relogin (is this really needed ? Coz we dont make a
#lot ot HTTP requests as such. Only once while login and another to fetch profiles.
