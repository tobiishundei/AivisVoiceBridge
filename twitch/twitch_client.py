"""
Twitch API / EventSub WebSocket との接続を管理する。

認証、ログインユーザー取得、チャットイベント購読を行い、
受信したチャットメッセージは ChatHandler へ渡す。
"""

from pathlib import Path

from twitchAPI.eventsub.websocket import EventSubWebsocket
from twitchAPI.helper import first
from twitchAPI.oauth import UserAuthenticationStorageHelper
from twitchAPI.twitch import Twitch

from core.config import Config
from twitch.handlers.chat_handler import ChatHandler


TOKEN_DIR = Path("tokens")


class TwitchClient:
    """
    Twitch接続とチャット購読を管理するクライアント。
    """

    def __init__(
        self,
        config: Config,
        logger,
        queue,
        dictionary,
        policy,
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
            policy,
        )

    async def start(self):
        """
        Twitchへ接続し、チャットメッセージ購読を開始する。
        """

        self.logger.info(
            "Connecting to Twitch..."
        )

        TOKEN_DIR.mkdir(
            exist_ok=True
        )

        await self._connect_twitch()
        await self._authenticate_user()
        await self._load_current_user()
        await self._start_eventsub()
        await self._subscribe_chat_messages()

    async def stop(self):
        """
        EventSub WebSocket と Twitch クライアントを停止する。
        """

        if self.eventsub is not None:
            await self.eventsub.stop()
            self.eventsub = None

        if self.twitch is not None:
            await self.twitch.close()
            self.twitch = None

    async def _connect_twitch(self):
        """
        Twitch API クライアントを作成する。
        """

        self.twitch = await Twitch(
            self.config.client_id,
            self.config.client_secret,
        )

    async def _authenticate_user(self):
        """
        ユーザー認証を行い、トークンを保存・再利用できるようにする。
        """

        helper = UserAuthenticationStorageHelper(
            self.twitch,
            self.config.scopes,
            storage_path=Path(
                self.config.token_file
            ),
        )

        await helper.bind()

    async def _load_current_user(self):
        """
        認証済みユーザー情報を取得する。
        """

        self.user = await first(
            self.twitch.get_users()
        )

        self.logger.info(
            "Connected!"
        )

        self.logger.info(
            f"Logged in as : {self.user.display_name}"
        )

        self.logger.info(
            f"User ID      : {self.user.id}"
        )

    async def _start_eventsub(self):
        """
        EventSub WebSocket を開始する。
        """

        self.eventsub = EventSubWebsocket(
            self.twitch
        )

        self.eventsub.start()

        self.logger.info(
            "EventSub WebSocket started."
        )

    async def _subscribe_chat_messages(self):
        """
        チャットメッセージイベントを購読する。
        """

        subscription_id = (
            await self.eventsub.listen_channel_chat_message(
                self.user.id,
                self.user.id,
                self.chat_handler.on_chat,
            )
        )

        self.logger.info(
            f"Chat subscription registered ({subscription_id})"
        )