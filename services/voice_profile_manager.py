from models.voice_profile import VoiceProfile


class VoiceProfileManager:

    def __init__(self, config):

        self.profiles = config.voice_profiles

    def get_profile(self, message) -> VoiceProfile:

        if message.is_broadcaster:
            return self.profiles.get(
                "broadcaster",
                self.profiles["default"]
            )

        if message.is_mod:
            return self.profiles.get(
                "moderator",
                self.profiles["default"]
            )

        if message.is_vip:
            return self.profiles.get(
                "vip",
                self.profiles["default"]
            )

        if message.is_subscriber:
            return self.profiles.get(
                "subscriber",
                self.profiles["default"]
            )

        return self.profiles["default"]