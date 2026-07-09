from collections import deque
from datetime import (
    datetime,
    timezone
)


MAX_SNIPE_DATA = 50


def load_snipes(bot):
    snipes = {}

    guilds = (
        bot.load_data()
        .get("guilds", {})
    )

    for gid, g in guilds.items():
        snipes[int(gid)] = deque(
            g.get("snipes", []),
            maxlen=MAX_SNIPE_DATA
        )

    return snipes


async def save_snipes(
    bot,
    snipes,
    gid
):
    guilds = bot.load_data().setdefault(
        "guilds",
        {}
    )

    guild = guilds.setdefault(
        str(gid),
        {}
    )

    guild["snipes"] = list(
        snipes.get(gid, [])
    )

    await bot.save_data()


async def add_delete_snipe(
    bot,
    snipes,
    message,
    files
):
    gid = message.guild.id

    guild_snipes = snipes.setdefault(
        gid,
        deque(maxlen=MAX_SNIPE_DATA)
    )

    data = {
        "content": message.content,
        "author": str(message.author),
        "avatar": message.author.display_avatar.url,
        "files": files,
        "channel": message.channel.id,
        "edited": False,
        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()
    }

    if message.reference:
        data["reply_url"] = (
            f"https://discord.com/channels/"
            f"{message.guild.id}/"
            f"{message.channel.id}/"
            f"{message.reference.message_id}"
        )

    guild_snipes.append(data)

    await save_snipes(
        bot,
        snipes,
        gid
    )


async def add_edit_snipe(
    bot,
    snipes,
    before,
    after,
    before_files,
    after_files
):
    gid = before.guild.id

    guild_snipes = snipes.setdefault(
        gid,
        deque(maxlen=MAX_SNIPE_DATA)
    )

    guild_snipes.append({
        "content": before.content,
        "after": after.content,

        "files_before": before_files,
        "files_after": after_files,

        "author": str(before.author),
        "avatar": before.author.display_avatar.url,

        "channel": before.channel.id,
        "edited": True,

        "timestamp": datetime.now(
            timezone.utc
        ).isoformat()
    })

    await save_snipes(
        bot,
        snipes,
        gid
    )