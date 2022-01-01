from mycroft import MycroftSkill, intent_file_handler
import requests
import json

class HubitatIntegration(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    def initialize(self):
        #This dict will hold the device name and its hubitat id number
        self.devIdDict={}
        #Get a few settings from the Mycroft web site (they are specific to the user site)
        self.accessToken = {'access_token':self.settings.get('access_token')}
        self.address=self.settings.get('local_address')
        #And finally, get the devices that we will can use from Hubitat
        self.update_devices()

    @intent_file_handler('turn.on.intent')
    def handle_on_intent(self, message):
        # This is for stuff like "turn on the xxx"
        device = self.get_hub_device_name(message)
        if self.is_command_available(command='on',device=device):
            self.speak_dialog('on.off', data={'device': device})
            self.hub_switch_devices(self.hub_get_device_id(device),"on")
    
    @intent_file_handler('turn.off.intent')
    def handle_off_intent(self, message):
        device = self.get_hub_device_name(message)
        if self.is_command_available(command='off',device=device):
            self.speak_dialog('on.off', data={'device': device})
            self.hub_switch_devices(self.hub_get_device_id(device),"off")

    @intent_file_handler('level.intent')
    def handle_level_intent(self,message):
        device = self.get_hub_device_name(message)
        level = message.data.get('level')
        if self.is_command_available(command='setLevel',device=device):
            self.hub_switch_devices(self.hub_get_device_id(device),"setLevel",level)

    @intent_file_handler('rescan.intent')
    def handle_rescan_intent(self,message):
        count=self.update_devices()
        self.log.info(str(count))
        self.speak_dialog('rescan',data={'count':count})

    def is_command_available(self,device,command):
        for realDev in self.devCommandsDict:
            if device.find(realDev) >= 0 and command in self.devCommandsDict[realDev]:
                return True
        self.speak_dialog('not.supported',data={'device':device,'command':command})
        return False;

    def get_hub_device_name(self,message):
        # The utterance may have something different than the real name like "the light" or "lights" rather
        # than the actual Hubitat name of light.  This finds the actual Hubitat name assuming the utterance
        # is a superset
        utt_device = message.data.get('device').replace("the ","")
        clean_utt_dev = utt_device.replace("the ","")
        if clean_utt_dev.endswith('s'):
            clean_utt_dev = clean_utt_dev[:-1]
        for hubDev in self.devIdDict:
            self.log.info("Hubitate="+hubDev.casefold()+", utterance="+utt_device)
            if (utt_device.find(hubDev.casefold()) >= 0):
                self.log.info("Changed "+utt_device+" to "+hubDev)
                return hubDev
        self.log.info("No device found for "+utt_device)
        return None
        

    def hub_get_device_id(self,device):
        #devIds is a dict with the device name and device is the device name spoken for the intent
        #This returns the ID number to send to hubitat
        #self.get_hub_device_name(device)
        
        for hubDev in self.devIdDict:
            if device.find(hubDev) >= 0:
                hubId=self.devIdDict[hubDev]
                self.log.info("Found what I said: "+hubDev+" ID="+hubId)
                return hubId

    def hub_switch_devices(self,devid,state,value=None):
        url="http://"+self.address+"/apps/api/34/devices/"+devid+"/"+state
        if(value != None):
            url = url+"/"+value
        self.log.info("URL for switching device "+url)
        r=requests.get(url,params=self.accessToken)
        
    def update_devices(self):
        self.devCommandsDict = {}
        self.log.debug(self.accessToken)
        r=requests.get("http://"+self.address+"/apps/api/34/devices/all",params=self.accessToken)
        jsonLevel1 = json.loads(r.text)
        count=0
        for device in jsonLevel1:
            # For every device returned, record as a dict the id to use in a URL and the label
            # to be spoken
            for a,b in device.items():
                self.log.debug("a is "+str(a)+" b is "+str(b))
                if a == 'id':
                    thisId=b
                elif a=='label':
                    if b.endswith("s"):
                        thisLabel = b[:-1]
                    else:
                        thisLabel=b
                    self.devCommandsDict[thisLabel]=[]
                elif a=='commands':
                    self.log.debug("Commands for "+thisLabel+" is=>"+str(b))
                    for c in b:
                        self.devCommandsDict[thisLabel].append(c['command'])
            self.devIdDict[thisLabel]=thisId
            self.log.debug(self.devCommandsDict[thisLabel])
            #if 'setLevel' in self.devCommandsDict[thisLabel]:
            #    self.log.info("setLevel Exists in "+thisLabel)
            count=count+1
        return count


def create_skill():
    return HubitatIntegration()



