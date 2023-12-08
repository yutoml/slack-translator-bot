from slack_bolt import App
from slack_bolt import Say
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

import deepl

import os
import logging
import json

# Token for Slack Bot
SLACK_BOT_TOKEN = os.environ["SLACK_BOT_TOKEN"]
# Token for Slack API WebSocket
SLACK_APP_TOKEN = os.environ["SLACK_APP_TOKEN"]
# Token for deepl
DEEPL_API_TOKEN = os.environ["DEEPL_API_TOKEN"]
app = App(token=SLACK_BOT_TOKEN)
app.client.chat_postMessage(channel="D0699TQKVGB", text="Bot started")


translator = deepl.Translator(DEEPL_API_TOKEN)

logging.basicConfig(level=logging.DEBUG)

languages = {
    "jp": "JA",  # Japanese
    "us": "EN-US",  # American
    "cn": "ZH",  # Chinese
}


class Setting():
    def __init__(self) -> None:
        self.path = os.path.join(os.path.dirname(
            os.path.dirname(__file__)), "setting.json")
        self.param = self.read()

    def read(self):
        with open(self.path, mode="r") as file:
            param: dict = json.load(file)
        return param

    def write(self):
        with open(self.path, mode="w") as file:
            json.dump(self.param, file)


setting = Setting()


@app.middleware
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@app.event("reaction_added")
def translate_reacted_text(event, say: Say):

    if not event["reaction"] in languages:
        return
    else:
        # 押されたreactionがlanguagesに含まれていた場合
        target_lang = languages[event["reaction"]]

    # reactionが押された情報から投稿の内容を抜き取る
    replies = say.client.conversations_replies(
        channel=event["item"]["channel"], ts=event["item"]["ts"])

    # まさかのeventに文章が格納されていないため、
    # threadを確認し、tsをみてどれがreactionが押されたmessageが探す
    # reactionが押された投稿の文章を格納
    message = [message for message in replies["messages"]
               if message.get("ts") == event["item"]["ts"]][0]

    translate_and_reply(message=message, say=say, target_lang=target_lang)


def translate_and_reply(message: dict, say: Say, target_lang: str):
    original_text: str = message["text"]

    # deeplを利用して翻訳
    result = translator.translate_text(
        original_text, target_lang=target_lang)

    # ">"を利用して引用扱い
    quoted_text = ""
    for m in original_text.split("\n"):
        quoted_text += f">{m}\n"

    # thread_tsがmessageに含まれていればthread_tsを使用し、なければtsを使用する
    thread_ts = message.get("thread_ts") or message.get("ts")

    # 翻訳元の文章を表示して後から翻訳語の文章を表示する
    say(text=f"{quoted_text}{result.text}",
        thread_ts=thread_ts)


# メンションされた場合に翻訳を行う人物とその言語を設定するshortcutとモーダル
# この情報はjsonで保存される
@app.shortcut("automatic_translate_setting")
def handle_shortcut(ack, body: dict, client: WebClient):
    # ack(acknowledge): slackサーバへの受付を始めたというレスポンス
    # 3秒以内にレスポンスしないとTimeout扱いになる
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view=setting.param["modal_view"],
    )


@app.view(setting.param["modal_view"]["callback_id"])
def handle_view_submission(ack, view, logger):
    # 送信された input ブロックの情報はこの階層以下に入っています
    inputs = view["state"]["values"]
    # 最後の "value" でアクセスしているところはブロックエレメントのタイプによっては異なります
    # パターンによってどのように異なるかは後ほど詳細を説明します

    user = inputs.get("user_select", {}
                      ).get("user_select-action", {}).get("value")
    languages = [selected_option["value"] for selected_option in inputs.get("languages_select", {}
                                                                            ).get("languages-select-action", {}).get("selected_options")]

    setting.param["automatic_translation_setting"].update({user: languages})
    setting.write()
    # 正常パターン、実際のアプリではこのタイミングでデータを保存したりする
    logger.info(
        f"Updated automatic translation setting: {setting.param['automatic_translation_setting']}")

    ack()


# イベント API
@app.message("こんにちは")
def handle_messge_evnts(message, say):
    say(f"こんにちは <@{message['user']}> さん！")


if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
