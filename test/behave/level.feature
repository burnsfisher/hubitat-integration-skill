Feature: level
   Scenario: Device does not exist
     Given an english speaking user
       When the user says "set nothing to 65 percent"
       Then "hubitat-integration" should reply with dialog from "device.not.supported"
   Scenario: Setting a device that has no level setting
     Given an english speaking user
        When the user says "set testOnDev to 65 percent"
        Then "hubitat-integration" should reply with dialog from "command.not.supported"
   Scenario: Try setting the brightness on a device that supports it
     Given an english speaking user
        When the user says "set testLevelDev to 60 percent"
        Then "hubitat-integration" should reply with dialog from "ok"


