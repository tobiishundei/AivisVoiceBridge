from dataclasses import dataclass, field


@dataclass(slots=True)
class ChatMessage:
    """
    アプリ内部で使用する共通チャットデータ

    Twitch固有のイベント構造には依存しない。
    """

    # 基本情報
    user_id: str
    user_name: str
    text: str

    # ユーザー情報
    color: str = ""

    badges: list[str] = field(default_factory=list)

    # 権限
    is_broadcaster: bool = False
    is_mod: bool = False
    is_vip: bool = False
    is_subscriber: bool = False

    # メッセージ属性
    is_reply: bool = False
    is_first_message: bool = False

    # 将来用
    emotes: list[str] = field(default_factory=list)