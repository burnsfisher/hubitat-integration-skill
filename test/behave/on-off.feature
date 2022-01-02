Feature: on-off
   Scenario: Device does not exist
     Given an english speaking user
       When the user says "turn on nothing"
       Then "hubitat-integration" should reply with dialog from "device.not.supported"
   Scenario: Turning on a real device
     Given an english speaking user
        When the user says "turn on the bookcase lights"
        Then "hubitat-integration" should reply with dialog from "ok"
