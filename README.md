# <img src='https://raw.githack.com/FortAwesome/Font-Awesome/master/svgs/solid/home.svg' card_color='#408BDB' width='50' height='50' style='vertical-align:bottom'/> Hubitat Integration
Use Mycroft for Home Automation with Hubitat Hub

## About
This is a skill to teach Mycroft how to send commands to the Hubitat Zigbee/ZWave hub based on spoken  commands.  This skill can deal with any Hubitat device that is enabled in the Hubitat "Maker" app and which has commands "on", "off" or "setLevel".  This includes essentially any switched outlets, lights,
dimmers, and scene activators.

You can also ask it to scan for new devices that Hubitat has made available to it, and you can list the devices it knows (but that takes a while for Mycroft to speak).

The device name that you speak to Mycroft is the device label you have specified in Hubitat, but the skill uses "fuzzywuzzy" to allow some leeway in what you say.

There are three settings for this skill (which you set via your Mycroft account).  You *must* specify the access token, which can be found by looking at the Hubitat "Maker" app.  The Hubitat address defaults to hubitat.local, which should work unless you have multiple hubitats on the LAN or for some other reason .local names are not supported.  You can also specify a 'score' between 0 and 100 for comparing the device name you speak to the Hubitat label.  For example, if the label is 'bookcase lights' you can say 'the bookcase lights', 'bookcase light', 'lights on the bookcase', etc.  A score of 65 seems to work well.

## Examples
* "Turn on the bookcase lights"
* "Turn off bookcase light"
* "Set the overhead light to 50%"
* "Scan for new devices"
* "Set overnight mode"

## Credits
Burns Fisher (@burnsfisher)

## Category
**IoT**

## Tags
#hubitat
#zigbee
#zwave
