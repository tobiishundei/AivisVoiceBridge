# AivisVoiceBridge

AivisVoiceBridge は、Twitch のチャットコメントを AivisSpeech Engine または VOICEVOX Engine で読み上げるアプリです。

Linux / PipeWire 環境では、読み上げ音声を OBS Studio に個別の音声ソースとして渡せます。

Web UIから音声エンジン、話者、読み上げ、Twitch、辞書などの設定を管理できます。

## 現在のバージョン

```text
v1.1.0
```

## 主な機能

* Twitchチャットコメントの受信
* AivisSpeech Engineによる音声合成
* VOICEVOX Engineによる音声合成
* TTSエンジンの切り替え
* PipeWire / `pw-play` による音声出力
* OBS Studioでの読み上げ音声の個別キャプチャ
* 読み上げキュー
* 配信者、モデレーター、VIP、サブスクライバー別の音声プロファイル
* 話速、音高、音量の調整
* 辞書による読み替え
* URL、笑い、拍手、句読点などの読み上げ向け整形
* 読み上げスキップ判定

  * 空メッセージ
  * URLのみ
  * 長文
  * 同一ユーザーの連投クールダウン
* ローカルWeb設定画面

## Web UI

AivisVoiceBridge v1.1.0では、ブラウザから設定を管理できます。

### Web UIで設定できる項目

* AivisSpeech Engine / VOICEVOX Engineの切り替え
* 音声エンジンのホストとポート
* 音声エンジンへの接続確認
* 話者とスタイルの選択
* 話速、音高、音量
* 選択した音声のテスト再生
* ユーザー種別ごとの音声プロファイル

  * 通常ユーザー
  * 配信者
  * モデレーター
  * VIP
  * サブスクライバー
* 最大読み上げ文字数
* 読み上げ間隔
* URLだけのコメントを無視
* 空コメントを無視
* Twitchチャンネル名
* Twitch OAuth Redirect URI
* Twitch認証状態
* Twitch再認証の準備
* ゲーム辞書の選択
* 辞書ファイル数、登録語数、JSONエラーの確認

### Web UIの起動

AivisVoiceBridge本体とは別のターミナルで起動します。

```bash
python -m webui.app
```

ブラウザで次を開きます。

```text
http://127.0.0.1:17564
```

Web UIは `127.0.0.1` で起動するため、通常は同じPCからだけアクセスできます。

Flaskの開発用サーバーに関する警告が表示されますが、ローカル専用の設定画面として使う場合は問題ありません。

## 必要環境

* Python 3.14以上
* AivisSpeech EngineまたはVOICEVOX Engine
* PipeWire
* `pw-play`
* OBS Studio
* obs-pipewire-audio-captureプラグイン

VOICEVOX Engineだけを使う場合、AivisSpeech Engineは必須ではありません。

## セットアップ

### リポジトリを取得

```bash
git clone https://github.com/tobiishundei/AivisVoiceBridge.git
cd AivisVoiceBridge
```

### Python仮想環境

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

### 設定ファイルの作成

サンプル設定をコピーします。

```bash
cp settings/config.json.example settings/config.json
```

`settings/config.json` に、Twitch Developer Consoleで取得した次の情報を設定します。

* `client_id`
* `client_secret`
* Twitchチャンネル名

`settings/config.json` は秘密情報を含むためGit管理されません。

## Twitchアプリの準備

Twitch Developer Consoleでアプリを作成します。

設定例:

```text
OAuth Redirect URL:
http://localhost:17563
```

Twitch Developer Consoleに登録するRedirect URLと、`settings/config.json` の `redirect_uri` は完全に同じ値にしてください。

初回起動時にブラウザ認証が開始され、認証情報は次へ保存されます。

```text
tokens/user_token.json
```

トークンやClient SecretはGitHubへ公開しないでください。

## 起動方法

### 通常起動

```bash
python main.py
```

初回起動時またはトークンがない場合は、Twitchのブラウザ認証が開始されます。

### Web UI

```bash
python -m webui.app
```

### OBS初回設定用の音声テスト

```bash
python main.py --audio-test
```

`--audio-test` はTwitchには接続せず、音声エンジンと音声出力だけを使用します。

OBS側でAivisVoiceBridgeのPipeWire音声ノードを選択しやすいよう、通常より長いテスト音声を再生します。

## TTSエンジン

対応しているバックエンド:

* `aivis`
* `voicevox`

設定はWeb UIから切り替えられます。

設定ファイルを直接編集する場合は、`tts.backend` を変更します。

### AivisSpeech Engine

```json
"tts": {
  "backend": "aivis"
},
"aivis": {
  "host": "127.0.0.1",
  "port": 10101
}
```

### VOICEVOX Engine

```json
"tts": {
  "backend": "voicevox"
},
"voicevox": {
  "host": "127.0.0.1",
  "port": 50021
}
```

AivisSpeech EngineとVOICEVOX Engineでは、話者・スタイルIDが異なります。

バックエンドを切り替えた場合は、そのエンジンに存在する話者とスタイルをWeb UIから選び直してください。

## 音声プロファイル

ユーザー種別ごとに異なる音声設定を使用できます。

対応しているプロファイル:

* `default`
* `broadcaster`
* `moderator`
* `vip`
* `subscriber`

判定の優先順位:

1. broadcaster
2. moderator
3. vip
4. subscriber
5. default

設定例:

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

各値の意味:

* `speaker`: 音声エンジン側の話者・スタイルID
* `speed`: 話速
* `pitch`: 音高
* `volume`: 音量
* `enabled`: この音声プロファイルを有効にするか

これらはWeb UIから設定できます。

## 読み上げ基本設定

```json
"speech": {
  "max_length": 120,
  "cooldown": 3.0,
  "skip_url_only": true,
  "skip_empty": true
}
```

* `max_length`: 最大読み上げ文字数
* `cooldown`: 同一ユーザーの連続コメントに対する待機時間
* `skip_url_only`: URLだけのコメントを読み上げない
* `skip_empty`: フィルター後に空になったコメントを読み上げない

これらもWeb UIから変更できます。

## 辞書

辞書は `dictionaries/` 以下に配置します。

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

読み込み順:

1. `dictionaries/common`
2. `dictionaries/game/<game_dictionary>`
3. `dictionaries/personal`

後から読み込まれた辞書が、同じキーを上書きします。

そのため、優先順位は次のとおりです。

```text
personal > game > common
```

辞書ファイルの形式:

```json
{
  "クリーパー": "くりーぱー",
  "ネザライト": "ネザーライト"
}
```

Web UIでは次を確認できます。

* 利用可能なゲーム辞書
* 選択中のゲーム辞書
* JSONファイル数
* 登録語数
* 統合後の有効語数
* JSON形式や値のエラー

辞書の単語追加・削除は、現在はJSONファイルを直接編集します。

## Twitch再認証

Web UIにはTwitch認証状態が表示されます。

再認証する場合は、次の順番で操作してください。

1. `python main.py` で動いている本体を停止
2. Web UIで「再認証の準備をする」を押す
3. AivisVoiceBridge本体を再起動
4. ブラウザでTwitch認証を完了

以前のトークンは次のような名前で退避されます。

```text
tokens/user_token.json.reauth-backup
```

Web UIにはアクセストークンやClient Secretは表示されません。

## OBS Studioで読み上げ音声を個別キャプチャする

AivisVoiceBridgeはLinux / PipeWire環境で `pw-play` を使用します。

OBS Studioでは、obs-pipewire-audio-captureプラグインを使うことで、AivisVoiceBridgeの音声だけを個別ソースとして扱えます。

### `pw-play` の確認

```bash
which pw-play
```

正常な例:

```text
/usr/bin/pw-play
```

### AivisVoiceBridge側の設定

```json
"audio": {
  "backend": "pipewire",
  "app_name": "AivisVoiceBridge",
  "media_role": "Communication"
}
```

### OBS初回設定

OBS Studioを起動した状態で、次を実行します。

```bash
python main.py --audio-test
```

テスト音声が再生されている間に、OBSで次を設定します。

1. ソースを追加
2. `Application Audio Capture (PipeWire)` を選択
3. アプリケーション一覧から `AivisVoiceBridge` を選択
4. 音声メーターが反応することを確認

読み上げ音声のノードは、音声再生中だけPipeWire上に表示される場合があります。

初回設定では、通常起動より `--audio-test` の使用をおすすめします。

## プロジェクト構成

```text
.
├── audio/        # 音声出力バックエンド
├── commands/     # CLI用コマンド
├── core/         # 設定とアプリケーション管理
├── dictionaries/ # 読み替え辞書
├── filters/      # テキスト正規化
├── models/       # 共通データモデル
├── services/     # 辞書、ポリシー、音声プロファイル
├── speech/       # 読み上げキューとワーカー
├── tts/          # TTSエンジン
├── twitch/       # Twitch接続とイベント処理
├── webui/        # ローカルWeb設定画面
├── VERSION
├── main.py
└── requirements.txt
```

## トラブルシューティング

### Twitchコメントが読まれない

ログに次のような表示がないか確認してください。

```text
Skip: cooldown
Skip: url_only
Skip: too_long
```

それぞれ、連投制限、URLのみ、最大文字数によるスキップです。

### 音声エンジンに接続できない

Web UIから次を確認してください。

* 選択しているTTSエンジン
* ホスト
* ポート
* 音声エンジンが起動しているか

標準ポート:

```text
AivisSpeech Engine: 10101
VOICEVOX Engine:    50021
```

### 話者が想定と異なる

AivisSpeech EngineとVOICEVOX Engineでは、同じ数値のIDでも別の話者を指す場合があります。

Web UIで接続中のエンジンから話者一覧を取得し、話者とスタイルを選び直してください。

### OBSのアプリ一覧に表示されない

次を実行します。

```bash
python main.py --audio-test
```

テスト音声が流れている間に、OBS側で `AivisVoiceBridge` を選択してください。

### `Unclosed client session` が表示される

終了処理が正しく通らなかった可能性があります。

通常は起動したターミナルで `Ctrl+C` を押し、`Application.stop()` を通して終了してください。

### Web UIでFlaskの警告が表示される

次の警告は、Flask内蔵サーバーが本番Webサービス向けではないことを示しています。

```text
WARNING: This is a development server.
```

AivisVoiceBridgeのWeb UIは `127.0.0.1` で動くローカル専用画面として使用するため、通常は問題ありません。

インターネットへ公開しないでください。

## v1.1.0で追加された機能

* ローカルWeb設定画面
* AivisSpeech / VOICEVOX切り替え
* 音声エンジン接続確認
* 話者・スタイル一覧取得
* 話者・スタイル選択
* テスト読み上げ
* 話速・音高・音量設定
* ユーザー種別ごとの音声プロファイル編集
* 読み上げ基本設定
* Twitchチャンネル設定
* Twitch認証状態表示
* Twitch再認証準備
* ゲーム辞書選択
* 辞書ファイル状態と登録語数表示
* 設定ファイルの自動バックアップ

## 今後の候補

* 辞書のブラウザ編集
* 音声出力設定のWeb UI化
* フィルタールールのON/OFF
* AivisSpeechとVOICEVOXの同時利用
* ユーザーごとの個別音声
* Web UIからの本体起動・停止
* Windows向け導入方法の整備

## ライセンス

AivisVoiceBridge本体はMIT Licenseで公開しています。

AivisSpeech Engine、VOICEVOX Engine、各音声モデル、音声ライブラリ、OBS Studio、obs-pipewire-audio-captureなどの外部ソフトウェアは、それぞれのライセンスや利用規約に従ってください。

本リポジトリには次のものを含めません。

* TTSエンジン本体
* 音声モデル
* Twitchトークン
* Client Secretを含む個人設定
* 個人用辞書

## 謝辞

OBS StudioでのPipeWireアプリ別音声キャプチャには、obs-pipewire-audio-captureプラグインを利用しています。

AivisVoiceBridgeの音声をOBS上で個別ソースとして扱える仕組みを提供している開発者の方に感謝します。
