from mycroft import MycroftSkill, intent_file_handler
from fuzzywuzzy import fuzz
import requests
import json
import socket

__author__ = "GonzRon"


class LCSHubitatIntegration(MycroftSkill):
    def __init__(self):
        super().__init__()
        self.configured = False
        self.dev_commands_dict = None
        self.address = None
        self.attr_dict = None
        self.min_fuzz = None
        self.access_token = None
        self.settings_change_callback = None
        self.name_dict_present = None
        self.dev_id_dict = None
        self.maker_api_app_id = None

    def initialize(self):
        # This dict will hold the device name and its hubitat id number
        self.dev_id_dict = {}
        self.name_dict_present = False
        # Get a few settings from the Mycroft web site (they are specific to the user site) and
        # get the current values
        self.settings_change_callback = self.on_settings_changed
        self.on_settings_changed()

    def on_settings_changed(self):
        # Fetch the settings from the user account on mycroft.ai
        self.access_token = {'access_token': self.settings.get('access_token')}
        self.address = self.settings.get('local_address')
        self.min_fuzz = self.settings.get('minimum_fuzzy_score')
        self.maker_api_app_id = str(self.settings.get('hubitat_maker_api_app_id'))
        # The attributes are a special case.  I want to end up with a dict indexed by attribute
        # name with the contents being the default device.  But I did not want the user to have
        # to specify this in Python syntax.  So I just have the user give CSVs, possibly in quotes,
        # and the convert them to lists and then to a dict.
        attr_name = self.settings.get('attr_name')
        dev_name = self.settings.get('dev_name')

        if None not in [self.access_token, self.address, self.min_fuzz, self.maker_api_app_id, attr_name, dev_name]:
            # Remove quotes
            attr_name = attr_name.replace('"', '').replace("'", "")
            dev_name = dev_name.replace('"', '').replace("'", "")
            self.log.debug("Settings are " + attr_name + " and " + dev_name)

            # Turn them into lists
            attrs = attr_name.rsplit(",")
            devs = dev_name.rsplit(",")
            # self.log.info("Changed to "+attrs+" and "+devs)

            # Now turn the two lists into a dict and add an attribute for testing
            self.attr_dict = dict(zip(attrs, devs))
            self.attr_dict["testattr"] = "testAttrDev"
            self.log.debug(self.attr_dict)

            # If the device name is local assume it is fairly slow and change it to a dotted quad
            try:
                self.address = socket.gethostbyname(self.address)
                socket.inet_aton(self.address)
            except socket.error:
                self.log.info("Invalid Hostname or IP Address: addr={}".format(self.address))
                return

            self.log.debug(
                f"Updated settings: access token={self.access_token}, fuzzy={self.min_fuzz}, addr={self.address}, "
                f"makerApiId={self.maker_api_app_id}, attr dictionary={self.attr_dict}")
            self.configured = True

    def not_configured(self):
        self.log.debug("Cannot Run Intent - Settings not Configured")
    #
    # Intent handlers
    #

    @intent_file_handler('turn.on.intent')
    def handle_on_intent(self, message):
        # This is for utterances like "turn on the xxx"
        if self.configured:
            self.handle_on_or_off_intent(message, 'on')
        else:
            self.not_configured()

    @intent_file_handler('turn.off.intent')
    def handle_off_intent(self, message):
        # For utterances like "turn off the xxx".  A
        if self.configured:
            self.handle_on_or_off_intent(message, 'off')
        else:
            self.not_configured()

    @intent_file_handler('level.intent')
    def handle_level_intent(self, message):
        if self.configured:
            # For utterances like "set the xxx to yyy%"
            try:
                device = self.get_hub_device_name(message)
            except:
                # g_h_d_n speaks a dialog before throwing anerror
                return

            level = message.data.get('level')
            supported_modes = self.hub_get_attribute(self.hub_get_device_id(device), "supportedThermostatModes")
            self.log.debug("Set Level Supported Modes: " + str(supported_modes))
            if level in supported_modes:
                if self.is_command_available(command='setThermostatMode', device=device):
                    self.hub_command_devices(self.hub_get_device_id(device), "setThermostatMode", level)
                else:
                    self.not_configured()
            elif self.is_command_available(command='setLevel', device=device):
                self.hub_command_devices(self.hub_get_device_id(device), "setLevel", level)
                self.speak_dialog('ok', data={'device': device})
        else:
            self.not_configured()

    @intent_file_handler('attr.intent')
    def handle_attr_intent(self, message):
        if self.configured:
            # This one is for getting device attributes like level or temperature
            try:
                attr = self.hub_get_attr_name(message.data.get('attr'))
            except:
                # Get_attr_name also speaks before throwing an error
                return
            try:
                device = self.get_hub_device_name(message)
            except:
                device = self.get_hub_device_name_from_text(self.attr_dict[attr])

            self.log.debug("Found attribute={},device={}".format(attr, device))
            val = self.hub_get_attribute(self.hub_get_device_id(device), attr)
            if val is None:
                self.speak_dialog('attr.not.supported', data={'device': device, 'attr': attr})
            else:
                self.speak_dialog('attr', data={'device': device, 'attr': attr, 'value': val})
        else:
            self.not_configured()

    @intent_file_handler('rescan.intent')
    def handle_rescan_intent(self, message):
        if self.configured:
            count = self.update_devices()
            self.log.info(str(count))
            self.speak_dialog('rescan', data={'count': count})
        else:
            self.not_configured()

    @intent_file_handler('list.devices.intent')
    def handle_list_devices_intent(self, message):
        if self.configured:
            if not self.name_dict_present:
                self.update_devices()
            number = 0
            for hubDev in self.dev_id_dict:
                ident = self.dev_id_dict[hubDev]

                # Speak the real devices, but not the test devices
                if ident[0:6] != '**test':
                    number = number + 1
                    self.speak_dialog('list.devices', data={'number': str(number), 'name': hubDev, 'id': ident})
        else:
            self.not_configured()

    #
    # Routines used by intent handlers
    #
    def handle_on_or_off_intent(self, message, cmd):
        # Used for both on and off
        try:
            self.log.debug("In on/off intent with command " + cmd)
            device = self.get_hub_device_name(message)
            silence = message.data.get('how')
        except:
            # get_hub_device_name speaks the error dialog
            return

        if self.is_command_available(command=cmd, device=device):
            try:
                self.hub_command_devices(self.hub_get_device_id(device), cmd)
                if silence is None:
                    self.speak_dialog('ok', data={'device': device})
            except:
                # If command devices throws an error, probably a bad URL
                self.speak_dialog('url.error')

    def is_command_available(self, device, command):
        # Complain if the specified attribute is not one in the Hubitat maker app.
        for real_dev in self.dev_commands_dict:
            if device.find(real_dev) >= 0 and command in self.dev_commands_dict[real_dev]:
                return True
        self.speak_dialog('command.not.supported', data={'device': device, 'command': command})
        return False

    def get_hub_device_name(self, message):
        # This one looks in an utterance message for 'device' and then passes the text to
        # get_hub_device_name_from_text to see if it is in Hubitat
        self.log.debug("In get_h_d_n with device=")
        utt_device = message.data.get('device')
        self.log.debug(utt_device)
        if utt_device is None:
            raise NameError('NoDevice')
        device_name = self.get_hub_device_name_from_text(utt_device)
        self.log.debug("Device is " + str(device_name))
        return device_name

    def get_hub_device_name_from_text(self, text):
        # Look for a device name in the list of Hubitat devices.
        # The text may have something a bit different than the real name like "the light" or "lights" rather
        # than the actual Hubitat name of light.  This finds the actual Hubitat name using 'fuzzy-wuzzy' and
        # the match score specified as a setting by the user
        if not self.name_dict_present:
            # In case we never got the devices
            self.update_devices()

        # Here we compare all the Hubitat devices against the requested device using fuzzy and take
        # the device with the highest score that exceeds the minimum
        best_name = None
        best_score = self.min_fuzz
        for hub_dev in self.dev_id_dict:
            score = fuzz.token_sort_ratio(hub_dev, text)
            self.log.debug("Hubitat=" + hub_dev + ", utterance=" + text + " score=" + str(score))
            if score > best_score:
                best_score = score
                best_name = hub_dev
        self.log.debug("Best score is " + str(best_score))
        if best_score > self.min_fuzz:
            self.log.debug("Changed " + text + " to " + best_name)
            return best_name

        # Nothing had a high enough score.  Speak and throw.
        self.log.debug("No device found for " + text)
        self.speak_dialog('device.not.supported', data={'device': text})
        raise Exception("Unsupported Device")

    def hub_get_device_id(self, device):
        # devIds is a dict with the device name from hubitat as the key, and the ID number as the value.
        # This returns the ID number to send to hubitat
        for hub_dev in self.dev_id_dict:
            # self.log.debug("hubDev:"+hubDev+" device="+device)
            if device.find(hub_dev) >= 0:
                hubId = self.dev_id_dict[hub_dev]
                self.log.debug("Found device I said: " + hub_dev + " ID=" + hubId)
                return hubId

    def hub_get_attr_name(self, name):
        # This is why we need a list of possible attributes.  Otherwise we could not do a fuzzy search.
        best_name = None
        best_score = self.min_fuzz
        self.log.debug(self.attr_dict)
        attr = None

        for attr in self.attr_dict:
            self.log.debug("attr is {}".format(attr))
            score = fuzz.token_sort_ratio(attr, name)
            # self.log.info("Hubitat="+hubDev+", utterance="+text+" score="+str(score))
            if score > best_score:
                best_score = score
                best_name = attr

        self.log.debug("Best score is " + str(best_score))
        if best_score > self.min_fuzz:
            self.log.debug("Changed " + attr + " to " + best_name)
            return best_name
        else:
            self.log.debug("No device found for " + name)
            self.speak_dialog('attr.not.supported', data={'device': 'any device in settings', 'attr': name})
            raise Exception("Unsupported Attribute")

    def hub_command_devices(self, dev_id, state, value=None):
        # Build a URL to send the requested command to the Hubitat and
        # send it via "access_hubitat".  Some commands also have a value like "setlevel"
        if dev_id[0:6] == "**test":
            # This is used for regression tests only
            return
        url = "/apps/api/" + self.maker_api_app_id + "/devices/" + dev_id + "/" + state  # This URL is as specified in Hubitat maker app
        if value:
            url = url + "/" + value
        self.log.debug("URL for switching device " + url)
        self.access_hubitat(url)

    def hub_get_attribute(self, dev_id, attr):
        self.log.debug("Looking for attr {}".format(attr))
        # The json string from Hubitat turns into a dict.  The key attributes
        # has a value of a list.  The list is a list of dicts with the attribute
        # name, value, and other things that we don't care about.  So here when
        # the device was a test device, we fake out the attributes for testing
        if dev_id == "**testAttr":
            tempList = [{'name': "testattr", "currentValue": 99}]
            jsn = {"attributes": tempList}
            x = jsn["attributes"]
        else:
            # Here we get the real json string from hubitat
            url = "/apps/api/" + self.maker_api_app_id + "/devices/" + dev_id
            retVal = self.access_hubitat(url)
            jsn = json.loads(retVal)
            self.log.debug(jsn)
        # Now we have a nested set of dicts and lists as described above, either a simple
        # one for test or the real (and more complex) one for a real Hubitat

        for info in jsn:
            if info == "attributes":
                for ret_attr in jsn[info]:
                    if ret_attr['name'] == attr:
                        self.log.debug("Found Attribute Match: " + str(ret_attr['currentValue']))
                        return ret_attr['currentValue']
        return None
    
    def update_devices(self):
        json_data = None
        this_label = None
        this_id = None
        # Init the device list and command list with tests
        self.dev_commands_dict = {"testOnDev": ["on"], "testOnOffDev": ["on", "off"],
                                  "testLevelDev": ["on", "off", "setLevel"]}
        self.dev_id_dict = {"testOnDev": "**testOnOff", "testOnOffDev": "**testOnOff", "testLevelDev": "**testLevel",
                            "testAttrDev": "**testAttr"}
        self.log.debug(self.access_token)

        # Now get the actual devices from Hubitat and parse out the devices and their IDs and valid
        # commands
        request = self.access_hubitat("/apps/api/" + self.maker_api_app_id + "/devices/all")
        try:
            json_data = json.loads(request)
        except:
            self.log.debug("Error on json load")
        count = 0
        for device in json_data:
            # For every device returned, record as a dict the id to use in a URL and the label to be spoken
            # thisId = device.items()['id']
            # thisLabel = device.items()['label']
            # self.log.info("Id is "+str(thisId)+"label is "+thisLabel)
            for k, v in device.items():
                self.log.debug("attribute is " + str(k) + " value is " + str(v))
                if k == 'id':
                    this_id = v
                elif k == 'label':
                    this_label = v
                    self.dev_commands_dict[this_label] = []
                elif k == 'commands':
                    self.log.debug("Commands for " + this_label + " is=>" + str(v))
                    for cmd in v:
                        self.dev_commands_dict[this_label].append(cmd['command'])
            self.dev_id_dict[this_label] = this_id
            self.log.debug(self.dev_commands_dict[this_label])
            count = count + 1
        self.name_dict_present = True
        return count

    def access_hubitat(self, part_url):
        # This routine knows how to talk to the hubitat.  It builds the URL from
        # the know access type (http://) and the domain info or dotted quad in
        # self.address, followed by the command info passed in by the caller.
        request = None
        url = "http://" + self.address + part_url
        try:
            request = requests.get(url, params=self.access_token, timeout=5)
        except:
            # If the request throws an error, the address may have changed.  Try
            # 'hubitat.local' as a backup.
            try:
                self.speak_dialog('url.backup')
                self.address = socket.gethostbyname("hubitat.local")
                url = "http://" + self.address + part_url
                self.log.debug("Fell back to hubitat.local which translated to " + self.address)
                request = requests.get(url, params=self.access_token, timeout=10)
            except:
                self.log.debug("Got an error from requests")
                self.speak_dialog('url.error')
        return request.text

