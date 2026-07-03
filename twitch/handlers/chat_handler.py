from filters.text_filter import TextFilter
from models.chat_message import ChatMessage


class ChatHandler:

    def __init__(
        self,
        logger,
        queue,
        dictionary,
        policy
    ):

        self.logger = logger
        self.queue = queue
        self.filter = TextFilter()
        self.policy = policy

        self.dictionary = dictionary
                
    async def on_chat(self, data):

        event = data.event

        badges = []

        if event.badges:
            badges = [
                badge.set_id
                for badge in event.badges
            ]

        message = ChatMessage(

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

            emotes=[
                fragment.text
                for fragment in event.message.fragments
                if fragment.type == "emote"
            ]
        )

        #
        # 辞書置換
        #
        message.text = self.dictionary.process(
            message.text
        )

        #
        # テキスト整形
        #
        message = self.filter.filter(message)

        #
        # 読み上げ判定
        #
        allowed, reason = self.policy.should_read(
            message
        )

        if not allowed:

            self.logger.info(
                f"Skip: {reason} ({message.user_name})"
            )

            return
        #
        # Queueへ
        #
        await self.queue.put(message)