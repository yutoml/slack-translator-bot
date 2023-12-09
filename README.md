# slack_translator_bot

## 概要

Slack上でdeeplのapiを利用して翻訳をおこなうbot.

## 機能

* 特定の人物にメンションしているメッセージをメンションされた人物にとって適切な言語で翻訳

![Alt text](/images/image.png)

* 特定のリアクションがついたメッセージにそのリアクションで指定される言語で翻訳

![Alt text](images/image-1.png)

## 実行方法

* slack apiからappを作成する
  * socket modeを有効化する
    ![Alt text](images/image-4.png)
  * Features -> OAuth & Permissions -> Scopes -> Bot Token Scopesから以下の権限を有効化する
    * channels:history
    * chat:write
    * commands
    * im:history
    * im:read
    * im:write
    * reactions:read
  * 以下の図のようにEventへの反応を有効化する
  ![Alt text](images/image-5.png)
  * ショートカットを作成する.
    * Globalショートカットを選択し、callback_idは"automatic_translate_setting"とする
    ![Alt text](images/image-6.png)
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

![Alt text](images/image-2.png)

![Alt text](images/image-3.png)

## 設定方法

templateにあるlanguage_config.jsonをdataディレクトリにコピーして言語とreactionとdeeplで使用される言語コードのセットを変更することで対応する言語を増やしたり、変更したりできる
モーダルやmentionの挙動もtemplateにあるjsonファイルをdataディレクトリにコピーして編集することで挙動を変えることができる
