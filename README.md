# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/home.svg' card_color='#408BDB' width='50' height='50' style='vertical-align:bottom'/> Hubitat Integration
Use Mycroft for Home Automation with Hubitat Hub

## About
This is a skill to teach Mycroft how to send commands to the Hubitat Zigbee/ZWave hub based on spoken  commands.  This skill can deal with any Hubitat device that is enabled in the Hubitat "Maker" app and which has commands "on", "off" or "setLevel".  This includes essentially any switched outlets, lights,
dimmers, and scene activators.  It can also read some attributes, although allowed attributes must be specified in settings.

You can also ask it to scan for new devices that Hubitat has made available to it, and you can list the devices it knows (but that takes a while for Mycroft to speak).

The device name that you speak to Mycroft is the device label you have specified in Hubitat, but the skill uses "fuzzywuzzy" to allow some leeway in what you say.

There are six settings for this skill (which you set via your Mycroft account).  You *must* specify the access token and the API number, both of which can be found by looking at the Hubitat "Maker" app. (Look at the example URLs.  The API number follows "api" and the access token follows "access_token"  The Hubitat address defaults to hubitat.local, which should work unless you have multiple hubitats on the LAN or for some other reason .local names are not supported.  You can also specify a 'score' between 0 and 100 for comparing the device name you speak to the Hubitat label.  For example, if the label is 'bookcase lights' you can say 'the bookcase lights', 'bookcase light', 'lights on the bookcase', etc.  A score of 65 seems to work well.

This skill can read attributes as well, but you must specify both the name of the attribute and the Hubitat label of the device in settings.  In the "attr" setting, include a comma-separated list of attributes with quotes, for example "temperature","heatingSetPoint","level".  In the device setting, enter a comma-separated list of default devices that match the attributes order.  For example, "thermostat","thermostat","overhead lights".  The your utterance can include the device, especially if more than one device has the same attribute.  Notest that these are hard intents to define because it is common to speak differently depending on the attribute.

## Examples
* "Turn on the bookcase lights"
* "Turn off bookcase light"
* "Set the overhead light to 50%"
* "Scan for new devices"
* "Set overnight mode"
* "Show me the inside temperature"
* "tell me the level of the window lights"

## Credits
Burns Fisher (@burnsfisher)
LC Style (@GonzRon)

## Installation Instructions (Work in progress)
I have successfully made this work on both Picroft and on Mycroft MkII hardware with Neon software

Here is the process for installing on Neon.  I assume you have a MkII hardware with a Neon flash drive.  If you have version 23.3.15, then say
"Hey Neon is there an update available".  There will be, and you should install it.  If you have 23.4.5 or later, there may not be a new version.

Next ssh to the MkII (if you have not done it before, ssh neon@neon.local, password neon.  You must change it and re-ssh)

Issue the following commands (answer y to uninstall, answer 1 [it says unknown--don't worry] and then y to osm install):

pip uninstall neon_homeassistant_skill
osm install https://github.com/burnsfisher/hubitat-integration-skill.git
cd ~/.config/neon/skills/hubitat-integration-skill.burnsfisher


Now use nano or whatever editor you want to edit settings.json.  It should initially
have only one line surrounded by braces.  Add extra lines so it looks like this:

{
    "__mycroft_skill_firstrun": false,
    "access_token": "xxxxxxxx",
    "local_address": "xxxxxxx",
    "minimum_fuzzy_score": 62,
    "hubitat_maker_api_app_id": xxx,
    "attr_name": "'temperature','heatingSetpoint','level'",
    "dev_name": "'thermostat','thermostat','overhead lights'"
}

You will need to get the access_token and the hubitat maker app ID from hubitat itself.  The access token is
a long series of numbers and letters, while the app id should be an integer.  The local address needs to be
a dotted quad (e.g. 192.168.1.2) which you can find from your wifi hub.  Hubitat.local will not work for some
reason.  You must be VERY careful to get settings.json to work correctly.  If the hubitat skill does not work
look back at this file.  If your hubitat lines have been deleted, there was a syntax error.  (Check for closing 
braces, parens, and be sure to add a comma after all but the last text line).  I've also found bizzare things that
go wrong...maybe and extra end-line character, maybe an extra space?  Reported to the Neon/OVOS guys.  

Enter
cd ~/.config/neon and similar to the above editing, you must edit neon.yaml to add

  - neon-homeassistant-skill
  
to the end of the blacklisted skills.  This will ensure that home assistant will not be installed again (HA has
conflicting commands with hubitat).


Now restart your MkII using the command

sudo reboot now

(Do not just power cycle it).
## Category
**IoT**

## Tags
#hubitat
#zigbee
#zwave
