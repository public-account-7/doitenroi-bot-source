from .storage import (
    save_files,
    MAX_SIZE
)

from .snipes import (
    add_edit_snipe,
    load_snipes
)


snipes = {}


async def message_edit(
    bot,
    before,
    after
):
    global snipes

    if not snipes:
        snipes = load_snipes(
            bot
        )

    if before.author.bot:
        return

    if not before.guild:
        return

    if (
        before.content == after.content
        and
        before.attachments == after.attachments
    ):
        return

    attachments_data = []

    for a in before.attachments:
        try:
            data = await a.read()

            if len(data) <= MAX_SIZE:
                attachments_data.append(
                    (a, data)
                )

        except:
            pass

    before_files = await save_files(
        bot,
        attachments_data
    )

    after_files = [
        f"{a.filename}|URL:{a.url}"
        for a in after.attachments
    ]

    await add_edit_snipe(
        bot,
        snipes,
        before,
        after,
        before_files,
        after_files
    )