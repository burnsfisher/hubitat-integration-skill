from mycroft import MycroftSkill, intent_file_handler
from fuzzywuzzy import fuzz
import requests
import json
import socket

__author__="BurnsFisher"

class HubitatIntegration(MycroftSkill):
    #
    ##############################Setup
    #
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
        # Fetch the settings from the user account on mycroft.ai
        self.accessToken = {'access_token':self.settings.get('access_token')}
        self.address=self.settings.get('local_address')
        self.minFuzz=self.settings.get('minimum_fuzzy_score')
        
        # The attributes are a special case.  I want to end up with a dict indexed by attribute
        # name with the contents being the default device.  But I did not want the user to have
        # to specify this in Python syntax.  So I just have the user give CSVs, possibly in quotes,
        # and the convert them to lists and then to a dict.
        
        a = self.settings.get('attr_name')
        b = self.settings.get('dev_name')
        
        # Remove quotes
        
        a = a.replace('"','').replace("'","")
        b = b.replace('"','').replace("'","")
        self.log.debug("Settings are "+a+" and "+b)
        
        #Turn them into lists
        
        attrs = a.rsplit(",")
        devs = b.rsplit(",")
        #self.log.info("Changed to "+attrs+" and "+devs)
        
        #Now turn the two lists into a dict and add an attribute for testing
        
        self.attrDict = dict(zip(attrs,devs))
        self.attrDict["testattr"] = "testAttrDev"
        self.log.debug(self.attrDict)
        
        # If the device name is local assume it is fairly slow and change it to a dotted quad
        
        if(self.address.endswith(".local")):
            self.address = socket.gethostbyname(self.address)

        self.log.debug("Updated settings: access token={}, fuzzy={}, addr={}, attr dictionary={}".format(
            self.accessToken,self.minFuzz,self.address,self.attrDict))
#
# Intent handlers
#

    @intent_file_handler('turn.on.intent')
    def handle_on_intent(self, message):
        # This is for utterances like "turn on the xxx"
        self.handle_on_or_off_intent(message,'on')
        
    @intent_file_handler('turn.off.intent')
    def handle_off_intent(self, message):
        # For utterances like "turn off the xxx".  A
        self.handle_on_or_off_intent(message,'off')

    def handle_on_or_off_intent(self,message,cmd):
        
        # Used for both on and off
        
        try:
            self.log.debug("In on/off intent with command "+cmd)
            device = self.get_hub_device_name(message)
            silence = message.data.get('how')
        except:
            # get_hub_device_name speaks the error dialog
            return
        
        if self.is_command_available(command=cmd,device=device):
            try:
                self.hub_command_devices(self.hub_get_device_id(device),cmd)
                if(silence is None):
                    self.speak_dialog('ok',data={'device': device})
            except:
                #If command devices throws an error, probably a bad URL
                self.speak_dialog('url.error')
    

    @intent_file_handler('level.intent')
    def handle_level_intent(self,message):
        
        # For utterances like "set the xxx to yyy%"
        
        try:
            device = self.get_hub_device_name(message)
        except:
            
            #g_h_d_n speaks a dialog before throwing anerror
            
            return
        level = message.data.get('level')
        if self.is_command_available(command='setLevel',device=device):
            self.hub_command_devices(self.hub_get_device_id(device),"setLevel",level)
            self.speak_dialog('ok', data={'device': device})

    @intent_file_handler('attr.intent')
    def handle_attr_intent(self,message):
        
        # This one is for getting device attributes like level or temperature
        
        try:
            attr=self.hub_get_attr_name(message.data.get('attr'))
        except:
            #Get_attr_name also speaks before throwing an error
            return
        try:
            device = self.get_hub_device_name(message)
        except:
            device = self.get_hub_device_name_from_text(self.attrDict[attr])
        self.log.debug("Found attribute={},device={}".format(attr,device))
        val=self.hub_get_attribute(self.hub_get_device_id(device),attr)
        if val==None:
            self.speak_dialog('attr.not.supported',data={'device':device,'attr':attr})
        else:
            self.speak_dialog('attr',data={'device':device,'attr':attr,'value':val})

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
            
            # Speak the real devices, but not the test devices
            
            if ident[0:6] != '**test':
                 number=number+1
                 self.speak_dialog('list.devices',data={'number':str(number),'name':hubDev,
                                       'id':ident})
                 
    #
    # Routines used by intent handlers
    #
    def is_command_available(self,device,command):
        
        # Complain if the specified attribute is not one in the Hubitat maker app.

        for realDev in self.devCommandsDict:
            if device.find(realDev) >= 0 and command in self.devCommandsDict[realDev]:
                return True
        self.speak_dialog('command.not.supported',data={'device':device,'command':command})
        return False;
        
    def get_hub_device_name(self,message):
        
        # This one looks in an utterance message for 'device' and then passes the text to
        # get_hub_device_name_from_text to see if it is in Hubitat
        
        self.log.debug("In get_h_d_n with device=")
        utt_device = message.data.get('device')
        self.log.debug(utt_device)
        if utt_device == None:
            raise NameError('NoDevice')
        a = self.get_hub_device_name_from_text(utt_device)
        self.log.debug("Device is "+str(a))
        return a
    
    def get_hub_device_name_from_text(self,text):
        
        # Look for a device name in the list of Hubitat devices.
        
        # The text may have something a bit different than the real name like "the light" or "lights" rather
        # than the actual Hubitat name of light.  This finds the actual Hubitat name using 'fuzzy-wuzzy' and
        # the match score specified as a setting by the user

        if not self.nameDictPresent:
            # In case we never got the devices
            self.update_devices()
            
        # Here we compare all the Hubitat devices against the requested device using fuzzy and take
        # the device with the highest score that exceeds the minimum
        
        best_name = None
        best_score=self.minFuzz
        for hubDev in self.devIdDict:
            score = fuzz.token_sort_ratio(
                hubDev,
                text)
            self.log.debug("Hubitate="+hubDev+", utterance="+text+" score="+str(score))
            if score > best_score:
                best_score = score
                best_name = hubDev
        self.log.debug("Best score is "+str(best_score))
        if best_score>self.minFuzz:
            self.log.debug("Changed "+text+" to "+best_name)
            return best_name
        
        # Nothing had a high enough score.  Speak and throw.
        
        self.log.debug("No device found for "+text)
        self.speak_dialog('device.not.supported',data={'device':text})
        raise Exception("Unsupported Device")
        

    def hub_get_device_id(self,device):

        #devIds is a dict with the device name from hubitat as the key, and the ID number as the value.
        #This returns the ID number to send to hubitat
        
        for hubDev in self.devIdDict:
            #self.log.debug("hubDev:"+hubDev+" device="+device)
            if device.find(hubDev) >= 0:
                hubId=self.devIdDict[hubDev]
                self.log.debug("Found device I said: "+hubDev+" ID="+hubId)
                return hubId
            
    def hub_get_attr_name(self,name):
        best_name = None
        best_score=self.minFuzz
        self.log.debug(self.attrDict)
        
        # This is why we need a list of possible attributes.  Otherwise we could not do a
        # fuzzy search.
        
        for attr in self.attrDict:
            self.log.debug("attr is {}".format(attr))
            score = fuzz.token_sort_ratio(
                attr,
                name)
            #self.log.info("Hubitate="+hubDev+", utterance="+text+" score="+str(score))
            if score > best_score:
                best_score = score
                best_name = attr
        self.log.debug("Best score is "+str(best_score))
        if best_score>self.minFuzz:
            self.log.debug("Changed "+attr+" to "+best_name)
            return best_name
        self.log.debug("No device found for "+name)
        self.speak_dialog('attr.not.supported',data={'device':'any device in settings','attr':name})
        raise Exception("Unsupported Attribute")

        return name

    def hub_command_devices(self,devid,state,value=None):
        
        # Build a URL to send the requested command to the Hubitat and
        # send it via "access_hubitat".  Some commands also have a value like "setlevel"
        
        if devid[0:6] == "**test":
            #This is used for regression tests only
            return
        url="/apps/api/34/devices/"+devid+"/"+state #This URL is as specified in Hubitat maker app
        if(value != None):
            url = url+"/"+value
        self.log.debug("URL for switching device "+url)
        r=self.access_hubitat(url)
    
    def hub_get_attribute(self,devid,attr):
        self.log.debug("Looking for attr {}".format(attr))

        if devid == "**testAttr":
            
            # The json string from Hubitat turns into a dict.  The key attributes
            # has a value of a list.  The list is a list of dicts with the attribute
            # name, value, and other things that we don't care about.  So here when
            # the device was a test device, we fake out the attributes for testing
            
            tempList=[{'name':"testattr","currentValue":99}]
            jsn = {"attributes":tempList}
            x = jsn["attributes"]            
        else:
            #Here we get the real json string from hubitat
            url = "/apps/api/34/devices/"+devid+"/poll"
            retVal = self.access_hubitat(url)
            jsn = json.loads(retVal)
        
        # Now we have a nested set of dicts and lists as described above, either a simple
        # one for test or the real (and more complex) one for a real Hubitat
        
        for info in jsn:
            if info == "attributes":
                for a in jsn[info]:
                    if a['name'] == attr:
                        self.log.debug(a['currentValue'])
                        return a['currentValue']
        return None
    
    def update_devices(self):
        #Init the device list and command list with tests
        self.devCommandsDict = {"testOnDev":["on"],"testOnOffDev":["on","off"],
                                "testLevelDev":["on","off","setLevel"]}
        self.devIdDict = {"testOnDev":"**testOnOff","testOnOffDev":"**testOnOff","testLevelDev":"**testLevel",
                          "testAttrDev":"**testAttr"}
        self.log.debug(self.accessToken)
        
        # Now get the actual devices from Hubitat and parse out the devices and their IDs and valid
        # commands
        
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
        
        # This routine knows how to talk to the hubitat.  It builds the URL from
        # the know access type (http://) and the domain info or dotted quad in
        # self.address, followed by the command info passed in by the caller.
        
        url = "http://"+self.address+partURL
        try:
            r=requests.get(url,params=self.accessToken,timeout=5)
        except:
            
            # If the request throws an error, the address may have changed.  Try
            # 'hubitat.local' as a backup.
            
            try:
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





