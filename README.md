# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/home.svg' card_color='#408BDB' width='50' height='50' style='vertical-align:bottom'/> Hubitat Integration
Use Mycroft for Home Automation with Hubitat Hub

## About
First note that Mycroft was an open source smart speaker app and hardware initially started with crowdfunding.  They produced both software to run a user's own Raspberry Pi (PiCroft)
and a hardware device called Mycroft Mark II.  (There is a Mark I but few people have it.).  They have since essentially closed their doors and the work and hardware support has been
taken over by  a company called Neon Gecko.  Unfortunately, all of Mycroft's servers have been shut down, so the PiCroft version no longer works.  Thus, this is about the Mark II running Neon.  (There may be some other possibilities through Neon Gecko, but I know nothing abut them).  

Neon Gecko is producing software using OVOS (Open Voice OS).  I am currently using a Mark II running the Neon/OVOS software, but I will
say "Mycroft" to stand for the MkII with Neon/OVOS.  This skill does not work with MkII and the Mycroft (dinkum) software because you can't access the Mk II via SSH 
when it is running dinkum and you need that in order to install the skill.  In addition, Dinkum depends on the Mycroft servers which no longer exist.

So now:
This is a skill to teach Mycroft how to send commands to the Hubitat Elevation Zigbee/ZWave hub based on spoken commands.  It should work with newer Hubitat models but I have
not tried it.  This skill can deal with any Hubitat device that is enabled in the Hubitat "Maker" app and which has commands "on", "off" or "setLevel".  This includes essentially any switched outlets, lights,
dimmers, and scene activators.  It can also read some attributes, although allowed attributes must be specified in settings.

You can also ask it to scan for new devices that Hubitat has made available to it, and you can list the devices it knows (but that takes a while for Mycroft to speak).

The device name that you speak to Mycroft is the device label you have specified in Hubitat, but the skill uses "fuzzywuzzy" to allow some leeway in what you say.

There are six configuration settings for this skill (which you set in a config file for Neon).  You *must* specify the access token and the API number, both of which can be found by looking at the Hubitat "Maker" app. (Look at the example URLs.  The API number follows "api" and the access token follows "access_token"  The Hubitat address defaults to hubitat.local, but for some reason, the .local domain does not work on Neon/OVOS so you should really set a reservation for the Hubitat and then specify the numeric address you chose (e.g. 192.168.2.3).  You can also specify a 'score' between 0 and 100 for comparing the device name you speak to the Hubitat label.  For example, if the label is 'bookcase lights' you can say 'the bookcase lights', 'bookcase light', 'lights on the bookcase', etc.  A score of 65 seems to work well.

This skill can read attributes as well, but you must specify both the name of the attribute and the Hubitat label of the device in settings.  In the "attr" setting, include a comma-separated list of attributes with quotes, for example "temperature","heatingSetPoint","level".  In the device setting, enter a comma-separated list of default devices that match the attributes order.  For example, "thermostat","thermostat","overhead lights".  The your utterance can include the device, especially if more than one device has the same attribute.  Notice that these are hard intents to define because it is common to speak differently depending on the attribute.

## Examples
* "Turn on the bookcase lights"
* "Turn off bookcase light"
* "Set the overhead light to 50%"
* "Scan for new devices"
* "Set overnight mode"
* "Show me the inside temperature"
* "tell me the level of the window lights"

## Credits
* Burns Fisher (@burnsfisher) -- Initial code and maintainer
* LC Style (@GonzRon) -- Update, improve, and generalize
* Mike Gray (@mikejgray) -- Lots of help with Neon/OVOS software.

## Installation Instructions (Work in progress)
I have successfully made this work on both Picroft and on Mycroft MkII hardware with Neon/OVOS software.

Here is the process for installing on Neon/OVOS 23.12.28.  Hopefully newer versions will be compatible  I assume you have a MkII hardware with a Neon flash drive or better with an SSD drive.

Next ssh to the MkII (if you have not done it before, ssh neon@neon.local, password neon.  You must change it and re-ssh)

Now use nano or vim or whatever editor you want to edit the file ~/.config/neon/neon.yaml so that it looks like this:
```
skills:
  default_skills:
  - git+https://github.com/burnsfisher/hubitat-integration-skill
  - ovos-tts-plugin-server==0.0.2a12
  - ovos-stt-plugin-server==0.0.4a7  
  blacklisted_skills:
  - skill-ovos-setup.openvoiceos
  - skill-messaging.neongeckocom
  - skill-custom_conversation.neongeckocom
  - skill-instructions.neongeckocom
  - skill-audio_record.neongeckocom
  - mycroft-wiki.mycroftai
  - neon_homeassistant_skill.mikejgray
```
Reboot the system (do not power cycle it!) using the command "sudo reboot now"

After it reboots, ssh in again and use the command

```
cd ~/.config/neon
```

Now use nano or vim or whatever editor you want to edit settings.json.  It should initially
have only one line surrounded by braces.  Add extra lines so it looks like this:
```
cd ~/.config/neon/skills/hubitat-integration-skill.burnsfisher

{
    "__mycroft_skill_firstrun": false,
    "access_token": "xxxxxxxx",
    "local_address": "xxxxxxx",
    "minimum_fuzzy_score": 62,
    "hubitat_maker_api_app_id": xxx,
    "attr_name": "'temperature','heatingSetpoint','level'",
    "dev_name": "'thermostat','thermostat','overhead lights'"
}

```

You will need to get the access_token and the hubitat maker app ID from hubitat itself.  The access token is
a long series of numbers and letters, while the app id should be an integer.  The local address needs to be
a dotted quad (e.g. 192.168.1.2) which hubitat will also tell you.  Hubitat.local will not work for some
reason on Neon.  You must be VERY careful to get settings.json to work correctly.  If the hubitat skill does not work
look back at this file.  If your hubitat lines have been deleted, there was a syntax error.  (Check for closing 
braces, parens, and be sure to add a comma after all but the last text line).  I've also found bizzare things that
go wrong...maybe and extra end-line character, maybe an extra space?  Reported to the Neon/OVOS guys.  

Now restart the Neon software using

sudo systemctl restart neon

Or you can also say:

sudo reboot now

(Do not just power cycle it).

The hubitat integration skill may work immediately, or you might need to give the command "scan for new devices".

## Category
**IoT**

## Tags
#hubitat
#zigbee
#zwave
