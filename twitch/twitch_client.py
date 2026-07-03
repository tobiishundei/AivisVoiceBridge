from pathlib import Path

from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.twitch import Twitch
from twitchAPI.eventsub.websocket import EventSubWebsocket

from core.config import Config
from twitch.handlers.chat_handler import ChatHandler


class TwitchClient:

    def __init__(
        self,
        config: Config,
        logger,
        queue,
        dictionary,
        policy
    ):

        self.config = config
        self.logger = logger

        self.twitch = None
        self.eventsub = None
        self.user = None

        self.chat_handler = ChatHandler(
            logger,
            queue,
            dictionary,
            policy
        )
        
    async def start(self):

        self.logger.info("Connecting to Twitch...")

        Path("tokens").mkdir(exist_ok=True)

        self.twitch = await Twitch(
            self.config.client_id,
            self.config.client_secret
        )

        helper = UserAuthenticationStorageHelper(
            self.twitch,
            self.config.scopes,
            storage_path=Path(self.config.token_file)
        )

        await helper.bind()

        self.user = await first(
            self.twitch.get_users()
        )

        self.logger.info("Connected!")
        self.logger.info(f"Logged in as : {self.user.display_name}")
        self.logger.info(f"User ID      : {self.user.id}")

        self.eventsub = EventSubWebsocket(self.twitch)

        self.eventsub.start()

        self.logger.info("EventSub WebSocket started.")

        #
        # Chat subscription
        #
        subscription_id = await self.eventsub.listen_channel_chat_message(
            self.user.id,
            self.user.id,
            self.chat_handler.on_chat
        )

        self.logger.info(
            f"Chat subscription registered ({subscription_id})"
        )

    async def stop(self):

        if self.eventsub is not None:
            await self.eventsub.stop()

        if self.twitch is not None:
            await self.twitch.close()