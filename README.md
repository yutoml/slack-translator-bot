# slack_translator_bot

## 概要

Slack上でdeeplのapiを利用して翻訳をおこなうbot.

## 機能

* 特定の人物にメンションしているメッセージをメンションされた人物にとって適切な言語で翻訳

* 特定のリアクションがついたメッセージにそのリアクションで指定される言語で翻訳

* Messageについている三点リーダからショートカット"Translate"を選択し、翻訳先の言語を選ぶと、操作者にしか見えないMessageで翻訳が見れる

## 実行方法

* slack apiからappを作成する
  * socket modeを有効化する
  * Features -> OAuth & Permissions -> Scopes -> Bot Token Scopesから以下の権限を有効化する
    * channels:history
    * chat:write
    * commands
    * im:history
    * im:read
    * im:write
    * reactions:read
  * Eventへの反応を有効化する(Event Subscription -> Subscribe to bot events)
    * app_mention
    * message.channels
    * message.im
    * reaction_added
  * ショートカットを2つ作成する.
    * Globalショートカットを選択し、callback_idは"automatic_translate_setting"とする. Nameはなんでもよい
    * Messagesショートカットを選択し、callback_idは"translate_ephemeral"とする.Nameについては同上
  * Install Appを選択してBotのトークンを発行する
* deepl apiのトークンも発行する
* .envファイルをDockerfileと同じ階層に作成し、以下のように書き込む

```.env
# Token for Slack Bot
SLACK_BOT_TOKEN = "xoxb-~"
# Token for Slack API WebSocket
SLACK_APP_TOKEN = "xapp-~"
# Token for deepl
DEEPL_API_TOKEN = "~"
```

* dockerfileからimageを作成し、dataディレクトリを/app/dataにマウントして実行する

```sh
docker build . -t slacktranslatorbot
docker run -it --volume $PWD/data/:/app/data slacktranslatorbot
```

* メンションされた場合に自動的な翻訳を実行するには、あらかじめ検索タブから"Auto Translation Setting"を選択して、メンション対象の人物と翻訳先の言語を選択する必要がある

## 設定方法

templateにあるlanguage_config.jsonをdataディレクトリにコピーして言語とreactionとdeeplで使用される言語コードのセットを変更することで対応する言語を増やしたり、変更したりできる
モーダルやmentionの挙動もtemplateにあるjsonファイルをdataディレクトリにコピーして編集することで挙動を変えることができる

## TODO

* 用語集の対応(主にUIにおいて問題が存在)
* 翻訳先と翻訳対象の人物のみならず翻訳元のメッセージを作成した人物も参照することによる翻訳機能の改善
* Tokenの残量や設定状態などを確認できるインターフェースの実装
