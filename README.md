cat > README.md <<'EOF'
# AivisVoiceBridge

AivisVoiceBridge は、Twitch のチャットコメントを AivisSpeech Engine で読み上げ、Linux / PipeWire 環境で OBS Studio に個別音声ソースとして渡すための読み上げアプリです。

## 主な機能

- Twitch チャットコメントの受信
- AivisSpeech Engine による音声合成
- PipeWire / `pw-play` による音声出力
- OBS Studio で読み上げ音声だけを個別キャプチャ
- 配信者、モデレーター、VIP、サブスクライバー別の音声プロファイル
- 辞書による読み替え
- URL、省略表現、笑い、拍手、句読点の読み上げ向け整形
- 読み上げスキップ判定
  - 空メッセージ
  - URLのみ
  - 長文
  - 同一ユーザーの連投 cooldown

## 必要環境

- Python 3.14+
- AivisSpeech Engine
- PipeWire
- `pw-play`
- OBS Studio
- obs-pipewire-audio-capture プラグイン

## セットアップ

### Python 仮想環境

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 設定ファイルの作成

`settings/config.json.example` をコピーして、実際の設定ファイルを作成します。

```bash
cp settings/config.json.example settings/config.json
```

`settings/config.json` に Twitch の `client_id`、`client_secret`、チャンネル名などを設定します。

`settings/config.json` は秘密情報を含むため Git 管理しません。

## 起動方法

通常起動:

```bash
python main.py
```

OBS 初回設定用の音声テスト:

```bash
python main.py --audio-test
```

`--audio-test` は Twitch には接続せず、AivisSpeech Engine と音声出力だけを使って長めのテスト音声を再生します。

## OBS Studio で読み上げ音声を個別キャプチャする

AivisVoiceBridge は Linux / PipeWire 環境では `pw-play` を使って音声を出力します。

OBS Studio では `obs-pipewire-audio-capture` プラグインを使うことで、AivisVoiceBridge の読み上げ音声だけを個別の音声ソースとして扱えます。

### 必要なもの

- PipeWire
- `pw-play`
- OBS Studio
- obs-pipewire-audio-capture プラグイン

`pw-play` が使えるか確認します。

```bash
which pw-play
```

以下のように表示されればOKです。

```text
/usr/bin/pw-play
```

### AivisVoiceBridge 側の設定

`settings/config.json` の `audio` を以下のように設定します。

```json
"audio": {
  "backend": "pipewire",
  "app_name": "AivisVoiceBridge",
  "media_role": "Communication"
}
```

`app_name` は OBS 側で認識されるアプリ名です。

一度 OBS 側で選択した後に `app_name` を変更すると、OBS 側で再設定が必要になる場合があります。

### OBS の初回設定

OBS Studio を起動します。

次に、AivisVoiceBridge の音声テストを実行します。

```bash
python main.py --audio-test
```

テスト音声が再生されている間に、OBS Studio で以下を設定します。

1. ソースを追加
2. `Application Audio Capture (PipeWire)` を選択
3. アプリケーション一覧から `AivisVoiceBridge` を選択
4. 音声メーターが反応することを確認

テスト音声は、OBS 側でアプリケーションを選択できるように少し長めに再生されます。

一度 `AivisVoiceBridge` を選択すると、以降は短い読み上げでも OBS 側で認識されます。

### 通常起動時の挙動

```bash
python main.py
```

Twitch コメントが読み上げられると、OBS の `AivisVoiceBridge` ソースだけが反応します。

ブラウザ、ゲーム、デスクトップ音声など、他のアプリケーション音声とは分離して扱えます。

### 動作確認済みの挙動

- AivisVoiceBridge の読み上げ音声だけが OBS の `AivisVoiceBridge` ソースに反応する
- ブラウザなど別アプリの音声には反応しない
- デスクトップ音声を無効にしても、AivisVoiceBridge の読み上げ音声だけを OBS へ送れる
- 初回設定時は `python main.py --audio-test` を使うと選択しやすい

### 注意点

AivisVoiceBridge の音声ノードは、読み上げ中だけ PipeWire 上に表示されます。

そのため、OBS の初回設定時には通常の短いコメント読み上げではなく、以下のテストコマンドを使ってください。

```bash
python main.py --audio-test
```

## 辞書

辞書は `dictionaries/` 以下に配置します。

読み込み順は以下です。

1. `dictionaries/common`
2. `dictionaries/game/<game_dictionary>`
3. `dictionaries/personal`

後から読み込まれた辞書が同じキーを上書きします。

そのため、`personal` 辞書が最も優先されます。

### 構成例

```text
dictionaries/
├── common/
│   └── common.json
├── game/
│   └── minecraft/
│       └── dictionary.json
└── personal/
    └── personal.json
```

## 音声プロファイル

`settings/config.json` の `voices` で、ユーザー種別ごとの音声を設定します。

対応しているプロファイル名:

- `default`
- `broadcaster`
- `moderator`
- `vip`
- `subscriber`

優先順位は以下です。

1. broadcaster
2. moderator
3. vip
4. subscriber
5. default

例:

```json
"voices": {
  "default": {
    "speaker": 888753760,
    "speed": 1.0,
    "pitch": 0.0,
    "volume": 1.0,
    "enabled": true
  }
}
```

`speaker` は AivisSpeech Engine 側の話者・スタイル ID です。

## プロジェクト構成

```text
.
├── audio/        # 音声出力バックエンド
├── commands/     # CLI用コマンド
├── core/         # アプリケーション設定・起動管理
├── dictionaries/ # 読み替え辞書
├── filters/      # テキスト正規化
├── models/       # 共通データモデル
├── services/     # 辞書、読み上げポリシー、音声プロファイル管理
├── speech/       # 音声合成と読み上げキュー
├── twitch/       # Twitch接続とイベント処理
├── main.py
└── requirements.txt
```

## トラブルシューティング

### `pw-play` が見つからない

```bash
which pw-play
```

で確認してください。

見つからない場合は、PipeWire 関連パッケージを確認してください。

### OBS のアプリ一覧に AivisVoiceBridge が出ない

短い読み上げでは、PipeWire ノードがすぐに消えて一覧に出ないことがあります。

初回設定時は以下を実行してください。

```bash
python main.py --audio-test
```

テスト音声が再生されている間に OBS 側で `AivisVoiceBridge` を選択します。

### `Unclosed client session` が出る

アプリの終了処理が正しく通っていない可能性があります。

通常は `Ctrl+C` で終了すれば、`Application.stop()` を通して AivisSpeech Engine との HTTP セッションが閉じられます。

### コメントが読まれない

ログに以下のような `Skip:` が出ていないか確認してください。

```text
Skip: cooldown
Skip: url_only
Skip: too_long
```

それぞれ、連投制限、URLのみ、長文制限によって読み上げがスキップされています。

## v1.0 ロードマップ

- [x] Twitch コメント受信
- [x] AivisSpeech Engine 連携
- [x] PipeWire / OBS 個別音声キャプチャ
- [x] `--audio-test`
- [x] 辞書読み替え
- [x] 音声プロファイル
- [x] 読み上げポリシー
- [ ] TTSエンジン抽象化
- [ ] VOICEVOX Engine 対応
- [ ] README 整備
- [ ] config.json.example 整備

## 今後の予定

v1.0 では、Twitch + AivisSpeech / VOICEVOX + PipeWire + OBS の構成に絞って完成を目指します。

YouTube 連携、GUI化、完全 Docker 化は v1.1 以降の検討対象です。
EOF

cat >> README.md <<'EOF'

## TTSエンジンの切り替え

AivisVoiceBridge は TTS エンジンを切り替えられます。

現在対応しているバックエンド:

- `aivis`
- `voicevox`

### AivisSpeech Engine を使う場合

`settings/config.json` の `tts.backend` を `aivis` にします。

```json
"tts": {
  "backend": "aivis"
},

"aivis": {
  "host": "127.0.0.1",
  "port": 10101
}
```

`voices` の `speaker` には、AivisSpeech Engine 側の話者・スタイル ID を指定します。

### VOICEVOX Engine を使う場合

`settings/config.json` の `tts.backend` を `voicevox` にします。

```json
"tts": {
  "backend": "voicevox"
},

"voicevox": {
  "host": "127.0.0.1",
  "port": 50021
}
```

`voices` の `speaker` には、VOICEVOX Engine 側の speaker/style ID を指定します。

VOICEVOX Engine が起動している状態で、以下のコマンドから利用可能な話者IDを確認できます。

```bash
curl http://127.0.0.1:50021/speakers
```

返ってきた JSON の `styles[].id` が、`settings/config.json` の `speaker` に指定する値です。

### 注意点

AivisSpeech Engine と VOICEVOX Engine では、同じ `speaker` 数値でも別の話者を指す場合があります。

TTSバックエンドを切り替える場合は、`voices` の `speaker` も対応するエンジンのIDに変更してください。
EOF