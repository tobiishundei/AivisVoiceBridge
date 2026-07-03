"""
チャットメッセージに応じて読み上げ用 VoiceProfile を選択する。

配信者、モデレーター、VIP、サブスクライバーなどの属性に応じて、
config.json で定義された音声プロファイルを返す。
"""

from models.voice_profile import VoiceProfile


class VoiceProfileManager:
    """
    ユーザー属性に応じて VoiceProfile を選択するクラス。
    """

    def __init__(self, config):
        self.profiles = config.voice_profiles

    def get_profile(self, message) -> VoiceProfile:
        """
        メッセージ送信者の属性に応じた VoiceProfile を返す。

        優先順位:
            broadcaster
            moderator
            vip
            subscriber
            default
        """

        if message.is_broadcaster:
            return self._get_profile(
                "broadcaster"
            )

        if message.is_mod:
            return self._get_profile(
                "moderator"
            )

        if message.is_vip:
            return self._get_profile(
                "vip"
            )

        if message.is_subscriber:
            return self._get_profile(
                "subscriber"
            )

        return self._get_default_profile()

    def _get_profile(self, name: str) -> VoiceProfile:
        """
        指定名の VoiceProfile を返す。

        存在しない場合、または enabled=False の場合は default を返す。
        """

        profile = self.profiles.get(name)

        if not profile:
            return self._get_default_profile()

        if not profile.enabled:
            return self._get_default_profile()

        return profile

    def _get_default_profile(self) -> VoiceProfile:
        """
        default VoiceProfile を返す。
        """

        return self.profiles["default"]