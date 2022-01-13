Feature: on-off
   Scenario: Device does not exist
     Given an english speaking user
       When the user says "turn on nothing"
       Then "hubitat-integration" should reply with dialog from "device.not.supported"
   Scenario: Turning on a device
     Given an english speaking user
        When the user says "turn on testOnDev"
        Then "hubitat-integration" should reply with dialog from "ok"
   Scenario: Try turning off a device that can't be turned off
     Given an english speaking user
        When the user says "turn off testOnDev"
        Then "hubitat-integration" should reply with dialog from "command.not.supported"
   Scenario: Turning off a device
     Given an english speaking user
        When the user says "turn off testOffDev"
        Then "hubitat-integration" should reply with dialog from "ok"


