from mycroft import MycroftSkill, intent_file_handler
import requests
import json

class HubitatIntegration(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)
        self.devIdDict={}
        self.access={'access_token':'66990086-b22b-4c83-9b88-579b434c97bb'}
        self.update_devices()
    #@intent_file_handler('test.hubitat.intent')
    @intent_file_handler('turn.on.intent')
    def handle_on_intent(self, message):
        device = message.data.get('device')
        self.speak_dialog('on.off', data={
            'device': device
        })
        self.hub_switch_devices(self.hub_get_device_id(device,self.devIdDict),"on")
    
    @intent_file_handler('turn.off.intent')
    def handle_off_intent(self, message):
        device = message.data.get('device')
        self.speak_dialog('on.off', data={
            'device': device
        })
        self.hub_switch_devices(self.hub_get_device_id(device,self.devIdDict),"off")
    
    @intent_file_handler('rescan.intent')
    def handle_rescan_intent(self,message):
        count=self.update_devices()
        self.log.info(str(count))
        self.speak_dialog('rescan',data={'count':count})

    def hub_get_device_id(self,device,devIds):
        #devIds is a dict with the device name and device is the device name spoken for the intent
        #This returns the ID number to send to hubitat
        for hubDev in devIds:
            if device.find(hubDev.casefold()) >= 0:
                hubId=self.devIdDict[hubDev]
                self.log.debug("Found what I said: "+hubDev+" ID="+hubId)
        return hubId

    def hub_switch_devices(self,devid,state):
        url="http://10.0.1.121/apps/api/34/devices/"+devid+"/"+state
        self.log.debug(url)
        r=requests.get(url,params=self.access)
        
    def update_devices(self):
        r=requests.get("http://10.0.1.121/apps/api/34/devices",params=self.access)
        myJson = json.loads(r.text)
        count=0
        for device in myJson:
            # For every device returned, record as a dict the id to use in a URL and the label
            # to be spoken
            for a,b in device.items():
                if a == 'id':
                    thisId=b
                elif a=='label':
                    thisLabel=b
            self.devIdDict[thisLabel]=thisId
            count=count+1
        return count


def create_skill():
    return HubitatIntegration()



