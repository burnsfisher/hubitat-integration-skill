Feature: Get attributes
   Scenario: Get an attribute from a device that has it
     Given an english speaking user
       When the user says "get testattr from testAttrDev"
       Then "hubitat-integration" should reply with dialog from "attr"
   Scenario: Get an attribute without specifying the device
     Given an english speaking user
        When the user says "tell me the room testattr"
        Then "hubitat-integration" should reply with dialog from "attr"
   Scenario: Get an attribute that does not exist
     Given an english speaking user
        When the user says "tell me the room whatis"
        Then "hubitat-integration" should reply with dialog from "attr.not.supported"
   Scenario: Get an attribute that exists, but specify a device that does not have it
     Given an english speaking user
        When the user says "get testattr from testOnDev"
        Then "hubitat-integration" should reply with dialog from "attr.not.supported"



