from slack_bolt import App
from slack_bolt import Say
from slack_bolt.adapter.socket_mode import SocketModeHandler
from slack_sdk import WebClient

import deepl

import re
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

translator = deepl.Translator(DEEPL_API_TOKEN)

logging.basicConfig(level=logging.DEBUG)


class StaticData():
    """もとのファイルを編集しないようなデータを取り扱うクラス"""

    def __init__(self, path: str) -> None:
        self.path: str = path
        self.param: dict = self.read()

    def read(self) -> dict:
        with open(self.path, mode="r") as file:
            param: dict = json.load(file)
        return param


class Data(StaticData):
    """もとのファイルを編集する可能性があるデータを取り扱うクラス"""

    def __init__(self, path: str) -> None:
        super().__init__(path)

    def write(self):
        """もとのファイルを上書き"""
        with open(self.path, mode="w") as file:
            json.dump(self.param, file)


class LanguageConfig(StaticData):
    def __init__(self, path: str) -> None:
        super().__init__(path)

    @property
    def reaction_to_language(self) -> dict[str, str]:
        """reactionをkey, language codeをvalueとしたdictを返す"""
        return {d["reaction"]: d["code"] for d in self.param["languages"]}

    @property
    def support_languages(self) -> list[str]:
        """対応している言語のlist"""
        return [d["code"] for d in self.param["languages"]]


class Modal(StaticData):
    def __init__(self, path: str, language_config: LanguageConfig) -> None:
        self.language_config: LanguageConfig = language_config
        super().__init__(path)

    def get_option(self, config):
        return {"text": {"type": "plain_text", "text": config["language"], "emoji": True}, "value": config["code"]}

    @property
    def auto_translation_config_modal_view(self):
        """modalのviewを対応言語に合うように変更する"""
        new_options = [self.get_option(
            config) for config in self.language_config.param["languages"]]
        self.param["auto_translation_config_modal_view"]["blocks"][2]["element"]["options"] = new_options
        return self.param["auto_translation_config_modal_view"]

    def get_error_modal_view(self, text: str | None = None):
        if text == None:
            text = "Error has occur"
        self.param["error_modal_view"]["blocks"][0]["text"]["text"] = text
        return self.param["error_modal_view"]


class AutoTranslationConfig(Data):
    def __init__(self, path) -> None:
        super().__init__(path)

    @property
    def mention_pattern(self) -> re.Pattern:
        """app.messageで検出するメンションのPatternを作成する

        Returns
        -------
        str
            re.Patternオブジェクト
        """
        mentions = [f"<@{key}>" for key in self.param.keys()]
        pattern = f"({'|'.join(mentions)})"
        return re.compile(pattern=pattern)


language_config = LanguageConfig(os.path.join(os.path.dirname(
    os.path.dirname(__file__)), "data", "language_config.json"))
modal = Modal(os.path.join(os.path.dirname(
    os.path.dirname(__file__)), "data", "modal.json"), language_config=language_config)
auto_translation_config = AutoTranslationConfig(os.path.join(os.path.dirname(
    os.path.dirname(__file__)), "data", "auto_translation_config.json"))


def translate_and_reply(message: dict, say: Say, target_langs: str | list[str]):

    if type(target_langs) == str:
        target_langs = [target_langs]

    if any([not target_lang in language_config.support_languages for target_lang in target_langs]):
        raise AttributeError("対応外の言語が選択された")
    original_text: str = message["text"]

    # ">"を利用して引用扱い
    quoted_text = ""
    for m in original_text.split("\n"):
        quoted_text += f">{m}\n"

    say_text = quoted_text
    for target_lang in target_langs:
        # deeplを利用して翻訳
        result = translator.translate_text(
            original_text, target_lang=target_lang)
        say_text += result.text + "\n"

    # thread_tsがmessageに含まれていればthread_tsを使用し、なければtsを使用する
    thread_ts = message.get("thread_ts") or message.get("ts")

    # 翻訳元の文章を表示して後から翻訳語の文章を表示する
    say(text=say_text,
        thread_ts=thread_ts)


@app.middleware
def log_request(logger, body, next):
    logger.debug(body)
    return next()


@app.event("app_mention")  # ほぼテスト用
def say_hello(message, say):
    say(f"こんにちは <@{message['user']}> さん！")


@app.event("reaction_added")
def translate_reacted_text(event, say: Say):

    if not event["reaction"] in language_config.reaction_to_language:
        return
    else:
        # 押されたreactionがlanguagesに含まれていた場合
        target_lang = language_config.reaction_to_language[event["reaction"]]

    # reactionが押された情報から投稿の内容を抜き取る
    replies = say.client.conversations_replies(
        channel=event["item"]["channel"], ts=event["item"]["ts"])

    # まさかのeventに文章が格納されていないため、
    # threadを確認し、tsをみてどれがreactionが押されたmessageが探す
    # reactionが押された投稿の文章を格納
    message = [message for message in replies["messages"]
               if message.get("ts") == event["item"]["ts"]][0]

    translate_and_reply(message=message, say=say, target_langs=target_lang)


# メンションされた場合に翻訳を行う人物とその言語を設定するshortcutとモーダル
# この情報はjsonで保存される
@app.shortcut("automatic_translate_setting")
def handle_shortcut(ack, body: dict, client: WebClient):
    # ack(acknowledge): slackサーバへの受付を始めたというレスポンス
    # 3秒以内にレスポンスしないとTimeout扱いになる
    ack()
    client.views_open(
        trigger_id=body["trigger_id"],
        view=modal.auto_translation_config_modal_view,
    )


@app.view(modal.param["auto_translation_config_modal_view"]["callback_id"])
def handle_view_submission(ack, view, logger):
    inputs = view["state"]["values"]
    logger.debug(f'inputs = {view["state"]["values"]}')
    user = inputs.get("user_select", {}
                      ).get("user_select-action", {}).get("selected_user")
    languages = [selected_option["value"] for selected_option in inputs.get("languages_select", {}
                                                                            ).get("languages-select-action", {}).get("selected_options")]

    if user is not None:
        # 正常パターン
        auto_translation_config.param.update({user: languages})
        auto_translation_config.write()

        logger.info(
            f"Updated automatic translation config: {auto_translation_config.param}")

        ack()

    else:
        ack(
            response_action="update",
            view=modal.get_error_modal_view(text="Error. Select a user"),
        )


# ある特定のメンションに対して翻訳を実行する
@app.message(auto_translation_config.mention_pattern)
def auto_translate(message, say, logger):
    logger.debug(
        f"mention detected. pattern = {auto_translation_config.mention_pattern}")
    target_langs = []
    mentioned_userIDs = [userID for userID in auto_translation_config.param if re.search(
        pattern=f"<@{userID}>", string=message["text"])]

    if len(mentioned_userIDs) == 0:
        return

    for userID in mentioned_userIDs:
        target_langs += auto_translation_config.param[userID]
    target_langs = list(set(target_langs))

    translate_and_reply(message=message, say=say, target_langs=target_langs)


if __name__ == "__main__":
    handler = SocketModeHandler(app, SLACK_APP_TOKEN)
    handler.start()
