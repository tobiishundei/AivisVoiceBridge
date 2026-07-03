README.md に追加するセクション
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

以下のように表示されればOKです。

/usr/bin/pw-play
AivisVoiceBridge 側の設定

settings/config.json の audio を以下のように設定します。

"audio": {
  "backend": "pipewire",
  "app_name": "AivisVoiceBridge",
  "media_role": "Communication"
}

app_name は OBS 側で認識されるアプリ名です。

一度 OBS 側で選択した後に app_name を変更すると、OBS 側で再設定が必要になる場合があります。

OBS の初回設定

OBS Studio を起動します。

次に、AivisVoiceBridge の音声テストを実行します。

python main.py --audio-test

テスト音声が再生されている間に、OBS Studio で以下を設定します。

ソースを追加
Application Audio Capture (PipeWire) を選択
アプリケーション一覧から AivisVoiceBridge を選択
音声メーターが反応することを確認

テスト音声は、OBS 側でアプリケーションを選択できるように少し長めに再生されます。

一度 AivisVoiceBridge を選択すると、以降は短い読み上げでも OBS 側で認識されます。

通常起動
python main.py

Twitch コメントが読み上げられると、OBS の AivisVoiceBridge ソースだけが反応します。

ブラウザ、ゲーム、デスクトップ音声など、他のアプリケーション音声とは分離して扱えます。

動作確認済みの挙動
AivisVoiceBridge の読み上げ音声だけが OBS の AivisVoiceBridge ソースに反応する
ブラウザなど別アプリの音声には反応しない
デスクトップ音声を無効にしても、AivisVoiceBridge の読み上げ音声だけをOBSへ送れる
初回設定時は python main.py --audio-test を使うと選択しやすい
注意点

AivisVoiceBridge の音声ノードは、読み上げ中だけ PipeWire 上に表示されます。

そのため、OBS の初回設定時には通常の短いコメント読み上げではなく、以下のテストコマンドを使ってください。

python main.py --audio-test

---

## このREADMEで押さえていること

今回かなり重要だった発見はこれです。

```text
短い読み上げでは OBS のアプリ一覧に出る前にノードが消えることがある
↓
--audio-test で長めに再生する
↓
OBS で AivisVoiceBridge を選択する
↓
以降は短い読み上げでも認識される