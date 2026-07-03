"""
アプリ内部で使う共通チャットメッセージモデル。

Twitch のイベント構造に直接依存しない形に変換してから、
フィルター、読み上げポリシー、音声キューへ渡す。
"""

from dataclasses import dataclass
from dataclasses import field


@dataclass(slots=True)
class ChatMessage:
    """
    配信チャット1件分の共通データ。
    """

    #
    # Basic message data
    #
    user_id: str
    user_name: str
    text: str

    #
    # User display data
    #
    color: str = ""
    badges: list[str] = field(default_factory=list)

    #
    # User roles
    #
    is_broadcaster: bool = False
    is_mod: bool = False
    is_vip: bool = False
    is_subscriber: bool = False

    #
    # Message attributes
    #
    is_reply: bool = False
    is_first_message: bool = False

    #
    # Platform-specific extras
    #
    emotes: list[str] = field(default_factory=list)