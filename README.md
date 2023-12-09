# slack_translator_bot

## 概要

Slack上でdeeplのapiを利用して翻訳をおこなうbot.

## 機能

* 特定の人物にメンションしているメッセージをメンションされた人物にとって適切な言語で翻訳

![Alt text](/images/image.png)

* 特定のリアクションがついたメッセージにそのリアクションで指定される言語で翻訳

![Alt text](images/image-1.png)

## 実行方法

* dockerfileからimageを作成し、dataディレクトリを/app/dataにマウントして実行する

```sh
docker build . -t slacktranslatorbot
docker run -it --volume $PWD/data/:/app/data slacktranslatorbot
```

* メンションされた場合に自動的な翻訳を実行するには、あらかじめ検索タブから"Auto Translation Setting"を選択して、メンション対象の人物と翻訳先の言語を選択する必要がある

![Alt text](images/image-2.png)

![Alt text](images/image-3.png)

## 設定方法

dataディレクトリ含まれるlanguage_config.jsonで言語とreactionとdeeplで使用される言語コードがセットになって保存されている。これを編集することで対応する言語を増やせる
