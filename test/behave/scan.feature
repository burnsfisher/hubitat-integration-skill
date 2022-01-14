Feature: Scan for new devices
   Scenario: Request a device update
     Given an english speaking user
        When the user says "check for new devices"
        Then "hubitat-integration" should reply with dialog from "rescan"


