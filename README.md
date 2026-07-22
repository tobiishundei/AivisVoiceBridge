# AivisVoiceBridge

AivisVoiceBridge は、Twitch のチャットコメントを AivisSpeech Engine または VOICEVOX Engine で読み上げるアプリです。

WindowsとLinuxに対応し、読み上げ音声をOBS Studioへ個別の音声ソースとして渡せます。

Web UIから音声エンジン、話者、読み上げ、Twitch、辞書などの設定を管理できます。

## 現在のバージョン

```text
v1.3.0
```

## 主な機能

- Twitchチャットコメントの受信
- AivisSpeech Engineによる音声合成
- VOICEVOX Engineによる音声合成
- AivisSpeech EngineとVOICEVOX Engineの同時利用
- 音声プロファイルごとのTTSエンジン切り替え
- Windows / Linux対応
- Pythonプロセス内での常駐音声出力
- 常駐音声出力ウィンドウ
- 簡易レベルメーター
- OBS Studioでの読み上げ音声の個別キャプチャ
- 従来のPipeWire / `pw-play`および`ffplay`出力
- 読み上げキュー
- 配信者、モデレーター、VIP、サブスクライバー別の音声プロファイル
- 話速、音高、音量の調整
- 辞書による読み替え
- URL、笑い、拍手、句読点などの読み上げ向け整形
- 読み上げスキップ判定
  - 空メッセージ
  - URLのみ
  - 長文
  - 同一ユーザーの連投クールダウン
- ローカルWeb設定画面

## Web UI

AivisVoiceBridgeでは、ブラウザから設定を管理できます。

### Web UIで設定できる項目

- AivisSpeech Engine / VOICEVOX Engineの切り替え
- 音声エンジンのホストとポート
- 音声エンジンへの接続確認
- 音声プロファイルごとのTTSエンジン選択
- 話者とスタイルの選択
- 話速、音高、音量
- 選択した音声のテスト再生
- ユーザー種別ごとの音声プロファイル
  - 通常ユーザー
  - 配信者
  - モデレーター
  - VIP
  - サブスクライバー
- 最大読み上げ文字数
- 読み上げ間隔
- URLだけのコメントを無視
- 空コメントを無視
- Twitchチャンネル名
- Twitch OAuth Redirect URI
- Twitch認証状態
- Twitch再認証の準備
- ゲーム辞書の選択
- 辞書ファイル数、登録語数、JSONエラーの確認

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

### 共通

- Python 3.14以上
- AivisSpeech EngineまたはVOICEVOX Engine
- OBS Studio

標準の`persistent`音声出力では、Pythonパッケージの`sounddevice`と`numpy`を使用します。これらは`requirements.txt`からインストールされます。

VOICEVOX Engineだけを使う場合、AivisSpeech Engineは必須ではありません。

AivisSpeech EngineとVOICEVOX Engineを役割ごとに使い分ける場合は、両方の音声エンジンを起動してください。

### Linux

LinuxではPipeWire環境を推奨します。

標準の`persistent`音声出力では、Pythonプロセスから直接音声を再生します。

従来の`pipewire`音声出力を使用する場合は、次も必要です。

- `pw-play`
- obs-pipewire-audio-captureプラグイン

### Windows

WindowsではOBS Studioの「アプリケーション音声キャプチャ」を使用します。

標準の`persistent`音声出力では、`AivisVoiceBridge Audio Output`という常駐ウィンドウが表示されます。

## セットアップ

### リポジトリを取得

```bash
git clone https://github.com/tobiishundei/AivisVoiceBridge.git
cd AivisVoiceBridge
```

### Python仮想環境

#### Linux

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

#### Windows PowerShell

Python 3.14で仮想環境を作成します。

```powershell
py -3.14 -m venv .venv
```

PowerShellでスクリプトの実行が無効になっている場合は、仮想環境を有効にする前に次を実行します。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

`-Scope Process`を指定しているため、設定が有効なのは現在開いているPowerShellだけです。PowerShellを閉じると元に戻ります。

仮想環境を有効にします。

```powershell
.\.venv\Scripts\Activate.ps1
```

必要なパッケージをインストールします。

```powershell
python -m pip install -r requirements.txt
```

### 設定ファイルの作成

#### Linux

```bash
cp settings/config.json.example settings/config.json
```

#### Windows PowerShell

```powershell
Copy-Item .\settings\config.json.example .\settings\config.json
```

`settings/config.json` に、Twitch Developer Consoleで取得した次の情報を設定します。

- `client_id`
- `client_secret`
- Twitchチャンネル名

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

OBS側でAivisVoiceBridgeの音声出力を選択しやすいよう、通常より長いテスト音声を再生します。

## TTSエンジン

対応しているバックエンド:

- `aivis`
- `voicevox`

音声プロファイルごとに使用するTTSエンジンを選択できます。

たとえば、通常ユーザーはAivisSpeech Engine、配信者はVOICEVOX Engineという使い分けが可能です。

```text
default       → AivisSpeech Engine
broadcaster   → VOICEVOX Engine
moderator     → AivisSpeech Engine
```

Web UIでは、役割ごとに次を設定できます。

- 音声エンジン
- 話者
- スタイル
- 話速
- 音高
- 音量
- 有効・無効

### 音声エンジンの接続先

```json
"aivis": {
  "host": "127.0.0.1",
  "port": 10101
},
"voicevox": {
  "host": "127.0.0.1",
  "port": 50021
}
```

AivisSpeech Engineだけを使用する場合は、AivisSpeech Engineだけを起動します。

VOICEVOX Engineだけを使用する場合は、VOICEVOX Engineだけを起動します。

両方のエンジンを音声プロファイルで使用する場合は、AivisSpeech EngineとVOICEVOX Engineの両方を起動してください。

### `tts.backend`について

```json
"tts": {
  "backend": "aivis"
}
```

`tts.backend` は、`voices` 内に `backend` がない旧設定との互換用として残されています。

新しい設定では、実際に使用する音声エンジンは各音声プロファイルの `backend` で決まります。

AivisSpeech EngineとVOICEVOX Engineでは、話者・スタイルIDが異なります。

バックエンドを変更した場合は、そのエンジンに存在する話者とスタイルをWeb UIから選び直してください。

## 音声出力

標準設定では、WindowsとLinuxの両方で利用できる`persistent`バックエンドを使用します。

```json
"audio": {
  "backend": "persistent",
  "app_name": "AivisVoiceBridge",
  "media_role": "Communication"
}
```

### `persistent`

Pythonプロセス内で直接音声を再生します。

AivisVoiceBridgeの起動中は、`AivisVoiceBridge Audio Output`という小さな常駐ウィンドウが表示されます。

ウィンドウには次の情報が表示されます。

- 待機中 / 再生中
- 簡易レベルメーター

音声ストリームは起動中ずっと保持されるため、OBS Studio側でキャプチャ対象が消えません。

### `pipewire`

Linux向けの従来バックエンドです。

```json
"audio": {
  "backend": "pipewire",
  "app_name": "AivisVoiceBridge",
  "media_role": "Communication"
}
```

`pw-play`を使用して音声を再生します。読み上げごとに音声プロセスが起動・終了します。

### `ffplay`

FFmpegの`ffplay`を使用するフォールバック用バックエンドです。

```json
"audio": {
  "backend": "ffplay",
  "app_name": "AivisVoiceBridge",
  "media_role": "Communication"
}
```

通常は`persistent`の利用を推奨します。

## OBS Studioで読み上げ音声を個別キャプチャする

### Linux

AivisVoiceBridgeを起動します。

```bash
python main.py
```

OBS Studioで次を設定します。

1. ソースを追加
2. `Application Audio Capture (PipeWire)`を選択
3. アプリケーション一覧からPythonの音声出力を選択
4. 音声メーターが反応することを確認

環境によっては、次のような名前で表示されます。

```text
PipeWire ALSA [python3.14]
```

`persistent`バックエンドは音声ストリームを常時保持するため、音声が再生されていない待機中でも選択できます。

### Windows

AivisVoiceBridgeを起動します。

```powershell
python main.py
```

OBS Studioで次を設定します。

1. ソースを追加
2. 「アプリケーション音声キャプチャ」を選択
3. 次のウィンドウを選択

```text
[python.exe]:AivisVoiceBridge Audio Output
```

ウィンドウの照合方法は、次を推奨します。

```text
ウィンドウのタイトルに一致する必要があります
```

ウィンドウタイトルは固定されているため、別のPythonアプリを誤って選びにくくなります。

次の照合方法でも動作を確認しています。

- タイトルに一致、そうでなければ同じ種類のウィンドウを見つける
- タイトルに一致、そうでなければ実行可能なファイルのウィンドウを見つける

### 音声テスト

OBSの音声メーターを確認する場合は、次を実行します。

```bash
python main.py --audio-test
```

## 音声プロファイル

ユーザー種別ごとに異なる音声設定を使用できます。

対応しているプロファイル:

- `default`
- `broadcaster`
- `moderator`
- `vip`
- `subscriber`

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
    "backend": "aivis",
    "speaker": 888753760,
    "speed": 1.0,
    "pitch": 0.0,
    "volume": 1.0,
    "enabled": true
  },
  "broadcaster": {
    "backend": "voicevox",
    "speaker": 3,
    "speed": 1.0,
    "pitch": 0.0,
    "volume": 1.0,
    "enabled": true
  }
}
```

各値の意味:

- `backend`: 使用する音声エンジン
- `speaker`: 音声エンジン側の話者・スタイルID
- `speed`: 話速
- `pitch`: 音高
- `volume`: 音量
- `enabled`: この音声プロファイルを有効にするか

`backend` を省略した旧設定では、`tts.backend` の値が自動的に使用されます。

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

- `max_length`: 最大読み上げ文字数
- `cooldown`: 同一ユーザーの連続コメントに対する待機時間
- `skip_url_only`: URLだけのコメントを読み上げない
- `skip_empty`: フィルター後に空になったコメントを読み上げない

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

- 利用可能なゲーム辞書
- 選択中のゲーム辞書
- JSONファイル数
- 登録語数
- 統合後の有効語数
- JSON形式や値のエラー

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

- 選択しているTTSエンジン
- ホスト
- ポート
- 音声エンジンが起動しているか

標準ポート:

```text
AivisSpeech Engine: 10101
VOICEVOX Engine:    50021
```

### 話者が想定と異なる

AivisSpeech EngineとVOICEVOX Engineでは、同じ数値のIDでも別の話者を指す場合があります。

Web UIで接続中のエンジンから話者一覧を取得し、話者とスタイルを選び直してください。

### OBSのアプリ一覧に表示されない

`audio.backend`が`persistent`になっていることを確認します。

```json
"audio": {
  "backend": "persistent",
  "app_name": "AivisVoiceBridge",
  "media_role": "Communication"
}
```

AivisVoiceBridgeを起動すると、常駐音声ウィンドウと音声ストリームが作成されます。

それでもOBS側で見つからない場合は、次を実行して音声を流しながら確認してください。

```bash
python main.py --audio-test
```

### Windowsで仮想環境を有効化できない

PowerShellで次を実行します。

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\.venv\Scripts\Activate.ps1
```

この変更は現在開いているPowerShellだけに適用されます。

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

## v1.3.0で追加された機能

- Windows対応
- Windows / Linux共通の`persistent`音声出力
- Pythonプロセス内での直接音声再生
- 常駐音声出力ウィンドウ
- 待機中 / 再生中の状態表示
- 簡易レベルメーター
- OBS Studioから常時選択できる音声ストリーム
- Windowsのアプリケーション音声キャプチャ対応
- Linuxで初回設定用の長い音声を流さなくてもOBSから選択できる構成
- `sounddevice`と`numpy`の依存関係追加
- Windows PowerShell向け導入手順
- OS共通の音声テスト案内
- `settings/config.json.example`の標準音声出力を`persistent`へ変更

## v1.2.0で追加された機能

- AivisSpeech EngineとVOICEVOX Engineの同時利用
- 音声プロファイルごとのTTSエンジン選択
- 配信者、モデレーター、VIP、サブスクライバーごとのエンジン切り替え
- Web UIからの役割別音声エンジン設定
- 選択したエンジンに応じた話者・スタイル一覧の動的取得
- 選択したエンジンでのテスト読み上げ
- 旧設定で`tts.backend`を使用する後方互換
- 複数TTSエンジンを管理する`TtsEngineManager`
- Web UIの設定カード順の整理

## 今後の候補

- 辞書のブラウザ編集
- 音声出力設定のWeb UI化
- フィルタールールのON/OFF
- ユーザーごとの個別音声
- Web UIからの本体起動・停止
- Windows向け配布方法の改善

## ライセンス

AivisVoiceBridge本体はMIT Licenseで公開しています。

AivisSpeech Engine、VOICEVOX Engine、各音声モデル、音声ライブラリ、OBS Studio、obs-pipewire-audio-captureなどの外部ソフトウェアは、それぞれのライセンスや利用規約に従ってください。

本リポジトリには次のものを含めません。

- TTSエンジン本体
- 音声モデル
- Twitchトークン
- Client Secretを含む個人設定
- 個人用辞書

## 謝辞

Linux環境でのPipeWireアプリ別音声キャプチャには、obs-pipewire-audio-captureプラグインを利用できます。

AivisVoiceBridgeの音声をOBS上で個別ソースとして扱える仕組みを提供している開発者の方に感謝します。
