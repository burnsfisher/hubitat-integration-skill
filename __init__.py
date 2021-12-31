from mycroft import MycroftSkill, intent_file_handler


class HubitatIntegration(MycroftSkill):
    def __init__(self):
        MycroftSkill.__init__(self)

    @intent_file_handler('integration.hubitat.intent')
    def handle_integration_hubitat(self, message):
        self.speak_dialog('integration.hubitat')


def create_skill():
    return HubitatIntegration()

