# slack_translator_bot

## 概要

Slack上でdeeplのapiを利用して翻訳をおこなうbot.

## 機能

* 特定の人物にメンションしているメッセージをメンションされた人物にとって適切な言語で翻訳
* 特定のリアクションがついたメッセージにそのリアクションで指定される言語で翻訳

## 実行方法

* dockerfileからimageを作成し、dataディレクトリを/app/dataにマウントして実行する

```sh
docker build . -t slacktranslatorbot
docker run -it --volume $PWD/data/:/app/data slacktranslatorbot
```
