from mycroft import MycroftSkill, intent_file_handler
from fuzzywuzzy import fuzz
import requests
import json
import socket

__author__="BurnsFisher"

class HubitatIntegration(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        #This dict will hold the device name and its hubitat id number
        self.devIdDict={}
        self.nameDictPresent=False
        #Get a few settings from the Mycroft web site (they are specific to the user site) and
        #get the current values
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()
        
    def on_settings_changed(self):
        self.accessToken = {'access_token':self.settings.get('access_token')}
        self.address=self.settings.get('local_address')
        self.minFuzz=self.settings.get('minimum_fuzzy_score')
        if(self.address.endswith(".local")):
            self.address = socket.gethostbyname(self.address)

        self.log.debug("Updated access token={}, fuzzy={}, addr={}".format(self.accessToken,self.minFuzz,self.address))

    @intent_file_handler('turn.on.intent')
    def handle_on_intent(self, message):
        # This is for utterances like "turn on the xxx"
        try:
            device = self.get_hub_device_name(message)
        except:
            return
        if self.is_command_available(command='on',device=device):
            try:
                self.hub_command_devices(self.hub_get_device_id(device),"on")
                self.speak_dialog('ok',data={'device': device})
            except:
                self.speak_dialog('url.error')
    
    @intent_file_handler('turn.off.intent')
    def handle_off_intent(self, message):
        # For utterances like "turn off the xxx"
        try:
            device = self.get_hub_device_name(message)
        except:
            return
        if self.is_command_available(command='off',device=device):
            self.speak_dialog('ok', data={'device': device})
            self.hub_command_devices(self.hub_get_device_id(device),"off")

    @intent_file_handler('level.intent')
    def handle_level_intent(self,message):
        # For utterances like "set the xxx to yyy%
        try:
            device = self.get_hub_device_name(message)
        except:
            return
        level = message.data.get('level')
        if self.is_command_available(command='setLevel',device=device):
            self.hub_command_devices(self.hub_get_device_id(device),"setLevel",level)
            self.speak_dialog('ok', data={'device': device})

    @intent_file_handler('attr.intent')
    def handle_attr_intent(self,message):
        device = self.get_hub_device_name(message)
        self.hub_get_attribute(self.hub_get_device_id(device),"temperature")


    @intent_file_handler('rescan.intent')
    def handle_rescan_intent(self,message):
        count=self.update_devices()
        self.log.info(str(count))
        self.speak_dialog('rescan',data={'count':count})

    @intent_file_handler('list.devices.intent')
    def handle_list_devices_intent(self,message):
        if not self.nameDictPresent:
            self.update_devices()
        number=0
        for hubDev in self.devIdDict:
            ident=self.devIdDict[hubDev]
            if ident != 'testonly':
                 number=number+1
                 self.speak_dialog('list.devices',data={'number':str(number),'name':hubDev,
                                       'id':ident})
    def is_command_available(self,device,command):
        for realDev in self.devCommandsDict:
            if device.find(realDev) >= 0 and command in self.devCommandsDict[realDev]:
                return True
        self.speak_dialog('command.not.supported',data={'device':device,'command':command})
        return False;

    def get_hub_device_name(self,message):
        # The utterance may have something different than the real name like "the light" or "lights" rather
        # than the actual Hubitat name of light.  This finds the actual Hubitat name assuming the utterance
        # is a superset
        if not self.nameDictPresent:
            self.update_devices()
        utt_device = message.data.get('device')
        best_name = None
        best_score=self.minFuzz
        self.log.debug("minFuzz is "+str(self.minFuzz))
        for hubDev in self.devIdDict:
            score = fuzz.token_sort_ratio(
                hubDev,
                utt_device)
            self.log.debug("Hubitate="+hubDev+", utterance="+utt_device+" score="+str(score))
            if score > best_score:
                best_score = score
                best_name = hubDev
        self.log.debug("Best score is "+str(best_score))
        if best_score>self.minFuzz:
            self.log.debug("Changed "+utt_device+" to "+best_name)
            return best_name
        self.log.debug("No device found for "+utt_device)
        self.speak_dialog('device.not.supported',data={'device':utt_device})
        raise Exception("Unsupported Device")
        

    def hub_get_device_id(self,device):
        #devIds is a dict with the device name and device is the device name spoken for the intent
        #This returns the ID number to send to hubitat
        #self.get_hub_device_name(device)
        
        for hubDev in self.devIdDict:
            if device.find(hubDev) >= 0:
                hubId=self.devIdDict[hubDev]
                self.log.debug("Found device I said: "+hubDev+" ID="+hubId)
                return hubId

    def hub_command_devices(self,devid,state,value=None):
        if devid == "testonly":
            return
        url="/apps/api/34/devices/"+devid+"/"+state
        if(value != None):
            url = url+"/"+value
        self.log.debug("URL for switching device "+url)
        r=self.access_hubitat(url)
    
    def hub_get_attribute(self,devid,attr):
        self.log.info("Devid is {}, attr is {}".format(devid,attr))
        if devid == "testonly":
            return "ok"
        url = "/apps/api/34/devices/"+devid+"/poll"
        retVal = self.access_hubitat(url)
        jsn = json.loads(retVal)
        self.log.info(str(type(jsn)))
        for info in jsn:
            self.log.info(str(type(info)))
            if info == "attributes":
                for a in jsn[info]:
                    self.log.info("type of a={},a={}".format(type(a),a))
    def update_devices(self):
        #Init the device list and command list with tests
        self.devCommandsDict = {"test on dev":["on"],"test onoff dev":["on","off"],
                                "test level dev":["on","off","setLevel"]}
        self.devIdDict = {"test on dev":"testonly","test off dev":"testonly","test level dev":"testonly"}
        self.log.debug(self.accessToken)
        r = self.access_hubitat("/apps/api/34/devices/all")
        try:
            jsonLevel1 = json.loads(r)
        except:
            self.log.debug("Error on json load")
        count=0
        for device in jsonLevel1:
            # For every device returned, record as a dict the id to use in a URL and the label
            # to be spoken
            #thisId = device.items()['id']
            #thisLabel = device.items()['label']
            #self.log.info("Id is "+str(thisId)+"label is "+thisLabel)
            for a,b in device.items():
                self.log.debug("a is "+str(a)+" b is "+str(b))
                if a == 'id':
                    thisId=b
                elif a=='label':
                    thisLabel=b
                    self.devCommandsDict[thisLabel]=[]
                elif a=='commands':
                    self.log.debug("Commands for "+thisLabel+" is=>"+str(b))
                    for c in b:
                        self.devCommandsDict[thisLabel].append(c['command'])
            self.devIdDict[thisLabel]=thisId
            self.log.debug(self.devCommandsDict[thisLabel])
            count=count+1
            self.nameDictPresent=True
        return count
    
    def access_hubitat(self,partURL):
        url = "http://"+self.address+partURL
        try:
            r=requests.get(url,params=self.accessToken,timeout=5)
        except:
            try:
                #self.address = "hubitat.local"
                self.speak_dialog('url.backup')
                self.address = socket.gethostbyname("hubitat.local")
                url = "http://"+self.address+partURL
                self.log.debug("Fell back to hubitat.local which translated to "+self.address)
                r=requests.get(url,params=self.accessToken,timeout=10)
            except:
                self.log.debug("Got an error from requests")
                self.speak_dialog('url.error')
        return r.text


def create_skill():
    return HubitatIntegration()





