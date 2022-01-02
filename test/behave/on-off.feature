Feature: on-off
   Scenario: Device does not exist
     Given an english speaking user
       When the user says "turn on nothing"
       Then "hubitat-integration" should reply with dialog from "device.not.supported"
   Scenario: Turning on a device
     Given an english speaking user
        When the user says "turn on test on dev"
        Then "hubitat-integration" should reply with dialog from "ok"
   Scenario: Try turning off a device that can't be turned off
     Given an english speaking user
        When the user says "turn off test on dev"
        Then "hubitat-integration" should reply with dialog from "command.not.supported"
   Scenario: Try setting the brightness on a device that supports it
     Given an english speaking user
        When the user says "set test level dev to 60 percent"
        Then "hubitat-integration" should reply with dialog from "ok"
   Scenario: Request a device update
     Given an english speaking user
        When the user says "check for new devices"
        Then "hubitat-integration" should reply with dialog from "rescan"


