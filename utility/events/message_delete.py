from .storage import (
    save_files,
    MAX_SIZE
)

from .snipes import (
    add_delete_snipe,
    load_snipes
)


snipes = {}


async def message_delete(
    bot,
    message
):
    global snipes

    if not snipes:
        snipes = load_snipes(
            bot
        )

    if message.author.bot:
        return

    if not message.guild:
        return

    attachments_data = []

    for a in message.attachments:
        try:
            data = await a.read()

            if len(data) <= MAX_SIZE:
                attachments_data.append(
                    (a, data)
                )

        except:
            pass

    files = await save_files(
        bot,
        attachments_data
    )

    await add_delete_snipe(
        bot,
        snipes,
        message,
        files
    )