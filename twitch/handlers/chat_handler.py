"""
Twitch のチャットイベントを処理するハンドラー。

Twitch固有のイベントデータをアプリ内部の ChatMessage に変換し、
辞書置換、テキスト整形、読み上げ判定を通した上で SpeechQueue に渡す。
"""

from filters.text_filter import TextFilter
from models.chat_message import ChatMessage


class ChatHandler:
    """
    Twitchチャットメッセージを読み上げキューへ流すクラス。
    """

    def __init__(
        self,
        logger,
        queue,
        dictionary,
        policy,
    ):
        self.logger = logger
        self.queue = queue
        self.dictionary = dictionary
        self.policy = policy
        self.filter = TextFilter()

    async def on_chat(self, data):
        """
        Twitch EventSub のチャットメッセージイベントを処理する。
        """

        message = self._create_message(
            data.event
        )

        message.text = self.dictionary.process(
            message.text
        )

        message = self.filter.filter(
            message
        )

        allowed, reason = self.policy.should_read(
            message
        )

        if not allowed:
            self.logger.info(
                f"Skip: {reason} ({message.user_name})"
            )

            return

        await self.queue.put(message)

    def _create_message(self, event) -> ChatMessage:
        """
        Twitchのイベントデータから ChatMessage を作成する。
        """

        badges = self._extract_badges(event)
        emotes = self._extract_emotes(event)

        return ChatMessage(
            user_id=event.chatter_user_id,
            user_name=event.chatter_user_name,
            text=event.message.text,
            color=event.color or "",
            badges=badges,
            is_broadcaster="broadcaster" in badges,
            is_mod="moderator" in badges,
            is_vip="vip" in badges,
            is_subscriber="subscriber" in badges,
            is_reply=event.reply is not None,
            is_first_message=False,
            emotes=emotes,
        )

    def _extract_badges(self, event) -> list[str]:
        """
        TwitchイベントからバッジIDの一覧を取り出す。
        """

        if not event.badges:
            return []

        return [
            badge.set_id
            for badge in event.badges
        ]

    def _extract_emotes(self, event) -> list[str]:
        """
        Twitchイベントからエモート文字列の一覧を取り出す。
        """

        return [
            fragment.text
            for fragment in event.message.fragments
            if fragment.type == "emote"
        ]