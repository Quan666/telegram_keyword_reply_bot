import json
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext
from telegram.ext.filters import TEXT
import re

# 依赖安装
# pip install python-telegram-bot

# 注意: 群组内需要添加机器人为管理员才能正常回复

# 管理员 ID
ADMIN_IDS = [1234567890]
# 机器人 Token
BOT_TOKEN = "1234567890:AAEbgLEbVt5h1Yz8p2Iw3f2UpIuJm9FMnbY"
# 回复CHAT_ID白名单, 为空则不限制, 设置后只有在白名单内的群组或用户才会回复
REPLY_CHAT_IDS = []

# 回复内容格式
PARSE_MODE = "Markdown"
# 关键词分隔符
KEYWORD_SEPARATOR = " "
# 回复内容用代码块包裹, 默认为 True, 可以设置为 False
CODE_BLOCK_TEXT = True
# 启用正则匹配, 默认为 True, 可以设置为 False
ENABLE_REGEX = True
# 大小写不敏感, 默认为 True, 可以设置为 False
IGNORE_CASE = True
# 回复内容解析模式是否解析为 Markdown
REPLY_PARSE_MODE_MARKDOWN = True

# 存储关键词和回复的字典
keywords_responses = {}


# 存储关键词
def save_keywords_responses():
    # json，utf-8编码
    with open("keywords_responses.json", "w", encoding="utf-8") as f:
        json.dump(keywords_responses, f, ensure_ascii=False, indent=4)


# 读取关键词
def load_keywords_responses():
    global keywords_responses
    try:
        with open("keywords_responses.json", "r", encoding="utf-8") as f:
            keywords_responses = json.load(f)
    except FileNotFoundError:
        keywords_responses = {}


def get_response_show_text(response: str, title: str = "回复内容") -> str:
    if CODE_BLOCK_TEXT and "```" not in response:
        return f"```回复内容\n{response}```"
    return f"{title}:\n{response}"


# 检查用户是否有权限执行增删改操作
def check_permission(user_id):
    # 这里只允许具有管理员权限的用户ID执行操作
    return user_id in ADMIN_IDS


# 增加关键词回复
async def add(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not check_permission(user_id):
        await update.message.reply_text("您没有权限执行此操作。")
        return
    msg = update.message.text.strip().removeprefix("/add").strip()
    arguments = msg.split(KEYWORD_SEPARATOR, 1)
    if len(arguments) < 2:
        await update.message.reply_text(
            f"请输入正确的格式 (关键词{KEYWORD_SEPARATOR}回复)。"
        )
        return
    keyword = arguments[0]
    response = KEYWORD_SEPARATOR.join(arguments[1:])
    if REPLY_PARSE_MODE_MARKDOWN:
        # 去掉消息中的命令、前后空格
        msg = update.message.text_markdown_v2.strip().removeprefix("/add").strip()
        arguments = msg.split(KEYWORD_SEPARATOR, 1)
        if len(arguments) < 2:
            await update.message.reply_text(
                f"请输入正确的格式 (关键词{KEYWORD_SEPARATOR}回复)。"
            )
            return
        response = KEYWORD_SEPARATOR.join(arguments[1:])

    # 如果关键词已存在
    if keyword in keywords_responses:
        await update.message.reply_text(
            f"关键词 `{keyword}` 已存在。", parse_mode="Markdown"
        )
        return
    keywords_responses[keyword] = response
    await update.message.reply_text(
        f"关键词 `{keyword}` 已添加。\n{get_response_show_text(response)}",
        parse_mode="Markdown",
    )
    save_keywords_responses()


# 修改关键词回复
async def modify(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not check_permission(user_id):
        await update.message.reply_text("您没有权限执行此操作。")
        return
    msg = update.message.text.strip().removeprefix("/modify").strip()
    arguments = msg.split(KEYWORD_SEPARATOR)
    if len(arguments) < 2:
        await update.message.reply_text(
            f"请输入正确的格式 (关键词{KEYWORD_SEPARATOR}回复)。"
        )
        return
    keyword = arguments[0]
    new_response = KEYWORD_SEPARATOR.join(arguments[1:])
    if REPLY_PARSE_MODE_MARKDOWN:
        # 去掉消息中的命令、前后空格
        msg = update.message.text_markdown_v2.strip().removeprefix("/modify").strip()
        arguments = msg.split(KEYWORD_SEPARATOR, 1)
        if len(arguments) < 2:
            await update.message.reply_text(
                f"请输入正确的格式 (关键词{KEYWORD_SEPARATOR}回复)。"
            )
            return
        new_response = KEYWORD_SEPARATOR.join(arguments[1:])

    if keyword in keywords_responses:
        await update.message.reply_text(
            f"关键词 `{keyword}` 已更新。\n{get_response_show_text(new_response,'新回复内容')}\n{get_response_show_text(keywords_responses[keyword],'旧回复内容')}",
            parse_mode="Markdown",
        )
        keywords_responses[keyword] = new_response
        save_keywords_responses()
    else:
        await update.message.reply_text(f'关键词 "{keyword}" 不存在。')


# 删除关键词回复
async def delete(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not check_permission(user_id):
        await update.message.reply_text("您没有权限执行此操作。")
        return
    keyword = " ".join(context.args)
    if keyword in keywords_responses:
        del_res = keywords_responses.pop(keyword)
        await update.message.reply_text(
            f"关键词 `{keyword}` 已删除。\n{get_response_show_text(del_res)}",
            parse_mode="Markdown",
        )
        save_keywords_responses()
    else:
        await update.message.reply_text(f"关键词 `{keyword}` 不存在。")


# 列出所有关键词及其回复, 如下格式
# 1. 关键词: a
#    回复: b
# -------------------
# 2. 关键词: c
#    回复: d
async def list_keywords(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not check_permission(user_id):
        await update.message.reply_text("您没有权限执行此操作。")
        return
    if keywords_responses:
        message = ""
        for i, (keyword, response) in enumerate(keywords_responses.items(), 1):
            message += (
                f"{i}. 关键词: `{keyword}`\n{get_response_show_text(response)}\n\n"
            )
        await update.message.reply_text(message, parse_mode="Markdown")
    else:
        await update.message.reply_text("目前没有设置任何关键词回复。")


# id
async def id(update: Update, context: CallbackContext) -> None:
    await update.message.reply_text(
        f"Chat ID: `{update.effective_chat.id}`\nSender ID: `{update.effective_user.id}`",
        parse_mode="Markdown",
    )


# help
async def help(update: Update, context: CallbackContext) -> None:
    user_id = update.effective_user.id
    if not check_permission(user_id):
        await update.message.reply_text("您没有权限执行此操作。")
        return
    help_message = f"""
    `/add 关键词{KEYWORD_SEPARATOR}回复`: 添加关键词回复
    `/modify 关键词{KEYWORD_SEPARATOR}回复`: 修改关键词回复
    `/delete 关键词`: 删除关键词回复
    `/list`: 列出所有关键词回复
    `/id`: 显示 Chat ID
    `/help`: 显示帮助信息
    """
    # 格式化
    help_message = help_message.strip()
    # 去掉每行前面的空格
    help_message = "\n".join(line.strip() for line in help_message.splitlines())
    await update.message.reply_text(help_message, parse_mode="Markdown")


# 处理普通消息
async def handle_message(update: Update, context: CallbackContext) -> None:
    # 输出群组ID
    if (REPLY_CHAT_IDS and update.effective_chat.id not in REPLY_CHAT_IDS) or (
        update.effective_user.id not in ADMIN_IDS
    ):
        return
    message = update.message.text
    for keyword, response in keywords_responses.items():
        if ENABLE_REGEX and re.search(keyword, message, re.I if IGNORE_CASE else 0):
            await update.message.reply_text(response, parse_mode=PARSE_MODE)
            break
        elif IGNORE_CASE and keyword.lower() in message.lower():
            await update.message.reply_text(response, parse_mode=PARSE_MODE)
            break
        elif keyword in message:
            await update.message.reply_text(response, parse_mode=PARSE_MODE)
            break


# 主函数
def main() -> None:

    load_keywords_responses()
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("add", add))
    application.add_handler(CommandHandler("modify", modify))
    application.add_handler(CommandHandler("delete", delete))
    application.add_handler(CommandHandler("list", list_keywords))
    application.add_handler(CommandHandler("id", id))
    application.add_handler(CommandHandler("help", help))
    application.add_handler(MessageHandler(TEXT, handle_message))
    print("开始运行...")
    print(f"共计 {len(keywords_responses)} 条关键词回复。")
    application.run_polling()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        save_keywords_responses()
        print("退出程序。")
