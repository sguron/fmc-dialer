from threading import Thread, Timer
import pjsua as pj
from utils import findCountry
from utils import *  #hets the http client from here
import requests
import time
import json
import re

__author__ = 'TheArchitect'

STUN_SERVER = 'stun.3cx.com'


class UnrecoverableFailure(RuntimeError):
    pass


class FMCAccountCallback(pj.AccountCallback):
    def __init__(self, sipphone):
        pj.AccountCallback.__init__(self, sipphone.account)
        self.sipphone = sipphone

    #def on_incoming_call(self, call):
    #    return self.sipphone.callback_onCall(call)

    def on_pager(self, from_uri, contact, mime_type, body):
        return self.sipphone.callback_onPager(from_uri, contact, mime_type, body)

    def on_reg_state(self):
        return self.sipphone.callback_onRegState(self.account)


class FMCCallCallback(pj.CallCallback):
    def __init__(self, sipphone):
        pj.CallCallback.__init__(self, None)
        self.sipphone = sipphone

    def on_state(self):
        print "Call is ", self.call.info().state_text,
        print "last code =", self.call.info().last_code,
        print "(" + self.call.info().last_reason + ")"
        return self.sipphone.callback_callState(self.call)

    def on_media_state(self):
        if self.call.info().media_state == pj.MediaState.ACTIVE:
            self.sipphone.callback_callmediaState(self.call)


class FMCMediaConfig(pj.MediaConfig):
    def __init__(self):
        pj.MediaConfig.__init__()
        self.turn_server = ''


class AccountResolver(Thread):
    def __init__(self, result_callback, clientid, *args, **kw_args):
        super(AccountResolver, self).__init__(*args, **kw_args)
        self.result_callback = result_callback
        self.session = None
        self.httpclient = ThreadedRequests(self.httpCallback)
        #self.retreveAccounts()

    def setSession(self, session):
        self.session = session
        self.httpclient = ThreadedRequests(self.httpCallback, self.session)

    def retreveAccounts(self):
        self.httpclient.get(API_PROFILE_URL, verify=True)

    def httpCallback(self, response):
        if not response.error:
            data = response.result.json()
            if data['success']:
                account = data['result']
                self.accounts = account
                self.initAccounts()
                self.default_account = self.accounts.pop('default')
                self.result_callback()
            else:
                raise Exception("Authentication error")
        else:
            raise Exception("Unable to retrieve accounts")

    def initAccounts(self):
        for cc_code, acc in self.accounts.items():
            #sipscc = pj.AccountConfig(str(acc['domain']), str(acc['username']), str(acc['password']),
            #                          str(acc['domain']))
            sipscc = pj.AccountConfig()
            sipscc.id = str(acc['domain']) + "<sip:" + str(acc['username']) + "@" + str(acc['domain']) + ">"
            sipscc.domain = str(acc['domain'])
            sipscc.auth_cred = [ pj.AuthCred("*", str(acc['username']), str(acc['password'])) ]
            sipscc.reg_uri = "sip:" + str(acc['domain'])
            if acc.has_key('proxy'):
                sipscc.proxy = [str(acc['proxy'][0])]
            if acc.has_key('srtp'):
                sipscc.use_srtp = str(acc['srtp'])
            if acc.has_key('srtp_sig'):
                sipscc.srtp_secure_signaling = str(acc['srtp_sig'])
            if acc.has_key('auth_algo'):
                sipscc.auth_initial_algorithm = str(acc['auth_algo'])

            if acc['transport'] == 'UDP':
                transport_type = pj.TransportType.UDP
                transport = pj.Lib.instance().create_transport(transport_type)
                sipscc.transport_id = transport._id

                acc['transport_object'] = transport
            else:
                transport_type = pj.TransportType.TCP
                #TCP transport is already created in initLib function of SipPhone class

            acc['acc_config'] = sipscc

    def resolveAccountFromCountry(self, cc_code):
        return self.accounts.get(cc_code, self.default_account)

    def resolveAccountFromNumber(self, number):
        """The number must include country code"""
        for key, value in self.accounts.items():
            match = re.match(key, number)
            if match is not None:
                return value
        # Humm nothing matches. Weird. Lets just return the default account
        # and handle this number in the default freeswitch profile
        return self.default_account


class Softphone(Thread):
    lib = None

    def __init__(self, *args, **kwargs):
        super(Softphone, self).__init__(*args, **kwargs)
        self.other_party = None
        self.other_party_country = ''
        self.call_direction = ''
        self.call_type = 'sip'
        self.phone_state = 'notready'  #/** "notready", "idle", "ringing", "dialing", "connected" */
        self.shutting_down = False
        self.connected = False
        self.call_time_elapsed = 0
        self.last_time = 0
        self.call = None

        self.ring_tone = '/path/to/ringtone'
        self.last_tone = None
        self.last_test_tone = None

        self.account_callback = None
        self.accountResolver = None

        self.account = None

        self.capture_device_id = -1
        self.capture_device_name = ''
        self.capture_volume = 1
        self.playback_device_id = -2
        self.playback_device_name = ''
        self.playback_volume = 1

        self.playback_devices = {}
        self.capture_devices = {}

        self.gui_callConnected = None
        self.gui_callDisconnected = None
        self.gui_updateStatus = None

    def __del__(self):
        try:
            #self.lib.hangup_all()
            self.lib.destroy()
            self.lib = None
        except:
            raise

    def destroy(self):
        self.shutting_down = True
        self.lib.destroy()
        self.lib = None

    def initLib(self):
        try:
            self.lib = pj.Lib()
        except:
            raise UnrecoverableFailure

        uaconfig = pj.UAConfig()
        #uaconfig.stun_host = STUN_SERVER
        if self.account:
            if self.account.has_key('useragent'):
                uaconfig.user_agent = self.account['useragent']

        def log_cb(lvl, str, len):
            pass
            print str

        try:
            self.lib.init(ua_cfg=uaconfig, log_cfg=pj.LogConfig(level=5, callback=log_cb))
            self.lib.create_transport(pj.TransportType.TCP)
            self.lib.start()
        except:
            raise UnrecoverableFailure

        self.broadcastStatus(CONNECTING)
        self.accountResolver = AccountResolver(self.callback_accountsRetrieved, clientid=None)


    def reinitLib(self):
        #if self.lib is not None:
        self.lib.destroy()
        self.initLib()

    def initAudioDevices(self):
        def_cap, def_play = self.lib.get_snd_dev()
        self.capture_devices['Default'] = def_cap
        self.playback_devices['Default'] = def_play
        sound_devices = self.lib.enum_snd_dev()
        for index, device in zip(range(0, len(sound_devices)), sound_devices):
            if device.input_channels:
                self.capture_devices[device.name] = index
            if device.output_channels:
                self.playback_devices[device.name] = index

    def setPlaybackDeviceByName(self, device_name, defaultonfail=False):
        if self.playback_devices.has_key(device_name):
            index = self.playback_devices[device_name]
            self.playback_device_id = index
            self.lib.set_snd_dev(self.capture_device_id, self.playback_device_id)
            return True
        else:
            if defaultonfail:
                return self.setPlaybackDeviceByName('Default')
            return False

    def setCaptureDeviceByName(self, device_name, defaultonfail=False):
        if self.capture_devices.has_key(device_name):
            index = self.capture_devices[device_name]
            self.capture_device_id = index
            self.lib.set_snd_dev(self.capture_device_id, self.playback_device_id)
            return True
        else:
            if defaultonfail:
                return self.setCaptureDeviceByName('Default')
            return False

    def getAudioDevices(self):
        dev = {'capture': [], 'playback': []}
        for device_name, index in self.capture_devices.items():
            if index == self.capture_device_id:
                selected = True
            else:
                selected = False

            dev['capture'].append((device_name, selected))

        for device_name, index in self.playback_devices.items():
            if index == self.playback_device_id:
                selected = True
            else:
                selected = False

            dev['playback'].append((device_name, selected))
        return dev

    def retreveAccounts(self, session):
        self.accountResolver.setSession(session)
        self.accountResolver.retreveAccounts()

    def initCodecs(self, acc_codecs):
        #first get all codecs in a list and disable all of them
        codecs = [codec.name for codec in self.lib.enum_codecs()]
        for codec in codecs:
            self.lib.set_codec_priority(codec, 0)

        for codec_name, priority in acc_codecs.items():
            if not codec_name in codecs:
                continue
            else:
                self.lib.set_codec_priority(str(codec_name), priority)

    def initAccount(self):
        #TODO impliment user agent changes by destroying and reiniting lib
        lck = self.lib.auto_lock()

        self.account = self.lib.create_account(self.account_config, True)
        self.account_callback = FMCAccountCallback(self)
        self.account.set_callback(self.account_callback)

        del lck


    def run(self):
        self.runSoftphone()

    def runSoftphone(self):
        self.initLib()
        self.initAudioDevices()


    def callFailed(self, failcode, failat, eobj):
        if self.gui_callDisconnected is not None:
            self.gui_callDisconnected()
        self.sipCallDisconnected()
        self.sipAccountDisconnect()
        self.broadcastStatus("%s (%s)" % ( CALLFAILED, failcode ))

    def start_ringtone(self):
        pass

    def stop_ringtone(self):
        pass

    def start_dialtone(self):
        pass

    def stop_dialtone(self):
        pass

    def disconnectHandler(self):
        pass

    def makePSTNCall(self, cc_code, dial_number):
        if self.phone_state == 'idle':
            self.phone_state = 'dialing'
            self.other_party = str(dial_number)
            self.other_party_country = str(cc_code)

            #startDialtone()
            self.broadcastStatus(CONNECTINGCALL)
            self.sipAccountConnect()
        elif self.phone_state == "notready":
            if self.gui_callDisconnected is not None:
                self.gui_callDisconnected()
            self.broadcastStatus(NOTREADY)

    def hangup(self):
        if self.phone_state == 'dialing' or self.phone_state == 'connected' or self.phone_state == 'ringing':
            self.phone_state = 'hangingup'
            self.sipHangup()

    def sendDtmf(self, num):
        if self.phone_state == 'connected' or self.phone_state == 'ringing':
            if self.call is not None:
                self.call.dial_dtmf(num)
        #play dtmf tones
        if self.last_tone is not None:
            try:
                self.lib.conf_disconnect(self.last_tone[1], 0)
                self.lib.player_destroy(self.last_tone[0])
            except:
                pass
            self.last_tone = None

        fname = num
        if fname == '*': fname = "star"
        if fname == '#': fname = "hash"

        try:
            player_id = self.lib.create_player('sounds\\dtmf\\%s.wav' % fname)
            player_slot = self.lib.player_get_slot(player_id)
            self.lib.conf_set_rx_level(player_slot, 0.2)
            self.lib.conf_connect(player_slot, 0)

            #Tone audio is playing
            self.last_tone = (player_id, player_slot)
        except:
            pass

    def playTestTone(self):
        if self.last_test_tone is not None:
            try:
                self.lib.conf_disconnect(self.last_test_tone[1], 0)
                self.lib.player_destroy(self.last_test_tone[0])
            except:
                pass
            self.last_test_tone = None

        try:
            player_id = self.lib.create_player('sounds\\tones\\incoming.wav')
            player_slot = self.lib.player_get_slot(player_id)
            self.lib.conf_set_rx_level(player_slot, 0.2)
            self.lib.conf_connect(player_slot, 0)

            #Tone audio is playing
            self.last_test_tone = (player_id, player_slot)
        except:
            pass

    def getCallDuration(self):
        if self.call is None:
            return 0
        else:
            time = self.call.info().call_time
            return time

    def setGuiCallbacks(self, connected=None, disconnected=None, status=None):
        if connected is not None:
            self.gui_callConnected = connected
        if disconnected is not None:
            self.gui_callDisconnected = disconnected
        if status is not None:
            self.gui_updateStatus = status

    def broadcastStatus(self, state):
        if self.gui_updateStatus is not None:
            self.gui_updateStatus(state)


    ######### SIP Account Callbacks

    def callback_onCall(self, call):
        pass

    def callback_onPager(self, from_uri, contact, mime_type, body):
        pass

    def callback_onRegState(self, account):
        acinfo = self.account.info()
        reg_status = acinfo.reg_status
        if acinfo.reg_status == 200 and acinfo.reg_expires > 0:
            if self.connected:
                # This is probably a keep alive registration event
                return
            self.connected = True
            #self.lib.set_null_snd_dev()
            self.sipDoCall()
        else:
            if not self.connected:
                self.callFailed(acinfo.reg_reason, "onRegState", None)  #failed to register
            #Unregistered
            self.connected = False
            self.account.delete()
            self.account = None
            #TODO::::::::::::::: auto unregister on disconnect
            #raise exception, delete account and account config and transport

    def callback_callState(self, call):
        call_state = call.info().state
        if call_state == pj.CallState.DISCONNECTED:
            self.sipCallDisconnected()
            self.broadcastStatus("%s (%s)" % ( CALLENDED, str(call.info().last_code) ))
        elif call_state == pj.CallState.CONFIRMED:
            self.sipCallConnected()
        elif call_state == pj.CallState.CONNECTING:
            pass
            #self.sipCallConnecting()
        elif call_state == pj.CallState.CALLING:
            pass
            #self.sipCalling()
        elif call_state == pj.CallState.INCOMING:
            pass
            #self.sipCallIncoming()


    def callback_callmediaState(self, call):
        call_slot = call.info().conf_slot
        self.lib.conf_connect(call_slot, 0)
        self.lib.conf_connect(0, call_slot)

    def callback_accountsRetrieved(self, success=True):
        self.phone_state = "idle"
        self.broadcastStatus(READY)


    ######### SIP FUNCTIONS

    def sipAccountConnect(self):
        if self.other_party is not None and self.other_party_country is not None:
            acc = self.accountResolver.resolveAccountFromNumber(self.other_party_country + self.other_party)
            self.account_config = acc['acc_config']
            if acc.has_key("codecs"):
                self.initCodecs(acc['codecs'])
            self.initAccount()

    def sipAccountDisconnect(self):
        if self.account is not None and self.connected:
            self.account.set_registration(False)
            #This will cause the account to deregister after a hangup

    def sipDoCall(self):
        dial_uri = "sip:%s%s@%s" % (str(self.other_party_country), self.other_party, self.account_config.domain )
        print "Calling=" + dial_uri
        callcallback = FMCCallCallback(self)
        self.broadcastStatus(CONNECTINGCALL)
        self.call = self.account.make_call(dial_uri, cb=callcallback)

    def sipCallDisconnected(self):
        self.phone_state = 'idle'
        self.other_party = ''
        self.other_party_country = ''
        self.call_direction = ''

        self.call = None
        if self.shutting_down: return

        self.sipAccountDisconnect()
        #Maybe account unregister at this point
        if self.gui_callDisconnected is not None:
            self.gui_callDisconnected()
        self.broadcastStatus(CALLENDED)

    def sipCallConnected(self):
        self.phone_state = 'connected'
        #stopRinging()
        #stopDialtone()
        if self.gui_callConnected is not None:
            self.gui_callConnected()
        self.broadcastStatus(CONNECTEDCALL)

    def sipHangup(self):
        if self.call is not None:
            if self.call.info().state in [pj.CallState.EARLY, pj.CallState.CALLING, pj.CallState.INCOMING,
                                          pj.CallState.CONFIRMED, pj.CallState.CONNECTING]:
                self.call.hangup()

                #TODO:  This would be a good point to send a disconnected broadcast
        self.phone_state = 'idle'

    def captureVolumeChange(self, vol):
        self.capture_volume = vol
        #if self.call is not None:
        #    call_slot = call.info().conf_slot
        try:
            self.lib.conf_set_rx_level(0, self.capture_volume)
        except:
            pass
            #conf_set_rx_level


    def playbackVolumeChange(self, vol):
        self.playback_volume = vol
        #if self.call is not None:
        #call_slot = call.info().conf_slot
        try:
            self.lib.conf_set_tx_level(0, self.playback_volume)
        except:
            pass

    def micChange(self, name):
        return self.setCaptureDeviceByName(name)

    def spkChange(self, name):
        return self.setPlaybackDeviceByName(name)


if __name__ == '__main__':
    phone = Softphone()
    phone.runSoftphone()
    #phone.setCaptureDeviceByName('Microphone Array (IDT High Defi')
    #phone.setPlaybackDeviceByName('Speakers / Headphones (IDT High')
    import time
    #time.sleep(5)
    phone.makePSTNCall('', '919041000000')
    ip = ''
    while ip != 'e':
        ip = raw_input('Enter command: ')
        if ip == 'h':
            print "Hangin up"
            phone.hangup()
        if ip == 'd':
            print "Dialing call"
            phone.sipDoCall()
    phone.lib.hangup_all()
    phone.lib.destroy()


